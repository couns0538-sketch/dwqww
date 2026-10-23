from pathlib import Path
import subprocess,hashlib,json,time,urllib.request,traceback
from datetime import datetime,timezone
r=Path('/workspace/dwqww'); out=Path('/workspace/forge-nnue-handoff-20261023/publication-completed-net-evidence-attempt1');out.mkdir(exist_ok=False)
rev='a6a3386debea08f0010cc8a1feed25d8c983f0af';branch='forge/nnue-pipeline-20261023'
def sha(x):return hashlib.sha256(x).hexdigest()
try:
 argv=['git','-c',"credential.helper=!gh auth git-credential",'ls-remote','origin','refs/heads/'+branch]
 (out/'ls-remote.command.json').write_text(json.dumps({'argv':argv})+'\n');t=time.monotonic()
 p=subprocess.run(argv,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/'ls-remote.stdout').write_bytes(p.stdout);(out/'ls-remote.stderr').write_bytes(p.stderr)
 (out/'ls-remote.receipt.json').write_text(json.dumps({'returncode':p.returncode,'elapsed_seconds':time.monotonic()-t})+'\n')
 assert p.returncode==0 and p.stdout.decode().split()[0]==rev
 paths=['releases/forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip','validation/nnue-pipeline-20261023/independent-audit-frozen-zeroep3-report-attempt1/metrics.json','validation/nnue-pipeline-20261023/windows-final-net-trial-recovery-index/RECOVERY-INDEX.json','validation/nnue-pipeline-20261023/full-warm20-recovery-attempt1/MANIFEST.json','validation/nnue-pipeline-20261023/QUALIFICATION_STATUS.md']
 # Manifest naming is read from committed tree rather than guessed.
 manifest_prefix='validation/nnue-pipeline-20261023/full-warm20-recovery-attempt1/'
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',rev,'--',manifest_prefix],cwd=r,text=True).splitlines()
 m=[n for n in names if n.endswith('/ARCHIVE-MANIFEST.json') or n.endswith('/MANIFEST.json') or n.endswith('/manifest.json')]
 assert len(m)==1,m
 paths[3]=m[0]; rows=[]
 for i,path in enumerate(paths):
  expected=subprocess.check_output(['git','show',rev+':'+path],cwd=r);url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+rev+'/'+path
  t=time.monotonic()
  with urllib.request.urlopen(url,timeout=90) as response:
   status=response.status;data=response.read()
  assert status==200 and data==expected,(path,len(data),sha(data),sha(expected))
  if i==0:
   assert len(data)==13008348 and sha(data)=='276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca'
   (out/'actual-public-download.zip').write_bytes(data)
  rows.append({'path':path,'url':url,'http_status':status,'bytes':len(data),'sha256':sha(data),'matches_committed_blob':True,'elapsed_seconds':time.monotonic()-t})
 result={'status':'PASS_REMOTE_HEAD_AND_PUBLIC_BYTE_READBACK','utc':datetime.now(timezone.utc).isoformat(),'commit':rev,'branch':branch,'downloads':rows}
 (out/'VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'downloads':len(rows),'windows_zip_sha256':rows[0]['sha256']}))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc());raise
