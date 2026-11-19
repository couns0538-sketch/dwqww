"""Job 19. Seeded one-process selfplay (R) and book-based persistent color pairs (F)."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from itertools import islice
import os
from pathlib import Path
import random
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
HARD = datetime.fromisoformat('2026-11-19T01:32:45+00:00').timestamp()
BOOK = Path('/workspace/work/j8gate/UHO_Lichess_4852_v1.epd')
NET = Path('/workspace/work/j7net/net768.nnue')
PC20 = Path('/workspace/work/j7base/pc20.txt')
BOOK_SHA = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
BUILDS = {
    'r15d': (Path('/workspace/work/j7base/build/forge'), '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671', (1,2)),
    'kF': (Path('/workspace/work/j16kf/build/forge'), 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb', (3,4)),
}
SETS = Path('/workspace/work/j18sets/sets.txt')
SETS_SHA = '8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81'
EDGE_FILE=Path('/workspace/work/j19sets/edge-sets.tsv')
EDGE_SHA='8a2c10231f4ea230831c6d2e73da26c369f121ddf93432c8135b17f42150d6d9'
ARMS={a:('r15d',3791,3792,250000,0,'F') for a in ('K19-1','K19-2','C19')}
for build in BUILDS:
    ARMS[f'D1-{build}']=(build,3793,3808,250000,0,'F')
    ARMS[f'D2-{build}']=(build,3809,3812,1000000,0,'F')
    for edge in range(1,81):
        first=500001+10*(edge-1)
        ARMS[f'E{edge:02}-{build}']=(build,first,first+4,2000,edge,'R')

def slot_count(arm):
    return 1

def edge_rows():
    if sha(EDGE_FILE)!=EDGE_SHA:
        raise ValueError('frozen edge table SHA mismatch')
    with EDGE_FILE.open() as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    if [int(r['edge']) for r in rows]!=list(range(1,81)):
        raise ValueError('expected ordered E01 through E80')
    return rows

def random_opening(game):
    rng=random.Random(game)
    board=chess.Board()
    opening=[]
    for _ in range(8):
        if board.is_game_over(claim_draw=True):
            break
        move=rng.choice(list(board.legal_moves))
        opening.append(move.uci())
        board.push(move)
    return board,opening

def live_settings(v,arm):
    old=PC20.read_text().splitlines()
    if len(old)!=22 or old[:2]!=['setoption name Threads value 1','setoption name Hash value 16'] or 'setoption name OwnBook value false' not in old:
        raise ValueError('unexpected PC20')
    network=['setoption name NNUEArchFile value '+str(NET),'setoption name NNUEArch value true']
    if not v:
        if arm=='C19':
            old[old.index('setoption name LmrQuietBase value 93')]='setoption name LmrQuietBase value 60'
        return old+network
    if sha(SETS)!=SETS_SHA:
        raise ValueError('frozen job18 table SHA mismatch')
    with SETS.open() as f:
        params=list(csv.DictReader(f,delimiter='\t'))
    values={r['name']:r['start'] for r in params}
    selected=edge_rows()[v-1]
    if selected['status']!='play' or selected['start']!=values[selected['name']] or selected['value']==selected['start']:
        raise ValueError('bad edge or starting value')
    if selected['name']!=params[(v-1)//2]['name'] or selected['bound']!=('min' if v%2 else 'max'):
        raise ValueError('edge name or bound out of order')
    if (int(selected['first_game']),int(selected['last_game']))!=ARMS[arm][1:3]:
        raise ValueError('edge game range mismatch')
    values[selected['name']]=selected['value']
    if len(values)!=40: raise ValueError('expected 40 settings')
    result=[]
    for cmd in old:
        name=cmd[15:].rsplit(' value ',1)[0]
        result.append('setoption name '+name+' value '+values.pop(name) if name in values else cmd)
    result.extend('setoption name '+name+' value '+value for name,value in values.items())
    return result+network

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

def search(p, position, moves, go):
    send(p,position+(' moves '+' '.join(moves) if moves else ''))
    send(p,go)
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
    build, first, last, limit, v, driver = ARMS[args.arm]
    go = ('go softnodes ' if driver=='R' else 'go nodes ')+str(limit)
    exe, expected_sha, cpus = BUILDS[build]
    slot = args.slot
    cpu = cpus[slot-1]
    nproc = int(subprocess.check_output(['nproc']))
    slots = slot_count(args.arm)
    if (nproc-1)//2 < slots or slot>slots or cpu not in os.sched_getaffinity(0):
        raise RuntimeError('unexpected CPU allocation')
    dest = RESULTS / args.arm / f'slot{slot}'
    dest.mkdir(parents=True)
    records = dest / 'records.txt'
    fens=[]
    if driver=='F':
        with BOOK.open() as f:
            fens=[s.strip() for s in islice(f,first-1,last)]
        if len(fens)!=last-first+1 or any(len(s.split())!=6 for s in fens):
            raise ValueError('bad original book lines')
    hashes = [sha(path) for path in (exe,BOOK,NET)]
    if hashes != [expected_sha,BOOK_SHA,NET_SHA]:
        raise ValueError(f'build/book/net SHA mismatch {hashes}')
    settings=live_settings(v,args.arm)
    stopfile=RESULTS/'JOB-STOP.txt'
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
        note('python_chess',chess.__version__,'go',go,'driver',driver,'set',v,'sets_sha256',SETS_SHA,'claim_draw',True,'max_plies_including_R_opening',300)
        note('protocol', 'pregame ucinewgame/isready. R single persistent process both sides; position startpos moves including random eight and all searched moves.' if driver=='R' else 'pregame BOTH ucinewgame/isready, wait both readyok. P1=White/P2=Black; only side to move receives position fen and prior moves.')
        if v:
            er=edge_rows()[v-1]
            note('edge_manifest_sha256',EDGE_SHA,'edge',v,er['name'],er['bound'],'requested',er['table_value'],'applied',er['value'])
        note('record_ply', 'zero-based absolute before move; normal first 8, final at most 299' if driver=='R' else 'one-based since book FEN; first 1, final at most 300')
        note('nodes field: final info line since current go; no info is NA. Search command:',go)
        for cmd in settings: note('both' if driver=='F' else 'engine',cmd)
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
            if stopfile.exists(): raise RuntimeError('job stopped by an earlier refusal')
            for role in (('P1_White','P2_Black') if driver=='F' else ('P1_Both',)):
                p = subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',bufsize=1)
                procs.append(p)
                note(role,'pid',p.pid,'child_cpu_affinity',sorted(os.sched_getaffinity(p.pid)))
                configure(p,role,settings,note)
            engines = procs if driver=='F' else [procs[0],procs[0]]
            if driver=='R': (dest/'openings.tsv').write_text('game\tmoves\n')
            for book_line in range(first+slot-1,last+1,slots):
                if driver=='R':
                    board,opening=random_opening(book_line)
                    with (dest/'openings.tsv').open('a') as op: op.write(str(book_line)+'\t'+' '.join(opening)+'\n')
                    position='position startpos'
                else:
                    opening=[]
                    fen=fens[book_line-first]
                    board=chess.Board(fen)
                    position='position fen '+fen
                moves = []
                game_rows = []
                na_rows = []
                role_counts = [0,0]
                role_na = [0,0]
                game_nodes = 0
                terminal_opening = driver=='R' and board.is_game_over(claim_draw=True)
                if not terminal_opening:
                    for p in procs:
                        send(p,'ucinewgame')
                        send(p,'isready')
                    for p in procs:
                        until(p,'readyok')
                note('game_start',book_line,utc(),'terminal_random_opening' if terminal_opening else 'readyok_all',*[p.pid for p in procs])
                while len(opening)+len(moves)<300 and not board.is_game_over(claim_draw=True):
                    ply=len(opening)+len(moves) if driver=='R' else len(moves)+1
                    role = 0 if board.turn == chess.WHITE else 1
                    active = role
                    if stopfile.exists(): raise RuntimeError('job stopped by another value refusal')
                    best,nodes = search(engines[role],position,opening+moves,go)
                    if best == '0000':
                        raise ValueError(f'nonterminal null move at {book_line}/{len(moves)+1}')
                    board.push_uci(best)
                    moves.append(best)
                    role_counts[role] += 1
                    if nodes is None:
                        role_na[role] += 1
                        na_rows.append([book_line,ply,'White' if role==0 else 'Black',engines[role].pid,best])
                    else:
                        game_nodes += nodes
                    game_rows.append(f"{book_line} {ply} {best} {nodes if nodes is not None else 'NA'}\n")
                    active = None
                outcome = board.outcome(claim_draw=True)
                result,termination = (outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
                mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM})
                try:
                    rec.write(''.join(game_rows).encode('ascii'))
                    rec.flush()
                    na_writer.writerows(na_rows)
                    nas.flush()
                    writer.writerow([book_line,len(moves),result,termination,game_nodes,len(na_rows),rec.tell(),slot,*[p.pid for p in engines],*role_counts,*role_na,utc()])
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
            if 'engine refusal pid=' in str(error):
                with stopfile.open('a') as fail: print(utc(),args.arm,slot,repr(error),file=fail)
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
