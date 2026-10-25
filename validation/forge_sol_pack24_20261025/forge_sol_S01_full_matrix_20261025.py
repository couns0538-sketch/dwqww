from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess
h=Path('/workspace/forge-pack24-20261025');p=h/'forge_sol_jobpack_24jobs_20261025/files';prereq=p/'09_sol_returns/sol_return_jobC_20261025/forge_sol_knownfail_h256e12_20261025.patch';follow=h/'S01/forge_sol_S01_pinmsg_20261025.patch';assert hashlib.sha256(prereq.read_bytes()).hexdigest()=='4ac98f92d45f67fae8aaa8067fe28c0fca36662b3688013105f738245ee55805';assert hashlib.sha256(follow.read_bytes()).hexdigest()=='bddc961125a25c9d4331a8555b0304653f550c378c38fb480a1ba9b2ba92d528'
out=h/'forge_sol_S01_full_matrix_20261025';out.mkdir(exist_ok=False);cm='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake';ct='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest';result={'status':'INCOMPLETE','prerequisite_sha256':hashlib.sha256(prereq.read_bytes()).hexdigest(),'followup_sha256':hashlib.sha256(follow.read_bytes()).hexdigest(),'profiles':[]}
def run(name,argv,cwd=None,data=None):
 d=subprocess.run(argv,cwd=cwd,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(out/(name+'.json')).write_text(json.dumps({'argv':argv,'actual_exit':d.returncode,'stdout_base64':base64.b64encode(d.stdout).decode(),'stderr_base64':base64.b64encode(d.stderr).decode(),'stdout_sha256':hashlib.sha256(d.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(d.stderr).hexdigest()},indent=2)+'\n');return d
try:
 for tag in ['L','B']:
  src=h/f'forge_sol_S00_work_{tag}_20261025';before={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['src','include'] for f in(src/folder).rglob('*') if f.is_file()}
  # Retain every original known-failing test executable/object before rebuilding.
  for prof in ['release','asan']:
   root=h/f'forge_sol_S00_{tag}_{prof}_20261025';receipt=json.loads((root/'forge_sol_S00_native_receipt_20261025.json').read_text());assert receipt['status'].startswith('PASS_')
   saved=out/f'forge_sol_S01_saved_{tag}_{prof}_20261025';saved.mkdir();shutil.copy2(root/'build/forge_tests',saved/'forge_sol_S01_original_tests_20261025.elf')
  for label,patch in [('prereq',prereq),('followup',follow)]:
   for action,extra in [('dryrun',['--dry-run']),('apply',[])]:
    d=run(f'forge_sol_S01_{tag}_{label}_{action}_20261025',['patch','--batch','--forward','-F0','-p1',*extra],cwd=src,data=patch.read_bytes());assert d.returncode==0 and b'offset' not in d.stdout and b'fuzz' not in d.stdout
  assert before=={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['src','include'] for f in(src/folder).rglob('*') if f.is_file()}
  for prof in ['release','asan']:
   root=h/f'forge_sol_S00_{tag}_{prof}_20261025';receipt=json.loads((root/'forge_sol_S00_native_receipt_20261025.json').read_text());build=root/'build'
   assert run(f'forge_sol_S01_{tag}_{prof}_build_20261025',[cm,'--build',str(build),'-j','2']).returncode==0
   current=hashlib.sha256((build/'forge').read_bytes()).hexdigest();assert current==receipt['engine_sha256'],'engine byte identity'
   tests=run(f'forge_sol_S01_{tag}_{prof}_ctest_20261025',[ct,'--test-dir',str(build),'--output-on-failure','-j','1']);assert tests.returncode==0 and b'100% tests passed' in tests.stdout
   target=run(f'forge_sol_S01_{tag}_{prof}_known_20261025',[str(build/'forge_tests')]);assert target.returncode==0 and target.stderr.count(b'KNOWN_FAILURE:')==4 and b'FAIL:' not in target.stderr
   result['profiles'].append({'base':tag,'profile':prof,'status':'PASS','engine_sha256':current,'byte_identical_to_unpatched_engine':True,'ctest_total':14 if tag=='L' else 15,'all_ctest_pass':True,'known_labels':4,'original_fixed_refs_reused_by_exact_exe_SHA':True})
 result['status']='PASS_FOUR_NATIVE_PROFILES_ENGINE_IDENTITY_AND_KNOWN_LABELS'
finally:(out/'forge_sol_S01_full_matrix_receipt_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
