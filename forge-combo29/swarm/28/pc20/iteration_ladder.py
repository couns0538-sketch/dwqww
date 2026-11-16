#!/usr/bin/env python3
"""iteration_ladder.py EXE LABEL WTIME — where in the iteration ladder does each build stop?

If the plans are identical (soft = 454 ms at wtime 10000) and the PC build stops at 311 ms where base
stops at 350 ms, the question is which ITERATION each one ended on and how far into the budget that
iteration began.

For each search this records the full (depth, cumulative time) ladder the engine printed, then reports:
  - the depth of the last completed iteration on each build;
  - the time that iteration FINISHED at, and the time the PREVIOUS one finished at (so the duration of
    the last iteration is visible);
  - whether the last iteration finished before softexpired or was cut mid-iteration;
  - what the NEXT iteration would have cost at the observed growth rate, i.e. how far short the stop was.

The point: an iteration costs roughly 3-5x the previous one, so a stop at 68 % vs 77 % of soft can be the
difference between fitting depth 20 and not. That makes the lost ply an arithmetic consequence of the
stop point, not a search weakness.

Usage: iteration_ladder.py EXE LABEL WTIME [NPOS]
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
OVERHEAD, SOFT_DIV = 10, 22


def cell(exe, fens, wtime, pc20):
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
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc 0 binc 0")
        out, ok = eng.read_until("bestmove", max(120, wtime / 1000 * 3))
        t1 = time.monotonic()
        if not ok:
            continue
        ladder = []
        for line in out:
            if line.startswith("info depth") and " time " in line:
                f = line.split()
                ladder.append((int(f[f.index("depth") + 1]), float(f[f.index("time") + 1])))
        # Collapse to the last time seen for each depth (a depth can print several lines).
        per_depth = {}
        for d, t in ladder:
            per_depth[d] = max(per_depth.get(d, 0.0), t)
        seq = sorted(per_depth.items())
        rows.append({"wall": (t1 - t0) * 1000.0, "seq": seq})
    eng.close()
    return rows


def main() -> int:
    exe, label, wtime = sys.argv[1], sys.argv[2], int(sys.argv[3])
    npos = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    soft = max(1, (wtime - OVERHEAD) // SOFT_DIV)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    rows = cell(exe, fens, wtime, label == "PC20")

    print(f"build {label}, wtime {wtime}, plan soft {soft} ms, {len(rows)} positions, Threads 1")
    print()
    print("| position (first 8) | depths visited -> cumulative ms | last depth | last iter finished at "
          "| prev iter finished at | last iteration cost |")
    print("|---|---|---|---|---|---|")
    for i, r in enumerate(rows[:8], 1):
        seq = r["seq"]
        if not seq:
            continue
        visited = " ".join(f"{d}:{t:.0f}" for d, t in seq)
        last_d, last_t = seq[-1]
        prev_t = seq[-2][1] if len(seq) > 1 else 0.0
        print(f"| {i} | {visited} | {last_d} | {last_t:.0f} | {prev_t:.0f} | {last_t-prev_t:.0f} |")

    # Summary over all positions.
    last_depths = [r["seq"][-1][0] for r in rows if r["seq"]]
    last_times = [r["seq"][-1][1] for r in rows if r["seq"]]
    costs = []
    growth = []
    for r in rows:
        seq = r["seq"]
        if len(seq) >= 2:
            costs.append(seq[-1][1] - seq[-2][1])
            if seq[-2][1] > 20:
                growth.append(seq[-1][1] / max(1.0, seq[-2][1]))
    print()
    print(f"median last depth {statistics.median(last_depths):.0f}, median last-iteration finish "
          f"{statistics.median(last_times):.0f} ms, median cost of the LAST iteration "
          f"{statistics.median(costs) if costs else 0:.0f} ms, median growth factor "
          f"{statistics.median(growth) if growth else 0:.2f}x")
    print(f"median last-iteration finish as a fraction of soft: "
          f"{statistics.median(last_times)/soft:.2f}")
    if costs:
        print(f"median next iteration would cost about "
              f"{statistics.median(costs)*statistics.median(growth):.0f} ms more, i.e. it would finish "
              f"at about {statistics.median(last_times)+statistics.median(costs)*statistics.median(growth):.0f} ms "
              f"vs a {soft} ms soft plan")
    with open(f"ladder_{label}_w{wtime}.tsv", "w") as fh:
        fh.write("index\tvisited\tlast_depth\tlast_time\tprev_time\tlast_cost\n")
        for i, r in enumerate(rows, 1):
            seq = r["seq"]
            if not seq:
                continue
            fh.write(f"{i}\t{' '.join(f'{d}:{t:.0f}' for d, t in seq)}\t{seq[-1][0]}\t"
                     f"{seq[-1][1]:.0f}\t{seq[-2][1] if len(seq) > 1 else 0:.0f}\t"
                     f"{seq[-1][1]-(seq[-2][1] if len(seq) > 1 else 0):.0f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
