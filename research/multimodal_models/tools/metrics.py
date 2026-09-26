import json,sys,collections
sys.path.insert(0,'research/multimodal_models/tools')
from parked import P
D='research/multimodal_models'
ev=json.load(open(f'{D}/.evidence.json'))
st=collections.Counter(e['st'] for e in ev); orgs=collections.Counter(e['org'] for e in ev)
import re
def active(e):
    # one rule: newest vendor member checkpoint, or push to a non-archived repo, within 12 months
    return max(e['newest'], e['repo_push'] or '')>='2025-09-26'
act=[e['slug'] for e in ev if active(e)]
scope=collections.Counter(e['scope'] for e in ev)
print('N',len(ev),dict(st)); print('orgs',len(orgs),orgs.most_common(4))
print('active',len(act)); print('inactive',[e['slug'] for e in ev if not active(e)])
print('scope',dict(scope))
sig_acc=sum(len(set(e['sig'])) for e in ev); sig_par=sum(len(set(p[4])) for p in P)
uniq=len(ev)+len(P); raw=sig_acc+sig_par
print('parked',len(P),'unique',uniq,'raw',raw,'dup',raw-uniq)
for s in ['vlm','video','gui','omni','unified']:
    sub=[e for e in ev if e['scope']==s]; o=collections.Counter(e['org'] for e in sub)
    print(s,len(sub),'orgs',len(o),'active',sum(active(e) for e in sub))
und=[e for e in ev if e['scope'] in('vlm','video','gui')]; o=collections.Counter(e['org'] for e in und)
print('understanding scope',len(und),'orgs',len(o),o.most_common(2),'active',sum(active(e) for e in und))
