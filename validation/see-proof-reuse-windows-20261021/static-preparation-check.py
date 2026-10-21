"""Offline AST/file-schema checks only. Never exports/builds/runs an engine."""
from pathlib import Path
import ast,datetime,hashlib,json,runpy
P=Path(__file__).resolve().parent;R=Path('/workspace/dwqww');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scripts=['pipeline_gate.py','prepare-source.py','prepare-records.py','build-driver.py','validation-driver.py','freeze-bench-signature.py','package-driver.py','independent-artifact-audit.py','run-phase.py','run-package.py']
checks=[]
def check(name,condition):
 checks.append({'name':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
texts={name:(P/name).read_text() for name in scripts}
for name,text in texts.items():ast.parse(text);check('syntax:'+name,True)
check('root_clearance_absent',not (P/'WINDOWS-BUILD-CLEAR.json').exists())
gate=runpy.run_path(str(P/'pipeline_gate.py'))
check('exact_source24',gate['SOURCE_COMMIT']=='7db08eac6ead99d641834c56ccec06a06600586a')
check('exact_parent23',gate['PARENT']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984')
for stage in ['source','build']:
 try:gate['load_freeze'](stage)
 except RuntimeError as e:check('closed:'+stage,'OFFLINE PREPARATION ONLY' in str(e))
 else:check('closed:'+stage,False)
for p in ['/workspace/.cloud-setup/windows6424-source','/workspace/.cloud-setup/windows6424-build','/workspace/.cloud-setup/windows6424-package-capture','/workspace/.cloud-setup/windows6424-package-ready','/workspace/dwqww/releases/forge-6.4.24-candidate-windows-zen5','/workspace/dwqww/releases/forge-6.4.24-candidate-windows-zen5.zip']:
 check('output_absent:'+p,not Path(p).exists())
rootgate=R/'validation/see-proof-reuse-candidate-20261021/ROOT-FROZEN24-SOURCE-GATES.json'
check('actual_root_gate_exacthash',sha(rootgate)=='8be7f3a73111350eca27adbe76bf001e5ab26915c73f1201c3056f881a87afd1')
g=json.loads(rootgate.read_text());m=json.loads((P/'PREPARED-EXPECTED77.json').read_text())
check('prepared77_equal_actual_root77',len(m)==77 and g['inputs']==m)
check('four_actual_changes',g['changed_paths']==['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tests.cpp'])
check('three_excluded_pyc',sum(x.endswith('.pyc') for x in m)==3)
check('all77_live_production_matches_frozen',all(sha(R/n)==h for n,h in m.items()))
check('stricttoolchain_baseline_path_retained',all('ubuntu-23.04' not in text and '24.1.3' not in text for text in texts.values()))
check('known_native_signature_not_used_as_Windows',all('292545' not in text for text in texts.values()))
check('core504_unique_marker_required',"see_summary==[(str(FREEZE['see_threshold_assertions']),'0')]" in texts['validation-driver.py'])
check('firstactual_signature_then_parentparity',"len(signature)==1 and int(signature[0])>0" in texts['validation-driver.py'] and "bench_nodes==FREEZE['parent_bench_parity_nodes']==334752" in texts['validation-driver.py'])
check('unknown_firstcapture_separate_from_parity',"FREEZE['bench_expected_nodes'] is None" in texts['freeze-bench-signature.py'])
check('freeze_exclusive',"(HERE/'BENCH-SIGNATURE-FREEZE.json').open('x')" in texts['freeze-bench-signature.py'])
check('parentparity_freezer',"record['bench11_nodes']==FREEZE['parent_bench_parity_nodes']==334752" in texts['freeze-bench-signature.py'])
check('same74_sourceinventory',"set(parent)==set(source) and len(source)==len(parent)==74" in texts['prepare-records.py'])
check('core_test_export_delta',"expected=['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tests.cpp']" in texts['prepare-records.py'])
check('unchanged_TTtest_source_binding',"'tt_test_source_sha256':source_hashes['tests/tt_coherence_tests.cpp']" in texts['package-driver.py'])
check('core_object_copied_and_bound',all(x in texts['package-driver.py'] for x in ["originals/'objects/tests.cpp.obj'","see-threshold-object-provenance.json","core_test_source_sha256","'assertions':504"]))
check('closed_package_writer',"windows6424-package-capture" in texts['run-package.py'] and "Package process stdout/stderr captured outside the raw snapshot" in texts['run-package.py'])
check('no_newmutable_proof_boolean_claim',"'pure_see_proof_reuse':True" in texts['package-driver.py'] and "'intended_eval_search_parity':True" in texts['package-driver.py'])
check('bench_single_producer_call',len([n for n in ast.walk(ast.parse(texts['validation-driver.py'])) if isinstance(n,ast.Call) and any(k.arg=='input' and isinstance(k.value,ast.Name) and k.value.id=='bench_stdin' for k in n.keywords)])==1)
commands=next(n.value for n in ast.walk(ast.parse(texts['validation-driver.py'])) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='commands' for t in n.targets))
check('12functional_plus_onebench_13checks',[n.elts[0].value for n in commands.elts]==['core','correction-history','runtime-psqt','pawn-span','nearest-pawn','pv-metadata','coherent-tt','rule50','legal-witness','uci','ponder','ownbook'])
check('auditor504_and_core_object_bindings',all(x in texts['independent-artifact-audit.py'] for x in ['see_threshold_assertions','see-threshold-object-provenance.json','core_test_source_sha256']))
before=json.loads((P/'parent6423-preservation-before.json').read_text());protocol=json.loads((P/'PROTOCOL.json').read_text())
check('actual597_parent23_inventory',len(before)==protocol['preserved_parent_files']==597)
check('all597_parent23_unchanged',all(sha(Path(n))==h for n,h in before.items()))
record={'status':'PASS_STATIC_PREPARATION_ALL_EXECUTION_GATES_CLOSED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks_passed':len(checks),'checks':checks,'helper_code_sha256':{name:sha(P/name) for name in scripts},'source_commit':gate['SOURCE_COMMIT'],'root_source_gate_sha256':sha(rootgate),'protected_parent23_files_unchanged':len(before),'source_export_compiler_engine_wine_package_audit_git_executed':False,'native_runtime_proof_and_root_clearance_pending':True}
(P/'STATIC-SCHEMA-CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['status','checks_passed','protected_parent23_files_unchanged']}))
