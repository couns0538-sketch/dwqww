#!/usr/bin/env python3
"""Precheck a JSON-list gate manifest against a warning-enabled UCI executable."""
from __future__ import annotations
import argparse,base64,hashlib,json,math,os,queue,re,subprocess,sys,threading,time
from collections import Counter
from pathlib import Path
PROBE='__Forge_S02_precheck_unknown_probe_20261025__'
CORE=('Threads','Hash','OwnBook')
WARNING=re.compile(r'^info string unknown option(?: (.*))?$')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def raw(data):return {'encoding':'base64','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'data':base64.b64encode(data).decode('ascii')}
def unique_object(pairs):
 value={}
 for key,item in pairs:
  if key in value:raise ValueError('duplicate JSON key '+repr(key))
  value[key]=item
 return value

def scalar(value):
 if type(value) is bool:text='true' if value else 'false'
 elif type(value) is int:text=str(value)
 elif type(value) is float and math.isfinite(value):text=json.dumps(value,allow_nan=False)
 elif type(value) is str:text=value
 else:raise ValueError('option values must be finite JSON scalar strings/numbers/bools')
 if not text or any(c.isspace() or c=='\x00' for c in text):raise ValueError('option value must be one nonempty UCI token; whitespace/control characters would be truncated by Forge')
 text.encode('utf-8','strict')
 return text

def gates_from(path):
 rows=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique_object)
 if not isinstance(rows,list) or not rows:raise ValueError('manifest must be a nonempty JSON list of gates')
 result=[];ids=set()
 for row in rows:
  if not isinstance(row,dict):raise ValueError('each gate must be a JSON object')
  gate=row.get('id')
  if not isinstance(gate,str) or not gate.strip() or gate in ids:raise ValueError('gate id must be a unique nonempty string')
  ids.add(gate)
  for key in ('Threads','Hash'):
   if type(row.get(key)) is not int or row[key]<1:raise ValueError(f'gate {gate}: {key} must be a positive integer')
  if type(row.get('OwnBook')) is not bool:raise ValueError(f'gate {gate}: OwnBook must be boolean')
  options=row.get('options')
  if not isinstance(options,dict):raise ValueError(f'gate {gate}: options must be an object')
  if any(key in options for key in CORE):raise ValueError(f'gate {gate}: options duplicates a top-level core setting')
  settings=[(key,row[key]) for key in CORE]+list(options.items());commands=[]
  for name,value in settings:
   if not isinstance(name,str) or not name.strip() or any(c in name for c in '\r\n\x00'):raise ValueError(f'gate {gate}: invalid option name')
   if name!=' '.join(name.split()) or 'value' in name.split():raise ValueError(f'gate {gate}: option name must use canonical whitespace and may not contain the reserved value token')
   line='setoption name '+name+' value '+scalar(value);line.encode('utf-8','strict');commands.append((name,line))
  result.append((gate,commands))
 return result

def observe(engine,gate,commands,timeout):
 p=subprocess.Popen([str(engine)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,
                    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 chunks={'stdout':[],'stderr':[]};events=queue.Queue();sent=[];failures=[];consumed=Counter();active='<warning-capability>';error=None;unclosed=None
 def reader(name):
  for data in iter(getattr(p,name).readline,b''):
   chunks[name].append(data)
   if name=='stdout':events.put(data)
  if name=='stdout':events.put(None)
 threads=[threading.Thread(target=reader,args=(name,),daemon=True) for name in chunks]
 for t in threads:t.start()
 def send(line):sent.append(line);p.stdin.write((line+'\n').encode('utf-8'));p.stdin.flush()
 def until(reply):
  deadline=time.monotonic()+timeout;lines=[]
  while True:
   remain=deadline-time.monotonic()
   if remain<=0:raise TimeoutError('UCI readiness deadline; no process was killed')
   try:data=events.get(timeout=remain)
   except queue.Empty:raise TimeoutError('UCI readiness deadline; no process was killed')
   if data is None:raise RuntimeError('stdout EOF before '+reply)
   line=data.decode('utf-8','strict').rstrip('\r\n');lines.append(line)
   if line==reply:return lines
 try:
  send('uci');handshake=until('uciok')
  if any(WARNING.fullmatch(line) for line in handshake):raise RuntimeError('unexpected unknown-option reply during handshake')
  send('setoption name '+PROBE+' value 1');send('isready');probe=until('readyok')
  warnings=[WARNING.fullmatch(line).group(1) for line in probe if WARNING.fullmatch(line)]
  if warnings!=[PROBE]:raise RuntimeError('warn-ON executable required: reserved unknown-option probe was not reported exactly once')
  consumed['info string unknown option '+PROBE]+=1
  for active,line in commands:
   send(line);send('isready');replies=until('readyok')
   for reply in replies:
    warning=WARNING.fullmatch(reply)
    if warning:
     failures.append({'gate':gate,'option':active,'kind':'unknown_option','reply':reply,'reported_name':warning.group(1) or ''});consumed[reply]+=1
    elif reply.startswith('info string invalid value for option '):
     failures.append({'gate':gate,'option':active,'kind':'invalid_value','reply':reply});consumed[reply]+=1
  send('quit');p.stdin.close();p.wait(timeout=timeout)
  for t in threads:t.join(timeout=min(timeout,2))
 except BaseException as exc:
  error=type(exc).__name__+': '+str(exc)
  failures.append({'gate':gate,'option':active,'kind':'protocol_error','reply':error})
  try:
   if p.poll() is None:send('quit');p.stdin.close();p.wait(timeout=min(timeout,3))
  except BaseException:unclosed=p.pid if p.poll() is None else None
  for t in threads:t.join(timeout=min(timeout,1))
 complete=not any(t.is_alive() for t in threads)
 # Sweep complete captured streams too: diagnostics after the last readyok count.
 remaining=consumed.copy()
 for stream in ('stdout','stderr'):
  for line in b''.join(chunks[stream]).decode('utf-8','replace').replace('\r\n','\n').splitlines():
   warning=WARNING.fullmatch(line);invalid=line.startswith('info string invalid value for option ')
   if not warning and not invalid:continue
   if stream=='stdout' and remaining[line]>0:remaining[line]-=1;continue
   option=(warning.group(1) or '<empty-name>') if warning else line[len('info string invalid value for option '):]
   failures.append({'gate':gate,'option':option,'kind':'unknown_option' if warning else 'invalid_value','reply':line,'stream':stream,'attribution':'full captured stream, including quit/EOF drain'})
 if p.returncode!=0:failures.append({'gate':gate,'option':'<process>','kind':'exit','reply':str(p.returncode)})
 if chunks['stderr']:failures.append({'gate':gate,'option':'<process>','kind':'stderr','reply':'engine wrote stderr; original bytes retained'})
 if not complete:failures.append({'gate':gate,'option':'<process>','kind':'incomplete_capture','reply':'stdout/stderr EOF not observed'})
 record={'gate':gate,'argv':[str(engine)],'stdin':raw(('\n'.join(sent)+'\n').encode('utf-8')),'stdout':raw(b''.join(chunks['stdout'])),
         'stderr':raw(b''.join(chunks['stderr'])),'exit':p.returncode,'unclosed_pid':unclosed,'child_waited':p.returncode is not None,
         'stream_capture_complete':complete,'error':error}
 return record,failures

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--engine',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--timeout',type=float,default=10.0);args=parser.parse_args(argv)
 if not math.isfinite(args.timeout) or args.timeout<=0:raise ValueError('--timeout must be finite and positive')
 manifest=args.manifest.resolve(strict=True);engine=args.engine.resolve(strict=True)
 if not manifest.is_file() or not engine.is_file():raise ValueError('manifest and engine must be regular files')
 gates=gates_from(manifest);before={'manifest':sha(manifest),'engine':sha(engine)}
 candidate=args.out.absolute()
 if os.path.lexists(candidate) or not candidate.parent.is_dir() or any(p.is_symlink() for p in candidate.parents):raise ValueError('--out must be NEW with an existing nonsymlink parent')
 out=candidate.resolve()
 if any(part=='baseline' or part.startswith('dist-v') for part in out.parts):raise ValueError('--out may not be inside baseline or dist-v directories')
 out.mkdir();processes=[];failures=[];gate_records=[]
 for gate,commands in gates:
  record,bad=observe(engine,gate,commands,args.timeout);processes.append(record);failures.extend(bad)
  gate_records.append({'gate':gate,'commands':[line for _,line in commands],'status':'FAIL' if bad else 'PASS'})
 after={'manifest':sha(manifest),'engine':sha(engine)}
 if before!=after:failures.append({'gate':'<inputs>','option':'<identity>','kind':'input_changed','reply':'manifest or engine changed during precheck'})
 result={'status':'FAIL' if failures else 'PASS','gates':gate_records,'failures':failures,'processes':processes,
         'manifest':str(manifest),'engine':str(engine),'input_hashes_before':before,'input_hashes_after':after,
         'tool_sha256':sha(Path(__file__).resolve()),'policy':'One fresh process per gate; warning capability first; only uci/setoption/isready/quit; no go/bench or caller/host control'}
 name='forge_sol_S02_gate_precheck_results_20261025.json';(out/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 old=Path.cwd()
 try:
  os.chdir(out);digest=sha(Path(name));sums=Path('forge_sol_S02_gate_precheck_SHA256SUMS_20261025.txt');sums.write_text(digest+'  '+name+'\n',encoding='ascii');assert sha(Path(name))==sums.read_text().split()[0]
 finally:os.chdir(old)
 print(json.dumps({'status':result['status'],'gates':len(gates),'failures':failures,'out':str(out),'manifest_sha256':sha(out/sums.name)},sort_keys=True))
 return 1 if failures else 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,KeyError,TypeError) as exc:
  print('ERROR: '+' '.join(str(exc).splitlines()),file=sys.stderr);raise SystemExit(1)
