#!/usr/bin/env python3
"""Freeze complete isolated 6.4.20 evidence after explicit root clearance.

No engine execution, Git mutation, ignore edit, deletion, or prior-6.4.19 archive copy.
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
EXPERIMENT = REPO / 'validation/pawn-span-fill-20261020'
NATIVE = REPO / 'validation/pawn-span-fill-native-20261020'
WINDOWS = REPO / 'validation/pawn-span-fill-windows-20261020'
CAPTURES = REPO / 'validation/hosted-pawn-span-performance-20261020/actual-five-captures'
OUT = EXPERIMENT / 'archive-complete'
STAGE = Path('/workspace/.cloud-setup/forge-pawn-span-fc23918-complete-evidence-stage')
ARCHIVER = REPO / '.github/hosted-tt-strength/archive_results.py'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
COMMIT = 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
PARENT = '61f598056572dfade6994af8ad2e38817cd28aa3'
NAME = 'forge-pawn-span-fc23918-20261020-complete'
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
            names[:] = sorted(name for name in names if parent / name not in {OUT, EXPERIMENT / 'coordination'})
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
    assert all('/archive-complete/' not in row['original'] and '/coordination/' not in row['original'] for row in files)
    return {'files': files, 'directories': directories}


def roots_and_originals():
    scope = load(OUT / 'INPUT-SCOPE.json')
    return ([(row['group'], Path(row['path'])) for row in scope['directory_roots']],
            [(row['group'], Path(row['path'])) for row in scope['original_files']])


def verify_hash_manifest(directory, path, exact=False):
    declared = {}
    for line in path.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts and name not in declared
        assert sha(directory / relative) == digest, name
        declared[name] = digest
    if exact:
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
        assert actual == set(declared) | {path.relative_to(directory).as_posix()}
    return declared


def validate_frozen_sources():
    # Saved/root-qualified identities only: no Git commands or engine execution.
    native = load(NATIVE / 'ORIGINALS-FINAL-SHA256.json')
    final = load(NATIVE / 'FINAL-RECEIPT.json')
    assert sha(NATIVE / 'FINAL-RECEIPT.json') == '8bbe2d327109a09a92f9666043aef848cad3004e3638d5fd8df60f01c6cff609'
    assert native['source_commit'] == final['source_commit'] == COMMIT
    assert sha(NATIVE / 'ORIGINALS-FINAL-SHA256.json') == final['originals_snapshot_sha256']
    assert final['status'] == 'STABLE'
    assert final['original_counts'] == {'source': 75, 'release': 163, 'asan': 163, 'tsan': 163}
    assert final['native_ctests'] == 36 and final['default_tsan_active_checks'] == 8
    assert final['exact_cold_warm_searches'] == 56 and final['independent_audit_checks'] == 2363
    native_manifest = verify_hash_manifest(NATIVE, NATIVE / 'EVIDENCE-SHA256SUMS', exact=True)
    assert len(native_manifest) == 242
    for label, tree in native['trees'].items():
        root = Path(tree['root'])
        actual = {p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size,
                                                'mode': stat.S_IMODE(p.stat().st_mode)}
                  for p in root.rglob('*') if p.is_file()}
        assert actual == tree['files'], 'Frozen native tree mismatch: ' + label
        assert len(actual) == final['original_counts'][label]
        directories = {'.': stat.S_IMODE(root.stat().st_mode)}
        directories.update({p.relative_to(root).as_posix(): stat.S_IMODE(p.stat().st_mode)
                            for p in root.rglob('*') if p.is_dir()})
        assert directories == tree['directory_modes'], 'Frozen native directory-mode mismatch: ' + label
    for label, item in native['single_files'].items():
        path = Path(item['path'])
        assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], label
        assert stat.S_IMODE(path.stat().st_mode) == item['mode'], label
    original_tar = NATIVE / 'frozen-source-fc23918.tar'
    assert sha(original_tar) == final['source_archive_sha256']
    with tarfile.open(original_tar, 'r:') as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        assert len({member.name for member in members}) == len(members) == 75
        tar_files = {member.name: {'sha256': hashlib.sha256(archive.extractfile(member).read()).hexdigest(),
                                  'bytes': member.size, 'mode': member.mode} for member in members}
    # TAR mode metadata and post-extraction live modes are different identities.
    # Authenticate TAR contents; live file/directory modes were checked above.
    assert {name: {'sha256': item['sha256'], 'bytes': item['bytes']}
            for name, item in tar_files.items()} == {
        name: {'sha256': item['sha256'], 'bytes': item['bytes']}
        for name, item in native['trees']['source']['files'].items()}
    root_native = load(EXPERIMENT / 'root-verification/NATIVE.json')
    assert root_native['status'] == 'PASS_ROOT_FULL_NATIVE20_ORIGINALS_AND_GIT_SOURCE_REVIEW'
    assert root_native['source_commit'] == COMMIT and root_native['ctest'] == 36
    assert root_native['whole_live_original_trees'] == final['original_counts']
    assert root_native['evidence_records_rehashed'] == 242 and root_native['exact_evidence_tree_verified'] is True
    windows_source = Path('/workspace/.cloud-setup/windows6420-source')
    expected = load(WINDOWS / 'source-hashes.json')
    actual = {p.relative_to(windows_source).as_posix(): sha(p)
              for p in windows_source.rglob('*') if p.is_file()}
    assert actual == expected and len(expected) == 72
    assert all(name in native['trees']['source']['files'] and
               native['trees']['source']['files'][name]['sha256'] == value
               for name, value in expected.items())
    win_final = load(WINDOWS / 'FINAL-STATUS.json')
    assert win_final['source_commit'] == COMMIT
    assert win_final['status'] == 'WINDOWS20_CANDIDATE_VALIDATED_NOT_ELO_ACCEPTED'
    assert sha(REPO / win_final['artifact']) == win_final['artifact_sha256']
    runtime = load(WINDOWS / 'runtime-attempt1/result.json')
    assert runtime['status'] == 'passed' and runtime['source_and_tests_commit'] == COMMIT
    assert len(runtime['checks']) == 11 and all(row['exit_code'] == 0 for row in runtime['checks'])
    assert runtime['bench11_nodes'] == 352313 and runtime['pawn_span_checks'] == 37320
    assert runtime['pawn_span_failures'] == 0 and runtime['runtime_psqt_checks'] == 347
    assert runtime['input_sha256_before'] == runtime['input_sha256_after']
    for profile in ['release', 'asan', 'tsan']:
        receipt = load(NATIVE / ('frozen-' + profile + '-attempt1/summary.json'))
        assert receipt['status'] == 'PASS' and receipt['source_commit'] == COMMIT
        assert len(receipt['ctest_names']) == 12
    # Preserve the existing prototype manifest honestly as historical coverage.
    # The archive's own frozen inventory, not this older list, defines its scope.
    prototype_manifest = verify_hash_manifest(EXPERIMENT, EXPERIMENT / 'EVIDENCE-SHA256SUMS', exact=False)
    assert len(prototype_manifest) >= 112
    capture = load(CAPTURES / 'PROVENANCE.json')
    assert capture['status'] == 'PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE'
    assert capture['final_rehash']['status'] == 'passed'
    executed = CAPTURES / 'owned_process.executed.py'
    assert sha(executed) == capture['helper_sha256'] == capture['helper_sha256_after'] == '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
    for label, entry in capture['captures'].items():
        source = Path('/workspace/.cloud-setup/' + ('lazy-runtime-psqt-native-source' if label == 'baseline' else 'pawn-span-fill-native-source'))
        assert entry['source_sha256_before'] == entry['source_sha256_after']
        assert len(entry['source_sha256_before']) == (74 if label == 'baseline' else 75)
        assert all(sha(source / name) == value for name, value in entry['source_sha256_before'].items())
        assert entry['binary_sha256_before'] == entry['binary_sha256_after']
        for name, path in entry['binary_paths'].items():
            assert sha(Path(path)) == entry['binary_sha256_before'][name]
        for leaf in ['stdout', 'stderr', 'stdin']:
            assert sha(CAPTURES / label / (leaf + '.txt')) == entry[leaf + '_sha256']
    assert sha(REPO / 'validation/lazy-runtime-psqt-native-20261020/ROOT-FROZEN-SOURCE-GATES.json') == capture['captures']['baseline']['source_manifest_sha256']
    assert sha(REPO / 'validation/lazy-runtime-psqt-native-20261020/frozen-release-attempt1/summary.json') == capture['captures']['baseline']['build_receipt_sha256']


def inventory_frozen(before):
    # Root may publish future coordination extras; only recheck the exact frozen list.
    files = [identity(row['group'], Path(row['original'])) for row in before['files']]
    directories = []
    for row in before['directories']:
        path = Path(row['original'])
        assert path.is_dir() and not path.is_symlink()
        directories.append({'group': row['group'], 'original': row['original'],
                            'payload_path': row['payload_path'], 'mode': stat.S_IMODE(path.stat().st_mode)})
    return {'files': files, 'directories': directories}


def prospective_ignore(path):
    # All already published flat raws remain; this archive adds recoverability.
    return False


def main():
    assert sys.dont_write_bytecode, 'Use Python -B / PYTHONDONTWRITEBYTECODE=1 to keep imported helpers unchanged'
    assert sys.argv[1:] == ['--root-clearance', '20-ARCHIVE-AUTHORIZED'], 'Explicit root-clearance invocation required'
    clearance = load(OUT / 'ROOT-CLEARANCE.json')
    assert clearance['authorization'] == '20 COMPLETE ARCHIVE TASK AUTHORIZED' and clearance['provided_by'] == '/root'
    assert clearance['included_writers_quiescent'] is True
    assert clearance['source_commit'] == COMMIT, 'Root clearance source identity differs'
    bindings = clearance.get('frozen_inputs_sha256', {})
    assert isinstance(bindings, dict) and bindings, 'Root proof/docs/source hash bindings required'
    for name, expected in bindings.items():
        path = Path(name)
        if not path.is_absolute():
            path = REPO / path
        assert path.is_file() and not path.is_symlink(), name
        assert sha(path) == expected, 'Root-bound input changed: ' + name
    assert not STAGE.exists(), 'Never reuse staging or overwrite evidence'
    assert not (OUT / 'RESULTS.json').exists(), 'Never overwrite an archive receipt'
    assert sha(ARCHIVER) == EXPECTED_ARCHIVER
    assert not any(OUT.glob(NAME + '.zip*')), 'Never reuse prior archive parts'
    # Freeze only preparation filenames here, before generating archive receipts.
    # This preserves every original checker failure and its exact before-driver.
    preparation_names = sorted(path.name for path in OUT.iterdir() if path.is_file())
    validate_frozen_sources()
    roots, originals = roots_and_originals()
    before = inventory(roots, originals)
    declared = load(OUT / 'INPUT-SCOPE.json').get('explicit_included_via_directory_roots', [])
    for row in declared:
        assert sum(item['original'] == row['path'] for item in before['files']) == 1, row['path']
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
    after_staging = inventory_frozen(before)
    save(OUT / 'LIVE-AFTER-STAGING.json', after_staging)
    assert after_staging == before, 'Included originals changed during staging; retain this failed attempt'
    provenance = STAGE / 'archive-provenance'
    provenance.mkdir()
    for name in preparation_names:
        shutil.copy2(OUT / name, provenance / name)
    save(provenance / 'LIVE-FILES-AND-MODES.json', before)
    command = {'operation': 'unchanged trusted archive_results.archive_results followed by verify_archive',
               'driver_command': [sys.executable, '-B', str(Path(__file__)), '--root-clearance', '20-ARCHIVE-AUTHORIZED'],
               'archiver_path': str(ARCHIVER), 'archiver_sha256': EXPECTED_ARCHIVER,
               'trusted_archiver_exact_pinned_hash': True, 'git_commands_executed': False,
               'frozen_candidate_source': COMMIT, 'parent_source': PARENT,
               'input': str(STAGE), 'output': str(OUT), 'archive_name': NAME,
               'split_size_bytes': SPLIT_SIZE, 'engine_executed': False,
               'excluded_to_prevent_recursion': [str(OUT)],
               'separate_experiments_excluded': ['.github/hosted-pawn-span-performance', 'validation/hosted-pawn-span-performance-20261020 except immutable actual-five-captures', 'prototype coordination subtree'],
               'older_evidence_reference':'Only consumed baseline19 source/engine/core/NNUE object and source/build/root receipts are included, not its complete build/archive. Full20 prototype/source/build/artifact/failure history and immutable actual-five producer captures are included.',
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
    after_archive = inventory_frozen(before)
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
    save(OUT / 'IGNORE-CANDIDATES.json', {'scope': 'No ignore candidates: all already published raw evidence remains directly accessible; archive is additional preservation only. No Git/index/ignore edit.', 'candidates': candidates})
    counts = {group: sum(row['group'] == group for row in before['files']) for group in sorted({row['group'] for row in before['files']})}
    receipt = {'status': 'PASS_COMPLETE_20_ARCHIVE_VERIFIED', 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_commit': COMMIT, 'parent_source_commit': PARENT, 'archive': manifest['archive'],
               'manifest': str(manifest_path), 'manifest_sha256': sha(manifest_path), 'parts': manifest['parts'],
               'split_size_bytes': manifest['split_size'], 'live_file_counts': counts, 'live_file_count': len(before['files']),
               'archive_payload_file_count': len(payload), 'live_bytes': sum(row['size'] for row in before['files']),
               'archive_payload_bytes': sum(row['size'] for row in payload.values()),
               'live_originals_unchanged_before_after_staging_and_archive': True,
               'all_staged_and_reassembled_payload_hashes_verified': True, 'all_original_modes_recorded_and_file_modes_copied': True,
               'originals_and_staging_retained': True, 'engine_executed': False, 'new_games_or_searches': 0,
               'archiver_sha256': EXPECTED_ARCHIVER, 'older_complete_experiment_or_archive_trees_recopied': False,
               'separate_hosted_strength_experiment_excluded': True,
               'complete_pawn_span_prototype_and_original_failures_included':True,
               'immutable_actual_five_producers_and_executed_helper_included':True,
               'frozen_exact_list_after_checks_future_coordination_excluded':True, 'user_release_zip_and_exes_ignored':False,
               'prospective_ignore_binary_archive_paths': len(candidates), 'ignore_applied': False,
               'scope': 'Complete local 6.4.20 evidence preservation, not validation, publication or an Elo/NPS/native hardware claim.'}
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
