# Audit fixes (issues 1, 2, 3, 16): recompute these family entries in .families.json.
import json,re
fam=json.load(open('.families.json'))
def fam_of(files,rx,ex=None):
    d=[]
    for f in files:
        d+=[m for m in json.load(open(f'raw/{f}.body')) if re.search(rx,m['id']) and not (ex and re.search(ex,m['id']))]
    ids=[m['id'] for m in sorted(d,key=lambda m:-m.get('downloads',0))]
    return dict(f=", ".join(files),sum=sum(m.get('downloads',0) for m in d),n=len(d),newest=max(m['createdAt'][:10] for m in d),top=ids[:6])
fam['ovis']=fam_of(['F0234'],r'^ATH-MaaS/Ovis',r'(?i)Ovis-U|Ovis-Image|OCR|Embed|Clip')
fam['blip']=fam_of(['F0039','F0235'],r'(?i)blip',r'(?i)BLIP3o')
fam['vita']=fam_of(['F0050'],r'VITA',r'QinYu|VITA-E')
fam['internvl']=fam_of(['F0236'],r'InternVL',r'InternVL-U')
fam['paligemma']=fam_of(['F0237'],r'(?i)paligemma')
json.dump(fam,open('.families.json','w'),indent=1)
for k in ['ovis','blip','vita','internvl','paligemma']: print(k,fam[k]['n'],fam[k]['sum'],fam[k]['newest'])
