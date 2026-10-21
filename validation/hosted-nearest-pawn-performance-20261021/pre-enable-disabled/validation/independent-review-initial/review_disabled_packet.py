#!/usr/bin/env python3
"""Read-only review of first disabled21 packet; never import or run reviewed code."""
import ast,datetime,hashlib,json,re,stat
from pathlib import Path,PurePosixPath
ROOT=Path('/workspace/dwqww')
PKG=ROOT/'.github/hosted-nearest-pawn-performance'
EVID=ROOT/'validation/hosted-nearest-pawn-performance-20261021'
OUT=EVID/'independent-review-initial'
WF=ROOT/'.github/workflows/forge-hosted-nearest-pawn-performance.yml'
BASE='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
CAND='2e151d019bc58dff2ab4e76e99ef99516af8d222'
FLAGS='-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto'
PROOFS=(
 'validation/pawn-span-fill-20261020/root-verification/NATIVE.json',
 'validation/pawn-span-fill-20261020/root-verification/WINDOWS.json',
 'validation/nearest-pawn-distance-20261020/root-verification/NATIVE.json',
 'validation/nearest-pawn-distance-20261020/root-verification/WINDOWS.json',
 'validation/nearest-pawn-native-20261020/ROOT-FROZEN-SOURCE-GATES.json',
 'validation/nearest-pawn-native-20261020/FINAL-RECEIPT.json',
 'validation/nearest-pawn-native-20261020/release-parity-wrapper-attempt1/summary.json',
 'validation/nearest-pawn-distance-20261020/independent-review/SOURCE-REVIEW.json',
 'validation/nearest-pawn-distance-20261020/public-diff/PROBE-RECEIPT.json',
 'validation/nearest-pawn-distance-20261020/public-diff/public-diff-attempt1/RESULT.json',
 'validation/hosted-nearest-pawn-performance-20261021/ROOT-PREPARATION-REVIEW.json',
 'validation/hosted-nearest-pawn-performance-20261021/ROOT-ONE-ATTEMPT-AUTHORIZATION.json',
 'validation/hosted-nearest-pawn-performance-20261021/independent-review/REVIEW.json')
BASE_TESTS=('forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression')
checks=[];observed={}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):
 assert p.is_file() and not p.is_symlink()
 return {'sha256':sha(p),'size':p.stat().st_size,'mode':stat.S_IMODE(p.stat().st_mode)}
def check(name,condition,detail=None):
 row={'name':name,'passed':bool(condition)}
 if detail is not None:row['detail']=detail
 checks.append(row)
def j(p):return json.loads(p.read_bytes())
def read_manifest(path,root):
 rows={}
 for line in path.read_text().splitlines():
  digest,name=line.split('  ',1);part=PurePosixPath(name)
  assert re.fullmatch('[0-9a-f]{64}',digest) and not part.is_absolute() and '..' not in part.parts and name not in rows
  target=root/name
  assert target.resolve().is_relative_to(root.resolve())
  check('Manifest file identity:'+name,sha(target)==digest)
  rows[name]=digest
 return rows

def assignment(tree,name):
 for node in ast.walk(tree):
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):return node.value
 raise ValueError('Missing assignment '+name)
def value(node,env):
 if isinstance(node,ast.Name):return env[node.id]
 if isinstance(node,ast.Dict):return {value(k,env):value(v,env) for k,v in zip(node.keys,node.values)}
 if isinstance(node,(ast.List,ast.Tuple)):return [value(x,env) for x in node.elts]
 return ast.literal_eval(node)
started=now()
package_manifest=PKG/'PACKAGE-SHA256SUMS'
check('Stable preparer protocol SHA',sha(PKG/'protocol.json')=='c122d2f437edb995aac75b0d0c08edee50f1b0aa0fa83395ebd6f5d14cad7da3')
check('Stable preparer workflow SHA',sha(WF)=='addd14b49a3322ac7399af577c19b002fbb2fd51d25d8579da79f33d56b3f449')
check('Stable preparer package inventory SHA',sha(package_manifest)=='e93211bd7d90f6999afc44f62082d1a11c2129437bacd1f1bca83fceac6bf0b7')
package_rows=read_manifest(package_manifest,ROOT)
actual=sorted([str(f.relative_to(ROOT)) for f in PKG.rglob('*') if f.is_file() and f!=package_manifest]+[str(WF.relative_to(ROOT))])
check('Complete exact package inventory21entries',list(package_rows)==actual and len(actual)==21)
check('No bytecode or symlink package entries',not any(f.is_symlink() or '__pycache__' in f.parts or f.suffix=='.pyc' for f in PKG.rglob('*')))
frozen_paths=[ROOT/n for n in package_rows]+[package_manifest]
for f in frozen_paths:observed[str(f.relative_to(ROOT))]=identity(f)
evidence_manifest=EVID/'EVIDENCE-SHA256SUMS'
check('Preparer closed evidence seal SHA',sha(evidence_manifest)=='a2ab339dac0318199439555950afd6a67a0dc8932d78e2c36de61fccc6d40ec3')
evidence_rows=read_manifest(evidence_manifest,EVID)
check('Preparer finite evidence inventory46entries',len(evidence_rows)==46)
frozen_paths += [EVID/n for n in evidence_rows]+[evidence_manifest,EVID/'PREPARATION-CHECKPOINT.json']
for f in frozen_paths:observed[str(f.relative_to(ROOT))]=identity(f)
old20=j(EVID/'IMMUTABLE20-BEFORE.json')
for name,digest in old20.items():check('Qualified20 predecessor unchanged:'+name,sha(ROOT/name)==digest)
check('Old20 baseline package identity independently preserved',len(old20)==22)
for f in sorted(PKG.glob('*.py')):ast.parse(f.read_bytes(),filename=str(f));check('Package AST parse:'+f.name,True)
cfg=j(PKG/'protocol.json');common=ast.parse((PKG/'common.py').read_text());guard=ast.parse((PKG/'build_evidence.py').read_text());prepare=ast.parse((PKG/'prepare_hosted.py').read_text())
check('Frozen distinct40hex source pins',cfg['baseline_sha']==BASE and cfg['candidate_sha']==CAND and BASE!=CAND and re.fullmatch('[0-9a-f]{40}',CAND))
check('Blocked initial status and all zero launches/proofs/captures',cfg['status']=='DRAFT_BLOCKED_PREPARATION_ONLY' and cfg['workflow_status']=='DISABLED' and cfg['correctness_evidence_sha256']==cfg['transport_captures']=={} and cfg['launches_during_preparation']==0)
check('All six qualification states remain blocked',all(cfg[k].startswith('BLOCKED') for k in ['source_gates_status','parity_review_status','capture_review_status','root_review_status','independent_review_status','operational_qualification_status']))
check('Exact complete13 finite proof paths',cfg['mandatory_finite_proof_paths']==list(PROOFS) and ast.literal_eval(assignment(common,'REQUIRED_PROOFS'))==PROOFS)
check('Compiler flags and source file counts75/76',cfg['compiler']=='g++-14' and cfg['release_flags']==FLAGS and cfg['source_file_counts']=={'baseline':75,'candidate':76} and ast.literal_eval(assignment(guard,'SOURCE_FILE_COUNTS'))==cfg['source_file_counts'])
check('Exact baseline12 namedCTest list',ast.literal_eval(assignment(guard,'BASELINE_TESTS'))==BASE_TESTS)
expected_candidate=ast.parse("(*BASELINE_TESTS[:4],'forge_nearest_pawn_tests',*BASELINE_TESTS[4:])",mode='eval').body
check('Candidate13 adds nearest exactly fifth',ast.dump(assignment(guard,'CANDIDATE_TESTS'))==ast.dump(expected_candidate))
text=(PKG/'build_evidence.py').read_text()
check('Actual source count checked before provenance acceptance',text.index('if len(inventory)!=SOURCE_FILE_COUNTS[label]')<text.index("provenance.get('source_commit')"))
check('Source PAX commit/export process/full namedCTest/LastTest all guarded',all(s in text for s in ["archive.pax_headers.get('comment')!=commit","['git','archive',cfg[label+'_sha']]","provenance.get('exported_source_sha256')!=inventory","enumerate(names,1)","last.count('Test Passed.')!=len(names)"]))
check('Release GCC14 generic nonLTO and every production source compiled guarded',all(s in text for s in ["cache.get('CMAKE_BUILD_TYPE')!='Release'","CMAKE_INTERPROCEDURAL_OPTIMIZATION","'.gnu.lto_' in sections","observed!=production","'-ffast-math'","'-funsafe-math-optimizations'","t.startswith('-flto')"]))
check('Runtime executable/core and complete observed process provenance guarded',all(s in text for s in ["set(artifacts)!=set(runtime)","os.access(path,os.X_OK)","owned_group_empty_before_verdict","owned_group_empty_after_cleanup","record['exit_code']!=0"]))
common_values={name:ast.literal_eval(assignment(common,name)) for name in ['READY','BASELINE','CANDIDATE','FLAGS']}
fixed=value(assignment(common,'fixed'),common_values)
check('READY requires exact source pins/counts/compiler/oneattempt/noretry',all(fixed[k]==v for k,v in {'baseline_sha':BASE,'candidate_sha':CAND,'compiler':'g++-14','source_file_counts':{'baseline':75,'candidate':76},'attempts':1,'fault_retries':0}.items()))
check('READY requires all final qualification flags incl root/independent',all(fixed[k]=='PASSED' for k in ['source_gates_status','parity_review_status','capture_review_status','root_review_status','independent_review_status']) and fixed['workflow_status']=='FROZEN')
check('Oneattempt15AA31AB188process940bench bounds consistent',cfg['attempts']==1 and cfg['fault_retries']==0 and (cfg['aa_blocks'],cfg['ab_blocks'])==(15,31) and 4+4*(15+31)==cfg['bounds']['planned_fresh_processes']==188 and 188*5==cfg['bounds']['planned_bench_commands']==940)
check('Canonical fivebench321912/depth11 and bootstrapseed20261029 frozen',all(cfg[k]==fixed[k]==v for k,v in {'bench_depth':11,'expected_nodes':321912,'benches_per_process':5,'bootstrap_seed':20261029,'bootstrap_draws':10000}.items()))
check('Future measurement bounded inside workflow',cfg['timing_work_seconds']==3600 and cfg['build_work_seconds']==690 and cfg['bounds']['timing_step_minutes']==65 and cfg['bounds']['build_step_minutes']==12 and cfg['bounds']['job_minutes']==90)
workflow=WF.read_text()
check('Workflow explicitly disabled with no push/dispatch trigger',bool(re.search(r'^on: \[\]$',workflow,re.M)) and bool(re.search(r'^    if: false$',workflow,re.M)) and not re.search(r'^\s*(push|workflow_dispatch|schedule):',workflow,re.M))
check('Workflow actual SHA matches blocked protocol',sha(WF)==cfg['workflow_sha256'])
check('Workflow source pins and first attempt frozen',BASE in workflow and CAND in workflow and "GITHUB_RUN_ATTEMPT')!='1'" in (PKG/'prepare_hosted.py').read_text())
check('Pinned action references only',all(re.fullmatch('[0-9a-f]{40}',s) for s in re.findall(r'uses: \S+@([^\s]+)',workflow)))
check('Future failure preservation/upload/freshresults includes original logs',workflow.count('if: always()')==3 and "upload-artifact@" in workflow and 'git switch --orphan' in workflow and 'git ls-remote origin' in workflow and 'collector-exit-code.txt' in workflow)
main=next(n for n in prepare.body if isinstance(n,ast.FunctionDef) and n.name=='main')
calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(main) if isinstance(n,ast.Call)]
line=lambda name:min(n for n,f in calls if f==name)
check('Collector READY/inventory/hashproof checks precede any stage',line('common.require_ready')<=line('common.inventory')<line('common.proof_paths')<line('stage'))
check('Actual 20/21 capture labels/source/binary/streams/process facts all checked before timing','Actual capture label/source/binary/process provenance differs' in (PKG/'common.py').read_text() and 'Original transport process was not normal' in (PKG/'common.py').read_text())
status=j(EVID/'OFFLINE-STATUS.json');run=status['actual_final_suite']
check('Original saved43offline suite rc0; not rerun by reviewer',run['tests']==43 and run['exit_code']==0 and len(re.findall(r'^test_.* \.\.\. ok$',(EVID/'offline-attempt1.stderr').read_text(),re.M))==43 and 'Ran 43 tests in 5.731s' in (EVID/'offline-attempt1.stderr').read_text() and (EVID/'offline-attempt1.stderr').read_text().rstrip().endswith('OK'))
for stream in ['stdout','stderr']:check('Original offline '+stream+' hash matches savedstatus',sha(EVID/('offline-attempt1.'+stream))==run[stream+'_sha256'])
old_inventory=EVID/'PACKAGE-SHA256SUMS.offline-attempt1'
check('Execution-time inventory itself hashbound',sha(old_inventory)==run['package_manifest_at_execution_sha256'])
oldrows={line.split('  ',1)[1]:line.split('  ',1)[0] for line in old_inventory.read_text().splitlines()}
changed=[n for n in package_rows if package_rows[n]!=oldrows.get(n)]
check('Only README changed after full43suite; executedcode exactly unchanged',set(oldrows)==set(package_rows) and changed==['.github/hosted-nearest-pawn-performance/README.md'])
control=status['source_count_control']
for name,prefix in [('red_attempt2','source-count-red-attempt2'),('green','source-count-green')]:
 row=control[name]
 for stream in ['stdout','stderr']:check('Source-count '+name+' original '+stream+' hash',sha(EVID/(prefix+'.'+stream))==row[stream+'_sha256'])
check('Valid source-count RED1 ValueError-not-raised and GREEN1 retained',control['red_attempt2']['exit_code']==1 and 'AssertionError: ValueError not raised' in (EVID/'source-count-red-attempt2.stderr').read_text() and control['green']['exit_code']==0 and 'Ran 1 test' in (EVID/'source-count-green.stderr').read_text() and (EVID/'source-count-green.stderr').read_text().rstrip().endswith('OK'))
check('Exact beforeguard/test bytes of REDexecution preserved',sha(EVID/'build_evidence.before-source-count.py')==control['red_attempt2']['executed_guard_sha256'] and sha(EVID/'source-count-red.executed-test.py')==control['red_attempt2']['executed_test_sha256'])
check('Initial pre-control failed lookup retained and disqualified',status['initial_preparation_error']['status']=='Retained; not a valid RED control' and sha(EVID/'source-count-red.stderr')==status['initial_preparation_error']['stderr_sha256'])
check('Derived testfixtures clearly marked neveractual21',all(x in (EVID/'test_build_evidence.py').read_text() for x in ['DERIVED UNIT','never actual21','INERT UNIT ARTIFACT NOT A PROGRAM','extra_source_file_rejected_despite_consistent_provenance']))
static=j(EVID/'PREPARER-STATIC-CHECKS.json')
check('Preparer actual blocked and finite-prooffailclose evidence preserved',static['actual_proofs']==static['actual_capture_entries']==0 and static['workflow_disabled'] and len([n for n in static['refusals'] if n.startswith('missing:')])==13)
for name,expected in observed.items():check('Final selected file bytes/mode unchanged:'+name,identity(ROOT/name)==expected)
failed=[c for c in checks if not c['passed']]
result={'status':'PASS_INITIAL_DISABLED_21_PACKET_STATIC_REVIEW_NOT_LAUNCH_AUTHORIZATION' if not failed else 'FAILED_INITIAL_DISABLED_21_PACKET_REVIEW','reviewer':'/root/archive_clock_complete','started_utc':started,'completed_utc':now(),'script_sha256':sha(Path(__file__)),'check_count':len(checks),'failed_check_count':len(failed),'findings':failed,'checks':checks,'baseline_sha':BASE,'candidate_sha':CAND,'selected_file_identities_unchanged_before_after':observed,'source_counts':{'baseline':75,'candidate':76},'named_ctests':{'baseline':12,'candidate':13,'nearest_test_candidate_ordinal':5},'observed_offline_test_count':43,'offline_tests_rerun_by_this_reviewer':False,'launch_ready':False,'runtime_inputs_and_final_metadata_require_new_review':True,'qualifications':['Read-only stdlib AST/hash/regex review. No reviewed module or test imported/executed. No engine/compiler/Git/network/timing execution.','This initial disabled snapshot has empty correctness-proof and capture maps. It is neither genuine source/native/Windows qualification nor final enabled workflow review.','Saved43offline tests and RED/GREEN runs were performed by preparer; reviewer authenticated originals and unchanged execution inputs without repeating them.','13 current proof paths, genuine20/21 captures including full executed461a helper provenance, root one-attempt authorization and final source-bound reviews must be independently reviewed before enabling.','Later capture-support files and descriptive additions outside the exact selected seal are outside this initial review.','Referenced native-experiment-integrity frozen-files skill resource was unavailable through provider; no optional troubleshooting repeated.']}
with (OUT/'STATIC-REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'failed':len(failed),'findings':failed},indent=2))
raise SystemExit(1 if failed else 0)
