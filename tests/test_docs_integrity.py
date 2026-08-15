"""Doc-integrity gate: keep the task-oriented docs single-sourced and linked.

The 2026-08-14 reorg made the docs a set of five task workflows over a shared reference
layer, with skills as thin wrappers pointing at the workflows. That structure only stays
true if something enforces it: a rule copied into two places drifts, a renamed doc leaves
dead links, and a skill that stops pointing at its workflow re-grows its own copy of the
procedure. This test is that enforcement, and it runs in `validate.yml` on every PR.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The hand-maintained documentation surface. Generated files (notebook_data.json,
# notebooks/*.py) and the gitignored session workspace are not part of it.
DOC_FILES = sorted(
    [p for p in REPO.glob("docs/**/*.md")]
    + [p for p in REPO.glob("skills/**/SKILL.md")]
    + [REPO / n for n in ("README.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md")]
)

PRIMARY_SKILLS = ["add-product", "update-product", "edit-category", "refresh-category", "migrate-axis"]

# Paths that were deleted or renamed in the reorg. A live reference to one is a regression.
DEAD_FRAGMENTS = [
    "docs/guides/",
    "docs/runbooks/",
    "verification-pass.md",
    "openness-spectrum.md",
    "product-info.md",
    "skills/curate-category",
    "skills/verify-product",
]


def test_doc_surface_is_present():
    """The five workflows, the router, and the reference set exist where the docs claim."""
    for rel in [
        "docs/README.md",
        "docs/reference/evidence-and-freshness.md",
        "docs/reference/capability.md",
    ] + [f"docs/workflows/{s}.md" for s in PRIMARY_SKILLS]:
        assert (REPO / rel).exists(), f"missing expected doc: {rel}"


def test_no_dead_path_references():
    """No hand-maintained doc references a path the reorg deleted or renamed."""
    problems = []
    for f in DOC_FILES:
        text = f.read_text(encoding="utf-8")
        for frag in DEAD_FRAGMENTS:
            if frag in text:
                problems.append(f"{f.relative_to(REPO)} references dead path '{frag}'")
    assert not problems, "dead-path references:\n" + "\n".join(problems)


def test_repo_relative_doc_paths_resolve():
    """Every `docs/.../x.md` path named in the doc surface points at a file that exists.

    Covers top-level docs (docs/README.md, docs/methodology.md) as well as the subtrees.
    """
    pat = re.compile(r"docs/[\w./-]+\.(?:md|json)")
    problems = []
    for f in DOC_FILES:
        for m in pat.findall(f.read_text(encoding="utf-8")):
            if not (REPO / m).exists():
                problems.append(f"{f.relative_to(REPO)} -> {m}")
    assert not problems, "unresolved repo-relative doc paths:\n" + "\n".join(problems)


def test_markdown_relative_links_resolve():
    """Markdown links between docs resolve to real files.

    Captures the path up to an optional #anchor, a title (`](x.md "t")`), or the closing
    paren, so a broken target is not hidden by a link that carries a title.
    """
    link = re.compile(r"\]\(\s*([^)\s#]+\.md)")
    problems = []
    for f in DOC_FILES:
        for target in link.findall(f.read_text(encoding="utf-8")):
            if target.startswith("http"):
                continue
            if not (f.parent / target).resolve().exists():
                problems.append(f"{f.relative_to(REPO)} -> {target}")
    assert not problems, "broken markdown links:\n" + "\n".join(problems)


def test_every_skill_name_matches_its_directory():
    for skill in REPO.glob("skills/*/SKILL.md"):
        name = re.search(r"^name:\s*(\S+)", skill.read_text(encoding="utf-8"), re.M)
        assert name, f"{skill.relative_to(REPO)} has no name in frontmatter"
        assert name.group(1) == skill.parent.name, (
            f"{skill.relative_to(REPO)} declares name '{name.group(1)}' "
            f"but lives in '{skill.parent.name}'"
        )


def test_primary_skills_point_at_their_workflow():
    """A thin wrapper must reference the workflow it wraps, so the procedure has one home."""
    problems = []
    for s in PRIMARY_SKILLS:
        skill = REPO / "skills" / s / "SKILL.md"
        assert skill.exists(), f"missing primary skill: {s}"
        wf = f"docs/workflows/{s}.md"
        if wf not in skill.read_text(encoding="utf-8"):
            problems.append(f"skills/{s}/SKILL.md does not reference {wf}")
    assert not problems, "skills not pointing at their workflow:\n" + "\n".join(problems)


def test_skills_are_delivered_to_the_harness():
    """Each skill is symlinked into .claude/skills/ so a session discovers it."""
    linked = {p.name for p in (REPO / ".claude" / "skills").iterdir()}
    have = {p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").exists()}
    missing = have - linked
    assert not missing, f"skills not registered under .claude/skills/: {sorted(missing)}"


def test_readme_router_lists_every_primary_skill():
    readme = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
    for s in PRIMARY_SKILLS:
        assert f"workflows/{s}.md" in readme, f"docs/README.md router omits {s}"
