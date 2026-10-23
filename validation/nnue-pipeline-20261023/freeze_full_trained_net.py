"""Apply the committed full-network selection rule; never read independent-audit data."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys
import numpy as np
R=Path('/workspace/dwqww'); H=Path('/workspace/forge-nnue-handoff-20261023')
sys.path.insert(0,str(R/'tools/nnue'))
from include_parser import load_include
from residual_train import verify_unchanged_inputs
OUT=H/'full-trained-net-freeze-attempt1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def params(net):return np.concatenate([np.asarray(net[n]).reshape(-1) for n in ('w1','b1','w2','b2')])*4096
assert sha(R/'validation/nnue-pipeline-20261023/CANDIDATE-FREEZE-RULE.json')=='fcb36f64af8600ac92304d5f5aae3fbc1cd008e2f22ca9b33ed63f48caeee2ea'
controller=H/'full-training-controller-attempt2'
assert read(controller/'RESULT.json')['status']=='PASS_TWO_FULL_DATA_TRAINING_RUNS_CLOSED_NO_ELO_CLAIM'
gate=read(controller/'DATA-GATE.json');protocol=read(controller/'PROTOCOL.json')
assert gate['train']==1000000 and gate['validation']==4149
for name,expected in protocol['source_hashes'].items():assert sha(R/name)==expected,name
manifest=read(H/'prepared-all13m-reservoir-attempt1/manifest.json')
verify_unchanged_inputs(H/'prepared-all13m-reservoir-attempt1',manifest,gate['manifest_sha256'])
old=load_include(R/'src/nnue_weights.inc',expected_hidden=128);old_parameters=params(old)
candidates=[];configs=[];runs=[]
for order,label in enumerate(('zero','warm')):
 run=H/('full1m-'+label+'20-attempt1');s=read(run/'summary.json');config=s['config'];configs.append(config)
 assert s['status']=='completed' and s['input_integrity']=='passed' and s['epochs_completed']==20
 assert s['manifest_sha256']==gate['manifest_sha256'] and s['training_count']==1000000 and s['validation_count']==4149
 assert config['data_dir']==str(H/'prepared-all13m-reservoir-attempt1') and config['run_dir']==str(run)
 assert config['initial_net'] is None if label=='zero' else config['initial_net']['sha256']==old['sha256']
 assert len(s['epochs'])==20
 runs.append({'label':label,'summary_sha256':sha(run/'summary.json'),'initial_metrics':s['initial'],'best_including_initial':s['best']})
 for epoch,record in enumerate(s['epochs'],1):
  assert record['epoch']==epoch and record['count']==4149
  stem=f'epoch-{epoch:04d}';inc=run/'exports'/(stem+'.inc');meta=read(run/'exports'/(stem+'.json'))
  assert sha(inc)==meta['inc_sha256'] and sha(run/'exports'/(stem+'.bin'))==meta['bin_sha256']
  assert meta['manifest_sha256']==gate['manifest_sha256'] and meta['epoch']==epoch
  assert meta['metrics']['teacher_mse_combined']==record['teacher_mse_combined']
  net=load_include(inc,expected_hidden=128);assert net['residual'] is True
  delta=params(net)-old_parameters;changed=int(np.count_nonzero(delta))
  candidates.append({'label':label,'order':order,'epoch':epoch,'stem':stem,'run':str(run),'inc':str(inc),'inc_sha256':sha(inc),'bin_sha256':meta['bin_sha256'],'checkpoint_sha256':sha(run/'checkpoints'/(stem+'.pt')),'teacher_mse_combined':record['teacher_mse_combined'],'changed_quantized_parameters':changed,'parameter_count':len(delta),'maximum_absolute_quantized_parameter_delta':int(np.max(np.abs(delta))),'eligible':changed>0})
for k in configs[0]:
 if k not in ('run_dir','initial_net'):assert configs[0][k]==configs[1][k],k
eligible=[c for c in candidates if c['eligible']]
assert eligible,'No changed full-trained export; no pilot substitution.'
chosen=min(eligible,key=lambda c:(c['teacher_mse_combined'],c['order'],c['epoch']))
OUT.mkdir(exist_ok=False)
source_run=Path(chosen['run']);stem=chosen['stem']
for source,name in [(source_run/'exports'/(stem+'.inc'),'nnue_weights.inc'),(source_run/'exports'/(stem+'.bin'),'nnue_weights.bin'),(source_run/'exports'/(stem+'.json'),'original-export.json'),(source_run/'checkpoints'/(stem+'.pt'),'checkpoint.pt')]:shutil.copy2(source,OUT/name)
assert sha(OUT/'nnue_weights.inc')==chosen['inc_sha256'] and sha(OUT/'checkpoint.pt')==chosen['checkpoint_sha256']
result={'status':'FROZEN_CHANGED_FULL_TRAINED_NET_BEFORE_INDEPENDENT_AUDIT_MODEL_EVALUATION','utc':datetime.now(timezone.utc).isoformat(),'base_sha':'1ab50b2dd64d9b2f752f7f1285f6968cad2fd792','selection_rule_sha256':sha(R/'validation/nnue-pipeline-20261023/CANDIDATE-FREEZE-RULE.json'),'selector_sha256':sha(Path(__file__)),'manifest_sha256':gate['manifest_sha256'],'validation_rows':4149,'training_rows':1000000,'selection_metric':'Complete original4149 validation pure-teacher MSE; selected from40epochs, conditional not independent evidence','runs':runs,'chosen':chosen,'ranked_candidates':sorted(candidates,key=lambda c:(c['teacher_mse_combined'],c['order'],c['epoch'])),'independent_audit_model_loss_read':False,'default_weights_changed':False,'elo_claim':None}
(OUT/'FREEZE.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(result['chosen']))
