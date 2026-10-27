#!/usr/bin/env python3
"""Pack a built S40 fixture directory into a deterministic .tar.gz (sorted members, mtime 0, uid/gid 0).
usage: python -I -B pack_fixture_s40.py FIXTURE_DIR OUT.tar.gz   (OUT must not exist)"""
import gzip
import hashlib
import io
import sys
import tarfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
if out.exists():
    sys.exit(f"{out} exists (never overwritten)")
top = "forge_sol_S40_fixture_20261027"
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as t:
    paths = sorted(p for p in src.rglob("*"))
    for d in [top] + [f"{top}/{p.relative_to(src).as_posix()}" for p in paths if p.is_dir()]:
        ti = tarfile.TarInfo(d); ti.type = tarfile.DIRTYPE; ti.mode = 0o755; ti.mtime = 0
        t.addfile(ti)
    for p in paths:
        if p.is_file():
            data = p.read_bytes()
            ti = tarfile.TarInfo(f"{top}/{p.relative_to(src).as_posix()}"); ti.size = len(data); ti.mode = 0o644; ti.mtime = 0
            t.addfile(ti, io.BytesIO(data))
raw = io.BytesIO()
with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as z:
    z.write(buf.getvalue())
with open(out, "xb") as f:
    f.write(raw.getvalue())
print(out, len(raw.getvalue()), hashlib.sha256(raw.getvalue()).hexdigest())
