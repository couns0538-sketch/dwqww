#!/usr/bin/env python3
"""Preserve both original failed profiles and the separately corrected Linux run."""
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time
import zipfile

BASE = Path('/workspace/forge-nnue-handoff-20261023')
DEST = BASE / 'linux-native-qualification-recovery-attempt1'
PART_BYTES = 31 * 1024 * 1024
CHUNK = 1024 * 1024


def main():
    os.nice(10)
    started = time.monotonic()
    closed = BASE / 'linux-final-net-repaired-harness-run-attempt1/FINAL-CLOSED.json'
    closure = json.loads(closed.read_text())
    if closure['actual_tool_session_id'] != 10660 or type(closure['actual_tool_exit_code']) is not int:
        raise ValueError('Actual corrected-run tool closure required before archiving')
    spec = importlib.util.spec_from_file_location('verified_archive_helpers', BASE / 'archive_full_preparation.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)  # Reuse hashing/path/new-file helpers only, never its main/data archive.
    DEST.mkdir()
    roots = [
        ('original-failed-release-trial', Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-attempt1')),
        ('original-failed-release-wrapper', BASE / 'linux-final-net-trial-run-attempt1'),
        ('original-failed-asan-build', Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-asan-diagnostic-attempt1')),
        ('original-failed-asan-wrapper', BASE / 'linux-final-net-asan-diagnostic-attempt1'),
        ('corrected-harness-trial', Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-repaired-harness-attempt1')),
        ('corrected-harness-wrapper', BASE / 'linux-final-net-repaired-harness-run-attempt1'),
        ('bounded-counter-diagnostic', BASE / 'null-counter-diagnostic-attempt1'),
        ('controlled-test-repair-proof', BASE / 'null-pruning-controlled-test-repair-attempt1'),
        ('original-reviewed-preparation', BASE / 'linux-final-net-trial-preparation-attempt1'),
        ('original-source-review', BASE / 'linux-final-net-trial-review-attempt1'),
        ('corrected-reviewed-preparation', BASE / 'linux-final-net-repaired-harness-preparation-attempt1'),
        ('corrected-source-review', BASE / 'linux-final-net-repaired-harness-review-attempt1'),
        ('immutable-selected-net-freeze', BASE / 'full-trained-net-freeze-attempt1'),
    ]
    origins = {}

    def add(source, name):
        if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
            raise ValueError('Only regular, non-symlink files accepted: ' + str(source))
        helper.safe_name(name)
        if name in origins:
            raise ValueError('Duplicate member: ' + name)
        origins[name] = source

    for role, root in roots:
        if root.is_symlink() or not root.is_dir():
            raise ValueError('Required closed evidence root missing/unsafe: ' + str(root))
        for source in sorted(root.rglob('*')):
            if source.is_symlink():
                raise ValueError('Symlink inside evidence root: ' + str(source))
            if source.is_file():
                add(source, role + '/' + source.relative_to(root).as_posix())
            elif not source.is_dir():
                raise ValueError('Nonregular evidence entry')
    extras = [
        ('shared-export-helper/export_trial.py', BASE / 'windows-final-net-trial-preparation-attempt1/export_trial.py'),
        ('shared-export-helper/include_parser.py', Path('/workspace/dwqww/tools/nnue/include_parser.py')),
        ('accepted-old-core-reference/libforge_core.a', Path('/workspace/.cloud-setup/nnue-pipeline-20261023-baseline-build/libforge_core.a')),
        ('original-diagnostic-handoff.json', BASE / 'LINUX-TRIAL-DIAGNOSTIC-HANDOFF.json'),
        ('archive-source/archive_linux_qualification.py', Path(__file__)),
        ('archive-source/archive_full_preparation_helpers.py', BASE / 'archive_full_preparation.py'),
    ]
    for name, source in extras:
        add(source, name)
    exclusions = [
        {'scope': 'Legacy/fresh training datasets and training checkpoints/runs',
         'reason': 'Outside native qualification scope; independently published recoverable data/training evidence is referenced by the immutable selected-net FREEZE.'},
        {'scope': 'Windows native qualification and Wine evidence',
         'reason': 'Independent platform experiment, preserved/published separately by root.'},
        {'scope': 'Toolchain installation/package byte trees',
         'reason': 'Not duplicated; exact tool file identities, actual version streams and configuration are included in each pinned native run.'},
        {'scope': 'Prior archive files, other historical workspace engines and unrelated jobs',
         'reason': 'No recursive archive duplication or accidental inclusion of unrelated/live experiments.'},
    ]
    readme = '''# Linux selected-network qualification recovery

This archive retains BOTH original failed Linux profiles and the separate corrected-harness qualification. Original Release and ASan/UBSan each attempted all14 tests:13 passed, while forge_tests failed its depth8 start-position null-pruning counter assertion. Their failures remain original, not erased or reclassified. The bounded old/new-core diagnostic shows new NMP attempts/cutoffs at depth10; it is not a strength test.

Root replaced that evaluation-dependent coverage assertion with an explicit controlled two-node TT/null-child fixture. Complete old/new positive and private NMP-disabled negative controls are included under controlled-test-repair-proof. Any search.nmp-disabled.cpp/object/binary there is ONLY a deliberately defective isolated negative control, never the selected production engine or an accepted source change.

Selected production source is clean net-only commit6e9622fd5be18e0155fc3ed5fcf6c4586705cca6, network SHAa52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7. The corrected harness additionally uses exactly tests/tests.cpp from f4a1ed6be3921a024e0d876cac2433153a96c66c, SHA6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce. All74 source files were compared to that explicit contract. Original baseline1ab source differs only by selected weights and the documented corrected test. No production search/evaluation/header/tuning change is hidden in the harness repair.

Read corrected-harness-wrapper/FINAL-CLOSED.json and corrected-harness-trial/evidence/RESULT.json for the actual terminal result, first genuine new-net bench and repeat. Do not infer success merely from an archive. The original reviewed strict Linux runner and its explicit repaired variant, pinned tools, all command/stdin/stdout/stderr/result receipts, CMake/compile/link/test metadata, source bytes, complete four build trees (including tested forge/core/test binaries and original objects) are retained. No files within the enumerated included roots were excluded. Native binary roles/test execution must be read from original commands/results: a compiled forge_bench or compiler-ID executable was not automatically run by qualification.

ARCHIVE-MANIFEST.json enumerates every member's original path, size, mode and SHA256, and all explicit outside-scope exclusions. ZIP uses deflate6. Numbered parts are at most31MiB and were physically reassembled; every member's bytes/CRC/type/mode were checked from that reassembly, then all source files were rehashed unchanged. Original successful full-training native-derived streams are unrelated to this archive and were not reconstructed; their declared retention limits remain in the published data checkpoint.

Recover by downloading the published ARCHIVE-MANIFEST.json and .zip.001 onward into a new directory. Authenticate the manifest against Git, verify each part's declared bytes/SHA, concatenate strictly in manifest order, and verify the archive bytes/SHA before opening it. Validate exact unique member names, reject absolute/traversal/backslash/symlink paths, and stream-check every size/SHA/mode against the manifest before extracting to a NEW destination. README in the earlier full-prepared-data-recovery checkpoint contains a standard-library Python verification/extraction example using the same archive/parts/members schema. Preserve original absolute paths in provenance; explicitly remap replay paths on another machine rather than rewriting historical evidence. Do not execute recovered code automatically.

These are Linux GCC14 strict-float correctness/repeatability artifacts. They establish no native Windows/Ryzen qualification, NPS improvement, Elo gain, Stockfish result or promotion. No match/PGN evidence exists in this qualification because no match was run. The selected network/default acceptance decision remains with the separately frozen validation/strength protocol and root's report.
'''
    helper_ast = ast.parse((BASE / 'archive_full_preparation.py').read_text())
    recovery_readme = next(node.value.value for node in ast.walk(helper_ast)
                           if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                           and any(isinstance(target, ast.Name) and target.id == 'readme' for target in node.targets))
    recovery_code = recovery_readme.split('```python\n', 1)[1].split('```', 1)[0]
    ast.parse(recovery_code, filename='native-checkpoint-recovery-example.py')
    readme += '\n## Standalone standard-library recovery example\n\n```python\n' + recovery_code + '```\n'
    (DEST / 'README.md').write_text(readme)
    add(DEST / 'README.md', 'README.md')

    def describe(name, source):
        return {'path': name, 'origin_path': str(source), 'bytes': source.stat().st_size,
                'mode': stat.S_IMODE(source.stat().st_mode), 'sha256': helper.sha256(source)}

    payload = [describe(name, source) for name, source in sorted(origins.items())]
    helper.write_new(DEST / 'CONTENT-MANIFEST.json',
                     {'schema_version': 1, 'included_roots_all_files': [{'role': role, 'path': str(root)} for role, root in roots],
                      'files': payload, 'no_files_excluded_within_included_roots': True,
                      'excluded_outside_scope': exclusions,
                      'scope': 'External ARCHIVE-MANIFEST additionally binds this manifest itself.'})
    add(DEST / 'CONTENT-MANIFEST.json', 'CONTENT-MANIFEST.json')
    members = [describe(name, source) for name, source in sorted(origins.items())]
    helper.write_new(DEST / 'SOURCE-SNAPSHOT.json', {'members': members})
    archive = DEST / 'forge-nnue-linux-original-failures-and-corrected-20261023.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for name, source in sorted(origins.items()):
            z.write(source, arcname=name)
    raw = {'name': archive.name, 'bytes': archive.stat().st_size, 'sha256': helper.sha256(archive),
           'compression': 'ZIP_DEFLATED', 'compresslevel': 6}
    parts = []
    with archive.open('rb') as source:
        index = 1
        while True:
            chunk = source.read(CHUNK)
            if not chunk:
                break
            path = DEST / (archive.name + '.' + str(index).zfill(3)); h = hashlib.sha256(); size = 0
            with path.open('xb') as stream:
                while chunk:
                    stream.write(chunk); h.update(chunk); size += len(chunk)
                    if size == PART_BYTES:
                        break
                    chunk = source.read(min(CHUNK, PART_BYTES - size))
            parts.append({'name': path.name, 'bytes': size, 'sha256': h.hexdigest()}); index += 1
    restored = DEST / 'READBACK-reassembled.zip'
    with restored.open('xb') as stream:
        for record in parts:
            path = DEST / record['name']
            if path.stat().st_size != record['bytes'] or helper.sha256(path) != record['sha256']:
                raise ValueError('Split-part readback differs')
            with path.open('rb') as source:
                for chunk in iter(lambda: source.read(CHUNK), b''):
                    stream.write(chunk)
    if restored.stat().st_size != raw['bytes'] or helper.sha256(restored) != raw['sha256']:
        raise ValueError('Physical reassembly differs')
    expected = {record['path']: record for record in members}
    with zipfile.ZipFile(restored) as z:
        if len(z.infolist()) != len(expected) or set(z.namelist()) != set(expected):
            raise ValueError('Readback unique member names/count differ')
        for info in z.infolist():
            helper.safe_name(info.filename); record = expected[info.filename]
            if not stat.S_ISREG(info.external_attr >> 16) or stat.S_IMODE(info.external_attr >> 16) != record['mode']:
                raise ValueError('Readback type/mode differs')
            h = hashlib.sha256(); size = 0
            with z.open(info) as stream:
                for chunk in iter(lambda: stream.read(CHUNK), b''):
                    h.update(chunk); size += len(chunk)
            if size != record['bytes'] or h.hexdigest() != record['sha256']:
                raise ValueError('Readback member bytes differ: ' + info.filename)
    for record in members:
        source = Path(record['origin_path'])
        if (source.stat().st_size != record['bytes'] or stat.S_IMODE(source.stat().st_mode) != record['mode']
                or helper.sha256(source) != record['sha256']):
            raise ValueError('Closed source changed while archiving: ' + str(source))
    result = {'schema_version': 1, 'status': 'PASS_NATIVE_QUALIFICATION_ARCHIVE_READBACK',
              'utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds_operational_only': time.monotonic() - started,
              'archive': raw, 'parts': parts, 'part_max_bytes': PART_BYTES,
              'member_count': len(members), 'expanded_bytes': sum(r['bytes'] for r in members), 'members': members,
              'included_roots_all_files': [{'role': role, 'path': str(root)} for role, root in roots],
              'excluded_outside_scope': exclusions, 'no_files_excluded_within_included_roots': True,
              'all_members_verified_from_physical_part_reassembly': True,
              'original_source_bytes_and_modes_rechecked_unchanged': True,
              'corrected_run_closure_sha256': helper.sha256(closed),
              'actual_original_failed_runs_preserved': True, 'speed_or_elo_conclusion': None}
    helper.write_new(DEST / 'ARCHIVE-MANIFEST.json', result)
    print(json.dumps({'status': result['status'], 'archive': raw, 'parts': parts,
                      'members': len(members), 'expanded_bytes': result['expanded_bytes'],
                      'manifest_path': str(DEST / 'ARCHIVE-MANIFEST.json'),
                      'manifest_sha256': helper.sha256(DEST / 'ARCHIVE-MANIFEST.json')}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
