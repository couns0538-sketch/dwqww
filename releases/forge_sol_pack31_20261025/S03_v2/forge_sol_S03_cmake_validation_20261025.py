#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,shutil,subprocess
h=Path(__file__).resolve().parent;cmake=Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake');ctest=cmake.with_name('ctest');all_results=[]
def call(argv,q,name):
 p=subprocess.run([str(x) for x in argv],stdout=subprocess.PIPE,stderr=subprocess.PIPE);(q/(name+'.stdout')).write_bytes(p.stdout);(q/(name+'.stderr')).write_bytes(p.stderr);(q/(name+'.json')).write_text(json.dumps({'argv':[str(x) for x in argv],'actual_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},indent=2)+'\n');return p
for label in ['L','B']:
 source=h/f'forge_sol_S03_{label}_source_20261025';base=Path(f'/workspace/forge-pack24-20261025/forge_sol_S00_{label}_release_20261025/build');q=h/f'forge_sol_S03_{label}_cmake_20261025';q.mkdir(exist_ok=False);off=q/'off';on=q/'on'
 for mode,build in [('OFF',off),('ON',on)]:
  p=call([cmake,'-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256','-DFORGE_FIXED_REFERENCES='+mode],q,'forge_sol_S03_configure_'+mode+'_20261025');assert p.returncode==0
  if mode=='ON':
   binaries={}
   for f in base.iterdir():
    if f.is_file() and f.suffix=='' and f.name.startswith('forge'):
     original=f
     if f.name=='forge_tests':original=Path(f'/workspace/forge-pack24-20261025/forge_sol_S01_full_matrix_20261025/forge_sol_S01_saved_{label}_release_20261025/forge_sol_S01_original_tests_20261025.elf')
     shutil.copyfile(original,build/f.name);(build/f.name).chmod(0o700);binaries[f.name]={'original':str(original),'sha256':hashlib.sha256(original.read_bytes()).hexdigest()};assert hashlib.sha256((build/f.name).read_bytes()).hexdigest()==binaries[f.name]['sha256']
   (q/'forge_sol_S03_reused_binaries_20261025.json').write_text(json.dumps({'scope':'Original completed Release ELF files reused byte-for-byte; original four-FAIL forge_tests restored only in private S03build. No parent build source/binary is modified.','files':binaries},indent=2)+'\n')
  p=call([ctest,'--test-dir',build,'-N'],q,'forge_sol_S03_list_'+mode+'_20261025');assert p.returncode==0;present=b'forge_fixed_references' in p.stdout;assert present==(mode=='ON')
 p=call([ctest,'--test-dir',on,'--output-on-failure','-j1'],q,'forge_sol_S03_full_ctest_20261025');assert p.returncode==8,p.returncode
 text=p.stdout.decode();assert 'forge_fixed_references' in text and '1 tests failed' in text and 'forge_tests (Failed)' in text
 fails=[s.strip() for s in text.splitlines() if s.strip().startswith('FAIL:')];expected=['FAIL: WAC 001 expected g3g6 got f6h5','FAIL: WAC 001 score 661 below 31997','FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion','FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion'];assert sorted(fails)==sorted(expected),fails
 row={'base':label,'status':'PASS_FIXED_SUITE_AND_ONLY_FOUR_ORIGINAL_KNOWN_FAILURE_LINES','cmake_option_default_off':True,'OFF_has_new_ctest':False,'ON_has_new_ctest':True,'ctest_total':15 if label=='L' else 16,'actual_ctest_exit':p.returncode,'only_failed_target':'forge_tests','known_fail_lines':fails,'main_engine_sha256':hashlib.sha256((on/'forge').read_bytes()).hexdigest(),'main_engine_identical_to_common':(on/'forge').read_bytes()==(base/'forge').read_bytes()};all_results.append(row);(h/'forge_sol_S03_cmake_results_20261025.json').write_text(json.dumps({'status':'PASS','profiles':all_results,'sanitizer_scope':'No new fixed-reference suite run under ASan in this controller; original unchanged common sanitizer suite results remain separate.'},indent=2)+'\n');print(label,'CMAKE_OFF_ON_AND_FULL_CTEST_POLICY_PASS',flush=True)
