from pathlib import Path
import datetime,hashlib,json
from pipeline_gate import load_freeze
FREEZE=load_freeze('source'); COMMIT=FREEZE['source_commit'];PARENT=FREEZE['parent_source_commit']
R=Path('/workspace/dwqww');OUT=Path(__file__).resolve().parent;OLD=R/'validation/correction-history-windows-20261020'
SOURCE=Path('/workspace/.cloud-setup/windows6419-source');BUILD=Path('/workspace/.cloud-setup/windows6419-build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def write(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n')
source=load(OUT/'source-hashes.json');parent=load(OLD/'source-hashes.json')
expected=['CMakeLists.txt','include/forge/eval.hpp','include/forge/search.hpp','src/eval.cpp','src/search.cpp','src/uci.cpp','tests/runtime_psqt_tests.cpp']
changed=sorted(n for n,h in source.items() if parent.get(n)!=h)
assert changed==expected and set(parent).issubset(source) and len(source)==len(parent)+1
assert 'VERSION 6.4.19' in (SOURCE/'CMakeLists.txt').read_text()
assert 'Chess Engine Forge 6.4.19 candidate' in (SOURCE/'src/uci.cpp').read_text()
assert 'add_executable(forge_runtime_psqt_tests tests/runtime_psqt_tests.cpp)' in (SOURCE/'CMakeLists.txt').read_text()
assert 'add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)' in (SOURCE/'CMakeLists.txt').read_text()
assert not BUILD.exists()
pinned=load(OLD/'PINNED-TOOLS.json');pinned['tools']['toolchain_source']['path']=str(SOURCE/'tools/windows-zen5.cmake');pinned['tools']['toolchain_source']['resolved_path']=str(SOURCE/'tools/windows-zen5.cmake')
for name,r in pinned['tools'].items():assert sha(Path(r['path']))==r['sha256'],name
pinned['version_evidence']='Reused immutable18 observed compiler/runtime evidence; no version query during19 preparation.'
pinned['parallel_build_jobs_after_clear']=1;write('PINNED-TOOLS.json',pinned)
write('STATIC-CHECKS.json',{'status':'SOURCE_EXPORTED_STATIC_CHECKS_ONLY_NO_BUILD','source_commit':COMMIT,'parent_source_commit':PARENT,'changed_exports':changed,'source_files':len(source),'runtime_summary_checks':FREEZE['runtime_summary_checks'],'correction_checks':54,'expected_bench_nodes':352313,'all_other_parent_exports_identical':True,'intended_eval_search_parity':True,'no_cpp_compiler_engine_wine_archive_executed':True})
print('Frozen19 source and pinned tools verified; no build/runtime/package yet.')
