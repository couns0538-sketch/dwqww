#!/usr/bin/env python3
"""runtime_hypothesis.py BASE EXE_A EXE_B — is the stop fraction driven by the node RATE, not the code?

The source of the soft-limit decision is byte-identical between the base tree and PC r15 (verified by
`diff` on the exact block: 0 differing lines, all five tuneable defaults equal). So S-F26's 0.68-vs-0.77
stop fraction cannot come from the code that consumes the constants. The remaining candidates are runtime
quantities. This script tests the strongest one directly:

  If the stop fraction follows the NODE RATE, then changing the node rate on ONE build — same source, same
  constants — changes the stop fraction in the same direction. The cleanest lever that changes the node
  rate without touching the time manager is `Hash`, which changes memory locality and TT hit rate, not the
  plan. (It is not a perfect isolation of node rate — it also changes the tree — so this is a test of
  whether the stop fraction is STABLE at a fixed node rate, which is the sharper question.)

It runs the same position set at wtime 10000 under several Hash sizes on ONE build, and reports the
achieved/soft stop fraction and the median last depth per Hash size:

  - If the stop fraction is roughly CONSTANT while the node rate varies, the fraction is a property of the
    time manager and node rate cannot explain the 0.68 vs 0.77 difference — which would mean my S-F26
    comparison is an artefact of sampling.
  - If the stop fraction TRACKS the node rate, the difference is a runtime quantity and not a constant.

Also reports the same cell twice in a row on the same build, to show the run-to-run spread of the fraction
itself — the number that decides whether 0.68 vs 0.77 is even outside the noise.

Usage: runtime_hypothesis.py EXE PC20(0|1) [NPOS]
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
WTIME, SOFT, OVERHEAD, DIV = 10000, 454, 10, 22


def cell(exe, fens, hash_mb, pc20):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    sent = [("Threads", 1), ("Hash", hash_mb)] + list(S14.items())
    sent += PC20_EXTRA if pc20 else [("OwnBook", "false")]
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    walls, depths, nps = [], [], []
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
        d, t, n = 0, 0.0, 0
        for line in out:
            if line.startswith("info depth"):
                f = line.split()
                d = max(d, int(f[f.index("depth") + 1]))
                if "time" in f:
                    t = float(f[f.index("time") + 1])
                if "nodes" in f:
                    n = int(f[f.index("nodes") + 1])
        walls.append((t1 - t0) * 1000.0)
        depths.append(d)
        if t > 0:
            nps.append(n / (t / 1000.0))
    eng.close()
    return walls, depths, nps


def main() -> int:
    exe, pc20 = sys.argv[1], sys.argv[2] == "1"
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print(f"build {'PC20' if pc20 else 'base-settings'}, wtime {WTIME}, soft plan {SOFT} ms, "
          f"{len(fens)} positions, Threads 1")
    print()
    print("| Hash MB | n | median achieved | stop fraction (achieved/soft) | median last depth | "
          "median nps |")
    print("|---|---|---|---|---|---|")
    for hash_mb in (16, 64, 256, 16):
        walls, depths, nps = cell(exe, fens, hash_mb, pc20)
        mw = statistics.median(walls)
        print(f"| {hash_mb} | {len(walls)} | {mw:.1f} | {mw/SOFT:.3f} | "
              f"{statistics.median(depths):.0f} | {statistics.median(nps):.0f} |", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
