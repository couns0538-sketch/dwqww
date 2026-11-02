"""Original manifest verifier for an immutable isolated CPU Python runtime."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

TREES = ('python', 'packages', 'bootstrap_packages')


def verify(root, expected_manifest_sha):
    root = Path(root).resolve(strict=True)
    manifest_path = root/'RUNTIME_FILES.json'
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not re.fullmatch('[0-9a-fA-F]{64}', expected_manifest_sha) or digest.lower() != expected_manifest_sha.lower():
        raise ValueError('private runtime manifest SHA256 differs from preregistered input')
    record = json.loads(raw.decode('utf-8-sig'))
    if record.get('schema') != 1 or record.get('status') != 'RUNTIME_ASSEMBLED' or Path(record.get('root','')).resolve() != root:
        raise ValueError('wrong runtime manifest schema/status/root')
    declared = {}
    byte_count = 0
    for item in record['files']:
        relative = item['path']
        if not isinstance(relative,str) or '\\' in relative or ':' in relative:
            raise ValueError('runtime file path must be normalized relative POSIX spelling')
        parts = PurePosixPath(relative).parts
        if not parts or parts[0] not in TREES or any(part in ('.','..') for part in relative.split('/')) or '/'.join(parts) != relative:
            raise ValueError('runtime file path escaped explicit input trees')
        key = relative.casefold()
        if key in declared:
            raise ValueError('duplicate runtime file identity')
        path = root.joinpath(*parts)
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError('runtime file resolved outside private root')
        for entry in (path,*path.parents):
            if entry.is_symlink() or getattr(entry.lstat(),'st_file_attributes',0) & 0x400:
                raise ValueError('runtime reparse input refused')
            if entry == root: break
        before = path.stat()
        sha = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                sha.update(block)
        after = path.stat()
        if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('runtime input changed while hashing')
        if after.st_size != item['bytes'] or sha.hexdigest().lower() != item['sha256'].lower():
            raise ValueError('private runtime file differs from assembled manifest: '+relative)
        declared[key] = relative
        byte_count += after.st_size
    actual = set()
    for name in TREES:
        tree = root/name
        if not tree.is_dir(): raise ValueError('private runtime input tree missing: '+name)
        for folder, directories, names in os.walk(tree,followlinks=False):
            for entry in [Path(folder),*(Path(folder)/name for name in directories)]:
                if entry.is_symlink() or getattr(entry.lstat(),'st_file_attributes',0) & 0x400:
                    raise ValueError('runtime reparse directory refused')
            actual.update((Path(folder)/name).relative_to(root).as_posix().casefold() for name in names)
    if actual != set(declared):
        raise ValueError('private runtime file set differs from manifest')
    if manifest_path.read_bytes() != raw:
        raise ValueError('private runtime manifest changed during verification')
    return {'manifest':str(manifest_path),'sha256':digest,'files':len(declared),'bytes':byte_count,
            'scope':'all files in python/packages/bootstrap_packages; execution caches are outside this immutable root'}
