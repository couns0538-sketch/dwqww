"""Job 25 fixed-node searches in one UCI process per (build, thread count)."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import chess

PINS={'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671','kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'}
COLUMNS='position repeat depth score nodes pv bestmove legal within60 elapsed_s first_raw_line last_raw_line info_count'.split()

class Engine:
    def __init__(self, exe, log):
        self.log=log
        self.seq=0
        self.p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,start_new_session=True)
        self.events=queue.Queue()
        self.t=threading.Thread(target=self.read,daemon=True)
        self.t.start()

    def read(self):
        # Line time is sampled when this reader receives it, before logging or parsing.
        import io
        for data in io.BufferedReader(self.p.stdout):
            self.events.put((time.monotonic_ns(),data.decode('utf-8').rstrip('\r\n')))
        self.events.put((time.monotonic_ns(),None))

    def record(self, stamp, direction, text):
        self.seq+=1
        self.log.write(f'{stamp} {direction} {text}\n')

    def send(self, cmd):
        at=time.monotonic_ns()
        self.record(at,'>',cmd)
        self.p.stdin.write((cmd+'\n').encode())
        self.p.stdin.flush()
        return at

    def receive(self, deadline):
        try:
            at,line=self.events.get(timeout=max(0,(deadline-time.monotonic_ns())/1e9))
        except queue.Empty:
            raise TimeoutError('engine response deadline')
        if line is None:
            raise EOFError(f'engine exited, status {self.p.poll()}')
        self.record(at,'<',line)
        if re.search(r'unknown option|invalid value|\bERROR\b',line,re.I):
            raise ValueError(line)
        return at,line

    def until(self, target):
        seen=[]
        deadline=time.monotonic_ns()+60_000_000_000
        while True:
            _,line=self.receive(deadline)
            seen.append(line)
            if line==target:return seen


def parse_info(line):
    fields=line.split(); depth=fields.index('depth'); score=fields.index('score'); nodes=fields.index('nodes'); pv=fields.index('pv')
    bound=fields[score+3:score+4]
    exact_score=' '.join(fields[score+1:score+3]+(bound if bound in (['lowerbound'],['upperbound']) else []))
    return fields[depth+1],exact_score,fields[nodes+1],' '.join(fields[pv+1:])


def match(args):
    exe=args.exe.resolve(); net=args.net.resolve(); out=args.out
    digest=hashlib.sha256(exe.read_bytes()).hexdigest(); assert digest==PINS[args.build]
    assert hashlib.sha256(net.read_bytes()).hexdigest()=='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
    pos=args.book.read_text().splitlines()[:30];assert len(pos)==30
    fens=[' '.join(s.split()[:4])+ ' 0 1' for s in pos];boards=[chess.Board(s) for s in fens];assert all(b.is_valid() for b in boards)
    settings=args.pc20.read_text().splitlines();assert settings[0]=='setoption name Threads value 1';settings[0]=f'setoption name Threads value {args.threads}'
    settings += [f'setoption name NNUEArchFile value {net}', 'setoption name NNUEArch value true']
    out.mkdir(parents=True,exist_ok=True)
    with (out/'uci.log').open('x',encoding='utf-8') as raw,(out/'searches.tsv').open('x',encoding='utf-8',newline='') as tab,(out/'run.meta').open('x',encoding='utf-8') as meta:
        writer=csv.DictWriter(tab,fieldnames=COLUMNS,delimiter='\t',lineterminator='\n');writer.writeheader()
        e=Engine(exe,raw)
        try:
            print(f'UTC start {datetime.now(timezone.utc).isoformat()}\nexe {exe}\nsha256 {digest}\npid {e.p.pid}\naffinity {sorted(os.sched_getaffinity(0))}\npython-chess {chess.__version__}\nbook {args.book}\nbook-sha256 {hashlib.sha256(args.book.read_bytes()).hexdigest()}\nnet {net}\ncolumn one in uci.log = monotonic nanoseconds; > send, < receive\nFour-field EPD normalized with halfmove/fullmove 0 1. Position outer loop, 8 repeats inner. Each search has its own 60-second deadline.',file=meta,flush=True)
            e.send('uci'); announced=e.until('uciok'); options={l.split(' type ',1)[0][12:] for l in announced if l.startswith('option name ')}
            for s in settings:
                assert s.split(' value ',1)[0][15:] in options,s
                e.send(s)
            e.send('isready'); setup=e.until('readyok');assert any('30ab43b4ba5db5f3' in l for l in setup) and any('NNUE v3 active' in l for l in setup),setup
            for i,(fen,board) in enumerate(zip(fens,boards),1):
                for rep in range(1,9):
                    first=e.seq+1;e.send('ucinewgame');e.send('isready');e.until('readyok');e.send('position fen '+fen)
                    start=e.send('go nodes 100000');deadline=start+60_000_000_000; last=None; count=0; best=''; at=deadline; timedout=False
                    while True:
                        try: received,line=e.receive(deadline)
                        except TimeoutError:
                            if timedout:break
                            timedout=True;e.send('stop');deadline=time.monotonic_ns()+5_000_000_000;continue
                        if line.startswith('info '):
                            count+=1
                            if re.search(r'\bdepth \d+',line) and re.search(r'\bnodes \d+',line):last=line
                        if line.startswith('bestmove '):
                            best=line.split()[1];at=received;break
                    within=bool(best) and at-start<=60_000_000_000
                    try: legal=bool(best) and chess.Move.from_uci(best) in board.legal_moves
                    except ValueError: legal=False
                    parsed=parse_info(last) if last else ('NA',)*4
                    writer.writerow(dict(zip(COLUMNS,[i,rep,*parsed,best or 'NA',int(legal),int(within),f'{(at-start)/1e9:.9f}',first,e.seq,count])))
                    raw.flush();tab.flush()
                    if not best:raise RuntimeError('No bestmove received by deadline or stop grace; single process cannot resume safely.')
                print(f'completed position {i} of 30',flush=True)
            e.send('quit');e.p.wait(timeout=10)
            print(f'UTC end {datetime.now(timezone.utc).isoformat()}\nexit {e.p.returncode}',file=meta)
            assert e.p.returncode==0
        finally:
            if e.p.poll() is None:e.p.kill();e.p.wait()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('build',choices=PINS);p.add_argument('threads',type=int,choices=[1,2,4]);p.add_argument('exe',type=Path);p.add_argument('net',type=Path);p.add_argument('book',type=Path);p.add_argument('pc20',type=Path);p.add_argument('out',type=Path)
    match(p.parse_args())
