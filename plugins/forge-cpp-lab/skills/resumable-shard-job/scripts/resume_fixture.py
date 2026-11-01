#!/usr/bin/env python3
"""Owned disposable-worker restart proof, not a production shard converter.
IDEA_SOURCE: immutable Forge shard checkpoints and the user-requested kill/resume MD5 proof.
All partial files/evidence remain; only the Popen-created fixture worker may terminate.
"""
import argparse,contextlib,hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path

def digest(path,algorithm='sha256'):
 h=hashlib.new(algorithm)
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def publish(path,data):
 path=Path(path)
 if path.exists():
  if path.is_symlink() or path.read_bytes()!=data:raise ValueError('sealed publication differs: '+str(path))
  return
 stage=path.parent/('partial_'+path.name+'_'+uuid.uuid4().hex)
 with stage.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.link(stage,path)  # Atomic exclusive publication; stages deliberately retained.

def json_bytes(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()

@contextlib.contextmanager
def lock(path):
 if path.is_symlink():raise ValueError('lock path must not be an alias')
 with path.open('a+b') as f:
  if not f.seek(0,2):f.write(b'0');f.flush()
  f.seek(0)
  if os.name=='nt':
   import msvcrt
   msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
   try:yield
   finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
  else:
   import fcntl
   fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
   try:yield
   finally:fcntl.flock(f.fileno(),fcntl.LOCK_UN)

def run(inputs,out,resume=False,delay=0):
 inputs=[Path(p).resolve(strict=True) for p in inputs];out=Path(out)
 if not inputs or any(not p.is_file() for p in inputs):raise ValueError('nonempty input file list required')
 if len(set(inputs))!=len(inputs):raise ValueError('duplicate input paths')
 if out.is_symlink() or any(out.resolve() in p.parents for p in inputs):raise ValueError('output must not contain sources or be an alias')
 config={'schema':1,'purpose':'deterministic disposable fixture only','worker_sha256':digest(Path(__file__)), 'inputs':[{'path':str(p),'sha256':digest(p)} for p in inputs]}
 if not resume:out.mkdir(exist_ok=False)
 elif not out.is_dir():raise ValueError('resume directory missing')
 with lock(out/'worker.lock'):
  config_path=out/'CONFIG.json'
  if resume:
   if not config_path.is_file() or json.loads(config_path.read_text())!=config:raise ValueError('configuration or source changed; refuse resume')
  else:publish(config_path,json_bytes(config))
  shards=[]
  for index,path in enumerate(inputs):
   final=out/f'shard_{index:06}.bin';checkpoint=out/f'checkpoint_{index:06}.json'
   if checkpoint.is_file():
    record=json.loads(checkpoint.read_text())
    if type(record.get('rows')) is not int or record['rows']<0 or record.get('source_sha256')!=config['inputs'][index]['sha256'] or record.get('file')!=final.name or not final.is_file() or final.is_symlink() or final.stat().st_size!=record['rows']*65 or digest(final)!=record.get('sha256') or digest(final,'md5')!=record.get('md5'):raise ValueError('checkpoint/shard hash mismatch')
   else:
    stage=out/(f'stage_shard_{index:06}_'+uuid.uuid4().hex)
    rows=0
    with path.open('rb') as source,stage.open('xb') as target:
     for line in source:
      target.write(hashlib.sha256(line).hexdigest().encode()+b'\n');target.flush();rows+=1
      if delay:time.sleep(delay)
     target.flush();os.fsync(target.fileno())
    if digest(path)!=config['inputs'][index]['sha256']:raise ValueError('source changed while processing')
    if final.exists():
     if final.is_symlink() or digest(final)!=digest(stage):raise ValueError('orphan published shard hash mismatch')
    else:os.link(stage,final)
    record={'file':final.name,'rows':rows,'source_sha256':config['inputs'][index]['sha256'],'sha256':digest(final),'md5':digest(final,'md5')}
    publish(checkpoint,json_bytes(record))
   shards.append(record)
  combined=out/'output.bin'
  if not combined.exists():
   stage=out/('stage_combined_'+uuid.uuid4().hex)
   with stage.open('xb') as target:
    for item in shards:
     with (out/item['file']).open('rb') as part:
      for data in iter(lambda:part.read(1024*1024),b''):target.write(data)
    target.flush();os.fsync(target.fileno())
   os.link(stage,combined)
  expected=hashlib.sha256()
  for item in shards:
   with (out/item['file']).open('rb') as part:
    for data in iter(lambda:part.read(1024*1024),b''):expected.update(data)
  if digest(combined)!=expected.hexdigest():raise ValueError('combined hash mismatch')
  result={'status':'PASS','scope':'Disposable fixture only; not production converter restart qualification','shards':shards,'sha256':digest(combined),'md5':digest(combined,'md5')}
  publish(out/'COMPLETE.json',json_bytes(result));return result

def verify_interruption(out,exit_code,expected_bytes):
 if type(exit_code) is not int or exit_code==0:raise RuntimeError('worker exited normally; no interruption proof')
 if (out/'checkpoint_000001.json').exists():raise RuntimeError('next checkpoint completed; no incomplete-shard proof')
 partials=[p for p in out.glob('stage_shard_000001_*') if p.is_file() and not p.is_symlink() and 0<p.stat().st_size<expected_bytes]
 if not partials:raise RuntimeError('no genuinely incomplete next-shard stage retained')
 return partials

def selftest(out):
 out=Path(out);out.mkdir(exist_ok=False)
 publish(out/'FIXTURE_OWNER.json',json_bytes({'purpose':'DISPOSABLE_RESUME_FIXTURE'}))
 inputs=[]
 for index in range(3):
  p=out/f'input_{index:03}.txt';p.write_bytes(b''.join(f'{index}:{row}:original fixture\n'.encode() for row in range(64)));inputs.append(p)
 full=run(inputs,out/'uninterrupted')
 command=[sys.executable,str(Path(__file__).resolve()),'_worker','--fixture-root',str(out.resolve()),'--delay','0.003']
 publish(out/'owned_worker_command.json',json_bytes({'argv':command,'termination_scope':'only this newly spawned Popen child'}))
 terminated=False
 with (out/'interrupted.stdout').open('xb') as stdout,(out/'interrupted.stderr').open('xb') as stderr:
  worker=subprocess.Popen(command,stdout=stdout,stderr=stderr)
  try:
   deadline=time.monotonic()+15
   while time.monotonic()<deadline:
    active=list((out/'interrupted').glob('stage_shard_000001_*'))
    if (out/'interrupted'/'checkpoint_000000.json').is_file() and any(p.stat().st_size>0 for p in active):
     if worker.poll() is None:worker.terminate();terminated=True
     break
    if worker.poll() is not None:raise RuntimeError('fixture exited before interruption point')
    time.sleep(0.01)
   if not terminated:raise RuntimeError('fixture interruption deadline expired')
   exit_code=worker.wait(timeout=5)
  finally:
   if worker.poll() is None:worker.kill();worker.wait() # Owned fixture only, never lookup/kill another PID.
 publish(out/'interrupted_exit.json',json_bytes({'exit_code':exit_code,'terminated_owned_worker':terminated}))
 incomplete=verify_interruption(out/'interrupted',exit_code,64*65)
 if (out/'uninterrupted'/'CONFIG.json').read_bytes()!=(out/'interrupted'/'CONFIG.json').read_bytes():raise ValueError('fixture configurations differ')
 retained={str(p.relative_to(out)):digest(p) for p in (out/'interrupted').glob('stage_shard_*')}
 resumed=run(inputs,out/'interrupted',True)
 if any(not (out/name).is_file() or digest(out/name)!=value for name,value in retained.items()):raise ValueError('interrupted evidence changed')
 result={'status':'PASS' if full['md5']==resumed['md5'] and full['sha256']==resumed['sha256'] else 'FAIL','scope':'Actual disposable fixture termination/resume only; real production job remains UNVERIFIED','owned_worker_terminated':terminated,'full_md5':full['md5'],'resumed_md5':resumed['md5'],'full_sha256':full['sha256'],'resumed_sha256':resumed['sha256'],'interrupted_exit_code':exit_code,'retained_partial_files':len(incomplete),'retained_stage_files':len(retained),'incomplete_stage_names':[p.name for p in incomplete]}
 publish(out/'RESTART_PROOF.json',json_bytes(result));return result

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
 t=sub.add_parser('selftest');t.add_argument('--out',required=True,type=Path)
 w=sub.add_parser('_worker');w.add_argument('--fixture-root',required=True,type=Path);w.add_argument('--delay',type=float,default=0)
 a=p.parse_args()
 try:
  if a.mode=='selftest':r=selftest(a.out)
  else:
   root=a.fixture_root.resolve(strict=True)
   if json.loads((root/'FIXTURE_OWNER.json').read_text())!={'purpose':'DISPOSABLE_RESUME_FIXTURE'}:raise ValueError('not an owned fixture')
   if not 0<=a.delay<=1:raise ValueError('invalid fixture delay')
   r=run([root/f'input_{n:03}.txt' for n in range(3)],root/'interrupted',delay=a.delay)
 except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:r={'status':'BLOCKED','error':str(e),'scope':'Fixture evidence retained; no production proof'}
 print(json.dumps(r,sort_keys=True,indent=2));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
