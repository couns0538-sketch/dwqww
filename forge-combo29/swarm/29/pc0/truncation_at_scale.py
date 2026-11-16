#!/usr/bin/env python3
"""Widen 29-C6 (which confirmed seat 05's S-F23 on only TWO boards) by testing the MECHANISM at scale.

S-F23 says PC20 removes the mate-PV truncation that S14 shows. Two boards cannot show that. This scans a whole set
at fixed depth under both regimes and counts, for every position reporting a MATE score, whether its PV is shorter
than the mate requires (2N-1 for N>0, 2|N| for N<0).

If S14 truncates some and PC20 truncates none, the mechanism holds at scale. If both truncate, or neither, 29-C6's
confirmation was board-specific and must be downgraded -- so this test can weaken my own confirmation, and that is
the point of running it.

Threads 1, Hash 16, fresh process per regime, drained to bestmove. Aborts on any missing info or score line.
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 12

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(settings):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    for k, v in settings:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break

    mates = truncated = 0
    bad = []
    for fen in FENS[:N]:
        send(f"position fen {fen}")
        send(f"go depth {DEPTH}")
        last = None
        for line in p.stdout:
            if line.startswith("info depth"):
                last = line.rstrip()
            if line.startswith("bestmove"):
                break
        if last is None:
            raise SystemExit(f"ABORT: no info line for {fen[:40]}")
        f = last.split()
        if "score" not in f:
            raise SystemExit(f"ABORT: no score field for {fen[:40]}")
        i = f.index("score")
        if f[i + 1] != "mate":
            continue
        n = int(f[i + 2])
        need = (2 * n - 1) if n > 0 else 2 * abs(n)
        pv = f[f.index("pv") + 1:] if "pv" in f else []
        mates += 1
        if len(pv) < need:
            truncated += 1
            bad.append((fen, n, len(pv), need))
    send("quit")
    p.wait(timeout=3600)
    return mates, truncated, bad


print(f"{min(N, len(FENS))} positions, depth {DEPTH}, Threads 1, Hash 16")
print()
print("| regime | mate positions | truncated PV | rate |")
print("|---|---|---|---|")
res = {}
for lbl, st in (("S14", S14), ("PC20", PC20)):
    mates, trunc, bad = run(st)
    res[lbl] = (mates, trunc, bad)
    rate = (100.0 * trunc / mates) if mates else 0.0
    print(f"| {lbl} | {mates} | {trunc} | {rate:.1f} % |")

for lbl in ("S14", "PC20"):
    mates, trunc, bad = res[lbl]
    if not mates:
        print(f"\n{lbl}: NO mate scores found -- this set cannot test the mechanism; say so rather than \"0 %\"")
        continue
    if bad:
        print(f"\n{lbl} truncated boards:")
        for fen, n, got, need in bad[:8]:
            print(f"  mate {n}, pv {got}/{need}  {fen}")
