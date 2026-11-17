#!/usr/bin/env python3
"""Recheck the drawn-root MOVE claims (section 2): the bail plays the generator's head,
and on a mate-in-one root that head forfeits the mate.

Two claims, each measured against python-chess rather than against the engine:

  M1  the bail's bestmove == the head of `go perft 1` on the SAME searched position
  M2  a mating move exists at that root, and the bail's move is not it
      (i.e. the forfeit is real and its size is one forced mate)

Every fixture is validated first: legal FEN, legal move list, and the searched position's
occurrence count asserted to exactly 3 on FIDE identity.  A fixture that fails is EXCLUDED
and counted as excluded, never as agreement.
"""
import sys

import chess

from harness import Engine

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/work/base/forge-combo29/build/forge"


def identity(board):
    ep = board.ep_square
    if ep is None or not any(m.to_square == ep for m in board.legal_moves):
        ep_field = "-"
    else:
        ep_field = chess.square_name(ep)
    return "%s|%s|%s|%s" % (board.board_fen(), "w" if board.turn else "b",
                            board.castling_xfen() or "-", ep_field)


def occ(board, moves):
    r = board.copy()
    seen = [identity(r)]
    for m in moves:
        r.push(chess.Move.from_uci(m))
        seen.append(identity(r))
    return seen.count(seen[-1])


def mating_moves(board):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return out


FIXTURES = [
    ("E3 back-rank, White to move", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
     ["g1h1", "g8h8", "h1g1", "h8g8"] * 2),
    ("M1 middlegame, Black to move", "rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b KQkq - 0 4",
     ["g8e7", "d3a6", "e7g8", "a6d3"] * 2),
]

eng = Engine(EXE)
rows = 0
excluded = 0
agree = 0
for label, fen, moves in FIXTURES:
    try:
        board = chess.Board(fen)
        if board.fen() != fen:
            raise ValueError("FEN does not round-trip")
        r = board.copy()
        for m in moves:
            mv = chess.Move.from_uci(m)
            if mv not in r.legal_moves:
                raise ValueError("illegal move %s" % m)
            r.push(mv)
        c = occ(board, moves)
        if c != 3:
            raise ValueError("occurrence count %d != 3" % c)
    except Exception as exc:
        print("%-32s EXCLUDED  %s" % (label, exc))
        excluded += 1
        continue

    rows += 1
    res = eng.search(board, "depth 10", moves)
    head = eng.first_generated_move(board, moves)
    mates = mating_moves(board)

    # M1 is the structural claim and applies at every drawn root.  M2 is the cost claim and
    # only applies where a mate in one exists; it reports N/A rather than agreement where it
    # cannot be tested, so a fixture that cannot test the claim cannot inflate the agree count.
    m1 = res["bestmove"] == head
    m2 = (res["bestmove"] not in mates) if mates else None
    agree += 1 if (m1 and m2 is not False) else 0
    print("%-32s occ=%d nodes=%-5s score=%-9s best=%-6s perft1-head=%-6s mates=%s"
          % (label, c, res["nodes"], res["score"], res["bestmove"], head, mates))
    print("%-32s   M1 bail==generator head: %s | M2 mate exists and was not played: %s"
          % ("", m1, "N/A (no mate in one at this root)" if m2 is None else m2))
eng.close()

print("\nrows examined: %d (excluded: %d)" % (rows, excluded))
print("agree: %d / %d" % (agree, rows))
sys.exit(0 if rows > 0 and agree == rows else 1)
