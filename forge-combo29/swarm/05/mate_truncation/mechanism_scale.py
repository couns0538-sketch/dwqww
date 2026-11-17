#!/usr/bin/env python3
"""mechanism_scale.py EXE N -- S-F74's mechanism on a WIDER sample.

S-F74 claims: the truncation is exactly the first iteration that reports a mate, and it clears one ply later. Evidence
was 4 positions (3 truncated at first mate, 0 later). This scales that: find N positions that report a mate at some
depth in 6..22, record the first mate depth and whether THAT line is complete, and whether any LATER depth truncates.

Prediction from S-F74:
  * a truncated first mate line always becomes complete at the very next depth
  * no depth AFTER the first mate line is ever truncated
  * a position whose first mate line is already complete never truncates at all
A single violation refutes S-F74.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 20
DEPTHS = range(6, 23)

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
    return dict(kind=m.group(1), val=int(m.group(2)), plies=len(moves))


def gen_pool(n):
    """mate-rich sparse positions: KQ or KR with a black pawn/rook, which produce mates at moderate depth"""
    R = random.Random(616161)
    out = []
    tries = 0
    while len(out) < n and tries < 400000:
        tries += 1
        b = chess.Board(None)
        sqs = R.sample(list(chess.SQUARES), 6)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        piece = R.choice([chess.QUEEN, chess.ROOK])
        b.set_piece_at(sqs[2], chess.Piece(piece, chess.WHITE))
        if R.random() < 0.6:
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


pool = gen_pool(240)
print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   fresh process per (position, depth)")
print(f"pool {len(pool)}; want {TARGET} positions that report a mate within depth {DEPTHS.start}..{DEPTHS.stop-1}")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

results = []
scanned = 0
for fen in pool:
    if len(results) >= TARGET:
        break
    scanned += 1
    ladder = []
    found_mate = False
    for d in DEPTHS:
        r = run(fen, d)
        if r is None:
            continue
        if r["kind"] == "mate" and r["val"] != 0:
            need = 2 * abs(r["val"]) - 1 if r["val"] > 0 else 2 * abs(r["val"])
            ladder.append((d, r["val"], r["plies"], need, r["plies"] == need))
            found_mate = True
        elif found_mate:
            # once a mate is found, a later cp score would be odd; record it as None-complete
            ladder.append((d, None, r["plies"], None, None))
    if ladder:
        results.append((fen, ladder))
        first = ladder[0]
        later_trunc = [x[0] for x in ladder[1:] if x[4] is False]
        print(f"  {fen[:44]:46s} first mate d{first[0]:2d} "
              f"{'TRUNC' if first[4] is False else 'ok  '}  later-truncated={later_trunc if later_trunc else 'none'}")

print()
print(f"scanned {scanned} positions; {len(results)} reported a mate in the depth window")
print()
print("| # | first mate depth | first line | next depth complete? | later truncations |")
print("|---|---|---|---|---|")
viol = 0
for i, (fen, ladder) in enumerate(results, 1):
    first = ladder[0]
    if first[4] is False:
        nxt = ladder[1] if len(ladder) > 1 else None
        nxt_ok = (nxt[4] is True) if nxt else None
        later = [x[0] for x in ladder[2:] if x[4] is False]
    else:
        nxt_ok = "n/a"
        later = [x[0] for x in ladder[1:] if x[4] is False]
    viol += len(later)
    print(f"| {i} | {first[0]} | {'**TRUNC**' if first[4] is False else 'ok'} | {nxt_ok} | "
          f"{later if later else 'none'} |")

n_trunc_first = sum(1 for _, l in results if l[0][4] is False)
print()
print(f"SUMMARY: {len(results)} positions with a mate line.")
print(f"  truncated at FIRST mate line: {n_trunc_first}")
print(f"  truncated at any LATER depth: {viol}   <- S-F74 predicts 0")
print(f"  S-F74 prediction holds: {viol == 0}")
