#!/usr/bin/env python3
"""analysis_advice.py EXE : given S-C22/S-C23, what Hash should someone use for MultiPV analysis?

The collapse is clock + MultiPV>1 + large Hash, and the cost is the between-line clear. So the practical question is:
for analysis at MultiPV 3-4, which Hash is safe on a clock? This sweeps Hash at MPV3 on a clock and reports depth
actually reached, so the answer is a measured recommendation rather than "use a small Hash".

Also checks the deterministic-limit case, where Hash should be free - if `go depth 20` at MPV3 is fine at Hash 256
then the advice is "on a clock, keep Hash small; for deep single-shot analysis, Hash is fine".
"""
import re
import shlex
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"


def run(go, mpv, hash_mb):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name MultiPV value {mpv}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    depth = 0
    for l in lines:
        d = re.search(r"depth (\d+)", l)
        if d:
            depth = max(depth, int(d.group(1)))
    n = re.search(r"nodes (\d+)", lines[-1]) if lines else None
    return depth, (int(n.group(1)) if n else 0), round(ms)


print("### what Hash to use for MultiPV analysis — PC r15/file-5, Threads 1, PC20")
print()
print("ON A CLOCK (go wtime 5000), MPV3 — depth actually reached:")
print(f"{'Hash':>6} {'depth':>6} {'nodes':>8} {'ms':>6}   verdict")
for h in (16, 32, 64, 128, 256, 512):
    d, n, ms = run("go wtime 5000 btime 5000 winc 0 binc 0", 3, h)
    verdict = "fine" if d >= 11 else ("degraded" if d >= 7 else "COLLAPSED")
    print(f"{h:>6} {d:>6} {n:>8} {ms:>6}   {verdict}")
print()
print("WITH A DEPTH LIMIT (go depth 20), MPV3 — depth should be reached regardless of Hash:")
print(f"{'Hash':>6} {'depth':>6} {'nodes':>9} {'ms':>7}")
for h in (16, 64, 256):
    d, n, ms = run("go depth 20", 3, h)
    print(f"{h:>6} {d:>6} {n:>9} {ms:>7}")
