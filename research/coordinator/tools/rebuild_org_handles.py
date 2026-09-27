"""Rebuild sources/org_handles.yaml as the blockwise union of the file at the given refs.
Blocks are copied verbatim (so notes and quoting survive), deduped on (org, platform, handle)
and sorted by org, platform, handle. Usage: rebuild_org_handles.py REF [REF ...]"""
import re, subprocess, sys
from pathlib import Path
R = Path("/home/user/os-ai-map")
def blocks_of(text):
    head, _, body = text.partition("handles:\n")
    out = []
    for b in re.split(r"(?m)^(?=- org: )", body):
        if not b.strip(): continue
        b = b if b.endswith("\n") else b + "\n"
        org = re.search(r"^- org: (.*)$", b, re.M).group(1).strip()
        plat = re.findall(r"^  platform: (.*)$", b, re.M); hand = re.findall(r"^  handle: (.*)$", b, re.M)
        assert len(plat) == 1 and len(hand) == 1, f"malformed block:\n{b}"
        out.append(((org, plat[0].strip(), hand[0].strip()), b))
    return head, out
seen, head = {}, None
for ref in sys.argv[1:]:
    t = subprocess.run(["git", "show", f"{ref}:sources/org_handles.yaml"], cwd=R, capture_output=True, text=True, check=True).stdout
    h, bl = blocks_of(t); head = head or h
    for k, b in bl:
        if k in seen and seen[k] != b: print(f"variant kept first: {k}")
        seen.setdefault(k, b)
items = sorted(seen.items(), key=lambda kb: (kb[0][0], kb[0][1], kb[0][2].lower()))
(R / "sources/org_handles.yaml").write_text(head + "handles:\n" + "".join(b for _, b in items))
print(len(items), "entries")
