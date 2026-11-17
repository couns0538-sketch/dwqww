#!/usr/bin/env python3
"""volatility_rate.py OUT N — the RATE of score volatility per class, not just a direction.

08-F30 gave a direction from 5 boards per class. This measures a rate on N boards per class, so the sparse-class
volatility can be quoted as a proportion rather than an anecdote.

Per board: the clocked search at the owner's control (6 s + 0.06) gives a score at its stop depth D; then
`go depth D+4` gives the completed deeper score. Two outcomes are counted separately, because they are different
events:
  MATE_APPEARED  the clocked score was cp and the deeper score is mate
  CP_MOVED       both are cp; record |delta|
Classes: sparse (<=12 pieces from my R set) and full-material middlegames (set G, >= 20 pieces).

ARGUMENT ORDER: OUT first, then N.
"""
import json
import statistics
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 20
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# sparse: <=12 pieces, at least 3 legal moves, from my own R set (deterministic order)
rset = [l.strip() for l in open("../job1/R_seed801.fens") if l.strip()]
sparse = []
for fen in rset:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    if len(b.piece_map()) <= 12 and b.legal_moves.count() >= 3:
        sparse.append(fen)
    if len(sparse) >= N:
        break

# full material: set G, >= 20 pieces
gset = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()]
full = []
for fen in gset:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    if len(b.piece_map()) >= 20:
        full.append(fen)
    if len(full) >= N:
        break

CLASSES = [("sparse (<=12 pieces)", sparse), ("full material (>=20 pieces)", full)]


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
    import threading
    t0 = time.monotonic()
    send(go)
    lines = []
    done = threading.Event()
    def _reader():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            l = l.rstrip("\n")
            lines.append(l)
            if l.startswith("bestmove"):
                break
        done.set()
    th = threading.Thread(target=_reader, daemon=True)
    th.start()
    finished = done.wait(90.0)
    wall = (time.monotonic() - t0) * 1000.0
    timed_out = not finished
    if timed_out:
        p.kill()
        return {"timeout": True, "wall": wall}
    sync()
    send("quit")
    try:
        p.wait(timeout=120)
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
    return {"wall": wall, "depth": depth, "score": score}


def cp(score):
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
        return None       # mate is counted as an event, never as a cp value
    return None


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Score volatility RATE per class — PC r15, PC20, Threads 1, owner's 6 s + 0.06 clock")
emit("")
emit("%d boards per class. Clocked stop depth D vs a COMPLETED `go depth D+4`." % N)
emit("")
emit("| class | boards | mate appeared | cp-moved boards | gap >= queen (>=900cp) | gap >= 200cp | median cp delta | largest |")
emit("|---|---|---|---|---|---|---|---|")
summary = {}
for cname, fens in CLASSES:
    mates = 0
    cpdel = []
    used = 0
    timeouts = 0
    clock_timeouts = 0
    for fen in fens:
        r = search(fen, CLOCK)
        if r.get("timeout"):
            clock_timeouts += 1
            with open(OUT + ".skip", "a") as fh:
                fh.write("clock_timeout %s\n" % fen)
            continue
        if "err" in r or r.get("depth", 0) < 3:
            with open(OUT + ".skip", "a") as fh:
                fh.write("clock_bad depth=%s err=%s %s\n" % (r.get("depth"), r.get("err"), fen))
            continue
        r2 = search(fen, "go depth %d" % (r["depth"] + 4))
        if r2.get("timeout"):
            timeouts += 1
            with open(OUT + ".skip", "a") as fh:
                fh.write("ref_timeout %s\n" % fen)
            continue
        if "err" in r2:
            continue
        used += 1
        a, b = r["score"], r2["score"]
        if a is None or b is None:
            with open(OUT + ".skip", "a") as fh:
                fh.write("unparsable a=%s b=%s %s\n" % (a, b, fen))
            continue
        if a.startswith("cp") and b.startswith("mate"):
            mates += 1
            kind = "mate_appeared"
            delta = None
        elif a.startswith("cp") and b.startswith("cp"):
            delta = abs(cp(b) - cp(a))
            cpdel.append(delta)
            kind = "cp_moved" if delta else "cp_same"
        else:
            delta = None
            kind = "other"
        with open(OUT + ".jsonl", "a") as fh:
            fh.write(json.dumps({"class": cname, "fen": fen, "D": r["depth"], "score_D": a,
                                 "score_D4": b, "kind": kind, "delta": delta,
                                 "wall_clock": r["wall"]}) + "\n")
    queen = sum(1 for x in cpdel if x >= 900)
    twohun = sum(1 for x in cpdel if x >= 200)
    summary[cname] = (used, mates, cpdel, queen, twohun, timeouts, clock_timeouts)
    emit("| %s | %d | **%d** | %d | **%d** | **%d** | %s | %s |" %
         (cname, used, mates, len(cpdel), queen, twohun,
          ("%.0f cp" % statistics.median(cpdel)) if cpdel else "-",
          ("%d cp" % max(cpdel)) if cpdel else "-"))

emit("")
emit("| class | boards | mate involved | gap >= queen | gap >= 200 cp | EITHER (mate OR >=200cp) |")
emit("|---|---|---|---|---|---|")
for cname, (used, mates, cpdel, queen, twohun, timeouts, clock_timeouts) in summary.items():
    if not used:
        continue
    either = mates + twohun
    emit("| %s | %d | **%d** | **%d** | **%d** | **%d of %d (%.0f %%)** |" %
         (cname, used, mates, queen, twohun, either, used, 100.0 * either / used))
    emit("| %s | CLOCKED searches that did not answer in 90 s (a hang, not a tail) | **%d** | | |" % (cname, clock_timeouts))
    emit("| %s | depth-(D+4) reference searches that did not finish in 90 s | **%d** | | |" % (cname, timeouts))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
