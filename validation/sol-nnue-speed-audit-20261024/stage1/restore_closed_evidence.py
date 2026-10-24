#!/usr/bin/env python3
"""Restore archived logical evidence beneath a caller-selected empty directory."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--map', type=Path, default=Path(__file__).with_name('closed-evidence-restore-map.json'))
parser.add_argument('--restore-dir', type=Path, required=True,
                    help='Destination root; existing destination files are never overwritten')
args = parser.parse_args()
manifest = json.loads(args.map.read_text())
logical_root = Path(manifest.get('logical_root', args.map.parent)).resolve()
target_root = args.restore_dir.resolve()

for item in manifest['files']:
    archive = Path(item['archive_path'])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != item['archive_sha256']:
        raise RuntimeError('Archive checksum mismatch: ' + str(archive))
    relative = Path(item['logical_original_path']).relative_to(logical_root)
    destination = target_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    # Exclusive creation protects both restored files and any retained originals.
    with destination.open('xb') as output:
        with gzip.open(archive, 'rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                output.write(block)
                digest.update(block)
                size += len(block)
    if size != item['original_size'] or digest.hexdigest() != item['original_sha256']:
        raise RuntimeError('Restored byte identity failed: ' + str(destination))
    destination.chmod(item['original_mode'])
    os.utime(destination, ns=(item['original_atime_ns'], item['original_mtime_ns']))
    print(str(destination) + ' SHA256=' + digest.hexdigest() + ' bytes=' + str(size))
