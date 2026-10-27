#!/usr/bin/env python3
"""A2 NPS ESTIMATE for king-bucket layouts: a one-parameter cost model calibrated on C4's measured lock replicas.

usage: a2_nps_estimate.py <kbstats_raw.log>

Inputs
  * Refresh counts per layout on the lock's own bench tree, from this job's microbench (kbstats_raw.log, the
    `a2kb total depth D` lines): xp = replayed plies whose mover's king key changes = the perspective refreshes
    of C4's engine, which replays ply by ply and refreshes a perspective through its refresh cache at every key
    change.
  * Measured CPU-time NPS changes of C4's engine vs the AL1 lock exe, same tree (node counts equal on every run),
    10 ABBA runs per depth on the loaded PC (opus-C4 23750a76, opus_round1/C4/REPORT.md, table "5. NPS",
    lines 163-166):
        r1   (v2 code path, 1 bucket, never refreshes):   d16 -1.31%  d20 -1.60%
        rm8  (refreshes exactly like M4 = U8, 8 blocks):    d16 -5.33%  d20 -4.13%
        rm16 (refreshes exactly like M8 = U16, 16 blocks):  d16 -8.94%  d20 -6.65%
Model (ESTIMATE)
  loss(L, d) = loss(r1, d) + beta * xp(L, d) / (nodes(d) / 1000)
  beta (% NPS per refresh per 1000 nodes) is fitted at each calibration point: (loss(rm) - loss(r1)) / rate(rm).
  The point estimate uses the mean beta of rm8 and rm16 at the same depth; the range uses the smallest and the
  largest beta of all four calibration points. Not modelled: weight blocks beyond 16 (the calibration nets hold
  6 and 12 MiB of float weights; 24-48 MiB layouts may lose more to cache misses), the hidden layers of a full
  NNUE, and a different tree searched by a differently trained net.
"""
import re
import sys

MEASURED = {  # depth -> (r1, rm8, rm16) CPU-time NPS change in %, C4 REPORT.md lines 164-166
    16: (-1.31, -5.33, -8.94),
    20: (-1.60, -4.13, -6.65),
}
CAL = {"rm8": "M4=U8", "rm16": "M8=U16"}


def parse(path):
    tot = {}
    rx_h = re.compile(r"a2kb total depth (\d+) nodes (\d+) ")
    rx_l = re.compile(r"a2kb total depth (\d+) layout (\S+) keys (\d+) xm (\d+) xp (\d+) xe (\d+)")
    for line in open(path, encoding="ascii"):
        m = rx_h.search(line)
        if m:
            tot.setdefault(int(m.group(1)), {})["nodes"] = int(m.group(2))
        m = rx_l.search(line)
        if m:
            tot.setdefault(int(m.group(1)), {})[m.group(2)] = (int(m.group(5)), int(m.group(6)))
    return tot


def main():
    tot = parse(sys.argv[1])
    betas = {}
    print("Calibration (xp per 1000 nodes from kbstats_raw.log; losses from C4 REPORT.md):\n")
    print("| depth | replica = layout | xp per 1000 nodes | measured loss | minus r1 | beta (% per refresh/1000 nodes) "
          "| implied time per refresh at 1/NPS = 513 ns per node |")
    print("|---|---|---|---|---|---|---|")
    for d, (r1, rm8, rm16) in MEASURED.items():
        nodes = tot[d]["nodes"]
        for rep, loss in (("rm8", rm8), ("rm16", rm16)):
            rate = tot[d][CAL[rep]][0] / (nodes / 1000)
            beta = (loss - r1) / rate
            betas[(d, rep)] = beta
            # 1.95M nps (C4 report, OFF bench d20 1949230 nps) -> 513 ns per node
            print(f"| {d} | {rep} = {CAL[rep]} | {rate:.2f} | {loss:+.2f}% | {loss - r1:+.2f}% | {-beta:.4f} "
                  f"| {-beta / 100 * 1000 * 513:.0f} ns |")
    lo, hi = min(betas.values()), max(betas.values())
    print(f"\nbeta range over the 4 points: {-hi:.4f} .. {-lo:.4f} % per (refresh per 1000 nodes)\n")
    print("ESTIMATE of the NPS change vs the AL1 lock (same tree, C4-style engine, Threads 1), per layout:\n")
    print("| layout | weight blocks (M / U) | d16 xp/1000 nodes | d16 ESTIMATE (range) | d20 xp/1000 nodes | d20 ESTIMATE (range) |")
    print("|---|---|---|---|---|---|")
    blocks = {"M1": "1 / 2", "M2=U4": "2 / 4", "M4=U8": "4 / 8", "M8=U16": "8 / 16", "M16=U32": "16 / 32",
              "M32=U64": "32 / 64", "R4": "4", "R8": "8"}
    for name in blocks:
        cells = []
        for d in (16, 20):
            nodes = tot[d]["nodes"]
            rate = tot[d][name][0] / (nodes / 1000)
            r1 = MEASURED[d][0]
            mid = r1 + rate * (betas[(d, "rm8")] + betas[(d, "rm16")]) / 2
            a, b = r1 + rate * hi, r1 + rate * lo
            cells.append(f"{rate:.2f} | {mid:+.1f}% ({max(a, b):+.1f} .. {min(a, b):+.1f})")
        print(f"| {name} | {blocks[name]} | " + " | ".join(cells) + " |")
    print("\n(M1 = mirroring alone, one weight block: refreshes only when the king crosses files d/e.)")


if __name__ == "__main__":
    main()
