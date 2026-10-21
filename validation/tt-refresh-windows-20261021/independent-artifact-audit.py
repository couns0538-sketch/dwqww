#!/usr/bin/env python3
"""Read-only Windows 6.4.23 artifact/provenance audit; executes no engine."""
from pathlib import Path, PurePosixPath
import datetime
import hashlib
import json
import re
import stat
import struct
import subprocess
import zipfile

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/tt-refresh-windows-20261021'
SOURCE = Path('/workspace/.cloud-setup/windows6423-source')
BUILD = Path('/workspace/.cloud-setup/windows6423-build')
PACKAGE = ROOT / 'releases/forge-6.4.23-candidate-windows-zen5'
ARCHIVE = PACKAGE.with_name(PACKAGE.name + '.zip')
from pipeline_gate import load_freeze, SOURCE_COMMIT
FREEZE = load_freeze()
COMMIT = FREEZE['source_commit']
PARENT = FREEZE['parent_source_commit']
assert COMMIT != PARENT, 'Windows23 source must be a distinct root-frozen revision'
assert COMMIT == SOURCE_COMMIT, 'Incorrect root-authorized frozen23 source'
assert PARENT == 'ff2e269c6058be84456e3b98344826d17b0056eb'
assert FREEZE['runtime_summary_checks'] == 347 and FREEZE['pawn_span_checks'] == 37320
assert FREEZE['bench_expected_nodes'] is None
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())
checks = []

def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    if not value:
        raise AssertionError(name)

def archive_safety(z):
    names = z.namelist()
    check('unique_zip_members', len(names) == len(set(names)))
    check('no_case_collisions', len(names) == len({n.casefold() for n in names}))
    for info in z.infolist():
        p = PurePosixPath(info.filename)
        check('safe_member:' + info.filename, not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename)
        check('not_symlink:' + info.filename, not stat.S_ISLNK(info.external_attr >> 16))
    check('zip_crc', z.testzip() is None)
    check('no_encrypted_members', all((i.flag_bits & 1)==0 for i in z.infolist()))

def pe_imports(data):
    check('pe_dos_magic', data[:2] == b'MZ')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    check('pe_signature', data[pe:pe+4] == b'PE\0\0')
    machine, sections = struct.unpack_from('<HH', data, pe+4)
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    optional = pe+24
    check('pe_amd64_machine', machine == 0x8664)
    check('pe32plus', struct.unpack_from('<H', data, optional)[0] == 0x20b)
    section_start = optional + optional_size
    def offset(rva):
        for i in range(sections):
            at = section_start + i*40
            virtual_size, virtual, raw_size, raw = struct.unpack_from('<IIII', data, at+8)
            if virtual <= rva < virtual + max(virtual_size, raw_size):
                return raw + rva - virtual
        raise AssertionError('unmapped PE RVA')
    import_rva = struct.unpack_from('<I', data, optional+120)[0]
    result = []
    at = offset(import_rva)
    while any(data[at:at+20]):
        name_rva = struct.unpack_from('<I', data, at+12)[0]
        name_offset = offset(name_rva)
        end = data.index(b'\0', name_offset)
        result.append(data[name_offset:end].decode('ascii'))
        at += 20
    return result

assert Path('/workspace/.cloud-setup/windows6423-package-ready').exists(), 'Package not final yet'
runtime = load(HERE/'runtime-attempt1/result.json')
build = load(HERE/'result.json')
artifact = load(HERE/'artifact.json')
check('runtime_passed', runtime['status'] == 'passed')
check('build_passed', build['status'] == 'build_passed')
check('frozen_source_identity', runtime['source_and_tests_commit'] == build['source_and_tests_commit'] == artifact['source_and_tests_commit'] == COMMIT)
check('thirteen_runtime_checks', len(runtime['checks']) == 13 and all(c['exit_code'] == 0 for c in runtime['checks']))
check('thirteen_named_checks', {c['name'] for c in runtime['checks']} == {'core','coherent-tt','rule50','legal-witness','correction-history','runtime-psqt','pawn-span','nearest-pawn','pv-metadata','uci','ponder','ownbook','stdin-bench11-signature'})
check('tt_groups', runtime['tt_groups'] == 12)
check('legal_witness_count', runtime['legal_witness_comparisons'] == 18947)
check('rule50_pass', runtime['rule50_targeted_failures'] == 0)
check('first_normal_candidate_bench_signature',type(runtime['bench11_nodes']) is int and runtime['bench11_nodes']>0 and FREEZE['bench_expected_nodes'] is None)
freeze_path = HERE/'BENCH-SIGNATURE-FREEZE.json'
freeze = load(freeze_path)
check('bench_freeze_candidate_source', freeze['source_and_tests_commit'] == COMMIT)
check('bench_freeze_actual_nodes', freeze['bench11_nodes'] == runtime['bench11_nodes'])
check('bench_freeze_tested_pe', freeze['engine_sha256'] == runtime['input_sha256_after']['forge.exe'])
check('bench_freeze_raw_stdout', freeze['raw_bench_stdout_sha256'] == sha((HERE/'runtime-attempt1/bench-stdout.log').read_bytes()))
check('bench_freeze_native_independent', freeze['native_independent'] is True)
check('bench_freeze_raw_stdin',freeze['raw_bench_stdin_sha256']==sha((HERE/'runtime-attempt1/bench-stdin.txt').read_bytes()))
check('bench_freeze_runtime_result',freeze['runtime_result_sha256']==sha((HERE/'runtime-attempt1/result.json').read_bytes()))
check('bench_freeze_settings',freeze['hash_mib']==16 and freeze['threads']==1 and (HERE/'runtime-attempt1/bench-stdin.txt').read_bytes()==b'bench 11\nquit\n')
raw_signature=re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',(HERE/'runtime-attempt1/bench-stdout.log').read_text(),re.M)
check('bench_freeze_exactly_one_original_summary',raw_signature==[str(runtime['bench11_nodes'])])
package_phase = load(HERE/'package-phase-command.json')
freeze_time = datetime.datetime.fromisoformat(freeze['frozen_utc'])
package_started = datetime.datetime.fromisoformat(package_phase['started_utc'])
package_completed = datetime.datetime.fromisoformat(package_phase['completed_utc'])
check('bench_freeze_timezone_aware', all(value.utcoffset() is not None for value in [freeze_time, package_started, package_completed]))
check('bench_freeze_before_package_execution', freeze_time <= package_started <= package_completed)
check('bench_freeze_before_release_zip', freeze_path.stat().st_mtime_ns <= ARCHIVE.stat().st_mtime_ns and freeze_time.timestamp() <= ARCHIVE.stat().st_mtime)

pv_raw=(HERE/'runtime-attempt1/pv-metadata-stdout.log').read_text()
pv_summary=re.findall(r'^PV metadata: assertions (\d+) failures (\d+)\s*$',pv_raw,re.M)
check('actual_pv_metadata_summary',pv_summary==[('56','0')] and not re.search(r'^FAIL ',pv_raw,re.M))
check('actual_pv_metadata_runtime_count',runtime['pv_metadata_assertions']==56 and runtime['pv_metadata_failures']==0)
check('raw_core_tests_pass', 'All tests passed' in (HERE/'runtime-attempt1/core-stdout.log').read_text())
tt_summary=re.findall(r'^All(\d+) TT coherence/regression groups passed\s*$',(HERE/'runtime-attempt1/coherent-tt-stdout.log').read_text(),re.M)
check('raw_tt12_unique_success_summary',tt_summary==['12'] and int(tt_summary[0])==runtime['tt_groups']==FREEZE['tt_groups'])
check('raw_rule50_pass', 'targeted_regression_failures=0' in (HERE/'runtime-attempt1/rule50-stdout.log').read_text())
check('raw_legal_oracle_pass', 'All 18947 legal-witness Boolean comparisons passed' in (HERE/'runtime-attempt1/legal-witness-stdout.log').read_text())
correction_raw = (HERE/'runtime-attempt1/correction-history-stdout.log').read_text()
correction_summary = re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', correction_raw, re.M)
check('actual_correction_test_summary', correction_summary == [('54','0')])
correction_checks = int(correction_summary[0][0])
check('actual_correction_pass_count', len(re.findall(r'^PASS ', correction_raw, re.M))==correction_checks and not re.search(r'^FAIL ',correction_raw,re.M))
check('actual_correction_raw_header', 'Correction-history residual increment contract' in correction_raw)
check('actual_correction_runtime_count', runtime['correction_history_checks']==correction_checks and runtime['correction_history_failures']==0)
runtime_psqt_raw = (HERE/'runtime-attempt1/runtime-psqt-stdout.log').read_text()
runtime_psqt_summary = re.findall(r'^SUMMARY checks=(\d+) failures=(\d+)\s*$', runtime_psqt_raw, re.M)
check('actual_runtime_psqt_summary', runtime_psqt_summary == [('347','0')] and FREEZE['runtime_summary_checks'] == 347)
check('actual_runtime_psqt_pass_count', len(re.findall(r'^PASS ',runtime_psqt_raw,re.M)) == 347 and not re.search(r'^FAIL ',runtime_psqt_raw,re.M))
check('actual_runtime_psqt_runtime_count', runtime['runtime_psqt_checks'] == 347 and runtime['runtime_psqt_failures'] == 0)
pawn_raw=(HERE/'runtime-attempt1/pawn-span-stdout.log').read_text()
pawn_summary=re.findall(r'^pawn_span_tests: (\d+) checks, (\d+) failures\s*$',pawn_raw,re.M)
check('actual_pawn_span_summary',pawn_summary==[('37320','0')] and not re.search(r'^FAIL ',pawn_raw,re.M))
check('actual_pawn_span_runtime_count',runtime['pawn_span_checks']==37320 and runtime['pawn_span_failures']==0)
nearest_raw=(HERE/'runtime-attempt1/nearest-pawn-stdout.log').read_text()
nearest_summary=re.findall(r'^Nearest pawn distance: sets (\d+) checks (\d+) failures (\d+)\s*$',nearest_raw,re.M)
check('actual_nearest_summary',nearest_summary==[('395840','791680','0')] and not re.search(r'^nearest mismatch ',nearest_raw,re.M))
check('actual_nearest_runtime_counts',runtime['nearest_pawn_checks']==791680 and runtime['nearest_pawn_sets']==395840 and runtime['nearest_pawn_failures']==0)
check('raw_bench_matches_record',re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$', (HERE/'runtime-attempt1/bench-stdout.log').read_text(),re.M)==[str(runtime['bench11_nodes'])])
check('five_book_transitions', len(runtime['ownbook_transitions']) == 5 and all(c['PASS'] and c['expected_book'] == c['actual_book'] for c in runtime['ownbook_transitions']))
check('runtime_inputs_unchanged', runtime['input_sha256_before'] == runtime['input_sha256_after'])
check('validation_command_rc0', load(HERE/'validation-phase-command.json')['exit_code'] == 0)
check('package_command_rc0', load(HERE/'package-phase-command.json')['exit_code'] == 0)
check('build_command_rc0', load(HERE/'build-phase-command.json')['exit_code'] == 0)

source_hashes = load(HERE/'source-hashes.json')
git_export_names = subprocess.check_output(['git','ls-tree','-r','--name-only',COMMIT,'--','CMakeLists.txt','LICENSE','src','include','tests','bench','tools'],cwd=ROOT,text=True).splitlines()
check('complete_git_export_inventory', set(source_hashes) == {name for name in git_export_names if not name.endswith('.pyc')})
check('production_manifest_complete', load(HERE/'production-hashes.json') == {name:digest for name,digest in source_hashes.items() if name == 'CMakeLists.txt' or name.startswith(('src/','include/'))})
check('test_manifest_complete', load(HERE/'test-hashes.json') == {name:digest for name,digest in source_hashes.items() if name.startswith('tests/')})
check('complete_source_export', source_hashes == {p.relative_to(SOURCE).as_posix(): sha(p.read_bytes()) for p in SOURCE.rglob('*') if p.is_file()})
for name, digest in source_hashes.items():
    check('git_source:' + name, sha(subprocess.check_output(['git', 'show', COMMIT + ':' + name], cwd=ROOT)) == digest)
production_names = [n for n in source_hashes if n == 'CMakeLists.txt' or n.startswith(('src/','include/'))]
changed = []
for name in production_names:
    parent_bytes = subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT)
    if sha(parent_bytes) != source_hashes[name]: changed.append(name)
check('only_reviewed_production_delta', sorted(changed)==['CMakeLists.txt','src/search.cpp','src/uci.cpp'])
check('exact_reviewed_search_source',source_hashes['src/search.cpp']==FREEZE['production_search_sha256'])
check('exact_reviewed_correction_test', source_hashes['tests/correction_history_tests.cpp'] == '3f5523ac462cde0a36ce3df4f5bfb99e59dbe34a08c9e2d06dcb9ecad5dad66d')
frozen_root=load(HERE/'ROOT-FROZEN-SOURCE-GATES.json')
check('root_frozen_source_proof_sha256',sha((HERE/'ROOT-FROZEN-SOURCE-GATES.json').read_bytes())==FREEZE['root_source_gates_sha256'])
check('root_frozen_source_identity',frozen_root['source_commit']==COMMIT and frozen_root['baseline_commit']==PARENT)
check('root_native77_filtered74_inventory',len(frozen_root['inputs'])==77 and sum(n.endswith('.pyc') for n in frozen_root['inputs'])==3)
check('root_frozen_source_inventory',source_hashes=={n:h for n,h in frozen_root['inputs'].items() if not n.endswith('.pyc')} and len(source_hashes)==74)
reviewed_tt_hashes={n:frozen_root['inputs'][n] for n in ['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tt_coherence_tests.cpp']}
for name,digest in reviewed_tt_hashes.items():
    check('reviewed_tt_source:'+name,source_hashes[name]==digest)
changed_all = []
for name, digest in source_hashes.items():
    parent = subprocess.run(['git','show',PARENT+':'+name],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if parent.returncode or sha(parent.stdout) != digest:
        changed_all.append(name)
check('only_declared_four_export_changes', sorted(changed_all) == sorted(reviewed_tt_hashes))
for name in [n for n in source_hashes if n.startswith('tests/') and n != 'tests/tt_coherence_tests.cpp']:
    check('unchanged_parent_test:'+name,sha(subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT))==source_hashes[name])
permanent_tests = (SOURCE/'tests/tests.cpp').read_text()
check('permanent_pin_regression_registered', 'void test_pinned_static_exchange()' in permanent_tests and '    test_pinned_static_exchange();' in permanent_tests)
check('permanent_see_regression_28_cases_mirrored', 'std::array<ExchangeCase, 28> cases' in permanent_tests and 'for (const bool mirrored : {false, true})' in permanent_tests)
check('permanent_see_zero_threshold_assertion', 'check(board.see_ge(*move, 0) == (item.gain >= 0), item.name);' in permanent_tests)
check('five_promotion_recapture_cases', all(name in permanent_tests for name in [
    'later promotion saves capture', 'enemy promotion poisons capture', 'pinned promoting recapturer',
    'promoted recapturer taken by king', 'promotion recapture changes victim']))


correction_test = (SOURCE/'tests/correction_history_tests.cpp').read_text()
check('actual_methods_used_by_permanent_correction_test', all(s in correction_test for s in ['return w.corrected_eval(b, raw);','w.update_correction(b, depth, best, corrected);','if (count != 1) throw std::runtime_error']))
check('correction_feedback_coverage_source', all(s in correction_test for s in ['zero-residual update retains learned feedback','fixed delta6 convergence','reachable range under constant clipped residual','shared material transfers correction to distinct pawn structure','unequal tables consume same precomputed joint residual','upper output mate boundary clamps','lower output mate boundary clamps','signed truncation on subgrain seeded entry']))
cmake_text = (SOURCE/'CMakeLists.txt').read_text()
check('correction_ctest_registered', 'add_executable(forge_correction_history_tests tests/correction_history_tests.cpp)' in cmake_text and 'add_test(NAME forge_correction_history_tests COMMAND forge_correction_history_tests)' in cmake_text)
check('runtime_psqt_ctest_registered', 'add_executable(forge_runtime_psqt_tests tests/runtime_psqt_tests.cpp)' in cmake_text and 'add_test(NAME forge_runtime_psqt_tests COMMAND forge_runtime_psqt_tests)' in cmake_text)
check('fourteen_ctests_registered', len(re.findall(r'^\s*add_test\(', cmake_text, re.M)) == 14)
check('pawn_ctest_registered','add_executable(forge_pawn_span_tests tests/pawn_span_tests.cpp)' in cmake_text and 'add_test(NAME forge_pawn_span_tests COMMAND forge_pawn_span_tests)' in cmake_text)
pawn_test=(SOURCE/'tests/pawn_span_tests.cpp').read_text()
check('three_pawn_constexpr_assertions_compiled',pawn_test.count('static_assert(')==3)
check('pawn_independent_geometry_oracles_retained',all(x in pawn_test for x in ['original_span','original_fill','table_pawn_attacks','passed_pawn_mask','pawn_attacks_bb','4096','256']))
check('tt12_frozen_test_source',source_hashes['tests/tt_coherence_tests.cpp']==FREEZE['tt_test_sha256'])
check('tt12_source_success_line','All12 TT coherence/regression groups passed' in (SOURCE/'tests/tt_coherence_tests.cpp').read_text())
check('pv_metadata_ctest_registered','add_executable(forge_pv_metadata_tests tests/pv_metadata_tests.cpp)' in cmake_text and 'add_test(NAME forge_pv_metadata_tests COMMAND forge_pv_metadata_tests)' in cmake_text)
check('pv_metadata_sixth_ctest',[line.split('NAME ',1)[1].split()[0] for line in cmake_text.splitlines() if 'add_test(NAME ' in line][5]=='forge_pv_metadata_tests')
check('pv_metadata_frozen_test_source',source_hashes['tests/pv_metadata_tests.cpp']==FREEZE['pv_metadata_test_sha256'])
check('nearest_ctest_registered','add_executable(forge_nearest_pawn_tests tests/nearest_pawn_tests.cpp)' in cmake_text and 'add_test(NAME forge_nearest_pawn_tests COMMAND forge_nearest_pawn_tests)' in cmake_text)
check('nearest_fifth_ctest',[line.split('NAME ',1)[1].split()[0] for line in cmake_text.splitlines() if 'add_test(NAME ' in line][4]=='forge_nearest_pawn_tests')
nearest_test=(SOURCE/'tests/nearest_pawn_tests.cpp').read_text()
check('six_nearest_constexpr_assertions_compiled',nearest_test.count('static_assert(')==6)
check('nearest_two_independent_oracles',all(x in nearest_test for x in ['scalar_reference','flood_reference','std::array<int, 2> expected','std::abs','reachable','2048','256']))
parent_search = subprocess.check_output(['git','show',PARENT+':src/search.cpp'],cwd=ROOT,text=True)
search_text = (SOURCE/'src/search.cpp').read_text()
increment = 'entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);'
check('inherited_residual_correction_preserved', parent_search.count(increment) == 1 and search_text.count(increment) == 1)
runtime_test = (SOURCE/'tests/runtime_psqt_tests.cpp').read_text()
check('runtime_psqt_actual_worker_oracle', all(term in runtime_test for term in (
    'return w.static_evaluate(b, ss);', 'Evaluator::evaluate_uncached(b)',
    'nnue::evaluate(b,ss->accumulator)', 'actual Worker evaluation equals full oracle with same NNUE accumulator')))
check('runtime_psqt_edge_and_fallback_coverage', all(term in runtime_test for term in (
    'en passant', 'capture promotion', 'raw phase25 to24 capture',
    'four unevaluated ancestor edges', 'NNUE valid PSQT invalid fallback',
    'NNUE replay with invalid PSQT ancestor fallback', 'null invalidates stale sibling',
    'public evaluate sees mutation after FEN', 'NNUE-disabled original public HCE path')))
for name in ['src/board.cpp','include/forge/board.hpp','src/nnue.cpp','src/nnue_weights.inc','include/forge/nnue.hpp','src/eval_params.cpp','src/eval_params_table.inc','include/forge/eval_params.hpp','include/forge/eval.hpp','include/forge/search.hpp','src/eval.cpp','include/forge/bitboard.hpp']:
    check('unchanged_parent_board_nnue_params:' + name, sha(subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT)) == source_hashes[name])

with zipfile.ZipFile(ARCHIVE) as z:
    archive_safety(z)
    files = sorted(p for p in PACKAGE.iterdir() if p.is_file())
    check('release_exact_directory_inventory', set(z.namelist()) == {PACKAGE.name + '/' + p.name for p in files})
    for p in files:
        check('release_bytes:' + p.name, z.read(PACKAGE.name + '/' + p.name) == p.read_bytes())
    sums = (PACKAGE/'SHA256SUMS').read_text().splitlines()
    check('checksum_complete_except_self', {line.split('  ', 1)[1] for line in sums} == {p.name for p in files if p.name != 'SHA256SUMS'})
    for line in sums:
        digest, name = line.split('  ', 1)
        check('release_sha:' + name, sha(z.read(PACKAGE.name + '/' + name)) == digest)
release_members = len(files)
check('release_artifact_hash_size', sha(ARCHIVE.read_bytes()) == artifact['sha256'] and ARCHIVE.stat().st_size == artifact['bytes'])

for record in list(build['binaries'].values()) + list(build['libraries'].values()):
    check('built_bytes:' + Path(record['path']).name, sha(Path(record['path']).read_bytes()) == record['sha256'] and Path(record['path']).stat().st_size == record['bytes'])
imports = {}
expected_built_pe = {'forge.exe','forge_bench.exe','forge_tests.exe','forge_tt_tests.exe','forge_rule50_tests.exe','forge_legal_witness_tests.exe','forge_correction_history_tests.exe','forge_runtime_psqt_tests.exe','forge_pawn_span_tests.exe','forge_nearest_pawn_tests.exe','forge_pv_metadata_tests.exe'}
check('eleven_built_pe_inventory', {p.name for p in BUILD.glob('*.exe')} == expected_built_pe)
for p in sorted(BUILD.glob('*.exe')):
    check('tested_actual_pe:' + p.name, sha(p.read_bytes()) == runtime['input_sha256_after'][p.name])
    imports[p.name] = pe_imports(p.read_bytes())
    check('system_crt_imports_only:' + p.name, bool(imports[p.name]) and all(n.lower() == 'kernel32.dll' or n.lower().startswith('api-ms-win-crt-') for n in imports[p.name]))
check('packaged_tested_engine', sha((PACKAGE/'forge-6.4.23-ryzen-9850x3d.exe').read_bytes()) == runtime['input_sha256_after']['forge.exe'])
for name in ['forge_tests.exe', 'forge_tt_tests.exe', 'forge_rule50_tests.exe', 'forge_legal_witness_tests.exe', 'forge_correction_history_tests.exe', 'forge_runtime_psqt_tests.exe','forge_pawn_span_tests.exe','forge_nearest_pawn_tests.exe','forge_pv_metadata_tests.exe']:
    check('packaged_tested_helper:' + name, sha((PACKAGE/name).read_bytes()) == runtime['input_sha256_after'][name])
check('tested_core', sha((BUILD/'libforge_core.a').read_bytes()) == runtime['input_sha256_after']['core_library'])
check('ten_distributed_pe_inventory', {p.name for p in PACKAGE.glob('*.exe')} == (expected_built_pe - {'forge.exe','forge_bench.exe'}) | {'forge-6.4.23-ryzen-9850x3d.exe'})

raw = HERE/'windows-originals.zip'
manifest = load(HERE/'windows-originals-SHA256.json')
check('bench_freeze_raw_archive_member', 'BENCH-SIGNATURE-FREEZE.json' in manifest)
check('runtime_object_raw_archive_members', all(n in manifest for n in ('originals/objects/runtime_psqt_tests.cpp.obj','runtime-object-provenance.json','originals/frozen-source/tests/runtime_psqt_tests.cpp','originals/binaries/forge_runtime_psqt_tests.exe')))
check('pawn_object_raw_archive_members',all(n in manifest for n in ('originals/objects/pawn_span_tests.cpp.obj','pawn-object-provenance.json','originals/frozen-source/tests/pawn_span_tests.cpp','originals/binaries/forge_pawn_span_tests.exe')))
check('nearest_object_raw_archive_members',all(n in manifest for n in ('originals/objects/nearest_pawn_tests.cpp.obj','nearest-object-provenance.json','originals/frozen-source/tests/nearest_pawn_tests.cpp','originals/binaries/forge_nearest_pawn_tests.exe')))
check('pv_metadata_object_raw_archive_members',all(n in manifest for n in ('originals/objects/pv_metadata_tests.cpp.obj','pv-metadata-object-provenance.json','originals/frozen-source/tests/pv_metadata_tests.cpp','originals/binaries/forge_pv_metadata_tests.exe')))
check('tt_object_raw_archive_members',all(n in manifest for n in ('originals/objects/tt_coherence_tests.cpp.obj','tt-object-provenance.json','originals/frozen-source/tests/tt_coherence_tests.cpp','originals/binaries/forge_tt_tests.exe')))
with zipfile.ZipFile(raw) as z:
    archive_safety(z)
    check('raw_exact_inventory', set(z.namelist()) == set(manifest) | {'windows-originals-SHA256.json'})
    check('embedded_raw_manifest', json.loads(z.read('windows-originals-SHA256.json')) == manifest)
    for name, item in manifest.items():
        data = z.read(name)
        check('raw_original:' + name, data == (HERE/name).read_bytes() and len(data) == item['bytes'] and sha(data) == item['sha256'])
check('packaged_raw_archive', (PACKAGE/'windows-originals.zip').read_bytes() == raw.read_bytes())
check('raw_recorded_hash', sha(raw.read_bytes()) == artifact['raw_archive_sha256'])

commands = load(HERE/'compile_commands.json')
runtime_object = BUILD/'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.obj'
runtime_object_copy = HERE/'originals/objects/runtime_psqt_tests.cpp.obj'
object_provenance = load(HERE/'runtime-object-provenance.json')
runtime_compile_records = [r for r in commands if r['file'].endswith('/tests/runtime_psqt_tests.cpp')]
check('runtime_actual_object_retained', runtime_object.read_bytes() == runtime_object_copy.read_bytes() and sha(runtime_object.read_bytes()) == object_provenance['object_sha256'])
check('runtime_object_source_identity', object_provenance['runtime_test_source_sha256'] == source_hashes['tests/runtime_psqt_tests.cpp'])
check('runtime_object_tested_pe_identity', object_provenance['tested_pe_sha256'] == runtime['input_sha256_after']['forge_runtime_psqt_tests.exe'])
check('runtime_object_compile_records', len(runtime_compile_records) == 1 and object_provenance['compile_records'] == runtime_compile_records)
check('runtime_object_exact_compile_input', runtime_compile_records[0]['file'] == str(SOURCE/'tests/runtime_psqt_tests.cpp'))
check('runtime_object_exact_compile_output', 'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.obj' in runtime_compile_records[0]['command'])
pawn_object=BUILD/'CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.obj'
pawn_copy=HERE/'originals/objects/pawn_span_tests.cpp.obj'
pawn_provenance=load(HERE/'pawn-object-provenance.json')
pawn_records=[r for r in commands if r['file'].endswith('/tests/pawn_span_tests.cpp')]
check('pawn_actual_object_retained',pawn_object.read_bytes()==pawn_copy.read_bytes() and sha(pawn_object.read_bytes())==pawn_provenance['object_sha256'])
check('pawn_object_source_identity',pawn_provenance['pawn_test_source_sha256']==source_hashes['tests/pawn_span_tests.cpp'])
check('pawn_object_tested_pe_identity',pawn_provenance['tested_pe_sha256']==runtime['input_sha256_after']['forge_pawn_span_tests.exe'])
check('pawn_object_compile_identity',len(pawn_records)==1 and pawn_provenance['compile_records']==pawn_records and pawn_records[0]['file']==str(SOURCE/'tests/pawn_span_tests.cpp') and 'CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.obj' in pawn_records[0]['command'])
check('pawn_constexpr_count_recorded',pawn_provenance['constexpr_assertions']==3)
nearest_object=BUILD/'CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.obj'
nearest_copy=HERE/'originals/objects/nearest_pawn_tests.cpp.obj'
nearest_provenance=load(HERE/'nearest-object-provenance.json')
nearest_records=[r for r in commands if r['file'].endswith('/tests/nearest_pawn_tests.cpp')]
check('nearest_actual_object_retained',nearest_object.read_bytes()==nearest_copy.read_bytes() and sha(nearest_object.read_bytes())==nearest_provenance['object_sha256'])
check('nearest_object_source_identity',nearest_provenance['nearest_test_source_sha256']==source_hashes['tests/nearest_pawn_tests.cpp'])
check('nearest_object_tested_pe_identity',nearest_provenance['tested_pe_sha256']==runtime['input_sha256_after']['forge_nearest_pawn_tests.exe'])
check('nearest_object_compile_identity',len(nearest_records)==1 and nearest_provenance['compile_records']==nearest_records and nearest_records[0]['file']==str(SOURCE/'tests/nearest_pawn_tests.cpp') and 'CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.obj' in nearest_records[0]['command'])
check('nearest_constexpr_count_recorded',nearest_provenance['constexpr_assertions']==6)
for row in commands:
    text = row['command']
    check('strict_compiler_flags:' + row['file'], all(s in text for s in ['-march=znver5', '-mtune=znver5', '-O3', '-DNDEBUG', '-std=gnu++20', '-fno-fast-math', '-ffp-contract=off']) and '-ffast-math' not in text and '-flto' not in text)
link_record = (BUILD/'CMakeFiles/forge.dir/link.txt').read_text()
check('static_link_no_lto', '-static' in link_record and '-flto' not in link_record)
disassembly = (HERE/'runtime-attempt1/disassembly.log').read_text()
check('avx2_instructions', all(re.search(expr, disassembly) for expr in [r'v(?:max|min)ps[^\n]*ymm', r'vmulps[^\n]*ymm', r'vaddps[^\n]*ymm']))
pv_object=BUILD/'CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.obj'
pv_provenance=load(HERE/'pv-metadata-object-provenance.json')
pv_records=[r for r in commands if r['file'].endswith('/tests/pv_metadata_tests.cpp')]
check('pv_metadata_actual_object_retained',pv_object.read_bytes()==(HERE/'originals/objects/pv_metadata_tests.cpp.obj').read_bytes() and sha(pv_object.read_bytes())==pv_provenance['object_sha256'])
check('pv_metadata_object_source_identity',pv_provenance['pv_metadata_test_source_sha256']==source_hashes['tests/pv_metadata_tests.cpp'])
check('pv_metadata_object_tested_pe_identity',pv_provenance['tested_pe_sha256']==runtime['input_sha256_after']['forge_pv_metadata_tests.exe'])
check('pv_metadata_object_compile_identity',len(pv_records)==1 and pv_provenance['compile_records']==pv_records and pv_records[0]['file']==str(SOURCE/'tests/pv_metadata_tests.cpp') and 'CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.obj' in pv_records[0]['command'])
check('pv_metadata_assertion_count_recorded',pv_provenance['assertions']==56)
tt_object=BUILD/'CMakeFiles/forge_tt_tests.dir/tests/tt_coherence_tests.cpp.obj'
tt_provenance=load(HERE/'tt-object-provenance.json')
tt_records=[r for r in commands if r['file'].endswith('/tests/tt_coherence_tests.cpp')]
check('tt_actual_object_retained',tt_object.read_bytes()==(HERE/'originals/objects/tt_coherence_tests.cpp.obj').read_bytes() and sha(tt_object.read_bytes())==tt_provenance['object_sha256'])
check('tt_object_source_identity',tt_provenance['tt_test_source_sha256']==source_hashes['tests/tt_coherence_tests.cpp'])
check('tt_object_tested_pe_identity',tt_provenance['tested_pe_sha256']==runtime['input_sha256_after']['forge_tt_tests.exe'])
check('tt_object_compile_identity',len(tt_records)==1 and tt_provenance['compile_records']==tt_records and tt_records[0]['file']==str(SOURCE/'tests/tt_coherence_tests.cpp') and 'CMakeFiles/forge_tt_tests.dir/tests/tt_coherence_tests.cpp.obj' in tt_records[0]['command'])
check('tt_twelve_groups_recorded',tt_provenance['groups']==12)
check('no_fused_operations', re.search(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b', disassembly) is None)
check('output_layer_checker_rc0', load(HERE/'output-layer-checker.json')['exit_code'] == 0)
before = load(HERE/'parent6422-preservation-before.json')
check('parent22_preservation_inventory', len(before) == load(HERE/'PROTOCOL.json')['preserved_parent_files'])
for name, digest in before.items():
    check('parent_preserved:' + name, sha(Path(name).read_bytes()) == digest)
crlf_logs = [p.name for p in (HERE/'runtime-attempt1').glob('*stdout.log') if b'\r\n' in p.read_bytes()]
check('wine_original_crlf_retained', bool(crlf_logs))
provenance = load(PACKAGE/'provenance.json')
check('embedded_bench_freeze_provenance', provenance['bench_signature_freeze'] == freeze)
readme = (PACKAGE/'README.txt').read_text()
check('honest_claim_flags', provenance['native_windows_tested'] is False and provenance['physical_ryzen_tested'] is False and provenance['accepted_elo_gain'] is None and provenance['stockfish_superiority_proven'] is False and provenance['new_nps_measurement'] is False)
claim_text = ' '.join(readme.lower().split())
check('readme_scope', all(term in claim_text for term in ('no measured','speed','nps','elo improvement','native windows/physical ryzen','stockfish superiority','is established')))
check('pv_metadata_scope_honest', provenance.get('board_nnue_network_replacement_unchanged') is True and provenance.get('evaluation_implementation_changed') is False and provenance.get('intended_eval_search_parity') is False and provenance.get('intended_evaluation_parity') is True and 'evaluation_network_replacement_unchanged' not in provenance)
check('tt_refresh_policy_scope_explicit',all(term in provenance.get('search_policy_change','').lower() for term in ('tt occupied-hit generation refresh','coupled replacement/admission/hashfull policy trial','intentional search change','unchanged evaluation','native correctness and sanitizer evidence remain separate')))
check('native_gates_separate_explicit', re.search(r'native\s*23 gates',claim_text) is not None and all(term in claim_text for term in ('reported separately',)))
check('unaccepted_candidate_explicit', 'this is an unaccepted candidate' in claim_text)
check('parent16_original_tsan_failure_qualified', all(term in claim_text for term in ('6.4.16','tsan')) and re.search(r'failed\s*8/9',claim_text) is not None and 'FAILED 8/9' in provenance['native_gate_status'])
check('strength_acceptance_not_inherited', provenance.get('search_change_accepted') is False and provenance.get('known_bug_repair') is False and provenance.get('coupled_tt_policy_trial') is True)
check('implementation_changes_declared', all(term in claim_text for term in ('search.cpp, existing tt tests and version metadata change','board, nnue source/headers/weights','all other tests remain unchanged')))
check('all_five_test_objects_declared','runtime/pawn/nearest/pv metadata/tt test objects' in claim_text)
check('first_capture_signature_not_speed_claim','first normal candidate capture' in provenance['bench_scope'].lower() and 'no time/nps comparison' in provenance['bench_scope'].lower())

report = {'status':'passed', 'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'auditor':'prepared read-only Windows23 artifact auditor; runtime invocation recorded separately', 'source_and_tests_commit':COMMIT, 'parent_source_commit':PARENT, 'engine_execution_during_audit':False, 'new_build_during_audit':False, 'check_count':len(checks), 'checks':checks, 'declared_export_changes':sorted(changed_all), 'bench_policy':'First normal candidate23 signature captured once and frozen before packaging; intended search change, no parent/Linux assumption or timing/NPS/Elo inference', 'bench_signature_freeze':freeze, 'native_gate_status_not_asserted':True, 'parent16_original_tsan_failure_qualification_retained':True, 'bench11_nodes':runtime['bench11_nodes'], 'tt_groups':12,'tt_object_sha256':tt_provenance['object_sha256'],'pv_metadata_assertions':56,'pv_metadata_failures':0,'pv_metadata_object_sha256':pv_provenance['object_sha256'],'correction_history_checks':correction_checks, 'correction_history_failures':0, 'nearest_pawn_checks':791680,'nearest_pawn_sets':395840,'nearest_pawn_failures':0,'nearest_constexpr_assertions':6,'nearest_object_sha256':nearest_provenance['object_sha256'],'pawn_span_checks':37320,'pawn_span_failures':0,'pawn_constexpr_assertions':3,'pawn_object_sha256':pawn_provenance['object_sha256'],'runtime_psqt_checks':347, 'runtime_psqt_failures':0, 'runtime_object_sha256':object_provenance['object_sha256'], 'source_files':len(source_hashes), 'release_members':release_members, 'release_sha_entries':len(sums), 'artifact':str(ARCHIVE.relative_to(ROOT)), 'artifact_bytes':ARCHIVE.stat().st_size, 'artifact_sha256':sha(ARCHIVE.read_bytes()), 'raw_files':len(manifest), 'raw_members':len(manifest)+1, 'raw_sha256':sha(raw.read_bytes()), 'raw_bytes':raw.stat().st_size, 'engine_sha256':runtime['input_sha256_after']['forge.exe'], 'core_sha256':runtime['input_sha256_after']['core_library'], 'pe_imports':imports, 'parent_preserved_files':len(before), 'crlf_stdout_logs':crlf_logs, 'scope':'Bounded Windows/Wine correctness and artifact provenance. No speed, NPS, Elo, native Windows, physical Ryzen or Stockfish superiority result.'}
(HERE/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(HERE/'independent-audit.md').write_text(f'''# Independent Windows 6.4.23 artifact audit

All **{len(checks)} checks passed** for source `{COMMIT}`, parent `{PARENT}`.
No engine or rebuild ran. All {len(source_hashes)} source files match frozen Git
and the root proof whose byte hash is explicitly pinned to root authorization.
The four changes are CMake/UCI metadata, search.cpp and extended TT tests;
all other tests, Board, NNUE, evaluation and evaluation parameters are unchanged.

The ZIP has {release_members} safe verified members and {len(sums)} checksum entries.
All eleven built and ten shipped PEs match tested bytes and system-CRT AMD64 PE32+
requirements. Core and all runtime/pawn/nearest/PV metadata/TT object/source/PE/compile identities
match originals. All {len(manifest)} raw files and {len(before)} protected Windows 22
files retain exact bytes/hashes, including original CRLF stream bytes.

Thirteen Wine checks passed with 791680 nearest comparisons across 395840 sets,
six nearest constexpr assertions, 37320 pawn-span/three constexpr assertions,
56 PV metadata assertions, 347 runtime PSQT, 54 correction, 12 TT groups, rule50, 18947 legal comparisons,
UCI/ponder, 5 OwnBook transitions and first normal candidate signature {runtime['bench11_nodes']}. Strict
Zen5 C++20 Release/static j1/noLTO/noFMA and AVX2 records agree with provenance.

ZIP SHA256: `{report['artifact_sha256']}`.
Engine SHA256: `{report['engine_sha256']}`.
Raw SHA256: `{report['raw_sha256']}`.

This is bounded Windows/Wine artifact correctness only. Native 23 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No 23 speed, NPS,
Elo, native Windows/physical Ryzen or Stockfish superiority result is established.
''')

print(json.dumps({k:report[k] for k in ['status','check_count','source_files','release_members','release_sha_entries','raw_files','artifact_sha256','engine_sha256','parent_preserved_files']},indent=2))
