#!/usr/bin/env python3
"""Protocol/history/terminal regression; no speed/strength claims."""
import json
import pathlib
import queue
import subprocess
import sys
import threading

exe = str(pathlib.Path(sys.argv[1]).resolve())
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
q = queue.Queue()
threading.Thread(target=lambda: [q.put(line.rstrip()) for line in p.stdout], daemon=True).start()
def send(s):
    p.stdin.write(s + '\n'); p.stdin.flush()
def until(prefix):
    lines = []
    while True:
        line = q.get(timeout=15); lines.append(line)
        if line.startswith(prefix): return lines
def search(position):
    send('ucinewgame'); send(position); send('go depth 4')
    lines = until('bestmove')
    info = [s for s in lines if s.startswith('info depth')][-1].split()
    return {'best': lines[-1].split()[1], 'score': info[info.index('score')+1:info.index('score')+3],
            'nodes': int(info[info.index('nodes')+1]), 'raw': lines}
def perft(position,depth=1):
    send(position); send('go perft '+str(depth)); return until('nodes ')
send('setoption name OwnBook value false')
results = []
for name,position,score,best in [
 ('mate_on_rule50','position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 100 1',['mate','0'],'0000'),
 ('stalemate','position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 100 1',['cp','0'],'0000'),
 ('rule50_legal','position fen 7k/8/8/8/8/8/8/R3K3 w - - 100 1',['cp','0'],None)]:
    r=search(position); assert r['score']==score,(name,r)
    assert (r['best']==best if best else r['best']!='0000'),(name,r)
    results.append({'case':name,**r})
cycle='g1f3 g8f6 f3g1 f6g8'
for repeats in [1,2]:
    r=search('position startpos moves '+' '.join([cycle]*repeats))
    assert (r['nodes']>0 if repeats==1 else r['nodes']==0 and r['score']==['cp','0']),r
    results.append({'case':'knight_cycle_'+str(repeats),**r})
send('ucinewgame');send('position startpos');send('go depth 4 searchmoves e2e5')
lines=until('bestmove');assert lines[-1]=='bestmove 0000',lines
assert any('restriction has no legal root moves' in s for s in lines),lines
results.append({'case':'empty_restriction','raw':lines})
send('position startpos')
lines=perft('position fen 8/8/8/8/8/8/8/4K3 w - - 0 1')
assert lines[-1]=='nodes 20' and any('invalid FEN' in s for s in lines),lines
results.append({'case':'invalid_fen_atomic','raw':lines})
lines=perft('position startpos moves e2e4 e7e5 e1e8')
assert lines[-1]=='nodes 20' and any('illegal move e1e8' in s for s in lines),lines
results.append({'case':'invalid_move_atomic','raw':lines})
lines=perft('position fen k4r2/8/8/8/8/8/8/4K2R w K - 0 1')
assert not any(s.startswith('e1g1:') for s in lines),lines
results.append({'case':'castle_through_check','raw':lines})
lines=perft('position fen 1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1')
for to in ['a8','b8']:
    for promotion in 'nbrq': assert any(s.startswith('a7'+to+promotion+':') for s in lines),lines
results.append({'case':'quiet_capture_promotions','raw':lines})
send('quit');p.wait(timeout=5);assert p.returncode==0,p.returncode
print(json.dumps({'binary':exe,'passed':True,'cases':results},indent=2))
