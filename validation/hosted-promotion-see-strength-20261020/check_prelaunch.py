#!/usr/bin/env python3
"""Read-only static readiness checker. No engine/build/match/launch/Git mutation."""
import argparse,ast,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
import yaml
REPO=Path(__file__).resolve().parents[2];PACKAGE=REPO/'.github/hosted-promotion-see-strength'
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--require-ready',action='store_true');a=p.parse_args()
 cfg=json.loads((PACKAGE/'protocol.json').read_text());spec=importlib.util.spec_from_file_location('pin_gate',PACKAGE/'run_hosted.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.verify_package_inventory(REPO,PACKAGE)
 assert re.fullmatch('[0-9a-f]{40}',cfg['candidate_sha']) and cfg['candidate_sha']==m.CANDIDATE_SHA
 assert cfg['candidate_version']=='6.4.17' and cfg['baseline_version']=='6.4.14'
 assert cfg['seed']==20261025
 assert cfg['candidate_benchmark_nodes']==385781
 prior=cfg['prior_native_tsan_failure'];raw=(REPO/prior['original_summary_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==prior['original_summary_sha256'];prior_summary=json.loads(raw);assert prior_summary['status']=='FAILED' and prior_summary['source_commit']=='553caef144ae2e1b696ba35d7a0eb1a50a03fde9'
 decision=cfg['root_readiness_decision'];assert hashlib.sha256((REPO/decision['path']).read_bytes()).hexdigest()==decision['sha256']
 assert json.loads((REPO/decision['path']).read_text())['qualification']==cfg['operational_qualification_status']
 ready=cfg['status']=='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
 if ready:
  m.require_launch_protocol(cfg)
  for path,digest in cfg['correctness_evidence_sha256'].items():assert m.sha(REPO/path)==digest
 else:
  assert cfg['status']=='PENDING_REVIEW'
  try:m.require_launch_protocol(cfg)
  except ValueError:pass
  else:raise AssertionError('Pending gate bypassed')
 workflow=REPO/'.github/workflows/forge-hosted-promotion-see-strength.yml';w=yaml.load(workflow.read_text(),Loader=yaml.BaseLoader)
 assert w['on']=={'push':{'branches':['forge/hosted-promotion-see-strength-20261020-*']}}
 job=w['jobs']['promotion-see-strength'];
 for name in ('BASELINE','CANDIDATE','FASTCHESS'):assert job['env'][name+'_SHA']==cfg[name.lower()+'_sha']
 assert job['if']=='github.run_attempt == 1';assert job['timeout-minutes']=='240';assert job['steps'][1]['timeout-minutes']=='8';assert job['steps'][2]['timeout-minutes']=='210'
 for step in job['steps']:
  if 'run' in step:subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)
 for path in PACKAGE.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
 exclusions=json.loads((PACKAGE/'provenance/historical-exclusions.json').read_text());selection=json.loads((PACKAGE/'provenance/openings-selection.json').read_text());runtime=json.loads((PACKAGE/'provenance/runtime-order.json').read_text());allf=set()
 for phase,count in [('aa',4),('sprt',128)]:
  raw=(PACKAGE/'openings'/(phase+'.epd')).read_bytes();fens=raw.decode().splitlines();assert len(fens)==len(set(fens))==count;assert all(f.split()[3]=='-' for f in fens);assert not set(fens)&allf;allf|=set(fens);assert not set(fens)&set(exclusions['excluded_canonical_positions'])
  assert hashlib.sha256(raw).hexdigest()==selection['prospective_selection']['outputs'][phase]['sha256'];ordered=sorted(fens,key=lambda f:hashlib.sha256(('20261025\n'+f).encode()).digest());assert ordered==runtime[phase]['ordered_fens'];assert hashlib.sha256(('\n'.join(ordered)+'\n').encode()).hexdigest()==runtime[phase]['selected_epd_sha256']
 assert cfg['sprt_settings']=={'elo0':0,'elo1':10,'alpha':.05,'beta':.05,'pair_cap':128,'game_cap':256,'tc':'10+0.1','concurrency':1,'emergency_seconds':12000}
 source=json.loads((Path(__file__).parent/'source-inputs-SHA256.json').read_text())
 for name,row in source.items():
  for label,digest in row.items():
   raw=subprocess.check_output(['git','show',cfg[label+'_sha']+':'+name],cwd=REPO);assert hashlib.sha256(raw).hexdigest()==digest
 report={'status':'passed','launch_authorized':ready,'source_gate_status':cfg['source_gates_status'],'operational_qualification_status':cfg['operational_qualification_status'],'frozen_aa_pairs':4,'frozen_sprt_pair_cap':128,'workflow_budgets_minutes':[240,8,210],'source_inventory_files':len(source),'historical_sources':len(exclusions['historical_sources_sha256']),'engine_executions':0}
 if a.require_ready:assert ready,'Final root review/current source gates remain PENDING'
 a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
