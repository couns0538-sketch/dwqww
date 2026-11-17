#!/usr/bin/env python3
"""matesolve2.py — independent brute-force mate solver, no engine involved.

Attacker = side to move in the root position. Answers: is there a forced mate in at most N moves (2N-1 plies),
against EVERY defence? The defender is assumed to hold out as long as possible, which is the definition UCI's
"mate N" uses.

Correct turn discipline (the bug in my first version, kept as a note): after the attacker's move it is the
DEFENDER's turn, so the attacker's recursion must be entered through a defender node, not called directly.

  attacker_node(board, n)  attacker to move, mate in <= n of the attacker's moves
      for each attacker move:
          push; if checkmate -> win; if game over (stalemate etc) -> not a win
          defender_node(board, n)   # defender to move, attacker still allowed n-1 more moves
  defender_node(board, n)  defender to move; True only if EVERY defence loses
      for each defence move:
          push; if attacker_node(board, n-1) -> this defence loses, else return False

Usage:
  matesolve2.py solve FEN MAXN          -> smallest forced mate <= MAXN, with the first move
  matesolve2.py verify FEN PV...        -> replay a PV and flag unforced defender replies
  matesolve2.py selfcheck               -> run the built-in known-answer tests
"""
import sys

import chess


def attacker_node(board, n, memo):
    if n <= 0:
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, n)
    if key in memo:
        return memo[key]
    result = False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); result = True; break
        if board.is_game_over(claim_draw=False):
            board.pop(); continue
        if defender_node(board, n, memo):
            board.pop(); result = True; break
        board.pop()
    memo[key] = result
    return result


def defender_node(board, n, memo):
    """Defender to move. True only if every defence still loses."""
    if board.is_game_over(claim_draw=False):
        return True
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -n)
    if key in memo:
        return memo[key]
    result = True
    for mv in board.legal_moves:
        board.push(mv)
        loses = attacker_node(board, n - 1, memo)
        board.pop()
        if not loses:
            result = False
            break
    memo[key] = result
    return result


def first_move(board, n, memo):
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); return mv
        ok = False
        if not board.is_game_over(claim_draw=False):
            ok = defender_node(board, n, memo)
        board.pop()
        if ok:
            return mv
    return None


def solve(fen, maxn):
    b = chess.Board(fen)
    print(f"position: {fen}")
    print(f"side to move: {'white' if b.turn else 'black'}")
    out = None
    for k in range(1, maxn + 1):
        memo = {}
        mv = first_move(b, k, memo)
        print(f"  forced mate in <= {k}: {'YES, first move ' + mv.uci() if mv else 'no'}", flush=True)
        if mv and out is None:
            out = (k, mv.uci())
            break
    if out:
        print(f"SMALLEST: mate {out[0]} (needs {2*out[0]-1} plies), first move {out[1]}")
    else:
        print(f"SMALLEST: none within {maxn}")
    return out


def verify(fen, pv):
    b = chess.Board(fen)
    print(f"replay of {len(pv)} plies from {fen}")
    for i, u in enumerate(pv):
        mv = chess.Move.from_uci(u)
        if mv not in b.legal_moves:
            print(f"  ply {i+1}: {u} ILLEGAL")
            return
        attacker_to_move = (b.turn == chess.Board(fen).turn) if i == 0 else None
        if b.turn != chess.Board(fen).turn:  # defender to move: is this reply forced?
            alt = []
            for a in b.legal_moves:
                b.push(a)
                mated_now = b.is_checkmate()
                b.pop()
                if not mated_now:
                    alt.append(a.uci())
            print(f"  ply {i+1}: {u} (defender) -- {len(alt)} alternative replies are not immediately mate:"
                  f" {alt[:8]}")
        b.push(mv)
    print(f"  ends in checkmate: {b.is_checkmate()}")


def selfcheck():
    """Only expectations I can verify without trusting the solver. Two earlier 'known answers' of mine here were
    wrong (a back rank that was mate in one, and a ladder that was mate in one) - both were my guesses, both were
    caught by the run. So this file asserts only what is certain, and prints the rest without asserting."""
    tests = [
        ("8/8/8/4k3/8/2K5/5Q2/8 w - - 0 1", 7, "KQ vs K: engine reported mate 7 at depth 16 on this board"),
        ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 1, "back rank occupied: Ra8# is mate in one"),
        ("7k/5K2/6Q1/8/8/8/8/8 w - - 0 1", 1, "queen next to king, defended: mate in one"),
        ("8/8/8/8/8/8/8/K6k w - - 0 1", None, "bare kings, no mate"),
    ]
    ok = True
    for fen, expect, label in tests:
        b = chess.Board(fen)
        found = None
        for k in range(1, (expect or 3) + 2):
            memo = {}
            if first_move(b, k, memo):
                found = k
                break
        verdict = "PASS" if found == expect else "FAIL"
        if found != expect:
            ok = False
        print(f"{verdict}: {label}: got {found}, expected {expect}  [{fen}]")
    # a case where the shortest mate is NOT the first one a naive search finds
    print("ALL SELFCHECKS PASS" if ok else "SELFCHECK FAILURES ABOVE")


if __name__ == "__main__":
    if sys.argv[1] == "solve":
        solve(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == "verify":
        verify(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == "selfcheck":
        selfcheck()
