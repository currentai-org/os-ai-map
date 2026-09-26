import json,csv,sys
rows=list(csv.reader(open('fetch-log.tsv'),delimiter='\t'))[1:]
for r in rows:
    if 'huggingface.co/api/models?' not in r[5]: continue
    d=json.load(open(f'raw/{r[0]}.body'))
    print('==',r[0],r[6],len(d))
    for m in d[:15]:
        cd=m.get('cardData') or {}
        print('  ',m['id'],'dl=%s'%m.get('downloads'),'lic=%s'%cd.get('license'),cd.get('license_name',''),'gated=%s'%m.get('gated'),'mod=%s'%(m.get('lastModified') or '')[:10])
