"""Unpack verified wheels into the isolated test runtime; no package code runs."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tarfile
import time
import zipfile
sys.path.insert(0, str(Path(__file__).parent/'regression'))
from path_guard import no_reparse, owned

ROOT = Path('D:/a11/runtime')
MAX_NEW_BYTES = 2_500_000_000


def guard(reservation=0):
    if shutil.disk_usage('C:/').free < 30 * 1024**3 or shutil.disk_usage('D:/').free < 50 * 1024**3 + reservation:
        raise ValueError('C30GiB / D50GiB plus reservation floor')
    for path in (ROOT, ROOT.parent):
        no_reparse(path)


def digest(path):
    path = no_reparse(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verified_archive(row):
    path = no_reparse(row['path'])
    if path.parent != ROOT / 'downloads' or path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
        raise ValueError('archive outside explicit download directory')
    if path.stat().st_size != row['bytes'] or digest(path) != row['sha256']:
        raise ValueError('archive identity mismatch')
    return path


def safe_name(name):
    parts = PurePosixPath(name).parts
    if not parts or '\\' in name or ':' in name or name.startswith('/') or any(p in ('', '.', '..') for p in name.rstrip('/').split('/')):
        raise ValueError('unsafe archive member')
    return parts


def write_file(path, source):
    path = owned(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        shutil.copyfileobj(source, out, 1024 * 1024)
        out.flush(); os.fsync(out.fileno())


def tree_files(root):
    pending = [no_reparse(root)]
    while pending:
        folder = pending.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                path = no_reparse(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    yield path


def verify_bootstrap():
    # The archive digests are pinned to the original official R10 receipts.
    archives = [('python.3.12.10.nupkg', '0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8', 'python'),
                ('pip-25.3-py3-none-any.whl', '9655943313a94722b7774661c21049070f6bbb0a1516bf02f7c8d5d9201514cd', 'bootstrap_packages')]
    for name, expected, prefix in archives:
        path = ROOT / 'downloads' / name
        if digest(path) != expected:
            raise ValueError('bootstrap archive differs')
        declared = set()
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member = info.filename
                if prefix == 'python':
                    if not member.startswith('tools/'):
                        continue
                    member = member[6:]
                safe_name(member)
                actual = ROOT / prefix / member
                if digest(actual) != hashlib.sha256(archive.read(info)).hexdigest():
                    raise ValueError('extracted bootstrap bytes differ')
                declared.add(member.casefold())
        actual_names = {p.relative_to(ROOT / prefix).as_posix().casefold() for p in tree_files(ROOT / prefix)}
        if actual_names != declared:
            raise ValueError('bootstrap extracted file set differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--lock-sha256', required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        raise ValueError('Windows native qualification required')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    kernel.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    proc = kernel.GetCurrentProcess(); affinity = ctypes.c_size_t(); system = ctypes.c_size_t()
    if kernel.GetPriorityClass(proc) != 0x40 or not kernel.GetProcessAffinityMask(proc, ctypes.byref(affinity), ctypes.byref(system)) or affinity.value not in (4, 8):
        raise ValueError('Idle single admitted CPU2 or CPU3 required')
    guard(MAX_NEW_BYTES)
    lock_path = ROOT / 'WHEEL_LOCK.json'; raw = lock_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.lock_sha256.lower():
        raise ValueError('wheel lock changed')
    lock = json.loads(raw)
    if lock['status'] != 'VERIFIED_OFFICIAL_DOWNLOADS' or len(lock['wheels']) != 31:
        raise ValueError('exact original dependency lock required')
    verify_bootstrap()
    chess_row = json.loads((ROOT / 'CHESS_SOURCE.json').read_bytes())
    chess_archive = verified_archive(chess_row)
    packages = ROOT / 'packages'
    if packages.exists() or (ROOT / 'RUNTIME_FILES.json').exists():
        raise ValueError('fresh package assembly required; preserve previous attempt')
    total = 0
    archives = []
    for row in lock['wheels']:
        path = verified_archive(row)
        with zipfile.ZipFile(path) as archive:
            observed = 0; seen = set()
            for info in archive.infolist():
                safe_name(info.filename)
                if info.filename.casefold() in seen or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('duplicate or symlink wheel member')
                seen.add(info.filename.casefold()); observed += info.file_size
            if observed != row['expanded_bytes']:
                raise ValueError('expanded wheel size differs')
        total += observed; archives.append((row, path))
    if total > MAX_NEW_BYTES - 100_000_000:
        raise ValueError('package expansion exceeds reservation')
    started = time.monotonic(); packages.mkdir()
    for row, path in archives:
        guard(total + 10_000_000)
        if time.monotonic() - started > 1800:
            raise ValueError('cooperative assembly deadline; retained partial package tree')
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                parts = safe_name(info.filename)
                if parts[0].endswith('.data'):
                    # Only the pinned SymPy manual is present in this lock.
                    if parts[1:] != ('data', 'share', 'man', 'man1', 'isympy.1') or row['name'] != 'sympy':
                        raise ValueError('unreviewed wheel relocation')
                    parts = parts[2:]
                with archive.open(info) as stream:
                    write_file(packages.joinpath(*parts), stream)
        total -= row['expanded_bytes']
    with tarfile.open(chess_archive, 'r:gz') as archive:
        total_chess = 0
        for member in archive.getmembers():
            parts = safe_name(member.name)
            if not member.isfile() or parts[0] != 'chess-1.11.2':
                continue
            if parts[1] == 'chess':
                dest = packages.joinpath(*parts[1:])
            elif parts[1:] == ('LICENSE.txt',):
                dest = packages / 'chess-1.11.2.dist-info' / 'LICENSE.txt'
            elif parts[1:] == ('PKG-INFO',):
                dest = packages / 'chess-1.11.2.dist-info' / 'METADATA'
            else:
                continue
            total_chess += member.size
            if total_chess > 5_000_000:
                raise ValueError('chess source size bound')
            with archive.extractfile(member) as stream:
                write_file(dest, stream)
    if not (packages / 'chess/__init__.py').is_file() or not (packages / 'chess-1.11.2.dist-info/LICENSE.txt').is_file():
        raise ValueError('chess package/license incomplete')
    verify_bootstrap()
    files = []
    for prefix in ('python', 'packages', 'bootstrap_packages'):
        for path in tree_files(ROOT / prefix):
            files.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)})
    files.sort(key=lambda item: item['path'].casefold())
    result = {'schema': 1, 'status': 'RUNTIME_ASSEMBLED', 'classification': 'UNPROVEN', 'root': str(ROOT),
              'files': files, 'wheel_lock_sha256': args.lock_sha256.lower(), 'installed_versions': {r['name']: r['version'] for r in lock['wheels']} | {'chess': '1.11.2'},
              'scope': 'Verified direct wheel extraction and external GPL chess test dependency only; no Torch/NPT import or training/GPU execution',
              'runtime_file_bytes': sum(item['bytes'] for item in files)}
    guard()
    with (ROOT / 'RUNTIME_FILES.json').open('x', encoding='utf8', newline='\n') as stream:
        json.dump(result, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': result['status'], 'files': len(files), 'bytes': result['runtime_file_bytes']}))


if __name__ == '__main__':
    main()
