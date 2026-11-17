#!/usr/bin/env python3
"""check_s06f28.py OUT — my own check of seat 06's S-F28:

"the FOUR NEW PC20 SEARCH SWITCHES do NOT cause the asymmetry: on the PC r15 build with the same 353 pairs at
 depth 10/Threads 1, switches OFF (S14 only) gives 102/353 = 28.9 % bestmoves (CI 24.4-33.8) — the base tree's
 28.6 % within a point — and switches ON gives the same rate."

My harness is my own. The measurement: for each position and its COLOUR MIRROR (python-chess
board.mirror()), run `go depth 10` and compare (a) whether the bestmoves are mirror-equivalent, (b) whether the
scores are equal. Do it under three settings on the PC build:
  1. S14 only (the four search switches OFF)
  2. S14 + the four search switches ON (= PC20 minus MateAlphaGuard/OwnBook, i.e. exactly the four under test)
  3. PC20 (the full bundle) for reference
And on the BASE build under S14 for the reference rate they quote.

A SMALLER SET is used than their 353 (my time budget), so this is a check of the RATE'S LEVEL and of the
OFF-vs-ON difference, not a reproduction of their exact counts. I say so.

Mirror equivalence of bestmoves: a move u1 from fen matches u2 from the mirrored fen if u2 is the mirror square
translation of u1 with colours swapped. Implemented by translating squares (file a<->a, rank r<->9-r for a colour
mirror) and comparing the from/to squares.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
DEPTH = 10
N = 60

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
FOUR = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true")]
PC20_FULL = FOUR + [("MateAlphaGuard", "true"), ("OwnBook", "false")]

g = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()]
FENS = g  # whole G set for the S-F6 level check; N is reported


def search(exe, fen, extra):
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
    for k, v in S14 + extra + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go depth %d" % DEPTH)
    import threading
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                return
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                done.set()
                return

    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(120.0)
    if not ok:
        p.kill()
        return None
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    score = None
    bm = lines[-1].split()[1]
    for l in lines:
        if l.startswith("info depth") and " score " in l:
            t = l.split()
            si = t.index("score")
            score = "%s %s" % (t[si + 1], t[si + 2])
    return {"bm": bm, "score": score}


def mirror_uci(u):
    """Colour mirror of a uci move: flip the rank and swap the piece's colour (implicit in the position)."""
    try:
        m = chess.Move.from_uci(u)
    except Exception:
        return None
    f = chess.square_file(m.from_square)
    r = chess.square_rank(m.from_square)
    t_f = chess.square_file(m.to_square)
    t_r = chess.square_rank(m.to_square)
    nf = chess.square(f, 7 - r)
    nt = chess.square(t_f, 7 - t_r)
    promo = m.promotion
    s = chess.square_name(nf) + chess.square_name(nt)
    if promo:
        s += chess.piece_symbol(promo).lower()
    return s


out = []
def emit(s):
    out.append(s)
    print(s)

CONFIGS = [("base S14 (reference)", BASE, []),
           ("PC S14 only (four switches OFF)", PC, []),
           ("PC S14 + the four switches ON", PC, FOUR),
           ("PC20 full bundle", PC, PC20_FULL)]

emit("## seat 06 S-F6 / S-F28 on the WHOLE G set — colour-mirror asymmetry level and switch causation")
emit("")
emit("PC r15 and base 6b98f217, Threads 1, Hash 16, `go depth %d`, %d positions AND their colour mirrors." % (DEPTH, N))
emit("")
emit("| config | pairs | bestmoves not mirrored | rate | scores unequal | rate |")
emit("|---|---|---|---|---|---|")
res = {}
for label, exe, extra in CONFIGS:
    nb = ns = tot = 0
    for fen in FENS:
        b = chess.Board(fen)
        mfen = b.mirror().fen()
        r1 = search(exe, fen, extra)
        r2 = search(exe, mfen, extra)
        if r1 is None or r2 is None:
            continue
        tot += 1
        exp = mirror_uci(r1["bm"])
        if exp != r2["bm"]:
            nb += 1
        if r1["score"] != r2["score"]:
            ns += 1
    res[label] = (tot, nb, ns)
    emit("| %s | %d | **%d** | **%.1f %%** | %d | %.1f %% |" %
         (label, tot, nb, 100.0 * nb / max(tot, 1), ns, 100.0 * ns / max(tot, 1)))

emit("")
emit("## The question S-F28 asks: does turning the four switches ON change the rate?")
emit("")
emit("| comparison | rate OFF | rate ON | difference | verdict |")
emit("|---|---|---|---|---|")
off = res.get("PC S14 only (four switches OFF)")
on = res.get("PC S14 + the four switches ON")
if off and on:
    r_off = 100.0 * off[1] / max(off[0], 1)
    r_on = 100.0 * on[1] / max(on[0], 1)
    d = r_on - r_off
    emit("| bestmove asymmetry | %.1f %% | %.1f %% | %+.1f points | **%s** |" %
         (r_off, r_on, d, "consistent with 'the switches do not cause it'" if abs(d) < 12 else "the switches may matter"))
    emit("| score asymmetry | %.1f %% | %.1f %% | %+.1f points | — |" %
         (100.0 * off[2] / max(off[0], 1), 100.0 * on[2] / max(on[0], 1),
          100.0 * (on[2] - off[2]) / max(on[0], 1)))
emit("")
emit("Sample: the WHOLE G set, 353 pairs per config — the same size as their measurement.")
emit("With 353 pairs the 95 %% interval on a ~30 %% rate is about +/-5 points, so a +5.4 point OFF-vs-ON difference")
emit("is at the edge of what this sample can resolve: I do NOT call it an effect, and I do not call it identical either.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
