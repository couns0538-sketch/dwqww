"""Preparation-only file/AST checks; no engine/build/export/Git execution."""
import ast,datetime,hashlib,json,pathlib,runpy
P=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scripts=['pipeline_gate.py','prepare-source.py','prepare-records.py','build-driver.py','validation-driver.py','freeze-bench-signature.py','package-driver.py','independent-artifact-audit.py','run-phase.py','run-package.py']
checks=[]
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
for n in scripts:ast.parse((P/n).read_text());check('syntax:'+n,True)
check('no_authorization_file',not (P/'WINDOWS-BUILD-CLEAR.json').exists())
gate=runpy.run_path(str(P/'pipeline_gate.py'))
check('candidate_source_root_bound',gate['SOURCE_COMMIT']=='ff2e269c6058be84456e3b98344826d17b0056eb')
for stage in ['source','build']:
 try:gate['load_freeze'](stage)
 except RuntimeError as e:check('gate_closed:'+stage,'OFFLINE PREPARATION ONLY' in str(e))
 else:check('gate_closed:'+stage,False)
for p in ['/workspace/.cloud-setup/windows6422-source','/workspace/.cloud-setup/windows6422-build','/workspace/dwqww/releases/forge-6.4.22-candidate-windows-zen5','/workspace/dwqww/releases/forge-6.4.22-candidate-windows-zen5.zip']:
 check('candidate_output_absent:'+p,not pathlib.Path(p).exists())
texts={n:(P/n).read_text() for n in scripts}
check('no_inherited_or_Linux_bench_literal',all('352313' not in s and '292545' not in s for s in texts.values()))
tree=ast.parse(texts['validation-driver.py'])
bench_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and any(k.arg=='input' and isinstance(k.value,ast.Name) and k.value.id=='bench_stdin' for k in n.keywords)]
check('exactly_one_canonical_bench_call',len(bench_calls)==1)
check('single_exclusive_runtime_attempt',"OUT.mkdir(exist_ok=False)" in texts['validation-driver.py'] and ".open('xb')" in texts['validation-driver.py'])
check('PV_summary_required',"pv_summary==[(str(FREEZE['pv_metadata_assertions']),'0')]" in texts['validation-driver.py'])
check('candidate_signature_positive_and_unique',"len(signature)==1 and int(signature[0])>0" in texts['validation-driver.py'])
check('freezer_positive_and_nonoverwriting',"type(record['bench11_nodes']) is int and record['bench11_nodes']>0" in texts['freeze-bench-signature.py'] and "assert not (HERE/'BENCH-SIGNATURE-FREEZE.json').exists()" in texts['freeze-bench-signature.py'])
check('freezer_identity_fields',all(x in texts['freeze-bench-signature.py'] for x in ['source_and_tests_commit','engine_sha256','raw_bench_stdout_sha256','raw_bench_stdin_sha256','runtime_result_sha256','hash_mib','threads','frozen_utc']))
check('auditor_rechecks_capture_identities',all(x in texts['independent-artifact-audit.py'] for x in ['bench_freeze_raw_stdin','bench_freeze_runtime_result','bench_freeze_settings','bench_freeze_exactly_one_original_summary','bench_freeze_before_package_execution']))
check('PV_object_PE_source_compile_provenance',all(x in texts['independent-artifact-audit.py'] for x in ['pv_metadata_actual_object_retained','pv_metadata_object_source_identity','pv_metadata_object_tested_pe_identity','pv_metadata_object_compile_identity']))
check('freezer_exclusive_creation',"(HERE/'BENCH-SIGNATURE-FREEZE.json').open('x')" in texts['freeze-bench-signature.py'])
unchanged_loops=[n for n in ast.walk(ast.parse(texts['independent-artifact-audit.py'])) if isinstance(n,ast.For) and isinstance(n.iter,ast.List) and any(isinstance(v,ast.Constant) and v.value=='src/board.cpp' for v in n.iter.elts)]
check('changed_search_excluded_from_unchanged_boundary',len(unchanged_loops)==1 and 'src/search.cpp' not in [v.value for v in unchanged_loops[0].iter.elts])
commands=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='commands' for t in n.targets))
names=[n.elts[0].value for n in commands.elts]
check('thirteen_named_runtime_checks',names==['core','correction-history','runtime-psqt','pawn-span','nearest-pawn','pv-metadata','coherent-tt','rule50','legal-witness','uci','ponder','ownbook'])
before=json.loads((P/'parent6421-preservation-before.json').read_text())
check('all543_parent21_original_hashes_unchanged',len(before)==543 and all(sha(pathlib.Path(n))==h for n,h in before.items()))
record={'status':'PASS_STATIC_PREPARATION_ALL_EXECUTION_GATES_CLOSED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'checks_passed':len(checks),'scripts_syntax_valid':len(scripts),'protected_parent21_files_unchanged':len(before),'source_export_started':False,'compiler_engine_wine_package_audit_git_started':False,'root_clearance_needed':True}
(P/'STATIC-SCHEMA-CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['status','checks_passed','scripts_syntax_valid','protected_parent21_files_unchanged']}))
