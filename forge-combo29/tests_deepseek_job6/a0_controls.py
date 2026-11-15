#!/usr/bin/env python3
"""Job 6 A0: controls that must pass BEFORE any engine result counts.

1. the reader: 1,000 random legal KQvK and 1,000 KRvK positions with the strong side
   to move must all be wins in my retrograde table;
2. the counter: run the counting code with a player that picks a RANDOM legal move (it
   must report many lost half points) and with a player that picks a tablebase-best move
   (it must report 0).

Usage: a0_controls.py <tables.json> <out.json> <seed>
"""
import json
import random
import sys

import chess


def class_key(board):
    return board.board_fen() + (" w" if board.turn else " b")


def kind_of(board):
    men = [s for s in chess.SQUARES
           if board.piece_at(s) and board.piece_at(s).piece_type != chess.KING]
    if len(men) != 1:
        return None
    pt = board.piece_at(men[0]).piece_type
    return {chess.QUEEN: "KQvK", chess.ROOK: "KRvK", chess.PAWN: "KPvK"}.get(pt)


def strong_colour(board):
    for s in chess.SQUARES:
        piece = board.piece_at(s)
        if piece and piece.piece_type != chess.KING:
            return piece.color
    return None


def random_positions(kind, count, rng):
    strong = {"KQvK": chess.QUEEN, "KRvK": chess.ROOK, "KPvK": chess.PAWN}[kind]
    out, seen = [], set()
    guard = 0
    while len(out) < count and guard < count * 500:
        guard += 1
        wk, bk, s = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        if strong == chess.PAWN and chess.square_rank(s) in (0, 7):
            continue
        sw = rng.random() < 0.5
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(s, chess.Piece(strong, chess.WHITE if sw else chess.BLACK))
        b.castling_rights = 0
        b.ep_square = None
        b.halfmove_clock = 0
        b.turn = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        if not b.is_valid():
            continue
        b.turn = not b.turn
        bad = b.is_check()
        b.turn = not b.turn
        if bad or b.is_game_over():
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
    return out


def mover_wdl_after(board_after):
    if board_after.is_checkmate():
        return "W"
    if board_after.is_stalemate() or board_after.is_insufficient_material():
        return "D"
    return None


def evaluate_move(before_board, move, tables):
    b = before_board.copy()
    b.push(move)
    direct = mover_wdl_after(b)
    if direct is not None:
        return direct
    kind = kind_of(b)
    if kind is None or kind not in tables:
        return None
    after = tables[kind].get(class_key(b))
    if after is None:
        return None
    return {"W": "L", "L": "W", "D": "D"}[after]


def best_moves(board, tables):
    order = {"W": 3, "D": 2, "L": 1}
    scored = []
    for move in board.legal_moves:
        v = evaluate_move(board, move, tables)
        if v is not None:
            scored.append((order[v], move))
    if not scored:
        return []
    best = max(v for v, _ in scored)
    return [m for v, m in scored if v == best]


def count_failures(positions, tables, chooser, rng):
    stats = {"positions": 0, "wins": 0, "win_to_draw": 0, "win_to_loss": 0,
             "draws": 0, "draw_to_loss": 0, "undetermined": 0}
    for fen in positions:
        b = chess.Board(fen)
        kind = kind_of(b)
        if kind is None or kind not in tables:
            continue
        before = tables[kind].get(class_key(b))
        if before is None:
            continue
        move = chooser(b, tables, rng)
        if move is None:
            stats["undetermined"] += 1
            continue
        after = evaluate_move(b, move, tables)
        if after is None:
            stats["undetermined"] += 1
            continue
        stats["positions"] += 1
        if before == "W":
            stats["wins"] += 1
            if after == "D":
                stats["win_to_draw"] += 1
            elif after == "L":
                stats["win_to_loss"] += 1
        elif before == "D":
            stats["draws"] += 1
            if after == "L":
                stats["draw_to_loss"] += 1
    return stats


def chooser_random(board, tables, rng):
    moves = list(board.legal_moves)
    return rng.choice(moves) if moves else None


def chooser_best(board, tables, rng):
    best = best_moves(board, tables)
    return rng.choice(best) if best else None


def main():
    tables_path, out_path, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    rng = random.Random(seed)
    with open(tables_path) as f:
        tables = json.load(f)

    reader = {}
    for kind in ("KQvK", "KRvK"):
        if kind not in tables:
            continue
        positions = random_positions(kind, 1000, rng)
        checked = 0
        bad = []
        for fen in positions:
            b = chess.Board(fen)
            b.turn = strong_colour(b)
            if not b.is_valid() or b.is_stalemate():
                continue
            checked += 1
            v = tables[kind].get(class_key(b))
            if v != "W":
                bad.append({"key": class_key(b), "value": v})
        reader[kind] = {"checked": checked, "not_win": len(bad),
                        "examples": bad[:5]}

    positions = random_positions("KQvK", 2000, rng)
    random_stats = count_failures(positions, tables, chooser_random, rng)
    best_stats = count_failures(positions, tables, chooser_best, rng)

    out = {"seed": seed, "reader": reader,
           "counter_random_player": random_stats,
           "counter_tablebase_best_player": best_stats}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
