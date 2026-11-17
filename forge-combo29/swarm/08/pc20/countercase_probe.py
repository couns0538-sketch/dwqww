#!/usr/bin/env python3
"""countercase_probe.py OUT — why do 2 of 11 boards show cap-OFF visiting MORE nodes?

08-F38 found cap-OFF visits fewer nodes on 9 of 11 boards (the clamping direction) but MORE on 2. The cap's gate
(patch lines ~1563-1574) fires at a NODE only when:
    root_bare_king_  AND  (White has only its king OR Black has only its king)
So a board where the lone-king condition disappears quickly below the root has a low cap FIRING RATE, and the cap
can have little or no effect — or an effect dominated by other pruning interactions.

This measures, per board, the FRACTION OF NODES in the legal tree (to a fixed depth) that satisfy the lone-king
condition. If the two counter-cases have markedly lower fractions than the nine, the counter-cases are explained by
the gate rather than being counter-examples to the mechanism.

ARGUMENT ORDER: OUT first.
"""
import re
import sys

import chess

OUT = sys.argv[1]
DEPTH = 4  # full legal tree; 4 is enough to see the material structure and cheap enough to count exactly


def load_nodes_table():
    """fen -> (v0 nodes, v1 nodes) from instrument_cap.txt"""
    rows = {}
    for line in open("instrument_cap.txt"):
        if not line.strip().startswith("|"):
            continue
        p = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(p) == 5 and " - - " in p[0]:
            try:
                rows[p[0]] = (int(p[1].replace(",", "")), int(p[2].replace(",", "")))
            except ValueError:
                pass
    return rows


def lone_king_at(b):
    for c in (0, 1):
        if b.occupied_co[c] == b.pieces(chess.KING, c):
            return True
    return False


def walk(b, depth, counts):
    counts["nodes"] += 1
    if lone_king_at(b):
        counts["lone"] += 1
    if depth == 0:
        return
    for m in b.legal_moves:
        b.push(m)
        walk(b, depth - 1, counts)
        b.pop()


out = []
def emit(s):
    out.append(s)
    print(s)

table = load_nodes_table()
emit("## Why do 2 boards show cap-OFF visiting MORE nodes? — the gate's firing rate")
emit("")
emit("The cap fires at a node only if the ROOT has a lone king AND that NODE has a side with only its king.")
emit("Fraction measured over the exact legal tree to depth %d." % DEPTH)
emit("")
emit("| board | V0 nodes | V1 nodes | Δ | lone-king node fraction | class |")
emit("|---|---|---|---|---|---|")
rows = []
for fen, (v0, v1) in table.items():
    b = chess.Board(fen)
    counts = {"nodes": 0, "lone": 0}
    walk(b, DEPTH, counts)
    frac = counts["lone"] / counts["nodes"] if counts["nodes"] else 0.0
    d = v1 - v0
    cls = "cap-OFF fewer (predicted)" if d < 0 else "cap-OFF MORE (counter-case)"
    rows.append((fen, frac, d, cls))
    emit("| %s | %s | %s | %+d | **%.1f %%** | %s |" %
         (fen[:34], f"{v0:,}", f"{v1:,}", d, 100 * frac, cls))

emit("")
emit("## Do the counter-cases have a lower firing rate?")
emit("")
emit("| class | boards | median lone-king node fraction |")
emit("|---|---|---|")
for cls in ("cap-OFF fewer (predicted)", "cap-OFF MORE (counter-case)"):
    fr = sorted(f for _, f, _, c in rows if c == cls)
    if fr:
        med = fr[len(fr) // 2]
        emit("| %s | %d | **%.1f %%** |" % (cls, len(fr), 100 * med))

pred = sorted(f for _, f, _, c in rows if c == "cap-OFF fewer (predicted)")
cnt = sorted(f for _, f, _, c in rows if c == "cap-OFF MORE (counter-case)")
emit("")
if pred and cnt:
    mp, mc = pred[len(pred) // 2], cnt[len(cnt) // 2]
    if mc < mp:
        emit("**The counter-cases DO have a lower lone-king node fraction** (%.1f %% vs %.1f %% median), which is" %
             (100 * mc, 100 * mp))
        emit("consistent with the gate explanation: where the lone-king condition disappears quickly below the root,")
        emit("the cap has less to act on and other pruning interactions can dominate. So they are boards where the")
        emit("mechanism is WEAK rather than boards that contradict it — though the fractions overlap and I do not")
        emit("claim a clean separation from 2 boards.")
    else:
        emit("**The firing rate does NOT separate them** (counter-cases %.1f %%, predicted %.1f %% median), so the gate" %
             (100 * mc, 100 * mp))
        emit("explanation does not hold on this measurement and the counter-cases remain unexplained — a second")
        emit("mechanism, as you said. I state that rather than forcing the gate story.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
