from pathlib import Path
import base64,gzip,hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parent;OUT=R/'forge_sol_S05_delivery_20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
for phase in ('release','asan'):assert load(R/f'forge_sol_S05_{phase}_final_evidence_20261025/forge_sol_S05_native_results_20261025.json')['status']=='PASS'
assert load(R/'forge_sol_S05_final_replay_evidence_20261025/forge_sol_S05_final_replay_results_20261025.json')['status']=='PASS'
assert load(R/'forge_sol_S05_private_probe_evidence_20261025/forge_sol_S05_probe_results_20261025.json')['status']=='PASS_FAULT_DETECTED'
assert load(R/'forge_sol_S05_source_identity_20261025.json')['status']=='PASS'
OUT.mkdir(exist_ok=False)
for name in ('forge_sol_S05_ctestwire_20261025.patch','forge_sol_S05_fmacheck_v3_20261025.py','forge_sol_S05_fmacheck_tests_20261025.py','forge_sol_S05_float_uci_20261025.py','forge_sol_S05_float_parity_20261025.cpp','forge_sol_S05_float_threads_20261025.cpp','forge_sol_S05_report_20261025.md','forge_sol_S05_checkpoint_20261025.md','forge_sol_S05_source_identity_20261025.json','forge_sol_S05_source_audit_20261025.py','forge_sol_S05_final_script_identity_20261025.json','forge_sol_S05_prebarrier_provenance_20261025.json','forge_sol_S05_private_probe_source_identity_20261025.json'):
 shutil.copyfile(R/name,OUT/name)
# Only receipts/logs/flags/proof snapshots; no copied engine source, arrays, objects, ELFs or private mutation generator.
files=set()
for name in ('forge_sol_S05_release_evidence_20261025','forge_sol_S05_release_final_evidence_20261025','forge_sol_S05_asan_final_evidence_20261025','forge_sol_S05_final_replay_evidence_20261025','forge_sol_S05_private_probe_evidence_20261025','forge_sol_S05_checker_red_20261025','forge_sol_S05_checker_green_20261025','forge_sol_S05_mask_red_20261025','forge_sol_S05_mask_green_20261025','forge_sol_S05_barrier_red_20261025','forge_sol_S05_barrier_green_20261025'):
 files.update((R/name).glob('*.json'))
for name in ('forge_sol_S05_ctestwire_v1_20261025.patch','forge_sol_S05_final_apply_results_20261025.json','forge_sol_S05_checker_red_20261025.txt','forge_sol_S05_checker_green_20261025.txt','forge_sol_S05_mask_red_20261025.txt','forge_sol_S05_mask_green_20261025.txt','forge_sol_S05_barrier_red_20261025.txt','forge_sol_S05_barrier_green_20261025.txt','forge_sol_S05_release_controller_20261025.txt','forge_sol_S05_release_final_controller_20261025.txt','forge_sol_S05_asan_final_controller_20261025.txt','forge_sol_S05_final_replay_controller_20261025.txt','forge_sol_S05_private_probe_controller_20261025.txt','forge_sol_S05_run_native_20261025.py','forge_sol_S05_run_native_final_20261025.py','forge_sol_S05_replay_final_tests_20261025.py','forge_sol_S05_private_probe_controller_20261025.py'):
 files.add(R/name)
for build in R.glob('forge_sol_S05_*_20261025'):
 if not build.is_dir() or not (build/'CMakeCache.txt').exists():continue
 for rel in ('Testing/Temporary/LastTest.log','Testing/Temporary/LastTestsFailed.log','uci-regression.log','ownbook-regression.json','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/flags.make','CMakeFiles/forge.dir/link.txt','CMakeFiles/forge_sol_S05_float_parity.dir/flags.make','CMakeFiles/forge_sol_S05_float_threads.dir/flags.make'):
  p=build/rel
  if p.is_file():files.add(p)
 for p in build.glob('forge_sol_S05_ctest_20261025_*/*.json'):files.add(p)
for base in ('L','B'):
 p=ROOT/f'S28/forge_sol_S28_native_v2_20261025/forge_sol_S28_{base}_lock_20261025/forge_sol_S28_results_20261025.json'
 files.add(p)
files={p for p in files if p.is_file()}
bundle=OUT/'forge_sol_S05_raw_evidence_20261025.jsonl.gz';index=[]
with bundle.open('xb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as stream:
  for p in sorted(files):
   data=p.read_bytes();row={'original_path':str(p.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};index.append(row)
   stream.write((json.dumps(dict(row,encoding='base64',data=base64.b64encode(data).decode()),sort_keys=True,separators=(',',':'))+'\n').encode())
observed=[]
with gzip.open(bundle,'rt') as stream:
 for line in stream:
  row=json.loads(line);data=base64.b64decode(row['data'],validate=True);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'];observed.append({k:row[k] for k in ('original_path','bytes','sha256')})
assert observed==index
(OUT/'forge_sol_S05_evidence_index_20261025.json').write_text(json.dumps({'status':'PASS','records':index,'count':len(index),'bundle':bundle.name,'bundle_sha256':sha(bundle),'scope':'Lossless original-file evidence. Includes failed unpublished prototype validation patch as evidence only, not a resubmitted candidate. Exact previous S28 control receipts anchor SHA-identical baseline reuse. Mutated engine source/generator, engine source copies, weights and binary/build products are not exported.'},indent=2)+'\n')
for p in OUT.iterdir():
 if p.is_file() and p.suffix!='.gz':assert bytes.fromhex('4f70656e4149') not in p.read_bytes(),p
names=sorted(p.name for p in OUT.iterdir() if p.is_file());m=OUT/'forge_sol_S05_SHA256SUMS_20261025.txt'
p=subprocess.run(['sha256sum','--',*names],cwd=OUT,capture_output=True,check=True);m.write_bytes(p.stdout)
p=subprocess.run(['sha256sum','-c',m.name],cwd=OUT,capture_output=True,check=True)
print(json.dumps({'status':'PASS','out':str(OUT),'files':len(names)+1,'raw_original_files':len(index),'bundle_sha256':sha(bundle),'manifest_sha256':sha(m),'inside_output_check_exit':p.returncode},indent=2))
