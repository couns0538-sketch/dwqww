"""Compare L1 on synchronized completed-game boundaries, then replay its last ten fresh."""
import csv
import fcntl
import hashlib
from pathlib import Path
import select
import subprocess
import sys
import time
from selfplay import ROOT,RESULTS,ARMS,MINUTE40,utc,sha,l1_bounds
from compare_stage import compare

BUILDS=('r15d','kF')

def receive(children,kind,timeout):
    # Read one logical message from each worker. The other may be waiting after its
    # own DONE, but cannot start another game until both new PLAY messages are sent.
    pending={p.stdout:i for i,p in enumerate(children)}
    deadline=time.monotonic()+timeout
    replies=[None]*len(children)
    while pending:
        wait=deadline-time.monotonic()
        if wait<=0: raise TimeoutError(f'paired {kind} timeout')
        readable,_,_=select.select(list(pending),[],[],wait)
        for stream in readable:
            i=pending.pop(stream)
            words=stream.readline().split()
            if not words or words[0]!=kind: raise RuntimeError(f'{BUILDS[i]} expected {kind}, got {words}')
            replies[i]=words[1:]
    return replies

def send_all(children,command):
    for p in children:
        p.stdin.write(command+'\n')
        p.stdin.flush()

def snapshot(completed,previous,offsets,prefix):
    dest=ROOT/'checkpoints'/'L1'/f'{completed:04}'
    dest.mkdir(parents=True)
    receipt=[f'created_utc {utc()}',f'common_completed_games {completed}',f'game_id_start {700001+previous} game_id_end {700000+completed}']
    data=[]
    for i,build in enumerate(BUILDS):
        arm=RESULTS/f'L1-{build}'
        with (arm/'games.tsv').open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        if len(rows)!=completed or int(rows[-1]['book_line'])!=700000+completed:
            raise ValueError('checkpoint escaped common state')
        end=int(rows[-1]['record_bytes'])
        with (arm/'records.txt').open('rb') as f:
            f.seek(offsets[i])
            raw=f.read(end-offsets[i])
        if len(raw)!=end-offsets[i]: raise ValueError('missing complete records')
        prefix[i].update(raw)
        data.append(raw)
        name=dest/f'{build}-records.txt'
        name.write_bytes(raw)
        receipt.append(f'{build} chunk_bytes {len(raw)} start_offset {offsets[i]} end_offset {end} chunk_sha256 {sha(name)} prefix_sha256 {prefix[i].hexdigest()}')
        offsets[i]=end
    receipt.append('chunk_bytes_equal '+str(data[0]==data[1]))
    temp=dest/'ready.tmp'
    temp.write_text('\n'.join(receipt)+'\n')
    temp.replace(dest/'ready.txt')
    print('common_checkpoint',completed,utc(),flush=True)

def l1():
    if not (RESULTS/'C22-cmp.txt').is_file() or 'exit 1\n' not in (RESULTS/'C22-cmp.txt').read_text():
        raise RuntimeError('C22 gate')
    errors=[];children=[]
    complete=previous=0
    offsets=[0,0]
    prefix=[hashlib.sha256(),hashlib.sha256()]
    slowest=1.
    reason=None
    try:
        for build in BUILDS:
            err=(ROOT/f'L1-{build}-stderr.txt').open('x')
            errors.append(err)
            children.append(subprocess.Popen([sys.executable,'-B',str(ROOT/'selfplay.py'),'L1-'+build],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1))
        ids=receive(children,'READY',60)
        if any(msg[0]!='L1-'+b for msg,b in zip(ids,BUILDS)): raise ValueError('unexpected arm handshake')
        with (RESULTS/'L1-barriers.tsv').open('x',buffering=1) as boundaries:
            print('ordinal\tgame\treleased_utc\tboth_done_utc\tr15d_pid\tkF_pid\tr15d_vmrss_kb\tkF_vmrss_kb',file=boundaries)
            for game in range(700001,705001):
                if time.time()+max(8,2*slowest+2)>=MINUTE40:
                    reason='minute40'
                    break
                start=utc()
                began=time.monotonic()
                send_all(children,f'PLAY {game}')
                prepared=receive(children,'PREPARED',min(90,max(.05,MINUTE40-time.time()-.5)))
                if any(msg[0]!=str(game) or msg[1]!=identity[1] for msg,identity in zip(prepared,ids)):
                    raise ValueError('wrong game or PID at prepare')
                send_all(children,f'COMMIT {game}')
                done=receive(children,'DONE',min(10,max(.05,MINUTE40-time.time()-.5)))
                if done!=prepared: raise RuntimeError('committed state differs from prepared state')
                if any(msg[0]!=str(game) or msg[1]!=identity[1] for msg,identity in zip(done,ids)):
                    raise ValueError('wrong game number or PID at shared boundary')
                slowest=max(slowest,time.monotonic()-began)
                complete+=1
                print(complete,game,start,utc(),ids[0][1],ids[1][1],done[0][2],done[1][2],sep='\t',file=boundaries)
                if complete%100==0:
                    snapshot(complete,previous,offsets,prefix)
                    previous=complete
            else:
                reason='target'
        if previous!=complete and complete>0: snapshot(complete,previous,offsets,prefix)
        cut=RESULTS/'L1-boundary.txt'
        cut.write_text(f'reason {reason}\ncommon_completed_games {complete}\nlast_game_id {700000+complete}\n'
            +f'r15d_completed {complete}\nkF_completed {complete}\nfinish_authorized_utc {utc()}\n'
            +f'operating_minute40_utc 2026-11-19T02:28:38Z\nlongest_observed_game_pair_seconds {slowest:.6f}\n'
            +'completion discipline both workers idle at their same game before next PLAY release; no post-hoc trimming\n')
        send_all(children,'FINISH '+reason)
        for p in children: p.stdin.close()
        for b,p in zip(BUILDS,children):
            remainder=p.stdout.read()
            rc=p.wait(timeout=8)
            print(remainder.strip(),flush=True)
            if rc: raise RuntimeError(f'{b} exit {rc}')
        if complete<1: raise RuntimeError('no L1 games')
        return compare('L1')
    except BaseException as exc:
        (RESULTS/'L1-interruption.txt').write_text(f'utc {utc()}\nlast_acknowledged_common_game {700000+complete}\ncommon_games {complete}\nreason {exc!r}\nCheck per-arm raw partial-game.txt and final games.tsv before interpreting any incomplete run.\n')
        raise
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill();p.wait()
            p.stdout.close()
            if not p.stdin.closed: p.stdin.close()
        for f in errors: f.close()

def l0():
    if not (RESULTS/'L1-cmp.txt').is_file(): raise RuntimeError('L1 not compared')
    bounds=[l1_bounds(b) for b in BUILDS]
    if bounds[0]!=bounds[1]: raise ValueError('L1 actual tails differ')
    first,last=bounds[0]
    print('L0 start_utc',utc(),'actual_seeds',first,last,flush=True)
    children=[subprocess.Popen([sys.executable,'-B',str(ROOT/'selfplay.py'),'L0-'+b]) for b in BUILDS]
    codes=[p.wait() for p in children]
    if any(codes): return 3
    combined=[]
    for b in BUILDS:
        old=RESULTS/('L1-'+b)
        new=RESULTS/('L0-'+b)
        with (old/'games.tsv').open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        start=int(rows[-11]['record_bytes']) if len(rows)>10 else 0
        stop=int(rows[-1]['record_bytes'])
        with (old/'records.txt').open('rb') as f:
            f.seek(start)
            data=f.read(stop-start)
        if len(data)!=stop-start: raise ValueError('incomplete L1 tail')
        cut=new/'from-L1.txt'
        cut.write_bytes(data)
        fresh=new/'records.txt'
        cmp=subprocess.run(['cmp',str(cut),str(fresh)],capture_output=True,text=True)
        if cmp.returncode not in (0,1): raise ValueError(cmp.stderr)
        reading='CARRIES' if cmp.returncode else 'SAME'
        with (RESULTS/f'L0-{b}-cmp.txt').open('x') as desc:
            print('source',old/'records.txt','start_byte_offset',start,'end_byte_offset',stop,file=desc)
            print('game_range',first,last,'games',len(rows[-10:]),file=desc)
            print('suffix_sha256',sha(cut),'fresh_sha256',sha(fresh),file=desc)
            print('cmp',cut,fresh,file=desc)
            print('exit',cmp.returncode,file=desc)
            if cmp.stdout: desc.write(cmp.stdout)
            if cmp.stderr: desc.write(cmp.stderr)
            if cmp.returncode:
                from itertools import zip_longest
                left,right=next((x,y) for x,y in zip_longest(cut.read_bytes().splitlines(),fresh.read_bytes().splitlines()) if x!=y)
                print('L1 suffix',left.decode() if left else 'EOF',file=desc)
                print('fresh L0',right.decode() if right else 'EOF',file=desc)
            print('reading',reading,file=desc)
        combined.append(f'{b} cmp_exit {cmp.returncode} reading {reading}')
    (RESULTS/'L0-cmp.txt').write_text('\n'.join(combined)+'\n')
    return 0

if __name__=='__main__':
    stage=sys.argv[1]
    if stage not in ('L1','L0'): raise ValueError(stage)
    with (ROOT/'stage.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(stage,'stage_start_utc',utc(),flush=True)
        code=l1() if stage=='L1' else l0()
        print(stage,'stage_end_utc',utc(),'exit',code,flush=True)
        sys.exit(code)
