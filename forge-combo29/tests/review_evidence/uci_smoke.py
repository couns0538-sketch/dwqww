import subprocess, threading, queue, time, json
p=subprocess.Popen([__import__('sys').argv[1]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
q=queue.Queue()
threading.Thread(target=lambda:[q.put(s.rstrip()) for s in p.stdout],daemon=True).start()
def send(s): p.stdin.write(s+'\n'); p.stdin.flush()
def waitprefix(prefix,timeout=5):
 out=[]; end=time.monotonic()+timeout
 while time.monotonic()<end:
  try: s=q.get(timeout=max(.001,end-time.monotonic()))
  except queue.Empty: break
  out.append(s)
  if s.startswith(prefix): return out
 raise RuntimeError((prefix,out))
send('setoption name OwnBook value false')
results=[]
for cmd in ['go nodes 0','go nodes 1','go movetime 0','go movetime 30','go depth 1 searchmoves e2e4']:
 send('position startpos'); send(cmd); lines=waitprefix('bestmove');results.append([cmd,lines])
for cmd,release in [('go infinite','stop'),('go ponder movetime 30','ponderhit')]:
 send('position startpos');send(cmd);time.sleep(.08); pre=[]
 while not q.empty():pre.append(q.get())
 assert not any(s.startswith('bestmove') for s in pre),(cmd,pre)
 send('isready'); pre+=waitprefix('readyok');send(release); lines=waitprefix('bestmove');results.append([cmd,pre+lines])
send('quit');p.wait(timeout=2)
print(json.dumps(results,indent=2))
