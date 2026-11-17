| go line | bestmove | info lines | nodes | ms | timeout |
|---|---|---|---|---|---|
| `go depth` | a2a3 | 0 | None | 2.05 | False |
| `go depth 5` | c2c4 | 5 | 1001 | 8.95 | False |
| `go wtime btime 50` | a2a3 | 0 | None | 1.75 | False |
| `go nodes abc` | a2a3 | 0 | None | 2.06 | False |
| `go movetime` | a2a3 | 0 | None | 1.96 | False |
| `go wtime 1000 btime 1000` | d2d4 | 9 | 9653 | 34.94 | False |
| `go depth -3` | d2d4 | 1 | 26 | 2.18 | False |
| `go depth 0` | d2d4 | 1 | 26 | 2.17 | False |
| `go banana` |  | 0 | None | 65506.15 | True |

| option | value | PC build | base build |
|---|---|---|---|
| HistRework | 0 | accepted | refused: info string unknown option HistRework |
| HistRework | 1 | accepted | refused: info string unknown option HistRework |
| HistRework | 2 | accepted | refused: info string unknown option HistRework |
| HistRework | 3 | accepted | refused: info string unknown option HistRework |
| HistRework | 4 | refused: info string invalid value for option HistRework | refused: info string unknown option HistRework |
| HistRework | -1 | refused: info string invalid value for option HistRework | refused: info string unknown option HistRework |
| MateAlphaGuard | true | accepted | refused: info string unknown option MateAlphaGuard |
| CuckooRep | true | accepted | refused: info string unknown option CuckooRep |
| TtPruneV2 | true | accepted | refused: info string unknown option TtPruneV2 |
| CorrHistV2 | true | accepted | refused: info string unknown option CorrHistV2 |
