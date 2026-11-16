| build | root | go | depth lines | max depth | nodes on last | bestmove |
|---|---|---|---|---|---|---|
| pc | checkmated | `go depth 4` | 4 | 4 | 0 | 0000 |
| pc | checkmated | `go nodes 100` | 64 | 64 | 0 | 0000 |
| pc | checkmated | `go movetime 50` | 64 | 64 | 0 | 0000 |
| pc | stalemated | `go depth 4` | 4 | 4 | 0 | 0000 |
| pc | stalemated | `go nodes 100` | 64 | 64 | 0 | 0000 |
| pc | stalemated | `go movetime 50` | 64 | 64 | 0 | 0000 |
| pc | normal | `go depth 4` | 4 | 4 | 404 | e2e4 |
| pc | normal | `go nodes 100` | 2 | 2 | 54 | d2d4 |
| pc | normal | `go movetime 50` | 9 | 9 | 9653 | d2d4 |
| base | checkmated | `go depth 4` | 4 | 4 | 0 | 0000 |
| base | checkmated | `go nodes 100` | 64 | 64 | 0 | 0000 |
| base | checkmated | `go movetime 50` | 64 | 64 | 0 | 0000 |
| base | stalemated | `go depth 4` | 4 | 4 | 0 | 0000 |
| base | stalemated | `go nodes 100` | 64 | 64 | 0 | 0000 |
| base | stalemated | `go movetime 50` | 64 | 64 | 0 | 0000 |
| base | normal | `go depth 4` | 4 | 4 | 404 | e2e4 |
| base | normal | `go nodes 100` | 2 | 2 | 54 | d2d4 |
| base | normal | `go movetime 50` | 9 | 9 | 9653 | d2d4 |

| question | outcome |
|---|---|
| P1 go depth 4 emits exactly 4 depth lines on a checkmated root | yes |
| P2 go nodes 100 walks beyond 4 depth lines (15-F5's ladder claim) | yes |
| P3 go movetime 50 also walks beyond 4 | yes |
| P4 every line on the terminal roots carries 0 nodes | yes |
| P5 PC build behaves the SAME as base on the ladder | yes |
