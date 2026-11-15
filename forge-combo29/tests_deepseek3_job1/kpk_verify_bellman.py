#!/usr/bin/env python3
"""Third opinion on the KPK table (job 1, part B): verify, do not re-solve.

Idea
  A table of game values is correct exactly when, for every position, it
  satisfies the definition of the game:

      V(p) = W  iff some legal move reaches a position whose value for the
                 opponent is L (or is an immediate win)
      V(p) = L  iff every legal move reaches a position whose value for the
                 opponent is W (or is an immediate loss)
      V(p) = D  otherwise

  plus the terminal cases (mate = L, stalemate = D).

  So instead of writing a third solver, this file checks that equation on the
  table produced by kpk_retrograde.py, using *python-chess's* move generator --
  code written by someone else, not by me.  My own move generator is thereby
  taken out of the loop.  If python-chess and my table disagree about which
  moves exist, or if any position violates the equation, this fails.

  Terminal moves are valued with the only two rules that apply here:
    * a move that captures the pawn leaves K vs K            -> draw
    * a move that promotes leaves K+Q vs K                   -> win, unless the
      enemy king immediately captures the undefended queen   -> draw
  The 50-move rule is not modelled, consistently with the table.

Usage: python3 kpk_verify_bellman.py [N]   (N = positions to check, default all)
"""
import sys
import chess

# my table's convention: value is from the side to move's point of view
FLIP = {"W": "L", "L": "W", "D": "D"}


def immediate_result(board, move):
    """Result of `move` for the mover when the move ends the KPK phase, else None.

    Two cases only:
      * capturing the pawn leaves K vs K -> draw;
      * promoting leaves K+piece vs K.  The new piece is lost at once (-> K vs K,
        a draw) exactly when the enemy king attacks it and our own does not
        defend it.  If it survives, a queen or rook wins and a bishop or knight
        is only a draw (K+B vs K and K+N vs K are dead draws).
    """
    if board.is_capture(move):
        target = board.piece_at(move.to_square)
        if target is not None and target.piece_type == chess.PAWN:
            return "D"                      # only a king can capture here
    if move.promotion is not None:
        after = board.copy()
        after.push(move)
        owner = not after.turn             # the side that just promoted
        promo_sq = move.to_square
        # stalemate first: the promoted position can leave the lone king with no
        # move and not in check, which is a DRAW, not a win.  (All three of my
        # earlier hand-written versions of this rule missed that case; it covers
        # 48 promotion moves in the table.)
        if after.is_stalemate():
            return "D"
        enemy_king = after.king(after.turn)
        own_king = after.king(owner)
        defended = own_king is not None and promo_sq in _king_ring(own_king)
        capturable = enemy_king is not None and promo_sq in _king_ring(enemy_king)
        if capturable and not defended:
            return "D"
        return "W" if move.promotion in (chess.QUEEN, chess.ROOK) else "D"
    return None


def _king_ring(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return {chess.square(f + df, r + dr)
            for df in (-1, 0, 1) for dr in (-1, 0, 1)
            if 0 <= f + df <= 7 and 0 <= r + dr <= 7 and (df, dr) != (0, 0)}


def norm(fen):
    """Key on the board and the side to move only.  python-chess increments the
    halfmove clock and the full move number when it pushes a move, so keying on
    the whole FEN would miss every successor."""
    parts = fen.split()
    return parts[0] + " " + parts[1]


def board_of(fen):
    """python-chess needs the castling and en-passant fields present; KPK has
    neither, so supply them canonically."""
    parts = fen.split()
    return chess.Board(parts[0] + " " + parts[1] + " - - 0 1")


def check_position(board, table):
    """True if the table's verdict for `board` satisfies the Bellman equation.
    Every legal move is examined: stopping at the first win would accept any
    claim of D without checking that no win exists."""
    claim = table[norm(board.fen())]
    moves = list(board.legal_moves)
    if not moves:
        terminal = "L" if board.is_check() else "D"
        return claim == terminal, terminal, "no legal moves"
    any_win = any_draw = False
    for mv in moves:
        r = immediate_result(board, mv)
        if r is None:
            after = board.copy()
            after.push(mv)
            child = table.get(norm(after.fen()))
            if child is None:
                return False, claim, f"successor not in table: {after.fen()}"
            r = FLIP[child]
        if r == "W":
            any_win = True
        elif r == "D":
            any_draw = True
    implied = "W" if any_win else ("D" if any_draw else "L")
    return claim == implied, implied, ""


def main():
    path = sys.argv[2] if len(sys.argv) > 2 else "kpk_2000.txt"
    table = {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        fen, verdict = line.split(";")
        table[norm(fen.strip())] = verdict.strip()
    print(f"loaded {len(table)} positions from {path}")

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(table)
    ok = bad = 0
    for i, (fen, claim) in enumerate(table.items()):
        if i >= limit:
            break
        board = board_of(fen)
        if not board.is_valid():
            print("INVALID POSITION", fen)
            bad += 1
            continue
        good, best, why = check_position(board, table)
        if good:
            ok += 1
        else:
            bad += 1
            print("BELLMAN VIOLATION", fen, "claimed", claim, "implies", best, why)
    print(f"checked {ok + bad}: consistent {ok}, violations {bad}")

    # ---- a negative control: a deliberately corrupted table must be caught ----
    import random
    rng = random.Random(7)
    keys = list(table)
    corrupt = dict(table)
    flipped_keys = rng.sample(keys, 200)
    for k in flipped_keys:
        corrupt[k] = rng.choice([v for v in "WDL" if v != table[k]])
    caught = 0
    for k in flipped_keys:
        board = board_of(k)
        good, _, _ = check_position(board, corrupt)
        if not good:
            caught += 1
    print(f"negative control (200 corrupted entries, same 200 re-checked): caught {caught}")


if __name__ == "__main__":
    main()
