#!/usr/bin/env python3
"""check_s03f13_mechanism.py OUT — CHARACTERISE the 11 divergences, not just bound them.

The 11 lone-king divergences are all K+material vs bare-king endings, and several look like "base probes, PC waits".
That is a mechanism signature worth testing rather than eyeballing.

Definition used (computed with python-chess, before any engine runs):
  A move is PROBING if it attacks an enemy piece or gives check — i.e. it creates a concrete threat.
  A move is WAITING if it does none of those (a king shift, a rook to a neutral square).
For each of the 11 boards: classify the BASE move and the PC move.
Prediction to test: base = PROBING and PC = WAITING on the boards where the repair changed the choice.

This is a CHARACTERISATION test, so it can come out "no, it is not that simple" — and I report it either way.

The 11 boards are taken verbatim from check_s03f13.txt so this tests exactly the divergences already found.

ARGUMENT ORDER: OUT first.
"""
import re
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"


def load_divergences():
    txt = open("check_s03f13.txt").read()
    rows = []
    for line in txt.splitlines():
        m = re.match(r"\| lone king at the root \| ([^|]+) \| ([a-h][1-8][a-h][1-8][qrbn]?) \| ([a-h][1-8][a-h][1-8][qrbn]?) \|", line)
        if m:
            rows.append((m.group(1).strip(), m.group(2), m.group(3)))
    return rows


def classify(fen, uci):
    """PROBING if the move gives check or attacks a piece that was not attacked before, else WAITING."""
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(uci)
    except Exception:
        return "unparsable", {}
    if m not in b.legal_moves:
        return "ILLEGAL", {}
    b.push(m)
    detail = {"check": b.is_check(), "capture": False}
    # a capture was on the from-board, so re-derive from the original
    orig = chess.Board(fen)
    detail["capture"] = orig.piece_at(m.to_square) is not None
    # "attacks a piece": does the moved piece now attack an enemy piece that it did not attack before?
    b2 = chess.Board(fen)
    # squares attacked by the piece on its original square (before the move)
    before = set()
    p0 = b2.piece_at(m.from_square)
    if p0 is not None:
        before = set(b2.attacks(m.from_square))
    after_board = chess.Board(fen)
    after_board.push(m)
    p1 = after_board.piece_at(m.to_square)
    after = set(after_board.attacks(m.to_square)) if p1 is not None else set()
    enemy = chess.BLACK if orig.turn == chess.WHITE else chess.WHITE
    detail["new_attacks_piece"] = any(
        after_board.piece_at(s) is not None and after_board.piece_at(s).color == enemy
        for s in (after - before)
    )
    probing = detail["check"] or detail["capture"] or detail["new_attacks_piece"]
    return ("PROBING" if probing else "WAITING"), detail


out = []
def emit(s):
    out.append(s)
    print(s)

divs = load_divergences()
emit("## Mechanism characterisation of the %d lone-king divergences" % len(divs))
emit("")
emit("PROBING = gives check, captures, or newly attacks an enemy piece. WAITING = none of those.")
emit("")
emit("| fen | base move | class | PC move | class | pattern |")
emit("|---|---|---|---|---|---|")
counts = {}
for fen, bm, pm in divs:
    cb, db = classify(fen, bm)
    cp, dp = classify(fen, pm)
    counts[(cb, cp)] = counts.get((cb, cp), 0) + 1
    pattern = "base PROBES, PC WAITS" if (cb == "PROBING" and cp == "WAITING") else \
              ("both probe" if cb == cp == "PROBING" else
               ("both wait" if cb == cp == "WAITING" else "reverse (base waits, PC probes)"))
    emit("| %s | %s | %s | %s | %s | **%s** |" % (fen[:40], bm, cb, pm, cp, pattern))

emit("")
emit("## The claim, tested")
emit("")
emit("| pattern | boards |")
emit("|---|---|")
for (cb, cp), n in sorted(counts.items(), key=lambda kv: -kv[1]):
    emit("| base %s -> PC %s | **%d** |" % (cb, cp, n))

emit("")
n_pw = counts.get(("PROBING", "WAITING"), 0)
emit("")
if n_pw == len(divs) and divs:
    emit("**YES — the signature is uniform**: on ALL %d divergences the base build PROBES and the PC build WAITS."
         % len(divs))
    emit("That is a characterisation of the bare-king repair, not just a boundary: the repair converts a concrete")
    emit("threat-move into a waiting move in bare-king endings.")
elif n_pw > 0:
    others = ", ".join("%s->%s x%d" % (a, b, n) for (a, b), n in counts.items() if (a, b) != ("PROBING", "WAITING"))
    emit("**NO — the pattern is NOT the rule, and 'dominant' would overstate it.** Only %d of %d divergences are"
         % (n_pw, len(divs)))
    emit("base-PROBES -> PC-WAITS. The other %d are %s. In particular %d of %d have BOTH moves waiting, so the repair"
         % (len(divs) - n_pw, others, counts.get(("WAITING", "WAITING"), 0), len(divs)))
    emit("usually changes WHICH waiting move is played, not whether the move probes at all. The eyeball impression"
         "\nfrom a few boards was wrong and this test replaces it.")
else:
    emit("**NO** — the base-probes/PC-waits pattern does not hold on these boards (%s). The eyeball impression was wrong."
         % ", ".join("%s->%s x%d" % (a, b, n) for (a, b), n in counts.items()))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
