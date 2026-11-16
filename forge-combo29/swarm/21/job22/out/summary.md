| build | go line | bestmoves | count | stop→bestmove ms | legal |
|---|---|---|---|---|---|
| pc | `go banana` | ['e2e4'] | 1 | 2.9 | True |
| pc | `go depth -3` | ['d2d4'] | 1 | 0.0 | True |
| pc | `go` | ['e2e4'] | 1 | 4.3 | True |
| pc | `go depth 0` | ['d2d4'] | 1 | 0.0 | True |
| pc | `go nodes 0` | ['a2a3'] | 1 | 0.0 | True |
| pc | `go movetime 0` | ['a2a3'] | 1 | 0.0 | True |
| pc | `go depth 5` | ['c2c4'] | 1 | 0.1 | True |
| base | `go banana` | ['e2e4'] | 1 | 0.8 | True |
| base | `go depth -3` | ['d2d4'] | 1 | 0.0 | True |
| base | `go` | ['e2e4'] | 1 | 1.4 | True |
| base | `go depth 0` | ['d2d4'] | 1 | 0.0 | True |
| base | `go nodes 0` | ['a2a3'] | 1 | 0.0 | True |
| base | `go movetime 0` | ['a2a3'] | 1 | 0.0 | True |
| base | `go depth 5` | ['c2c4'] | 1 | 0.1 | True |

Every go line yields exactly one legal bestmove after stop:
PC build: True
base build: True

=> CONFIRMS 30-F1 on both builds
