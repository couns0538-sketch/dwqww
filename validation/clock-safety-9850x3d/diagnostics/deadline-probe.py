#!/usr/bin/env python3
import json,os,queue,re,subprocess,threading,time
from pathlib import Path
root=Path('/workspace/.cloud-setup/clock-audit/deadline-probe');root.mkdir(exist_ok=False)
log=Path('/workspace/dwqww/validation/clock-safety-9850x3d/matches/timed-pilot/fastchess.log').read_text().splitlines()
position=[s.split('Candidate <--- ',1)[1] for s in log if 'Candidate <--- position ' in s][-1]
go='go wtime 1323 btime 308 winc 100 binc 100'
(root/'protocol.json').write_text(json.dumps({'kind':'diagnostic, not Elo','position':position,'go':go,'hard_budget_ms':124,'remaining_ms':308,'trials_per_engine':100,'proc_sampling_interval_ms':2,'affinity':sorted(os.sched_getaffinity(0))},indent=2)+'\n')
class Engine:
 def __init__(self,name,path):
  self.name=name;self.path=path;self.q=queue.Queue();self.p=subprocess.Popen([path],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
  def reader():
   for line in self.p.stdout:self.q.put((time.monotonic_ns(),line.rstrip()))
   self.q.put((time.monotonic_ns(),None))
  self.t=threading.Thread(target=reader,daemon=True);self.t.start()
  self.send('uci');self.until('uciok',20)
  for s in ['setoption name OwnBook value false','setoption name Hash value 32','setoption name Threads value 1','setoption name Move Overhead value 100']:self.send(s)
  self.send('isready');self.until('readyok',20)
 def send(self,s):self.p.stdin.write(s+'\n');self.p.stdin.flush()
 def until(self,prefix,seconds):
  deadline=time.monotonic()+seconds;lines=[]
  while True:
   stamp,line=self.q.get(timeout=max(.001,deadline-time.monotonic()))
   if line is None:raise RuntimeError('engine EOF')
   lines.append((stamp,line))
   if line.startswith(prefix):return lines
 def close(self):
  self.send('quit')
  try:self.p.wait(timeout=10)
  except subprocess.TimeoutExpired:self.p.kill();self.p.wait()
  self.t.join(timeout=1)
def sample(pid,done,records):
 base=Path(f'/proc/{pid}/task')
 while not done.is_set():
  stamp=time.monotonic_ns();tasks={}
  try:dirs=list(base.iterdir())
  except FileNotFoundError:return
  for d in dirs:
   try:
    fields=(d/'stat').read_text().split();sched=[int(x) for x in (d/'schedstat').read_text().split()];wchan=(d/'wchan').read_text().strip()
    tasks[d.name]={'state':fields[2],'ticks':int(fields[13])+int(fields[14]),'runtime_ns':sched[0],'run_delay_ns':sched[1],'timeslices':sched[2],'wchan':wchan}
   except (FileNotFoundError,ProcessLookupError):pass
  records.append({'t_ns':stamp,'tasks':tasks});done.wait(.002)
engines=[Engine('reference','/workspace/.cloud-setup/forge-clock-reference-build/forge'),Engine('candidate','/workspace/.cloud-setup/forge-clock-build/forge')]
results=[]
try:
 for iteration in range(100):
  for e in engines[iteration%2:]+engines[:iteration%2]:
   e.send('ucinewgame');e.send(position);e.send('isready');e.until('readyok',20)
   records=[];done=threading.Event();sampler=threading.Thread(target=sample,args=(e.p.pid,done,records),daemon=True);sampler.start()
   start=time.monotonic_ns();e.send(go);stopped=False
   try:lines=e.until('bestmove ',2)
   except queue.Empty:
    e.send('stop');stopped=True;lines=e.until('bestmove ',10)
   finish=lines[-1][0];done.set();sampler.join(timeout=2)
   info=[line for _,line in lines if line.startswith('info depth')]
   result={'engine':e.name,'iteration':iteration,'pid':e.p.pid,'wall_ms':(finish-start)/1e6,'go_ns':start,'last_info':info[-1] if info else None,'bestmove':lines[-1][1],'stop_sent':stopped}
   results.append(result)
   (root/f'{iteration:03}-{e.name}.json').write_text(json.dumps({'result':result,'output':lines,'samples':records},separators=(',',':'))+'\n')
   if result['wall_ms']>308 or stopped:print(json.dumps(result),flush=True)
  if iteration%10==0:print('completed iteration',iteration,flush=True)
finally:
 for e in engines:e.close()
 (root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'trials':len(results),'over_remaining':sum(r['wall_ms']>308 for r in results),'max_wall_ms':max(r['wall_ms'] for r in results)},indent=2))
