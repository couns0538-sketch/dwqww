#!/usr/bin/env python3
"""transition_case.py EXE LABEL OUTDIR — construct the "300 ms then a slow search" transition and see if it flags.

The mechanism claimed in S-F39/S-F40: a side with ~300 ms that hits one p90-sized search (262 ms) loses
200+ ms and lands near 100 ms, where the next p90 move flags.

A flag needs   wall_ms > clock_before + increment(60).
A clock search's wall is bounded by its HARD plan:
    available = clock - 10
    soft      = available/22 + 60*0.75        (increment share)
    hard      = min(available*0.60, soft*5)
and hard <= 0.60 * available.

So the question is arithmetic before it is empirical: can `hard` ever exceed `clock + 60`? If it cannot,
a clock search cannot flag on search time at all, and the "transition" story is wrong — the engine's
survival at low clock would be STRUCTURAL (hard = 60 % of remaining), not adaptive.

This script does both:
  1. tabulates hard vs clock + 60 across the clock range, to show whether a flag is arithmetically possible;
  2. measures, on a deliberately complex middlegame, the real search time at clock 300 / 200 / 150 / 111 ms,
     and reports wall vs clock + 60 for each — the constructed case.

Complex middlegame: a queen-and-rook position with many captures available, chosen so the search has real
work to do (the S-F31 sparse-endgame positions are the *slow* ones, but a middlegame is what the coordinator
asked to force).

Usage: transition_case.py EXE OUTDIR
"""
import os
import statistics
import sys
import time

import chess

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
INC = 60
OVERHEAD, SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT = 10, 22, 75, 60, 5

# Complex middlegames: heavy pieces, open lines, many captures — real search work.
POSITIONS = [
    ("sharp queen+rooks", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8"),
    ("opposite castling", "r1bq1rk1/1pp1bppp/p1np1n2/4p3/2B1P3/2NP1N2/PPP2PPP/R1BQR1K1 w - - 0 8"),
    ("many captures", "r2qkb1r/pp1n1ppp/2p1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7"),
    ("open centre", "r1bqr1k1/pp3ppp/2n2n2/2bp4/8/2NP1N2/PPP1BPPP/R1BQ1RK1 w - - 0 10"),
]


def plan(clock):
    if clock <= OVERHEAD:
        return 0, 0
    avail = clock - OVERHEAD
    soft = avail // SOFT_DIV + INC * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


def probe(exe, fen, clock):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    t0 = time.monotonic()
    eng.send(f"go wtime {int(clock)} btime {int(clock)} winc {INC} binc {INC}")
    out, ok = eng.read_until("bestmove", 40)
    t1 = time.monotonic()
    eng.close()
    depth = 0
    for line in out:
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
    return (t1 - t0) * 1000.0, depth, ok


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    print("## 1. Is a flag arithmetically possible from a clock search?")
    print()
    print("A flag needs wall > clock + 60. A clock search is capped at `hard`, and hard <= 0.60 x available.")
    print()
    print("| clock ms | available | soft plan | hard plan | clock + 60 (flag threshold) | "
          "hard vs threshold | flag possible? |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for clock in (3000, 1000, 500, 300, 200, 150, 111, 60, 30, 10):
        soft, hard = plan(clock)
        thr = clock + INC
        print(f"| {clock} | {max(0, clock-OVERHEAD)} | {soft} | {hard} | {thr} | "
              f"{'BELOW' if hard < thr else 'above'} | {'no' if hard < thr else '**yes**'} |")
        rows.append((clock, hard, thr))

    print()
    print("## 2. The constructed case: complex middlegame at a small clock")
    print()
    print("| position | clock ms | plan hard | measured wall | clock+60 | flagged? | depth |")
    print("|---|---|---|---|---|---|---|")
    any_flag = False
    for name, fen in POSITIONS:
        for clock in (300, 200, 150, 111):
            soft, hard = plan(clock)
            wall, depth, ok = probe(exe, fen, clock)
            flagged = wall > clock + INC
            any_flag = any_flag or flagged
            print(f"| {name} | {clock} | {hard} | {wall:.0f} | {clock + INC} | "
                  f"{'**YES**' if flagged else 'no'} | {depth} |", flush=True)

    print()
    print(f"any constructed case flagged: {any_flag}")
    with open(os.path.join(outdir, "transition.tsv"), "w") as fh:
        fh.write("clock\thard\tthreshold\n")
        for clock, hard, thr in rows:
            fh.write(f"{clock}\t{hard}\t{thr}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
