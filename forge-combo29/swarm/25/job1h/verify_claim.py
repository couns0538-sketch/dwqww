#!/usr/bin/env python3
"""verify_claim.py FEN MATEVALUE [MOVE] -- the CHEAP sound verifier for a mate-N claim.

Why this exists (S-C60): my exhaustive `claimcheck.py` asks "is there ANY first move that mates in <= N", which is the
expensive question and is NOT the question a mate-N claim requires. UCI's `mate N` means "the shortest forced mate is
exactly N", so a claim is correct iff BOTH of these hold:

  (A) SOME legal first move forces mate in <= N.      The engine reports its bestmove, so this is usually a PINNED
                                                      search of one subtree - cheap.
  (B) NO legal first move forces mate in <= N-1.      A full search at budget N-1 - cheap, because it is one less.

Neither step is the full budget-N search across all moves, which is what `claimcheck.py` did and what timed out at
600 s on a board whose claim is verifiable in 110 s by this route.

Two modes:
  verify_claim.py FEN N MOVE    verify the claim assuming the engine's move M is the mating move
                                -> prints (A) pinned result; (B) is the caller's job at budget N-1 (this script
                                   also runs it, via a full search at N-1, and prints it)
  verify_claim.py FEN N         no move known: falls back to the exhaustive question and may time out - the old path

Verdicts: CONFIRMED (both A and B established), REFUTED-A (the move does not mate in N), REFUTED-B (a shorter mate
exists, so the claim over-estimates), UNRESOLVED (a budget ran out - never reported as a negative answer).
"""
import sys
import time

import chess

sys.setrecursionlimit(100000)


class Timeout(Exception):
    pass


class Bud:
    def __init__(self, secs):
        self.deadline = time.time() + secs

    def tick(self):
        if time.time() > self.deadline:
            raise Timeout()


def A(board, n, memo, b):
    b.tick()
    if n <= 0:
        return False
    k = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, n)
    if k in memo:
        return memo[k]
    res = False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); res = True; break
        if board.is_game_over(claim_draw=False):
            board.pop(); continue
        hit = D(board, n - 1, memo, b)
        board.pop()
        if hit:
            res = True; break
    memo[k] = res
    return res


def D(board, m, memo, b):
    b.tick()
    if board.is_checkmate():
        return True
    if board.is_game_over(claim_draw=False):
        return False
    k = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -m)
    if k in memo:
        return memo[k]
    res = True
    for mv in board.legal_moves:
        board.push(mv)
        ok = A(board, m, memo, b)
        board.pop()
        if not ok:
            res = False
            break
    memo[k] = res
    return res


def timed(fn, secs):
    b = Bud(secs)
    memo = {}
    t0 = time.time()
    try:
        return fn(b, memo), time.time() - t0, len(memo), False
    except Timeout:
        return None, time.time() - t0, len(memo), True


def main():
    fen, claimed = sys.argv[1], int(sys.argv[2])
    move = sys.argv[3] if len(sys.argv) > 3 else None
    cap = float(sys.argv[4]) if len(sys.argv) > 4 else 900.0
    board = chess.Board(fen)
    stm = "white" if board.turn else "black"
    attacker_is_stm = claimed > 0
    N = abs(claimed)
    print(f"fen: {fen}")
    print(f"side to move {stm}; claim mate {claimed} => attacker is "
          f"{'the side to move' if attacker_is_stm else 'the other side'}; N={N}; cap {cap:.0f}s per budget")

    # (B) no shorter forced mate: full search at budget N-1
    print("\n(B) is there a forced mate in <= N-1 by ANY move?")
    nb = chessturn = chess.Board(fen)
    if N - 1 >= 1:
        fn = (lambda b, m: A(nb, N - 1, m, b)) if attacker_is_stm else (lambda b, m: D(nb, N - 1, m, b))
        got, dt, memo, to = timed(fn, cap)
        if to:
            print(f"    TIMEOUT after {dt:.1f}s (memo {memo}) -> (B) NOT ESTABLISHED")
            b_state = "timeout"
        elif got:
            print(f"    YES - a shorter mate exists ({dt:.1f}s) => the claim OVER-ESTIMATES. REFUTED-B.")
            return
        else:
            print(f"    no ({dt:.1f}s, memo {memo}) => claim does not over-estimate")
            b_state = "ok"
    else:
        print("    N=1, nothing shorter to exclude")
        b_state = "ok"

    # (A) does the given move mate within N?
    if move is None:
        print("\n(A) no move supplied - the general question 'any move mates in <= N' is the EXPENSIVE one")
        fn = (lambda b, m: A(nb, N, m, b)) if attacker_is_stm else (lambda b, m: D(nb, N, m, b))
        got, dt, memo, to = timed(fn, cap)
        if to:
            print(f"    TIMEOUT after {dt:.1f}s -> UNRESOLVED (a timeout is not a refutation)")
        elif got:
            print(f"    YES ({dt:.1f}s) => CONFIRMED (subject to (B) above)")
        else:
            print(f"    no ({dt:.1f}s) => REFUTED-A")
        return

    mv = chess.Move.from_uci(move)
    if mv not in board.legal_moves:
        print(f"\n(A) {move} is ILLEGAL in this position")
        return
    nb.push(mv)
    if nb.is_checkmate():
        print(f"\n(A) {move} mates immediately => CONFIRMED")
        return
    print(f"\n(A) after {move}, can the attacker force mate in <= {N-1} more?")
    fn = (lambda b, m: D(nb, N - 1, m, b)) if attacker_is_stm else (lambda b, m: A(nb, N - 1, m, b))
    got, dt, memo, to = timed(fn, cap)
    if to:
        print(f"    TIMEOUT after {dt:.1f}s (memo {memo}) -> UNRESOLVED")
        return
    if not got:
        print(f"    no ({dt:.1f}s) => REFUTED-A: {move} does not force mate in {N}")
        return
    print(f"    yes ({dt:.1f}s, memo {memo})")
    if b_state == "ok":
        print(f"\nVERDICT: CONFIRMED - {move} forces mate in <= {N} and nothing forces mate in <= {N-1},")
        print(f"         so the shortest forced mate is exactly {N}.")
    else:
        print(f"\nVERDICT: (A) established, (B) unresolved - the claim is CONSISTENT but not proven.")


if __name__ == "__main__":
    main()
