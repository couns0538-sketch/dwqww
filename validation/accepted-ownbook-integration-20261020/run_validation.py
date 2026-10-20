#!/usr/bin/env python3
"""Bounded exact accepted-lineage OwnBook validation; no source/Git mutations."""
from pathlib import Path
import ctypes
import datetime
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time

REPO=Path('/workspace/dwqww')
OUT=REPO/'validation/accepted-ownbook-integration-20261020'
BASE=Path('/workspace/.cloud-setup')
COMMITS={'baseline':'356e863dbd86d2ce24b8ee9486d7406f1d525480','candidate':'5101c2529d386b7c3a04ba9156a69ee34df6bb43'}
CMAKE='/workspace/.cloud-setup/venv/bin/cmake'
CTEST='/workspace/.cloud-setup/venv/bin/ctest'
CXX='/usr/bin/g++-14'
PYTHON=sys.executable
TEST_REL='validation/hourly/2026-10-20-ownbook-native/test_ownbook.py'
COMMON_FLAGS='-fno-fast-math -ffp-contract=off -fno-lto'
EXPECTED_TESTS={'forge_tests','match_tool_tests','uci_regression','ponder_regression'}
ENV=os.environ.copy();ENV['PYTHONDONTWRITEBYTECODE']='1'
assert sys.dont_write_bytecode, 'Invoke with Python -B / PYTHONDONTWRITEBYTECODE=1'
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0, 'Need child-subreaper for owned orphan cleanup'

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def load(path):return json.loads(path.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def source(label):return BASE/('accepted-ownbook-'+label+'-source')
def files(root):return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}
def source_identity(label):
    actual=files(source(label));expected=load(OUT/(label+'-source.json'))['files']
    expected={n:{'sha256':r['sha256'],'bytes':r['bytes']} for n,r in expected.items()}
    return {'source_commit':COMMITS[label],'sha256':actual,'matches_frozen_source':actual==expected}
def build_identity(build):
    names=['forge','forge_tests','forge_bench','libforge_core.a','CMakeCache.txt','compile_commands.json','CTestTestfile.cmake']
    return {name:({'sha256':sha(build/name),'bytes':(build/name).stat().st_size} if (build/name).is_file() else None) for name in names}
def group_members(pgid):
    result=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            raw=(p/'stat').read_text();end=raw.rfind(')');fields=raw[end+2:].split()
            if int(fields[2])==pgid:result.append({'pid':int(p.name),'state':fields[0]})
        except (OSError,ValueError,IndexError):pass
    return result

def cleanup(pgid):
    before=group_members(pgid);actions=[];reaped=[]
    def reap():
        while True:
            try:pid,status=os.waitpid(-1,os.WNOHANG)
            except ChildProcessError:break
            if pid==0:break
            reaped.append({'pid':pid,'wait_status':status})
    live=lambda:[r for r in group_members(pgid) if r['state']!='Z']
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        if not live():break
        try:os.killpg(pgid,sig);actions.append(signal.Signals(sig).name)
        except ProcessLookupError:pass
        until=time.monotonic()+2
        while time.monotonic()<until and live():reap();time.sleep(.02)
    reap();after=group_members(pgid)
    return {'group_id':pgid,'before':before,'actions':actions,'reaped_children':reaped,'after':after,'no_live_owned_processes':not any(r['state']!='Z' for r in after),'unexpected_live_members_after_command':any(r['state']!='Z' for r in before)}

def run_command(directory,label,command,deadline,environment,label_source=None,build=None):
    before={'source':source_identity(label_source) if label_source else None,'build':build_identity(build) if build else None}
    started=utc();t=time.monotonic();remaining=deadline-t
    if remaining<=0:raise TimeoutError('Phase1200s budget exhausted before '+label)
    stdout=directory/(label+'.stdout');stderr=directory/(label+'.stderr');p=None;error=None;timed_out=False;rc=None
    try:
        with stdout.open('xb') as out,stderr.open('xb') as err:
            p=subprocess.Popen(command,cwd=str(REPO),env=environment,stdout=out,stderr=err,start_new_session=True)
            try:rc=p.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out=True;error='Phase deadline reached';os.killpg(p.pid,signal.SIGKILL);rc=p.wait(timeout=10)
    except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        cleaned=cleanup(p.pid) if p else {'not_started':True,'no_live_owned_processes':True}
        after={'source':source_identity(label_source) if label_source else None,'build':build_identity(build) if build else None}
        record={'label':label,'command':command,'cwd':str(REPO),'started_utc':started,'completed_utc':utc(),'return_code':rc,'phase_timeout_remaining_seconds':remaining,'elapsed_seconds_diagnostic_only':time.monotonic()-t,'timed_out':timed_out,'error':error,'pid':p.pid if p else None,'cleanup':cleaned,'before':before,'after':after,'stdout_sha256':sha(stdout) if stdout.exists() else None,'stderr_sha256':sha(stderr) if stderr.exists() else None}
        save(directory/(label+'-command.json'),record)
    assert rc==0 and error is None and not timed_out, label+' failed: '+str(record)
    assert cleaned['no_live_owned_processes'] and not cleaned.get('unexpected_live_members_after_command',False), 'Unexpected owned process cleanup: '+label
    if label_source:assert before['source']['matches_frozen_source'] and after['source']['matches_frozen_source'],'Source changed: '+label
    if build and label in ['ctest-discovery','ctest','ownbook']:
        for name in ['forge','forge_tests','forge_bench','libforge_core.a']:assert before['build'][name]==after['build'][name], 'Binary/core changed: '+label+' '+name
    return record

def export_sources():
    assert not (OUT/'PROTOCOL.json').exists(),'Never reuse an existing validation run'
    for label,commit in COMMITS.items():
        root=source(label);assert not root.exists(),root;root.mkdir()
        selectors=['CMakeLists.txt','LICENSE','src','include','tests','bench','tools']
        if label=='candidate':selectors.append(TEST_REL)
        rows=git('ls-tree','-r',commit,'--',*selectors).decode().splitlines();manifest={}
        for row in rows:
            metadata,name=row.split('\t',1);mode,kind,blob=metadata.split();assert kind=='blob'
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',commit+':'+name));p.chmod(int(mode,8)&0o777)
            manifest[name]={'sha256':sha(p),'bytes':p.stat().st_size,'git_mode':mode,'git_blob':blob}
        save(OUT/(label+'-source.json'),{'commit':commit,'tree':git('rev-parse',commit+'^{tree}').decode().strip(),'root':str(root),'selectors':selectors,'tracked_bytecode_preserved_unmodified':True,'files':manifest})
    a=load(OUT/'baseline-source.json')['files'];b=load(OUT/'candidate-source.json')['files'];changed=sorted(n for n in a if a[n]['sha256']!=b[n]['sha256'])
    assert changed==['src/uci.cpp'];assert sorted(set(b)-set(a))==[TEST_REL]
    save(OUT/'SOURCE-DELTA.json',{'changed_required_existing_files':changed,'added_required_files':[TEST_REL],'candidate_original_test_sha256':b[TEST_REL]['sha256'],'production_change':'Exact existing OwnBook one-line condition; no reimplementation or source edits.'})

def command_set(label,asan=False):
    profile='candidate-asan' if asan else label+'-release';build=BASE/('accepted-ownbook-'+profile);directory=OUT/(profile+'-attempt1');ownbook=directory/'ownbook-original'
    flags=COMMON_FLAGS+(' -g -fno-pie' if asan else '')
    configure=[CMAKE,'-S',str(source(label)),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER='+CXX,'-DPython3_EXECUTABLE='+PYTHON,'-DFORGE_NATIVE=OFF','-DFORGE_ENABLE_SANITIZERS='+('ON' if asan else 'OFF'),'-DCMAKE_CXX_FLAGS='+flags,'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    if asan:configure.append('-DCMAKE_EXE_LINKER_FLAGS=-no-pie')
    cmds=[('configure',configure),('build',[CMAKE,'--build',str(build),'--parallel','2']),('ctest-discovery',[CTEST,'--test-dir',str(build),'--show-only=json-v1']),('ctest',[CTEST,'--test-dir',str(build),'--output-on-failure','--parallel','1','--timeout','300']),('ownbook',[PYTHON,'-B',str(source('candidate')/TEST_REL),str(build/'forge'),'--expect-leak','yes' if label=='baseline' else 'no','--out',str(ownbook)])]
    return profile,build,directory,ownbook,cmds

def profile(label,asan=False):
    name,build,directory,ownbook,commands=command_set(label,asan);assert not build.exists() and not directory.exists() and not ownbook.exists();directory.mkdir()
    environment=ENV.copy()
    if asan:environment.update(ASAN_OPTIONS='halt_on_error=1:abort_on_error=1:detect_leaks=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    deadline=time.monotonic()+1200;steps=[];error=None;before={'source':source_identity(label),'build':build_identity(build)}
    try:
        for step,command in commands:
            if step=='ownbook':assert not ownbook.exists(),'Fresh original test output required'
            steps.append(run_command(directory,step,command,deadline,environment,label,build))
            if step=='ctest-discovery':
                discovery=json.loads((directory/'ctest-discovery.stdout').read_text());assert {r['name'] for r in discovery['tests']}==EXPECTED_TESTS and len(discovery['tests'])==4
            if step=='ctest':assert re.search(r'100% tests passed, 0 tests failed out of 4',(directory/'ctest.stdout').read_text())
        result=load(ownbook/'result.json');expected=label=='baseline'
        assert result['result']=='PASS' and result['expected_baseline_leak']==expected
        assert result['disabled_first']==result['disabled_after_toggle']==expected and result['enabled'] is True and len(result['tests'])==5
        text=(ownbook/'raw_uci.log').read_text();assert '> go depth 2' in text and text.count('> go movetime 150')==3
        if asan:
            diagnostics=re.compile(r'AddressSanitizer|LeakSanitizer|runtime error:|UndefinedBehaviorSanitizer|SUMMARY:.*Sanitizer')
            scan=[directory/'ctest.stdout',directory/'ctest.stderr',directory/'ownbook.stdout',directory/'ownbook.stderr',ownbook/'raw_uci.log',build/'Testing/Temporary/LastTest.log']
            assert not any(diagnostics.search(p.read_text(errors='replace')) for p in scan if p.exists()),'Sanitizer diagnostic found'
        assert sha(source('candidate')/TEST_REL)==load(OUT/'candidate-source.json')['files'][TEST_REL]['sha256']
    except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        after={'source':source_identity(label),'build':build_identity(build)}
        report={'phase':name,'status':'PASS' if error is None else 'FAIL_STOP_NO_RETRY','error':error,'source_commit':COMMITS[label],'candidate_original_test_commit':COMMITS['candidate'],'candidate_original_test_sha256':sha(source('candidate')/TEST_REL),'expected_baseline_leak':label=='baseline','asan_ubsan':asan,'timeout_seconds_total_phase':1200,'steps':steps,'before':before,'after':after,'environment_subset':{k:environment[k] for k in ['PYTHONDONTWRITEBYTECODE','ASAN_OPTIONS','UBSAN_OPTIONS'] if k in environment},'original_ownbook_result':load(ownbook/'result.json') if (ownbook/'result.json').exists() else None,'raw_uci_transcript':str(ownbook/'raw_uci.log'),'transcript_scope':'Original script directional text transcript with stdout/stderr combined; not raw byte capture.','scope':'Specific external-book toggle/depth contract on exact accepted lineage; no universal legality,strength,speed or integration acceptance.'}
        save(directory/'RESULTS.json',report)
        if (build/'compile_commands.json').exists():
            rows=load(build/'compile_commands.json');assert all('-fno-fast-math' in r['command'] and '-ffp-contract=off' in r['command'] and '-fno-lto' in r['command'] for r in rows)
        print(json.dumps({'phase':name,'status':report['status'],'error':error,'result_path':str(directory/'RESULTS.json'),'test_command':commands[-1][1],'original_ownbook_result':report['original_ownbook_result']},indent=2),flush=True)
    if error:raise RuntimeError(name+' failed without retry: '+error)
    return report

def main():
    export_sources()
    plans=[command_set('baseline'),command_set('candidate'),command_set('candidate',True)]
    protocol={'created_utc':utc(),'commits':COMMITS,'gcc_path':CXX,'gcc_sha256':sha(Path(CXX)),'cmake_path':CMAKE,'cmake_sha256':sha(Path(CMAKE)),'python_path':PYTHON,'python_sha256':sha(Path(PYTHON)),'common_release_flags':COMMON_FLAGS,'forge_native':False,'jobs':2,'phases_serial':True,'phase_timeout_seconds':1200,'no_retries':True,'candidate_original_test':str(source('candidate')/TEST_REL),'candidate_original_test_sha256':sha(source('candidate')/TEST_REL),'asan_additional_flags':'-g -fno-pie; linker-no-pie; fatal ASan/UBSan + leak checks, no disabled sanitizer checks','commands':{name:commands for name,_,_,_,commands in plans},'rationale':'New local exact accepted-lineage evidence; priorCI metadataSUCCESS does not provide accessible rawartifact. No proof transfer from17.','process_policy':'Per-command owned new session/process group; local child-subreaper; preserve timeout/failure; TERM/KILL/reap owned leftovers only; unexpected live leftovers fail gate.','scope':'No branch/Git/source edit, integration, benchmark,match,Elo orNPS claim.'}
    save(OUT/'PROTOCOL.json',protocol);save(OUT/'TESTCOMMANDS.json',{'phases':protocol['commands'],'help_command':[PYTHON,'-B',str(source('candidate')/TEST_REL),'--help']})
    (OUT/'TESTCOMMANDS.md').write_text('\n\n'.join('**'+name+'**\n\n'+'\n'.join('`'+shlex.join(command)+'`' for _,command in commands) for name,_,_,_,commands in plans)+'\n')
    preflight=OUT/'preflight';preflight.mkdir();deadline=time.monotonic()+1200
    run_command(preflight,'gcc-version',[CXX,'--version'],deadline,ENV)
    assert '14.2.0' in (preflight/'gcc-version.stdout').read_text()
    run_command(preflight,'original-test-help',[PYTHON,'-B',str(source('candidate')/TEST_REL),'--help'],deadline,ENV,'candidate')
    results=[]
    try:
        results.append(profile('baseline'));results.append(profile('candidate'));results.append(profile('candidate',True))
        save(OUT/'SUMMARY.json',{'status':'PASS_ALL_LOCAL_ACCEPTED_LINEAGE_GATES','completed_utc':utc(),'phases':[{k:r[k] for k in ['phase','status','source_commit','original_ownbook_result']} for r in results],'all_source_exports_unchanged':all(source_identity(n)['matches_frozen_source'] for n in COMMITS),'original_candidate_test_unmodified':True,'no_retries':True,'integration_performed':False,'scope':'12originalCTest suites +15originalOwnBook assertions across three profiles; bounded correctness contract only, no strength/performance or integration decision.'})
    except BaseException as exc:
        save(OUT/'SUMMARY.json',{'status':'STOPPED_NO_RETRY','error':type(exc).__name__+': '+str(exc),'completed_utc':utc(),'completed_phases':[r['phase'] for r in results],'source_identities_after_failure':{n:source_identity(n) for n in COMMITS},'integration_performed':False});raise

if __name__=='__main__':main()
