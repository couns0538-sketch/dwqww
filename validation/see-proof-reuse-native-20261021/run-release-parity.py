#!/usr/bin/env python3
"""Bounded full56 cold/warm parity after separate first observed signature and Release14."""
from pathlib import Path
from datetime import datetime,timezone
import ctypes,hashlib,json,os,re,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from process_facts import cleanup
HERE=Path(__file__).resolve().parent
SOURCE=Path('/workspace/.cloud-setup/see-proof-reuse-native-source')
BUILD=Path('/workspace/.cloud-setup/see-proof-reuse-native-release')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree(path):return {str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()}
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text())
assert clear.get('authorized') is True and isinstance(clear.get('source_commit'),str), 'Root build clearance required'
gate=json.loads((HERE/'frozen-release-attempt1/summary.json').read_text())
assert gate['status']=='PASS' and gate['source_commit']==clear['source_commit'] and len(gate['ctest_names'])==14
assert clear.get('exact_search_parity_required') is True and clear.get('expected_cold_warm_searches')==56
signature=json.loads((HERE/'release-signature-wrapper-attempt1/summary.json').read_text());assert signature['status']=='PASS' and signature['source_commit']==clear['source_commit']
freeze=json.loads((HERE/'BENCH-SIGNATURE-FREEZE.json').read_text());assert freeze['source_commit']==clear['source_commit'] and freeze['nodes']==292545
protocol=json.loads((HERE/'PARITY-PROTOCOL.json').read_text())
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
OUT=HERE/'release-parity-wrapper-attempt1';OUT.mkdir(exist_ok=False)
ENV=os.environ.copy()
for name in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']:ENV.pop(name,None)
ENV['PYTHONDONTWRITEBYTECODE']='1'
inputs={('candidate/'+name):BUILD/name for name in gate['binary_sha256_after']}
inputs.update(baseline_engine=Path(protocol['engines']['baseline']),baseline_core=Path(protocol['baseline_core']),baseline_nnue_object=Path(protocol['baseline_nnue_object']),
              parity_driver=HERE/'search-parity.py',trusted_driver=HERE/'trusted-run-full-engine-tt.py',parity_protocol=HERE/'PARITY-PROTOCOL.json')
baseline_source=Path(protocol['baseline_public_source_root'])
for name in protocol['baseline_public_source_sha256']:inputs['baseline_public/'+name]=baseline_source/name
before={name:sha(path) for name,path in inputs.items()};source_before=tree(SOURCE);baseline_source_before=tree(baseline_source)
summary={'status':'RUNNING','source_commit':clear['source_commit'],'started_utc':datetime.now(timezone.utc).isoformat(),
 'input_paths':{name:str(path) for name,path in inputs.items()},'input_sha256_before':before,'source_sha256_before':source_before,
 'baseline_source_sha256_before':baseline_source_before,'steps':[],'bench_signature_freeze_sha256':sha(HERE/'BENCH-SIGNATURE-FREEZE.json'),'no_parent_red':True,'timing_comparison':False}
save(OUT/'summary.json',summary)
def run(label,command,timeout,stdin=None):
    proc=None;rc=None;error=None;timed=False;started=time.monotonic()
    if stdin is not None:(OUT/(label+'.stdin.bin')).write_bytes(stdin)
    with (OUT/(label+'.stdout.bin')).open('xb') as out,(OUT/(label+'.stderr.bin')).open('xb') as err:
        try:
            proc=subprocess.Popen(command,cwd=HERE.parents[1],env=ENV,stdout=out,stderr=err,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,start_new_session=True)
            try:proc.communicate(stdin,timeout=timeout);rc=proc.returncode
            except subprocess.TimeoutExpired:
                timed=True;error='command timeout';os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=10);rc=proc.returncode
        except BaseException as exc:error=repr(exc)
        finally:clean=cleanup(proc.pid) if proc else {'no_live_owned_processes':True,'not_started':True}
    facts={'command':command,'cwd':str(HERE.parents[1]),'timeout_seconds':timeout,'exit_code':rc,'error':error,'timed_out':timed,
       'pid':proc.pid if proc else None,'cleanup':clean,'elapsed_seconds_operational_only':time.monotonic()-started,
       'input_sha256_after':{name:sha(path) for name,path in inputs.items()},'source_sha256_after':tree(SOURCE),
       'baseline_source_sha256_after':tree(baseline_source),'stdout_sha256':sha(OUT/(label+'.stdout.bin')),'stderr_sha256':sha(OUT/(label+'.stderr.bin'))}
    summary['steps'].append({'label':label,**facts});save(OUT/(label+'-command.json'),facts);save(OUT/'summary.json',summary)
    assert rc==0 and not error and not timed and clean['no_live_owned_processes'] and not clean.get('unexpected_live_members_after_command'), label+' failed; facts saved'
    assert facts['input_sha256_after']==before and facts['source_sha256_after']==source_before and facts['baseline_source_sha256_after']==baseline_source_before
try:
    assert source_before==gate['source_sha256_after_tests']
    assert all(before['candidate/'+name]==value for name,value in gate['binary_sha256_after'].items())
    assert before['baseline_engine']==protocol['baseline_engine_sha256'] and before['baseline_core']==protocol['baseline_core_sha256']
    assert before['baseline_nnue_object']==protocol['baseline_nnue_object_sha256']
    assert before['candidate/CMakeFiles/forge_core.dir/src/nnue.cpp.o']==before['baseline_nnue_object'], 'Release NNUE object must remain byte-identical to matched parent23'
    public_actual={name:sha(SOURCE/name) for name in protocol['baseline_public_source_sha256']}
    summary['candidate_public_source_sha256']=public_actual;save(OUT/'summary.json',summary)
    board_actual={name:public_actual[name] for name in protocol['unchanged_board_source_sha256']}
    summary['candidate_board_source_sha256']=board_actual
    summary['candidate_evaluator_file_byte_equality_required']=False
    save(OUT/'summary.json',summary)
    assert board_actual==protocol['unchanged_board_source_sha256'], 'Unchanged Board source contract changed'
    assert all(before['baseline_public/'+name]==value for name,value in protocol['baseline_public_source_sha256'].items())
    run('cold-warm-parity',['/workspace/.cloud-setup/venv/bin/python','-B',str(HERE/'search-parity.py')],1200)
    inner=json.loads((HERE/'search-parity-attempt1/summary.json').read_text())
    summary['parity_summary_status']=inner['status'];summary['parity_comparisons']=inner['comparisons'];save(OUT/'summary.json',summary)
    assert inner['status']=='passed' and len(inner['sessions'])==28 and len(inner['comparisons'])==14
    assert all(item['cold_exact'] and item['warm_exact'] for item in inner['comparisons'])
    pattern=re.compile(rb'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|ThreadSanitizer|runtime error:',re.I)
    logs=[OUT/'cold-warm-parity.stdout.bin',OUT/'cold-warm-parity.stderr.bin',*sorted((HERE/'search-parity-attempt1').glob('process-*/stderr.bin'))]
    summary['sanitizer_scan']={str(path):{'sha256':sha(path),'matches':[m.group().decode('utf-8','replace') for m in pattern.finditer(path.read_bytes())]} for path in logs}
    save(OUT/'summary.json',summary)
    assert not any(item['matches'] for item in summary['sanitizer_scan'].values())
    summary['status']='PASS'
except BaseException as exc:summary.update(status='FAILED',error=repr(exc));raise
finally:
    summary.update(input_sha256_after={name:sha(path) for name,path in inputs.items()},source_sha256_after=tree(SOURCE),baseline_source_sha256_after=tree(baseline_source),completed_utc=datetime.now(timezone.utc).isoformat())
    save(OUT/'summary.json',summary)
print(json.dumps({'status':summary['status'],'actual_default_bench11_nodes':freeze['nodes'],'exact_cold_warm_pairs':14,'total_depth_searches':56}))
