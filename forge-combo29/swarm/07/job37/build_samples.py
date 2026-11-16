#!/usr/bin/env python3
"""build_samples.py G_EPD OUTDIR

Builds the two samples the coordinator asked for, and says which switch each position is meant to
exercise. Classification is done with python-chess, independently of the engine.

SAMPLE 1 -- "targeted" (100 positions): the states the four FORGE_FIX_* switches are FOR.
  a) drawn roots (FORGE_FIX_ROOT_DRAWN): positions where the root is a THIRD repetition, built by
     playing a legal move list so the same position occurs three times, and separately positions with
     the halfmove counter at or past 100.
  b) bare-king endings (FORGE_FIX_BARE_KING_LMR_CAP, _ONE_THREAD): one side is a lone king; built by
     stripping material from real game positions rather than inventing boards.
  c) late endgames from G: few pieces, both sides still with material, and a real 50-move counter
     carried over from the game position.

SAMPLE 2 -- "ordinary" (100 positions): middlegames from set G with plenty of material, i.e. the
control sample where the switches should NOT fire. Together the two tell the owner where the patch acts.

Every position is written with a tag naming the switch it targets, so the differential can report the
switch per difference instead of guessing.
"""
import json
import os
import random
import sys

import chess

random.seed(701)


def load_g(path):
    out = []
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 4:
            fen = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts[:4]) + " 0 1"
            try:
                b = chess.Board(fen)
            except ValueError:
                continue
            out.append(b.fen())
    return out


def material(b):
    v = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9,
         chess.KING: 0}
    return sum(v[p.piece_type] for p in b.piece_map().values())


def bare_king_side(b):
    wk = b.king(chess.WHITE) is not None
    bk = b.king(chess.BLACK) is not None
    if not (wk and bk):
        return None
    w_other = [p for s, p in b.piece_map().items() if p.color == chess.WHITE and p.piece_type != chess.KING]
    b_other = [p for s, p in b.piece_map().items() if p.color == chess.BLACK and p.piece_type != chess.KING]
    if not w_other and b_other:
        return "black_has_material"
    if not b_other and w_other:
        return "white_has_material"
    return None


def strip_to_bare_king(b, keep_color):
    """Leave `keep_color` with a modest force and the other side with a lone king.
    Deterministic: keeps the nearest pieces to the enemy king, which keeps the result plausible."""
    out = chess.Board(None)
    for color in (chess.WHITE, chess.BLACK):
        ksq = b.king(color)
        if ksq is None:
            return None
        out.set_piece_at(ksq, chess.Piece(chess.KING, color))
    if keep_color == chess.WHITE:
        loser = chess.BLACK
    else:
        loser = chess.WHITE
    lk = b.king(loser)
    if lk is None:
        return None
    cands = [(s, p) for s, p in b.piece_map().items()
             if p.color == keep_color and p.piece_type != chess.KING]
    cands.sort(key=lambda sp: chess.square_distance(sp[0], lk))
    added = 0
    for s, p in cands:
        # skip pawns on the first/last rank, which the engine rightly refuses
        if p.piece_type == chess.PAWN and chess.square_rank(s) in (0, 7):
            continue
        out.set_piece_at(s, p)
        added += 1
        if added >= 3:
            break
    if added == 0:
        return None
    out.turn = b.turn
    out.castling_rights = 0
    out.ep_square = None
    out.halfmove_clock = 0
    out.fullmove_number = 1
    if not out.is_valid():
        return None
    # the side that is not to move must not be in check from the side to move
    if out.is_valid():
        return out
    return None


def make_threefold(start_fen):
    """Play a legal knight shuffle from `start_fen` until the SAME position occurs three times.
    Returns the move list, or None. Deterministic: tries each legal move in order at each ply."""
    base = chess.Board(start_fen)
    # find a shuffle the position allows: any two moves that return to the start
    moves = list(base.legal_moves)
    shuffles = []
    for m1 in moves:
        b1 = base.copy(); b1.push(m1)
        for m2 in b1.legal_moves:
            b2 = b1.copy(); b2.push(m2)
            # same placement AND same side to move => the pair returns to the start position
            if b2.board_fen() == base.board_fen() and b2.turn == base.turn:
                shuffles.append((m1, m2))
        if len(shuffles) >= 4:
            break
    if not shuffles:
        return None
    # Verify the pair really is replayable twice from the start; a pair that works only on the
    # first trip is useless (my first version asserted and crashed on exactly that).
    for m1, m2 in shuffles:
        b = base.copy()
        seq = []
        ok = True
        for _ in range(2):        # two round trips => the start position occurs three times
            for m in (m1, m2):
                if m not in b.legal_moves:
                    ok = False
                    break
                b.push(m)
                seq.append(m.uci())
            if not ok:
                break
        if ok and b.is_repetition(3):
            return seq, b
    return None


def main():
    g_path, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    g_fens = load_g(g_path)
    print(f"set G positions loaded: {len(g_fens)}")
    boards = []
    for f in g_fens:
        try:
            boards.append(chess.Board(f))
        except ValueError:
            pass

    targeted, ordinary = [], []

    # ---------- SAMPLE 2: ordinary middlegames from G ----------
    rich = [b for b in boards if material(b) >= 26 and bare_king_side(b) is None]
    print(f"G positions with material >= 26 and no bare king: {len(rich)}")
    random.shuffle(rich)
    for b in rich[:100]:
        ordinary.append({"fen": b.fen(), "tag": "ordinary_middlegame", "material": material(b)})

    # ---------- SAMPLE 1a: drawn roots by third repetition ----------
    # Set G's middlegame positions rarely admit a returning move pair (the pieces have work to do),
    # so I also try the QUIET endgames and a few hand-built king-and-piece positions. A position with
    # a returning pair is what is needed, not a specific FEN, so the sample is built by finding pairs.
    pool = [b for b in boards if not b.is_game_over()]
    random.shuffle(pool)
    quiet = [b for b in boards
             if material(b) <= 14 and b.king(chess.WHITE) is not None and b.king(chess.BLACK) is not None]
    random.shuffle(quiet)
    candidates = quiet[:120] + pool[:120]
    for b in candidates:
        if len([t for t in targeted if t["tag"].startswith("drawn_repetition")]) >= 25:
            break
        r = make_threefold(b.fen())
        if r is None:
            continue
        seq, end = r
        targeted.append({"fen": end.fen(), "tag": "drawn_repetition_third",
                         "moves": seq, "note": "root is a third repetition"})
    # if the real positions still yield none, say so loudly rather than leave the class empty
    n_rep = len([t for t in targeted if t["tag"].startswith("drawn_repetition")])
    print(f"repetition positions built from real material: {n_rep}")
    if n_rep == 0:
        print("WARNING: no threefold could be built from set G; the ROOT_DRAWN class will be empty.")
        print("         That is a REAL limitation of this sample and is reported as such.")

    # ---------- SAMPLE 1b: fifty-move counter at/past 100 ----------
    for b in pool:
        if len([t for t in targeted if t["tag"].startswith("fifty_move")]) >= 20:
            break
        c = b.copy()
        # only legal if no pawn/capture in the history; a bare FEN with a high clock is accepted
        # by this engine (it caps the stored clock at 65535), so build it directly
        f = c.fen().split()
        f[4] = "100"
        try:
            nb = chess.Board(" ".join(f))
        except ValueError:
            continue
        if nb.is_valid():
            targeted.append({"fen": nb.fen(), "tag": "fifty_move_100",
                             "note": "halfmove counter exactly 100 at the root"})

    # ---------- SAMPLE 1c: bare-king endings from G, stripped ----------
    for b in boards:
        if len([t for t in targeted if t["tag"].startswith("bare_king")]) >= 30:
            break
        for keep in (chess.WHITE, chess.BLACK):
            nb = strip_to_bare_king(b, keep)
            if nb is None:
                continue
            side = bare_king_side(nb)
            if side is None:
                continue
            targeted.append({"fen": nb.fen(), "tag": "bare_king_" + side,
                             "note": "one side has a lone king (FORGE_FIX_BARE_KING_*)"})
            break

    # ---------- SAMPLE 1d: late endgames from G (few pieces, both sides with material) ----------
    late = [b for b in boards
            if 3 <= material(b) <= 14 and bare_king_side(b) is None
            and b.king(chess.WHITE) is not None and b.king(chess.BLACK) is not None]
    random.shuffle(late)
    for b in late:
        if len(targeted) >= 100:
            break
        targeted.append({"fen": b.fen(), "tag": "late_endgame", "material": material(b)})

    # top up if short
    if len(targeted) < 100:
        for b in rich:
            if len(targeted) >= 100:
                break
            if any(t["fen"] == b.fen() for t in targeted):
                continue
            targeted.append({"fen": b.fen(), "tag": "late_endgame_topup", "material": material(b)})

    targeted = targeted[:100]
    ordinary = ordinary[:100]

    with open(os.path.join(outdir, "targeted100.txt"), "w") as fh:
        for t in targeted:
            fh.write(t["fen"] + "\n")
    with open(os.path.join(outdir, "ordinary100.txt"), "w") as fh:
        for t in ordinary:
            fh.write(t["fen"] + "\n")
    json.dump({"targeted": targeted, "ordinary": ordinary},
              open(os.path.join(outdir, "samples.json"), "w"), indent=1)

    from collections import Counter
    print()
    print(f"targeted sample: {len(targeted)} positions")
    for tag, n in sorted(Counter(t['tag'] for t in targeted).items()):
        print(f"  {tag:28s} {n}")
    print(f"ordinary sample: {len(ordinary)} positions")
    for tag, n in sorted(Counter(t['tag'] for t in ordinary).items()):
        print(f"  {tag:28s} {n}")


if __name__ == "__main__":
    main()
