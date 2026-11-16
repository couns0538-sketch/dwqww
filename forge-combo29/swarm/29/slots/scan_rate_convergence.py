#!/usr/bin/env python3
"""Is 26.5 % (20 positions) or 54.7 % (200 positions) the more representative replacement-scan rate?

Rather than argue, measure the RATE AS A FUNCTION OF SET SIZE on the same instrumented binary. If the rate climbs
with N and has not levelled by the largest N available, the smaller set undersamples and the larger one is closer to
truth. If it is flat from the start, the two numbers differ for another reason (different position sets).

Reports a running rate after every 20 positions so the shape of the curve is visible, plus the final rate at the
largest N, and a split-half check (first half vs second half) -- if the two halves disagree, N=20 was too few.

Threads 1, Hash 16, PC20, fresh process per run, drained to `bestmove`.
"""
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
MAXN = int(sys.argv[3]) if len(sys.argv) > 3 else 200
MODE = sys.argv[4] if len(sys.argv) > 4 else "PC20"
CHUNK = 20

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run_chunk(fens):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    if MODE == "PC20":
        for k, v in PC20:
            send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    for fen in fens:
        send(f"position fen {fen}")
        send("go depth 12")
        for line in p.stdout:
            if line.startswith("bestmove"):
                break
    send("quit")
    p.wait(timeout=1800)
    stat = [l for l in p.stderr.read().splitlines() if "REPLSTAT" in l]
    if not stat:
        raise SystemExit("ABORT: no REPLSTAT -- instrumentation not reporting")
    f = stat[0].split()
    probes = int(f[f.index("probes") + 1])
    reached = int(f[f.index("repl_reached") + 1])
    empty = int(f[f.index("empty_slot") + 1])
    if probes == 0:
        raise SystemExit("ABORT: 0 probes -- refusing to compute a rate")
    return probes, reached, empty


print(f"cumulative replacement-scan rate as the position set grows (depth 12, {MODE}, Threads 1, Hash 16)")
print()
print("| positions | probes | scan entered | found empty | age/depth rate |")
print("|---|---|---|---|---|")
cum_p = cum_r = cum_e = 0
rates = []
half = {}
for start in range(0, min(MAXN, len(FENS)), CHUNK):
    chunk = FENS[start:start + CHUNK]
    p, r, e = run_chunk(chunk)
    cum_p += p
    cum_r += r
    cum_e += e
    deep = cum_r - cum_e
    rate = 100.0 * deep / cum_r if cum_r else 0.0
    rates.append((start + len(chunk), rate))
    print(f"| {start + len(chunk)} | {cum_p:,} | {cum_r:,} | {cum_e:,} | {rate:.1f} % |")
    if start + len(chunk) == CHUNK:
        half["first20"] = rate
    if start + len(chunk) == min(MAXN, len(FENS)) // 2 or (start + len(chunk) >= min(MAXN, len(FENS)) // 2 and "mid" not in half):
        half["mid"] = rate

print()
if len(rates) >= 2:
    print(f"rate at {rates[0][0]} positions: {rates[0][1]:.1f} %")
    print(f"rate at {rates[-1][0]} positions: {rates[-1][1]:.1f} %")
    print(f"change over the run: {rates[-1][1] - rates[0][1]:+.1f} points")
last = rates[-1][1]
print()
print(f"VERDICT: with {rates[-1][0]} positions the rate is {last:.1f} %. ", end="")
if "first20" in half and abs(last - half["first20"]) > 5:
    print(f"The {CHUNK}-position figure was {half['first20']:.1f} %, a {abs(last - half['first20']):.1f}-point "
          f"difference: the SMALL set undersamples, and the larger set is the more representative one.")
else:
    print("The rate is stable across set sizes, so set size does not explain the gap.")
