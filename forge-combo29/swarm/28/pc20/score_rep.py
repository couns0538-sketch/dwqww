#!/usr/bin/env python3
"""score_rep.py EXE OUTDIR — seat 04's rule applied to my own measurements: are SCORES reproducible?

Seat 04 measured the PC build at Threads 4 depth 12 under PC20 on one position: +2576, mate 13, mate 18,
mate 16 across four fresh runs, nodes 5.0M-31.4M. At Threads 1 the same setup gave +2207 four times with
identical nodes 75,311. The move never varied; the score did.

Every clock number in my area depends on the tree, and a non-reproducible score changes the tree, which
changes the time. So this script measures, at THREADS 1 under PC20, the same position five times in five
fresh processes at `go depth 12`, and records bestmove, score, nodes, and whether all five agree.

It also does the same at Threads 4 for contrast, so the table shows whether the non-reproducibility seat 04
saw is thread-dependent on THIS build and settings.

Usage: score_rep.py EXE OUTDIR
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
# A tactically sharp, materially unbalanced position (a queen down for a rook) — the kind seat 04 used.
FEN = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
RUNS = 5


def one(exe, threads, depth=12):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", threads), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {FEN}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    t0 = time.monotonic()
    eng.send(f"go depth {depth}")
    out, ok = eng.read_until("bestmove", 600)
    t1 = time.monotonic()
    eng.close()
    best, score, nodes, d = "", "", 0, 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            d = max(d, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
            if "score" in f:
                score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
    return {"best": best, "score": score, "nodes": nodes, "depth": d,
            "wall": (t1 - t0) * 1000.0, "ok": ok}


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    print(f"position: {FEN}")
    print(f"PC20, go depth 12, {RUNS} fresh processes per thread count")
    print()
    print("| threads | run | bestmove | score | nodes | depth | wall ms |")
    print("|---|---|---|---|---|---|---|")
    results = {}
    for threads in (1, 4):
        rs = []
        for i in range(RUNS):
            r = one(exe, threads)
            rs.append(r)
            print(f"| {threads} | {i+1} | {r['best']} | {r['score']} | {r['nodes']} | {r['depth']} | "
                  f"{r['wall']:.0f} |", flush=True)
        results[threads] = rs
    print()
    for threads, rs in results.items():
        scores = {r["score"] for r in rs}
        moves = {r["best"] for r in rs}
        nodes = {r["nodes"] for r in rs}
        print(f"Threads {threads}: distinct scores {len(scores)} {sorted(scores)}, "
              f"distinct moves {len(moves)} {sorted(moves)}, distinct node counts {len(nodes)}")
    with open(os.path.join(outdir, "score_rep.tsv"), "w") as fh:
        fh.write("threads\trun\tbestmove\tscore\tnodes\tdepth\twall_ms\n")
        for threads, rs in results.items():
            for i, r in enumerate(rs, 1):
                fh.write(f"{threads}\t{i}\t{r['best']}\t{r['score']}\t{r['nodes']}\t{r['depth']}\t"
                         f"{r['wall']:.0f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
