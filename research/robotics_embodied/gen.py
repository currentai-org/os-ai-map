"""Generate rows.<slug>.yaml and the section 2/6/7/8 fragments from spec.py. Run: python3 gen.py"""
import collections, csv, re
import yaml
import spec

TODAY = "2026-09-26"
CUT = "2025-09-26"  # 12 months before this run
ORDER = ["github", "huggingface_model", "huggingface_dataset", "pypi", "arxiv", "homepage"]


def rows_yaml(cat, rows):
    prods = []
    for r in rows:
        p = {"slug": r["slug"], "display_name": r["name"], "type": r["type"], "org": r["org"]}
        for k in ORDER:
            if k in r["art"]:
                p[k] = r["art"][k]
        prods.append(p)
    return yaml.safe_dump({"category": cat, "products": prods}, sort_keys=False, allow_unicode=True, width=200)


def first_date(s):
    m = re.search(r"20\d\d-\d\d-\d\d", s)
    return m.group(0) if m else None


def active(r):
    # latest date named in the push or release cells; a closed product counts when its page is live
    ds = re.findall(r"20\d\d-\d\d-\d\d", r["push"] + " " + r["rel"])
    if r["status"] == "closed" and r["alive"].startswith("live"):
        return True
    return bool(ds and max(ds) >= CUT)


def metrics(rows):
    st = collections.Counter(r["status"] for r in rows)
    orgs = collections.Counter(r["org"] for r in rows)
    top, n = orgs.most_common(1)[0]
    ties = [o for o, c in orgs.items() if c == n]
    act = [r["slug"] for r in rows if active(r)]
    closedlive = sum(1 for r in rows if r["status"] == "closed" and not any(d >= CUT for d in re.findall(r"20\d\d-\d\d-\d\d", r["push"] + " " + r["rel"])))
    usage = [r["slug"] for r in rows if any(k in r["art"] for k in ("pypi", "huggingface_model", "huggingface_dataset"))]
    types = collections.Counter(r["type"] for r in rows)
    return dict(n=len(rows), st=st, norg=len(orgs), top=ties, topn=n, share=100.0 * n / len(rows),
                act=act, closedlive=closedlive, usage=usage, types=types, orgs=orgs)


def fmt_metrics(m):
    st = m["st"]
    return "\n".join([
        f"- accepted candidates: {m['n']}  (open: {st['open']}, open-weights: {st['open-weights']}, source-available: {st['source-available']}, closed: {st['closed']})",
        f"- by type: " + ", ".join(f"{k} {v}" for k, v in sorted(m["types"].items())),
        f"- independent organizations: {m['norg']}; largest org's share: {m['share']:.1f}% ({' / '.join(m['top'])}, {m['topn']} rows{' each' if len(m['top'])>1 else ''})",
        f"- candidates active in the last 12 months (a dated push or release on/after {CUT}; a closed product counts when its product page is live): {len(m['act'])} of {m['n']}" + (f" ({m['closedlive']} of them only by the live-page rule)" if m['closedlive'] else ""),
        f"- candidates with a usage instrument (PyPI or HF downloads) declared: {len(m['usage'])} of {m['n']}; the rest are stars-only or unmeasured",
    ])


def evidence(rows):
    out = ["| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = [r["slug"], r["status"], r["lic"], r["alive"], r["push"], r["rel"], r["adopt"], r["members"], r["handle"], r["notes"]]
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(out)


def parked(pr):
    out = ["| name | reason | source ids | fetch date |", "|---|---|---|---|"]
    for n, why, src in pr:
        out.append(f"| {n} | {why} | {src} | {TODAY} |")
    return "\n".join(out)


def counts(rows, pr, dups=()):
    n = lambda s: len([x for x in s.split(",") if x.strip()])
    # cross-category duplicates add signals but no unique candidates
    sig = sum(len(r["src"]) for r in rows) + sum(n(s) for _, _, s in pr) + sum(n(s) for _, _, s in dups)
    uniq = len(rows) + len(pr)
    return dict(raw=sig, dup=sig - uniq, uniq=uniq, acc=len(rows), park=len(pr))


def ids_in(text):
    return set(re.findall(r"\b[FW]\d{4}\b", text))


def dedup(rows):
    idx = list(csv.DictReader(open("../corpus-index.tsv"), delimiter="\t"))
    slugs, arts = set(), set()
    for x in idx:
        slugs.add(x["slug"])
        slugs.update(a for a in (x["retired_aliases"] or "").split(",") if a)
        for col in ("github", "huggingface", "pypi"):
            for a in re.split(r"[,;]", x[col] or ""):
                if a.strip():
                    arts.add(a.strip().lower())
    hits = []
    for r in rows:
        if r["slug"] in slugs:
            hits.append(("slug", r["slug"]))
        for k, v in r["art"].items():
            if k != "homepage" and str(v).lower() in arts:
                hits.append((k, v))
    return hits


if __name__ == "__main__":
    for cat, rows in (("robotics_embodied", spec.R), ("world_models", spec.W)):
        open(f"rows.{cat}.yaml", "w").write(rows_yaml(cat, rows))
    allrows = spec.R + spec.W
    slugs = [r["slug"] for r in allrows]
    assert len(slugs) == len(set(slugs)), "duplicate slug across the two files"
    arts = [(k, v) for r in allrows for k, v in r["art"].items() if k != "homepage"]
    dupart = [a for a, c in collections.Counter(arts).items() if c > 1]
    assert not dupart, dupart
    frag = {}
    for key, rows, pr, du in (("R", spec.R, spec.PR, ()), ("W", spec.W, spec.PW, spec.DW)):
        m = metrics(rows)
        frag[key] = dict(metrics=fmt_metrics(m), evidence=evidence(rows), parked=parked(pr), dups=parked(du) if du else "", counts=counts(rows, pr, du), m=m)
    import json
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "m"} for k, v in frag.items()}, open("frag.json", "w"), indent=1, default=str)
    for k in frag:
        print(k, frag[k]["metrics"], frag[k]["counts"], sep="\n")
        print("inactive:", [r["slug"] for r in (spec.R if k == "R" else spec.W) if not active(r)])
        print("orgs:", dict(frag[k]["m"]["orgs"]))
    print("dedup hits:", dedup(allrows))
    # every id cited must exist in the logs with a good status
    good = set()
    for r in list(csv.reader(open("fetch-log.tsv"), delimiter="\t"))[1:]:
        if r[2] == "200":
            good.add(r[0])
    for r in list(csv.reader(open("web-log.tsv"), delimiter="\t"))[1:]:
        good.add(r[0])
    cited = set()
    for r in allrows:
        for f in ("lic", "alive", "push", "rel", "adopt", "members", "notes"):
            cited |= ids_in(r[f])
    for _, w, s in spec.PR + spec.PW + spec.DW:
        cited |= ids_in(w + " " + s)
    print("cited ids not good in logs:", sorted(cited - good))
