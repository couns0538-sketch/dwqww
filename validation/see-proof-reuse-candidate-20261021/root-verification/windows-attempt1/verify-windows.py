"""Independent DATA-ONLY root review of closed Windows24 evidence.

No producer imports, engine/test/build/archive execution or source/Git mutation.
Only frozen-commit Git ls-tree/cat-file reads run; root executes this script.
WINDOWS.json is created exclusively after all checks, never overwritten.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, io, json, re, shlex, struct, subprocess, zipfile

ROOT=Path('/workspace/dwqww')
BASE=ROOT/'validation/see-proof-reuse-windows-20261021'
HERE=Path(__file__).resolve().parent
COMMIT='7db08eac6ead99d641834c56ccec06a06600586a'
PARENT='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
EXPECTED_FINAL='ee5015b5c0f5e055702e68d0e973ccaef1f03b98451c9e9b2f28e5fa25d0dfce'
EXPECTED_MANIFEST='cd5b451f9ca8b7dee74fc26379ecd7b900e82334ba3e9adf9be1f74357dff1ea'
EXPECTED_ZIP='0db112fab29653eb43ac74924fb08a4a956bbf5085555f1a166a64d83fc392db'
checks=0;git_reads=[]
def require(condition,message):
 global checks
 if not condition:raise AssertionError(message)
 checks+=1
def safe(path):
 path=Path(path)
 require(path.is_absolute() and all(not p.is_symlink() for p in [path,*path.parents]),'Unsafe/symlink original '+str(path))
 require(path.is_file(),'Missing original '+str(path));return path
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def load(name):return json.loads(safe(BASE/name).read_text())
def integer(record,key,wanted):require(type(record[key]) is int and record[key]==wanted,'Integer '+key+' differs')
def relative(name):
 require(type(name) is str,'Relative path must be a string')
 p=PurePosixPath(name)
 require(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name and bool(name),'Unsafe relative path '+name)
 return p
def inventory(root):
 require(root.is_dir() and not root.is_symlink(),'Missing/unsafe directory '+str(root))
 require(all(not p.is_symlink() for p in root.rglob('*')),'Symlink in directory '+str(root))
 return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
def git(*args,stdin=None):
 command=['git','-C',str(ROOT),*args]
 result=subprocess.run(command,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 git_reads.append({'command':command,'returncode':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
 require(result.returncode==0 and not result.stderr,'Frozen Git data read failed')
 return result.stdout
def git_source(commit):
 raw=git('ls-tree','-r','-z',commit,'--','CMakeLists.txt','LICENSE','include','src','bench','tests','tools')
 entries={}
 for row in raw.split(b'\0'):
  if not row:continue
  head,name=row.split(b'\t',1);mode,kind,oid=head.split();name=name.decode('utf-8');relative(name)
  require(kind==b'blob' and mode in (b'100644',b'100755') and name not in entries,'Unsafe/duplicate Git source entry')
  entries[name]=oid.decode('ascii')
 names=sorted(entries);stream=io.BytesIO(git('cat-file','--batch',stdin=''.join(entries[n]+'\n' for n in names).encode('ascii')));result={}
 for name in names:
  header=stream.readline().rstrip(b'\n').split();require(len(header)==3 and header[:2]==[entries[name].encode(),b'blob'],'Git batch header differs')
  data=stream.read(int(header[2]));require(len(data)==int(header[2]) and stream.read(1)==b'\n','Incomplete Git blob')
  result[name]=hashlib.sha256(data).hexdigest()
 require(stream.read()==b'','Unexpected Git batch data');return result
def pe(data,name):
 require(len(data)>64 and data[:2]==b'MZ','Not a PE file: '+name)
 offset=struct.unpack_from('<I',data,0x3c)[0]
 require(offset+26<=len(data) and data[offset:offset+4]==b'PE\0\0','Invalid PE header: '+name)
 require(struct.unpack_from('<H',data,offset+4)[0]==0x8664 and struct.unpack_from('<H',data,offset+24)[0]==0x20b,'PE is not AMD64/PE32+: '+name)

require(not (HERE/'WINDOWS.json').exists(),'Root proof already exists; refusing overwrite')
require(sha(BASE/'FINAL-STATUS.json')==EXPECTED_FINAL,'Frozen final24 receipt differs')
require(sha(BASE/'FINAL-SHA256SUMS')==EXPECTED_MANIFEST,'Frozen final24 manifest differs')
final=load('FINAL-STATUS.json')
require(final['status']=='WINDOWS24_FIRST_CHAIN_QUALIFIED_NOT_ELO_ACCEPTED' and final['source_commit']==COMMIT and final['parent_source_commit']==PARENT,'Final24 identity/status differs')
bound={}
for line in (BASE/'FINAL-SHA256SUMS').read_text().splitlines():
 wanted,name=line.split('  ',1);relative(name)
 require(re.fullmatch('[0-9a-f]{64}',wanted) and name not in bound,'Malformed/duplicate final manifest entry')
 require(sha(BASE/name)==wanted,'Final evidence changed: '+name);bound[name]=wanted
require(len(bound)==287 and inventory(BASE)==set(bound)|{'FINAL-SHA256SUMS'},'Final287 exact namespace inventory differs')

audit=load('independent-audit.json');runtime=load('runtime-attempt1/result.json');build=load('result.json')
require(audit['status']=='passed' and audit['source_and_tests_commit']==COMMIT and audit['parent_source_commit']==PARENT,'Actual artifact audit differs')
integer(audit,'check_count',1870)
require(len(audit['checks'])==1870 and all(c['passed'] is True for c in audit['checks']),'Actual1870 audit checks not all PASS')
require(audit['engine_execution_during_audit'] is False and audit['new_build_during_audit'] is False,'Artifact audit execution scope differs')
require(runtime['status']=='passed' and runtime['source_and_tests_commit']==COMMIT and runtime['source_inputs_unchanged'] is True,'Actual runtime not passed/source unchanged')
names=['core','correction-history','runtime-psqt','pawn-span','nearest-pawn','pv-metadata','coherent-tt','rule50','legal-witness','uci','ponder','ownbook','stdin-bench11-signature']
require([c['name'] for c in runtime['checks']]==names==final['wine_check_names'] and all(type(c['exit_code']) is int and c['exit_code']==0 for c in runtime['checks']),'Actual13 named runtime checks differ')
values={'see_threshold_assertions':504,'see_threshold_failures':0,'tt_groups':12,'pv_metadata_assertions':56,'pv_metadata_failures':0,
 'nearest_pawn_checks':791680,'nearest_pawn_sets':395840,'nearest_pawn_failures':0,'nearest_constexpr_assertions':6,
 'pawn_span_checks':37320,'pawn_span_failures':0,'pawn_constexpr_assertions':3,'runtime_psqt_checks':347,'runtime_psqt_failures':0,
 'correction_history_checks':54,'correction_history_failures':0,'bench11_nodes':334752}
for record in (audit,runtime,final):
 for key,wanted in values.items():integer(record,key,wanted)
for key,wanted in [('rule50_targeted_failures',0),('legal_witness_comparisons',18947)]:integer(runtime,key,wanted);integer(final,key,wanted)
require(runtime['core_reference_perft_passed'] is True and len(runtime['ownbook_transitions'])==5 and all(t['PASS'] is True for t in runtime['ownbook_transitions']),'Perft/OwnBook original result differs')
require(runtime['input_sha256_before']==runtime['input_sha256_after'],'Runtime input hashes changed')
require(re.findall(rb'^SEE threshold contract: assertions (\d+) failures (\d+)\r?$',(BASE/'runtime-attempt1/core-stdout.log').read_bytes(),re.M)==[(b'504',b'0')],'Actual core stdout SEE504/0 summary differs')
require(re.findall(rb'^PV metadata: assertions (\d+) failures (\d+)\r?$',(BASE/'runtime-attempt1/pv-metadata-stdout.log').read_bytes(),re.M)==[(b'56',b'0')],'Actual PV stdout56/0 summary differs')
require(re.findall(rb'^All(\d+) TT coherence/regression groups passed\r?$',(BASE/'runtime-attempt1/coherent-tt-stdout.log').read_bytes(),re.M)==[b'12'],'Actual TT stdout12 summary differs')
for key in ('fresh_build_attempts','wine_runtime_attempts','benchmark_producer_attempts','independent_artifact_audit_attempts'):integer(final,key,1)
for key in ('build_passed','all_archived_originals_and_release_immutable','first_actual_capture_matches_parent'):require(final[key] is True,'Final true fact differs: '+key)
for key in ('production_source_or_Git_mutations','build_engine_audit_retries_or_waivers','windows_bench_nodes_known_before_first_capture','whole_cross_build_windows_NNUE_object_identity_claimed','root_verifier_executed_on_behalf','new24_NPS_measurement','native_windows_or_physical_ryzen_tested','stockfish_superiority_proven'):require(final[key] is False,'Final false fact differs: '+key)
require(final['accepted_elo_gain'] is None and final['nested_PE_historical_PID_reconstruction'] is None,'Unsupported gain/nested PID reconstruction claim')
integer(final,'optional_core_comparison_attempts',0);integer(final,'new_timed_match_games',0)

native_proof=HERE/'NATIVE.json';clear=load('WINDOWS-BUILD-CLEAR.json')
require(sha(native_proof)==final['root_native_proof_sha256']==clear['root_native_proof_sha256']=='92cd28951c1a6f9fc81eebb568a6173dcee5c2f0255f0ab3722e3b0114a12193','Genuine native24 root proof differs')
native=json.loads(native_proof.read_text());require(native['source_commit']==COMMIT and native['baseline_source_commit']==PARENT,'Native proof source differs')
for key,wanted in [('ctest',42),('active_uci',8),('exact_cold_warm_searches',56),('see_threshold_assertions_each_profile',504)]:integer(native,key,wanted)
require(sha(BASE/'WINDOWS-BUILD-CLEAR.json')==final['root_build_clear_sha256'],'Windows build clearance receipt differs')
sourcegate=Path(clear['root_source_gates_path']);require(sha(sourcegate)==final['source_gate_sha256']==clear['root_source_gates_sha256'],'Root source gate differs')
gate=json.loads(sourcegate.read_text());expected=gate['inputs'];require(gate['source_commit']==COMMIT and gate['baseline_commit']==PARENT and len(expected)==77,'Root77 source identity differs')
require(sha(BASE/'ROOT-FROZEN-SOURCE-GATES.json')==sha(sourcegate) and load('PREPARED-EXPECTED77.json')==expected,'Captured source gate/map differ')
actual_git=git_source(COMMIT);require(actual_git==expected,'Actual frozen Git77 blobs differ from gate')
parent_git=git_source(PARENT)
changed={name for name in set(actual_git)|set(parent_git) if actual_git.get(name)!=parent_git.get(name)}
require(changed==set(final['declared_export_changes'])=={'CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tests.cpp'},'Actual four source deltas differ')
source=load('source-hashes.json');require(len(source)==74 and source=={n:h for n,h in expected.items() if not n.endswith('.pyc')},'Export74 is not Git77 minus3pyc')
prepared=load('PREPARED-SOURCE.json');live_source=Path(prepared['source_directory']);live_build=Path(prepared['build_directory'])
require(prepared['source_commit']==COMMIT and prepared['source_files']==74,'Prepared source identity differs')
require(inventory(live_source)==set(source)==inventory(BASE/'originals/frozen-source'),'Exported/captured source inventories differ')
for name,wanted in source.items():require(sha(live_source/name)==sha(BASE/'originals/frozen-source'/name)==wanted,'Exported/captured Git source bytes differ: '+name)
require(load('production-hashes.json')=={n:h for n,h in source.items() if n=='CMakeLists.txt' or n.startswith(('src/','include/'))},'Production source subset differs')
require(load('test-hashes.json')=={n:h for n,h in source.items() if n.startswith('tests/')},'Test source subset differs')

outside=load('OUTSIDE-CLOSED-ORIGINALS.json')
require(sha(BASE/'OUTSIDE-CLOSED-ORIGINALS.json')==final['outside_originals_manifest_sha256'],'Closed outside original map differs')
expected_roots={str(live_source):74,str(live_build):220,'/workspace/.cloud-setup/windows6424-package-capture':2,
 '/workspace/.cloud-setup/windows6424-package-supervisor':2,'/workspace/.cloud-setup/windows6424-package-ready':1,
 str(ROOT/'releases/forge-6.4.24-candidate-windows-zen5'):23,str(ROOT/'releases/forge-6.4.24-candidate-windows-zen5.zip'):1}
require(set(outside)==set(expected_roots) and final['outside_closed_counts']==expected_roots,'Seven exact outside roots/counts differ')
outside_count=0
for rootname,record in outside.items():
 root=Path(rootname);integer(record,'files',expected_roots[rootname]);entries=record['sha256'];require(len(entries)==record['files'],'Outside entry count differs')
 if root.is_dir():
  require(inventory(root)==set(entries),'Outside directory inventory differs: '+rootname)
  for name,wanted in entries.items():relative(name);require(sha(root/name)==wanted,'Outside original changed: '+str(root/name))
 else:
  require(set(entries)=={rootname} and sha(root)==entries[rootname],'Outside standalone file map differs: '+rootname)
 outside_count+=len(entries)

protected=load('parent6423-preservation-before.json');parent_check=load('parent6423-preservation-check.json')
require(len(protected)==597 and parent_check['status']=='unchanged' and parent_check['files']==597 and parent_check['input_sha256_before']==parent_check['input_sha256_after']==protected,'Actual parent597 preservation maps differ')
for name,wanted in protected.items():require(Path(name).is_absolute() and sha(Path(name))==wanted,'Protected parent changed: '+name)

require(build['status']=='build_passed' and build['source_and_tests_commit']==COMMIT and build['source_inputs_unchanged'] is True,'Original build receipt differs')
require(len(build['binaries'])==11 and set(build['libraries'])=={'libforge_core.a'},'Original build binary/core inventory differs')
pe_records=load('pe-validation.json');require(set(pe_records)==set(build['binaries']),'Retained PE records differ')
for name,record in build['binaries'].items():
 path=Path(record['path']);original=BASE/'originals/binaries'/name
 require(path==live_build/name and sha(path)==sha(original)==record['sha256'] and path.stat().st_size==record['bytes'],'Original built PE differs: '+name)
 pe(path.read_bytes(),name);require(pe_records[name]['sha256']==record['sha256'] and pe_records[name]['architecture']=='AMD64' and pe_records[name]['system_or_ucrt_imports_only'] is True,'Retained PE qualification differs: '+name)
 record_text=(BASE/(name+'-pe-headers-imports.txt')).read_text()
 require(all(dll in record_text for dll in pe_records[name]['imports']),'Retained import list missing from original readobj bytes')
core=build['libraries']['libforge_core.a']
require(sha(Path(core['path']))==sha(BASE/'originals/static-core/libforge_core.a')==audit['core_sha256']==final['core_sha256']==core['sha256'],'Original static core identity differs')
require(Path(core['path'])==live_build/'libforge_core.a' and Path(core['path']).stat().st_size==core['bytes'],'Original static core path/size differs')
compile_contract=load('compile-contract.json');require(compile_contract['status']=='passed' and compile_contract['compilation_records']==18 and compile_contract['lto'] is False and compile_contract['static_link'] is True and compile_contract['parallel_jobs']==1,'Original compilation contract differs')
require(compile_contract['flags']==['-march=znver5','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-O3','-DNDEBUG','-std=gnu++20'],'Actual Windows strict compiler flag list differs')
compilations=load('compile_commands.json');require(len(compilations)==18,'Original18 compilation records differ')
for record in compilations:
 tokens=shlex.split(record['command'])
 require(all(flag in tokens for flag in compile_contract['flags']) and not any(t=='-ffast-math' or t.startswith('-flto') for t in tokens),'Compiled strict FP/ISA flags differ')
 require(Path(record['file']).is_relative_to(live_source) and record['directory']==str(live_build),'Compile source/build provenance differs')
require('-static' in (BASE/'CMakeFiles_forge.dir_link.txt').read_text(),'Static Windows link flag absent')
see=load('see-threshold-object-provenance.json')
require(see['assertions']==504 and see['core_test_source_sha256']==source['tests/tests.cpp'] and see['tested_pe_sha256']==build['binaries']['forge_tests.exe']['sha256'],'Actual SEE test/source/PE binding differs')
require(sha(BASE/'originals/objects/tests.cpp.obj')==sha(live_build/'CMakeFiles/forge_tests.dir/tests/tests.cpp.obj')==see['object_sha256']==final['see_threshold_object_sha256'],'Actual SEE test object differs')

freeze=load('BENCH-SIGNATURE-FREEZE.json')
require(freeze['source_and_tests_commit']==COMMIT and freeze['bench11_nodes']==334752 and freeze['engine_sha256']==final['engine_sha256']==audit['engine_sha256'],'First Windows24 signature identity differs')
require(freeze['raw_bench_stdout_sha256']==sha(BASE/'runtime-attempt1/bench-stdout.log') and freeze['raw_bench_stdin_sha256']==sha(BASE/'runtime-attempt1/bench-stdin.txt') and freeze['runtime_result_sha256']==sha(BASE/'runtime-attempt1/result.json'),'First signature raw bindings differ')
require(final['bench_signature_policy']=='FIRST_NORMAL_CANDIDATE_CAPTURE_ONLY' and final['parent_same_platform_parity_nodes']==334752,'Windows first-capture parity policy differs')

raws=load('windows-originals-SHA256.json');rawpath=BASE/'windows-originals.zip'
require(len(raws)==audit['raw_files']==271 and sha(rawpath)==audit['raw_sha256']==final['raw_archive_sha256'] and rawpath.stat().st_size==audit['raw_bytes']==10400983,'Raw original archive identity differs')
with zipfile.ZipFile(rawpath) as raw:
 require(len(raw.namelist())==len(set(raw.namelist()))==272 and set(raw.namelist())==set(raws)|{'windows-originals-SHA256.json'},'Raw272 archive members differ')
 require(raw.read('windows-originals-SHA256.json')==(BASE/'windows-originals-SHA256.json').read_bytes(),'Raw embedded map differs')
 for name,record in raws.items():
  relative(name);original=safe(BASE/name).read_bytes()
  require(len(original)==record['bytes'] and hashlib.sha256(original).hexdigest()==record['sha256'] and raw.read(name)==original,'Raw original/archive member differs: '+name)

artifact=ROOT/audit['artifact'];require(sha(artifact)==audit['artifact_sha256']==final['artifact_sha256']==EXPECTED_ZIP and artifact.stat().st_size==audit['artifact_bytes']==17077385,'User release ZIP identity differs')
prefix='forge-6.4.24-candidate-windows-zen5/'
with zipfile.ZipFile(artifact) as release:
 require(len(release.namelist())==len(set(release.namelist()))==23,'Release23 member inventory differs')
 require(all(name.startswith(prefix) for name in release.namelist()),'Release prefix differs')
 records=release.read(prefix+'SHA256SUMS').decode().splitlines();require(len(records)==22,'Release22 checksum entries differ');names=set()
 for line in records:
  wanted,name=line.split('  ',1);relative(name);require(name not in names and re.fullmatch('[0-9a-f]{64}',wanted),'Malformed/duplicate release checksum')
  names.add(name);data=release.read(prefix+name)
  require(hashlib.sha256(data).hexdigest()==wanted and data==(ROOT/'releases'/prefix/name).read_bytes(),'Release checksum/expanded bytes differ: '+name)
 require(names=={n[len(prefix):] for n in release.namelist()}-{'SHA256SUMS'},'Exact release checksum set differs')
 shipped={n for n in names if n.endswith('.exe')};expected_shipped=(set(build['binaries'])-{'forge.exe','forge_bench.exe'})|{'forge-6.4.24-ryzen-9850x3d.exe'}
 require(shipped==expected_shipped and len(shipped)==10==final['shipped_PE_files'],'Ten shipped PE inventory differs')
 for name in shipped:
  original='forge.exe' if name=='forge-6.4.24-ryzen-9850x3d.exe' else name
  data=release.read(prefix+name);pe(data,name);require(data==(BASE/'originals/binaries'/original).read_bytes(),'Shipped PE differs from tested original: '+name)
 require(release.read(prefix+'windows-originals.zip')==rawpath.read_bytes(),'Release retained raw ZIP differs')
 for name in ('source-hashes.json','test-hashes.json','windows-originals-SHA256.json'):
  require(release.read(prefix+name)==(BASE/name).read_bytes(),'Release source/raw provenance differs: '+name)

outer=final['actual_outer_owned_process_group_records'];require(set(outer)=={'source-export','source-records','first-build','first-runtime','first-signature-freeze','first-package','first-artifact-audit'},'Actual outer group set differs')
for name,record in outer.items():
 require(record==load(name+'.status.json') and type(record['returncode']) is int and record['returncode']==0 and record['timeout'] is False and record['owned_group_closed'] is True,'Original outer group not closed normally: '+name)
 for stream in ('stdout','stderr'):
  path=Path('/workspace/.cloud-setup/windows6424-package-supervisor')/(name+'.'+stream) if name=='first-package' else BASE/(name+'.'+stream)
  require(sha(path)==record[stream+'_sha256'],'Original outer stream changed: '+str(path))

# Final source/evidence/outside rehash; never chmod/write originals or rerun tools.
for name,wanted in source.items():require(sha(live_source/name)==sha(BASE/'originals/frozen-source'/name)==wanted,'Source changed during data review')
for name,wanted in bound.items():require(sha(BASE/name)==wanted,'Evidence changed during data review: '+name)
require(sha(BASE/'FINAL-SHA256SUMS')==EXPECTED_MANIFEST and inventory(BASE)==set(bound)|{'FINAL-SHA256SUMS'},'Closed namespace changed during review')
for rootname,record in outside.items():
 root=Path(rootname)
 require((inventory(root)==set(record['sha256'])) if root.is_dir() else set(record['sha256'])=={rootname},'Outside inventory changed during review')
 for name,wanted in record['sha256'].items():require(sha(root/name if root.is_dir() else root)==wanted,'Outside original changed during review')
proof={'status':'ROOT_VERIFIED_WINDOWS24_ORIGINAL_SOURCE_ARTIFACT_AND_OUTSIDE_EVIDENCE','utc':datetime.now(timezone.utc).isoformat(),
 'source_commit':COMMIT,'baseline_source_commit':PARENT,'verification_checks':checks,'audit_checks_verified':1870,
 'final_evidence_records_rehashed':len(bound),'exact_final_evidence_tree_verified':True,'source_git_blobs_verified':len(actual_git),
 'source_files_rehashed':len(source),'pyc_excluded':3,'actual_source_changed_paths':sorted(changed),'source_equivalence_to_git_verified':True,
 'outside_original_roots':len(outside),'outside_original_files_rehashed':outside_count,'outside_original_root_counts':expected_roots,
 'protected_parent_files_rehashed':len(protected),'raw_originals_byte_verified':len(raws),'raw_archive_members':272,
 'original_built_pe_files_rehashed':11,'shipped_pe_files_byte_verified':10,'static_core_byte_verified':True,'release_members':23,'release_checksum_entries':22,
 'wine_checks_passed':13,'see_threshold_assertions':504,'see_threshold_failures':0,'tt_groups':12,'pv_metadata_assertions':56,'pv_metadata_failures':0,
 'nearest_pawn_checks':791680,'nearest_target_sets':395840,'bench11_nodes':334752,'first_actual_windows_signature_verified':True,
 'outer_owned_group_records_verified':len(outer),'nested_PE_historical_PID_reconstruction':None,'git_reads':git_reads,
 'artifact':audit['artifact'],'artifact_sha256':EXPECTED_ZIP,'artifact_bytes':17077385,'engine_sha256':audit['engine_sha256'],'core_sha256':audit['core_sha256'],
 'raw_archive_sha256':audit['raw_sha256'],'final_status_sha256':EXPECTED_FINAL,'final_manifest_sha256':EXPECTED_MANIFEST,
 'root_native_proof_sha256':final['root_native_proof_sha256'],'root_verifier_sha256':sha(Path(__file__)),
 'engine_test_build_archive_execution_by_this_review':0,'originals_or_source_modified':False,'native_windows_or_physical_ryzen_tested':False,
 'nps_difference':None,'elo_gain':None,'scope':'Independent data-only source/retained Wine/artifact/original evidence review; no native Windows/Ryzen, speed, match or Stockfish claim.'}
with (HERE/'WINDOWS.json').open('x') as output:json.dump(proof,output,indent=2);output.write('\n')
print(json.dumps(proof,indent=2))
