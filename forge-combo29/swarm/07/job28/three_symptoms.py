#!/usr/bin/env python3
"""three_symptoms.py PC_EXE OUTDIR

Runs the three reported symptoms SIDE BY SIDE on the PC r15 build under PC20, Threads 1, Hash 16,
one fresh process per case, and then decides from the CODE whether they share one path.

  1. 07-F1        `go searchmoves` naming nothing legal (board HAS legal moves)
  2. 19-F12       `go depth 12` followed by an immediate `quit` (aborted search)
  3. no-match+NB  `go nodes 100000 searchmoves <illegal>`

For each: record every info line, the bestmove (if any), whether the reported nodes are 0, and
whether the move is legal for the position. A case that never answers is recorded as ABSENT, not as
a pass.

This script does NOT send anything while a `go` is running except in case 2, where the early `quit`
IS the phenomenon under test; that is stated in the output so nobody mistakes it for the harness bug
seat 19 warned about.
"""
import os
import queue
import re
import subprocess
import sys
import threading

import chess

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=120):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def session(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1"] + PC20:
        send("setoption name " + opt)
        send("isready")
        drain()
    return p, r, send, drain


def collect(r, send, deadline_s=60.0, early_quit_at=None):
    """Read lines until bestmove. If early_quit_at is set, send `quit` after that many seconds
    (case 2 only: the early quit is the phenomenon)."""
    import time
    t0 = time.monotonic()
    quit_sent = False
    lines = []
    while True:
        if early_quit_at is not None and not quit_sent and time.monotonic() - t0 >= early_quit_at:
            send("quit")
            quit_sent = True
        line = r.get(1.0)
        if line is None:
            if time.monotonic() - t0 > deadline_s:
                return lines, None
            continue
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            return lines, line.split()[1]


def analyse(lines, best, fen):
    zero, last_nodes, infos = 0, None, []
    for l in lines:
        if l.startswith("info depth"):
            infos.append(l)
            m = re.search(r" nodes (\d+) ", l + " ")
            if m:
                last_nodes = int(m.group(1))
                if last_nodes == 0:
                    zero += 1
    legal_ok = None
    if best is not None and fen:
        try:
            b = chess.Board(fen)
            legal = [m.uci() for m in b.legal_moves]
            legal_ok = (best == "0000" and not legal) or (best in legal)
        except ValueError:
            legal_ok = None
    return {"depth_lines": len(infos), "zero_node_lines": zero,
            "last_nodes": last_nodes, "bestmove": best,
            "bestmove_legal": legal_ok,
            "fabricated": zero > 0}


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    results = {}

    # ---- case 1: 07-F1 ----
    p, r, send, drain = session(exe)
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send("go searchmoves e2e5")
    lines, best = collect(r, send)
    results["1_07F1_searchmoves_no_legal_name"] = analyse(
        lines, best, chess.Board().fen())
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()

    # ---- case 2: 19-F12 aborted search ----
    p, r, send, drain = session(exe)
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send("go depth 12")
    lines, best = collect(r, send, deadline_s=30.0, early_quit_at=0.0)
    results["2_19F12_aborted_search"] = analyse(lines, best, chess.Board().fen())
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()

    # ---- case 3: no-match searchmoves with a node budget ----
    p, r, send, drain = session(exe)
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send("go nodes 100000 searchmoves e2e5")
    lines, best = collect(r, send)
    results["3_nomatch_node_budget"] = analyse(lines, best, chess.Board().fen())
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()

    # ---- control: the same three shapes but with a legal target / no restriction ----
    p, r, send, drain = session(exe)
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send("go searchmoves e2e4")
    lines, best = collect(r, send)
    results["control_searchmoves_legal"] = analyse(lines, best, chess.Board().fen())
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()

    import json
    json.dump(results, open(os.path.join(outdir, "three_symptoms.json"), "w"), indent=1)

    print(f"{'case':38s} {'bestmove':>10s} {'depthlines':>10s} {'zeronodes':>10s} {'last_nodes':>11s} legal")
    for k, v in results.items():
        print(f"{k:38s} {str(v['bestmove']):>10s} {v['depth_lines']:>10d} {v['zero_node_lines']:>10d} "
              f"{str(v['last_nodes']):>11s} {v['bestmove_legal']}")
    zeros = [k for k, v in results.items() if v["fabricated"]]
    print()
    print("cases with a zero-node report: " + (", ".join(zeros) if zeros else "none"))
    print("NOTE: case 2 sends `quit` deliberately at t=0; that early quit is the phenomenon 19-F12")
    print("      describes, not the harness bug seat 19 warned everyone about.")


if __name__ == "__main__":
    main()
