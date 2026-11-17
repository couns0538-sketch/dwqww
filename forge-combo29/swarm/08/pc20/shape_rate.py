#!/usr/bin/env python3
"""shape_rate.py OUT N — the SHAPE classification at a size that supports a rate.

08-F28 classified five shapes on 19 hand-built boards and gave medians 161-853 ms. The coordinator called that the
headline of the clock work. This repeats it at N boards per class from SOURCES rather than hand-built boards, so the
numbers can be quoted as class rates rather than as illustrations.

Classes and how each board is obtained:
  sparse_endgame   from my R sets: <=12 pieces, <=20 legal moves (the class 08-F28 found slowest)
  sparse_open      from my R sets: <=12 pieces, >20 legal moves
  full_few         from the R sets: >=24 pieces, <=25 legal moves
  full_many        from set G:     >=24 pieces, >25 legal moves
  quiet_endgame    from my R sets: <=8 pieces (a narrower slice of the sparse class, to see if it is even slower)

Each board is searched ONCE at the owner's control, fresh process, PC20, Threads 1, Hash 16. Records wall, depth,
and the last iteration's cost.

ARGUMENT ORDER: OUT first, then N.
"""
import json
import statistics
import subprocess
import sys
import threading
import time

import chess

OUT = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 15
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

rsets = []
for path in ("../job1/R_seed801.fens", "./R_seed902.fens"):
    try:
        rsets += [l.strip() for l in open(path) if l.strip()]
    except FileNotFoundError:
        pass
gset = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()]

buckets = {"sparse_endgame": [], "sparse_open": [], "full_few": [], "full_many": [], "quiet_endgame": []}
for fen in rsets:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    pc = len(b.piece_map())
    mv = b.legal_moves.count()
    if pc <= 8 and mv >= 3 and len(buckets["quiet_endgame"]) < N:
        buckets["quiet_endgame"].append(fen)
    elif pc <= 12 and mv >= 3:
        if mv <= 20 and len(buckets["sparse_endgame"]) < N:
            buckets["sparse_endgame"].append(fen)
        elif mv > 20 and len(buckets["sparse_open"]) < N:
            buckets["sparse_open"].append(fen)
    elif pc >= 24:
        if mv <= 25 and len(buckets["full_few"]) < N:
            buckets["full_few"].append(fen)
for fen in gset:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    if len(b.piece_map()) >= 24 and b.legal_moves.count() > 25 and len(buckets["full_many"]) < N:
        buckets["full_many"].append(fen)


def probe(fen):
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
        return None
    t0 = time.monotonic()
    send(CLOCK)
    marks = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            ms = (time.monotonic() - t0) * 1000.0
            if l.startswith("info depth"):
                try:
                    marks.append((int(l.split()[2]), ms))
                except (IndexError, ValueError):
                    pass
            if l.startswith("bestmove"):
                break
        done.set()

    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(30.0)
    wall = (time.monotonic() - t0) * 1000.0
    if not ok:
        p.kill()
        return {"timeout": True, "wall": wall}
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    lastd = marks[-1][0] if marks else 0
    itc = (marks[-1][1] - marks[-2][1]) if len(marks) >= 2 else (marks[-1][1] if marks else None)
    return {"wall": wall, "depth": lastd, "itercost": itc}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## The shape classification at N=%d boards per class — owner's 6 s + 0.06 clock, PC20, Threads 1" % N)
emit("")
emit("| class | n | median wall | worst | median depth | median last-iteration cost | over 1200 ms |")
emit("|---|---|---|---|---|---|---|")
rowsby = {}
for cname in ("quiet_endgame", "sparse_endgame", "sparse_open", "full_few", "full_many"):
    fens = buckets[cname]
    rows = []
    for fen in fens:
        r = probe(fen)
        if r and not r.get("timeout"):
            rows.append(r)
        with open(OUT + ".jsonl", "a") as fh:
            fh.write(json.dumps({"class": cname, "fen": fen, "r": r}) + "\n")
    rowsby[cname] = rows
    if not rows:
        emit("| %s | 0 usable | | | | | |" % cname)
        continue
    w = [r["wall"] for r in rows]
    d = [r["depth"] for r in rows]
    ic = [r["itercost"] for r in rows if r["itercost"] is not None]
    emit("| %s | %d | **%.1f** | **%.1f** | %.0f | %s | %d |" %
         (cname, len(rows), statistics.median(w), max(w), statistics.median(d),
          ("%.1f ms" % statistics.median(ic)) if ic else "-",
          sum(1 for x in w if x > 1200)))

emit("")
emit("| question | answer |")
emit("|---|---|")
meds = {c: statistics.median([r["wall"] for r in rows]) for c, rows in rowsby.items() if rows}
if meds:
    lo = min(meds.items(), key=lambda kv: kv[1])
    hi = max(meds.items(), key=lambda kv: kv[1])
    emit("| slowest class | **%s at %.1f ms** |" % (hi[0], hi[1]))
    emit("| fastest class | **%s at %.1f ms** |" % (lo[0], lo[1]))
    emit("| spread | **%.1fx** |" % (hi[1] / lo[1] if lo[1] else 0))
    emit("| classes over 1200 ms at any board | %s |" %
         (", ".join("%s (%d of %d)" % (c, sum(1 for r in rows if r["wall"] > 1200), len(rows))
                    for c, rows in rowsby.items() if any(r["wall"] > 1200 for r in rows)) or "none"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
