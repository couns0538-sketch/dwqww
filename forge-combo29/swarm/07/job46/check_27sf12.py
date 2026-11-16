#!/usr/bin/env python3
"""check_27sf12.py PC_EXE BASE_EXE OUTDIR

Independent check of seat 27's S-F12:
  "THE CLOCK IS IGNORED ENTIRELY WHEN BLACK IS TO MOVE — `go wtime N` searches the same tree for
   every N, including `wtime 0`. go wtime 0/1/3/10/50/200/1000/3000 all give the SAME answer —
   depth 20, 286,156 nodes, ~124 ms on FEN 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55.
   `go movetime 5` stops at depth 1/39 nodes. The discriminator is the side to move."

If true this is a live defect on the owner's match path, so it needs an independent check with a
harness that measures the WALL clock as well as the engine's own reported numbers.

Protocol, per cell: fresh process, PC20, Threads 1, Hash 16, `ucinewgame`, `position fen`, then one
`go` command; read until `bestmove` while timing with a monotonic clock.

Cells: the reported FEN with each `go wtime N btime N` for N in {0,1,3,10,50,200,1000,3000}, plus
`go movetime 5`, plus the SAME board with the side to move swapped (`w`), plus a second board of my
own choosing with Black to move (so the result is not one position's quirk).

Controls, required before any conclusion:
  * `go movetime 5` must be SHORT (the movetime path works) - if it is not, the harness cannot see
    a short search at all and no "clock ignored" claim can be measured.
  * `go movetime 3000` must be LONGER than `go movetime 5` - proving the harness can distinguish.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

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

REPORTED_FEN = "2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55"
# my own second board with Black to move: a normal middlegame, chosen without reference to theirs
MY_FEN_BLACK = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R b KQ - 0 8"


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, fen, go, options, limit_s=8.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = R(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get(60)
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()

    t0 = time.monotonic()
    send(go)
    dlines, nodes, score, best = 0, None, None, None
    while True:
        l = r.get(limit_s)
        if l is None:
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
    wall_ms = (time.monotonic() - t0) * 1000.0
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return {"go": go, "wall_ms": round(wall_ms, 1), "depth_lines": dlines,
            "nodes": nodes, "score": score, "best": best}


def main():
    pc, base, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)

    # ---- controls ----
    c_short = run(pc, REPORTED_FEN, "go movetime 5", PC20)
    c_long = run(pc, REPORTED_FEN, "go movetime 3000", PC20)
    print("CONTROLS on the reported FEN:")
    print(f"  go movetime 5    wall {c_short['wall_ms']:>7} ms  depth lines {c_short['depth_lines']:>3}  "
          f"nodes {c_short['nodes']}")
    print(f"  go movetime 3000 wall {c_long['wall_ms']:>7} ms  depth lines {c_long['depth_lines']:>3}  "
          f"nodes {c_long['nodes']}")
    short_ok = c_short["wall_ms"] < 100
    order_ok = c_long["wall_ms"] > c_short["wall_ms"] * 3
    print(f"  control: movetime 5 is short (<100 ms): {short_ok}")
    print(f"  control: movetime 3000 much longer     : {order_ok}")
    if not (short_ok and order_ok):
        raise SystemExit("FAIL the harness cannot distinguish a short from a long search; "
                         "no 'clock ignored' claim can be measured")

    rows = []
    print("\nBLACK to move, the reported FEN, `go wtime N btime N`:")
    for n in (0, 1, 3, 10, 50, 200, 1000, 3000):
        r = run(pc, REPORTED_FEN, f"go wtime {n} btime {n}", PC20)
        r["cell"] = f"black_wtime{n}"
        rows.append(r)
        print(f"  wtime {n:>5}: wall {r['wall_ms']:>8} ms  depth lines {r['depth_lines']:>3}  "
              f"nodes {r['nodes']}  {r['score']}  {r['best']}")

    print("\nthe SAME board with WHITE to move (seat 27's discriminator):")
    white_fen = REPORTED_FEN.replace(" b ", " w ", 1)
    for n in (0, 2000):
        r = run(pc, white_fen, f"go wtime {n} btime {n}", PC20)
        r["cell"] = f"white_wtime{n}"
        rows.append(r)
        print(f"  wtime {n:>5}: wall {r['wall_ms']:>8} ms  depth lines {r['depth_lines']:>3}  "
              f"nodes {r['nodes']}  {r['score']}  {r['best']}")

    print("\nMY OWN second board, BLACK to move (not one position's quirk):")
    for n in (0, 50, 3000):
        r = run(pc, MY_FEN_BLACK, f"go wtime {n} btime {n}", PC20)
        r["cell"] = f"mine_black_wtime{n}"
        rows.append(r)
        print(f"  wtime {n:>5}: wall {r['wall_ms']:>8} ms  depth lines {r['depth_lines']:>3}  "
              f"nodes {r['nodes']}  {r['score']}  {r['best']}")

    print("\nBASE build, the reported FEN, BLACK to move (is this PC-specific?):")
    for n in (0, 3000):
        r = run(base, REPORTED_FEN, f"go wtime {n} btime {n}", [])
        r["cell"] = f"base_black_wtime{n}"
        rows.append(r)
        print(f"  wtime {n:>5}: wall {r['wall_ms']:>8} ms  depth lines {r['depth_lines']:>3}  "
              f"nodes {r['nodes']}  {r['score']}  {r['best']}")

    json.dump(rows, open(os.path.join(outdir, "check_27sf12.json"), "w"), indent=1)

    black = [r for r in rows if r["cell"].startswith("black_wtime")]
    same = len({(r["nodes"], r["best"], r["depth_lines"]) for r in black}) == 1
    print()
    print(f"all eight `wtime` values gave the same (nodes, bestmove, depth lines): {same}")
    if same:
        print("=> seat 27's S-F12 REPRODUCES on the reported FEN with my harness.")
    else:
        print("=> S-F12 does NOT reproduce as stated; see the per-cell rows above.")


if __name__ == "__main__":
    main()
