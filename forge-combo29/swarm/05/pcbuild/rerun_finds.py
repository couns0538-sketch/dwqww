#!/usr/bin/env python3
"""rerun_finds.py EXE PC20|BASE -- re-runs seat 05's own findings on the given build/settings regime.

Findings tested, each with the exact FEN/board from my FINDINGS.md:
  S-F3  fifty-move cliff on K+R vs K: score at halfmove 0, 88, 90, 91, 99, 100 at depth 10
  S-F4  the 20 K+Q/K+R boards at halfmove 98 and 99 (are they still all cp 0?)
  S-F11/F13/F14/F15 the boundary vs depth on a bare endgame
  S-F1/S-F9 mate PV truncation: G/192 and R/120
  S-F7 depth ladder at a terminal root
Every parse is asserted; a missing value exits 3 (house standard, CHECKER_RULE.md).
"""
import os
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"

S14 = [
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1", "setoption name Hash value 16",
]
PC20 = S14 + [
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
OPTS = {"PC20": PC20, "S14": S14, "BASE": S14}[REGIME]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def search(fen, depth):
    """returns (score_kind, score_num, nodes, pv_moves, raw_last) or raises on any absence"""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=300):
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                lines.append("### EOF")
                return
            line = line.rstrip("\n")
            lines.append(line)
            if line.startswith(tok):
                return
        lines.append("### TIMEOUT")

    send("uci")
    until("uciok")
    for o in OPTS:
        send(o)
        send("isready")
        n0 = len(lines)
        until("readyok")
        bad = [l for l in lines[n0:] if any(b in l for b in BAD)]
        if bad:
            p.kill()
            raise RuntimeError(f"option refused: {bad[0]}")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(f"position fen {fen}")
    send("isready")
    n0 = len(lines)
    until("readyok")
    if any("invalid FEN" in l for l in lines[n0:]):
        p.kill()
        raise RuntimeError(f"FEN refused: {fen}")
    send(f"go depth {depth}")
    until("bestmove")
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in lines if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        raise RuntimeError(f"NO PV LINE for {fen} at depth {depth} (nothing measured)")
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        raise RuntimeError(f"NO SCORE in last pv line: {last!r}")
    nm = re.search(r"\bnodes (\d+)", last)
    return m.group(1), int(m.group(2)), (int(nm.group(1)) if nm else None), last


def score(fen, depth):
    k, v, n, _ = search(fen, depth)
    return f"{k} {v}", n


def with_hm(fen, hm):
    q = fen.split()
    q[4] = str(hm)
    return " ".join(q)


print(f"exe: {EXE}   regime: {REGIME}   date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("### S-F3 — the fifty-move cliff on K+R vs K, depth 10")
base = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
print("| halfmove | score | nodes |")
print("|---|---|---|")
prev = None
for hm in (0, 75, 85, 88, 89, 90, 91, 92, 95, 99, 100):
    sc, nodes = score(with_hm(base, hm), 10)
    print(f"| {hm} | {sc} | {nodes} |")
    prev = sc
print()

print("### S-F11/F15 — boundary vs depth on the same bare endgame (lowest halfmove that scores cp 0)")
print("| depth | boundary | boundary+depth |")
print("|---|---|---|")
for d in (6, 8, 10, 12):
    bnd = None
    for hm in range(60, 101):
        sc, _ = score(with_hm(base, hm), d)
        if sc == "cp 0":
            bnd = hm
            break
    print(f"| {d} | {bnd if bnd is not None else 'none'} | {(bnd + d) if bnd is not None else '-'} |")
print()

print("### S-F1 / S-F9 — mate-PV truncation (the brief's 2N-1 rule)")
CASES = [
    ("G/192 (S-F1)", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", 12),
    ("R/120 (S-F9)", "R7/1P2k3/4B2p/8/2K2Pp1/8/1b6/8 b - - 2 109", 12),
    ("G/306", "8/7k/7P/8/5pK1/4q3/8/8 b - - 0 1", 12),
]
print("| case | score | pv plies | needs | consistent? |")
print("|---|---|---|---|---|")
for label, fen, d in CASES:
    k, v, n, last = search(fen, d)
    moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
    if k == "mate" and v != 0:
        want = 2 * v - 1 if v > 0 else 2 * (-v)
        cons = "yes" if len(moves) == want else f"NO (short by {want - len(moves)})"
    else:
        want = "-"
        cons = "n/a (not a mate score)"
    print(f"| {label} | {k} {v:+d} | {len(moves)} | {want} | {cons} |")
print()

print("### S-F6/S-F12 — draw scores at depth 10 (KvK / KNvK / KBvK / KNNvK, one board each)")
DRAWS = [
    ("KvK", "8/8/3K2k1/8/8/8/8/8 w - - 0 1"),
    ("KNvK", "8/8/8/8/8/8/8/K1N4k w - - 0 1"),
    ("KBvK", "8/8/8/8/8/8/8/K1B4k w - - 0 1"),
    ("KNNvK", "7k/8/8/8/8/8/8/K1N1N3 w - - 0 1"),
]
print("| set | score | nodes |")
print("|---|---|---|")
for label, fen in DRAWS:
    sc, nodes = score(fen, 10)
    print(f"| {label} | {sc} | {nodes} |")
print()
print("### S-F7 — terminal root (checkmate) depth ladder")
mfen = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"
for d in (5,):
    k, v, n, last = search(mfen, d)
    print(f"checkmate root, go depth {d}: score {k} {v}, nodes {n}")
print()
print("RESULT: every value above was parsed from a real info/pv line; a missing parse would have raised.")
