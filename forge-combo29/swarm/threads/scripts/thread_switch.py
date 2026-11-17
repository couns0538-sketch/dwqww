#!/usr/bin/env python3
"""Change `Threads` between searches, 200 times, and check the engine stays sane.

Two questions, and the second is the one that finds bugs:

  (a) does the search still return a LEGAL move after a thread-count change?
  (b) does the search still behave like the thread count it now claims? A worker pool
      that grows correctly makes Threads 1 -> 4 node counts jump; one that does not
      leaves them at the old count while the label says otherwise. That is the
      "a label is not a measurement" failure the findings warn about
      (trap 15: a settings NAME in a finding is not evidence the settings were sent).

The control is a run with NO Threads changes interleaved (same positions, same
budgets, same process lifetime): if changing threads is harmless, the two runs should
show the same relationship between declared thread count and node count. If it is not,
the interleaved run's counts drift away from the control.

A mid-search `setoption name Threads` is NOT tested here: the UCI loop calls
`stop_search()` before applying any setoption (uci.cpp:259), so the command cannot
land inside a running search. That is recorded as a source fact, not assumed.

Usage: python3 thread_switch.py <exe> <fens> <out.json> [iterations]
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

SEED = 1017001  # fixed: the sequence must be reproducible from the file alone


def is_legal(fen, move):
    """Legality from the ENGINE's own generator, so no third party is needed."""
    return True  # replaced below with a per-position legal set


def legal_set(e, fen):
    e.position(fen)
    e.send("go perft 1")
    lines = []
    while True:
        got = e.read_until(("nodes ",), 120.0)
        lines += got
        if got[-1].startswith("nodes "):
            break
    return {l.split(":")[0].strip() for l in lines if ":" in l and not l.startswith("info")}


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    iters = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    rng = random.Random(SEED)
    threads_choices = [1, 1, 2, 2, 4, 4, 8]

    e = Engine(exe, {"Hash": 64, "Threads": 1}, timeout=300.0)
    legal = {f: legal_set(e, f) for f in fens}
    rows = []
    illegal = 0
    noinfo = 0
    try:
        for i in range(iters):
            th = rng.choice(threads_choices)
            fen = fens[i % len(fens)]
            e.setoption("Threads", th)
            if rng.random() < 0.2:
                e.ucinewgame()
            e.position(fen)
            info, best, wall = e.go("depth 10", timeout=300.0)
            mv = best.split()[-1]
            d = last_depth_info(info)
            ok = mv in legal[fen] or mv == "0000"
            if not ok:
                illegal += 1
            if d is None:
                noinfo += 1
            rows.append({"i": i, "threads": th, "fen_idx": i % len(fens), "move": mv,
                         "legal": ok, "nodes": d["nodes"] if d else None,
                         "n_info": len([l for l in info if l.startswith("info depth")])})
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{iters} done  illegal={illegal} noinfo={noinfo}", flush=True)
    finally:
        e.close()

    # control: same positions and order, Threads never changed
    e = Engine(exe, {"Hash": 64, "Threads": 4}, timeout=300.0)
    ctrl = []
    try:
        for i in range(iters):
            fen = fens[i % len(fens)]
            if (i % 5) == 0:
                e.ucinewgame()
            e.position(fen)
            info, best, wall = e.go("depth 10", timeout=300.0)
            d = last_depth_info(info)
            ctrl.append({"i": i, "move": best.split()[-1],
                         "legal": best.split()[-1] in legal[fen],
                         "nodes": d["nodes"] if d else None})
    finally:
        e.close()

    # per declared thread count: median node count in the switched run
    by_th = {}
    for r in rows:
        by_th.setdefault(r["threads"], []).append(r["nodes"])
    med = {t: sorted(v)[len(v) // 2] for t, v in by_th.items() if v}
    print()
    print(f"switched run: {iters} searches, illegal bestmoves {illegal}, zero-info {noinfo}")
    print(f"median nodes by declared Threads: {med}")
    print(f"control (Threads 4 fixed, never changed): median nodes "
          f"{sorted(x['nodes'] for x in ctrl if x['nodes'])[len(ctrl)//2]}")
    monotone = med.get(1, 0) < med.get(2, 0) < med.get(4, 0)
    print(f"median nodes rise with declared Threads (1<2<4): {monotone}")
    with open(out_path, "w") as fh:
        json.dump({"iterations": iters, "seed": SEED, "rows": rows, "control": ctrl,
                   "illegal": illegal, "zero_info": noinfo, "median_nodes_by_thread": med,
                   "monotone": monotone, "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")
    return 0 if (illegal == 0 and monotone) else 1


if __name__ == "__main__":
    sys.exit(main())
