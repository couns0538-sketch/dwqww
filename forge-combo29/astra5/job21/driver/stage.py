"""Start an authorized job-21 stage, capture pair checkpoints, reconcile cut results."""
import fcntl
import subprocess
import sys
import time
from run_match import ROOT,STAGES,DEADLINE

def main(stage):
    if stage not in STAGES: raise ValueError(stage)
    if time.time() >= DEADLINE: return 3
    cmd=[sys.executable,'-B',str(ROOT/'run_match.py'),stage]
    res=ROOT/'results'
    if stage=='B2' and not (res/'B1-cutoff.txt').read_text().startswith('B1 status COMPLETE\n'):
        raise RuntimeError('B1 incomplete')
    if (res/f'{stage}.meta').exists(): raise RuntimeError('existing match evidence')
    with (ROOT/f'{stage}-controller.txt').open('x') as output,(ROOT/f'{stage}-checkpoints.log').open('x') as snapshot_log:
        controller=subprocess.Popen(cmd,stdout=output,stderr=subprocess.STDOUT)
        sampler=subprocess.Popen([sys.executable,'-B',str(ROOT/'checkpoints.py'),stage],stdout=snapshot_log,stderr=subprocess.STDOUT)
        rc=controller.wait()
        if not (res/f'{stage}.out').exists():
            sampler.terminate()
            sampler.wait()
            return rc or 1
        s=sampler.wait(timeout=30)
        check=subprocess.run([sys.executable,'-B',str(ROOT/'finish_check.py'),stage],stdout=output,stderr=subprocess.STDOUT)
        return rc or s or check.returncode

if __name__=='__main__':
    with (ROOT/'stage.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sys.exit(main(sys.argv[1]))
