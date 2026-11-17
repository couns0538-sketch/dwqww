#!/usr/bin/env python3
"""blindspot_wide.py EXE : try harder to demonstrate the PV-length filter's blind spot.

S-C32 tried five boards and could not demonstrate it: every PV that PASSED the length filter also had the correct
mate distance at a deeper search. That leaves the filter's blind spot as a caveat rather than a demonstrated limit.

This tries harder with a targeted construction: the blind spot requires a SHALLOW search to emit `mate N` with a
right-length PV that IS checkmate, while the TRUE distance is shorter than N. That happens when the search finds A
mate but not the FASTEST one - plausible when mate-in-k boards are searched at a depth where the shorter mate is
beyond the horizon but a longer one is inside it.

Construction: take positions with a KNOWN short mate (KQ vs K, KR vs K drawn from random layouts), search them at
LOW depth, and check whether a passing PV reports a longer distance than the deep reference. Low depth is the key -
S-C32 used softnodes 1000 which may already have been deep enough.
"""
import random
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]


def run(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv " in s:
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, []
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv


def passes(fen, mate, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False
        if mm not in b.legal_moves:
            return False
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    return b.is_checkmate() and len(pv) == need


BOARDS = []
rng = random.Random(2521)
kinds = [[chess.QUEEN, chess.ROOK], [chess.QUEEN], [chess.ROOK, chess.ROOK]]
for _ in range(4000):
    w = list(rng.choice(kinds))
    sqs = rng.sample(range(64), 2 + len(w))
    b = chess.Board(None)
    b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
    for i, pt in enumerate(w):
        b.set_piece_at(sqs[2 + i], chess.Piece(pt, chess.WHITE))
    b.turn = chess.WHITE
    b.clear_stack()
    if b.is_valid() and not b.is_game_over(claim_draw=False) and not b.is_insufficient_material():
        f = b.fen()
        if f not in BOARDS:
            BOARDS.append(f)
    if len(BOARDS) >= 25:
        break

print("### trying to DEMONSTRATE the PV-length filter's blind spot (low depths, known-short mates)")
print(f"{'board':<40} {'shallow d8':>22} {'ref d24':>16}  blind spot?")
found = []
for fen in BOARDS:
    m1, pv1 = run(fen, "go depth 8")
    if m1 is None:
        continue
    ok = passes(fen, m1, pv1)
    m2, pv2 = run(fen, "go depth 24")
    if not ok:
        continue                      # the filter already rejects it - not a blind spot
    if m2 is None:
        continue
    blind = (m1 > 0 and m2 > 0 and m2 < m1)
    tag = "YES" if blind else ""
    print(f"{fen[:40]:<40} {('mate ' + str(m1)):>22} {('mate ' + str(m2)):>16}  {tag}")
    if blind:
        found.append((fen, m1, m2))

print()
if found:
    print(f"BLIND SPOT DEMONSTRATED on {len(found)} boards: a depth-8 search PASSED the length filter (right length,")
    print("ending in checkmate) while the true distance was shorter:")
    for fen, m1, m2 in found:
        print(f"  {fen}: shallow mate {m1} passes the filter, true mate {m2}")
    print("So the filter removes undeliverable claims but can PASS an over-long one - the caveat is now a demonstrated limit.")
else:
    print("Not demonstrated on these boards either. The caveat stays a caveat: a passing score was again always correct")
    print("at the deeper depth, so I have not shown the filter can pass a wrong distance - only that it has not been")
    print("shown incapable of it.")
