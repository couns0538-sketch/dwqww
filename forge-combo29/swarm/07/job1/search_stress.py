#!/usr/bin/env python3
"""search_stress.py EXE FENS OUTDIR DEPTH [TIMEOUT_S]

For every FEN: fresh `position fen`, `isready` to readyok, `go depth D`, then read
stdout until `bestmove` before the next command. Nothing is ever pipelined and
stdin is never closed mid-search. Each bestmove is checked with python-chess; a
bestmove that is illegal, or `0000` on a position that has legal moves, is recorded.

Writes OUTDIR/<index>.json and OUTDIR/all.json.
"""
import json
import os
import re
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from uci_drive import LineReader  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402


def main():
    exe, fens_path, outdir, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    timeout_s = float(sys.argv[5]) if len(sys.argv) > 5 else 120.0
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path, encoding="utf-8") if l.strip()]
    rows = []
    errpath = os.path.join(outdir, "stderr_all.txt")
    errfh = open(errpath, "w", encoding="utf-8")
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=errfh, text=True, bufsize=1)
    reader = LineReader(proc.stdout)

    def send(cmd):
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def drain(tag, timeout=120):
        deadline = time.monotonic() + timeout
        while True:
            line = reader.readline(deadline)
            if line is None:
                raise RuntimeError(f"no readyok after {tag}")
            if line.strip() == "readyok":
                return

    send("uci")
    deadline = time.monotonic() + 60
    while True:
        line = reader.readline(deadline)
        if line is None or line.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1",
                "LmrQuietBase value 93", "LmrQuietDivisor value 205",
                "LmrNoisyBase value 13", "LmrNoisyDivisor value 333",
                "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
                "LmpBase value 8", "HistoryPruneMultiplier value 2220",
                "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
                "HistoryBonusMax value 2212", "SingularDepth value 6",
                "IirDepth value 2", "NonPawnCorrection value true"]:
        send("setoption name " + opt)
        send("isready")
        drain("setoption " + opt)
    send("ucinewgame")
    send("isready")
    drain("ucinewgame")

    for index, fen in enumerate(fens):
        rec = {"index": index, "fen": fen, "depth": depth}
        try:
            board = chess.Board(fen)
            rec["pythonchess_ok"] = True
        except ValueError as exc:
            board = None
            rec["pythonchess_ok"] = False
            rec["pythonchess_error"] = str(exc)
        send("position fen " + fen)
        send("isready")
        drain("position " + fen)
        send(f"go depth {depth}")
        best = None
        nodes = None
        last_info = None
        deadline = time.monotonic() + timeout_s
        while True:
            line = reader.readline(deadline)
            if line is None:
                rec["hang"] = True
                break
            if line.startswith("info ") and " nodes " in line:
                m = re.search(r" nodes (\d+)", line)
                if m:
                    nodes = int(m.group(1))
                last_info = line.strip()
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
        rec["best"] = best
        rec["nodes"] = nodes
        rec["last_info"] = last_info
        rec["illegal_answer"] = False
        if board is not None and best and best != "0000":
            try:
                move = chess.Move.from_uci(best)
                rec["illegal_answer"] = move not in board.legal_moves
            except ValueError:
                rec["illegal_answer"] = True
        elif board is not None and best == "0000":
            rec["illegal_answer"] = board.legal_moves.count() > 0
        rows.append(rec)
        if index % 25 == 0:
            print(f"{index}/{len(fens)} {fen} -> {best} nodes={nodes}", flush=True)
        json.dump(rec, open(os.path.join(outdir, f"{index:04d}.json"), "w"), indent=1)
    send("quit")
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    errfh.close()
    json.dump(rows, open(os.path.join(outdir, "all.json"), "w"), indent=1)
    hangs = sum(1 for r in rows if r.get("hang"))
    bad = sum(1 for r in rows if r.get("illegal_answer"))
    zero = sum(1 for r in rows if r.get("nodes") == 0)
    print(f"SUMMARY cases={len(rows)} hangs={hangs} illegal_answers={bad} zero_nodes={zero}", flush=True)


if __name__ == "__main__":
    main()
