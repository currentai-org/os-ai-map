"""Verify a category's `scoring_recipe` reproduces its hand-authored scores.

The rubric in each category YAML was reverse-engineered from scores humans wrote.
That only stays true if something checks it. This replays the rubric's formula
against every product's recorded evidence and compares the result to the recorded
score.

Two ways this earns its place:

  * **Before layer-2 exists**, it proves the rubric is a faithful description of
    how the category was actually scored, rather than a plausible-looking
    invention. A rubric that cannot reproduce the past should not be trusted to
    write the future.
  * **After layer-2 exists**, it is the regression test for rubric edits. Changing
    a threshold should produce a small, explainable diff. If a one-line change
    moves 30 products, that is the signal to stop.

It reads the openness `components` string, which is the evidence the human
recorded. It does NOT re-research anything — this checks the formula, not the
facts.

Exit status is 1 on any mismatch, so CI can gate on it.

Usage:
    uv run python -m build.check_rubric                        # every category with a recipe
    uv run python -m build.check_rubric --category base_pretrained
    uv run python -m build.check_rubric --verbose              # show every product
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import NamedTuple

import yaml

from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants

ROOT = Path(__file__).resolve().parents[1]


def split_components(text: str) -> dict[str, str]:
    """Parse the `k:v;k:v` components string into a dict.

    Splits on `;` only at paren depth zero. Values routinely contain semicolons
    inside parentheses — 'license:Apache-2.0(OSI; see LICENSE)' — and a naive
    split silently invents dimensions out of the fragments.
    """
    parts: list[str] = []
    depth = 0
    current = ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == ";" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)

    out: dict[str, str] = {}
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def head(value: str) -> str:
    """The bare value, before any parenthetical or comma-separated detail.

    Reads a DIMENSION value — `open(downloadable on HF, gated)` -> `open`. Dimension
    vocabularies are single tokens, so cutting at the first `(` or `,` is the whole job.

    It has no part in license resolution. A license value is not a single token, and
    cutting one here resolved the product on its first half and never saw the restrictive
    one. Licenses are now recorded as parts (see `license_segments`), so the reader is
    handed a bare name and has nothing left to cut.
    """
    return re.split(r"[(,]", value)[0].strip()


def license_segments(raw: str) -> list[str]:
    """A recorded license clause cut into its `+`-joined segments, at paren depth zero.

    RECORDING-time only. This is the one place the mechanical split lives, and it runs
    when a clause is first structured into parts — never when a score is read. Reading
    resolves the parts the curator recorded, so a compound the curator meant as one
    declared name stays one part and nothing has to infer that from punctuation.

    Depth zero because annotations carry their own punctuation —
    `Sustainable-Use-License(fair-code,non-OSI: internal-use-only,no-resale/SaaS)+n8n-Enterprise-License`
    is two licenses, and a naive split on `+` or on `,` invents fragments out of the
    parenthetical.

    Only `+` separates licenses. A depth-zero comma does not: every one in the corpus is
    prose trailing a single license (`Proprietary, proprietary service`,
    `MIT(Maple-client)+AGPL-3.0(OpenSecret-platform),both-OSI`), which is why the comma is
    left inside a segment, to be split off as that part's `detail`.

    Segments come back VERBATIM, padding included, and empties are kept. `+`.join of them
    is the clause byte-for-byte, which is what lets a part carry its own `raw` and
    `recompose` still reproduce what the file said — `internlm` is the one record whose
    join is written ` + ` rather than `+`.
    """
    segments: list[str] = []
    depth = 0
    current = ""
    for char in raw:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "+" and depth == 0:
            segments.append(current)
            current = ""
        else:
            current += char
    segments.append(current)
    return segments


def split_value(raw: str) -> tuple[str, str]:
    """Split a recorded component into its bare value and its trailing detail.

    'open(downloadable on HF, gated)' -> ('open', 'downloadable on HF, gated')

    Lives beside `head` because the bare half must equal `head(raw)` exactly — that is
    what makes a structured `components` mapping score-neutral, and two modules apart is
    how the two would drift. `build/serialize_rubric.py` re-exports it.
    """
    text = (raw or "").strip()
    parts = re.split(r"[(,]", text, maxsplit=1)
    bare = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return bare, rest.rstrip(")").strip()


FREE_TEXT = "free_text"


def is_license_key(key: str) -> bool:
    """Whether a recorded `components` key carries a license.

    Five keys in the corpus do — `license`, `model-license`, `repo-license`,
    `license-terms`, `per-dataset-licenses` — and three of them are named in some ladder's
    `license_tier.reads`. The substring test covers all five and any future spelling,
    which matters because the alternative is a hardcoded list that a new key silently
    falls off, landing a license back in the unstructured shape.

    All five take the structured part list, not just the three a ladder reads. One shape
    for a recorded license wherever it appears; a reader should never have to know which
    keys a recipe happens to consult to know what shape the value is in.
    """
    return "license" in key.lower()


def render_license_part(part: dict) -> str:
    """One recorded license part back as the text it was cut from.

    `raw` wins where it is present, for the same reason it does on a dimension entry: the
    `{name, detail}` split cannot reproduce a clause whose prose runs past the closing
    paren (`Apache-2.0(OSI) for the framework`) or whose comma is a separator rather than
    a value boundary (`Proprietary, proprietary service`).
    """
    if "raw" in part:
        return part["raw"]
    detail = part.get("detail")
    return f"{part['name']}({detail})" if detail else part["name"]


def license_part(segment: str) -> dict:
    """One verbatim segment as `{name, detail?, raw?}`.

    `name` is the bare license as recorded — `code `/`model ` prefixes and `assumed-`
    included. Those are reading rules (`normalize_license` applies them), not recording
    rules, and stripping them here would turn re-derivable evidence into a conclusion.

    `raw` is the segment VERBATIM, padding included, for the segments `{name, detail}`
    cannot reproduce. Padding is part of that: `internlm` writes its join as ` + `, and
    since `recompose` joins on a bare `+` the spaces have to be carried by the segments
    either side or the record recomposes one byte off what its file says.
    """
    bare, detail = split_value(segment.strip())
    part: dict = {"name": bare}
    if detail:
        part["detail"] = detail
    if render_license_part(part) != segment:
        part["raw"] = segment
    return part


def license_entry(value: str) -> list[dict]:
    """A recorded license clause as the list of parts a ladder resolves.

    The mechanical split, applied once when the clause is structured. A curator who
    recorded a compound-looking string that is genuinely ONE declared name overrides this
    by hand, to a single-element list — which is the whole point of structuring: the
    intent lives in the data rather than being re-inferred from a `+` on every read.
    """
    return [license_part(segment) for segment in license_segments(value)]


def render_entry(entry: dict | list) -> str:
    """One structured `components` entry back as its raw clause.

    Both shapes: a license is a list of parts joined on `+`, anything else is the
    `{value, detail?, raw?}` mapping.
    """
    if isinstance(entry, list):
        return "+".join(render_license_part(part) for part in entry)
    if "raw" in entry:
        return entry["raw"]
    detail = entry.get("detail")
    return f"{entry['value']}({detail})" if detail else entry["value"]


def license_parts_of(entry: object) -> list[dict]:
    """The parts a ladder resolves, from whatever shape the entry is in.

    A list is already parts. A mapping is an unmigrated license — the gate in
    `check_components` rejects one, so this is for tools and tests rather than the corpus,
    and it structures the recomposed clause rather than growing a second splitter.
    """
    if isinstance(entry, list):
        return entry
    if isinstance(entry, dict):
        return license_entry(render_entry(entry))
    return []


def _clauses(text: str) -> list[str]:
    """Depth-0 clause split, KEEPING the keyless clauses `split_components` discards.

    `split_components` drops any clause with no colon, silently — 221 of them across 168
    files. The structured form has to put those somewhere, so the migration needs a splitter
    that hands them back.
    """
    parts: list[str] = []
    depth = 0
    current = ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == ";" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return parts


def structure(text: str) -> dict:
    """The flat `k:v;k:v` string as a mapping of key -> {value, detail?, raw?}.

    A license key takes the other shape — a LIST of `{name, detail?, raw?}` parts, one per
    `+`-joined segment. This is the only place that split runs.

    `raw` appears only when `f"{value}({detail})"` does not reproduce the clause
    byte-for-byte. 155 entries on 81 products need one, in three shapes: text after the
    closing paren ('Apache-2.0(OSI) for the framework'), a comma that is a list separator
    rather than a value/detail boundary ('rows:169,352', which every caller of split_value
    already reads as '169' today), and nested parens, where rstrip(')') removes one closer
    and leaves the inner one unbalanced.

    Keyless clauses accumulate under `free_text` in the order they appeared. They are not
    promoted to dimensions here: `dimension_value` would start answering where it answered
    '' and that can change which rung fires, which this phase is not allowed to do.
    """
    out: dict = {}
    free: list[str] = []
    for clause in _clauses(text):
        clause = clause.strip()
        if ":" not in clause:
            free.append(clause)
            continue
        key, value = clause.split(":", 1)
        key, value = key.strip(), value.strip()
        if is_license_key(key):
            out[key] = license_entry(value)
            continue
        bare, detail = split_value(value)
        entry: dict = {"value": bare}
        if detail:
            entry["detail"] = detail
        if (f"{bare}({detail})" if detail else bare) != value:
            entry["raw"] = value
        out[key] = entry
    if free:
        out[FREE_TEXT] = free
    return out


def recompose(mapping: dict) -> dict[str, str]:
    """The mapping back to the key -> raw-clause dict `split_components` produces.

    This is the join that makes the migration score-neutral: every reader keeps seeing the
    exact strings it saw before the shape changed.
    """
    return {key: render_entry(entry) for key, entry in mapping.items() if key != FREE_TEXT}


def components_of(openness: dict) -> dict[str, str]:
    """The recorded components as key -> raw clause, from either shape.

    The one function every reader calls. Both shapes are on `main` at once while the corpus
    migrates in batches, so no reader may assume either.
    """
    components = (openness or {}).get("components")
    if isinstance(components, dict):
        return recompose(components)
    return split_components(components or "")


def structured_components_of(openness: dict) -> dict:
    """The components as the structured mapping, from either shape.

    The counterpart to `components_of` for the one reader that needs structure rather than
    a clause: license resolution, which consumes recorded parts. A string-shaped record is
    structured on the way past, so there is still exactly one splitter.
    """
    components = (openness or {}).get("components")
    if isinstance(components, dict):
        return components
    return structure(components or "")


def components_string(openness: dict) -> str:
    """The flat string, for the payload and for anything that re-splits it itself.

    Prefers the verbatim `raw` sibling, which is what the file said before it was migrated;
    falls back to rejoining the mapping. The payload key stays a string so the front end and
    the rendered notebook see no change at all from this migration.
    """
    block = openness or {}
    raw = block.get("raw")
    if isinstance(raw, str) and raw:
        return raw
    components = block.get("components")
    if isinstance(components, str):
        return components
    return ";".join(f"{key}:{value}" for key, value in recompose(components or {}).items())


_RECORDED_ALIASES: dict[str, str] | None = None


def recorded_license_aliases() -> dict[str, str]:
    """Canonical license name for a name as hand-written in a `components` string.

    Read from `sources/signal_routing.yaml`, which already owns the equivalent map
    for Hub-published slugs. One declaration for both, because they are the same
    kind of fact — what a license is CALLED — and two copies would drift.

    Deliberately does not carry a tier. Which tier a license belongs to stays a
    per-category judgment, and a canonical name that appears in no category example
    still abstains. That abstention is the signal to extend the rubric.
    """
    global _RECORDED_ALIASES
    if _RECORDED_ALIASES is None:
        routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text()) or {}
        aliases = ((routing.get("dimensions") or {}).get("license") or {}).get("aliases") or {}
        _RECORDED_ALIASES = {
            str(slug).strip().lower(): str(name).strip()
            for slug, name in (aliases.get("recorded") or {}).items()
        }
    return _RECORDED_ALIASES


def normalize_license(raw: str) -> str:
    """Reduce ONE recorded license NAME to the spelling the tier examples use.

    Runs on a part's `name`, which the record already carries bare — the annotation is
    `detail` and no reader has to cut it off. Two mechanical steps, both spelled out in
    the recipe's `normalization` list:
      * a `code ` or `model ` scope prefix is dropped, because the scope is which
        artifact the license covers, not a different license;
      * `assumed-Modified-MIT` — the `assumed-` prefix marks confidence, not a
        different license.

    Then the recorded-name alias, which resolves spellings of one license to one
    name. Applied last, so it sees the value after the mechanical steps rather
    than having to enumerate every prefixed variant.

    It does NOT truncate. It used to open with `head`, which cut at the first `(` or `,`;
    on a structured name there is nothing to cut, and a name that still contains one is a
    recording error that should abstain rather than resolve on its first token.

    The `code X + model Y` rule that used to live here — the MODEL license governs —
    is now a consequence rather than a special case: both parts resolve and the most
    restrictive wins, and a weights license is the restrictive half in every recorded
    instance. Where it would not be, the old rule was wrong anyway: a permissive
    weights license does not buy back a restrictive code license.

    Purely mechanical. Anything needing judgment is left alone to be flagged.
    """
    value = re.sub(r"(?i)^\s*(code|model)\s+", "", raw.strip()).strip()
    value = re.sub(r"(?i)^assumed-", "", value).strip()
    return recorded_license_aliases().get(value.lower(), value)


def tier_rank(tiers: dict) -> dict[str, int]:
    """Tier name -> position in the recipe's declaration order.

    Declaration order IS restrictiveness order, ascending — every ladder declares
    `ordered_by: restrictiveness_ascending` and `check_recipe` requires it. A name the
    recipe does not declare ranks last, so an unrecognized tier can never be treated as
    the more permissive of a pair.
    """
    return {name: rank for rank, name in enumerate(tiers)}


def _tier_of(needle: str, tiers: dict) -> str | None:
    """The tier whose examples contain `needle`, already normalized and lowercased."""
    for name, spec in tiers.items():
        for example in (spec or {}).get("examples") or []:
            if example.lower() == needle:
                return name
    # Proprietary is the one tier defined by meaning rather than an example list.
    if needle in ("proprietary", "closed", "none"):
        return "proprietary"
    return None


def license_tier(parts: list[dict], recipe: dict) -> str | None:
    """Map the recorded license parts onto a tier from the recipe's own examples.

    Every part is resolved and the most restrictive governs. That is what
    `docs/reference/identity.md` already says openness does across a release's SKUs — "a
    product is as open as the most restrictive license you must accept to use it" — and a
    product recording two licenses is that same fact written on one axis.

    It takes PARTS, not a string, and that is the whole design. There is no split here and
    no whole-value pre-check: the curator recorded how many licenses there are, so a
    compound-looking phrase that is really one declared name — `follows mC4 + OSCAR-2301
    terms`, where neither operand is a license — arrives as a single part and resolves as
    the one thing it is. Inferring that from punctuation is what needed the pre-check, and
    what made this rubric expensive to state twice: `build/serialize_rubric.py` published
    the same values through a splitter that cut at the first `(` and scored two products
    differently from the repo.

    One thing this deliberately does not do: skip a part it cannot map. Every part must
    resolve or the whole value abstains, because an unmapped part can only ever be MORE
    restrictive than the tier the mapped parts reached — ignoring it is exactly how
    partial coverage overstates openness.

    Returns None when the license is unmapped, which is a finding rather than an
    error — an unmapped license means the rubric has not yet been told how to
    treat it, and `mixed` means the evidence never recorded the outcome.
    """
    tiers = ((recipe.get("openness") or {}).get("license_tier") or {}).get("values") or {}
    if not tiers:
        return None

    resolved = [tier for _part, tier in resolve_license_parts(parts, recipe)]
    if not resolved or any(tier is None for tier in resolved):
        return None
    rank = tier_rank(tiers)
    return max(resolved, key=lambda name: rank.get(name, len(tiers)))


def resolve_license_parts(parts: list[dict], recipe: dict) -> list[tuple[dict, str | None]]:
    """Each recorded license part paired with the tier it maps to, or None if unmapped.

    The per-part decomposition `license_tier` reduces to a single governing tier — the
    scoring trace publishes it whole so the chain `result -> matched rule -> normalized
    fact` can name which license part carried the cap. It is the SAME resolution
    `license_tier` performs (normalize the recorded name, look it up in the recipe's own
    tier examples); factoring it here keeps one implementation, so the trace cannot resolve
    a part differently from the score. An empty `tiers` (a ladder with no `license_tier`,
    e.g. hardware) yields no pairs.
    """
    tiers = ((recipe.get("openness") or {}).get("license_tier") or {}).get("values") or {}
    if not tiers:
        return []
    return [(part, _tier_of(normalize_license(part.get("name", "")).lower(), tiers)) for part in parts]


def dimension_spec(dimension: str, recipe: dict) -> dict:
    return (((recipe.get("openness") or {}).get("dimensions") or {}).get(dimension)) or {}


def normalize_dimension_value(value: str, spec: dict) -> str:
    """A recorded spelling translated to the declared value it means.

    `reads:` widens which KEY answers a dimension; this widens which VALUE does. The two
    are separate because `reads:` selects a key and takes its value verbatim, so a synonym
    key whose vocabulary differs - `self-host: none` for `core_gated: gated` - still reads
    as unanswered without a translation step. `dataset.yaml`'s `availability` note is the
    same observation from the other side: there, every spelling was declared as its own
    value and the rules were written to test only one polarity, which works because the
    other polarity falls through. `core_gated` has a rung on both sides, so falling through
    is not available and the spellings have to collapse onto the two declared values.

    An unmapped spelling is returned unchanged, which puts it outside the enum and leaves
    the dimension unanswered. That is deliberate: the formula declares no `otherwise`, so
    abstaining is what happens to evidence the ladder does not understand, and guessing a
    polarity from an unrecognized word is exactly the failure that would not surface.
    """
    return (spec.get("value_aliases") or {}).get(value, value)


def resolve_dimension(components: dict[str, str], dimension: str, recipe: dict) -> str | None:
    """Which recorded key answers a dimension, or None if nothing does.

    A dimension's `reads` list names the `components` keys that carry its answer,
    in preference order. It exists because the same question is recorded under
    different keys in different categories: for a base model the data question is
    `data`, the pretraining corpus, while for a fine-tune the corpus belongs to
    somebody else's model and the honest answer lives in `post-training-data`.

    Prefers the first key whose value is in the declared enum, rather than the
    first key present. A product recording both `data:closed` and
    `post-training-data:open` is answering two different questions, and taking
    whichever appeared first in the string would pick between them by accident.

    Falls back to the first present key when none is in the enum, so an
    unrecognized value surfaces in the mismatch message instead of silently
    reading as absent.

    Returns the KEY rather than the value, because callers that write evidence out
    need the parenthetical detail attached to that key too, and re-deriving the
    preference in a second place is how the two would drift.
    """
    spec = dimension_spec(dimension, recipe)
    keys = spec.get("reads") or [dimension]
    allowed = set(spec.get("values") or ())
    present = [key for key in keys if key in components]
    for key in present:
        if normalize_dimension_value(head(components[key]), spec) in allowed:
            return key
    return present[0] if present else None


def dimension_value(components: dict[str, str], dimension: str, recipe: dict) -> str:
    """The bare value the formula reads for a dimension, or '' if unanswered.

    Alias-translated, so the formula only ever tests the declared vocabulary.
    """
    key = resolve_dimension(components, dimension, recipe)
    if key is None:
        return ""
    return normalize_dimension_value(head(components[key]), dimension_spec(dimension, recipe))


def dimension_read_map(recipe: dict) -> dict[str, str]:
    """Recorded key -> the dimension it can answer.

    A key named in some dimension's `reads` is declared vocabulary even though it is
    not itself a dimension name, so it must not be reported as vocabulary drift.
    """
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    return {
        key: name
        for name, spec in declared.items()
        for key in ((spec or {}).get("reads") or [name])
    }


def license_read_keys(recipe: dict) -> list[str]:
    """Recorded keys that may carry the license the tier lookup consumes."""
    return (((recipe.get("openness") or {}).get("license_tier") or {}).get("reads")) or ["license"]


def matches(rule_when: dict, facts: dict) -> bool:
    return all(facts.get(key) == value for key, value in rule_when.items())


def apply_formula(recipe: dict, facts: dict) -> tuple[int, str] | None:
    """Walk the ordered rules, first match wins.

    `facts` is a COMPLETE fact set, `license_tier` included where the ladder has one.
    Callers that may not be able to resolve a tier want `walk_formula`, which decides
    whether the tier is needed at all before insisting on it.
    """
    result, _ = walk_formula(recipe, facts, tier=facts.get("license_tier"))
    return result


class RuleStep(NamedTuple):
    """One rung of the ordered-rule walk, as the walk actually evaluated it.

    The scoring trace (`build/axis_scoring_trace.py`) needs the walk decomposed rung by
    rung — which rules were skipped, which fired, which fell through on a tier — and that
    decomposition must come from the SAME walk that produces the score, or it is a second
    scoring implementation (ADR-001). So the walk records its steps here and
    `walk_formula` is a thin projection of it, rather than the trace re-deriving the walk.

    `outcome` is one of:
      * ``fired`` — this rung produced the result; first match wins, so the walk stops here;
      * ``skipped`` — the rung's non-tier conditions did not all match `facts`;
      * ``fell_through_tier`` — the non-tier conditions matched but the rung's required
        `license_tier` did not equal the resolved tier, so the walk continues past it;
      * ``blocked_on_tier`` — the non-tier conditions matched and the rung tests a
        `license_tier`, but no tier resolved, so the walk cannot continue (an unmapped
        license may sit on this restrictive rung; falling through would overstate openness).
    """

    rule_index: int
    kind: str  # "when" | "otherwise"
    conditions: dict  # the rung's non-tier `when` conditions ({} for `otherwise`)
    tests_tier: bool
    wanted_tier: str | None
    non_tier_matched: bool
    outcome: str  # fired | skipped | fell_through_tier | blocked_on_tier
    result: tuple[int, str] | None


def walk_formula(
    recipe: dict, facts: dict, tier: str | None
) -> tuple[tuple[int, str] | None, bool]:
    """First match wins, consulting `tier` only where a rung actually tests it.

    Returns `(result, blocked)` — a thin projection of `walk_formula_trace`, which owns the
    walk. `blocked` is True when a rung whose other conditions all match tests
    `license_tier` and no tier resolved — the walk cannot continue past a rung it cannot
    evaluate, because first-match-wins means a later rung only fires if this one did not.

    Why the tier is not simply resolved up front: it used to be, and a product whose
    recorded license names nothing the tier lookup recognizes abstained before the formula
    ran, even when the rung that decides it never asks about a license. `apify` records
    `mixed(platform closed, SDK open)` and `source:partial`; the software ladder settles
    `source:partial` at 2/source_available on the source dimension alone, and the license
    it could not map was never going to be consulted. Four more products across three
    categories were deferred for the same non-reason.

    The narrower rule — resolve a tier only when a rung needs one — keeps the property
    that made the eager version defensible. An unmapped license still blocks any rung that
    turns on it, so nothing is scored by ignoring a license the ladder could not read.
    That distinction is the whole fix: `dify` records `source:public`, which reaches the
    `competition_restricted` rung, so its unmapped vendor license still blocks it and it
    stays deferred.

    Skipping an unevaluable rung and carrying on would be the other failure this repo
    already names: partial coverage overstating openness. A product whose license may sit
    on the restrictive rung would fall through to a more permissive one below it.
    """
    result, blocked, _steps = walk_formula_trace(recipe, facts, tier)
    return result, blocked


def walk_formula_trace(
    recipe: dict, facts: dict, tier: str | None
) -> tuple[tuple[int, str] | None, bool, list[RuleStep]]:
    """The ordered-rule walk, returning `(result, blocked, steps)`.

    The single owner of first-match-wins. `steps` records every rung the walk actually
    touched, in order, up to and including the one that fired or blocked — never the rungs
    after a match, because first-match-wins never reaches them and recording them would
    invent an evaluation that did not happen. When nothing fires and there is no
    `otherwise`, every rung is touched and the walk returns `(None, False, steps)`; the
    ladder is telling us it does not decide this product.

    `result` and `blocked` are exactly what `walk_formula` returned before this function
    existed — that method now projects this one — so no caller or golden changes.
    """
    steps: list[RuleStep] = []
    for index, rule in enumerate((recipe.get("openness") or {}).get("formula") or []):
        if "otherwise" in rule:
            spec = rule["otherwise"]
            result = (spec["score"], spec["class"])
            steps.append(RuleStep(index, "otherwise", {}, False, None, True, "fired", result))
            return result, False, steps
        when = rule.get("when") or {}
        wanted = when.get("license_tier")
        tests_tier = wanted is not None
        non_tier = {k: v for k, v in when.items() if k != "license_tier"}
        if not matches(non_tier, facts):
            steps.append(RuleStep(index, "when", non_tier, tests_tier, wanted, False, "skipped", None))
            continue
        if wanted is None:
            spec = rule["then"]
            result = (spec["score"], spec["class"])
            steps.append(RuleStep(index, "when", non_tier, False, None, True, "fired", result))
            return result, False, steps
        if tier is None:
            steps.append(RuleStep(index, "when", non_tier, True, wanted, True, "blocked_on_tier", None))
            return None, True, steps
        if tier == wanted:
            spec = rule["then"]
            result = (spec["score"], spec["class"])
            steps.append(RuleStep(index, "when", non_tier, True, wanted, True, "fired", result))
            return result, False, steps
        steps.append(RuleStep(index, "when", non_tier, True, wanted, True, "fell_through_tier", None))
    return None, False, steps


class Outcome(NamedTuple):
    """What a ladder makes of one product's recorded evidence.

    One resolution path for the three modules that replay a ladder — `check_rubric`,
    `check_recipe`'s stale-deferral test and `check_parity`. They each had their own copy
    of "resolve the tier, build the facts, walk the formula", and the copies are exactly
    what let the tier gate live in one of them and not the others.
    """

    result: tuple[int, str] | None
    facts: dict[str, str]
    has_tiers: bool
    raw_license: str
    tier: str | None
    blocked_on_tier: bool


def score_openness(recipe: dict, openness: dict) -> Outcome:
    """Replay one ladder against one product's recorded openness axis.

    Takes the axis BLOCK rather than the recomposed clause dict it used to take, because
    the license is resolved from its recorded parts and a clause dict has thrown that
    structure away. Every caller had the block in hand already.

    The tier is resolved eagerly for REPORTING — `tier is None` on a product that still
    scores is what `check_recipe` counts and names — but it is only ever REQUIRED by
    `walk_formula`, and only for a rung that tests it.

    A ladder need not turn on a source license at all. Hardware openness is scored on
    design, toolchain and availability: `sources/rubrics/hardware.yaml` declares no
    `license_tier` and none of the 20 edge products records a license, so `has_tiers` is
    False and no tier is looked for. `check_recipe`'s unreachable-rule assertion rejects a
    `license_tier` condition with no declared tiers, so such a ladder cannot have a rung
    that needs one.
    """
    resolved = _resolve_openness(recipe, openness)
    result, blocked, _steps = walk_formula_trace(recipe, resolved.facts, resolved.tier)
    return Outcome(
        result, resolved.facts, resolved.has_tiers, resolved.raw_license, resolved.tier, blocked
    )


class _ResolvedOpenness(NamedTuple):
    """The evidence one ladder resolves from a product's recorded openness axis, before the
    walk. The single resolution `score_openness` and `trace_openness` share, so the trace
    can never resolve a fact or a license differently from the score."""

    components: dict[str, str]
    has_tiers: bool
    license_key: str | None
    raw_license: str
    tier: str | None
    facts: dict[str, str]


def _resolve_openness(recipe: dict, openness: dict) -> _ResolvedOpenness:
    """Resolve the license tier and the declared-dimension facts, shared by both readers."""
    components = components_of(openness)
    has_tiers = bool(((recipe.get("openness") or {}).get("license_tier") or {}).get("values"))
    license_key = None
    raw_license = ""
    tier = None
    if has_tiers:
        # The key is chosen once and both the clause and the parts come from it. Choosing
        # twice is how the reported license and the resolved one could name different keys.
        license_key = next((key for key in license_read_keys(recipe) if components.get(key)), None)
        if license_key is not None:
            raw_license = components[license_key]
            tier = license_tier(
                license_parts_of(structured_components_of(openness).get(license_key)), recipe
            )

    # Facts come from the dimensions the recipe DECLARES, not a fixed list. The model
    # categories ask about weights/data/code; software categories ask whether the source is
    # public, whether the real thing self-hosts, and whether the core is feature-gated.
    # Hardcoding the model's four here is what would have forced a checker change per
    # product type.
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    facts = {name: dimension_value(components, name, recipe) for name in declared}
    return _ResolvedOpenness(components, has_tiers, license_key, raw_license, tier, facts)


class OpennessTrace(NamedTuple):
    """A product's openness evaluation decomposed into fact / rule-walk / result.

    The scoring trace (`build/axis_scoring_trace.py`) reads this instead of `Outcome`
    because the three trace tables need what `Outcome` folds away: the recorded key each
    fact was read under, the per-part license-tier resolution, and the ordered rung walk
    with the index of the rung that fired. Every field comes from the same resolution and
    the same walk that `score_openness` runs, so the trace and the score cannot diverge.

    `matched_index` is the `rule_index` of the rung that fired, or None when the ladder
    reached no deciding rung (an undecided product) or blocked on an unmapped tier.
    `license_parts` pairs each recorded license part with the tier it maps to (empty for a
    tier-free ladder or an unrecorded license). `fact_keys` maps each declared dimension to
    the recorded `components` key that answered it, or None where nothing did.
    """

    result: tuple[int, str] | None
    facts: dict[str, str]
    fact_keys: dict[str, str | None]
    has_tiers: bool
    license_key: str | None
    raw_license: str
    tier: str | None
    license_parts: list[tuple[dict, str | None]]
    blocked_on_tier: bool
    steps: list[RuleStep]
    matched_index: int | None


def trace_openness(recipe: dict, openness: dict) -> OpennessTrace:
    """`score_openness` with the walk and the license decomposition kept, for the trace.

    Runs the identical resolution and walk as `score_openness`; it only retains the
    intermediate structure the score discards. It is not a second scoring path — the
    `result` it returns is `walk_formula_trace`'s, the same one `score_openness` reports.
    """
    resolved = _resolve_openness(recipe, openness)
    result, blocked, steps = walk_formula_trace(recipe, resolved.facts, resolved.tier)
    fact_keys = {
        name: resolve_dimension(resolved.components, name, recipe) for name in resolved.facts
    }
    license_parts: list[tuple[dict, str | None]] = []
    if resolved.has_tiers and resolved.license_key is not None:
        parts = license_parts_of(structured_components_of(openness).get(resolved.license_key))
        license_parts = resolve_license_parts(parts, recipe)
    matched_index = next((s.rule_index for s in steps if s.outcome == "fired"), None)
    return OpennessTrace(
        result=result,
        facts=resolved.facts,
        fact_keys=fact_keys,
        has_tiers=resolved.has_tiers,
        license_key=resolved.license_key,
        raw_license=resolved.raw_license,
        tier=resolved.tier,
        license_parts=license_parts,
        blocked_on_tier=blocked,
        steps=steps,
        matched_index=matched_index,
    )


class CategoryReport(NamedTuple):
    """What one category's replay produced.

    `tierless` is the set the tier-gate fix made possible: products that SCORE while their
    recorded license maps to no tier, because no rung the walk reached asked for one. They
    are correct scores and they must stay countable, because a score whose license nobody
    could read is a score standing on less evidence than its neighbours. What remains here
    is licenses nobody has NAMED — `apify`'s `mixed(platform closed, SDK open)`, `confer`'s
    `none-declared`, three products recording no license key at all. That is a curation
    prompt, not a rubric gap: there is nothing to map until someone reads the card.

    It is deliberately not the same set as the products blocked ON a tier. Those reach a
    rung that asks, and they stay deferred until their license joins a tier — which is what
    happened to the five vendor licenses (`Modular-Community-License`,
    `Dify-Open-Source-License`, `Open-WebUI-License`, `LobeHub-Community-License`,
    `PolyForm-Shield`) that were held for exactly that reason. All five landed on
    `competition_restricted` and none of the five products moved a score, because the rung
    they reach produces the 2/source_available they already recorded.
    """

    reproduced: int
    total: int
    problems: list[str]
    deferred: list[str]
    tierless: list[str]


def check_category(slug: str, verbose: bool) -> CategoryReport:
    """Return (reproduced, total, problems, deferred, tierless)."""
    category = yaml.safe_load((ROOT / "sources" / "categories" / f"{slug}.yaml").read_text())
    # `extends: software` pulls in one shared ladder for every product; `extends: {model:
    # ..., software: ...}` pulls in one per product type, as `safeguards` does. Resolution
    # errors are returned as problems rather than raising, so one broken category cannot
    # stop the others being checked - and cannot pass silently either.
    variants, recipe_errors = resolve_recipe_variants(category, load_shared(ROOT))
    if recipe_errors:
        return CategoryReport(0, 0, [f"{slug}: {e}" for e in recipe_errors], [], [])
    if not variants:
        return CategoryReport(0, 0, [], [], [])
    product_types = load_product_types(ROOT)
    # Deferrals are a property of the category's declaration, not of any one ladder:
    # products the category has declared the rubric does not yet decide, each with a
    # reason. Deferring is not the same as passing: these are excluded from the
    # reproduction count rather than counted as reproduced, and printed every run so
    # the exclusion cannot go quiet. A rubric that reproduces 45 of 45 while deferring
    # the one product that contradicts it has proved nothing.
    deferrals = (category.get("scoring_recipe") or {}).get("deferred") or {}

    reproduced = 0
    total = 0
    problems: list[str] = []
    deferred: list[str] = []
    tierless: list[str] = []

    for product in category.get("products") or []:
        path = ROOT / "sources" / "scores" / f"{product}.yaml"
        if not path.exists():
            continue
        if product in deferrals:
            because = (deferrals[product] or {}).get("because", "no reason recorded")
            deferred.append(f"{product}: {' '.join(str(because).split())}")
            continue
        recipe, why = recipe_for(variants, product_types.get(product, ""))
        if recipe is None:
            problems.append(f"{product}: {why}")
            continue
        scores = yaml.safe_load(path.read_text())
        openness = scores.get("openness") or {}
        components = components_of(openness)
        total += 1

        # One resolution path, shared with check_recipe and check_parity. The tier is
        # consulted only by a rung that tests it, so a license the lookup cannot read stops
        # only the products a license was going to decide. `blocked_on_tier` is that stop,
        # and it stays a hard failure: the ladder reached a rung it could not evaluate.
        #
        # A ladder need not turn on a source license at all. Hardware openness is scored on
        # design, toolchain and availability - `sources/rubrics/hardware.yaml` declares no
        # `license_tier`, and none of the 20 edge products records a license, so `has_tiers`
        # is False and no tier is looked for at all.
        #
        # `serialize_rubric` already tolerated a tier-free ladder - `license_tiers()` emits
        # zero rows and only requires `ordered_by` above one tier. Both allowances change
        # shared resolution semantics, so the warehouse mirror in
        # `currentai.scores.openness_computed` needs them too.
        outcome = score_openness(recipe, openness)
        facts, tier, has_tiers = outcome.facts, outcome.tier, outcome.has_tiers
        if outcome.blocked_on_tier:
            problems.append(
                f"{product}: license {outcome.raw_license!r} maps to no tier, and a rung "
                f"the ladder reached tests one "
                f"(recorded {openness.get('score')} {openness.get('class')})"
            )
            continue

        got = outcome.result
        expected = (openness.get("score"), openness.get("class"))

        # No rule matched and the recipe declares no `otherwise`, so it is telling us it
        # does not decide this product. Abstain rather than score it.
        #
        # This is how a category opts out of guessing. The model recipes end in an
        # `otherwise` and so can never reach here; the software recipes deliberately do
        # not, because their discriminating evidence - whether the published source is the
        # whole product - is recorded for only about two thirds of products, and the
        # `otherwise` rule would quietly record the rest at whatever the last tier was.
        #
        # The facts go in the reason, so the two causes stay distinguishable: a blank
        # value means nobody recorded that dimension, while a full set of values means the
        # ladder itself has a gap. Abstentions print every run and are excluded from the
        # reproduced count, so neither can go quiet.
        if got is None:
            shown = " ".join(f"{name}={value!r}" for name, value in facts.items())
            if has_tiers:
                shown = f"{shown} tier={tier}"
            deferred.append(
                f"{product}: recipe does not decide it [{shown}] "
                f"(recorded {openness.get('score')} {openness.get('class')})"
            )
            total -= 1
            continue

        # Scored, but on a license nobody could place. Correct - no rung the walk reached
        # asked for one - and worth naming every run rather than letting it read as an
        # ordinary score.
        if has_tiers and tier is None:
            tierless.append(
                f"{product}: {got[0]}/{got[1]} on license {outcome.raw_license!r}, "
                f"which maps to no tier"
            )

        if got == expected:
            reproduced += 1
            if verbose:
                print(f"  ok    {product:<24} {expected[0]} {expected[1]}")
        else:
            shown = " ".join(f"{name}={value!r}" for name, value in facts.items())
            if has_tiers:
                shown = f"{shown} tier={tier}"
            problems.append(
                f"{product}: rubric says {got}, scores say {expected} [{shown}]"
            )

    unknown = sorted(set(deferrals) - set(category.get("products") or []))
    for product in unknown:
        problems.append(f"{product}: deferred by the recipe but not a product of this category")

    return CategoryReport(reproduced, total, problems, deferred, tierless)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    slugs = (
        [args.category]
        if args.category
        else sorted(p.stem for p in (ROOT / "sources" / "categories").glob("*.yaml"))
    )

    failed = False
    checked_any = False
    for slug in slugs:
        reproduced, total, problems, deferred, tierless = check_category(slug, args.verbose)
        if total == 0 and not deferred and not problems:
            continue
        checked_any = True
        status = "OK" if not problems else "FAIL"
        suffix = f", {len(deferred)} deferred" if deferred else ""
        suffix += f", {len(tierless)} scored with no tier" if tierless else ""
        print(f"{slug}: {reproduced}/{total} reproduced{suffix}  [{status}]")
        for problem in problems:
            print(f"  ! {problem}")
        for entry in deferred:
            print(f"  ~ deferred  {entry}")
        # Reported, never gating. A gate that fails on the day it lands gets switched off,
        # and every one of these is a correct score - the finding is that the score rests on
        # a license the ladder could not read, which is a curation prompt rather than a
        # defect in the ladder. It prints unconditionally for the reason the deferrals do:
        # an exclusion nobody sees is an exclusion nobody acts on.
        for entry in tierless:
            print(f"  ~ no tier   {entry}")
        if problems:
            failed = True

    if not checked_any:
        print("no category defines a scoring_recipe yet")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
