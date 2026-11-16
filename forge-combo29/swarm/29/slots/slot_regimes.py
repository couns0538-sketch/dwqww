#!/usr/bin/env python3
"""Run the slot-instrumented PC build in two regimes and print the slot-hit histogram.

Regimes, both Threads 1 and Hash 16:
  bench13  : the built-in `bench 13` (8 positions)
  R1911    : real-game positions at depth 12 (the PC-relevant workload)

The instrumented binary prints `SLOTSTAT probes N hits M slots a b c d genwrites G` to stderr at exit. Each is
reported as a percentage of HITS, and the harness ABORTS if hits == 0 so a broken run cannot be read as "0 %".
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 200
DEPTH = 12

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def drive(regime):
    fens = [l.strip() for l in open(FENS) if l.strip()][:N]
    src = f'''
import subprocess
p = subprocess.Popen([{EXE!r}], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, bufsize=1)
def send(c):
    p.stdin.write(c + "\\n"); p.stdin.flush()
send("uci")
for line in p.stdout:
    if line.startswith("uciok"): break
send("setoption name Hash value 16"); send("setoption name Threads value 1")
for k, v in {PC20!r}: send(f"setoption name {{k}} value {{v}}")
send("isready")
for line in p.stdout:
    if line.startswith("readyok"): break
if {regime!r} == "bench13":
    send("bench 13")
    for line in p.stdout:
        if line.startswith("info string bench"): break
else:
    for fen in {fens!r}:
        send("position fen " + fen)
        send("go depth {DEPTH}")
        for line in p.stdout:
            if line.startswith("bestmove"): break
send("quit")
p.wait(timeout=1800)
err = p.stderr.read()
print(err)
'''
    path = f"/tmp/_slotdrive_{regime}.py"
    open(path, "w").write(src)
    r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=1800)
    line = [l for l in r.stdout.splitlines() if "SLOTSTAT" in l]
    if not line:
        raise SystemExit(f"ABORT: no SLOTSTAT line for {regime}; stderr was: {r.stderr[-300:]}")
    f = line[0].split()
    probes = int(f[f.index("probes") + 1])
    hits = int(f[f.index("hits") + 1])
    si = f.index("slots")
    slots = [int(f[si + 1]), int(f[si + 2]), int(f[si + 3]), int(f[si + 4])]
    gen = int(f[f.index("genwrites") + 1])
    if hits == 0:
        raise SystemExit(f"ABORT: {regime} recorded 0 hits -- instrumentation not working")
    return probes, hits, slots, gen


print("| regime | probes | hits | slot0 | slot1 | slot2 | slot3 | gen writes |")
print("|---|---|---|---|---|---|---|---|")
for regime in ("bench13", "R1911"):
    probes, hits, slots, gen = drive(regime)
    pct = [100.0 * s / hits for s in slots]
    print(f"| {regime} | {probes:,} | {hits:,} | " + " | ".join(f"{p:.1f} %" for p in pct) +
          f" | {gen:,} ({100.0*gen/hits:.2f} %) |")
