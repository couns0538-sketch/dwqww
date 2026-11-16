#!/usr/bin/env python3
"""check_08f10.py EXE OUT.json — seat 12's check of seat 08's 08-F10.

Claim: the two stop paths have OPPOSITE error modes.

  `go movetime M`  the hard limit is checked INSIDE the search, so the PARTIAL iteration is
                   discarded: the wall time lands AT the plan (+ a small constant), but the
                   iteration the engine KEPT (its own `time` field on the last info line) is
                   well BELOW the plan.

  `go wtime ...`   the soft limit breaks at an ITERATION BOUNDARY and discards nothing: the kept
                   iteration's `time` is at or just past the plan, and the wall overshoots by up
                   to a whole iteration.

How this is measured without trusting the engine's own bookkeeping for the wall:
  * wall  = monotonic clock from writing `go` to reading `bestmove` (the GUI's number);
  * kept  = the `time` field of the LAST `info depth` line (the iteration the engine chose to
            keep, in its own words).
The two are compared against the PLAN, which is what the engine computes from the clock.

Every case is a fresh process, Threads 1, Hash 16, MultiPV 1, OwnBook false, read to `bestmove`.
Cases are repeated so a single unlucky search cannot carry the verdict.
"""
import json
import queue
import re
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

POS = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def one(exe, go, overhead=None, bound=120.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(t):
        p.stdin.write(t + "\n")
        p.stdin.flush()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    try:
        send("uci")
        wait(lambda l: l == "uciok", 30)
        for name, value in (("Hash", 16), ("MultiPV", 1), ("Threads", 1), ("OwnBook", "false")):
            send(f"setoption name {name} value {value}")
            send("isready")
            wait(lambda l: l == "readyok", 30)
        if overhead is not None:
            send(f"setoption name Move Overhead value {overhead}")
            send("isready")
            wait(lambda l: l == "readyok", 30)
        send(f"position fen {POS}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
        t0 = time.monotonic()
        send(go)
        bm = wait(lambda l: l.startswith("bestmove"), bound)
        wall = (time.monotonic() - t0) * 1000
        send("quit")
    except (BrokenPipeError, OSError, ValueError):
        wall, bm = None, None
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    # wall measured around the `go` only; re-time from the recorded send point is above.
    infos = [l for l in out if l.startswith("info depth")]
    kept_ms = kept_depth = kept_nodes = None
    if infos:
        last = infos[-1]
        m = re.search(r" time (\d+)", last)
        kept_ms = int(m.group(1)) if m else None
        m = re.search(r"^info depth (\d+)", last)
        kept_depth = int(m.group(1)) if m else None
        m = re.search(r" nodes (\d+)", last)
        kept_nodes = int(m.group(1)) if m else None
    return {"go": go, "wall_ms": wall, "kept_ms": kept_ms, "kept_depth": kept_depth,
            "kept_nodes": kept_nodes, "info_lines": len(infos),
            "answered": isinstance(bm, str) and bm.startswith("bestmove")}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    reps = 6
    print(f"exe {exe}   Threads 1, Hash 16, MultiPV 1, OwnBook false, {reps} runs per case\n")
    print(f"{'case':40} {'plan':>6} {'wall med':>9} {'kept med':>9} {'wall-plan':>10} "
          f"{'kept-plan':>10} {'depth':>6}")
    print("-" * 100)
    out = {"exe": exe, "threads": 1, "cases": []}

    rows = []
    # ---- path A: movetime (hard limit inside the search)
    for movetime, overhead in ((50, None), (500, None), (200, None), (50, 0), (50, 45)):
        go = f"go movetime {movetime}"
        plan = movetime - (10 if overhead is None else overhead)
        rs = [one(exe, go, overhead) for _ in range(reps)]
        ok = [r for r in rs if r["answered"] and r["kept_ms"] is not None]
        if not ok:
            print(f"{go + ('' if overhead is None else f' (overhead {overhead})'):40} "
                  f"no completed search")
            continue
        wall = statistics.median(r["wall_ms"] for r in ok)
        kept = statistics.median(r["kept_ms"] for r in ok)
        depth = statistics.median(r["kept_depth"] for r in ok)
        label = go + ("" if overhead is None else f" ovh {overhead}")
        print(f"{label:40} {plan:>6} {wall:>9.1f} {kept:>9.1f} {wall-plan:>+10.1f} "
              f"{kept-plan:>+10.1f} {depth:>6.0f}")
        rows.append({"path": "movetime", "go": go, "overhead": overhead, "plan": plan,
                     "wall_med": round(wall, 1), "kept_med": round(kept, 1),
                     "wall_minus_plan": round(wall - plan, 1),
                     "kept_minus_plan": round(kept - plan, 1),
                     "kept_plan_min": round(min(r["kept_ms"] for r in ok) - plan, 1),
                     "kept_plan_max": round(max(r["kept_ms"] for r in ok) - plan, 1),
                     "wall_min": round(min(r["wall_ms"] for r in ok), 1),
                     "wall_max": round(max(r["wall_ms"] for r in ok), 1),
                     "depth_med": depth, "n": len(ok)})

    # ---- path B: the clock (soft limit at an iteration boundary)
    for args, plan_note in (("go wtime 1000 btime 1000", None),
                            ("go wtime 500 btime 500", None),
                            ("go wtime 1000 btime 1000 movestogo 1", None),
                            ("go wtime 200 btime 200", None)):
        go = args
        rs = [one(exe, go) for _ in range(reps)]
        ok = [r for r in rs if r["answered"] and r["kept_ms"] is not None]
        if not ok:
            print(f"{go:40} no completed search")
            continue
        wall = statistics.median(r["wall_ms"] for r in ok)
        kept = statistics.median(r["kept_ms"] for r in ok)
        depth = statistics.median(r["kept_depth"] for r in ok)
        print(f"{go:40} {'?':>6} {wall:>9.1f} {kept:>9.1f} {'':>10} {'':>10} {depth:>6.0f}")
        rows.append({"path": "clock", "go": go, "plan": None,
                     "wall_med": round(wall, 1), "kept_med": round(kept, 1),
                     "wall_min": round(min(r["wall_ms"] for r in ok), 1),
                     "wall_max": round(max(r["wall_ms"] for r in ok), 1),
                     "kept_min": min(r["kept_ms"] for r in ok),
                     "kept_max": max(r["kept_ms"] for r in ok),
                     "depth_med": depth, "n": len(ok)})

    out["cases"] = rows
    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")

    # ---- verdict on the two halves
    mt = [r for r in rows if r["path"] == "movetime"]
    clk = [r for r in rows if r["path"] == "clock"]
    print("\n=== verdict")
    if mt:
        wall_deltas = [r["wall_minus_plan"] for r in mt]
        kept_deltas = [r["kept_minus_plan"] for r in mt]
        wall_tight = all(-5 <= d <= 15 for d in wall_deltas)
        kept_below = all(d < 0 for d in kept_deltas)
        print(f"movetime path: wall-plan in {min(wall_deltas):+.1f}..{max(wall_deltas):+.1f} ms "
              f"({'tight to the plan' if wall_tight else 'NOT tight'})")
        print(f"               kept-plan in {min(kept_deltas):+.1f}..{max(kept_deltas):+.1f} ms "
              f"({'kept iteration is BELOW the plan — partial work discarded' if kept_below else 'kept at/above plan'})")
        print(f"  -> 08-F10 movetime half: "
              f"{'CONFIRMED' if (wall_tight and kept_below) else 'NOT CONFIRMED'}")
    if clk:
        print(f"clock path: kept times {[r['kept_med'] for r in clk]} ms, wall "
              f"{[r['wall_med'] for r in clk]} ms")
        print(f"  -> 08-F10 clock half: the kept iteration carries the time actually spent "
              f"(see table); compare with the movetime rows where it does not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
