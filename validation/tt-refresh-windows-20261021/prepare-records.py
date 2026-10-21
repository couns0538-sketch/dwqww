from pathlib import Path
import hashlib,json
from pipeline_gate import load_freeze
FREEZE=load_freeze('source');COMMIT=FREEZE['source_commit'];PARENT=FREEZE['parent_source_commit']
R=Path('/workspace/dwqww');OUT=Path(__file__).resolve().parent;OLD=R/'validation/pv-metadata-windows-20261021'
SOURCE=Path('/workspace/.cloud-setup/windows6423-source');BUILD=Path('/workspace/.cloud-setup/windows6423-build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def write(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n')
source=load(OUT/'source-hashes.json');parent=load(OLD/'source-hashes.json')
expected=['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tt_coherence_tests.cpp']
changed=sorted(n for n,h in source.items() if parent.get(n)!=h)
assert changed==expected and set(parent)==set(source) and len(source)==len(parent)==74
assert 'VERSION 6.4.23' in (SOURCE/'CMakeLists.txt').read_text()
assert 'Chess Engine Forge 6.4.23 candidate' in (SOURCE/'src/uci.cpp').read_text()
cmake=(SOURCE/'CMakeLists.txt').read_text();assert cmake.count('add_test(NAME ')==14
assert 'add_executable(forge_pawn_span_tests tests/pawn_span_tests.cpp)' in cmake
assert 'add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)' in cmake
assert (SOURCE/'tests/pawn_span_tests.cpp').read_text().count('static_assert(')==3
assert 'add_executable(forge_nearest_pawn_tests tests/nearest_pawn_tests.cpp)' in cmake
assert 'add_test(NAME forge_nearest_pawn_tests COMMAND forge_nearest_pawn_tests)' in cmake
assert (SOURCE/'tests/nearest_pawn_tests.cpp').read_text().count('static_assert(')==6
assert [line.split('NAME ',1)[1].split()[0] for line in cmake.splitlines() if 'add_test(NAME ' in line][:5]==['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests']
assert 'add_executable(forge_pv_metadata_tests tests/pv_metadata_tests.cpp)' in cmake
assert 'add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)' in cmake
assert [line.split('NAME ',1)[1].split()[0] for line in cmake.splitlines() if 'add_test(NAME ' in line][5]=='forge_pv_metadata_tests'
assert sha(SOURCE/'tests/tt_coherence_tests.cpp')==FREEZE['tt_test_sha256']
assert 'All12 TT coherence/regression groups passed' in (SOURCE/'tests/tt_coherence_tests.cpp').read_text()
assert sha(SOURCE/'tests/pv_metadata_tests.cpp')==FREEZE['pv_metadata_test_sha256']
assert not BUILD.exists()
# Root native freeze is required; copy its exact bytes before any compiler starts.
gate_path=Path(FREEZE['root_source_gates_path']);assert sha(gate_path)==FREEZE['root_source_gates_sha256']
gates=load(gate_path);assert gates['source_commit']==COMMIT and gates['baseline_commit']==PARENT
assert len(gates['inputs'])==77 and sum(n.endswith('.pyc') for n in gates['inputs'])==3
assert source=={n:h for n,h in gates['inputs'].items() if not n.endswith('.pyc')}
assert source['src/search.cpp']==FREEZE['production_search_sha256']
(OUT/'ROOT-FROZEN-SOURCE-GATES.json').write_bytes(gate_path.read_bytes())
pinned=load(OLD/'PINNED-TOOLS.json');pinned['tools']['toolchain_source']['path']=str(SOURCE/'tools/windows-zen5.cmake');pinned['tools']['toolchain_source']['resolved_path']=str(SOURCE/'tools/windows-zen5.cmake')
for name,r in pinned['tools'].items():assert sha(Path(r['path']))==r['sha256'],name
pinned['version_evidence']='Reused immutable22 compiler/runtime evidence; no version query during23 offline preparation.'
pinned['parallel_build_jobs_after_clear']=1;write('PINNED-TOOLS.json',pinned)
write('STATIC-CHECKS.json',{'status':'SOURCE_EXPORTED_STATIC_CHECKS_ONLY_NO_BUILD','source_commit':COMMIT,'parent_source_commit':PARENT,'changed_exports':changed,'source_files':74,'runtime_summary_checks':347,'pawn_span_checks':37320,'pawn_constexpr_assertions':3,'nearest_pawn_checks':791680,'nearest_pawn_sets':395840,'nearest_constexpr_assertions':6,'correction_checks':54,'tt_groups':12,'expected_bench_nodes':None,'pv_metadata_assertions':56,'all_other_parent_exports_identical':True,'intended_eval_search_parity':False,'intended_evaluation_parity':True,'no_cpp_compiler_engine_wine_archive_executed':True})
print('Frozen23 source/root gate and pinned tools verified; no build/runtime/package yet.')
