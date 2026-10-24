#!/usr/bin/env python3
"""Verify immutable public delivery bytes against exact local Git blobs."""
import argparse,datetime,hashlib,json,subprocess,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=Path('/workspace/dwqww')
paths=['SOL_REPORT_20261024.md','releases/sol-next-20261024/forge-buffer-source.zip','releases/sol-next-20261024/forge-int16-research-source.zip','releases/sol-next-20261024/int16_fix.patch','releases/sol-next-20261024/int16-source-manifest.json','releases/sol-next-20261024/sol-zen5-qualification.zip','validation/sol-next-20261024/int16/CR_DRAFT.md','validation/sol-next-20261024/buffer/CR_DRAFT.md']
rows=[]
for name in paths:
 expected=subprocess.check_output(['git','show',a.commit+':'+name],cwd=r);url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+a.commit+'/'+name
 with urllib.request.urlopen(url,timeout=30) as response:data=response.read();code=response.status
 assert code==200 and data==expected,(name,code)
 rows.append({'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'http':code,'exact_git_blob':True})
a.out.write_text(json.dumps({'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'publication_commit':a.commit,'source_commit':'074102419c90c6b3725cd83c172e1ec22a2d8203','scope':'Actual immutable public HTTP downloads, not just push acknowledgement','downloads':rows},indent=2)+'\n');print(json.dumps({'status':'PASS','downloads':len(rows),'publication_commit':a.commit}))
