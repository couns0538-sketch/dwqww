| case | root | expect | got | bestmove | verdict |
|---|---|---|---|---|---|
| S1 | halfmove 100 + mate in 1 | mate | ('cp', 0) | f2f3 | **FAIL** |
| S2 | halfmove 100, no mate | cp0 | ('cp', 0) | e2e3 | **PASS** |
| S3 | insufficient material | cp0 | ('cp', 0) | e1d1 | **PASS** |
| S4 | threefold + mate in 1 | mate | ('cp', 0) | f2f3 | **FAIL** |
| S5 | threefold, no mate | cp0 | ('cp', 0) | e2e3 | **PASS** |

| pin | expected | got | verdict |
|---|---|---|---|
| `bench 11` | 312866 | 312866 | PASS |
| `bench 13` | 862329 | 862329 | PASS |
| `bench 16` | 3024920 | 3024920 | PASS |
| `go perft 5` | 4865609 | 4865609 | PASS |

base: spec FAILED, pins PASSED
