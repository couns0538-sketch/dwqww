#!/usr/bin/env python3
"""Restore this archive's exact logical bytes beneath a new empty destination."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--map', type=Path, default=Path(__file__).with_name('forge_sol_restore_map_20261025.json'))
parser.add_argument('--restore-dir', type=Path, required=True,
                    help='New or empty destination; no existing file is overwritten')
args = parser.parse_args()
manifest = json.loads(args.map.read_text())
logical_root = Path(manifest['logical_root'])
target_root = args.restore_dir.absolute()
if target_root.is_symlink() or target_root.resolve() != target_root:
    raise RuntimeError('Restore directory must not contain symlinks')
if target_root.exists() and (not target_root.is_dir() or any(target_root.iterdir())):
    raise RuntimeError('Restore directory must be new or empty')
target_root.mkdir(parents=True, exist_ok=True)
relative_paths = []
for item in manifest['files']:
    relative = Path(item['logical_original_path']).relative_to(logical_root)
    if '..' in relative.parts or relative in relative_paths:
        raise RuntimeError('Unsafe or duplicate logical path')
    relative_paths.append(relative)
    archive = Path(item['archive_path'])
    if archive.is_symlink() or sha(archive) != item['archive_sha256']:
        raise RuntimeError('Archive checksum mismatch: ' + str(archive))
    if item['original_uid'] != os.getuid():
        raise RuntimeError('Cannot preserve original owner without changing user')
for item, relative in zip(manifest['files'], relative_paths):
    archive = Path(item['archive_path'])
    destination = target_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(); size = 0
    with destination.open('xb') as output:
        with gzip.open(archive, 'rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                output.write(block); digest.update(block); size += len(block)
        output.flush(); os.fsync(output.fileno())
    if size != item['original_size'] or digest.hexdigest() != item['original_sha256']:
        raise RuntimeError('Restored byte identity failed: ' + str(destination))
    if destination.stat().st_gid != item['original_gid']:
        os.chown(destination, -1, item['original_gid'])
    destination.chmod(item['original_mode'])
    os.utime(destination, ns=(item['original_atime_ns'], item['original_mtime_ns']))
    info = destination.stat()
    if (info.st_uid != item['original_uid'] or info.st_gid != item['original_gid']
            or info.st_mtime_ns != item['original_mtime_ns']):
        raise RuntimeError('Restored metadata differs: ' + str(destination))
    with destination.open('rb') as restored:
        os.fsync(restored.fileno())
    parent = destination.parent
    while True:
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if parent == target_root:
            break
        parent = parent.parent
    print(str(destination) + ' SHA256=' + digest.hexdigest() + ' bytes=' + str(size))
