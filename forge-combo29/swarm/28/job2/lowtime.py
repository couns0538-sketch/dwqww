#!/usr/bin/env python3
"""lowtime.py EXE OUTDIR — AREA 8 job 2: very little time.

Configurations: wtime 100 / 30 / 10 / 1 / 0, each with winc 0 and winc 10 (10 configs).
Positions: the first 20 of O and the first 20 of G (40 searches per config) — small on purpose: forty
searches per config still gives 400 samples and keeps the whole job inside one command.

For every search: wall time `go` -> `bestmove` on a monotonic clock, the engine's own reported time,
the bestmove, and whether that bestmove is LEGAL by python-chess. A loss on time is defined here as
wall time > the wtime sent (the clock a GUI would deduct), and the engine's own time > wtime.

Writes OUTDIR/<config>.tsv and OUTDIR/<config>.meta.
"""
import hashlib
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
# (wtime, winc) pairs; wtime 0 is the "flag fell" case.
CONFIGS = [(w, i) for w in (100, 30, 10, 1, 0) for i in (0, 10)]


def legal_any(fen, bestmove):
    """True if bestmove is legal in fen (python-chess), or if fen cannot be parsed by python-chess."""
    try:
        board = chess.Board(fen)
    except ValueError:
        return "unparsed"
    if not bestmove or bestmove == "0000":
        return board.is_game_over()
    try:
        move = chess.Move.from_uci(bestmove)
    except ValueError:
        return False
    return move in board.legal_moves


def run_config(exe, fens, outdir, wtime, winc):
    name = f"w{wtime}_i{winc}"
    eng = Engine(exe)
    eng.send("uci")
    lines, _ = eng.read_until("uciok", 20)
    idname = next((l for l in lines if l.startswith("id name")), "id name MISSING")
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()):
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        _l, ok = eng.read_until("readyok", 20)
        if not ok:
            print(f"STOP no readyok for {opt}", file=sys.stderr)
            return False
    go = f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}"
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        import time
        t0 = time.monotonic()
        eng.send(go)
        out, ok = eng.read_until("bestmove", 30)
        t1 = time.monotonic()
        best, etime = "", ""
        for line in out:
            if line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else ""
            if line.startswith("info") and " time " in line:
                f = line.split()
                etime = f[f.index("time") + 1]
        rows.append((fen, f"{(t1 - t0) * 1000:.3f}", etime, best, "ok" if ok else "NORESP",
                     legal_any(fen, best)))
    eng.close()
    with open(os.path.join(outdir, name + ".tsv"), "w") as fh:
        fh.write("fen\twall_ms\tengine_time_ms\tbestmove\tstatus\tbestmove_legal\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    with open(os.path.join(outdir, name + ".meta"), "w") as fh:
        fh.write(f"exe_started {os.path.abspath(exe)}\n")
        fh.write(f"exe_sha256 {hashlib.sha256(open(exe, 'rb').read()).hexdigest()}\n")
        fh.write(idname + "\n")
        fh.write(f"go_line {go}\noption Threads 1\noption Hash 16\n")
        fh.write("".join(f"option {k} {v}\n" for k, v in S14.items()))
        fh.write(f"positions {len(rows)}\n")
    print(f"{name}: {len(rows)} searches")
    return True


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], 40)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    for wtime, winc in CONFIGS:
        if not run_config(exe, fens, outdir, wtime, winc):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
