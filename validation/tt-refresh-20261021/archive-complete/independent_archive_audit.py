#!/usr/bin/env python3
"""Independent data-only audit. Never imports any archive/recovery producer.

Only the new audit receipt is written. Parts are combined into an anonymous
temporary file, and ZIP members are streamed; no member is extracted or chmoded.
Expected hashes/counts come from a separately root-bound EXTERNAL-PINS.json,
not from RESULTS.json. Preparation does not authorize audit or recovery.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import traceback
import zipfile

BASE = Path('/workspace/dwqww/validation/tt-refresh-20261021/archive-complete')
REPO = Path('/workspace/dwqww')
STAGE = Path('/workspace/.cloud-setup/forge-tt-refresh-1d3ed25-complete-evidence-stage')
RECEIPT = BASE / 'INDEPENDENT-ARCHIVE-AUDIT.json'
NAME = 'forge-tt-refresh-1d3ed25-20261021-complete'
MANIFEST = NAME + '.manifest.json'
SOURCE = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
PARENT_SOURCE = 'ff2e269c6058be84456e3b98344826d17b0056eb'
SPLIT_SIZE = 64 * 1024 * 1024
PINS = None
MANIFEST_SHA = ZIP_SHA = ZIP_SIZE = PARTS = None
REPORT = {
    'schema_version': 1,
    'status': 'RUNNING',
    'auditor': '/root/archive6417',
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_commit_recorded_not_independently_git_authenticated': SOURCE,
    'method': 'Independent Python standard library hashing, JSON, zipfile and anonymous tempfile; no producer/helper import or execution.',
    'checks': [], 'findings': [], 'qualifications': [],
    'operations': {'engine_compiler_git_network_execution': False,
                   'real_archive_extraction': False, 'chmod': False,
                   'original_or_stage_writes': False, 'recovery_claimed': False},
}


def check(name, passed, **detail):
    result = {'name': name, 'passed': bool(passed), **detail}
    REPORT['checks'].append(result)
    if not passed:
        REPORT['findings'].append(result)
        print('FAIL:', name, json.dumps(detail, sort_keys=True), flush=True)
    return bool(passed)


def require(name, passed, **detail):
    if not check(name, passed, **detail):
        raise ValueError(name)


def digest(stream, target=None):
    h = hashlib.sha256()
    size = 0
    while True:
        data = stream.read(1024 * 1024)
        if not data:
            return size, h.hexdigest()
        size += len(data)
        h.update(data)
        if target is not None:
            target.write(data)


def identity(path):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Not a regular non-symlink file: ' + str(path))
    with path.open('rb') as source:
        size, sha = digest(source)
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode):
        raise ValueError('File changed while read: ' + str(path))
    return {'size': size, 'sha256': sha, 'mode': stat.S_IMODE(after.st_mode),
            'mtime_ns': after.st_mtime_ns}


def json_file(path):
    return json.loads(path.read_bytes())


def safe_relative(path):
    return (isinstance(path, str) and path and '\\' not in path and '\x00' not in path
            and ':' not in path and not path.startswith('/')
            and all(part not in ('', '.', '..') for part in path.split('/'))
            and str(PurePosixPath(path)) == path)


def under(path, root):
    return path == root or path.startswith(root.rstrip('/') + '/')


def stage_inventory():
    files, directories, bad = set(), set(), []
    for root, dirs, names in os.walk(STAGE, followlinks=False):
        for name in dirs + names:
            path = Path(root) / name
            mode = path.lstat().st_mode
            rel = path.relative_to(STAGE).as_posix()
            if stat.S_ISLNK(mode):
                bad.append(rel)
            elif stat.S_ISREG(mode):
                files.add(rel)
            elif stat.S_ISDIR(mode):
                directories.add(rel)
            else:
                bad.append(rel)
    return files, directories, bad


def audit():
    manifest_id = identity(BASE / MANIFEST)
    require('External manifest matches independently supplied hash',
            manifest_id['sha256'] == MANIFEST_SHA, observed=manifest_id)
    external = json_file(BASE / MANIFEST)
    require('External manifest canonical producer JSON bytes', (BASE / MANIFEST).read_bytes() == canonical_json(external))
    require('External manifest schema and archive identity',
            external['schema_version'] == 1 and external['format'] == 'raw-split-zip'
            and external['archive'] == {
                'file': NAME + '.zip',
                'size': ZIP_SIZE, 'sha256': ZIP_SHA}
            and external['parts'] == PARTS and external['split_size'] == 67108864
            and external['manifest_member'] == 'manifest.json')
    entries = external['files']
    paths = [r['path'] for r in entries]
    require('Unique safe externally counted payload paths', len(paths) == PINS['counts']['payload_files']
            and len(set(paths)) == len(paths) and all(map(safe_relative, paths)))
    files = dict(zip(paths, entries))
    REPORT['external_manifest'] = {'file': MANIFEST, **manifest_id}
    REPORT['archive_payload_file_count'] = len(entries)
    REPORT['archive_payload_bytes'] = sum(r['size'] for r in entries)
    require('Archive payload bytes match external pins', REPORT['archive_payload_bytes'] == PINS['counts']['payload_bytes'])

    before = json_file(BASE / 'LIVE-BEFORE.json')
    live_rows, dir_rows = before['files'], before['directories']
    require('Frozen live counts and bytes match external pins', len(live_rows) == PINS['counts']['live_files']
            and len(dir_rows) == PINS['counts']['live_directories'] and sum(r['size'] for r in live_rows) == PINS['counts']['live_bytes'])
    require('Unique frozen original and payload file/directory paths',
            all(len({r[k] for r in rows}) == len(rows)
                for rows in [live_rows, dir_rows] for k in ['original', 'payload_path']))
    require('Frozen payload paths map to absolute original paths',
            all(r['original'].startswith('/workspace/')
                and r['payload_path'] == 'payload' + r['original']
                and safe_relative(r['payload_path']) for r in live_rows + dir_rows))
    live_by_original = {r['original']: r for r in live_rows}
    live_by_payload = {r['payload_path']: r for r in live_rows}
    REPORT['frozen_ledger_identities'] = {}
    for name in ['LIVE-BEFORE.json', 'LIVE-AFTER-STAGING.json', 'LIVE-AFTER-ARCHIVE.json']:
        REPORT['frozen_ledger_identities'][name] = identity(BASE / name)
        check('Exact frozen list including modes and mtimes: ' + name,
              (BASE / name).read_bytes() == (BASE / 'LIVE-BEFORE.json').read_bytes())

    require('Retained stage is a real directory', stat.S_ISDIR(STAGE.lstat().st_mode))
    stage_files, stage_dirs, special = stage_inventory()
    check('Stage inventory exactly equals manifest, with no symlinks/special files',
          stage_files == set(paths) and not special,
          extra=sorted(stage_files - set(paths)), missing=sorted(set(paths) - stage_files),
          special=special)
    expected_stage_dirs = {str(parent) for path in paths for parent in PurePosixPath(path).parents if str(parent) != '.'}
    expected_stage_dirs.update(row['payload_path'] for row in dir_rows)
    check('Stage directory inventory exactly frozen mapped plus structural parents',
          stage_dirs == expected_stage_dirs,
          extra=sorted(stage_dirs-expected_stage_dirs), missing=sorted(expected_stage_dirs-stage_dirs))
    require('Archive payload is exactly frozen live files plus externally counted provenance',
            {p for p in paths if p.startswith('payload/')} == set(live_by_payload)
            and len([p for p in paths if p.startswith('archive-provenance/')]) == PINS['counts']['provenance_files']
            and all(p.startswith(('payload/', 'archive-provenance/')) for p in paths))

    staged_observations = {}
    for path, expected in files.items():
        observed = identity(STAGE / path)
        check('Staged payload bytes: ' + path,
              all(observed[k] == expected[k] for k in ['size', 'sha256']))
        staged_observations[path] = observed
    REPORT['staged_payloads_verified'] = len(staged_observations)
    print('Checked stage bytes:', len(staged_observations), 'payloads', flush=True)

    REPORT['live_originals'] = []
    for row in live_rows:
        observed = identity(Path(row['original']))
        staged = staged_observations[row['payload_path']]
        equal = all(observed[k] == row[k] for k in ['size', 'sha256', 'mode', 'mtime_ns'])
        stage_equal = all(staged[k] == row[k] for k in ['size', 'sha256', 'mode', 'mtime_ns'])
        check('Live original hash/size/mode/mtime and stage hash/size/mode: ' + row['original'],
              equal and stage_equal)
        check('Frozen live identity equals external archive entry: ' + row['payload_path'],
              all(files[row['payload_path']][k] == row[k] for k in ['size', 'sha256']))
        REPORT['live_originals'].append({'original': row['original'],
            'payload_path': row['payload_path'], **observed,
            'stage_mode': staged['mode'], 'matches_frozen': equal,
            'stage_matches_frozen': stage_equal})
    REPORT['directories'] = []
    for row in dir_rows:
        original = Path(row['original']).lstat()
        staged = (STAGE / row['payload_path']).lstat()
        equal = (stat.S_ISDIR(original.st_mode) and stat.S_ISDIR(staged.st_mode)
                 and stat.S_IMODE(original.st_mode) == row['mode']
                 and stat.S_IMODE(staged.st_mode) == row['mode'])
        check('Live and staged directory modes: ' + row['original'], equal)
        REPORT['directories'].append({'original': row['original'],
            'payload_path': row['payload_path'], 'mode': stat.S_IMODE(original.st_mode),
            'stage_mode': stat.S_IMODE(staged.st_mode), 'matches_frozen': equal})
    print('Checked live identities:', len(live_rows), 'files,', len(dir_rows), 'directories', flush=True)

    with tempfile.TemporaryFile(mode='w+b', dir='/tmp') as combined:
        part_observations = []
        for part in PARTS:
            observed = identity(BASE / part['file'])
            require('Split part identity: ' + part['file'],
                    all(observed[k] == part[k] for k in ['size', 'sha256']))
            with (BASE / part['file']).open('rb') as stream:
                copied_size, copied_sha = digest(stream, combined)
            require('Split part copied without change: ' + part['file'],
                    copied_size == part['size'] and copied_sha == part['sha256'])
            part_observations.append({'file': part['file'], **observed})
        combined.seek(0)
        combined_size, combined_sha = digest(combined)
        require('Independent reassembly combined ZIP hash and size',
                combined_size == ZIP_SIZE and combined_sha == ZIP_SHA,
                size=combined_size, sha256=combined_sha)
        REPORT['parts'] = part_observations
        REPORT['combined_zip'] = {'size': combined_size, 'sha256': combined_sha,
                                  'persistent_reassembled_copy_created': False}
        combined.seek(0)
        with zipfile.ZipFile(combined) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            require('ZIP exactly unique payload members plus internal manifest',
                    len(names) == PINS['counts']['payload_files'] + 1 and len(set(names)) == len(names)
                    and set(names) == {'files/' + p for p in paths} | {'manifest.json'}
                    and all(map(safe_relative, names)))
            require('ZIP contains no encrypted, directory, symlink or special members',
                    all(not i.is_dir() and not i.flag_bits & 1
                        and stat.S_IFMT(i.external_attr >> 16) in (0, stat.S_IFREG)
                        for i in infos))
            internal_bytes = archive.read('manifest.json')
            internal = json.loads(internal_bytes)
            require('Internal manifest schema and exact external payload records',
                    internal == {'schema_version': 1, 'files': entries})
            require('Internal manifest canonical producer JSON bytes', internal_bytes == canonical_json(internal))
            REPORT['internal_manifest'] = {'size': len(internal_bytes),
                'sha256': hashlib.sha256(internal_bytes).hexdigest()}
            for path, expected in files.items():
                info = archive.getinfo('files/' + path)
                with archive.open(info) as stream:
                    size, sha = digest(stream)
                check('Direct ZIP member SHA/size/CRC read: ' + path,
                      size == expected['size'] == info.file_size and sha == expected['sha256'])
            require('Embedded original file/directory mode map exactly equals LIVE-BEFORE',
                    archive.read('files/archive-provenance/LIVE-FILES-AND-MODES.json')
                    == (BASE / 'LIVE-BEFORE.json').read_bytes())
            zip_modes = sorted({stat.S_IMODE(i.external_attr >> 16) for i in infos})
            check('ZIP generic0600 permission qualification observed', zip_modes == [0o600],
                  observed_modes_octal=[oct(mode) for mode in zip_modes])
            REPORT['zip_payloads_verified_directly'] = len(entries)
            REPORT['zip_crc_verification'] = 'Every member read to EOF through zipfile, including its CRC check.'
            REPORT['zip_member_modes_octal'] = [oct(mode) for mode in zip_modes]
    print('Checked independent ZIP members:', len(entries), 'payloads', flush=True)

    result = json_file(BASE / 'RESULTS.json')
    require('Actual23 producer completion agrees with independently supplied pins',
            result['status'] == 'PASS_COMPLETE_23_ARCHIVE_VERIFIED'
            and result['source_commit'] == SOURCE and result['parent_source_commit'] == PARENT_SOURCE
            and result['live_file_count'] == PINS['counts']['live_files']
            and result['archive_payload_file_count'] == PINS['counts']['payload_files']
            and result['live_bytes'] == PINS['counts']['live_bytes']
            and result['archive_payload_bytes'] == PINS['counts']['payload_bytes']
            and result['archive'] == external['archive'] == PINS['archive']
            and result['parts'] == PARTS and result['manifest_sha256'] == MANIFEST_SHA
            and result['split_size_bytes'] == SPLIT_SIZE)
    REPORT['producer_results_identity'] = identity(BASE / 'RESULTS.json')
    clearance = json_file(BASE / 'ROOT-CLEARANCE.json')
    require('Root exact23 authorization and quiescent included writers',
            clearance['authorized'] is True and clearance['provided_by'] == '/root'
            and clearance['source_commit'] == SOURCE
            and clearance['included_writers_quiescent'] is True)
    bindings = clearance['frozen_inputs_sha256']
    require('Root exact external binding count', len(bindings) == PINS['counts']['root_bindings'])
    REPORT['root_bound_files'] = []
    for path, expected_sha in bindings.items():
        original = Path(path)
        require('Safe absolute root binding: ' + path, safe_absolute(path) and under(path, str(REPO)))
        if path in live_by_original:
            payload = live_by_original[path]['payload_path']
        else:
            require('Non-live root binding is immediate archive provenance: ' + path, original.parent == BASE)
            payload = 'archive-provenance/' + original.name
        observed = identity(original)
        check('Root bound live and archived bytes unchanged: ' + path,
              observed['sha256'] == expected_sha == files.get(payload, {}).get('sha256'))
        REPORT['root_bound_files'].append({'path': path, 'expected_sha256': expected_sha,
                                          'archive_payload': payload, 'observed_sha256': observed['sha256']})
    scope = json_file(BASE / 'INPUT-SCOPE.json')
    require('Ready scope matches external root/single counts and source',
            scope['ready'] is True and scope['source_commit'] == SOURCE
            and len(scope['directory_roots']) == PINS['counts']['directory_roots']
            and len(scope['original_files']) == PINS['counts']['original_files'])
    for value in [r['path'] for r in scope['directory_roots'] + scope['original_files']] + scope['excluded_subtrees']:
        require('Safe absolute declared scope path: ' + value, safe_absolute(value))
    excluded = {Path(x) for x in scope['excluded_subtrees']}
    observed_files, observed_directories, additions_special = {}, {}, []
    def scope_file(group, path):
        require('Declared original path selected only once: ' + str(path), str(path) not in observed_files)
        observed_files[str(path)] = group
    for root in scope['directory_roots']:
        root_path = Path(root['path'])
        require('Declared scope root is real directory: ' + str(root_path),
                stat.S_ISDIR(root_path.lstat().st_mode))
        for current, dirs, leaves in os.walk(root_path, followlinks=False):
            current = Path(current)
            dirs[:] = sorted(n for n in dirs if current / n not in excluded)
            require('Declared directory selected only once: ' + str(current), str(current) not in observed_directories)
            observed_directories[str(current)] = root['group']
            real_dirs = []
            for name in dirs:
                child = current / name
                if stat.S_ISLNK(child.lstat().st_mode):
                    scope_file(root['group'], child)
                    additions_special.append({'path': str(child), 'kind': 'symlink_directory_not_followed'})
                else:
                    real_dirs.append(name)
            dirs[:] = real_dirs
            for name in sorted(leaves):
                child = current / name
                scope_file(root['group'], child)
                if not stat.S_ISREG(child.lstat().st_mode):
                    additions_special.append({'path': str(child), 'kind': 'nonregular_not_read'})
    for row in scope['original_files']:
        scope_file(row['group'], Path(row['path']))
    frozen_file_groups = {row['original']: row['group'] for row in live_rows}
    frozen_directory_groups = {row['original']: row['group'] for row in dir_rows}
    check('Every frozen scope original remains present in its exact declared group',
          {path: observed_files.get(path) for path in frozen_file_groups} == frozen_file_groups,
          missing=sorted(set(frozen_file_groups) - set(observed_files)))
    check('Every frozen scope directory remains present in its exact declared group',
          {path: observed_directories.get(path) for path in frozen_directory_groups} == frozen_directory_groups,
          missing=sorted(set(frozen_directory_groups) - set(observed_directories)))
    REPORT['post_freeze_scope_additions_not_claimed_archived'] = {
        'files': sorted(set(observed_files) - set(frozen_file_groups)),
        'directories': sorted(set(observed_directories) - set(frozen_directory_groups)),
        'special_additions_not_read': [r for r in additions_special if r['path'] not in frozen_file_groups],
        'qualification': 'Only the exact frozen originals and directories are audited as archived; later additions are listed separately.'}
    for row in live_rows + dir_rows:
        selected = (any(row['group'] == r['group'] and under(row['original'], r['path']) for r in scope['directory_roots'])
                    or any(row['group'] == r['group'] and row['original'] == r['path'] for r in scope['original_files']))
        check('Frozen original fits declared scope: ' + row['original'], selected
              and not any(under(row['original'], str(x)) for x in excluded))
    counts = dict(sorted(collections.Counter(row['group'] for row in live_rows).items()))
    check('Frozen group counts equal external pins and producer receipt',
          counts == PINS['live_file_counts'] == result['live_file_counts'])
    differences = []
    for path in paths:
        if path.startswith('archive-provenance/'):
            require('Immediate archive provenance filename: ' + path, len(PurePosixPath(path).parts) == 2)
            outer = BASE / Path(path).name
            if outer.exists():
                observed = identity(outer)
                if any(observed[k] != files[path][k] for k in ['size', 'sha256']):
                    differences.append({'outer_path': str(outer), 'archive_payload': path,
                                        'archived_sha256': files[path]['sha256'], 'current_outer_sha256': observed['sha256']})
    REPORT['outer_provenance_differences_not_live_originals'] = differences
    REPORT['qualifications'].append('Current outer provenance differences are reported separately; archived bytes are independently verified, and root-bound files remain mandatory.')
    REPORT['live_file_count'] = len(live_rows)
    REPORT['live_directory_count'] = len(dir_rows)
    REPORT['live_bytes'] = sum(r['size'] for r in live_rows)
    REPORT['live_group_counts'] = dict(sorted(collections.Counter(r['group'] for r in live_rows).items()))
    REPORT['qualifications'] += [
        'ZIP members carry generic0600 permissions. Original file/directory modes and file mtimes are preserved in the independently verified embedded map and retained stage; unzip alone does not restore executable permissions.',
        'No real recovery, extraction or chmod was performed by this auditor. Recovery requires its own root-authorized NEW scratch step after audit PASS.',
        'Source and parent commits are checked for consistency with root-supplied and archived provenance; no independent Git or remote-publication authentication is performed.',
        'No engine correctness, speed, NPS, native hardware or Elo acceptance follows from this data-preservation audit.',
        'Only actual INPUT-SCOPE, frozen ledgers, producer RESULTS and independently bound external pins define archive23 counts; no inherited21 fixture/capture/prototype counts or assumption notes are required.',
        'No original or stage artifact was written, deleted, chmoded, ignored or untracked. Anonymous reassembly is outside Git and leaves no persistent combined ZIP.',
    ]



def canonical_json(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')


def safe_absolute(path):
    return isinstance(path, str) and path.startswith('/workspace/') and safe_relative(path[1:])


def load_external_pins(expected_sha):
    global PINS, MANIFEST_SHA, ZIP_SHA, ZIP_SIZE, PARTS
    if re.fullmatch(r'[0-9a-f]{64}', expected_sha) is None:
        raise SystemExit('Root-bound external pins SHA256 is required; no audit attempted')
    pins_path = BASE / 'EXTERNAL-PINS.json'
    observed = identity(pins_path)
    if observed['sha256'] != expected_sha:
        raise SystemExit('External pins SHA256 mismatch; no audit attempted')
    pins = json_file(pins_path)
    if not (pins['authorized'] is True and pins['provided_by'] == '/root' and pins['source_commit'] == SOURCE):
        raise SystemExit('Explicit root-authorized actual23 pins required; no audit attempted')
    if pins['manifest']['file'] != MANIFEST or pins['archive']['file'] != NAME + '.zip':
        raise SystemExit('Exact actual23 archive/manifest names required; no audit attempted')
    counts = pins['counts']
    count_names = {'live_files', 'live_directories', 'live_bytes', 'payload_files', 'payload_bytes',
                   'provenance_files', 'directory_roots', 'original_files', 'root_bindings'}
    if set(counts) != count_names or not all(type(n) is int and n >= 0 for n in counts.values()):
        raise SystemExit('Exact root-observed nonnegative count schema required; no audit attempted')
    if not (counts['live_files'] > 0 and counts['payload_files'] == counts['live_files'] + counts['provenance_files']
            and counts['payload_bytes'] >= counts['live_bytes'] > 0
            and sum(pins['live_file_counts'].values()) == counts['live_files']):
        raise SystemExit('Root-observed count relations invalid; no audit attempted')
    archive, parts = pins['archive'], pins['parts']
    hashes = [pins['manifest']['sha256'], archive['sha256']] + [p['sha256'] for p in parts]
    if not all(isinstance(h, str) and re.fullmatch(r'[0-9a-f]{64}', h) for h in hashes):
        raise SystemExit('Exact root-observed SHA256 pins required; no audit attempted')
    if not (parts and type(archive['size']) is int and archive['size'] > 0
            and sum(p['size'] for p in parts) == archive['size']
            and all(type(p['size']) is int and 0 < p['size'] <= SPLIT_SIZE for p in parts)
            and all(p['size'] == SPLIT_SIZE for p in parts[:-1])
            and [p['file'] for p in parts] == [NAME + '.zip.part' + str(i).zfill(4) for i in range(1, len(parts) + 1)]):
        raise SystemExit('Canonical ordered64MiB split part pins required; no audit attempted')
    PINS = pins
    MANIFEST_SHA, ZIP_SHA, ZIP_SIZE, PARTS = pins['manifest']['sha256'], archive['sha256'], archive['size'], parts
    REPORT['external_pins'] = {'file': str(pins_path), 'sha256_supplied_independently': expected_sha, **observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-authorized', required=True, choices=['23-ARCHIVE-AUDIT-AUTHORIZED'])
    parser.add_argument('--external-pins-sha256', required=True)
    args = parser.parse_args()
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise SystemExit('Refusing to overwrite existing independent audit receipt')
    load_external_pins(args.external_pins_sha256)
    try:
        audit()
    except Exception as error:
        REPORT['findings'].append({'name': 'Audit exception', 'type': type(error).__name__, 'message': str(error)})
        traceback.print_exc(file=sys.stderr)
    REPORT['status'] = ('PASS_INDEPENDENT_COMPLETE_23_ARCHIVE_AUDIT'
                        if not REPORT['findings'] else 'FAIL_INDEPENDENT_COMPLETE_23_ARCHIVE_AUDIT')
    REPORT['completed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    REPORT['check_count'] = len(REPORT['checks'])
    REPORT['failed_check_count'] = sum(not c['passed'] for c in REPORT['checks'])
    REPORT['audit_script_sha256'] = identity(Path(__file__))['sha256']
    with RECEIPT.open('x', encoding='utf-8') as output:
        json.dump(REPORT, output, indent=2, sort_keys=True)
        output.write('\n')
    print(REPORT['status'], 'checks=' + str(REPORT['check_count']),
          'findings=' + str(len(REPORT['findings'])), flush=True)
    return int(bool(REPORT['findings']))


if __name__ == '__main__':
    sys.exit(main())
