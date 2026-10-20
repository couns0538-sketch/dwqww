#!/usr/bin/env python3
"""Independent data-only audit. Never imports any archive/recovery producer.

Only the new audit receipt is written. Parts are combined into an anonymous
temporary file, and ZIP members are streamed; no member is extracted or chmoded.
The expected hashes below came from the independent task, not RESULTS.json.
"""
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import traceback
import zipfile

BASE = Path('/workspace/dwqww/validation/pawn-span-fill-20261020/archive-complete')
REPO = Path('/workspace/dwqww')
STAGE = Path('/workspace/.cloud-setup/forge-pawn-span-fc23918-complete-evidence-stage')
RECEIPT = BASE / 'INDEPENDENT-ARCHIVE-AUDIT.json'
MANIFEST = 'forge-pawn-span-fc23918-20261020-complete.manifest.json'
SOURCE = 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
MANIFEST_SHA = '9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478'
ZIP_SHA = 'ee1bdd21707175cd57107a3a4a1c1daacd106975974b53d40338f0b9f1a22f7e'
ZIP_SIZE = 113855291
HELPER_SHA = '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
PARTS = [
    {'file': 'forge-pawn-span-fc23918-20261020-complete.zip.part0001', 'size': 67108864,
     'sha256': '44de1a6ff175ecf9ae74b93e31663d312393b1b380ca8bef92a7d52cefad01d9'},
    {'file': 'forge-pawn-span-fc23918-20261020-complete.zip.part0002', 'size': 46746427,
     'sha256': 'f7e7e3bddd083e01ac9bd051f47774195c78e26f3d87bc7c5634f18df0d42398'},
]
REPORT = {
    'schema_version': 1,
    'status': 'RUNNING',
    'auditor': '/root/archive_clock_complete/audit20_archive_fresh',
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
    require('External manifest schema and archive identity',
            external['schema_version'] == 1 and external['format'] == 'raw-split-zip'
            and external['archive'] == {
                'file': 'forge-pawn-span-fc23918-20261020-complete.zip',
                'size': ZIP_SIZE, 'sha256': ZIP_SHA}
            and external['parts'] == PARTS and external['split_size'] == 67108864
            and external['manifest_member'] == 'manifest.json')
    entries = external['files']
    paths = [r['path'] for r in entries]
    require('1937 unique safe payload paths', len(paths) == 1937
            and len(set(paths)) == len(paths) and all(map(safe_relative, paths)))
    files = dict(zip(paths, entries))
    REPORT['external_manifest'] = {'file': MANIFEST, **manifest_id}
    REPORT['archive_payload_file_count'] = len(entries)
    REPORT['archive_payload_bytes'] = sum(r['size'] for r in entries)

    before = json_file(BASE / 'LIVE-BEFORE.json')
    live_rows, dir_rows = before['files'], before['directories']
    require('Frozen live counts and bytes', len(live_rows) == 1889
            and len(dir_rows) == 306 and sum(r['size'] for r in live_rows) == 303693001)
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

    stage_files, stage_dirs, special = stage_inventory()
    check('Stage inventory exactly equals manifest, with no symlinks/special files',
          stage_files == set(paths) and not special,
          extra=sorted(stage_files - set(paths)), missing=sorted(set(paths) - stage_files),
          special=special)
    require('Archive payload is exactly frozen live files plus48 provenance files',
            {p for p in paths if p.startswith('payload/')} == set(live_by_payload)
            and len([p for p in paths if p.startswith('archive-provenance/')]) == 48
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
        stage_equal = all(staged[k] == row[k] for k in ['size', 'sha256', 'mode'])
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
            require('ZIP exactly1937 unique payload members plus internal manifest',
                    len(names) == 1938 and len(set(names)) == len(names)
                    and set(names) == {'files/' + p for p in paths} | {'manifest.json'}
                    and all(map(safe_relative, names)))
            require('ZIP contains no encrypted, directory, symlink or special members',
                    all(not i.is_dir() and not i.flag_bits & 1
                        and stat.S_IFMT(i.external_attr >> 16) in (0, stat.S_IFREG)
                        for i in infos))
            internal_bytes = archive.read('manifest.json')
            internal = json.loads(internal_bytes)
            require('Internal manifest schema and exact external payload records',
                    internal['schema_version'] == 1 and internal['files'] == entries)
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

    clearance = json_file(BASE / 'ROOT-CLEARANCE.json')
    require('Root clearance binds exact source and quiescent included writers',
            clearance['source_commit'] == SOURCE
            and clearance['included_writers_quiescent'] is True)
    bindings = clearance['frozen_inputs_sha256']
    require('Root clearance contains15 bound files', len(bindings) == 15)
    REPORT['root_bound_files'] = []
    for path, sha in bindings.items():
        require('Safe repository-relative root binding: ' + path, safe_relative(path))
        observed = identity(REPO / path)
        if str(REPO / path) in live_by_original:
            payload = live_by_original[str(REPO / path)]['payload_path']
        else:
            payload = 'archive-provenance/' + Path(path).name
        archived = files.get(payload, {})
        check('Root-bound original and archived identity unchanged: ' + path,
              observed['sha256'] == sha == archived.get('sha256'))
        REPORT['root_bound_files'].append({'path': path, 'expected_sha256': sha,
                                         'observed_sha256': observed['sha256'],
                                         'archive_payload': payload})

    scope = json_file(BASE / 'INPUT-SCOPE.json')
    for row in live_rows:
        selected = any(row['group'] == r['group'] and under(row['original'], r['path'])
                       for r in scope['directory_roots']) or any(
                           row['group'] == r['group'] and row['original'] == r['path']
                           for r in scope['original_files'])
        check('Frozen original fits independently parsed declared scope: ' + row['original'], selected)
    publication = '/workspace/dwqww/validation/pawn-span-fill-20261020/root-verification/WINDOWS-PUBLICATION.json'
    check('Mandatory WINDOWS-PUBLICATION selected exactly once',
          sum(row['original'] == publication for row in live_rows) == 1
          and sum(path.endswith('/root-verification/WINDOWS-PUBLICATION.json') for path in paths) == 1)
    consumed = [r for r in live_rows if r['group'].startswith('consumed-baseline19-')]
    check('Only83 explicitly consumed19 files; no earlier complete archives recopied',
          len(consumed) == 83
          and collections.Counter(r['group'] for r in consumed) == {
              'consumed-baseline19-source': 74, 'consumed-baseline19-engine': 1,
              'consumed-baseline19-core': 1, 'consumed-baseline19-nnue-object': 1,
              'consumed-baseline19-proof': 5, 'consumed-baseline19-rootproof': 1}
          and not any('/archive-complete/' in r['original'] or '.zip.part' in r['original']
                      for r in live_rows))
    capture_root = '/workspace/dwqww/validation/hosted-pawn-span-performance-20261020/actual-five-captures'
    captures = [r for r in live_rows if under(r['original'], capture_root)]
    check('Performance root excluded except15 immutable capture files; no monitoring',
          len(captures) == 15 and all(
              not ('/validation/hosted-pawn-span-performance-20261020/' in r['original'])
              or under(r['original'], capture_root) for r in live_rows)
          and not any('/.github/hosted-pawn-span-performance/' in r['original']
                      or '/coordination/' in r['original']
                      or 'monitor' in Path(r['original']).name.lower() for r in live_rows))
    helper_path = capture_root + '/owned_process.executed.py'
    capture_provenance = json_file(Path(capture_root) / 'PROVENANCE.json')
    authorization = json_file(Path(capture_root) / 'ROOT-CAPTURE-AUTHORIZATION.executed.json')
    check('Executed461a helper included and linked by immutable capture records',
          live_by_original[helper_path]['sha256'] == HELPER_SHA
          and capture_provenance['helper_sha256'] == HELPER_SHA
          and capture_provenance['helper_executed_path'] == helper_path
          and authorization['helper_sha256'] == HELPER_SHA)
    REPORT['immutable_captures'] = {'file_count': len(captures),
        'helper_executed_path': helper_path, 'helper_sha256': HELPER_SHA,
        'performance_acceptance_claimed': False}
    for label in ['baseline', 'candidate']:
        status = json_file(Path(capture_root) / label / 'status.json')
        prefix = 'payload' + capture_root + '/' + label + '/'
        check('Retained capture output and input identities: ' + label,
              all(status[name + '_sha256'] == files[prefix + name + '.txt']['sha256']
                  for name in ['stdin', 'stdout', 'stderr'])
              and status['returncode'] == 0 and status['process_observations_valid'] is True)

    history = [
        'archive_complete.pre-native20-mode-schema.py', 'archive_complete.pre-tar-content-projection.py',
        'archive_complete.pre-prototype-manifest-base.py', 'archive_complete.pre-windows20-schema.py',
        'DRIVER-REVIEW-attempt1.json', 'DRIVER-REVIEW-attempt2.json',
        'native20-mode-consumer-fix.diff', 'tar-mode-content-qualification.diff',
        'prototype-manifest-base-consumer-fix.diff', 'windows20-status-consumer-fix.diff',
    ]
    check('Prior driver versions, reviews and exact correction diffs retained',
          all('archive-provenance/' + p in files for p in history))
    for label, command, version in [
        ('live-gates', 'LIVE-GATES-COMMAND.json', 'archive_complete.pre-native20-mode-schema.py'),
        ('live-gates-attempt2', 'LIVE-GATES-ATTEMPT2-COMMAND.json', 'archive_complete.pre-tar-content-projection.py'),
        ('live-gates-attempt3', 'LIVE-GATES-ATTEMPT3-COMMAND.json', 'archive_complete.pre-prototype-manifest-base.py'),
        ('live-gates-attempt4', 'LIVE-GATES-ATTEMPT4-COMMAND.json', 'archive_complete.py'),
    ]:
        command_row = json_file(STAGE / 'archive-provenance' / command)
        check('Preflight logs and exact executed driver identity retained: ' + label,
              command_row['driver_sha256'] == files['archive-provenance/' + version]['sha256']
              and all(command_row[k + '_sha256'] == files['archive-provenance/' + label + '.' + k]['sha256']
                      for k in ['stdout', 'stderr'])
              and command_row['exit_code'] == (0 if label.endswith('attempt4') else 1))

    metadata_outer_differences = []
    for path in paths:
        if path.startswith('archive-provenance/'):
            outer = BASE / Path(path).name
            if outer.exists():
                observed = identity(outer)
                if any(observed[k] != files[path][k] for k in ['size', 'sha256']):
                    metadata_outer_differences.append({'outer_path': str(outer),
                        'archive_payload': path, 'archived_sha256': files[path]['sha256'],
                        'current_outer_sha256': observed['sha256']})
    REPORT['outer_provenance_differences_not_frozen_live_originals'] = metadata_outer_differences
    check('Only operational outer README differs from archived preparation metadata',
          all(Path(r['outer_path']).name == 'README.md' for r in metadata_outer_differences))
    REPORT['live_file_count'] = len(live_rows)
    REPORT['live_directory_count'] = len(dir_rows)
    REPORT['live_bytes'] = sum(r['size'] for r in live_rows)
    REPORT['live_group_counts'] = dict(sorted(collections.Counter(r['group'] for r in live_rows).items()))
    REPORT['qualifications'] = [
        'ZIP members carry generic0600 permissions. Original file and directory modes are preserved in the independently verified embedded mode map and stage; unzip alone is not executable-permission restoration.',
        'No real archive recovery, extraction or chmod was performed. A successful byte/mode audit is not a recovery execution claim.',
        'Source commit is checked for consistency with supplied and archived provenance; no independent Git authenticity or remote publication audit was performed.',
        'No engine correctness, calibrated speed, native hardware, NPS or Elo acceptance follows from this data-preservation audit.',
        'The archived preparation README remains preserved; an outer operational README may advance after packaging and is outside the frozen LIVE ledger and15 root-bound files.',
        'Raw originals, retained stage and previous evidence were read without writes. No original artifact was deleted, replaced, ignored or untracked by this audit.',
    ]


def main():
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise SystemExit('Refusing to overwrite existing independent audit receipt')
    try:
        audit()
    except Exception as error:
        REPORT['findings'].append({'name': 'Audit exception', 'type': type(error).__name__,
                                   'message': str(error)})
        traceback.print_exc(file=sys.stderr)
    REPORT['status'] = ('PASS_INDEPENDENT_DATA_ONLY_ARCHIVE_AUDIT'
                        if not REPORT['findings'] else 'FAIL_INDEPENDENT_DATA_ONLY_ARCHIVE_AUDIT')
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
