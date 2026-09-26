import json,sys,csv,re
sys.path.insert(0,'research/multimodal_models/tools')
from parked import P
D='research/multimodal_models'
ev=json.load(open(f'{D}/.evidence.json'))
esc=lambda s:str(s).replace('|','\\|')
t6=["| slug | scope | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints | org GitHub/HF handle | notes |","|---|---|---|---|---|---|---|---|---|---|---|"]
for e in ev:
    t6.append("| "+" | ".join(esc(x) for x in [e['slug'],e['scope'],e['st'],e['lic'],e['arch'],e['push'],e['rel'],e['adopt'],e['members'],e['handle'],e['notes']])+" |")
t7=["| name | reason | evidence | source URL | fetch date |","|---|---|---|---|---|"]
for n,r,i,u,s in P: t7.append(f"| {esc(n)} | {esc(r)} | {i} | {u} | 2026-09-26 |")
# source list: every F/W id cited in 6b/7
txt="\n".join(t6+t7)+open('research/multimodal_models/tools/head.md').read()+open('research/multimodal_models/tools/tail.md').read()
for x,y in re.findall(r'F(\d{4})-F(\d{4})',txt): txt+=" "+" ".join(f"F{i:04d}" for i in range(int(x),int(y)+1))
ids=sorted(set(re.findall(r'\b[FW]\d{4}\b',txt)))
fl={r['id']:r for r in csv.DictReader(open(f'{D}/fetch-log.tsv'),delimiter='\t')}
wl={r['id']:r for r in csv.DictReader(open(f'{D}/web-log.tsv'),delimiter='\t')}
src=["| id | fetched (UTC) | HTTP / tool | URL or query |","|---|---|---|---|"]
for i in ids:
    if i in fl: r=fl[i]; src.append(f"| {i} | {r['fetched_at_utc']} | {r['http']} | {esc(r['url'])} |")
    elif i in wl: r=wl[i]; src.append(f"| {i} | {r['utc_timestamp']} | {r['tool']} | {esc(r['query_or_url'])} |")
    else: src.append(f"| {i} | MISSING | | |")
open('research/multimodal_models/tools/t6b.md','w').write("\n".join(t6))
open('research/multimodal_models/tools/t7.md','w').write("\n".join(t7))
open('research/multimodal_models/tools/t6c.md','w').write("\n".join(src))
print(len(ids),'ids cited; missing:',[i for i in ids if i not in fl and i not in wl])
