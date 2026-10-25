from pathlib import Path
import hashlib,json,shutil,datetime
r=Path('/workspace/dwqww');h=Path('/workspace/forge-jobACD-20261025');d=Path('/workspace/forge-jobACD-D-20261025');release=r/'releases/forge_sol_jobACD_20261025';v=r/'validation/forge_sol_jobACD_20261025';e=v/'forge_sol_jobD_evidence_20261025';e.mkdir(exist_ok=False)
for line in(d/'forge_sol_jobD_evidence_sha256_20261025.txt').read_text().splitlines():
 if not line or line.startswith('#'):continue
 digest,rel=line.split(None,1);rel=rel.strip();f=d/rel;assert hashlib.sha256(f.read_bytes()).hexdigest()==digest;target=e/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
shutil.copyfile(d/'forge_sol_jobD_evidence_sha256_20261025.txt',e/'forge_sol_jobD_evidence_sha256_20261025.txt')
# Preserve complete derived sample rows, not only prose counts; no ZIP generated.
for name in ['forge_sol_data32_filtered_off_20261025','forge_sol_data32_filtered_threshold300_20261025']:
 src=d/name;dst=e/name;dst.mkdir(exist_ok=True)
 for f in src.iterdir():
  if f.is_file():
   target=dst/f.name
   if target.exists():assert target.read_bytes()==f.read_bytes()
   else:shutil.copy2(f,target)
 for line in(dst/'forge_sol_datafilter_manifest_20261025.md5').read_text().splitlines():
  digest,name=line.split(None,1);assert hashlib.md5((dst/name.strip()).read_bytes()).hexdigest()==digest
for name in ['forge_sol_datafilter_20261025.py','forge_sol_datafilter_tests_20261025.py','forge_sol_jobD_report_20261025.md']:
 shutil.copyfile(d/name,release/name)
shutil.copyfile(h/'forge_sol_data32_cpu_smoke_20261025.py',release/'forge_sol_data32_cpu_smoke_20261025.py')
for name in ['forge_sol_v3b_filtered_load_20261025.py','forge_sol_v3b_filtered_load_20261025.json','forge_sol_v3b_filtered_load_20261025.stdout','forge_sol_v3b_filtered_load_20261025.stderr','forge_sol_realtext_alignment_20261025.json','forge_sol_data32_smoke_controller_20261025.stdout','forge_sol_data32_smoke_controller_20261025.stderr','forge_sol_data32_cpu_smoke_20261025.py','forge_sol_cpu_runtime_setup_20261025.json','forge_sol_cpu_import_20261025.json']:
 shutil.copyfile(h/name,e/name)
sm=h/'forge_sol_data32_cpu_smoke_run_20261025';dst=e/'forge_sol_cpu_smoke_20261025';dst.mkdir()
for f in sm.iterdir():
 if f.is_file():shutil.copyfile(f,dst/f.name)
# Freeze hashes of the actual disposable smoke exports without suggesting them as engine weights.
exports=[]
for f in(sm/'forge_sol_cpu_steps_20261025').iterdir():
 if f.is_file():exports.append({'name':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'purpose':'Three-step synthetic CPU smoke only, not trained engine release'})
(dst/'forge_sol_cpu_smoke_export_hashes_20261025.json').write_text(json.dumps(exports,indent=2)+'\n')
review=Path('/workspace/forge-jobACD-D-review-20261025');rv=e/'forge_sol_independent_review_20261025';rv.mkdir()
for f in review.iterdir():
 if f.is_file() and f.suffix in ['.json','.md','.py','.stdout','.stderr']:shutil.copyfile(f,rv/f.name)
# Whole deliverable identity manifest for D only; excludes itself.
names=['forge_sol_datafilter_20261025.py','forge_sol_datafilter_tests_20261025.py','forge_sol_jobD_report_20261025.md','forge_sol_data32_cpu_smoke_20261025.py']
(release/'forge_sol_jobD_sha256_20261025.txt').write_text(''.join(hashlib.sha256((release/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names))
cp=v/'forge_sol_jobACD_checkpoint_20261025.json';state=json.loads(cp.read_text());state.update({'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'D_COMPLETE_PUBLICATION_PENDING','D':'SAMPLE_VALIDATED21_TESTS_OFF200K_ON157666_ACTUAL_V3B_CPU3STEP_PASS','D_source_sha256':'6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3','D_real_013_014_overlap':'UNVERIFIED_ABSENT','D_synthetic_game_isolation':'UNVERIFIED_NO_ORDERED_TEXT','D_CPU_loss':0.029621,'live_jobs':[],'next':'Publish and verify independentJobD delivery, then save combinedreport/nextcheckpoint. No adoptedA speedgain, no Elo/traininggain claim; ownerrealholdout/textreview next.'});cp.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps({'D_copied_files':len([f for f in e.rglob('*') if f.is_file()]),'tool_sha256':hashlib.sha256((release/names[0]).read_bytes()).hexdigest(),'sample_raw_files_preserved':16}))
