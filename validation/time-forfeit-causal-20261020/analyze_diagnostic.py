#!/usr/bin/env python3
"""Offline phase summaries for the single retained causal diagnostic, no engine execution."""
from pathlib import Path
import argparse, collections, json

def phase(a,b):
 row={'wall_ms':(b['wall_ns']-a['wall_ns'])/1e6}
 if a['pid']==b['pid']:
  row['process_cpu_ms']=(b['process_cpu_ns']-a['process_cpu_ns'])/1e6
  if a['tid']==b['tid']:
   row['thread_cpu_ms']=(b['thread_cpu_ns']-a['thread_cpu_ns'])/1e6
   row['wall_minus_thread_cpu_ms']=row['wall_ms']-row['thread_cpu_ms']
 return row

def analyze(directory):
 case=json.loads((directory/'case.json').read_text())
 events=[json.loads(l) for l in (directory/'engine-events.jsonl').read_text().splitlines()]
 rows=[]
 for search in case.get('searches',[]):
  seq=search['search'];own=[e for e in events if e['search']==seq]
  tags=collections.defaultdict(list)
  for e in own:tags[e['event']].append(e)
  one=lambda tag: tags[tag][0]
  go=search['manager_go_prewrite'];seen=search['manager_observed_bestmove']['observed']
  origin=one('worker_origin')['origin_ns'];budget=one('budget_ready')
  item={'search':seq,'requested_fen':search['position_fen'],'go_original':search['go_original'],'bestmove':search['bestmove'],'original_expected_bestmove':search['original_expected_bestmove'],'differs_from_original':search['differs_from_original'],'go_to_engine_receipt_ms':(one('go_receipt')['origin_ns']-go['wall_ns'])/1e6,'go_to_observed_bestmove_ms':(seen['wall_ns']-go['wall_ns'])/1e6,'receipt_to_dispatch_ms':(one('worker_dispatch_begin')['wall_ns']-one('go_receipt')['origin_ns'])/1e6,'resolved_request_origin_ns':origin,'hard_budget_ms':budget['budget_ms'],'soft_budget_ms':budget['detail'],'reported_result_elapsed_ms':one('worker_result')['detail'],'engine_result_nodes':one('worker_result')['nodes'],'event_counts':{k:len(v) for k,v in tags.items()}}
  pairs=[('dispatch_to_facade','worker_dispatch_begin','facade_enter'),('facade_to_worker_begin','facade_enter','worker_search_begin'),('worker_begin_to_result','worker_search_begin','worker_result'),('result_to_uci_return','worker_result','uci_search_return'),('uci_return_to_bestmove_lock','uci_search_return','bestmove_pre_lock'),('bestmove_lock_wait','bestmove_pre_lock','bestmove_pre_output'),('bestmove_output_flush','bestmove_pre_output','bestmove_post_flush')]
  item['phases']={name:phase(one(a),one(b)) for name,a,b in pairs}
  item['bestmove_pre_output_to_manager_observed_ms']=(seen['wall_ns']-one('bestmove_pre_output')['wall_ns'])/1e6
  item['bestmove_post_flush_to_manager_observed_signed_ms']=(seen['wall_ns']-one('bestmove_post_flush')['wall_ns'])/1e6
  item['info_phases']=[]
  for a,b,c,d in zip(tags['info_pre_lock'],tags['info_pre_output'],tags['info_pre_flush'],tags['info_post_flush']):
   assert len({x['budget_ms'] for x in [a,b,c,d]})==1
   assert len({x['detail'] for x in [a,b,c,d]})==1
   item['info_phases'].append({'depth':a['budget_ms'],'reported_elapsed_ms':a['detail'],'sampled_pre_lock_elapsed_ms':(a['wall_ns']-origin)/1e6,'lock_wait':phase(a,b),'format_before_flush':phase(b,c),'flush':phase(c,d)})
  item['timer_polls']=[{'event':e['event'],'nodes':e['nodes'],'observed_elapsed_ms':(e['wall_ns']-e['origin_ns'])/1e6,'hard_ms':e['budget_ms'],'reason_code':e['detail']} for e in own if e['event'] in ['timer_poll_begin','timer_poll_end']]
  own_ids={e['id'] for e in own}
  previous=[e for e in own if e['previous_event_id'] in own_ids]
  item['recorded_prior_event_cost_ms']={'wall_ms':sum(e['previous_write_wall_ns'] for e in previous)/1e6,'thread_cpu_ms':sum(e['previous_write_thread_cpu_ns'] for e in previous)/1e6,'scope':'Prior complete event formatting+append costs; not syscall-only and excludes each thread final event cost.'}
  rows.append(item)
 return {'case':case['case'],'capture_status':case['status'],'searches':rows,'last_search':rows[-1] if rows else None,'scope':'Local diagnostic only. Forced historical positions/time values and instrumented searches are not games or identical original internal state. Wall-minus-CPU cannot uniquely identify scheduling; failure to reproduce does not explain original hosted forfeit.'}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 summary=json.loads((a.out/'summary.json').read_text());assert summary['status']=='COMPLETE_CAUSAL_DIAGNOSTIC_NO_STRENGTH_CLAIM' and summary['inputs_unchanged']
 result={'status':'OFFLINE_PHASE_ANALYSIS_COMPLETED','case_order':['cold','warm'],'cases':[analyze(a.out/c) for c in ['cold','warm']],'interpretation_limits':['New local phases can locate a newly observed stall; they cannot assign the original hosted stall without corresponding original phase telemetry.','Receive after stdout flush can have a negative signed interval because sampling is sequential around a real concurrent pipe read; retain signed value.','CPU deltas are emitted only across the same process, and thread CPU only across the same pid/tid.','No games, Elo, throughput, native-Windows or clock-reliability claim.']}
 (a.out/'phase-analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'status':result['status'],'cases':[{'case':x['case'],'search_count':len(x['searches']),'last_go_to_bestmove_ms':x['last_search']['go_to_observed_bestmove_ms']} for x in result['cases']]}))
if __name__=='__main__':main()
