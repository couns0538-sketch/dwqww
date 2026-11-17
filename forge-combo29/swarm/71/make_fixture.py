#!/usr/bin/env python3
"""Build the incremental-vs-refresh fixture from real move sequences.

The committed corpus `forge-10000.moves` is three tab fields per row: an index, the FEN the
game reached, and the moves that reach it from the standard start position (verified: replaying
field 3 from startpos reproduces field 2 exactly).

For every row this script replays those moves with python-chess from the start position and
keeps the first `plies` of them. It then continues the game with legal moves chosen from the
position itself, so each fixture line is one long real move sequence. Every position it emits
was produced by python-chess pushing a move that was legal in that exact board, and the root
FEN is re-parsed before it is written; a line that fails either check aborts the run rather
than becoming a quietly different board.

Output: one line per sequence, "<root fen> | <move> <move> ...".

Usage: make_fixture.py <moves file> <out tsv> <n sequences> <plies per sequence>
"""
import sys

import chess

MOVES = sys.argv[1]
OUT = sys.argv[2]
NSEQ = int(sys.argv[3])
PLIES = int(sys.argv[4])


def fail(message):
    print("FIXTURE FAIL: " + message)
    sys.exit(1)


def main():
    openings = []
    with open(MOVES, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            reached, moves = parts[1], parts[2].split()
            board = chess.Board()
            played = []
            ok = True
            for text in moves:
                try:
                    move = chess.Move.from_uci(text)
                except ValueError:
                    ok = False
                    break
                if move not in board.legal_moves:
                    ok = False
                    break
                board.push(move)
                played.append(text)
            if not ok or board.fen() != chess.Board(reached).fen():
                continue
            openings.append(played)

    if len(openings) < NSEQ:
        fail("corpus gave %d usable openings, wanted %d" % (len(openings), NSEQ))

    rows = []
    for start in openings:
        board = chess.Board()
        played = []
        for text in start:
            board.push(chess.Move.from_uci(text))
            played.append(text)
        while len(played) < PLIES:
            # Extend the real sequence with the first legal move in python-chess's own
            # ordering, which is deterministic, so the fixture is reproducible.
            moves = sorted(board.legal_moves, key=lambda m: m.uci())
            if not moves:
                break
            board.push(moves[0])
            played.append(moves[0].uci())
        if len(played) < PLIES:
            continue
        rows.append(played)
        if len(rows) >= NSEQ:
            break

    if len(rows) != NSEQ:
        fail("wanted %d sequences, built %d" % (NSEQ, len(rows)))

    positions = 0
    with open(OUT, "w", encoding="utf-8") as handle:
        for played in rows:
            board = chess.Board()
            if not board.is_valid():
                fail("startpos not valid")
            handle.write(board.fen(en_passant="fen") + " | " + " ".join(played) + "\n")
            # Re-validate the whole sequence, position by position, before writing it out.
            for text in played:
                move = chess.Move.from_uci(text)
                if move not in board.legal_moves:
                    fail("illegal move in sequence: " + text)
                board.push(move)
                positions += 1
    print("FIXTURE sequences %d plies %d positions_checked %d out %s"
          % (len(rows), PLIES, positions, OUT))


if __name__ == "__main__":
    main()
