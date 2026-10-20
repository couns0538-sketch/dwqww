#!/usr/bin/env python3
"""One-shot independent read-only archive audit; only its own JSON/logs are written."""
from pathlib import Path, PurePosixPath
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import stat
import sys
import traceback
import zipfile

BASE = Path('/workspace/dwqww/validation/lazy-runtime-psqt-20261020/archive-complete')
OUTPUT = BASE / 'INDEPENDENT-ARCHIVE-AUDIT.json'
REPO = Path('/workspace/dwqww')
NATIVE = REPO / 'validation/lazy-runtime-psqt-native-20261020'
PROTOTYPE = BASE.parent
WINDOWS = REPO / 'validation/lazy-runtime-psqt-windows-20261020'
CAPTURES = REPO / 'validation/hosted-runtime-psqt-performance-20261020/actual-five-captures'
MANIFEST = BASE / 'forge-runtime-psqt-61f5980-20261020-complete.manifest.json'
EXPECTED_MANIFEST_SHA = '905893a4d808c904e5189540a945e38b3d000e0891a62e88b1f707027394e37d'
EXPECTED_ZIP_SHA = 'd90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31'
EXPECTED_HELPER = 'de13ad7c32832144a75f9c5080558f3c3e08952390eece6d70bd249058dcebea'
BLOCK = 1024 * 1024
REPORT = {
    'status': 'INDEPENDENT_AUDIT_IN_PROGRESS',
    'reviewer': '/root/archive6417/review_archive_driver',
    'started_utc': datetime.now(timezone.utc).isoformat(),
    'method': 'Python standard-library hashlib/io.BytesIO/zipfile; no driver or trusted-archive helper imported or executed.',
    'writes': 'Only this independent audit script, stdout/stderr logs and the new audit JSON under archive-complete; combined ZIP exists only in memory.',
    'failures': [],
}


def check(condition, label, detail=None):
    if not condition:
        item = {'check': label}
        if detail is not None:
            item['detail'] = detail
        REPORT['failures'].append(item)
    return bool(condition)


def fingerprint(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_mode)


def safe_relative(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and p.as_posix() == name


def audit():
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    receipt = json.loads((BASE / 'RESULTS.json').read_bytes())
    before = json.loads((BASE / 'LIVE-BEFORE.json').read_bytes())
    command = json.loads((BASE / 'ARCHIVE-COMMAND.json').read_bytes())
    stage = Path(command['input'])
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    check(manifest_sha == EXPECTED_MANIFEST_SHA == receipt['manifest_sha256'], 'external_manifest_sha256')
    check(manifest['archive'] == receipt['archive'], 'receipt_archive_identity')
    check(manifest['parts'] == receipt['parts'], 'receipt_parts')
    check(manifest['format'] == 'raw-split-zip' and manifest['split_size'] == 67108864, '64MiB_raw_split_contract')
    check(len(manifest['parts']) == 2, 'two_parts')
    check(len(before['files']) == 1762 and sum(r['size'] for r in before['files']) == 298643155, 'frozen_live_count_and_bytes')
    check(len(manifest['files']) == 1774, 'manifest_1774_payloads')
    by_payload = {r['payload_path']: r for r in before['files']}
    by_original = {r['original']: r for r in before['files']}
    check(len(by_payload) == len(by_original) == len(before['files']), 'unique_frozen_originals')
    check(all('/archive-complete/' not in r['original'] and '/coordination/' not in r['original'] for r in before['files']), 'excluded_mutable_and_archive_paths')
    for name in ['LIVE-AFTER-STAGING.json', 'LIVE-AFTER-ARCHIVE.json']:
        check(json.loads((BASE / name).read_bytes()) == before, 'saved_inventory_equals_before:' + name)

    combined = io.BytesIO()
    digest = hashlib.sha256()
    part_facts = []
    total = 0
    for index, row in enumerate(manifest['parts']):
        check(Path(row['file']).name == row['file'], 'safe_part_name', row['file'])
        path = BASE / row['file']
        part_digest, size = hashlib.sha256(), 0
        with path.open('rb') as stream:
            initial = fingerprint(os.fstat(stream.fileno()))
            while True:
                data = stream.read(BLOCK)
                if not data:
                    break
                combined.write(data)
                part_digest.update(data)
                digest.update(data)
                size += len(data)
            check(initial == fingerprint(os.fstat(stream.fileno())), 'part_unchanged_while_reading', row['file'])
        actual = {'file': row['file'], 'size': size, 'sha256': part_digest.hexdigest()}
        check(actual == row, 'part_size_sha256', actual)
        check(size <= 67108864 and (index == len(manifest['parts']) - 1 or size == 67108864), 'part_boundary', actual)
        part_facts.append(actual)
        total += size
    zip_sha = digest.hexdigest()
    check(total == manifest['archive']['size'] == 112207796, 'combined_size')
    check(zip_sha == manifest['archive']['sha256'] == EXPECTED_ZIP_SHA, 'combined_sha256')
    REPORT['archive_identity'] = {'manifest_sha256': manifest_sha, 'archive_size': total, 'archive_sha256': zip_sha, 'parts': part_facts, 'combined_zip_written_to_disk': False}
    combined.seek(0)

    provenance_names = [
        'archive_complete.py', 'INPUT-SCOPE.json', 'PREPARATION.json', 'DRIVER-REVIEW.json',
        'PARENT-ADAPTATION.json', 'STATIC-CHECKS.json', 'SCOPE-QUALIFICATIONS.json',
        'driver-adaptation.diff', 'ROOT-CLEARANCE.json', 'LIVE-FILES-AND-MODES.json',
        'ARCHIVE-COMMAND.json', 'STAGING-CHECK.json',
    ]
    expected_payload_paths = set(by_payload) | {'archive-provenance/' + n for n in provenance_names}
    declared = {r['path']: r for r in manifest['files']}
    check(len(declared) == len(manifest['files']), 'unique_manifest_payloads')
    check(all(safe_relative(n) for n in declared), 'safe_payload_paths')
    check(set(declared) == expected_payload_paths, 'exact_originals_plus_12_provenance_payloads')
    payload_facts, original_fingerprints = [], {}
    zip_modes = Counter()
    zip_original_mode_matches = 0
    with zipfile.ZipFile(combined) as archive:
        embedded = json.loads(archive.read('manifest.json'))
        check(embedded == {'schema_version': 1, 'files': manifest['files']}, 'embedded_external_manifest_exact_match')
        expected_members = {'manifest.json'} | {'files/' + n for n in declared}
        names = archive.namelist()
        check(len(names) == len(set(names)) == 1775 and set(names) == expected_members, 'exact_unique_zip_members')
        archived_before = json.loads(archive.read('files/archive-provenance/LIVE-FILES-AND-MODES.json'))
        check(archived_before == before, 'embedded_original_file_and_directory_modes_exact')
        for index, row in enumerate(manifest['files'], 1):
            name = row['path']
            frozen = by_payload.get(name)
            staged_path = stage / name
            fact = {'path': name}
            try:
                check(stat.S_ISREG(staged_path.lstat().st_mode), 'regular_staged_payload', name)
                info = archive.getinfo('files/' + name)
                zip_mode = (info.external_attr >> 16) & 0o7777
                zip_modes[oct(zip_mode)] += 1
                with ExitStack() as stack:
                    member = stack.enter_context(archive.open(info))
                    staged = stack.enter_context(staged_path.open('rb'))
                    staged_initial = fingerprint(os.fstat(staged.fileno()))
                    live = None
                    if frozen is not None:
                        live_path = Path(frozen['original'])
                        check(stat.S_ISREG(live_path.lstat().st_mode), 'regular_original', frozen['original'])
                        live = stack.enter_context(live_path.open('rb'))
                        live_initial_stat = os.fstat(live.fileno())
                        live_initial = fingerprint(live_initial_stat)
                        original_fingerprints[frozen['original']] = live_initial
                        live_mode = stat.S_IMODE(live_initial_stat.st_mode)
                        stage_mode = stat.S_IMODE(os.fstat(staged.fileno()).st_mode)
                        check(live_mode == stage_mode == frozen['mode'], 'original_and_stage_file_modes', frozen['original'])
                        check(live_initial_stat.st_mtime_ns == frozen['mtime_ns'], 'original_mtime_unchanged', frozen['original'])
                        check((live_initial_stat.st_dev, live_initial_stat.st_ino) != (os.fstat(staged.fileno()).st_dev, os.fstat(staged.fileno()).st_ino), 'stage_is_distinct_copy', name)
                        zip_original_mode_matches += int(zip_mode == frozen['mode'])
                        fact.update({'original': frozen['original'], 'original_mode': oct(live_mode), 'stage_mode': oct(stage_mode)})
                    payload_digest, size = hashlib.sha256(), 0
                    stage_equal, live_equal = True, True
                    while True:
                        data = member.read(BLOCK)
                        if not data:
                            break
                        payload_digest.update(data)
                        size += len(data)
                        stage_equal = (staged.read(len(data)) == data) and stage_equal
                        if live is not None:
                            live_equal = (live.read(len(data)) == data) and live_equal
                    stage_equal = (staged.read(1) == b'') and stage_equal
                    check(stage_equal, 'archive_stage_direct_byte_comparison', name)
                    check(staged_initial == fingerprint(os.fstat(staged.fileno())), 'stage_unchanged_while_compared', name)
                    if live is not None:
                        live_equal = (live.read(1) == b'') and live_equal
                        check(live_equal, 'archive_original_direct_byte_comparison', frozen['original'])
                        check(live_initial == fingerprint(os.fstat(live.fileno())), 'original_unchanged_while_compared', frozen['original'])
                    actual_digest = payload_digest.hexdigest()
                    check(size == row['size'] and actual_digest == row['sha256'], 'every_payload_size_sha256', name)
                    if frozen is not None:
                        check(size == frozen['size'] and actual_digest == frozen['sha256'], 'payload_matches_frozen_original_manifest', name)
                    fact.update({'size': size, 'sha256': actual_digest, 'archive_stage_byte_equal': stage_equal, 'archive_original_byte_equal': live_equal if live is not None else None, 'zip_external_mode': oct(zip_mode)})
            except Exception as error:
                check(False, 'payload_audit_exception', {'path': name, 'type': type(error).__name__, 'error': str(error)})
            payload_facts.append(fact)
            if index % 400 == 0:
                print('Compared', index, 'of', len(manifest['files']), 'archive payloads', flush=True)

        def archive_json(original):
            return json.loads(archive.read('files/' + by_original[str(original)]['payload_path']))

        def archived_hash_list(directory, filename):
            records = {}
            text = archive.read('files/' + by_original[str(directory / filename)]['payload_path']).decode()
            for line in text.splitlines():
                digest_value, relative = line.split(maxsplit=1)
                relative = PurePosixPath(relative.lstrip('*')).as_posix()
                check(relative not in records and safe_relative(relative), 'hash_list_safe_unique:' + filename, relative)
                row = by_original.get(str(directory / relative))
                check(row is not None and row['sha256'] == digest_value, 'hash_list_payload_coverage:' + filename, relative)
                records[relative] = digest_value
            return records

        native_hashes = archived_hash_list(NATIVE, 'EVIDENCE-SHA256SUMS')
        native_rows = {Path(r['original']).relative_to(NATIVE).as_posix() for r in before['files'] if r['group'] == 'immutable-native-validation'}
        check(len(native_hashes) == 251 and native_rows == set(native_hashes) | {'EVIDENCE-SHA256SUMS'}, 'native_exact_252_frozen_files')
        originals = archive_json(NATIVE / 'ORIGINALS-FINAL-SHA256.json')
        outside_count = 0
        for label, tree in originals['trees'].items():
            root = Path(tree['root'])
            rows = {Path(r['original']).relative_to(root).as_posix(): {'sha256': r['sha256'], 'bytes': r['size']} for r in before['files'] if Path(r['original']).is_relative_to(root)}
            check(rows == tree['files'], 'native_outside_exact_original_map:' + label)
            outside_count += len(rows)
        check(outside_count == 524, 'native_524_outside_originals')
        for label, item in originals['single_files'].items():
            row = by_original.get(item['path'])
            check(row is not None and row['sha256'] == item['sha256'] and row['size'] == item['bytes'], 'native_single_original:' + label)
        prototype_hashes = archived_hash_list(PROTOTYPE, 'SHA256SUMS')
        check(len(prototype_hashes) == 242, 'prototype_historical_242_coverage')
        required_history = [
            'PREPARATION-ERROR-FIRST.json', 'PARENT-RED-INPUTS.json', 'red-to-green-test-refinement.diff',
            'release-red-attempt1/runtime-psqt-test.stderr', 'release-green-attempt1/ctest.stdout',
            'root-verification/NATIVE.json', 'root-verification/WINDOWS-CHECKER-ATTEMPT0.json',
            'root-verification/WINDOWS.json', 'REMOTE-PUBLICATION.json',
        ]
        check(all(str(PROTOTYPE / n) in by_original for n in required_history), 'prototype_failure_rootproof_publication_history')
        capture = archive_json(CAPTURES / 'PROVENANCE.json')
        helper = by_original[str(CAPTURES / 'owned_process.executed.py')]
        check(helper['sha256'] == capture['helper_sha256'] == capture['helper_sha256_after'] == EXPECTED_HELPER, 'executed_capture_helper_de13')
        for label, entry in capture['captures'].items():
            root = Path('/workspace/.cloud-setup/' + ('correction-history-native-source' if label == 'baseline' else 'lazy-runtime-psqt-native-source'))
            check(entry['source_sha256_before'] == entry['source_sha256_after'], 'capture_source_before_after:' + label)
            check(all(by_original[str(root / name)]['sha256'] == value for name, value in entry['source_sha256_before'].items()), 'capture_consumed_source_origins:' + label)
            check(entry['binary_sha256_before'] == entry['binary_sha256_after'], 'capture_binary_before_after:' + label)
            check(all(by_original[path]['sha256'] == entry['binary_sha256_before'][key] for key, path in entry['binary_paths'].items()), 'capture_exact_named_binary_origins:' + label)
            for stream_name in ['stdin', 'stdout', 'stderr']:
                check(by_original[str(CAPTURES / label / (stream_name + '.txt'))]['sha256'] == entry[stream_name + '_sha256'], 'capture_transcript:' + label + ':' + stream_name)
        check(by_original[str(REPO / 'validation/correction-history-native-20261020/frozen-source-fc51e43-files.json')]['sha256'] == capture['captures']['baseline']['source_manifest_sha256'], 'consumed_baseline18_source_receipt')
        check(by_original[str(REPO / 'validation/correction-history-native-20261020/frozen-release-attempt1/summary.json')]['sha256'] == capture['captures']['baseline']['build_receipt_sha256'], 'consumed_baseline18_build_receipt')
        windows_raw = [r['original'] for r in before['files'] if r['group'] == 'windows-validation' and any(t in r['original'] for t in ['/originals/binaries/', '/originals/static-core/', '/runtime-attempt1/disassembly.log', '/windows-originals.zip'])]
        check(len(windows_raw) == 11, 'windows_8PE_core_disassembly_originalZIP')
        win_final = archive_json(WINDOWS / 'FINAL-STATUS.json')
        check(by_original[str(REPO / win_final['artifact'])]['sha256'] == win_final['artifact_sha256'] == 'f0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85', 'windows_release_original_zip_identity')
        REPORT['coverage'] = {
            'native_immutable_manifest_entries': len(native_hashes), 'native_immutable_total_files': len(native_rows),
            'native_outside_source_and_3_build_originals': outside_count,
            'prototype_historical_manifest_entries': len(prototype_hashes), 'prototype_failure_and_rootproof_paths': required_history,
            'windows_raw_PE_core_disassembly_original_zip_paths': windows_raw,
            'consumed_baseline18': {'source_files': 73, 'engine': True, 'core': True, 'source_and_build_receipts': True},
            'immutable_actual_five_capture_files': 14, 'executed_capture_helper_sha256': helper['sha256'],
            'capture_interpretation': 'Producer/provenance preservation only; no calibrated speed or Elo result.',
        }

    for original, initial in original_fingerprints.items():
        check(fingerprint(Path(original).lstat()) == initial, 'original_still_unchanged_at_audit_end', original)
    for row in before['directories']:
        path = Path(row['original'])
        st = path.lstat()
        check(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode) == row['mode'], 'frozen_original_directory_mode', row['original'])
    ignore = json.loads((BASE / 'IGNORE-CANDIDATES.json').read_bytes())
    check(ignore['candidates'] == [] and receipt['prospective_ignore_binary_archive_paths'] == 0 and receipt['ignore_applied'] is False, 'zero_ignore_candidates_no_application')
    check(hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == manifest_sha, 'external_manifest_still_unchanged')
    group_counts = dict(Counter(r['group'] for r in before['files']))
    check(group_counts == receipt['live_file_counts'], 'receipt_group_counts')
    REPORT['counts'] = {'parts': len(part_facts), 'zip_members': len(names), 'payloads_hashed_and_stage_compared': len(payload_facts), 'frozen_originals_byte_compared': len(original_fingerprints), 'frozen_original_bytes': sum(r['size'] for r in before['files']), 'frozen_original_directories_mode_checked': len(before['directories']), 'group_counts': group_counts}
    REPORT['mode_verification'] = {
        'all_1762_original_and_staged_file_modes_equal_frozen_record': not any(f['check'] == 'original_and_stage_file_modes' for f in REPORT['failures']),
        'embedded_original_file_and_directory_mode_manifest_equals_live_before': archived_before == before,
        'zip_external_mode_counts_all_payloads': dict(zip_modes),
        'zip_external_modes_matching_original_file_modes': zip_original_mode_matches,
        'limitation': 'ZIP member external modes are generic archive defaults, not an original-mode preservation contract. Original file/directory modes are preserved in the embedded LIVE-FILES-AND-MODES.json; staged original files retain their modes. No executable-mode restoration was attempted.',
    }
    REPORT['payloads'] = payload_facts
    REPORT['originals_preserved'] = not any('original' in f['check'] or 'hash_list_payload' in f['check'] for f in REPORT['failures'])
    REPORT['no_future_coordination_extras_enumerated'] = True
    REPORT['engines_compilers_tests_git_index_ignore_or_source_edits'] = False
    REPORT['scope'] = 'Independent local preservation audit only: no Git source-authenticity audit, engine validation, publication, calibrated speed or Elo acceptance.'


if __name__ == '__main__':
    if OUTPUT.exists():
        raise SystemExit('Refusing to overwrite an existing audit receipt; no audit attempted.')
    try:
        audit()
    except BaseException as error:
        check(False, 'audit_exception', {'type': type(error).__name__, 'error': str(error), 'traceback': traceback.format_exc()})
    REPORT['finished_utc'] = datetime.now(timezone.utc).isoformat()
    REPORT['audit_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    REPORT['status'] = 'PASS_INDEPENDENT_COMPLETE_19_ARCHIVE_AUDIT' if not REPORT['failures'] else 'FAILED_INDEPENDENT_19_ARCHIVE_AUDIT_RETAINED'
    with OUTPUT.open('x') as stream:
        json.dump(REPORT, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: REPORT[k] for k in ['status', 'archive_identity', 'counts', 'failures'] if k in REPORT}, indent=2), flush=True)
    sys.exit(0 if not REPORT['failures'] else 1)
