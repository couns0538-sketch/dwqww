"""Run one Job 29 soft-node limit on set O in one fresh process."""
import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import chess

PINS = {
    1000: (300918,1166,2,0,'9236b769d992254f'),
    2000: (590929,1393,0,0,'377dc0ab7edb4b30'),
    4000: (1140737,1613,0,0,'eb6b6afce426e7ea'),
}
FIRST_2000 = ['1 2474 f1e2','2 2039 f1c4','3 3174 e5d4']

def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def verified_bytes(path, expected):
    data=path.read_bytes()
    if sha256(data).hexdigest()!=expected: raise ValueError(f'identity mismatch: {path}')
    return data

def run(args):
    exe=args.exe.resolve(strict=True)
    verified_bytes(exe,'9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3')
    epd=verified_bytes(args.epd,'02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300')
    options=verified_bytes(args.settings,'d3caef4a239fbd1c3a4c2a1295523c090ddfc6f259fb1d080e8850e35f45945f').decode().splitlines()
    if len(options)!=22 or any('NodeClock' in s for s in options): raise ValueError('unexpected options')
    fens=[' '.join(line.split()[:4])+' 0 1' for line in epd.decode('ascii').splitlines()]
    assert len(fens)==200
    limit=args.limit
    dest=args.out/str(limit)
    dest.mkdir(parents=True,exist_ok=False)
    meta=dest/'run.meta'
    meta.write_text(f'Start UTC {now()}\nExecutable {exe}\nSet O {args.epd.resolve()}\n'
                    f'Options {args.settings.resolve()}\nLimit {limit}\nOne fresh process for all 200 positions; '
                    'ucinewgame and isready for each. Built-in evaluation.\n')
    spent=depths=caps=no_score=info_spent=0
    def alarm(signum,frame): raise TimeoutError('120 seconds waiting for engine UCI')
    signal.signal(signal.SIGALRM,alarm)
    with (dest/'wire.txt').open('x',buffering=1) as wire, (dest/'rows.txt').open('x',buffering=1) as rows, \
         (dest/'searches.tsv').open('x',newline='') as details, \
         subprocess.Popen([exe],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,bufsize=1,text=True) as p:
        with meta.open('a') as m: print('PID',p.pid,file=m)
        def send(line):
            print('> '+line,file=wire)
            p.stdin.write(line+'\n');p.stdin.flush()
        def read():
            result=p.stdout.readline()
            if not result: raise EOFError('engine closed its pipe')
            line=result.rstrip('\r\n')
            print('< '+line,file=wire)
            if re.search('unknown option|invalid value|ERROR|NNUE v3 (?:active|loaded)',line,re.I):
                raise ValueError(line)
            return line
        writer=csv.writer(details,delimiter='\t',lineterminator='\n')
        writer.writerow(('position','fen','limit','n','depth','last_depth_nodes','last_score','bestmove'))
        try:
            signal.alarm(120)
            send('uci')
            names=set()
            while (line:=read())!='uciok':
                m=re.match(r'option name (.+?) type ',line)
                if m:names.add(m[1])
            for opt in options:
                if opt.split(' value ')[0].removeprefix('setoption name ') not in names: raise ValueError(opt)
                send(opt)
            for i,fen in enumerate(fens,1):
                signal.alarm(120)
                send('ucinewgame');send('isready')
                while read()!='readyok': pass
                send('position fen '+fen);send(f'go softnodes {limit}')
                depth=latest_nodes=0
                score=None;actual=None
                while not (line:=read()).startswith('bestmove '):
                    if line.startswith('info '):
                        if d:=re.search(r'\bdepth (\d+)\b',line):
                            depth=int(d[1])
                            if n:=re.search(r'\bnodes (\d+)\b',line): latest_nodes=int(n[1])
                        if sc:=re.search(r'\bscore (cp|mate) (-?\d+)\b',line):score=sc[1]+' '+sc[2]
                    if footer:=re.fullmatch(r'info string softnodes nodes (\d+)',line):
                        if actual is not None:raise ValueError(f'duplicate final n at {i}')
                        actual=int(footer[1])
                if actual is None:raise ValueError(f'missing final n at {i}')
                best=line.split()[1]
                if chess.Move.from_uci(best) not in chess.Board(fen).legal_moves: raise ValueError(f'illegal move at {i}: {best}')
                row=f'{i} {actual} {best}'
                print(row,file=rows)
                writer.writerow((i,fen,limit,actual,depth,latest_nodes,score or 'NA',best))
                if limit==2000 and i<=3 and row!=FIRST_2000[i-1]:
                    raise ValueError(f'first differing known row {i}: observed {row}, expected {FIRST_2000[i-1]}')
                spent+=actual;depths+=depth;caps+=actual>=4*limit;no_score+=score is None;info_spent+=latest_nodes
            send('quit');p.stdin.close()
            if p.wait(timeout=10): raise ValueError(f'engine exit {p.returncode}')
        finally:
            signal.alarm(0)
            if p.poll() is None:p.kill()
    sig=sha256((dest/'rows.txt').read_bytes()).hexdigest()
    expected=PINS.get(limit)
    passed=expected is None or (spent,depths,caps,no_score,sig[:16])==expected
    if limit==1000 and info_spent!=294764:passed=False
    with (dest/'summary.tsv').open('x',newline='') as f:
        writer=csv.writer(f,delimiter='\t',lineterminator='\n')
        writer.writerow(('limit','searches','sum_n','sum_depth','n_ge_4N','no_score','row_sha16','sum_last_depth_nodes',
                         'expected_sum_n','expected_sum_depth','expected_n_ge_4N','expected_no_score','expected_sha16','check'))
        writer.writerow((limit,len(fens),spent,depths,caps,no_score,sig[:16],info_spent,
                         *(expected if expected else ('NA',)*5),'withheld' if not expected else 'PASS' if passed else 'FAIL'))
    with meta.open('a') as m: print(f'End UTC {now()}\nRows SHA256 {sig}',file=m)
    print((dest/'summary.tsv').read_text(),end='')
    if not passed:raise RuntimeError(f'Part 1 mismatch at {limit}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('limit',type=int,choices=(500,1000,2000,4000,8000))
    for key in ('exe','epd','settings','out'):p.add_argument(key,type=Path)
    run(p.parse_args())
