"""Start one measured stage or finalize E after all individual edge receipts."""
import fcntl
import subprocess
import sys
from aggregate import aggregate
from selfplay import RESULTS, ROOT, edge_rows, utc
from compare_stage import compare

def play(stage):
    edges=[f'E{int(r["edge"]):02}' for r in edge_rows() if r['status']=='play']
    if (RESULTS/'JOB-STOP.txt').exists(): raise ValueError('refusal stopped job')
    if stage=='aggregate':
        return aggregate(edges)
    order=['D1']+edges+['D2']
    i=order.index(stage)
    prior='C19' if i==0 else ('E' if stage=='D2' else order[i-1])
    path=RESULTS/f'{prior}-cmp.txt'
    if not path.is_file(): raise ValueError(f'preceding stage missing: {prior}')
    if prior=='C19' and 'exit 1\n' not in path.read_text(): raise ValueError('failed C19')
    print('stage',stage,'stage_start_utc',utc(),'global_game_limit',2,flush=True)
    children=[subprocess.Popen([sys.executable,'-B',str(ROOT/'arm.py'),f'{stage}-{build}']) for build in ('r15d','kF')]
    exits=[p.wait() for p in children]
    print('arm_exit',exits,'end_utc',utc(),flush=True)
    if any(exits) or (RESULTS/'JOB-STOP.txt').exists(): return 3
    rc=compare(stage)
    if stage.startswith('E'):
        files=[RESULTS/f'{stage}-{build}'/'openings.tsv' for build in ('r15d','kF')]
        op=subprocess.run(['cmp',*files],capture_output=True,text=True)
        with (RESULTS/f'{stage}-cmp.txt').open('a') as f:
            print('cmp',*files,file=f)
            print('opening_cmp_exit',op.returncode,file=f)
            if op.stdout: f.write(op.stdout)
            if op.stderr: f.write(op.stderr)
        if op.returncode: return 3
    return rc

if __name__=='__main__':
    with (ROOT/'stage.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sys.exit(play(sys.argv[1]))
