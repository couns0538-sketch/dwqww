#!/usr/bin/env python3
"""Verify or restore dated S27 original-byte records into a NEW directory."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def load(archive, index):
    expected = json.loads(index.read_text())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected['archive_sha256']:
        raise ValueError('archive SHA256 mismatch')
    rows = []
    seen = set()
    with gzip.open(archive, 'rt', encoding='utf-8', newline='') as stream:
        for line in stream:
            row = json.loads(line)
            name = row['relative_path']
            safe = PurePosixPath(name)
            if (not name or safe.is_absolute() or safe.as_posix() != name or
                    any(part in ('.', '..', '') or ':' in part for part in safe.parts) or
                    '\\' in name or name in seen):
                raise ValueError('unsafe or duplicate record path')
            data = base64.b64decode(row['base64'], validate=True)
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('record SHA256/size mismatch: ' + name)
            seen.add(name)
            rows.append((row, data))
    actual = [{key: row[key] for key in ('relative_path', 'bytes', 'sha256')} for row, _ in rows]
    if actual != expected['files']:
        raise ValueError('record index mismatch')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--out', type=Path, help='New directory; omitted means verify only')
    args = parser.parse_args()
    rows = load(args.archive, args.index)
    if args.out is not None:
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('output already exists')
        if any(parent.is_symlink() for parent in args.out.absolute().parents):
            raise ValueError('symlink output ancestor')
        args.out.mkdir(parents=True)
        for row, data in rows:
            target = args.out.joinpath(*PurePosixPath(row['relative_path']).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
    print('VERIFIED records=' + str(len(rows)) + ('; restored to NEW output' if args.out else '; no files written'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit('error: ' + str(error))
