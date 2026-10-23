#!/usr/bin/env python3
"""Freeze complete isolated 6.4.23 evidence after explicit root clearance.

No engine execution, Git mutation, ignore edit, deletion, or prior-6.4.22 archive copy.
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
import re
from pathlib import PurePosixPath

REPO = Path('/workspace/dwqww')
EXPERIMENT = REPO / 'validation/tt-refresh-20261021'
NATIVE = REPO / 'validation/tt-refresh-native-20261021'
WINDOWS = REPO / 'validation/tt-refresh-windows-20261021'
CAPTURES = None  # Exact closed capture path is supplied by root, never guessed.
OUT = EXPERIMENT / 'archive-complete'
PREPARATION = EXPERIMENT / 'archive-complete-preparation'
STAGE = Path('/workspace/.cloud-setup/forge-tt-refresh-1d3ed25-complete-evidence-stage')
ARCHIVER = REPO / '.github/hosted-tt-strength/archive_results.py'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
COMMIT = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
PARENT = 'ff2e269c6058be84456e3b98344826d17b0056eb'
NAME = 'forge-tt-refresh-1d3ed25-20261021-complete'
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
    for parent in path.parents:
        assert not parent.is_symlink(), parent
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
            excluded = {OUT, PREPARATION, EXPERIMENT / 'coordination'} | {Path(value) for value in load(OUT / 'INPUT-SCOPE.json').get('excluded_subtrees', [])}
            names[:] = sorted(name for name in names if parent / name not in excluded)
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
    assert all('/archive-complete/' not in row['original'] and '/archive-complete-preparation/' not in row['original'] and '/coordination/' not in row['original'] for row in files)
    return {'files': files, 'directories': directories}


def roots_and_originals():
    scope = load(OUT / 'INPUT-SCOPE.json')
    assert scope['ready'] is True, 'Root must close and bind every selected raw scope first'
    assert all(isinstance(row.get('path'),str) and Path(row['path']).is_absolute() for row in scope['directory_roots']+scope['original_files']), 'No pending or relative scope paths'
    return ([(row['group'], Path(row['path'])) for row in scope['directory_roots']],
            [(row['group'], Path(row['path'])) for row in scope['original_files']])


def verify_hash_manifest(base, path, exact=False, allowed_scope=None):
    # Explicit producer path schema/base, no prefix guessing or normalization.
    scope = allowed_scope or base
    declared = {}
    for line in path.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        assert match is not None, line
        digest, name = match.groups()
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and all(p not in ('','.','..') for p in name.split('/')) and str(relative)==name and name not in declared
        assert not any(c in name for c in ['\\',':','\x00']), name
        target = base / name
        assert target.is_relative_to(scope), target
        assert target.is_file() and not target.is_symlink(), target
        assert all(not p.is_symlink() for p in target.parents), target
        assert sha(target) == digest, name
        declared[name] = digest
    if exact:
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        assert actual == set(declared) | {path.relative_to(base).as_posix()}
    return declared


def validate_snapshot(snapshot):
    for label, tree in snapshot['trees'].items():
        root = Path(tree['root'])
        actual = {f.relative_to(root).as_posix(): {'sha256': sha(f), 'bytes': f.stat().st_size, 'mode': stat.S_IMODE(f.stat().st_mode)} for f in root.rglob('*') if f.is_file()}
        assert actual == tree['files'], 'Original byte/size/live-mode mismatch: '+label
        dirs = {'.': stat.S_IMODE(root.stat().st_mode), **{f.relative_to(root).as_posix(): stat.S_IMODE(f.stat().st_mode) for f in root.rglob('*') if f.is_dir()}}
        assert dirs == tree['directory_modes'], 'Original directory-mode mismatch: '+label
    for label, item in snapshot['single_files'].items():
        path = Path(item['path'])
        assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes'] and stat.S_IMODE(path.stat().st_mode)==item['mode'], label


def validate_frozen_sources():
    # Data-only verification of genuine current23 schemas. Never import/run validators.
    closed = load(OUT/'CLOSED-EVIDENCE-CONTRACT.json')
    assert closed['ready'] is True and closed['source_commit']==COMMIT
    for path, expected in closed['closed_file_hash_bindings'].items():
        assert sha(Path(path)) == expected, path
    native = load(NATIVE/'ORIGINALS-FINAL-SHA256.json')
    final = load(NATIVE/'FINAL-RECEIPT.json')
    assert native['source_commit']==final['source_commit']==COMMIT and final['status']=='STABLE'
    assert final['native_ctests']==42 and final['default_tsan_active_checks']==8 and final['independent_audit_checks']==1185 and final['independent_audit_failed']==0
    assert final['original_counts']=={'source':77,'release':189,'asan':189,'tsan':189} and final['tt_coherence_groups_each_profile']==12 and final['pv_metadata_assertions_each_profile']==56
    assert final['exact_search_parity_required'] is False and final['observational_cold_warm_searches']==0
    assert len(verify_hash_manifest(NATIVE,NATIVE/'EVIDENCE-SHA256SUMS',exact=True))==138
    validate_snapshot(native)
    for profile in ['release','asan','tsan']:
        p=load(NATIVE/('frozen-'+profile+'-attempt1/summary.json'))
        assert p['status']=='PASS' and p['source_commit']==COMMIT and len(p['ctest_names'])==14
        assert p['tt_coherence_contract_actual_groups']==['12'] and p['pv_metadata_contract_actual_summaries']==[['56','0']]
        assert final['native_profiles'][profile]['attempts']==1 and final['native_profiles'][profile]['ctest_count']==14
    original_tar=NATIVE/('frozen-source-'+COMMIT[:7]+'.tar')
    assert sha(original_tar)==final['source_archive_sha256']
    with tarfile.open(original_tar,'r:') as archive:
        members=[m for m in archive.getmembers() if m.isfile()]
        assert len(members)==len({m.name for m in members})==77
        assert not any(m.issym() or m.islnk() for m in archive.getmembers())
        tar_files={m.name:{'sha256':hashlib.sha256(archive.extractfile(m).read()).hexdigest(),'bytes':m.size} for m in members}
    assert tar_files=={n:{'sha256':v['sha256'],'bytes':v['bytes']} for n,v in native['trees']['source']['files'].items()}
    win=load(WINDOWS/'FINAL-STATUS.json')
    assert win['status']=='WINDOWS23_FIRST_CHAIN_QUALIFIED_NOT_ELO_ACCEPTED' and win['source_commit']==COMMIT and win['parent_source_commit']==PARENT
    assert win['source_files']==74 and win['wine_checks_passed']==13 and win['tt_groups']==12 and win['pv_metadata_assertions']==56 and win['independent_artifact_checks_passed']==1827
    assert win['fresh_build_attempts']==win['wine_runtime_attempts']==win['benchmark_producer_attempts']==1
    assert len(verify_hash_manifest(WINDOWS,WINDOWS/'FINAL-SHA256SUMS',exact=True))==275
    assert sha(REPO/win['artifact'])==win['artifact_sha256'] and (REPO/win['artifact']).stat().st_size==win['artifact_bytes']
    assert sha(REPO/win['raw_archive'])==win['raw_archive_sha256']
    originals=load(WINDOWS/'windows-originals-SHA256.json')
    assert len(originals)==259
    for name,row in originals.items():
        assert sha(WINDOWS/name)==row['sha256'] and (WINDOWS/name).stat().st_size==row['bytes'], name
    win_source=Path('/workspace/.cloud-setup/windows6423-source')
    expected=load(WINDOWS/'source-hashes.json')
    actual={p.relative_to(win_source).as_posix():sha(p) for p in win_source.rglob('*') if p.is_file()}
    assert len(actual)==74 and actual==expected and all(native['trees']['source']['files'][name]['sha256']==value for name,value in actual.items())
    runtime=load(WINDOWS/'runtime-attempt1/result.json')
    assert runtime['status']=='passed' and runtime['source_and_tests_commit']==COMMIT and len(runtime['checks'])==13 and all(x['exit_code']==0 for x in runtime['checks']) and runtime['input_sha256_before']==runtime['input_sha256_after']
    assert sha(Path('/workspace/.cloud-setup/windows6423-build/forge.exe'))==win['engine_sha256'] and sha(Path('/workspace/.cloud-setup/windows6423-build/libforge_core.a'))==win['core_sha256']
    consumed=load(OUT/'CONSUMED-INPUT-MAPPINGS.json')
    for path,expected_hash in consumed['expected_original_hashes'].items(): assert sha(Path(path))==expected_hash, path
    captures=Path(closed['actual_captures_path']);cap=load(captures/'PROVENANCE.json')
    assert cap['status']=='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' and cap['final_rehash']['status']=='passed'
    assert len(cap['frozen_inputs'])==189 and cap['final_rehash']['mismatches']==[]
    assert sha(captures/'PROVENANCE.json')==win['native_captures_closed_provenance_sha256']
    for label,row in cap['captures'].items():
        assert row['status']=='PASS_ACTUAL_FIVE_CANONICAL_ROWS' and row['rows']==5 and row['source_sha256_before']==row['source_sha256_after'] and row['binary_sha256_before']==row['binary_sha256_after']
        assert row['process_facts']['returncode']==0 and row['process_facts']['owned_group_empty_after_cleanup'] is True
        for leaf in ['stdin','stdout','stderr']:assert sha(captures/label/(leaf+'.txt'))==row[leaf+'_sha256']
    # Snapshot only the closed qualification; active launch/match/READY metadata is excluded.


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
    assert Path(__file__).resolve().parent==OUT, 'Preparation source is not an execution location; root must promote reviewed files first'
    assert sys.dont_write_bytecode, 'Use Python -B / PYTHONDONTWRITEBYTECODE=1 to keep imported helpers unchanged'
    assert sys.argv[1:] == ['--root-clearance', '23-ARCHIVE-AUTHORIZED'], 'Explicit root-clearance invocation required'
    clearance = load(OUT / 'ROOT-CLEARANCE.json')
    assert clearance['authorization'] == '23 COMPLETE ARCHIVE TASK AUTHORIZED' and clearance['provided_by'] == '/root'
    assert clearance.get('authorized') is True and clearance['included_writers_quiescent'] is True
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
    for row in sorted(before['directories'], key=lambda r: len(Path(r['payload_path']).parts), reverse=True):
        target=STAGE/row['payload_path']
        os.chmod(target,row['mode'])  # New stage only; never chmod originals.
        assert stat.S_IMODE(target.stat().st_mode)==row['mode']
    after_staging = inventory_frozen(before)
    save(OUT / 'LIVE-AFTER-STAGING.json', after_staging)
    assert after_staging == before, 'Included originals changed during staging; retain this failed attempt'
    provenance = STAGE / 'archive-provenance'
    provenance.mkdir()
    for name in preparation_names:
        shutil.copy2(OUT / name, provenance / name)
    save(provenance / 'LIVE-FILES-AND-MODES.json', before)
    command = {'operation': 'unchanged trusted archive_results.archive_results followed by verify_archive',
               'driver_command': [sys.executable, '-B', str(Path(__file__)), '--root-clearance', '23-ARCHIVE-AUTHORIZED'],
               'archiver_path': str(ARCHIVER), 'archiver_sha256': EXPECTED_ARCHIVER,
               'trusted_archiver_exact_pinned_hash': True, 'git_commands_executed': False,
               'frozen_candidate_source': COMMIT, 'parent_source': PARENT,
               'input': str(STAGE), 'output': str(OUT), 'archive_name': NAME,
               'split_size_bytes': SPLIT_SIZE, 'engine_executed': False,
               'excluded_to_prevent_recursion': [str(OUT)],
               'separate_experiments_excluded': ['Active23finalreview/READY/launch/matchmetadata and live docs/skills', 'Alloldercompletearchives', 'Coordination outside boundedqualification scope'],
               'older_evidence_reference':'Only exact consumed parent22 Windows604/native source+references and historicalPV21RED proof/core/header/executable inputs are included. No older complete archive. Closed capture preparation needed for Windows23qualification is included; activefinalreview/launch/matchdata excluded.',
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
    receipt = {'status': 'PASS_COMPLETE_23_ARCHIVE_VERIFIED', 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
               'bounded_qualified23_source_native_windows_originals_included':True,
               'immutable_actual_five_producers_and_executed_helper_included':True,
               'frozen_exact_list_after_checks_future_coordination_excluded':True, 'user_release_zip_and_exes_ignored':False,
               'prospective_ignore_binary_archive_paths': len(candidates), 'ignore_applied': False,
               'scope': 'Bounded complete23 qualification-recovery scope, not all currentwork, new validation, publication or Elo/NPS/native hardware evidence.'}
    save(OUT / 'RESULTS.json', receipt)
    print(json.dumps({key: receipt[key] for key in ['status', 'archive', 'manifest_sha256', 'parts', 'live_file_counts', 'live_file_count', 'archive_payload_file_count', 'prospective_ignore_binary_archive_paths', 'engine_executed']}, indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = OUT / 'FAILURE.json'
        if OUT.is_dir() and Path(__file__).resolve().parent==OUT and not failure.exists():
            save(failure, {'status': 'FAILED_ATTEMPT_RETAINED', 'error_type': type(error).__name__, 'error': str(error),
                          'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'engine_executed': False})
        raise
