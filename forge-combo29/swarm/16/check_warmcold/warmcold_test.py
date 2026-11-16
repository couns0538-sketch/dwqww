#!/usr/bin/env python3
"""warmcold_test.py EXE OUT.txt : is my published symmetry number a warm/cold artefact?

Two disciplines, same positions, same depths:
  COLD   : one fresh process per search (what my job3 table used)
  WARM   : one process for the whole sweep, with `ucinewgame` before each search (seat 10's allowed
           substitute), never Clear Hash
It also runs the WRONG discipline (no ucinewgame, nothing between searches) to show the confound is live
in this build, so the comparison is meaningful.
Reports, per discipline, the bestmove-mismatch count and the score-mismatch count on the same positions.
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
DEPTH = 8
S14 = [("OwnBook", "false"), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


class Missing(Exception):
    pass


def open_engine():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=120):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci"); to("uciok", 15)
    for n, v in [("Threads", 1), ("Hash", 16)] + S14:
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 15)
    return p, send, to


def parse(lines):
    best = None
    score = None
    nodes = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {DEPTH} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = (m.group(1), int(m.group(2)))
            nodes = int(m.group(3))
    if best is None or score is None:
        raise Missing("search produced no bestmove or no depth score")
    return best, score, nodes


def search_cold(fen):
    p, send, to = open_engine()
    send("position fen " + fen)
    send("isready"); to("readyok", 15)
    send(f"go depth {DEPTH}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove (cold)")
    return parse(lines)


class WarmSweeper:
    """One process; `ucinewgame` (allowed cold reset) before every search, never Clear Hash."""

    def __init__(self, use_newgame=True):
        self.p, self.send, self.to = open_engine()
        self.use_newgame = use_newgame

    def search(self, fen):
        if self.use_newgame:
            self.send("ucinewgame")
            self.send("isready")
            got, ok = self.to("readyok", 20)
            if not ok:
                raise Missing("no readyok after ucinewgame")
        self.send("position fen " + fen)
        self.send("isready")
        self.to("readyok", 15)
        self.send(f"go depth {DEPTH}")
        lines, ok = self.to("bestmove", 300)
        if not ok:
            raise Missing("no bestmove (warm)")
        return parse(lines)

    def close(self):
        self.send("quit")
        try:
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job2/G_nocastle.fens")
        if l.strip()][:12]
pairs = []
for fen in fens:
    mir = chess.Board(fen).mirror().fen()
    # the mirror bestmove maps back by square
    pairs.append((fen, mir))


def back(mv):
    if not mv or mv == "0000":
        return None
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


out = [f"depth {DEPTH}, {len(pairs)} pairs, exe {EXE}", ""]

# COLD
bm_bad = sc_bad = 0
node_rows = []
for fen, mir in pairs:
    a = search_cold(fen)
    b = search_cold(mir)
    if a[0] != back(b[0]):
        bm_bad += 1
    if a[1] != b[1]:
        sc_bad += 1
    node_rows.append((a[2], b[2]))
out.append(f"COLD  (fresh process per search): bestmove mismatch {bm_bad}/{len(pairs)}, "
           f"score mismatch {sc_bad}/{len(pairs)}")
print(out[-1])

# WARM with ucinewgame (allowed)
w = WarmSweeper(True)
bm_bad2 = sc_bad2 = 0
try:
    for fen, mir in pairs:
        a = w.search(fen)
        b = w.search(mir)
        if a[0] != back(b[0]):
            bm_bad2 += 1
        if a[1] != b[1]:
            sc_bad2 += 1
finally:
    w.close()
out.append(f"WARM  (one process, ucinewgame before each search): bestmove mismatch {bm_bad2}/{len(pairs)}, "
           f"score mismatch {sc_bad2}/{len(pairs)}")
print(out[-1])

# WRONG discipline: no ucinewgame, nothing between searches
w2 = WarmSweeper(False)
bm_bad3 = sc_bad3 = 0
nodes_seen = []
try:
    for fen, mir in pairs:
        a = w2.search(fen)
        b = w2.search(mir)
        nodes_seen += [a[2], b[2]]
        if a[0] != back(b[0]):
            bm_bad3 += 1
        if a[1] != b[1]:
            sc_bad3 += 1
finally:
    w2.close()
out.append(f"WARM  (NO ucinewgame, nothing between - the WRONG discipline): bestmove mismatch "
           f"{bm_bad3}/{len(pairs)}, score mismatch {sc_bad3}/{len(pairs)}")
print(out[-1])

out.append("")
out.append(f"node counts cold, first 6 pairs: {node_rows[:6]}")
out.append(f"node counts warm-no-reset, first 12: {nodes_seen[:12]}")
text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
