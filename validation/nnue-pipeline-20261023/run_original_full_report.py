from pathlib import Path
import subprocess,os,json,time,hashlib,signal
R=Path('/workspace/dwqww');H=Path('/workspace/forge-nnue-handoff-20261023');O=H/'full-selected-original-report-controller-attempt1';O.mkdir(exist_ok=False)
net=H/'full-trained-net-freeze-attempt1/nnue_weights.inc';freeze=H/'full-trained-net-freeze-attempt1/FREEZE.json'
assert hashlib.sha256(net.read_bytes()).hexdigest()=='a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7'
assert hashlib.sha256(freeze.read_bytes()).hexdigest()=='3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c'
command=['/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python','-B','tools/nnue/compare_holdout.py','--data-dir',str(H/'prepared-all13m-reservoir-attempt1'),'--shipped-net','src/nnue_weights.inc','--candidate-net',str(net),'--reference-baseline-run',str(H/'baseline-shipped-fresh4149-attempt1'),'--out',str(H/'full-selected-original-report-attempt1'),'--batch-size','1024','--bootstrap-draws','2000','--seed','20261023']
(O/'command.json').write_text(json.dumps(command,indent=2)+'\n')
start=time.monotonic();error=None
with (O/'stdout').open('wb') as out,(O/'stderr').open('wb') as err:
 p=subprocess.Popen(command,cwd=R,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},stdout=out,stderr=err,start_new_session=True)
 (O/'START.json').write_text(json.dumps({'pid':p.pid,'frozen_network_sha256':hashlib.sha256(net.read_bytes()).hexdigest(),'freeze_sha256':hashlib.sha256(freeze.read_bytes()).hexdigest(),'selection_rule':'Frozen before report; no reselection from this result','scope':'Originalselection4149set; intervals conditional on40-epochselection, not independent audit or Elo'},indent=2)+'\n')
 try:p.wait(timeout=600)
 except BaseException as e:
  error=repr(e)
  if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
  p.wait()
result={'returncode':p.returncode,'owned_process_reaped':True,'elapsed_seconds':time.monotonic()-start,'error':error}
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if error or p.returncode:raise SystemExit(1)
