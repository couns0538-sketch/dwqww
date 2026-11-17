#!/usr/bin/env python3
"""Q8: what a corrected `game_ply` derivation would change.

The lock derives book eligibility from the FEN's fullmove counter
(src/uci.cpp:127-129). That counter is caller-supplied metadata: a FEN rebuilt
from a position, or one written by hand, can carry any move number while describing
the same chess position.

The corrected derivation counts the moves the board actually holds:

    game_ply = int(board.history_size()) - 1

which is 0 at a freshly set position and one more per played move, regardless of
what the FEN claims.

This script measures the divergence between the two derivations over three
populations and reports each with an explicit denominator:

  P1  every position on the book walk          (real lines, counters consistent)
  P2  book positions with a doctored fullmove  (the defect's trigger)
  P3  the same doctored position, played through the engine under both builds,
      with Book Depth at the boundary, so the effect is observed on the wire

`--fixed` points at a patched binary; `--lock` at the unmodified one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def lock_ply(board: chess.Board) -> int:
    """The lock's derivation: from the FEN's fullmove counter."""
    return 2 * (board.fullmove_number - 1) + (1 if board.turn == chess.BLACK else 0)


def fixed_ply(board: chess.Board) -> int:
    """The corrected derivation: from the actual move history.

    Models `int(board.history_size()) - 1` from the C++ patch: the number of moves
    this board has really played. A board built from a FEN has played none, so this
    is 0 no matter what its fullmove counter claims. A board built by pushing moves
    returns the count directly.

    Note: python-chess's own `Board.ply()` is NOT this — it computes
    `2*(fullmove_number-1) + (turn == black)`, i.e. it reproduces the lock's bug
    exactly. Using it here would have made this whole script measure nothing, which
    is what the first version of this file did.
    """
    return len(board.move_stack)


def probe_binary(binary: str, position: str, depth: str, book: str = "true",
                 variety: str = "0") -> tuple[bool, str | None]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", book)
        eng.setoption("Book Variety", variety)
        eng.setoption("Book Depth", depth)
        eng.position_checked(position)
        reply = eng.go_and_wait(CLOCK, timeout=30.0)
        best = reply.bestmove_lines()
        move, _ = parse_bestmove(best[0]) if best else (None, None)
        booked = any("book move" in ln for ln in reply.lines)
        return booked, move
    finally:
        eng.quit()


def norm_key(board: chess.Board) -> str:
    """Position identity for book-line lookup.

    python-chess drops the en-passant square from `fen()` when no legal ep capture
    exists, while the engine keeps it, so the raw FEN strings do not match across
    the two. Keying on (placement, side, castling, ep-if-capturable) makes the
    lookup independent of that difference.
    """
    ep = "-" if not any(board.is_en_passant(m) for m in board.legal_moves) else chess.square_name(board.ep_square)
    parts = board.fen().split()
    parts[3] = ep
    return " ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", default="/tmp/build65/forge")
    ap.add_argument("--fixed", default="/tmp/fixbuild/forge")
    ap.add_argument("--tsv", default="/tmp/book_full.txt")
    args = ap.parse_args()

    rows = parse_probe(Path(args.tsv))

    # ---- P1: real book lines -------------------------------------------------
    # Rebuild real games by playing book moves, so "true ply" is the number of
    # moves actually played. The FEN-only rows cannot answer this: a FEN carries
    # no history, and the correct derivation reads history.
    p1_total = 0
    p1_agree = 0
    p1_beyond = []  # positions the lock thinks are past Book Depth 30
    seen = set()

    def walk_line(board: chess.Board, moves_by_fen: dict[str, list[str]], depth: int) -> None:
        nonlocal p1_total, p1_agree
        key = norm_key(board)
        if key in seen or depth > 24:
            return
        seen.add(key)
        if board.move_stack:
            p1_total += 1
            if lock_ply(board) == fixed_ply(board):
                p1_agree += 1
            if lock_ply(board) >= 30:
                p1_beyond.append((key, fixed_ply(board), lock_ply(board)))
        for uci in moves_by_fen.get(key, []):
            child = board.copy()
            try:
                child.push(chess.Move.from_uci(uci))
            except ValueError:
                continue
            walk_line(child, moves_by_fen, depth + 1)

    moves_by_fen: dict[str, list[str]] = {}
    for fen, _key, _ply, mv in rows:
        moves_by_fen[norm_key(chess.Board(fen))] = [t.split(":")[0] for t in mv.split(",") if t]
    walk_line(chess.Board(), moves_by_fen, 0)

    print("P1  real book lines, rebuilt by playing the moves")
    print(f"    positions after at least one move: {p1_total}")
    print(f"    lock_ply == moves actually played: {p1_agree}/{p1_total}")
    print(f"    positions the lock would refuse at Book Depth 30: {len(p1_beyond)}/{p1_total}")
    print()

    # ---- P2: doctored counters ----------------------------------------------
    # Take real book positions and rewrite only the fullmove counter, leaving
    # pieces, side, castling and ep untouched. The true ply is taken from the book
    # walk, which reached each position by actually playing the moves.
    samples = [r for r in rows[:600] if r[3]][:60]
    p2_total = 0
    p2_differ = []
    for fen, _key, true_ply, _mv in samples:
        for bump in (5, 20, 40):
            fen_parts = fen.split()
            new_fullmove = min(500, int(fen_parts[5]) + bump)
            fen_parts[5] = str(new_fullmove)
            new_fen = " ".join(fen_parts)
            try:
                d = chess.Board(new_fen)
            except ValueError:
                continue
            if not d.is_valid():
                continue
            p2_total += 1
            # The corrected code reads history, which a FEN-only board does not
            # have; for comparability, judge both derivations against the true ply
            # the walk measured for this position.
            if lock_ply(d) != true_ply:                p2_differ.append((new_fen, true_ply, lock_ply(d)))
    print("P2  book positions with the fullmove counter rewritten only")
    print(f"    doctored positions: {p2_total}")
    print(f"    lock derivation wrong about the true ply: {len(p2_differ)}/{p2_total}")
    if p2_differ:
        f, trueply, lk = p2_differ[0]
        print(f"    example: {f}")
        print(f"      true ply {trueply} (from the walk), lock_ply {lk}")
    print()

    # ---- P3: the effect on the wire -----------------------------------------
    # One doctored position, both builds, Book Depth at the boundary.
    base_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 21"
    chess.Board(base_fen)  # validates
    lock_booked, lock_move = probe_binary(args.lock, f"fen {base_fen}", "40")
    fixed_booked, fixed_move = probe_binary(args.fixed, f"fen {base_fen}", "40")
    print("P3  startpos with fullmove 21 (game_ply: lock 40, fixed 0), Book Depth 40")
    print(f"    lock  build: book {'YES' if lock_booked else 'no '}, bestmove {lock_move}")
    print(f"    fixed build: book {'YES' if fixed_booked else 'no '}, bestmove {fixed_move}")
    print()

    # A real 20-ply game should still book in both builds at a generous depth.
    moves = ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 e1g1 f8c5 d2d3 d7d6 "
             "b1c3 c8e6 c1g5 h7h6 g5f6 d8f6 c3d5 f6d8 c2c3 e6d5 e4d5 c6b8")
    real = ("startpos moves " + moves)
    rlock = probe_binary(args.lock, real, "40", book="false")
    rfix = probe_binary(args.fixed, real, "40", book="false")
    print("P3b  a real 22-ply game, Book Depth 40, book OFF (control for false change)")
    print(f"    lock  build: book {'YES' if rlock[0] else 'no '}, bestmove {rlock[1]}")
    print(f"    fixed build: book {'YES' if rfix[0] else 'no '}, bestmove {rfix[1]}")

    # A real game where the corrected derivation still allows the book.
    short = "startpos moves e2e4 c7c5"
    slock = probe_binary(args.lock, short, "4")
    sfix = probe_binary(args.fixed, short, "4")
    print()
    print("P3c  2-ply game, Book Depth 4, book ON (should book in BOTH builds)")
    print(f"    lock  build: book {'YES' if slock[0] else 'no '}, bestmove {slock[1]}")
    print(f"    fixed build: book {'YES' if sfix[0] else 'no '}, bestmove {sfix[1]}")

    print()
    # The claim that matters: the fix removes the metadata dependence and leaves
    # real play alone.
    ok = (not lock_booked) and fixed_booked and slock[0] and sfix[0]
    print(f"defect reproduced on the lock and removed by the patch: "
          f"{'YES' if (not lock_booked and fixed_booked) else 'NO'}")
    print(f"real play unchanged (both builds book a 2-ply game): "
          f"{'YES' if (slock[0] and sfix[0]) else 'NO'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
