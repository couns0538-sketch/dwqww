#!/usr/bin/env python3
"""dtm_compare.py FENS SOLVER_OUT OUTDIR EXE : the engine's DTM versus the best available DTM, per position.

Reads the per-position DTM tables that `dtm_oracle.py` produced, asks the engine (PC r15, PC20, Threads 1,
Hash 16, cold) for its move at depth 16 and at `go nodes 20000`, and compares:

    engine DTM   -- the true DTM of the position after the engine's move
    best DTM     -- the smallest DTM over all legal moves

A position is a DEFECT when the engine's DTM is strictly worse than the best available, i.e. it reaches a mate
in more plies than it could have. "draw/unsolved" on the engine's move while a mate exists is a worse defect.

This is the upgrade over 19-F54: 19-F54 could only see a MISSED IMMEDIATE MATE. Here the DTM is exact, so a move
that mates in 7 instead of 3 counts.
"""
import os
import re
import subprocess
import sys

import chess

fens_path, solver_out, outdir, exe = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16")]


def parse_solver(path):
    """{position index -> {move -> dtm or None}, 'best': int}"""
    out = {}
    cur = None
    for line in open(path):
        m = re.match(r"### position (\d+): `([^`]+)`", line)
        if m:
            cur = int(m.group(1))
            out[cur] = {"fen": m.group(2), "moves": {}, "best": None}
            continue
        m = re.match(r"\| ([a-h][1-8][a-h][1-8][qrbn]?) \| ([^|]+) \|", line)
        if m and cur is not None:
            val = m.group(2).strip()
            out[cur]["moves"][m.group(1)] = None if "draw" in val else int(val)
            continue
        m = re.match(r"best DTM available: (\S+) plies", line)
        if m and cur is not None:
            v = m.group(1)
            out[cur]["best"] = None if v == "None" else int(v)
    return out


def ask(fen, cmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(400000):
            l = p.stdout.readline()
            if not l:
                return got
            got.append(l.rstrip("\n"))
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send(cmd)
    blk = readto(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return bm


solver = parse_solver(solver_out)
fens = [l.strip() for l in open(fens_path) if l.strip()]
rows = []
for idx in sorted(solver):
    info = solver[idx]
    fen = info["fen"]
    if not info["moves"]:
        continue
    best = info["best"]
    m16 = ask(fen, "go depth 16")
    m20k = ask(fen, "go nodes 20000")
    d16 = info["moves"].get(m16, "not-in-table") if m16 else None
    d20k = info["moves"].get(m20k, "not-in-table") if m20k else None
    def worse(d):
        if best is None:
            return False
        if d == "not-in-table":
            return False      # a promotion that leaves the table; not adjudicable here
        if d is None:
            return True       # engine drew where a mate existed
        return d > best
    rows.append((idx, fen, best, m16, d16, worse(d16), m20k, d20k, worse(d20k)))
    print("pos %2d best %s | depth16 %s -> %s %s | nodes20k %s -> %s %s"
          % (idx, best, m16, d16, "WORSE" if worse(d16) else "ok",
             m20k, d20k, "WORSE" if worse(d20k) else "ok"), flush=True)

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("# engine DTM vs best available DTM, lone-king vs ONE piece (exact retrograde solver)\n\n")
    fh.write("PC r15, PC20, Threads 1, Hash 16, cold. Positions the oracle covers: %d.\n\n" % len(rows))
    fh.write("| pos | best DTM | depth16 move | its DTM | worse? | nodes20k move | its DTM | worse? |\n")
    fh.write("|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write("| %d | %s | %s | %s | **%s** | %s | %s | **%s** |\n"
                 % (r[0], r[2], r[3], r[4], "YES" if r[5] else "no", r[6], r[7], "YES" if r[8] else "no"))
    n16 = sum(1 for r in rows if r[5])
    n20 = sum(1 for r in rows if r[8])
    fh.write("\n**positions where the engine's move reaches a worse DTM than available: %d of %d** "
             "(depth16 %d, nodes20k %d)\n" % (sum(1 for r in rows if r[5] or r[8]), len(rows), n16, n20))
print("\n" + open(os.path.join(outdir, "RESULT.txt")).read()[-700:])
