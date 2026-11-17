#!/usr/bin/env python3
"""claimcheck.py FEN MATEVALUE [MAXN] — is a reported mate score true, and what is the true distance?

This exists because three of my earlier tools each got the ATTACKER wrong in a different way:
  - matesolve2.checkpv assumed the side to move was the attacker, so every NEGATIVE mate PV reported nonsense;
  - solve_after_incremental assumed the first move was played by the DEFENDER, which is false when the side to
    move is the side being mated (a negative mate score).
So the sign of the mate score decides everything, and it is resolved ONCE, here, explicitly:

  MATEVALUE > 0  -> the side to move delivers mate. Root is an ATTACKER node: A(root, n).
  MATEVALUE < 0  -> the side to move is mated.      Root is a DEFENDER node: D(root, |n|).

  A(n): attacker to move, can force mate within n of its own moves against every defence.
  D(m): defender to move, m attacker moves remaining; True only if EVERY defence leads to A(m).

The claim is TRUE iff the smallest n with the right node test equals |MATEVALUE|. A claim of a SHORTER distance than
the truth is a wrong score even when its PV ends in checkmate, because the defender in that PV was not playing best.

Prints, for each n from 1 to MAXN, whether the claim's distance is reached, and stops at the first success.
"""
import sys
import time

import chess

sys.setrecursionlimit(100000)


def A(board, n, memo):
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
        hit = D(board, n - 1, memo)
        board.pop()
        if hit:
            res = True; break
    memo[key] = res
    return res


def D(board, m, memo):
    if board.is_checkmate():
        return True
    if board.is_game_over(claim_draw=False):
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -m)
    if key in memo:
        return memo[key]
    res = True
    for mv in board.legal_moves:
        board.push(mv)
        ok = A(board, m, memo)
        board.pop()
        if not ok:
            res = False
            break
    memo[key] = res
    return res


def main():
    fen, claimed = sys.argv[1], int(sys.argv[2])
    maxn = int(sys.argv[3]) if len(sys.argv) > 3 else abs(claimed) + 2
    b = chess.Board(fen)
    stm = "white" if b.turn else "black"
    attacker_is_stm = claimed > 0
    attacker = stm if attacker_is_stm else ("black" if stm == "white" else "white")
    print(f"fen: {fen}")
    print(f"side to move: {stm}; claimed score: mate {claimed} "
          f"=> attacker is {'the side to move' if attacker_is_stm else 'the other side'} ({attacker})")
    truth = None
    for n in range(1, maxn + 1):
        t0 = time.time()
        memo = {}
        hit = A(b, n, memo) if attacker_is_stm else D(b, n, memo)
        dt = time.time() - t0
        print(f"  n={n:2d} (mate in <= {n}): forced={hit}  [{dt:.1f}s, memo {len(memo)}]", flush=True)
        if hit:
            truth = n
            break
    if truth is None:
        print(f"RESULT: no forced mate within {maxn} => the claim 'mate {claimed}' is FALSE (or beyond this budget)")
    elif truth == abs(claimed):
        print(f"RESULT: true distance is mate {truth} => the claim 'mate {claimed}' is CORRECT")
    else:
        print(f"RESULT: true distance is mate {truth}, claim was 'mate {claimed}' => CLAIM IS WRONG "
              f"({'too short' if truth > abs(claimed) else 'too long'})")


if __name__ == "__main__":
    main()
