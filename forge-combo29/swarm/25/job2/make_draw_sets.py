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


def find_cycle(b):
    """Find a pair of legal moves (m1, m2) that returns to the same position. None if no pair."""
    before = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
    for m1 in list(b.legal_moves):
        b.push(m1)
        for m2 in list(b.legal_moves):
            b.push(m2)
            now = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
            b.pop()
            if now == before:
                b.pop()
                return m1, m2
        b.pop()
    return None


def random_threefolds(rng, count):
    """Distinct games that reach a position repeated three times, reached by a real move list.

    Method: play a short random opening, find a pair of moves that returns to the same position, then
    play that pair three times. The third occurrence is a genuine threefold in the engine's history.
    Distinctness is by MOVE LIST (a threefold repeats a position by definition, so FENs coincide).
    """
    good = []
    seen = set()
    tries = 0
    while len(good) < count and tries < 5000:
        tries += 1
        b = chess.Board()
        moves = []
        try:
            for _ in range(rng.choice([2, 4, 6, 8])):
                legal = list(b.legal_moves)
                if not legal:
                    break
                mv = rng.choice(legal)
                b.push(mv)
                moves.append(mv.uci())
            if len(moves) < 2:
                continue
            cyc = find_cycle(b)
            if cyc is None:
                continue
            m1, m2 = cyc
            for _ in range(3):
                b.push(m1)
                moves.append(m1.uci())
                b.push(m2)
                moves.append(m2.uci())
            if not b.is_repetition(2):
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
