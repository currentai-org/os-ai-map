"""Resolve a test_check_parity.py `deferred` census conflict: keep both comment blocks, and set
the assert to ours + (theirs - base_value), where base_value is the pre-tranche count parsed from
theirs' "N -> M" line. Prints the new value."""
import re, sys
p = "tests/test_check_parity.py"; t = open(p).read()
H = re.compile(r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n", re.S)
def fix(m):
    o, th = m.group(1), m.group(2)
    vo = int(re.search(r"assert len\(deferred\) == (\d+)", o).group(1))
    a, b = map(int, re.search(r"# (\d+) -> (\d+) (?:on [\d-]+ )?with", th).groups())
    vt = int(re.search(r"assert len\(deferred\) == (\d+)", th).group(1)); assert vt == b
    new = vo + (b - a)
    co = re.sub(r"\s*assert len\(deferred\) == \d+\n", "\n", o).rstrip("\n") + "\n"
    ct = re.sub(r"\s*assert len\(deferred\) == \d+\n", "\n", th).rstrip("\n") + "\n"
    ct = re.sub(r"# \d+ -> \d+ ((?:on [\d-]+ )?with)", lambda mm: f"# {vo} -> {new} " + mm.group(1), ct, count=1)
    print("deferred:", vo, "->", new)
    return co + "    #\n" + ct + f"    assert len(deferred) == {new}\n"
t2, n = H.subn(fix, t); assert n >= 1 and "<<<<<<<" not in t2
open(p, "w").write(t2)
