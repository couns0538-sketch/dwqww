#!/usr/bin/env python3
"""mechanism_variants.py OUT — does the "both waiting" pattern survive with the bare-king switches toggled?

08-W2 found that of the 11 lone-king divergences, 8 have BOTH base and PC moves WAITING, 2 are base-PROBING ->
PC-WAITING, 1 reverses. I hypothesised that a move-ORDERING change would explain "both waiting, different one
picked", and named seat 03's build variants as the instrument. This runs that instrument.

Variants (all from the same PC r15 source, one switch toggled, pins verified identical at 312,866 so they are the
same engine):
  V0  shipped PC r15        BARE_KING_LMR_CAP=1, BARE_KING_ONE_THREAD=0
  V1  LMR_CAP off           BARE_KING_LMR_CAP=0, BARE_KING_ONE_THREAD=0
  V2  ONE_THREAD on         BARE_KING_LMR_CAP=1, BARE_KING_ONE_THREAD=1
  B   base 6b98f217

For each of the 11 boards I record the move each of V1 and V2 plays, and classify it with the same PROBING/WAITING
test as 08-W2. The question: does the both-waiting pattern persist in the variants, or does a variant turn some into
probing moves (which would implicate that switch's ordering effect)?

ARGUMENT ORDER: OUT first.
"""
import re
import subprocess
import sys

import chess

OUT = sys.argv[1]
V0 = "/home/ubuntu/builds/pc/forge"
V1 = "/home/ubuntu/builds/v_nocap/forge"
V2 = "/home/ubuntu/builds/v_onethr/forge"
BASE = "/home/ubuntu/builds/release/forge"
DEPTH = 8


def load_boards():
    txt = open("check_s03f13.txt").read()
    rows = []
    for line in txt.splitlines():
        m = re.match(r"\| lone king at the root \| ([^|]+) \| ([a-h][1-8][a-h][1-8][qrbn]?) \| ([a-h][1-8][a-h][1-8][qrbn]?) \|", line)
        if m:
            rows.append((m.group(1).strip(), m.group(2), m.group(3)))
    return rows


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


def classify(fen, uci):
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(uci)
    except Exception:
        return "?"
    if m not in b.legal_moves:
        return "ILLEGAL"
    orig = chess.Board(fen)
    cap = orig.piece_at(m.to_square) is not None
    after = chess.Board(fen)
    after.push(m)
    chk = after.is_check()
    before_att = set(orig.attacks(m.from_square)) if orig.piece_at(m.from_square) else set()
    p1 = after.piece_at(m.to_square)
    after_att = set(after.attacks(m.to_square)) if p1 is not None else set()
    enemy = chess.BLACK if orig.turn == chess.WHITE else chess.WHITE
    newatt = any(after.piece_at(s) is not None and after.piece_at(s).color == enemy for s in (after_att - before_att))
    return "PROBING" if (chk or cap or newatt) else "WAITING"


out = []
def emit(s):
    out.append(s)
    print(s)

boards = load_boards()
emit("## Mechanism variants — does the both-waiting pattern survive toggling the bare-king switches?")
emit("")
emit("Depth %d, Threads 1, Hash 16. V0 shipped, V1 = LMR_CAP off, V2 = ONE_THREAD on, B = base.")
emit("")
emit("| fen | B | V0 (shipped) | V1 (cap off) | V2 (1-thread on) | V0 class | V1 class | V2 class |")
emit("|---|---|---|---|---|---|---|---|")
moves = []
for fen, bm_base, bm_pc in boards:
    v0 = best(V0, fen)
    v1 = best(V1, fen)
    v2 = best(V2, fen)
    c0, c1, c2 = classify(fen, v0), classify(fen, v1), classify(fen, v2)
    moves.append((fen, bm_base, v0, v1, v2, c0, c1, c2))
    emit("| %s | %s | %s | %s | %s | %s | %s | %s |" %
         (fen[:34], bm_base, v0, v1, v2, c0, c1, c2))

emit("")
emit("## Pattern counts per build")
emit("")
emit("| build | both WAITING | base-PROBING -> it-WAITING | other |")
emit("|---|---|---|---|")
for idx, label in ((2, "V0 shipped"), (3, "V1 cap off"), (4, "V2 1-thread on")):
    bw = pw = other = 0
    for fen, bm_base, v0, v1, v2, c0, c1, c2 in moves:
        cb = classify(fen, bm_base)
        cm = (c0, c1, c2)[idx - 2]
        if cb == "WAITING" and cm == "WAITING":
            bw += 1
        elif cb == "PROBING" and cm == "WAITING":
            pw += 1
        else:
            other += 1
    emit("| %s | **%d** | %d | %d |" % (label, bw, pw, other))

emit("")
emit("## Verdict")
emit("")
emit("| question | answer |")
emit("|---|---|")
same_v0_v1 = sum(1 for m in moves if m[2] == m[3])
same_v0_v2 = sum(1 for m in moves if m[2] == m[4])
emit("| V1 (cap off) plays the SAME move as V0 | %d of %d |" % (same_v0_v1, len(moves)))
emit("| V2 (1-thread on) plays the SAME move as V0 | %d of %d |" % (same_v0_v2, len(moves)))
emit("")
if same_v0_v1 == len(moves) and same_v0_v2 == len(moves):
    emit("**Neither switch changes any of these 11 moves** — so the both-waiting pattern is not caused by an ordering")
    emit("effect of these two switches, and my ordering hypothesis is KILLED. The divergences come from something else")
    emit("in the patch (the four search switches, or a pruning change), and I have not identified it.")
else:
    emit("**At least one switch does change moves here** (V1 differs on %d boards, V2 on %d), so the ordering"
         % (len(moves) - same_v0_v1, len(moves) - same_v0_v2))
    emit("hypothesis is not eliminated by this test — see the table for which boards.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
