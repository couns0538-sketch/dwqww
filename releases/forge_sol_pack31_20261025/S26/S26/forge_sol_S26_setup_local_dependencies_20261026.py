#!/usr/bin/env python3
"""Verify delivered S26 bytes and create owner-local dependency/empty-lock files."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DECLARATIONS_SHA256 = '8a719c05c2e94b918c3e9b70fdc8b03036ffa23488748b848d5baa0541472744'
V4_SHA256 = '4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f'
NAMES = ('screen', 'fma', 'pins', 'recipe')
DECLARATIONS = 'S26/forge_sol_S26_dependencies_20261026.json'
V4 = 'S26/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py'


def absolute(path, *, directory=False):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError('absolute physical paths without symlink components required: ' + str(path))
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError('required packet input missing: ' + str(path))
    return path


def verified_bytes(path, expected):
    data = absolute(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('SHA256 mismatch: ' + str(path))
    return data


def new_output(path, root):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path or os.path.lexists(path):
        raise ValueError('output must be a NEW absolute nonsymlink path: ' + str(path))
    if not path.is_relative_to(root) or not path.parent.is_dir():
        raise ValueError('output must have an existing parent inside --packet-root: ' + str(path))
    return path


def setup(packet_root, output, lock_file):
    root = absolute(packet_root, directory=True)
    declarations = json.loads(verified_bytes(root / DECLARATIONS, DECLARATIONS_SHA256))
    if set(declarations) != set(NAMES):
        raise ValueError('frozen declaration helper set differs')
    verified_bytes(root / V4, V4_SHA256)
    local = {}
    for name in NAMES:
        record = declarations[name]
        path = root / 'provided_tools' / name / Path(record['path']).name
        verified_bytes(path, record['sha256'])
        local[name] = {'path': str(path), 'sha256': record['sha256']}
    # Validate both destinations before creating either file. Never edit inputs.
    output, lock_file = new_output(output, root), new_output(lock_file, root)
    if output == lock_file:
        raise ValueError('dependency output and lock must be distinct NEW files')
    data = (json.dumps(local, indent=2) + '\n').encode()
    with output.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    with lock_file.open('xb') as stream:
        stream.flush()
        os.fsync(stream.fileno())
    return {'status': 'PASS', 'dependencies': str(output), 'lock_file': str(lock_file),
            'helper_count': len(local), 'original_declarations_sha256': DECLARATIONS_SHA256,
            'delivered_v4_sha256': V4_SHA256,
            'scope': 'Verified delivered bytes only; no imports, compiler, engine, installation, pin edits or native qualification.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='NEW dependency FILE inside packet root')
    parser.add_argument('--lock-file', type=Path, required=True, help='NEW empty local lock FILE inside packet root')
    args = parser.parse_args(argv)
    print(json.dumps(setup(args.packet_root, args.out, args.lock_file), sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('S26 LOCAL SETUP FAIL: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
