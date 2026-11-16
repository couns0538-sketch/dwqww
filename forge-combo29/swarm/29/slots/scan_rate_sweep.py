#!/usr/bin/env python3
"""Is the 11.1 % age/depth replacement-scan rate stable across DEPTH and HASH, or is it one configuration's number?

Sweeps a 2x2: depth in {10, 12} x Hash in {16, 64}, under PC20, Threads 1, on the same real-game positions.
A rate that moves with depth or table size is a different claim from "the PC build reaches the replacement path
11 % of the time", and the FINAL figure must say which it is.

Fresh process per cell, drained to `bestmove`, instrumentation prints REPLSTAT at exit.
Aborts if any cell reports 0 probes (a zero rate must be a measurement, not a default).
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def cell(hash_mb, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send(f"setoption name Hash value {hash_mb}")
    send("setoption name Threads value 1")
    for k, v in PC20:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    for fen in FENS[:N]:
        send(f"position fen {fen}")
        send(f"go depth {depth}")
        for line in p.stdout:
            if line.startswith("bestmove"):
                break
    send("quit")
    p.wait(timeout=3600)
    st = [l for l in p.stderr.read().splitlines() if "REPLSTAT" in l]
    if not st:
        raise SystemExit(f"ABORT: no REPLSTAT for Hash {hash_mb} depth {depth}")
    f = st[0].split()
    probes = int(f[f.index("probes") + 1])
    reached = int(f[f.index("repl_reached") + 1])
    empty = int(f[f.index("empty_slot") + 1])
    if probes == 0:
        raise SystemExit(f"ABORT: 0 probes for Hash {hash_mb} depth {depth} -- not a measured zero")
    if reached == 0:
        raise SystemExit(f"ABORT: 0 scans entered for Hash {hash_mb} depth {depth}")
    return probes, reached, empty


print(f"{min(N, len(FENS))} real-game positions, PC20, Threads 1")
print()
print("| Hash | depth | probes | scans entered | found empty | age/depth rate |")
print("|---|---|---|---|---|---|")
for hash_mb in (16, 64):
    for depth in (10, 12):
        probes, reached, empty = cell(hash_mb, depth)
        rate = 100.0 * (reached - empty) / reached
        print(f"| {hash_mb} | {depth} | {probes:,} | {reached:,} | {empty:,} | **{rate:.1f} %** |")
