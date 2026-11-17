| true distance | board (at halfmove 100) | go | score | bestmove | verdict |
|---|---|---|---|---|---|
| 1 | `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60` | `go depth 4` | ('mate', 1) | e1e8 | **PASS** |
| 1 | `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60` | `go nodes 20000` | ('mate', 1) | e1e8 | **PASS** |
| 2 | `6k1/8/5K2/8/8/8/8/7Q w - - 100 60` | `go depth 4` | ('cp', 0) | h1g1 | **FAIL** |
| 2 | `6k1/8/5K2/8/8/8/8/7Q w - - 100 60` | `go nodes 20000` | ('cp', 0) | h1g1 | **FAIL** |

boards found (verified distances): {1: '6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60', 2: '6k1/8/5K2/8/8/8/8/7Q w - - 0 60'}
missing distances: [3]
pc: 2 of 4 cases PASS
