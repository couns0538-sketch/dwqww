"""Run the K23/C23 controls or a paired S1/B1 stage under one engine process per build."""
import argparse
import csv
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from selfplay import MINUTE40, RESULTS, ROOT, sha, utc


def receive(children, kind, timeout):
    # Each worker emits exactly one message and then waits at this barrier.
    pending={p.stdout:i for i,p in enumerate(children)}
    deadline=time.monotonic()+timeout
    replies=[None]*len(children)
    while pending:
        wait=deadline-time.monotonic()
        if wait<=0:
            raise TimeoutError(f'paired {kind} timeout')
        readable,_,_=select.select(list(pending),[],[],wait)
        for stream in readable:
            i=pending.pop(stream)
            words=stream.readline().split()
            if not words or words[0]!=kind:
                raise RuntimeError(f'worker {i} expected {kind}, got {words}')
            replies[i]=words[1:]
    return replies


def send_all(children,command):
    for p in children:
        p.stdin.write(command+'\n')
        p.stdin.flush()


def run_control(stage):
    labels=('K23-1','K23-2') if stage=='K23' else ('C23',)
    if stage=='C23' and '\nexit 0\n' not in (RESULTS/'K23-cmp.txt').read_text():
        raise ValueError('K23 did not pass')
    for arm in labels:
        with (RESULTS/f'{arm}-controller.txt').open('x') as log:
            subprocess.run([sys.executable,'-B',str(ROOT/'selfplay.py'),arm],stdout=log,stderr=subprocess.STDOUT,check=True)
        with (RESULTS/arm/'games.tsv').open() as receipts:
            numbers=[int(r['book_line']) for r in csv.DictReader(receipts,delimiter='\t')]
        if numbers!=list(range(700001,700011)):
            raise ValueError(f'{arm}: incomplete game range')
    left=RESULTS/'K23-1/records.txt'
    right=RESULTS/('K23-2' if stage=='K23' else 'C23')/'records.txt'
    comparison=subprocess.run(['cmp',str(left),str(right)],capture_output=True,text=True)
    with (RESULTS/f'{stage}-cmp.txt').open('x') as audit:
        print('utc',utc(),file=audit)
        print('cmp',left,right,file=audit)
        print('exit',comparison.returncode,file=audit)
        print('sha256_left',sha(left),'sha256_right',sha(right),file=audit)
        audit.write(comparison.stdout+comparison.stderr)
    if comparison.returncode!=(0 if stage=='K23' else 1):
        raise ValueError(f'{stage}: unexpected cmp exit {comparison.returncode}')


def run_pair(stage):
    if '\nexit 1\n' not in (RESULTS/'C23-cmp.txt').read_text():
        raise ValueError('C23 did not pass')
    children=[]; outputs=[]
    labels=[stage+'-'+b for b in ('r15d','kF')]
    complete=0; slowest=1.; reason='target'; interrupted=False
    try:
        for label in labels:
            err=(RESULTS/f'{label}-stderr.txt').open('x')
            outputs.append(err)
            children.append(subprocess.Popen([sys.executable,'-B',str(ROOT/'selfplay.py'),label],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1))
        ids=receive(children,'READY',60)
        if [r[0] for r in ids]!=labels:
            raise ValueError('wrong workers')
        with (RESULTS/f'{stage}-barriers.tsv').open('x',buffering=1) as log:
            print('completed\tgame\treleased_utc\tboth_done_utc\tr15d_pid\tkF_pid',file=log)
            for game in range(700001,702001):
                if time.time()+max(2,1.25*slowest+.2)>=MINUTE40:
                    reason='minute40'; break
                began=time.monotonic(); release=utc()
                send_all(children,f'PLAY {game}')
                try:
                    ready=receive(children,'PREPARED',max(.01,MINUTE40-time.time()-.25))
                except TimeoutError:
                    # Both workers still lack authorization to commit. Cancel the
                    # in-flight game on each; all earlier receipts remain intact.
                    reason='minute40'; interrupted=True
                    for p in children: p.send_signal(signal.SIGUSR1)
                    break
                if any(r[:2]!=[str(game),who[1]] for r,who in zip(ready,ids)):
                    raise ValueError('bad PREPARED receipt')
                send_all(children,f'COMMIT {game}')
                if receive(children,'DONE',30)!=ready:
                    raise ValueError('bad DONE receipt')
                slowest=max(slowest,time.monotonic()-began)
                complete+=1
                print(complete,game,release,utc(),ids[0][1],ids[1][1],sep='\t',file=log)
        if not interrupted:
            send_all(children,'FINISH '+reason)
        for p in children: p.stdin.close()
        for p in children:
            trailer=p.stdout.read()
            print(trailer.strip(),flush=True)
            if p.wait(timeout=10):
                raise RuntimeError(f'worker exit {p.returncode}')
        for label in labels:
            with (RESULTS/label/'games.tsv').open() as stream:
                games=[int(r['book_line']) for r in csv.DictReader(stream,delimiter='\t')]
            if games!=list(range(700001,700001+complete)):
                raise ValueError(label+' not at common boundary')
        with (RESULTS/f'{stage}-boundary.txt').open('x') as out:
            print('reason',reason,'\ncommon_completed_games',complete,'\nlast_game_id',700000+complete,file=out)
            print('stop_utc',utc(),'\nlongest_game_pair_seconds',slowest,file=out)
            print('inflight_game_discarded_before_commit',interrupted,file=out)
            print('common_game_commit_before_next_release true',file=out)
        if not complete: raise ValueError('no common games completed')
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: p.kill();p.wait()
            p.stdout.close()
            if not p.stdin.closed: p.stdin.close()
        for output in outputs: output.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('K23','C23','S1','B1'))
    stage=parser.parse_args().stage
    RESULTS.mkdir(exist_ok=True)
    print('start',stage,utc(),flush=True)
    if stage in ('K23','C23'): run_control(stage)
    else: run_pair(stage)
    print('finished',stage,utc(),flush=True)
