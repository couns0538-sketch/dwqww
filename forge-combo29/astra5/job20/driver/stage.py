"""Run both builds with one persistent engine each; snapshot matching completed-game ranges."""
import csv
import fcntl
import hashlib
from pathlib import Path
import subprocess
import sys
import time
from selfplay import ROOT,RESULTS,ARMS,utc,sha
from compare_stage import compare

def snapshot(stage,n,width,offs,prefix):
    first=ARMS[stage+'-r15d'][1]
    root=ROOT/'checkpoints'/stage/f'{n:04}'
    dests=[RESULTS/f'{stage}-{build}' for build in ('r15d','kF')]
    batches=[]
    for dest in dests:
        ix=dest/'games.tsv'
        if not ix.exists(): return False
        with ix.open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        if len(rows)<n or not rows[n-1].get('mate',''): return False
        batch=rows[n-width:n]
        if [int(r['book_line']) for r in batch]!=list(range(first+n-width,first+n)):
            raise RuntimeError('unexpected game order')
        batches.append(batch)
    root.mkdir(parents=True)
    receipt=[f'created_utc {utc()}',f'common_completed_games {n}',f'chunk_games {width} first {first+n-width} last {first+n-1}']
    chunks=[]
    for i,(dest,rows,build) in enumerate(zip(dests,batches,('r15d','kF'))):
        end=int(rows[-1]['record_bytes'])
        with (dest/'records.txt').open('rb') as f:
            f.seek(offs[i])
            data=f.read(end-offs[i])
        if len(data)!=end-offs[i]: raise RuntimeError('incomplete records slice')
        chunks.append(data)
        prefix[i].update(data)
        (root/f'{build}-records.txt').write_bytes(data)
        receipt.append(f'{build} first_byte_offset {offs[i]} end_byte_offset {end} chunk_records {sum(int(r["plies"]) for r in rows)} chunk_na {sum(int(r["na"]) for r in rows)} chunk_mate {sum(int(r["mate"]) for r in rows)} chunk_sha256 {hashlib.sha256(data).hexdigest()} prefix_sha256 {prefix[i].hexdigest()}')
        offs[i]=end
    receipt.append(f'chunk_bytes_equal {chunks[0]==chunks[1]}')
    tmp=root/'ready.tmp'
    tmp.write_text('\n'.join(receipt)+'\n')
    tmp.replace(root/'ready.txt')
    print('common_checkpoint',n,utc(),flush=True)
    return True

def play(stage):
    order=['P1','P2','P3']
    i=order.index(stage)
    prior='C20' if i==0 else order[i-1]
    gate=RESULTS/f'{prior}-cmp.txt'
    if not gate.exists() or (RESULTS/'JOB-STOP.txt').exists(): raise RuntimeError('missing preceding stage or refusal')
    if prior=='C20' and 'exit 1\n' not in gate.read_text(): raise RuntimeError('C20 gate failed')
    print('stage_start_utc',utc(),flush=True)
    children=[subprocess.Popen([sys.executable,'-B',str(ROOT/'selfplay.py'),stage+'-'+b]) for b in ('r15d','kF')]
    width=100
    next_n=width
    offsets=[0,0]
    prefixes=[hashlib.sha256(),hashlib.sha256()]
    while True:
        if snapshot(stage,next_n,width,offsets,prefixes): next_n+=width
        if all(p.poll() is not None for p in children):
            while snapshot(stage,next_n,width,offsets,prefixes): next_n+=width
            break
        time.sleep(.5)
    exits=[p.wait() for p in children]
    print('arm_exit',exits,'end_utc',utc(),flush=True)
    if any(exits) or (RESULTS/'JOB-STOP.txt').exists(): return 3
    return compare(stage)

if __name__=='__main__':
    with (ROOT/'stage.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sys.exit(play(sys.argv[1]))
