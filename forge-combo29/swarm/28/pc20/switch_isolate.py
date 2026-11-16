#!/usr/bin/env python3
"""switch_isolate.py EXE — which PC20 switch shortens each iteration?

The stop fraction difference is now characterised: at wtime 10000 the base build finishes 20 iterations
with the last costing 98 ms and stops at 0.764 of soft; the PC build finishes 19 iterations with the last
costing 60 ms and stops at 0.623. Both builds share the SAME soft plan (454 ms) and the SAME byte-identical
timing code. So the difference is that PC20's iterations are individually CHEAPER and there are FEWER of
them — which is what a pruning/ordering change does, not a time-manager change.

This script isolates which of the five PC20 switches causes it, by running the same cell five times on the
PC build: PC20 with all switches, then with each switch turned off in turn. If turning one switch off
restores 20 iterations and a ~0.76 stop fraction, that switch is the cause.

Usage: switch_isolate.py EXE [NPOS]
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
FULL = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
OFF_VALUE = {"CuckooRep": "false", "HistRework": "0", "TtPruneV2": "false",
             "CorrHistV2": "false", "MateAlphaGuard": "false"}
WTIME, SOFT = 10000, 454


def cell(exe, fens, overrides):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    extra = []
    for k, v in FULL:
        extra.append((k, overrides.get(k, v)))
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items()) + extra
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
        if seq:
            rows.append({"wall": (t1 - t0) * 1000.0, "n_iter": len(seq), "last_t": seq[-1][1],
                         "last_depth": seq[-1][0]})
    eng.close()
    return rows


def main() -> int:
    exe = sys.argv[1]
    npos = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print(f"PC r15, wtime {WTIME}, soft {SOFT} ms, {len(fens)} positions, Threads 1, one switch off at a time")
    print()
    print("| configuration | n | median achieved | achieved/soft | median #iter | median last depth |")
    print("|---|---|---|---|---|---|")
    configs = [("PC20 (all on)", {})]
    for k in OFF_VALUE:
        configs.append((f"{k} off", {k: OFF_VALUE[k]}))
    for label, overrides in configs:
        rows = cell(exe, fens, overrides)
        if not rows:
            print(f"| {label} | 0 | - | - | - | - |")
            continue
        mw = statistics.median([r["wall"] for r in rows])
        print(f"| {label} | {len(rows)} | {mw:.1f} | {mw/SOFT:.3f} | "
              f"{statistics.median([r['n_iter'] for r in rows]):.0f} | "
              f"{statistics.median([r['last_depth'] for r in rows]):.0f} |", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
