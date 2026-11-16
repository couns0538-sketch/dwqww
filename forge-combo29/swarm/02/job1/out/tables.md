| quantity | value |
|---|---|
| sequences run | 2000 |
| engine processes started | 2000 (one fresh process per sequence) |
| crashes (non-zero exit, not a timeout) | 0 |
| hangs (no exit within 25 s -> SIGKILL) | 0 |
| sanitizer lines (ASan/UBSan) | 0 |
| `go` lines sent | 5827 |
| `bestmove` lines seen | 5827 |
| sequences where go/bestmove counts differ | 0 |
| sequences where at least one search was judged | 1779 |
| illegal bestmoves | 0 |
| `bestmove 0000` on a board WITH legal moves, go without searchmoves | 0 |
| `bestmove 0000` on a board WITH legal moves, go WITH searchmoves | 67 |
| `isready` answered late/missing (`readyok` absent) | 0 |
| `uci` answered without `uciok` | 0 |
| sequences with any flag set | 0 |
| wall time per sequence: median / p99 / max (s) | 0.044 / 1.832 / 4.691 |
| sum of all wall times (s) | 393.4 |

### every sequence that set a flag (raw output in out/bad/)
count 0

### the go forms that were exercised (counted from seqs.jsonl)
- `go depth` 2412
- `go nodes` 1148
- `go movetime` 1038
- `go infinite` 552
- `go ponder` 351
- `go searchmoves` 108
- `go (bare go)` 94
- `go mate` 71
- `go wtime` 53
