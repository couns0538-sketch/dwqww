## control position
`rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
root moves: 20, python total: 197281

| plant | method | total unchanged? | caught | result |
|---|---|---|---|---|
| P0 identity | engine copy of reference | yes | False | correctly NOT flagged |
| A compensating | a2a3 +1, a2a4 -1 | yes (197281 vs 197281) | True | CAUGHT (a2a3,a2a4) |
| B missing move | delete h2h4 | no | True | CAUGHT |
| C extra move | insert a move not in python's list | no | True | CAUGHT |

**Rule 1 verdict: the per-divide checker catches every planted difference, and does not flag an identical set, so a reported zero from this harness is a real measurement**