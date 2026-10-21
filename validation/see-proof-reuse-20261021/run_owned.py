#!/usr/bin/env python3
from pathlib import Path
import subprocess,os,signal,time,json,hashlib,sys
E=Path('/workspace/dwqww/validation/see-proof-reuse-20261021')
def run(name,argv,timeout=180,env_extra=None,stdin=None,cwd=None):
 out=E/(name+'.stdout');err=E/(name+'.stderr');status={'name':name,'argv':argv,'timeout_seconds':timeout,'cwd':str(cwd) if cwd else None,'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'returncode':None,'timeout':False,'owned_group_closed':False}
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.update(env_extra or {})
 proc=None;fault=None
 try:
  with out.open('xb') as fo,err.open('xb') as fe:
   proc=subprocess.Popen(argv,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,stdout=fo,stderr=fe,start_new_session=True,env=env,cwd=cwd)
   status['pid']=proc.pid;status['pgid']=proc.pid
   try:proc.communicate(stdin,timeout=timeout)
   except subprocess.TimeoutExpired:
    status['timeout']=True
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(3)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(3)
   status['returncode']=proc.returncode
 except BaseException as ex:fault=ex;status['exception']=repr(ex)
 finally:
  # Cleanup is independent of evidence hashing/status persistence.
  if proc is not None:
   try:
    os.killpg(proc.pid,0)
   except ProcessLookupError:status['owned_group_closed']=True
   else:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    if proc.poll() is None:proc.wait(3)
    try:os.killpg(proc.pid,0)
    except ProcessLookupError:status['owned_group_closed']=True
    else:status['cleanup_fault']='owned process group still exists'
  status['end_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
  for p in (out,err):
   if p.exists():status[p.suffix[1:]+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  (E/(name+'.status.json')).write_text(json.dumps(status,indent=2)+'\n')
 if fault:raise fault
 if status['returncode']!=0 or status['timeout'] or not status['owned_group_closed']:raise RuntimeError(status)
 return status
if __name__=='__main__':
 task=sys.argv[1]
 if task=='configure':run('configure-attempt2',['/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake','-S','/workspace/.cloud-setup/see-proof-reuse23-source','-B','/workspace/.cloud-setup/see-proof-reuse23-release','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=/usr/bin/g++-14','-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
 elif task=='build':run('build-attempt2',['/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake','--build','/workspace/.cloud-setup/see-proof-reuse23-release','--target','forge','forge_see_threshold','-j1'],240)
 elif task=='version':run('compiler-version',['/usr/bin/g++-14','--version'],10)
