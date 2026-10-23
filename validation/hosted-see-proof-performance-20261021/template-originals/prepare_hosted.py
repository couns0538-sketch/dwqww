#!/usr/bin/env python3
"""Future hosted collector. Inactive workflow; never run during local preparation.

Source/build-provenance fields match the original17 collector. Additional stage
records use observed command/exit/stdout/stderr hash fields and retain failures.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import time

sys.dont_write_bytecode=True

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

# Reserve30sof the720-second workflow step for cleanup/copy/finalization.
BUILD_WORK_SECONDS=690

HERE=Path(__file__).resolve().parent
runner=load('collector_runner',HERE/'owned_process.py')
evidence=load('collector_evidence',HERE/'build_evidence.py')
common=load('collector_common',HERE/'common.py')

def stage(out,name,command,cwd,timeout,deadline,stdout_path=None):
    stdout_path=stdout_path or out/(name+'.stdout');stderr_path=out/(name+'.stderr')
    stdout_path.parent.mkdir(parents=True,exist_ok=True)
    record={'label':name,'command':[str(x) for x in command],'cwd':str(cwd),
            'timeout_seconds':min(timeout,max(0.,deadline-time.monotonic())),
            'status':'pending','exit_code':None,'returncode_before_verdict':None,'timed_out':False,
            'cleanup_attempted':False}
    runner.save(out/(name+'-command.json'),record)
    if record['timeout_seconds']<=0:
        record.update(status='failed',error='Aggregate build deadline before processlaunch',exit_code=None);runner.save(out/(name+'-command.json'),record);raise TimeoutError(record['error'])
    process=None;started=time.monotonic()
    with stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
        try:
            process=subprocess.Popen(record['command'],cwd=cwd,stdout=stdout,stderr=stderr,
                start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            record['pid']=process.pid
            try:process.wait(timeout=record['timeout_seconds'])
            except BaseException as wait_error:
                record.update(wait_error=repr(wait_error),timed_out=isinstance(wait_error,subprocess.TimeoutExpired))
                raise
            finally:
                stdout.flush();stderr.flush()
                record.update(returncode_before_verdict=process.returncode,
                    owned_group_empty_before_verdict=runner._owned_group_empty(process),
                    stdout_sha256_before_verdict=runner.sha(stdout_path),
                    stderr_sha256_before_verdict=runner.sha(stderr_path))
                runner.save(out/(name+'-command.json'),record)
            if process.returncode!=0 or not record['owned_group_empty_before_verdict']:
                raise RuntimeError('Build stage failed/orphaned: '+name)
            record['status']='passed'
        except BaseException as error:
            record.update(status='failed',error=repr(error))
            if process is not None:
                record['cleanup_attempted']=True
                try:runner.stop_group(process)
                except BaseException as cleanup:record['cleanup_error']=repr(cleanup)
            raise
        finally:
            stdout.flush();stderr.flush()
            record.update(exit_code=process.returncode if process is not None else None,
                owned_group_empty_after_cleanup=runner._owned_group_empty(process) if process is not None else None,
                stdout_sha256=runner.sha(stdout_path),stderr_sha256=runner.sha(stderr_path),
                elapsed_seconds=time.monotonic()-started)
            runner.save(out/(name+'-command.json'),record)
    return record

def publish_existing(out):
    artifacts=out/'artifacts'
    runner.save(out/'artifacts-SHA256.json',{p.relative_to(artifacts).as_posix():runner.sha(p)
        for p in sorted(artifacts.rglob('*')) if p.is_file()})
    # Manifest includes failed stage logs/partial source/config/artifacts as observed.
    # An incomplete set will fail the mandatory guard; raw bytes remain archived.
    runner.save(out/'build-evidence-SHA256.json',{p.relative_to(out).as_posix():runner.sha(p)
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='build-evidence-SHA256.json'})

def collect_label(out,label,commit,source,build):
    for name,target in [('forge',out/'artifacts'/label/'forge'),('libforge_core.a',out/'artifacts'/label/'libforge_core.a'),
                        ('compile_commands.json',out/(label+'-compile-commands.json')),
                        ('CMakeCache.txt',out/(label+'-CMakeCache.txt')),
                        ('Testing/Temporary/LastTest.log',out/(label+'-LastTest.log'))]:
        if (build/name).is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(build/name,target)
    archive=out/'source'/(label+'.tar')
    record={'source_commit':commit,'exported_source_sha256':{p.relative_to(source).as_posix():runner.sha(p)
                for p in sorted(source.rglob('*')) if p.is_file()},
            'built_artifacts_sha256':{name:runner.sha(build/name) for name in ('forge','libforge_core.a') if (build/name).is_file()},
            'last_test_log_sha256':runner.sha(build/'Testing/Temporary/LastTest.log') if (build/'Testing/Temporary/LastTest.log').is_file() else None,
            'source_tar_sha256':runner.sha(archive) if archive.is_file() else None}
    runner.save(out/(label+'-build-provenance.json'),record)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--finalize-only',action='store_true')
    args=parser.parse_args();repo=args.repo.resolve(strict=True);out=args.out.resolve();work=args.work.resolve()
    if args.finalize_only:
        publish_existing(out)
        return
    out.mkdir(parents=True,exist_ok=False);work.mkdir(parents=True,exist_ok=False)
    (out/'source').mkdir();(out/'artifacts').mkdir()
    cfg=json.loads((HERE/'protocol.json').read_text());deadline=time.monotonic()+BUILD_WORK_SECONDS
    state={'status':'pending','protocol':cfg,'source_scope':'Fresh actual20/21source/builds; baseline12/candidate13CTest, no gameplay.'}
    def interrupted(signum,frame):raise KeyboardInterrupt('Build termination signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:
        shutil.copytree(HERE,out/'package');shutil.copyfile(repo/'.github/workflows/forge-hosted-nearest-pawn-performance.yml',out/'workflow.yml')
        common.require_ready(cfg);common.inventory(repo,HERE)
        for label in ('baseline','candidate'):
            if os.environ.get(label.upper()+'_SHA')!=cfg[label+'_sha']:
                raise ValueError('Workflow/protocol source pin mismatch: '+label)
        if os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('Only the first fresh hosted attempt is permitted')
        if runner.sha(out/'workflow.yml')!=cfg['workflow_sha256']:raise ValueError('Workflow differs from reviewed hash')
        for proof in common.proof_paths(repo,cfg):
            path=proof.relative_to(repo);target=out/'proofs'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(proof,target)
        if not shutil.which('g++-14'):
            stage(out,'apt-update',['sudo','apt-get','update'],repo,60,deadline)
            stage(out,'apt-install',['sudo','apt-get','install','-y','g++-14'],repo,60,deadline)
        stage(out,'compiler',['g++-14','--version'],repo,10,deadline)
        stage(out,'cmake-version',['cmake','--version'],repo,10,deadline)
        for label in ('baseline','candidate'):
            commit=cfg[label+'_sha'];source=work/('src-'+label);build=work/('build-'+label);source.mkdir()
            try:
                stage(out,'source-'+label,['git','archive',commit,'CMakeLists.txt','LICENSE','src','include','tests','bench','tools'],repo,30,deadline,stdout_path=out/'source'/(label+'.tar'))
                evidence.source_inventory(out/'source'/(label+'.tar'),commit)
                with tarfile.open(out/'source'/(label+'.tar')) as archive:archive.extractall(source,filter='data')
                stage(out,label+'-configure',['cmake','-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=g++-14',
                    '-DCMAKE_CXX_FLAGS=','-DCMAKE_CXX_FLAGS_RELEASE='+evidence.RELEASE_FLAGS,
                    '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DFORGE_NATIVE=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],repo,90,deadline)
                stage(out,label+'-build',['cmake','--build',build,'-j2'],repo,360,deadline)
                stage(out,label+'-ctest',['ctest','--test-dir',build,'--output-on-failure','-j','1'],repo,150,deadline)
                stage(out,label+'-core-sections',['objdump','-h',build/'libforge_core.a'],repo,20,deadline)
            finally:collect_label(out,label,commit,source,build)
        state['status']='collected'
        runner.save(out/'prepare-summary.json',state);publish_existing(out)
        state['status']='passed'
    except BaseException as error:
        state.update(status='failed',error=repr(error));raise
    finally:
        runner.save(out/'prepare-summary.json',state);publish_existing(out)

if __name__=='__main__':main()
