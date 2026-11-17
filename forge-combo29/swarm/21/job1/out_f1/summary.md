| case | answer to `position fen` | perft 3 nodes |
|---|---|---|
| A  FEN only (fresh process) | refused | 8902 |
| B  startpos then FEN | refused | 8902 |
| C  FEN then a legal FEN | refused | 170 |

reference numbers: startpos perft 3 = 8902; python-chess perft 3 of the impossible-castling FEN = 8802

The refused command's answer line (case A) was:
    info string invalid FEN: castling right without king and rook
