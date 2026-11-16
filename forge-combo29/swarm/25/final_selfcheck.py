#!/usr/bin/env python3
"""final_selfcheck.py EXE : re-run every LIVE headline claim in my FINAL from scratch.

The FINAL is a document a reader trusts top-down. This script checks that each claim it still presents as live
can be reproduced from the commands it names, so a stale or environment-dependent claim cannot sit in the document.

Covers only the claims that are (a) still live and (b) cheap to re-run. Anything not covered is listed as
NOT RE-CHECKED here, so the output cannot be read as "the whole FINAL is verified".
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
results = []


def claim(name, ok, detail):
    results.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def run(fen, go, mpv=1, hash_mb=16):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    if mpv != 1:
        p.stdin.write(f"setoption name MultiPV value {mpv}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
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
    score = "?"
    if lines:
        m = re.search(r"score (cp|mate) (-?\d+)", lines[-1])
        score = m.group(0) if m else "?"
    n = re.search(r"nodes (\d+)", lines[-1]) if lines else None
    return depth, score, best, (int(n.group(1)) if n else 0), len(lines)


# S-F29: the depth-18 threshold. KQ-vs-K board must NOT report a mate at depth 16 but must at 20.
d16, s16, _, _, _ = run("8/8/8/8/3k4/8/8/K1Q5 w - - 0 1", "go depth 16")
d20, s20, _, _, _ = run("8/8/8/8/3k4/8/8/K1Q5 w - - 0 1", "go depth 20")
claim("S-F29 depth-18 threshold", "cp" in s16 and "mate" in s20 and "mate" not in s16,
      f"depth16 {s16}, depth20 {s20}")

# S-C26: the terminal ladder
_, s_mated, b_mated, n_mated, _ = run("8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1", "go depth 5")
_, s_m1, b_m1, n_m1, _ = run("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "go depth 5")
claim("S-C26 terminal ladder (mate 0/0000 vs mate 1/move)",
      s_mated == "score mate 0" and b_mated == "0000" and n_mated == 0
      and s_m1 == "score mate 1" and b_m1 not in (None, "0000"),
      f"mated: {s_mated}/{b_mated}/{n_mated}n ; mate-in-1: {s_m1}/{b_m1}/{n_m1}n")

# S-C27: the burst is 64 lines and the answer matches go depth 10 on a resolved root
n_burst, s_burst, b_burst, _, lines_burst = run("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "go nodes 50000")
_, s10, b10, _, _ = run("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "go depth 10")
claim("S-C27 burst bounded and answer correct",
      lines_burst == 64 and s_burst == s10 and b_burst == b10,
      f"{lines_burst} lines, {s_burst}/{b_burst} vs depth10 {s10}/{b10}")

# S-C22: Hash 16 ladder stable and multi-PV depth falls with Hash
d16_3, _, _, _, _ = run("rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
                        "go wtime 5000 btime 5000 winc 0 binc 0", mpv=3, hash_mb=16)
d256_3, _, _, _, _ = run("rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
                         "go wtime 5000 btime 5000 winc 0 binc 0", mpv=3, hash_mb=256)
claim("S-C22 Hash-16 ladder above Hash-256 depth", d16_3 > d256_3,
      f"MPV3 clock: Hash16 depth {d16_3}, Hash256 depth {d256_3}")

print()
n = sum(1 for _, ok in results if ok)
print(f"{n}/{len(results)} live headline claims re-checked PASS")
print("NOT RE-CHECKED here: S-F30/S-F31 (full games), S-F25/S-F32 (regime sweeps), S-C12/S-C25 (needs the")
print("variant build), S-C18..20 (needs seat 27's binary). Those have their own committed evidence files.")
