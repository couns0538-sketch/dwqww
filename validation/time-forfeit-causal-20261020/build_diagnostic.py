#!/usr/bin/env python3
"""Compile the frozen instrumented export; never run an engine or timing case."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, os, subprocess, time
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SOURCE=json.loads((HERE/'SOURCE.json').read_text())
SRC=Path(SOURCE['source_export'])
BUILD=Path('/workspace/.cloud-setup/forge-forfeit-causal-build-v2')
OUT=HERE/'build-attempt1'
OUT.mkdir(exist_ok=False)
assert not BUILD.exists(), 'Never replace an existing build'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory():return {str(p.relative_to(SRC)):sha(p) for p in sorted(SRC.rglob('*')) if p.is_file()}
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
before=inventory();assert before==SOURCE['instrumented_sha256']
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
report={'status':'RUNNING_BUILD_ONLY','baseline_sha':SOURCE['baseline_sha'],'source_export':str(SRC),'source_manifest_sha256':sha(HERE/'SOURCE.json'),'source_sha256_before':before,'started_utc':datetime.now(timezone.utc).isoformat(),'steps':[],'engine_executed':False}
save(OUT/'commands.json',report)
def run(label,command,expected=0):
 start=time.monotonic()
 with (OUT/(label+'.stdout')).open('xb') as so,(OUT/(label+'.stderr')).open('xb') as se:
  r=subprocess.run(command,cwd=REPO,env=env,stdout=so,stderr=se,timeout=1200)
 row={'label':label,'command':command,'cwd':str(REPO),'exit_code':r.returncode,'expected_exit_code':expected,'elapsed_seconds_diagnostic_only':time.monotonic()-start,'stdout_sha256':sha(OUT/(label+'.stdout')),'stderr_sha256':sha(OUT/(label+'.stderr'))}
 report['steps'].append(row);save(OUT/'commands.json',report);print(json.dumps(row),flush=True)
 assert r.returncode==expected,(label,r.returncode)
try:
 run('syntax-green',['g++','-std=c++20','-O0','-march=x86-64-v3','-fno-fast-math','-ffp-contract=off','-I'+str(SRC/'include'),'-fsyntax-only',str(SRC/'src/search.cpp')])
 cmake='/workspace/.cloud-setup/venv/bin/cmake'
 flags='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto'
 run('configure',[cmake,'-S',str(SRC),'-B',str(BUILD),'-DCMAKE_BUILD_TYPE=Release','-DFORGE_ENABLE_SANITIZERS=OFF','-DFORGE_NATIVE=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_CXX_FLAGS='+flags])
 run('build',[cmake,'--build',str(BUILD),'--target','forge','--parallel','1'])
 after=inventory();assert after==before
 for name in ['CMakeCache.txt','compile_commands.json']:(OUT/name).write_bytes((BUILD/name).read_bytes())
 report.update(status='PASS_BUILD_ONLY',source_files_unchanged=True,source_sha256_after=after,completed_utc=datetime.now(timezone.utc).isoformat())
 save(OUT/'commands.json',report)
 output={'status':'PASS_BUILD_ONLY','baseline_sha':SOURCE['baseline_sha'],'source_manifest_sha256':sha(HERE/'SOURCE.json'),'engine':{'path':str(BUILD/'forge'),'sha256':sha(BUILD/'forge'),'bytes':(BUILD/'forge').stat().st_size},'core_library':{'path':str(BUILD/'libforge_core.a'),'sha256':sha(BUILD/'libforge_core.a'),'bytes':(BUILD/'libforge_core.a').stat().st_size},'compile_commands_sha256':sha(BUILD/'compile_commands.json'),'cmake_cache_sha256':sha(BUILD/'CMakeCache.txt'),'commands':'build-attempt1/commands.json','engine_executed':False,'correctness_or_strength_claim':None}
 save(HERE/'BUILD.json',output);print(json.dumps(output),flush=True)
except BaseException as error:
 report.update(status='FAILED_OR_INCOMPLETE_BUILD_ONLY',error=repr(error),completed_utc=datetime.now(timezone.utc).isoformat());save(OUT/'commands.json',report);raise
