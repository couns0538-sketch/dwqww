"""Authenticate completed audit artifacts without model inference or new resampling."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math

H=Path('/workspace/forge-nnue-handoff-20261023');O=Path(__file__).resolve().parent

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(path):return json.loads(path.read_text())
protocol=read(O/'PROTOCOL.json');closed=read(O/'CLOSED.json');report=H/'independent-audit-frozen-zeroep3-report-attempt1';metrics=read(report/'metrics.json')
assert closed['status']=='PASS_ONCE_ONLY_FROZEN_CANDIDATE_INDEPENDENT_AUDIT_EXECUTION_NOT_ELO'
assert closed['baseline_result']['returncode']==closed['comparison_result']['returncode']==0
assert closed['baseline_result']['owned_process_reaped'] and closed['comparison_result']['owned_process_reaped']
assert not any((O/name).read_bytes() for name in ['baseline.stderr.txt','comparison.stderr.txt','controller.stderr.txt'])
assert sha(O/'PROTOCOL.json')==closed['protocol_sha256']=='942677f2268db47c922292cdf29fc90a722a999d26b68f2e842bcb9ce7f92ab0'
assert sha(report/'metrics.json')==closed['metrics_sha256'] and sha(report/'REPORT.md')==closed['report_sha256']
assert sha(report/'per-row-losses.npz')==metrics['per_row_artifact']['sha256']=='4a66e20daeaa54a0acd61326e77a61fa62ede752227efd489d3649323033ab7c'
assert metrics['rows']==8881 and metrics['represented_games']==109 and metrics['listed_validation_games']==111
assert metrics['reference_holdout_check']['status']=='PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE'
assert metrics['reference_holdout_check']['reference_run']==str(H/'independent-audit-shipped-baseline-attempt1')
for identity in read(O/'BOUND-INPUTS-BEFORE.json')['files']:assert sha(identity['path'])==identity['sha256'],identity['path']
for key in ['hce_vs_shipped','hce_vs_candidate','shipped_vs_candidate']:
 c=metrics['comparisons'][key]
 assert math.isfinite(c['improvement_abs']) and len(c['ci95_abs'])==2 and c['ci95_abs'][0]<=c['ci95_abs'][1]
loss=metrics['loss_mse'];hc=metrics['comparisons']['hce_vs_candidate'];sc=metrics['comparisons']['shipped_vs_candidate']
assert abs(sc['improvement_abs']-(loss['shipped_hce_plus_net']-loss['candidate_hce_plus_net']))<1e-15
assert abs(hc['improvement_abs']-(loss['hce_only']-loss['candidate_hce_plus_net']))<1e-15
result={'status':'PASS_ACTUAL_ONCE_ONLY_INDEPENDENT_AUDIT_TOOL_CLOSED_NO_ELO','utc':datetime.now(timezone.utc).isoformat(),
 'actual_audit_tool_session_id':45840,'actual_audit_tool_exit_code':0,'baseline_child_returncode':0,'comparison_child_returncode':0,'all_owned_processes_reaped':True,
 'controller_path':str(O),'protocol_sha256':sha(O/'PROTOCOL.json'),'controller_closure_sha256':sha(O/'CLOSED.json'),
 'public_selection_commit':protocol['public_selection_commit'],'public_net_only_source_commit':protocol['public_net_only_source_commit'],'public_proof':protocol['public_proof'],
 'frozen_candidate':protocol['frozen_candidate'],'frozen_selection':protocol['frozen_selection'],'masked_audit_manifest':protocol['masked_data_manifest'],
 'baseline_path':str(H/'independent-audit-shipped-baseline-attempt1'),'original_report_path':str(report/'REPORT.md'),'metrics_path':str(report/'metrics.json'),
 'metrics_sha256':sha(report/'metrics.json'),'per_row_loss_artifact_sha256':sha(report/'per-row-losses.npz'),
 'rows':8881,'represented_game_clusters':109,'assigned_validation_game_ids':111,'unused_train_rows':1321,'all_train_arrays_unused':True,
 'loss_mse':loss,'candidate_vs_hce':hc,'candidate_vs_shipped':sc,
 'teacher_loss_conclusion':'Candidate improves HCE on this independent audit, but does not demonstrate improvement over the shipped residual network: candidate point MSE is higher and the paired whole-game CI includes zero.',
 'no_reselection_retraining_tuning_or_other_candidate_evaluation':True,'no_full_native_qualification_claim':True,'elo_claim':None,
 'baseline_only_optimizer_steps':0,'original_inputs_source_networks_freeze_publicproof_and_data_unchanged':True,
 'next_action':'Preserve and report the fixed result. Keep shipped accepted default unchanged unless separate qualification/strength evidence supports a future change; do not select/retrain another model using this audit.'}
path=H/'INDEPENDENT-AUDIT-EVALUATION-TOOL-CLOSED.json'
with path.open('x') as stream:stream.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
(O/'INTERPRETATION.md').write_text(f'''# Once-only independent audit of the publicly frozen network

The fixed candidate was publicly frozen as zero-initialized full-data epoch3 before any independent-audit model losses. Selection used only the original4,149-position set; this separate8,881-position audit was never used for training or candidate selection. Both the new shipped-only baseline and the one fixed-candidate comparison actually exited0; the controller tool45840 exited0. All original source, network, freeze/public-proof and data hashes remained unchanged.

| Evaluator | Pure teacher probability MSE |
| --- | ---: |
| HCE | {loss['hce_only']:.12f} |
| Shipped HCE + residual | {loss['shipped_hce_plus_net']:.12f} |
| Frozen candidate HCE + residual | {loss['candidate_hce_plus_net']:.12f} |

Candidate versus HCE: {100*hc['improvement_relative']:.3f}% lower loss,95% whole-game interval[{100*hc['ci95_relative'][0]:.3f}%,{100*hc['ci95_relative'][1]:.3f}%]. Candidate versus shipped: improvement {100*sc['improvement_relative']:.3f}% (negative means worse),95% interval[{100*sc['ci95_relative'][0]:.3f}%,{100*sc['ci95_relative'][1]:.3f}%]. The candidate point is slightly worse than shipped and the interval includes zero: no teacher-loss improvement over the accepted network is demonstrated.

The2,000 paired whole-game bootstrap draws use seed20261023 and ratio(sum loss/sum rows). There are109 represented game clusters,111 assigned validation IDs and1,321 UNUSED train rows. Residual-term-only scores in the original report are diagnostic; the engine uses HCE plus residual. The original generic report cautions against selection on the same holdout; the attached freeze/publication protocol establishes that this audit was separate from selection.

These are teacher-loss results. They do not establish Elo or complete native-runtime qualification. No reselection, retraining, tuning, alternate candidate or audit retry occurred. Root owns separate native qualification, publication and any future equal-time strength test.
''')
print(json.dumps({'status':result['status'],'teacher_loss_conclusion':result['teacher_loss_conclusion'],'receipt_path':str(path),'receipt_sha256':sha(path),'candidate_relative_hce_improvement':hc['improvement_relative'],'candidate_relative_shipped_improvement':sc['improvement_relative']},indent=2))
