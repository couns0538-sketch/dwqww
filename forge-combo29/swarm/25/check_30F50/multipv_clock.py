#!/usr/bin/env python3
"""multipv_clock.py EXE : how much depth does MultiPV cost on a CLOCK, and does it affect the match path?

S-C21 found that `wtime 5000` + MultiPV 3 returns depth 1-4 while MultiPV 1 reaches 16 on the same clock. That is
either (a) a genuine time-manager fault, or (b) correct behaviour because each extra PV line costs a full search
and the time manager divides the budget. This measures the ladder on a CLOCK at fixed Hash, for MPV 1..4, and asks
the question that decides severity: does it starve to depth 1, or does it degrade gracefully?

It also confirms the owner's match path is unaffected: the matches use MultiPV 1 (default). So this is about
whether enabling MultiPV for analysis would be usable.
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
RUNS = 4


def run(go, mpv, hash_mb=16):
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
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if not lines:
        return 0, 0, 0
    # with MultiPV>1 the last line is for the LAST pv index; take the max depth seen
    best_depth = 0
    for l in lines:
        d = re.search(r"depth (\d+)", l)
        if d:
            best_depth = max(best_depth, int(d.group(1)))
    n = re.search(r"nodes (\d+)", lines[-1])
    return best_depth, (int(n.group(1)) if n else 0), round(ms)


print(f"### MultiPV cost on a clock and on deterministic limits — PC r15/file-5, Threads 1, Hash 16")
print(f"position: {FEN}")
print()
print(f"{'limit':<28} {'MPV':>4} {'depth(s)':>16} {'nodes range':>18} {'ms':>5}")
for go in ("go wtime 5000 btime 5000 winc 0 binc 0", "go depth 12", "go nodes 50000"):
    for mpv in (1, 2, 3, 4):
        rs = [run(go, mpv) for _ in range(RUNS)]
        depths = sorted({r[0] for r in rs})
        nodes = [r[1] for r in rs]
        ms = rs[0][2]
        print(f"{go:<28} {mpv:>4} {str(depths):>16} {str(min(nodes)) + '-' + str(max(nodes)):>18} {ms:>5}")
    print()
