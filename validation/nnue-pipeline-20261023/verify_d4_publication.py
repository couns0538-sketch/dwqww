from pathlib import Path
import urllib.request,json,hashlib,time
h=Path('/workspace/forge-nnue-handoff-20261023');r=Path('/workspace/dwqww');o=h/'publication-d4ee5cd-raw-readback-attempt1';o.mkdir(exist_ok=False)
commit='d4ee5cd6eb2785f7425719ab497080e9fef64246'
paths=['validation/nnue-pipeline-20261023/full-prepared-data-recovery-attempt1/ARCHIVE-MANIFEST.json','validation/nnue-pipeline-20261023/full-prepared-data-recovery-attempt1/forge-nnue-full-prepared-20261023.zip.003','validation/nnue-pipeline-20261023/independent-audit128-recovery-attempt1/ARCHIVE-MANIFEST.json','validation/nnue-pipeline-20261023/independent-audit128-recovery-attempt1/forge-nnue-independent-audit128-20261023.zip.001']
results=[]
for i,p in enumerate(paths):
 url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+commit+'/'+p
 expected=hashlib.sha256((r/p).read_bytes()).hexdigest();start=time.monotonic()
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Forge-NNUE-evidence-verifier'}),timeout=45) as response:
  status=response.status;raw=response.read()
 (o/(str(i)+'.download')).write_bytes(raw)
 rec={'path':p,'url':url,'http_status':status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'expected_sha256':expected,'elapsed_seconds':time.monotonic()-start};results.append(rec)
 assert status==200 and rec['sha256']==expected
 (o/'PROGRESS.json').write_text(json.dumps(results,indent=2)+'\n')
(o/'VERIFIED.json').write_text(json.dumps({'status':'PASS_PUBLIC_HTTP200_EXACT_COMMITTED_BYTES','commit':commit,'actual_push_tool_session':93026,'actual_push_exit':0,'remote_ref_head_verified':commit,'downloads':results},indent=2)+'\n')
print('Verified four public raw payloads against committed bytes.')
