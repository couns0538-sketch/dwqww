#!/usr/bin/env python3
"""check_s03f13.py OUT — my own check of seat 03's S-F13:

"The divergence set is EXACTLY a subset of the positions with a lone king at the ROOT: 9 of 200 positions have one
 and all 4 differing positions are among those 9 (0 of the other 191 differ) — the predicate the r15 code gates on
 (`root_bare_king_`), not the material proxy I first used. builds: base vs r15; settings: depth 8, Threads 1."

Their exact counts depend on their 200-position set, which I do not have. What I CAN check is the STRUCTURAL claim,
on my own positions: at depth 8, Threads 1, does the PC build differ from the base build ONLY on positions where one
side has a lone king at the root?

My sample: a set of R positions split into "lone king at the root" and "not", searched on both builds at depth 8,
bestmoves compared. If any non-lone-king position differs, their exclusive-subset claim is REFUTED; if none do while
lone-king positions do differ, it is supported.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
DEPTH = 8


def lone_king_at_root(b):
    for colour in (chess.WHITE, chess.BLACK):
        pieces = [p for s, p in b.piece_map().items() if p.color == colour]
        if len(pieces) == 1 and pieces[0].piece_type == chess.KING:
            return True
    return False


r = [l.strip() for l in open("../job1/R_seed801.fens") if l.strip()]
lone, other = [], []
for fen in r:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    (lone if lone_king_at_root(b) else other).append(fen)

# cap for time, but keep EVERY lone-king board available (they are the rare class)
lone = lone[:40]
other = other[:60]


def best(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("setoption name OwnBook value false")
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go depth %d" % DEPTH)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    return lines[-1].split()[1]


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 03 S-F13 — does the PC-vs-base move divergence happen ONLY at lone-king roots?")
emit("")
emit("Both builds, default options + Threads 1 + Hash 16 + OwnBook false, `go depth %d`." % DEPTH)
emit("")
emit("| class | boards | differing moves |")
emit("|---|---|---|")
res = {}
for label, fens in (("lone king at the root", lone), ("no lone king", other)):
    diffs = []
    for fen in fens:
        a = best(BASE, fen)
        b = best(PC, fen)
        if a != b:
            diffs.append((fen, a, b))
    res[label] = (len(fens), diffs)
    emit("| %s | %d | **%d** |" % (label, len(fens), len(diffs)))

emit("")
emit("| class | boards | differing | rate |")
emit("|---|---|---|---|")
for label, (n, diffs) in res.items():
    emit("| %s | %d | %d | %.1f %% |" % (label, n, len(diffs), 100.0 * len(diffs) / max(n, 1)))

emit("")
emit("### the differing boards, listed")
emit("| class | fen | base bestmove | PC bestmove |")
emit("|---|---|---|---|")
for label, (n, diffs) in res.items():
    for fen, a, b in diffs:
        emit("| %s | %s | %s | %s |" % (label, fen[:40], a, b))

emit("")
emit("## The claim, tested")
emit("")
lone_diffs = res["lone king at the root"][1]
other_diffs = res["no lone king"][1]
emit("| their statement | my measurement |")
emit("|---|---|")
emit("| lone-king roots DO diverge | **%d of %d** |" % (len(lone_diffs), res["lone king at the root"][0]))
emit("| no non-lone-king position diverges | **%d of %d** |" % (len(other_diffs), res["no lone king"][0]))
emit("")
if other_diffs:
    emit("**REFUTES the exclusivity**: %d non-lone-king position(s) differ, listed above. The divergence is not confined"
         % len(other_diffs))
    emit("to lone-king roots on my sample. This does not refute their counts on THEIR set; it refutes the general rule.")
elif lone_diffs:
    emit("**SUPPORTS the exclusivity**: every divergence I found is at a lone-king root, and none of the %d non-lone"
         % res["no lone king"][0])
    emit("positions differed. Their predicate holds on my independent sample.")
else:
    emit("**INCONCLUSIVE on my sample**: NO position differed at all, so I cannot test the exclusivity claim — with")
    emit("zero divergences there is nothing to confine. Stated rather than reported as agreement.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
