#!/usr/bin/env python3
"""matecheck.py FEN [--depth N] [--plies P]

1. sends the FEN to the engine at depth N (S14, Threads 1, Hash 16) and prints the
   last info line and bestmove;
2. replays the PV with python-chess and prints the board after it, whether that is
   checkmate, and the number of plies;
3. solves the mate distance with python-chess by iterative deepening up to P plies
   (negamax, mate distance in plies), so the engine's number can be compared to truth.
"""
import argparse
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", True)]

EXE = "/home/ubuntu/builds/rel/forge"


def engine_lines(fen, depth):
    cmds = ["uci", "setoption name MultiPV value 1", "setoption name Threads value 1",
            "setoption name Hash value 16"]
    cmds += ["setoption name %s value %s" % (k, "true" if v is True else v) for k, v in S14]
    cmds += ["isready", "ucinewgame", "isready", "position fen " + fen, "isready",
             "go depth %d" % depth]
    p = subprocess.run([EXE], input="\n".join(cmds) + "\n", capture_output=True, text=True,
                       timeout=300)
    return p.stdout.splitlines()


def mate_in(board, plies):
    """shortest mate for the side to move within `plies` plies, or None."""
    if plies <= 0:
        return None
    if board.is_checkmate():
        return 0
    if not any(board.legal_moves):
        return None
    best = None
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            r = 1
        else:
            r = mate_in_for_defender(board, plies - 1)
            r = None if r is None else r + 1
        board.pop()
        if r is not None and (best is None or r < best):
            best = r
    return best


def mate_in_for_defender(board, plies):
    """the defender moves next; return the LONGEST mate it can avoid... simplified:
    return plies to mate if EVERY defence loses within plies, else None."""
    if plies <= 0:
        return None
    if board.is_checkmate():
        return 0
    worst = 0
    any_move = False
    for mv in board.legal_moves:
        any_move = True
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return None  # defender is mated here?? cannot be, it is its move
        r = mate_in(board, plies - 1)
        board.pop()
        if r is None:
            return None
        worst = max(worst, r + 1)
    if not any_move:
        return None
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fen")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--plies", type=int, default=12)
    args = ap.parse_args()

    lines = engine_lines(args.fen, args.depth)
    infos = [l for l in lines if l.startswith("info ") and " pv " in l]
    bm = [l for l in lines if l.startswith("bestmove")]
    print("LAST_INFO %s" % (infos[-1] if infos else "(none)"))
    print("BESTMOVE %s" % (bm[-1] if bm else "(none)"))

    board = chess.Board(args.fen)
    pv = infos[-1].split()[infos[-1].split().index("pv") + 1:] if infos else []
    ok = True
    for m in pv:
        mv = chess.Move.from_uci(m)
        if mv not in board.legal_moves:
            print("PV_MOVE_ILLEGAL %s at ply %d" % (m, board.ply()))
            ok = False
            break
        board.push(mv)
    if ok:
        print("PV_PLIES %d" % len(pv))
        print("BOARD_AFTER_PV %s" % board.fen())
        print("IS_CHECKMATE %s  IS_STALEMATE %s" % (board.is_checkmate(), board.is_stalemate()))

    # true mate distance from the root, mover = side to move at the root
    root = chess.Board(args.fen)
    for d in range(1, args.plies + 1):
        r = mate_in(root, d)
        if r is not None:
            print("PYTHON_CHESS_MATE_PLIES %d (score mate %+d for the side to move)"
                  % (r, -(r + 1) // 2 if r % 2 == 1 else 0))
            break
    else:
        print("PYTHON_CHESS_NO_MATE_FOR_SIDE_TO_MOVE_WITHIN_%d_PLIES" % args.plies)
        # try the opponent mating: pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
