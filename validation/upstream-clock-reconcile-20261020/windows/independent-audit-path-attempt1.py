#!/usr/bin/env python3
"""Read-only Windows 6.4.13 artifact/provenance audit; executes no engine."""
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
HERE = ROOT / 'validation/upstream-clock-reconcile-20261020/windows'
SOURCE = Path('/workspace/.cloud-setup/forge-windows-clock-contract-source')
BUILD = Path('/workspace/.cloud-setup/forge-windows-clock-contract')
PACKAGE = ROOT / 'releases/forge-6.4.13-candidate-windows-zen5'
ARCHIVE = PACKAGE.with_suffix('.zip')
COMMIT = 'cecf0b9e3af5602053bcaf5c5d16ffc09f58850d'
PARENT = '8865666cc0ab4961cd507bae40ff6ce44e9319df'
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
check('bench_signature', runtime['bench11_nodes'] == 351063)
check('five_book_transitions', len(runtime['ownbook_transitions']) == 5 and all(c['PASS'] and c['expected_book'] == c['actual_book'] for c in runtime['ownbook_transitions']))
check('runtime_inputs_unchanged', runtime['input_sha256_before'] == runtime['input_sha256_after'])
check('resume_command_rc0', load(HERE/'resume-validation-command.json')['exit_code'] == 0)
check('package_command_rc0', load(HERE/'resume-packaging-command.json')['exit_code'] == 0)

source_hashes = load(HERE/'source-hashes.json')
check('complete_source_export', source_hashes == {p.relative_to(SOURCE).as_posix(): sha(p.read_bytes()) for p in SOURCE.rglob('*') if p.is_file()})
for name, digest in source_hashes.items():
    check('git_source:' + name, sha(subprocess.check_output(['git', 'show', COMMIT + ':' + name], cwd=ROOT)) == digest)
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
check('packaged_tested_engine', sha((PACKAGE/'forge-6.4.13-ryzen-9850x3d.exe').read_bytes()) == runtime['input_sha256_after']['forge.exe'])
for name in ['forge_tests.exe', 'forge_tt_tests.exe', 'forge_rule50_tests.exe', 'forge_legal_witness_tests.exe']:
    check('packaged_tested_helper:' + name, sha((PACKAGE/name).read_bytes()) == runtime['input_sha256_after'][name])
check('tested_core', sha((BUILD/'libforge_core.a').read_bytes()) == runtime['input_sha256_after']['core_library'])

raw = HERE/'windows-originals.zip'
manifest = load(HERE/'windows-originals-SHA256.json')
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
    check('strict_compiler_flags:' + row['file'], all(s in text for s in ['-march=znver5', '-mtune=znver5', '-O3', '-DNDEBUG', '-std=gnu++20', '-fno-fast-math', '-ffp-contract=off']) and '-ffast-math' not in text)
check('static_link', '-static' in (BUILD/'CMakeFiles/forge.dir/link.txt').read_text())
disassembly = (HERE/'runtime-attempt1/disassembly.log').read_text()
check('avx2_instructions', all(re.search(expr, disassembly) for expr in [r'v(?:max|min)ps[^\n]*ymm', r'vmulps[^\n]*ymm', r'vaddps[^\n]*ymm']))
check('no_fused_operations', re.search(r'\bv(?:fmadd|fmsub|fnmadd|fnmsub)\w*\b', disassembly) is None)
check('output_layer_checker_rc0', load(HERE/'output-layer-checker.json')['exit_code'] == 0)
before = load(HERE/'parent6412-preservation-before.json')
for name, digest in before.items():
    check('parent_preserved:' + name, sha(Path(name).read_bytes()) == digest)
crlf_logs = [p.name for p in (HERE/'runtime-attempt1').glob('*stdout.log') if b'\r\n' in p.read_bytes()]
check('wine_original_crlf_retained', bool(crlf_logs))
provenance = load(PACKAGE/'provenance.json')
readme = (PACKAGE/'README.txt').read_text()
check('honest_claim_flags', provenance['native_windows_tested'] is False and provenance['physical_ryzen_tested'] is False and provenance['accepted_elo_gain'] is None and provenance['stockfish_superiority_proven'] is False and provenance['new_nps_measurement'] is False)
check('readme_scope', 'no accepted NPS or Elo improvement exists' in readme and 'Native Windows, physical Ryzen and Stockfish superiority remain' in readme)
report = {'status':'passed', 'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'auditor':'independent nested artifact agent /root/resume_windows6413/artifact_audit', 'source_and_tests_commit':COMMIT, 'parent_source_commit':PARENT, 'engine_execution_during_audit':False, 'new_build_during_audit':False, 'check_count':len(checks), 'checks':checks, 'source_files':len(source_hashes), 'release_members':release_members, 'release_sha_entries':len(sums), 'artifact':str(ARCHIVE.relative_to(ROOT)), 'artifact_bytes':ARCHIVE.stat().st_size, 'artifact_sha256':sha(ARCHIVE.read_bytes()), 'raw_files':len(manifest), 'raw_members':len(manifest)+1, 'raw_sha256':sha(raw.read_bytes()), 'raw_bytes':raw.stat().st_size, 'engine_sha256':runtime['input_sha256_after']['forge.exe'], 'core_sha256':runtime['input_sha256_after']['core_library'], 'pe_imports':imports, 'parent_preserved_files':len(before), 'crlf_stdout_logs':crlf_logs, 'scope':'Bounded Windows/Wine correctness and artifact provenance. No speed, NPS, Elo, native Windows, physical Ryzen or Stockfish superiority result.'}
(HERE/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(HERE/'independent-audit.md').write_text(f'''# Independent Windows 6.4.13 artifact audit

All **{len(checks)} checks passed** on the immutable source `{COMMIT}`.
The audit executed no engine and performed no rebuild.

The release ZIP ({report['artifact_bytes']:,} bytes) has {release_members} unique,
safe, non-symlink members, complete CRC and {len(sums)} verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All {len(source_hashes)} source-export hashes match frozen Git objects. NNUE/eval
source, headers and weights match parent `{PARENT}`. All {len(manifest)} raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All {len(before)}
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 351,063-node signature. Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. README/provenance correctly limit the claims.

Release SHA256: `{report['artifact_sha256']}`.
Engine SHA256: `{report['engine_sha256']}`.
Raw evidence SHA256: `{report['raw_sha256']}`.

This validates bounded Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
''')
print(json.dumps({k:report[k] for k in ['status','check_count','source_files','release_members','release_sha_entries','raw_files','artifact_sha256','engine_sha256','parent_preserved_files']},indent=2))
