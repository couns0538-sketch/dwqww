#!/usr/bin/env python3
"""Freeze complete isolated 6.4.17 evidence after explicit root clearance.

No engine execution, Git mutation, ignore edit, deletion, or prior-6.4.16 archive copy.
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
import subprocess
import sys

REPO = Path('/workspace/dwqww')
EXPERIMENT = REPO / 'validation/promotion-see-20261020'
OUT = EXPERIMENT / 'archive-complete'
STAGE = Path('/workspace/.cloud-setup/forge-promotion-47f0560-complete-evidence-stage')
ARCHIVER = REPO / '.github/hosted-tt-strength/archive_results.py'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
COMMIT = '47f0560221d986e41a309853e1295c557fcf5bf6'
PARENT = '553caef144ae2e1b696ba35d7a0eb1a50a03fde9'
NAME = 'forge-promotion-47f0560-20261020-complete'
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


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=REPO)


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
    assert all(not any('/' + old + '/' in row['original'] for old in ['pin-mask-see-20261020', 'pin-aware-see-20261020', 'double-extension-path-20261020']) for row in files)
    return {'files': files, 'directories': directories}


def roots_and_originals():
    scope = load(OUT / 'INPUT-SCOPE.json')
    return ([(row['group'], Path(row['path'])) for row in scope['directory_roots']],
            [(row['group'], Path(row['path'])) for row in scope['original_files']])


def validate_frozen_sources():
    for directory, manifest in [
        (Path('/workspace/.cloud-setup/forge-promotion-source'), EXPERIMENT / 'native/frozen-source-47f0560-files.json'),
        (Path('/workspace/.cloud-setup/forge-promotion-windows-source'), EXPERIMENT / 'windows/source-hashes.json')]:
        expected = load(manifest)
        actual = {path.relative_to(directory).as_posix(): sha(path) for path in directory.rglob('*') if path.is_file()}
        assert actual == expected, str(directory) + ' differs from frozen manifest'
        for name, digest in expected.items():
            assert hashlib.sha256(git('show', COMMIT + ':' + name)).hexdigest() == digest, name
    # Preservation can retain a completed failed gate; it never turns failure
    # into acceptance. Root clearance attests that every included writer stopped.
    for profile in ['release', 'asan', 'tsan']:
        result = load(EXPERIMENT / ('native/frozen-' + profile + '-attempt1/summary.json'))
        assert result['status'] in {'PASS', 'FAILED'}, 'Native writer still running: ' + profile
    for name in ['windows/final-verification.json', 'windows/independent-audit.json']:
        result = load(EXPERIMENT / name)
        assert result['status'] in {'passed', 'failed'}, 'Windows writer not complete: ' + name


def prospective_ignore(path):
    # Only new17 validation raw files. User-facing releases and prototype files
    # remain outside this list even though their bytes are archived.
    if not path.is_relative_to(EXPERIMENT):
        return False
    relative = path.relative_to(EXPERIMENT).as_posix()
    if relative.startswith('native/') and path.suffix.lower() == '.tar':
        return True
    if relative.startswith('windows/originals/binaries/') and path.suffix.lower() == '.exe':
        return True
    if relative.startswith('windows/originals/static-core/') and path.suffix.lower() == '.a':
        return True
    return relative in {'windows/runtime-attempt1/disassembly.log', 'windows/windows-originals.zip'}


def main():
    assert sys.dont_write_bytecode, 'Use Python -B / PYTHONDONTWRITEBYTECODE=1 to keep imported helpers unchanged'
    assert sys.argv[1:] == ['--root-clearance', '17-ARCHIVE-CLEAR'], 'Explicit root-clearance invocation required'
    clearance = load(OUT / 'ROOT-CLEARANCE.json')
    assert clearance['authorization'] == '17 ARCHIVE CLEAR' and clearance['provided_by'] == '/root'
    assert clearance['included_writers_quiescent'] is True
    assert not STAGE.exists(), 'Never reuse staging or overwrite evidence'
    assert not (OUT / 'RESULTS.json').exists(), 'Never overwrite an archive receipt'
    assert sha(ARCHIVER) == EXPECTED_ARCHIVER
    assert git('show', 'HEAD:.github/hosted-tt-strength/archive_results.py') == ARCHIVER.read_bytes()
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
    for name in ['archive_complete.py', 'INPUT-SCOPE.json', 'PREPARATION.json', 'DRIVER-REVIEW.json', 'PARENT-ADAPTATION.json', 'STATIC-CHECKS.json', 'STATIC-CHECKS-FAILED-ATTEMPT1.json', 'driver-adaptation.diff', 'ROOT-CLEARANCE.json']:
        shutil.copy2(OUT / name, provenance / name)
    save(provenance / 'LIVE-FILES-AND-MODES.json', before)
    command = {'operation': 'unchanged trusted archive_results.archive_results followed by verify_archive',
               'driver_command': [sys.executable, '-B', str(Path(__file__)), '--root-clearance', '17-ARCHIVE-CLEAR'],
               'archiver_path': str(ARCHIVER), 'archiver_sha256': EXPECTED_ARCHIVER,
               'archiver_byte_matches_git_HEAD': True, 'git_head_at_clearance': git('rev-parse', 'HEAD').decode().strip(),
               'frozen_candidate_source': COMMIT, 'parent_source': PARENT,
               'input': str(STAGE), 'output': str(OUT), 'archive_name': NAME,
               'split_size_bytes': SPLIT_SIZE, 'engine_executed': False,
               'excluded_to_prevent_recursion': [str(OUT)],
               'separate_experiments_excluded': ['.github/hosted-promotion-see-strength', 'validation/hosted-promotion-see-strength-20261020'],
               'older_evidence_reference':'Parent16 and older experiment trees remain in their verified archives and Git. Full local promotion research/prototype is included because it directly establishes this repair; no older validation/build/release tree is recopied.',
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
    save(OUT / 'IGNORE-CANDIDATES.json', {'scope': 'Only exact new17 validation raw TAR, Windows original binaries/core, disassembly and windows-originals.zip paths verified against archive. User-facing release ZIP/exes and prototype files excluded; no Git or ignore edit.', 'candidates': candidates})
    counts = {group: sum(row['group'] == group for row in before['files']) for group in sorted({row['group'] for row in before['files']})}
    receipt = {'status': 'PASS_COMPLETE_17_ARCHIVE_VERIFIED', 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_commit': COMMIT, 'parent_source_commit': PARENT, 'archive': manifest['archive'],
               'manifest': str(manifest_path), 'manifest_sha256': sha(manifest_path), 'parts': manifest['parts'],
               'split_size_bytes': manifest['split_size'], 'live_file_counts': counts, 'live_file_count': len(before['files']),
               'archive_payload_file_count': len(payload), 'live_bytes': sum(row['size'] for row in before['files']),
               'archive_payload_bytes': sum(row['size'] for row in payload.values()),
               'live_originals_unchanged_before_after_staging_and_archive': True,
               'all_staged_and_reassembled_payload_hashes_verified': True, 'all_original_modes_recorded_and_file_modes_copied': True,
               'originals_and_staging_retained': True, 'engine_executed': False, 'new_games_or_searches': 0,
               'archiver_sha256': EXPECTED_ARCHIVER, 'prior_16_or_older_experiment_trees_recopied': False,
               'separate_hosted_strength_experiment_excluded': True,
               'complete_promotion_research_and_prototype_included':True, 'user_release_zip_and_exes_ignored':False,
               'prospective_ignore_binary_archive_paths': len(candidates), 'ignore_applied': False,
               'scope': 'Complete local 6.4.17 evidence preservation, not validation, publication or an Elo/NPS/native hardware claim.'}
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
