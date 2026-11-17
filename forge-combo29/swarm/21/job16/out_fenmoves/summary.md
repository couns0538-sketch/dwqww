| case | position command | search | refused | result | bestmove | info |
|---|---|---|---|---|---|---|
| 1 | `position fen F` (reference) | go perft 1 | False | 20 (python: 20) | – | – |
| 2 | `position fen F moves e1d1` | go perft 1 | False | 8 (python after e1d1: 8) | – | – |
| 3 | `position startpos moves e2e4` (control) | go perft 1 | False | 20 (startpos: 20) | – | – |
| 4 | `position fen F moves e1e8` (a mate) | go depth 3 | False | – | 0000 | 3 seldepth 3 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv |
| 5 | `position startpos moves <8-move cycle>` | go depth 3 | False | – | e2e4 | p 18 nodes 215 nps 53750 hashfull 0 time 4 pv e2e4 h7h6 d2d4 |

python-chess: after e1e8 in F the board is checkmate: True
python-chess: F has 20 legal moves; after e1d1, 8
