#!/usr/bin/env python3
"""solve_after_incremental.py FEN MOVE MAXN : smallest forced mate after MOVE, printing each budget as it finishes.

Separate process per budget would lose the memo; instead this walks n upward and prints after each n, flushing, so a
timeout still leaves the answered budgets on record. "none within N" is only printed when the loop finished.
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
    fen, move, maxn = sys.argv[1], sys.argv[2], int(sys.argv[3])
    b = chess.Board(fen)
    mv = chess.Move.from_uci(move)
    assert mv in b.legal_moves, f"{move} illegal"
    b.push(mv)
    print(f"after {move}: {b.fen()}", flush=True)
    if b.is_checkmate():
        print("RESULT mate 1", flush=True)
        return
    for m in range(1, maxn):
        t0 = time.time()
        memo = {}
        ok = D(b, m, memo)
        dt = time.time() - t0
        print(f"budget m={m} (total mate in {m+1}): forced={ok}  [{dt:.1f}s, memo {len(memo)}]", flush=True)
        if ok:
            print(f"RESULT mate {m+1}", flush=True)
            return
    print(f"RESULT none within {maxn}", flush=True)


if __name__ == "__main__":
    main()
