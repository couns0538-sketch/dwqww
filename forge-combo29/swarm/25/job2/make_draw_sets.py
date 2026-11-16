#!/usr/bin/env python3
"""make_draw_sets.py OUTDIR SEED : builds the five draw-score position groups + the control.

Group A: K v K, random non-adjacent kings
Group B: KN v K, group C: KB v K, group D: KNN v K
Group E: positions with a threefold repetition, given as a move list from startpos
Group F: halfmove clock at 99, from a RANDOM set of game positions
Control: K + Q v K (must not score 0)
All randomness from SEED, so the sets are reproducible from the seed alone.
"""
import os
import random
import sys

import chess

FILES = "abcdefgh"


def rand_sq(rng):
    return chess.square(rng.randrange(8), rng.randrange(8))


def kings_apart(rng, mindist=2):
    while True:
        wk, bk = rand_sq(rng), rand_sq(rng)
        if wk == bk:
            continue
        if max(abs(chess.square_file(wk) - chess.square_file(bk)),
               abs(chess.square_rank(wk) - chess.square_rank(bk))) < mindist:
            continue
        return wk, bk


def free_sq(rng, taken):
    while True:
        s = rand_sq(rng)
        if s not in taken:
            return s


def make_simple(rng, white_pieces):
    """white_pieces: list of (piece_type, ...) placed on random free squares.

    Generated until the position is legal (a bare-king setup can land in an impossible check);
    the loop is bounded so a bug cannot hang the job.
    """
    for _ in range(400):
        wk, bk = kings_apart(rng)
        taken = {wk, bk}
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        for pt in white_pieces:
            s = free_sq(rng, taken)
            taken.add(s)
            board.set_piece_at(s, chess.Piece(pt, chess.WHITE))
        board.turn = chess.WHITE
        board.clear_stack()
        if board.is_valid():
            return board
    raise RuntimeError("could not build a legal position")


def find_quick_cycle(b):
    """Find w1, b1, w2, b2 returning to the same position, cheaply and reliably.

    Direct construction instead of a 4-deep search: take a white piece that can move out and back
    (w1, w2), and a black piece that can move out and back (b1, b2), and verify the pair commute
    (neither move interferes with the other). Only a handful of move pairs are examined.
    """
    start = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)

    def same(bb):
        return (bb.board_fen(), bb.turn, bb.castling_rights, bb.ep_square) == start

    white_moves = list(b.legal_moves)
    for w1 in white_moves:
        if b.is_capture(w1) or b.gives_check(w1) or w1.promotion:
            continue
        b.push(w1)
        # a white move that takes the same piece back to where it came from is the cheap candidate
        back = [m for m in b.legal_moves
                if m.from_square == w1.to_square and m.to_square == w1.from_square
                and not b.is_capture(m) and not m.promotion]
        if back:
            w2 = back[0]
            b.push(w2)
            # now the black side must have a quick out-and-back of its own
            for b1 in list(b.legal_moves):
                if b.is_capture(b1) or b.gives_check(b1) or b1.promotion:
                    continue
                b.push(b1)
                back_b = [m for m in b.legal_moves
                          if m.from_square == b1.to_square and m.to_square == b1.from_square
                          and not b.is_capture(m) and not m.promotion]
                if back_b:
                    b2 = back_b[0]
                    b.push(b2)
                    ok = same(b)
                    b.pop()
                    if ok:
                        b.pop()
                        b.pop()
                        b.pop()
                        return w1, b1, w2, b2
                b.pop()
            b.pop()
        b.pop()
    return None


def four_ply_cycle(b):
    """A genuine 4-ply cycle [wo, bo, wr, br] that returns to the SAME position.

    Structure, with the side to move alternating correctly at each ply:
        wo  white moves a piece out      (now black to move)
        bo  black moves a piece out      (now white to move)
        wr  white moves that piece back  (now black to move)
        br  black moves that piece back  -> position must equal the start
    Verified by comparing the full position key after the 4th ply, so castling and ep changes are
    caught. Bounded: only the first 24 moves of each ply are examined.
    """
    start = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
    for wo in list(b.legal_moves)[:24]:
        if b.is_capture(wo) or wo.promotion:
            continue
        b.push(wo)
        for bo in list(b.legal_moves)[:24]:
            if b.is_capture(bo) or bo.promotion:
                continue
            b.push(bo)
            wr = [m for m in b.legal_moves
                  if m.from_square == wo.to_square and m.to_square == wo.from_square
                  and not m.promotion]
            if wr:
                b.push(wr[0])
                br = [m for m in b.legal_moves
                      if m.from_square == bo.to_square and m.to_square == bo.from_square
                      and not m.promotion]
                if br:
                    b.push(br[0])
                    ok = (b.board_fen(), b.turn, b.castling_rights, b.ep_square) == start
                    b.pop()
                    if ok:
                        b.pop(); b.pop(); b.pop()
                        return [wo, bo, wr[0], br[0]]
                b.pop()
            b.pop()
        b.pop()
    return None


def random_threefolds(rng, count):
    """Distinct games reaching a position repeated three times, by a real move list.

    Play a short random opening (this is what makes the games distinct), find a real 4-ply cycle,
    then play that cycle TWICE more: the position at the top of the cycle has then occurred three
    times. Every candidate is confirmed with python-chess's own `is_repetition(3)` before it is kept.

    Distinctness is by MOVE LIST: a threefold repeats a position by definition, so two different
    games legitimately share a final FEN, but the engine sees a different history each time.
    """
    good = []
    seen = set()
    for _ in range(count * 60):
        if len(good) >= count:
            break
        b = chess.Board()
        moves = []
        try:
            for _ in range(rng.choice([0, 2, 4, 6, 8])):
                legal = list(b.legal_moves)
                if not legal:
                    break
                mv = rng.choice(legal)
                b.push(mv)
                moves.append(mv.uci())
            cycle = four_ply_cycle(b)
            if cycle is None:
                continue
            for _ in range(3):
                for mv in cycle:
                    b.push(mv)
                    moves.append(mv.uci())
            if not b.is_repetition(3):
                continue
            key = tuple(moves)
            if key in seen:
                continue
            seen.add(key)
            good.append((key, b.fen()))
        except Exception:
            continue
    return good


def main():
    outdir = sys.argv[1]
    seed = int(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)

    groups = {
        "A_KvK": [],
        "B_KNvK": [],
        "C_KBvK": [],
        "D_KNNvK": [],
        "Control_KQvK": [],
    }
    for i in range(20):
        groups["A_KvK"].append(make_simple(rng, []))
        groups["B_KNvK"].append(make_simple(rng, [chess.KNIGHT]))
        groups["C_KBvK"].append(make_simple(rng, [chess.BISHOP]))
        groups["D_KNNvK"].append(make_simple(rng, [chess.KNIGHT, chess.KNIGHT]))
        groups["Control_KQvK"].append(make_simple(rng, [chess.QUEEN]))

    for name, boards in groups.items():
        path = os.path.join(outdir, name + ".fens")
        with open(path, "w") as f:
            for b in boards:
                f.write(b.fen() + "\n")
        print(name, "->", path, sum(1 for _ in open(path)), "positions")

    # E: threefold repetition, reached by a real move list, distinct games
    path = os.path.join(outdir, "E_threefold.moves")
    good = random_threefolds(rng, 20)
    with open(path, "w") as f:
        for seq, _fen in good:
            f.write(" ".join(seq) + "\n")
    print("E_threefold ->", path, len(good), "distinct games")
    for seq, fen in good[:3]:
        print("   e.g.", " ".join(seq), "->", fen)
    if len(good) < 20:
        print("WARNING: only", len(good), "distinct threefold games found")

    # F: halfmove clock 99, taken from game positions with the clock set to 99
    gpath = "/agent/repos/dwqww/forge-combo29/swarm/25/positions/set_G.epd"
    fens = [l.split(";")[0].strip() for l in open(gpath) if l.strip()]
    rng.shuffle(fens)
    path = os.path.join(outdir, "F_clock99.fens")
    written = 0
    with open(path, "w") as f:
        for fen in fens:
            parts = fen.split()
            if len(parts) != 6:
                continue
            b = chess.Board(fen)
            if not b.is_valid() or b.is_checkmate() or b.is_stalemate():
                continue
            parts[4] = "99"
            parts[5] = "1"
            f.write(" ".join(parts) + "\n")
            written += 1
            if written == 20:
                break
    print("F_clock99 ->", path, written, "positions")


if __name__ == "__main__":
    main()
