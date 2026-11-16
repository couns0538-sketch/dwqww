| case | python mate in 1 | engine bestmove | is it a mate | nodes | search | process |
|---|---|---|---|---|---|---|
| W_hm100 | e1e8 | e1e8 | MATE | 105 | go depth 5 | fresh |
| W_hm99 | e1e8 | e1e8 | MATE | 105 | go depth 5 | fresh |
| B_hm100 | a8a1 | a8a1 | MATE | 105 | go depth 5 | fresh |
| B_hm99 | a8a1 | a8a1 | MATE | 105 | go depth 5 | fresh |
| W_rep3 | e1e8 | e1e8 | MATE | 105 | go depth 5 | fresh |
| W_rep2 | e1e8 | e1e8 | MATE | 105 | go depth 5 | fresh |
| B_rep3 | a8a1 | a8a1 | MATE | 105 | go depth 5 | fresh |
| B_rep2 | a8a1 | a8a1 | MATE | 105 | go depth 5 | fresh |
| QUIET_hm100 | none | e2e3 | 0 NODES | 0 | go depth 5 | fresh |
| QUIET_hm99 | none | e2e4 | searched | 759 | go depth 5 | fresh |

| pin | expected | got | verdict |
|---|---|---|---|
| bench 11 | 312866 | 312866 | PASS |
| bench 13 | 862329 | 862329 | PASS |
| bench 16 | 3024920 | 3024920 | PASS |
| perft 5 | 4865609 | 4865609 | PASS |

sanitizer lines anywhere in the case outputs: none

both doors closed, White: True
both doors closed, Black: True
counter-99 / two-occurrence controls find the mate: True
quiet drawn root still adjudicated (0 nodes at 100, searched at 99): True
pins unchanged: True
sanitizer lines: none

=> FIX VERIFIED (third independent check)
