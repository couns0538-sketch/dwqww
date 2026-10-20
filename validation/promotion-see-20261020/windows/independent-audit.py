#!/usr/bin/env python3
"""Read-only Windows 6.4.17 artifact/provenance audit; executes no engine."""
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
HERE = ROOT / 'validation/promotion-see-20261020/windows'
SOURCE = Path('/workspace/.cloud-setup/forge-promotion-windows-source')
BUILD = Path('/workspace/.cloud-setup/forge-promotion-windows-build')
PACKAGE = ROOT / 'releases/forge-6.4.17-candidate-windows-zen5'
ARCHIVE = PACKAGE.with_name(PACKAGE.name + '.zip')
COMMIT = '47f0560221d986e41a309853e1295c557fcf5bf6'
PARENT = '553caef144ae2e1b696ba35d7a0eb1a50a03fde9'
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

assert Path('/workspace/.cloud-setup/windows6417-package-ready').exists(), 'Package not final yet'
runtime = load(HERE/'runtime-attempt1/result.json')
build = load(HERE/'result.json')
artifact = load(HERE/'artifact.json')
check('runtime_passed', runtime['status'] == 'passed')
check('build_passed', build['status'] == 'build_passed')
check('frozen_source_identity', runtime['source_and_tests_commit'] == build['source_and_tests_commit'] == artifact['source_and_tests_commit'] == COMMIT)
check('eight_runtime_checks', len(runtime['checks']) == 8 and all(c['exit_code'] == 0 for c in runtime['checks']))
check('tt_groups', runtime['tt_groups'] == 8)
check('legal_witness_count', runtime['legal_witness_comparisons'] == 18947)
check('rule50_pass', runtime['rule50_targeted_failures'] == 0)
check('candidate_bench_signature_recorded_positive', isinstance(runtime['bench11_nodes'], int) and not isinstance(runtime['bench11_nodes'], bool) and runtime['bench11_nodes'] > 0)
freeze_path = HERE/'BENCH-SIGNATURE-FREEZE.json'
freeze = load(freeze_path)
check('bench_freeze_candidate_source', freeze['source_and_tests_commit'] == COMMIT)
check('bench_freeze_actual_nodes', freeze['bench11_nodes'] == runtime['bench11_nodes'])
check('bench_freeze_tested_pe', freeze['engine_sha256'] == runtime['input_sha256_after']['forge.exe'])
check('bench_freeze_raw_stdout', freeze['raw_bench_stdout_sha256'] == sha((HERE/'runtime-attempt1/bench-stdout.log').read_bytes()))
check('bench_freeze_native_independent', freeze['native_independent'] is True)
package_phase = load(HERE/'package-phase-command.json')
freeze_time = datetime.datetime.fromisoformat(freeze['frozen_utc'])
package_started = datetime.datetime.fromisoformat(package_phase['started_utc'])
package_completed = datetime.datetime.fromisoformat(package_phase['completed_utc'])
check('bench_freeze_timezone_aware', all(value.utcoffset() is not None for value in [freeze_time, package_started, package_completed]))
check('bench_freeze_before_package_execution', freeze_time <= package_started <= package_completed)
check('bench_freeze_before_release_zip', freeze_path.stat().st_mtime_ns <= ARCHIVE.stat().st_mtime_ns and freeze_time.timestamp() <= ARCHIVE.stat().st_mtime)

check('raw_core_tests_pass', 'All tests passed' in (HERE/'runtime-attempt1/core-stdout.log').read_text())
check('raw_tt8_pass', 'All8 TT coherence/regression groups passed' in (HERE/'runtime-attempt1/coherent-tt-stdout.log').read_text())
check('raw_rule50_pass', 'targeted_regression_failures=0' in (HERE/'runtime-attempt1/rule50-stdout.log').read_text())
check('raw_legal_oracle_pass', 'All 18947 legal-witness Boolean comparisons passed' in (HERE/'runtime-attempt1/legal-witness-stdout.log').read_text())
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
check('only_reviewed_production_delta', sorted(changed)==['CMakeLists.txt','src/board.cpp','src/uci.cpp'])
check('exact_reviewed_board_source', source_hashes['src/board.cpp'] == 'ad3290611e5f88d95b8fd0f674370eadc17e0c529902fba3e92ac48ac46ed239')
changed_all = []
for name, digest in source_hashes.items():
    parent_data = subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT)
    if sha(parent_data) != digest:
        changed_all.append(name)
check('only_declared_four_export_changes', sorted(changed_all) == ['CMakeLists.txt','src/board.cpp','src/uci.cpp','tests/tests.cpp'])
for name in [n for n in source_hashes if n.startswith('tests/') and n != 'tests/tests.cpp']:
    check('unchanged_parent_test:'+name,sha(subprocess.check_output(['git','show',PARENT+':'+name],cwd=ROOT))==source_hashes[name])
permanent_tests = (SOURCE/'tests/tests.cpp').read_text()
check('permanent_pin_regression_registered', 'void test_pinned_static_exchange()' in permanent_tests and '    test_pinned_static_exchange();' in permanent_tests)
check('permanent_see_regression_28_cases_mirrored', 'std::array<ExchangeCase, 28> cases' in permanent_tests and 'for (const bool mirrored : {false, true})' in permanent_tests)
check('permanent_see_zero_threshold_assertion', 'check(board.see_ge(*move, 0) == (item.gain >= 0), item.name);' in permanent_tests)
check('five_promotion_recapture_cases', all(name in permanent_tests for name in [
    'later promotion saves capture', 'enemy promotion poisons capture', 'pinned promoting recapturer',
    'promoted recapturer taken by king', 'promotion recapture changes victim']))


for name in ['src/nnue.cpp', 'src/nnue_weights.inc', 'include/forge/nnue.hpp', 'src/eval.cpp', 'src/eval_params.cpp', 'include/forge/eval.hpp', 'include/forge/eval_params.hpp']:
    check('unchanged_parent_eval:' + name, sha(subprocess.check_output(['git', 'show', PARENT + ':' + name], cwd=ROOT)) == source_hashes[name])

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
for p in sorted(BUILD.glob('*.exe')):
    check('tested_actual_pe:' + p.name, sha(p.read_bytes()) == runtime['input_sha256_after'][p.name])
    imports[p.name] = pe_imports(p.read_bytes())
    check('system_crt_imports_only:' + p.name, bool(imports[p.name]) and all(n.lower() == 'kernel32.dll' or n.lower().startswith('api-ms-win-crt-') for n in imports[p.name]))
check('packaged_tested_engine', sha((PACKAGE/'forge-6.4.17-ryzen-9850x3d.exe').read_bytes()) == runtime['input_sha256_after']['forge.exe'])
for name in ['forge_tests.exe', 'forge_tt_tests.exe', 'forge_rule50_tests.exe', 'forge_legal_witness_tests.exe']:
    check('packaged_tested_helper:' + name, sha((PACKAGE/name).read_bytes()) == runtime['input_sha256_after'][name])
check('tested_core', sha((BUILD/'libforge_core.a').read_bytes()) == runtime['input_sha256_after']['core_library'])

raw = HERE/'windows-originals.zip'
manifest = load(HERE/'windows-originals-SHA256.json')
check('bench_freeze_raw_archive_member', 'BENCH-SIGNATURE-FREEZE.json' in manifest)
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
for row in commands:
    text = row['command']
    check('strict_compiler_flags:' + row['file'], all(s in text for s in ['-march=znver5', '-mtune=znver5', '-O3', '-DNDEBUG', '-std=gnu++20', '-fno-fast-math', '-ffp-contract=off']) and '-ffast-math' not in text and '-flto' not in text)
link_record = (BUILD/'CMakeFiles/forge.dir/link.txt').read_text()
check('static_link_no_lto', '-static' in link_record and '-flto' not in link_record)
disassembly = (HERE/'runtime-attempt1/disassembly.log').read_text()
check('avx2_instructions', all(re.search(expr, disassembly) for expr in [r'v(?:max|min)ps[^\n]*ymm', r'vmulps[^\n]*ymm', r'vaddps[^\n]*ymm']))
check('no_fused_operations', re.search(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b', disassembly) is None)
check('output_layer_checker_rc0', load(HERE/'output-layer-checker.json')['exit_code'] == 0)
before = load(HERE/'parent6416-preservation-before.json')
for name, digest in before.items():
    check('parent_preserved:' + name, sha(Path(name).read_bytes()) == digest)
crlf_logs = [p.name for p in (HERE/'runtime-attempt1').glob('*stdout.log') if b'\r\n' in p.read_bytes()]
check('wine_original_crlf_retained', bool(crlf_logs))
provenance = load(PACKAGE/'provenance.json')
check('embedded_bench_freeze_provenance', provenance['bench_signature_freeze'] == freeze)
readme = (PACKAGE/'README.txt').read_text()
check('honest_claim_flags', provenance['native_windows_tested'] is False and provenance['physical_ryzen_tested'] is False and provenance['accepted_elo_gain'] is None and provenance['stockfish_superiority_proven'] is False and provenance['new_nps_measurement'] is False)
check('readme_scope', 'no accepted NPS or Elo improvement exists' in readme and 'Native Windows, physical Ryzen' in readme and 'Stockfish superiority remain' in readme)
check('search_policy_not_mislabelled_unchanged', provenance.get('evaluation_network_replacement_unchanged') is True and 'search_policy_eval_network_replacement_unchanged' not in provenance and 'promotion' in provenance.get('search_policy_change','').lower())
claim_text = ' '.join(readme.lower().split())
check('windows_stage_scope_explicit', 'windows stage' in claim_text and 'only' in claim_text)
check('native_gates_separate_explicit', 'native' in claim_text and 'gates' in claim_text and 'separate' in claim_text)
check('not_accepted_release_explicit', re.search(r'(?:not (?:an? )?|no )accepted release', claim_text) is not None)
check('parent16_original_tsan_failure_qualified', all(term in claim_text for term in ('6.4.16', 'tsan', 'failed', '8/9')))

report = {'status':'passed', 'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'auditor':'independent nested artifact agent /root/windows6415/artifact_audit', 'source_and_tests_commit':COMMIT, 'parent_source_commit':PARENT, 'engine_execution_during_audit':False, 'new_build_during_audit':False, 'check_count':len(checks), 'checks':checks, 'declared_export_changes':sorted(changed_all), 'bench_policy':'Actual Windows candidate signature frozen before packaging; no parent or native node-signature requirement', 'bench_signature_freeze':freeze, 'native_gate_status_not_asserted':True, 'parent16_original_tsan_failure_qualification_retained':True, 'bench11_nodes':runtime['bench11_nodes'], 'source_files':len(source_hashes), 'release_members':release_members, 'release_sha_entries':len(sums), 'artifact':str(ARCHIVE.relative_to(ROOT)), 'artifact_bytes':ARCHIVE.stat().st_size, 'artifact_sha256':sha(ARCHIVE.read_bytes()), 'raw_files':len(manifest), 'raw_members':len(manifest)+1, 'raw_sha256':sha(raw.read_bytes()), 'raw_bytes':raw.stat().st_size, 'engine_sha256':runtime['input_sha256_after']['forge.exe'], 'core_sha256':runtime['input_sha256_after']['core_library'], 'pe_imports':imports, 'parent_preserved_files':len(before), 'crlf_stdout_logs':crlf_logs, 'scope':'Bounded Windows/Wine correctness and artifact provenance. No speed, NPS, Elo, native Windows, physical Ryzen or Stockfish superiority result.'}
(HERE/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(HERE/'independent-audit.md').write_text(f'''# Independent Windows 6.4.17 artifact audit

All **{len(checks)} checks passed** on the immutable source `{COMMIT}`.
The audit executed no engine and performed no rebuild.

The release ZIP ({report['artifact_bytes']:,} bytes) has {release_members} unique,
safe, non-symlink members, complete CRC and {len(sums)} verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All {len(source_hashes)} source-export hashes match frozen Git objects. The exact
four changed files are board.cpp, tests/tests.cpp and the two version labels.
The other four test files, NNUE/eval source, headers and weights match parent `{PARENT}`. All {len(manifest)} raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All {len(before)}
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the {runtime['bench11_nodes']:,}-node signature (actual Windows signature frozen before packaging; no parent/native-parity requirement). Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. The source, tested PE and raw bench transcript
match the pre-package signature freeze embedded in provenance. Freeze/package
timestamps establish the declared ordering. README/provenance correctly limit
the claims.

Release SHA256: `{report['artifact_sha256']}`.
Engine SHA256: `{report['engine_sha256']}`.
Raw evidence SHA256: `{report['raw_sha256']}`.

This validates the Windows stage only; native gates remain separate and this is
not an accepted release. The original 6.4.16 TSan FAILED 8/9 qualification remains
explicit; no full parent native pass is inherited. This audit validates bounded
Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
''')
print(json.dumps({k:report[k] for k in ['status','check_count','source_files','release_members','release_sha_entries','raw_files','artifact_sha256','engine_sha256','parent_preserved_files']},indent=2))
