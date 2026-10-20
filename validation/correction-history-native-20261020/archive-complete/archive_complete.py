#!/usr/bin/env python3
"""Freeze complete isolated 6.4.18 evidence after explicit root clearance.

No engine execution, Git mutation, ignore edit, deletion, or prior-6.4.17 archive copy.
Originals, stage, trusted-archiver split outputs and verification receipts remain local.
"""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import tarfile

REPO = Path('/workspace/dwqww')
EXPERIMENT = REPO / 'validation/correction-history-native-20261020'
WINDOWS = REPO / 'validation/correction-history-windows-20261020'
OUT = EXPERIMENT / 'archive-complete'
STAGE = Path('/workspace/.cloud-setup/forge-correction-fc51-complete-evidence-stage')
ARCHIVER = REPO / '.github/hosted-tt-strength/archive_results.py'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
COMMIT = 'fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
PARENT = '47f0560221d986e41a309853e1295c557fcf5bf6'
NAME = 'forge-correction-fc51e43-20261020-complete'
SPLIT_SIZE = 64 * 1024 * 1024


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def load(path):
    return json.loads(path.read_text())


def identity(group, path):
    assert path.is_file() and not path.is_symlink(), path
    before = path.stat()
    digest = sha(path)
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), path
    return {'group': group, 'original': str(path),
            'payload_path': 'payload/' + str(path).lstrip('/'),
            'size': before.st_size, 'sha256': digest,
            'mode': stat.S_IMODE(before.st_mode), 'mtime_ns': before.st_mtime_ns}


def inventory(roots, originals):
    files, directories = [], []
    for group, root in roots:
        assert root.is_dir() and not root.is_symlink(), root
        for directory, names, leaves in os.walk(root, followlinks=False):
            parent = Path(directory)
            names[:] = sorted(name for name in names if parent / name != OUT)
            assert not parent.is_symlink(), parent
            directories.append({'group': group, 'original': str(parent),
                                'payload_path': 'payload/' + str(parent).lstrip('/'),
                                'mode': stat.S_IMODE(parent.stat().st_mode)})
            for name in names:
                assert not (parent / name).is_symlink(), parent / name
            for name in sorted(leaves):
                files.append(identity(group, parent / name))
    files.extend(identity(group, path) for group, path in originals)
    files.sort(key=lambda row: row['payload_path'])
    directories.sort(key=lambda row: row['payload_path'])
    assert len({row['payload_path'] for row in files}) == len(files), 'Duplicate payload paths'
    assert all(not any('/validation/' + old + '/' in row['original'] for old in ['promotion-see-20261020', 'pin-mask-see-20261020', 'pin-aware-see-20261020', 'double-extension-path-20261020']) for row in files)
    return {'files': files, 'directories': directories}


def roots_and_originals():
    scope = load(OUT / 'INPUT-SCOPE.json')
    return ([(row['group'], Path(row['path'])) for row in scope['directory_roots']],
            [(row['group'], Path(row['path'])) for row in scope['original_files']])


def validate_frozen_sources():
    # IO-only: validate saved root-audited source/build maps and original TAR.
    # This repeats byte identity, not an independent Git revision authenticity audit.
    native = load(EXPERIMENT / 'ORIGINALS-FINAL-SHA256.json')
    final = load(EXPERIMENT / 'FINAL-RECEIPT.json')
    assert native['source_commit'] == final['source_commit'] == COMMIT
    for label, tree in native['trees'].items():
        root = Path(tree['root'])
        actual = {p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
                  for p in root.rglob('*') if p.is_file()}
        assert actual == tree['files'], 'Frozen native tree mismatch: ' + label
    for label, item in native['single_files'].items():
        path = Path(item['path'])
        assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], label
    original_tar = EXPERIMENT / 'frozen-source-fc51e43.tar'
    assert sha(original_tar) == final['source_archive_sha256']
    with tarfile.open(original_tar, 'r:') as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        assert len({member.name for member in members}) == len(members)
        tar_files = {member.name: {'sha256': hashlib.sha256(archive.extractfile(member).read()).hexdigest(),
                                   'bytes': member.size} for member in members}
    assert tar_files == native['trees']['source']['files']
    windows_source = Path('/workspace/.cloud-setup/windows6418-source')
    expected = load(WINDOWS / 'source-hashes.json')
    actual = {p.relative_to(windows_source).as_posix(): sha(p)
              for p in windows_source.rglob('*') if p.is_file()}
    assert actual == expected, 'Frozen Windows source manifest mismatch'
    native_source = native['trees']['source']['files']
    assert all(name in native_source and native_source[name]['sha256'] == value
               for name, value in expected.items()), 'Native/Windows source mismatch'
    windows_evidence = load(WINDOWS / 'evidence-SHA256.json')
    for name, item in windows_evidence.items():
        path = WINDOWS / name
        assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], name
    for profile in ['release', 'asan', 'tsan']:
        result = load(EXPERIMENT / ('frozen-' + profile + '-attempt1/summary.json'))
        assert result['status'] in {'PASS', 'FAILED'}, 'Native writer still running: ' + profile
    win_final = load(WINDOWS / 'final-verification.json')
    assert win_final['source_and_tests_commit'] == COMMIT
    assert win_final['status'] in {'passed', 'failed'}, 'Windows writer not complete'


def prospective_ignore(path):
    # Only exact duplicate raw inputs from the new18 validation trees qualify.
    # User release ZIP/EXEs and all outside prototypes remain excluded.
    if path.is_relative_to(EXPERIMENT):
        relative = path.relative_to(EXPERIMENT).as_posix()
        return relative.startswith('frozen-source-') and path.suffix.lower() == '.tar'
    if not path.is_relative_to(WINDOWS):
        return False
    relative = path.relative_to(WINDOWS).as_posix()
    if relative.startswith('originals/binaries/') and path.suffix.lower() == '.exe':
        return True
    if relative.startswith('originals/static-core/') and path.suffix.lower() == '.a':
        return True
    return relative in {'runtime-attempt1/disassembly.log', 'windows-originals.zip'}


def main():
    assert sys.dont_write_bytecode, 'Use Python -B / PYTHONDONTWRITEBYTECODE=1 to keep imported helpers unchanged'
    assert sys.argv[1:] == ['--root-clearance', '18-ARCHIVE-AUTHORIZED'], 'Explicit root-clearance invocation required'
    clearance = load(OUT / 'ROOT-CLEARANCE.json')
    assert clearance['authorization'] == '18 COMPLETE ARCHIVE TASK AUTHORIZED' and clearance['provided_by'] == '/root'
    assert clearance['included_writers_quiescent'] is True
    assert not STAGE.exists(), 'Never reuse staging or overwrite evidence'
    assert not (OUT / 'RESULTS.json').exists(), 'Never overwrite an archive receipt'
    assert sha(ARCHIVER) == EXPECTED_ARCHIVER
    validate_frozen_sources()
    roots, originals = roots_and_originals()
    before = inventory(roots, originals)
    save(OUT / 'LIVE-BEFORE.json', before)
    STAGE.mkdir()
    for row in before['directories']:
        (STAGE / row['payload_path']).mkdir(parents=True, exist_ok=True)
    for row in before['files']:
        source, destination = Path(row['original']), STAGE / row['payload_path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        assert destination.stat().st_ino != source.stat().st_ino, source
        assert sha(destination) == row['sha256'] and destination.stat().st_size == row['size'], source
        assert stat.S_IMODE(destination.stat().st_mode) == row['mode'], source
    after_staging = inventory(roots, originals)
    save(OUT / 'LIVE-AFTER-STAGING.json', after_staging)
    assert after_staging == before, 'Included originals changed during staging; retain this failed attempt'
    provenance = STAGE / 'archive-provenance'
    provenance.mkdir()
    for name in ['archive_complete.py', 'INPUT-SCOPE.json', 'PREPARATION.json', 'DRIVER-REVIEW.json', 'PARENT-ADAPTATION.json', 'STATIC-CHECKS.json', 'PREPARATION-READ-NOTES.json', 'driver-adaptation.diff', 'ROOT-CLEARANCE.json']:
        shutil.copy2(OUT / name, provenance / name)
    save(provenance / 'LIVE-FILES-AND-MODES.json', before)
    command = {'operation': 'unchanged trusted archive_results.archive_results followed by verify_archive',
               'driver_command': [sys.executable, '-B', str(Path(__file__)), '--root-clearance', '18-ARCHIVE-AUTHORIZED'],
               'archiver_path': str(ARCHIVER), 'archiver_sha256': EXPECTED_ARCHIVER,
               'trusted_archiver_exact_pinned_hash': True, 'git_commands_executed': False,
               'frozen_candidate_source': COMMIT, 'parent_source': PARENT,
               'input': str(STAGE), 'output': str(OUT), 'archive_name': NAME,
               'split_size_bytes': SPLIT_SIZE, 'engine_executed': False,
               'excluded_to_prevent_recursion': [str(OUT)],
               'separate_experiments_excluded': ['.github/hosted-correction-history-strength', 'validation/hosted-correction-history-strength-20261020'],
               'older_evidence_reference':'Parent17andolder experiment trees remain in verified archives/Git. Only exact parent17core referenced by nativeREDproof is included, not its whole build. Full correction-history original attempt1andattempt2 prototype trees are directly included.',
               'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(provenance / 'ARCHIVE-COMMAND.json', command)
    save(provenance / 'STAGING-CHECK.json', {'status': 'PASS', 'live_before_equals_after_staging': True,
         'staged_file_hashes_sizes_modes_equal_live_before': True, 'live_file_count': len(before['files']),
         'live_bytes': sum(row['size'] for row in before['files'])})
    save(OUT / 'ARCHIVE-COMMAND.json', command)
    spec = importlib.util.spec_from_file_location('trusted_archive_results', ARCHIVER)
    trusted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trusted)
    manifest_path = trusted.archive_results(STAGE, OUT, NAME, SPLIT_SIZE)
    manifest = trusted.verify_archive(manifest_path)
    payload = {row['path']: row for row in manifest['files']}
    staged = {path.relative_to(STAGE).as_posix(): {'size': path.stat().st_size, 'sha256': sha(path)}
              for path in STAGE.rglob('*') if path.is_file()}
    assert set(payload) == set(staged)
    assert all((payload[name]['sha256'], payload[name]['size']) == (item['sha256'], item['size']) for name, item in staged.items())
    for row in before['files']:
        archived = payload[row['payload_path']]
        assert (archived['sha256'], archived['size']) == (row['sha256'], row['size'])
    after_archive = inventory(roots, originals)
    save(OUT / 'LIVE-AFTER-ARCHIVE.json', after_archive)
    assert after_archive == before, 'Included originals changed during archive verification; retain this failed attempt'
    candidates = []
    for row in before['files']:
        path = Path(row['original'])
        if not prospective_ignore(path):
            continue
        archived = payload[row['payload_path']]
        assert sha(path) == archived['sha256'] and path.stat().st_size == archived['size']
        candidates.append({'gitignore_line': '/' + path.relative_to(REPO).as_posix(), 'live_path': str(path),
                           'archive_member': 'files/' + archived['path'], 'size': archived['size'],
                           'sha256': archived['sha256'], 'verified_live_and_archive_byte_match': True, 'ignore_applied': False})
    save(OUT / 'IGNORE-CANDIDATES.json', {'scope': 'Only exact new18 validation raw TAR, Windows original binaries/core, disassembly and windows-originals.zip paths verified against archive. User-facing release ZIP/exes and prototype files excluded; no Git or ignore edit.', 'candidates': candidates})
    counts = {group: sum(row['group'] == group for row in before['files']) for group in sorted({row['group'] for row in before['files']})}
    receipt = {'status': 'PASS_COMPLETE_18_ARCHIVE_VERIFIED', 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_commit': COMMIT, 'parent_source_commit': PARENT, 'archive': manifest['archive'],
               'manifest': str(manifest_path), 'manifest_sha256': sha(manifest_path), 'parts': manifest['parts'],
               'split_size_bytes': manifest['split_size'], 'live_file_counts': counts, 'live_file_count': len(before['files']),
               'archive_payload_file_count': len(payload), 'live_bytes': sum(row['size'] for row in before['files']),
               'archive_payload_bytes': sum(row['size'] for row in payload.values()),
               'live_originals_unchanged_before_after_staging_and_archive': True,
               'all_staged_and_reassembled_payload_hashes_verified': True, 'all_original_modes_recorded_and_file_modes_copied': True,
               'originals_and_staging_retained': True, 'engine_executed': False, 'new_games_or_searches': 0,
               'archiver_sha256': EXPECTED_ARCHIVER, 'prior_17_or_older_experiment_trees_recopied': False,
               'separate_hosted_strength_experiment_excluded': True,
               'complete_correction_history_research_and_both_prototype_attempts_included':True, 'user_release_zip_and_exes_ignored':False,
               'prospective_ignore_binary_archive_paths': len(candidates), 'ignore_applied': False,
               'scope': 'Complete local 6.4.18 evidence preservation, not validation, publication or an Elo/NPS/native hardware claim.'}
    save(OUT / 'RESULTS.json', receipt)
    print(json.dumps({key: receipt[key] for key in ['status', 'archive', 'manifest_sha256', 'parts', 'live_file_counts', 'live_file_count', 'archive_payload_file_count', 'prospective_ignore_binary_archive_paths', 'engine_executed']}, indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = OUT / 'FAILURE.json'
        if not failure.exists():
            save(failure, {'status': 'FAILED_ATTEMPT_RETAINED', 'error_type': type(error).__name__, 'error': str(error),
                          'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'engine_executed': False})
        raise
