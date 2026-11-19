"""Run one measured stage after its predecessor, as authorized by the publisher."""
import subprocess
import sys
from selfplay import ROOT, RESULTS, HARD, utc
from compare_stage import compare

STAGES=[f'{driver}{v}' for v in range(1,6) for driver in ('R','F')]

def run(stage):
    idx=STAGES.index(stage)
    prior=STAGES[idx-1] if idx else 'C18'
    gate=RESULTS/f'{prior}-cmp.txt'
    if not gate.is_file() or (RESULTS/'JOB-STOP.txt').exists():
        raise RuntimeError('preceding controls incomplete or job stopped')
    if not idx and 'exit 1\n' not in gate.read_text():
        raise RuntimeError('C18 failed to detect a difference')
    print('stage_start_utc',utc(),flush=True)
    children=[subprocess.Popen([sys.executable,'-B',str(ROOT/'arm.py'),f'{stage}-{build}']) for build in ('r15d','kF')]
    exits=[p.wait() for p in children]
    print('arm_exit',exits,'end_utc',utc(),flush=True)
    if any(exits) or (RESULTS/'JOB-STOP.txt').exists(): return 3
    rc=compare(stage)
    if stage.startswith('R'):
        files=[RESULTS/f'{stage}-{build}'/'openings.tsv' for build in ('r15d','kF')]
        op=subprocess.run(['cmp',*files],capture_output=True,text=True)
        with (RESULTS/f'{stage}-cmp.txt').open('a') as f:
            print('cmp',*files,file=f)
            print('opening_cmp_exit',op.returncode,file=f)
            if op.stdout: f.write(op.stdout)
            if op.stderr: f.write(op.stderr)
        if op.returncode: return 3
    return rc

if __name__=='__main__': sys.exit(run(sys.argv[1]))
