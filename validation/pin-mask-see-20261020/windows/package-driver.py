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
COMMIT = '553caef144ae2e1b696ba35d7a0eb1a50a03fde9'
PARENT = '8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad'
SOURCE = Path('/workspace/.cloud-setup/forge-pin-mask-windows-source')
BUILD = Path('/workspace/.cloud-setup/forge-pin-mask-windows-build')
OUT = REPO / 'validation/pin-mask-see-20261020/windows'
PACKAGE = REPO / 'releases/forge-6.4.16-candidate-windows-zen5'
ARCHIVE = PACKAGE.with_name(PACKAGE.name + '.zip')
TOOLS = Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

assert not PACKAGE.exists() and not ARCHIVE.exists()
runtime = load(OUT / 'runtime-attempt1/result.json')
build = load(OUT / 'result.json')
assert runtime['status'] == 'passed' and build['status'] == 'build_passed'
assert runtime['source_and_tests_commit'] == build['source_and_tests_commit'] == COMMIT
assert len(runtime['checks']) == 8 and all(c['exit_code'] == 0 for c in runtime['checks'])
assert runtime['legal_witness_comparisons'] == 18947 and runtime['bench11_nodes'] == 382424
assert runtime['input_sha256_before'] == runtime['input_sha256_after']
assert len(runtime['ownbook_transitions']) == 5 and all(t['PASS'] for t in runtime['ownbook_transitions'])

source_hashes = load(OUT / 'source-hashes.json')
assert {p.relative_to(SOURCE).as_posix(): sha(p) for p in SOURCE.rglob('*') if p.is_file()} == source_hashes
for name, digest in source_hashes.items():
    assert hashlib.sha256(subprocess.check_output(['git', '-C', str(REPO), 'show', COMMIT + ':' + name])).hexdigest() == digest
parent_hashes = load(REPO / 'validation/pin-aware-see-20261020/windows/source-hashes.json')
production = load(OUT / 'production-hashes.json')
changed_production = sorted(name for name, digest in production.items() if parent_hashes.get(name) != digest)
assert changed_production == ['CMakeLists.txt', 'src/board.cpp', 'src/uci.cpp']
assert source_hashes['src/board.cpp']=='239f1475fd48e9dba3babefe2399b22de5962f42e7a90a775271dbe49f6f6f31'
assert load(OUT/'test-hashes.json')==load(REPO/'validation/pin-aware-see-20261020/windows/test-hashes.json')
unchanged_names = ['src/nnue.cpp', 'src/nnue_weights.inc', 'include/forge/nnue.hpp',
                   'src/eval.cpp', 'src/eval_params.cpp', 'include/forge/eval.hpp', 'include/forge/eval_params.hpp']
nnue = {'candidate_source_commit': COMMIT, 'parent_source_commit': PARENT,
        'changed_production_files': changed_production,
        'unchanged_source_guards': {name: {'candidate_sha256': source_hashes[name], 'parent_sha256': parent_hashes[name],
                                         'identical': source_hashes[name] == parent_hashes[name]} for name in unchanged_names},
        'network_sha256': source_hashes['src/nnue_weights.inc'],
        'new_snapshot_differential_run': False,
        'reason': 'Only SEE own-king pin lookup masks and version labels changed; every test, NNUE/eval source, header and weight is byte-identical to frozen 6.4.15.',
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
      'wrapper_path': str(OUT / 'forge-pin-mask-wine'), 'wrapper_sha256': sha(OUT / 'forge-pin-mask-wine'),
      'actual_windows_engine': str(BUILD / 'forge.exe'), 'actual_windows_engine_sha256': sha(BUILD / 'forge.exe'),
      'transitions': runtime['ownbook_transitions'], 'scope': 'Wine correctness only; no speed/NPS/Elo/native-hardware claim'})

preserved_before = load(OUT / 'parent6415-preservation-before.json')
preserved_after = {name: sha(Path(name)) for name in preserved_before}
assert preserved_before == preserved_after
write(OUT / 'parent6415-preservation-check.json', {'status': 'unchanged', 'files': len(preserved_before),
      'input_sha256_before': preserved_before, 'input_sha256_after': preserved_after})

originals = OUT / 'originals'
assert not originals.exists()
(originals / 'binaries').mkdir(parents=True)
(originals / 'static-core').mkdir()
for p in sorted(BUILD.glob('*.exe')):
    assert sha(p) == runtime['input_sha256_after'][p.name]
    shutil.copyfile(p, originals / 'binaries' / p.name)
shutil.copyfile(BUILD / 'libforge_core.a', originals / 'static-core/libforge_core.a')
assert sha(originals / 'static-core/libforge_core.a') == runtime['input_sha256_after']['core_library']
shutil.copytree(SOURCE, originals / 'frozen-source')
write(OUT / 'README-checks.json', {'status': 'passed', 'source_and_tests_commit': COMMIT,
      'wine_functional_and_signature_checks': runtime['checks'], 'simd': runtime['simd'],
      'output_layer_checker_exit_code': checked.returncode, 'tt_groups': 8, 'rule50_targeted_failures': 0,
      'legal_witness_comparisons': 18947, 'ownbook_transitions': 5, 'bench11_nodes': runtime['bench11_nodes'],
      'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
      'new_nps_measurement': False, 'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging',
      'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging'})
(OUT / 'README.md').write_text(f'''Frozen Forge 6.4.16 Windows correctness evidence

Source/tests: `{COMMIT}`. Parent: `{PARENT}` (6.4.15).
Strict static LLVM-MinGW23.1.3 Zen5/C++20 Release build, one job, no FMA/LTO/fast-math.
Eight Wine checks passed: core/perft including unchanged 23 mirrored SEE cases,
eight TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook
transitions and exact parent15 Windows bench11 signature {runtime['bench11_nodes']}.
This signature was required before execution; no expectation was relaxed.

The own-king pin lookup mask replaces repeated per-attacker SEE attack queries.
King recapture logic remains unchanged. Only src/board.cpp and two version labels
differ from frozen15; all tests, headers, NNUE/eval sources and weights match exactly.
This Windows evidence is separate from native gates; packaging alone does not accept
this candidate or establish release readiness. No NPS/Elo/native Windows/Ryzen claim.
All six original PEs, core, frozen source, commands, logs and disassembly are retained
and archived. Prior 6.4.14 native bench-output anomaly remains qualified separately.
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
members = {'forge.exe': 'forge-6.4.16-ryzen-9850x3d.exe', 'forge_tests.exe': 'forge_tests.exe',
           'forge_tt_tests.exe': 'forge_tt_tests.exe', 'forge_rule50_tests.exe': 'forge_rule50_tests.exe',
           'forge_legal_witness_tests.exe': 'forge_legal_witness_tests.exe'}
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
    'engine_version': '6.4.16 candidate', 'source_and_tests_commit': COMMIT, 'parent_source_commit': PARENT,
    'source_url': 'https://github.com/couns0538-sketch/dwqww/tree/' + COMMIT,
    'production_source_sha256': production, 'test_source_sha256': load(OUT / 'test-hashes.json'),
    'compiler': build['compiler'], 'flags': 'C++20 Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
    'target': 'Windows x64 Ryzen 7 9850X3D / Zen5', 'parallel_build_jobs': 1,
    'inherited_tt_policy': 'Explicit UCI go/bench exclusive request for exactly one worker, one coarse gate plus atomic request plus sequential 1024-stripe drain, table-bound lexical owner TLS bypass; default library/SMP callers retain shared stripes.',
    'lifecycle_limit': 'Clear, resize, new_search and destruction still require all accessors quiescent; foreign entry-call safety assumes stable storage/generation. Arbitrary concurrent lifecycle operations unsupported.',
    'evaluation_network_replacement_unchanged': True,
    'native_gate_status':'Separate native gates; Windows packaging alone does not accept this candidate or establish release readiness.',
    'prior_6414_native_bench_output_anomaly':'Remains qualified in validation/double-extension-path-20261020/native6414; this Windows evidence does not resolve it.',
    'search_policy_change': 'SEE own-king pin lookup mask replaces per-attacker attack queries with the same eligibility result; king recapture branch unchanged; exact parent15 semantics required.',
    'inherited_clock_policy': 'Finite timed UCI admission accounting; unset untimed/infinite/ponder origins are worker-local; start_time authoritative, request_start supported, ponder budget begins at hit.', 'nnue_parent_identity': nnue,
    'entry_bytes': 16, 'cluster_bytes': 64,
    'inherited_halfmove_policy': 'Both capped clocks below90 or exact capped match (cap100); old main-search current-clock<90 guard retained. This remains a heuristic, not universal history correctness.',
    'wine_version': wine_version, 'wine_checks': runtime['checks'], 'tt_groups': 8,
    'legal_witness_comparisons': 18947, 'ownbook_transitions': runtime['ownbook_transitions'],
    'bench11_nodes': runtime['bench11_nodes'], 'bench_scope': 'Hash16MiB/Threads1 exact parent15 Windows bench11 signature382424 required and verified; no time/NPS comparison',
    'simd': runtime['simd'], 'output_layer_checker_exit_code': checked.returncode,
    'source_binary_and_tool_hashes_unchanged': True, 'static_libraries': build['libraries'],
    'binaries': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in PACKAGE.glob('*.exe')},
    'raw_windows_evidence_archive': raw_archive.name, 'raw_windows_evidence_sha256': sha(raw_archive),
    'raw_windows_evidence_file_count': len(raw_files), 'raw_windows_originals_retained': True,
    'evidence_directory': 'validation/pin-mask-see-20261020/windows/',
    'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging', 'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging',
    'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
    'stockfish_superiority_proven': False, 'new_nps_measurement': False,
    'performance_claim': 'No throughput, NPS, timed match, Elo or native hardware measurement performed.',
    'compile_flags_record': (BUILD / 'CMakeFiles/forge_core.dir/flags.make').read_text(),
    'link_record': (BUILD / 'CMakeFiles/forge.dir/link.txt').read_text(),
}
write(PACKAGE / 'provenance.json', provenance)
(PACKAGE / 'README.txt').write_text(f'''Forge 6.4.16 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.16-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source/tests: {COMMIT}. Parent: {PARENT} (6.4.15).

This candidate uses own-king pin lookup masks for hypothetical SEE recaptures,
replacing repeated per-attacker attack queries while requiring the same eligibility
results. King recapture logic is unchanged. Only board.cpp and version labels differ
from frozen15. All tests, headers, NNUE/eval source and weights match the parent.
Earlier clock, TT, legal/rule50, OwnBook and double-extension fixes remain inherited.
Lifecycle operations still require quiescent accessors; rule50 remains a heuristic.

Eight Wine checks passed: core/perft with unchanged 23 mirrored SEE cases, eight
TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook
transitions and exact parent15 Windows bench11 signature {runtime['bench11_nodes']}.
Parent parity was required before execution, without relaxed expectations.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.

Compiler: LLVM-MinGW23.1.3, strict C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, no LTO. All six built PEs, actual
core, frozen source, commands, stdout/stderr and disassembly are retained and saved
in manifest-verified windows-originals.zip. Prior6.4.14 native bench-output anomaly
remains qualified in its separate evidence.

This Windows stage establishes bounded correctness only; native gates are separate.
This is not an accepted release; packaging alone does not establish release readiness. This is an isolated candidate;
no accepted NPS or Elo improvement exists. No throughput or timed match was run.
Native Windows, physical Ryzen and Stockfish superiority remain unproven.

Optional tests:
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See provenance.json, source-hashes.json, test-hashes.json, nnue-parent-identity.json,
windows-originals-SHA256.json and SHA256SUMS.
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
          'engine_sha256': sha(PACKAGE / 'forge-6.4.16-ryzen-9850x3d.exe'),
          'core_sha256': sha(BUILD / 'libforge_core.a'), 'runtime_checks': 8, 'ownbook_transitions': 5,
          'legal_witness_comparisons': 18947, 'bench11_nodes': runtime['bench11_nodes'],
          'raw_archive': str(raw_archive.relative_to(REPO)), 'raw_archive_sha256': sha(raw_archive),
          'raw_original_files': len(raw_files), 'all_archived_original_bytes_sha256_verified': True,
          'scope': 'Wine correctness and bounded node signature; no NPS, Elo or native hardware result',
          'full_candidate_asan_ubsan': 'reported separately in repository; not asserted by Windows packaging', 'full_candidate_tsan': 'reported separately in repository; not asserted by Windows packaging'}
write(OUT / 'artifact.json', report)
print(json.dumps(report, indent=2))
