"""Resolve mechanical conflicts during the round-1 integration merge (run from the worktree).
- tests/fixtures/identity_*: ours (regenerated after all merges)
- sources/organizations/*.yaml: ours text + union of `products:` slugs (theirs' missing lines inserted, order kept)
Anything else is reported for hand resolution."""
import re, subprocess, sys
def sh(*a): return subprocess.run(a, capture_output=True, text=True).stdout
left = []
for p in [x for x in sh("git","diff","--name-only","--diff-filter=U").split() if x]:
    ours, theirs = sh("git","show",f":2:{p}"), sh("git","show",f":3:{p}")
    if p.startswith("tests/fixtures/identity_"):
        open(p,"w").write(ours)
    elif p.startswith("sources/organizations/"):
        def roster(t):
            m = re.search(r"(?ms)^products:\n((?:- .*\n)+)", t); return m, (m.group(1).splitlines() if m else [])
        mo, lo = roster(ours); mt, lt = roster(theirs)
        extra = [l for l in lt if l not in lo]
        if not mo: print("NO ROSTER", p); left.append(p); continue
        new = ours[:mo.start(1)] + "\n".join(lo + extra) + "\n" + ours[mo.end(1):]
        rest_o = ours[:mo.start()] + ours[mo.end():]; rest_t = theirs[:mt.start()] + theirs[mt.end():] if mt else theirs
        if rest_o != rest_t: print("NON-ROSTER DIFF (kept ours)", p)
        open(p,"w").write(new)
    else:
        left.append(p); continue
    subprocess.run(["git","add",p])
print("hand-resolve:", left)
