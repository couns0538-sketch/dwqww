#!/usr/bin/env python3
"""isolate_pc20.py PC_EXE FENS OUTDIR DEPTH

Which PC20 option drives the difference? The four-leg attribution showed:

    base + S14   9,500,069
    PC   + S14   9,500,069   <- identical, so the patch's FORGE_FIX_* switches change nothing here
    PC   + PC20  8,315,168   <- the whole difference needs the PC-only options

So one (or more) of the six PC20 additions does it. This runs S14 + each addition ALONE over a
subset of positions, so the owner can see which default actually matters.

The base build cannot honour these five options at all (it answers `unknown option`, verified), which
is why the base+PC20 leg equals base+S14 trivially and is NOT evidence about the settings.
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
ADDITIONS = [
    ("CuckooRep", ["CuckooRep value true"]),
    ("HistRework2", ["HistRework value 2"]),
    ("HistRework3", ["HistRework value 3"]),
    ("TtPruneV2", ["TtPruneV2 value true"]),
    ("CorrHistV2", ["CorrHistV2 value true"]),
    ("MateAlphaGuard", ["MateAlphaGuard value true"]),
    ("OwnBookOff", ["OwnBook value false"]),
]


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
        send("setoption name " + opt); send("isready"); drain(opt)
    send("ucinewgame"); send("isready"); drain("ucinewgame")
    send("position fen " + fen); send("isready"); drain("position")
    send(f"go depth {depth}")
    nodes, best = None, None
    while True:
        l = r.get(600)
        if l is None:
            raise RuntimeError(f"no bestmove for {fen}")
        if l.startswith(f"info depth {depth}") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    if nodes is None:
        raise SystemExit(f"FAIL no nodes for {fen}")
    return nodes, best


def sum_for(exe, options, fens, depth):
    total = 0
    for fen in fens:
        n, _ = go_once(exe, options, fen, depth)
        total += n
    return total


def main():
    exe, fens_path, outdir, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path) if l.strip()][:limit]
    print(f"positions {len(fens)}, depth {depth}, PC build, Threads 1, Hash 16", flush=True)

    base_s14 = sum_for(exe, S14, fens, depth)
    print(f"S14 alone                      sum {base_s14}", flush=True)
    rows = [{"config": "S14", "sum": base_s14, "delta": 0}]
    for name, opt in ADDITIONS:
        s = sum_for(exe, S14 + opt, fens, depth)
        d = s - base_s14
        rows.append({"config": "S14+" + name, "sum": s, "delta": d})
        print(f"S14 + {name:16s} sum {s:>10d}  delta {d:>+9d} "
              f"({100.0 * d / base_s14:+.1f}%)", flush=True)
    all_pc20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
                      "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]
    s = sum_for(exe, all_pc20, fens, depth)
    rows.append({"config": "S14+all PC20", "sum": s, "delta": s - base_s14})
    print(f"S14 + all six (PC20)           sum {s:>10d}  delta {s - base_s14:>+9d} "
          f"({100.0 * (s - base_s14) / base_s14:+.1f}%)", flush=True)
    json.dump({"positions": len(fens), "depth": depth, "rows": rows},
              open(os.path.join(outdir, "isolate.json"), "w"), indent=1)
    print()
    ranked = sorted([r for r in rows if r["config"] != "S14"],
                    key=lambda r: -abs(r["delta"]))
    print("largest single-option effects, in order:")
    for r in ranked[:5]:
        print(f"  {r['config']:20s} delta {r['delta']:+9d}")


if __name__ == "__main__":
    main()
