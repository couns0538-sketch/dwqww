#!/usr/bin/env python3
"""rule_every_depth.py EXE -- S-F73's rule at EVERY depth, not one line per position.

S-F73: "a line whose PV is shorter than 2|N|-1 does not mate; a complete one does" — 63 of 63 on lines collected at
specific budgets. This tests it on EVERY mate line a ladder produces: for each position, `go depth 6..20` in a fresh
process per depth, and for every line that reports a mate, REPLAY its PV and compare the rule's prediction with reality.
That is many more lines than before and at depths no earlier run covered.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
NPOS = int(sys.argv[2]) if len(sys.argv) > 2 else 12

OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
        "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
        "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
        "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
        "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
        "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
        "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=200):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip(); L.append(l)
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci")
    if not u("uciok"):
        p.kill(); return None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill(); return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}")
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return None
    moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
    return dict(kind=m.group(1), val=int(m.group(2)), moves=moves)


def replay(fen, moves):
    b = chess.Board(fen)
    for i, uci in enumerate(moves):
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            return False, i
        if mv not in b.legal_moves:
            return False, i
        b.push(mv)
    return b.is_checkmate(), len(moves)


def gen_pool(n):
    R = random.Random(818181)
    out = []
    tries = 0
    while len(out) < n and tries < 200000:
        tries += 1
        b = chess.Board(None)
        sqs = R.sample(list(chess.SQUARES), 5)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sqs[2], chess.Piece(R.choice([chess.QUEEN, chess.ROOK]), chess.WHITE))
        if R.random() < 0.5:
            b.set_piece_at(sqs[3], chess.Piece(R.choice([chess.PAWN, chess.ROOK]), chess.BLACK))
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.clear_stack()
        if not b.is_valid() or b.is_game_over(claim_draw=False):
            continue
        if b.is_attacked_by(chess.WHITE, b.king(chess.BLACK)):
            continue
        if b.legal_moves.count() < 6:
            continue
        out.append(b.fen())
    return out


pool = gen_pool(NPOS)
print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   fresh process per (position, depth)")
print(f"{len(pool)} positions x depths 6..20; EVERY mate line replayed.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

rows = []
for fen in pool:
    for d in range(6, 21):
        r = run(fen, d)
        if not r or r["kind"] != "mate" or r["val"] == 0:
            continue
        need = 2 * abs(r["val"]) - 1 if r["val"] > 0 else 2 * abs(r["val"])
        complete = len(r["moves"]) == need
        ok, nply = replay(fen, r["moves"])
        rows.append((fen, d, r["val"], len(r["moves"]), need, complete, ok))

print(f"mate lines collected: {len(rows)}")
print()
print("| complete PV? | count | line mates? |")
print("|---|---|---|")
c_ok = sum(1 for r in rows if r[5] and r[6])
c_no = sum(1 for r in rows if r[5] and not r[6])
i_ok = sum(1 for r in rows if not r[5] and r[6])
i_no = sum(1 for r in rows if not r[5] and not r[6])
print(f"| yes | {c_ok + c_no} | **{c_ok} yes, {c_no} no** |")
print(f"| no  | {i_ok + i_no} | **{i_ok} yes, {i_no} no** |")
print()
total_agree = c_ok + i_no
print(f"S-F73's rule holds on {total_agree} of {len(rows)} lines; violations: {c_no + i_ok}")
if c_no or i_ok:
    print()
    print("VIOLATIONS (each one refutes the rule as stated):")
    for r in rows:
        if (r[5] and not r[6]) or (not r[5] and r[6]):
            print(f"  depth {r[1]} mate {r[2]:+d} pv {r[3]}/{r[4]} complete={r[5]} mates={r[6]}  {r[0]}")
