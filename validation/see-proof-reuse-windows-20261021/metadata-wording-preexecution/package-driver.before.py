from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile

REPO = Path('/workspace/dwqww')
from pipeline_gate import load_freeze
FREEZE=load_freeze()
COMMIT = FREEZE['source_commit']
PARENT = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
SOURCE = Path('/workspace/.cloud-setup/windows6424-source')
BUILD = Path('/workspace/.cloud-setup/windows6424-build')
OUT = REPO / 'validation/see-proof-reuse-windows-20261021'
PACKAGE = REPO / 'releases/forge-6.4.24-candidate-windows-zen5'
ARCHIVE = PACKAGE.with_name(PACKAGE.name + '.zip')
TOOLS = Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

assert load(OUT/'WINDOWS-BUILD-CLEAR.json')['authorization']=='24 WINDOWS BUILD CLEAR'
assert not PACKAGE.exists() and not ARCHIVE.exists()
runtime = load(OUT / 'runtime-attempt1/result.json')
build = load(OUT / 'result.json')
assert runtime['status'] == 'passed' and build['status'] == 'build_passed'
assert runtime['source_and_tests_commit'] == build['source_and_tests_commit'] == COMMIT
assert len(runtime['checks']) == 13 and all(c['exit_code'] == 0 for c in runtime['checks'])
assert runtime['tt_groups']==FREEZE['tt_groups']==12
assert runtime['correction_history_checks'] == 54 and runtime['correction_history_failures'] == 0
assert runtime['runtime_psqt_checks'] == FREEZE['runtime_summary_checks'] and runtime['runtime_psqt_failures'] == 0
assert runtime['pawn_span_checks'] == FREEZE['pawn_span_checks'] == 37320 and runtime['pawn_span_failures'] == 0
assert runtime['nearest_pawn_checks']==FREEZE['nearest_pawn_checks']==791680 and runtime['nearest_pawn_sets']==FREEZE['nearest_pawn_sets']==395840 and runtime['nearest_pawn_failures']==0
assert runtime['legal_witness_comparisons'] == 18947 and type(runtime['bench11_nodes']) is int and runtime['bench11_nodes']>0
assert runtime['pv_metadata_assertions']==FREEZE['pv_metadata_assertions']==56 and runtime['pv_metadata_failures']==0
assert FREEZE['bench_expected_nodes'] is None
assert runtime['bench11_nodes']==FREEZE['parent_bench_parity_nodes']==334752
assert runtime['see_threshold_assertions']==FREEZE['see_threshold_assertions']==504 and runtime['see_threshold_failures']==0
assert runtime['input_sha256_before'] == runtime['input_sha256_after']
assert len(runtime['ownbook_transitions']) == 5 and all(t['PASS'] for t in runtime['ownbook_transitions'])

freeze=load(OUT/'BENCH-SIGNATURE-FREEZE.json')
assert freeze['source_and_tests_commit']==COMMIT and freeze['bench11_nodes']==runtime['bench11_nodes']
assert freeze['engine_sha256']==sha(BUILD/'forge.exe')==runtime['input_sha256_after']['forge.exe']
assert freeze['raw_bench_stdout_sha256']==sha(OUT/'runtime-attempt1/bench-stdout.log')
assert freeze['raw_bench_stdin_sha256']==sha(OUT/'runtime-attempt1/bench-stdin.txt')
assert freeze['runtime_result_sha256']==sha(OUT/'runtime-attempt1/result.json')
assert freeze['hash_mib']==16 and freeze['threads']==1
assert freeze['native_independent'] is True

source_hashes = load(OUT / 'source-hashes.json')
assert {p.relative_to(SOURCE).as_posix(): sha(p) for p in SOURCE.rglob('*') if p.is_file()} == source_hashes
for name, digest in source_hashes.items():
    assert hashlib.sha256(subprocess.check_output(['git', '-C', str(REPO), 'show', COMMIT + ':' + name])).hexdigest() == digest
parent_hashes = load(REPO / 'validation/tt-refresh-windows-20261021/source-hashes.json')
production = load(OUT / 'production-hashes.json')
changed_production = sorted(name for name, digest in production.items() if parent_hashes.get(name) != digest)
assert changed_production == ['CMakeLists.txt','src/search.cpp','src/uci.cpp']
assert sorted(name for name,h in source_hashes.items() if parent_hashes.get(name)!=h)==['CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tests.cpp']
assert all(parent_hashes[name]==h for name,h in load(OUT/'test-hashes.json').items() if name!='tests/tests.cpp')
unchanged_names = ['src/nnue.cpp','src/nnue_weights.inc','include/forge/nnue.hpp','src/board.cpp','include/forge/board.hpp','src/eval_params.cpp','src/eval_params_table.inc','include/forge/eval_params.hpp','include/forge/eval.hpp','include/forge/search.hpp','src/eval.cpp','include/forge/bitboard.hpp']
nnue = {'candidate_source_commit': COMMIT, 'parent_source_commit': PARENT,
        'changed_production_files': changed_production,
        'unchanged_source_guards': {name: {'candidate_sha256': source_hashes[name], 'parent_sha256': parent_hashes[name],
                                         'identical': source_hashes[name] == parent_hashes[name]} for name in unchanged_names},
        'network_sha256': source_hashes['src/nnue_weights.inc'],
        'new_snapshot_differential_run': False,
        'reason': 'Pure SEE proof reuse optimization in the unchanged Board scope, with actual threshold <= 0 guard and defined arithmetic. Only search.cpp, existing core tests and version metadata change; Board, NNUE source/weights, unchanged evaluation, parameters and other tests match23. Exact search parity expected; no24 speed or Elo result.',
        'inherited_differential_evidence': 'validation/nnue-capture-fusion-20261019/windows/differential-attempt1/result.json'}
assert all(record['identical'] for record in nnue['unchanged_source_guards'].values())
write(OUT / 'nnue-parent-identity.json', nnue)

checker_command = [sys.executable, str(SOURCE / 'tools/check_nnue_simd.py'), str(BUILD / 'forge.exe')]
with (OUT / 'output-layer-checker.stdout.log').open('x') as stdout, (OUT / 'output-layer-checker.stderr.log').open('x') as stderr:
    checked = subprocess.run(checker_command, stdout=stdout, stderr=stderr)
assert checked.returncode == 0
write(OUT / 'output-layer-checker.json', {'command': checker_command, 'exit_code': checked.returncode,
      'checker_sha256': sha(SOURCE / 'tools/check_nnue_simd.py'), 'engine_sha256': sha(BUILD / 'forge.exe'),
      'scope': 'Existing output-layer 256-bit checker; no output-layer source changes.'})

pe_records = {}
for binary in sorted(BUILD.glob('*.exe')):
    command = [str(TOOLS / 'llvm-readobj'), '--file-headers', '--coff-imports', str(binary)]
    output = subprocess.check_output(command, text=True)
    imports = re.findall(r'^  Name: (.+)$', output, re.M)
    assert 'Machine: IMAGE_FILE_MACHINE_AMD64' in output and 'AddressSize: 64bit' in output
    assert imports and all(name.lower() == 'kernel32.dll' or name.lower().startswith('api-ms-win-crt-') for name in imports), imports
    pe_records[binary.name] = {'command': command, 'sha256': sha(binary), 'architecture': 'AMD64',
                               'imports': imports, 'system_or_ucrt_imports_only': True}
    (OUT / (binary.name + '-pe-headers-imports.txt')).write_text(output)
write(OUT / 'pe-validation.json', pe_records)

compile_commands = load(OUT / 'compile_commands.json')
for record in compile_commands:
    command = record['command']
    assert all(flag in command for flag in ['-march=znver5', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-O3', '-DNDEBUG', '-std=gnu++20'])
assert '-static' in (BUILD / 'CMakeFiles/forge.dir/link.txt').read_text()
assert all('-flto' not in row['command'] and '-ffast-math' not in row['command'] for row in compile_commands)
assert '-flto' not in (BUILD / 'CMakeFiles/forge.dir/link.txt').read_text()
write(OUT / 'compile-contract.json', {'status': 'passed', 'compilation_records': len(compile_commands),
      'flags': ['-march=znver5', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-O3', '-DNDEBUG', '-std=gnu++20'],
      'static_link': True, 'lto':False, 'parallel_jobs': 1})

environment = __import__('os').environ.copy()
environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready', WINEDEBUG='-all')
wine_command = ['/workspace/.cloud-setup/wine/usr/lib/wine/wine64', '--version']
wine_version = subprocess.check_output(wine_command, env=environment, text=True).strip()
(OUT / 'wine-version.txt').write_text(wine_version + '\n')
write(OUT / 'ownbook-adaptation-provenance.json', {
      'frozen_source_commit': COMMIT, 'source_ownbook_tool_sha256': sha(SOURCE / 'tools/ownbook_regression.py'),
      'adapter_sha256': sha(OUT / 'runtime-attempt1/ownbook-wine-regression.py'),
      'adapter_changes': 'Only import root and Linux tempfile book path to existing Wine Z: mapping; all assertions/five transitions retained.',
      'test_harness_engine_field': 'Harness engine hash identifies the immutable Wine wrapper; actual PE hash is recorded separately.',
      'wrapper_path': str(OUT / 'forge-see-proof-reuse-wine'), 'wrapper_sha256': sha(OUT / 'forge-see-proof-reuse-wine'),
      'actual_windows_engine': str(BUILD / 'forge.exe'), 'actual_windows_engine_sha256': sha(BUILD / 'forge.exe'),
      'transitions': runtime['ownbook_transitions'], 'scope': 'Wine correctness only; no speed/NPS/Elo/native-hardware claim'})

preserved_before = load(OUT / 'parent6423-preservation-before.json')
preserved_after = {name: sha(Path(name)) for name in preserved_before}
assert preserved_before == preserved_after
write(OUT / 'parent6423-preservation-check.json', {'status': 'unchanged', 'files': len(preserved_before),
      'input_sha256_before': preserved_before, 'input_sha256_after': preserved_after})

originals = OUT / 'originals'
assert not originals.exists()
(originals / 'binaries').mkdir(parents=True)
(originals / 'static-core').mkdir()
for p in sorted(BUILD.glob('*.exe')):
    assert sha(p) == runtime['input_sha256_after'][p.name]
    shutil.copyfile(p, originals / 'binaries' / p.name)
shutil.copyfile(BUILD / 'libforge_core.a', originals / 'static-core/libforge_core.a')
runtime_object=BUILD/'CMakeFiles/forge_runtime_psqt_tests.dir/tests/runtime_psqt_tests.cpp.obj'
assert runtime_object.is_file()
(originals/'objects').mkdir()
shutil.copyfile(runtime_object,originals/'objects/runtime_psqt_tests.cpp.obj')
assert sha(runtime_object)==sha(originals/'objects/runtime_psqt_tests.cpp.obj')
write(OUT/'runtime-object-provenance.json',{'object_sha256':sha(runtime_object),'runtime_test_source_sha256':source_hashes['tests/runtime_psqt_tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_runtime_psqt_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/runtime_psqt_tests.cpp')],'scope':'Actual runtime test object/source/PE identity; no independent native result'})
pawn_object=BUILD/'CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.obj'
assert pawn_object.is_file()
shutil.copyfile(pawn_object,originals/'objects/pawn_span_tests.cpp.obj')
assert sha(pawn_object)==sha(originals/'objects/pawn_span_tests.cpp.obj')
write(OUT/'pawn-object-provenance.json',{'object_sha256':sha(pawn_object),'pawn_test_source_sha256':source_hashes['tests/pawn_span_tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_pawn_span_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/pawn_span_tests.cpp')],'constexpr_assertions':3,'scope':'Actual pawn test object/source/testedPE identity; no independent native or speed result'})
nearest_object=BUILD/'CMakeFiles/forge_nearest_pawn_tests.dir/tests/nearest_pawn_tests.cpp.obj'
assert nearest_object.is_file()
shutil.copyfile(nearest_object,originals/'objects/nearest_pawn_tests.cpp.obj')
assert sha(nearest_object)==sha(originals/'objects/nearest_pawn_tests.cpp.obj')
write(OUT/'nearest-object-provenance.json',{'object_sha256':sha(nearest_object),'nearest_test_source_sha256':source_hashes['tests/nearest_pawn_tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_nearest_pawn_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/nearest_pawn_tests.cpp')],'constexpr_assertions':6,'scope':'Actual nearest-pawn object/source/testedPE identity only; no native or speed inference'})
pv_object=BUILD/'CMakeFiles/forge_pv_metadata_tests.dir/tests/pv_metadata_tests.cpp.obj'
assert pv_object.is_file()
shutil.copyfile(pv_object,originals/'objects/pv_metadata_tests.cpp.obj')
assert sha(pv_object)==sha(originals/'objects/pv_metadata_tests.cpp.obj')
write(OUT/'pv-metadata-object-provenance.json',{'object_sha256':sha(pv_object),'pv_metadata_test_source_sha256':source_hashes['tests/pv_metadata_tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_pv_metadata_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/pv_metadata_tests.cpp')],'assertions':56,'scope':'Actual PV metadata test object/source/testedPE identity; native and strength gates separate'})
tt_object=BUILD/'CMakeFiles/forge_tt_tests.dir/tests/tt_coherence_tests.cpp.obj'
assert tt_object.is_file()
shutil.copyfile(tt_object,originals/'objects/tt_coherence_tests.cpp.obj')
assert sha(tt_object)==sha(originals/'objects/tt_coherence_tests.cpp.obj')
write(OUT/'tt-object-provenance.json',{'object_sha256':sha(tt_object),'tt_test_source_sha256':source_hashes['tests/tt_coherence_tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_tt_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/tt_coherence_tests.cpp')],'groups':12,'scope':'Actual TT test object/source/testedPE identity only; no cross-build raw object bit-identity claim'})
core_test_object=BUILD/'CMakeFiles/forge_tests.dir/tests/tests.cpp.obj'
assert core_test_object.is_file()
shutil.copyfile(core_test_object,originals/'objects/tests.cpp.obj')
assert sha(core_test_object)==sha(originals/'objects/tests.cpp.obj')
write(OUT/'see-threshold-object-provenance.json',{'object_sha256':sha(core_test_object),'core_test_source_sha256':source_hashes['tests/tests.cpp'],'tested_pe_sha256':sha(BUILD/'forge_tests.exe'),'compile_records':[r for r in load(OUT/'compile_commands.json') if r['file'].endswith('/tests/tests.cpp')],'assertions':504,'scope':'Actual core SEE threshold-contract object/source/testedPE identity; not a new native or speed result'})
assert sha(originals / 'static-core/libforge_core.a') == runtime['input_sha256_after']['core_library']
shutil.copytree(SOURCE, originals / 'frozen-source')
write(OUT / 'README-checks.json', {'status': 'passed', 'source_and_tests_commit': COMMIT,
      'wine_functional_and_signature_checks': runtime['checks'], 'simd': runtime['simd'],
      'output_layer_checker_exit_code': checked.returncode, 'tt_groups': 12, 'see_threshold_assertions':runtime['see_threshold_assertions'],'see_threshold_failures':0,'pv_metadata_assertions':runtime['pv_metadata_assertions'],'pv_metadata_failures':0,'nearest_pawn_checks':runtime['nearest_pawn_checks'],'nearest_pawn_sets':runtime['nearest_pawn_sets'],'nearest_pawn_failures':0,'nearest_constexpr_assertions':6,'pawn_span_checks':runtime['pawn_span_checks'],'pawn_span_failures':0,'pawn_constexpr_assertions':3, 'runtime_psqt_checks':runtime['runtime_psqt_checks'],'runtime_psqt_failures':0,'correction_history_checks':runtime['correction_history_checks'], 'correction_history_failures':0, 'rule50_targeted_failures': 0,
      'legal_witness_comparisons': 18947, 'ownbook_transitions': 5, 'bench11_nodes': runtime['bench11_nodes'],
      'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
      'new_nps_measurement': False, 'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging',
      'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging'})
(OUT / 'README.md').write_text(f'''# Frozen Forge 6.4.24 Windows correctness evidence

Source/tests `{COMMIT}`, parent `{PARENT}` (6.4.23).
Strict static LLVM-MinGW 23.1.3 Zen5 C++20 Release, j1, no FMA/LTO/fast-math.
Thirteen Wine checks passed: core/perft and 504 SEE threshold assertions, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and {runtime['nearest_pawn_checks']:,} nearest-pawn comparisons
across {runtime['nearest_pawn_sets']:,} sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature {runtime['bench11_nodes']}.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
Pure SEE proof reuse optimization preserves exact search behavior and unchanged evaluation.
Reuse is guarded by actual threshold <= 0 and defined arithmetic in the unchanged Board scope.
Only search.cpp, existing core tests and version metadata change; Board, NNUE,
evaluation, parameters and other tests remain unchanged.
Native 24 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
All actual PEs/core, runtime/pawn/nearest/PV metadata/TT objects, source, commands and logs remain.
No new 24 speed, NPS, Elo, native Windows/Ryzen or Stockfish claim follows.
''')

# Snapshot every original Windows record before creating the archive metadata.
raw_files = sorted(p for p in OUT.rglob('*') if p.is_file())
raw_manifest = {p.relative_to(OUT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in raw_files}
write(OUT / 'windows-originals-SHA256.json', raw_manifest)
raw_archive = OUT / 'windows-originals.zip'
with zipfile.ZipFile(raw_archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in raw_files:
        z.write(p, p.relative_to(OUT).as_posix())
    z.write(OUT / 'windows-originals-SHA256.json', 'windows-originals-SHA256.json')
with zipfile.ZipFile(raw_archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(set(z.namelist())) == len(raw_files) + 1
    assert set(z.namelist()) == set(raw_manifest) | {'windows-originals-SHA256.json'}
    for name, item in raw_manifest.items():
        assert z.read(name) == (OUT / name).read_bytes()
        assert hashlib.sha256(z.read(name)).hexdigest() == item['sha256']
write(OUT / 'windows-originals-verification.json', {'status': 'passed', 'archive': str(raw_archive.relative_to(REPO)),
      'sha256': sha(raw_archive), 'bytes': raw_archive.stat().st_size, 'original_files': len(raw_files),
      'manifest_files': len(raw_manifest), 'crc': 'passed', 'all_original_bytes_and_sha256_equal': True,
      'originals_retained': True, 'scope': 'All original Windows validation, core, executable, frozen-source and log records at packaging; audit/report outputs follow separately.'})

PACKAGE.mkdir()
members = {'forge.exe': 'forge-6.4.24-ryzen-9850x3d.exe', 'forge_tests.exe': 'forge_tests.exe',
           'forge_tt_tests.exe': 'forge_tt_tests.exe', 'forge_rule50_tests.exe': 'forge_rule50_tests.exe',
           'forge_legal_witness_tests.exe': 'forge_legal_witness_tests.exe',
           'forge_correction_history_tests.exe': 'forge_correction_history_tests.exe',
           'forge_runtime_psqt_tests.exe': 'forge_runtime_psqt_tests.exe',
           'forge_pawn_span_tests.exe': 'forge_pawn_span_tests.exe',
           'forge_nearest_pawn_tests.exe': 'forge_nearest_pawn_tests.exe',
           'forge_pv_metadata_tests.exe': 'forge_pv_metadata_tests.exe'}
for source, name in members.items():
    shutil.copyfile(BUILD / source, PACKAGE / name)
for source, name in [(SOURCE / 'LICENSE', 'LICENSE'), (OUT / 'production-hashes.json', 'source-hashes.json'),
                     (OUT / 'test-hashes.json', 'test-hashes.json'),
                     (SOURCE / 'tests/legal_witness_fixtures.tsv', 'legal_witness_fixtures.tsv'),
                     (SOURCE / 'tools/openings/forge-10000.epd', 'forge-10000.epd'),
                     (raw_archive, raw_archive.name), (OUT / 'windows-originals-SHA256.json', 'windows-originals-SHA256.json'),
                     (OUT / 'windows-originals-verification.json', 'windows-originals-verification.json'),
                     (OUT / 'README-checks.json', 'README-checks.json'),
                     (OUT / 'nnue-parent-identity.json', 'nnue-parent-identity.json')]:
    shutil.copyfile(source, PACKAGE / name)
provenance = {
    'engine_version': '6.4.24 candidate', 'source_and_tests_commit': COMMIT, 'parent_source_commit': PARENT,
    'source_url': 'https://github.com/couns0538-sketch/dwqww/tree/' + COMMIT,
    'production_source_sha256': production, 'test_source_sha256': load(OUT / 'test-hashes.json'),
    'compiler': build['compiler'], 'flags': 'C++20 Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
    'target': 'Windows x64 Ryzen 7 9850X3D / Zen5', 'parallel_build_jobs': 1,
    'inherited_tt_policy': 'Explicit UCI go/bench exclusive request for exactly one worker, one coarse gate plus atomic request plus sequential 1024-stripe drain, table-bound lexical owner TLS bypass; default library/SMP callers retain shared stripes.',
    'lifecycle_limit': 'Clear, resize, new_search and destruction still require all accessors quiescent; foreign entry-call safety assumes stable storage/generation. Arbitrary concurrent lifecycle operations unsupported.',
    'whole_nnue_object_raw_identity_claimed':False, 'board_nnue_network_replacement_unchanged': True, 'evaluation_implementation_changed':False, 'intended_eval_search_parity':True, 'intended_evaluation_parity':True,'search_change_accepted':False, 'known_bug_repair':False,'coupled_tt_policy_trial':False,'pure_see_proof_reuse':True,
    'native_gate_status':'Separate candidate24 native gates; Windows packaging alone does not accept this candidate or establish release readiness. Original 6.4.16 TSan suite FAILED 8/9; its separate five-case OwnBook diagnostic remains finite coverage only.',
    'prior_6414_native_bench_output_anomaly':'Remains qualified in validation/double-extension-path-20261020/native6414; this Windows evidence does not resolve it.',
    'search_policy_change': 'Pure SEE proof reuse optimization in the unchanged Board scope, with actual threshold <= 0 guard and defined arithmetic. Exact search parity and unchanged evaluation intended; no accepted speed or Elo claim. Native correctness and sanitizer evidence remain separate.',
    'inherited_clock_policy': 'Finite timed UCI admission accounting; unset untimed/infinite/ponder origins are worker-local; start_time authoritative, request_start supported, ponder budget begins at hit.', 'nnue_parent_identity': nnue,
    'entry_bytes': 16, 'cluster_bytes': 64,
    'inherited_halfmove_policy': 'Both capped clocks below90 or exact capped match (cap100); old main-search current-clock<90 guard retained. This remains a heuristic, not universal history correctness.',
    'wine_version': wine_version, 'wine_checks': runtime['checks'], 'tt_groups': 12, 'see_threshold_assertions':runtime['see_threshold_assertions'],'see_threshold_failures':0,'pv_metadata_assertions':runtime['pv_metadata_assertions'],'pv_metadata_failures':0,'nearest_pawn_checks':runtime['nearest_pawn_checks'],'nearest_pawn_sets':runtime['nearest_pawn_sets'],'nearest_pawn_failures':0,'nearest_constexpr_assertions':6,'pawn_span_checks':runtime['pawn_span_checks'],'pawn_span_failures':0,'pawn_constexpr_assertions':3, 'runtime_psqt_checks':runtime['runtime_psqt_checks'],'runtime_psqt_failures':0,'correction_history_checks':runtime['correction_history_checks'], 'correction_history_failures':0,
    'legal_witness_comparisons': 18947, 'ownbook_transitions': runtime['ownbook_transitions'],
    'bench11_nodes': runtime['bench11_nodes'], 'bench_signature_freeze':freeze, 'bench_signature_freeze_sha256':sha(OUT/'BENCH-SIGNATURE-FREEZE.json'), 'bench_scope': 'Hash16MiB/Threads1 first actual candidate capture matches parent23 same-platform334752; pure optimization, no time/NPS comparison',
    'simd': runtime['simd'], 'output_layer_checker_exit_code': checked.returncode,
    'source_binary_and_tool_hashes_unchanged': True, 'static_libraries': build['libraries'],
    'binaries': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in PACKAGE.glob('*.exe')},
    'raw_windows_evidence_archive': raw_archive.name, 'raw_windows_evidence_sha256': sha(raw_archive),
    'raw_windows_evidence_file_count': len(raw_files), 'raw_windows_originals_retained': True,
    'evidence_directory': 'validation/see-proof-reuse-windows-20261021/',
    'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging', 'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging',
    'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
    'stockfish_superiority_proven': False, 'new_nps_measurement': False,
    'performance_claim': 'No throughput, NPS, timed match, Elo or native hardware measurement performed.',
    'compile_flags_record': (BUILD / 'CMakeFiles/forge_core.dir/flags.make').read_text(),
    'link_record': (BUILD / 'CMakeFiles/forge.dir/link.txt').read_text(),
}
write(PACKAGE / 'provenance.json', provenance)
(PACKAGE / 'README.txt').write_text(f'''Forge 6.4.24 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.24-ryzen-9850x3d.exe as a UCI engine.
Source/tests {COMMIT}; parent {PARENT} (6.4.23).

Pure SEE proof reuse avoids repeated exchange queries already established by
Main GoodCaptures in the unchanged Board scope. Reuse has an actual threshold <= 0
guard and defined arithmetic; exact search parity and unchanged evaluation are intended.
Only search.cpp, existing core tests and version metadata change. Board, NNUE
source/headers/weights, evaluation and evaluation parameters and other tests remain
unchanged; TT refresh and the accepted PV metadata fix are retained.

Thirteen Wine checks passed: core/perft and 504 SEE threshold assertions, 56 PV metadata assertions, 54 correction-history, 347 runtime PSQT,
37,320 pawn-span and {runtime['nearest_pawn_checks']:,} nearest-pawn comparisons
across {runtime['nearest_pawn_sets']:,} sets; twelve TT groups, rule50, 18,947 legal
witnesses, UCI/ponder, five OwnBook transitions and first-capture candidate signature {runtime['bench11_nodes']}.
Three pawn-span and six nearest-pawn constexpr assertions compiled.
AVX2 output-layer checks passed with no fused operations. Strict LLVM-MinGW 23.1.3
Zen5 C++20 Release/static, j1, no FMA/LTO/fast-math. All eleven built PEs, actual core,
runtime/pawn/nearest/PV metadata/TT test objects, frozen source and original commands/streams/logs
remain in verified windows-originals.zip.

This is an unaccepted candidate. Native 24 gates and differential checks are
reported separately. Original 6.4.16 TSan FAILED 8/9 remains qualified. No measured
24 speed, NPS or Elo improvement, native Windows/physical Ryzen testing, or
Stockfish superiority is established. Parent 23 performance does not validate 24.

Optional tests: forge_tests.exe; forge_correction_history_tests.exe;
forge_runtime_psqt_tests.exe; forge_pawn_span_tests.exe; forge_nearest_pawn_tests.exe; forge_pv_metadata_tests.exe;
forge_tt_tests.exe; forge_rule50_tests.exe; forge_legal_witness_tests.exe
legal_witness_fixtures.tsv forge-10000.epd. See provenance.json, source/test hashes,
nnue-parent-identity.json, windows-originals-SHA256.json and SHA256SUMS.
''')

(PACKAGE / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(PACKAGE.iterdir()) if p.is_file()))
with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(PACKAGE.iterdir()):
        z.write(p, PACKAGE.name + '/' + p.name)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(set(z.namelist())) == len(list(PACKAGE.iterdir()))
    assert set(z.namelist()) == {PACKAGE.name + '/' + p.name for p in PACKAGE.iterdir()}
    for p in PACKAGE.iterdir():
        assert z.read(PACKAGE.name + '/' + p.name) == p.read_bytes()
    for line in (PACKAGE / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert hashlib.sha256(z.read(PACKAGE.name + '/' + name)).hexdigest() == expected
    for source, name in members.items():
        assert hashlib.sha256(z.read(PACKAGE.name + '/' + name)).hexdigest() == runtime['input_sha256_after'][source]
assert {name: sha(Path(name)) for name in preserved_before} == preserved_before
report = {'status': 'packaged_and_verified', 'artifact': str(ARCHIVE.relative_to(REPO)),
          'sha256': sha(ARCHIVE), 'bytes': ARCHIVE.stat().st_size, 'source_and_tests_commit': COMMIT,
          'engine_sha256': sha(PACKAGE / 'forge-6.4.24-ryzen-9850x3d.exe'),
          'core_sha256': sha(BUILD / 'libforge_core.a'), 'runtime_checks': 13, 'ownbook_transitions': 5,
          'legal_witness_comparisons': 18947, 'bench11_nodes': runtime['bench11_nodes'],
          'raw_archive': str(raw_archive.relative_to(REPO)), 'raw_archive_sha256': sha(raw_archive),
          'raw_original_files': len(raw_files), 'all_archived_original_bytes_sha256_verified': True,
          'scope': 'Wine correctness and bounded node signature; no NPS, Elo or native hardware result',
          'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging', 'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging'}
write(OUT / 'artifact.json', report)
print(json.dumps(report, indent=2))
