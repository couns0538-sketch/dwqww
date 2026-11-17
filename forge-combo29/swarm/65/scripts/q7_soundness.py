#!/usr/bin/env python3
"""Q7: is any book move illegal, or does any book move lose material?

Input is the TSV produced by scripts/probe_book.cpp:

    /tmp/probe_book 40 > /tmp/book_full.txt

Checks, per book position:
  1. python-chess accepts the FEN (an illegal FEN makes every downstream claim
     meaningless).
  2. the engine's polyglot key equals chess.polyglot.zobrist_hash(), i.e. the
     book is keyed the way the format says.
  3. every book move is legal, judged by python-chess, an independent move
     generator from the engine's own board.cpp.
  4. the move does not hand over material: SEE of the opponent's best capture in
     the resulting position. The swap list only ever uses legally playable
     captures, so a pinned attacker cannot prop up a false defence.

Exit code is 1 when any hard-defect category is non-empty, so it can fail.

SEE caveat: a positive value for the opponent means a capture sequence that wins
material inside the swap list. It cannot see that the winning side is mated, or
that the material comes back by a skewer three moves later. Positions flagged
here are "material at risk"; the largest swings are re-checked against the
engine's own search in the report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess
import chess.polyglot

VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 30000,
}


def see(board: chess.Board, move: chess.Move) -> int:
    """Pin-aware static exchange evaluation of `move`, from the mover's view.

    Standard swap list: repeatedly take the least valuable *legally playable*
    attacker on the destination square, recording the value of the piece it
    captures, then fold the list backwards so either side may decline.
    """
    target = move.to_square
    victim = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(target)
    if victim is None:
        return 0

    captured = [VALUE[victim]]
    b = board.copy(stack=False)
    b.push(move)
    on_target = b.piece_type_at(target)
    if on_target is None:
        return captured[0]
    on_target_value = VALUE[on_target]

    side = b.turn
    while True:
        # `b.turn` is the side that just moved, so legality must be tested with
        # the turn set to the side whose capture we are trying. Testing the
        # wrong side silently drops every recapture and turns a won exchange
        # into a bogus loss; see see_selftest.py's regression cases.
        previous_turn = b.turn
        b.turn = side
        best_sq = None
        best_value = None
        for from_sq in b.attackers(side, target):
            mover = b.piece_type_at(from_sq)
            candidate = chess.Move(from_sq, target)
            if mover == chess.PAWN and chess.square_rank(target) in (0, 7):
                candidate = chess.Move(from_sq, target, promotion=chess.QUEEN)
            if candidate not in b.legal_moves:
                continue  # pinned, or would leave its own king in check
            if best_value is None or VALUE[mover] < best_value:
                best_value, best_sq = VALUE[mover], from_sq
        b.turn = previous_turn
        if best_sq is None:
            break

        mover = b.piece_type_at(best_sq)
        captured.append(on_target_value)
        b.remove_piece_at(best_sq)
        b.set_piece_at(target, chess.Piece(mover, side))
        if mover == chess.KING:
            break  # a king cannot be captured, so the sequence stops here
        on_target_value = VALUE[mover]
        side = not side

    # The mover has already committed to the first capture, so only the later
    # captures are declinable: value = c0 - max(0, c1 - max(0, c2 - ...)).
    # Clamping the final step too would report a losing capture as even.
    score = 0
    for value in reversed(captured[1:]):
        score = max(0, value - score)
    return captured[0] - score


def best_capture(board: chess.Board) -> tuple[int, chess.Move | None]:
    """Best SEE the side to move can achieve with any legal capture."""
    best, best_move = 0, None
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        value = see(board, move)
        if value > best:
            best, best_move = value, move
    return best, best_move


def parse_probe(path: Path):
    rows = []
    header_seen = False
    with path.open() as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if line.startswith("FEN\t"):
                header_seen = True
                continue
            if not header_seen:
                continue
            fen, key, ply, moves = line.split("\t")
            rows.append((fen, key, int(ply), moves))
    return rows


def audit(rows):
    positions = 0
    bad_fen: list[tuple[str, str]] = []
    key_mismatch: list[tuple[str, str, str]] = []
    moves_total = 0
    illegal: list[tuple[str, str, str, int]] = []
    losing: list[tuple[str, str, str, int, int, str]] = []

    for fen, key, ply, moves_field in rows:
        positions += 1
        try:
            board = chess.Board(fen)
        except ValueError as exc:
            bad_fen.append((fen, str(exc)))
            continue
        if not board.is_valid():
            bad_fen.append((fen, str(board.status())))
            continue

        local_key = format(chess.polyglot.zobrist_hash(board), "016x")
        if local_key != key:
            key_mismatch.append((fen, key, local_key))

        for token in [t for t in moves_field.split(",") if t]:
            uci, weight = token.split(":")
            moves_total += 1
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                illegal.append((fen, uci, weight, ply))
                continue
            if move not in board.legal_moves:
                illegal.append((fen, uci, weight, ply))
                continue

            after = board.copy(stack=False)
            after.push(move)

            if board.is_capture(move):
                value = see(board, move)
                if value < 0:
                    losing.append((fen, uci, weight, ply, value, "book capture loses material"))
                continue

            value, reply = best_capture(after)
            if value > 0:
                losing.append((fen, uci, weight, ply, value, f"quiet; {reply} wins {value}"))

    return positions, bad_fen, key_mismatch, moves_total, illegal, losing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="?", default="/tmp/book_full.txt")
    ap.add_argument("--limit", type=int, default=0, help="only the first N positions (0 = all)")
    args = ap.parse_args()

    all_rows = parse_probe(Path(args.tsv))
    rows = all_rows[: args.limit] if args.limit else all_rows

    positions, bad_fen, key_mismatch, moves_total, illegal, losing = audit(rows)

    print(f"probe file: {args.tsv}")
    print(f"positions checked: {positions}/{len(rows)} (file has {len(all_rows)})")
    print(f"book moves checked: {moves_total}")
    print(f"invalid FEN (python-chess): {len(bad_fen)}/{positions}")
    print(f"polyglot key mismatch vs chess.polyglot: {len(key_mismatch)}/{positions}")
    print(f"illegal book moves (python-chess): {len(illegal)}/{moves_total}")
    print(f"material-at-risk book moves: {len(losing)}/{moves_total}")

    for label, items in (("BAD FEN", bad_fen), ("KEY MISMATCH", key_mismatch),
                         ("ILLEGAL", illegal), ("MATERIAL AT RISK", losing)):
        if not items:
            continue
        print(f"\n{label} ({len(items)}):")
        for item in items[:40]:
            print("  " + " | ".join(str(x) for x in item))
        if len(items) > 40:
            print(f"  ... {len(items) - 40} more")

    if losing:
        print("\nTop 10 by size of the material swing:")
        for item in sorted(losing, key=lambda t: -abs(t[4]))[:10]:
            print(f"  {item[4]:>4} | {item[1]} w={item[2]} ply={item[3]} | {item[0]} | {item[5]}")

    return 1 if (bad_fen or illegal or key_mismatch) else 0


if __name__ == "__main__":
    sys.exit(main())
