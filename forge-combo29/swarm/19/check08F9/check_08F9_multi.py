"""check_08F9_multi.py EXE FENS OUTDIR : 08-F9 across MANY positions, not one.

The single-position version of this check (raw2/) gave 52.3 %, 50.6 %, 85.9 % and 169.8 % of the computed
soft limit — two cases outside 08-F9's "55-79 %" band, one far above. But seat 08 measured 200 positions and
I measured one, so that comparison was not like-for-like. This version uses 100 positions from the R_1911
set, so the distribution of usage is visible and the band can be judged properly.

For each position and each of four clock settings: send `go ...`, read to `bestmove`, and record measured
wall ms over the computed soft limit. Report per case: median, p10, p90, and the fraction of searches whose
usage falls inside [0.50, 0.85].

Verdict rule, fixed BEFORE running:
  CONFIRMS if, for EVERY case, the MEDIAN usage is inside [0.50, 0.85].
  REFUTES if any case's median usage is outside that band.
  (The median is the right statistic for their claim, which is about typical behaviour, not the extremes;
  their own text quotes medians 329.09 / 217.09 / 18.84 / 34.56.)
"""
import os
import statistics
import subprocess
import sys
import time

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

OVERHEAD = 10
CASES = [("movestogo 1", 0, 1), ("movestogo 2", 0, 2), ("movestogo 40", 0, 40), ("no movestogo", 0, 0)]
WTIME = 1000
positions = [l.strip() for l in open(fens) if l.strip()][:100]


def planned_soft(mtg):
    available = WTIME - OVERHEAD
    if mtg > 0:
        return available // (min(mtg, 50) + 1)
    return available // 22


proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)


def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_to_bestmove():
    while True:
        line = proc.stdout.readline()
        if not line:
            return False
        if line.startswith("bestmove"):
            return True


send("uci")
while proc.stdout.readline().strip() != "uciok":
    pass
send("isready")
while proc.stdout.readline().strip() != "readyok":
    pass
send("setoption name OwnBook value false")
send("isready")
while proc.stdout.readline().strip() != "readyok":
    pass

results = {}
missing = 0
for label, winc, mtg in CASES:
    go = "go wtime %d btime %d winc %d binc %d" % (WTIME, WTIME, winc, winc)
    if mtg:
        go += " movestogo %d" % mtg
    usages = []
    for fen in positions:
        send("position fen " + fen)
        send("isready")
        while proc.stdout.readline().strip() != "readyok":
            pass
        t0 = time.monotonic()
        send(go)
        ok = read_to_bestmove()
        t1 = time.monotonic()
        if not ok:
            missing += 1
            break
        soft = planned_soft(mtg)
        usages.append((t1 - t0) * 1000.0 / soft)
    results[label] = (usages, planned_soft(mtg))

send("quit")
try:
    proc.communicate(timeout=60)
except subprocess.TimeoutExpired:
    proc.kill()

lines = ["| case | computed soft ms | n | median usage | p10 | p90 | share in [0.50,0.85] |",
         "|---|---|---|---|---|---|---|"]
medians_ok = True
for label, (usages, soft) in results.items():
    if not usages:
        medians_ok = False
        lines.append("| %s | %d | 0 | n/a | n/a | n/a | n/a |" % (label, soft))
        continue
    u = sorted(usages)
    med = statistics.median(u)
    p10 = u[max(0, int(0.10 * len(u)) - 1)]
    p90 = u[min(len(u) - 1, int(0.90 * len(u)))]
    inband = sum(1 for x in u if 0.50 <= x <= 0.85) / len(u)
    if not (0.50 <= med <= 0.85):
        medians_ok = False
    lines.append("| %s | %d | %d | %.1f %% | %.1f %% | %.1f %% | %.0f %% |"
                 % (label, soft, len(u), 100 * med, 100 * p10, 100 * p90, 100 * inband))

verdict = "INCONCLUSIVE" if missing or not results else ("CONFIRMS" if medians_ok else "REFUTES")
with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("exe: %s\npositions: %d from %s\nwtime %d, winc 0, Move Overhead %d\n\n"
             % (os.path.abspath(exe), len(positions), fens, WTIME, OVERHEAD))
    fh.write("\n".join(lines) + "\n\n")
    fh.write("bestmoves missing: %d\n" % missing)
    fh.write("verdict rule (fixed beforehand): CONFIRMS iff every case's MEDIAN usage is in [0.50,0.85]\n")
    fh.write("\nVERDICT %s 08-F9\n" % verdict)
print(open(os.path.join(outdir, "RESULT.txt")).read())
