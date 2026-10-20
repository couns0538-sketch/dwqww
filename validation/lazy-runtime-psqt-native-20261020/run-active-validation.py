#!/usr/bin/env python3
"""One bounded inherited positive-node active-UCI session after full TSan PASS."""
from pathlib import Path
import ctypes, hashlib, json, os, signal, subprocess, time
from datetime import datetime, timezone
import sys
sys.dont_write_bytecode=True
from process_facts import cleanup
HERE=Path(__file__).resolve().parent
SOURCE=Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-source')
BUILD=Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-tsan')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*')) if x.is_file()}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text())
assert clear.get('authorized') is True and isinstance(clear.get('source_commit'),str), 'Root clearance required'
gate=json.loads((HERE/'frozen-tsan-attempt1/summary.json').read_text())
assert gate['status']=='PASS' and len(gate['ctest_names'])==11 and gate['source_commit']==clear['source_commit']
assert tree(SOURCE)==gate['source_sha256_after_tests'], 'Frozen source changed since full TSan suite'
assert all(sha(BUILD/name)==digest for name,digest in gate['binary_sha256_after'].items()), 'TSan artifacts changed before active session'
OUT=HERE/'active-uci-wrapper-attempt1';OUT.mkdir(exist_ok=False)
ENV=os.environ.copy()
for k in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']:ENV.pop(k,None)
ENV.update(PYTHONDONTWRITEBYTECODE='1',TSAN_OPTIONS='halt_on_error=1:exitcode=66')
inputs={'engine':BUILD/'forge','core':BUILD/'libforge_core.a','runtime_psqt_test_object':BUILD/'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.o','runtime_psqt_test_executable':BUILD/'forge_runtime_psqt_tests',
        'active_driver':HERE/'active-uci-edges.py','trusted_driver':HERE/'trusted-run-full-engine-tt.py'}
before={k:sha(p) for k,p in inputs.items()};source_before=tree(SOURCE)
cmd=['/workspace/.cloud-setup/venv/bin/python','-B',str(HERE/'active-uci-edges.py'),'--engine',str(BUILD/'forge'),'--output',str(HERE/'active-uci-tsan-attempt1'),'--session-timeout','90']
facts={'status':'RUNNING','source_commit':gate['source_commit'],'command':cmd,'cwd':str(HERE.parents[1]),'timeout_seconds':120,
 'started_utc':datetime.now(timezone.utc).isoformat(),'tsan_options':ENV['TSAN_OPTIONS'],'tsan_disabled_checks':[],
 'input_sha256_before':before,'source_sha256_before':source_before,'protocol':json.loads((HERE/'ACTIVE-UCI-PROTOCOL.json').read_text())}
save(OUT/'COMMAND.json',facts)
proc=None;error=None;timed=False;rc=None;started=time.monotonic()
with (OUT/'stdout.bin').open('xb') as out,(OUT/'stderr.bin').open('xb') as err:
    try:
        proc=subprocess.Popen(cmd,cwd=HERE.parents[1],env=ENV,stdout=out,stderr=err,start_new_session=True)
        try:rc=proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            timed=True;error='outer active-session timeout';os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait(timeout=10)
    except BaseException as exc:error=repr(exc)
    finally:clean=cleanup(proc.pid) if proc else {'no_live_owned_processes':True,'not_started':True}
facts.update(exit_code=rc,error=error,timed_out=timed,cleanup=clean,pid=proc.pid if proc else None,elapsed_seconds_operational_only=time.monotonic()-started,
 input_sha256_after={k:sha(p) for k,p in inputs.items()},source_sha256_after=tree(SOURCE),
 stdout_sha256=sha(OUT/'stdout.bin'),stderr_sha256=sha(OUT/'stderr.bin'),completed_utc=datetime.now(timezone.utc).isoformat(),status='FACTS_CAPTURED')
save(OUT/'COMMAND.json',facts)
try:
    assert rc==0 and not error and not timed and clean['no_live_owned_processes'] and not clean.get('unexpected_live_members_after_command')
    assert before==facts['input_sha256_after'] and source_before==facts['source_sha256_after']
    inner=json.loads((HERE/'active-uci-tsan-attempt1/summary.json').read_text())
    assert inner['status']=='passed' and inner['completed_all_scenarios'] and len(inner['session']['searches'])==8
    facts['status']='PASS'
except BaseException as exc:facts.update(status='FAILED',assertion_error=repr(exc));raise
finally:save(OUT/'COMMAND.json',facts)
print(json.dumps({'status':facts['status'],'active_uci_scenarios':8,'tsan_options':ENV['TSAN_OPTIONS']}))
