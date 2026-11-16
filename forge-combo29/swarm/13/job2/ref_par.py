#!/usr/bin/env python3
"""Sharded reference perft: one worker per shard of the FEN file, merged output.

Usage: ref_par.py FENS OUT DEPTHS WORKERS
Each worker writes raw_ref.part<k>.txt; merged in index order into OUT.
"""
import subprocess
import sys
import time

FENS, OUT, DEPTHS, WORKERS = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])

fens = [l.strip() for l in open(FENS) if l.strip()]
n = len(fens)
shards = []
procs = []
t0 = time.monotonic()
for k in range(WORKERS):
    lo = n * k // WORKERS
    hi = n * (k + 1) // WORKERS
    part_fen = f"/tmp/refpart{k}.fens"
    with open(part_fen, "w") as f:
        f.write("\n".join(fens[lo:hi]) + "\n")
    out = f"/tmp/refpart{k}.txt"
    shards.append((lo, hi, out))
    procs.append(subprocess.Popen(
        ["python3", "ref_perft.py", part_fen, out, DEPTHS],
        stdout=open(f"/tmp/refpart{k}.log", "w"), stderr=subprocess.STDOUT))
for p in procs:
    p.wait()

with open(OUT, "w") as out:
    out.write("# idx depth nodes marker\n")
    for lo, hi, path in shards:
        for line in open(path):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            out.write(f"{int(parts[0]) + lo} {' '.join(parts[1:])}\n")
print("ref merged", n, "positions", round(time.monotonic() - t0, 1), "s")
