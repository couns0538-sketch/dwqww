#!/usr/bin/env python3
"""Freeze complete isolated 6.4.21 evidence after explicit root clearance.

No engine execution, Git mutation, ignore edit, deletion, or prior-6.4.20 archive copy.
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
EXPERIMENT = REPO / 'validation/nearest-pawn-distance-20261020'
NATIVE = REPO / 'validation/nearest-pawn-native-20261020'
WINDOWS = REPO / 'validation/nearest-pawn-windows-20261021'
CAPTURES = None  # Exact closed capture path is supplied by root, never guessed.
OUT = EXPERIMENT / 'archive-complete'
PREPARATION = EXPERIMENT / 'archive-complete-preparation'
STAGE = Path('/workspace/.cloud-setup/forge-nearest-pawn-2e151d0-complete-evidence-stage')
ARCHIVER = REPO / '.github/hosted-tt-strength/archive_results.py'
EXPECTED_ARCHIVER = '952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
COMMIT = '2e151d019bc58dff2ab4e76e99ef99516af8d222'
PARENT = 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
NAME = 'forge-nearest-pawn-2e151d0-20261020-complete'
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
    # No Git/engines/retests. This function is invoked only after explicit root archive clearance.
    native = load(NATIVE/'ORIGINALS-FINAL-SHA256.json')
    final = load(NATIVE/'FINAL-RECEIPT.json')
    assert sha(NATIVE/'FINAL-RECEIPT.json')=='4b24b57e087ffc97149e66fc15bcfc551ccd6649692660010513502c5b9d3390'
    assert sha(NATIVE/'EVIDENCE-SHA256SUMS')=='8a5489d9c75575b02f9081a522ca5e9732dc5b0d57656a0a5dcc30b34fd6a79e'
    assert native['source_commit']==final['source_commit']==COMMIT and final['status']=='STABLE'
    assert sha(NATIVE/'ORIGINALS-FINAL-SHA256.json')==final['originals_snapshot_sha256']=='1c7e57f6d6f193af6597f18f4c3eb15789522664df7665f0742e2909d1d19b8d'
    assert final['original_counts']=={'source':76,'release':176,'asan':176,'tsan':176}
    assert final['native_ctests']==39 and final['default_tsan_active_checks']==8 and final['exact_cold_warm_searches']==56 and final['independent_audit_checks']==2421
    assert len(verify_hash_manifest(NATIVE,NATIVE/'EVIDENCE-SHA256SUMS',exact=True))==245
    validate_snapshot(native)
    for profile in ['release','asan','tsan']:
        receipt=load(NATIVE/('frozen-'+profile+'-attempt1/summary.json'))
        assert receipt['status']=='PASS' and receipt['source_commit']==COMMIT and len(receipt['ctest_names'])==13
        assert receipt['nearest_pawn_contract_actual_summaries']==[['395840','791680','0']] and receipt['nearest_constexpr_assertions']==6
        assert receipt['pawn_span_contract_actual_summaries']==[['37320','0']] and receipt['runtime_psqt_contract_actual_summaries']==[['347','0']]
        assert final['native_profiles'][profile]['attempts']==1 and final['native_profiles'][profile]['ctest_count']==13
    original_tar=NATIVE/'frozen-source-2e151d0.tar'
    assert sha(original_tar)==final['source_archive_sha256']
    with tarfile.open(original_tar,'r:') as archive:
        members=[m for m in archive.getmembers() if m.isfile()]
        assert len(members)==len({m.name for m in members})==76
        tar_files={m.name:{'sha256':hashlib.sha256(archive.extractfile(m).read()).hexdigest(),'bytes':m.size,'mode':m.mode} for m in members}
    # Authenticate original TAR bytes; its mode metadata is distinct from live extracted-source modes.
    assert {n:{'sha256':r['sha256'],'bytes':r['bytes']} for n,r in tar_files.items()}=={n:{'sha256':r['sha256'],'bytes':r['bytes']} for n,r in native['trees']['source']['files'].items()}
    root_native=load(EXPERIMENT/'root-verification/NATIVE.json')
    assert root_native['status']=='PASS_ROOT_FULL_NATIVE21_ORIGINALS_AND_GIT_SOURCE_REVIEW' and root_native['source_commit']==COMMIT
    assert root_native['ctest']==39 and root_native['whole_live_original_trees']==final['original_counts'] and root_native['whole_live_original_files']==604
    assert root_native['evidence_records_rehashed']==245 and root_native['exact_evidence_tree_verified'] is True
    prototype=EXPERIMENT/'native-release'
    assert len(verify_hash_manifest(prototype,prototype/'EVIDENCE-SHA256SUMS',exact=True))==167
    proto=load(prototype/'ORIGINALS-FINAL-SHA256.json');validate_snapshot(proto)
    assert len(proto['trees']['source']['files'])==76 and len(proto['trees']['release']['files'])==176 and len(proto['trees']['baseline_source']['files'])==75
    assert proto['source_commit'] is None and proto['version_metadata']=='6.4.20' and proto['baseline_source_commit']==PARENT
    public=load(EXPERIMENT/'public-diff/PROBE-RECEIPT.json')
    assert public['status']=='PASS_EXACT_95_PUBLIC_EVALUATION_AND_FULL_TRACE_ROWS' and public['compared_integer_fields']==61465
    for name,value in public['files_sha256'].items():assert sha(EXPERIMENT/'public-diff'/name)==value
    # Never project mutable Windows or future producer schemas from an earlier release.
    # Root supplies exact closed receipt hashes and observed runtime/helper fields here.
    closed=load(OUT/'CLOSED-EVIDENCE-CONTRACT.json')
    assert closed['ready'] is True, 'Windows and actual producer captures must close before any mutable-path read'
    assert closed['source_commit']==COMMIT
    for item in closed['closed_file_bindings']:
        assert sha(Path(item['path']))==item['sha256'], item['path']
    windows_source=Path('/workspace/.cloud-setup/windows6421-source')
    expected=load(WINDOWS/'source-hashes.json')
    actual={f.relative_to(windows_source).as_posix():sha(f) for f in windows_source.rglob('*') if f.is_file()}
    assert actual==expected and len(expected)==73
    assert all(native['trees']['source']['files'][n]['sha256']==value for n,value in expected.items())
    win_final=load(WINDOWS/'FINAL-STATUS.json')
    assert win_final['source_commit']==COMMIT and win_final['status']=='WINDOWS21_FIRST_CHAIN_QUALIFIED_NOT_ELO_ACCEPTED'
    assert sha(REPO/win_final['artifact'])==win_final['artifact_sha256']
    for key,value in closed['observed_windows_final_values'].items():assert win_final[key]==value,key
    runtime=load(WINDOWS/'runtime-attempt1/result.json')
    assert runtime['status']=='passed' and runtime['source_and_tests_commit']==COMMIT
    assert len(runtime['checks'])==12 and all(row['exit_code']==0 for row in runtime['checks'])
    assert runtime['input_sha256_before']==runtime['input_sha256_after']
    for key,value in closed['observed_windows_runtime_values'].items():assert runtime[key]==value,key
    captures=Path(closed['actual_captures_path'])
    assert any(row['path']==str(captures) for row in load(OUT/'INPUT-SCOPE.json')['directory_roots']), 'Capture scope binding missing'
    capture=load(captures/'PROVENANCE.json')
    assert capture['status']=='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' and capture['final_rehash']['status']=='passed'
    helper=captures/'owned_process.executed.py'
    assert sha(helper)==capture['helper_sha256']==capture['helper_sha256_after']==closed['actual_producer_helper_sha256']
    assert len(capture['frozen_inputs'])==len(capture['final_rehash']['observed'])==181 and capture['final_rehash']['mismatches']==[]
    assert sha(captures/'ROOT-CAPTURE-AUTHORIZATION.executed.json')==closed['actual_capture_executed_authorization_sha256']
    review=load(Path(closed['actual_capture_root_review']))
    assert review['normal_outer_tool_exit_code']==0 and review['frozen_inputs_rehashed']==181 and review['provenance_sha256']==sha(captures/'PROVENANCE.json')
    for label,entry in capture['captures'].items():
        facts=entry['process_facts']
        assert entry['status']=='PASS_ACTUAL_FIVE_CANONICAL_ROWS' and entry['rows']==5
        assert facts['returncode']==facts['returncode_after_cleanup']==0 and facts['owned_group_empty_after_cleanup'] is True and facts['process_observations_valid'] is True and facts['timed_out'] is False
        source=Path(closed['actual_capture_source_roots'][label])
        assert entry['source_sha256_before']==entry['source_sha256_after'] and len(entry['source_sha256_before'])==closed['actual_capture_source_counts'][label]
        assert all(sha(source/name)==value for name,value in entry['source_sha256_before'].items())
        assert entry['binary_sha256_before']==entry['binary_sha256_after']
        for name,path in entry['binary_paths'].items():assert sha(Path(path))==entry['binary_sha256_before'][name]
        for leaf in ['stdout','stderr','stdin']:assert sha(captures/label/(leaf+'.txt'))==entry[leaf+'_sha256']
        for field in ['source_manifest_sha256','build_receipt_sha256']:
            bound=closed['actual_capture_proof_files'][label][field]
            assert sha(Path(bound['path']))==entry[field]==bound['sha256']


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
    assert sys.argv[1:] == ['--root-clearance', '21-ARCHIVE-AUTHORIZED'], 'Explicit root-clearance invocation required'
    clearance = load(OUT / 'ROOT-CLEARANCE.json')
    assert clearance['authorization'] == '21 COMPLETE ARCHIVE TASK AUTHORIZED' and clearance['provided_by'] == '/root'
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
    after_staging = inventory_frozen(before)
    save(OUT / 'LIVE-AFTER-STAGING.json', after_staging)
    assert after_staging == before, 'Included originals changed during staging; retain this failed attempt'
    provenance = STAGE / 'archive-provenance'
    provenance.mkdir()
    for name in preparation_names:
        shutil.copy2(OUT / name, provenance / name)
    save(provenance / 'LIVE-FILES-AND-MODES.json', before)
    command = {'operation': 'unchanged trusted archive_results.archive_results followed by verify_archive',
               'driver_command': [sys.executable, '-B', str(Path(__file__)), '--root-clearance', '21-ARCHIVE-AUTHORIZED'],
               'archiver_path': str(ARCHIVER), 'archiver_sha256': EXPECTED_ARCHIVER,
               'trusted_archiver_exact_pinned_hash': True, 'git_commands_executed': False,
               'frozen_candidate_source': COMMIT, 'parent_source': PARENT,
               'input': str(STAGE), 'output': str(OUT), 'archive_name': NAME,
               'split_size_bytes': SPLIT_SIZE, 'engine_executed': False,
               'excluded_to_prevent_recursion': [str(OUT)],
               'separate_experiments_excluded': ['.github/hosted-nearest-pawn-performance', 'validation/hosted-nearest-pawn-performance-20261020 except immutable actual-five-captures', 'prototype coordination/archive-preparation/future22 subtrees and live skills/docs'],
               'older_evidence_reference':'Only consumed baseline20 source/engine/core/NNUE object and source/build/root receipts are included, not its complete build/archive. Full21 prototype/source/build/helper/public/artifact/failure history and immutable actual-five producer captures are included; mutableperformance/future22/live docs/skills excluded unless explicitly frozen.',
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
    receipt = {'status': 'PASS_COMPLETE_21_ARCHIVE_VERIFIED', 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
               'complete_nearest_pawn_prototype_and_originals_included':True,
               'immutable_actual_five_producers_and_executed_helper_included':True,
               'frozen_exact_list_after_checks_future_coordination_excluded':True, 'user_release_zip_and_exes_ignored':False,
               'prospective_ignore_binary_archive_paths': len(candidates), 'ignore_applied': False,
               'scope': 'Complete local 6.4.21 evidence preservation, not validation, publication or an Elo/NPS/native hardware claim.'}
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
