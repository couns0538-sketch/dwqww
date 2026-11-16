| measure | count |
|---|---|
| REFUSED | 18820 |
| ACCEPTED | 1180 |
| accepted & python-chess valid | 1145 |
| accepted & python-chess INVALID | 35 |
| python-invalid share of accepted | 2.97 % |

| mutation kind | drawn | accepted | refused | acceptance rate |
|---|---|---|---|---|
| delete | 4119 | 234 | 3885 | 5.7 % |
| dropfld | 4308 | 0 | 4308 | 0.0 % |
| insert | 4066 | 232 | 3834 | 5.7 % |
| replace | 3561 | 526 | 3035 | 14.8 % |
| swapfld | 3946 | 188 | 3758 | 4.8 % |

| accepted-but-python-invalid FEN | engine bestmove |
|---|---|
| `211r3/pp3k2/q3ppp1/3p1n1p/1P1P3P/P2P3Q/R3NPP1/4R1K1 b - - 0 1` | a6a4 |
| `8/8/8/8/7P/8/4B2K/2k4n w - - 37 1 8` | h4h5 |
| `1n1k2nr/1p2q3/Q5pp/2pPpp2/p1PP11bb/N2B2R1/PP3P1P/R1K5 w - - 2 29` | a6b6 |
| `8/11B3p1/6Rr/P2k4/2p5/8/5nK1/n7 b - - 20 74` | h6g6 |
| `8/8/4P3/17/8/2N5/1K5k/8 w - - 5 148` | e6e7 |
| `rnb1k1nr/1p1p1p2/3b2pp/11p1p3/P3P1Q1/2PP4/RP1N1PPP/1NB1KB1R b Kkq - 3 11` | g8f6 |
| `4k2N/8/n1p11p2/1p1R4/1p3P1P/B2pr3/P3RPq1/3K4 w - - 0 43` | e2e3 |
| `5R2/p7/P5k1/8/4p3/8/8/5K2 w - - 0 1 7` | f8a8 |
| `r1b2k2/pp3p2/n5p1/1PpN2P1/P2Bp3/4K3/2PP13/2R1QB1r b - - 2 25` | c5d4 |
| `6k1/6P1/2N5/7N/6bP/3K4/8/8 w - - 1 7 8` | c6e7 |
| `2k5/8/5pn1/p7/8/212KBp/8/r7 b - - 0 88` | a5a4 |
| `rn11kbnr/p3pp1p/1p5R/3p4/8/4P3/PPPKBPP1/RNBQN3 w kq - 3 15` | h6h5 |
| `8/3b4/5p2/1k2B3/1pp41/1p6/1K6/8 w - - 1 78` | e5f6 |
| `4k21/r1P5/8/q4pPp/3N4/6Q1/2R4R/2B2K2 w - - 3 85` | c7c8q |
| `2n3k1/6nr/1N6/p1pP2B1/1P2R1P1/61B/8/1N5K w - - 4 71` | b6c8 |
| `b2k4/7b/8/5N2/5N1P/8/8/5K2 b - - 1 2 130` | h7f5 |
| `8/8/3K4/8/8/p4k2/8/8 b - - 9 1 44` | a3a2 |
| `1k6/3P4/1rP5/8/8/N511/K7/8 b - - 1 123` | b8c7 |
| `n2k4/4nppr/Np312/rP1b3Q/PR5P/B1b1PN1R/5K2/8 w - - 3 43` | h5h7 |
| `8/8/1k6/6K1/5r2/215/8/8 w - - 10 92` | g5f4 |
| `8/p1pkNpb1/Q7/n111pPr1/3p3P/5B1b/P3K2P/2B1R1R1 b - - 0 39` | g5g1 |
| `1n1qkb1r/r3pp1p/pQp2n2/3b4/2pp1pPP/7B/PP11PP1R/1RBK2N1 w k - 0 15` | b6a7 |
| `r2knb2/P3pbq1/8/5p2/5rp1/1P1B1P2/R1PPN2P/2BK3R w - - 1 1 57` | e2f4 |
| `1nb1k1nr/1p3pp1/Q213p/2p1p1q1/p1PPPB1b/N5R1/PP3P1P/1RK2B2 w k - 0 22` | a6b5 |
| `2b3nb/1pq1k1r1/n3p2p/prP13N/Pp1P1Q2/R3P1PP/5P2/1NB1KB1R w - - 3 22` | f4c7 |
| `4N3/8/N213k/7p/6r1/pR6/2n5/6K1 w - - 2 92` | g1h2 |
| `rn6/1b2rk1p/114p1/3p4/PPp3n1/2N5/2N5/3K4 b - - 3 53` | h7h5 |
| `7k/p7/RpP5/4p3/2P112P/4n3/P4P2/1K3BR1 w - - 1 71` | f2e3 |
| `8/8/1k6/4P12/8/p3n3/8/BK6 w - - 6 85` | a1d4 |
| `rn2r1k1/pp3pp1/1q312/2bpp3/6bR/1BPP1N2/PP1NQP2/R1B1K3 b Q - 0 1` | b6e6 |
| `21r4/8/3P2k1/2Pb2Pp/1P2R1PP/8/3K4/5R2 b - - 0 67` | d5e4 |
| `116/5Bk1/p1p5/1p3R1r/5KnN/b6P/r6B/1N6 b - - 8 67` | h5f5 |
| `4r3/2K5/7R/4pk2/pP1p4/P511/6PP/3r4 w - - 0 1` | b4b5 |
| `4R1nb/3k1r2/511p/p4P1P/5P2/6r1/4K3/8 b - - 4 67` | f7e7 |
| `8/4N3/8/8/3k1b2/8/K7/8 b - - 4 13 0` | f4h2 |
