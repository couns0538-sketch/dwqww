"""Replay physical book lines in one persistent Forge process, both colors, with full move history."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from itertools import islice
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

try:
    import chess
except ImportError:
    sys.path.insert(0,'/workspace/work/j10fens/vendor')
    import chess

HARD=datetime.fromisoformat('2026-11-19T00:57:07+00:00').timestamp()
BOOK_SHA='7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
NET_SHA='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
EXES={'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
      'kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'}
# build, physical lines, Hash MB, LmrQuietBase
ARMS={
    'K16-1':('r15d',2201,2220,16,93),'K16-2':('r15d',2201,2220,16,93),
    'C16':('r15d',2201,2220,16,60),
    'S1-r15d':('r15d',2201,3200,16,93),'S1-kF':('kF',2201,3200,16,93),
    'S2-r15d':('r15d',3201,3400,64,93),'S2-kF':('kF',3201,3400,64,93),
}
REFUSAL=re.compile(r'unknown option|invalid value|\bERROR\b',re.I)
NODES=re.compile(r'(?:^| )nodes (\d+)\b')


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def send(proc,cmd):
    proc.stdin.write(cmd+'\n')
    proc.stdin.flush()


def lines(proc):
    for raw in proc.stdout:
        s=raw.rstrip('\r\n')
        if REFUSAL.search(s):
            raise ValueError(f'engine refusal: {s}')
        yield s


def until(proc,marker):
    result=[]
    for s in lines(proc):
        result.append(s)
        if s==marker:
            return result
    raise EOFError('engine closed before '+marker)


def search(proc,fen,moves):
    send(proc,'position fen '+fen+(' moves '+' '.join(moves) if moves else ''))
    send(proc,'go softnodes 2000')
    last=None
    for s in lines(proc):
        if s.startswith('info '):
            last=s
        if s.startswith('bestmove '):
            fields=s.split()
            if last is None or not (m:=NODES.search(last)):
                raise RuntimeError('last info line before bestmove lacks nodes: '+repr(last))
            return fields[1],int(m[1]),last.startswith('info string softnodes nodes ')
    raise EOFError('engine closed before bestmove')


def run(args,stats):
    code,first,last,hash_mb,lmr=ARMS[args.arm]
    exe=args.exe.resolve(strict=True)
    net=args.net.resolve(strict=True)
    book=args.book.resolve(strict=True)
    dest=args.out/args.arm
    dest.mkdir(parents=True)
    records=dest/'records.txt'
    settings=args.settings.read_text().splitlines()
    if len(settings)!=22 or 'setoption name LmrQuietBase value 93' not in settings or settings[:2]!=['setoption name Threads value 1','setoption name Hash value 16']:
        raise ValueError('wrong settings reference')
    settings[1]=f'setoption name Hash value {hash_mb}'
    settings[settings.index('setoption name LmrQuietBase value 93')]=f'setoption name LmrQuietBase value {lmr}'
    settings+=['setoption name NNUEArchFile value '+str(net),'setoption name NNUEArch value true']
    args.out.mkdir(exist_ok=True)
    with book.open() as f:
        fens=[x.strip() for x in islice(f,first-1,last)]
    if len(fens)!=last-first+1:
        raise ValueError('incomplete book range')
    for fen in fens:
        if len(fen.split())!=6:
            raise ValueError('expected original six-field FEN')
    exe_sha,net_sha,book_sha=sha(exe),sha(net),sha(book)
    if exe_sha!=EXES[code] or net_sha!=NET_SHA or book_sha!=BOOK_SHA:
        raise ValueError(f'build/net/book SHA mismatch: {exe_sha} {net_sha} {book_sha}')
    partial=[]
    line_no=0
    soft_cap_rows=0
    with (dest/'run.log').open('x',buffering=1) as log, records.open('xb') as rec, (dest/'games.tsv').open('x',newline='',buffering=1) as games:
        def note(*words):
            print(*words,file=log,flush=True)
        w=csv.writer(games,delimiter='\t',lineterminator='\n')
        w.writerow('book_line plies result termination nodes record_bytes end_utc'.split())
        note('start_utc',utc())
        note('arm',args.arm,'build',code,'book_lines',first,last,'planned_games',len(fens))
        note('executable',exe,'sha256',exe_sha)
        note('book',book,'sha256',book_sha)
        note('net',net,'sha256',net_sha)
        note('python_chess',chess.__version__,'logical_cpu',args.cpu,'go softnodes 2000','threads',1,'Hash',hash_mb)
        note('settings begin')
        for setting in settings: note(setting)
        note('settings end')
        proc=None
        status='INCOMPLETE'
        try:
            os.sched_setaffinity(0,{args.cpu})
            proc=subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,text=True,encoding='utf8',bufsize=1)
            note('single_engine_pid',proc.pid,'child_cpu_affinity',sorted(os.sched_getaffinity(proc.pid)))
            send(proc,'uci')
            offered=until(proc,'uciok')
            declared={s[12:].split(' type ',1)[0] for s in offered if s.startswith('option name ')}
            for s in offered:
                if s.startswith('id '): note(s)
            for cmd in settings:
                if cmd[15:].rsplit(' value ',1)[0] not in declared:
                    raise ValueError('missing option: '+cmd)
                send(proc,cmd)
            send(proc,'isready')
            rsp=until(proc,'readyok')
            for s in rsp:note(s)
            for marker in ('NNUE v3 loaded','NNUE v3 active'):
                if not any(marker in s and 'checksum 30ab43b4ba5db5f3' in s for s in rsp):
                    raise ValueError('missing network marker: '+marker)
            for line_no,fen in enumerate(fens,first):
                board=chess.Board(fen)
                moves=[]
                partial=[]
                game_nodes=0
                game_soft=0
                send(proc,'ucinewgame')
                send(proc,'isready')
                until(proc,'readyok')
                while len(moves)<300 and not board.is_game_over(claim_draw=True):
                    best,nodes,is_soft=search(proc,fen,moves)
                    # push_uci rejects illegal moves. A null move is never a legal chess move.
                    if best=='0000':
                        raise ValueError(f'nonterminal null bestmove at line {line_no}, ply {len(moves)+1}')
                    board.push_uci(best)
                    moves.append(best)
                    partial.append(f'{line_no} {len(moves)} {best} {nodes}\n')
                    game_nodes+=nodes
                    game_soft+=is_soft
                outcome=board.outcome(claim_draw=True)
                receipt_result=outcome.result() if outcome else '*'
                reason=outcome.termination.name if outcome else 'PLY_LIMIT'
                # Publish records and the completion index together at each full-game boundary.
                # Mask stop briefly so a partially published game cannot enter the counts.
                blocked=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM})
                try:
                    data=''.join(partial).encode('ascii')
                    rec.write(data);rec.flush()
                    stats['games']+=1;stats['records']+=len(moves);stats['sum_nodes']+=game_nodes
                    soft_cap_rows+=game_soft
                    w.writerow([line_no,len(moves),receipt_result,reason,game_nodes,rec.tell(),utc()])
                    games.flush()
                    partial=[]
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK,blocked)
            send(proc,'quit')
            if proc.wait(timeout=10):
                raise RuntimeError(f'engine exit {proc.returncode}')
            status='COMPLETE'
        except (Exception,KeyboardInterrupt) as error:
            note('interrupted_utc',utc(),'reason',repr(error),'current_book_line',line_no,'uncommitted_plies',len(partial))
            if partial:
                (dest/'partial-game.txt').write_text(''.join(partial))
            if not isinstance(error,TimeoutError):
                raise
        finally:
            if proc is not None:
                if proc.poll() is None:proc.kill()
                proc.wait()
                proc.stdin.close();proc.stdout.close()
            note('end_utc',utc())
            for key,val in stats.items():note(key,val)
            note('last_info_softnodes_diagnostic_records',soft_cap_rows)
            note('records_sha256',sha(records))
            note('status',status)
    return 0 if status=='COMPLETE' else 3


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm',choices=ARMS)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True)
    p.add_argument('--book',type=Path,default=Path('/workspace/work/j8gate/UHO_Lichess_4852_v1.epd'))
    p.add_argument('--net',type=Path,default=Path('/workspace/work/j7net/net768.nnue'))
    p.add_argument('--settings',type=Path,default=Path('/workspace/work/j7base/pc20.txt'))
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'results')
    a=p.parse_args()
    if a.cpu not in os.sched_getaffinity(0):p.error('unavailable CPU')
    remaining=HARD-time.time()-.5
    if remaining<=0:p.exit(3,'past hard cutoff\n')
    def stop(signum,frame):raise TimeoutError('job 16 hard cutoff or stop')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop)
    signal.setitimer(signal.ITIMER_REAL,remaining)
    return run(a,dict(games=0,records=0,sum_nodes=0))


if __name__=='__main__':
    sys.exit(main())
