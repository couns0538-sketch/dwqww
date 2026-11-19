"""Job 17. One fixed slot, persistent White/Black processes, hard-node searches."""
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
    sys.path.insert(0, '/workspace/work/j10fens/vendor')
    import chess

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'
HARD = datetime.fromisoformat('2026-11-19T01:08:00+00:00').timestamp()
BOOK = Path('/workspace/work/j8gate/UHO_Lichess_4852_v1.epd')
NET = Path('/workspace/work/j7net/net768.nnue')
PC20 = Path('/workspace/work/j7base/pc20.txt')
BOOK_SHA = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
BUILDS = {
    'r15d': (Path('/workspace/work/j7base/build/forge'), '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671', (1,2)),
    'kF': (Path('/workspace/work/j16kf/build/forge'), 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb', (3,4)),
}
# build, physical line range inclusive, hard nodes, LmrQuietBase
ARMS = {a: ('r15d',3401,3410,50000,60 if a == 'C17' else 93) for a in ('K17-1','K17-2','C17')}
for stage, first, last, nodes in [('G1',3401,3600,50000), ('G2',3601,3640,250000)]:
    for build in BUILDS:
        ARMS[f'{stage}-{build}'] = (build,first,last,nodes,93)
HEADER = 'book_line plies result termination nodes na record_bytes slot p1_pid p2_pid p1_search p2_search p1_na p2_na end_utc'.split()
NA_HEADER = 'book_line ply side engine_pid bestmove'.split()
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b', re.I)
NODES = re.compile(r'(?:^| )nodes (\d+)\b')

def utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def send(p, command):
    p.stdin.write(command+'\n')
    p.stdin.flush()

def lines(p):
    for raw in p.stdout:
        line = raw.rstrip('\r\n')
        if REFUSAL.search(line):
            raise ValueError(f'engine refusal pid={p.pid}: {line}')
        yield line

def until(p, marker):
    reply = []
    for line in lines(p):
        reply.append(line)
        if line == marker:
            return reply
    raise EOFError(f'pid={p.pid} closed before {marker}')

def configure(p, role, settings, note):
    send(p,'uci')
    offered = until(p,'uciok')
    declared = {s[12:].split(' type ',1)[0] for s in offered if s.startswith('option name ')}
    for s in offered:
        if s.startswith('id '):
            note(role,s)
    for cmd in settings:
        if cmd[15:].rsplit(' value ',1)[0] not in declared:
            raise ValueError(f'{role} missing option {cmd}')
        send(p,cmd)
    send(p,'isready')
    reply = until(p,'readyok')
    for s in reply:
        note(role,s)
    for marker in ('NNUE v3 loaded','NNUE v3 active'):
        if not any(marker in s and 'checksum 30ab43b4ba5db5f3' in s for s in reply):
            raise ValueError(f'{role} missing {marker}/checksum')

def search(p, fen, moves, limit):
    send(p,'position fen '+fen+(' moves '+' '.join(moves) if moves else ''))
    send(p,'go nodes '+str(limit))
    last_info = None
    for s in lines(p):
        if s.startswith('info '):
            last_info = s
        if s.startswith('bestmove '):
            if last_info is None:
                return s.split()[1], None
            match = NODES.search(last_info)
            if not match:
                raise ValueError('last info line lacks nodes: '+last_info)
            return s.split()[1], int(match[1])
    raise EOFError(f'pid={p.pid} closed before bestmove')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arm', choices=ARMS)
    parser.add_argument('slot', type=int, choices=(1,2))
    args = parser.parse_args()
    build, first, last, limit, lmr = ARMS[args.arm]
    exe, expected_sha, cpus = BUILDS[build]
    slot = args.slot
    cpu = cpus[slot-1]
    nproc = int(subprocess.check_output(['nproc']))
    slots = (nproc-1)//2
    if slots != 2 or cpu not in os.sched_getaffinity(0):
        raise RuntimeError('unexpected CPU allocation')
    dest = RESULTS / args.arm / f'slot{slot}'
    dest.mkdir(parents=True)
    records = dest / 'records.txt'
    with BOOK.open() as f:
        fens = [s.strip() for s in islice(f,first-1,last)]
    if len(fens) != last-first+1 or any(len(s.split()) != 6 for s in fens):
        raise ValueError('bad original book lines')
    hashes = [sha(path) for path in (exe,BOOK,NET)]
    if hashes != [expected_sha,BOOK_SHA,NET_SHA]:
        raise ValueError(f'build/book/net SHA mismatch {hashes}')
    settings = PC20.read_text().splitlines()
    if len(settings)!=22 or settings[:2] != ['setoption name Threads value 1','setoption name Hash value 16'] or 'setoption name OwnBook value false' not in settings:
        raise ValueError('wrong PC20 settings')
    settings[settings.index('setoption name LmrQuietBase value 93')] = f'setoption name LmrQuietBase value {lmr}'
    settings += ['setoption name NNUEArchFile value '+str(NET),'setoption name NNUEArch value true']
    def stop(signum,frame):
        raise TimeoutError('deadline or requested stop')
    remaining = HARD - time.time() - .5
    if remaining <= 0: return 3
    signal.signal(signal.SIGALRM,stop)
    signal.signal(signal.SIGTERM,stop)
    signal.setitimer(signal.ITIMER_REAL,remaining)
    with (dest/'run.log').open('x',buffering=1) as log, records.open('xb') as rec, (dest/'games.tsv').open('x',newline='',buffering=1) as games, (dest/'no-info.tsv').open('x',newline='',buffering=1) as nas:
        def note(*parts):
            print(*parts,file=log,flush=True)
        writer = csv.writer(games,delimiter='\t',lineterminator='\n')
        na_writer = csv.writer(nas,delimiter='\t',lineterminator='\n')
        writer.writerow(HEADER)
        na_writer.writerow(NA_HEADER)
        note('start_utc',utc())
        note('arm',args.arm,'build',build,'slot',slot,'nproc',nproc,'S',slots,'logical_cpu',cpu,'book_range',first,last,'slot_first',first+slot-1,'stride',slots)
        for name,path,digest in zip(('executable','book','net'),(exe,BOOK,NET),hashes):
            note(name,path,'sha256',digest)
        note('python_chess',chess.__version__,'hard_node_limit',limit,'claim_draw',True,'max_plies',300)
        note('protocol pregame BOTH ucinewgame and isready, wait both readyok. P1=White P2=Black. Only side to move receives position fen with entire played-UCI history and go nodes N. Fresh last-info variable per search. No info means NA.')
        for cmd in settings: note('both',cmd)
        os.sched_setaffinity(0,{cpu})
        procs = []
        totals = [0,0,0,0]
        total_games = total_nodes = 0
        game_rows = []
        role_counts = [0,0]
        role_na = [0,0]
        book_line = None
        active = None
        status = 'INCOMPLETE'
        try:
            for role in ('P1_White','P2_Black'):
                p = subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',bufsize=1)
                procs.append(p)
                note(role,'pid',p.pid,'child_cpu_affinity',sorted(os.sched_getaffinity(p.pid)))
                configure(p,role,settings,note)
            for book_line in range(first+slot-1,last+1,slots):
                fen = fens[book_line-first]
                board = chess.Board(fen)
                moves = []
                game_rows = []
                na_rows = []
                role_counts = [0,0]
                role_na = [0,0]
                game_nodes = 0
                for p in procs:
                    send(p,'ucinewgame')
                    send(p,'isready')
                for p in procs:
                    until(p,'readyok')
                note('game_start',book_line,utc(),'readyok_both',*[p.pid for p in procs])
                while len(moves) < 300 and not board.is_game_over(claim_draw=True):
                    role = 0 if board.turn == chess.WHITE else 1
                    active = role
                    best,nodes = search(procs[role],fen,moves,limit)
                    if best == '0000':
                        raise ValueError(f'nonterminal null move at {book_line}/{len(moves)+1}')
                    board.push_uci(best)
                    moves.append(best)
                    role_counts[role] += 1
                    if nodes is None:
                        role_na[role] += 1
                        na_rows.append([book_line,len(moves),'White' if role==0 else 'Black',procs[role].pid,best])
                    else:
                        game_nodes += nodes
                    game_rows.append(f"{book_line} {len(moves)} {best} {nodes if nodes is not None else 'NA'}\n")
                    active = None
                outcome = board.outcome(claim_draw=True)
                result,termination = (outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
                mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM})
                try:
                    rec.write(''.join(game_rows).encode('ascii'))
                    rec.flush()
                    na_writer.writerows(na_rows)
                    nas.flush()
                    writer.writerow([book_line,len(moves),result,termination,game_nodes,len(na_rows),rec.tell(),slot,*[p.pid for p in procs],*role_counts,*role_na,utc()])
                    games.flush()
                    total_games += 1
                    total_nodes += game_nodes
                    totals = [a+b for a,b in zip(totals,role_counts+role_na)]
                    game_rows = []
                    role_counts = [0,0]
                    role_na = [0,0]
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK,mask)
            for p in procs: send(p,'quit')
            for p in procs:
                if p.wait(timeout=5): raise RuntimeError(f'engine exit {p.returncode}')
            status = 'COMPLETE'
        except BaseException as error:
            note('interrupted_utc',utc(),'reason',repr(error),'current_book_line',book_line,'uncommitted_plies',len(game_rows),'p1_p2_search_returns',role_counts,'p1_p2_na',role_na,'search_in_progress_role',active)
            if game_rows: (dest/'partial-game.txt').write_text(''.join(game_rows))
            if not isinstance(error,TimeoutError): raise
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            for p in procs:
                if p.poll() is None: p.kill()
                p.wait()
                p.stdin.close()
                p.stdout.close()
            for key,val in zip(('p1_search','p2_search','p1_na','p2_na'),totals): note(key,val)
            note('end_utc',utc())
            note('games',total_games)
            note('records',sum(totals[:2]))
            note('na_records',sum(totals[2:]))
            note('sum_nodes',total_nodes)
            note('records_sha256',sha(records))
            note('status',status)
    return 0 if status=='COMPLETE' else 3

if __name__=='__main__': sys.exit(main())
