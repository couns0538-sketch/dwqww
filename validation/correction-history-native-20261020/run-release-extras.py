#!/usr/bin/env python3
"""Single-attempt same-object parent contract RED and raw Release bench capture."""
from pathlib import Path
import ctypes, hashlib, json, os, re, signal, subprocess, time
from datetime import datetime, timezone
from process_facts import cleanup

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SOURCE=Path('/workspace/.cloud-setup/correction-history-native-source')
BUILD=Path('/workspace/.cloud-setup/correction-history-native-release')
PARENT=Path('/workspace/.cloud-setup/forge-promotion-release/libforge_core.a')
OBJECT=BUILD/'CMakeFiles/forge_correction_history_tests.dir/tests/correction_history_tests.cpp.o'
RED=Path('/workspace/.cloud-setup/correction-history-native-parent-red')
REV='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
FLAGS=['-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto','-O3','-DNDEBUG']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*')) if x.is_file()}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
assert json.loads((HERE/'frozen-release-attempt1/summary.json').read_text())['status']=='PASS'
assert not RED.exists()
OUT=HERE/'release-extras-attempt1';OUT.mkdir(exist_ok=False)
ENV=os.environ.copy()
for k in ['ASAN_OPTIONS','UBSAN_OPTIONS','TSAN_OPTIONS','LSAN_OPTIONS']:ENV.pop(k,None)
ENV['PYTHONDONTWRITEBYTECODE']='1'
before=tree(SOURCE)
inputs={'parent_core':PARENT,'candidate_test_object':OBJECT,'candidate_engine':BUILD/'forge','candidate_core':BUILD/'libforge_core.a'}
identities={k:sha(p) for k,p in inputs.items()}
summary={'status':'RUNNING','source_commit':REV,'started_utc':datetime.now(timezone.utc).isoformat(),
 'input_paths':{k:str(p) for k,p in inputs.items()},'input_sha256_before':identities,'source_sha256_before':before,'steps':[],
 'parent_contract_scope':'Expected RED for the newly selected residual-increment behavior contract; this is not evidence of an old correctness bug.',
 'performance_scope':'One uncalibrated bench11 logical signature; no speed, NPS, Elo or physical-hardware comparison.'}
save(OUT/'summary.json',summary)
def run(label,cmd,expected=0,stdin=None,timeout=1200):
    if stdin is not None:(OUT/(label+'.stdin.bin')).write_bytes(stdin)
    proc=None;error=None;timed=False;rc=None;start=time.monotonic()
    with (OUT/(label+'.stdout.bin')).open('xb') as out,(OUT/(label+'.stderr.bin')).open('xb') as err:
        try:
            proc=subprocess.Popen(cmd,cwd=REPO,env=ENV,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
            try:proc.communicate(stdin,timeout=timeout);rc=proc.returncode
            except subprocess.TimeoutExpired:
                timed=True;error='command timeout';os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=10);rc=proc.returncode
        except BaseException as exc:error=repr(exc)
        finally:facts=cleanup(proc.pid) if proc else {'no_live_owned_processes':True,'not_started':True}
    step={'label':label,'command':cmd,'cwd':str(REPO),'expected_exit_code':expected,'exit_code':rc,'error':error,'timed_out':timed,
          'elapsed_seconds':time.monotonic()-start,'timeout_seconds':timeout,'pid':proc.pid if proc else None,'cleanup':facts,
          'input_sha256_after':{k:sha(p) for k,p in inputs.items()},'source_sha256_after':tree(SOURCE),
          'stdout_sha256':sha(OUT/(label+'.stdout.bin')),'stderr_sha256':sha(OUT/(label+'.stderr.bin'))}
    summary['steps'].append(step);save(OUT/(label+'-command.json'),step);save(OUT/'summary.json',summary)
    if rc!=expected or error or timed or not facts['no_live_owned_processes'] or facts.get('unexpected_live_members_after_command'):
        raise RuntimeError(label+' failed; facts saved before assertion')
    if step['input_sha256_after']!=identities or step['source_sha256_after']!=before:raise RuntimeError(label+' changed inputs')
try:
    assert identities['parent_core']=='d772f89980edb0e9f7fd5da99ef5c7bdb402aa8319082907b2bf31180359bd12'
    parent_headers=subprocess.check_output(['git','ls-tree','-r','--format=%(path) %(objectname)','47f0560221d986e41a309853e1295c557fcf5bf6','include'],cwd=REPO)
    candidate_headers=subprocess.check_output(['git','ls-tree','-r','--format=%(path) %(objectname)',REV,'include'],cwd=REPO)
    save(OUT/'ABI-PROVENANCE.json',{'compiler':'/usr/bin/g++-14','flags':FLAGS,'candidate_headers_tree':candidate_headers.decode(),
      'parent_headers_tree':parent_headers.decode(),'headers_identical':parent_headers==candidate_headers,
      'test_object_recompiled_for_parent':False,'parent_core_rebuilt':False,
      'candidate_original_link_command':(BUILD/'CMakeFiles/forge_correction_history_tests.dir/link.txt').read_text(),
      'parent_original_link_command':Path('/workspace/.cloud-setup/forge-promotion-release/CMakeFiles/forge_tests.dir/link.txt').read_text()})
    assert parent_headers==candidate_headers
    run('link-parent-red',['/usr/bin/g++-14',*FLAGS,str(OBJECT),str(PARENT),'-pthread','-o',str(RED)])
    summary['parent_red_executable_sha256_before']=sha(RED);save(OUT/'summary.json',summary)
    run('parent-contract-red',[str(RED)],expected=1,timeout=30)
    summary['parent_red_executable_sha256_after']=sha(RED)
    redtext=(OUT/'parent-contract-red.stdout.bin').read_text()
    summary['parent_contract_actual_summaries']=re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$',redtext,re.M)
    summary['parent_contract_actual_fail_lines']=[s for s in redtext.splitlines() if s.startswith('FAIL ')]
    save(OUT/'summary.json',summary)
    assert summary['parent_contract_actual_summaries']==[('54','17')]
    assert len(summary['parent_contract_actual_fail_lines'])==17
    assert summary['parent_red_executable_sha256_before']==summary['parent_red_executable_sha256_after']
    run('bench11',[str(BUILD/'forge')],stdin=b'bench 11\nquit\n',timeout=30)
    sig=re.findall(rb'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',(OUT/'bench11.stdout.bin').read_bytes(),re.M)
    summary['actual_bench11_signatures']=[int(x) for x in sig];save(OUT/'summary.json',summary)
    assert len(sig)==1 and int(sig[0])>0
    summary['status']='PASS'
except BaseException as exc:
    summary.update(status='FAILED',error=repr(exc));raise
finally:
    summary['input_sha256_after']={k:sha(p) for k,p in inputs.items()}
    summary['source_sha256_after']=tree(SOURCE)
    summary['completed_utc']=datetime.now(timezone.utc).isoformat()
    if RED.is_file():summary['parent_red_executable_sha256_final']=sha(RED)
    save(OUT/'summary.json',summary)
print(json.dumps({'status':summary['status'],'expected_parent_contract_failures':17,'actual_bench11_nodes':summary['actual_bench11_signatures'][0]}))
