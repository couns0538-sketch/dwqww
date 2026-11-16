#!/usr/bin/env python3
"""discriminate_paths.py PC_EXE OUTDIR

Three symptoms were reported. Cases 1 and 3 (this seat's 07-F1, and the no-match case with a node
budget) both print depth lines with `nodes 0`. Case 2 (19-F12, `go depth 12` + immediate quit) prints
NO depth lines and answers a legal move. That difference suggests a different code path, and this
script tests it discriminatorily rather than by reading alone.

Discriminating experiment for case 2: if the answer comes from
`if (result.best_move.is_none()) result.best_move = root_candidates.front();` (src/search.cpp:3017),
then restricting the root changes the answer to the FIRST move of the restricted set. So:

  go depth 12                       + quit at t=0  -> a2a3  (first of all 20 legal moves)
  go depth 12 searchmoves d2d4      + quit at t=0  -> d2d4  (first of the restricted set)
  go depth 12 searchmoves h2h4      + quit at t=0  -> h2h4

If all three follow `root_candidates.front()`, case 2 is that fallback and NOT the same path as
cases 1/3 (where root_candidates is EMPTY and the early return at 2581 fires).

For contrast, case 1 is re-run with the same restriction so the two can be compared directly.
"""
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


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=60):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, go, quit_immediately):
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
        send("setoption name " + opt); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send(go)
    if quit_immediately:
        send("quit")
    lines, best = [], None
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        line = r.get(2.0)
        if line is None:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            best = line.split()[1]
            break
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    depth = [l for l in lines if l.startswith("info depth")]
    nodes = None
    if depth:
        m = re.search(r" nodes (\d+) ", depth[-1] + " ")
        if m:
            nodes = int(m.group(1))
    return {"go": go, "quit_immediately": quit_immediately, "bestmove": best,
            "depth_lines": len(depth), "last_nodes": nodes}


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    cases = [
        ("2a_no_restriction",      "go depth 12", False),
        ("2b_restrict_d2d4",       "go depth 12 searchmoves d2d4", False),
        ("2c_restrict_h2h4",       "go depth 12 searchmoves h2h4", False),
        ("2d_restrict_multi",      "go depth 12 searchmoves h2h4 g2g3", False),
        ("1_empty_root",           "go searchmoves e2e5", False),
        ("1_empty_root_with_nb",   "go nodes 100000 searchmoves e2e5", False),
    ]
    rows = []
    print(f"{'case':24s} {'quit@t0':>8s} {'bestmove':>10s} {'depthlines':>10s} {'nodes':>10s}")
    for name, go, qi in cases:
        rec = run(exe, go, qi)
        rec["case"] = name
        rows.append(rec)
        print(f"{name:24s} {str(qi):>8s} {str(rec['bestmove']):>10s} "
              f"{rec['depth_lines']:>10d} {str(rec['last_nodes']):>10s}", flush=True)

    # The discriminating runs: same go, but quit fired immediately.
    print()
    print("--- the same three searches with `quit` sent immediately (the 19-F12 shape) ---")
    for name, go in [("2a_q", "go depth 12"),
                     ("2b_q", "go depth 12 searchmoves d2d4"),
                     ("2c_q", "go depth 12 searchmoves h2h4"),
                     ("2d_q", "go depth 12 searchmoves h2h4 g2g3")]:
        rec = run(exe, go, True)
        rec["case"] = name + "_quit_t0"
        rec["quit_immediately"] = True
        rows.append(rec)
        print(f"{name:24s} {'True':>8s} {str(rec['bestmove']):>10s} "
              f"{rec['depth_lines']:>10d} {str(rec['last_nodes']):>10s}", flush=True)

    import json
    json.dump(rows, open(os.path.join(outdir, "discriminate.json"), "w"), indent=1)
    print()
    followed = [r for r in rows if r["case"].startswith(("2a_q", "2b_q", "2c_q", "2d_q"))]
    print("If every *_quit_t0 answer equals the FIRST move of its own restriction, the abort case is")
    print("the `root_candidates.front()` fallback and a DIFFERENT path from the empty-root cases.")
    for r in followed:
        print(f"  {r['case']:22s} go=[{r['go']}] -> {r['bestmove']} "
              f"(depth lines {r['depth_lines']}, nodes {r['last_nodes']})")


if __name__ == "__main__":
    main()
