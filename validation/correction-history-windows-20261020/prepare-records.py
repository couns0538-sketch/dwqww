from pathlib import Path
import datetime,hashlib,json,subprocess
ROOT=Path('/workspace/dwqww');OUT=ROOT/'validation/correction-history-windows-20261020';OLD=ROOT/'validation/promotion-see-20261020/windows';SOURCE=Path('/workspace/.cloud-setup/windows6418-source');BUILD=Path('/workspace/.cloud-setup/windows6418-build')
COMMIT='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b';PARENT='47f0560221d986e41a309853e1295c557fcf5bf6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2)+'\n')
load=lambda p:json.loads(p.read_text())
source=load(OUT/'source-hashes.json');parent=load(OLD/'source-hashes.json')
changed=sorted(n for n,h in source.items() if parent.get(n)!=h)
assert changed==['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/correction_history_tests.cpp']
assert set(parent).issubset(source) and len(source)==len(parent)+1
assert source['src/search.cpp']=='5cba75f2227d4e69cff8769a18785c2c55c899d5e6bd96c0c58b5368b6322225'
assert source['tests/correction_history_tests.cpp']=='3f5523ac462cde0a36ce3df4f5bfb99e59dbe34a08c9e2d06dcb9ecad5dad66d'
assert not BUILD.exists()
write('STATIC-CHECKS.json',{'status':'STATIC_PREPARATION_PASS_NO_BUILD_OR_RUNTIME','source_commit':COMMIT,'parent_source_commit':PARENT,'source_files':len(source),'export_changes':changed,'search_sha256':source['src/search.cpp'],'correction_history_test_sha256':source['tests/correction_history_tests.cpp'],'all_other_parent_exports_identical':True,'new_test_registered_in_cmake':True,'search_scope':'Independent unaccepted correction-history EMA-to-residual increment ablation; behavior intentionally changes, no established bug repair or accepted Elo/NPS claim.','windows_bench_expectation':None,'windows_bench_policy':'UNKNOWN until first actual18 run; freeze authentic positive signature before packaging, independent of parent/native count.','no_compiler_engine_wine_archive_executed':True,'build_directory_exists':False})
pinned=load(OLD/'PINNED-TOOLS.json');pinned['tools']['toolchain_source']['path']=str(SOURCE/'tools/windows-zen5.cmake');pinned['tools']['toolchain_source']['resolved_path']=str(SOURCE/'tools/windows-zen5.cmake')
for v in pinned['tools'].values():assert sha(Path(v['path']))==v['sha256']
toolroot=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
for name,path in [('compiler_implementation',toolroot/'bin/clang-23'),('compiler_shared_library',toolroot/'lib/libclang-cpp.so.23.1'),('linker',toolroot/'bin/ld.lld'),('archiver',toolroot/'bin/llvm-ar')]:
 if path.is_file():pinned['tools'][name]={'path':str(path),'resolved_path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':sha(path)}
pinned['version_evidence']='Copied completed17 version evidence; no compiler/version query executed during18 preparation.'
pinned['parallel_build_jobs_after_clear']=1
write('PINNED-TOOLS.json',pinned)
files=sorted(p for p in OLD.rglob('*') if p.is_file())
files+=sorted(p for p in (ROOT/'releases/forge-6.4.17-candidate-windows-zen5').rglob('*') if p.is_file())
files += [ROOT/'releases/forge-6.4.17-candidate-windows-zen5.zip']
write('parent6417-preservation-before.json',{str(p):sha(p) for p in files})
write('PROTOCOL.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_and_tests_commit':COMMIT,'parent_source_commit':PARENT,'build_phase':'Reuse exact17 configure/build command structure with strict static Zen5 toolchain and --parallel 1; wait for root18 WINDOWS BUILD CLEAR.','runtime_check_names':['core','correction-history','coherent-tt','rule50','legal-witness','uci','ponder','ownbook','stdin-bench11-signature'],'correction_history_contract':'Actual Worker corrected_eval/update_correction via existing test friendship: signed depth/clipping, zero residual retention, signed subgrain rounding, table coupling, convergence, shared-material conflict, saturation and mate-score boundaries. All assertions retained.','old_checks_retained':True,'simd':'Actual PE disassembly AVX2 min/max,mul,add and no fused arithmetic; existing output-layer 256-bit checker.','pe':'AMD64 PE32+ system/UCRT imports only, shipped bytes must equal actual Wine inputs.','bench_expectation':None,'bench_policy':'Preserve first actual Windows18 signature and raw stdout, freeze with tested PE hash before packaging; no retries, parent or native-signature requirement.','first_failure_policy':'Keep all first-attempt logs and stop failed phase; no retry/gate weakening.','artifacts':'New candidate18 ZIP and expanded directory only; manifest-verified full original source/PE/static-core/commands/log archive plus independent audit.','scope':'Windows/Wine bounded correctness and artifact provenance only; independent unaccepted search ablation, no NPS/Elo/native Windows/physical Ryzen/Stockfish proof.'})
write('PREPARATION.json',{'status':'PREPARED_WAITING_FOR_18_WINDOWS_BUILD_CLEAR','prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,'source_directory':str(SOURCE),'planned_build_directory':str(BUILD),'source_files':len(source),'source_manifest_sha256':sha(OUT/'source-hashes.json'),'test_manifest_sha256':sha(OUT/'test-hashes.json'),'pinned_tools_metadata':'PINNED-TOOLS.json','static_checks':'STATIC-CHECKS.json','protocol':'PROTOCOL.json','build_started':False,'runtime_started':False,'archives_created':False,'no_compiler_engine_wine_archive_executed':True,'gate':'Wait for root18 WINDOWS BUILD CLEAR, preserve exact clearance in WINDOWS-BUILD-CLEAR.json before any build/runtime/package phase.','windows_bench_expectation':None,'prior_evidence_preserved_files':len(files),'known_parent_limit':'Original16 TSan8/9 failure remains qualified; native18 gates separate.'})
print('Prepared frozen18 source',len(source),'files; protected17 files',len(files),'; no build/runtime/archive')
