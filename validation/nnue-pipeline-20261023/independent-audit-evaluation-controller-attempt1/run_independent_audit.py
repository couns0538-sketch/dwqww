"""Execute the publicly frozen candidate's preregistered independent audit once."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,subprocess,time

OUT=Path(__file__).resolve().parent
ROOT=Path('/workspace/dwqww')
HAND=Path('/workspace/forge-nnue-handoff-20261023')
EXPECTED_PROTOCOL='942677f2268db47c922292cdf29fc90a722a999d26b68f2e842bcb9ce7f92ab0'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()

def require(condition,message):
 if not condition:raise ValueError(message)

def dump(path,value):
 with Path(path).open('x') as stream:stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')

def run(label):
 spec=json.loads((OUT/(label+'.command.json')).read_text())
 t=time.monotonic();process=None
 with (OUT/(label+'.stdout.txt')).open('xb') as stdout,(OUT/(label+'.stderr.txt')).open('xb') as stderr:
  process=subprocess.Popen(spec['argv'],cwd=spec['cwd'],env={**os.environ,**spec['environment_overrides'],'OPENBLAS_NUM_THREADS':'1'},stdout=stdout,stderr=stderr,start_new_session=True)
  dump(OUT/(label+'.START.json'),{'pid':process.pid,'utc':datetime.now(timezone.utc).isoformat(),'argv':spec['argv'],'environment_overrides':{**spec['environment_overrides'],'OPENBLAS_NUM_THREADS':'1'}})
  error=None
  try:rc=process.wait(timeout=600)
  except BaseException as failure:
   error=repr(failure)
   if process.poll() is None:os.killpg(process.pid,signal.SIGINT)
   try:rc=process.wait(timeout=30)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);rc=process.wait()
  result={'returncode':rc,'elapsed_seconds':time.monotonic()-t,'utc':datetime.now(timezone.utc).isoformat(),'error':error,'owned_process_reaped':process.poll() is not None,'stdout_sha256':sha(OUT/(label+'.stdout.txt')),'stderr_sha256':sha(OUT/(label+'.stderr.txt'))}
  dump(OUT/(label+'.RESULT.json'),result)
 require(error is None and rc==0,label+' failed; stop first audit attempt without retry or reselection')
 return result

def main():
 t=time.monotonic();protocol_path=OUT/'PROTOCOL.json'
 require(sha(protocol_path)==EXPECTED_PROTOCOL,'Preregistered evaluation protocol changed')
 protocol=json.loads(protocol_path.read_text())
 bound=[protocol[k] for k in ['public_proof','frozen_selection','frozen_candidate','shipped_network','masked_data_manifest','original_audit_protocol','actual_unused_audit_data_closure']]
 bound += [{'path':str(ROOT/name),'sha256':value} for name,value in protocol['source_hashes'].items()]
 bound += [{'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__))}, {'path':str(protocol_path),'sha256':EXPECTED_PROTOCOL}]
 def verify_bound():
  for identity in bound:require(sha(identity['path'])==identity['sha256'],'Changed frozen input: '+identity['path'])
 dump(OUT/'BOUND-INPUTS-BEFORE.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':bound})
 verify_bound()
 baseline_result=run('baseline')
 baseline=HAND/'independent-audit-shipped-baseline-attempt1'
 s=json.loads((baseline/'summary.json').read_text())
 require(s['status']=='baseline_only' and s['input_integrity']=='passed' and s['epochs_completed']==0 and not s['epochs'],'Baseline unexpectedly trained or did not close')
 require(s['validation_count']==8881 and s['initial']['count']==8881 and s['training_count']==1321,'Baseline audit row counts differ')
 require(s['manifest_sha256']==protocol['masked_data_manifest']['sha256'],'Baseline did not use frozen audit manifest')
 require(s['config']['threads']==1 and s['config']['baseline_only'] is True and s['config']['initial_net']['sha256']==protocol['shipped_network']['sha256'],'Baseline model/thread identity differs')
 verify_bound()
 compare_result=run('comparison')
 comparison=HAND/'independent-audit-frozen-zeroep3-report-attempt1'
 m=json.loads((comparison/'metrics.json').read_text())
 require(m['status']=='PASS_FIXED_HELDOUT_LOSS_COMPARISON_NOT_ELO' and m['input_integrity']=='passed','Comparison did not close with input integrity')
 require(m['rows']==8881 and m['represented_games']==109 and m['listed_validation_games']==111,'Complete audit row/game counts differ')
 require(m['manifest_sha256']==protocol['masked_data_manifest']['sha256'],'Comparison audit manifest differs')
 require(m['candidate_net']['sha256']==protocol['frozen_candidate']['sha256'] and m['shipped_net']['sha256']==protocol['shipped_network']['sha256'],'Compared network identities differ')
 require(m['bootstrap_draws']==2000 and m['seed']==20261023,'Bootstrap differs from preregistration')
 require(m['reference_holdout_check']['status']=='PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE' and m['reference_holdout_check']['reference_run']==str(baseline),'Comparison lacks the new same-audit reference')
 require(sha(comparison/'per-row-losses.npz')==m['per_row_artifact']['sha256'],'Original per-row loss artifact differs')
 verify_bound()
 result={'status':'PASS_ONCE_ONLY_FROZEN_CANDIDATE_INDEPENDENT_AUDIT_EXECUTION_NOT_ELO','utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-t,
         'protocol_sha256':EXPECTED_PROTOCOL,'baseline_run':str(baseline),'comparison_run':str(comparison),'baseline_result':baseline_result,'comparison_result':compare_result,
         'metrics_path':str(comparison/'metrics.json'),'metrics_sha256':sha(comparison/'metrics.json'),'report_sha256':sha(comparison/'REPORT.md'),'per_row_artifact':m['per_row_artifact'],
         'frozen_candidate':protocol['frozen_candidate'],'frozen_selection':protocol['frozen_selection'],'public_selection_commit':protocol['public_selection_commit'],'public_net_only_source_commit':protocol['public_net_only_source_commit'],
         'rows':m['rows'],'represented_games':m['represented_games'],'listed_validation_games':m['listed_validation_games'],'loss_mse':m['loss_mse'],'comparisons':m['comparisons'],
         'all_source_net_public_freeze_and_data_input_bindings_unchanged':True,'baseline_only_optimizer_steps':0,'all_audit_train_arrays_unused':True,'reselection_retraining_or_tuning_performed':False,
         'native_full_qualification_claim':False,'elo_claim':None,'next_action':'Report this single fixed-candidate audit honestly. No alternative candidate selection/retraining from audit outcomes. Root owns separate native qualification and publication.'}
 dump(OUT/'CLOSED.json',result)
 print(json.dumps({'status':result['status'],'rows':result['rows'],'represented_games':result['represented_games'],'loss_mse':result['loss_mse']}),flush=True)
 return 0

if __name__=='__main__':
 try:raise SystemExit(main())
 except BaseException as failure:
  if isinstance(failure,SystemExit) and failure.code in (None,0):raise
  dump(OUT/'FAILED.json',{'status':'FIRST_AUDIT_ATTEMPT_FAILED_NO_AUTOMATIC_RETRY_OR_RESELECTION','error':repr(failure),'utc':datetime.now(timezone.utc).isoformat()})
  raise
