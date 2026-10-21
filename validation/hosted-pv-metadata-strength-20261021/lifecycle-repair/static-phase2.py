"""Read-only disabled packet checks, no engine/compiler/match/collector execution."""
from pathlib import Path
import ast,copy,difflib,hashlib,importlib.util,json,yaml
R=Path('/workspace/dwqww');V=R/'validation/hosted-pv-metadata-strength-20261021';P=R/'.github/hosted-pv-metadata-strength';OLD=R/'.github/hosted-correction-history-strength';W=R/'.github/workflows/forge-hosted-pv-metadata-strength.yml'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
runner=load('pv_static_runner',P/'run_hosted.py');guard=load('pv_static_build_guard',P/'build_evidence.py');cfg=read(P/'protocol.json')
assert cfg['status']=='DRAFT_BLOCKED_PREPARATION_ONLY' and cfg['correctness_evidence_sha256']=={} and cfg['workflow_sha256'] is None
assert cfg['candidate_sha']==runner.CANDIDATE_SHA=='ff2e269c6058be84456e3b98344826d17b0056eb'
assert cfg['baseline_sha']=='2e151d019bc58dff2ab4e76e99ef99516af8d222'
assert cfg['candidate_bench_capture_status']=='PENDING_ACTUAL_FROZEN22_CAPTURE'
assert cfg['baseline_benchmark_nodes']==321912 and cfg['candidate_benchmark_nodes']==runner.CANDIDATE_BENCHMARK_NODES==292545
assert cfg['source_file_counts']==guard.SOURCE_COUNTS=={'baseline':76,'candidate':77}
assert len(guard.BASELINE_TESTS)==13 and len(guard.CANDIDATE_TESTS)==14 and guard.CANDIDATE_TESTS[5]=='forge_pv_metadata_tests'
assert cfg['sprt_settings']=={'elo0':0,'elo1':10,'alpha':.05,'beta':.05,'pair_cap':512,'game_cap':1024,'tc':'1+0.01','concurrency':1,'emergency_seconds':18000}
assert cfg['aa_settings']=={'pairs':4,'tc':'1+0.01','nodes':0,'identical_moves_required':False,'binary':'baseline'} and cfg['seed']==20261031
manifest=runner.verify_package_inventory(R,P);assert len(manifest)==24
workflow=yaml.load(W.read_text(),Loader=yaml.BaseLoader);assert workflow['on']==[]
job=workflow['jobs']['pv-metadata-strength'];assert job['if']=='${{ false }}' and job['timeout-minutes']=='360'
assert job['env']['BASELINE_SHA']==cfg['baseline_sha'] and job['env']['CANDIDATE_SHA']==cfg['candidate_sha']
assert job['steps'][1]['timeout-minutes']=='8' and job['steps'][2]['timeout-minutes']=='310'
assert "BUILD_WORK_SECONDS=450" in (P/'prepare_hosted.py').read_text()
for name in ('archive_results.py','match/run_match.py','match/pgn_stats.py'):assert (P/name).read_bytes()==(OLD/name).read_bytes()
for name,digest in read(V/'IMMUTABLE18-BEFORE.json').items():assert sha(R/name)==digest,name
for file in (V/'captures').iterdir():
 if file.is_file():assert file.read_bytes()==(R/'validation/hosted-correction-history-strength-20261020/captures'/file.name).read_bytes()
checks={}
for label,change in [('actual_draft',{}),('status_only',{'status':'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'})]:
 d=copy.deepcopy(cfg);d.update(change)
 try:runner.require_launch_protocol(d)
 except ValueError as error:checks[label]=str(error)
 else:raise AssertionError('Disabled actual packet accepted')
synthetic=copy.deepcopy(cfg);synthetic.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',source_gates_status='PASSED',source_scope_review_status='PASSED',root_review_status='PASSED',astra_review_status='PASSED',correctness_evidence_sha256={'SYNTHETIC_ONLY':'1'*64},workflow_status='FROZEN',workflow_sha256='2'*64,operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved')
try:runner.require_launch_protocol(synthetic)
except ValueError as error:checks['forced_status_without_actual22_capture']=str(error)
else:raise AssertionError('Missing frozen22 capture accepted')
synthetic['candidate_bench_capture_status']='PASSED_ACTUAL_FROZEN22_CANONICAL_CAPTURE';runner.require_launch_protocol(synthetic)
for key,value in [('aa_settings',{'pairs':4,'tc':'inf','nodes':10000,'identical_moves_required':True,'binary':'baseline'}),('source_file_counts',{'baseline':75,'candidate':76})]:
 d=copy.deepcopy(synthetic);d[key]=value
 try:runner.require_launch_protocol(d)
 except ValueError as error:checks[key]=str(error)
 else:raise AssertionError('Old protocol accepted')
opening=read(V/'opening-check.json');assert opening['status']=='passed' and opening['fresh_unique_positions']==516 and opening['independent_selected_source_games_legally_replayed']==516 and opening['full_corpus_replays_this_preparation']==0
assert opening['full_reserved_cohorts_excluded']['hosted-correction-history-strength']==260
for name in ('aa','sprt'):
 raw=(P/'openings'/f'{name}.epd').read_bytes();assert len(raw.splitlines())==(4 if name=='aa' else 512)
 for fen in raw.decode().splitlines():assert len(fen.split())==4 and fen.split()[3]=='-'
assert len(set((P/'openings/aa.epd').read_text().splitlines()+(P/'openings/sprt.epd').read_text().splitlines()))==516
assert len(read(R/cfg['candidate_source_manifest_path']))==77 and sha(R/cfg['candidate_source_manifest_path'])==cfg['candidate_source_manifest_sha256']
for p in P.rglob('*.py'):ast.parse(p.read_text())
files=sorted([p for p in P.rglob('*') if p.is_file()]+[W]);snapshot={p.relative_to(R).as_posix():{'sha256':sha(p),'mode':p.stat().st_mode&0o777} for p in files}
changes=[]
for name in ('run_hosted.py','prepare_hosted.py','build_evidence.py'):
 changes.extend(difflib.unified_diff((OLD/name).read_text().splitlines(True),(P/name).read_text().splitlines(True),fromfile='qualified18/'+name,tofile='disabled22/'+name))
(V/'lifecycle-repair/CODE-ADAPTATION-PHASE2.diff').write_text(''.join(changes))
assert all(sha(R/name)==row['sha256'] and (R/name).stat().st_mode&0o777==row['mode'] for name,row in snapshot.items())
result={'status':'PASS_DISABLED_SOURCE22_PREPARATION_ONLY_NOT_LAUNCH_READY','package_entries':24,'baseline':cfg['baseline_sha'],'candidate':cfg['candidate_sha'],'candidate_actual_qualification':'PENDING','candidate_bench_capture':'PENDING actual22;292545 only prototype signature','named_ctests':{'baseline':13,'candidate':14,'pv_test_ordinal':6},'source_files':cfg['source_file_counts'],'statistical_design':cfg['sprt_settings'],'aa_design':cfg['aa_settings'],'metadata_refusals':checks,'opening_positions':516,'active18_reserved_cohort_excluded':260,'matched_historical18_fixture_bytes':True,'qualified18_packet_workflow_unchanged':True,'snapshot':snapshot,'engine_build_match_hosted_git_actions':0}
(V/'lifecycle-repair/STATIC-PHASE2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='snapshot'}))
