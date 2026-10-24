#!/usr/bin/env python3
"""Execute one frozen command with original stdout/stderr and actual exit receipt."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--step');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
raw=a.spec.read_bytes();s=json.loads(raw)
if a.step:
 matches=[c for c in s['commands'] if c['name']==a.step]
 if len(matches)!=1:raise ValueError('Exactly one declared step required')
 c=matches[0]
else:c=s['command']
argv=c['argv'];assert isinstance(argv,list) and argv and all(isinstance(v,str) for v in argv)
a.out.mkdir(parents=True,exist_ok=False)
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**c.get('environment',c.get('env',{}))}
r={'status':'LAUNCHING','spec_path':str(a.spec.absolute()),'spec_sha256':hashlib.sha256(raw).hexdigest(),'step':a.step,'argv':argv,'cwd':'/workspace/dwqww','env_overrides':{'PYTHONDONTWRITEBYTECODE':'1',**c.get('environment',c.get('env',{}))},'started_utc':datetime.now(timezone.utc).isoformat(),'actual_exit':None}
(a.out/'command.json').write_text(json.dumps(r,indent=2)+'\n');start=time.monotonic()
with (a.out/'stdout').open('xb') as stdout,(a.out/'stderr').open('xb') as stderr:
 child=subprocess.Popen(argv,cwd=r['cwd'],env=env,stdout=stdout,stderr=stderr)
 r.update(status='RUNNING',pid=child.pid)
 try:r['proc_start_ticks']=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:r['proc_start_ticks']=None
 (a.out/'command.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({k:r[k] for k in ('status','step','pid','proc_start_ticks','started_utc')}),flush=True)
 result=child.wait()
r.update(status='COMPLETED' if result==0 else 'NONZERO_EXIT_OR_PARTIAL',actual_exit=result,elapsed_seconds=time.monotonic()-start,closed_utc=datetime.now(timezone.utc).isoformat())
for name in ('stdout','stderr'):
 d=hashlib.sha256()
 with (a.out/name).open('rb') as stream:
  for b in iter(lambda:stream.read(1<<20),b''):d.update(b)
 r[name+'_sha256']=d.hexdigest();r[name+'_bytes']=(a.out/name).stat().st_size
(a.out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('status','actual_exit','elapsed_seconds','closed_utc')}),flush=True)
raise SystemExit(result)
