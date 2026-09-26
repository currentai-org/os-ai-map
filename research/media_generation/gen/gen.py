import yaml,collections,re,csv,sys
exec(open('research/media_generation/gen/data.py').read())
exec(open('research/media_generation/gen/parked.py').read())
OUT='research/media_generation/gen/out_'
# rows.yaml
rows=[]
for x in A:
    r={'slug':x['slug'],'display_name':x['name'],'type':x['type'],'org':x['org']}
    if x.get('gh'): r['github']=x['gh']
    if x.get('hf'): r['huggingface_model']=x['hf']
    if x.get('pypi'): r['pypi']=x['pypi']
    if x.get('home'): r['homepage']=x['home']
    rows.append(r)
with open(OUT+'rows.yaml','w') as f:
    f.write('# Proposed category media_generation (issue #603). Candidate rows from the 2026-09-26 live sweep.\n# Evidence: research/media_generation/sweep.md section 6b. Not yet a registry file.\n')
    yaml.safe_dump({'category':'media_generation','products':rows},f,sort_keys=False,allow_unicode=True)
# evidence table
esc=lambda s:(s or '').replace('|','\\|')
L=['| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |','|---|---|---|---|---|---|---|---|---|---|']
for x in A:
    L.append('| '+' | '.join(esc(v) for v in [x['slug'],x['status'],x['lic'],x['arch'],x['push'],x['rel'],x['adopt'],x.get('members',''),x.get('handle',''),x.get('notes','')])+' |')
open(OUT+'_evidence.md','w').write('\n'.join(L)+'\n')
# parked table
L=['| name | reason | evidence | discovery source |','|---|---|---|---|']
for n,r,e,s in P: L.append(f'| {esc(n)} | {esc(r)} | {esc(e)} | {", ".join(s)} |')
open(OUT+'_parked.md','w').write('\n'.join(L)+'\n')
L=['| signal | matched | evidence |','|---|---|---|']
for n,m,e in D: L.append(f'| {esc(n)} | {esc(m)} | {esc(e)} |')
open(OUT+'_dups.md','w').write('\n'.join(L)+'\n')
# metrics
acc=len(A); st=collections.Counter(x['status'] for x in A)
# parent company for concentration
parent={'alibaba-cloud':'Alibaba','modelscope-alibaba':'Alibaba','tencent':'Tencent','tencent-ai-lab':'Tencent','bytedance':'ByteDance','bytedance-seed-volcano-engine':'ByteDance','stability-ai':'Stability AI','kuaishou':'Kuaishou','google':'Google','meta':'Meta','stepfun':'StepFun','minimax':'MiniMax','meituan':'Meituan','lllyasviel':'lllyasviel','vast-ai':'VAST'}
orgs=collections.Counter(x['org'] for x in A); par=collections.Counter(parent.get(x['org'],x['org']) for x in A)
def push_date(x):
    m=re.findall(r'(20\d\d-\d\d-\d\d)',x['push']); return max(m) if m else None
active=[x for x in A if x['bucket']!='closed' and push_date(x) and push_date(x)>='2025-09-26']
nonclosed=[x for x in A if x['bucket']!='closed']
usage=[x for x in A if x.get('pypi') or (x.get('hf') and 'HF 30d downloads' in x['adopt'])]
mod=collections.Counter((x['bucket'],x['modality']) for x in A)
print('accepted',acc,dict(st)); print('orgs',len(orgs),orgs.most_common(4)); print('parents',len(par),par.most_common(5))
print('active12m',len(active),'of',len(nonclosed)); print('usage',len(usage))
print('modality',dict(mod))
inactive=[ (x['slug'],push_date(x)) for x in nonclosed if x not in active]; print('inactive',inactive)
print('nousage',[x['slug'] for x in A if x not in usage])
srcs=sum(len(x['src']) for x in A)+sum(len(p[3]) for p in P); dups_multi=srcs-acc-len(P)
print('raw signals: candidate-source pairs',srcs,'+ index matches',len(D),'=',srcs+len(D)); print('parked',len(P),'unique',acc+len(P),'dup',dups_multi+len(D))
# not in brief (discovered)
brief_names=set('flux stable-diffusion hunyuan-video hunyuan-image hunyuan-3d wan cogvideo ltx mochi open-sora qwen-image hidream sana pixart kolors lumina trellis stable-audio musicgen audiocraft ace-step yue comfyui stable-diffusion-webui forge invokeai fooocus sdnext swarmui midjourney gpt-image nano-banana veo runway-gen kling suno'.split())
print('not named in brief',[x['slug'] for x in A if x['slug'] not in brief_names])
