python-chess perft 3 of the CONTROL FEN (r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8) = 55117
startpos perft 3 = 8902 (the brief's known number)

| case | refusal lines seen | readyok after refusal | perft 3 result | board searched | bestmove on stale board | that bestmove legal in startpos |
|---|---|---|---|---|---|---|
| bad castling right | 2: info string invalid FEN: castling right without king and roo / info string invalid FEN: castling right without king and roo | yes | 8902 | startpos (STALE) | e2e4 | True |
| three fields | 2: info string invalid FEN: FEN must contain six fields / info string invalid FEN: FEN must contain six fields | yes | 8902 | startpos (STALE) | e2e4 | True |
| pure garbage | 2: info string invalid FEN: FEN must contain six fields / info string invalid FEN: FEN must contain six fields | yes | 8902 | startpos (STALE) | e2e4 | True |
| CONTROL: legal FEN after a refusal | - | yes | 55117 | the control FEN (GOOD) | - | - |

`d` command produces a board diagram: False (0 diagram lines)
