"""Owned bounded Release stages. Preserve observations before verdict and on cleanup."""
from pathlib import Path
import importlib.util,json,hashlib,subprocess,sys,os,time
REPO=Path('/workspace/dwqww');ROOT=REPO/'validation/lazy-runtime-psqt-20261020';BUILD=Path('/workspace/.cloud-setup/lazy-runtime-psqt-release')
spec=importlib.util.spec_from_file_location('owned_runtime_cleanup',REPO/'.github/hosted-correction-history-strength/run_hosted.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE_NAMES=sorted(set(json.loads((REPO/'validation/correction-history-native-20261020/frozen-source-fc51e43-files.json').read_text()))|{'tests/runtime_psqt_tests.cpp'})
def source_snapshot():return {name:sha(REPO/name) for name in SOURCE_NAMES}
def artifact_snapshot():return {name:sha(BUILD/name) for name in ('forge','libforge_core.a','forge_runtime_psqt_tests') if (BUILD/name).is_file()}
def run(name,command,timeout,out):
    out.mkdir(parents=True,exist_ok=True);record={'command':[str(x) for x in command],'timeout_seconds':timeout,'exit_code':None,'status':'pending','source_sha256_before':source_snapshot(),'artifacts_sha256_before':artifact_snapshot()};helper.save(out/(name+'-command.json'),record);proc=None;start=time.monotonic()
    with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:
        try:
            proc=subprocess.Popen(record['command'],cwd=REPO,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));record['pid']=proc.pid
            try:proc.wait(timeout=timeout)
            finally:
                stdout.flush();stderr.flush();record.update(returncode_before_verdict=proc.returncode,owned_group_empty_before_verdict=helper._owned_group_empty(proc),stdout_sha256_before_verdict=sha(out/(name+'.stdout')),stderr_sha256_before_verdict=sha(out/(name+'.stderr')));helper.save(out/(name+'-command.json'),record)
            record['status']='completed'
        except BaseException as error:
            record.update(status='failed',error=repr(error))
            if proc is not None:
                record['cleanup_attempted']=True
                try:helper.stop_group(proc)
                except BaseException as e:record['cleanup_error']=repr(e)
            raise
        finally:
            stdout.flush();stderr.flush();record.update(exit_code=proc.returncode if proc else None,owned_group_empty_after_cleanup=helper._owned_group_empty(proc) if proc else None,elapsed_seconds=time.monotonic()-start,source_sha256_after=source_snapshot(),artifacts_sha256_after=artifact_snapshot(),stdout_sha256=sha(out/(name+'.stdout')),stderr_sha256=sha(out/(name+'.stderr')));helper.save(out/(name+'-command.json'),record)
    if record['source_sha256_before']!=record['source_sha256_after']:raise RuntimeError('Source changed during '+name)
    if not record['owned_group_empty_after_cleanup']:raise RuntimeError('Owned descendants remain after '+name)
    print(name,record['exit_code'],flush=True);return record['exit_code']
if __name__=='__main__':
    phase=sys.argv[1];out=ROOT/phase
    if phase=='release-red-attempt1':
        assert not BUILD.exists()
        assert run('configure',['/workspace/.cloud-setup/venv/bin/cmake','-S',REPO,'-B',BUILD,'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=g++-14','-DCMAKE_CXX_FLAGS=','-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DFORGE_NATIVE=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],120,out)==0
    assert run('build',['/workspace/.cloud-setup/venv/bin/cmake','--build',BUILD,'-j2'],300,out)==0
    if phase=='release-red-attempt1':
        code=run('runtime-psqt-test',[BUILD/'forge_runtime_psqt_tests'],60,out);assert code==1,code
    else:
        code=run('ctest',['/workspace/.cloud-setup/venv/bin/ctest','--test-dir',BUILD,'--output-on-failure','-j','1'],180,out);assert code==0,code
