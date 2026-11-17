#!/usr/bin/env python3
"""rule_negative.py EXE -- S-F73's rule on LOST positions (mate -N) specifically.

All my supporting data is skewed: of the 28 lines I split by sign, 21 were `mate +N` and only 7 `mate -N`. A pipeline
that consumes labels cares about both — "I am mating" and "I am being mated" are different labels — so the rule needs
its own test on lost positions.

This builds positions where the SIDE TO MOVE is lost (black to move, white has the extra material), searches a depth
ladder, and replays every `mate -N` line.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
NPOS = int(sys.argv[2]) if len(sys.argv) > 2 else 10

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


def replay_from(fen, moves, mover_is_black):
    """the mate may be delivered by either side; just replay and ask if the final position is checkmate"""
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


def gen_lost(n):
    """black to move, white has queen or rook extra: black is the side being mated"""
    R = random.Random(292929)
    out = []
    tries = 0
    while len(out) < n and tries < 300000:
        tries += 1
        b = chess.Board(None)
        sqs = R.sample(list(chess.SQUARES), 5)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sqs[2], chess.Piece(R.choice([chess.QUEEN, chess.ROOK]), chess.WHITE))
        if R.random() < 0.4:
            b.set_piece_at(sqs[3], chess.Piece(chess.PAWN, chess.BLACK))
        b.turn = chess.BLACK
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.clear_stack()
        if not b.is_valid() or b.is_game_over(claim_draw=False):
            continue
        # white (the mating side) must not be in check — black is to move
        if b.is_attacked_by(chess.BLACK, b.king(chess.WHITE)):
            continue
        if b.legal_moves.count() < 4:
            continue
        out.append(b.fen())
    return out


pool = gen_lost(NPOS)
print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   fresh process per (position, depth)")
print(f"{len(pool)} BLACK-to-move (losing) positions x depths 6..20; every mate -N line replayed.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

rows = []
for fen in pool:
    for d in range(6, 21):
        r = run(fen, d)
        if not r or r["kind"] != "mate" or r["val"] == 0:
            continue
        n = r["val"]
        need = 2 * abs(n) - 1 if n > 0 else 2 * abs(n)
        complete = len(r["moves"]) == need
        ok, nply = replay_from(fen, r["moves"], True)
        rows.append((fen, d, n, len(r["moves"]), need, complete, ok))

neg = [r for r in rows if r[2] < 0]
pos = [r for r in rows if r[2] > 0]
print(f"mate lines collected: {len(rows)}  (mate -N: {len(neg)}, mate +N: {len(pos)})")
print()
print("| sign | complete PV? | count | line mates? |")
print("|---|---|---|---|")
for label, subset in (("mate -N", neg), ("mate +N", pos)):
    for comp in (True, False):
        sub = [r for r in subset if r[5] == comp]
        if not sub:
            continue
        yes = sum(1 for r in sub if r[6])
        print(f"| {label} | {'yes' if comp else 'no'} | {len(sub)} | **{yes} yes, {len(sub)-yes} no** |")
print()
viol = [r for r in rows if r[5] != r[6]]
print(f"violations of S-F73's rule: {len(viol)} of {len(rows)}")
for r in viol:
    print(f"  depth {r[1]} mate {r[2]:+d} pv {r[3]}/{r[4]} complete={r[5]} mates={r[6]}  {r[0]}")
