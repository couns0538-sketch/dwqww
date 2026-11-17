## book

Build: base@6b98f217 (g++ 13.3.0, sha256 e06310ec). Cap: 20 s per cell. Fresh process per cell.

| command | returned? | ms | depth | nodes | bestmove | info depth lines | pv? | note |
|---|---|---|---|---|---|---|---|---|
| `go wtime 1000` | yes | 2.1 | - | - | `e2e4` | 0 | no | startpos, OwnBook true |
| `go movetime abc` | yes | 2.1 | - | - | `c2c4` | 0 | no | the seat's accidental case |
| `go movetime 0` | yes | 2.1 | - | - | `e2e4` | 0 | no | zero clock |
| `go wtime abc` | yes | 2.1 | - | - | `e2e4` | 0 | no | 0-ms clock via failure |
| `go btime 1000` | **NO (capped)** | 20000.4 | 27 | 30606312 | `None` | 24 | yes | no clock for this side |
| `go depth abc` | yes | 2.2 | 1 | 26 | `d2d4` | 1 | yes | no clock -> analysis path |
| `go depth 5` | yes | 2.2 | 5 | 1001 | `c2c4` | 5 | yes | no clock -> analysis path |
| `go nodes abc` | **NO (capped)** | 20001.9 | 27 | 30606312 | `None` | 24 | yes | no clock -> analysis path |
| `go mate abc` | **NO (capped)** | 20001.1 | 27 | 30606312 | `None` | 24 | yes | mate 0, no clock |
| `go searchmoves e2e4 wtime 1000` | yes | 23.2 | 14 | 41260 | `e2e4` | 14 | yes | restriction disables the book |
| `go infinite wtime 1000` | **NO (capped)** | 20000.7 | 27 | 30606312 | `None` | 24 | yes | infinite disables the book |
| `go ponder wtime 1000` | **NO (capped)** | 20001.8 | 27 | 30606312 | `None` | 24 | yes | ponder disables the book |
| `go movetime abc depth 5` | yes | 2.1 | - | - | `e2e4` | 0 | no | clock present, depth beside it |
| `go movetime 100` | yes | 2.2 | - | - | `e2e4` | 0 | no | short real clock |
