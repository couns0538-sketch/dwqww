## control position
`1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`
root moves: 37, python total: 743255

| plant | method | total unchanged? | caught | result |
|---|---|---|---|---|
| P0 identity | engine copy of reference | yes | False | correctly NOT flagged |
| A compensating | b8a8 +1, b8b3 -1 | yes (743255 vs 743255) | True | CAUGHT (b8a8,b8b3) |
| B missing move | delete g7g6 | no | True | CAUGHT |
| C extra move | insert a move not in python's list | no | True | CAUGHT |

**Rule 1 verdict: the per-divide checker catches every planted difference, and does not flag an identical set, so a reported zero from this harness is a real measurement**