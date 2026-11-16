#!/usr/bin/env python3
"""fenmoves.py EXE OUTDIR

What does Forge do with `position fen <FEN> moves <moves>`?

`apply_position` (src/uci.cpp:27-68) reads at most SIX tokens after `fen`, then scans forward
for the literal token `moves`. So `position fen F moves e1e8` should apply F and then e1e8.
This script measures whether it does, using positions whose perft 1 differs from startpos (20)
and one where the move is a mate.

Cases, each a FRESH process, read to terminator (19-F12), with the FEN-acceptance and
`nodes`-presence assertions:
  1  `position fen F` then go perft 1                        (reference for F's own count)
  2  `position fen F moves <legal move>` then go perft 1     (does the move apply?)
  3  `position startpos moves <legal move>` then go perft 1  (the control form)
  4  `position fen F moves <mate>` then go depth 3           (is the mate seen?)
  5  `position startpos moves <the same 8-move repetition cycle>` then go depth 3
     (the repetition door, in the form that DOES build a history)
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

W_FEN = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
W_START_MOVES = ""  # the FEN already is the start of the cycle


def perft1py(fen):
    return chess.Board(fen).legal_moves.count()


def run(exe, outdir, tag, pos, search, token="nodes"):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"))
    ans = e.position(pos)
    refused = any("invalid FEN" in l for l in ans)
    try:
        lines = e.go(search, token=token, timeout=180)
    except Timeout:
        lines = []
    e.close()
    if token == "nodes":
        vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
        if not vals:
            raise AssertionError("%s: no nodes line" % tag)
        n = vals[0]
    else:
        n = "-"
    return refused, n, bestmove_of(lines), last_info(lines), lines


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | position command | search | refused | result | bestmove | info |",
            "|---|---|---|---|---|---|---|"]

    # 1 / 2 / 3: does `fen ... moves ...` apply the move?
    ref_refused, ref_n, _, _, _ = run(exe, outdir, "1_fen_only",
                                      "position fen " + W_FEN, "go perft 1")
    # e1d1 is legal in W_FEN; after it, Black has 7 legal moves (from 7? measure with python)
    b0 = chess.Board(W_FEN)
    b1 = b0.copy()
    b1.push_uci("e1d1")
    moved_n_py = b1.legal_moves.count()
    r2, n2, _, _, _ = run(exe, outdir, "2_fen_then_moves",
                          "position fen %s moves e1d1" % W_FEN, "go perft 1")
    r3, n3, _, _, _ = run(exe, outdir, "3_startpos_then_moves",
                          "position startpos moves e2e4", "go perft 1")
    rows.append("| 1 | `position fen F` (reference) | go perft 1 | %s | %d (python: %d) | – | – |"
                % (ref_refused, ref_n, perft1py(W_FEN)))
    rows.append("| 2 | `position fen F moves e1d1` | go perft 1 | %s | %d (python after e1d1: %d) | – | – |"
                % (r2, n2, moved_n_py))
    rows.append("| 3 | `position startpos moves e2e4` (control) | go perft 1 | %s | %d (startpos: 20) | – | – |"
                % (r3, n3))

    # 4: is the mate found through the fen+moves form?
    r4, _, bm4, info4, _ = run(exe, outdir, "4_fen_then_mate_move",
                               "position fen %s moves e1e8" % W_FEN, "go depth 3", token="bestmove")
    r5, _, bm5, info5, _ = run(exe, outdir, "5_startpos_repetition",
                               "position startpos moves e1d1 g8h8 d1e1 h8g8 e1d1 g8h8 d1e1 h8g8",
                               "go depth 3", token="bestmove")
    rows.append("| 4 | `position fen F moves e1e8` (a mate) | go depth 3 | %s | – | %s | %s |"
                % (r4, bm4, info4[-60:]))
    rows.append("| 5 | `position startpos moves <8-move cycle>` | go depth 3 | %s | – | %s | %s |"
                % (r5, bm5, info5[-60:]))

    # the python truth for case 4's board
    b2 = chess.Board(W_FEN)
    b2.push_uci("e1e8")
    mate_truth = b2.is_checkmate()
    text = "\n".join(rows) + ("\n\npython-chess: after e1e8 in F the board is checkmate: %s\n"
                              "python-chess: F has %d legal moves; after e1d1, %d\n"
                              % (mate_truth, perft1py(W_FEN), moved_n_py))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()