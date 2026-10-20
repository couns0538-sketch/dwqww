#!/usr/bin/env python3
"""Read-only independent verification of the one authorized completed recovery.

Does not import or execute any archive, restore, launch or earlier audit helper.
Does not open original live paths, modify the recovered tree, extract, or chmod.
Only the new independent receipt is written; ZIP reassembly is anonymous/temp.
"""
import ast
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
DEST = Path('/workspace/.cloud-setup/forge20-recovery-check-attempt1')
OUTSIDE_LAUNCHER = Path('/workspace/.cloud-setup/forge20-actual-recovery-once.py')
RECEIPT = BASE / 'INDEPENDENT-RECOVERY-AUDIT.json'
NAME = 'forge-pawn-span-fc23918-20261020-complete.manifest.json'
MANIFEST_SHA = '9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478'
ZIP_SHA = 'ee1bdd21707175cd57107a3a4a1c1daacd106975974b53d40338f0b9f1a22f7e'
HELPER_SHA = '1efc0d1998d33973eed109e28e042ed047237ffc3ddcc94d4651ef3eb91050fc'
LAUNCHER_SHA = '1761771dded19cbe73918251087b5aaaeef1ed7ca2e2b2ffbe8bd531e5aa92d3'
ARCHIVE_AUDIT_SHA = '20f9e01a4897442b8209a7ebe47e0c2705f8c451e0fe62e7f64df3114fa0d628'
PARTS = [
    ('forge-pawn-span-fc23918-20261020-complete.zip.part0001', 67108864,
     '44de1a6ff175ecf9ae74b93e31663d312393b1b380ca8bef92a7d52cefad01d9'),
    ('forge-pawn-span-fc23918-20261020-complete.zip.part0002', 46746427,
     'f7e7e3bddd083e01ac9bd051f47774195c78e26f3d87bc7c5634f18df0d42398'),
]
REPORT = {
    'schema_version': 1, 'status': 'RUNNING',
    'auditor': '/root/archive_clock_complete/audit20_archive_fresh',
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'method': 'Independent stdlib hash/zipfile/anonymous tempfile/AST read audit after helper completion; no helper imported or executed.',
    'destination': str(DEST), 'checks': [], 'findings': [],
    'audit_operations': {'recovered_tree_writes': False, 'original_live_path_reads': False,
        'original_live_path_writes': False, 'engine_compiler_git_network_execution': False,
        'extraction': False, 'chmod': False},
}


def check(name, passed, **details):
    row = {'name': name, 'passed': bool(passed), **details}
    REPORT['checks'].append(row)
    if not passed:
        REPORT['findings'].append(row)
        print('FAIL:', name, json.dumps(details, sort_keys=True), flush=True)
    return bool(passed)


def require(name, passed, **details):
    if not check(name, passed, **details):
        raise ValueError(name)


def digest(stream, target=None):
    size, sha = 0, hashlib.sha256()
    while True:
        data = stream.read(1024 * 1024)
        if not data:
            return size, sha.hexdigest()
        size += len(data)
        sha.update(data)
        if target is not None:
            target.write(data)


def identity(path):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Expected non-symlink regular file: ' + str(path))
    with path.open('rb') as stream:
        size, sha = digest(stream)
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mode, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mode, after.st_mtime_ns):
        raise ValueError('File changed during read: ' + str(path))
    return {'size': size, 'sha256': sha, 'mode': stat.S_IMODE(after.st_mode),
            'mtime_ns': after.st_mtime_ns}


def load(path):
    return json.loads(path.read_bytes())


def safe(path):
    return (isinstance(path, str) and bool(path) and '\\' not in path and '\x00' not in path
            and ':' not in path and not path.startswith('/')
            and all(p not in ('', '.', '..') for p in path.split('/'))
            and str(PurePosixPath(path)) == path)


def provenance():
    names = ['ACTUAL-RECOVERY-COMMAND.json', 'ACTUAL-RECOVERY-EXIT.json',
             'ROOT-ACTUAL-RECOVERY-CLEAR.json', 'actual-recovery.stdout',
             'actual-recovery.stderr', 'restore_new_scratch.py',
             'launch_actual_recovery_once.py', 'INDEPENDENT-ARCHIVE-AUDIT.json', NAME]
    identities = {name: identity(BASE / name) for name in names}
    identities[str(OUTSIDE_LAUNCHER)] = identity(OUTSIDE_LAUNCHER)
    REPORT['recovery_provenance_identities'] = identities
    command, exit_receipt, clear, stdout = [load(BASE / name) for name in names[:4]]
    require('Pinned recovery helper, saved launcher, outside launcher and archive audit hashes',
            identities['restore_new_scratch.py']['sha256'] == HELPER_SHA
            and identities['launch_actual_recovery_once.py']['sha256'] == LAUNCHER_SHA
            and identities[str(OUTSIDE_LAUNCHER)]['sha256'] == LAUNCHER_SHA
            and identities['INDEPENDENT-ARCHIVE-AUDIT.json']['sha256'] == ARCHIVE_AUDIT_SHA)
    require('Root clearance binds this one new destination and verified archive',
            clear['authorization'] == 'ROOT_AUTHORIZES_ONE_ACTUAL_FRESH_SCRATCH_RECOVERY_ONLY'
            and clear['target'] == str(DEST) and clear['must_be_new_empty_destination'] is True
            and clear['helper_sha256'] == HELPER_SHA and clear['manifest_sha256'] == MANIFEST_SHA
            and clear['combined_zip_sha256'] == ZIP_SHA)
    expected_command = [
        '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3', '-B',
        str(BASE / 'restore_new_scratch.py'), '--parts', str(BASE),
        '--destination', str(DEST), '--manifest-sha256', MANIFEST_SHA,
    ]
    require('Actual command exactly matches completed one-shot scratch recovery',
            command['command'] == expected_command == exit_receipt['command']
            and command['cwd'] == '/workspace/dwqww'
            and command['destination_absent_before_execution'] is True
            and exit_receipt['destination'] == str(DEST)
            and exit_receipt['destination_retained'] is True)
    require('Launch record correctly hashes clearance, helper, manifest, audit and wrapper',
            command['root_clearance_sha256'] == identities['ROOT-ACTUAL-RECOVERY-CLEAR.json']['sha256']
            and command['helper_sha256'] == HELPER_SHA
            and command['manifest_sha256'] == identities[NAME]['sha256'] == MANIFEST_SHA
            and command['independent_archive_audit_sha256'] == ARCHIVE_AUDIT_SHA
            and command['wrapper_sha256'] == LAUNCHER_SHA)
    require('Actual completed execution stdout/stderr identities and zero exit',
            exit_receipt['status'] == 'PASS_ACTUAL_RECOVERY_COMMAND_EXIT'
            and exit_receipt['exit_code'] == 0
            and exit_receipt['stdout_sha256'] == identities['actual-recovery.stdout']['sha256']
            and exit_receipt['stderr_sha256'] == identities['actual-recovery.stderr']['sha256']
            and exit_receipt['stdout_bytes'] == identities['actual-recovery.stdout']['size']
            and exit_receipt['stderr_bytes'] == identities['actual-recovery.stderr']['size'] == 0)
    require('Helper completed recovery report counts and original-path scope',
            stdout['status'] == 'PASS_NEW_SCRATCH_RECOVERY'
            and stdout['destination'] == str(DEST) and stdout['manifest_sha256'] == MANIFEST_SHA
            and stdout['payload_files_verified'] == 1937
            and stdout['original_file_modes_restored'] == 1889
            and stdout['directory_modes_restored'] == 306
            and stdout['engines_or_compilers_executed'] is False
            and stdout['original_absolute_paths_written'] is False
            and command['no_engine_compiler_git_or_original_absolute_path_writes'] is True
            and exit_receipt['engines_compilers_git_executed'] is False)
    helper_source = (BASE / 'restore_new_scratch.py').read_text()
    launcher_source = (BASE / 'launch_actual_recovery_once.py').read_text()
    helper_ast = ast.parse(helper_source)
    ast.parse(launcher_source)
    mutations = []
    for node in ast.walk(helper_ast):
        if isinstance(node, ast.Call):
            expression = ast.unparse(node.func)
            if expression.endswith(('.mkdir', '.chmod', '.utime', '.open')):
                if expression.endswith('.open') and not any(
                        isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and any(c in a.value for c in 'wax+') for a in node.args):
                    continue
                mutations.append({'line': node.lineno, 'expression': ast.get_source_segment(helper_source, node)})
    REPORT['pinned_helper_mutation_calls_static_read'] = sorted(mutations, key=lambda row: row['line'])
    require('Pinned helper write targets derived from scratch destination, not original path fields',
            'target = destination / \'files\' / row[\'path\']' in helper_source
            and 'target = destination / \'files\' / row[\'payload_path\']' in helper_source
            and "destination.mkdir(parents=False, exist_ok=False)" in helper_source
            and "row['original']" not in helper_source
            and "target.open('xb')" in helper_source)
    REPORT['execution_receipt'] = exit_receipt
    REPORT['original_absolute_path_write_scope'] = (
        'No original-path writes by the recorded recovery command according to its pinned helper static scope, '
        'one-shot launcher, command and completed result receipts. This is not a syscall trace or a fresh '
        'comparison of live originals/docs; live originals were deliberately not opened by this audit.')


def audit():
    provenance()
    manifest = load(BASE / NAME)
    entries = manifest['files']
    paths = [r['path'] for r in entries]
    require('Independent external manifest and1937 unique safe payload paths',
            identity(BASE / NAME)['sha256'] == MANIFEST_SHA
            and len(paths) == 1937 and len(set(paths)) == 1937 and all(map(safe, paths)))
    require('Independently pinned split and combined archive identity',
            manifest['archive']['size'] == 113855291 and manifest['archive']['sha256'] == ZIP_SHA
            and manifest['parts'] == [{'file': n, 'size': size, 'sha256': sha} for n, size, sha in PARTS])
    with tempfile.TemporaryFile(mode='w+b', dir='/tmp') as combined:
        REPORT['parts'] = []
        for name, expected_size, expected_sha in PARTS:
            with (BASE / name).open('rb') as stream:
                size, sha = digest(stream, combined)
            require('Archive part hash and size: ' + name, size == expected_size and sha == expected_sha)
            REPORT['parts'].append({'file': name, 'size': size, 'sha256': sha})
        combined.seek(0)
        size, sha = digest(combined)
        require('Independent temporary ZIP reassembly', size == 113855291 and sha == ZIP_SHA)
        combined.seek(0)
        with zipfile.ZipFile(combined) as archive:
            names = archive.namelist()
            require('ZIP exact payload/member inventory with no duplicate names',
                    len(names) == len(set(names)) == 1938
                    and set(names) == {'files/' + p for p in paths} | {'manifest.json'})
            require('Internal manifest exactly matches external payload records',
                    json.loads(archive.read('manifest.json')) == {'schema_version': 1, 'files': entries})
            mode_bytes = archive.read('files/archive-provenance/LIVE-FILES-AND-MODES.json')
            modes = json.loads(mode_bytes)
            mode_entry = next(r for r in entries if r['path'] == 'archive-provenance/LIVE-FILES-AND-MODES.json')
            require('Direct archived mode-map bytes authenticated by external manifest',
                    len(mode_bytes) == mode_entry['size']
                    and hashlib.sha256(mode_bytes).hexdigest() == mode_entry['sha256'])
            REPORT['embedded_mode_map_sha256'] = hashlib.sha256(mode_bytes).hexdigest()
            for row in entries:
                with archive.open('files/' + row['path']) as stream:
                    size, sha = digest(stream)
                check('Direct ZIP bytes and CRC: ' + row['path'],
                      size == row['size'] and sha == row['sha256'])
    live, directories = modes['files'], modes['directories']
    require('Authenticated original mode-map has1889 unique files and306 unique directories',
            len(live) == 1889 and len(directories) == 306
            and len({r['payload_path'] for r in live}) == 1889
            and len({r['payload_path'] for r in directories}) == 306
            and all(safe(r['payload_path']) for r in live + directories))
    by_path = {r['path']: r for r in entries}
    require('Original map is exactly the1889 payload files and identities match external manifest',
            {r['payload_path'] for r in live} == {p for p in paths if p.startswith('payload/')}
            and all(all(row[k] == by_path[row['payload_path']][k] for k in ['size', 'sha256']) for row in live))
    require('Recovered root is a real directory, not a symlink',
            stat.S_ISDIR(DEST.lstat().st_mode) and not DEST.is_symlink())
    actual_files, actual_dirs, unsafe = set(), set(), []
    for root, dirs, names in os.walk(DEST, followlinks=False):
        for name in dirs + names:
            path = Path(root) / name
            rel = path.relative_to(DEST).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                unsafe.append(rel)
            elif stat.S_ISDIR(mode):
                actual_dirs.add(rel)
            elif stat.S_ISREG(mode):
                actual_files.add(rel)
            else:
                unsafe.append(rel)
    expected_files = {'files/' + p for p in paths}
    expected_dirs = set()
    for rel in list(expected_files) + ['files/' + r['payload_path'] for r in directories]:
        path = PurePosixPath(rel)
        if rel not in expected_files:
            expected_dirs.add(rel)
        expected_dirs.update(p.as_posix() for p in path.parents if p.as_posix() != '.')
    require('Exact recovered inventory:1937files, no extra files/directories/symlinks/special entries',
            actual_files == expected_files and actual_dirs == expected_dirs and not unsafe,
            file_count=len(actual_files), directory_count=len(actual_dirs),
            missing_files=sorted(expected_files - actual_files), extra_files=sorted(actual_files - expected_files),
            missing_directories=sorted(expected_dirs - actual_dirs),
            extra_directories=sorted(actual_dirs - expected_dirs), unsafe_entries=unsafe)
    REPORT['recovered_files'] = []
    observations = {}
    for row in entries:
        observed = identity(DEST / 'files' / row['path'])
        observations[row['path']] = observed
        check('Recovered payload hash and size: ' + row['path'],
              all(row[k] == observed[k] for k in ['size', 'sha256']))
        REPORT['recovered_files'].append({'path': row['path'], **observed})
    for row in live:
        observed = observations[row['payload_path']]
        check('Recovered original mode and exact mtime_ns: ' + row['payload_path'],
              observed['mode'] == row['mode'] and observed['mtime_ns'] == row['mtime_ns'])
    REPORT['recovered_original_directories'] = []
    for row in directories:
        observed = (DEST / 'files' / row['payload_path']).lstat()
        mode = stat.S_IMODE(observed.st_mode)
        check('Recovered original directory mode: ' + row['payload_path'],
              stat.S_ISDIR(observed.st_mode) and mode == row['mode'])
        REPORT['recovered_original_directories'].append({'path': row['payload_path'], 'mode': mode})
    check('48 recovered provenance files retain generic0600 ZIP permissions',
          all(observations[p]['mode'] == 0o600 for p in paths if p.startswith('archive-provenance/')))
    REPORT.update({'recovered_payload_files': len(actual_files),
        'recovered_payload_bytes': sum(r['size'] for r in entries),
        'recovered_original_files_with_mode_and_mtime_verified': len(live),
        'recovered_original_directories_with_modes_verified': len(directories),
        'all_recovered_directories_including_structural_parents': len(actual_dirs),
        'zip_payloads_verified_directly': len(entries),
        'qualifications': [
            'The original1889file modes and nanosecond mtimes, and306directory modes are independently verified against the authenticated archive map. Structural parent directory permissions and48provenance timestamps were not specified by that map.',
            'No engine, compiler, Git, network, extraction or chmod was run by this audit. The separately authorized helper performed the actual recovery once before this audit.',
            'The recovered tree remains retained. Byte/permission recovery proves local recoverability of this package, not engine correctness, speed, Elo, source authenticity or durable remote publication.',
            REPORT['original_absolute_path_write_scope'],
        ]})
    print('Checked recovered tree:', len(actual_files), 'payloads;', len(live),
          'original file modes/mtimes;', len(directories), 'directory modes', flush=True)


def main():
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise SystemExit('Refusing to overwrite previous recovery audit receipt')
    try:
        audit()
    except Exception as error:
        REPORT['findings'].append({'name': 'Audit exception', 'type': type(error).__name__, 'message': str(error)})
        traceback.print_exc(file=sys.stderr)
    REPORT['status'] = ('PASS_INDEPENDENT_ACTUAL_RECOVERY_AUDIT'
                        if not REPORT['findings'] else 'FAIL_INDEPENDENT_ACTUAL_RECOVERY_AUDIT')
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
