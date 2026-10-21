from pathlib import Path
import io,json,subprocess,hashlib,re
R=Path('/workspace/dwqww');D=R/'validation/hosted-pv-metadata-strength-20261021/final-audit';B=Path('/workspace/.cloud-setup/pv-metadata-result-39528641493/extracted/files');cfg=json.loads((B/'package/protocol.json').read_text());payload='452a4a9ca96afd7356c8dadc2203efd41c162e47'
objects={n:B/'proofs'/n for n in cfg['correctness_evidence_sha256']}
for p in (B/'package').rglob('*'):
 if p.is_file():objects['.github/hosted-pv-metadata-strength/'+p.relative_to(B/'package').as_posix()]=p
objects['.github/workflows/forge-hosted-pv-metadata-strength.yml']=B/'workflow.yml';objects['tools/match/windows_validate.py']=B/'windows_validate.py'
request=''.join(payload+':'+n+'\n' for n in objects).encode();p=subprocess.run(['git','cat-file','--batch'],cwd=R,input=request,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);assert not p.stderr;f=io.BytesIO(p.stdout)
for name,path in objects.items():
 header=f.readline().decode().strip().split();assert len(header)==3 and header[1]=='blob',(name,header)
 raw=f.read(int(header[2]));assert f.read(1)==b'\n';assert raw==path.read_bytes(),name
assert not f.read()
print('authentic fixedpayload exactGit',len(objects),flush=True)
counts={}
for phase,cap in [('aa',8),('sprt',1024)]:
 text=(B/'strength'/phase/'console.txt').read_text();started=[int(n) for n in re.findall(r'^Started game (\d+) of \d+',text,re.M)];finished=[int(n) for n in re.findall(r'^Finished game (\d+) ',text,re.M)]
 assert started==list(range(1,cap+1)) and sorted(finished)==started
 llr=[float(x) for x in re.findall(r'^LLR:\s*([^\s]+)',text,re.M)]
 counts[phase]={'started':len(started),'finished':len(finished),'unclosed':0,'native_printed_llr_range':None if not llr else [min(llr),max(llr)]}
final=json.loads((B/'proofs/validation/pv-metadata-native-20261021/FINAL-RECEIPT.json').read_text());assert final['status']=='STABLE' and final['source_commit']==cfg['candidate_sha'];assert final['source_export_files']==77 and final['native_ctests']==42 and final['default_tsan_active_checks']==8 and final['pv_metadata_assertions_each_profile']==56
original=(B/'package/build_evidence.py').read_text();assert 'not path.stat().st_mode & 0o111 or not os.access(path,os.X_OK)' in original
assert json.loads((B/'strength/preflight-evidence.json').read_text())['status']=='passed'
supp={'status':'PASS','fixed_public_payload_commit':payload,'payload_git_blobs_verified':len(objects),'normal_completion':counts,'candidate_native_actual':{'source':final['source_commit'],'source_files':77,'ctests':42,'active_uci':8,'pv_assertions_each':56},'mode_limitation':'Original ZIP raw members0600 cannot replay original executable modes. Original archived checker requires bits and X_OK, actual preflight passed and normal readiness+games prove execution. No explicit original postrun numeric permission rows are asserted; original final input hashes prove bytes. Data-only archive adapter omits only this relocated-mode predicate, never an original live or operational gate.','aa_scope':'Actual frozen22 is four TIMED operational baseline/baseline pairs1+0.01; no identical-game or Elo-zero gate.','proof_binding':'All original correctness proofs, package files, workflow and windows_validate.py match genuine sole public trigger payloadGit exactly.'}
(D/'SUPPLEMENT.json').write_text(json.dumps(supp,indent=2)+'\n');print('SUPPLEMENT PASS',hashlib.sha256((D/'SUPPLEMENT.json').read_bytes()).hexdigest())
