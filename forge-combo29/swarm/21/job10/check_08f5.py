#!/usr/bin/env python3
"""check_08f5.py EXE FENFILE OUTDIR

CHECK of seat 08's 08-F5 (the reserve-empty clock branch) with my own harness and my own
positions (the first 8 FENs of O).

For each position, in ONE fresh engine process (so the TT is fresh for the depth-1
reference, and the clock queries do not benefit from it):
  ref_depth1 : `go depth 1`
  first_legal: python-chess's first legal move (a fixed order, reported)
  t10, t1, t0: `go wtime 10 btime 10`, `go wtime 1 btime 1`, `go wtime 0 btime 0`
  inc        : `go wtime 10 btime 10 winc 10 binc 10`
Each search is timed from just before writing `go` to just after reading `bestmove`
(monotonic clock), read to bestmove by the safe driver, and its answer is checked for legality.

Asserts: a bestmove was actually read (empty answers cannot pass), and every bestmove is a
legal move per python-chess (n/a counted and listed, never silently dropped).
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402

import chess


def timed_go(e, line, timeout=30):
    t0 = time.monotonic()
    lines = e.go(line, timeout=timeout)
    dt = (time.monotonic() - t0) * 1000.0
    bm = bestmove_of(lines)
    if not bm:
        raise AssertionError("no bestmove read for %r" % line)
    return bm, dt, lines


def main():
    exe, fenfile, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fenfile) if l.strip()][:8]
    rows = ["| # | FEN | depth1 | first legal | wtime10 | wtime1 | wtime0 | wtime10+winc10 | wtime1 == depth1 | wtime1 == first legal |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    agg = dict(eq_depth1=0, eq_first=0, illegal=0, n=0, t10=[], t1=[], t0=[], tinc=[],
               inc_eq_noinc=0)
    for i, fen in enumerate(fens):
        e = SafeEngine(exe, os.path.join(outdir, "pos_%02d_raw.txt" % i))
        ans = e.position("position fen " + fen)
        if any("invalid FEN" in l for l in ans):
            e.close()
            raise AssertionError("FEN %d refused: %s" % (i, fen))
        b_depth, d_depth, _ = timed_go(e, "go depth 1")
        b10, d10, _ = timed_go(e, "go wtime 10 btime 10")
        b1, d1, _ = timed_go(e, "go wtime 1 btime 1")
        b0, d0, _ = timed_go(e, "go wtime 0 btime 0")
        binc, dinc, _ = timed_go(e, "go wtime 10 btime 10 winc 10 binc 10")
        e.close()
        board = chess.Board(fen)
        legal = [m.uci() for m in board.legal_moves]
        first = legal[0] if legal else "-"
        for bm in (b_depth, b10, b1, b0, binc):
            if bm not in legal:
                agg["illegal"] += 1
        agg["n"] += 1
        agg["eq_depth1"] += (b1 == b_depth)
        agg["eq_first"] += (b1 == first)
        agg["inc_eq_noinc"] += (binc == b10)
        agg["t10"].append(d10)
        agg["t1"].append(d1)
        agg["t0"].append(d0)
        agg["tinc"].append(dinc)
        rows.append("| %d | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            i, fen, b_depth, first, b10, b1, b0, binc,
            b1 == b_depth, b1 == first))

    def med(xs):
        s = sorted(xs)
        return s[len(s) // 2]

    n = agg["n"]
    out = rows + ["",
                  "| measure | value |", "|---|---|",
                  "| positions | %d |" % n,
                  "| wtime1 == go depth 1 | %d of %d |" % (agg["eq_depth1"], n),
                  "| wtime1 == first legal move | %d of %d |" % (agg["eq_first"], n),
                  "| wtime10+winc10 == wtime10 | %d of %d |" % (agg["inc_eq_noinc"], n),
                  "| illegal bestmoves | %d |" % agg["illegal"],
                  "| median wall time, wtime10 | %.3f ms |" % med(agg["t10"]),
                  "| median wall time, wtime1 | %.3f ms |" % med(agg["t1"]),
                  "| median wall time, wtime0 | %.3f ms |" % med(agg["t0"]),
                  "| median wall time, wtime10+winc10 | %.3f ms |" % med(agg["tinc"]),
                  "| max wall time, any clock case | %.3f ms |" %
                  max(max(agg["t10"]), max(agg["t1"]), max(agg["t0"]), max(agg["tinc"]))]

    slow = max(max(agg["t10"]), max(agg["t1"]), max(agg["t0"])) >= 2.0
    if slow:
        verdict = "REFUTES 08-F5 (a clock case took 2 ms or more)"
    elif agg["eq_depth1"] >= 6 and agg["eq_first"] <= 2 and agg["illegal"] == 0 \
            and agg["inc_eq_noinc"] >= 7:
        verdict = "CONFIRMS 08-F5"
    else:
        verdict = "REFUTES 08-F5 (a discriminating measure missed its band)"
    out.append("")
    out.append("=> %s" % verdict)
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()