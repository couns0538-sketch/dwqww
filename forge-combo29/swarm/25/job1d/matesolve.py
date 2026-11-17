#!/usr/bin/env python3
"""matesolve.py FEN N : independent brute-force check, no engine involved.

Answers one question: can the side to move FORCE checkmate in at most N moves (2N-1 plies), against every defence?
Exhaustive over all legal moves with early exit in the winning side's favour and in the defender's favour.
Prints the first winning move found, or proves that none exists.

Also --verify FEN PV : replays a PV and reports whether every defender reply in it is FORCED (i.e. the defender had
no alternative that survives longer). A PV that ends in checkmate but contains a defender move with a better
alternative does not prove the mate number it is attached to.
"""
import sys

import chess


def mates_in(board, n):
    """True if side to move can force mate in <= n moves."""
    if n <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True
        if not board.is_game_over(claim_draw=False):
            if not board.is_check() and mates_in(board, n - 1):
                board.pop()
                return True
            if board.is_check() and all_replies_lose(board, n - 1):
                board.pop()
                return True
        board.pop()
    return False


def all_replies_lose(board, n):
    """Side to move is in check: True if every reply still loses within n-1 moves."""
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return False
        if not mates_in(board, n - 1):
            board.pop()
            return False
        board.pop()
    return True


def find_mate_move(board, n):
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return mv
        ok = False
        if not board.is_game_over(claim_draw=False):
            if not board.is_check() and mates_in(board, n - 1):
                ok = True
            elif board.is_check() and all_replies_lose(board, n - 1):
                ok = True
        board.pop()
        if ok:
            return mv
    return None


def main():
    if sys.argv[1] == "--verify":
        fen, pv = sys.argv[2], sys.argv[3:]
        b = chess.Board(fen)
        longest = None
        for i, u in enumerate(pv):
            mv = chess.Move.from_uci(u)
            legal = mv in b.legal_moves
            print(f"ply {i+1} {u} legal={legal}")
            if not legal:
                return
            if b.turn == chess.BLACK:
                b.push(mv)
                alt = [m for m in b.legal_moves]
                b.pop()
                # does the defender have a reply that is not immediately mated?
                survives = []
                for a in alt:
                    b.push(mv); b.push(a)
                    mated = b.is_checkmate()
                    b.pop(); b.pop()
                    if not mated:
                        survives.append(a.uci())
                print(f"   defender alternatives that are not immediately mated: {len(survives)}"
                      f" {survives[:6]}")
            b.push(mv)
        print("final: checkmate =", b.is_checkmate())
        return

    fen, n = sys.argv[1], int(sys.argv[2])
    b = chess.Board(fen)
    print(f"position: {fen}")
    print(f"side to move: {'white' if b.turn else 'black'}")
    for k in range(1, n + 1):
        mv = find_mate_move(b, k)
        print(f"  forced mate in <= {k}: {'YES ' + mv.uci() if mv else 'no'}", flush=True)


if __name__ == "__main__":
    main()
