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

# Reserve30sof the480-second workflow step for cleanup/copy/finalization.
BUILD_WORK_SECONDS=450

HERE=Path(__file__).resolve().parent
runner=load('collector_runner',HERE/'run_hosted.py')
evidence=load('collector_evidence',HERE/'build_evidence.py')

def stage(out,name,command,cwd,timeout,deadline,stdout_path=None):
    stdout_path=stdout_path or out/(name+'.stdout');stderr_path=out/(name+'.stderr')
    stdout_path.parent.mkdir(parents=True,exist_ok=True)
    record={'label':name,'command':[str(x) for x in command],'cwd':str(cwd),
            'timeout_seconds':min(timeout,max(.001,deadline-time.monotonic())),
            'status':'pending','exit_code':None,'returncode_before_verdict':None,
            'cleanup_attempted':False}
    runner.save(out/(name+'-command.json'),record)
    process=None;started=time.monotonic()
    with stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
        try:
            process=subprocess.Popen(record['command'],cwd=cwd,stdout=stdout,stderr=stderr,
                start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            record['pid']=process.pid
            try:process.wait(timeout=record['timeout_seconds'])
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
    (out/'source').mkdir();(out/'artifacts/runner').mkdir(parents=True)
    cfg=json.loads((HERE/'protocol.json').read_text());deadline=time.monotonic()+BUILD_WORK_SECONDS
    state={'status':'pending','protocol':cfg,'source_scope':'Fresh actual baseline/candidate builds; no relabeled historical47 binaries.'}
    def interrupted(signum,frame):raise KeyboardInterrupt('Build termination signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:
        shutil.copytree(HERE,out/'package');shutil.copyfile(repo/'.github/workflows/forge-hosted-pv-metadata-strength.yml',out/'workflow.yml')
        shutil.copyfile(repo/'tools/match/windows_validate.py',out/'windows_validate.py')
        runner.require_launch_protocol(cfg);runner.verify_package_inventory(repo,HERE)
        for label in ('baseline','candidate','fastchess'):
            if os.environ.get(label.upper()+'_SHA')!=cfg[label+'_sha']:
                raise ValueError('Workflow/protocol source pin mismatch: '+label)
        if os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('Only the first fresh hosted attempt is permitted')
        if runner.sha(out/'workflow.yml')!=cfg['workflow_sha256']:raise ValueError('Workflow differs from reviewed hash')
        for relative,digest in cfg['correctness_evidence_sha256'].items():
            path=Path(relative)
            if path.is_absolute() or '..' in path.parts or not (repo/path).is_file() or runner.sha(repo/path)!=digest:
                raise ValueError('Correctness proof missing/changed: '+relative)
            target=out/'proofs'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/path,target)
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
                stage(out,label+'-build',['cmake','--build',build,'-j2'],repo,300,deadline)
                stage(out,label+'-ctest',['ctest','--test-dir',build,'--output-on-failure','-j','1'],repo,120,deadline)
            finally:collect_label(out,label,commit,source,build)
        fast=work/'fastchess'
        stage(out,'fastchess-clone',['git','clone','https://github.com/Disservin/fastchess.git',fast],repo,60,deadline)
        stage(out,'fastchess-checkout',['git','-C',fast,'checkout','--detach',cfg['fastchess_sha']],repo,20,deadline)
        stage(out,'source-fastchess',['git','-C',fast,'archive','HEAD'],repo,20,deadline,stdout_path=out/'source/fastchess.tar')
        evidence.source_inventory(out/'source/fastchess.tar',cfg['fastchess_sha'])
        try:stage(out,'fastchess-build',['make','-C',fast,'-j2','CXX=g++-14'],repo,180,deadline)
        finally:
            if (fast/'fastchess').is_file():shutil.copy2(fast/'fastchess',out/'artifacts/runner/fastchess')
            runner.save(out/'fastchess-build-provenance.json',{'source_commit':cfg['fastchess_sha'],
                'source_tar_sha256':runner.sha(out/'source/fastchess.tar'),
                'built_artifacts_sha256':{'fastchess':runner.sha(fast/'fastchess')} if (fast/'fastchess').is_file() else {}})
        state['status']='collected'
        runner.save(out/'prepare-summary.json',state);publish_existing(out)
        state['status']='passed'
    except BaseException as error:
        state.update(status='failed',error=repr(error));raise
    finally:
        runner.save(out/'prepare-summary.json',state);publish_existing(out)

if __name__=='__main__':main()
