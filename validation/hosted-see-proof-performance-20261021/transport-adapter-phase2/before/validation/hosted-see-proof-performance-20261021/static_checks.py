"""Source/data-only packet checks; no reviewed imports, processes or launches."""
import ast,hashlib,json
from pathlib import Path
R=Path('/workspace/dwqww');V=R/'validation/hosted-see-proof-performance-20261021';P=R/'.github/hosted-see-proof-performance';OLD=R/'.github/hosted-nearest-pawn-performance'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
checks=[]
def check(name,condition):
 assert condition,name
 checks.append(name)
def assignments(p):
 result={}
 for n in ast.parse(p.read_text()).body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:result[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 return result
cfg=read(P/'protocol.json');common=assignments(P/'common.py');analysis=assignments(P/'analysis.py');build=assignments(P/'build_evidence.py');wf=R/common['WORKFLOW'];w=wf.read_text()
check('workflow stays DISABLED no events, false job and no dispatch','on: []\n' in w and '    if: ${{ false }}\n' in w and '\n  push:' not in w and 'workflow_dispatch' not in w)
check('source identity exact23 and24',cfg['baseline_sha']==common['BASELINE']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984' and cfg['candidate_sha']==common['CANDIDATE']=='7db08eac6ead99d641834c56ccec06a06600586a')
check('all signature fields remain genuinely unknown',common['EXPECTED_NODES'] is None and analysis['EXPECTED_NODES'] is None and cfg['expected_nodes'] is None and cfg['candidate_first_native_signature_nodes'] is None)
check('no actual future proof/capture/workflow binding fabricated',cfg['correctness_evidence_sha256']=={} and cfg['transport_captures']=={} and cfg['workflow_sha256'] is None and cfg['workflow_status']=='DISABLED' and cfg['launches_during_preparation']==0)
check('all current production readiness gates pending',all(cfg[k].startswith('PENDING') for k in ['source_gates_status','parity_review_status','capture_review_status','root_review_status','independent_review_status']))
check('exact77 source maps and14 named suite order',cfg['source_file_counts']==build['SOURCE_FILE_COUNTS']=={'baseline':77,'candidate':77} and len(build['BASELINE_TESTS'])==14 and build['BASELINE_TESTS'][4:6]==('forge_nearest_pawn_tests','forge_pv_metadata_tests'))
check('required finite proof paths13 exact/no duplicates/no hash cycles',len(common['REQUIRED_PROOFS'])==13 and len(set(common['REQUIRED_PROOFS']))==13 and cfg['mandatory_finite_proof_paths']==list(common['REQUIRED_PROOFS']) and all(not Path(p).is_absolute() and '..' not in Path(p).parts and not p.startswith('.github/hosted-see-proof-performance/') for p in common['REQUIRED_PROOFS']))
check('calibrated complete counts/bounds unchanged',all(cfg[k]==v for k,v in {'aa_blocks':15,'ab_blocks':31,'benches_per_process':5,'sample_timeout_seconds':60,'timing_work_seconds':3600,'build_work_seconds':690,'attempts':1,'fault_retries':0}.items()) and cfg['bounds']['planned_fresh_processes']==188 and cfg['bounds']['planned_bench_commands']==940)
check('preregistered bootstrap seed agrees',cfg['bootstrap_seed']==analysis['BOOTSTRAP_SEED']==20261102)
for name in ['owned_process.py','archive_results.py']:
 check(name+' exact trusted21 bytes',sha(P/name)==sha(OLD/name))
check('owned process exact qualified461a',sha(P/'owned_process.py')=='461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d')
def funcs(p):return {n.name:ast.dump(n) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
a,b=funcs(P/'run_hosted.py'),funcs(OLD/'run_hosted.py')
check('same run_experiment and sample validator (no timing/statistical change)',a['run_experiment']==b['run_experiment'] and a['validate_sample']==b['validate_sample'])
a,b=funcs(P/'analysis.py'),funcs(OLD/'analysis.py')
check('all statistical functions unchanged',all(a[n]==b[n] for n in b if n!='parse_bench'))
a,b=funcs(P/'build_evidence.py'),funcs(OLD/'build_evidence.py')
check('complete strong performance build-evidence schema unchanged',a==b)
for name,expected in read(V/'IMMUTABLE-REFERENCES.json').items():
 p=R/name;check('old immutable '+name,sha(p)==expected['sha256'] and p.stat().st_mode&0o7777==expected['mode'])
manifest=P/'PACKAGE-SHA256SUMS';records={}
for line in manifest.read_text().splitlines():
 digest,name=line.split('  ',1);check('package hash '+name,sha(R/name)==digest and name not in records);records[name]=digest
actual=sorted([p.relative_to(R).as_posix() for p in P.rglob('*') if p.is_file() and p!=manifest]+[common['WORKFLOW']])
check('complete10 package inventory exact/nonbytecode',list(records)==actual and len(records)==10 and all('__pycache__' not in Path(n).parts and not n.endswith('.pyc') for n in actual))
for name,entry in read(V/'ACTUAL23-REUSE-REFERENCE.json')['input_bytes_modes'].items():
 p=R/name;check('actual23 untouched '+name,sha(p)==entry['sha256'] and p.stat().st_mode&0o7777==entry['mode'])
result={'status':'PASS_DISABLED24_SOURCE_ONLY_STATIC_CHECKS_NOT_LAUNCHED','checks_passed':len(checks),'checks':checks,'pins':{p.relative_to(R).as_posix():sha(p) for p in [P/'protocol.json',wf,P/'run_hosted.py',manifest,P/'owned_process.py',P/'build_evidence.py',P/'common.py',P/'analysis.py']},'counts':{'source_each':77,'ctest_each':14,'package_inventory':10,'required_future_finite_paths':13,'python_execution_files':7},'actual24_native_signature_capture_proofs':'PENDING_NOT_FABRICATED','engines_builds_matches_git_network_triggers_executed':0}
with (V/'PREPARER-STATIC-CHECKS.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','pins']}))
