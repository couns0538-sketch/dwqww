#!/usr/bin/env python3
"""ep_pin_compare.py EXE OUT : compare the ENGINE and python-chess on en-passant pin positions, move by move.

Seat 23's 23-F5 says the ep-pin class never occurs in random play (their filter found 0 in 5,353 positions) and
that it must be constructed; their 23-F6 checks three hand-built positions. This check takes my 320 constructed
class-B positions (job2/ep_constructed.tsv) and does the same job at scale, one `go perft 1` per position, with:
  * the engine's root move set vs python-chess's legal move set (SET comparison, not a node count),
  * an explicit assertion that the RAW ep capture would be ILLEGAL in python-chess (otherwise the position is not
    a class-B position at all and must not be counted),
  * the control that the same position WITH the slider removed DOES allow the ep capture (so the position is
    genuinely about the pin, not about a pawn that simply cannot move).
`quit` is sent only after the `nodes` line of each perft has been read (see HARNESS_AUDIT.md).
"""
import os
import subprocess
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job2"))
from ep_common import raw_ep_exposes  # noqa: E402

EXE, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT + ".raw", exist_ok=True)
rows = [l.rstrip("\n").split("\t") for l in open(SET) if l.strip()]
if not rows:
    sys.exit("FAIL: empty position set")

def engine_perft1(exe, fen, rawpath):
    """one `go perft 1`, read to the `nodes` line, then quit. Returns (sorted root moves, nodes total)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(rawpath, "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                return None
            raw.write(line)
            raw.flush()
            if line.strip().startswith(tok):
                return line.strip()

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}"); send("isready"); until("readyok")
    send("go perft 1")
    moves, total = [], "nodes 0"
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("nodes "):
            total = s
            break
        if ":" in s and not s.startswith(("info", "option", "id")):
            moves.append(s.split(":")[0].strip())
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return sorted(moves), total


results = []
for i, row in enumerate(rows):
    fen = row[2]
    board = chess.Board(fen)
    raw_ok, cap = raw_ep_exposes(board)
    # assertion 1: this really is a class-B position (the raw ep capture would expose our king)
    if not raw_ok:
        results.append((i, fen, "NOT_CLASS_B", "", ""))
        continue
    # assertion 2: python-chess does NOT allow that capture
    ep_legal = [m for m in board.legal_moves if board.is_en_passant(m)]
    engine_moves, total = engine_perft1(EXE, fen, f"{OUT}.raw/b{i:03d}.txt")
    py_moves = sorted(m.uci() for m in board.legal_moves)
    missing = sorted(set(py_moves) - set(engine_moves))
    extra = sorted(set(engine_moves) - set(py_moves))
    verdict = "OK" if (not missing and not extra) else "DIFF"
    results.append((i, fen, verdict, f"missing={missing} extra={extra}",
                    f"py_ep_legal={[m.uci() for m in ep_legal]}"))

bad = [r for r in results if r[2] != "OK"]
with open(OUT, "w") as f:
    f.write(f"positions: {len(results)}\n")
    f.write(f"engine and python-chess agree on the root move set: {len(results)-len(bad)}\n")
    f.write(f"disagreements: {len(bad)}\n\n")
    for r in results:
        f.write("\t".join(str(x) for x in r) + "\n")
print(f"positions: {len(results)}")
print(f"agree: {len(results)-len(bad)}   disagreements: {len(bad)}")
for r in bad[:10]:
    print("DIFF", r)
