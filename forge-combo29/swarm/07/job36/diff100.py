#!/usr/bin/env python3
"""diff100.py BASE_EXE PC_EXE FENS OUTDIR DEPTH

The 100-case differential: for each position, run the same search on base and on the PC build under
IDENTICAL settings, then for every position where the answer differs, isolate which FORGE_FIX_* switch
is responsible by testing scratch builds with each switch alone.

Settings: Threads 1, Hash 16, OwnBook false, ucinewgame + isready before the go, fresh process per
run. No S14/PC20 options here on purpose -- this compares the BUILDS, so the settings must be equal
and minimal.

Stage 1  base vs PC under identical settings -> list of differing positions.
Stage 2  for each differing position, and for whichever switches the caller supplies as scratch
         builds, re-run that one position and record which build reproduces the PC answer.

Isolation builds are passed as `--variant NAME=PATH` and must have been built from the PC tree with
exactly one switch changed; the caller is responsible for that (see job33 for the recipe), and this
script records the mapping so the report can name the switch per difference.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading


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


def run_one(exe, fen, depth):
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
    for opt in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + opt); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(f"go depth {depth}")
    nodes, score, best, dlines = None, None, None, 0
    while True:
        l = r.get(600)
        if l is None:
            best = "ABSENT"
            break
        if l.startswith("info depth"):
            dlines += 1
            m = re.search(r" nodes (\d+) ", l + " ")
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"nodes": nodes, "score": score, "best": best, "depth_lines": dlines}


def main():
    args = sys.argv[1:]
    variants = []
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--variant":
            name, path = args[i + 1].split("=", 1)
            variants.append((name, path))
            i += 2
        else:
            positional.append(args[i]); i += 1
    base_exe, pc_exe, fens_path, outdir, depth = (positional[0], positional[1], positional[2],
                                                  positional[3], int(positional[4]))
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path) if l.strip()]
    print(f"positions {len(fens)}, depth {depth}, Threads 1, Hash 16, OwnBook false")
    print(f"isolation variants supplied: {[v[0] for v in variants]}")

    stage1 = []
    for idx, fen in enumerate(fens):
        b = run_one(base_exe, fen, depth)
        p = run_one(pc_exe, fen, depth)
        same = (b["nodes"] == p["nodes"] and b["score"] == p["score"] and b["best"] == p["best"])
        rec = {"i": idx, "fen": fen, "base": b, "pc": p, "differs": not same}
        stage1.append(rec)
        if not same:
            print(f"  DIFF {idx:3d} base {b['best']}/{b['score']}/{b['nodes']}  "
                  f"pc {p['best']}/{p['score']}/{p['nodes']}", flush=True)
        if (idx + 1) % 25 == 0:
            n = sum(1 for r in stage1 if r["differs"])
            print(f"  ...{idx+1}/{len(fens)}  differences so far {n}", flush=True)

    differing = [r for r in stage1 if r["differs"]]
    print(f"\nstage 1: {len(differing)} of {len(fens)} positions differ "
          f"({100.0 * len(differing) / len(fens):.1f}%)")

    # stage 2: isolate, per differing position, which variant reproduces the PC answer
    if variants and differing:
        print("\nstage 2: isolating the responsible switch per differing position")
        for rec in differing:
            rec["isolation"] = {}
            for name, path in variants:
                v = run_one(path, rec["fen"], depth)
                rec["isolation"][name] = v
                if (v["best"] == rec["pc"]["best"] and v["nodes"] == rec["pc"]["nodes"]):
                    print(f"  {rec['i']:3d} switch {name} reproduces the PC answer exactly",
                          flush=True)
            # name the single switch that matches, when exactly one does
            matches = [n for n, v in rec["isolation"].items()
                       if v["best"] == rec["pc"]["best"] and v["nodes"] == rec["pc"]["nodes"]]
            rec["responsible"] = matches if matches else ["NONE/COMBINATION"]

    json.dump({"positions": len(fens), "depth": depth,
               "variants": [v[0] for v in variants], "rows": stage1},
              open(os.path.join(outdir, "diff100.json"), "w"), indent=1)

    print("\n=== SUMMARY ===")
    print(f"positions differing: {len(differing)} / {len(fens)}")
    if variants:
        tally = {}
        for rec in differing:
            for name in rec.get("responsible", ["?"]):
                tally[name] = tally.get(name, 0) + 1
        print("responsible switch, counted over differing positions:")
        for name, n in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"  {name:34s} {n}")
    # any illegal or absent answer is a fault worth naming
    bad = [(r["i"], "base", r["base"]["best"]) for r in stage1
           if r["base"]["best"] in (None, "ABSENT")]
    bad += [(r["i"], "pc", r["pc"]["best"]) for r in stage1
            if r["pc"]["best"] in (None, "ABSENT")]
    print(f"absent answers: {bad if bad else 'none'}")


if __name__ == "__main__":
    main()
