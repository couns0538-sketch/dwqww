## control A: published perft values

| position | depth | published | engine | reference | both equal published |
|---|---|---|---|---|---|
| 0 | 1 | 20 | 20 | 20 | YES |
| 0 | 2 | 400 | 400 | 400 | YES |
| 0 | 3 | 8902 | 8902 | 8902 | YES |
| 0 | 4 | 197281 | 197281 | 197281 | YES |
| 0 | 5 | 4865609 | 4865609 | 4865609 | YES |
| 1 | 1 | 48 | 48 | 48 | YES |
| 1 | 2 | 2039 | 2039 | 2039 | YES |
| 1 | 3 | 97862 | 97862 | 97862 | YES |
| 1 | 4 | 4085603 | 4085603 | 4085603 | YES |

control A verdict: PASS - both sides reproduce every published value

## control B: the checker must catch a planted wrong number

compare.py stdout on the mutant:
```
differing pairs 1
DIFF (0, 1, '21', '20')
```

control B verdict: PASS - exactly one differing pair reported
