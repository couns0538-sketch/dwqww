#!/usr/bin/env python3
"""dtm_compare_mirror.py FENS SOLVER_OUT OUTDIR EXE : the MIRROR test — the bare king defends.

For a position where the BARE KING is to move, the correct play is to MAXIMISE the distance to mate (and to
reach a draw if one exists). So the test inverts:

    engine DTM  >  best defensive DTM   ->  the engine gave up the mate SOONER than necessary: a DEFECT
    engine reaches a DRAW where a longer-but-saved defence existed -> not a defect (a draw is best of all)

Equivalently: for the bare side, a move is best when its DTM is the LARGEST among the legal moves (or a draw /
unsolved). A move is a defect when some other legal move survives strictly longer.

Everything else mirrors dtm_compare.py: same build, same settings, same two budgets, cold, and the same
validation gate (the solver refuses if KQvK does not reproduce 19 plies).
"""
import os
import re
import subprocess
import sys

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16")]


def parse(path):
    out, cur = {}, None
    for line in open(path):
        m = re.match(r"### position (\d+): `([^`]+)`", line)
        if m:
            cur = int(m.group(1))
            out[cur] = {"fen": m.group(2), "moves": {}}
            continue
        m = re.match(r"\| ([a-h][1-8][a-h][1-8][qrbn]?) \| ([^|]+) \|", line)
        if m and cur is not None:
            v = m.group(2).strip()
            out[cur]["moves"][m.group(1)] = None if "draw" in v else int(v)
    return out


def ask(exe, fen, cmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def rt(pred):
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
    rt(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        rt(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    rt(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    rt(lambda l: l.startswith("readyok"))
    send(cmd)
    blk = rt(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            return parts[1] if len(parts) > 1 else None
    return None


fens_path, solver_out, outdir, exe = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(outdir, exist_ok=True)
solver = parse(solver_out)
rows = []
for idx in sorted(solver):
    info = solver[idx]
    if not info["moves"]:
        continue
    vals = [v for v in info["moves"].values() if v is not None]
    best_defence = max(vals) if vals else None      # the bare side wants the LARGEST dtm
    draw_available = any(v is None for v in info["moves"].values())
    m16 = ask(exe, info["fen"], "go depth 16")
    m20 = ask(exe, info["fen"], "go nodes 20000")
    d16 = info["moves"].get(m16, "not-in-table")
    d20 = info["moves"].get(m20, "not-in-table")
    def defect(d):
        if d == "not-in-table" or best_defence is None:
            return False
        if d is None:
            return False        # a draw is the best a defender can do
        return d < best_defence
    rows.append((idx, info["fen"], best_defence, draw_available, m16, d16, defect(d16), m20, d20, defect(d20)))
    print("pos %2d best-defence %s | depth16 %s -> %s %s | nodes20k %s -> %s %s"
          % (idx, best_defence, m16, d16, "SHORTER" if defect(d16) else "ok",
             m20, d20, "SHORTER" if defect(d20) else "ok"), flush=True)

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("# MIRROR test: the bare king must MAXIMISE distance to mate\n\n")
    fh.write("PC r15, PC20, Threads 1, Hash 16, cold. Covered positions: %d.\n\n" % len(rows))
    fh.write("| pos | longest defence avail. | draw available | depth16 move | its DTM | shorter? | nodes20k move | its DTM | shorter? |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write("| %d | %s | %s | %s | %s | **%s** | %s | %s | **%s** |\n"
                 % (r[0], r[2], "yes" if r[3] else "no", r[4], r[5], "YES" if r[6] else "no",
                    r[7], r[8], "YES" if r[9] else "no"))
    bad = sum(1 for r in rows if r[6] or r[9])
    fh.write("\n**positions where the bare king defended for SHORTER than it could: %d of %d** "
             "(depth16 %d, nodes20k %d)\n" % (bad, len(rows),
                                              sum(1 for r in rows if r[6]), sum(1 for r in rows if r[9])))
print("\n" + open(os.path.join(outdir, "RESULT.txt")).read()[-600:])
