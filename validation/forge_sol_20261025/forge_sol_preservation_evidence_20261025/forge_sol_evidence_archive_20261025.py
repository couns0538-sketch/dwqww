#!/usr/bin/env python3
"""Losslessly freeze only the four explicitly authorized closed build profiles.

Adapted from ../forge-sol-next-20261024/space-agent/archive_closed_builds.py.
One verified file is committed at a time to fit the initially nearly full disk.
No source, main forge executable, configuration, log, PGN, ZIP, existing archive,
or build outside ROOTS is selected. No build or engine is executed.
"""
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import traceback

BASE = Path('/workspace/forge-sol-next-20261024')
OWN = Path('/workspace/forge-sol-20261025-space')
ROOTS = tuple(BASE / name for name in (
    'build-buffer-asan-on', 'build-int16-asan',
    'build-buffer-release', 'build-int16-release'))
MAP = OWN / 'forge_sol_restore_map_20261025.json'
JOURNAL = OWN / 'forge_sol_archive_journal_20261025.jsonl'
SUMMARY = OWN / 'forge_sol_archive_summary_20261025.json'
HELPER = OWN / 'forge_sol_restore_20261025.py'
MARKER = 'forge_sol_FROZEN_RESTORE_BEFORE_REBUILD_20261025.txt'
WRITERS = {'ctest', 'cmake', 'make', 'gmake', 'ninja', 'c++', 'g++',
           'cc1plus', 'collect2', 'ld', 'ar', 'ranlib'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def beneath(path):
    return any(path == str(root) or path.startswith(str(root) + '/')
               for root in ROOTS)


def process_preflight():
    """Check actual executable/cwd/writable FDs plus build/test command lines."""
    blocked = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            comm = (proc / 'comm').read_text().strip()
            args = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            try:
                cwd = os.readlink(proc / 'cwd')
            except OSError:
                cwd = None
            try:
                exe = os.readlink(proc / 'exe')
            except OSError:
                exe = None
            reasons = []
            if cwd and beneath(cwd):
                reasons.append('cwd is inside a closed root')
            if exe and beneath(exe.removesuffix(' (deleted)')):
                reasons.append('executable is inside a closed root')
            writer = (comm in WRITERS or comm in {'forge_tests', 'forge_bench'}
                      or (comm.startswith('forge_') and comm.endswith('_tests')))
            if writer and any(str(root) in args for root in ROOTS):
                reasons.append('build/test command line names a closed root')
            writable = []
            try:
                fds = list((proc / 'fd').iterdir())
            except (PermissionError, FileNotFoundError):
                fds = []
            for fd in fds:
                try:
                    target = os.readlink(fd).removesuffix(' (deleted)')
                    if not beneath(target):
                        continue
                    flags_line = next(line for line in (proc / 'fdinfo' / fd.name).read_text().splitlines()
                                      if line.startswith('flags:'))
                    flags = int(flags_line.split()[1], 8)
                    if flags & os.O_ACCMODE in (os.O_WRONLY, os.O_RDWR):
                        writable.append({'fd': fd.name, 'target': target, 'flags_octal': oct(flags)})
                except (OSError, StopIteration):
                    continue
            if writable:
                reasons.append('open writable descriptor inside a closed root')
            if reasons:
                blocked.append({'pid': int(proc.name), 'comm': comm, 'args': args,
                                'cwd': cwd, 'exe': exe, 'reasons': reasons, 'writable_fds': writable})
        except (FileNotFoundError, ProcessLookupError):
            continue
    result = {'checked_utc': utc(), 'blocked': blocked}
    if blocked:
        raise RuntimeError('Active process references a closed root: ' + json.dumps(result))
    return result


def durable_json(path, data):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    sync_dir(path.parent)


def sync_dir(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def journal(event, **fields):
    with JOURNAL.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'utc': utc(), 'event': event, **fields}) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def metadata(path):
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != os.getuid() or path.resolve() != path):
        raise RuntimeError('Not a plain, owned, single-link file: ' + str(path))
    return {'size': info.st_size, 'mode': stat.S_IMODE(info.st_mode),
            'mtime_ns': info.st_mtime_ns, 'atime_ns': info.st_atime_ns,
            'uid': info.st_uid, 'gid': info.st_gid, 'nlink': info.st_nlink,
            'device': info.st_dev, 'inode': info.st_ino}


def fingerprint(path):
    info = metadata(path)
    info.pop('atime_ns')
    info['sha256'] = sha(path)
    return info


def verify_original(item):
    path = Path(item['logical_original_path'])
    current = metadata(path)
    for key in ('size', 'mode', 'mtime_ns', 'uid', 'gid', 'nlink', 'device', 'inode'):
        if current[key] != item['original_' + key]:
            raise RuntimeError('Original metadata changed (' + key + '): ' + str(path))
    if sha(path) != item['original_sha256']:
        raise RuntimeError('Original byte identity changed: ' + str(path))


def inventory():
    files = []
    for root in ROOTS:
        if root.is_symlink() or root.resolve() != root or not root.is_dir():
            raise RuntimeError('Unsafe build root: ' + str(root))
        names = set(root.glob('forge_*_tests'))
        names.update(root / name for name in ('forge_tests', 'forge_bench', 'libforge_core.a')
                     if (root / name).exists())
        names.update((root / 'CMakeFiles').rglob('*.o'))
        for path in sorted(names):
            if path.name == 'forge' or path.suffix == '.gz':
                raise RuntimeError('Excluded path selected: ' + str(path))
            info = metadata(path)
            archive = Path(str(path) + '.gz')
            if archive.exists() or archive.is_symlink():
                raise RuntimeError('Refusing existing archive path: ' + str(archive))
            files.append({'logical_original_path': str(path), 'archive_path': str(archive),
                          **{'original_' + key: value for key, value in info.items()},
                          'original_sha256': sha(path),
                          'removed_uncompressed_after_proofs': False})
    # Larger files first make room quickly, after complete inventory is recorded.
    return sorted(files, key=lambda item: (-item['original_size'], item['logical_original_path']))


def marker_text():
    return ('FROZEN_RESTORE_BEFORE_REBUILD\n'
            'Closed build test/object/library representations are losslessly preserved in read-only .gz files.\n'
            'Restore all logical original paths before rebuilding or running CTest in these directories.\n'
            'The main forge executable remains raw and unchanged. Use a fresh directory for new builds.\n'
            'Restore map: ' + str(MAP) + '\nRestore helper: ' + str(HELPER) + '\n'
            'Restore command: python ' + str(HELPER) + ' --map ' + str(MAP)
            + ' --restore-dir /path/to/new-empty-directory\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory-only', action='store_true')
    args = parser.parse_args()
    preflight = process_preflight()
    files = inventory()
    mains = {str(root / 'forge'): fingerprint(root / 'forge') for root in ROOTS}
    if args.inventory_only:
        print(json.dumps({'preflight': preflight, 'files': len(files),
                          'original_bytes': sum(item['original_size'] for item in files),
                          'main_forge_before': mains, 'free_bytes': shutil.disk_usage(BASE).free}, indent=2))
        return
    for path in (MAP, JOURNAL, SUMMARY):
        if path.exists() or path.is_symlink():
            raise RuntimeError('Refusing previous record: ' + str(path))
    for root in ROOTS:
        marker = root / MARKER
        if marker.exists() or marker.is_symlink():
            raise RuntimeError('Refusing previous marker: ' + str(marker))
    receipt = {'created_utc': utc(), 'logical_root': str(BASE),
               'scope_roots': [str(root) for root in ROOTS],
               'scope': 'Only test executables forge_tests/forge_*_tests/forge_bench, libforge_core.a, and CMakeFiles/**/*.o; main forge stays raw; existing .gz files excluded.',
               'adapted_from': str(BASE / 'space-agent/archive_closed_builds.py'),
               'restore_helper': str(HELPER), 'journal': str(JOURNAL),
               'free_bytes_before': shutil.disk_usage(BASE).free,
               'preflight_before': preflight, 'main_forge_before': mains,
               'files': files, 'commands': [], 'phase': 'inventory recorded; no original removed'}
    # Create the new map exclusively before any marker or archive is created.
    with MAP.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    sync_dir(OWN)
    journal('inventory_committed', files=len(files), original_bytes=sum(i['original_size'] for i in files))
    try:
        for root in ROOTS:
            with (root / MARKER).open('x', encoding='utf-8') as stream:
                stream.write(marker_text()); stream.flush(); os.fsync(stream.fileno())
            sync_dir(root)
        receipt['markers'] = [str(root / MARKER) for root in ROOTS]
        durable_json(MAP, receipt)
        for index, item in enumerate(files):
            path, archive = Path(item['logical_original_path']), Path(item['archive_path'])
            verify_original(item)
            item['preflight_before_compression'] = process_preflight()
            receipt['phase'] = 'compressing ' + str(index + 1) + '/' + str(len(files))
            durable_json(MAP, receipt)
            journal('compression_start', index=index, path=str(path))
            error_path = OWN / ('forge_sol_gzip_' + str(index).zfill(3) + '_20261025.stderr')
            command = ['gzip', '-n', '-6', '-c', str(path)]
            with archive.open('xb') as output, error_path.open('xb') as errors:
                result = subprocess.run(command, stdout=output, stderr=errors)
                output.flush(); os.fsync(output.fileno())
            receipt['commands'].append({'label': 'gzip-' + str(index), 'command': command,
                                        'returncode': result.returncode, 'stdout': str(archive), 'stderr': str(error_path)})
            if result.returncode != 0:
                raise RuntimeError('gzip failed for ' + str(path))
            item['archive_size'] = archive.stat().st_size
            item['archive_sha256'] = sha(archive)
            digest = hashlib.sha256(); size = 0
            error_path = OWN / ('forge_sol_roundtrip_' + str(index).zfill(3) + '_20261025.stderr')
            command = ['gzip', '-cd', str(archive)]
            with error_path.open('xb') as errors:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
                for block in iter(lambda: process.stdout.read(1024 * 1024), b''):
                    digest.update(block); size += len(block)
                process.stdout.close(); code = process.wait()
            receipt['commands'].append({'label': 'roundtrip-' + str(index), 'command': command,
                                        'returncode': code, 'stdout': 'full independent SHA256 and byte count', 'stderr': str(error_path)})
            item.update(roundtrip_sha256=digest.hexdigest(), roundtrip_size=size, roundtrip_returncode=code)
            if code != 0 or size != item['original_size'] or digest.hexdigest() != item['original_sha256']:
                raise RuntimeError('Full independent decompression proof failed: ' + str(path))
            verify_original(item)
            if sha(archive) != item['archive_sha256']:
                raise RuntimeError('Compressed archive changed: ' + str(archive))
            archive.chmod(0o444)
            # Keep original mtime on the archive; precise logical metadata remains in map.
            os.utime(archive, ns=(item['original_atime_ns'], item['original_mtime_ns']))
            with archive.open('rb') as source:
                os.fsync(source.fileno())
            sync_dir(archive.parent)
            archive_info = archive.stat()
            item.update(archive_mode=stat.S_IMODE(archive_info.st_mode), archive_device=archive_info.st_dev,
                        archive_inode=archive_info.st_ino, original_unchanged_through_proofs=True,
                        preflight_before_removal=process_preflight(),
                        unlink_intent_committed_utc=utc())
            # Durable proof and intent MUST precede unlink, for interruption recovery.
            receipt['phase'] = 'verified; unlink intent for ' + str(path)
            durable_json(MAP, receipt)
            journal('verified_unlink_intent', index=index, path=str(path), archive=str(archive),
                    original_sha256=item['original_sha256'], archive_sha256=item['archive_sha256'])
            verify_original(item)
            path.unlink()
            sync_dir(path.parent)
            item.update(removed_uncompressed_after_proofs=True, removed_utc=utc())
            receipt['phase'] = 'archived ' + str(index + 1) + '/' + str(len(files))
            durable_json(MAP, receipt)
            journal('uncompressed_representation_removed_after_proofs', index=index, path=str(path),
                    free_bytes=shutil.disk_usage(BASE).free)
            print(receipt['phase'] + ' free_bytes=' + str(shutil.disk_usage(BASE).free), flush=True)
        receipt['main_forge_after'] = {str(root / 'forge'): fingerprint(root / 'forge') for root in ROOTS}
        if receipt['main_forge_after'] != mains:
            raise RuntimeError('A main forge fingerprint changed')
        receipt['preflight_after'] = process_preflight()
        receipt['original_total_bytes'] = sum(i['original_size'] for i in files)
        receipt['archive_total_bytes'] = sum(i['archive_size'] for i in files)
        receipt['logical_reclaimed_bytes'] = receipt['original_total_bytes'] - receipt['archive_total_bytes']
        receipt['free_bytes_after'] = shutil.disk_usage(BASE).free
        receipt['phase'] = 'complete; all four closed profiles frozen; main forge unchanged'
        receipt['completed_utc'] = utc()
        durable_json(MAP, receipt)
        summary = {key: receipt[key] for key in ('phase', 'created_utc', 'completed_utc',
                    'original_total_bytes', 'archive_total_bytes', 'logical_reclaimed_bytes',
                    'free_bytes_before', 'free_bytes_after', 'main_forge_before', 'main_forge_after')}
        summary['files'] = len(files)
        summary['map'] = str(MAP)
        durable_json(SUMMARY, summary)
        journal('complete', summary=summary)
        print(json.dumps(summary, indent=2))
    except BaseException as error:
        receipt['phase'] = 'stopped after failure; originals retained unless already fully proven and journaled'
        receipt['failure'] = {'utc': utc(), 'type': type(error).__name__, 'message': str(error),
                              'traceback': traceback.format_exc()}
        try:
            durable_json(MAP, receipt)
            journal('failure', **receipt['failure'])
        except BaseException as save_error:
            print('Failure record save also failed: ' + repr(save_error), file=sys.stderr)
        raise


if __name__ == '__main__':
    main()
