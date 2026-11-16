#!/usr/bin/env python3
"""kimi5 job1 B2(ii): pick the 20 worst-for-the-clock positions out of the first 300
UHO lines, by the TIME_MODEL: dense positions cost more per node (lower NPS -> a longer
1024-node interval) and wide/tactical positions lengthen the unfinished iteration.
Score = on-board pieces + 2*legal captures + 2*legal checking moves. Prints CSV evidence
and writes the 20 FENs, one per line, to k5_worst20.fens."""
import chess

EPD = "/tmp/kimi5/UHO_Lichess_4852_v1.epd"
N = 300
TOP = 20

rows = []
with open(EPD, encoding="utf-8", errors="replace") as fh:
    for i, line in enumerate(fh):
        if i >= N:
            break
        fen = line.strip()
        board = chess.Board(fen)
        pieces = len(board.piece_map())
        captures = 0
        checks = 0
        for mv in board.legal_moves:
            if board.is_capture(mv):
                captures += 1
            if board.gives_check(mv):
                checks += 1
        rows.append((pieces + 2 * captures + 2 * checks, pieces, captures, checks, i + 1, fen))

rows.sort(reverse=True)
print("rank,score,pieces,captures,checks,epd_line,fen")
with open("/tmp/kimi5/k5_worst20.fens", "w") as out:
    for rank, row in enumerate(rows[:TOP], 1):
        print(f"{rank},{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}")
        out.write(row[5] + "\n")
