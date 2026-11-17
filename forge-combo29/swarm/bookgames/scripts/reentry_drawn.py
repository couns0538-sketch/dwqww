"""Can play that LEAVES the book re-enter it on a DRAWN root?

The book graph from startpos is acyclic (book_paths.py), so a game that never
leaves the book cannot repeat a position. The residual route to trap 19a is: a
game leaves the book where the book has no move, play continues, and play later
reaches a position that IS in the book AND is already a drawn root (threefold,
halfmove >= 100, or insufficient material). The book would then fire on it.

Two facts make this checkable rather than open-ended:

  1. A position can only be repeated if every move in between is REVERSIBLE. A
     pawn move or a capture can never be undone, so it permanently separates all
     later positions from all earlier ones. The same is true of a move that
     changes castling rights. So for a book line, the only positions that can
     EVER recur are those reached after the line's last irreversible move.
  2. A drawn root by repetition needs the same position THREE times. One revisit
     is ordinary shuffling; the engine's own is_repetition() requires two prior
     matches in the reversible window.

WHAT THIS SCRIPT CLAIMS, AND WHAT IT DOES NOT

It reports, per book leaf, how many positions after the last irreversible move
could possibly recur. For the leaves where that count is ZERO, the conclusion is
complete at any depth: no repetition is possible through that leaf, because every
earlier position is separated forever by an irreversible move. Those leaves need
no search and admit no depth bound.

For the remaining leaves the script runs a bounded search and reports it as a
BOUNDED result, clearly labelled. It does not upgrade a bounded clean run into a
proof, and it is not the primary evidence for these leaves either -- the 320-game
set is, and it is unbounded in the only sense that matters here (it plays real
games to a conclusion and never leaves the book on a drawn root).

Earlier versions of this script were wrong in three separate ways, all recorded
in FINDINGS.md: v1 walked all legal moves and timed out silently; v2 walked all
legal moves under a node cap and reported the cap as a null; v3 built the "line"
from a FEN, which carries no move history, so its ancestor indices were meaningless
and it reported 77 phantom "hits".
"""

from __future__ import annotations

import json
import sys
import time
from collections import deque

import chess
import chess.polyglot

import book_graph as bg


def collect_book(book_path: str):
    entries = bg.load_book(book_path)
    book_keys = {k for k, _m, _w in entries}
    by_key: dict[int, list[int]] = {}
    for k, m, _w in entries:
        by_key.setdefault(k, []).append(m)
    return book_keys, by_key


def book_leaves(by_key) -> list[list[chess.Move]]:
    """Every maximal book line, as its move list from startpos."""
    start = chess.Board()
    leaves: list[list[chess.Move]] = []
    seen: set = set()

    def walk(board: chess.Board, moves: list[chess.Move]) -> None:
        key = board._transposition_key()
        if key in seen:
            return
        seen.add(key)
        legal = []
        for enc in by_key.get(chess.polyglot.zobrist_hash(board), []):
            mv = bg.decode(board, enc)
            if mv is not None and board.is_legal(mv):
                legal.append(mv)
        if not legal:
            leaves.append(list(moves))
            return
        for mv in legal:
            child = board.copy()
            child.push(mv)
            moves.append(mv)
            walk(child, moves)
            moves.pop()
        seen.discard(key)

    sys.setrecursionlimit(20000)
    walk(start, [])
    return leaves


def is_irreversible(board: chess.Board, move: chess.Move) -> bool:
    if board.is_capture(move):
        return True
    if board.piece_type_at(move.from_square) == chess.PAWN:
        return True
    child = board.copy()
    child.push(move)
    return child.clean_castling_rights() != board.clean_castling_rights()


def line_positions(moves: list[chess.Move]):
    positions = [chess.Board()]
    for mv in moves:
        nxt = positions[-1].copy()
        nxt.push(mv)
        positions.append(nxt)
    last_irrev = -1
    for i, mv in enumerate(moves):
        if is_irreversible(positions[i], mv):
            last_irrev = i
    return positions, last_irrev


def reversible_moves(board: chess.Board) -> list[chess.Move]:
    out = []
    rights = board.clean_castling_rights()
    for mv in board.legal_moves:
        if board.is_capture(mv) or board.piece_type_at(mv.from_square) == chess.PAWN:
            continue
        child = board.copy()
        child.push(mv)
        if child.clean_castling_rights() != rights:
            continue
        out.append(mv)
    return out


def main() -> int:
    book_path, out_path = sys.argv[1], sys.argv[2]
    depth_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    moves_per_leaf = int(sys.argv[4]) if len(sys.argv) > 4 else 4000

    book_keys, by_key = collect_book(book_path)
    leaves = book_leaves(by_key)

    zero = 0
    nonzero = 0
    examples: list[dict] = []
    hits: list[dict] = []
    bounded_clean = 0
    bounded_incomplete = 0
    nodes_total = 0
    started = time.monotonic()

    for moves in leaves:
        positions, last_irrev = line_positions(moves)
        leaf = positions[-1]
        # only positions strictly after the last irreversible move can ever recur
        candidates = {positions[i]._transposition_key(): i
                      for i in range(last_irrev + 1, len(positions) - 1)}
        if not candidates:
            zero += 1
            if len(examples) < 5:
                examples.append({
                    "leaf": leaf.fen(),
                    "last_irreversible_ply": last_irrev,
                    "line": " ".join(m.uci() for m in moves),
                    "why": "every earlier position is separated by a pawn move, a "
                           "capture, or a castling-rights change",
                })
            continue
        nonzero += 1

        frontier = deque([(leaf, 0)])
        visited = {leaf._transposition_key()}
        found = False
        exhausted = True
        budget = moves_per_leaf
        while frontier and not found:
            board, d = frontier.popleft()
            if d >= depth_limit:
                continue
            for mv in reversible_moves(board):
                budget -= 1
                if budget <= 0:
                    exhausted = False
                    break
                child = board.copy()
                child.push(mv)
                pk = child._transposition_key()
                if pk in visited:
                    continue
                visited.add(pk)
                nodes_total += 1
                # a drawn root the book would fire on: a book position that has
                # now occurred for the SECOND time after leaving the book, which
                # with its line occurrence makes three.
                if pk in candidates and chess.polyglot.zobrist_hash(child) in book_keys:
                    hits.append({
                        "leaf": leaf.fen(),
                        "first_occurrence_ply": candidates[pk],
                        "plies_after_leaf": d + 1,
                        "reached_fen": child.fen(),
                        "note": "book position revisited after leaving the book; "
                                "one more occurrence reaches threefold",
                    })
                    found = True
                    break
                frontier.append((child, d + 1))
            if not exhausted:
                break
        if found:
            continue
        if exhausted:
            bounded_clean += 1
        else:
            bounded_incomplete += 1

    report = {
        "book_leaves": len(leaves),
        "leaves_with_no_returnable_position": zero,
        "leaves_with_returnable_positions": nonzero,
        "examples_of_zero_case": examples,
        "revisit_found": len(hits) > 0,
        "hits": hits[:10],
        "hits_total": len(hits),
        "hits_note": "the list above is truncated to the first 10; hits_total is the "
                     "full count. `revisit_found` is set from hits_total, not the "
                     "truncated list.",
        "bounded_search": {
            "depth_limit": depth_limit,
            "move_budget_per_leaf": moves_per_leaf,
            "leaves_clean_and_complete": bounded_clean,
            "leaves_hit_budget": bounded_incomplete,
            "positions_examined": nodes_total,
        },
        "elapsed_s": round(time.monotonic() - started, 1),
    }
    report["verdict"] = (
        f"{zero} of {len(leaves)} book leaves admit NO returnable earlier position at "
        "any depth: an irreversible move separates every earlier position forever. "
        f"On the other {nonzero} leaves a bounded search (depth {depth_limit}, "
        f"{moves_per_leaf} moves per leaf) "
        + ("COMPLETED on all of them" if bounded_incomplete == 0
           else f"completed on {bounded_clean} and hit the budget on {bounded_incomplete}")
        + (" and found no revisit of a book position"
           if not hits else f" and found {len(hits)} revisit(s)")
        + f". {nodes_total} positions examined. The bounded part is a bounded result, "
        "not a proof; the two-sided game set is the unbounded evidence."
    )
    json.dump(report, open(out_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "hits"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
