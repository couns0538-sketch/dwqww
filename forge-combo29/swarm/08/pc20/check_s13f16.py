#!/usr/bin/env python3
"""check_s13f16.py OUT — my own check of seat 13's S-F16:

"the built-in book's moves DIFFER from the engine's own choice on 12 of 16 opening plies, but score within
 -26 to +18 cp of the engine's preference."

This is a two-part claim: a COUNT (12 of 16 differ) and a SCORE BOUND (within -26..+18 cp). I can test both, and it
connects to my own 08-F12/F36 (how wide the book is).

Method: walk the same 16 opening plies by both routes.
  - BOOK route: OwnBook true, `go wtime 6000`, take the bestmove (which is the book move).
  - ENGINE route: OwnBook false, `go depth 18`, take the bestmove (the engine's own preference).
  Count differences. Then for the differing plies, compare the SCORE the engine gives the book move (via
  `go depth 18 searchmoves <bookmove>`) against the score of its own choice — that is the "how much worse is the
  book move" measure.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true")]
DEPTH = 18


def ask(fen, go, ownbook):
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
    for k, v in PC20 + [("Threads", "1"), ("Hash", "16")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go " + go)
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
        p.wait(timeout=30)
    except Exception:
        p.kill()
    score = None
    for l in lines:
        if l.startswith("info depth") and " score " in l:
            t = l.split()
            si = t.index("score")
            score = "%s %s" % (t[si + 1], t[si + 2])
    return {"bm": lines[-1].split()[1], "score": score}


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
        return (30000 - abs(v)) * (1 if v > 0 else -1)
    return None


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 13 S-F16 — do the book's moves differ from the engine's own choice, and by how much?")
emit("")
emit("PC r15 PC20, Threads 1, Hash 16. Book route = OwnBook true + `go wtime 6000`; engine route = OwnBook false + `go depth %d`." % DEPTH)
emit("")
emit("| ply | position | book move | engine move | differ? | engine score of own | engine score of book move | gap cp |")
emit("|---|---|---|---|---|---|---|---|")
b = chess.Board()
diffs = []
gaps = []
for ply in range(1, 17):
    fen = b.fen()
    book = ask(fen, "wtime 6000 btime 6000", True)
    eng = ask(fen, "go depth %d" % DEPTH, False)
    d = book["bm"] != eng["bm"]
    gap = None
    if d:
        # score the engine gives the BOOK move, via a restricted search of the same depth
        rb = ask(fen, "depth %d searchmoves %s" % (DEPTH, book["bm"]), False) if False else \
             ask(fen, "go depth %d searchmoves %s" % (DEPTH, book["bm"]), False)
        a, c = cp(eng["score"]), cp(rb["score"])
        if a is not None and c is not None:
            gap = c - a
            gaps.append(gap)
        diffs.append((ply, book["bm"], eng["bm"], gap))
    emit("| %d | %s | %s | %s | %s | %s | %s | %s |" %
         (ply, fen.split(" ")[0][:22], book["bm"], eng["bm"], "**YES**" if d else "no",
          eng["score"], (str(gap) if gap is not None else "-"), (str(gap) if gap is not None else "-")))
    try:
        b.push(chess.Move.from_uci(book["bm"]))
    except Exception:
        break

emit("")
emit("## The claim, tested")
emit("")
emit("| their statement | my measurement |")
emit("|---|---|")
emit("| book differs from the engine's choice on 12 of 16 plies | **%d of %d** |" % (len(diffs), 16))
if gaps:
    emit("| the difference is small: within -26 to +18 cp | **range %+d to %+d cp, median %+d** |" %
         (min(gaps), max(gaps), sorted(gaps)[len(gaps) // 2]))
emit("")
if gaps:
    inband = sum(1 for g in gaps if -26 <= g <= 18)
    emit("| their band (-26..+18 cp) | **%d of %d differing plies fall inside it** |" % (inband, len(gaps)))
    emit("")
    if inband == len(gaps):
        emit("**CONFIRMS in kind**: every differing ply's book move is scored within their stated band of the")
        emit("engine's own preference, so the book is not playing bad moves — it is playing near-equal ones.")
    else:
        emit("**PARTIAL**: %d of %d differ by more than their band, which would widen their claim rather than confirm"
             % (len(gaps) - inband, len(gaps)))
        emit("it. The out-of-band plies are listed in the table.")
else:
    emit("**No differing plies found**, so the score half is untested on my route — stated rather than reported as agreement.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
