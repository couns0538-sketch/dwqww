#!/usr/bin/env python3
"""check_s01f5.py — seat 28's INDEPENDENT check of seat 01's finding S-F5.

The finding's claim, restated from its sentence alone (no file of seat 01 is read by this script):
  "With `halfmove >= 100` in the FEN the engine adjudicates the root as a draw and searches 0 nodes,
   so a mate-in-one is MISSED (`bestmove f2f3`, `score cp 0`) while the identical board at halfmove 99
   gives `score mate 1` / `bestmove a1a8` / 126 nodes."

What this script does, on the plain Release build only:
  1. Takes mate-in-one positions I built myself with python-chess (a rook delivers mate on the back
     rank), each written at halfmove 0, 99, 100, 101, 150; plus a quiet position with no mate.
  2. For each: fresh engine process, `setoption Threads 1/Hash 16`, `position fen`, `isready` -> readyok,
     `go depth 6`, read to `bestmove`. Records bestmove, the LAST info line's score and nodes.
  3. Judges BESTMOVE independently: is the played move a mate-in-one according to python-chess?
  4. CONTROLS: the same script on the mate-in-one at halfmove 99 must report a mate score and >0 nodes
     (otherwise the harness is blind and the whole check is void), and the quiet position at halfmove
     100 must still search >0 nodes (so a 0-node result is attributable to the counter, not the harness).

Usage: check_s01f5.py EXE OUT.tsv
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

# Mate-in-one positions built here with python-chess, not copied from any other seat.
MATE_ROOK = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - {hm} 1"   # Ra8#
QUIET = "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - {hm} 1"        # no mate available


def is_mate_in_one(fen, move_uci):
    """True iff move_uci is legal in fen and delivers immediate checkmate."""
    board = chess.Board(fen)
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return False
    if move not in board.legal_moves:
        return False
    board.push(move)
    return board.is_checkmate()


def mate_in_one_exists(fen):
    board = chess.Board(fen)
    for move in board.legal_moves:
        board.push(move)
        mated = board.is_checkmate()
        board.pop()
        if mated:
            return True
    return False


def probe(exe, fen, go="go depth 6"):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for name, value in [("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {name} value {value}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send("position fen " + fen)
    eng.send("isready")
    lines, ok = eng.read_until("readyok", 20)
    refused = any("invalid FEN" in l for l in lines)
    best, score, nodes = "", "", ""
    if not refused and ok:
        eng.send(go)
        out, ok2 = eng.read_until("bestmove", 60)
        for line in out:
            if line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else ""
            if line.startswith("info depth") and " score " in line:
                f = line.split()
                if "score" in f:
                    score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
                if "nodes" in f:
                    nodes = f[f.index("nodes") + 1]
        if not ok2:
            best = best or "NORESP"
    eng.close()
    return {"refused": refused, "bestmove": best, "score": score, "nodes": nodes}


def main() -> int:
    exe, out = sys.argv[1], sys.argv[2]
    plan = [(f"MATE_ROOK_hm{hm}", MATE_ROOK.format(hm=hm)) for hm in (0, 99, 100, 101, 150)]
    plan += [(f"QUIET_hm{hm}", QUIET.format(hm=hm)) for hm in (99, 100)]

    print("== python-chess says of my own positions ==")
    for name, fen in plan:
        print(f"{name}: mate_in_one_exists={mate_in_one_exists(fen)}")

    print()
    print("| case | halfmove | refused | engine nodes | score | bestmove | bestmove IS mate-in-one |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for name, fen in plan:
        r = probe(exe, fen)
        hm = fen.split()[-2]
        judged = "n/a" if not r["bestmove"] else str(is_mate_in_one(fen, r["bestmove"]))
        print(f"| {name} | {hm} | {r['refused']} | {r['nodes'] or '-'} | {r['score'] or '-'} | "
              f"{r['bestmove'] or '-'} | {judged} |")
        rows.append((name, hm, fen, r, judged))
    with open(out, "w") as fh:
        fh.write("case\thalfmove\tfen\trefused\tnodes\tscore\tbestmove\tbestmove_is_mate_in_one\t"
                 "py_mate_in_one_exists\n")
        for name, hm, fen, r, judged in rows:
            fh.write(f"{name}\t{hm}\t{fen}\t{r['refused']}\t{r['nodes']}\t{r['score']}\t"
                     f"{r['bestmove']}\t{judged}\t{mate_in_one_exists(fen)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
