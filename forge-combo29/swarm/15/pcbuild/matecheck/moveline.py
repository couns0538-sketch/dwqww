#!/usr/bin/env python3
"""moveline.py FEN MOVE

Question: is MOVE (the engine's bestmove) part of a CORRECT forced mate line, or does it
abandon the mate?

For a root where the side to move is the LOSING side (score mate -N): truth says the side to
move is mated in `d` plies. After the engine's move, the opponent must mate in exactly d-1
plies for the move to be on a longest-defence line. The engine's own score claims 2N plies.

Reports, for every legal move:
  - plies to mate for the loser after that move (opponent to move), or "no forced mate"
  - so we can see whether the engine's move is a longest-defence move, a SHORTER loss, or a
    move that escapes the mate entirely.
Uses python-chess only. Brute force (no pruning), so the numbers are exact.
"""
import sys

import chess

INF = 10 ** 6


def attacker_mates(board, plies):
    """attacker (side to move) forces mate within `plies` plies?  -> smallest plies to mate or None"""
    if plies <= 0:
        return None
    if board.is_checkmate():
        return 0
    moves = list(board.legal_moves)
    if not moves:
        return None
    best = None
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return 1
        sub = defender_holds_how_long(board, plies - 1)
        board.pop()
        if sub is not None and (best is None or sub + 1 < best):
            best = sub + 1
    return best


def defender_holds_how_long(board, plies):
    """defender to move; if EVERY defence loses within `plies`, return the longest it can hold."""
    if plies <= 0:
        return None
    moves = list(board.legal_moves)
    if not moves:
        return None
    worst = 0
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return None
        sub = attacker_mates(board, plies - 1)
        board.pop()
        if sub is None:
            return None
        worst = max(worst, sub + 1)
    return worst


def mate_for_side_to_move(board, maxplies):
    """smallest number of plies for the SIDE TO MOVE to force mate, or None."""
    for n in range(1, maxplies + 1, 2):
        if attacker_mates(board, n) is not None:
            return n
    return None


def main():
    fen, uci = sys.argv[1], sys.argv[2]
    maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    root = chess.Board(fen)
    mover_colour = "white" if root.turn == chess.WHITE else "black"
    print("root: %s" % fen)
    print("side to move: %s  (%s is the side we are judging)" % (mover_colour, mover_colour))
    print("engine's move: %s" % uci)
    print()

    # Truth for the root: if the side to move is the LOSING side, the other side mates.
    # Ask the opponent's mating distance from the root by making a null move is impossible in
    # chess, so instead: for each candidate move by the loser, the opponent is to move, and we
    # ask how fast the opponent mates.
    rows = []
    for mv in root.legal_moves:
        board = root.copy()
        board.push(mv)
        m = mate_for_side_to_move(board, maxp)
        rows.append((mv.uci(), m))

    if not rows:
        print("no legal moves")
        return
    mates = [(u, m) for u, m in rows if m is not None]
    nomate = [u for u, m in rows if m is None]

    print("%-8s %-22s %s" % ("move", "opponent mates in", "note"))
    for u, m in sorted(rows, key=lambda r: (r[1] is None, r[1] if r[1] is not None else 0)):
        note = ""
        if u == uci:
            note = "<-- ENGINE'S MOVE"
        print("%-8s %-22s %s" % (u, ("%d plies (mate in %d)" % (m, (m + 1) // 2)) if m is not None
                                 else "NO forced mate", note))
    print()
    if nomate:
        print("moves that ESCAPE the mate entirely: %s" % ", ".join(nomate))
    if mates:
        longest = max(m for _, m in mates)
        shortest = min(m for _, m in mates)
        print("best defence (longest loss): %d plies; quickest loss: %d plies" % (longest, shortest))
        chosen = dict(rows).get(uci)
        if chosen is None:
            print("ENGINE'S MOVE LEADS TO NO FORCED MATE  => it abandons the mate")
        elif chosen == longest:
            print("ENGINE'S MOVE = longest defence (%d plies) => it plays a CORRECT best defence;"
                  " the reported number of plies is what is wrong" % chosen)
        elif chosen == shortest:
            print("ENGINE'S MOVE = QUICKEST loss (%d plies) => it walks into the fastest mate" % chosen)
        else:
            print("ENGINE'S MOVE = %d plies, between shortest %d and longest %d"
                  % (chosen, shortest, longest))


if __name__ == "__main__":
    main()
