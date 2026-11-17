#!/usr/bin/env python3
"""matescore_survey.py EXE FENS SOLVER_OUT OUTDIR : are the engine's mate scores on KRvK/KQvK TRUE distances?

19-C24 found two boards where the engine's `mate N` was arithmetically impossible on KRvK. That raises the
question this script answers at scale: over many 1-piece endings, how often does the engine's mate score match
the exact DTM?

Method, per position:
  * run `go depth D` (D configurable) on the PC build under PC20, Threads 1, cold, awaiting `bestmove`;
  * read the last `info depth` line's score and PV;
  * compare, when the score is `mate N`:
      - the PROMISED plies (2N-1 for N>0 with the side to move winning),
      - the engine's own PV length,
      - the ORACLE's exact best DTM (and the DTM of the move the engine actually played);
  * classify: EXACT (promise == oracle), SHORT-PV only (promise == oracle but PV shorter),
    OVER-CLAIM (promise > oracle DTM, i.e. claims a longer mate than exists),
    IMPOSSIBLE (promise > 31 plies for KRvK / > 19 for KQvK), UNDER-CLAIM (promise < oracle, i.e. a faster
    mate existed and the engine reported a slower one).

Only positions the solver covers are used (single bare king vs one piece).
"""
import os
import re
import subprocess
import sys

import chess

exe, fens, solver_out, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
depth = int(sys.argv[5]) if len(sys.argv) > 5 else 20
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
    """{position index: {move: dtm or None}} plus the board fens, from dtm_oracle.py output."""
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


def ask(fen, d):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def rt(pred):
        got = []
        for _ in range(600000):
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
    send("go depth %d" % d)
    blk = rt(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=300)
    except subprocess.TimeoutExpired:
        p.kill()
    last = None
    best = None
    for l in blk:
        if l.startswith("info depth") and " pv " in l:
            last = l
        if l.startswith("bestmove"):
            best = l.split()[1] if len(l.split()) > 1 else None
    if not last:
        return None, None, 0, best
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    score = (m.group(1), int(m.group(2))) if m else None
    pv = last.split(" pv ")[1].split() if " pv " in last else []
    return score, pv, len(pv), best


solver = parse_solver(solver_out)
rows = []
for idx in sorted(solver):
    info = solver[idx]
    fen = info["fen"]
    score, pv, pvlen, best = ask(fen, depth)
    if score is None:
        rows.append((idx, fen, "no-score", None, None, pvlen, best, None, None))
        continue
    kind, val = score
    if kind != "mate":
        rows.append((idx, fen, "cp", val, None, pvlen, best, None, None))
        continue
    promised = 2 * abs(val) - 1 if val != 0 else 0
    oracle_by_move = info["moves"]
    dts = [v for v in oracle_by_move.values() if v is not None]
    oracle_best = min(dts) if dts else None
    played_dtm = oracle_by_move.get(best)
    rows.append((idx, fen, "mate", val, promised, pvlen, best, oracle_best, played_dtm))

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("# engine mate scores vs exact DTM on 1-piece endings (PC r15, PC20, Threads 1, Hash 16, cold, depth %d)\n\n" % depth)
    fh.write("| pos | score | promised plies | PV plies | played | oracle best DTM | verdict |\n")
    fh.write("|---|---|---|---|---|---|---|\n")
    counts = {}
    for (idx, fen, kind, val, promised, pvlen, best, ob, pd) in rows:
        if kind != "mate":
            fh.write("| %d | %s | - | %d | %s | %s | not a mate score |\n" % (idx, kind, pvlen, best, ob))
            counts["not-mate"] = counts.get("not-mate", 0) + 1
            continue
        if ob is None:
            verdict = "oracle has no mate"
        elif promised == ob:
            verdict = "EXACT" if pvlen >= promised else "EXACT but PV short (%d of %d)" % (pvlen, promised)
        elif promised > ob:
            verdict = "OVER-CLAIM (promises %d, best is %d)" % (promised, ob)
        else:
            verdict = "UNDER-CLAIM (reports %d, faster %d existed)" % (promised, ob)
        key = verdict.split(" (")[0]
        counts[key] = counts.get(key, 0) + 1
        fh.write("| %d | mate %+d | %d | %d | %s | %s | **%s** |\n" % (idx, val, promised, pvlen, best, ob, verdict))
    fh.write("\n## counts\n\n")
    for k, v in sorted(counts.items()):
        fh.write("- %s: %d\n" % (k, v))
print(open(os.path.join(outdir, "RESULT.txt")).read()[-1800:])
