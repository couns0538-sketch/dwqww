"""Job 20. Seeded single-process selfplay; compare the literal last depth line."""
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
HARD = datetime.fromisoformat('2026-11-19T01:54:00+00:00').timestamp()
NET = Path('/workspace/work/j7net/net768.nnue')
PC20 = Path('/workspace/work/j7base/pc20.txt')
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
BUILDS = {
    'r15d': (Path('/workspace/work/j7base/build/forge'), '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671', (1,2)),
    'kF': (Path('/workspace/work/j16kf/build/forge'), 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb', (3,4)),
}
ARMS={a:('r15d',600001,600020,'go softnodes 2000',16,60 if a=='C20' else 93) for a in ('K20-1','K20-2','C20')}
for build in BUILDS:
    ARMS[f'P1-{build}']=(build,600101,603100,'go softnodes 2000',16,93)
    ARMS[f'P2-{build}']=(build,610001,610500,'go softnodes 2000',1,93)
    ARMS[f'P3-{build}']=(build,620001,620100,'go nodes 20000',16,93)

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

HEADER = 'book_line plies result termination nodes na record_bytes slot p1_pid p2_pid p1_search p2_search p1_na p2_na end_utc score mate'.split()
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

# Each timing pair owns one separating horizontal whitespace before its key.
# Retain every other original character, including separators around untouched fields.
TIMING_FIELDS=re.compile(r'[ \t](?:time|nps)[ \t]+[0-9]+(?=[ \t]|$)')
SCORE=re.compile(r'(?:^|[ \t])score[ \t]+(cp|mate)[ \t]+[+-]?\d+(?=[ \t]|$)')

def normalize_depth(line):
    return TIMING_FIELDS.sub('',line)

def search(proc, position, go):
    send(proc,position)
    send(proc,go)
    selected=None
    reply=[]
    for line in lines(proc):
        reply.append(line)
        if line.startswith('info depth'):
            selected=line
        if line.startswith('bestmove '):
            return line.split()[1],selected,reply
    raise EOFError(f'pid={proc.pid} closed before bestmove')

def config(hash_mb,lmr):
    settings=PC20.read_text().splitlines()
    if len(settings)!=22 or settings[:2]!=['setoption name Threads value 1','setoption name Hash value 16'] or 'setoption name OwnBook value false' not in settings:
        raise ValueError('unexpected PC20')
    settings[1]=f'setoption name Hash value {hash_mb}'
    settings[settings.index('setoption name LmrQuietBase value 93')]=f'setoption name LmrQuietBase value {lmr}'
    return settings+['setoption name NNUEArchFile value '+str(NET),'setoption name NNUEArch value true']

def run(arm):
    build,first,last,go,hash_mb,lmr=ARMS[arm]
    exe,exe_sha,cpus=BUILDS[build]
    cpu=cpus[0]
    if sha(exe)!=exe_sha or sha(NET)!=NET_SHA: raise ValueError('wrong executable or net')
    if chess.__version__!='1.11.2' or cpu not in os.sched_getaffinity(0): raise RuntimeError('unexpected software/CPU')
    nproc=int(subprocess.check_output(['nproc']))
    options=config(hash_mb,lmr)
    dest=RESULTS/arm
    dest.mkdir(parents=True)
    raw_dir=ROOT/'raw-labels'
    raw_dir.mkdir(exist_ok=True)
    stopfile=RESULTS/'JOB-STOP.txt'
    def stop(signum,frame):
        raise TimeoutError('deadline or requested stop')
    remaining=HARD-time.time()-.5
    if remaining<=0: return 3
    signal.signal(signal.SIGALRM,stop)
    signal.signal(signal.SIGTERM,stop)
    signal.setitimer(signal.ITIMER_REAL,remaining)
    from contextlib import ExitStack
    with ExitStack() as stack:
        def output(name):
            return stack.enter_context((dest/name).open('x',encoding='ascii',newline='',buffering=1))
        log=output('run.log')
        sample=output('sample-uci.txt')
        ix=output('games.tsv')
        openings=output('openings.tsv')
        no_info=output('no-info.tsv')
        records=stack.enter_context((dest/'records.txt').open('xb'))
        raws=stack.enter_context((raw_dir/f'{arm}.txt').open('xb'))
        games=csv.writer(ix,delimiter='\t',lineterminator='\n')
        games.writerow(HEADER)
        na_output=csv.writer(no_info,delimiter='\t',lineterminator='\n')
        na_output.writerow(NA_HEADER)
        print('game\tmoves',file=openings)
        def note(*parts): print(*parts,file=log,flush=True)
        note('start_utc',utc())
        note('arm',arm,'build',build,'game_range',first,last,'go',go,'hash_mb',hash_mb)
        note('nproc',nproc,'S',1,'logical_cpu',cpu,'python_chess',chess.__version__)
        note('executable',exe,'sha256',exe_sha)
        note('net',NET,'sha256',NET_SHA)
        note('record_ply zero-based absolute ply before move; normal first 8, final at most 299')
        note('protocol One persistent engine, both sides. Reset/isready before each searched game; position startpos moves prefix and full searched history.')
        note('label Last literal info depth line since go, remove only time/nps key and decimal integer plus its one preceding separator; none gives NA.')
        for option in options: note('engine',option)
        os.sched_setaffinity(0,{cpu})
        proc=None
        status='INCOMPLETE'
        totals=dict(games=0,records=0,na_records=0,score_records=0,mate_records=0,sum_nodes=0)
        samples=set()
        sample_count=0
        game=None
        game_rows=[]
        try:
            if stopfile.exists(): raise RuntimeError('job already stopped')
            proc=subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='ascii',bufsize=1)
            note('P1_Both','pid',proc.pid,'child_cpu_affinity',sorted(os.sched_getaffinity(proc.pid)))
            configure(proc,'P1_Both',options,note)
            for game in range(first,last+1):
                board,opening=random_opening(game)
                print(game,' '.join(opening),sep='\t',file=openings)
                moves=list(opening)
                game_rows=[]
                raw_rows=[]
                na_rows=[]
                counts=[0,0]
                no_info_counts=[0,0]
                nodes=score_count=mate_count=0
                terminal=board.is_game_over(claim_draw=True)
                if not terminal:
                    send(proc,'ucinewgame')
                    send(proc,'isready')
                    until(proc,'readyok')
                note('game_start',game,utc(),'terminal_random_opening' if terminal else 'readyok_all',proc.pid)
                while len(moves)<300 and not board.is_game_over(claim_draw=True):
                    if stopfile.exists(): raise RuntimeError('job stopped by refusal')
                    ply=len(moves)
                    side=0 if board.turn==chess.WHITE else 1
                    position='position startpos moves '+' '.join(moves)
                    best,raw,reply=search(proc,position,go)
                    label=normalize_depth(raw) if raw is not None else 'NA'
                    scored=SCORE.search(label)
                    mate=bool(scored and scored[1]=='mate')
                    node_field=NODES.search(label)
                    duplicate_reason=('NA' if raw is None else 'mate' if mate else None)
                    if sample_count<3 or duplicate_reason is not None and duplicate_reason not in samples:
                        print(f'begin {game} {ply}',file=sample)
                        print('> '+position+'\n> '+go,file=sample)
                        for s in reply: print('< '+s,file=sample)
                        print('record '+f'{game} {ply} {best} '+label,file=sample)
                        print('end',file=sample)
                        sample_count+=1
                        if duplicate_reason: samples.add(duplicate_reason)
                    if best=='0000': raise ValueError(f'nonterminal null bestmove {game} {ply}')
                    board.push_uci(best)
                    moves.append(best)
                    counts[side]+=1
                    if raw is None:
                        no_info_counts[side]+=1
                        na_rows.append([game,ply,'White' if side==0 else 'Black',proc.pid,best])
                    nodes+=int(node_field[1]) if node_field else 0
                    score_count+=bool(scored)
                    mate_count+=mate
                    prefix=f'{game} {ply} {best} '
                    game_rows.append(prefix+label+'\n')
                    raw_rows.append(prefix+(raw if raw is not None else 'NA')+'\n')
                outcome=board.outcome(claim_draw=True)
                result,termination=(outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
                mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM})
                try:
                    records.write(''.join(game_rows).encode('ascii'))
                    records.flush()
                    raws.write(''.join(raw_rows).encode('ascii'))
                    raws.flush()
                    na_output.writerows(na_rows)
                    no_info.flush()
                    games.writerow([game,len(game_rows),result,termination,nodes,len(na_rows),records.tell(),1,proc.pid,proc.pid,*counts,*no_info_counts,utc(),score_count,mate_count])
                    ix.flush()
                    for key,delta in zip(totals,(1,len(game_rows),len(na_rows),score_count,mate_count,nodes)):
                        totals[key]+=delta
                    game_rows=[]
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK,mask)
            send(proc,'quit')
            if proc.wait(timeout=5): raise RuntimeError(f'engine exit {proc.returncode}')
            status='COMPLETE'
        except BaseException as error:
            if 'engine refusal pid=' in str(error):
                with stopfile.open('a') as refusal: print(utc(),arm,repr(error),file=refusal)
            note('interrupted_utc',utc(),'reason',repr(error),'game',game,'uncommitted_plies',len(game_rows))
            if game_rows: (dest/'partial-game.txt').write_text(''.join(game_rows))
            if not isinstance(error,TimeoutError): raise
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            if proc is not None:
                if proc.poll() is None: proc.kill()
                proc.wait()
                proc.stdin.close()
                proc.stdout.close()
            note('end_utc',utc())
            for key,value in totals.items(): note(key,value)
            note('records_sha256',sha(dest/'records.txt'))
            note('raw_labels_sha256',sha(raw_dir/f'{arm}.txt'))
            note('status',status)
    print(arm,status,totals,flush=True)
    return 0 if status=='COMPLETE' else 3

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm',choices=ARMS)
    sys.exit(run(p.parse_args().arm))
