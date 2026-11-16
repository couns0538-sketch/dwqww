#!/usr/bin/env python3
"""pick_set.py N INFILE OUTFILE SEED : deterministic first-N / random-N selection helper (records the picks)."""
import random, sys
n = int(sys.argv[1]); inf = sys.argv[2]; outf = sys.argv[3]; seed = int(sys.argv[4])
lines = [l.strip() for l in open(inf) if l.strip()]
rng = random.Random(seed)
if n >= len(lines):
    picked = lines
else:
    picked = rng.sample(lines, n) if "random" in outf else lines[:n]
with open(outf, "w") as f:
    for l in picked:
        f.write(l + "\n")
print(f"{len(picked)} of {len(lines)} written to {outf} (seed {seed})")
