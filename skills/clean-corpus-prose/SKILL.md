---
name: clean-corpus-prose
description: Use when rewriting published prose that was written for the score auditor rather than the visitor — score notes in rubric vocabulary, notes that restate their sources' figures, template openings, footnotes that repeat a note. One category per unit of work, prose only, never a score or a date, in os-ai-map.
---

# Clean corpus prose

A score `note` explains a rung to a reader who has never seen the rubric. A `shows` says what a
page shows. A product `comments` is a footnote about our reading or nothing. The contract is
`docs/reference/product-copy.md`; this skill is the pass that brings a category's records to it
without touching anything that carries evidence.

The defect it works on was measured on 2026-09-17 (#619): a third of the notes said "rung 4",
"one below the anchor", "level 5 here is measured, not inferred", restated the exact figures the
source lines beneath already showed, or opened with the same three words as seventy others. The
same prompt wrote them all, and the page reads that way.

## Trigger
`uv run python -m build.prose_worklist` shows a category with flagged notes. Run one category per
pass. For a single product whose *score* is wrong, this is the wrong door: `update-product`.

## Required reading
- `docs/reference/product-copy.md`, in full: the one rule, the note shape, the vocabulary table,
  and the goldens. The goldens are the standard; read them before the first note, and again cold
  when the category is done.
- `docs/reference/evidence-and-freshness.md`, the section on what `last_verified` means. This
  pass may not write one.

## One objective, and a log for everything else

**The objective is the audience.** Not better scores, not fresher evidence, not a tidier
argument. A pass that stops to fix what it finds never finishes.

**Everything the pass may not fix, it writes down.** A note whose argument contradicts its own
score, a fact that looks stale, a thin note the vocabulary was hiding: slug, axis, one sentence,
into the findings log. The log lands on the PR; each entry is somebody's later `update-product`.

**A score file must still hold everything needed to settle a disagreement afterwards.** If
deleting a clause would leave a reader unable to reconstruct why the score is what it is, the
clause is durable. It moves into `shows` or `components[].detail` if it is evidence, or stays in
the note in plain words if it is the argument. It is not deleted.

## The unit of work is one record, and the tool is the worklist

```bash
uv run python -m build.prose_worklist --category <slug>     # what is flagged, and why
uv run python -m build.prose_worklist --json > worklist.json
```

Each row names a slug, an axis and its tells: `vocabulary`, `figure`, `opening`, `retracting`,
`length` on a note; `shows_vocabulary` (with the source index) on a source line; `restates_notes`
or `vocabulary` on a footnote. All three fields are published, and `tests/test_score_notes.py`
holds every one of them at zero. Work the flagged rows only; a note with no tells is
left alone even when a rewrite would be nicer. For each flagged record:

1. **Read the whole score file** and the product file: all three notes, every `shows`,
   `components`, `comments`. The same argument often sits in two of them.
2. **Classify the note against the goldens.** Already right, or one of the tells.
3. **Rewrite in the two-sentence shape**, from the facts the record already carries. The
   worklist's `shape` tell (over 400 characters or more than two sentences) is advisory, because
   three goldens run past it; a third sentence stays only for a distinction the score turns on. What puts
   it on this rung; what keeps it off the next. Plain words for every rubric word. Figures
   rounded, exact ones left to `shows`. Peers named. A capability note that names a peer with
   no `relative_to` recorded goes in the findings log; recording the comparison is a structured
   edit with a gate behind it, and `check_prose_diff` fails a prose commit that makes one.
4. **Move, do not lose.** A detail the note leaned on that no `shows` carries goes into the
   relevant `shows`. A vocabulary ruling goes into the findings log for `docs/reference/`.
5. **Drop a footnote that restates a note.** Keep one that says something no other field does.
6. **Do not open a source.** This is a rewrite, not a refresh. A fact the record does not
   already carry is not written.

## Edits go through `build/prose_edit.py`, and nothing else

```bash
uv run python -m build.prose_edit note <slug> <axis> --text-file new.txt
uv run python -m build.prose_edit shows <slug> <axis> <index> --text-file new.txt
uv run python -m build.prose_edit comments <slug> --text-file new.txt
uv run python -m build.prose_edit comments <slug> --drop
uv run python -m build.prose_edit description <slug> --text-file new.txt
```

It wraps `build/components.py`, so nothing else in the file can move, and it refuses the edits
this pass is not allowed to make: emptying a note, running past the 600-character guard, adding
a date, dropping a phrase `check_channel_authority` reads (`understates`, `inflated`, `minority
channel`), dropping a date on the product-fact allowlist, writing a `Verified … via` sentence
into a footnote, a description that refers to this record or the map, speaks as "we" or "you",
or carries a rubric word (the worklist's `description_*` tells). A refusal is a finding for the log, not a reason to reach for a text editor.
Never load-modify-dump a corpus file, and never hand-splice one; both have shipped defects here.

## What a pass may never do

- **Change a score, a level, a class, `reach`, `basis`, `value`.** If the rewrite reveals the
  score is wrong, log it and move on.
- **Touch `last_verified`, `accessed`, `http_status`, `content_sha256`, `establishes`, a URL, or
  the `sources` list's length.** `build/check_prose_diff.py` fails the commit if one moved.
- **Withdraw a claim a gate reads.** The 19 notes that say the signal understates the product
  are pinned in `tests/test_check_channel_authority.py`; withdrawing the claim is a re-read.
- **Add a fact.** No source is opened, so no new fact is known.
- **Leave a note that no longer stands alone.** The vocabulary was sometimes carrying the whole
  argument. Rewrite it in plain words; do not cut it to a fragment.
- **Lengthen a note without a reason, or paste one paragraph across products.** The pilot pass
  turned fourteen one-line notes ("Fully OSI-licensed (Apache-2.0), full source public") into
  the same 330-character paragraph with the vendor swapped, lifting the `shows` lines up into
  the note to do it. Identical facts get the same short sentence. A `shows` detail stays in
  `shows`.
- **State a usage figure.** A star, download, pull, user or customer count is stale the day the
  source refreshes, and "the most in this category" is false the day a product is added. The
  number is in the source line with its date and in `Reach`; the note says what was measured,
  why it stands for the product, and what it cannot show. A durable product fact with a number
  in it (8B parameters, a 32k context, a benchmark score at release) stays. Nor any grading of a
  figure: "comfortably", "solid", "mid-range" are filler.
- **Write scorer's shorthand.** "Holds it at", "stands in", "is read the same way", "a band
  lower", "at this band", "the adoption band", "nothing to band on", "bands on stars",
  "countable channel", "star-based reading", a fragment where a sentence was wanted. "Band" as
  the name of a score is machinery wherever it appears; a spectral band is not. Every note is full sentences an editor would publish without noticing
  the prose; clear but visibly written from a rubric is not good enough.

## Order and size

**One category per pass, one commit per category, worst-first by the worklist's count.** A
reviewer reads a category as one editorial voice. Inside a pass, work products in worklist
order; run up to four categories in parallel only with a scratch directory per category and per
product, because two passes sharing a filename have overwritten each other here before.

## Validation, before the commit

```bash
uv run python -m build.check_prose_diff                 # only note / shows / comments moved
uv run python -m build.validate                         # 0 error(s)
uv run pytest -q -n auto tests/test_score_notes.py tests/test_product_prose.py \
    tests/test_check_channel_authority.py tests/test_banded_quantity.py \
    tests/test_check_capability.py tests/test_prose_tools.py
uv run python -m build.check_instrument                 # reads adoption notes for figures
uv run python -m build.check_channel_authority          # reads adoption notes for the admission
uv run python -m build.check_capability                 # recorded comparisons still hold
uv run python -m build.prose_worklist --category <slug> # what is left, and why
```

`tests/test_score_notes.py` holds every count at zero: a note, source line or footnote in the
rubric's words, a note over the guard, or a note opening on a template fails the suite. Zero
means zero matches to the detector as it stands, not that no sentence written for the auditor
remains: every pass so far has found a phrasing the last one missed ("one band below", "the top
level, reserved for"). The detector is the floor; the sample read cold is the standard, and a
phrasing the sample turns up becomes a pattern before the pass closes. Before pushing,
`uv run python -m build.preflight`.

**The review bar, per category:** the checks above green; three files read cold at random
against the goldens, plus every note the pass logged as thin; and the findings log on the PR.

## Stop and escalate
- A note's argument is wrong, not just badly framed → `update-product`.
- The category's evidence is stale throughout → `refresh-category`.
- The `note` contract itself needs to change → `migrate-axis`.
- A rubric ruling turns up in a note and nowhere in `docs/reference/` → log it; the doc edit is
  its own change.

## Related
- Issue #619, the audit this skill works from; #322, the verification-log pass before it.
- `docs/reference/product-copy.md`, the contract and the goldens.
- `build/prose_worklist.py`, `build/prose_edit.py`, `build/check_prose_diff.py`.
- `skills/update-product/SKILL.md`, the door for anything that moves a score.
