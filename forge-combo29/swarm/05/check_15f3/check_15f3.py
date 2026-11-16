#!/usr/bin/env python3
"""check_15f3.py EXE -- my own check of seat 15's finding 15-F3, written from its one-sentence claim only:
"With S14 (DeadMaterial off) the engine scores KNN v K as a win — 19 of 20 such positions at depth 10 report
cp 147…309 — although KNN v K cannot be won by force; setting `DeadMaterial true` makes all 20 report cp 0".

I use MY OWN 20 KNN v K positions (positions/KNNvK.epd from job2, seed 501), not theirs, and my own harness.
Controls, both required before any CONFIRMS:
  C1  the same 20 positions with `DeadMaterial true` -> all cp 0?  (their claim's second half)
  C2  my harness CAN see a change: K+Q v K with DeadMaterial true still reports a non-zero score
      (i.e. turning it on does not simply zero every position)
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
DEPTH = 10
BASE = ["setoption name Threads value 1", "setoption name Hash value 16"]
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]
DEADMAT_TRUE = ["setoption name DeadMaterial value true"]
DEADMAT_FALSE = ["setoption name DeadMaterial value false"]


def search(fen, extra):
    """live process, read to bestmove (19-F12 discipline)"""
    opts = BASE + S14 + extra
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in opts:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {DEPTH}")
    bad = False
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            bad = True
            out.append("### HARNESS_STOP")
            break
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    if bad:
        return None, "HARNESS_STOP"
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None, "NO_PV_LINE"        # an absent parse must never be read as a score
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    if not m:
        return None, "NO_SCORE_MATCH"
    return (m.group(1), int(m.group(2))), pv[-1]


def load(path):
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]


knn = load("../job2/positions/KNNvK.epd")
print(f"exe: {EXE}   go depth {DEPTH}   S14 + Threads 1 + Hash 16")
print(f"KNN v K positions: {len(knn)} (MY OWN set from job2, seed 501 — not seat 15's)")
print()

fails = []


def need(cond, msg):
    if not cond:
        fails.append(msg)
        print(f"  !! FAIL-LOUD: {msg}")
    return cond


print("=== part 1: DeadMaterial OFF (engine default; S14 does not set it)")
off = []
for i, fen in enumerate(knn):
    sc, raw = search(fen, DEADMAT_FALSE)
    need(sc is not None, f"DeadMaterial off, pos {i}: {raw} -- no score could be parsed")
    off.append(sc)
    print(f"  pos {i:2d} {sc[0] if sc else '?':5s} {sc[1] if sc else '?':>6}   {fen}")

print()
print("=== part 2: DeadMaterial TRUE")
on = []
for i, fen in enumerate(knn):
    sc, raw = search(fen, DEADMAT_TRUE)
    need(sc is not None, f"DeadMaterial true, pos {i}: {raw} -- no score could be parsed")
    on.append(sc)
    print(f"  pos {i:2d} {sc[0] if sc else '?':5s} {sc[1] if sc else '?':>6}   {fen}")

print()
nonzero_off = [s for s in off if s and s[0] == "cp" and s[1] != 0]
mate_off = [s for s in off if s and s[0] == "mate"]
allzero_on = all(s and s[0] == "cp" and s[1] == 0 for s in on)
print(f"OFF: non-zero cp scores: {len(nonzero_off)}/{len(off)}   mate scores: {len(mate_off)}")
vals = sorted(s[1] for s in nonzero_off)
if vals:
    print(f"OFF: range of the non-zero cp scores: {vals[0]} .. {vals[-1]}   (seat 15 claims 147..309 for 19 of 20)")
print(f"ON : all exactly cp 0? {allzero_on}  ({sum(1 for s in on if s and s[0]=='cp' and s[1]==0)}/{len(on)} are cp 0)")

print()
print("=== CONTROL C2: does DeadMaterial true zero EVERY position, or only dead ones?")
print("    (K+Q v K is a WIN, so a correct DeadMaterial switch must NOT zero it)")
kq = load("../job2/positions/fifty0.epd")[:5]
kq_scores = []
for fen in kq:
    sc, raw = search(fen, DEADMAT_TRUE)
    need(sc is not None, f"control K+Q v K: {raw}")
    kq_scores.append(sc)
    print(f"  {sc[0] if sc else '?':5s} {sc[1] if sc else '?':>6}   {fen}")
control_ok = all(s and not (s[0] == "cp" and s[1] == 0) for s in kq_scores)
print(f"  control C2 (K+Q v K stays non-zero with DeadMaterial true): {control_ok}")
need(control_ok, "control C2 failed: DeadMaterial true zeroed a winning K+Q v K position")

print()
print("=" * 90)
print(f"their claim part 1: KNN v K non-zero with DeadMaterial off -> "
      f"{'MATCHES' if len(nonzero_off) >= 15 else 'DOES NOT MATCH'} ({len(nonzero_off)}/{len(off)} non-zero; "
      f"they said 19 of 20)")
print(f"their claim part 2: all cp 0 with DeadMaterial true    -> "
      f"{'MATCHES' if allzero_on else 'DOES NOT MATCH'}")
if vals:
    in_range = all(100 <= v <= 400 for v in vals)
    print(f"their claimed range 147..309 vs my range {vals[0]}..{vals[-1]}: "
          f"{'same ballpark' if in_range else 'DIFFERENT'}")
print()
if fails:
    print(f"RESULT: {len(fails)} ASSERTION FAILURE(S) — do not record a verdict from this run")
    for f_ in fails:
        print("  -", f_)
    sys.exit(1)
print("RESULT: every parse asserted; both controls passed; the comparison above is a measurement.")
