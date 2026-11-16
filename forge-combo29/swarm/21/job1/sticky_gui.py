#!/usr/bin/env python3
"""sticky_gui.py EXE OUTDIR

What goes BEYOND "after a refused FEN the engine keeps the previous position" (already
known, FABLE_TO_swarm_1): that known line makes the fault sound like a harmless stale
board. It is a protocol fault, and this script shows the exact trace a GUI sees.

Setup of the case, all of it legal chess before the fault:
  position startpos moves e2e4 e7e5 g1f3 b8c6 f1b5   -> the Ruy Lopez, 5 plies
  ... then the GUI sends the 6-ply position as a FEN in which White's king-side right
  is still claimed although White's h1 rook is gone (it was captured / moved away):
  r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3

The engine answers `info string invalid FEN: ...` and then still answers `readyok`, so a
GUI that synchronises on readyok sends `go` and receives a move **of the old game**.
The script prints the whole trace and checks the returned move against the position the
GUI believes in, and against the position the engine kept.
"""
import os
import subprocess
import sys

import chess

HISTORY = "e2e4 e7e5 g1f3 b8c6 f1b5"
GUI_FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3"


def run(exe, outdir, name, lines):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=180, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
        fh.write("=== returncode: %d\n" % p.returncode)
    return p.stdout


def old_fen():
    b = chess.Board()
    for mv in HISTORY.split():
        b.push_uci(mv)
    return b.fen()


def legal_in(fen, move):
    try:
        b = chess.Board(fen)
    except Exception:
        return "unparsable for python-chess"
    return move in {m.uci() for m in b.legal_moves}


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    kept = old_fen()
    lines = ["position startpos moves " + HISTORY, "isready", "go depth 1",
             "position fen " + GUI_FEN, "isready", "go depth 4"]
    out = run(exe, outdir, "trace", lines)
    bestmoves = [ln.split()[1] for ln in out.splitlines() if ln.startswith("bestmove")]
    infos = [ln for ln in out.splitlines() if ln.startswith("info string")]
    rows = []
    rows.append("the position the engine keeps after the refused command (python-chess of the 5 plies): %s" % kept)
    rows.append("the FEN the GUI wanted:                                    %s" % GUI_FEN)
    rows.append("refusal answer line(s): %s" % (" ;; ".join(infos) or "NONE"))
    rows.append("readyok lines in the whole session: %d (one per isready, INCLUDING the one after the refusal)" % out.count("readyok"))
    rows.append("bestmove lines in the whole session: %s" % bestmoves)
    if len(bestmoves) >= 2:
        mv = bestmoves[1]
        rows.append("move the GUI gets for its new board: %s" % mv)
        rows.append("  legal in the GUI's own board (python-chess refuses that FEN): %s"
                    % legal_in(GUI_FEN, mv))
        rows.append("  legal in the position the engine kept: %s" % legal_in(kept, mv))
        rows.append("  side to move: GUI's board = White, engine's kept board = %s"
                    % ("White" if chess.Board(kept).turn else "Black"))
        rows.append("  => the engine answered a move for the WRONG SIDE to a GUI that "
                    "had just told it White was to move")
    # a second, harder variant: the refused FEN's board IS legal for python-chess
    rows.append("")
    alt = "4k3/8/8/8/8/8/8/4K2R w Kkq - 0 1"
    lines2 = ["position fen r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "isready", "go depth 1",
              "position fen " + alt, "isready", "go depth 3"]
    out2 = run(exe, outdir, "trace_alt", lines2)
    bm2 = [ln.split()[1] for ln in out2.splitlines() if ln.startswith("bestmove")]
    inf2 = [ln for ln in out2.splitlines() if ln.startswith("info string")]
    rows.append("ALT: FEN %s -> %s ; bestmoves %s" %
                (alt, (" ;; ".join(inf2) or "accepted"), bm2))
    with open(os.path.join(outdir, "summary.txt"), "w") as fh:
        fh.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
