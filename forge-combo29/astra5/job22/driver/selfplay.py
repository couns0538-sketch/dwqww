"""Job 22. Whole-game lifetime, literal last-info nodes and engine-resident memory."""
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
HARD = datetime.fromisoformat('2026-11-19T02:38:38+00:00').timestamp()
NET = Path('/workspace/work/j7net/net768.nnue')
PC20 = Path('/workspace/work/j7base/pc20.txt')
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
BUILDS = {
    'r15d': (Path('/workspace/work/j7base/build/forge'), '9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671', (1,2)),
    'kF': (Path('/workspace/work/j16kf/build/forge'), 'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb', (3,4)),
}
MINUTE40=datetime.fromisoformat('2026-11-19T02:28:38+00:00').timestamp()
ARMS={a:('r15d',700001,700010,'go softnodes 2000',16,60 if a=='C22' else 93) for a in ('K22-1','K22-2','C22')}
for build in BUILDS:
    ARMS[f'L1-{build}']=(build,700001,705000,'go softnodes 2000',16,93)
    ARMS[f'L0-{build}']=(build,None,None,'go softnodes 2000',16,93)

def l1_bounds(build):
    path=RESULTS/f'L1-{build}'/'games.tsv'
    with path.open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
    if len(rows)<10: raise RuntimeError('L1 has fewer than ten complete games')
    return int(rows[-10]['book_line']),int(rows[-1]['book_line'])

def start_ticks(pid):
    return int(Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19])

def resident(pid,expected_ticks):
    status=Path(f'/proc/{pid}/status').read_text().splitlines()
    line=next(s for s in status if s.startswith('VmRSS:'))
    match=re.fullmatch(r'VmRSS:\s+(\d+) kB',line)
    if not match or start_ticks(pid)!=expected_ticks: raise RuntimeError('PID changed or VmRSS unit unavailable')
    return int(match[1]),line,utc()

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

def search(proc, position, go):
    send(proc,position)
    send(proc,go)
    selected=None
    reply=[]
    for line in lines(proc):
        reply.append(line)
        if line.startswith('info '):
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
    if first is None: first,last=l1_bounds(build)
    synced=arm.startswith('L1-')
    exe,exe_sha,cpus=BUILDS[build]
    cpu=cpus[0]
    if sha(exe)!=exe_sha or sha(NET)!=NET_SHA: raise ValueError('wrong executable or net')
    if chess.__version__!='1.11.2' or cpu not in os.sched_getaffinity(0): raise RuntimeError('unexpected software/CPU')
    nproc=int(subprocess.check_output(['nproc']))
    options=config(hash_mb,lmr)
    dest=RESULTS/arm
    dest.mkdir(parents=True)
    raw_dir=ROOT/'raw-last'
    raw_dir.mkdir(exist_ok=True)
    stopfile=RESULTS/'JOB-STOP.txt'
    def stop(signum,frame):
        raise TimeoutError('deadline or requested stop')
    remaining=(MINUTE40 if synced else HARD)-time.time()-.3
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
        rssfile=output('rss-all.tsv')
        rss_milestones=output('rss.tsv')
        rss_source=output('rss-source.txt')
        rss_head='completed\tgame\tpid\tstart_ticks\tvmrss_kb\tobserved_utc'
        print(rss_head,file=rssfile);print(rss_head,file=rss_milestones)
        last_rss=None
        last_milestone=None
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
        note('protocol One persistent engine, both sides. Reset/isready before each game including terminal random roots; position startpos moves prefix and full searched history.')
        note('record node count of literal final info line of this search, including info string softnodes; absence is NA.')
        for option in options: note('engine',option)
        os.sched_setaffinity(0,{cpu})
        proc=None
        status='INCOMPLETE'
        totals=dict(games=0,records=0,na_records=0,sum_nodes=0)
        samples=set()
        sample_count=0
        game=None
        game_rows=[]
        try:
            if stopfile.exists(): raise RuntimeError('job already stopped')
            proc=subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='ascii',bufsize=1)
            note('P1_Both','pid',proc.pid,'child_cpu_affinity',sorted(os.sched_getaffinity(proc.pid)))
            ticks=start_ticks(proc.pid)
            observed_exe=Path(f'/proc/{proc.pid}/exe').resolve(strict=True)
            if observed_exe!=exe.resolve(strict=True): raise RuntimeError('unexpected live executable')
            note('proc_pid_exe',proc.pid,observed_exe)
            note('engine_start_ticks',ticks)
            configure(proc,'P1_Both',options,note)
            if synced:
                print('READY',arm,proc.pid,ticks,flush=True)
            cut=False
            for game in range(first,last+1):
                if synced:
                    token=sys.stdin.readline().strip()
                    if token=='FINISH minute40':
                        cut=True
                        break
                    if token!=f'PLAY {game}': raise RuntimeError('incorrect/absent common game release '+token)
                board,opening=random_opening(game)
                print(game,' '.join(opening),sep='\t',file=openings)
                moves=list(opening)
                game_rows=[]
                raw_rows=[]
                na_rows=[]
                counts=[0,0]
                no_info_counts=[0,0]
                nodes=0
                terminal=board.is_game_over(claim_draw=True)
                send(proc,'ucinewgame')
                send(proc,'isready')
                until(proc,'readyok')
                note('game_start',game,utc(),'terminal_random_opening_readyok_all' if terminal else 'readyok_all',proc.pid)
                while len(moves)<300 and not board.is_game_over(claim_draw=True):
                    if stopfile.exists(): raise RuntimeError('job stopped by refusal')
                    ply=len(moves)
                    side=0 if board.turn==chess.WHITE else 1
                    position='position startpos moves '+' '.join(moves)
                    best,raw,reply=search(proc,position,go)
                    node_field=NODES.search(raw) if raw is not None else None
                    if raw is not None and not node_field: raise ValueError('literal last info has no nodes: '+raw)
                    label=node_field[1] if node_field else 'NA'
                    duplicate_reason=('NA' if raw is None else None)
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
                    prefix=f'{game} {ply} {best} '
                    game_rows.append(prefix+label+'\n')
                    raw_rows.append(prefix+(raw if raw is not None else 'NA')+'\n')
                mem_kb,raw_vm,observed=resident(proc.pid,ticks)
                ordinal=game-first+1
                rssrow=(ordinal,game,proc.pid,ticks,mem_kb,observed)
                outcome=board.outcome(claim_draw=True)
                result,termination=(outcome.result(),outcome.termination.name) if outcome else ('*','PLY_LIMIT')
                if synced:
                    print('PREPARED',game,proc.pid,mem_kb,flush=True)
                    if sys.stdin.readline().strip()!=f'COMMIT {game}':
                        raise RuntimeError('missing simultaneous game commit authorization')
                mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM})
                try:
                    records.write(''.join(game_rows).encode('ascii'))
                    records.flush()
                    raws.write(''.join(raw_rows).encode('ascii'))
                    raws.flush()
                    na_output.writerows(na_rows)
                    no_info.flush()
                    print(*rssrow,sep='\t',file=rssfile)
                    print(f'{ordinal} {game} {proc.pid} {observed} '+raw_vm,file=rss_source)
                    last_rss=rssrow
                    if ordinal in {1,1000,2000,3000,4000}:
                        print(*rssrow,sep='\t',file=rss_milestones)
                        last_milestone=ordinal
                    games.writerow([game,len(game_rows),result,termination,nodes,len(na_rows),records.tell(),1,proc.pid,proc.pid,*counts,*no_info_counts,utc()])
                    ix.flush()
                    for key,delta in zip(totals,(1,len(game_rows),len(na_rows),nodes)):
                        totals[key]+=delta
                    game_rows=[]
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK,mask)
                if synced: print('DONE',game,proc.pid,mem_kb,flush=True)
            if synced and not cut:
                if sys.stdin.readline().strip()!='FINISH target': raise RuntimeError('missing target-close signal')
            send(proc,'quit')
            if proc.wait(timeout=5): raise RuntimeError(f'engine exit {proc.returncode}')
            status='CUT_MINUTE40' if cut else 'COMPLETE'
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
            if last_rss is not None and last_milestone!=last_rss[0]:
                print(*last_rss,sep='\t',file=rss_milestones)
            note('end_utc',utc())
            for key,value in totals.items(): note(key,value)
            note('records_sha256',sha(dest/'records.txt'))
            note('raw_last_sha256',sha(raw_dir/f'{arm}.txt'))
            note('status',status)
    print(arm,status,totals,flush=True)
    return 0 if status in ('COMPLETE','CUT_MINUTE40') else 3

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm',choices=ARMS)
    sys.exit(run(p.parse_args().arm))
