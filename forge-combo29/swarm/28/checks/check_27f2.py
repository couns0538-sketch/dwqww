#!/usr/bin/env python3
"""check_27f2.py — seat 28's INDEPENDENT check of seat 27's S-F2.

Claim restated from its sentence alone (no file of seat 27 is read by this script):
  "`go nodes N` below one root iteration (N < 26 at startpos) answers the first legal move in
   generation order (a2a3) with no info line at all; N = 26 answers d2d4."

Critical control, from seat 20's S-F12: with the default `OwnBook true` startpos is answered by the
opening book (`info string book move`, no `info depth` line), which looks exactly like an unsearched
reply. Every measured case here sets `OwnBook false`, and one separate case measures the book behaviour
explicitly.

For every (nodes, OwnBook) case: fresh process, setoption, ucinewgame+isready, position, isready,
`go nodes N`, read to bestmove, and record: the bestmove, whether ANY `info depth` line appeared,
whether a book line appeared, and the move's legality by python-chess.

Usage: check_27f2.py EXE OUT.tsv
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# A position outside the book, from seat 28's own job-1 set.
NONBOOK = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"


def first_legal(fen):
    board = chess.Board(fen)
    return next(iter(board.legal_moves)).uci()


def generate_order_guess(fen):
    """python-chess's move list order, for the P5 comparison (NOT the engine's order)."""
    board = chess.Board(fen)
    return [m.uci() for m in board.legal_moves][:5]


def probe(exe, fen, nodes, ownbook):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    eng.send(f"setoption name OwnBook value {'true' if ownbook else 'false'}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"go nodes {nodes}")
    out, ok = eng.read_until("bestmove", 30)
    eng.close()
    best = ""
    info_depth = 0
    book = 0
    for line in out:
        if line.startswith("bestmove"):
            parts = line.split()
            best = parts[1] if len(parts) > 1 else ""
        if line.startswith("info depth"):
            info_depth += 1
        if "book move" in line:
            book += 1
    legal = "n/a"
    if best and best != "0000":
        try:
            legal = str(chess.Move.from_uci(best) in chess.Board(fen).legal_moves)
        except ValueError:
            legal = "unparsable"
    return {"bestmove": best, "info_depth": info_depth, "book": book, "legal": legal,
            "answered": ok}


def main() -> int:
    exe, out = sys.argv[1], sys.argv[2]
    print("python-chess legal-move order from startpos (first five):", generate_order_guess(STARTPOS))
    print("python-chess first legal move at startpos:", first_legal(STARTPOS))
    print("python-chess first legal move at NONBOOK :", first_legal(NONBOOK))
    print()

    cases = [(1, False), (5, False), (25, False), (26, False), (27, False), (200, False)]
    rows = []
    print("| position | nodes | OwnBook | bestmove | info depth lines | book lines | answered | legal |")
    print("|---|---|---|---|---|---|---|---|")
    for nodes, ob in cases:
        r = probe(exe, STARTPOS, nodes, ob)
        print(f"| startpos | {nodes} | false | {r['bestmove'] or '-'} | {r['info_depth']} | {r['book']} | "
              f"{r['answered']} | {r['legal']} |")
        rows.append(("startpos", nodes, False, r))
    for nodes in (1, 25, 26, 200):
        r = probe(exe, NONBOOK, nodes, False)
        print(f"| NONBOOK | {nodes} | false | {r['bestmove'] or '-'} | {r['info_depth']} | {r['book']} | "
              f"{r['answered']} | {r['legal']} |")
        rows.append(("NONBOOK", nodes, False, r))
    r = probe(exe, STARTPOS, 1, True)
    print(f"| startpos | 1 | TRUE (book control) | {r['bestmove'] or '-'} | {r['info_depth']} | {r['book']} | "
          f"{r['answered']} | {r['legal']} |")
    rows.append(("startpos", 1, True, r))

    with open(out, "w") as fh:
        fh.write("position\tnodes\townbook\tbestmove\tinfo_depth\tbook\tanswered\tlegal\n")
        for pos, nodes, ob, r in rows:
            fh.write(f"{pos}\t{nodes}\t{str(ob).lower()}\t{r['bestmove']}\t{r['info_depth']}\t{r['book']}\t"
                     f"{r['answered']}\t{r['legal']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
