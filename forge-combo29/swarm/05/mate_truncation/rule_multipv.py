#!/usr/bin/env python3
"""rule_multipv.py EXE -- does S-F73's rule hold for EVERY PV when MultiPV > 1?

Seat 07 (07-C49) showed MultiPV silently shrinks a fixed node budget, so lines behave differently under MultiPV. My rule
was validated only at MultiPV 1. Under MultiPV the engine prints several `info ... multipv k ... pv ...` lines per
depth — each carries its own score and its own PV, and the rule should apply to EACH INDEPENDENTLY.

Test: for each position, search at `go depth D` with `MultiPV 3`, then for EVERY multipv line that reports a mate score,
check whether that line's PV length equals 2|N|-1 and whether replaying it mates. A violation is any line where those
disagree.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
NPOS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
MPV = int(sys.argv[3]) if len(sys.argv) > 3 else 3
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 14

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
        "setoption name MateAlphaGuard value true",
        f"setoption name MultiPV value {MPV}"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=300):
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
        p.kill(); return None, None
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"):
            p.kill(); return None, None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}")
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    if not ok:
        return None, None
    mpv = re.search(r"multipv (\d+)", L[0] if L else "")
    return L, mpv


def last_per_multipv(L):
    """the LAST line for each multipv index at the deepest depth reached"""
    out = {}
    for l in L:
        if " pv " not in l:
            continue
        m = re.search(r"multipv (\d+)", l)
        k = int(m.group(1)) if m else 1
        out[k] = l          # later lines overwrite earlier, so we keep the deepest
    return out


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
    R = random.Random(737373)
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
        if b.legal_moves.count() < 8:
            continue
        out.append(b.fen())
    return out


pool = gen_pool(NPOS)
print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false, **MultiPV {MPV}**")
print(f"{len(pool)} positions at go depth {DEPTH}; every multipv mate line replayed independently.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| position | multipv | score | pv plies | needed | complete? | mates? | rule holds? |")
print("|---|---|---|---|---|---|---|---|")

rows = []
for fen in pool:
    L, _ = run(fen, DEPTH)
    if not L:
        continue
    per = last_per_multipv(L)
    for k in sorted(per):
        line = per[k]
        m = re.search(r"score (mate|cp) (-?\d+)", line)
        if not m or m.group(1) != "mate" or int(m.group(2)) == 0:
            continue
        n = int(m.group(2))
        need = 2 * abs(n) - 1 if n > 0 else 2 * abs(n)
        moves = line.split(" pv ", 1)[1].split()
        complete = len(moves) == need
        mates, nply = replay(fen, moves)
        holds = (complete == mates)
        rows.append((fen, k, n, len(moves), need, complete, mates, holds))
        print(f"| {fen[:30]} | {k} | mate {n:+d} | {len(moves)} | {need} | "
              f"{'yes' if complete else 'NO'} | {'yes' if mates else 'NO'} | "
              f"{'ok' if holds else '**VIOLATION**'} |")

print()
ok = sum(1 for r in rows if r[7])
print(f"multipv mate lines collected: {len(rows)}")
print(f"rule holds: {ok} of {len(rows)}; violations: {len(rows)-ok}")
if len(rows) == 0:
    print("NOTE: no multipv mate lines were produced at this depth — the test measures nothing and is reported as such.")
