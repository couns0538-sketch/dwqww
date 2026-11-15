#!/usr/bin/env python3
"""Job 1 part C requirement: check 10 of the found mate-in-3-move positions by
hand listing -- i.e. print the complete exhaustive justification in readable
form so a human can follow it: every white first move together with every
black reply that refutes it, for the first 10 positions.

This is a *third* implementation (plain recursion, printing as it goes) so it
does not share code with either solver.
"""

import json
import sys

import chess

POSFILE = sys.argv[1]
OUT = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 10


def all_white_moves(board):
    return list(board.legal_moves)


def mate_in_1_moves(board):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return out


def white_forces_in_3(board, log):
    """Return list of white moves that force mate within 3 plies, with proof."""
    wins = []
    for w1 in board.legal_moves:
        board.push(w1)
        if board.is_stalemate() or board.is_insufficient_material():
            board.pop()
            continue
        replies = list(board.legal_moves)
        refutation = None
        if not replies:
            board.pop()
            continue
        proof = {}
        for reply in replies:
            board.push(reply)
            m1 = mate_in_1_moves(board)
            board.pop()
            if not m1:
                refutation = reply.uci()
                break
            proof[reply.uci()] = m1
        board.pop()
        if refutation is None:
            wins.append((w1.uci(), proof))
    return wins


def white_forces_in_5(board):
    """(white move, the black replies, and for each reply a mate-in-3 proof)."""
    results = []
    for w1 in board.legal_moves:
        board.push(w1)
        if board.is_stalemate() or board.is_insufficient_material():
            board.pop()
            continue
        replies = list(board.legal_moves)
        if not replies:
            board.pop()
            continue
        ok = True
        block = {}
        for reply in replies:
            board.push(reply)
            sub = white_forces_in_3(board, None)
            board.pop()
            if not sub:
                ok = False
                break
            block[reply.uci()] = sub
        board.pop()
        if ok:
            results.append((w1.uci(), block))
    return results


def main():
    positions = json.load(open(POSFILE))["positions"][:N]
    with open(OUT, "w") as f:
        for i, p in enumerate(positions):
            b = chess.Board(p["fen"])
            m1 = mate_in_1_moves(b)
            three = white_forces_in_3(b, None)
            five = white_forces_in_5(b)
            f.write(f"=== position {i+1}: {p['fen']}\n")
            f.write(f"  mate in 1 moves: {m1}  (must be empty)\n")
            f.write(f"  white moves forcing mate in <=3 plies: {[w for w, _ in three]}  (must be empty)\n")
            f.write(f"  white moves forcing mate in <=5 plies: {len(five)}\n")
            for w1, block in five:
                f.write(f"    first move {w1}: all {len(block)} black replies covered\n")
                for reply, subs in block.items():
                    f.write(f"      black {reply} -> white mates in <=3: {[w for w, _ in subs]}\n")
                    for w2, proof in subs:
                        f.write(f"        {w2} then mates: {proof}\n")
            f.write("\n")
    print(f"wrote {OUT} for {len(positions)} positions")


if __name__ == "__main__":
    main()
