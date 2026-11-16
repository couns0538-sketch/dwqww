#!/usr/bin/env python3
"""check.py EXE CASEFILE OUTFILE — does the engine refuse an unreachable en-passant square?

Written for seat 12's check of seat 06's finding S-F2 (an ep square no pawn move could have
created is refused with `info string invalid FEN: inconsistent en-passant square`).
Only the finding's one command line is reused; this harness, the case list and the
comparison against python-chess are mine.

For each case: fresh process, `position fen <FEN>` + `isready` (read every line up to readyok),
then `go depth 2` and wait for bestmove. Recorded: the answer lines, whether the engine
refused the FEN (`invalid FEN` line), whether python-chess parses the FEN at all, and
whether the engine's bestmove is legal according to python-chess when both parsed.
"""
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess


def run_fen(exe, fen, timeout_s=20.0):
    script = f"position fen {fen}\nisready\ngo depth 2\nquit\n"
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={"PATH": "/usr/bin:/bin"})
    q = queue.Queue()
    lines = []

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip("\n"))
        q.put(None)
    threading.Thread(target=reader, daemon=True).start()
    p.stdin.write(script)
    p.stdin.flush()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        lines.append(ln)
        if ln.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
    except OSError:
        pass
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


def main():
    exe, casefile, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
    cases = [ln.split("\t", 1) for ln in Path(casefile).read_text().splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    rows = []
    with open(outfile, "w") as out:
        for name, fen in cases:
            lines = run_fen(exe, fen)
            refused = any("invalid FEN" in l for l in lines)
            reason = next((l for l in lines if "invalid FEN" in l), "")
            bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
            try:
                board = chess.Board(fen)
                py_ok = True
            except Exception as exc:
                board, py_ok = None, False
                py_err = str(exc)
            legal = ""
            if py_ok and bm:
                try:
                    legal = str(chess.Move.from_uci(bm) in board.legal_moves)
                except ValueError:
                    legal = "unparseable"
            row = (name, fen, refused, py_ok, bm, legal, reason)
            rows.append(row)
            out.write(f"{name}\t{fen}\trefused={refused}\tpython_chess_ok={py_ok}\t"
                      f"bestmove={bm}\tbm_legal={legal}\t{reason}\n")
            out.write("  lines: " + " | ".join(lines[:8]) + "\n")
            out.flush()
    print(f"{'case':32} {'refused':8} {'py-chess':9} {'bestmove':9} legal")
    for name, fen, refused, py_ok, bm, legal, _ in rows:
        print(f"{name:32} {str(refused):8} {str(py_ok):9} {str(bm):9} {legal}")


if __name__ == "__main__":
    main()
