#!/usr/bin/env python3
"""probe_N1415.py EXE -- convert the |N| = 14/15 GAP from S-F70 into a BOUNDARY.

S-F70 pooled 12 gained mate labels from two sparse sets and found no overlap: every |N| <= 14 was delivered by its PV,
every |N| >= 15 was not. But no single set contained BOTH a 14 and a 15, so the boundary could sit anywhere in that gap
or the gap could be sampling luck.

This hunts specifically for gained mate labels at exactly |N| = 14 and |N| = 15 (and 13 and 16 as controls), then
replays each. Method per candidate: clocked search -> if it is cp, deeper search at D+4 -> if that reports mate N with
|N| in the wanted set, replay the PV and record delivered/not.

Screening a large pool is the only way (S-F61: these are rare), so positions are generated in bulk and filtered.
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
WANT = {13, 14, 15, 16}
NEEDED = {13: 1, 14: 2, 15: 2, 16: 1}     # how many of each we want before stopping
POOLMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 600

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


def run(fen, go):
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
    s(go)
    ok = u("bestmove")
    s("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    d = re.search(r"depth (\d+)", last)
    if not m or not d:
        return None
    moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
    return dict(kind=m.group(1), val=int(m.group(2)), depth=int(d.group(1)), moves=moves)


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
    """sparse, clearly winning positions: KR/KQ with a black pawn or rook, which produce long mates"""
    R = random.Random(515151)
    out = []
    tries = 0
    while len(out) < n and tries < 900000:
        tries += 1
        b = chess.Board(None)
        sqs = R.sample(list(chess.SQUARES), 5)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sqs[2], chess.Piece(chess.ROOK, chess.WHITE))
        b.set_piece_at(sqs[3], chess.Piece(R.choice([chess.PAWN, chess.ROOK]), chess.BLACK))
        if R.random() < 0.5:
            b.set_piece_at(sqs[4], chess.Piece(chess.PAWN, chess.BLACK))
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


pool = gen_pool(POOLMAX)
print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   COLD per search")
print(f"pool: {len(pool)} sparse KR/KQ positions. Hunting gained mate labels with |N| in {sorted(WANT)}.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

found = {}          # N -> list of (fen, delivered, pvlen)
scanned = 0
for fen in pool:
    scanned += 1
    if all(len(found.get(N, [])) >= NEEDED[N] for N in NEEDED):
        break
    c = run(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
    if c is None or c["kind"] != "cp":
        continue
    d = run(fen, f"go depth {c['depth'] + 4}")
    if d is None or d["kind"] != "mate" or d["val"] == 0:
        continue
    N = abs(d["val"])
    if N not in WANT:
        continue
    need = 2 * N - 1 if d["val"] > 0 else 2 * N
    ok, nply = replay(fen, d["moves"])
    found.setdefault(N, []).append((fen, ok, len(d["moves"]), need))
    print(f"  |N|={N}: clocked d{c['depth']} -> mate {d['val']:+d}, pv {len(d['moves'])}/{need}, "
          f"delivered={ok}")

print()
print(f"scanned {scanned} of {len(pool)} pool positions")
print()
print("| |N| | fen | pv plies | needed | delivered by PV? |")
print("|---|---|---|---|---|")
for N in sorted(found):
    for fen, ok, pl, need in found[N]:
        print(f"| {N} | {fen} | {pl} | {need} | {'**YES**' if ok else '**NO**'} |")
print()
tot = sum(len(v) for v in found.values())
yes = sum(1 for v in found.values() for _, ok, _, _ in v if ok)
print(f"gained labels found: {tot}; delivered: {yes}; not delivered: {tot - yes}")
for N in sorted(found):
    d = found[N]
    print(f"  |N|={N}: {sum(1 for _,ok,_,_ in d if ok)}/{len(d)} delivered")
