#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import signal
import ctypes
import re
import sys
sys.dont_write_bytecode=True
from process_facts import cleanup

REPO=Path("/workspace/dwqww")
HERE=Path(__file__).resolve().parent
REV=None # Read only from explicit root clearance after the source is frozen.
SOURCE=Path("/workspace/.cloud-setup/tt-refresh-native-source")
CMAKE="/workspace/.cloud-setup/venv/bin/cmake"
CTEST="/workspace/.cloud-setup/venv/bin/ctest"
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto"
ARTIFACT_NAMES=['forge', 'forge_tests', 'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests', 'forge_correction_history_tests', 'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_nearest_pawn_tests', 'forge_pv_metadata_tests', 'forge_bench', 'libforge_core.a', 'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.o', 'CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o', 'CMakeFiles/forge_core.dir/src/nnue.cpp.o', 'CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.o', 'CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.o']
SANITIZER_DIAGNOSTIC=re.compile(rb"AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|ThreadSanitizer|runtime error:",re.I)
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def files(root): return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob("*")) if p.is_file()}
def write(path,data): path.write_text(json.dumps(data,indent=2)+"\n")
parser=argparse.ArgumentParser()
parser.add_argument("profile",choices=["release","asan","tsan"])
args=parser.parse_args()
profile=args.profile
clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text())
assert clear.get('authorized') is True, 'Preparation only: root build clearance is pending'
REV=clear.get('source_commit')
assert isinstance(REV,str) and re.fullmatch(r'[0-9a-f]{40}',REV), 'Exact frozen source SHA required'
assert isinstance(clear.get('expected_runtime_psqt_checks'),int) and clear['expected_runtime_psqt_checks']>0, 'Root-frozen permanent test check count required'
assert isinstance(clear.get('expected_pawn_span_checks'),int) and clear['expected_pawn_span_checks']>0, 'Root-frozen pawn-span test check count required'
assert clear.get('expected_nearest_checks')==791680 and clear.get('expected_nearest_sets')==395840 and clear.get('expected_nearest_constexpr_assertions')==6, 'Frozen nearest-square schema required'
assert clear.get('expected_pv_metadata_assertions')==56 and clear.get('exact_search_parity_required') is False and clear.get('observational_cold_warm_searches')==0, 'Root-approved bounded PV regression protocol required'
assert clear.get('source_files')==77 and clear.get('expected_ctest_per_profile')==14, 'Exact77-source/14-suite protocol required'
assert clear.get('required_version')=='6.4.23' and clear.get('baseline_source_commit')=='ff2e269c6058be84456e3b98344826d17b0056eb', 'Actual23 and parent22 source protocol required'
assert type(clear.get('expected_tt_groups')) is int and clear['expected_tt_groups']>0 and isinstance(clear.get('expected_tt_group_success_line'),str), 'Root-frozen actual TT test schema required'
assert clear.get('benchmark_signature_mode')=='FIRST_CAPTURE_EXCLUSIVE_FREEZE' and clear.get('expected_bench11_nodes') is None, 'Unknown23 benchmark must be captured once, not inherited'
root_source=json.loads((HERE/'ROOT-FROZEN-SOURCE-GATES.json').read_text())
assert root_source['source_commit']==REV and len(root_source['inputs'])==77, 'Root source gate required'
assert root_source['inputs']['tests/pv_metadata_tests.cpp']==clear['expected_pv_metadata_test_source_sha256']=='8000b717a298c4c8bb637752fcc57a0ce485110a12edc4a505f3d0452620bd1e', 'Exact RED-tested permanent PV regression source required'
assert root_source['inputs']['tests/tt_coherence_tests.cpp']==clear['expected_tt_test_source_sha256'] and re.fullmatch(r'[0-9a-f]{64}',clear['expected_tt_test_source_sha256']), 'Exact root-frozen TT regression source required'
prior={'asan':'release','tsan':'asan'}.get(profile)
if prior:
    previous=json.loads((HERE/('frozen-'+prior+'-attempt1/summary.json')).read_text())
    assert previous['status']=='PASS' and previous['source_commit']==REV, 'Prior profile must finish successfully before next profile starts'
if profile=='asan':
    signature=json.loads((HERE/'release-signature-wrapper-attempt1/summary.json').read_text())
    frozen_signature=json.loads((HERE/'BENCH-SIGNATURE-FREEZE.json').read_text())
    assert signature['status']=='PASS' and frozen_signature['source_commit']==REV and frozen_signature['status']=='FROZEN_FIRST_ACTUAL_RELEASE_BENCH11'
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
OUT=HERE/("frozen-"+profile+"-attempt1")
OUT.mkdir(exist_ok=False)
BUILD=Path("/workspace/.cloud-setup/tt-refresh-native-"+profile)
if BUILD.exists(): raise SystemExit("Refusing existing build directory: "+str(BUILD))
archive=subprocess.check_output(["git","archive",REV,"CMakeLists.txt","LICENSE","src","include","tests","bench","tools"],cwd=REPO)
expected_tar=HERE/("frozen-source-"+REV[:7]+".tar")
if not expected_tar.exists(): expected_tar.write_bytes(archive)
assert expected_tar.read_bytes()==archive
if not SOURCE.exists():
    SOURCE.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(SOURCE,filter="data")
before=files(SOURCE)
archive_members={}
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    for member in tar.getmembers():
        if member.isfile(): archive_members[member.name]=hashlib.sha256(tar.extractfile(member).read()).hexdigest()
assert len(before)==77 and before==archive_members==root_source['inputs']
write(HERE/("frozen-source-"+REV[:7]+"-files.json"),before)
ENV=os.environ.copy()
for key in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']: ENV.pop(key,None)
ENV["PYTHONDONTWRITEBYTECODE"]="1"
if profile=="asan":
    ENV["ASAN_OPTIONS"]="detect_leaks=1:halt_on_error=1:abort_on_error=1"
    ENV["UBSAN_OPTIONS"]="halt_on_error=1:print_stacktrace=1"
elif profile=="tsan": ENV["TSAN_OPTIONS"]="halt_on_error=1:exitcode=66"
config=[CMAKE,"-S",str(SOURCE),"-B",str(BUILD),"-DCMAKE_EXPORT_COMPILE_COMMANDS=ON","-DCMAKE_CXX_COMPILER=/usr/bin/g++-14","-DPython3_EXECUTABLE=/workspace/.cloud-setup/venv/bin/python","-DFORGE_NATIVE=OFF"]
if profile=="release": config += ["-DCMAKE_BUILD_TYPE=Release","-DFORGE_ENABLE_SANITIZERS=OFF","-DCMAKE_CXX_FLAGS="+FLAGS]
elif profile=="asan": config += ["-DCMAKE_BUILD_TYPE=RelWithDebInfo","-DFORGE_ENABLE_SANITIZERS=ON","-DCMAKE_CXX_FLAGS="+FLAGS+" -fno-pie","-DCMAKE_EXE_LINKER_FLAGS=-no-pie"]
else: config += ["-DCMAKE_BUILD_TYPE=RelWithDebInfo","-DFORGE_ENABLE_SANITIZERS=OFF","-DCMAKE_CXX_FLAGS="+FLAGS+" -fsanitize=thread -fno-omit-frame-pointer -fno-pie","-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -no-pie"]
summary={"source_commit":REV,"source_export":str(SOURCE),"source_archive_sha256":hashlib.sha256(archive).hexdigest(),
         "profile":profile,"started_utc":datetime.now(timezone.utc).isoformat(),"steps":[],
         "environment_overrides":{name:ENV[name] for name in ["PYTHONDONTWRITEBYTECODE","ASAN_OPTIONS","UBSAN_OPTIONS","TSAN_OPTIONS"] if name in ENV},
         "tsan_deadlock_detector":"default enabled; no disabling options", "status":"RUNNING"}
write(OUT/"summary.json",summary)
def run(label,command,timeout=1200):
    print("START "+profile+" "+label,flush=True)
    start=time.monotonic(); done=None; error=None; timed_out=False; returncode=None
    source_before_step=files(SOURCE)
    artifacts_before_step={name:digest(BUILD/name) for name in ARTIFACT_NAMES if (BUILD/name).is_file()}
    with (OUT/(label+".stdout")).open("xb") as stdout, (OUT/(label+".stderr")).open("xb") as stderr:
        try:
            done=subprocess.Popen(command,cwd=REPO,env=ENV,stdout=stdout,stderr=stderr,start_new_session=True)
            try: returncode=done.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True; error="command timeout"; os.killpg(done.pid,signal.SIGKILL); returncode=done.wait(timeout=10)
        except BaseException as exc: error=repr(exc)
        finally: cleanup_facts=cleanup(done.pid) if done else {"no_live_owned_processes":True,"not_started":True}
    step={"label":label,"command":command,"cwd":str(REPO),"timeout_seconds":timeout,
          "exit_code":returncode,"elapsed_seconds":time.monotonic()-start,"timed_out":timed_out,"error":error,
          "pid":done.pid if done else None,"cleanup":cleanup_facts,
          "source_sha256_before_step":source_before_step,"source_sha256_after_step":files(SOURCE),
          "artifact_sha256_before_step":artifacts_before_step,"artifact_sha256_after_step":{name:digest(BUILD/name) for name in ARTIFACT_NAMES if (BUILD/name).is_file()},
          "stdout_sha256":digest(OUT/(label+".stdout")),"stderr_sha256":digest(OUT/(label+".stderr"))}
    summary["steps"].append(step)
    write(OUT/(label+"-command.json"),step)
    write(OUT/"summary.json",summary)
    print(json.dumps({k:step[k] for k in ['label','command','exit_code','timed_out','error','cleanup']}),flush=True)
    if returncode or error or timed_out or not cleanup_facts['no_live_owned_processes'] or cleanup_facts.get('unexpected_live_members_after_command',False):
        raise RuntimeError(label+" failed; all facts saved before gate assertion")
    if source_before_step!=files(SOURCE): raise RuntimeError("source changed during "+label)
    if label not in ["configure","build"] and step["artifact_sha256_before_step"]!=step["artifact_sha256_after_step"]: raise RuntimeError("artifacts changed during "+label)
try:
    run("configure",config)
    run("build",[CMAKE,"--build",str(BUILD),"--parallel","2"])
    binary_before={name:digest(BUILD/name) for name in ARTIFACT_NAMES}
    summary["binary_sha256_before"] = binary_before
    summary["source_sha256_before_tests"]=files(SOURCE)
    summary["test_source_sha256_before_tests"]={n:h for n,h in files(SOURCE).items() if n.startswith("tests/")}
    write(OUT/"summary.json",summary)
    run("ctest-discovery",[CTEST,"--test-dir",str(BUILD),"--show-only=json-v1"])
    discovery=json.loads((OUT/"ctest-discovery.stdout").read_text())
    summary["ctest_names"]=[r["name"] for r in discovery["tests"]]
    write(OUT/"summary.json",summary)
    expected_template=json.loads((HERE/'EXPECTED-CTEST-COMMANDS.json').read_text())
    replacements={'@BUILD@':str(BUILD),'@SOURCE@':str(SOURCE),'@PYTHON@':'/workspace/.cloud-setup/venv/bin/python'}
    expected={name:[next((value.replace(token,path) for token,path in replacements.items() if token in value),value) for value in command] for name,command in expected_template.items()}
    actual={item['name']:item['command'] for item in discovery['tests']}
    summary['expected_ctest_commands']=expected
    summary['actual_ctest_commands']=actual
    write(OUT/'summary.json',summary)
    assert len(discovery['tests'])==14 and len(actual)==14 and actual==expected
    assert summary['ctest_names'][4:6]==['forge_nearest_pawn_tests','forge_pv_metadata_tests'], 'Actual PV metadata suite must be sixth after nearest'
    run("ctest",[CTEST,"--test-dir",str(BUILD),"--output-on-failure","-j","1","--timeout","300"])
    summary["source_sha256_after_tests"]=files(SOURCE)
    summary["test_source_sha256_after_tests"]={n:h for n,h in files(SOURCE).items() if n.startswith("tests/")}
    summary["binary_sha256_after_tests"]={name:digest(BUILD/name) for name in binary_before}
    write(OUT/"summary.json",summary)
    assert "100% tests passed, 0 tests failed out of 14" in (OUT/"ctest.stdout").read_text()
    diagnostic_files=[OUT/'ctest.stdout',OUT/'ctest.stderr',BUILD/'Testing/Temporary/LastTest.log',BUILD/'uci-regression.log',BUILD/'ownbook-regression.json']
    summary['sanitizer_diagnostic_file_presence']={str(f):f.is_file() for f in diagnostic_files}
    summary['sanitizer_diagnostic_scan']={str(f):{'sha256':digest(f),'matches':[m.group().decode('utf-8','replace') for m in SANITIZER_DIAGNOSTIC.finditer(f.read_bytes())]} for f in diagnostic_files if f.is_file()}
    log=(BUILD/'Testing/Temporary/LastTest.log').read_text()
    tt_block=re.search(r'(?ms)^\d+/\d+ Testing: forge_tt_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',log)
    summary['tt_coherence_log_block_present']=tt_block is not None
    summary['tt_coherence_contract_actual_groups']=re.findall(r'^All(\d+) TT coherence/regression groups passed\s*$',tt_block.group() if tt_block else '',re.M)
    summary['tt_coherence_actual_success_lines']=re.findall(r'^All\d+ TT coherence/regression groups passed\s*$',tt_block.group() if tt_block else '',re.M)
    summary['tt_coherence_actual_success_lines']=[line.strip() for line in summary['tt_coherence_actual_success_lines']]
    block=re.search(r'(?ms)^\d+/\d+ Testing: forge_runtime_psqt_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',log)
    summary['runtime_psqt_test_log_block_present']=block is not None
    summary['runtime_psqt_contract_actual_summaries']=re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$',block.group() if block else '',re.M)
    pawn_block=re.search(r'(?ms)^\d+/\d+ Testing: forge_pawn_span_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',log)
    summary['pawn_span_test_log_block_present']=pawn_block is not None
    summary['pawn_span_contract_actual_summaries']=re.findall(r'^pawn_span_tests: (\d+) checks, (\d+) failures\s*$',pawn_block.group() if pawn_block else '',re.M)
    nearest_block=re.search(r'(?ms)^\d+/\d+ Testing: forge_nearest_pawn_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',log)
    summary['nearest_pawn_log_block_present']=nearest_block is not None
    summary['nearest_pawn_contract_actual_summaries']=re.findall(r'^Nearest pawn distance: sets (\d+) checks (\d+) failures (\d+)\s*$',nearest_block.group() if nearest_block else '',re.M)
    summary['nearest_constexpr_assertions']=len(re.findall(r'(?m)^static_assert\(', (SOURCE/'tests/nearest_pawn_tests.cpp').read_text()))
    pv_block=re.search(r'(?ms)^\d+/\d+ Testing: forge_pv_metadata_tests\n.*?(?=^\d+/\d+ Testing: |\Z)',log)
    summary['pv_metadata_log_block_present']=pv_block is not None
    summary['pv_metadata_contract_actual_summaries']=re.findall(r'^PV metadata: assertions (\d+) failures (\d+)\s*$',pv_block.group() if pv_block else '',re.M)
    summary['pv_metadata_case_rows']=re.findall(r'^PV_METADATA_CASE (\w+) nodes=(\d+) aborted=([01]) flag=([01]) pv_moves=(\d+)\s*$',pv_block.group() if pv_block else '',re.M)
    write(OUT/'summary.json',summary)
    assert all(summary['sanitizer_diagnostic_file_presence'].values()), 'Expected original diagnostic files missing'
    assert not any(v['matches'] for v in summary['sanitizer_diagnostic_scan'].values())
    assert summary['tt_coherence_contract_actual_groups']==[str(clear['expected_tt_groups'])]
    assert summary['tt_coherence_actual_success_lines']==[clear['expected_tt_group_success_line']]
    assert summary['runtime_psqt_contract_actual_summaries']==[(str(clear['expected_runtime_psqt_checks']),'0')]
    assert summary['pawn_span_contract_actual_summaries']==[(str(clear['expected_pawn_span_checks']),'0')]
    assert summary['nearest_pawn_contract_actual_summaries']==[(str(clear['expected_nearest_sets']),str(clear['expected_nearest_checks']),'0')]
    assert summary['nearest_constexpr_assertions']==clear['expected_nearest_constexpr_assertions']
    assert summary['pv_metadata_contract_actual_summaries']==[(str(clear['expected_pv_metadata_assertions']),'0')]
    assert [row[0] for row in summary['pv_metadata_case_rows']]==['PV_nonPVhit','PV_PVhit','PV_nohit','nullwindow_TTcut','PV_abort_verification']
    binary_after={name:digest(BUILD/name) for name in binary_before}
    after=files(SOURCE)
    assert before==after
    assert binary_before==binary_after
    summary.update({"binary_sha256_before":binary_before,"binary_sha256_after":binary_after,
                    "source_files_unchanged":True,"status":"PASS","completed_utc":datetime.now(timezone.utc).isoformat()})
    write(OUT/"summary.json",summary)
    print("PASS "+profile+" full CTest 14/14; source and binary hashes unchanged",flush=True)
except Exception as exc:
    summary["binary_sha256_after_failure"] = {name:digest(BUILD/name) for name in ARTIFACT_NAMES if (BUILD/name).is_file()}
    summary["source_sha256_after_failure"] = files(SOURCE)
    summary["test_source_sha256_after_failure"]={n:h for n,h in files(SOURCE).items() if n.startswith("tests/")}
    summary["source_files_unchanged_after_failure"] = before == files(SOURCE)
    summary.update({"status":"FAILED","error":repr(exc),"completed_utc":datetime.now(timezone.utc).isoformat()})
    write(OUT/"summary.json",summary)
    raise
finally:
    for name in ["ownbook-regression.json", "Testing/Temporary/LastTest.log", "Testing/Temporary/LastTestsFailed.log", "Testing/Temporary/CTestCostData.txt", "uci-regression.log", "CMakeCache.txt", "compile_commands.json"]:
        original = BUILD/name
        if original.is_file():
            (OUT/("original-"+original.name)).write_bytes(original.read_bytes())
