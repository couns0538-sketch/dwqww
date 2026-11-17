## extra

Build: base@6b98f217 (g++ 13.3.0, sha256 e06310ec). Cap: 20 s per cell. Fresh process per cell.

| command | returned? | ms | depth | nodes | bestmove | info depth lines | pv? | note |
|---|---|---|---|---|---|---|---|---|
| `go` | **NO (capped)** | 20001.2 | 30 | 32776370 | `None` | 24 | yes | no arguments at all |
| `go foo` | **NO (capped)** | 20000.8 | 30 | 32776370 | `None` | 24 | yes | unknown keyword |
| `go depht 5` | **NO (capped)** | 20002.1 | 30 | 32776370 | `None` | 24 | yes | typo'd keyword |
| `go wtime 1000 depht 5` | yes | 48.9 | 13 | 84245 | `e1g1` | 13 | yes | typo beside a good clock |
| `go Depth 5` | **NO (capped)** | 20001.7 | 30 | 32776370 | `None` | 24 | yes | wrong case |
| `go depth=5` | **NO (capped)** | 20001.9 | 30 | 32776370 | `None` | 24 | yes | shell-style assignment |
| `go depth 10 depth 3` | yes | 2.1 | 3 | 174 | `e1g1` | 3 | yes | which occurrence wins |
| `go nodes 50000 nodes abc` | yes | 29.8 | 12 | 38459 | `e1g1` | 12 | yes | good then bad |
| `go xyz depth 5` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | junk before a good keyword |
| `go depth 5 xyz` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | junk after a good keyword |
| `go depth 5.5` | yes | 2.2 | 1 | 42 | `e1g1` | 1 | yes | not an integer |
| `go depth 0x10` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | not decimal |
| `go depth +5` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | explicit plus |
| `go depth 5 0` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | stray extra token |
| `go movetime 1` | yes | 2.1 | 4 | 302 | `e1g1` | 4 | yes | 1 ms |
