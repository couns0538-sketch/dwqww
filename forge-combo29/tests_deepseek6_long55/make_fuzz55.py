#!/usr/bin/env python3
"""make_fuzz55.py -- 20,000 FENs made from G by random mutations (seed 55).
One mutation per FEN, written beside it: replace / insert / delete one character, swap two
fields, drop a field."""
import random
import sys

random.seed(55)
src = [l.strip() for l in open("/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd",
                               encoding="utf-8", errors="replace") if l.strip()]
out = []
for i in range(20000):
    fen = random.choice(src)
    fields = fen.split()
    kind = random.choice(["replace", "insert", "delete", "swap", "drop"])
    if kind == "replace":
        # replace one character somewhere in the FEN string
        pos = random.randrange(len(fen))
        c = random.choice("pnbrqkPNBRQK12345678/w-")
        mutated = fen[:pos] + c + fen[pos + 1:]
        note = f"replace char at {pos} with {c!r}"
    elif kind == "insert":
        pos = random.randrange(len(fen) + 1)
        c = random.choice("pnbrqkPNBRQK12345678/w- ")
        mutated = fen[:pos] + c + fen[pos:]
        note = f"insert {c!r} at {pos}"
    elif kind == "delete":
        pos = random.randrange(len(fen))
        mutated = fen[:pos] + fen[pos + 1:]
        note = f"delete char at {pos} ({fen[pos]!r})"
    elif kind == "swap" and len(fields) >= 2:
        i1, i2 = random.sample(range(len(fields)), 2)
        fields[i1], fields[i2] = fields[i2], fields[i1]
        mutated = " ".join(fields)
        note = f"swap fields {i1} and {i2}"
    elif kind == "drop" and len(fields) >= 3:
        i1 = random.randrange(len(fields))
        mutated = " ".join(fields[:i1] + fields[i1 + 1:])
        note = f"drop field {i1}"
    else:
        mutated = fen
        note = "identity"
    out.append(f"{i}|{kind}|{note}|{mutated}")
with open("/tmp/fuzz55.fens", "w") as f:
    for row in out:
        f.write(row + "\n")
print(f"wrote /tmp/fuzz55.fens with {len(out)} mutated FENs")
