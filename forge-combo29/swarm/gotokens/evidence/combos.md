## combos

Build: base@6b98f217 (g++ 13.3.0, sha256 e06310ec). Cap: 20 s per cell. Fresh process per cell.

| command | returned? | ms | depth | nodes | bestmove | info depth lines | pv? | note |
|---|---|---|---|---|---|---|---|---|
| `go depth 5 nodes abc` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | does depth still bind? |
| `go nodes abc depth 5` | yes | 2.3 | 5 | 818 | `a2a3` | 5 | yes | order swapped |
| `go nodes abc movetime 100` | yes | 91.7 | 13 | 84245 | `e1g1` | 13 | yes | does movetime still bind? |
| `go depth abc nodes 50000` | yes | 2.2 | 1 | 42 | `e1g1` | 1 | yes | does the node limit still bind? |
| `go depth 5 wtime abc` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | does a 0-ms clock crush depth 5? |
| `go depth 5 wtime 0` | yes | 2.2 | 1 | 42 | `e1g1` | 1 | yes | same, written out |
| `go depth 5 movetime abc` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | does a 0-ms movetime crush depth 5? |
| `go depth 5 wtime 1000` | yes | 2.2 | 5 | 818 | `a2a3` | 5 | yes | two well-formed limits |
| `go depth abc wtime 1000` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | clock beats a 1-ply depth |
| `go depth 5 mate abc` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | mate 0 beside depth 5 |
| `go nodes abc mate 3` | yes | 27.7 | 5 | 53074 | `e1g1` | 5 | yes | does mate still bind? |
| `go depth 5 softnodes abc` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | does depth still bind? |
| `go searchmoves e2e4 nodes abc` | yes | 4.3 | 64 | 0 | `0000` | 64 | no | restricted but unbounded? |
| `go wtime 1000 nodes abc` | yes | 55.1 | 13 | 84245 | `e1g1` | 13 | yes | clock binds |
| `go depth 5 btime abc` | yes | 2.1 | 5 | 818 | `a2a3` | 5 | yes | btime ignored on white |
| `go depth 5 nodes 0` | yes | 2.3 | - | - | `a2a3` | 0 | no | which wins, the 0 or the depth? |
| `go movestogo abc wtime 1000` | yes | 379.3 | 19 | 665334 | `d2d3` | 19 | yes | clock binds |
| `go movestogo 20 wtime 1000` | yes | 55.4 | 13 | 84245 | `e1g1` | 13 | yes | movestogo + clock |
| `go movestogo 20` | **NO (capped)** | 20001.9 | 30 | 32776370 | `None` | 24 | yes | no clock at all |
