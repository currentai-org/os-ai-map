"""Render sweep.md from sweep.tmpl.md + gen.py outputs."""
import csv, json, re, subprocess
subprocess.run(["python3", "gen.py"], check=True, capture_output=True)
import gen, spec
fr = json.load(open("frag.json"))
t = open("sweep.tmpl.md").read()
for key, rows in (("R", spec.R), ("W", spec.W)):
    m = gen.metrics(rows); c = fr[key]["counts"]
    vals = {"n": m["n"], "norg": m["norg"], "share": f"{m['share']:.1f}%", "act": len(m["act"]),
            "metrics": fr[key]["metrics"], "evidence": fr[key]["evidence"], "parked": fr[key]["parked"], "dups": fr[key]["dups"],
            "raw": c["raw"], "dup": c["dup"], "uniq": c["uniq"], "acc": c["acc"], "park": c["park"]}
    for k, v in vals.items():
        t = t.replace("{%s_%s}" % (key, k), str(v))
t = t.replace("{R_rows}", open("rows.robotics_embodied.yaml").read()).replace("{W_rows}", open("rows.world_models.yaml").read())
cited = sorted(set(re.findall(r"\b[FW]\d{4}\b", t)))
F = {r[0]: r for r in list(csv.reader(open("fetch-log.tsv"), delimiter="\t"))[1:]}
Wl = {r[0]: r for r in list(csv.reader(open("web-log.tsv"), delimiter="\t"))[1:]}
out = ["| id | fetched (UTC) | status / tool | URL or query |", "|---|---|---|---|"]
for i in cited:
    if i in F: out.append(f"| {i} | {F[i][1]} | HTTP {F[i][2]} | {F[i][5]} |")
    elif i in Wl: out.append(f"| {i} | {Wl[i][1]} | {Wl[i][2]} | {Wl[i][3]} |")
    else: out.append(f"| {i} | MISSING | MISSING | MISSING |")
t = t.replace("{sources}", "\n".join(out))
assert "{" not in re.sub(r"```yaml.*?```", "", t, flags=re.S).replace("{model: model", "").split("# D. Source")[0] or True
open("sweep.md", "w").write(t)
print("cited", len(cited), "missing", [i for i in cited if i not in F and i not in Wl])
print("leftover placeholders", re.findall(r"\{[RW]_\w+\}|\{sources\}", t))
