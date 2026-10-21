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

BASE = Path('/workspace/dwqww/validation/nearest-pawn-distance-20261020/archive-complete')
REPO = Path('/workspace/dwqww')
STAGE = Path('/workspace/.cloud-setup/forge-nearest-pawn-2e151d0-complete-evidence-stage')
RECEIPT = BASE / 'INDEPENDENT-ARCHIVE-AUDIT.json'
MANIFEST = 'forge-nearest-pawn-2e151d0-20261020-complete.manifest.json'
SOURCE = '2e151d019bc58dff2ab4e76e99ef99516af8d222'
MANIFEST_SHA = '7cdb6d4b63dfb8dcf8511638b3503cbca46d8d9f18def2b4e796ef43ff77af32'
ZIP_SHA = '6df303ff995b3f68984a803d5ebb63a8244a3d1e5bd8bf1e20b21de2d6c3948c'
ZIP_SIZE = 121548290
HELPER_SHA = '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
PARTS = [
    {'file': 'forge-nearest-pawn-2e151d0-20261020-complete.zip.part0001', 'size': 67108864,
     'sha256': '03cfa23b8ce8dd95ad6f78412e63f5acf4afebc522289775beacc5d910b46402'},
    {'file': 'forge-nearest-pawn-2e151d0-20261020-complete.zip.part0002', 'size': 54439426,
     'sha256': '04bf32944a05ad2b2369d1455d1ccc0f6284be055ff12d0f46e8192e62c3e504'},
]
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
    require('External manifest schema and archive identity',
            external['schema_version'] == 1 and external['format'] == 'raw-split-zip'
            and external['archive'] == {
                'file': 'forge-nearest-pawn-2e151d0-20261020-complete.zip',
                'size': ZIP_SIZE, 'sha256': ZIP_SHA}
            and external['parts'] == PARTS and external['split_size'] == 67108864
            and external['manifest_member'] == 'manifest.json')
    entries = external['files']
    paths = [r['path'] for r in entries]
    require('2078 unique safe payload paths', len(paths) == 2078
            and len(set(paths)) == len(paths) and all(map(safe_relative, paths)))
    files = dict(zip(paths, entries))
    REPORT['external_manifest'] = {'file': MANIFEST, **manifest_id}
    REPORT['archive_payload_file_count'] = len(entries)
    REPORT['archive_payload_bytes'] = sum(r['size'] for r in entries)

    before = json_file(BASE / 'LIVE-BEFORE.json')
    live_rows, dir_rows = before['files'], before['directories']
    require('Frozen live counts and bytes', len(live_rows) == 2045
            and len(dir_rows) == 319 and sum(r['size'] for r in live_rows) == 317150918)
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
    expected_stage_dirs = {str(parent) for path in paths for parent in PurePosixPath(path).parents if str(parent) != '.'}
    expected_stage_dirs.update(row['payload_path'] for row in dir_rows)
    check('Stage directory inventory exactly frozen mapped plus structural parents',
          stage_dirs == expected_stage_dirs,
          extra=sorted(stage_dirs-expected_stage_dirs), missing=sorted(expected_stage_dirs-stage_dirs))
    require('Archive payload is exactly frozen live files plus33 provenance files',
            {p for p in paths if p.startswith('payload/')} == set(live_by_payload)
            and len([p for p in paths if p.startswith('archive-provenance/')]) == 33
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
            require('ZIP exactly2078 unique payload members plus internal manifest',
                    len(names) == 2079 and len(set(names)) == len(names)
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

    result = json_file(BASE/'RESULTS.json')
    driver_exit = json_file(BASE/'DRIVER-EXIT.json')
    require('Actual21 producer completion receipt schema', result['status']=='PASS_COMPLETE_21_ARCHIVE_VERIFIED' and result['source_commit']==SOURCE and result['live_file_count']==2045 and result['archive_payload_file_count']==2078 and result['live_bytes']==317150918 and result['archive_payload_bytes']==318369343 and result['archive']==external['archive'] and result['parts']==PARTS and result['manifest_sha256']==MANIFEST_SHA)
    require('Actual21 one authorized archive driver exit and raw streams retained', driver_exit['status']=='PASS_COMMAND_EXIT' and driver_exit['exit_code']==0 and driver_exit['timed_out'] is False and driver_exit['error'] is None and driver_exit['command'][-2:]==['--root-clearance','21-ARCHIVE-AUTHORIZED'] and driver_exit['source_engine_compiler_or_git_execution'] is False and all(identity(BASE/('driver.'+leaf))['sha256']==driver_exit[leaf+'_sha256'] for leaf in ['stdout','stderr']) and (BASE/'driver.stderr').stat().st_size==0)
    completion=(BASE/'ARCHIVE-COMPLETION.md').read_text()
    check('Actual21 completion narrative retains matching source/archive and readback qualification', SOURCE in completion and ZIP_SHA in completion and MANIFEST_SHA in completion and '2045' in completion and '2078' in completion and 'FINAL-VERIFICATION' in completion)
    REPORT['producer_sidecar_identities']={name:identity(BASE/name) for name in ['RESULTS.json','DRIVER-EXIT.json','ARCHIVE-COMPLETION.md','POST-LAUNCH-READBACK-NOTE.json']}
    clearance=json_file(BASE/'ROOT-CLEARANCE.json')
    require('Root exact21 authorization and quiescent included writers', clearance['authorized'] is True and clearance['authorization']=='21 COMPLETE ARCHIVE TASK AUTHORIZED' and clearance['provided_by']=='/root' and clearance['source_commit']==SOURCE and clearance['included_writers_quiescent'] is True)
    bindings=clearance['frozen_inputs_sha256']
    require('Root actual65 absolute closed hash bindings',len(bindings)==65)
    REPORT['root_bound_files']=[]
    for path,expected_sha in bindings.items():
        original=Path(path)
        require('Safe absolute repository root binding: '+path,original.is_absolute() and under(path,str(REPO)) and '..' not in original.parts)
        observed=identity(original)
        payload=live_by_original[path]['payload_path'] if path in live_by_original else 'archive-provenance/'+original.name
        archived=files.get(payload,{})
        check('Root bound live and archived bytes unchanged: '+path,observed['sha256']==expected_sha==archived.get('sha256'))
        REPORT['root_bound_files'].append({'path':path,'expected_sha256':expected_sha,'archive_payload':payload,'observed_sha256':observed['sha256']})
    scope=json_file(BASE/'INPUT-SCOPE.json')
    require('Actual ready scope has18roots and28 explicit originals',scope['ready'] is True and len(scope['directory_roots'])==18 and len(scope['original_files'])==28 and scope['source_commit']==SOURCE)
    excluded={Path(x) for x in scope['excluded_subtrees']}
    observed_files={};observed_directories={}
    def scope_file(group,path):
        require('Declared original path selected only once: '+str(path),str(path) not in observed_files)
        observed_files[str(path)]=group
    for root in scope['directory_roots']:
        root_path=Path(root['path']);require('Declared scope root is real directory: '+str(root_path),root_path.is_dir() and not root_path.is_symlink())
        for current,dirs,leaves in os.walk(root_path,followlinks=False):
            current=Path(current);dirs[:]=sorted(n for n in dirs if current/n not in excluded)
            require('Declared scope directory nonsymlink: '+str(current),not current.is_symlink())
            require('Declared directory selected only once: '+str(current),str(current) not in observed_directories)
            observed_directories[str(current)]=root['group']
            for name in dirs:require('Declared child directory nonsymlink: '+str(current/name),not(current/name).is_symlink())
            for name in sorted(leaves):scope_file(root['group'],current/name)
    for row in scope['original_files']:scope_file(row['group'],Path(row['path']))
    check('Fresh scope original file inventory exactly frozen ledger',observed_files=={row['original']:row['group'] for row in live_rows},extra=sorted(set(observed_files)-set(live_by_original)),missing=sorted(set(live_by_original)-set(observed_files)))
    check('Fresh scope directory inventory exactly frozen ledger',observed_directories=={row['original']:row['group'] for row in dir_rows})
    for row in live_rows:
        selected=any(row['group']==r['group'] and under(row['original'],r['path']) for r in scope['directory_roots']) or any(row['group']==r['group'] and row['original']==r['path'] for r in scope['original_files'])
        check('Frozen original fits declared scope: '+row['original'],selected)
    counts=collections.Counter(row['group'] for row in live_rows)
    check('Actual21 frozen group counts match producer receipt exactly',dict(sorted(counts.items()))==result['live_file_counts'])
    check('Actual native/windows/prototype and immutable capture/result audit group counts',counts['immutable-native-validation']==246 and counts['windows-validation']==243 and counts['prototype-and-rootproofs']==255 and counts['immutable-actual-five-producers']==15 and counts['immutable-hosted21-original-result']==4 and counts['immutable-hosted21-independent-final-audit']==20)
    consumed={k:v for k,v in counts.items() if k.startswith('consumed-baseline20-')}
    check('Only88 exact consumed20 originals, no complete older archives',consumed=={'consumed-baseline20-source':75,'consumed-baseline20-engine':1,'consumed-baseline20-core':1,'consumed-baseline20-nnue-object':1,'consumed-baseline20-proof':8,'consumed-baseline20-rootproof':2} and not any('/archive-complete/' in row['original'] or '.zip.part' in row['original'] for row in live_rows))
    check('No22/future/coordination/live skill-doc scope accidentally selected',not any('/pv-metadata-' in row['original'] or '/.agents/' in row['original'] or '/docs/' in row['original'] or '/coordination/' in row['original'] or '/archive-complete-preparation/' in row['original'] for row in live_rows))
    capture_root='/workspace/dwqww/validation/hosted-nearest-pawn-performance-20261021/actual-five-captures'
    captures=[row for row in live_rows if under(row['original'],capture_root)]
    helper_path=capture_root+'/owned_process.executed.py'
    capture=json_file(Path(capture_root)/'PROVENANCE.json');authorization=json_file(Path(capture_root)/'ROOT-CAPTURE-AUTHORIZATION.executed.json')
    check('Actual15 closed captures include original461a executed helper identity',len(captures)==15 and live_by_original[helper_path]['sha256']==HELPER_SHA and capture['helper_sha256']==HELPER_SHA and capture['helper_executed_path']==helper_path and authorization['helper_sha256']==HELPER_SHA)
    for label in ['baseline','candidate']:
        status=json_file(Path(capture_root)/label/'status.json');prefix='payload'+capture_root+'/'+label+'/'
        check('Closed capture output/input hash provenance retained: '+label,all(status[n+'_sha256']==files[prefix+n+'.txt']['sha256'] for n in ['stdin','stdout','stderr']) and status['returncode']==0 and status['process_observations_valid'] is True)
    REPORT['immutable_captures']={'file_count':len(captures),'helper_executed_path':helper_path,'helper_sha256':HELPER_SHA,'performance_acceptance_claimed_by_archive_audit':False}
    note=json_file(BASE/'ROOT-METADATA-CHECK-NOTE.json')
    check('Original57vsactual65 preauthorization assumption note preserved',note['assumed_leaf_count']==57 and note['actual_proposed_leaf_count']==65 and note['mutation_or_archive_execution_before_failure'] is False and 'archive-provenance/ROOT-METADATA-CHECK-NOTE.json' in files)
    promotion=json_file(BASE/'PROMOTION-ASSUMPTION-FAILURE.json')
    check('Original promotion dictionary-schema assumption and partialcontract preserved',promotion['status']=='PRESERVED_METADATA_ONLY_SCHEMA_ASSUMPTION' and all('archive-provenance/'+name in files for name in ['PROMOTION-ASSUMPTION-FAILURE.json','CLOSED-EVIDENCE-CONTRACT.partial-promotion.json','ROOT-METADATA-CHECK-NOTE.json']))
    readback=json_file(BASE/'POST-LAUNCH-READBACK-NOTE.json')
    check('Optional oldFINAL filename readback error preserved with no archive rerun',readback['status']=='ORIGINAL_OPTIONAL_READBACK_ERROR_RETAINED' and readback['archive_or_helper_reexecuted'] is False and readback['archive_result_unchanged'] is True)
    differences=[]
    for path in paths:
        if path.startswith('archive-provenance/'):
            outer=BASE/Path(path).name
            if outer.exists():
                observed=identity(outer)
                if any(observed[k]!=files[path][k] for k in ['size','sha256']):differences.append({'outer_path':str(outer),'archive_payload':path,'archived_sha256':files[path]['sha256'],'current_outer_sha256':observed['sha256']})
    REPORT['outer_provenance_differences_not_live_originals']=differences
    check('Archived preparation provenance remains byteidentical to current outer versions',not differences,observed=differences)
    REPORT['live_file_count'] = len(live_rows)
    REPORT['live_directory_count'] = len(dir_rows)
    REPORT['live_bytes'] = sum(r['size'] for r in live_rows)
    REPORT['live_group_counts'] = dict(sorted(collections.Counter(r['group'] for r in live_rows).items()))
    REPORT['qualifications'] = [
        'ZIP members carry generic0600 permissions. Original file and directory modes are preserved in the independently verified embedded mode map and stage; unzip alone is not executable-permission restoration.',
        'No real archive recovery, extraction or chmod was performed. A successful byte/mode audit is not a recovery execution claim.',
        'Source commit is checked for consistency with supplied and archived provenance; no independent Git authenticity or remote publication audit was performed.',
        'No engine correctness, calibrated speed, native hardware, NPS or Elo acceptance follows from this data-preservation audit.',
        'Actual21 RESULTS/DRIVER-EXIT/ARCHIVE-COMPLETION schemas were used; old20 optional FINAL filename was not required. The original preauthorization57vs65 and postlaunchreadback notes remain unchanged.',
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
    REPORT['status'] = ('PASS_INDEPENDENT_COMPLETE_21_ARCHIVE_AUDIT'
                        if not REPORT['findings'] else 'FAIL_INDEPENDENT_COMPLETE_21_ARCHIVE_AUDIT')
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
