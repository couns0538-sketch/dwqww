#!/usr/bin/env python3
"""check_switches.py OUT — the PC20 switches, isolated, on mate scores. Threads 1 throughout.

Task A: MateAlphaGuard alone, on top of S14, on/off, fresh process per cell, both boards.
Task B: each of the four PC20 SEARCH switches alone on top of S14, for mate scores — a switch that silently
        worsens a mate score is worse than one that does nothing.

Boards:
  B1 = seat 20's S-F19 / S-F38 board   `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`
  B2 = seat 01's S-F19 board           `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1`

ARGUMENT ORDER: OUT first (the lesson from the overwritten-binary incident).

CONTROLS (enforced): every cell must reach depth 12 and produce a parsable score; the S14 baseline must be
identical across the two runs of the same arm (repeatability — Threads 1 must be stable, else nothing below means
anything).
"""
import subprocess
import sys

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
DEPTH = 12

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]

BOARDS = [
    ("B1 seat20 S-F19 board", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("B2 seat01 S-F19 board", "8/8/8/8/2K4Q/8/8/1k6 w - - 100 1"),
]

# Task A: the guard alone, on top of S14
A_ARMS = [("S14 only (no guard)", []),
          ("S14 + MateAlphaGuard true", [("MateAlphaGuard", "true")]),
          ("S14 + MateAlphaGuard false", [("MateAlphaGuard", "false")])]

# Task B: each PC20 SEARCH switch alone, on top of S14
B_ARMS = [("S14 only (baseline)", []),
          ("S14 + CuckooRep true", [("CuckooRep", "true")]),
          ("S14 + HistRework 2", [("HistRework", "2")]),
          ("S14 + TtPruneV2 true", [("TtPruneV2", "true")]),
          ("S14 + CorrHistV2 true", [("CorrHistV2", "true")]),
          ("S14 + all four", [("CuckooRep", "true"), ("HistRework", "2"),
                              ("TtPruneV2", "true"), ("CorrHistV2", "true")])]


def probe(fen, extra):
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    opts = S14 + extra + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
    for n, v in opts:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "invalid FEN"}
    if any("unknown option" in l or "invalid value" in l for l in pre):
        return {"err": "option refused"}
    send("go depth %d" % DEPTH)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    score = nodes = None
    maxd = 0
    pvlen = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if d == DEPTH and "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
                    pvlen = (len(t) - t.index("pv") - 1) if "pv" in t else 0
            except (IndexError, ValueError):
                pass
    return {"score": score, "nodes": nodes, "maxd": maxd, "pvlen": pvlen, "bm": lines[-1].split()[1]}


def plies(score):
    if not score or not score.startswith("mate"):
        return None
    n = int(score.split()[1])
    return 2 * abs(n) if n < 0 else 2 * n - 1


out = []
def emit(s):
    out.append(s)
    print(s)


def run_table(title, arms):
    emit("## " + title)
    emit("")
    emit("| board | arm | score | plies | nodes | pv length | bestmove | verdict |")
    emit("|---|---|---|---|---|---|---|---|")
    res = {}
    for blabel, fen in BOARDS:
        base_score = None
        for alabel, extra in arms:
            r = probe(fen, extra)
            if "err" in r:
                raise SystemExit("CONTROL FAILED: %s / %s -> %s" % (blabel, alabel, r["err"]))
            if r["maxd"] < DEPTH or r["score"] is None:
                raise SystemExit("CONTROL FAILED: %s / %s did not reach depth %d with a parsable score"
                                 % (blabel, alabel, DEPTH))
            if alabel.startswith("S14 only"):
                base_score = r["score"]
            verdict = ""
            if base_score is not None and not alabel.startswith("S14 only"):
                if r["score"] == base_score:
                    verdict = "no change"
                elif r["score"].startswith("cp") and base_score.startswith("mate"):
                    verdict = "**LOST THE MATE**"
                elif r["score"].startswith("mate") and base_score.startswith("mate"):
                    verdict = "distance changed"
                else:
                    verdict = "score changed"
            emit("| %s | %s | **%s** | %s | %s | %d | %s | %s |" %
                 (blabel, alabel, r["score"], plies(r["score"]) or "-", f"{r['nodes']:,}", r["pvlen"],
                  r["bm"], verdict))
            res[(blabel, alabel)] = r
        emit("| | | | | | | | |")
    emit("")
    return res


ra = run_table("TASK A — MateAlphaGuard alone, on top of S14, `go depth 12`, Threads 1, PC r15 build", A_ARMS)
rb = run_table("TASK B — each PC20 SEARCH switch alone on top of S14, `go depth 12`, Threads 1, PC r15 build", B_ARMS)

# repeatability control: the baseline in both tasks must agree
for blabel, fen in BOARDS:
    a_base = ra[(blabel, "S14 only (no guard)")]["score"]
    b_base = rb[(blabel, "S14 only (baseline)")]["score"]
    if a_base != b_base:
        raise SystemExit("CONTROL FAILED: the S14 baseline on %s gave %s and %s in two runs — Threads 1 is not "
                         "stable, so no switch comparison is meaningful" % (blabel, a_base, b_base))

emit("")
emit("## Summary")
emit("")
emit("| question | B1 | B2 |")
emit("|---|---|---|")
def g(res, arm, board):
    return res[(board, arm)]["score"]
emit("| S14 baseline | %s | %s |" % (g(ra, "S14 only (no guard)", BOARDS[0][0]), g(ra, "S14 only (no guard)", BOARDS[1][0])))
emit("| + MateAlphaGuard true | **%s** | **%s** |" % (g(ra, "S14 + MateAlphaGuard true", BOARDS[0][0]),
                                                      g(ra, "S14 + MateAlphaGuard true", BOARDS[1][0])))
emit("| + MateAlphaGuard false | %s | %s |" % (g(ra, "S14 + MateAlphaGuard false", BOARDS[0][0]),
                                               g(ra, "S14 + MateAlphaGuard false", BOARDS[1][0])))
for arm in ("S14 + CuckooRep true", "S14 + HistRework 2", "S14 + TtPruneV2 true", "S14 + CorrHistV2 true", "S14 + all four"):
    emit("| %s | %s | %s |" % (arm, g(rb, arm, BOARDS[0][0]), g(rb, arm, BOARDS[1][0])))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
