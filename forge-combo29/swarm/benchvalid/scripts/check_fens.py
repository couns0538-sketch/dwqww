#!/usr/bin/env python3
"""Independently validate the eight bench FENs with python-chess.

The brief's rule 4: a refused FEN manufactures a pass. The engine silently `continue`s
past a FEN it will not load (`uci.cpp`, the `bench` branch: `if (!bench_board.set_fen(fen))
continue;`), so a bench whose list were half-refused would print a smaller number and
call it a pin.

Three independent checks:
  1. python-chess parses and validates each FEN;
  2. the engine's own benchprobe prints `REFUSED` and exits non-zero on any of them;
  3. the total the probe reports equals the pin.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import chess

FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]

SRC = pathlib.Path("/home/ubuntu/work/base/forge-combo29/src/uci.cpp")
PROBE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/work/bin/probe_base"

fails = []

# 1. the list in this script must be the list in the engine
engine_text = SRC.read_text()
start = engine_text.index("std::array<std::string_view, 8> fens{")
end = engine_text.index("};", start)
block = engine_text[start:end]
for i, f in enumerate(FENS):
    if f not in block and not (i == 0 and "StandardStartFen" in block):
        fails.append(f"FEN {i} is not in uci.cpp: {f}")
if "StandardStartFen" in block and FENS[0] != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
    fails.append("slot 0 is StandardStartFen in the source but not in this list")

# 2. python-chess validates each
rows = []
for i, f in enumerate(FENS):
    b = chess.Board(f)
    rows.append({"idx": i, "fen": f, "valid": b.is_valid(), "check": b.is_check(),
                 "halfmove": b.halfmove_clock, "legal": b.legal_moves.count(),
                 "turn": "w" if b.turn else "b"})
    if not b.is_valid():
        fails.append(f"python-chess rejects FEN {i}")

# 3. the engine refuses none, and its total still equals the pin
p = subprocess.run([PROBE, "13"], capture_output=True, text=True, timeout=600)
if "REFUSED" in p.stdout:
    fails.append("the engine refused at least one bench FEN")
total = None
for line in p.stdout.splitlines():
    if line.startswith("TOTAL\t"):
        total = int(line.split("\t")[1])
if total != 862329:
    fails.append(f"probe total {total} != pin 862329")

print(f"{'idx':>3} {'turn':>4} {'legal':>5} {'hm':>3} {'valid':>5}  fen")
for r in rows:
    print(f"{r['idx']:>3} {r['turn']:>4} {r['legal']:>5} {r['halfmove']:>3} {r['valid']!s:>5}  {r['fen']}")
print(f"\nprobe total at depth 13: {total}   pin: 862329")
print("white to move:", sum(1 for r in rows if r["turn"] == "w"), "of", len(rows))
print("halfmove clock 0:", sum(1 for r in rows if r["halfmove"] == 0), "of", len(rows))

if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("PASS  all 8 FENs valid in python-chess, none refused by the engine, total matches the pin")
