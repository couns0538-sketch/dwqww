"""check_08F9.py EXE OUTDIR : independent check of seat 08's 08-F9, second attempt.

FIRST ATTEMPT WAS WRONG AND IS RECORDED AS SUCH (raw_v1_vacuous/): I searched the engine's output for a
`clock_plan` line to learn the planned soft limit. The engine prints no such line, so `soft` was None, the
usage ratio was NaN, and my `0.50 <= usage <= 0.85` test passed VACUOUSLY on NaN — it "CONFIRMED" a claim it
had not measured. That is exactly the vacuity Opus's Rule 1 warns about, in my own harness. This version
computes the planned soft limit from the source instead, and refuses to return a verdict if the plan is
missing.

Planned soft limit, from include/forge/clock_plan.hpp + the defaults in src/search.cpp:
    available = wtime - Move Overhead            (overhead 10 by default)
    movestogo M > 0:  soft = available/(min(M,50)+1) + winc*3/4
    no movestogo:     soft = available/TmSoftDivisor(22) + winc*TmIncrementPercent(75)/100
Then 08-F9's claim is that measured wall time is only 55-79 % of that soft number, because a per-iteration
`factor` (floor TmMinFactorPercent 45 %) multiplies the deadline.

Verdict rule, fixed BEFORE running this version:
  CONFIRMS if every case's measured median is between 0.50 and 0.85 of its computed soft limit, AND all
  cases produce a computed soft limit > 0, AND 0 bestmoves are missing.
  REFUTES if any case falls outside [0.50, 0.85] — and the output says which.
  INCONCLUSIVE (never a pass) if any soft limit comes out <= 0 or any bestmove is missing.
"""
import os
import statistics
import subprocess
import sys
import time

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

OVERHEAD = 10
TM_SOFT_DIVISOR = 22
TM_INCREMENT_PERCENT = 75

CASES = [
    ("wtime 1000 movestogo 1", 1000, 0, 1),
    ("wtime 1000 movestogo 2", 1000, 0, 2),
    ("wtime 1000 movestogo 40", 1000, 0, 40),
    ("wtime 1000 no movestogo", 1000, 0, 0),
]
POS = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
REPS = 7


def planned_soft(wtime, winc, mtg):
    available = wtime - OVERHEAD
    if available <= 0:
        return 0
    if mtg > 0:
        return available // (min(mtg, 50) + 1) + winc * 3 // 4
    return available // TM_SOFT_DIVISOR + winc * TM_INCREMENT_PERCENT // 100


def run_go(go):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    proc.stdin.write("uci\nisready\nsetoption name OwnBook value false\nisready\n" + POS + "\nisready\n")
    proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        if not line or line.strip() == "readyok":
            break
    t0 = time.monotonic()
    proc.stdin.write(go + "\n")
    proc.stdin.flush()
    got_best = False
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if line.startswith("bestmove"):
            got_best = True
            break
    t1 = time.monotonic()
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    return (t1 - t0) * 1000.0, got_best


rows = []
raw = open(os.path.join(outdir, "raw_all.txt"), "w")
missing = 0
for label, wt, wi, mtg in CASES:
    go = "go wtime %d btime %d winc %d binc %d" % (wt, wt, wi, wi)
    if mtg:
        go += " movestogo %d" % mtg
    times, bests = [], []
    for _ in range(REPS):
        ms, got = run_go(go)
        times.append(ms)
        bests.append(got)
        raw.write("%s | %.2f ms | bestmove seen %s\n" % (label, ms, got))
    missing += sum(1 for b in bests if not b)
    rows.append((label, times, planned_soft(wt, wi, mtg)))
raw.close()

lines = ["| case | computed soft ms | median ms | min | max | usage | in [0.50,0.85] |",
         "|---|---|---|---|---|---|---|"]
all_in_band = True
soft_ok = True
for label, times, soft in rows:
    med = statistics.median(times)
    if soft <= 0:
        soft_ok = False
        lines.append("| %s | 0 | %.1f | %.1f | %.1f | n/a | NO |" % (label, med, min(times), max(times)))
        continue
    usage = med / soft
    inband = 0.50 <= usage <= 0.85
    all_in_band = all_in_band and inband
    lines.append("| %s | %d | %.1f | %.1f | %.1f | %.1f %% | %s |"
                 % (label, soft, med, min(times), max(times), 100 * usage, "yes" if inband else "NO"))

if not soft_ok or missing:
    verdict = "INCONCLUSIVE"
elif all_in_band:
    verdict = "CONFIRMS"
else:
    verdict = "REFUTES"

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("exe: %s\nreps per case: %d\n\n" % (os.path.abspath(exe), REPS))
    fh.write("\n".join(lines) + "\n\n")
    fh.write("bestmoves missing: %d\n" % missing)
    fh.write("soft limits all computed > 0: %s\n" % soft_ok)
    fh.write("verdict rule (fixed beforehand): CONFIRMS iff every usage in [0.50,0.85] and no missing data\n")
    fh.write("\nVERDICT %s 08-F9\n" % verdict)
print(open(os.path.join(outdir, "RESULT.txt")).read())
