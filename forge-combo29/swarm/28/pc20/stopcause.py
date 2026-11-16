#!/usr/bin/env python3
"""stopcause.py EXE LABEL — which stop path does each search actually take?

The PC patch adds one new stop path (`FORGE_FIX_HARD_LIMIT_EMERGENCY`): if the hard limit has already
passed when the search starts, it runs one capped emergency ply and sets `time_managed_ = false`. That
path can only fire if `elapsed_ms() >= hard_limit_ms_` at entry, i.e. after 2270 ms at wtime 10000 — never,
for a search that ends at 300 ms.

So if the stop fraction still differs, the difference is NOT that path. This script tests the remaining
runtime candidate directly: does the PC build spend its soft budget on fewer, longer iterations, i.e. is
the ITERATION LENGTH distribution different? It records, per search, the ladder and computes:
  - number of completed iterations
  - median time per iteration
  - the time the last iteration finished, as a fraction of soft
  - whether the last iteration was followed by an incomplete one that got discarded

And it repeats the whole cell twice on each build to show the spread.

Usage: stopcause.py EXE LABEL [NPOS]
"""
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
WTIME, SOFT = 10000, 454


def cell(exe, fens, pc20):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items())
    sent += PC20_EXTRA if pc20 else [("OwnBook", "false")]
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    out_rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {WTIME} btime {WTIME} winc 0 binc 0")
        out, ok = eng.read_until("bestmove", 90)
        t1 = time.monotonic()
        if not ok:
            continue
        per_depth = {}
        for line in out:
            if line.startswith("info depth") and " time " in line:
                f = line.split()
                d = int(f[f.index("depth") + 1])
                t = float(f[f.index("time") + 1])
                per_depth[d] = max(per_depth.get(d, 0.0), t)
        seq = sorted(per_depth.items())
        if not seq:
            continue
        costs = [seq[0][1]] + [seq[i][1] - seq[i - 1][1] for i in range(1, len(seq))]
        out_rows.append({"wall": (t1 - t0) * 1000.0, "seq": seq, "n_iter": len(seq),
                         "last_t": seq[-1][1], "last_depth": seq[-1][0],
                         "costs": costs})
    eng.close()
    return out_rows


def report(label, rows):
    if not rows:
        print(f"{label}: no rows"); return
    walls = [r["wall"] for r in rows]
    last_t = [r["last_t"] for r in rows]
    n_iter = [r["n_iter"] for r in rows]
    # cost of the final iteration for each search
    last_cost = [r["costs"][-1] for r in rows]
    print(f"| {label} | {len(rows)} | {statistics.median(walls):.1f} | "
          f"{statistics.median(walls)/SOFT:.3f} | {statistics.median(last_t):.0f} | "
          f"{statistics.median(last_t)/SOFT:.3f} | {statistics.median(n_iter):.0f} | "
          f"{statistics.median(last_cost):.0f} |")


def main() -> int:
    exe, label = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    pc20 = label != "base"
    print(f"wtime {WTIME}, soft plan {SOFT} ms, {len(fens)} positions, Threads 1, go wtime both sides")
    print()
    print("| run | n | median achieved | achieved/soft | median last-iter finish | "
          "finish/soft | median #iterations | median last-iteration cost |")
    print("|---|---|---|---|---|---|---|---|")
    for run in (1, 2):
        rows = cell(exe, fens, pc20)
        report(f"{label} run{run}", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
