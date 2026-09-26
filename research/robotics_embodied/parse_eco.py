import json,csv,sys
rows=list(csv.reader(open('fetch-log.tsv'),delimiter='\t'))[1:]
for r in rows:
    if 'repos.ecosyste.ms' not in r[5]: continue
    fid=r[0]
    if r[2]!='200': print(fid,r[2],r[6]); continue
    d=json.load(open(f'raw/{fid}.body'))
    print(fid,d.get('full_name'),'arch=%s'%d.get('archived'),'fork=%s'%d.get('fork'),'lic=%s'%d.get('license'),'push=%s'%(d.get('pushed_at') or '')[:10],'stars=%s'%d.get('stargazers_count'),'rel=%s'%(d.get('latest_release_published_at') or '')[:10],d.get('latest_release_tag_name'),'upd=%s'%(d.get('updated_at') or '')[:10])
