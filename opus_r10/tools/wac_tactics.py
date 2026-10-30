#!/usr/bin/env python3
"""R10 copy (only change: no external 'nice'; run it under run_pinned for priority) of the lock's 4_tests/wac300_harness/tactics.py, itself a Pack E copy of /workspace/ep10_lock/tactics.py. Only additions: env OPTS="Name=V,Name=V" -> extra setoption lines;
records final score and the first depth/time at which a mate score appears.
usage: tactics.py <engine> <tag> <suite.epd> <movetime_ms> <out.json> [ids_file]
Fresh ucinewgame + Clear Hash per position, Threads=1 Hash=16 OwnBook=false, go movetime T. Solved = bestmove in bm (and not in am)."""
import sys, subprocess, threading, queue, json, time, chess
path, tag, suite, mt, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
only = set(open(sys.argv[6]).read().split()) if len(sys.argv) > 6 else None
p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
q = queue.Queue()
threading.Thread(target=lambda: [q.put(l.rstrip()) for l in p.stdout] , daemon=True).start()
def send(c): p.stdin.write(c+'\n'); p.stdin.flush()
def until(pred, t):
    end = time.monotonic()+t; seen=[]
    while True:
        l = q.get(timeout=max(0.01,end-time.monotonic())); seen.append(l)
        if pred(l): return seen
send('uci'); until(lambda l:l=='uciok',10)
import os
extra=[x.split('=') for x in os.environ.get('OPTS','').split(',') if x]
for o in ('Threads value 1','Hash value 16','OwnBook value false'): send('setoption name '+o)
for k,v in extra: send(f'setoption name {k} value {v}')
send('isready'); until(lambda l:l=='readyok',10)
res = {}
for line in open(suite):
    line=line.strip()
    if not line: continue
    b, ops = chess.Board.from_epd(line); pid = ops['id']
    if only and pid not in only: continue
    send('ucinewgame'); send('setoption name Clear Hash'); send('isready'); until(lambda l:l=='readyok',10)
    send('position fen '+b.fen()); send(f'go movetime {mt}')
    t0=time.monotonic()
    ls = until(lambda l:l.startswith('bestmove'), 30)
    el = time.monotonic()-t0
    bm = chess.Move.from_uci(ls[-1].split()[1])
    ok = (bm in ops.get('bm',[]) if 'bm' in ops else True) and bm not in ops.get('am',[])
    info=[l for l in ls if l.startswith('info depth')]
    d = int(info[-1].split()[2]) if info else 0
    sc=None; mate_first=None
    for l in info:
        t=l.split()
        if 'score' in t:
            i=t.index('score'); sc=t[i+1]+' '+t[i+2]
            if t[i+1]=='mate' and mate_first is None: mate_first={'depth':int(t[2]),'time':int(t[t.index('time')+1]) if 'time' in t else None,'mate':int(t[i+2])}
    res[pid] = {'solved':ok,'move':b.san(bm),'bm':[b.san(m) for m in ops.get('bm',[])],'depth':d,'elapsed_ms':round(el*1000),'score':sc,'first_mate':mate_first}
send('quit'); p.wait(timeout=5)
json.dump({'tag':tag,'opts':os.environ.get('OPTS',''),'engine':path,'suite':suite,'movetime':mt,'results':res}, open(out,'w'))
print(tag, suite.split('/')[-1], mt, 'solved', sum(r['solved'] for r in res.values()), '/', len(res), 'maxelapsed', max(r['elapsed_ms'] for r in res.values()))
