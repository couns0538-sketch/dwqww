#!/usr/bin/env python3
"""Check every mate score in the job-3 G output: does the reported PV actually deliver mate?

For each record whose last `info ... pv` line carries `score mate N` with N > 0, play the PV on the
position with python-chess and require: every move legal, and the final position is checkmate, after
the right number of plies (2N-1). For N < 0 require the same for the opponent's forced mate
(2|N| plies); if the PV is shorter than that, report it as NOT CHECKED rather than as a failure.
For every `score cp` record, report whether the cp is at or above the engine's mate threshold
(MateInMaxPly = 32000 - 128 = 31872), which would mean a mate score leaked into a cp field.

usage: check_mate_pv.py OUTFILE.jsonl
"""
import json
import sys

import chess

MATE_IN_MAX_PLY = 32000 - 128


def main(path):
    total = 0
    mate_pos = 0
    ok = 0
    illegal = []
    not_mate = []
    too_short = []
    cp_over = []
    for raw in open(path):
        r = json.loads(raw)
        total += 1
        for side in ("self", "mirror"):
            pvline = r[side]["last_pv"]
            if not pvline or " mate " not in pvline:
                t = pvline.split()
                if "cp" in t:
                    cp = int(t[t.index("score") + 2])
                    if abs(cp) >= MATE_IN_MAX_PLY:
                        cp_over.append((r["index"], side, cp))
                continue
            t = pvline.split()
            n = int(t[t.index("score") + 2])
            pv = t[t.index("pv") + 1:]
            mate_pos += 1
            board = chess.Board(r["fen"] if side == "self" else r["mfen"])
            expected_plies = 2 * n - 1 if n > 0 else 2 * (-n)
            played = 0
            broke = False
            for uci in pv:
                try:
                    move = chess.Move.from_uci(uci)
                except Exception:
                    illegal.append((r["index"], side, "bad uci", uci))
                    broke = True
                    break
                if move not in board.legal_moves:
                    illegal.append((r["index"], side, "illegal", uci, board.fen()))
                    broke = True
                    break
                board.push(move)
                played += 1
            if broke:
                continue
            if played < expected_plies:
                too_short.append((r["index"], side, n, played, expected_plies))
                continue
            if board.is_checkmate():
                ok += 1
            else:
                not_mate.append((r["index"], side, n, played, board.fen(), board.is_check(), board.is_game_over()))

    print("records: %d" % total)
    print("mate scores found: %d" % mate_pos)
    print("  PV delivers checkmate at the expected ply: %d" % ok)
    print("  PV has an ILLEGAL move:                    %d" % len(illegal))
    print("  PV legal but final position is NOT mate:   %d" % len(not_mate))
    print("  PV shorter than 2N-1 plies (not checked):  %d" % len(too_short))
    print("cp scores at or above the mate threshold (should be 0): %d" % len(cp_over))
    for name, rows in (("ILLEGAL", illegal), ("NOT-MATE", not_mate),
                       ("TOO-SHORT", too_short), ("CP-OVER", cp_over)):
        if rows:
            print("")
            print(name + ":")
            for row in rows[:20]:
                print("  " + "\t".join(str(x) for x in row))


if __name__ == "__main__":
    main(sys.argv[1])
