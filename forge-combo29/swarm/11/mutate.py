#!/usr/bin/env python3
"""mutate.py SEED N OUTFENS OUTMUT : 20,000 FENs from G and R, ONE random mutation each.

Mutations (the brief's list): replace a character, insert a character, delete a
character, swap two fields, drop a field. The mutation applied is written beside
the FEN in OUTMUT as "<index>\\t<mutation description>\\t<mutated fen>".
"""
import random, sys

seed, n, out_fens, out_mut = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
rng = random.Random(seed)

src = []
for path in ("forge-combo29/swarm/11/positions/G_set_G.epd",
             "forge-combo29/swarm/11/positions/R_seed1101.fens"):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            src.append(line.split(";")[0].strip().split(" ")[:6])
            if len(src[-1]) != 6:
                src.pop()

ALPHA = list("pnbrqkPNBRQK12345678/-w b0123456789abcdefgh ")

out = []
seen = set()
tries = 0
while len(out) < n and tries < n * 40:
    tries += 1
    fields = list(rng.choice(src))
    kind = rng.choice(["replace", "insert", "delete", "swap", "drop"])
    if kind == "replace":
        fi = rng.randrange(6)
        if not fields[fi]:
            continue
        ci = rng.randrange(len(fields[fi]))
        new = rng.choice(ALPHA)
        old = fields[fi][ci]
        fields[fi] = fields[fi][:ci] + new + fields[fi][ci + 1:]
        desc = f"replace field{fi+1}[{ci}] {old!r}->{new!r}"
    elif kind == "insert":
        fi = rng.randrange(6)
        ci = rng.randrange(len(fields[fi]) + 1)
        new = rng.choice(ALPHA)
        fields[fi] = fields[fi][:ci] + new + fields[fi][ci:]
        desc = f"insert field{fi+1}[{ci}] {new!r}"
    elif kind == "delete":
        fi = rng.randrange(6)
        if len(fields[fi]) < 2:
            continue
        ci = rng.randrange(len(fields[fi]))
        old = fields[fi][ci]
        fields[fi] = fields[fi][:ci] + fields[fi][ci + 1:]
        desc = f"delete field{fi+1}[{ci}] {old!r}"
    elif kind == "swap":
        a, b = rng.sample(range(6), 2)
        fields[a], fields[b] = fields[b], fields[a]
        desc = f"swap fields {a+1}<->{b+1}"
    else:
        fi = rng.randrange(6)
        if len(fields) <= 1:
            continue
        removed = fields.pop(fi)
        desc = f"drop field{fi+1} {removed!r}"
    fen = " ".join(fields)
    if fen in seen:
        continue
    seen.add(fen)
    out.append((desc, fen))

with open(out_fens, "w") as ff, open(out_mut, "w") as fm:
    for i, (desc, fen) in enumerate(out):
        ff.write(fen + "\n")
        fm.write(f"{i}\t{desc}\t{fen}\n")
print("wrote", len(out), "mutated fens, tried", tries)
