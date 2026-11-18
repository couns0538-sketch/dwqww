"""Run one C10 guard arm on the frozen job-10 FEN sequence, using a single engine process."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from counters import ALL, parse_counters

BASE_COLUMNS = ('index', 'fen', 'bestmove', 'info_depth', 'info_nodes', 'nodes')
DEADLINE = datetime.fromisoformat('2026-11-18T21:32:42+00:00').timestamp()


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')


def sha(path):
    with path.open('rb') as src:
        return hashlib.file_digest(src, 'sha256').hexdigest()


def send(process, log, command):
    print('> ' + command, file=log)
    process.stdin.write(command + '\n')
    process.stdin.flush()


def read_until(process, log, marker):
    lines=[]
    for text in process.stdout:
        line=text.rstrip('\r\n')
        print('< ' + line, file=log)
        if re.search(r'unknown option|invalid value|\bERROR\b', line, re.I):
            raise RuntimeError('engine diagnostic: ' + line)
        lines.append(line)
        if line == marker or line.startswith(marker+' '):
            return lines
    raise EOFError('engine closed before ' + marker)


def parse_response(response):
    totals=[s for s in response if s.startswith('info string guard10nodes ')]
    if len(totals) != 1 or not (m := re.fullmatch(r'info string guard10nodes total (\d+)',totals[0])):
        raise ValueError('invalid final engine node diagnostic: ' + repr(totals))
    total=int(m[1])
    depth,nodes='NA','NA'
    for line in response:
        if line.startswith('info depth '):
            match=re.search(r'^info depth (\d+)\b.*?\bnodes (\d+)\b',line)
            if match:
                depth,nodes=match.groups()
    best=re.fullmatch(r'bestmove (0000|[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder \S+)?',response[-1])
    if not best:
        raise ValueError('malformed bestmove ' + response[-1])
    return dict(bestmove=best[1],info_depth=depth,info_nodes=nodes,nodes=total,**parse_counters(response))


def run(args,target,stats):
    exe=args.exe.resolve(strict=True)
    fenfile=args.fens.resolve(strict=True)
    common=args.settings.resolve(strict=True).read_text().splitlines()
    if len(common)!=22 or common[:2]!=['setoption name Threads value 1','setoption name Hash value 16'] or common[-1]!='setoption name OwnBook value false':
        raise ValueError('PC20 plus Threads and Hash settings are incomplete')
    settings=common+[f'setoption name NullMateGuard value {args.guard}']
    fens=fenfile.read_text().splitlines()
    if len(fens)!=2000 or any(len(f.split())!=6 for f in fens):
        raise ValueError('expected 2,000 six-field FENs')
    (target/'settings.txt').write_text(
        f'executable {exe}\nexecutable_sha256 {sha(exe)}\n'
        f'fen_file {fenfile}\nfen_sha256 {sha(fenfile)}\n'
        'evaluation built-in\nprocesses 1\n' + '\n'.join(settings) + '\n'
        'per position: ucinewgame, isready, wait readyok, position fen, go nodes 20000, wait bestmove\n'
        'nodes = final SearchInfo.nodes in info string guard10nodes total X, including unfinished iteration work.\n'
        'info_nodes and info_depth = last depth-bearing UCI info; NA if none was emitted.\n')
    with (target/'uci.log').open('x') as transcript, (target/'rows.tsv').open('x',newline='') as dest:
        writer=csv.DictWriter(dest,BASE_COLUMNS+ALL,delimiter='\t',lineterminator='\n')
        writer.writeheader()
        process=subprocess.Popen([str(exe)], cwd=exe.parent, text=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        try:
            send(process,transcript,'uci')
            ids=read_until(process,transcript,'uciok')
            offered={s[12:].split(' type ',1)[0] for s in ids if s.startswith('option name ')}
            for s in settings:
                if s[15:].rsplit(' value ',1)[0] not in offered:
                    raise ValueError('option missing: ' + s)
                send(process,transcript,s)
            if 'option name NullMateGuard type spin default 0 min 0 max 2' not in ids:
                raise ValueError('unexpected guard option')
            send(process,transcript,'isready')
            read_until(process,transcript,'readyok')
            for i,fen in enumerate(fens,1):
                send(process,transcript,'ucinewgame')
                send(process,transcript,'isready')
                read_until(process,transcript,'readyok')
                send(process,transcript,'position fen '+fen)
                send(process,transcript,'go nodes 20000')
                data=parse_response(read_until(process,transcript,'bestmove'))
                writer.writerow(dict(index=i,fen=fen,**data))
                dest.flush()
                transcript.flush()
                stats['positions']=i
                stats['total nodes']+=int(data['nodes'])
                if data['info_nodes']=='NA':
                    stats['no depth info']+=1
                elif int(data['info_nodes'])!=int(data['nodes']):
                    stats['info nodes differ from final total']+=1
                if data['bestmove']=='0000':
                    stats['bestmove 0000']+=1
            send(process,transcript,'quit')
            for line in process.stdout:
                transcript.write('< '+line)
            if process.wait(timeout=10):
                raise RuntimeError(f'engine exit {process.returncode}')
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdin.close()
            process.stdout.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('guard',type=int,choices=(0,2))
    p.add_argument('exe',type=Path)
    p.add_argument('--fens',type=Path,default=Path('/workspace/work/j10fens/results/game_positions.fen'))
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'results')
    p.add_argument('--settings',type=Path,default=Path('/workspace/work/j7base/pc20.txt'))
    args=p.parse_args()
    remaining=DEADLINE-time.time()
    if remaining<=0:
        p.exit(3,'minute 50 reached\n')
    def stop(signum,frame):
        raise TimeoutError('stopped or minute 50 cutoff')
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGALRM,stop)
    signal.setitimer(signal.ITIMER_REAL,remaining)
    target=args.out/f'guard{args.guard}'
    target.mkdir(parents=True)
    stats=dict.fromkeys(('positions','total nodes','no depth info','info nodes differ from final total','bestmove 0000'),0)
    with (target/'checks.txt').open('x') as f:
        print(stamp(),'start',file=f,flush=True)
        try:
            run(args,target,stats)
        except (RuntimeError,OSError,ValueError,EOFError) as exc:
            print(stamp(),'incomplete',repr(exc),stats,file=f,flush=True)
            raise
        print(stamp(),'complete',file=f)
        for key,val in stats.items():
            print(f'{key}: {val}',file=f)
        print(stats,flush=True)


if __name__=='__main__':
    main()
