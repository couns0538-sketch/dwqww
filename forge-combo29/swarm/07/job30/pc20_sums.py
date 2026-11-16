#!/usr/bin/env python3
"""pc20_sums.py PC_EXE FENS OUTDIR DEPTH [--pc20|--s14]

Re-runs this seat's known-sum checks on the PC r15 build under a chosen regime.

Why this matters: on the BASE tree all four published S14 sums reproduced exactly (07-C3/C4/C6/C8).
The PC build changes search behaviour (FORGE_FIX_* switches and four new options), so the same sums
CANNOT be expected to reproduce under S14 — file 5 publishes PC20 bench numbers instead, and only
those. This job therefore establishes what the PC build's own sums are, as a reproducible baseline
for later re-checks, rather than asserting a number it was never published for.

Rules honoured: Threads 1, Hash 16, `ucinewgame` + `isready` before EVERY `go`, one fresh process
per position (so nothing can be warm), and every node figure is parsed and asserted present.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

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

    def get(s, t=300):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def go_once(exe, options, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain(tag):
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError(f"no readyok after {tag}")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + opt)
        send("isready")
        drain(opt)
    send("ucinewgame")
    send("isready")
    drain("ucinewgame")
    send("position fen " + fen)
    send("isready")
    drain("position")
    send(f"go depth {depth}")
    nodes, score, best = None, None, None
    while True:
        l = r.get(600)
        if l is None:
            raise RuntimeError(f"no bestmove for {fen}")
        if l.startswith(f"info depth {depth}") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if nodes is None:
        raise SystemExit(f"FAIL no nodes parsed for {fen} at depth {depth}")
    return nodes, score, best


def main():
    # positional args are the first four; any --flag may appear anywhere after them
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    exe, fens_path, outdir, depth = positional[0], positional[1], positional[2], int(positional[3])
    regime = "PC20" if "--pc20" in flags else ("S14" if "--s14" in flags else "none")
    options = {"none": [], "S14": S14, "PC20": PC20}[regime]
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path, encoding="utf-8") if l.strip()]
    rows, total = [], 0
    for i, fen in enumerate(fens):
        nodes, score, best = go_once(exe, options, fen, depth)
        rows.append({"i": i, "fen": fen, "nodes": nodes, "score": score, "best": best})
        total += nodes
        if i < 3:
            print(f"  first{i+1}: nodes {nodes} score {score} best {best}", flush=True)
        if (i + 1) % 50 == 0:
            print(f"  ...{i+1}/{len(fens)} running sum {total}", flush=True)
    print(f"positions {len(rows)} depth {depth} regime {regime}")
    print(f"SUM {total}")
    json.dump({"regime": regime, "depth": depth, "fens": fens_path, "rows": rows, "sum": total},
              open(os.path.join(outdir, f"sum_{regime}_d{depth}.json"), "w"), indent=1)
    if total == 0:
        raise SystemExit("FAIL sum is zero: nothing measured")


if __name__ == "__main__":
    main()
