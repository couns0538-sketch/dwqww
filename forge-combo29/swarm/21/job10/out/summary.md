| # | FEN | depth1 | first legal | wtime10 | wtime1 | wtime0 | wtime10+winc10 | wtime1 == depth1 | wtime1 == first legal |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1` | b8a8 | b8h8 | b8a8 | b8a8 | b8a8 | b8a8 | True | False |
| 1 | `r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1` | b6b5 | g8h8 | b6b5 | b6b5 | b6b5 | b6b5 | True | False |
| 2 | `6k1/p4r1p/1p2Q3/2p5/2P1N3/1P3P2/PK6/6q1 b - - 0 1` | g1g6 | g8h8 | g1g6 | g1g6 | g1g6 | g1g6 | True | False |
| 3 | `5R2/5npp/5k2/8/4p3/4P3/3K1PPP/8 b - - 0 1` | h7h5 | f6e7 | h7h5 | h7h5 | h7h5 | h7h5 | True | False |
| 4 | `8/1p1k1KN1/4pB2/4P2P/8/P2p3r/2b5/8 w - - 0 1` | f6g5 | g7e8 | f6g5 | f6g5 | f6g5 | f6g5 | True | False |
| 5 | `8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1` | e4f5 | e4f5 | e4f5 | e4f5 | e4f5 | e4f5 | True | True |
| 6 | `2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b - - 0 1` | h8e8 | h8g8 | h8e8 | h8e8 | h8e8 | h8e8 | True | False |
| 7 | `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1` | g5h5 | g5h6 | g5h5 | g5h5 | g5h5 | g5h5 | True | False |

| measure | value |
|---|---|
| positions | 8 |
| wtime1 == go depth 1 | 8 of 8 |
| wtime1 == first legal move | 1 of 8 |
| wtime10+winc10 == wtime10 | 8 of 8 |
| illegal bestmoves | 0 |
| median wall time, wtime10 | 0.302 ms |
| median wall time, wtime1 | 0.457 ms |
| median wall time, wtime0 | 0.106 ms |
| median wall time, wtime10+winc10 | 0.100 ms |
| max wall time, any clock case | 0.641 ms |

=> CONFIRMS 08-F5
