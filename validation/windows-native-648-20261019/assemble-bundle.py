from pathlib import Path,PurePosixPath
import datetime,hashlib,importlib.util,json,os,re,shutil,subprocess,zipfile
REPO=Path('/workspace/dwqww');OLD=REPO/'releases/forge-6.4.2-windows-validation-bundle.zip';ZIP=REPO/'releases/forge-6.4.8-windows-validation-bundle.zip'
STAGE=Path('/workspace/.cloud-setup/forge-6.4.8-windows-validation-bundle with spaces');OUT=REPO/'validation/windows-native-648-20261019'
COMMIT='7125b3379a850de34041d42529cf95993607f93c';OLD_SHA='27022666ef6e9eb14ce5b84109810be3f6caa1d97a25066409f915dd0029367c';ENGINE_SHA='e39a240e3f7380e84c4e585013c2d602cba379f15e9e23d7a036a9712c415644'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
assert not STAGE.exists() and not ZIP.exists() and not OUT.exists()
assert sha(OLD)==OLD_SHA
OUT.mkdir(parents=True);STAGE.mkdir()
with zipfile.ZipFile(OLD) as z:
 assert z.testzip() is None
 oldprefix='forge-6.4.2-windows-validation-bundle/'
 original_manifest=json.loads(z.read(oldprefix+'manifest.json'));original_relative={}
 for info in z.infolist():
  assert info.filename.startswith(oldprefix)
  relative=PurePosixPath(info.filename.removeprefix(oldprefix));assert not relative.is_absolute() and '..' not in relative.parts
  if info.is_dir():continue
  data=z.read(info);target=STAGE/str(relative);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);original_relative[str(relative)]=hashlib.sha256(data).hexdigest()
assert set(original_manifest['files'])==set(original_relative)-{'manifest.json'}
assert all(original_relative[n]==h for n,h in original_manifest['files'].items())
# Remove superseded candidate source/build provenance and unused old optional test PE.
shutil.rmtree(STAGE/'sources/candidate-6.4.2')
for relative in ['engine/forge_tests.exe','provenance/candidate-6.4.2.json','provenance/candidate-source-files.json']:
 (STAGE/relative).unlink()
assert not any((STAGE/n).exists() for n in ['results','aa','pilot','sprt','state.json','result.json'])
engine=REPO/'releases/forge-6.4.8-candidate-windows-zen5/forge-6.4.8-ryzen-9850x3d.exe';assert sha(engine)==ENGINE_SHA
shutil.copyfile(engine,STAGE/'engine/candidate.exe')
# Include all frozen build/support inputs, including README/LICENSE and nested manifests.
env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
names=subprocess.check_output(['git','ls-tree','-r','--name-only',COMMIT,'--','CMakeLists.txt','README.md','LICENSE','include','src','tests','bench','tools'],cwd=REPO,env=env,text=True).splitlines()
source_dir=STAGE/'sources/candidate-6.4.8';source_map={}
for name in names:
 if name.endswith('.pyc'):continue
 data=subprocess.check_output(['git','show',COMMIT+':'+name],cwd=REPO,env=env)
 target=source_dir/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);source_map[name]=hashlib.sha256(data).hexdigest()
assert {'README.md','LICENSE','CMakeLists.txt','tests/legal_witness_fixtures.tsv','tests/legal_witness_tests.cpp','tools/openings/forge-10000.epd','tools/openings/manifest.json'}<=source_map.keys()
release=load(REPO/'releases/forge-6.4.8-candidate-windows-zen5/provenance.json')
runtime=load(REPO/'validation/root-effort-20261019/windows/runtime-attempt1/result.json')
assert runtime['status']=='passed' and len(runtime['checks'])==7 and runtime['input_sha256_after']['forge.exe']==ENGINE_SHA
assert all(c['exit_code']==0 for c in runtime['checks'])
write(STAGE/'provenance/standalone-6.4.8-windows.json',release)
write(STAGE/'provenance/candidate-source-files.json',source_map)
candidate={'engine_version':'6.4.8 candidate','engine_source_commit':COMMIT,'source_and_tests_commit':COMMIT,'source_url':'https://github.com/couns0538-sketch/dwqww/tree/'+COMMIT,'source_files_sha256':source_map,'bundled_source_directory':'sources/candidate-6.4.8','binary_sha256':ENGINE_SHA,'binary_path':'engine/candidate.exe','windows_compiler':release['compiler'],'windows_flags':release['flags'],'target':release['target'],'record':'provenance/candidate-6.4.8.json','standalone_build_record':'provenance/standalone-6.4.8-windows.json','standalone_wine_checks':runtime['checks'],'standalone_wine_scope':'Seven standalone functional/node-signature checks; no new bundle A/A or native match has run','native_windows_tested':False,'physical_ryzen_tested':False,'accepted_elo_gain':None,'stockfish_superiority_proven':False,'change_scope':release['root_effort_change']}
write(STAGE/'provenance/candidate-6.4.8.json',candidate)
readiness={'status':'manifest_verified; standalone_648_Wine_checks_passed; native_match_pending','candidate_source_commit':COMMIT,'candidate_sha256':ENGINE_SHA,'standalone_checks':7,'new_bundle_aa':'pending','new_native_pilot':'pending','new_native_sprt':'pending','equal_clock_gain_established':False,'historical_component_checks':'Unchanged Python/Fastchess/original-PE component logs retained from the immutable parent; they are not new bundle A/A results','original_reference':'Exact unmodified Forge6.4.0 ZIP release PE, never6.4.7'}
write(STAGE/'provenance/readiness-6.4.8.json',readiness)
readme=(STAGE/'README.txt').read_text().replace('6.4.2','6.4.8')
start=readme.index('Candidate: engine');end=readme.index('Reference: engine',start)
readme=readme[:start]+'''Candidate: engine\\candidate.exe, Forge 6.4.8 candidate, frozen source/test
commit 7125b3379a850de34041d42529cf95993607f93c, LLVM-MinGW Clang23.1.3,
Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static.
The exact candidate already passed seven standalone Wine functional/signature
checks. It includes the repaired TT coherence/context, legal-move witness,
query/move-picker optimizations and stable root-Move effort attribution.
Time-manager constants are unchanged; actual timed-stop/clock effects and
Elo impact remain unproven. Full candidate CMake inputs, tests, fixtures,
10,000-position corpus and tools are in sources\\candidate-6.4.8.
No optional 6.4.2 test executable or 6.4.2 candidate source is carried forward.

'''+readme[end:]
readme=readme.replace('Current bundle\nreadiness checks under Wine are not native Windows or physical Ryzen testing.','Standalone candidate checks under Wine are not native Windows or physical Ryzen testing.')
readme=readme.replace('RUN\n\n','''CURRENT STATUS

Manifest/source/component hashes were verified for this new bundle. Native
A/A, pilot and SPRT are PENDING. No old A/A pass, game result, launch state or
SPRT acceptance is a result for this bundle. The parent bundle and its prior
readiness evidence remain preserved separately. Unchanged component smoke
logs under provenance are historical component checks only.

RUN

''',1)
(STAGE/'README.txt').write_text(readme)
# Runtime, safety tools, original PE/source metadata, component licenses, and
# planned match protocol/openings remain byte-identical to the immutable parent.
unchanged={n:h for n,h in original_relative.items() if n not in {'README.txt','manifest.json','engine/candidate.exe','engine/forge_tests.exe','provenance/candidate-6.4.2.json','provenance/candidate-source-files.json'} and not n.startswith('sources/candidate-6.4.2/')}
for name,h in unchanged.items():assert sha(STAGE/name)==h,name
assert (STAGE/'windows_validate.py').read_bytes()==(REPO/'tools/match/windows_validate.py').read_bytes()
assert sha(STAGE/'engine/original-6.4.exe')=='593dae1d6ac7afa83112a9db0a647aa640767f9edf838855ac998a2b1f969e04'
manifest={'schema_version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bundle':'Forge6.4.8 candidate native Windows validation','manifest_revision':1,'derived_from':{'archive':'forge-6.4.2-windows-validation-bundle.zip','archive_sha256':OLD_SHA,'parent_manifest_sha256':original_relative['manifest.json'],'preserved_unchanged':True},'provenance':dict(original_manifest['provenance']),'protocol':original_manifest['protocol'],'readiness':readiness}
manifest['provenance']['candidate']=candidate
manifest['files']={p.relative_to(STAGE).as_posix():sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file() and p.relative_to(STAGE).as_posix()!='manifest.json'}
write(STAGE/'manifest.json',manifest)
actual={p.relative_to(STAGE).as_posix() for p in STAGE.rglob('*') if p.is_file()}
assert actual==set(manifest['files'])|{'manifest.json'}
assert 'sources/candidate-6.4.8/tools/openings/manifest.json' in manifest['files'] and 'sources/original-6.4.0/tools/openings/manifest.json' in manifest['files']
spec=importlib.util.spec_from_file_location('windows_validate_648',STAGE/'windows_validate.py');validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
loaded,frozen=validator.load_bundle(STAGE);assert loaded==manifest and len(frozen)==len(actual)
assert loaded['protocol']==original_manifest['protocol'] and loaded['provenance']['original']==original_manifest['provenance']['original']
with zipfile.ZipFile(ZIP,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():z.write(p,'forge-6.4.8-windows-validation-bundle/'+p.relative_to(STAGE).as_posix())
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(actual)
 for n in z.namelist():
  relative=n.removeprefix('forge-6.4.8-windows-validation-bundle/')
  assert relative in actual and hashlib.sha256(z.read(n)).hexdigest()==sha(STAGE/relative)
assert sha(OLD)==OLD_SHA
# Only compact metadata/checks are written to the checkout, never loose runtime trees.
shutil.copyfile(STAGE/'manifest.json',OUT/'manifest.json')
shutil.copyfile(STAGE/'provenance/candidate-6.4.8.json',OUT/'candidate-provenance.json')
shutil.copyfile(Path(__file__),OUT/'assemble-bundle.py')
result={'status':'manifest_and_zip_verified; native_AA_pilot_SPRT_pending','artifact':str(ZIP.relative_to(REPO)),'sha256':sha(ZIP),'bytes':ZIP.stat().st_size,'members':len(actual),'manifest_sha256':sha(STAGE/'manifest.json'),'stage':str(STAGE),'candidate_sha256':ENGINE_SHA,'source_commit':COMMIT,'candidate_source_files':len(source_map),'old_archive_sha256_before':OLD_SHA,'old_archive_sha256_after':sha(OLD),'unchanged_parent_files_verified':len(unchanged),'standalone_648_Wine_checks':7,'bundle_games_launched':0,'load_bundle_semantic_check':'passed','exhaustive_inventory_exact':'passed (only root manifest excluded)','nested_source_opening_manifests_listed':True,'ZIP_CRC_all_member_hashes':'passed','full_protocol_and_original_metadata_unchanged':True,'native_aa':'pending','native_pilot':'pending','native_sprt':'pending','equal_clock_gain_established':False}
write(OUT/'bundle-verification.json',result)
print(json.dumps(result,indent=2),flush=True)
