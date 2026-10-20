from pathlib import Path
import hashlib,json
from pipeline_gate import load_freeze
FREEZE=load_freeze('source');COMMIT=FREEZE['source_commit'];PARENT=FREEZE['parent_source_commit']
R=Path('/workspace/dwqww');OUT=Path(__file__).resolve().parent;OLD=R/'validation/lazy-runtime-psqt-windows-20261020'
SOURCE=Path('/workspace/.cloud-setup/windows6420-source');BUILD=Path('/workspace/.cloud-setup/windows6420-build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def write(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n')
source=load(OUT/'source-hashes.json');parent=load(OLD/'source-hashes.json')
expected=['CMakeLists.txt','include/forge/bitboard.hpp','src/eval.cpp','src/uci.cpp','tests/pawn_span_tests.cpp']
changed=sorted(n for n,h in source.items() if parent.get(n)!=h)
assert changed==expected and set(parent).issubset(source) and len(source)==len(parent)+1==72
assert 'VERSION 6.4.20' in (SOURCE/'CMakeLists.txt').read_text()
assert 'Chess Engine Forge 6.4.20 candidate' in (SOURCE/'src/uci.cpp').read_text()
cmake=(SOURCE/'CMakeLists.txt').read_text();assert cmake.count('add_test(NAME ')==12
assert 'add_executable(forge_pawn_span_tests tests/pawn_span_tests.cpp)' in cmake
assert 'add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)' in cmake
assert (SOURCE/'tests/pawn_span_tests.cpp').read_text().count('static_assert(')==3
assert not BUILD.exists()
# Root native freeze is required; copy its exact bytes before any compiler starts.
gate_path=Path(FREEZE['root_source_gates_path']);assert sha(gate_path)==FREEZE['root_source_gates_sha256']
gates=load(gate_path);assert gates['source_commit']==COMMIT and gates['baseline_commit']==PARENT
assert source=={n:h for n,h in gates['inputs'].items() if not n.endswith('.pyc')}
(OUT/'ROOT-FROZEN-SOURCE-GATES.json').write_bytes(gate_path.read_bytes())
pinned=load(OLD/'PINNED-TOOLS.json');pinned['tools']['toolchain_source']['path']=str(SOURCE/'tools/windows-zen5.cmake');pinned['tools']['toolchain_source']['resolved_path']=str(SOURCE/'tools/windows-zen5.cmake')
for name,r in pinned['tools'].items():assert sha(Path(r['path']))==r['sha256'],name
pinned['version_evidence']='Reused immutable19 compiler/runtime evidence; no version query during20 preparation.'
pinned['parallel_build_jobs_after_clear']=1;write('PINNED-TOOLS.json',pinned)
write('STATIC-CHECKS.json',{'status':'SOURCE_EXPORTED_STATIC_CHECKS_ONLY_NO_BUILD','source_commit':COMMIT,'parent_source_commit':PARENT,'changed_exports':changed,'source_files':72,'runtime_summary_checks':347,'pawn_span_checks':37320,'pawn_constexpr_assertions':3,'correction_checks':54,'expected_bench_nodes':352313,'all_other_parent_exports_identical':True,'intended_eval_search_parity':True,'no_cpp_compiler_engine_wine_archive_executed':True})
print('Frozen20 source/root gate and pinned tools verified; no build/runtime/package yet.')
