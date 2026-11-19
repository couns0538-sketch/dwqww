"""Capture original PGN blocks for the earliest contiguous closed opening rounds."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import time
from run_match import ROOT,STAGES,now

def pgbytes(pgn,stage,target):
    raw=pgn.read_bytes()
    selected={}
    for block in re.split(rb'(?=^\[Event )',raw,flags=re.M)[1:]:
        if not block.rstrip().endswith((b'1-0',b'0-1',b'1/2-1/2')):
            continue
        rnd=re.search(rb'^\[Round "(\d+)"\]',block,re.M)
        who=re.search(rb'^\[White "([^"]+)"\]',block,re.M)
        if not rnd or not who: continue
        game=2*int(rnd[1])-(who[1]==(stage+'-A').encode())
        if game>target: continue
        if game in selected: raise ValueError(f'duplicate PGN id {game}')
        selected[game]=block
    return b''.join(selected.values()) if set(selected)==set(range(1,target+1)) else None

def monitor(stage):
    base=ROOT/'results'
    output=base/f'{stage}.out'
    pgn=base/f'{stage}.pgn'
    ended=base/f'{stage}.meta'
    while not output.exists(): time.sleep(.1)
    seen=set()
    prefix=[]
    goals=iter(range(50,STAGES[stage][0]//2+1,50))
    need=next(goals)
    floor=0
    with output.open('rb') as src:
        while need:
            line=src.readline()
            if not line:
                if ended.exists() and f' {stage} end' in ended.read_text(): break
                time.sleep(.2);continue
            if not line.endswith(b'\n'):
                src.seek(-len(line),1)
                time.sleep(.1);continue
            prefix.append(line)
            found=re.match(rb'^Finished game (\d+) ',line)
            if not found: continue
            game=int(found[1])
            if game in seen: raise ValueError('duplicate finished ID')
            seen.add(game)
            while floor+1 in seen: floor+=1
            if floor<2*need: continue
            data=None
            for _ in range(100):
                if pgn.exists(): data=pgbytes(pgn,stage,need*2)
                if data is not None: break
                time.sleep(.1)
            if data is None: raise RuntimeError('published finished games lack matching complete PGN')
            dest=ROOT/'checkpoints'/stage/f'{need:04}'
            dest.mkdir(parents=True)
            (dest/'games.pgn').write_bytes(data)
            stdout=b''.join(prefix)
            (dest/'prefix.out').write_bytes(stdout)
            text=[f'{now()} {stage} complete-pair checkpoint',f'opening_rounds 1 through {need}',f'games {2*need}',
                f'controller_prefix_finished_games {len(seen)}; prefix may include other in-flight round results',
                f'{hashlib.sha256(data).hexdigest()}  games.pgn',f'{hashlib.sha256(stdout).hexdigest()}  prefix.out']
            tmp=dest/'ready.tmp'
            tmp.write_text('\n'.join(text)+'\n')
            tmp.replace(dest/'ready.txt')
            print('\n'.join(text),flush=True)
            need=next(goals,None)

if __name__=='__main__': monitor(sys.argv[1])
