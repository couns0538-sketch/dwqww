#!/usr/bin/env python3
"""Copy the second self-play folder's files to scratch with read-only opens (S40 real run, Opus 5.5, 2026-10-27).
usage: python -I -B real_stage_inputs_s40.py SRC_DIR DST_DIR NAME...
The sources are hashed before and after the copy (they must be unchanged); the destination files are new ('x' mode).
The generator's SQLite DB is copied together with its -wal file, so the copy holds the committed offsets."""
import hashlib
import json
import os
import sys
from pathlib import Path


def sha_md5(p):
    s, m = hashlib.sha256(), hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            s.update(b); m.update(b)
    return s.hexdigest(), m.hexdigest(), os.path.getsize(p), os.path.getmtime(p)


src, dst = Path(sys.argv[1]), Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
report = []
for name in sys.argv[3:]:
    a = src / name
    before = sha_md5(a)
    with open(a, "rb") as fi, open(dst / name, "xb") as fo:
        for b in iter(lambda: fi.read(1 << 22), b""):
            fo.write(b)
    after = sha_md5(a); copy = sha_md5(dst / name)
    report.append({"name": name, "bytes": before[2], "sha256": before[0], "md5": before[1], "source_mtime": before[3],
                   "source_unchanged": before == after, "copy_identical": copy[:3] == before[:3]})
print(json.dumps(report, indent=1))
sys.exit(0 if all(r["source_unchanged"] and r["copy_identical"] for r in report) else 1)
