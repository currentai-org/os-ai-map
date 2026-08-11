"""The only supported way to edit an `openness.components` field in place.

## Why a module rather than a `re.sub`

`components` is a structured mapping — `key -> {value, detail?, raw?}`, plus a reserved
`free_text` list for keyless clauses — and PyYAML renders it as a nested block, so it spans
multiple lines in every one of the 472 score files. Before phase 1a migrated the corpus, this
field was a single `k:v;k:v` string that PyYAML folded across lines whenever it ran past the
configured width, and folding was the hazard the obvious edit did not see:

    re.sub(r"^  components: (.*)$", ..., text, flags=re.M)

matched only the FIRST line of a folded scalar and left the continuation lines standing. The
result parsed cleanly and was wrong: the old tail was spliced onto the new value, usually
mid-key, producing something like `...;core-gated:gatedn(OSI);source:public`. Nothing
downstream complained, because the string was only ever split on `;` and `:` and those
fragments were still shaped like keys. It corrupted silently, which is the one failure mode
worth building a mechanism against.

The structured mapping does not fold the same way — every record's value is already
multi-line by construction — but the discipline carries over unchanged, because the general
hazard is the same: any multi-line YAML value invites a line-oriented substitution, and the
right fix is to stop reasoning about lines at all.

Rather than get the regex right, this module does not use one:

  * locate the field by INDENT, taking every following more-indented line as part of it;
  * re-emit the value with PyYAML, so quoting and block-style formatting are the emitter's
    problem;
  * re-parse the whole file and assert the new value is what was asked for AND that every
    other field is unchanged, then assert the bytes outside the span never moved.

Nothing is written unless both assertions hold. A file this cannot handle raises rather
than producing a plausible-looking edit.

## Why the assertion is the point

A single-line test passes against a single-line regex by accident, so `tests/
test_components.py` folds a value across three lines. The helper exists so the next
script cannot re-invent the substitution; the assertion exists because the helper itself
could have the same bug.

Usage:
    from build.components import rewrite, set_field
    rewrite(
        Path("sources/scores/mastra.yaml"),
        {"license": {"value": "Apache-2.0", "detail": "OSI"}, "source": {"value": "public"}},
    )
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

# PyYAML's `width` is a soft target: it breaks at the first space AFTER the column is
# exceeded, so 100 yields lines in the 100-115 range. That matches what the score files
# already contain (the folded blocks peak at columns 102-103), so an edit does not reflow
# the whole field and bury the real change in a whitespace diff.
WIDTH = 100
INDENT = "  "


def block_bounds(lines: list[str], key: str) -> tuple[int, int] | None:
    """Line range [start, end) of the top-level `key:` mapping.

    Shared with `build/apply_scores.py`, which used to define its own copy. One
    definition, because both are locating a block in the same file format.
    """
    start = None
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:") and not line[:1].isspace():
            start = index
            break
    if start is None:
        return None
    for index in range(start + 1, len(lines)):
        if lines[index].strip() and not lines[index][:1].isspace():
            return start, index
    return start, len(lines)


def find_key(lines: list[str], bounds: tuple[int, int], key: str) -> int | None:
    """Index of a two-space-indented `key:` inside the block, or None.

    Indent is checked exactly. A `score:` nested deeper — inside a `sources` entry, say —
    is a different key and must not be mistaken for the axis's own.
    """
    for index in range(bounds[0] + 1, bounds[1]):
        line = lines[index]
        if line.startswith(f"  {key}:") and not line[2:3].isspace():
            return index
    return None


def field_span(lines: list[str], bounds: tuple[int, int], key: str) -> tuple[int, int] | None:
    """[start, end) covering `  key:` AND every folded continuation line.

    The continuation test is indentation, not content. A sibling key sits at the same
    indent as `key`, so anything MORE indented belongs to this field's value. That is the
    entire reason this is not a line-oriented regex.

    One exception, and it is not a special case so much as the same rule read correctly: a
    block sequence puts its items at the KEY's indent, so `sources:` is followed by `  - url:`
    at two spaces. Those items are the value. Treating them as siblings ends the span after
    the `sources:` line alone, and the replacement then sits above the old items rather than
    replacing them — which the re-parse assertion catches as a doubled list rather than
    letting it through, but catching it is not the same as handling it.

    A blank line ends the span. Nothing in `sources/scores/` puts one inside a scalar, and
    treating it as a terminator fails loudly via the reparse assertion if that ever stops
    being true, rather than swallowing the rest of the block.
    """
    start = find_key(lines, bounds, key)
    if start is None:
        return None
    end = start + 1
    while end < bounds[1]:
        line = lines[end]
        if not line.strip():
            break
        indent = len(line) - len(line.lstrip())
        if indent <= len(INDENT) and not line.startswith(f"{INDENT}- "):
            break
        end += 1
    return start, end


def render(key: str, value: object, width: int = WIDTH) -> list[str]:
    """The `  key: ...` lines for a value, quoted and folded by PyYAML.

    Emitting through the YAML dumper rather than by hand is what makes an arbitrary value
    safe: `vellum`'s components contains `vellum-assistant: gateway+clients`, and a bare
    `: ` inside a plain scalar changes the parse. The dumper quotes it; a format string
    would not have known to.
    """
    dumped = yaml.safe_dump(
        {key: value},
        default_flow_style=False,
        allow_unicode=True,
        width=width,
        sort_keys=False,
    )
    return [f"{INDENT}{line}\n" if line.strip() else "\n" for line in dumped.splitlines()]


def set_field(text: str, value: object, axis: str = "openness", key: str = "components") -> str:
    """Return `text` with `axis.key` replaced by `value`. Raises rather than guessing.

    Generic over the field, though `components` is the motivating case and the default.
    `score` and `class` go through the same path, which is what makes a score correction
    and a components edit the same operation with the same reparse assertion behind it -
    and `value` is typed loosely because `score` is an int.

    Three checks before returning, in order of what they catch:

      1. the re-parsed field equals `value` — the edit did what was asked;
      2. the re-parsed document equals the original with only that one field changed —
         nothing else was spliced, reflowed or swallowed. This is the check that catches
         folded-scalar corruption, because a spliced tail lands in a NEIGHBORING key;
      3. the bytes before and after the span are identical — true by construction, so a
         failure here means the span itself was computed wrong.
    """
    lines = text.splitlines(keepends=True)
    bounds = block_bounds(lines, axis)
    if bounds is None:
        raise ValueError(f"no top-level {axis!r} block")
    span = field_span(lines, bounds, key)
    if span is None:
        raise ValueError(f"{axis} has no {key!r} field to rewrite")

    rendered = render(key, value)
    new_lines = lines[: span[0]] + rendered + lines[span[1] :]
    new_text = "".join(new_lines)

    before = yaml.safe_load(text)
    after = yaml.safe_load(new_text)
    got = ((after or {}).get(axis) or {}).get(key)
    if got != value:
        raise ValueError(f"{axis}.{key} re-parsed as {got!r}, not the value asked for")
    expected = copy.deepcopy(before)
    expected[axis][key] = value
    if after != expected:
        raise ValueError(
            f"rewriting {axis}.{key} changed something else in the document; refusing to write"
        )
    tail = span[0] + len(rendered)
    if new_lines[: span[0]] != lines[: span[0]] or new_lines[tail:] != lines[span[1] :]:
        raise ValueError(f"rewriting {axis}.{key} moved bytes outside its own span")

    return new_text


def add_field(
    text: str,
    value: object,
    axis: str = "openness",
    key: str = "last_verified",
    before: str = "sources",
) -> str:
    """Return `text` with a field `axis.key` that did not exist, inserted before `before`.

    `set_field` rewrites a field that is already there and raises when it is not, which is
    the right default for `components` — a missing one means the file is not what the caller
    thinks. The re-read pass needs the other operation: `last_verified` is absent on almost
    every axis, and that is exactly the state it exists to change.

    Insertion is positional, so it needs a rule. The convention in the files that already
    carry a date is immediately before `sources:`, which also reads correctly: the date is a
    claim about the evidence listed under it.

    The same three assertions as `set_field`, one of them strengthened — re-parsing must show
    the original document plus this one key and nothing else, which is what catches an insert
    that landed inside a neighboring folded scalar rather than between two fields.
    """
    lines = text.splitlines(keepends=True)
    bounds = block_bounds(lines, axis)
    if bounds is None:
        raise ValueError(f"no top-level {axis!r} block")
    if find_key(lines, bounds, key) is not None:
        raise ValueError(f"{axis}.{key} already exists; use set_field to change it")
    anchor = find_key(lines, bounds, before)
    if anchor is None:
        raise ValueError(f"{axis} has no {before!r} field to insert before")

    rendered = render(key, value)
    new_lines = lines[:anchor] + rendered + lines[anchor:]
    new_text = "".join(new_lines)

    before_doc = yaml.safe_load(text)
    after = yaml.safe_load(new_text)
    expected = copy.deepcopy(before_doc)
    expected[axis][key] = value
    if after != expected:
        raise ValueError(
            f"inserting {axis}.{key} changed something else in the document; refusing to write"
        )
    tail = anchor + len(rendered)
    if new_lines[:anchor] != lines[:anchor] or new_lines[tail:] != lines[anchor:]:
        raise ValueError(f"inserting {axis}.{key} moved bytes outside its own span")

    return new_text


def put_field(
    text: str, value: object, axis: str = "openness", key: str = "components", before: str = "sources"
) -> str:
    """`set_field` when the key is there, `add_field` when it is not."""
    lines = text.splitlines(keepends=True)
    bounds = block_bounds(lines, axis)
    if bounds is None:
        raise ValueError(f"no top-level {axis!r} block")
    if find_key(lines, bounds, key) is None:
        return add_field(text, value, axis=axis, key=key, before=before)
    return set_field(text, value, axis=axis, key=key)


# `sources/products/*.yaml` wrap wider than the score files do. Same reasoning as WIDTH: match
# what the corpus already contains so an edit does not reflow the file around itself.
PRODUCT_WIDTH = 105


def document_field_span(lines: list[str], key: str) -> tuple[int, int] | None:
    """[start, end) covering a TOP-LEVEL `key:` and its continuation lines.

    The product files put `description` and `comments` at the document root rather than inside
    an axis block, so the field is at indent 0 and its continuations are indented by two — the
    same shape one level up. A block sequence still puts its items at the key's indent, which
    at the root means `- url: ...` in column 0, so that case is carried over too.
    """
    start = None
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:") and not line[:1].isspace():
            start = index
            break
    if start is None:
        return None
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if not line.strip():
            break
        if not line[:1].isspace() and not line.startswith("- "):
            break
        end += 1
    return start, end


def set_document_field(text: str, key: str, value: object, width: int = PRODUCT_WIDTH) -> str:
    """Return `text` with a top-level `key` replaced by `value`. Raises rather than guessing.

    The product prose needs this and `set_field` cannot do it: that one locates a field inside
    an axis block, and `description` has no block to be inside. Same three assertions, because
    the hazard is the same one — `sources/products/*.yaml` are hand-wrapped and do not
    round-trip, so a whole-document load-modify-dump rewraps every scalar in the file and
    buries a two-field edit in a corpus-wide diff.
    """
    lines = text.splitlines(keepends=True)
    span = document_field_span(lines, key)
    if span is None:
        raise ValueError(f"no top-level {key!r} field to rewrite")

    dumped = yaml.safe_dump(
        {key: value}, default_flow_style=False, allow_unicode=True, width=width, sort_keys=False
    )
    rendered = [f"{line}\n" for line in dumped.splitlines()]
    new_lines = lines[: span[0]] + rendered + lines[span[1] :]
    new_text = "".join(new_lines)

    before = yaml.safe_load(text)
    after = yaml.safe_load(new_text)
    if (after or {}).get(key) != value:
        raise ValueError(f"{key} re-parsed as {(after or {}).get(key)!r}, not the value asked for")
    expected = copy.deepcopy(before)
    expected[key] = value
    if after != expected:
        raise ValueError(f"rewriting {key} changed something else in the document; refusing to write")
    tail = span[0] + len(rendered)
    if new_lines[: span[0]] != lines[: span[0]] or new_lines[tail:] != lines[span[1] :]:
        raise ValueError(f"rewriting {key} moved bytes outside its own span")

    return new_text


def rewrite(path: Path, value: object, axis: str = "openness", key: str = "components") -> bool:
    """Write the new value into the file. True when the file changed."""
    text = path.read_text()
    new_text = set_field(text, value, axis=axis, key=key)
    if new_text == text:
        return False
    path.write_text(new_text)
    return True


def parse(value: str) -> dict[str, str]:
    """`k:v;k:v` -> dict, paren-aware. Re-exported from the checker that owns it.

    Editing a components string almost always means reading it first, and there must be
    exactly one parser or a writer and a reader can disagree about what a value says.
    """
    from build.check_rubric import split_components

    return split_components(value)


def format(fields: dict[str, str]) -> str:  # noqa: A001 - the inverse of `parse`, so named for it
    """dict -> `k:v;k:v`, preserving insertion order.

    No spaces after the separators, matching what the 470 files already contain.
    """
    return ";".join(f"{key}:{val}" for key, val in fields.items())
