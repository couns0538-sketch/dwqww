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
COMMIT = '8865666cc0ab4961cd507bae40ff6ce44e9319df'
PARENT = 'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e'
SOURCE = Path('/workspace/.cloud-setup/forge-windows-tt-gated-source')
BUILD = Path('/workspace/.cloud-setup/forge-windows-tt-gated')
OUT = REPO / 'validation/single-thread-tt-20261020/windows'
PACKAGE = REPO / 'releases/forge-6.4.12-candidate-windows-zen5'
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
assert runtime['legal_witness_comparisons'] == 18947 and runtime['bench11_nodes'] == 351063
assert runtime['input_sha256_before'] == runtime['input_sha256_after']
assert len(runtime['ownbook_transitions']) == 5 and all(t['PASS'] for t in runtime['ownbook_transitions'])

source_hashes = load(OUT / 'source-hashes.json')
assert {p.relative_to(SOURCE).as_posix(): sha(p) for p in SOURCE.rglob('*') if p.is_file()} == source_hashes
for name, digest in source_hashes.items():
    assert hashlib.sha256(subprocess.check_output(['git', '-C', str(REPO), 'show', COMMIT + ':' + name])).hexdigest() == digest
parent_hashes = load(REPO / 'validation/nnue-capture-fusion-20261019/windows/source-hashes.json')
production = load(OUT / 'production-hashes.json')
changed_production = sorted(name for name, digest in production.items() if parent_hashes.get(name) != digest)
assert changed_production == ['CMakeLists.txt', 'include/forge/search.hpp', 'src/search.cpp', 'src/uci.cpp']
unchanged_names = ['src/nnue.cpp', 'src/nnue_weights.inc', 'include/forge/nnue.hpp',
                   'src/eval.cpp', 'src/eval_params.cpp', 'include/forge/eval.hpp', 'include/forge/eval_params.hpp']
nnue = {'candidate_source_commit': COMMIT, 'parent_source_commit': PARENT,
        'changed_production_files': changed_production,
        'unchanged_source_guards': {name: {'candidate_sha256': source_hashes[name], 'parent_sha256': parent_hashes[name],
                                         'identical': source_hashes[name] == parent_hashes[name]} for name in unchanged_names},
        'network_sha256': source_hashes['src/nnue_weights.inc'],
        'new_snapshot_differential_run': False,
        'reason': 'Only TT synchronization, opt-in call sites and version strings changed; NNUE/eval sources, headers and weights are byte-identical to frozen 6.4.11.',
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
write(OUT / 'compile-contract.json', {'status': 'passed', 'compilation_records': len(compile_commands),
      'flags': ['-march=znver5', '-mtune=znver5', '-fno-fast-math', '-ffp-contract=off', '-O3', '-DNDEBUG', '-std=gnu++20'],
      'static_link': True, 'parallel_jobs': 2})

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
      'wrapper_path': str(OUT / 'forge-tt-gated-wine'), 'wrapper_sha256': sha(OUT / 'forge-tt-gated-wine'),
      'actual_windows_engine': str(BUILD / 'forge.exe'), 'actual_windows_engine_sha256': sha(BUILD / 'forge.exe'),
      'transitions': runtime['ownbook_transitions'], 'scope': 'Wine correctness only; no speed/NPS/Elo/native-hardware claim'})

preserved_before = load(OUT / 'parent6411-preservation-before.json')
preserved_after = {name: sha(Path(name)) for name in preserved_before}
assert preserved_before == preserved_after
write(OUT / 'parent6411-preservation-check.json', {'status': 'unchanged', 'files': len(preserved_before),
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
      'legal_witness_comparisons': 18947, 'ownbook_transitions': 5, 'bench11_nodes': 351063,
      'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
      'new_nps_measurement': False, 'full_candidate_asan_ubsan': 'pending separately at packaging',
      'full_candidate_tsan': 'pending separately at packaging'})
(OUT / 'README.md').write_text('''Frozen Forge 6.4.12 Windows correctness evidence

Source and tests: `8865666cc0ab4961cd507bae40ff6ce44e9319df`.
Build: LLVM-MinGW 23.1.3, C++20 Release, znver5, strict float and static linking, two jobs.
All eight Wine checks passed: core/reference perft, coherent TT (eight groups), rule50,
legal witness (18,947 comparisons), UCI, ponder, OwnBook (five transitions), and
bench11 node signature 351,063. Output-layer SIMD and no-fused-arithmetic checks passed.

UCI go/bench explicitly request exclusive TT access, activated only for one worker.
A coarse gate and atomic request protect a sequential 1,024-stripe drain, followed by
table-bound owner TLS bypass; foreign entry calls retain synchronized access.
Default library callers and multiworker searches retain the shared stripe path.
Clear/resize/new_search/destruction still require every accessor to be quiescent.
This change does not alter NNUE, evaluation weights, search/replacement policy or
the rule50 heuristic. The unchanged NNUE/eval hashes are compared with frozen 6.4.11;
no new large snapshot differential was needed or run.

The originals directory retains every built Windows executable, the actual static core
and frozen build input tree. Runtime logs, exact commands, source/test manifests,
compiler/link records, disassembly and wrapper/OwnBook adapter provenance remain here.
windows-originals.zip and its per-file manifest preserve these bytes in the release.

Full candidate ASan/UBSan and TSan status is pending separately at packaging.
Wine establishes bounded correctness; speed, Elo, native Windows, physical Ryzen and
Stockfish superiority remain unproven. No timed trial or new NPS measurement was run.
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
members = {'forge.exe': 'forge-6.4.12-ryzen-9850x3d.exe', 'forge_tests.exe': 'forge_tests.exe',
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
    'engine_version': '6.4.12 candidate', 'source_and_tests_commit': COMMIT, 'parent_source_commit': PARENT,
    'source_url': 'https://github.com/couns0538-sketch/dwqww/tree/' + COMMIT,
    'production_source_sha256': production, 'test_source_sha256': load(OUT / 'test-hashes.json'),
    'compiler': build['compiler'], 'flags': 'C++20 Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
    'target': 'Windows x64 Ryzen 7 9850X3D / Zen5', 'parallel_build_jobs': 2,
    'tt_change': 'Explicit UCI go/bench exclusive request for exactly one worker, one coarse gate plus atomic request plus sequential 1024-stripe drain, table-bound lexical owner TLS bypass; default library/SMP callers retain shared stripes.',
    'lifecycle_limit': 'Clear, resize, new_search and destruction still require all accessors quiescent; foreign entry-call safety assumes stable storage/generation. Arbitrary concurrent lifecycle operations unsupported.',
    'search_eval_network_replacement_unchanged': True, 'nnue_parent_identity': nnue,
    'entry_bytes': 16, 'cluster_bytes': 64,
    'inherited_halfmove_policy': 'Both capped clocks below90 or exact capped match (cap100); old main-search current-clock<90 guard retained. This remains a heuristic, not universal history correctness.',
    'wine_version': wine_version, 'wine_checks': runtime['checks'], 'tt_groups': 8,
    'legal_witness_comparisons': 18947, 'ownbook_transitions': runtime['ownbook_transitions'],
    'bench11_nodes': 351063, 'bench_scope': 'Hash16MiB/Threads1 node signature matching frozen Windows6.4.11; no time/NPS comparison',
    'simd': runtime['simd'], 'output_layer_checker_exit_code': checked.returncode,
    'source_binary_and_tool_hashes_unchanged': True, 'static_libraries': build['libraries'],
    'binaries': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in PACKAGE.glob('*.exe')},
    'raw_windows_evidence_archive': raw_archive.name, 'raw_windows_evidence_sha256': sha(raw_archive),
    'raw_windows_evidence_file_count': len(raw_files), 'raw_windows_originals_retained': True,
    'evidence_directory': 'validation/single-thread-tt-20261020/windows/',
    'full_candidate_asan_ubsan': 'pending separately at packaging', 'full_candidate_tsan': 'pending separately at packaging',
    'native_windows_tested': False, 'physical_ryzen_tested': False, 'accepted_elo_gain': None,
    'stockfish_superiority_proven': False, 'new_nps_measurement': False,
    'performance_claim': 'No throughput, NPS, timed match, Elo or native hardware measurement performed.',
    'compile_flags_record': (BUILD / 'CMakeFiles/forge_core.dir/flags.make').read_text(),
    'link_record': (BUILD / 'CMakeFiles/forge.dir/link.txt').read_text(),
}
write(PACKAGE / 'provenance.json', provenance)
(PACKAGE / 'README.txt').write_text('''Forge 6.4.12 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.12-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5. Source and tests:
8865666cc0ab4961cd507bae40ff6ce44e9319df

This candidate changes TT synchronization for explicitly opted-in one-worker
UCI searches and the UCI bench command. It acquires a coarse gate, publishes an
atomic request, sequentially drains the existing 1,024 stripes, then permits the
owner thread to skip per-entry locks through table-bound TLS. Foreign entry calls
wait safely while table storage/generation remain stable. Default public library
searches and multiworker UCI searches retain the shared stripe path. Clear,
resize, new_search and destruction still require all accessors to be quiescent.
Foreign diagnostics may block for an entire search; the lease does not make
arbitrary concurrent lifecycle changes safe.

NNUE/eval sources, headers and network weights are byte-identical to frozen
6.4.11. Search policy, replacement selection and rule50 policy are unchanged.
The inherited below90 rule50 grouping remains heuristic and does not solve
every repetition or history issue. Entry/cluster sizes remain16/64 bytes.
No new large NNUE snapshot differential was needed or run for this TT change.

Eight Wine10 checks passed: core/reference perft, eight TT groups, rule50,
18,947 legal-witness comparisons, UCI, ponder, five external OwnBook transitions,
and stdin bench11 at351,063 nodes (Hash16MiB/Threads1), matching Windows6.4.11.
The existing output-layer checker verified 256-bit clamp/multiply/add without
fused arithmetic. All source, fixture, corpus, binary and tool hashes remained
unchanged during validation. See README-checks.json and provenance.json.

The compiler is LLVM-MinGW23.1.3, C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off and static linking. All six original Windows
executables, actual static core, frozen source tree, exact commands, compiler/link
records, runtime stdout/stderr and full disassembly are in windows-originals.zip.
Its per-file manifest was checked against every archived byte. Originals remain
in the repository validation directory; the release engine is the tested PE.

Full candidate ASan/UBSan and TSan validation is pending separately at packaging.
This is a correctness candidate; no accepted NPS or Elo gain exists. No Windows
throughput or timed match was run. Native Windows, physical Ryzen and Stockfish
superiority remain unproven. Earlier portable offline validators are separate;
no new offline validation bundle was built for this executable.

Optional included tests (from this directory):
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See source-hashes.json, test-hashes.json, nnue-parent-identity.json,
provenance.json, windows-originals-SHA256.json and SHA256SUMS.
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
          'engine_sha256': sha(PACKAGE / 'forge-6.4.12-ryzen-9850x3d.exe'),
          'core_sha256': sha(BUILD / 'libforge_core.a'), 'runtime_checks': 8, 'ownbook_transitions': 5,
          'legal_witness_comparisons': 18947, 'bench11_nodes': 351063,
          'raw_archive': str(raw_archive.relative_to(REPO)), 'raw_archive_sha256': sha(raw_archive),
          'raw_original_files': len(raw_files), 'all_archived_original_bytes_sha256_verified': True,
          'scope': 'Wine correctness and bounded node signature; no NPS, Elo or native hardware result',
          'full_candidate_asan_ubsan': 'pending separately at packaging', 'full_candidate_tsan': 'pending separately at packaging'}
write(OUT / 'artifact.json', report)
print(json.dumps(report, indent=2))
