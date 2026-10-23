"""Read back a final checkpoint and every Git-safe native-recovery part."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,urllib.request,sys,time,traceback
r=Path('/workspace/dwqww');h=Path('/workspace/forge-nnue-handoff-20261023');rev=sys.argv[1]
assert len(rev)==40
out=h/('final-pipeline-publication-'+rev[:7]);out.mkdir(exist_ok=False)
try:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==rev
 argv=['git','-c','credential.helper=!gh auth git-credential','ls-remote','origin','refs/heads/forge/nnue-pipeline-20261023']
 (out/'ls-remote.command.json').write_text(json.dumps({'argv':argv})+'\n');start=time.monotonic();p=subprocess.run(argv,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/'ls-remote.stdout').write_bytes(p.stdout);(out/'ls-remote.stderr').write_bytes(p.stderr);(out/'ls-remote.receipt.json').write_text(json.dumps({'returncode':p.returncode,'elapsed_seconds':time.monotonic()-start})+'\n')
 assert p.returncode==0 and p.stdout.decode().split()[0]==rev
 prefix='validation/nnue-pipeline-20261023/';ar=prefix+'linux-native-qualification-recovery-attempt1/'
 m=json.loads((r/ar/'ARCHIVE-MANIFEST.json').read_text())
 paths=[prefix+'FINAL_REPORT.md',prefix+'QUALIFICATION_STATUS.md',ar+'ARCHIVE-MANIFEST.json']+[ar+x['name'] for x in m['parts']]
 rows=[]
 for path in paths:
  expected=subprocess.check_output(['git','show',rev+':'+path],cwd=r);expected_hash=hashlib.sha256(expected).hexdigest();expected_size=len(expected);del expected
  url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+rev+'/'+path;start=time.monotonic();d=hashlib.sha256();size=0
  with urllib.request.urlopen(url,timeout=90) as response:
   status=response.status
   for block in iter(lambda:response.read(1048576),b''):d.update(block);size+=len(block)
  assert status==200 and size==expected_size and d.hexdigest()==expected_hash,path
  rows.append({'path':path,'url':url,'http_status':status,'bytes':size,'sha256':d.hexdigest(),'matches_committed_blob':True,'elapsed_seconds':time.monotonic()-start})
 z='releases/forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip';prior='a6a3386debea08f0010cc8a1feed25d8c983f0af'
 assert subprocess.check_output(['git','rev-parse',rev+':'+z],cwd=r)==subprocess.check_output(['git','rev-parse',prior+':'+z],cwd=r)
 result={'status':'PASS_FINAL_REMOTE_AND_SIX_PUBLIC_BYTE_READBACKS','utc':datetime.now(timezone.utc).isoformat(),'source_commit':rev,'downloads':rows,'windows_release_blob_unchanged_from_actual_public_verification_commit':prior,'windows_zip_sha256':'276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca','scope':'Actual final checkpoint and every3-part Linux archive download; no tests/games rerun'}
 assert len(rows)==6
 (out/'VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'source_commit':rev,'public_files':len(rows)}))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc());raise
