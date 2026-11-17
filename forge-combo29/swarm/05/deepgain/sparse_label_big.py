#!/usr/bin/env python3
"""sparse_label_big.py EXE -- the sparse-endgame label test with a real denominator.

Three seats now agree on the direction (sparse gains mates from a deeper search, middlegames do not) but the counts are
8, 5 and 8 positions. This runs ~30 sparse endgames and ~30 middlegames, my own construction, my own build, COLD process
per search, and REPLAYS every mate it claims so a "gained mate" is only counted when the line actually mates.

Per position: clocked `go wtime 6000 btime 6000 winc 60 binc 60` -> (score, depth D); then `go depth D+4` on the same
board. Count:
  gained_label : clocked not mate, deeper reports mate      (what a training label would record)
  gained_real  : ... and the deeper PV REPLAYS into checkmate (what is actually true)
  false_mate   : ... and it does not replay into checkmate  (the truncation defect)
"""
import random
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
NPOS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
DPLUS = int(sys.argv[3]) if len(sys.argv) > 3 else 4

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


def build_sparse(n):
    """sparse endgames: 3-6 pieces, white clearly winning material (a mate must exist eventually).
    Constructed by random placement with validity checks, so the set is reproducible from the seed."""
    R = random.Random(90210)
    out = []
    tries = 0
    while len(out) < n and tries < 300000:
        tries += 1
        kind = R.choice(["KQ", "KR", "KQ", "KR", "KBB", "KQr", "KRp"])
        b = chess.Board(None)
        sqs = R.sample(list(chess.SQUARES), 6)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        if kind in ("KQ",):
            b.set_piece_at(sqs[2], chess.Piece(chess.QUEEN, chess.WHITE))
        elif kind in ("KR",):
            b.set_piece_at(sqs[2], chess.Piece(chess.ROOK, chess.WHITE))
        elif kind == "KBB":
            b.set_piece_at(sqs[2], chess.Piece(chess.BISHOP, chess.WHITE))
            b.set_piece_at(sqs[3], chess.Piece(chess.BISHOP, chess.WHITE))
        elif kind == "KQr":
            b.set_piece_at(sqs[2], chess.Piece(chess.QUEEN, chess.WHITE))
            b.set_piece_at(sqs[3], chess.Piece(chess.ROOK, chess.BLACK))
        elif kind == "KRp":
            b.set_piece_at(sqs[2], chess.Piece(chess.ROOK, chess.WHITE))
            b.set_piece_at(sqs[3], chess.Piece(chess.PAWN, chess.BLACK))
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.clear_stack()
        if not b.is_valid() or b.is_game_over(claim_draw=False):
            continue
        # black must not already be in check (white to move)
        if b.is_attacked_by(chess.WHITE, b.king(chess.BLACK)):
            continue
        # keep it sparse AND non-trivial: at least 8 legal white moves
        if b.legal_moves.count() < 8:
            continue
        out.append((f"{kind} #{len(out)+1}", b.fen()))
    return out


def build_mid(n):
    R = random.Random(777001)
    out = []
    tries = 0
    while len(out) < n and tries < 40000:
        tries += 1
        b = chess.Board()
        for _ in range(R.randint(18, 44)):
            lg = list(b.legal_moves)
            if not lg:
                break
            b.push(R.choice(lg))
        if b.is_game_over(claim_draw=False or b.is_check()):
            continue
        if len(b.piece_map()) < 20:
            continue
        if b.is_check():
            continue
        out.append((f"mid #{len(out)+1} ({len(b.piece_map())}pc)", b.fen()))
    return out


def search(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def u(t, lim=600):
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
        p.wait(timeout=90)
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


def median(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if not n:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def run_class(name, positions):
    label = real = false = 0
    moves = []
    print(f"### {name} ({len(positions)} positions)")
    print()
    print("| position | clocked | D | deeper | label? | real mate? | movement |")
    print("|---|---|---|---|---|---|---|")
    for lbl, fen in positions:
        c = search(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
        if c is None:
            print(f"| {lbl} | NO MEAS | - | - | - | - | - |")
            continue
        d = search(fen, f"go depth {c['depth'] + DPLUS}")
        if d is None:
            print(f"| {lbl} | {c['kind']} {c['val']:+d} | {c['depth']} | NO MEAS | - | - | - |")
            continue
        gained = (c["kind"] == "cp" and d["kind"] == "mate" and d["val"] != 0)
        realmate = "-"
        mv = "-"
        if gained:
            label += 1
            ok, nply = replay(fen, d["moves"])
            if ok:
                real += 1
                realmate = f"**YES** (ply {nply})"
            else:
                false += 1
                realmate = f"**NO** ({nply} plies, no mate)"
        else:
            a = c["val"] if c["kind"] == "cp" else None
            bb = d["val"] if d["kind"] == "cp" else None
            if a is not None and bb is not None:
                m = abs(bb - a)
                moves.append(m)
                mv = f"{m} cp"
        print(f"| {lbl} | {c['kind']} {c['val']:+d} | {c['depth']} | {d['kind']} {d['val']:+d} | "
              f"{'YES' if gained else 'no'} | {realmate} | {mv} |")
    print()
    print(f"**{name}: mate LABEL gained {label}/{len(positions)}; PV actually mates {real}; "
          f"mate label NOT delivered {false}; median movement on the rest {median(moves)} cp (n={len(moves)})**")
    print()
    return label, real, false, median(moves), len(moves), len(positions)


print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   COLD fresh process per search")
print(f"clock 6s+0.06 then go depth D+{DPLUS}   date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
sp = build_sparse(NPOS)
md = build_mid(NPOS)
print(f"constructed {len(sp)} sparse endgames and {len(md)} middlegames")
print()
sl, sr, sf, sm, sn, st = run_class("SPARSE ENDGAMES", sp)
ml, mr, mf, mm, mn, mt = run_class("MIDDLEGAMES", md)
print("=" * 96)
print(f"SPARSE : label {sl}/{st}  real {sr}  undelivered {sf}  median movement {sm} cp (n={sn})")
print(f"MIDDLE : label {ml}/{mt}  real {mr}  undelivered {mf}  median movement {mm} cp (n={mn})")
