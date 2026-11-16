#!/usr/bin/env python3
"""Sharded reference perft with LOUD failure on any inconsistency.

Hardened after I found that this script's fixed /tmp shard paths let a STALE shard file from an
earlier run be merged into a new result, producing 1,929 phantom differences. It now:

  * uses a fresh unique working directory per run (never a reused /tmp path);
  * checks every shard's line count equals its expected position count x depths;
  * checks every shard exited 0;
  * refuses to write OUT at all if anything is off.

Usage: ref_par.py FENS OUT DEPTHS WORKERS
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

FENS, OUT, DEPTHS, WORKERS = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])

fens = [l.strip() for l in open(FENS) if l.strip()]
n = len(fens)
ndepths = len([d for d in DEPTHS.split(",") if d])
if n == 0:
    raise SystemExit("FAIL: %s holds no positions" % FENS)

workdir = tempfile.mkdtemp(prefix="refpar-")
print("workdir", workdir, "positions", n, "workers", WORKERS, flush=True)

shards = []
procs = []
t0 = time.monotonic()
for k in range(WORKERS):
    lo = n * k // WORKERS
    hi = n * (k + 1) // WORKERS
    if hi <= lo:
        continue
    part_fen = os.path.join(workdir, "part%d.fens" % k)
    with open(part_fen, "w") as f:
        f.write("\n".join(fens[lo:hi]) + "\n")
    out = os.path.join(workdir, "part%d.txt" % k)
    shards.append((lo, hi, out, hi - lo))
    log = open(os.path.join(workdir, "part%d.log" % k), "w")
    procs.append((subprocess.Popen(["python3", "ref_perft.py", part_fen, out, DEPTHS],
                                   stdout=log, stderr=subprocess.STDOUT), k))

failed = []
for p, k in procs:
    rc = p.wait()
    if rc != 0:
        failed.append((k, rc))
if failed:
    raise SystemExit("FAIL: reference shards failed: %s (workdir %s)" % (failed, workdir))

merged = 0
for lo, hi, path, expect in shards:
    if not os.path.exists(path):
        raise SystemExit("FAIL: shard file %s missing" % path)
    rows = [l for l in open(path) if not l.startswith("#") and l.strip()]
    want = expect * ndepths
    if len(rows) != want:
        raise SystemExit("FAIL: shard %s has %d records, expected %d positions x %d depths = %d"
                         % (path, len(rows), expect, ndepths, want))
    merged += len(rows)
    # every row must be numeric
    for r in rows:
        p = r.split()
        if len(p) < 4 or not p[2].isdigit():
            raise SystemExit("FAIL: shard %s holds a non-numeric row: %r" % (path, r))

if merged != n * ndepths:
    raise SystemExit("FAIL: merged %d records, expected %d x %d = %d"
                     % (merged, n, ndepths, n * ndepths))

with open(OUT, "w") as out:
    out.write("# idx depth nodes marker\n")
    for lo, hi, path, expect in shards:
        for line in open(path):
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            out.write("%d %s\n" % (int(p[0]) + lo, " ".join(p[1:])))

print("ref merged %d positions x %d depths = %d records in %.1f s"
      % (n, ndepths, merged, time.monotonic() - t0), flush=True)
print("workdir kept:", workdir)
