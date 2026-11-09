#!/usr/bin/env python3
"""gen_warm_read_fixture.py - two-position warm rows where one read-side rule of SyzygyRule50 bit 1 decides. Bug hunter's finding H1.1: mutants of both rules survived the older fixtures.

usage: <venv python> -I -B gen_warm_read_fixture.py <tables> <out.tsv> --kind k0|mate [--rows 1500] [--seed 71]
Output rows: "<first fen>\t<second fen>", for tb_claims with TB_CLAIMS_WARM=2. A stored score crosses clocks only below clock 90 (score_usable), so every read here is at clock c <= 89.

kind k0, rule "a stored probe result (distance 0) is used at clock 0 only":
  P: 4 men, a table win or loss, distance d >= 12. First fen R: 5 men, clock 0, a capture leads to P, so the search of R probes P at clock 0 and stores distance 0.
  Second fen Q: P's position one reversible move earlier, at clock c - 1, with d + c >= 101: at clock c P is not a win or loss any more. Q -> P is among the root's best-ranked moves, so P is searched.
  With the rule broken the stored result is used at clock c, and the claim harness counts it wrong.

kind mate, rule "a stored mate that cannot be completed before move 100 is not used":
  P: 3 or 4 men, a table win or loss, distance d in 12..24, where a mate line has the table's distance. First fen Q at clock 0: the search of Q stores P's mate. Second fen: Q at clock c - 1 with c = 101 - d:
  at clock c the mate lands on half-move 101. With the rule off by one the stored mate is used, and the harness counts it wrong by d + c = 101. Rows where the search stores a longer mate stay inert.

Each row only sets up the read. Whether it happens shows in the harness's event counts and in the mutants (tools/mutants_read_side.sh).
"""
import argparse
import os
import random
import sys

import chess
import chess.syzygy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_warm_pred_fixture import predecessors  # noqa: E402

MATERIAL_K0 = ['KBN/K', 'KBB/K', 'KR/KB', 'KR/KN', 'KQ/KR', 'KQ/KB', 'KQ/KN', 'KR/KP', 'KQ/KP', 'KNP/K', 'KBP/K', 'KRP/K']
MATERIAL_MATE = ['KQ/K', 'KR/K', 'KQQ/K', 'KQR/K', 'KRR/K', 'KBB/K', 'KBN/K', 'KQB/K', 'KQN/K', 'KRB/K', 'KRN/K']
PIECE = {'K': chess.KING, 'Q': chess.QUEEN, 'R': chess.ROOK, 'B': chess.BISHOP, 'N': chess.KNIGHT, 'P': chess.PAWN}


def random_position(rnd, material):
    a, b = material.split('/')
    if rnd.random() < 0.5:
        white, black = a, b
    else:
        white, black = b, a
    board = chess.Board(None)
    squares = rnd.sample(list(chess.SQUARES), len(a) + len(b))
    i = 0
    for color, text in ((chess.WHITE, white), (chess.BLACK, black)):
        for ch in text:
            piece = PIECE[ch]
            sq = squares[i]
            i += 1
            if piece == chess.PAWN and chess.square_rank(sq) in (0, 7):
                return None
            board.set_piece_at(sq, chess.Piece(piece, color))
    board.turn = rnd.random() < 0.5
    board.halfmove_clock = 0
    board.fullmove_number = 1
    return board if board.is_valid() else None


def move_value(tb, board, move):
    """The move's signed distance from the root, as the root ranks count it: 0 draw, > 0 win, < 0 loss; zeroing moves 1, 101, 0, -101, -1; a mate 1."""
    zeroing = board.is_zeroing(move)
    child = board.copy(stack=False)
    child.push(move)
    if child.is_checkmate():
        return 1
    if child.is_stalemate() or child.is_insufficient_material() and tb.probe_wdl(child) == 0:
        return 0
    if zeroing:
        wdl = tb.probe_wdl(child)
        return {2: -1, 1: -101, 0: 0, -1: 101, -2: 1}[wdl]
    dtz = tb.probe_dtz(child)
    if dtz == 0:
        return 0
    return -dtz + 1 if dtz < 0 else -dtz - 1


def rank(value, counter):
    if value == 0:
        return 0
    d = abs(value)
    if value > 0:
        return 2000 if d + counter <= 99 else (900 if d + counter == 100 else 1000 - (d + counter))
    return -2000 if d + counter <= 100 else -1000 + (d + counter)


def kept_moves(tb, board):
    """The root's best-ranked moves at the board's clock."""
    moves = list(board.legal_moves)
    ranks = {m: rank(move_value(tb, board, m), board.halfmove_clock) for m in moves}
    best = max(ranks.values())
    return [m for m in moves if ranks[m] == best]


def capture_predecessors(p, rnd):
    """5-man positions at clock 0 from which a non-pawn capture gives p's position with p's side to move."""
    mover = not p.turn
    out = []
    for sq, piece in p.piece_map().items():
        if piece.color != mover or piece.piece_type == chess.PAWN:
            continue
        for frm in chess.SquareSet(chess.BaseBoard.attacks(p, sq)):
            if p.piece_at(frm) is not None:
                continue
            for captured in (chess.KNIGHT, chess.BISHOP, chess.ROOK):
                r = p.copy(stack=False)
                r.remove_piece_at(sq)
                r.set_piece_at(frm, piece)
                r.set_piece_at(sq, chess.Piece(captured, p.turn))
                r.turn = mover
                r.ep_square = None
                r.halfmove_clock = 0
                r.fullmove_number = 1
                if not r.is_valid():
                    continue
                m = chess.Move(frm, sq)
                if m in r.legal_moves:
                    out.append(r)
    rnd.shuffle(out)
    return out


def gen_k0(tb, rnd, want, f):
    n = tries = 0
    while n < want and tries < 40_000_000:
        tries += 1
        p = random_position(rnd, rnd.choice(MATERIAL_K0))
        if p is None or p.is_game_over() or len(p.piece_map()) != 4:
            continue
        if abs(tb.probe_wdl(p)) != 2:
            continue
        d = abs(tb.probe_dtz(p))
        if d < 12:
            continue
        c = 101 - d + rnd.randint(0, 3)
        if not 1 <= c <= 89:
            continue
        rows = capture_predecessors(p, rnd)
        if not rows:
            continue
        for q in predecessors(p, c - 1):
            if not q.is_valid() or q.is_game_over():
                continue
            kept = kept_moves(tb, q)
            hit = [m for m in kept if not q.is_zeroing(m) and q.board_fen() != '' and child_is(q, m, p)]
            if hit and len(kept) >= 2:
                f.write(rows[0].fen() + '\t' + q.fen() + '\n')
                n += 1
                break
    return n, tries


def child_is(q, move, p):
    child = q.copy(stack=False)
    child.push(move)
    return child.board_fen() == p.board_fen() and child.turn == p.turn


def gen_mate(tb, rnd, want, f):
    n = tries = 0
    while n < want and tries < 40_000_000:
        tries += 1
        p = random_position(rnd, rnd.choice(MATERIAL_MATE))
        if p is None or p.is_game_over() or abs(tb.probe_wdl(p)) != 2:
            continue
        d = abs(tb.probe_dtz(p))
        if not 12 <= d <= 24:
            continue
        c = 101 - d
        for q in predecessors(p, c - 1):
            if not q.is_valid() or q.is_game_over():
                continue
            if any(child_is(q, m, p) for m in kept_moves(tb, q)):
                first = q.copy(stack=False)
                first.halfmove_clock = 0
                first.fullmove_number = 1
                f.write(first.fen() + '\t' + q.fen() + '\n')
                n += 1
                break
    return n, tries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables')
    ap.add_argument('out')
    ap.add_argument('--kind', required=True, choices=('k0', 'mate'))
    ap.add_argument('--rows', type=int, default=1500)
    ap.add_argument('--seed', type=int, default=71)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    with chess.syzygy.open_tablebase(a.tables) as tb, open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        n, tries = (gen_k0 if a.kind == 'k0' else gen_mate)(tb, rnd, a.rows, f)
    print(f'kind {a.kind} rows {n} of {a.rows}, tries {tries}')
    return 0 if n == a.rows else 1


if __name__ == '__main__':
    sys.exit(main())
