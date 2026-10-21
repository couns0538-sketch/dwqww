#!/usr/bin/env python3
"""One first actual frozen23 benchmark capture after Release14; no inherited search signature or equality gate."""
from pathlib import Path
from datetime import datetime,timezone
import ctypes,hashlib,json,os,re,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from process_facts import cleanup
HERE=Path(__file__).resolve().parent;SOURCE=Path('/workspace/.cloud-setup/tt-refresh-native-source');BUILD=Path('/workspace/.cloud-setup/tt-refresh-native-release')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text());assert clear.get('authorized') is True and isinstance(clear.get('source_commit'),str), 'Root frozen23 clearance required'
assert clear.get('exact_search_parity_required') is False and clear.get('observational_cold_warm_searches')==0
assert clear.get('expected_bench11_nodes') is None and clear.get('benchmark_signature_mode')=='FIRST_CAPTURE_EXCLUSIVE_FREEZE'
gate=json.loads((HERE/'frozen-release-attempt1/summary.json').read_text());assert gate['status']=='PASS' and gate['source_commit']==clear['source_commit'] and len(gate['ctest_names'])==14
assert gate['pv_metadata_contract_actual_summaries']==[['56','0']]
protocol=json.loads((HERE/'RELEASE-SIGNATURE-PROTOCOL.json').read_text());assert protocol['schema']=='tt-refresh-release-signature-v1' and protocol['default_bench11_expected_nodes'] is None and protocol['benchmark_signature_mode']=='FIRST_CAPTURE_EXCLUSIVE_FREEZE'
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
assert not (HERE/'BENCH-SIGNATURE-FREEZE.json').exists() and not (HERE/'BENCH-SIGNATURE-FREEZE.json').is_symlink(), 'Refusing to capture over an existing first benchmark freeze'
OUT=HERE/'release-signature-wrapper-attempt1';OUT.mkdir(exist_ok=False)
ENV=os.environ.copy()
for key in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']:ENV.pop(key,None)
ENV['PYTHONDONTWRITEBYTECODE']='1'
baseline_source=Path(protocol['baseline_source_root'])
inputs={('candidate/'+n):BUILD/n for n in gate['binary_sha256_after']}
inputs.update(baseline_engine=Path(protocol['baseline_engine']),baseline_core=Path(protocol['baseline_core']),baseline_nnue_object=Path(protocol['baseline_nnue_object']),release_signature_protocol=HERE/'RELEASE-SIGNATURE-PROTOCOL.json')
for n in protocol['protected_nonsearch_source_sha256']:inputs['baseline_source/'+n]=baseline_source/n
before={n:sha(f) for n,f in inputs.items()};source_before=tree(SOURCE);baseline_before=tree(baseline_source)
summary={'status':'RUNNING','source_commit':clear['source_commit'],'started_utc':datetime.now(timezone.utc).isoformat(),'input_paths':{n:str(f) for n,f in inputs.items()},'input_sha256_before':before,'source_sha256_before':source_before,'baseline_source_sha256_before':baseline_before,'steps':[],'bench11_expected_nodes':None,'benchmark_signature_mode':'FIRST_CAPTURE_EXCLUSIVE_FREEZE','exact_search_parity_required':False,'observational_cold_warm_searches':0,'timing_comparison':False}
save(OUT/'summary.json',summary)
child=None;rc=None;error=None;timed=False;started=time.monotonic();stdin=b'bench 11\nquit\n';command=[str(BUILD/'forge')]
try:
    assert source_before==gate['source_sha256_after_tests'] and len(source_before)==77 and len(baseline_before)==77
    assert all(before['candidate/'+n]==h for n,h in gate['binary_sha256_after'].items())
    assert before['baseline_engine']==protocol['baseline_engine_sha256'] and before['baseline_core']==protocol['baseline_core_sha256'] and before['baseline_nnue_object']==protocol['baseline_nnue_object_sha256']
    assert before['candidate/CMakeFiles/forge_core.dir/src/nnue.cpp.o']==before['baseline_nnue_object']
    for n,h in protocol['protected_nonsearch_source_sha256'].items():assert before['baseline_source/'+n]==sha(SOURCE/n)==h,n
    (OUT/'bench11.stdin.bin').write_bytes(stdin)
    with (OUT/'bench11.stdout.bin').open('xb') as out,(OUT/'bench11.stderr.bin').open('xb') as err:
        try:
            child=subprocess.Popen(command,cwd=HERE.parents[1],env=ENV,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True)
            try:child.communicate(stdin,timeout=30);rc=child.returncode
            except subprocess.TimeoutExpired:timed=True;error='benchmark signature timeout';os.killpg(child.pid,signal.SIGKILL);child.communicate(timeout=10);rc=child.returncode
        except BaseException as exc:error=repr(exc)
        finally:clean=cleanup(child.pid) if child else {'no_live_owned_processes':True,'not_started':True}
    facts={'command':command,'cwd':str(HERE.parents[1]),'timeout_seconds':30,'pid':child.pid if child else None,'exit_code':rc,'error':error,'timed_out':timed,'cleanup':clean,'elapsed_seconds_operational_only':time.monotonic()-started,'stdin_sha256':sha(OUT/'bench11.stdin.bin'),'stdout_sha256':sha(OUT/'bench11.stdout.bin'),'stderr_sha256':sha(OUT/'bench11.stderr.bin'),'input_sha256_after':{n:sha(f) for n,f in inputs.items()},'source_sha256_after':tree(SOURCE),'baseline_source_sha256_after':tree(baseline_source)}
    summary['steps'].append({'label':'bench11',**facts});save(OUT/'bench11-command.json',facts);save(OUT/'summary.json',summary)
    assert rc==0 and not error and not timed and clean['no_live_owned_processes'] and not clean.get('unexpected_live_members_after_command'), 'Benchmark process fault, facts retained'
    assert facts['input_sha256_after']==before and facts['source_sha256_after']==source_before and facts['baseline_source_sha256_after']==baseline_before
    signatures=re.findall(rb'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',(OUT/'bench11.stdout.bin').read_bytes(),re.M)
    summary['actual_bench11_signatures']=[int(v) for v in signatures];save(OUT/'summary.json',summary)
    assert len(summary['actual_bench11_signatures'])==1 and summary['actual_bench11_signatures'][0]>0, 'Exactly one actual positive benchmark signature required'
    pattern=re.compile(rb'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|ThreadSanitizer|runtime error:',re.I)
    summary['sanitizer_scan']={str(f):{'sha256':sha(f),'matches':[m.group().decode('utf-8','replace') for m in pattern.finditer(f.read_bytes())]} for f in [OUT/'bench11.stdout.bin',OUT/'bench11.stderr.bin']};save(OUT/'summary.json',summary)
    assert not any(row['matches'] for row in summary['sanitizer_scan'].values())
    freeze={'status':'FROZEN_FIRST_ACTUAL_RELEASE_BENCH11','source_commit':clear['source_commit'],'benchmark_depth':11,'nodes':summary['actual_bench11_signatures'][0],'release_engine_sha256':before['candidate/forge'],'release_core_sha256':before['candidate/libforge_core.a'],'raw_stdin_sha256':facts['stdin_sha256'],'raw_stdout_sha256':facts['stdout_sha256'],'raw_stderr_sha256':facts['stderr_sha256'],'input_sha256_before':before,'input_sha256_after':facts['input_sha256_after'],'captured_utc':datetime.now(timezone.utc).isoformat(),'signature_processes':1,'timing_or_elo_inference':False}
    with (HERE/'BENCH-SIGNATURE-FREEZE.json').open('x') as stream:json.dump(freeze,stream,indent=2);stream.write('\n')
    summary['bench_signature_freeze_path']='BENCH-SIGNATURE-FREEZE.json';summary['bench_signature_freeze_sha256']=sha(HERE/'BENCH-SIGNATURE-FREEZE.json')
    summary['status']='PASS'
except BaseException as exc:summary.update(status='FAILED',error=repr(exc));raise
finally:
    summary.update(input_sha256_after={n:sha(f) for n,f in inputs.items()},source_sha256_after=tree(SOURCE),baseline_source_sha256_after=tree(baseline_source),completed_utc=datetime.now(timezone.utc).isoformat());save(OUT/'summary.json',summary)
print(json.dumps({'status':summary['status'],'actual_default_bench11_nodes':summary['actual_bench11_signatures'][0],'exact_parent_search_parity_required':False,'observational_searches':0,'timing_or_elo_inference':False}))
