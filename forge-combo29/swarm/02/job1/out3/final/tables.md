| quantity | value |
|---|---|
| sequences run | 2000 |
| engine processes started | 2000 (one fresh process per sequence) |
| `go` lines sent | 5827 |
| `bestmove` lines received | 5827 |
| searches with NO bestmove | 0 |
| crashes (signal / non-zero exit) | 0 |
| hangs (process alive after 5 s of quit) | 0 |
| sanitizer lines (ASan/UBSan) | 0 |
| illegal bestmoves | 0 |
| `bestmove 0000` on a board with legal moves, go WITHOUT searchmoves | 0 |
| `bestmove 0000` on a board with legal moves, go WITH searchmoves (empty restriction) | 67 |
| `isready` without `readyok` | 0 |
| `uci` without `uciok` | 0 |
| bestmoves with 0 preceding `info depth` lines (counted, NOT a fault) | 463 |
| bestmoves answered from the built-in book | 764 |
| searches the driver had to stop itself (unbounded/ponder/opponent-clock-only) | 1123 |
| sequences with any fault flag | 0 |
| wall per sequence: median / p99 / max (s) | 0.102 / 1.979 / 21.636 |

### sequences that set a fault flag
count 0 (none; out/bad/ is empty by construction)
