#!/usr/bin/env python3
"""CHECK of seat 05's S-F23, with a harness of my own built from their stated method.

S-F23 claims: on the PC r15 build, depth 12, Threads 1, the mate-PV truncation rate is 0 of 27 under PC20 but
2 of 28 = 7.1 % under S14 -- the same two boards as the base tree -- and the position that stops being a mate
score under PC20 is R/120 (cp -2713).

Method (mine, not a copy of their script): for every position in a set, run `go depth 12` with a fresh process
(drained to `bestmove`, so nothing is aborted), take the LAST `info depth` line, and classify it:
  - a MATE score is `score mate N`
  - of those, a PV is TRUNCATED when the number of moves in `pv` is fewer than 2N-1 (N>0) or 2|N| (N<0)
Then compare the truncated/total rate under S14 and under PC20 on the same build and the same positions.

Guards: a run that produces no `info depth` line aborts (never counted as "clean"); every option name is checked
against the exe's list; `unknown option`/`invalid value`/`ERROR` aborts.
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
DEPTH = 12

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")


def options():
    out = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True).stdout
    return {l[len("option name "):].split(" type ")[0]
            for l in out.splitlines() if l.startswith("option name ")}


def search(fen, settings):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    for k, v in settings:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        for b in BAD:
            if b in line:
                raise SystemExit(f"ABORT: {line.strip()}")
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(f"go depth {DEPTH}")
    last = None
    for line in p.stdout:
        if line.startswith("info depth"):
            last = line.rstrip()
        if line.startswith("bestmove"):
            break
    send("quit")
    p.wait(timeout=60)
    if last is None:
        raise SystemExit(f"ABORT: no info line for {fen} -- refusing to classify it")
    return last


def classify(info):
    f = info.split()
    if "score" not in f:
        return None
    i = f.index("score")
    kind = f[i + 1]
    if kind != "mate":
        return ("cp", None, None)
    n = int(f[i + 2])
    needed = (2 * n - 1) if n > 0 else (2 * abs(n))
    pv = f[f.index("pv") + 1:] if "pv" in f else []
    return ("mate", n, len(pv) < needed)


opts = options()
need = {k for k, _ in PC20}
missing = need - opts
if missing:
    raise SystemExit(f"ABORT: exe does not list {sorted(missing)} -- wrong build?")

for label, settings in (("S14", S14), ("PC20", PC20)):
    mates = trunc = 0
    trunc_boards = []
    for i, fen in enumerate(FENS, 1):
        info = search(fen, settings)
        c = classify(info)
        if c and c[0] == "mate":
            mates += 1
            if c[2]:
                trunc += 1
                trunc_boards.append((i, fen, c[1], info))
    print(f"\n=== {label}: {trunc} of {mates} mate positions truncated")
    for i, fen, n, info in trunc_boards:
        print(f"   pos {i} mate {n}: {fen}")
        print(f"      {info[:150]}")

print("\nseat 05 S-F23 claims: PC20 0 of 27 ; S14 2 of 28 (7.1 %), and R/120 stops being a mate score under PC20.")
