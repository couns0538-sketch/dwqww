#!/usr/bin/env python3
"""Verify this archive and restore only into a NEW nonexistent scratch directory.

No engines, compilers, Git, network access, original-path writes or cleanup occur.
The expected external-manifest hash must come from the independently verified
publication receipt. Archive hashes establish identity, not chess correctness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import zipfile

BLOCK = 1024 * 1024
NAME = 'forge-pawn-span-fc23918-20261020-complete.manifest.json'
MODE_MEMBER = 'files/archive-provenance/LIVE-FILES-AND-MODES.json'


def safe_name(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and p.as_posix() == name and '\\' not in name


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(BLOCK), b''):
            h.update(block)
    return h.hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def restore(parts, destination, expected_manifest, manifest_name=NAME):
    parts, destination = Path(parts).resolve(strict=True), Path(destination)
    check(destination.is_absolute(), 'Scratch destination must be absolute')
    check(not destination.exists() and not destination.is_symlink(), 'Choose a NEW nonexistent scratch destination')
    check(destination.parent.is_dir() and not destination.parent.is_symlink(), 'Scratch parent must be an existing real directory')
    check(Path(manifest_name).name == manifest_name, 'Manifest must be a plain filename')
    check(re.fullmatch('[0-9a-f]{64}', expected_manifest), 'Supply the verified manifest SHA256')
    manifest_path = parts / manifest_name
    check(manifest_path.is_file() and not manifest_path.is_symlink(), 'Missing or symlinked manifest')
    check(digest(manifest_path) == expected_manifest, 'External manifest SHA256 mismatch')
    manifest = json.loads(manifest_path.read_bytes())
    check(manifest['format'] == 'raw-split-zip' and manifest['split_size'] == 67108864, 'Unexpected archive format')
    files = manifest['files']
    check(len({r['path'] for r in files}) == len(files), 'Duplicate payload paths')
    check(all(safe_name(r['path']) for r in files), 'Unsafe payload path')
    with tempfile.TemporaryFile() as combined:
        total, whole = 0, hashlib.sha256()
        names = set()
        for row in manifest['parts']:
            name = row['file']
            check(Path(name).name == name and name not in names, 'Unsafe or duplicate part name')
            names.add(name)
            source_path = parts / name
            check(source_path.is_file() and not source_path.is_symlink(), 'Missing or symlinked archive part')
            h, size = hashlib.sha256(), 0
            with source_path.open('rb') as source:
                for block in iter(lambda: source.read(BLOCK), b''):
                    h.update(block); whole.update(block); size += len(block); combined.write(block)
            check(size == row['size'] and h.hexdigest() == row['sha256'], 'Part integrity mismatch: ' + name)
            check(size <= 67108864, 'Unexpected oversized archive part')
            total += size
        check(total == manifest['archive']['size'] and whole.hexdigest() == manifest['archive']['sha256'], 'Combined ZIP integrity mismatch')
        combined.seek(0)
        with zipfile.ZipFile(combined) as archive:
            expected = {manifest['manifest_member']} | {'files/' + row['path'] for row in files}
            check(len(archive.namelist()) == len(set(archive.namelist())) == len(expected), 'Duplicate/missing ZIP members')
            check(set(archive.namelist()) == expected, 'Unexpected ZIP members')
            check(all(safe_name(info.filename) and not stat.S_ISLNK(info.external_attr >> 16) for info in archive.infolist()), 'Unsafe ZIP path or symlink')
            internal = json.loads(archive.read(manifest['manifest_member']))
            check(internal == {'schema_version': 1, 'files': files}, 'Internal/external file manifests differ')
            for row in files:
                h, size = hashlib.sha256(), 0
                with archive.open('files/' + row['path']) as source:
                    for block in iter(lambda: source.read(BLOCK), b''):
                        h.update(block); size += len(block)
                check(size == row['size'] and h.hexdigest() == row['sha256'], 'Payload integrity mismatch: ' + row['path'])
            modes = json.loads(archive.read(MODE_MEMBER))
            by_path = {row['path']: row for row in files}
            check(len({r['payload_path'] for r in modes['files']}) == len(modes['files']), 'Duplicate original mode records')
            for row in modes['files']:
                name = row['payload_path']
                check(safe_name(name) and name in by_path, 'Unsafe/missing mode-map file')
                check((row['sha256'], row['size']) == (by_path[name]['sha256'], by_path[name]['size']), 'Mode map and payload identity differ')
                check(isinstance(row['mode'], int) and 0 <= row['mode'] <= 0o777, 'Unsafe file mode')
            for row in modes['directories']:
                check(safe_name(row['payload_path']) and isinstance(row['mode'], int) and 0 <= row['mode'] <= 0o777, 'Unsafe directory mode record')
            # Verification precedes creation. Never extract over an existing tree.
            destination.mkdir(parents=False, exist_ok=False)
            for row in files:
                target = destination / 'files' / row['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open('files/' + row['path']) as source, target.open('xb') as output:
                    for block in iter(lambda: source.read(BLOCK), b''):
                        output.write(block)
                os.chmod(target, 0o600)
            for row in modes['directories']:
                (destination / 'files' / row['payload_path']).mkdir(parents=True, exist_ok=True)
            for row in modes['files']:
                target = destination / 'files' / row['payload_path']
                check(target.stat().st_size == row['size'] and digest(target) == row['sha256'], 'Restored original mismatch')
                os.chmod(target, row['mode'])
                os.utime(target, ns=(row['mtime_ns'], row['mtime_ns']))
            for row in sorted(modes['directories'], key=lambda r: len(PurePosixPath(r['payload_path']).parts), reverse=True):
                os.chmod(destination / 'files' / row['payload_path'], row['mode'])
    return {'status': 'PASS_NEW_SCRATCH_RECOVERY', 'destination': str(destination),
            'manifest_sha256': expected_manifest, 'payload_files_verified': len(files),
            'original_file_modes_restored': len(modes['files']), 'directory_modes_restored': len(modes['directories']),
            'engines_or_compilers_executed': False, 'original_absolute_paths_written': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--manifest-name', default=NAME)
    args = parser.parse_args()
    print(json.dumps(restore(args.parts, args.destination, args.manifest_sha256, args.manifest_name), indent=2))


if __name__ == '__main__':
    main()
