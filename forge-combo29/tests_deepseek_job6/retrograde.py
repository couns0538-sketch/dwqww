#!/usr/bin/env python3
"""Job 6: retrograde solving of KQvK, KRvK and KPvK (no Syzygy available here).

The Syzygy mirror is unreachable from this machine (HTTP 403 over http, TLS handshake
failure over https), so the job's fallback applies: compute KQvK, KRvK and KPvK by
retrograde analysis and do only those.

State space = every legal (placement, side to move) of the class. Indexed densely so the
fixpoint is a few array passes rather than a dict walk.

Terminal handling, which is what makes this correct:
  * checkmate: the mover wins -> WIN for the side to move at that node.
  * stalemate: DRAW.
  * a capture that leaves KvK (always a draw): DRAW for the capturer.
  * KPvK promotion: after the promotion the position is still KQvK/KRvK/KBvK/KNvK, all
    won for the pawn side except KBvK/KNvK which are drawn. To avoid needing those
    classes, promotion is scored as: promote to Q or R -> WIN for the pawn side; promote
    to B or N -> DRAW. That is exact, since a lone bishop or knight cannot mate.
  * KQvK / KRvK: the only capture the weak king can make takes the strong piece, giving
    KvK, scored DRAW.

The recursion is the usual one: a node is WIN if some move leads to a LOSS for the
opponent, LOSS if every move leads to a WIN for the opponent, else DRAW at the fixpoint.

Output: {fen: "W"|"D"|"L"} from the side-to-move's view, where W/L mean forced win/loss.
"""
import json
import sys
from collections import deque

import chess

PAWN, KNIGHT, BISHOP, ROOK, QUEEN = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


def build(kind):
    """Returns (index_of, states) for all legal states of `kind`."""
    if kind == "KQvK":
        strong = QUEEN
    elif kind == "KRvK":
        strong = ROOK
    elif kind == "KPvK":
        strong = PAWN
    else:
        raise SystemExit(f"unsupported {kind}")
    index_of = {}
    boards = []
    for strong_white in (True, False):
        for wk in range(64):
            for bk in range(64):
                if wk == bk or chess.square_distance(wk, bk) < 2:
                    continue
                for s in range(64):
                    if s in (wk, bk):
                        continue
                    if strong == PAWN and chess.square_rank(s) in (0, 7):
                        continue
                    for turn_white in (True, False):
                        b = chess.Board(None)
                        sw = chess.WHITE if strong_white else chess.BLACK
                        ks_w = chess.WHITE if strong_white else chess.BLACK
                        # Place: white king, black king, strong piece of colour sw.
                        # wk is the square of the WHITE king, bk of the BLACK king.
                        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                        b.set_piece_at(s, chess.Piece(strong, sw))
                        b.castling_rights = 0
                        b.turn = chess.WHITE if turn_white else chess.BLACK
                        if not b.is_valid():
                            continue
                        index_of[b.board_fen() + (" w" if turn_white else " b")] = len(boards)
                        boards.append(b.copy())
    return index_of, boards


def solve(kind):
    index_of, boards = build(kind)
    n = len(boards)
    print(f"{kind}: {n} states", flush=True)
    WIN, LOSS, DRAW, UNKNOWN = 1, -1, 0, 2
    value = [UNKNOWN] * n
    # Out-edges: list of (child_index or None, terminal_value or None)
    out = [None] * n

    for i, b in enumerate(boards):
        moves = []
        mate = False
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                mate = True
                b.pop()
                break
            if b.is_stalemate():
                moves.append((None, DRAW))
                b.pop()
                continue
            # Capture of the strong piece, or the pawn, leaving KvK: a draw.
            if b.is_insufficient_material():
                moves.append((None, DRAW))
                b.pop()
                continue
            if m.promotion is not None:
                # Promotion from KPvK: Q/R win, B/N draw (a lone minor cannot mate).
                moves.append((None, WIN if m.promotion in (QUEEN, ROOK) else DRAW))
                b.pop()
                continue
            child_key = b.board_fen() + (" w" if b.turn else " b")
            ci = index_of.get(child_key)
            if ci is None:
                # Should not happen inside a closed class; treat as unknown and let it
                # stay out of the fixpoint (reported if it ever occurs).
                b.pop()
                continue
            moves.append((ci, None))
            b.pop()
        if mate:
            value[i] = WIN
            out[i] = []
        elif not moves:
            value[i] = DRAW          # stalemate
            out[i] = []
        else:
            out[i] = moves

    # Fixpoint by repeated relaxation over the whole array.
    changed = True
    rounds = 0
    while changed:
        changed = False
        rounds += 1
        for i in range(n):
            if value[i] in (WIN, LOSS):
                continue
            moves = out[i]
            if not moves:
                continue
            best = None
            all_win_for_opp = True
            unknown = False
            for ci, term in moves:
                if term is not None:
                    # A terminal recorded while generating OUR move list is already
                    # from OUR point of view: a promotion to Q/R is a WIN for us, and
                    # "capture the strong piece" is a DRAW for us. It must NOT be
                    # negated. (An earlier version negated it, which turned every
                    # promotion win into a loss and made KPvK read as 99% draws.)
                    here = term
                else:
                    cv = value[ci]
                    if cv == UNKNOWN:
                        unknown = True
                        all_win_for_opp = False
                        continue
                    here = -cv        # child value is opponent's view
                if here == WIN:
                    best = WIN
                    break
                if here == LOSS:
                    pass
                else:
                    all_win_for_opp = False
                    if best is None:
                        best = DRAW
            if best == WIN:
                value[i] = WIN
                changed = True
            elif all_win_for_opp and not unknown:
                value[i] = LOSS
                changed = True
            elif best == DRAW:
                if value[i] != DRAW:
                    value[i] = DRAW
                    changed = True
    from collections import Counter
    sym = {WIN: "W", LOSS: "L", DRAW: "D", UNKNOWN: "?"}
    print(f"  rounds {rounds}, counts {dict(Counter(sym[v] for v in value))}")
    return {b.board_fen() + (" w" if b.turn else " b"): sym[value[i]]
            for i, b in enumerate(boards)}


def main():
    kinds = sys.argv[1].split(",")
    out_path = sys.argv[2]
    result = {}
    for kind in kinds:
        result[kind] = solve(kind)
    with open(out_path, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
