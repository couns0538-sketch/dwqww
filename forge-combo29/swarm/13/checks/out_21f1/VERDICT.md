## my own run of seat 21's finding 21-F1 (seat 13, own build, own harness)

python-chess perft 3: refused FEN = 8802, startpos = 8902, legal-castling FEN = 13744, K v K = 170

| case | what I check | engine nodes | engine refusal line | verdict |
|---|---|---|---|---|
| A_badfen_only | refused, perft3 = startpos 8902? | 8902 | info string invalid FEN: castling right without king and rook | HOLDS |
| B_badfen_then_kvk | refused, next FEN sticks (perft3 = 170)? | 170 | info string invalid FEN: castling right without king and rook | HOLDS |
| C_badfen_then_start | refused, startpos sticks (8902)? | 8902 | info string invalid FEN: castling right without king and rook | HOLDS |
| D_legal_castling | ACCEPTED, perft3 = 13744 (python-chess)? | 13744 | (none) | HOLDS |
| E_start_then_badfen | refused, previous startpos still there (8902)? | 8902 | info string invalid FEN: castling right without king and rook | HOLDS |

Reading:
- The brief says the impossible-castling FEN is ACCEPTED with perft 3 = 8,902.
- If case A got 8,902 AND a refusal line, then 8,902 is startpos after a REFUSAL,
  not the accepted FEN's perft: seat 21's correction holds.
- python-chess's perft 3 of the FEN itself is 8802, which is the brief's other number 8,802.
