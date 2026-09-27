"""Resolve a seed merge in progress. Usage: resolve_seed_merge.py MERGED_REF [MERGED_REF ...]
(list every seed ref merged so far, including the one being merged; origin/main is implied).
- sources/org_handles.yaml: rebuilt as a clean blockwise union (rebuild_org_handles.py)
- sources/taxonomy.yaml: both sides' category entries kept, each with its status line
- .github/ISSUE_TEMPLATE/*: both sides' lines kept
- sources/organizations/*.yaml (add/add) and tests/fixtures/identity_*: ours (fixtures are
  regenerated after the merge); org files whose sides differ are reported."""
import re, subprocess, sys
from pathlib import Path
R = Path("/home/user/os-ai-map")
def sh(*a): return subprocess.run(a, cwd=R, capture_output=True, text=True).stdout
H = r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n"
for p in [x for x in sh("git", "diff", "--name-only", "--diff-filter=U").split() if x]:
    f = R / p
    if p == "sources/org_handles.yaml":
        subprocess.run(["uv", "run", "python", "research/tools/rebuild_org_handles.py", "origin/main", *sys.argv[1:]], cwd=R, check=True)
    elif p == "sources/taxonomy.yaml":
        s = f.read_text()
        s = re.sub(H + r"(      status: \w+\n)", lambda m: m.group(1) + m.group(3) + m.group(2) + m.group(3), s, flags=re.S)
        f.write_text(s)
    elif p.startswith(".github/ISSUE_TEMPLATE/"):
        f.write_text(re.sub(H, lambda m: m.group(1) + m.group(2), f.read_text(), flags=re.S))
    elif p.startswith("sources/organizations/") or p.startswith("tests/fixtures/identity_"):
        ours, theirs = sh("git", "show", f":2:{p}"), sh("git", "show", f":3:{p}")
        f.write_text(ours)
        if p.startswith("sources/organizations/") and ours != theirs: print(f"org differs, kept ours: {p}")
    else:
        print(f"UNHANDLED {p}"); continue
    if "<<<<<<<" in f.read_text(): print(f"MARKERS LEFT {p}"); continue
    subprocess.run(["git", "add", p], cwd=R)
left = [x for x in sh("git", "diff", "--name-only", "--diff-filter=U").split() if x]
print("unresolved:", left); sys.exit(1 if left else 0)
