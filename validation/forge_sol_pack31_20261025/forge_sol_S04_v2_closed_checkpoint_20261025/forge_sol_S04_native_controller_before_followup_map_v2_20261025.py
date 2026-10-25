#!/usr/bin/env python3
"""Current merged-test qualification with explicit, qualified S04 cache reuse."""
from pathlib import Path
import argparse,base64,datetime,gzip,hashlib,json,os,re,shlex,shutil,subprocess,traceback

P=Path(__file__).resolve().parent
H=P.parent/'S04'
PACK=P.parent/'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
CM=Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake')
CT=CM.with_name('ctest')
PATCH=P/'forge_sol_S04_source_checkpoint_v2_20261025/forge_sol_S04_v2_20261025.patch'
PATCH_SHA='b425157e6e9521a544e3612f3c32c3955bb1fd3195735692975d5a6d6d89590b'
TEST_SHA='55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c'
BASES={'Lp':PACK/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':PACK/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}
FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2)+'\n')
def blob(b):return {'encoding':'base64','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'data':base64.b64encode(b).decode()}
def inventory(root,folders):return {str(f.relative_to(root)):sha(f) for folder in folders for f in (root/folder).rglob('*') if f.is_file()}
def overlay(base):
 src=BASES[base];dst=P/f'forge_sol_S04_current_{base}_source_v2_20261025'
 patched=P/f'forge_sol_S04_patchwork_retry_v2_20261025/forge_sol_S04_new_{base}_v2_20261025'
 if dst.exists():
  assert sha(dst/'tests/tests.cpp')==TEST_SHA
  return dst
 dst.mkdir()
 for f in src.iterdir():
  if f.name in {'src','tests'}:
   (dst/f.name).mkdir()
   for q in f.iterdir():(dst/f.name/q.name).symlink_to(q,target_is_directory=q.is_dir())
  else:(dst/f.name).symlink_to(f,target_is_directory=f.is_dir())
 for rel in ['CMakeLists.txt','IDEA_SOURCE.md','src/bitboard.cpp','tests/forge_sol_S04_tsan_test_20261025.cpp']:
  target=dst/rel
  if target.is_symlink():target.unlink()
  target.write_bytes((patched/rel).read_bytes())
 assert sha(dst/'tests/tests.cpp')==TEST_SHA
 old=H/f"forge_sol_S04_{'L' if base=='Lp' else 'B'}_source_20261025"
 assert inventory(dst,['src','include'])==inventory(old,['src','include'])
 return dst
def archive_map():
 result={}
 for name in ['fourth','fifth']:
  path=P.parent/f'forge_sol_S00_{name}_space_20261025/forge_sol_S00_{name}_cache_restore_map_20261025.json'
  for row in json.loads(path.read_text())['files']:
   if '/S04/' in row['path']:result[row['path']]=row
 return result
def flags_make(path):
 text=Path(path).read_text();out={}
 for key in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']:
  match=re.search(r'^'+key+r' = (.*)$',text,re.M);assert match,key;out[key]=match[1]
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--case',choices=[f'{b}:{p}:{o}' for b in BASES for p in ['release','asan'] for o in ['OFF','ON']]);ap.add_argument('--cache-root',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--min-free-mib',type=int,default=16);args=ap.parse_args()
 assert sha(PATCH)==PATCH_SHA
 if args.prepare_only:
  rows=[]
  for base in BASES:
   src=overlay(base);rows.append({'base':base,'source':str(src),'production_source_hashes':inventory(src,['src','include']),'current_tests_sha256':sha(src/'tests/tests.cpp')})
  dump(P/'forge_sol_S04_prepared_sources_v2_20261025.json',{'status':'PREPARED_NO_NATIVE_EXECUTION','patch_sha256':PATCH_SHA,'profiles_planned':8,'rows':rows});print('PREPARED_NO_NATIVE_EXECUTION');return
 assert args.case and args.cache_root
 base,profile,option=args.case.split(':');oldbase='L' if base=='Lp' else 'B';oldroot=H/f'forge_sol_S04_{oldbase}_{profile}_{option}_20261025';oldbuild=oldroot/'build';oldreceipt=json.loads((oldroot/'forge_sol_S04_native_receipt_20261025.json').read_text());src=overlay(base)
 out=args.out or P/f'forge_sol_S04_{base}_{profile}_{option}_native_v2_20261025';out.mkdir(exist_ok=False);record={'status':'INCOMPLETE','base':base,'profile':profile,'option':option,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controller_sha256':sha(Path(__file__)),'commands':[],'source':str(src),'current_tests_sha256':TEST_SHA,'qualification_scope':'Fresh current tests.cpp + actual current CMake registration/full CTest, qualified old production core/main/helpers; ON dedicated cold TSan target built fresh; no fresh full-target engine rebuild','production_source_hashes':inventory(src,['src','include'])}
 def save():dump(out/'forge_sol_S04_current_native_receipt_v2_20261025.json',record)
 def run(label,argv,stdin=None,cwd=None):
  env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';proc=subprocess.run([str(x) for x in argv],input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=cwd,env=env);r={'label':label,'argv':[str(x) for x in argv],'cwd':str(cwd) if cwd else None,'child_environment_override':{'PYTHONDONTWRITEBYTECODE':'1'},'stdin':blob(stdin) if stdin is not None else None,'exit_code':proc.returncode,'stdout':blob(proc.stdout),'stderr':blob(proc.stderr)};record['commands'].append(r);save();return proc
 try:
  assert shutil.disk_usage(P).free>=args.min_free_mib*(1<<20),'Insufficient free space before profile'
  historical_source=H/f'forge_sol_S04_{oldbase}_source_20261025';support_hashes={}
  for folder in ['tests','tools','bench']:
   for historical in (historical_source/folder).rglob('*'):
    if not historical.is_file() or '__pycache__' in historical.parts:continue
    rel=historical.relative_to(historical_source)
    if str(rel)=='tests/tests.cpp':continue
    assert sha(src/rel)==sha(historical),('Support source or fixture drift',str(rel));support_hashes[str(rel)]=sha(src/rel)
  record['unchanged_support_source_and_fixture_hashes']=support_hashes
  maps=archive_map();artifacts=[]
  def artifact(name):
   original=oldbuild/name;expected=maps.get(str(original));candidates=[original]
   candidates += [f for f in args.cache_root.rglob(name) if oldroot.name in f.parts]
   actual=next((f for f in candidates if f.is_file()),None);assert actual,('Missing qualified artifact',original)
   actual_sha=sha(actual)
   if expected:assert actual_sha==expected['sha256'],(name,actual_sha,expected['sha256'])
   elif name=='forge':assert actual_sha==oldreceipt['engine_sha256']
   elif 'tsan' in name:assert name=='forge_sol_S04_cold_tsan_test_20261025'
   else:raise AssertionError(('No archived exact identity',name))
   artifacts.append({'name':name,'actual_path':str(actual),'original_path':str(original),'sha256':actual_sha,'bytes':actual.stat().st_size,'archived_original_identity':expected});return actual
  exe=artifact('forge');core=artifact('libforge_core.a');record['engine_sha256']=sha(exe)
  # The first current revalidation invocation is bare OFF d11, before UCI/options.
  first=run('first_bare_d11',[exe],b'bench 11\nquit\n');assert first.returncode==0 and re.search(rb'(?m)^(?:info string )?bench depth 11 nodes 308972 ',first.stdout)
  build=out/'build';configure=[CM,'-S',src,'-B',build,'-DCMAKE_BUILD_TYPE='+('Release' if profile=='release' else 'RelWithDebInfo'),'-DCMAKE_CXX_FLAGS='+FLAGS,'-DFORGE_ATTACKS_INIT_ONCE='+option]
  if profile=='asan':configure+=['-DFORGE_ENABLE_SANITIZERS=ON','-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O1 -g1 -DNDEBUG']
  assert run('configure_current_cmake',configure).returncode==0
  proofs=[]
  for target in ['forge_core','forge','forge_tests']+(['forge_sol_S04_cold_tsan_test_20261025'] if option=='ON' else []):
   oldflags=flags_make(oldbuild/f'CMakeFiles/{target}.dir/flags.make');newflags=flags_make(build/f'CMakeFiles/{target}.dir/flags.make')
   assert oldflags['CXX_DEFINES']==newflags['CXX_DEFINES'] and oldflags['CXX_FLAGS']==newflags['CXX_FLAGS']
   assert oldflags['CXX_INCLUDES'].replace(str(H/f'forge_sol_S04_{oldbase}_source_20261025'),str(src))==newflags['CXX_INCLUDES']
   proofs.append({'target':target,'old_flags_file':blob((oldbuild/f'CMakeFiles/{target}.dir/flags.make').read_bytes()),'new_flags_file':blob((build/f'CMakeFiles/{target}.dir/flags.make').read_bytes()),'exact_flags_and_defines_equal':True,'only_include_root_differs':True})
  members=[]
  for tu in ['bitboard','board','book','eval','eval_params','nnue','search']:
   obj=oldbuild/f'CMakeFiles/forge_core.dir/src/{tu}.cpp.o';expected=maps.get(str(obj));assert expected,('No core object identity',obj)
   argv=['ar','p',str(core),tu+'.cpp.o'];process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);digest=hashlib.sha256();length=0
   for chunk in iter(lambda:process.stdout.read(1<<20),b''):digest.update(chunk);length+=len(chunk)
   stderr=process.stderr.read();exitcode=process.wait();assert exitcode==0 and digest.hexdigest()==expected['sha256']
   members.append({'tu':tu,'argv':argv,'exit_code':exitcode,'stdout_original_external_bytes':{'archive':str(core),'member':tu+'.cpp.o','bytes':length,'sha256':digest.hexdigest()},'stderr':blob(stderr),'object_sha256':expected['sha256'],'archived_object_identity':expected,'current_source_sha256':sha(src/f'src/{tu}.cpp')})
  record['core_reuse_proof']={'flags':proofs,'members':members,'all_current_source_include_exact_historical_candidate':True,'historical_system_header_byte_identity':'UNVERIFIED; no historical header snapshot claimed'}
  f=flags_make(build/'CMakeFiles/forge_tests.dir/flags.make');cpp=src/'tests/tests.cpp';obj=out/'forge_sol_S04_current_tests_v2_20261025.o';testexe=out/'forge_sol_S04_current_tests_v2_20261025.elf'
  compiler=['/usr/bin/c++']+shlex.split(f['CXX_DEFINES'])+shlex.split(f['CXX_INCLUDES'])+shlex.split(f['CXX_FLAGS'])
  assert run('compile_current_tests',compiler+['-MD','-MF',out/'forge_sol_S04_current_tests_v2_20261025.d','-c',cpp,'-o',obj]).returncode==0
  link=shlex.split((build/'CMakeFiles/forge_tests.dir/link.txt').read_text());link=[str(obj) if x=='CMakeFiles/forge_tests.dir/tests/tests.cpp.o' else str(testexe) if x=='forge_tests' else str(core) if x=='libforge_core.a' else x for x in link]
  assert run('link_current_tests',link,cwd=build).returncode==0
  record['fresh_current_test_elf_sha256']=sha(testexe)
  direct=run('current_cpp_known4',[testexe]);lines=(direct.stdout+b'\n'+direct.stderr).decode(errors='replace').splitlines();known=[x for x in lines if x.startswith('KNOWN_FAILURE:')];bad=[x for x in lines if x.startswith(('FAIL:','PIN_MISMATCH:'))];assert direct.returncode==0 and len(known)==4 and not bad,(direct.returncode,known,bad);record['current_known_failure_lines']=known
  if option=='ON':
   assert run('build_current_cold_tsan_target',[CM,'--build',build,'--target','forge_sol_S04_cold_tsan_test_20261025','--parallel','2']).returncode==0
   record['fresh_cold_tsan_executable_sha256']=sha(build/'forge_sol_S04_cold_tsan_test_20261025')
  # Rewrite only native executable locations in generated current CMake test harness.
  ctestfile=build/'CTestTestfile.cmake';original=ctestfile.read_text();patched=original;rewrites=[]
  for target in re.findall(r'add_test\([^\s]+ "([^"]+)"',original):
   path=Path(target)
   if path.parent!=build:continue
   name=path.name
   replacement=testexe if name=='forge_tests' else exe if name=='forge' else path if name=='forge_sol_S04_cold_tsan_test_20261025' else artifact(name)
   patched=patched.replace('"'+target+'"','"'+str(replacement)+'"');rewrites.append({'configured_path':target,'executed_path':str(replacement),'sha256':sha(replacement)})
  # Engine paths can also appear as arguments of the Python UCI regressions.
  patched=patched.replace('"'+str(build/'forge')+'"','"'+str(exe)+'"')
  (out/'forge_sol_S04_generated_ctest_original_v2_20261025.cmake').write_text(original);ctestfile.write_text(patched);record['harness_rewrites']=rewrites;record['qualified_artifacts']=artifacts
  listed=run('current_ctest_list',[CT,'--test-dir',build,'-N']);expected_total=(14 if base=='Lp' else 15)+(option=='ON');assert listed.returncode==0 and re.search(fr'Total Tests: {expected_total}\b'.encode(),listed.stdout);assert (b'forge_sol_S04_cold_tsan_test_20261025' in listed.stdout)==(option=='ON')
  if option=='ON':
   linktext=(build/'CMakeFiles/forge_sol_S04_cold_tsan_test_20261025.dir/link.txt').read_text();assert '-fsanitize=thread' in linktext and '-fsanitize=address' not in linktext and 'forge_core' not in linktext;record['independent_cold_tsan_link']=blob(linktext.encode())
  ctest=run('current_full_ctest',[CT,'--test-dir',build,'--output-on-failure','-j','1']);assert ctest.returncode==0 and re.search(fr'100% tests passed, 0 tests failed out of {expected_total}\b'.encode(),ctest.stdout)
  last=(build/'Testing/Temporary/LastTest.log').read_bytes();record['complete_last_test_log']=blob(last)
  diagnostics=re.findall(rb'(?im)^.*(?:ERROR: AddressSanitizer|WARNING: ThreadSanitizer|runtime error:|UndefinedBehaviorSanitizer).*$' ,last);assert not diagnostics,diagnostics
  record['ctest_total']=expected_total;record['cold_tsan_registered']=(option=='ON');record['fixed_refs_perft_fma_scope']='Inherited only through exact production source/include, original qualified engine SHA and old raw qualification receipt; fresh bare d11 above'
  record['inherited_closed_receipt']={'path':str(oldroot/'forge_sol_S04_native_receipt_20261025.json'),'sha256':sha(oldroot/'forge_sol_S04_native_receipt_20261025.json'),'old_source_hashes':oldreceipt['source_hashes'],'qualification_status':oldreceipt['status']}
  record['status']='PASS_CURRENT_KNOWN4_FULL_CTEST_WITH_QUALIFIED_ENGINE_REUSE';record['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(base,profile,option,record['status'],flush=True)
 except BaseException as exc:
  record['error']=str(exc);record['traceback']=traceback.format_exc();save();raise
if __name__=='__main__':main()
