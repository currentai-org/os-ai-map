"""Tell a re-encoded image from a replaced one, for the hash-mismatched rows of the DataComp-1B pilot.

Why this exists. `build.recoverability_pilot` found that a quarter of the sampled DataComp-1B rows
still serve an image whose sha256 differs from the published one, and a hash cannot say whether
that is the same picture re-encoded or resized or a different picture. DataComp publishes, beside
each metadata parquet, a `.npz` holding the CLIP image embedding it computed for every row. This
module re-fetches only rows the pilot already sampled, embeds each fetched image in memory with the
same model and preprocessing, and compares the result with the published embedding. It keeps no
image, enlarges no sample, moves no score and gates nothing; like the pilot it is a survey and is
never wired into preflight or CI.

Run it with the heavy dependencies as an ephemeral overlay, so they never enter `pyproject.toml`:

    uv run --index pytorch-cpu=https://download.pytorch.org/whl/cpu \\
        --index-strategy unsafe-best-match --with torch --with torchvision \\
        --with open_clip_torch --with opencv-python-headless \\
        python -m build.hash_mismatch_embeddings --only control --cache <control.npz>

then, once the control reproduces its stored embeddings, the same with `--only mismatch` and
`--cache <mismatch.npz>`. `--analyze <control.npz> <mismatch.npz> --out <result.json>` merges the
two and computes thresholds, bands and intervals without touching the network or loading a model.
A cache holds embeddings and per-sample records, never image bytes or URLs; keep it out of the
repository.

What is compared. The published `l14_img` column (OpenAI CLIP ViT-L/14, float16) is primary and
`b32_img` (ViT-B/32) a corroborating second opinion. DataComp computed both on its own download, in
which img2dataset capped the longest side at 512 pixels and re-encoded as a quality-95 JPEG only
what it resized, alpha-matted or did not recognize as JPEG, keeping other downloads byte for byte;
`datacomp_view` reproduces that step before the standard CLIP transform. The control is what
showed the skip: without it, small JPEGs miss their stored embedding by a re-encode.

Samples and controls. Every row the pilot recorded as `changed_content`, plus a calibration control
of rows the pilot recorded as `hash_match`, drawn with `random.Random(f"{seed}:control")`. A
control that still matches its hash must reproduce its published embedding, which validates the
pipeline; the same controls, re-encoded and resized in memory, measure how far a known-same image
can drift. The null is each fetched embedding against the published embeddings of the other
sampled rows, so it costs no extra fetch.

Fetch rules are the pilot's, by reuse of its `Fetcher` and `fetch_sample`; see that module's
docstring. Method, thresholds and results are in
`docs/briefs/2026-11-14-openclip-hash-mismatch-embeddings.md`.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import io
import json
import platform
import random
import struct
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from build import recoverability_pilot as pilot

DEFAULT_PILOT = Path("docs/briefs/2026-11-14-openclip-recoverability-pilot.json")
DEFAULT_CONTROL_SIZE = 50
NPZ_MEMBERS = {"l14": "l14_img.npy", "b32": "b32_img.npy"}
OPEN_CLIP_MODELS = {"l14": "ViT-L-14-quickgelu", "b32": "ViT-B-32-quickgelu"}
PRIMARY = "l14"
META_COLUMNS = ["uid", "url", "sha256", "original_width", "original_height", "face_bboxes"]

# img2dataset's Resizer as DataComp's download called it (download_upstream.py defaults):
# image_size 512, resize_mode keep_ratio_largest, resize_only_if_bigger, jpg at quality 95.
I2D_SIZE = 512
I2D_QUALITY = 95
# A decoded image above this many pixels is recorded as `too_many_pixels` and not embedded, so a
# single body cannot exhaust the session's memory; every sample it touches is reported.
MAX_PIXELS = 64_000_000

# Transformations a host plausibly applies to the same picture. Each is applied in memory to a
# control image whose bytes still match the published hash, then passed through the same view as
# a fetched image. `family` decides which "same image" threshold the variant sets: `reencode`
# (same pixel dimensions) applies to a fetched image at the original dimensions, `resize` to one
# at other dimensions; the extreme and geometric variants are reported only.
VARIANTS: tuple[tuple[str, str, dict], ...] = (
    ("as_served", "reencode", {}),
    ("png", "reencode", {"fmt": "PNG"}),
    ("jpeg_q90", "reencode", {"fmt": "JPEG", "q": 90}),
    ("jpeg_q75", "reencode", {"fmt": "JPEG", "q": 75}),
    ("jpeg_q50", "reencode", {"fmt": "JPEG", "q": 50}),
    ("jpeg_q30", "reencode", {"fmt": "JPEG", "q": 30}),
    ("webp_q80", "reencode", {"fmt": "WEBP", "q": 80}),
    ("scale_0.5_q85", "resize", {"fmt": "JPEG", "q": 85, "scale": 0.5}),
    ("scale_0.25_q85", "resize", {"fmt": "JPEG", "q": 85, "scale": 0.25}),
    ("jpeg_q10", "extreme", {"fmt": "JPEG", "q": 10}),
    ("scale_0.125_q85", "extreme", {"fmt": "JPEG", "q": 85, "scale": 0.125}),
    ("crop_center_80", "geometry", {"fmt": "JPEG", "q": 90, "crop": 0.8}),
    ("pad_square_white", "geometry", {"fmt": "JPEG", "q": 90, "pad": True}),
)

HIST_EDGES = (-1.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 0.99, 1.0001)
QUANTILES = (0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
# The three embedding bands, then the two ways a row gets no comparison at all.
BANDS = ("same", "indeterminate", "different", "undecodable", "not_refetched")


# ── published metadata and embeddings ─────────────────────────────────────────────────────


def _hf_path(repo: str, revision: str, name: str) -> str:
    return f"datasets/{repo}@{revision}/{name}"


def read_metadata(repo: str, revision: str, wanted: dict[str, list[int]], workers: int = 4):
    """{(shard, row): metadata row} for the requested rows, read from the parquet files."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem(token=False)

    def one(shard):
        rows = sorted(wanted[shard])
        with fs.open(_hf_path(repo, revision, shard), "rb", block_size=8 << 20) as fh:
            table = pq.ParquetFile(fh).read(columns=META_COLUMNS).take(rows).to_pylist()
        return {(shard, r): rec for r, rec in zip(rows, table)}

    out = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(one, sorted(wanted)):
            out.update(part)
    return out


def _npy_offsets(fh, members: dict[str, str]) -> dict[str, tuple[int, tuple, str]]:
    """Locate each stored member's array data: {key: (data offset, shape, dtype)}.

    The `.npz` files are uncompressed zip archives, so a row is a fixed-size slice at a
    computable offset and can be read with one range request instead of a 3 GB download.
    """
    import numpy as np

    infos = {zi.filename: zi for zi in zipfile.ZipFile(fh).infolist()}
    out = {}
    for key, name in members.items():
        zi = infos[name]
        if zi.compress_type != zipfile.ZIP_STORED:
            raise ValueError(f"{name} is compressed; row reads need a stored member")
        fh.seek(zi.header_offset)
        local = fh.read(30)
        if local[:4] != b"PK\x03\x04":
            raise ValueError("bad local file header")
        name_len, extra_len = struct.unpack("<HH", local[26:30])
        start = zi.header_offset + 30 + name_len + extra_len
        fh.seek(start)
        head = io.BytesIO(fh.read(4096))
        version = np.lib.format.read_magic(head)
        reader = (np.lib.format.read_array_header_1_0 if version == (1, 0)
                  else np.lib.format.read_array_header_2_0)
        shape, fortran, dtype = reader(head)
        if fortran:
            raise ValueError(f"{name} is Fortran-ordered")
        out[key] = (start + head.tell(), shape, dtype.str)
    return out


def read_stored_embeddings(repo: str, revision: str, wanted: dict[str, list[int]],
                           num_rows: dict[str, int], workers: int = 8):
    """{key: {(shard, row): unit vector}} for each member in NPZ_MEMBERS."""
    import numpy as np
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem(token=False)

    def one(shard):
        npz = shard.replace(".parquet", ".npz")
        got = {k: {} for k in NPZ_MEMBERS}
        with fs.open(_hf_path(repo, revision, npz), "rb", block_size=64 << 10) as fh:
            offsets = _npy_offsets(fh, NPZ_MEMBERS)
            for key, (base, shape, dtype) in offsets.items():
                if shape[0] != num_rows[shard]:
                    raise ValueError(f"{npz}:{key} has {shape[0]} rows, parquet {num_rows[shard]}")
                width = int(np.prod(shape[1:])) * np.dtype(dtype).itemsize
                for row in sorted(wanted[shard]):
                    fh.seek(base + row * width)
                    vec = np.frombuffer(fh.read(width), dtype=dtype).astype(np.float32)
                    got[key][(shard, row)] = vec
        return got

    out = {k: {} for k in NPZ_MEMBERS}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(one, sorted(wanted)):
            for k, rows in out.items():
                rows.update(part[k])
    norms = {k: [float(np.linalg.norm(v)) for v in rows.values()] for k, rows in out.items()}
    unit = {k: {key: v / np.linalg.norm(v) for key, v in rows.items()} for k, rows in out.items()}
    return unit, norms


# ── the in-memory image views ─────────────────────────────────────────────────────────────


def _cv2_decode(body: bytes):
    """img2dataset's decode: cv2 IMREAD_UNCHANGED (no EXIF rotation), alpha matted on white."""
    import cv2
    import numpy as np
    from PIL import Image

    try:  # header only: Pillow reads the size without decoding pixels
        w, h = Image.open(io.BytesIO(body)).size
    except Exception:  # noqa: BLE001  -- cv2 may still read what Pillow cannot identify
        w = h = 0
    if w * h > MAX_PIXELS:
        raise ValueError("too_many_pixels")
    img = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_UNCHANGED)
    decoder = "cv2"
    if img is None:
        # cv2 cannot read this container (img2dataset would have failed on it). Decode the first
        # frame with Pillow so the image can still be compared; the record says which was used.
        pil = Image.open(io.BytesIO(body))
        pil.seek(0)
        pil = pil.convert("RGBA")
        img = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGBA2BGRA)
        decoder = "pillow_fallback"
    if img.shape[0] * img.shape[1] > MAX_PIXELS:
        raise ValueError("too_many_pixels")
    if img.dtype != np.uint8:
        img = (img.astype(np.float32) / 257.0).round().clip(0, 255).astype(np.uint8)
    if img.ndim == 3 and img.shape[-1] == 4:
        # img2dataset's matte, in float32 rather than float64 to bound memory.
        alpha = img[:, :, 3, np.newaxis].astype(np.float32)
        img = alpha / 255 * img[..., :3].astype(np.float32) + 255 - alpha
        img = np.rint(img.clip(min=0, max=255)).astype(np.uint8)
        return img, decoder, True
    return img, decoder, False


IMGHDR_RULES = ("markers", "markers_or_raw")


def imghdr_says_jpeg(body: bytes, rule: str) -> bool:
    """`imghdr.what(...) == "jpeg"`, which img2dataset's `skip_reencode` tests.

    `imghdr` (removed in Python 3.13) tested the first bytes: a JFIF or Exif marker at offset 6
    in every version, and, in later versions only, a bare `FF D8 FF DB` start. Which Python ran
    DataComp's download is not recorded, so both readings are kept and the control decides.
    """
    if body[6:10] in (b"JFIF", b"Exif"):
        return True
    return rule == "markers_or_raw" and body[:4] == b"\xff\xd8\xff\xdb"


def reencode_needed(flags: dict, rule: str) -> bool:
    """img2dataset 1.41 with skip_reencode: re-encode after a resize, an alpha matte, or a
    container `imghdr` does not call JPEG; otherwise store the downloaded bytes unchanged."""
    return flags["resized"] or flags["alpha"] or not flags[f"imghdr_jpeg_{rule}"]


def reencoded_view(body: bytes):
    """The image after img2dataset's resize and JPEG re-encode, as a PIL RGB image.

    img2dataset's Resizer with DataComp's arguments: longest side capped at 512 with cv2's
    INTER_AREA only when larger, then encoded as JPEG quality 95. Returns (image, decoded
    (width, height), decoder, flags), where flags say whether img2dataset would have re-encoded
    at all (see `reencode_needed`).
    """
    import cv2
    from PIL import Image

    img, decoder, alpha = _cv2_decode(body)
    h, w = img.shape[:2]
    resized = max(h, w) > I2D_SIZE
    if resized:
        scale = I2D_SIZE / float(max(h, w))
        img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    ok, enc = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), I2D_QUALITY])
    if not ok:
        raise ValueError("jpeg encode failed")
    flags = {"resized": resized, "alpha": alpha,
             **{f"imghdr_jpeg_{r}": imghdr_says_jpeg(body, r) for r in IMGHDR_RULES}}
    return Image.open(io.BytesIO(enc.tobytes())).convert("RGB"), (w, h), decoder, flags


def datacomp_view(body: bytes, rule: str):
    """The image as DataComp's download stored it: re-encoded if needed, else the bytes as is."""
    view, _dims, _decoder, flags = reencoded_view(body)
    return view if reencode_needed(flags, rule) else raw_view(body)


def raw_view(body: bytes):
    """The downloaded bytes straight through Pillow, with no img2dataset step."""
    from PIL import Image

    pil = Image.open(io.BytesIO(body))
    pil.seek(0)
    return pil.convert("RGB")


def transformed_bytes(body: bytes, spec: dict) -> bytes:
    """A control image re-encoded, resized, cropped or padded in memory, as a host might."""
    from PIL import Image

    if not spec:
        return body
    pil = Image.open(io.BytesIO(body))
    pil.seek(0)
    rgba = pil.convert("RGBA")
    base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    img = Image.alpha_composite(base, rgba).convert("RGB")
    w, h = img.size
    if "crop" in spec:
        cw, ch = max(1, round(w * spec["crop"])), max(1, round(h * spec["crop"]))
        left, top = (w - cw) // 2, (h - ch) // 2
        img = img.crop((left, top, left + cw, top + ch))
    if spec.get("pad"):
        side = max(w, h)
        canvas = Image.new("RGB", (side, side), (255, 255, 255))
        canvas.paste(img, ((side - w) // 2, (side - h) // 2))
        img = canvas
    if "scale" in spec:
        nw, nh = max(1, round(w * spec["scale"])), max(1, round(h * spec["scale"]))
        img = img.resize((nw, nh), Image.LANCZOS)
    out = io.BytesIO()
    kwargs = {"quality": spec["q"]} if "q" in spec else {}
    img.save(out, format=spec["fmt"], **kwargs)
    return out.getvalue()


class Embedder:
    """The two OpenAI CLIP image towers, called from one worker thread only."""

    def __init__(self):
        import open_clip
        import torch

        torch.set_grad_enabled(False)
        self.torch = torch
        self.models = {}
        for key, name in OPEN_CLIP_MODELS.items():
            model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained="openai")
            model.eval()
            self.models[key] = (model, preprocess)
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embed")
        self.images_embedded = 0
        self.seconds = 0.0

    def embed(self, images) -> dict:
        import numpy as np

        t = time.monotonic()
        out = {}
        for key, (model, preprocess) in self.models.items():
            parts = []
            with self.torch.inference_mode():
                for k in range(0, len(images), 4):   # small batches bound activation memory
                    batch = self.torch.stack([preprocess(im) for im in images[k:k + 4]])
                    feats = model.encode_image(batch).float()
                    parts.append((feats / feats.norm(dim=-1, keepdim=True)).numpy())
            out[key] = np.concatenate(parts).astype(np.float32)
        self.images_embedded += len(images)
        self.seconds += time.monotonic() - t
        return out


def embed_body(embedder: Embedder, body: bytes, calibrate: bool) -> dict:
    """Everything this module keeps from one image body: hashes, dimensions, embeddings."""
    rec = {"sha256": hashlib.sha256(body).hexdigest()}
    # Decoding and embedding run on the embedder's one worker thread, so at most one decoded image
    # is in memory at a time. The first two runs of this module were killed for memory because
    # torch's no-grad switch is per thread: set in the main thread, it did not cover the fetch
    # threads that called the model, which then recorded autograd state. `embed` now enters
    # inference mode itself.
    return embedder.worker.submit(_embed_locked, embedder, body, calibrate, rec).result()


def _embed_locked(embedder: Embedder, body: bytes, calibrate: bool, rec: dict) -> dict:
    try:
        names, images = [], []
        view, dims, decoder, flags = reencoded_view(body)
        rec.update(decoded_dims=list(dims), decoder=decoder, i2d_flags=flags)
        names.append("reencoded_view")
        images.append(view)
        try:
            images.append(raw_view(body))
            names.append("raw_view")
        except Exception as err:  # noqa: BLE001  -- recorded, the primary view stands
            rec["raw_view_error"] = type(err).__name__
        if calibrate:
            for name, _family, spec in VARIANTS[1:]:
                try:
                    # Pillow writes a JFIF marker, so both imghdr readings agree here.
                    images.append(datacomp_view(transformed_bytes(body, spec), "markers"))
                    names.append(f"variant:{name}")
                except Exception as err:  # noqa: BLE001
                    rec.setdefault("variant_errors", {})[name] = type(err).__name__
        feats = embedder.embed(images)
        rec["embeddings"] = {key: {n: feats[key][i] for i, n in enumerate(names)}
                             for key in feats}
    except Exception as err:  # noqa: BLE001  -- an undecodable body is an outcome, not a crash
        rec["embed_error"] = f"{type(err).__name__}: {err}"[:200]
    return rec


# ── selection ─────────────────────────────────────────────────────────────────────────────


def choose(pilot_result: dict, control_size: int, seed: int, only: str | None = None) -> list[dict]:
    manifest = pilot_result["manifest"]
    mismatch = [dict(m, group="mismatch") for m in manifest if m["outcome"] == pilot.CHANGED]
    matched = [m for m in manifest if m["outcome"] == pilot.SUCCESS]
    control = random.Random(f"{seed}:control").sample(matched, control_size)
    chosen = mismatch + [dict(m, group="control") for m in control]
    return [s for s in chosen if only is None or s["group"] == only]


# ── statistics ────────────────────────────────────────────────────────────────────────────


def quantiles(values) -> dict:
    import numpy as np

    if len(values) == 0:
        return {}
    arr = np.asarray(values, dtype=np.float64)
    return {f"q{int(q * 100):02d}" if q not in (0.0, 1.0) else ("min" if q == 0 else "max"):
            round(float(np.quantile(arr, q)), 4) for q in QUANTILES} | {
        "n": int(arr.size), "mean": round(float(arr.mean()), 4)}


def histogram(values) -> list[dict]:
    import numpy as np

    counts, _ = np.histogram(np.asarray(values, dtype=np.float64), bins=HIST_EDGES)
    out = []
    for lo, hi, c in zip(HIST_EDGES[:-1], HIST_EDGES[1:], counts):
        label = (f"< {hi:g}" if lo == HIST_EDGES[0]
                 else f"{lo:g} to {min(hi, 1.0):g}")
        out.append({"bin": label, "count": int(c)})
    return out


def band_of(cos: float | None, t_same: float, t_diff: float, decoded: bool = True) -> str:
    if cos is None:
        return "not_refetched" if decoded else "undecodable"
    if cos >= t_same and cos > t_diff:
        return "same"
    if cos <= t_diff and cos < t_same:
        return "different"
    return "indeterminate"


def bootstrap_bands(records: list[dict], levels, reps: int, seed: str) -> dict:
    """Shard-bootstrap shares of `records` at each band, by the pilot's own `shard_bootstrap`.

    The pilot is two-stage: files drawn, then rows within them. Resampling whole files with
    replacement carries the between-file variance, so these intervals respect the design, but
    with 50 clusters they are approximate, and the brief labels them so.
    """
    if not records:   # a control-only stage has no mismatch rows to band
        return {"n": 0, "bands": {}}
    est = pilot.shard_bootstrap(records, {b: (lambda r, b=b: r["band"] == b) for b in levels},
                                reps=reps, seed=seed)
    n = len(records)
    out = {}
    for b in levels:
        e = est["estimates"][b]
        k = sum(1 for r in records if r["band"] == b)
        out[b] = {"count": k, "share": e["share"], "share_ci95_approx": e["ci95"],
                  "count_ci95_approx": [round(e["ci95"][0] * n, 1), round(e["ci95"][1] * n, 1)],
                  "design_effect": e["design_effect"]}
    return {"method": est["method"], "replicates": est["replicates"], "seed": est["seed"],
            "clusters": est["clusters"], "n": n, "bands": out}


# ── analysis ──────────────────────────────────────────────────────────────────────────────


def analyze(cache: dict, args) -> dict:
    import numpy as np

    samples = cache["samples"]
    stored = cache["stored"]           # {key: {(shard,row): vec}}
    fetched = cache["fetched"]         # {i: {key: {view: vec}}}
    all_rows = sorted(stored[PRIMARY])
    row_pos = {r: i for i, r in enumerate(all_rows)}
    hosts = cache["hosts"]             # {(shard,row): host}
    host_types = cache["host_types"]
    mats = {k: np.stack([stored[k][r] for r in all_rows]) for k in stored}

    # Which `imghdr` reading DataComp's download had is not recorded; the control decides it,
    # as the reading under which hash-matched images best reproduce their stored embeddings.
    def resolve(rule):
        for i, by_key in fetched.items():
            flags = samples[i].get("i2d_flags")
            for views in by_key.values():
                if flags is None or "reencoded_view" not in views:
                    continue
                pick = "reencoded_view" if reencode_needed(flags, rule) else "raw_view"
                if pick in views:
                    views["datacomp_view"] = views[pick]

    def cos(key, i, view="datacomp_view"):
        emb = fetched.get(i, {}).get(key, {}).get(view)
        if emb is None:
            return None
        s = samples[i]
        return float(emb @ stored[key][(s["shard"], s["row"])])

    # Control: validation and calibration.
    controls = [i for i, s in enumerate(samples) if s["group"] == "control"]
    ctrl_ok = [i for i in controls if samples[i].get("refetch_hash_matches_published")
               and i in fetched]
    validation, calibration, families = {}, {}, {}
    rule_fit = {}
    for rule in IMGHDR_RULES:
        resolve(rule)
        rule_fit[rule] = float(np.mean([cos(PRIMARY, i) for i in ctrl_ok]))
    rule = args.imghdr_rule if args.imghdr_rule != "auto" else max(rule_fit, key=rule_fit.get)
    for key in stored:
        validation[key] = {}
        for r in IMGHDR_RULES:
            resolve(r)
            validation[key][f"datacomp_view[{r}]"] = quantiles([cos(key, i) for i in ctrl_ok])
        for view in ("reencoded_view", "raw_view"):
            validation[key][view] = quantiles(
                [c for c in (cos(key, i, view) for i in ctrl_ok) if c is not None])
    resolve(rule)
    for key in stored:
        calibration[key] = {}
        fam_vals = collections.defaultdict(list)
        for name, family, _spec in VARIANTS:
            view = "datacomp_view" if name == "as_served" else f"variant:{name}"
            vals = [c for c in (cos(key, i, view) for i in ctrl_ok) if c is not None]
            calibration[key][name] = {"family": family, **quantiles(vals)}
            fam_vals[family].extend(vals)
        families[key] = fam_vals

    # Null: each fetched image against the stored embeddings of the other sampled rows.
    fetched_idx = [i for i in sorted(fetched) if fetched[i].get(PRIMARY)]
    null, null_random, null_same_host, null_same_type = {}, {}, {}, {}
    rng = random.Random(f"{args.seed}:null-pairing")
    pairing = {}
    for i in fetched_idx:
        own = (samples[i]["shard"], samples[i]["row"])
        j = own
        while j == own:
            j = all_rows[rng.randrange(len(all_rows))]
        pairing[i] = j
    for key in stored:
        allv, rnd, sh, st = [], [], [], []
        for i in fetched_idx:
            s = samples[i]
            own = (s["shard"], s["row"])
            sims = mats[key] @ fetched[i][key]["datacomp_view"]
            mask = np.ones(len(all_rows), dtype=bool)
            mask[row_pos[own]] = False
            allv.append(sims[mask])
            rnd.append(float(sims[row_pos[pairing[i]]]))
            for r in all_rows:
                if r == own:
                    continue
                if hosts[r] == hosts[own]:
                    sh.append(float(sims[row_pos[r]]))
                if host_types[r] == host_types[own] and host_types[own] != "other":
                    st.append(float(sims[row_pos[r]]))
        allv = np.concatenate(allv)
        null[key] = allv
        null_random[key], null_same_host[key], null_same_type[key] = rnd, sh, st

    thresholds = {}
    for key in stored:
        t_diff = float(np.quantile(null[key], args.null_quantile))
        thresholds[key] = {
            "different_at_or_below": round(t_diff, 4),
            "different_rule": f"{args.null_quantile:g} quantile of the all-pairs null",
            "null_q999": round(float(np.quantile(null[key], 0.999)), 4),
            "null_max": round(float(null[key].max()), 4),
        }
        for fam_name in ("reencode", "resize"):
            fam = np.asarray(families[key][fam_name])
            t_same = float(np.quantile(fam, args.same_quantile))
            thresholds[key][fam_name] = {
                "same_at_or_above": round(t_same, 4),
                "same_rule": (f"{args.same_quantile:g} quantile of control cosines over the "
                              f"{fam_name} calibration variants"),
                "family_min": round(float(fam.min()), 4),
                "overlaps_null": t_diff >= t_same,
            }

    def family_of(s):
        # This run's decoded dimensions when an image came back, else the pilot's.
        dims = s.get("refetch_dims") or ("different_dims" if s["code"] == "different_dims"
                                         else "same_dims")
        return "reencode" if dims == "same_dims" else "resize"


    # Per-sample records and bands.
    out_samples = []
    for i, s in enumerate(samples):
        rec = {k: s[k] for k in ("uid", "shard", "row", "group", "host_type") if k in s}
        rec["pilot_code"] = s["code"]
        rec["refetch_outcome"], rec["refetch_code"] = s["refetch_outcome"], s["refetch_code"]
        for k in ("refetch_hash_matches_published", "refetch_dims", "decoder", "placeholder_group",
                  "embed_error", "face_boxes"):
            if s.get(k) is not None:
                rec[k] = s[k]
        rec["threshold_family"] = family_of(s)
        if s.get("refetch_scale") is not None:
            rec["refetch_scale"] = s["refetch_scale"]
        for key in stored:
            c = cos(key, i)
            rec[f"cosine_{key}"] = None if c is None else round(c, 4)
            rec[f"band_{key}"] = band_of(c, thresholds[key][family_of(s)]["same_at_or_above"],
                                         thresholds[key]["different_at_or_below"],
                                         decoded=not s.get("embed_error"))
        c_raw = cos(PRIMARY, i, "raw_view")
        if c_raw is not None:
            rec[f"cosine_{PRIMARY}_raw_view"] = round(c_raw, 4)
        out_samples.append(rec)
    mm = [r for r in out_samples if r["group"] == "mismatch"]
    for r in mm:
        r["band"] = r[f"band_{PRIMARY}"]

    band_levels = list(BANDS)
    boot_seed = f"{args.seed}:embedding-band-bootstrap"
    bands = bootstrap_bands(mm, band_levels, args.bootstrap, boot_seed)
    # The same counts as shares of all pilot samples: every pilot row enters, non-mismatch rows
    # at a level of their own, so each replicate's denominator is its 1,000 resampled rows.
    by_uid = {r["uid"]: r["band"] for r in mm}
    pilot_rows = [{"shard": m["shard"], "band": by_uid.get(m["uid"], "not_in_mismatch")}
                  for m in cache["pilot_manifest"]]
    bands_of_all = bootstrap_bands(pilot_rows, band_levels, args.bootstrap, boot_seed)
    # Read together with the pilot: rows whose bytes matched the published hash in the pilot, or
    # whose changed bytes fall in the "same" band here.
    with open(args.pilot, encoding="utf-8") as fh:
        outcome = {m["uid"]: m["outcome"] for m in json.load(fh)["manifest"]}
    combined_rows = [{"shard": m["shard"],
                      "band": ("same_picture" if outcome[m["uid"]] == pilot.SUCCESS
                               or by_uid.get(m["uid"]) == "same" else "other")}
                     for m in cache["pilot_manifest"]]
    combined = bootstrap_bands(combined_rows, ["same_picture"], args.bootstrap, boot_seed)

    def split(field):
        groups = collections.defaultdict(list)
        for r in mm:
            groups[r[field]].append(r)
        table = {}
        for g, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            cs = [r[f"cosine_{PRIMARY}"] for r in rows if r[f"cosine_{PRIMARY}"] is not None]
            table[g] = {"samples": len(rows),
                        **{b: sum(1 for r in rows if r["band"] == b) for b in BANDS},
                        "cosine": quantiles(cs)}
        return table

    mm_cos = {key: [r[f"cosine_{key}"] for r in mm if r[f"cosine_{key}"] is not None]
              for key in stored}
    agree = collections.Counter((r[f"band_{PRIMARY}"], r["band_b32"]) for r in mm
                                if r["band"] not in ("not_refetched", "undecodable"))

    # How the counts move if the thresholds are set at other quantiles; nothing is refetched.
    sensitivity = []
    for sq, nq in ((0.0, 0.99), (0.01, 0.99), (0.05, 0.99), (0.01, 0.95), (0.01, 0.999),
                   (0.0, 0.999)):
        t_diff = float(np.quantile(null[PRIMARY], nq))
        t_same = {f: float(np.quantile(np.asarray(families[PRIMARY][f]), sq))
                  for f in ("reencode", "resize")}
        counts = collections.Counter(
            band_of(r[f"cosine_{PRIMARY}"], t_same[r["threshold_family"]], t_diff,
                    decoded="embed_error" not in r) for r in mm)
        sensitivity.append({"same_quantile": sq, "null_quantile": nq,
                            "same_at_or_above": {f: round(v, 4) for f, v in t_same.items()},
                            "different_at_or_below": round(t_diff, 4),
                            **{b: counts[b] for b in BANDS}})
    ph = collections.defaultdict(list)
    for r in out_samples:
        if r.get("placeholder_group") is not None:
            ph[r["placeholder_group"]].append(r)
    refetch = {g: dict(collections.Counter(
        f"{r['refetch_outcome']}:{r['refetch_code']}" for r in out_samples if r["group"] == g
    ).most_common()) for g in ("mismatch", "control")}
    hash_now = {g: dict(collections.Counter(
        "matches_published" if r.get("refetch_hash_matches_published") else
        ("differs" if r["refetch_outcome"] in (pilot.SUCCESS, pilot.CHANGED) else "no_image")
        for r in out_samples if r["group"] == g)) for g in ("mismatch", "control")}

    return {
        "imghdr_rule": {"chosen": rule, "control_mean_cosine_l14": {
            k: round(v, 5) for k, v in rule_fit.items()}},
        "validation_control_vs_stored": validation,
        "control_refetch_hash_matched": len(ctrl_ok),
        "calibration_control_variants_vs_stored": calibration,
        "null": {key: {"all_pairs": quantiles(null[key]),
                       "random_single_pairing": quantiles(null_random[key]),
                       "same_host_pairs": quantiles(null_same_host[key]),
                       "same_host_type_pairs_excluding_other": quantiles(null_same_type[key]),
                       "histogram_all_pairs": histogram(null[key])}
                 for key in stored},
        "thresholds": thresholds,
        "mismatch_cosine": {key: {"all": quantiles(mm_cos[key]),
                                  "histogram": histogram(mm_cos[key])} for key in stored},
        "bands_of_mismatch": bands,
        "bands_as_share_of_all_pilot_samples": bands_of_all,
        "pilot_hash_match_or_same_band_of_all_pilot_samples": combined,
        "threshold_sensitivity_l14": sensitivity,
        "hash_matches_again": [{"uid": r["uid"], f"cosine_{PRIMARY}": r[f"cosine_{PRIMARY}"]}
                               for r in mm if r.get("refetch_hash_matches_published")],
        "by_pilot_dims": split("pilot_code"),
        "by_host_type": split("host_type"),
        "band_agreement_l14_vs_b32": {f"{a}|{b}": n for (a, b), n in sorted(agree.items())},
        "placeholders": [{"group": g, "samples": len(rows),
                          "groups_present": sorted({r["group"] for r in rows}),
                          "bands": dict(collections.Counter(r.get("band", "control")
                                                            for r in rows))}
                         for g, rows in sorted(ph.items())],
        "refetch_outcomes": refetch,
        "refetch_hash_vs_published": hash_now,
        "samples": out_samples,
    }


# ── cache ─────────────────────────────────────────────────────────────────────────────────


def save_cache(path: str, cache: dict) -> None:
    import numpy as np

    arrays, index = {}, {"stored": {}, "fetched": {}}
    for key, rows in cache["stored"].items():
        order = sorted(rows)
        arrays[f"stored_{key}"] = np.stack([rows[r] for r in order])
        index["stored"][key] = [list(r) for r in order]
    for i, by_key in cache["fetched"].items():
        for key, views in by_key.items():
            for view, vec in views.items():
                name = f"f{i}_{key}_{len(index['fetched'])}"
                arrays[name] = vec
                index["fetched"][name] = [i, key, view]
    meta = {k: v for k, v in cache.items() if k not in ("stored", "fetched")}
    meta["hosts"] = [[list(k), v] for k, v in cache["hosts"].items()]
    meta["host_types"] = [[list(k), v] for k, v in cache["host_types"].items()]
    arrays["_meta"] = np.frombuffer(json.dumps({**meta, "_index": index}).encode(), dtype=np.uint8)
    np.savez(path, **arrays)


def merge_caches(caches: list[dict]) -> dict:
    """One cache from several staged runs (controls first, then mismatches)."""
    if len(caches) == 1:
        return caches[0]
    merged = {**caches[0], "samples": [], "fetched": {}, "stored": {}, "runs": []}
    for c in caches:
        offset = len(merged["samples"])
        merged["samples"].extend(c["samples"])
        merged["fetched"].update({offset + i: v for i, v in c["fetched"].items()})
        for key, rows in c["stored"].items():
            merged["stored"].setdefault(key, {}).update(rows)
        merged["runs"].extend(c.get("runs") or [c["run"]])
    uids = [s["uid"] for s in merged["samples"]]
    if len(uids) != len(set(uids)):
        raise SystemExit("the caches overlap; each sample must come from one run")
    merged["run"] = {"stages": merged.pop("runs")}
    return merged


def load_cache(path: str) -> dict:
    import numpy as np

    z = np.load(path)
    meta = json.loads(bytes(z["_meta"]).decode())
    index = meta.pop("_index")
    stored = {key: {tuple(r): z[f"stored_{key}"][n] for n, r in enumerate(rows)}
              for key, rows in index["stored"].items()}
    fetched: dict = {}
    for name, (i, key, view) in index["fetched"].items():
        fetched.setdefault(int(i), {}).setdefault(key, {})[view] = z[name]
    meta["hosts"] = {tuple(k): v for k, v in meta["hosts"]}
    meta["host_types"] = {tuple(k): v for k, v in meta["host_types"]}
    return {**meta, "stored": stored, "fetched": fetched}


# ── run ───────────────────────────────────────────────────────────────────────────────────


def collect(args) -> dict:
    started = dt.datetime.now(dt.UTC)
    t0 = time.monotonic()
    with open(args.pilot, encoding="utf-8") as fh:
        pilot_result = json.load(fh)
    repo, revision = pilot_result["source"]["repo"], pilot_result["source"]["revision"]
    num_rows = {s["file"]: s["num_rows"] for s in pilot_result["source"]["shards"]}
    manifest = pilot_result["manifest"]
    samples = choose(pilot_result, args.control_size, args.seed, args.only)

    wanted_meta: dict[str, list[int]] = collections.defaultdict(list)
    for s in samples:
        wanted_meta[s["shard"]].append(s["row"])
    wanted_emb: dict[str, list[int]] = collections.defaultdict(list)
    for m in manifest:
        wanted_emb[m["shard"]].append(m["row"])

    print(f"reading metadata for {len(samples)} rows", file=sys.stderr, flush=True)
    meta = read_metadata(repo, revision, wanted_meta)
    t_meta = time.monotonic() - t0
    print(f"reading stored embeddings for {len(manifest)} rows", file=sys.stderr, flush=True)
    t1 = time.monotonic()
    stored, norms = read_stored_embeddings(repo, revision, wanted_emb, num_rows)
    t_emb = time.monotonic() - t1
    for s in samples:
        row = meta[(s["shard"], s["row"])]
        if row["uid"] != s["uid"]:
            raise SystemExit(f"uid mismatch at {s['shard']}:{s['row']}; wrong revision?")
        s["url"], s["sha256"] = row["url"], row["sha256"]
        s["original_width"], s["original_height"] = row["original_width"], row["original_height"]
        s["face_boxes"] = len(row["face_bboxes"] or [])

    print("loading models", file=sys.stderr, flush=True)
    embedder = Embedder()
    fetcher = pilot.Fetcher(args.per_host_delay, args.timeout)
    results: list[dict | None] = [None] * len(samples)
    order = list(range(len(samples)))
    random.Random(f"{args.seed}:embedding-fetch-order").shuffle(order)
    done, lock = [0], threading.Lock()

    def work(i):
        s = samples[i]
        calibrate = s["group"] == "control"
        results[i] = pilot.fetch_sample(fetcher, s,
                                        on_image=lambda body: embed_body(embedder, body, calibrate))
        with lock:
            done[0] += 1
            if done[0] % 10 == 0:
                import resource

                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
                print(f"  {done[0]}/{len(samples)} fetched, peak RSS {peak} MB",
                      file=sys.stderr, flush=True)

    t2 = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, order))
    t_fetch = time.monotonic() - t2

    fetched, hashes = {}, collections.defaultdict(list)
    for i, (s, r) in enumerate(zip(samples, results)):
        s["refetch_outcome"], s["refetch_code"] = r["category"], r["code"]
        got = r.get("on_image")
        if not got:
            continue
        s["refetch_hash_matches_published"] = got["sha256"] == (s["sha256"] or "").lower()
        hashes[got["sha256"]].append(i)
        if got.get("decoded_dims"):
            same = tuple(got["decoded_dims"]) == (s["original_width"], s["original_height"])
            s["refetch_dims"] = "same_dims" if same else "different_dims"
            s["decoder"] = got["decoder"]
            s["i2d_flags"] = got["i2d_flags"]
            orig_side = max(s["original_width"] or 0, s["original_height"] or 0)
            if orig_side:
                s["refetch_scale"] = round(max(got["decoded_dims"]) / orig_side, 3)
        if got.get("embed_error"):
            s["embed_error"] = got["embed_error"]
        if got.get("embeddings"):
            fetched[i] = got["embeddings"]
    group_no = 0
    for digest, idxs in sorted(hashes.items(), key=lambda kv: min(kv[1])):
        if len(idxs) > 1:
            group_no += 1
            for i in idxs:
                samples[i]["placeholder_group"] = group_no
    for s in samples:
        for k in ("url", "sha256"):
            s.pop(k, None)
    finished = dt.datetime.now(dt.UTC)
    return {
        "pilot_manifest": [{k: m[k] for k in ("uid", "shard", "row")} for m in manifest],
        "samples": samples,
        "stored": stored,
        "fetched": fetched,
        "hosts": {(m["shard"], m["row"]): m["host"] for m in manifest},
        "host_types": {(m["shard"], m["row"]): m["host_type"] for m in manifest},
        "source": {"repo": repo, "revision": revision,
                   "embedding_files": "<shard>.npz beside each parquet, members "
                                      + ", ".join(f"{k}={v}" for k, v in NPZ_MEMBERS.items()),
                   "stored_norms": {k: quantiles(v) for k, v in norms.items()}},
        "run": {"started_at": started.isoformat(timespec="seconds"),
                "finished_at": finished.isoformat(timespec="seconds"),
                "metadata_seconds": round(t_meta, 1),
                "stored_embedding_seconds": round(t_emb, 1),
                "fetch_and_embed_seconds": round(t_fetch, 1),
                "embedding_seconds": round(embedder.seconds, 1),
                "images_embedded_incl_variants": embedder.images_embedded,
                "http_requests_to_image_hosts": fetcher.request_count,
                "robots_origins": len(fetcher.robots),
                "observed_max_in_flight": fetcher.gate.max_in_flight,
                "observed_min_same_host_gap_s": (
                    None if fetcher.gate.min_same_host_gap is None
                    else round(fetcher.gate.min_same_host_gap, 3)),
                "python": platform.python_version(),
                "libraries": _versions()},
    }


def _versions() -> dict:
    out = {}
    for mod in ("torch", "open_clip", "cv2", "PIL", "numpy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001
            out[mod] = None
    return out


def build_result(cache: dict, args) -> dict:
    analysis = analyze(cache, args)
    return {
        "study": "DataComp-1B hash-mismatch embedding comparison (openclip.openness hold)",
        "generated_by": "uv run ... python -m build.hash_mismatch_embeddings",
        "pilot": str(args.pilot),
        "run": cache["run"],
        "parameters": {
            "seed": args.seed, "control_size": args.control_size,
            "control_draw": "random.Random(f'{seed}:control').sample(hash_match rows in "
                            "pilot manifest order, control_size)",
            "null_pairing": "random.Random(f'{seed}:null-pairing')",
            "bootstrap_replicates": args.bootstrap,
            "bootstrap": "recoverability_pilot.shard_bootstrap, seed f'{seed}:embedding-band-"
                         "bootstrap': resample the drawn files with replacement",
            "same_quantile": args.same_quantile, "null_quantile": args.null_quantile,
            "models": {k: f"open_clip {v}, pretrained=openai" for k, v in OPEN_CLIP_MODELS.items()},
            "primary": PRIMARY,
            "datacomp_view": "img2dataset 1.41 Resizer with skip_reencode: cv2 IMREAD_UNCHANGED, "
                             f"alpha on white, longest side <= {I2D_SIZE} (INTER_AREA, only if "
                             f"larger), JPEG q{I2D_QUALITY} if resized, matted or not JPEG by "
                             "imghdr, else the downloaded bytes unchanged; Pillow RGB; then the "
                             "OpenAI CLIP transform (bicubic 224, center crop, normalize)",
            "imghdr_rule": args.imghdr_rule,
            "variants": [{"name": n, "family": f, "spec": s} for n, f, s in VARIANTS],
            "fetch": {"concurrency": args.concurrency, "per_host_delay_s": args.per_host_delay,
                      "timeout_s": args.timeout, "max_retries": pilot.MAX_RETRIES,
                      "user_agent": pilot.USER_AGENT},
        },
        "source": cache["source"],
        **analysis,
    }


def print_report(result: dict) -> None:
    print("imghdr rule:", result["imghdr_rule"])
    for key, views in result["validation_control_vs_stored"].items():
        for view, q in views.items():
            print(f"control {key} {view}: min {q.get('min')} q05 {q.get('q05')} "
                  f"median {q.get('q50')} n {q.get('n')}")
    for key, t in result["thresholds"].items():
        print(f"thresholds {key}: same >= {t['reencode']['same_at_or_above']} (reencode), "
              f">= {t['resize']['same_at_or_above']} (resize); "
              f"different <= {t['different_at_or_below']}")
    for b, v in result["bands_of_mismatch"]["bands"].items():
        print(f"  {b:14s} {v['count']:4d}  {v['share']}  ~95% {v['share_ci95_approx']}")
    print("refetch:", result["refetch_outcomes"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pilot", default=str(DEFAULT_PILOT),
                        help="the pilot's result JSON, whose manifest names the rows")
    parser.add_argument("--seed", type=int, default=pilot.DEFAULT_SEED,
                        help="seeds the control draw, fetch order, null pairing and bootstrap")
    parser.add_argument("--control-size", type=int, default=DEFAULT_CONTROL_SIZE)
    parser.add_argument("--concurrency", type=int, default=pilot.DEFAULT_CONCURRENCY)
    parser.add_argument("--per-host-delay", type=float, default=pilot.DEFAULT_PER_HOST_DELAY)
    parser.add_argument("--timeout", type=float, default=pilot.DEFAULT_TIMEOUT)
    parser.add_argument("--same-quantile", type=float, default=0.01,
                        help="quantile of the calibrated re-encode/resize cosines that opens "
                             "the 'same' band")
    parser.add_argument("--null-quantile", type=float, default=0.99,
                        help="quantile of the null that closes the 'different' band")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--imghdr-rule", choices=("auto", *IMGHDR_RULES), default="auto",
                        help="which imghdr reading decides img2dataset's skip_reencode; auto "
                             "takes the one the control reproduces best")
    parser.add_argument("--cache", help="save embeddings and per-sample records here (npz; "
                                        "no image bytes, no URLs); keep it out of the repo")
    parser.add_argument("--only", choices=("control", "mismatch"),
                        help="fetch one group only, so the control can validate the pipeline "
                             "before any mismatch row is fetched; merge the caches with --analyze")
    parser.add_argument("--analyze", metavar="CACHE", nargs="+",
                        help="recompute the result from saved caches (merged in order); no "
                             "network, no model")
    parser.add_argument("--out", help="write the JSON result here instead of stdout")
    args = parser.parse_args(argv)
    if not 1 <= args.concurrency <= 8:
        parser.error("--concurrency must be between 1 and 8")
    if args.per_host_delay < 1.0:
        parser.error("--per-host-delay must be at least 1 second")
    if args.analyze:
        cache = merge_caches([load_cache(p) for p in args.analyze])
    else:
        cache = collect(args)
        if args.cache:
            save_cache(args.cache, cache)
    result = build_result(cache, args)
    text = json.dumps(result, indent=1) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print_report(result)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
