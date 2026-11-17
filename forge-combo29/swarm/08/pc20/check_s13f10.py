#!/usr/bin/env python3
"""check_s13f10.py OUT — my own check of seat 13's S-F10 (the owner's clock path), and a reconcile with my own
4-position-independent measurement of the same control.

Their claim:
"On PC r15 under PC20 at Threads 1/Hash 16 with the owner's 6 s + 0.06 s clock: 0 overruns and 0 illegal moves in
 80 clocked moves, but the engine uses only 4.1 % of its clock (median 207 ms of 6,000) reaching median depth 19;
 allocation scales with the clock (6 s -> ~0.36 s, 30 s -> ~1.28 s, movestogo 40 -> 88 ms) and the search is
 deterministic in nodes/depth/move (650,246 nodes, depth 19, e2e4 five times). Limit: 4 of the 12 G positions."

MY OWN measurement of the same control (08-F24, CLOCK_HEADLINE) gave a median of 295 ms at a pinned 6000 ms clock
across 120 moves over 3 positions — 4.9 % rather than 4.1 %. Both cannot be the whole story, so this checks their
specific numbers on their specific setup and asks whether the difference is the position set.

Checks:
  1. their determinism claim: the SAME position searched repeatedly at the owner's clock must give identical
     nodes/depth/bestmove (I run it 5 times).
  2. their clock-share claim: median wall / 6000 for a few positions.
  3. the CLOCK-SCALING claim: 6 s vs 30 s, does the used time scale roughly linearly?
  4. both controls: a real search must show info lines, and 0 illegal moves across the sample.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
DETERMINISM_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
G12 = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()][:8]


def run(fen, go, timeout=90.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    t0 = time.monotonic()
    send(go)
    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(timeout)
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
    depth = nodes = 0
    n_info = 0
    score = None
    for l in lines:
        if l.startswith("info depth"):
            n_info += 1
            t = l.split()
            try:
                depth = max(depth, int(t[2]))
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
                if "score" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "depth": depth, "nodes": nodes, "n_info": n_info,
            "bm": lines[-1].split()[1], "score": score}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 13 S-F10 — the owner's clock path, checked and reconciled with my own numbers")
emit("")
emit("PC r15, PC20, Threads 1, Hash 16.")
emit("")
emit("### 1. determinism at the owner's clock — the same position 5 times")
emit("")
emit("| run | wall ms | depth | nodes | bestmove | score |")
emit("|---|---|---|---|---|---|")
dets = []
for i in range(1, 6):
    r = run(DETERMINISM_FEN, "go wtime 6000 btime 6000 winc 60 binc 60")
    dets.append(r)
    emit("| %d | %.1f | %d | %s | %s | %s |" % (i, r["wall"], r["depth"], f"{r['nodes']:,}", r["bm"], r["score"]))
same = (len({r["depth"] for r in dets}) == 1 and len({r["nodes"] for r in dets}) == 1
        and len({r["bm"] for r in dets}) == 1)
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| identical depth, nodes and move in 5 fresh processes? | **%s** |" % ("YES" if same else "NO"))

emit("")
emit("### 2. clock share on G positions at 6 s + 0.06")
emit("")
emit("| position | wall ms | share of 6000 ms | depth | info lines |")
emit("|---|---|---|---|---|")
shares = []
illegal = 0
for fen in G12:
    r = run(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
    if r.get("timeout"):
        emit("| %s | TIMEOUT | | | |" % fen[:30])
        continue
    b = chess.Board(fen)
    if chess.Move.from_uci(r["bm"]) not in b.legal_moves:
        illegal += 1
    shares.append(100.0 * r["wall"] / 6000.0)
    emit("| %s | %.1f | **%.1f %%** | %d | %d |" % (fen[:30], r["wall"], 100.0 * r["wall"] / 6000.0,
                                                    r["depth"], r["n_info"]))
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| median share of the clock on these positions | **%.1f %%** |" %
     (sorted(shares)[len(shares) // 2] if shares else 0))
emit("| seat 13 reported | **4.1 %%** (median 207 ms) |")
emit("| my 08-F24 reported (120 moves, 3 positions) | **4.9 %%** (median 295 ms) |")
emit("| illegal bestmoves in this sample | **%d** |" % illegal)

emit("")
emit("### 3. does the used time scale with the clock?")
emit("")
emit("| clock | wall ms | share |")
emit("|---|---|---|")
for c in (6000, 30000):
    r = run(DETERMINISM_FEN, "go wtime %d btime %d winc 60 binc 60" % (c, c))
    emit("| %d | %.1f | %.1f %% |" % (c, r["wall"], 100.0 * r["wall"] / c))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
