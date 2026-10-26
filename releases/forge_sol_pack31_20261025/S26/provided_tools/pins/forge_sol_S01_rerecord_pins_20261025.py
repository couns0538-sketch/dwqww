#!/usr/bin/env python3
"""Observe the exact Job C search cases; preserve raw streams encoded without edits."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,queue,subprocess,threading,time
from pathlib import Path

CASES=[
 ('WAC001','2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1',12,8,'f6h5',661),
 ('promotion_white','8/k1P5/2K5/8/8/8/8/8 w - - 0 1',1,1,'c6d7',None),
 ('promotion_black','8/8/8/8/8/2k5/K1p5/8 b - - 0 1',1,1,'c3d2',None),
]

def raw_record(data):
 return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'encoding':'base64','data':base64.b64encode(data).decode('ascii')}

def observe(exe,case,out,timeout):
 label,fen,depth,hashmb,move,score=case
 p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
 chunks={'stdout':[],'stderr':[]};events=queue.Queue();sent=[];deadline=time.monotonic()+timeout;row={'case':label,'fen':fen,'requested_depth':depth,'Hash':hashmb,'Threads':1,'OwnBook':False,'pid':p.pid}
 def reader(name,pipe):
  while True:
   b=pipe.readline()
   if not b:break
   chunks[name].append(b)
   if name=='stdout':events.put(b)
  if name=='stdout':events.put(None)
 threads=[threading.Thread(target=reader,args=(n,getattr(p,n)),daemon=True) for n in chunks]
 for t in threads:t.start()
 def send(line):
  sent.append(line);p.stdin.write((line+'\n').encode());p.stdin.flush()
 def get_line():
  remain=deadline-time.monotonic()
  if remain<=0:raise TimeoutError('observation deadline; no process is killed')
  try:b=events.get(timeout=remain)
  except queue.Empty:raise TimeoutError('observation deadline; no process is killed')
  if b is None:raise RuntimeError('engine closed stdout before required reply')
  return b.decode('utf-8','replace').rstrip('\r\n')
 def until(wanted):
  while True:
   line=get_line()
   if line==wanted:return
 last_info=None
 try:
  send('uci');until('uciok')
  for line in ['setoption name Threads value 1',f'setoption name Hash value {hashmb}','setoption name OwnBook value false','ucinewgame','isready']:send(line)
  until('readyok');send('position fen '+fen);send(f'go depth {depth}')
  while True:
   line=get_line();fields=line.split()
   if fields and fields[0]=='info' and all(k in fields for k in ['depth','score','pv']):
    try:
     d=int(fields[fields.index('depth')+1]);i=fields.index('score');kind=fields[i+1];v=int(fields[i+2]);pv=fields[fields.index('pv')+1:]
     if d==depth:last_info={'depth':d,'score_kind':kind,'score':v,'pv':pv}
    except (ValueError,IndexError):pass
   elif fields and fields[0]=='bestmove':
    if len(fields)<2:raise RuntimeError('malformed bestmove')
    row['bestmove']=fields[1];break
  if last_info is None:raise RuntimeError('missing completed requested-depth score/PV')
  row.update(last_info);send('quit');p.stdin.close();p.wait(timeout=max(0.1,min(10,deadline-time.monotonic())))
  for t in threads:t.join(timeout=1)
  if any(t.is_alive() for t in threads):
   raise RuntimeError('stream capture incomplete: stdout/stderr reader did not close; partial raw evidence retained')
  if p.returncode!=0:raise RuntimeError('engine exit '+str(p.returncode))
  if row['pv'][:1]!=[row['bestmove']]:raise RuntimeError('bestmove and completed-depth PV disagree')
  row['documented_pin_matches']=(row['bestmove']==move and row['score_kind']=='cp' and (row['score']==score if score is not None else row['score']>100) and row['depth']==depth)
  row['status']='OBSERVED'
 except Exception as e:
  row['status']='UNVERIFIED';row['error']=str(e)
  if p.poll() is None:
   try:send('stop');send('quit');p.stdin.close();p.wait(timeout=2)
   except (OSError,ValueError,subprocess.TimeoutExpired):pass
 finally:
  row['exit']=p.poll();row['unclosed_pid']=p.pid if p.poll() is None else None
  for t in threads:t.join(timeout=0.1)
  row['stream_capture_complete']=not any(t.is_alive() for t in threads)
  raw={'argv':[str(exe)],'sent':sent,'stdout':raw_record(b''.join(chunks['stdout'])),'stderr':raw_record(b''.join(chunks['stderr'])),'exit':p.poll(),'stream_capture_complete':row['stream_capture_complete']}
  (out/f'forge_sol_S01_{label}_raw_20261025.json').write_text(json.dumps(raw,indent=2)+'\n')
 return row

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('exe',type=Path);a.add_argument('--out',type=Path,required=True);a.add_argument('--timeout',type=float,default=300);a.add_argument('--expect-lock',action='store_true');args=a.parse_args()
 if args.timeout<=0:raise SystemExit('--timeout must be positive')
 exe=args.exe.resolve(strict=True)
 if not exe.is_file() or not os.access(exe,os.X_OK):raise SystemExit('executable is not readable/executable')
 args.out.mkdir(parents=False,exist_ok=False)
 record={'exe':str(exe),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'policy':'Observations only; no pins, engine or input files edited. No affinity, host-limit or process termination changes. Raw streams preserved as base64 with original SHA256.','cases':[]}
 for case in CASES:
  row=observe(exe,case,args.out,args.timeout);record['cases'].append(row)
  if row['status']=='OBSERVED':
   print(f"{row['case']}: best={row['bestmove']} score={row['score_kind']}:{row['score']} depth={row['depth']} pv0={row['pv'][0]} documented_pin_matches={row['documented_pin_matches']}",flush=True)
  else:print(f"{row['case']}: UNVERIFIED {row.get('error','')} unclosed_pid={row['unclosed_pid']}",flush=True)
  if row['unclosed_pid'] is not None:break
 record['status']='PASS' if len(record['cases'])==3 and all(r['status']=='OBSERVED' and (not args.expect_lock or r['documented_pin_matches']) for r in record['cases']) else 'UNVERIFIED'
 (args.out/'forge_sol_S01_pin_results_20261025.json').write_text(json.dumps(record,indent=2)+'\n');print('PIN_OBSERVATION_'+record['status']);return 0 if record['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
