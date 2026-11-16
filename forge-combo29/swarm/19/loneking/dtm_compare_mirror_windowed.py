#!/usr/bin/env python3
"""dtm_compare_mirror_windowed.py FENS SOLVER_OUT OUTDIR EXE : the MIRROR test THROUGH windowed_verdict().

The bare king is to move and wants to survive. Published numbers must come only through the window clamp
(19-C10/19-F57): with counter c, only 100-c half-moves remain, so a move whose mate needs more plies than that
IS a draw, and a defender who reaches that window has defended correctly.

For each covered position:
    for every legal move, its WINDOWED verdict:  "win"  (mate fits the window, bad for the defender)
                                                 "draw" (no mate, or mate too long -> drawn, GOOD)
    best defence = draw if any move draws, else the largest fitting DTM
    engine defect = its move's windowed verdict is a WIN while some alternative DRAWS, or its
                    fitting DTM is strictly smaller (dies sooner than necessary)
A move recorded as "not-in-table" (a promotion leaving the signature) is never counted as a defect.
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


def windowed(dtm, counter):
    if dtm is None:
        return "draw"
    return "win" if dtm <= 100 - counter else "draw"


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


import chess

fens_path, solver_out, outdir, exe = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(outdir, exist_ok=True)
solver = parse(solver_out)
fens = [l.strip() for l in open(fens_path) if l.strip()]
rows = []
for idx in sorted(solver):
    info = solver[idx]
    if not info["moves"]:
        continue
    b = chess.Board(fens[idx])
    c = b.halfmove_clock
    verdicts = {m: windowed(v, c) for m, v in info["moves"].items()}
    dts = {m: v for m, v in info["moves"].items() if v is not None and v <= 100 - c}
    draw_available = any(v == "draw" for v in verdicts.values())
    best_hold = max(dts.values()) if dts else None
    m16 = ask(exe, fens[idx], "go depth 16")
    m20 = ask(exe, fens[idx], "go nodes 20000")
    def defect(m):
        if m not in verdicts:
            return False
        if verdicts[m] == "draw":
            return False                    # drawing is the best a defender can do
        if draw_available:
            return True                     # it lost where a draw existed
        if best_hold is None:
            return False
        v = info["moves"].get(m)
        return v is not None and v < best_hold
    rows.append((idx, c, 100 - c, draw_available, best_hold, m16, verdicts.get(m16), defect(m16),
                 m20, verdicts.get(m20), defect(m20)))
    print("pos %2d counter %2d window %3d draw-avail %-3s besthold %-4s | depth16 %s %s %s | nodes20k %s %s %s"
          % (idx, c, 100 - c, draw_available, best_hold, m16, verdicts.get(m16),
             "DEFECT" if defect(m16) else "ok", m20, verdicts.get(m20),
             "DEFECT" if defect(m20) else "ok"), flush=True)

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("# MIRROR test through windowed_verdict(): the bare king must survive, window = 100 - counter\n\n")
    fh.write("PC r15, PC20, Threads 1, Hash 16, cold. Covered: %d positions.\n\n" % len(rows))
    fh.write("| pos | counter | window | draw avail | best hold | depth16 | verdict | defect | nodes20k | verdict | defect |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write("| %d | %d | %d | %s | %s | %s | %s | **%s** | %s | %s | **%s** |\n"
                 % (r[0], r[1], r[2], "yes" if r[3] else "no", r[4], r[5], r[6],
                    "YES" if r[7] else "no", r[8], r[9], "YES" if r[10] else "no"))
    bad = sum(1 for r in rows if r[7] or r[10])
    fh.write("\n**positions where the bare king was lost/hastened by a move that a draw or a longer defence "
             "avoided: %d of %d**\n" % (bad, len(rows)))
print("\n" + open(os.path.join(outdir, "RESULT.txt")).read()[-500:])
