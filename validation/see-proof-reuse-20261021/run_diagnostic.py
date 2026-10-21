#!/usr/bin/env python3
from pathlib import Path
import os,sys,json,subprocess,time,signal,selectors,re,hashlib
from run_owned import run
E=Path(__file__).resolve().parent;B=Path('/workspace/.cloud-setup/tt-refresh-native-release/forge');O=Path('/workspace/.cloud-setup/see-proof-reuse23-release/forge')
F=[('start','rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'),('kiwipete','r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'),('middlegame','r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10'),('endgame','8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1'),('pin','4k3/4n3/8/3p4/8/8/8/3QR1K1 w - - 0 1'),('ep','3r3k/8/8/3pP3/8/8/8/7K w - d6 0 1'),('underpromotion','r6k/1P6/8/8/8/8/8/7K w - - 0 1'),('later-promotion','1r6/P1Q5/2n4k/8/8/8/8/7K w - - 0 1')]
canonical=lambda s:re.sub(r'\b(time|nps) \d+',r'\1 <omitted>',s)
def fixtures(label,engine):
 name=label+'-fixtures';status={'argv':[str(engine)],'returncode':None,'timeout':False,'owned_group_closed':False,'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};p=None;records=[];sent=[];fault=None
 raw=(E/(name+'.stdout')).open('xb');err=(E/(name+'.stderr')).open('xb');buf=b'';sel=selectors.DefaultSelector();pending=[];global_deadline=time.monotonic()+180
 def send(s):sent.append(s);p.stdin.write((s+'\n').encode());p.stdin.flush()
 def until(pred,timeout=40):
  nonlocal buf
  lines=[];deadline=min(global_deadline,time.monotonic()+timeout)
  while True:
   if pending:line=pending.pop(0)
   else:
    remain=deadline-time.monotonic()
    if remain<=0:raise TimeoutError('UCI response deadline')
    if not sel.select(remain):raise TimeoutError('UCI response deadline')
    data=os.read(p.stdout.fileno(),65536)
    if not data:raise RuntimeError('UCI stream closed before predicate')
    raw.write(data);raw.flush();buf+=data
    parts=buf.split(b'\n');buf=parts.pop()
    pending.extend(x.decode('utf-8','strict').rstrip('\r') for x in parts)
    continue
   lines.append(line)
   if pred(line):return lines
 try:
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
  if label=='observer':env['FORGE_SEE_OBSERVER']=str(E/(name+'.counters.json'))
  p=subprocess.Popen([str(engine)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=env,start_new_session=True);status['pid']=p.pid;sel.register(p.stdout,selectors.EVENT_READ)
  send('uci');until(lambda s:s=='uciok',10)
  for cmd in ['setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false','isready']:send(cmd)
  until(lambda s:s=='readyok',10)
  for fixture,fen in F:
   send('ucinewgame');send('isready');until(lambda s:s=='readyok',10)
   for state in ['cold','warm']:
    send('position fen '+fen);send('go depth 8');lines=until(lambda s:s.startswith('bestmove '))
    assert any(s.startswith('info depth 8 ') for s in lines),(fixture,state,lines)
    assert lines[-1].split()[1]!='0000',(fixture,state)
    records.append({'fixture':fixture,'fen':fen,'state':state,'lines':lines,'canonical':[canonical(s) for s in lines]})
  send('quit');p.stdin.close();p.wait(10);status['returncode']=p.returncode
  rest=p.stdout.read();raw.write(rest)
 except BaseException as ex:
  fault=ex;status['exception']=repr(ex);status['timeout']=isinstance(ex,TimeoutError)
 finally:
  if p is not None:
   try:os.killpg(p.pid,0)
   except ProcessLookupError:status['owned_group_closed']=True
   else:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    if p.poll() is None:p.wait(3)
    try:os.killpg(p.pid,0)
    except ProcessLookupError:status['owned_group_closed']=True
   if status['returncode'] is None:status['returncode']=p.returncode
  sel.close();raw.close();err.close();status['end_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
  (E/(name+'.stdin')).write_text('\n'.join(sent)+'\n')
  (E/(name+'.status.json')).write_text(json.dumps(status,indent=2)+'\n')
  (E/(name+'.records.json')).write_text(json.dumps(records,indent=2)+'\n')
 if fault:raise fault
 assert status['returncode']==0 and status['owned_group_closed'] and len(records)==16,status
 return records
if __name__=='__main__':
 (E/'fixture-corpus.json').write_text(json.dumps({'depth':8,'threads':1,'hash_mb':16,'ownbook':False,'states':['cold','same-position warm repeated with retained TT/history'],'fixtures':F},indent=2)+'\n')
 bench=b'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nquit\n'
 (E/'bench.stdin').write_bytes(bench)
 run('baseline-bench11',[str(B)],60,stdin=bench)
 run('observer-bench11',[str(O)],60,env_extra={'FORGE_SEE_OBSERVER':str(E/'observer-bench11.counters.json')},stdin=bench)
 a=(E/'baseline-bench11.stdout').read_text().splitlines();b=(E/'observer-bench11.stdout').read_text().splitlines()
 assert [canonical(s) for s in a]==[canonical(s) for s in b],('bench canonical mismatch',a,b)
 assert any('bench depth 11 nodes 292545 ' in s for s in a),a
 a=fixtures('baseline',B);b=fixtures('observer',O)
 assert [(x['fixture'],x['state'],x['canonical']) for x in a]==[(x['fixture'],x['state'],x['canonical']) for x in b],'fixture canonical mismatch'
 replay=[]
 for label,rs in [('baseline',a),('observer',b)]:
  for x in rs:
   for line in x['lines']:
    if ' pv ' in line:replay.append(x['fen']+'\t'+line.split(' pv ',1)[1])
    if line.startswith('bestmove '):replay.append(x['fen']+'\t'+line.split()[1])
 (E/'pv-replay.tsv').write_text('\n'.join(replay)+'\n')
 for name in ['observer-bench11','observer-fixtures']:
  c=json.loads((E/(name+'.counters.json')).read_text());assert c['stage_faults']==c['scope_faults']==c['proof_positive_threshold']==0,c
  assert all(x['proof_false']==0 for x in c['sites']),c
 (E/'PARITY.json').write_text(json.dumps({'status':'PASS_EXACT_CANONICAL_OBSERVER_PARITY','bench11_nodes':292545,'baseline_and_observer_searches_each':16,'canonical_ignored_fields':['time','nps'],'pv_replay_rows_pending':len(replay),'claims':['observer behavior preserved for these frozen workloads'],'nps_gain':None,'elo_gain':None},indent=2)+'\n')
 print('PASS bench292545, 16 exact cold/warm searches per engine; replay rows',len(replay))
