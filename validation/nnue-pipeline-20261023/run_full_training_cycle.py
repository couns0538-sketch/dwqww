"""Bounded orchestration for the already frozen NNUE protocol; no automatic retry."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,subprocess,time,sys
root=Path('/workspace/dwqww');hand=Path('/workspace/forge-nnue-handoff-20261023')
py='/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python'
out=hand/'full-training-controller-attempt1';out.mkdir(exist_ok=False)
def dump(name,value):(out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
source_names=['tools/nnue/residual_train.py','tools/nnue/train_nnue.py','tools/nnue/include_parser.py','tools/nnue/engine_contract.json','tools/nnue/compare_holdout.py','tools/nnue/prepare_residual_data.py','src/search.cpp','src/nnue.cpp','src/nnue_weights.inc','include/forge/nnue.hpp']
source_hashes={name:digest(root/name) for name in source_names}
protocol={'status':'PREDECLARED_BEFORE_FULL_DATA_TRAINING_OUTCOMES','utc':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'source_hashes':source_hashes,'primary_protocol':str(root/'validation/nnue-pipeline-20261023/TRAINING-PROTOCOL.json'),'sequence':['zero residual output main20epochs','separate shipped-network warm-start20epochs, same other parameters'],'warm_start_justification':'Measured shipped teacherMSE0.006082049055657535 below HCE0.006660536215902123 on frozen4149-row heldout; already allowed by primary protocol. Fresh-only warm run did not improve, retained separately.','data_gate':'Original fullprep24911 closedPASS, strictsource/hash/array validator, same4149-row validation arrays and provenance as baseline, all9sources/13.5Mexamined.','selection':'Keep initial and everyepoch. Fixed complete heldout pureteacher MSE per run. Selection intervals remain conditional, not an independent test or Elo.','retry_policy':'none; preserve firstfailure and stop','gpu':False}
dump('PROTOCOL.json',protocol)
started=time.monotonic();child=None
try:
 receipt=hand/'FULL-PREP-CLOSED.json'
 while not receipt.exists():
  if time.monotonic()-started>14400:raise TimeoutError('Original preparer did not close within bounded controller wait')
  time.sleep(5)
 closed=json.loads(receipt.read_text());dump('PREP-CLOSED-SNAPSHOT.json',closed)
 if closed.get('status')!='PASS_PREPARED_DATA_CLOSED':raise RuntimeError('Original preparer did not close PASS; no training attempted')
 sys.path.insert(0,str(root/'tools/nnue'))
 import numpy as np
 from residual_train import load_prepared_data
 data=hand/'prepared-all13m-reservoir-attempt1';train,val,manifest,manifest_sha=load_prepared_data(data)
 fresh=hand/'prepared-fresh-only-attempt1';fresh_manifest=json.loads((fresh/'manifest.json').read_text())
 assert len(train['score'])<=1000000 and len(train['score'])>14895 and len(val['score'])==4149
 assert manifest['statistics']['legacy_rows_examined']==13500000 and len(manifest['legacy_per_source'])==9
 assert manifest['artifacts']['validation-provenance.jsonl']['sha256']==fresh_manifest['artifacts']['validation-provenance.jsonl']['sha256']
 with np.load(fresh/'validation.npz',allow_pickle=False) as old:
  for name in ['features','score','hce','result_stm']:
   assert old[name].dtype==val[name].dtype and old[name].shape==val[name].shape and old[name].tobytes()==val[name].tobytes(),name
 assert {name:digest(root/name) for name in source_names}==source_hashes
 dump('DATA-GATE.json',{'status':'PASS_FULL_DATA_AND_EXACT_FROZEN_VALIDATION','manifest_sha256':manifest_sha,'train':len(train['score']),'validation':len(val['score']),'legacy_rows_examined':13500000,'legacy_per_source':manifest['legacy_per_source']})
 del train,val
 jobs=[]
 for label,warm in [('zero',False),('warm',True)]:
  run_dir=hand/('full1m-'+label+'20-attempt1')
  cmd=[py,'-B','tools/nnue/residual_train.py','--data-dir',str(data),'--run-dir',str(run_dir),'--epochs','20','--batch-size','1024','--threads','4','--lr','0.001','--min-lr','0.00001','--result-start','0','--result-end','0.1','--seed','20261023']
  if warm:cmd+=['--initial-net','src/nnue_weights.inc']
  dump(label+'.command.json',cmd);start=time.monotonic()
  with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
   child=subprocess.Popen(cmd,cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4'},stdout=stdout,stderr=stderr,start_new_session=True)
   dump(label+'.START.json',{'pid':child.pid,'utc':datetime.now(timezone.utc).isoformat(),'command':cmd})
   rc=child.wait();child=None
  result={'returncode':rc,'elapsed_seconds':time.monotonic()-start,'utc':datetime.now(timezone.utc).isoformat()};dump(label+'.result.json',result)
  if rc:raise RuntimeError(label+' actual training failed; originals retained; no retry')
  summary=json.loads((run_dir/'summary.json').read_text());assert summary['status']=='completed' and summary['epochs_completed']==20 and summary['input_integrity']=='passed'
  assert {name:digest(root/name) for name in source_names}==source_hashes
  jobs.append({'label':label,'run':str(run_dir),'best':summary['best'],'training_count':summary['training_count'],'validation_count':summary['validation_count'],'result':result})
  print(json.dumps(jobs[-1]),flush=True)
 dump('RESULT.json',{'status':'PASS_TWO_FULL_DATA_TRAINING_RUNS_CLOSED_NO_ELO_CLAIM','jobs':jobs,'utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started})
except BaseException as error:
 if child is not None:
  if child.poll() is None:os.killpg(child.pid,signal.SIGINT)
  try:child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 dump('FAILED.json',{'status':'FAILED_NO_RETRY','error':repr(error),'utc':datetime.now(timezone.utc).isoformat()})
 raise
