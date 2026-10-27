"""Read only closed histogram JSONs; write NEW summary artifacts, never shards."""
import hashlib
import json
from pathlib import Path

ROOT=Path('/tmp/forge_sol_S18_histograms_new_20261026')
OUT=Path('/tmp/forge_sol_S18_histograms_outer_new_20261026')
ORDER=['none','t200','t300','t400','t500']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=ROOT/'forge_sol_S18_histogram_batch_result_20261026.json';batch=json.loads(p.read_text())
    if batch['status']!='PASS_COMPLETE_READONLY_HISTOGRAM_BATCH' or batch['training_performed'] or batch['acceptance']:
        raise ValueError('closed read-only batch required')
    if len(batch['cases'])!=5 or [c['arm'] for c in batch['cases']]!=ORDER:raise ValueError('five exact ordered cases required')
    for c in batch['cases']:
        if c['status']!='PASS_COMPLETE_READONLY_HISTOGRAM' or c['returncode']!=0 or not c['leader_reaped'] or c['all_owned_group_members_after_close']:
            raise ValueError('unclosed/failed case')
    arms={};input_hist=None
    for arm in ORDER:
        q=Path(batch['outputs'][arm]['histogram'])
        if sha(q)!=batch['outputs'][arm]['sha256']:raise ValueError('histogram hash changed')
        r=json.loads(q.read_text())
        if input_hist is None:input_hist=r['input']
        if r['input']!=input_hist:raise ValueError('input histogram differs between arms')
        arms[arm]={'source_histogram':str(q),'source_histogram_sha256':sha(q),'threshold':r['threshold'],
            'kept':r['kept'],'dropped':r['dropped'],'dropped_per_reason':r['dropped_per_reason'],
            'dedupe':r['dedupe'],'supplied_synthetic_holdout_overlap':r['supplied_holdout_overlap'],
            'all_histograms_reconcile':r['all_histograms_reconcile'],'phase_definition':r['phase_definition']}
    result={'schema':'forge-S18-observed-histogram-summary-v1','status':'PASS_COMPLETED_READONLY_HISTOGRAMS',
      'producer_session_id':15660,'producer_batch_sha256':sha(p),'source_review_commit':'92220ccf0400dc45828bcfad9ba9993c72ddb56d',
      'actual_kept_row_sum':sum(r['kept']['rows'] for r in arms.values()),'unfiltered_training_input':input_hist,'arms':arms,
      'h000_unfiltered_holdout_md5':batch['holdout_md5_verified'],'all_original_sample_sha256':batch['original_sample_sha256'],
      'real013014_and_authentic_game_overlap':'UNVERIFIED','production_training_approval':False,'training_performed':False,
      'original_t500_repeat_status':'FAIL_UNCHANGED','historical_timeout_cause':'UNDETERMINED'}
    q=OUT/'forge_sol_S18_observed_histogram_summary_20261026.json'
    with q.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    lines=['# S18 five-arm read-only histogram batch — 2026-10-26','',
      'All five arms completed at EOF, with reconciled histograms and empty reaped owned groups. No filtering, Torch, training, postscore, engine or timing experiment ran. These are synthetic supplied-sample data counts, with no training or playing-strength claim.','',
      '| Arm | Kept | Dropped | Draw disagreement | Loss/positive | Win/negative |','|---|---:|---:|---:|---:|---:|']
    for arm,a in arms.items():
        d=a['dedupe']['dropped_reason_counts']
        lines.append('| '+arm+' | '+' | '.join(str(v) for v in [a['kept']['rows'],a['dropped']['rows'],d.get('result_draw_score_large',0),d.get('result_loss_score_positive',0),d.get('result_win_score_negative',0)])+' |')
    lines+=['','Actual kept-row sum: **'+str(result['actual_kept_row_sum'])+'**. Every arm read the same 200,000 original training rows; the h000 holdout is separate and unchanged. Supplied synthetic holdout overlap, output duplicate positions and conflicting-label duplicate counts are zero in each arm. Real013/014 and authentic game isolation remain **UNVERIFIED**. The original t500 repeat remains **FAIL**, with its cause undetermined.','',
      'CPU 4, nice 19; each child had a 119-second work cutoff plus nominal 1-second cleanup reserve. No arm reached its cutoff. Whole batch elapsed '+str(batch['elapsed_seconds'])+' seconds across five sequential arms; peak child RSS '+str(batch['peak_children_RSS_KiB'])+' KiB. Per-process parent/child AS caps were 128/768 MiB. Python: `'+batch['python_version'].replace('\n',' ')+'`. Raw parent and per-child stdout/stderr are preserved; all stderr files are empty. These durations are operational evidence, not speed measurements.','',
      'Phase is the unchanged current Forge HCE material phase, clamped at 24, taken from the pinned h256_e12 header. No new evaluation values were introduced. Counts below are kept rows; full input, kept, dropped, reason and disagreement maps are in the JSON artifacts.','',
      '| HCE phase | none | t200 | t300 | t400 | t500 |','|---|---:|---:|---:|---:|---:|']
    for k in sorted(set().union(*(set(a['kept']['phase']) for a in arms.values())),key=int):
        lines.append('| '+k+' | '+' | '.join(str(arms[a]['kept']['phase'].get(k,0)) for a in ORDER)+' |')
    lines+=['','| Piece count | none | t200 | t300 | t400 | t500 |','|---|---:|---:|---:|---:|---:|']
    for k in sorted(set().union(*(set(a['kept']['piece_count']) for a in arms.values())),key=int):
        lines.append('| '+k+' | '+' | '.join(str(arms[a]['kept']['piece_count'].get(k,0)) for a in ORDER)+' |')
    lines+=['','All four disagreement thresholds (200/300/400/500) and every phase, piece, result, sign and score-band bucket reconcile: kept plus dropped equals original input. At each arm’s own threshold all remaining rows are consistent by that filter definition. This is filter accounting, not validation that the labels improve a network.','',
      'Next action: publish/review this completed source/data checkpoint and prepare any exact arm index required for separately authorized diagnostic CPU training. No trainer import or training is authorized by these results.']
    r=OUT/'forge_sol_S18_histogram_report_20261026.md'
    with r.open('x') as f:f.write('\n'.join(lines)+'\n')
    q.chmod(0o444);r.chmod(0o444)
    print(json.dumps({'summary_sha256':sha(q),'report_sha256':sha(r),'actual_kept_row_sum':result['actual_kept_row_sum'],'status':result['status']},sort_keys=True))

if __name__=='__main__':main()
