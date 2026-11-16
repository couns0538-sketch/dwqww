#!/usr/bin/env python3
"""check_30F50.py EXE : is seat 30's F50 instability caused by MultiPV, or by the CLOCK in their command?

Seat 30's claim: on identical runs at MultiPV 3, the shipped build gives different answers (Hash 256: depths {7,11},
nodes 5,395-47,818 = 8.9x) while their patched build is exact. Their command is `go wtime 5000` - a CLOCK.

My S-C15 already established that a clock-based search is NOT reproducible in score, nodes or depth (only the move),
because the stop is wall-clock dependent. So their instability may be entirely explained by the clock, with nothing
to do with MultiPV - in which case the "patched build is exact" half would need explaining instead.

Test: run their exact cells, and the same cells with `go depth` or `go nodes` (deterministic search limits) at
MultiPV 3. If the spread appears ONLY with the clock, the cause is the clock and the finding's framing is wrong.
If it appears with deterministic limits too, MultiPV is implicated and their claim stands.
"""
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
RUNS = 6


def run(go, hash_mb, multipv):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name MultiPV value {multipv}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
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
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if not lines:
        return 0, 0
    d = re.search(r"depth (\d+)", lines[-1])
    n = re.search(r"nodes (\d+)", lines[-1])
    return (int(d.group(1)) if d else 0), (int(n.group(1)) if n else 0)


CASES = [
    ("their cell: wtime 5000, MPV3, Hash 256", "go wtime 5000 btime 5000 winc 0 binc 0", 256, 3),
    ("CONTROL same but go nodes 50000", "go nodes 50000", 256, 3),
    ("CONTROL same but go depth 12", "go depth 12", 256, 3),
    ("their cell: wtime 5000, MPV1, Hash 256", "go wtime 5000 btime 5000 winc 0 binc 0", 256, 1),
    ("CONTROL MPV1 go depth 12", "go depth 12", 256, 1),
]
print(f"### is 30-F50's instability MultiPV, or the CLOCK? ({RUNS} fresh runs each)")
print(f"PC r15/file-5 build: {EXE}")
print()
for label, go, h, mpv in CASES:
    res = [run(go, h, mpv) for _ in range(RUNS)]
    depths = [r[0] for r in res]
    nodes = [r[1] for r in res]
    spread = (max(nodes) / min(nodes)) if min(nodes) > 0 else 0
    print(f"{label:<42} depths {sorted(set(depths))} nodes {min(nodes)}-{max(nodes)} spread {spread:.1f}x")
