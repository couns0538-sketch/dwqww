#!/usr/bin/env python3
"""Original binary transport chunks (not independently extractable archives).

split ARCHIVE NEW_DIR [--part-bytes N]; verify DIR/transport_manifest.json;
join DIR/transport_manifest.json NEW_ARCHIVE. Never overwrites or deletes.
Joining retains NEW_ARCHIVE.partial and publishes via an atomic exclusive hard
link; the partial and final file share storage, not independent backups. A
filesystem without hard-link support fails safely, retaining the partial.
IDEA_SOURCE: user durable-evidence contract and Python standard-library APIs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re

MAX_PART = 1_800_000_000
MAX_PARTS = 10_000  # Bounds metadata below the 4 MiB reader limit and limits RAM.
BUFFER = 1024 * 1024
MANIFEST = 'transport_manifest.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def name_ok(name):
    return (isinstance(name, str) and name not in ('', '.', '..')
            and not any(c in name for c in '/\\\x00:<>"|?*')
            and not name.endswith(('.', ' ')) and not PureWindowsPath(name).drive)


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(BUFFER), b''):
            result.update(block)
    return result.hexdigest()


def snapshot(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate manifest key')
        result[key] = value
    return result


def validate(data):
    require(isinstance(data, dict) and data.get('format') == 'forge-transport-v1', 'manifest format')
    cap = data.get('part_bytes')
    require(type(cap) is int and 1 <= cap <= MAX_PART, 'part size outside transport limit')
    whole, parts = data.get('whole'), data.get('parts')
    require(isinstance(whole, dict) and name_ok(whole.get('name')), 'unsafe whole filename')
    require(type(whole.get('size')) is int and whole['size'] >= 0, 'whole size')
    require(isinstance(parts, list), 'parts list')
    require(len(parts) <= MAX_PARTS, 'transport part count exceeds 10000')
    require(isinstance(whole.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', whole['sha256']), 'whole digest syntax')
    offset = 0
    for index, part in enumerate(parts):
        require(isinstance(part, dict), 'part entry')
        require(part.get('name') == f'transport_part_{index:06d}.bin', 'unsafe or unordered part filename')
        require(type(part.get('offset')) is int and part['offset'] == offset, 'part offset')
        require(type(part.get('size')) is int and part['size'] == min(cap, whole['size'] - offset) and part['size'] > 0, 'part size')
        require(isinstance(part.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', part['sha256']), 'part digest syntax')
        offset += part['size']
    require(offset == whole['size'], 'whole size disagrees with ordered parts')
    return data


def check_files(data, directory, manifest_present=True):
    expected = {part['name'] for part in data['parts']}
    if manifest_present:
        expected.add(MANIFEST)
    require({path.name for path in directory.iterdir()} == expected, 'missing or extra transport files')
    for part in data['parts']:
        path = directory / part['name']
        require(not path.is_symlink(), 'symlinked transport part')
        require(path.is_file() and path.stat().st_size == part['size'], 'part file size mismatch')


def check_bytes(data, directory, destination=None, manifest_present=True):
    check_files(data, directory, manifest_present)
    whole = hashlib.sha256()
    for part in data['parts']:
        actual, count = hashlib.sha256(), 0
        with (directory / part['name']).open('rb') as source:
            for block in iter(lambda: source.read(BUFFER), b''):
                count += len(block); actual.update(block); whole.update(block)
                if destination is not None:
                    destination.write(block)
        require(count == part['size'] and actual.hexdigest() == part['sha256'], 'part size/digest mismatch')
    require(whole.hexdigest() == data['whole']['sha256'], 'whole digest mismatch')
    check_files(data, directory, manifest_present)


def verify(manifest):
    manifest = Path(manifest)
    require(manifest.name == MANIFEST and not manifest.is_symlink(), 'invalid or symlinked manifest')
    before = snapshot(manifest)
    with manifest.open('rb') as source:
        raw = source.read(4 * BUFFER + 1)
    require(len(raw) <= 4 * BUFFER, 'manifest too large')
    data = validate(json.loads(raw, object_pairs_hook=unique_object))
    check_bytes(data, manifest.parent)
    require(snapshot(manifest) == before and digest(manifest) == hashlib.sha256(raw).hexdigest(), 'manifest changed during verification')
    return data


def split(archive, directory, part_bytes=MAX_PART):
    archive, directory = Path(archive), Path(directory)
    require(type(part_bytes) is int and 1 <= part_bytes <= MAX_PART, 'part size outside transport limit')
    require(name_ok(archive.name) and not archive.is_symlink() and archive.is_file(), 'invalid source archive')
    before = snapshot(archive)
    require((before[2] + part_bytes - 1) // part_bytes <= MAX_PARTS,
            'transport part count exceeds 10000; increase --part-bytes')
    directory.mkdir(parents=True, exist_ok=False)
    data = {'format': 'forge-transport-v1', 'part_bytes': part_bytes,
            'whole': {'name': archive.name, 'size': before[2]}, 'parts': []}
    whole, offset = hashlib.sha256(), 0
    with archive.open('rb') as source:
        while offset < before[2]:
            size = min(part_bytes, before[2] - offset)
            part = {'name': f'transport_part_{len(data["parts"]):06d}.bin', 'offset': offset, 'size': size}
            actual, left = hashlib.sha256(), size
            with (directory / part['name']).open('xb') as target:
                while left:
                    block = source.read(min(BUFFER, left))
                    require(bool(block), 'source archive truncated during split')
                    target.write(block); actual.update(block); whole.update(block); left -= len(block)
                target.flush(); os.fsync(target.fileno())
            part['sha256'] = actual.hexdigest(); data['parts'].append(part); offset += size
        require(not source.read(1), 'source archive grew during split')
    data['whole']['sha256'] = whole.hexdigest()
    check_bytes(validate(data), directory, manifest_present=False)
    require(digest(archive) == data['whole']['sha256'] and snapshot(archive) == before, 'source archive changed during split')
    manifest = directory / MANIFEST
    with manifest.open('x', encoding='utf-8', newline='\n') as target:
        json.dump(data, target, sort_keys=True, indent=2); target.write('\n')
        target.flush(); os.fsync(target.fileno())
    return manifest


def join(manifest, destination):
    manifest, destination = Path(manifest), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('destination already exists')
    manifest_before = digest(manifest)
    data = verify(manifest)
    require(destination.parent.resolve() != manifest.parent.resolve(), 'join destination must be outside the parts directory')
    partial = destination.with_name(destination.name + '.partial')
    with partial.open('xb') as target:
        check_bytes(data, manifest.parent, target)
        target.flush(); os.fsync(target.fileno())
    require(snapshot(partial)[2] == data['whole']['size'] and digest(partial) == data['whole']['sha256'], 'joined partial digest mismatch')
    require(digest(manifest) == manifest_before, 'manifest changed during join')
    # link() fails if destination exists on both Windows and POSIX; rename()
    # would overwrite on POSIX. Retain the partial on success and every failure.
    os.link(partial, destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('split'); command.add_argument('archive', type=Path); command.add_argument('directory', type=Path)
    command.add_argument('--part-bytes', type=int, default=MAX_PART)
    command = commands.add_parser('verify'); command.add_argument('manifest', type=Path)
    command = commands.add_parser('join'); command.add_argument('manifest', type=Path); command.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'split':
            print(split(args.archive, args.directory, args.part_bytes))
        elif args.command == 'verify':
            print(json.dumps({'status': 'PASS', 'whole': verify(args.manifest)['whole']}, sort_keys=True))
        else:
            print(join(args.manifest, args.destination))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'FAIL: {error}; existing files and partials retained\n')


if __name__ == '__main__':
    main()
