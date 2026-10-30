#!/usr/bin/env python3
"""Keep the active full-data experiment checkpointed while it executes.
IDEA_SOURCE: user's explicit ten-minute commit/push requirement.
No engine/process mutation, branch switch, force push, deletion or data acceptance.
"""
import argparse,json,subprocess,time
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]
BRANCH='astra-a1-data'

def git(*args):
    result=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError('git '+args[0]+' failed: '+result.stderr)
    return result.stdout.strip()

def checkpoint(progress):
    if git('branch','--show-current')!=BRANCH:raise RuntimeError('unexpected branch; no mutation')
    if Path(git('rev-parse','--show-toplevel')).resolve()!=ROOT:raise RuntimeError('unexpected worktree')
    if git('remote','get-url','origin')!='https://github.com/couns0538-sketch/dwqww.git':
        raise RuntimeError('unexpected remote; no mutation')
    if git('status','--porcelain','--','src','include','CMakeLists.txt','tools/nnue/train_resid_v3b.py'):
        raise RuntimeError('engine/trainer changes detected; no automated staging')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder=ROOT/'validation/astra-a1-data/live_checkpoints'
    folder.mkdir(exist_ok=True)
    with (folder/('full10m_'+stamp+'.json')).open('x') as f:json.dump(progress,f,indent=2);f.write('\n')
    with (ROOT/'docs/ASTRA_A1_DATA.md').open('a') as f:
        f.write('\nCheckpoint '+stamp+': full10M status '+str(progress.get('status'))+
                ', processed '+str(progress.get('input_rows'))+', kept '+str(progress.get('kept'))+
                '. Final independent bundle verification is still required. No Elo claim.\n')
    git('add','--sparse','-A')
    git('commit','-q','-m','astra-a1-data: preserve active full-data checkpoint '+stamp,
        '-m','IDEA_SOURCE: original data validation workflow and user-authorized periodic evidence preservation.')
    local=git('rev-parse','HEAD')
    git('push','origin','HEAD:'+BRANCH)
    remote=git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]
    if local!=remote:raise RuntimeError('remote checkpoint SHA does not match local HEAD')
    receipt={'utc':stamp,'local':local,'remote':remote,'status':'PUSH_VERIFIED'}
    with (folder/('publication_'+stamp+'.json')).open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt),flush=True)

p=argparse.ArgumentParser()
p.add_argument('--run',type=Path,required=True)
p.add_argument('--log',type=Path,required=True)
p.add_argument('--first-after',type=int,default=600)
p.add_argument('--once',action='store_true',help='read-only path/progress validation, no checkpoint or push')
a=p.parse_args()
if git('branch','--show-current')!=BRANCH:raise SystemExit('wrong branch')
next_push=time.monotonic()+a.first_after
with a.log.open('x') as log:
    while True:
        try:progress=json.loads((a.run/'progress.json').read_text())
        except (OSError,ValueError) as e:
            if a.once:raise
            print('Progress read pending: '+str(e),flush=True);time.sleep(5);continue
        sample={'utc':datetime.now(timezone.utc).isoformat(),**{k:progress.get(k) for k in ('status','input_rows','kept','wall_seconds_so_far')}}
        log.write(json.dumps(sample)+'\n');log.flush();print(json.dumps(sample),flush=True)
        if a.once:break
        finished=progress.get('status')!='RUNNING'
        if finished or time.monotonic()>=next_push:
            checkpoint(progress);next_push=time.monotonic()+600
        if finished:break
        time.sleep(30)
