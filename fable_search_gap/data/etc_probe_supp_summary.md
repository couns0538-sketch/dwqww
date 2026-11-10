# etc_probe summary: etc_probe_supp.tsv

Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.
Terms are defined at the top of `tools/etc_probe/summarize.py`.

Positions in the file: 336. Left out: 0 stopped by the node cap, 0 with a board that repeats an earlier position. Used: 336, from 48 base positions.

- endgame: 123 positions from 46 bases
- middlegame: 213 positions from 48 bases

## Counting runs (identical tree)

| rule | group | positions | same nodes as plain | plain nodes | eligible share | hit rate | first proof is the hash move | below-hit share | lookup time | plain search also failed high |
|---|---|---|---|---|---|---|---|---|---|---|
| cut6 | all | 336 | 336/336 | 222282796 | 2.37 % | 8.1 % | 24.2 % | 3.96 % | +7.5 % | 100.0 % |
| cut6 | endgame | 123 | 123/123 | 147867995 | 2.88 % | 9.0 % | 24.0 % | 5.20 % | +9.7 % | 100.0 % |
| cut6 | middlegame | 213 | 213/213 | 74414801 | 1.35 % | 4.0 % | 26.1 % | 1.50 % | +4.3 % | 100.0 % |
| cut8 | all | 336 | 336/336 | 222282796 | 0.85 % | 7.1 % | 27.9 % | 2.57 % | +0.7 % | 100.0 % |
| cut8 | endgame | 123 | 123/123 | 147867995 | 1.10 % | 7.8 % | 27.6 % | 3.47 % | +0.4 % | 100.0 % |
| cut8 | middlegame | 213 | 213/213 | 74414801 | 0.37 % | 3.2 % | 32.3 % | 0.78 % | +1.2 % | 100.0 % |

## Runs that change the search (cutoff taken, variants, placebo)

| run | group | positions | node ratio sum | node ratio geo | 95 % range by position | 95 % range by base | geo without the 2 smallest ratios | smallest / largest ratio | time ratio | best move differs | score moves by 50 or more |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off_p | all | 336 | 0.982 | 0.999 | [0.960, 1.039] | [0.962, 1.037] | 1.007 | 0.195 / 3.683 | 0.994 | 95/336 | 18/336 |
| off_p | endgame | 123 | 0.975 | 1.009 | [0.945, 1.078] | [0.960, 1.112] | 1.024 | 0.425 / 3.683 | 0.985 | 32/123 | 12/123 |
| off_p | middlegame | 213 | 0.995 | 0.993 | [0.944, 1.044] | [0.957, 1.046] | 1.006 | 0.195 / 3.036 | 1.007 | 63/213 | 6/213 |
| etc_cut6 | all | 336 | 0.942 | 0.987 | [0.952, 1.024] | [0.954, 1.022] | 0.993 | 0.369 / 4.003 | 1.017 | 80/336 | 10/336 |
| etc_cut6 | endgame | 123 | 0.905 | 0.939 | [0.876, 1.007] | [0.868, 1.010] | 0.953 | 0.369 / 4.003 | 0.999 | 29/123 | 7/123 |
| etc_cut6 | middlegame | 213 | 1.013 | 1.016 | [0.975, 1.058] | [0.981, 1.053] | 1.024 | 0.426 / 3.325 | 1.042 | 51/213 | 3/213 |
| etc_cut8 | all | 336 | 0.972 | 0.986 | [0.954, 1.019] | [0.958, 1.015] | 0.992 | 0.302 / 2.429 | 1.019 | 72/336 | 14/336 |
| etc_cut8 | endgame | 123 | 0.952 | 0.954 | [0.899, 1.013] | [0.893, 1.029] | 0.970 | 0.302 / 2.124 | 1.015 | 21/123 | 9/123 |
| etc_cut8 | middlegame | 213 | 1.012 | 1.005 | [0.967, 1.045] | [0.975, 1.047] | 1.013 | 0.384 / 2.429 | 1.026 | 51/213 | 5/213 |

## Base positions against the positions generated from them

| run | bases: positions | bases: node ratio geo | generated: positions | generated: node ratio geo |
|---|---|---|---|---|
| off_p | 48 | 0.964 | 288 | 1.005 |
| etc_cut6 | 48 | 1.083 | 288 | 0.972 |
| etc_cut8 | 48 | 1.066 | 288 | 0.973 |

