#!/usr/bin/env python3
"""Preserve the completed causal diagnostic; no engine execution or Git writes."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys

REPO = Path('/workspace/dwqww')
CAUSAL = REPO/'validation/time-forfeit-causal-20261020'
OUT = CAUSAL/'archive-complete'
STAGE = Path('/workspace/.cloud-setup/forge-forfeit-causal-archive-stage-20261020')
ARCHIVER = REPO/'.github/hosted-tt-strength/archive_results.py'
NAME = 'forge-baseline-time-forfeit-causal-20261020-complete'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def inventory(roots, originals):
    files, directories = [], []
    for group, root in roots:
        for directory, names, leaves in os.walk(root, followlinks=False):
            parent = Path(directory)
            names[:] = sorted(n for n in names if parent/n != OUT)
            assert not parent.is_symlink(), parent
            directories.append({'group': group, 'original': str(parent),
                                'payload_path': 'payload/'+str(parent).lstrip('/'),
                                'mode': stat.S_IMODE(parent.stat().st_mode)})
            for name in names:
                assert not (parent/name).is_symlink(), parent/name
            for name in sorted(leaves):
                path = parent/name
                if path == CAUSAL/'ARCHIVE.md':
                    continue
                assert path.is_file() and not path.is_symlink(), path
                files.append(identity(group, path))
    files.extend(identity(group, path) for group, path in originals)
    files.sort(key=lambda row: row['payload_path'])
    directories.sort(key=lambda row: row['payload_path'])
    assert len({row['payload_path'] for row in files}) == len(files)
    return {'files': files, 'directories': directories}


def identity(group, path):
    info = path.stat()
    return {'group': group, 'original': str(path),
            'payload_path': 'payload/'+str(path).lstrip('/'),
            'size': info.st_size, 'sha256': sha(path),
            'mode': stat.S_IMODE(info.st_mode)}


def main():
    assert sha(ARCHIVER) == EXPECTED_ARCHIVER
    assert subprocess.check_output(['git', 'show', 'HEAD:.github/hosted-tt-strength/archive_results.py'], cwd=REPO) == ARCHIVER.read_bytes()
    assert not STAGE.exists(), 'Never reuse archive staging'
    assert not (OUT/'RESULTS.json').exists(), 'Never overwrite an archive receipt'
    protocol = json.loads((CAUSAL/'PROTOCOL.json').read_text())
    summary = json.loads((CAUSAL/'diagnostic-attempt1/summary.json').read_text())
    assert summary['status'] == 'COMPLETE_CAUSAL_DIAGNOSTIC_NO_STRENGTH_CLAIM'
    assert summary['inputs_unchanged'] is True
    source = json.loads((CAUSAL/'SOURCE.json').read_text())
    build = json.loads((CAUSAL/'BUILD.json').read_text())
    assert sha(CAUSAL/'PROTOCOL.json') == summary['frozen_inputs_after']['protocol_sha256']
    assert sha(CAUSAL/'SOURCE.json') == protocol['source_manifest_sha256']
    assert sha(CAUSAL/'BUILD.json') == protocol['build_provenance_sha256']
    assert sha(CAUSAL/'baseline-source.tar') == source['baseline_archive_sha256']
    for name in ['engine', 'core_library']:
        assert sha(protocol[name]['path']) == protocol[name]['sha256']
    exported = Path(source['source_export'])
    assert {str(p.relative_to(exported)): sha(p) for p in exported.rglob('*') if p.is_file()} == source['instrumented_sha256']
    build_directory = Path(protocol['engine']['path']).parent
    assert sha(build_directory/'compile_commands.json') == build['compile_commands_sha256']
    assert sha(build_directory/'CMakeCache.txt') == build['cmake_cache_sha256']
    roots = [('causal-validation', CAUSAL),
             ('instrumented-source-v2', Path(protocol['source_export'])),
             ('instrumented-build-v2', Path(protocol['engine']['path']).parent)]
    originals = [('trusted-archiver', ARCHIVER)]
    for row in protocol['original_inputs'].values():
        path = Path(row['path'])
        if not path.is_absolute():
            path = REPO/path
        assert sha(path) == row['sha256']
        originals.append(('original-hosted-input', path))
    before = inventory(roots, originals)
    save(OUT/'LIVE-BEFORE.json', before)
    STAGE.mkdir()
    for row in before['directories']:
        (STAGE/row['payload_path']).mkdir(parents=True, exist_ok=True)
    for row in before['files']:
        source, destination = Path(row['original']), STAGE/row['payload_path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        assert destination.stat().st_ino != source.stat().st_ino
        assert sha(destination) == row['sha256'] and destination.stat().st_size == row['size']
    after_staging = inventory(roots, originals)
    assert after_staging == before, 'Live originals changed during staging'
    save(OUT/'LIVE-AFTER-STAGING.json', after_staging)
    provenance = STAGE/'archive-provenance'
    provenance.mkdir()
    shutil.copy2(OUT/'archive_complete.py', provenance/'archive_complete.py')
    save(provenance/'LIVE-FILES-AND-MODES.json', before)
    archive_command = [sys.executable, '-B', str(ARCHIVER), '--input', str(STAGE),
                       '--out', str(OUT), '--name', NAME, '--split-size', '67108864']
    command = {'command': archive_command, 'cwd': str(REPO),
               'archiver_sha256': EXPECTED_ARCHIVER,
               'archiver_byte_matches_git_HEAD': True,
               'stage': str(STAGE), 'split_size_bytes': 67108864,
               'excluded_to_prevent_recursion': [str(OUT), str(CAUSAL/'ARCHIVE.md')],
               'engine_executed': False,
               'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(provenance/'ARCHIVE-COMMAND.json', command)
    save(provenance/'STAGING-CHECK.json', {'status': 'PASS', 'live_before_equals_after_staging': True,
                                         'staged_files_hash_equal_live_before': True,
                                         'live_file_count': len(before['files']),
                                         'live_bytes': sum(row['size'] for row in before['files'])})
    save(OUT/'ARCHIVE-COMMAND.json', command)
    result = subprocess.run(archive_command, cwd=REPO, capture_output=True, timeout=120)
    (OUT/'archive.stdout').write_bytes(result.stdout)
    (OUT/'archive.stderr').write_bytes(result.stderr)
    save(OUT/'ARCHIVE-EXIT.json', {'return_code': result.returncode, 'engine_executed': False})
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    spec = importlib.util.spec_from_file_location('trusted_archive_verifier', ARCHIVER)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    manifest_path = OUT/(NAME+'.manifest.json')
    manifest = tool.verify_archive(manifest_path)
    payload = {row['path']: row for row in manifest['files']}
    staged = {str(path.relative_to(STAGE)): {'size': path.stat().st_size, 'sha256': sha(path)}
              for path in STAGE.rglob('*') if path.is_file()}
    assert set(payload) == set(staged)
    assert all(payload[path]['sha256'] == row['sha256'] and payload[path]['size'] == row['size']
               for path, row in staged.items())
    for row in before['files']:
        archived = payload[row['payload_path']]
        assert (archived['sha256'], archived['size']) == (row['sha256'], row['size'])
    after_archive = inventory(roots, originals)
    assert after_archive == before, 'Live originals changed during archival verification'
    save(OUT/'LIVE-AFTER-ARCHIVE.json', after_archive)
    candidates = []
    for rel in ['baseline-source.tar', 'diagnostic-attempt1/warm/engine-events.jsonl',
                'diagnostic-attempt1/warm/manager-events.jsonl']:
        path = CAUSAL/rel
        archived = payload['payload/'+str(path).lstrip('/')]
        assert sha(path) == archived['sha256'] and path.stat().st_size == archived['size']
        candidates.append({'gitignore_line': '/'+str(path.relative_to(REPO)),
                           'live_path': str(path), 'archive_member': 'files/'+archived['path'],
                           'size': archived['size'], 'sha256': archived['sha256'],
                           'verified_live_and_archive_byte_match': True, 'ignore_applied': False})
    save(OUT/'IGNORE-CANDIDATES.json', {'scope': 'Exact paths only; originals retained. No Git or ignore-file edit performed.',
                                      'candidates': candidates})
    counts = {group: sum(row['group'] == group for row in before['files'])
              for group in sorted({row['group'] for row in before['files']})}
    receipt = {'status': 'PASS_COMPLETE_ARCHIVE_VERIFIED',
               'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'archive': manifest['archive'], 'manifest': str(manifest_path),
               'manifest_sha256': sha(manifest_path), 'parts': manifest['parts'],
               'split_size_bytes': manifest['split_size'], 'live_file_counts': counts,
               'live_file_count': len(before['files']), 'archive_payload_file_count': len(payload),
               'live_bytes': sum(row['size'] for row in before['files']),
               'archive_payload_bytes': sum(row['size'] for row in payload.values()),
               'live_originals_unchanged_before_after_staging_and_archive': True,
               'all_staged_and_reassembled_payload_hashes_verified': True,
               'originals_and_staging_retained': True, 'engine_executed': False,
               'new_games_or_searches': 0, 'source_baseline_tar_included': True,
               'archiver_sha256': EXPECTED_ARCHIVER, 'scope': command['excluded_to_prevent_recursion'],
               'prospective_ignored_raw_files_byte_match': candidates}
    save(OUT/'RESULTS.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'archive', 'manifest_sha256', 'live_file_counts',
                                            'live_file_count', 'archive_payload_file_count', 'engine_executed']}))


if __name__ == '__main__':
    main()
