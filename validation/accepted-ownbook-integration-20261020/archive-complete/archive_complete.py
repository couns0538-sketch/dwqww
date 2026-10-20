#!/usr/bin/env python3
"""Preserve completed accepted-lineage OwnBook originals; no engine/Git writes."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,stat,sys

REPO=Path('/workspace/dwqww')
EVIDENCE=REPO/'validation/accepted-ownbook-integration-20261020'
OUT=EVIDENCE/'archive-complete'
STAGE=Path('/workspace/.cloud-setup/accepted-ownbook-integration-complete-evidence-stage')
ARCHIVER=REPO/'.github/hosted-tt-strength/archive_results.py'
TRUSTED='952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
NAME='forge-accepted-ownbook-356e863-5101c25-20261020-complete'
SPLIT=67108864

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def row(group,path):
 assert path.is_file() and not path.is_symlink(),path
 a=path.stat();digest=sha(path);b=path.stat()
 assert (a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_size,b.st_mtime_ns,b.st_ctime_ns),path
 return {'group':group,'original':str(path),'payload_path':'payload/'+str(path).lstrip('/'),'size':a.st_size,'sha256':digest,'mode':stat.S_IMODE(a.st_mode),'mtime_ns':a.st_mtime_ns}
def inventory(roots):
 files=[];dirs=[]
 for group,root in roots:
  assert root.is_dir() and not root.is_symlink(),root
  for directory,names,leaves in os.walk(root,followlinks=False):
   parent=Path(directory);names[:]=sorted(n for n in names if parent/n!=OUT)
   assert not parent.is_symlink(),parent
   dirs.append({'group':group,'original':str(parent),'payload_path':'payload/'+str(parent).lstrip('/'),'mode':stat.S_IMODE(parent.stat().st_mode)})
   for n in names:assert not (parent/n).is_symlink(),parent/n
   files.extend(row(group,parent/n) for n in sorted(leaves))
 files.append(row('trusted-archiver',ARCHIVER));files.sort(key=lambda r:r['payload_path']);dirs.sort(key=lambda r:r['payload_path'])
 assert len({r['payload_path'] for r in files})==len(files)
 return {'files':files,'directories':dirs}
def verify_originals():
 manifest=load(EVIDENCE/'EVIDENCE-SHA256.json');assert len(manifest)==76
 for name,r in manifest.items():assert sha(EVIDENCE/name)==r['sha256'] and (EVIDENCE/name).stat().st_size==r['bytes'],name
 assert load(EVIDENCE/'FINAL-VERIFY.json')['status']=='PASS_EVIDENCE_STABLE'
 assert load(EVIDENCE/'independent-audit.json')['status']=='passed'
 for label in ['baseline','candidate']:
  m=load(EVIDENCE/(label+'-source.json'));root=Path(m['root'])
  actual={p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in root.rglob('*') if p.is_file()}
  assert actual=={n:{'sha256':r['sha256'],'bytes':r['bytes']} for n,r in m['files'].items()}
 for profile in ['baseline-release','candidate-release','candidate-asan']:
  r=load(EVIDENCE/(profile+'-attempt1/RESULTS.json'));assert r['status']=='PASS'
  build=Path('/workspace/.cloud-setup')/('accepted-ownbook-'+profile)
  for name,item in r['after']['build'].items():
   if item is not None:assert sha(build/name)==item['sha256'] and (build/name).stat().st_size==item['bytes']
 return sha(EVIDENCE/'EVIDENCE-SHA256.json')

def main():
 assert sys.dont_write_bytecode,'Use Python-B / PYTHONDONTWRITEBYTECODE=1'
 assert sys.argv[1:]==['--preserve-originals']
 assert not STAGE.exists() and not (OUT/'RESULTS.json').exists(),'Never reuse/overwrite an archive attempt'
 assert sha(ARCHIVER)==TRUSTED
 scope=load(OUT/'INPUT-SCOPE.json');roots=[(r['group'],Path(r['path'])) for r in scope['directory_roots']]
 original_manifest_sha=verify_originals();before=inventory(roots);save(OUT/'LIVE-BEFORE.json',before)
 STAGE.mkdir()
 for r in before['directories']:
  p=STAGE/r['payload_path'];p.mkdir(parents=True,exist_ok=True);p.chmod(r['mode'])
 for r in before['files']:
  source=Path(r['original']);dest=STAGE/r['payload_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
  assert dest.stat().st_ino!=source.stat().st_ino and sha(dest)==r['sha256'] and dest.stat().st_size==r['size']
  assert stat.S_IMODE(dest.stat().st_mode)==r['mode']
 after=inventory(roots);save(OUT/'LIVE-AFTER-STAGING.json',after);assert after==before,'Originals changed during copying'
 assert verify_originals()==original_manifest_sha
 provenance=STAGE/'archive-provenance';provenance.mkdir()
 for name in ['archive_complete.py','INPUT-SCOPE.json']:shutil.copy2(OUT/name,provenance/name)
 save(provenance/'LIVE-FILES-AND-MODES.json',before)
 command={'operation':'Unchanged trusted archive_results.archive_results and verify_archive APIs in one process','driver_command':[sys.executable,'-B',str(Path(__file__)),'--preserve-originals'],'archiver':str(ARCHIVER),'archiver_sha256':TRUSTED,'input':str(STAGE),'output':str(OUT),'name':NAME,'split_size_bytes':SPLIT,'excluded_to_prevent_recursion':[str(OUT)],'original_evidence_manifest_sha256':original_manifest_sha,'original_evidence_manifest_entries':76,'recorded_utc':utc(),'engine_executed':False,'tests_executed':False,'git_or_ignore_mutation':False,'authorization':'Root requested complete checkpoint of exact accepted OwnBook source/build/evidence originals; stable evidence unchanged.'}
 save(OUT/'ARCHIVE-COMMAND.json',command);save(provenance/'ARCHIVE-COMMAND.json',command)
 save(provenance/'COPY-CHECK.json',{'status':'PASS','all_original_files_bytes_sizes_modes_equal_staged_copies':True,'live_before_equals_after_staging':True,'files':len(before['files'])})
 spec=importlib.util.spec_from_file_location('trusted_archive_results',ARCHIVER);trusted=importlib.util.module_from_spec(spec);spec.loader.exec_module(trusted)
 manifest_path=trusted.archive_results(STAGE,OUT,NAME,SPLIT);manifest=trusted.verify_archive(manifest_path)
 archived={r['path']:r for r in manifest['files']}
 staged={p.relative_to(STAGE).as_posix():{'size':p.stat().st_size,'sha256':sha(p)} for p in STAGE.rglob('*') if p.is_file()}
 assert set(archived)==set(staged)
 assert all((archived[n]['sha256'],archived[n]['size'])==(r['sha256'],r['size']) for n,r in staged.items())
 for r in before['files']:
  got=archived[r['payload_path']];assert (got['sha256'],got['size'])==(r['sha256'],r['size'])
 after=inventory(roots);save(OUT/'LIVE-AFTER-ARCHIVE.json',after);assert after==before,'Originals changed during archival verification'
 assert verify_originals()==original_manifest_sha and sha(ARCHIVER)==TRUSTED
 counts={g:sum(r['group']==g for r in before['files']) for g in sorted({r['group'] for r in before['files']})}
 receipt={'status':'PASS_COMPLETE_ACCEPTED_OWNBOOK_ORIGINALS_ARCHIVE','completed_utc':utc(),'baseline_commit':'356e863dbd86d2ce24b8ee9486d7406f1d525480','candidate_commit':'5101c2529d386b7c3a04ba9156a69ee34df6bb43','archive':manifest['archive'],'manifest':str(manifest_path),'manifest_sha256':sha(manifest_path),'parts':manifest['parts'],'split_size_bytes':SPLIT,'live_file_counts':counts,'live_file_count':len(before['files']),'live_bytes':sum(r['size'] for r in before['files']),'archive_payload_file_count':len(archived),'archive_payload_bytes':sum(r['size'] for r in archived.values()),'original_evidence_manifest_sha256':original_manifest_sha,'stable_original76records_and_manifest_unchanged':True,'all_sources_builds_engines_core_configs_original_ctest_logs_included':True,'live_before_after_copy_after_archive_identical':True,'copied_file_hashes_sizes_modes_verified':True,'reassembled_archive_every_payload_hash_verified':True,'originals_and_stage_retained':True,'engine_executed':False,'tests_executed':False,'git_or_ignore_mutation':False,'archiver_sha256':TRUSTED,'scope':'Durable complete local correctness evidence; does not integrate accepted branches or establish strength/performance.'}
 save(OUT/'RESULTS.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':
 try:main()
 except BaseException as exc:
  if not (OUT/'FAILURE.json').exists():save(OUT/'FAILURE.json',{'status':'FAILED_ATTEMPT_RETAINED','error_type':type(exc).__name__,'error':str(exc),'recorded_utc':utc(),'originals_and_partial_stage_retained':True,'engine_executed':False})
  raise
