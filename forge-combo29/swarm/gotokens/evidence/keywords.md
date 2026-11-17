## keywords

Build: base@6b98f217 (g++ 13.3.0, sha256 e06310ec). Cap: 20 s per cell. Fresh process per cell.

| command | returned? | ms | depth | nodes | bestmove | info depth lines | pv? | note |
|---|---|---|---|---|---|---|---|---|
| `go depth` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | token consumed by the reader, nothing after it |
| `go depth abc` | yes | 2.3 | 1 | 42 | `e1g1` | 1 | yes | unparseable |
| `go depth -1` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | sign |
| `go depth 9223372036854775808` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | int64 overflow; uint64 still fits |
| `go depth 0` | yes | 2.2 | 1 | 42 | `e1g1` | 1 | yes | the value the parser substitutes on failure |
| `go depth 5` | yes | 2.2 | 5 | 818 | `a2a3` | 5 | yes | 5 plies |
| `go nodes` | **NO (capped)** | 20001.4 | 30 | 32776370 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go nodes abc` | **NO (capped)** | 20002.1 | 30 | 32776370 | `None` | 24 | yes | unparseable |
| `go nodes -1` | **NO (capped)** | 20001.7 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go nodes 9223372036854775808` | **NO (capped)** | 20001.3 | 30 | 32776370 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go nodes 18446744073709551616` | **NO (capped)** | 20000.6 | 30 | 32776370 | `None` | 24 | yes | uint64 overflow |
| `go nodes 0` | yes | 2.1 | - | - | `a2a3` | 0 | no | the value the parser substitutes on failure |
| `go nodes 50000` | yes | 32.6 | 12 | 38459 | `e1g1` | 12 | yes | 50k node budget |
| `go softnodes` | **NO (capped)** | 20000.1 | 30 | 32776370 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go softnodes abc` | **NO (capped)** | 20001.9 | 29 | 27242371 | `None` | 24 | yes | unparseable |
| `go softnodes -1` | **NO (capped)** | 20001 | 30 | 32776370 | `None` | 24 | yes | sign |
| `go softnodes 9223372036854775808` | **NO (capped)** | 20000.7 | 29 | 27242371 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go softnodes 18446744073709551616` | **NO (capped)** | 20001 | 29 | 27242371 | `None` | 24 | yes | uint64 overflow |
| `go softnodes 0` | yes | 2.1 | - | - | `a2a3` | 0 | no | the value the parser substitutes on failure |
| `go softnodes 50000` | yes | 63.5 | 13 | 84245 | `e1g1` | 13 | yes | finish the passing iteration, hard cap 4x |
| `go movetime` | yes | 2.1 | 4 | 302 | `e1g1` | 4 | yes | token consumed by the reader, nothing after it |
| `go movetime abc` | yes | 2.2 | 5 | 818 | `a2a3` | 5 | yes | unparseable |
| `go movetime -1` | yes | 2.2 | 5 | 818 | `a2a3` | 5 | yes | sign |
| `go movetime 9223372036854775808` | **NO (capped)** | 20000.8 | 29 | 27242371 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go movetime 0` | yes | 2.1 | 3 | 174 | `e1g1` | 3 | yes | the value the parser substitutes on failure |
| `go movetime 100` | yes | 91.3 | 13 | 84245 | `e1g1` | 13 | yes | 100 ms |
| `go movestogo` | **NO (capped)** | 20001.5 | 29 | 27242371 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go movestogo abc` | **NO (capped)** | 20001.8 | 29 | 27242371 | `None` | 24 | yes | unparseable |
| `go movestogo -1` | **NO (capped)** | 20001.4 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go movestogo 9223372036854775808` | **NO (capped)** | 20001.8 | 29 | 27242371 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go movestogo 0` | **NO (capped)** | 20000.6 | 29 | 27242371 | `None` | 24 | yes | the value the parser substitutes on failure |
| `go movestogo 20` | **NO (capped)** | 20000.5 | 29 | 27242371 | `None` | 24 | yes | no clock -> see combos section |
| `go wtime` | yes | 2.2 | 1 | 42 | `e1g1` | 1 | yes | token consumed by the reader, nothing after it |
| `go wtime abc` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | unparseable |
| `go wtime -1` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | sign |
| `go wtime 9223372036854775808` | **NO (capped)** | 20000.8 | 29 | 27242371 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go wtime 0` | yes | 2.1 | 1 | 42 | `e1g1` | 1 | yes | the value the parser substitutes on failure |
| `go wtime 1000` | yes | 53.5 | 13 | 84245 | `e1g1` | 13 | yes | 1 s, white to move |
| `go btime` | **NO (capped)** | 20001.6 | 30 | 32776370 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go btime abc` | **NO (capped)** | 20000.2 | 29 | 27242371 | `None` | 24 | yes | unparseable |
| `go btime -1` | **NO (capped)** | 20000.2 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go btime 9223372036854775808` | **NO (capped)** | 20000.1 | 29 | 27242371 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go btime 0` | **NO (capped)** | 20000.2 | 29 | 27242371 | `None` | 24 | yes | the value the parser substitutes on failure |
| `go btime 1000` | **NO (capped)** | 20002.2 | 29 | 27242371 | `None` | 24 | yes | 1 s, WRONG side on a white-to-move board |
| `go winc` | **NO (capped)** | 20000.3 | 30 | 32776370 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go winc abc` | **NO (capped)** | 20002 | 30 | 32776370 | `None` | 24 | yes | unparseable |
| `go winc -1` | **NO (capped)** | 20000.6 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go winc 9223372036854775808` | **NO (capped)** | 20000.7 | 30 | 32776370 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go winc 0` | **NO (capped)** | 20001.6 | 29 | 27242371 | `None` | 24 | yes | the value the parser substitutes on failure |
| `go winc 100` | **NO (capped)** | 20001.1 | 29 | 27242371 | `None` | 24 | yes | increment only |
| `go binc` | **NO (capped)** | 20001.5 | 29 | 27242371 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go binc abc` | **NO (capped)** | 20001 | 29 | 27242371 | `None` | 24 | yes | unparseable |
| `go binc -1` | **NO (capped)** | 20000.3 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go binc 9223372036854775808` | **NO (capped)** | 20000.9 | 30 | 32776370 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go binc 0` | **NO (capped)** | 20001.5 | 30 | 32776370 | `None` | 24 | yes | the value the parser substitutes on failure |
| `go binc 100` | **NO (capped)** | 20001.5 | 30 | 32776370 | `None` | 24 | yes | increment only, wrong side |
| `go mate` | **NO (capped)** | 20001.5 | 29 | 27242371 | `None` | 24 | yes | token consumed by the reader, nothing after it |
| `go mate abc` | **NO (capped)** | 20001.7 | 29 | 27242371 | `None` | 24 | yes | unparseable |
| `go mate -1` | **NO (capped)** | 20002 | 29 | 27242371 | `None` | 24 | yes | sign |
| `go mate 9223372036854775808` | **NO (capped)** | 20002 | 30 | 32776370 | `None` | 24 | yes | int64 overflow; uint64 still fits |
| `go mate 0` | **NO (capped)** | 20001.1 | 30 | 32776370 | `None` | 24 | yes | the value the parser substitutes on failure |
| `go mate 3` | yes | 23.2 | 5 | 53074 | `e1g1` | 5 | yes | mate in 3 |
| `go infinite` | **NO (capped)** | 20001.5 | 30 | 32776370 | `None` | 24 | yes | no limit by definition |
| `go infinite abc` | **NO (capped)** | 20000.1 | 29 | 27242371 | `None` | 24 | yes | junk token ignored |
| `go infinite depth 5` | **NO (capped)** | 20001 | 5 | 818 | `None` | 5 | yes | does a depth beside infinite bind? |
| `go ponder` | **NO (capped)** | 20002 | 30 | 32776370 | `None` | 24 | yes | suppresses the clock, needs ponderhit/stop |
| `go ponder abc` | **NO (capped)** | 20000.6 | 30 | 32776370 | `None` | 24 | yes | junk token ignored |
| `go ponder wtime 1000` | **NO (capped)** | 20000.7 | 30 | 32776370 | `None` | 24 | yes | does a clock beside ponder bind? |
| `go searchmoves` | yes | 4.3 | 64 | 0 | `0000` | 64 | no | specified but empty |
| `go searchmoves abc` | yes | 2.1 | 64 | 0 | `0000` | 64 | no | not a move |
| `go searchmoves a7a8` | yes | 2.2 | 64 | 0 | `0000` | 64 | no | a legal-format illegal move |
| `go searchmoves e2e4` | yes | 2.2 | 64 | 0 | `0000` | 64 | no | valid move, no other limit |
| `go searchmoves e2e4 depth 8` | yes | 2.1 | 8 | 0 | `0000` | 8 | no | valid move + depth |
| `go searchmoves e2e4 a7a8` | yes | 2.2 | 64 | 0 | `0000` | 64 | no | one legal, one illegal |
| `go searchmoves abc depth 8` | yes | 2.1 | 8 | 0 | `0000` | 8 | no | junk move + depth |
