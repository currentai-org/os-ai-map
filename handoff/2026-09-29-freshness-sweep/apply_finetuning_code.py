"""Deterministic applier for the search_retrieval refresh packets.

Input: the workflow result JSON (packets, evidence verdicts, prose verdicts) and a decisions
file naming how each escalated axis is settled. Writes only sources/{scores,products}/<slug>.yaml
for packet products and sources/verification_queue.yaml, through build.components.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import yaml

from build import components

ROOT = Path("/home/user/os-ai-map")
TODAY = "2026-09-28"


def load(path):
    return json.loads(Path(path).read_text())


def corrections_by(verdicts):
    out = {}
    for v in verdicts:
        out.setdefault((v["slug"], v["axis"]), []).append(v)
    return out


def prose_by(verdicts):
    return {(v["slug"], v["field"]): v for v in verdicts}


def prose_text(prose, slug, field, packet_text):
    """Replacement from the prose audit; packet text only where the audit judged it ok."""
    v = prose.get((slug, field))
    if v is None:
        return ""
    if v["verdict"] in ("suspect", "failed"):
        return v["replacement"].strip() or ("CLEAR" if v["verdict"] == "failed" and field == "comments" else "")
    return packet_text.strip()


def apply_corrections(src_list, corrs, axis="openness"):
    """Apply auditor corrections keyed by url. Returns (list, dropped_urls)."""
    dropped = set()
    for c in corrs:
        for s in src_list:
            if s.get("url") != c["source_url"]:
                continue
            if c["field"] == "drop":
                dropped.add(c["source_url"])
            elif c["field"] == "http_status":
                s["http_status"] = int(c["value"])
            elif c["field"] == "establishes":
                if axis != "openness":
                    continue
                s["establishes"] = [x.strip() for x in c["value"].split(",") if x.strip()]
            else:
                s[c["field"]] = c["value"]
    return [s for s in src_list if s.get("url") not in dropped]


def build_sources(current, packet_sources, drop_idx, axis):
    new = copy.deepcopy(current or [])
    appended = []
    for ps in packet_sources:
        if not ps.get("content_sha256") or len(ps["content_sha256"]) != 64:
            continue  # undigested sources are never written as fresh evidence
        entry = {
            "url": ps["url"],
            "shows": ps["shows"],
            "accessed": TODAY,
            "http_status": ps["http_status"],
            "content_sha256": ps["content_sha256"],
        }
        if axis == "openness" and ps.get("establishes"):
            entry["establishes"] = ps["establishes"]
        i = ps["replaces_index"]
        if 0 <= i < len(new):
            kept = {k: v for k, v in new[i].items() if k not in entry and k not in ("establishes",)}
            if axis == "openness" and not ps.get("establishes") and "establishes" in new[i]:
                entry["establishes"] = new[i]["establishes"]
            new[i] = {**entry, **kept}
        else:
            appended.append(entry)
    new = [s for j, s in enumerate(new) if j not in set(drop_idx)] + appended
    return new


def main(result_path, decisions_path, mode):
    res = load(result_path)
    decisions = load(decisions_path)
    ev = corrections_by(res["evidence"])
    prose = prose_by(res["prose"])
    queue_path = ROOT / "sources/verification_queue.yaml"
    queue = yaml.safe_load(queue_path.read_text())
    held = {}
    report = []
    for pk in res["packets"]:
        slug = pk["slug"]
        spath = ROOT / f"sources/scores/{slug}.yaml"
        ppath = ROOT / f"sources/products/{slug}.yaml"
        text = spath.read_text()
        doc = yaml.safe_load(text)
        for ax in pk["axes"]:
            axis = ax["axis"]
            verdicts = ev.get((slug, axis), [])
            failed = any(v["verdict"] == "failed" for v in verdicts)
            decision = decisions.get(f"{slug}.{axis}", {})
            hold = ax["outcome"] == "hold" or failed or decision.get("hold")
            if ax["outcome"] == "moved" and not decision.get("set"):
                report.append(f"{slug}.{axis}: MOVED, no decision -> held")
                hold = True
            if hold:
                reason = decision.get("reason") or ax["hold_reason"] or "; ".join(
                    p for v in verdicts for p in v["problems"]) or ax["escalation"]
                if doc[axis].get("last_verified"):
                    text = components.drop_field(text, axis, "last_verified")
                entries = [e for e in held.get(slug, []) if e.get("axis") != axis]
                entries.append({"axis": axis, "since": TODAY, "reason": reason.strip()})
                held[slug] = entries
                report.append(f"{slug}.{axis}: held - {reason.strip()[:140]}")
                continue
            srcs = build_sources(doc[axis].get("sources"), ax["sources"], ax["drop_source_indices"], axis)
            corrs = [c for v in verdicts for c in v["corrections"]]
            srcs = apply_corrections(srcs, corrs, axis)
            text = components.set_field(text, srcs, axis=axis, key="sources")
            note = prose_text(prose, slug, f"{axis}.note", ax["note"]) if (slug, f"{axis}.note") in prose else ax["note"]
            for field, value in (decision.get("set") or {}).items():
                text = components.put_field(text, value, axis=axis, key=field)
            if note.strip() and "note" not in (decision.get("set") or {}):
                text = components.set_field(text, note.strip(), axis=axis, key="note")
            text = components.put_field(text, TODAY, axis=axis, key="last_verified")
            report.append(f"{slug}.{axis}: dated {TODAY} ({len(srcs)} sources, {len(corrs)} corrections)")
        ptext = ppath.read_text()
        desc = prose_text(prose, slug, "description", pk["description"])
        if desc.strip():
            ptext = components.set_document_field(ptext, "description", desc.strip())
        com = prose_text(prose, slug, "comments", pk["comments"])
        if com.strip() == "CLEAR":
            if "comments" in yaml.safe_load(ptext):
                ptext = components.drop_document_field(ptext, "comments")
        elif com.strip():
            ptext = components.set_document_field(ptext, "comments", com.strip())
        if mode == "write":
            spath.write_text(text)
            ppath.write_text(ptext)
    done = {(pk["slug"], ax["axis"]) for pk in res["packets"] for ax in pk["axes"]}
    for key, decision in decisions.items():
        slug, axis = key.rsplit(".", 1)
        if not decision.get("hold") or (slug, axis) in done:
            continue
        spath = ROOT / f"sources/scores/{slug}.yaml"
        text = spath.read_text()
        if yaml.safe_load(text)[axis].get("last_verified"):
            text = components.drop_field(text, axis, "last_verified")
        entries = [e for e in held.get(slug, []) if e.get("axis") != axis]
        entries.append({"axis": axis, "since": TODAY, "reason": decision["reason"]})
        held[slug] = entries
        report.append(f"{slug}.{axis}: held (no packet) - {decision['reason'][:120]}")
        if mode == "write":
            spath.write_text(text)
    if mode == "write":
        body = queue_path.read_text()
        head = body[: body.index("held:")]
        existing = queue.get("held") or {}
        merged = {s: dict(axes) for s, axes in existing.items() if isinstance(axes, dict)}
        for slug, entries in held.items():
            if isinstance(entries, list):
                for e in entries:
                    merged.setdefault(slug, {})[e["axis"]] = {"since": e["since"], "because": e["reason"]}

        class D(yaml.SafeDumper):
            pass

        D.add_representer(str, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", v, style=">" if len(v) > 80 else None))
        queue_path.write_text(head + yaml.dump({"held": merged}, Dumper=D, sort_keys=True, allow_unicode=True, width=96))
    print("\n".join(report))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "dry")
