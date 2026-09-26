import json,csv,sys,yaml,re
sys.path.insert(0,'research/multimodal_models/tools')
from cands import A
D='research/multimodal_models'
log=list(csv.DictReader(open(f'{D}/fetch-log.tsv'),delimiter='\t'))
fam=json.load(open(f'{D}/.families.json'))
def find(label):
    for r in log:
        if r['label']==label and r['http']=='200':
            try:
                d=json.load(open(f"{D}/raw/{r['id']}.body"))
                if isinstance(d,dict): return r['id'],d
            except Exception: pass
    return None,None
repo_override={'moondream':'F0201','fastvlm':'F0200','ovis':'F0233'}
famkeys={'llava':['llava-lmms','llava-hf'],'moondream':['moondream','moondream3']}
rows=[];ev=[]
def disc(hf,fks):
    # a top-listing signal counts when the flagship or any of the family's top-6 member ids appears in it
    ids={hf}|{i for k in fks for i in fam[k]['top']}
    out=set()
    for f in ['F0001','F0002','F0003','F0004','F0005']:
        if ids & {m['id'] for m in json.load(open(f'{D}/raw/{f}.body'))}: out.add(f)
    return out
for (slug,dn,org,gh,hf,st,scope,lic,members,notes,fk,sig) in A:
    hid,hd=find(f"HF model {slug} {hf}")
    if slug=="pixtral": hid="F0187"; hd=json.load(open(f"{D}/raw/F0187.body"))
    assert hid,(slug,hf)
    if gh:
        rid=repo_override.get(slug) or find(f"ecosystems repo {slug} {gh}")[0]
        rd=json.load(open(f"{D}/raw/{rid}.body"))
        assert rd['full_name'].lower()==gh.lower(),(slug,rd['full_name'],gh)
        arch=f"archived={rd['archived']}, fork={rd['fork']} ({rid})"
        push=f"{rd['pushed_at'][:10]} ({rid}); {rd['stargazers_count']:,} stars"+(" [archived: not counted as activity]" if rd['archived'] else "")
        repo_push=None if rd['archived'] else rd['pushed_at'][:10]
    else:
        arch="n/a (no repo declared)"
        push=f"no repo; HF lastModified {str(hd.get('lastModified'))[:10]} ({hid}) [not counted as activity]"
        repo_push=None
    fks=famkeys.get(slug,[fk])
    tot=sum(fam[k]['sum'] for k in fks); n=sum(fam[k]['n'] for k in fks)
    newest=max(fam[k]['newest'] for k in fks)
    fids=", ".join(fam[k]['f'] for k in fks)
    adopt=f"HF downloads (rolling 30d) summed over {n} vendor checkpoints: {tot:,} ({fids}); flagship {hf}: {hd.get('downloads'):,} ({hid})"
    lastrel=f"newest checkpoint {newest} ({fids})"
    row={'slug':slug,'display_name':dn,'type':'model','org':org}
    if gh: row['github']=gh
    row['huggingface_model']=hf
    rows.append(row)
    handle=(gh.split('/')[0]+' / ' if gh else '')+hf.split('/')[0]
    ev.append(dict(slug=slug,st=st,scope=scope,lic=lic,arch=arch,push=push,rel=lastrel,adopt=adopt,members=members,handle=handle,notes=notes,tot=tot,newest=newest,org=org,repo_push=repo_push,sig=sorted(set(sig)|{x.strip() for x in fids.split(',')}|disc(hf,fks))))
json.dump(ev,open(f'{D}/.evidence.json','w'),indent=1)
out={'category':'multimodal_models','products':rows}
with open(f'{D}/rows.yaml','w') as f:
    f.write("# Registry rows for the proposed multimodal_models category (issue #9), 2026-09-26 sweep.\n# Evidence per row: research/multimodal_models/sweep.md section 6b.\n")
    yaml.safe_dump(out,f,sort_keys=False,allow_unicode=True,width=200)
print(len(rows),'rows')
