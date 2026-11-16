#!/usr/bin/env python3
"""seat 24: how far does the terminal-root defect reach on the PC r15 build under PC20, Threads 1?

Established so far (24-F7): `go infinite` at a terminal root never volunteers a bestmove on the PC build; `stop`
produces `bestmove 0000` in ~0.2 s.  This harness maps the REST of the command space at a terminal root, because a
GUI does not always use `go infinite`:

  go depth 5            bounded depth
  go nodes 1000         bounded nodes
  go movetime 200       bounded time
  go wtime 1000 btime 1000
  go mate 3
  go infinite           (control: expected to hang)
  go ponder             (the other unbounded form)
  go searchmoves e2e4 depth 3   (restricted; on a mate root there is no legal move to name)

For each: does a bestmove arrive, how fast, and is it 0000 (correct for a terminal root)?
Every case asserts that its bestmove line was actually found; a missing line is reported MISSING, never a pass.
Threads 1, Hash 16, PC20, OwnBook false.  No score is read or compared.
"""
import argparse
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

import chess

MATE = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def one(exe, fen, cmd, wait, stop_ms):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, env=env)
    q = queue.Queue()

    def rd():
        for l in p.stdout:
            q.put(l.decode("utf-8", "replace").rstrip())
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(s):
        p.stdin.write((s + "\n").encode()); p.stdin.flush()

    def until(pred, to):
        out = []; t = time.monotonic()
        while time.monotonic() - t < to:
            try:
                l = q.get(timeout=max(0.01, to - (time.monotonic() - t)))
            except queue.Empty:
                return out, False
            if l is None:
                return out, False
            out.append(l)
            if pred(l):
                return out, True
        return out, False

    send("uci"); until(lambda l: l == "uciok", 60)
    for k, v in S14 + PC20 + [("Threads", 1), ("Hash", 16)]:
        send(f"setoption name {k} value {v}"); send("isready"); until(lambda l: l == "readyok", 60)
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + fen); send("isready"); until(lambda l: l == "readyok", 60)
    t0 = time.monotonic()
    send(cmd)
    if stop_ms is not None:
        time.sleep(stop_ms / 1000.0)
        send("stop")
    lines, ok = until(lambda l: l.startswith("bestmove"), wait)
    dt = time.monotonic() - t0
    bm = lines[-1].split()[1] if (lines and lines[-1].startswith("bestmove")) else None
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    return bm, dt, ok


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

bx, bs = chess.Board(MATE), chess.Board(STALEMATE)
CASES = [
    ("mate", "go depth 5", 30, None),
    ("mate", "go nodes 1000", 30, None),
    ("mate", "go movetime 200", 30, None),
    ("mate", "go wtime 1000 btime 1000", 30, None),
    ("mate", "go mate 3", 30, None),
    ("mate", "go searchmoves e2e4 depth 3", 30, None),
    ("mate", "go infinite", 30, None),
    ("mate", "go infinite", 10, 200),
    ("mate", "go ponder", 10, 200),
    ("stalemate", "go depth 5", 30, None),
    ("stalemate", "go nodes 1000", 30, None),
    ("stalemate", "go movetime 200", 30, None),
    ("stalemate", "go infinite", 30, None),
]

with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()
    w(f"exe {os.path.abspath(a.exe)}")
    w(f"sha256 {hashlib.sha256(open(a.exe,'rb').read()).hexdigest()}")
    w(f"regime PC20, Threads 1, Hash 16, OwnBook false")
    w(f"mate fen: python-chess checkmate={bx.is_checkmate()} legal={bx.legal_moves.count()}")
    w(f"stalemate fen: python-chess stalemate={bs.is_stalemate()} legal={bs.legal_moves.count()}")
    w("")
    w("| board | command | stop after | bestmove | wall s | found |")
    w("|---|---|---|---|---|---|")
    hangs = []
    for board, cmd, wait, stop in CASES:
        fen = MATE if board == "mate" else STALEMATE
        bm, dt, ok = one(a.exe, fen, cmd, wait, stop)
        if not ok:
            hangs.append((board, cmd, stop))
        w(f"| {board} | `{cmd}` | {stop if stop else '-'} ms | {bm or 'MISSING'} | {dt:.2f} | {'yes' if ok else 'NO'} |")
    w("")
    w("MISSING bestmove (no answer in the window):")
    if not hangs:
        w("  none")
    for board, cmd, stop in hangs:
        w(f"  {board}: `{cmd}` stop={stop}")
