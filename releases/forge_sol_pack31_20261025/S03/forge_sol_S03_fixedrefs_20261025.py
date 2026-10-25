#!/usr/bin/env python3
"""Run fixed bench/perft/mate references; preserve complete original UCI streams."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,queue,re,subprocess,tempfile,threading,time
from pathlib import Path

def sealed_bytes(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}

class Engine:
 def __init__(self,exe,raw,timeout):
  self.exe=exe;self.raw=raw;self.timeout=timeout;self.sent=[];self.chunks={'stdout':[],'stderr':[]};self.q=queue.Queue();self.p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0);self.threads=[]
  for name in self.chunks:
   t=threading.Thread(target=self.read,args=(name,),daemon=True);self.threads.append(t);t.start()
 def read(self,name):
  for b in iter(getattr(self.p,name).readline,b''):
   self.chunks[name].append(b)
   if name=='stdout':self.q.put(b)
  if name=='stdout':self.q.put(None)
 def send(self,s):self.sent.append(s);self.p.stdin.write((s+'\n').encode());self.p.stdin.flush()
 def wait(self,predicate):
  end=time.monotonic()+self.timeout
  while True:
   remaining=end-time.monotonic()
   if remaining<=0:raise RuntimeError('reply deadline; no process is killed')
   try:b=self.q.get(timeout=remaining)
   except queue.Empty:raise RuntimeError('reply deadline; no process is killed')
   if b is None:raise RuntimeError('engine stdout closed before expected reply')
   s=b.decode('utf-8','replace').rstrip('\r\n')
   if s.startswith(('info string illegal move','info string invalid FEN')):raise RuntimeError('position/PV rejected: '+s)
   value=predicate(s)
   if value is not None:return value
 def setup(self):
  self.send('uci');self.wait(lambda s: True if s=='uciok' else None)
  for s in ['setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false','ucinewgame','isready']:self.send(s)
  self.wait(lambda s: True if s=='readyok' else None)
 def perft(self,fen,depth,moves=None):
  self.send('position fen '+fen+(' moves '+' '.join(moves) if moves else''));self.send('go perft '+str(depth));return self.wait(lambda s:int(s[6:]) if re.fullmatch(r'nodes [0-9]+',s) else None)
 def search(self,fen,depth,moves=None):
  self.send('position fen '+fen+(' moves '+' '.join(moves) if moves else''));self.send('go depth '+str(depth));last={}
  def parse(s):
   fields=s.split()
   if fields and fields[0]=='info' and all(k in fields for k in ['depth','score','pv']):
    try:
     i=fields.index('score');last.update(depth=int(fields[fields.index('depth')+1]),kind=fields[i+1],score=int(fields[i+2]),pv=fields[fields.index('pv')+1:])
    except (ValueError,IndexError):raise RuntimeError('malformed search info')
   if fields and fields[0]=='bestmove':
    if len(fields)<2:raise RuntimeError('malformed bestmove')
    return dict(last,bestmove=fields[1])
   return None
  return self.wait(parse)
 def close(self):
  if self.p.poll() is None:
   try:self.send('quit');self.p.stdin.close();self.p.wait(timeout=10)
   except (OSError,ValueError,subprocess.TimeoutExpired):pass
  for t in self.threads:t.join(timeout=1)
  complete=not any(t.is_alive() for t in self.threads);r={'argv':[str(self.exe)],'sent':self.sent,'exit':self.p.poll(),'unclosed_pid':self.p.pid if self.p.poll() is None else None,'stream_capture_complete':complete,'stdout':sealed_bytes(b''.join(self.chunks['stdout'])),'stderr':sealed_bytes(b''.join(self.chunks['stderr']))};self.raw.write_text(json.dumps(r,indent=2)+'\n')
  if self.p.poll()!=0 or not complete:raise RuntimeError('unclean engine/stream closure; raw evidence retained, no process killed')

def run(exe,out,timeout,label,fn):
 e=Engine(exe,out/f'forge_sol_S03_{label}_raw_20261025.json',timeout)
 try:e.setup();value=fn(e)
 finally:e.close()
 return value

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--out',type=Path);g.add_argument('--out-root',type=Path);p.add_argument('--timeout',type=float,default=300);a=p.parse_args();exe=a.exe.resolve(strict=True)
 if not exe.is_file() or not os.access(exe,os.X_OK) or a.timeout<=0:raise SystemExit('valid executable and positive timeout required')
 if a.out:out=a.out;out.mkdir(parents=False,exist_ok=False)
 else:
  root=a.out_root or Path.cwd();root.mkdir(parents=True,exist_ok=True);out=Path(tempfile.mkdtemp(prefix='forge_sol_S03_run_20261025_',dir=root))
 oracle=Path(__file__).with_name('forge_sol_S03_oracle_20261025.json');refs=json.loads(oracle.read_text());result={'status':'UNVERIFIED','exe':str(exe),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'oracle_sha256':hashlib.sha256(oracle.read_bytes()).hexdigest(),'rows':[],'output':str(out)}
 def record(kind,label,expected,actual):
  okay=actual==expected;result['rows'].append({'kind':kind,'id':label,'expected':expected,'actual':actual,'status':'PASS' if okay else'FAIL'});print(('PASS' if okay else'FAIL'),kind,label,'expected',expected,'actual',actual,flush=True)
  if not okay:raise RuntimeError(f'{kind} {label}: expected {expected}, observed {actual}')
 try:
  # Always first engine exercise: explicit user d11 OFF precondition.
  def bench(depth):
   def job(e):
    e.send('bench '+str(depth));return e.wait(lambda s:int(m.group(1)) if (m:=re.search(r'^info string bench depth '+str(depth)+r' nodes ([0-9]+)\b',s)) else None)
   return job
  first=refs['bench'][0];record('bench','d11',first['nodes'],run(exe,out,a.timeout,'first_off_d11',bench(11)))
  # Catch a perft regression cheaply before the deeper reference work.
  for case in refs['perft']:
   def check(e,c=case):
    for d,n in enumerate(c['depths_1_to_5'],1):record('perft',c['id']+'_d'+str(d),n,e.perft(c['fen'],d))
   run(exe,out,a.timeout,'perft_'+case['id'],check)
  for case in refs['mate']:
   def check(e,c=case):
    r=e.search(c['fen'],c['depth']);expected={'kind':'mate','score':c['mate_moves'],'bestmove':c['bestmove'],'pv_plies':c['pv_plies']};actual={k:r.get(k) for k in ['kind','score','bestmove']};actual['pv_plies']=len(r.get('pv',[]));record('mate',c['id'],expected,actual);record('mate_pv_first',c['id'],c['bestmove'],r['pv'][0]);record('mate_pv_terminal_legal_moves',c['id'],0,e.perft(c['fen'],1,r['pv']));terminal=e.search(c['fen'],1,r['pv']);record('mate_pv_terminal_score',c['id'],{'kind':'mate','score':0,'bestmove':'0000'},{k:terminal.get(k) for k in ['kind','score','bestmove']});result['rows'].append({'kind':'mate_pv_observed','id':c['id'],'pv':r['pv'],'status':'PASS'})
   run(exe,out,a.timeout,'mate_'+case['id'],check)
  for c in refs['bench'][1:]:record('bench','d'+str(c['depth']),c['nodes'],run(exe,out,a.timeout,'bench_d'+str(c['depth']),bench(c['depth'])))
  result['status']='PASS';print('FIXED_REFERENCES_PASS',len(result['rows']),'checks; output',out)
 except Exception as exc:
  result['status']='FAIL';result['error']=str(exc);print('FIXED_REFERENCES_FAIL',str(exc),flush=True)
 finally:(out/'forge_sol_S03_results_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
