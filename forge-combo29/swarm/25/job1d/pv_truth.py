#!/usr/bin/env python3
"""pv_truth.py FEN PV... : is this PV a genuine forced mate of the length its score claims?

Walks the PV. At every DEFENDER node it enumerates all legal replies and, for each one, asks the independent solver
whether the attacker still mates within the remaining budget. If some defence survives longer than the budget, the
PV is not proof of the claimed distance (the line is one defender's choice, not the defender's best).

At every ATTACKER node it also reports whether a mate of the claimed length was available at all, and how many
first moves achieve it - which is what makes "the engine's move was shorter than the true best" distinguishable
from "the engine was wrong".
"""
import sys

import chess

sys.setrecursionlimit(10000)


def attacker_node(board, n, memo):
    if n <= 0:
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, n)
    if key in memo:
        return memo[key]
    res = False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); res = True; break
        if board.is_game_over(claim_draw=False):
            board.pop(); continue
        if defender_node(board, n, memo):
            board.pop(); res = True; break
        board.pop()
    memo[key] = res
    return res


def defender_node(board, n, memo):
    if board.is_game_over(claim_draw=False):
        return True
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -n)
    if key in memo:
        return memo[key]
    res = True
    for mv in board.legal_moves:
        board.push(mv)
        loses = attacker_node(board, n - 1, memo)
        board.pop()
        if not loses:
            res = False
            break
    memo[key] = res
    return res


def main():
    fen = sys.argv[1]
    pv = sys.argv[2:]
    root = chess.Board(fen)
    attacker = root.turn
    b = chess.Board(fen)
    print(f"PV: {' '.join(pv)}   ({len(pv)} plies)")
    ok = True
    for i, u in enumerate(pv):
        mv = chess.Move.from_uci(u)
        if mv not in b.legal_moves:
            print(f"  ply {i+1}: {u} ILLEGAL -- stopping")
            return 1
        plies_done = i + 1
        if b.turn != attacker:
            # After this defence, the attacker has however many moves the claimed line still contains:
            # ceil(remaining_plies / 2). (First version used floor, which asked the attacker to mate in one move
            # too few and made every correct line look unforced.)
            remaining = len(pv) - plies_done
            budget = (remaining + 1) // 2
            memo = {}
            survive = []
            for a in list(b.legal_moves):
                b.push(a)
                mates = attacker_node(b, budget, memo)
                b.pop()
                if not mates:
                    survive.append(a.uci())
            status = "every defence still loses" if not survive else f"{len(survive)} defence(s) survive longer"
            print(f"  ply {i+1}: defender {u}: {status}"
                  + (f" -> {survive[:8]}" if survive else ""))
            if survive:
                ok = False
        b.push(mv)
    print(f"  final checkmate: {b.is_checkmate()}")
    print(f"  FORCED MATE OF CLAIMED LENGTH: {'YES' if ok and b.is_checkmate() else 'NO'}")
    return 0 if ok and b.is_checkmate() else 1


if __name__ == "__main__":
    sys.exit(main())
