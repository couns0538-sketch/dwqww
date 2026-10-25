#!/usr/bin/env python3
"""Exercise completed UCI searches and reset-to-reset float NNUE replay."""
import argparse,base64,hashlib,json,queue,re,subprocess,threading,time

def raw(data):return {'encoding':'base64','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'data':base64.b64encode(data).decode('ascii')}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('engine');args=ap.parse_args()
 p=subprocess.Popen([args.engine],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
 chunks={'stdout':[],'stderr':[]};events=queue.Queue();sent=[];checks={};searches=[];error=None;unclosed=None
 def read(name):
  for data in iter(getattr(p,name).readline,b''):
   chunks[name].append(data)
   if name=='stdout':events.put(data)
  if name=='stdout':events.put(None)
 readers=[threading.Thread(target=read,args=(name,),daemon=True) for name in chunks]
 for t in readers:t.start()
 def send(text):sent.append(text);p.stdin.write((text+'\n').encode());p.stdin.flush()
 def until(predicate):
  deadline=time.monotonic()+30;lines=[]
  while True:
   remain=deadline-time.monotonic()
   if remain<=0:raise RuntimeError('protocol deadline; no process is killed')
   try:data=events.get(timeout=remain)
   except queue.Empty:raise RuntimeError('protocol deadline; no process is killed')
   if data is None:raise RuntimeError('stdout closed before required protocol reply')
   line=data.decode('utf-8','strict').rstrip('\r\n');lines.append(line)
   if re.search(r'(?i)^(?:FAIL:|error\b|info string (?:invalid|unknown|error|.*unavailable))',line):raise RuntimeError('unexpected protocol diagnostic: '+line)
   if predicate(line):return lines
 def cold(label,enabled):
  send('setoption name UseNNUE value '+('true' if enabled else 'false'))
  send('ucinewgame');send('isready');until(lambda x:x=='readyok')
  send('position startpos');send('go depth 4');lines=until(lambda x:x.startswith('bestmove '))
  last=None
  for line in lines:
   fields=line.split()
   if fields[:1]==['info'] and all(k in fields for k in ('depth','score','pv')):
    at=fields.index('score')
    if int(fields[fields.index('depth')+1])==4:
     last={'depth':4,'score_kind':fields[at+1],'score':int(fields[at+2]),'pv':fields[fields.index('pv')+1:]}
  move=lines[-1].split()[1]
  legal={f'{f}2{f}{rank}' for f in 'abcdefgh' for rank in ('3','4')}|{'b1a3','b1c3','g1f3','g1h3'}
  if last is None or last['pv'][:1]!=[move] or move not in legal:raise RuntimeError('missing complete d4 score/PV or illegal startpos bestmove')
  last.update(bestmove=move,label=label,UseNNUE=enabled);searches.append(last)
  return {k:last[k] for k in ('depth','score_kind','score','pv','bestmove')}
 try:
  send('uci');handshake=until(lambda x:x=='uciok')
  checks['UseNNUE_advertised_default_true']=handshake.count('option name UseNNUE type check default true')==1
  for command in ('setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false'):send(command)
  first=cold('cold_nnue_a',True);cold('cold_hce',False);replay=cold('cold_nnue_b',True)
  checks['three_completed_real_searches']=len(searches)==3
  checks['reset_to_reset_nnue_signature']=first==replay
  send('ucinewgame');send('position startpos');send('go perft 1')
  lines=until(lambda x:x.startswith('nodes '));checks['perft_startpos_1']=lines[-1]=='nodes 20'
  send('quit');p.stdin.close();p.wait(timeout=10)
  for t in readers:t.join(timeout=2)
  checks['exit_zero']=p.returncode==0;checks['reader_EOF']=not any(t.is_alive() for t in readers)
  checks['stderr_empty']=not b''.join(chunks['stderr'])
 except BaseException as exc:
  error=type(exc).__name__+': '+str(exc)
  try:
   if p.poll() is None:send('stop');send('quit');p.stdin.close();p.wait(timeout=5)
  except BaseException:unclosed=p.pid if p.poll() is None else None
  for t in readers:t.join(timeout=1)
 stdout=b''.join(chunks['stdout']);stderr=b''.join(chunks['stderr']);complete=not any(t.is_alive() for t in readers)
 passed=error is None and all(checks.values()) and complete and p.returncode==0 and not stderr
 print(json.dumps({'status':'PASS' if passed else 'FAIL','checks':checks,'searches':searches,'error':error,
   'scope':'Three actual depth4 UCI searches, each preceded by ucinewgame; equality only between identically reset NNUE-enabled replays. No integer-backend controls or general warm/cold claim.',
   'argv':[args.engine],'stdin':raw(('\n'.join(sent)+'\n').encode()),'stdout':raw(stdout),'stderr':raw(stderr),
   'exit':p.returncode,'unclosed_pid':unclosed,'stream_capture_complete':complete,'child_waited':p.returncode is not None},sort_keys=True))
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
