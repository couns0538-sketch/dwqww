#!/usr/bin/env python3
"""score_volatility.py OUT — does the sparse class ALSO have the largest score change between the clocked
(interrupted) answer and a completed deeper search?

This is the link the coordinator asked about: if the class that blows the time tail is also the class whose score
moves most when given more depth, then one explanation covers both — expensive iterations mean the clocked search
reaches a shallow, unreliable depth exactly where depth matters most, which is also what makes a bad training
target.

Method, per board: run at the owner's control (6 s + 0.06) and record the score at the depth it stopped at (D) and
the score at D+4 from a depth-limited search (a COMPLETED deeper search of the same board). Report |delta| per class.

Classes reused from 08-F28 so the comparison is like-for-like.

ARGUMENT ORDER: OUT first.
"""
import statistics
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

CLASSES = [
    ("few pieces, few moves", [
        "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1",
        "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1",
        "8/8/4k3/8/8/4K3/8/4R3 w - - 0 1",
        "8/6k1/8/8/8/8/6PK/7R w - - 0 1",
        "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1",
    ]),
    ("full material, many moves", [
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
        "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
        "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
        "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10",
        "2r2rk1/1p1nbppp/pq1pb3/3Np3/1P2P3/P1N1B3/1BPP1PPP/R2Q1RK1 w - - 0 14",
    ]),
]


def search(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused"}
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    depth = 0
    score = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                depth = max(depth, int(t[2]))
                if "score" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "depth": depth, "score": score, "bm": lines[-1].split()[1]}


def cp(score):
    """centipawns; mate mapped to +-30000. None if unparsable."""
    if not score:
        return None
    t = score.split()
    try:
        v = int(t[1])
    except (IndexError, ValueError):
        return None
    if t[0] == "cp":
        return v
    if t[0] == "mate":
        return (30000 - abs(v)) * (1 if v > 0 else -1)
    return None


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Does the sparse class ALSO have the most volatile score? PC r15, PC20, Threads 1")
emit("")
emit("Score at the clocked stop (depth D) vs a COMPLETED search at D+4 of the same board. Threads 1.")
emit("")
emit("| class | board | clocked depth D | score at D | score at D+4 | \\|delta\\| cp |")
emit("|---|---|---|---|---|---|")
per = {}
for cname, fens in CLASSES:
    per[cname] = []
    for fen in fens:
        r = search(fen, CLOCK)
        if "err" in r:
            emit("| %s | %s | REFUSED | | | |" % (cname, fen[:32]))
            continue
        D = r["depth"]
        # a COMPLETED search at D+4 (depth-limited, so it finishes the requested depth)
        r2 = search(fen, "go depth %d" % (D + 4))
        if "err" in r2:
            continue
        a, b = cp(r["score"]), cp(r2["score"])
        if a is None or b is None:
            raise SystemExit("CONTROL FAILED: unparsable score for %r (%r / %r)" % (fen, r["score"], r2["score"]))
        d = abs(b - a)
        per[cname].append(d)
        emit("| %s | %s | %d | %s | %s | **%d** |" % (cname, fen[:32], D, r["score"], r2["score"], d))

emit("")
emit("| class | n | median \\|delta\\| cp | mean | largest |")
emit("|---|---|---|---|---|")
for cname, vals in per.items():
    if not vals:
        continue
    emit("| %s | %d | **%.0f** | %.0f | %d |" %
         (cname, len(vals), statistics.median(vals), sum(vals) / len(vals), max(vals)))

emit("")
emit("| verdict | see the event table above: mate appearances and cp movements are reported separately, "
     "because a mate appearing at D+4 is not a centipawn movement and mapping it to 30000 inflates any ratio. |")
emit("")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
