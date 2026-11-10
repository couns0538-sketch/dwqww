# etc_probe summary: etc_probe_wide.tsv

Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.
Terms are defined at the top of `tools/etc_probe/summarize.py`.

Positions in the file: 95. Left out: 0 stopped by the node cap, 4 with a board that repeats an earlier position. Used: 91, from 24 base positions.

- endgame: 35 positions from 10 bases
- middlegame: 56 positions from 14 bases

Plain run repeated: identical node counts in 91/91 positions; time ratio of the totals 0.9996; per position the time ratio has standard deviation 4.8 %.

## Counting runs (identical tree)

| rule | group | positions | same nodes as plain | plain nodes | eligible share | hit rate | first proof is the hash move | below-hit share | lookup time | plain search also failed high |
|---|---|---|---|---|---|---|---|---|---|---|
| cut4 | all | 91 | 91/91 | 57047775 | 5.77 % | 13.9 % | 24.5 % | 9.60 % | +13.3 % | 99.8 % |
| cut4 | endgame | 35 | 35/35 | 30641405 | 6.66 % | 19.5 % | 25.2 % | 15.25 % | +12.0 % | 99.8 % |
| cut4 | middlegame | 56 | 56/56 | 26406370 | 4.74 % | 4.7 % | 19.8 % | 3.05 % | +14.0 % | 99.8 % |
| cut6 | all | 91 | 91/91 | 57047775 | 2.17 % | 13.5 % | 29.0 % | 6.85 % | +5.5 % | 100.0 % |
| cut6 | endgame | 35 | 35/35 | 30641405 | 2.80 % | 17.7 % | 29.4 % | 11.07 % | +5.0 % | 100.0 % |
| cut6 | middlegame | 56 | 56/56 | 26406370 | 1.44 % | 4.2 % | 24.6 % | 1.96 % | +5.7 % | 100.0 % |
| cut8 | all | 91 | 91/91 | 57047775 | 0.84 % | 14.2 % | 33.4 % | 4.73 % | +2.9 % | 100.0 % |
| cut8 | endgame | 35 | 35/35 | 30641405 | 1.22 % | 17.1 % | 33.7 % | 7.76 % | +3.8 % | 100.0 % |
| cut8 | middlegame | 56 | 56/56 | 26406370 | 0.41 % | 3.9 % | 29.9 % | 1.21 % | +2.5 % | 100.0 % |
| cut10 | all | 91 | 91/91 | 57047775 | 0.34 % | 16.1 % | 37.6 % | 3.15 % | +2.0 % | 100.0 % |
| cut10 | endgame | 35 | 35/35 | 30641405 | 0.55 % | 18.0 % | 37.6 % | 5.32 % | +2.6 % | 100.0 % |
| cut10 | middlegame | 56 | 56/56 | 26406370 | 0.10 % | 3.7 % | 37.5 % | 0.63 % | +1.6 % | 100.0 % |

## Runs that change the search (cutoff taken, variants, placebo)

| run | group | positions | node ratio sum | node ratio geo | 95 % range by position | 95 % range by base | geo without the 2 smallest ratios | smallest / largest ratio | time ratio | best move differs | score moves by 50 or more |
|---|---|---|---|---|---|---|---|---|---|---|---|
| etc_cut4 | all | 91 | 1.016 | 0.950 | [0.864, 1.045] | [0.836, 1.070] | 0.986 | 0.165 / 3.503 | 1.149 | 19/91 | 6/91 |
| etc_cut4 | endgame | 35 | 1.090 | 0.883 | [0.720, 1.082] | [0.681, 1.142] | 0.972 | 0.165 / 2.944 | 1.323 | 5/35 | 3/35 |
| etc_cut4 | middlegame | 56 | 0.931 | 0.995 | [0.911, 1.086] | [0.894, 1.107] | 1.015 | 0.548 / 3.503 | 1.052 | 14/56 | 3/56 |
| etc_cut6 | all | 91 | 1.003 | 0.950 | [0.870, 1.037] | [0.829, 1.072] | 0.989 | 0.079 / 1.995 | 1.074 | 20/91 | 4/91 |
| etc_cut6 | endgame | 35 | 0.999 | 0.884 | [0.727, 1.075] | [0.652, 1.177] | 0.983 | 0.079 / 1.995 | 1.115 | 7/35 | 3/35 |
| etc_cut6 | middlegame | 56 | 1.009 | 0.993 | [0.924, 1.068] | [0.924, 1.068] | 1.020 | 0.467 / 1.856 | 1.050 | 13/56 | 1/56 |
| etc_cut8 | all | 91 | 0.937 | 0.919 | [0.831, 1.016] | [0.806, 1.030] | 0.970 | 0.064 / 2.498 | 0.974 | 15/91 | 5/91 |
| etc_cut8 | endgame | 35 | 0.919 | 0.818 | [0.650, 1.029] | [0.617, 1.070] | 0.940 | 0.064 / 2.498 | 0.976 | 3/35 | 5/35 |
| etc_cut8 | middlegame | 56 | 0.958 | 0.989 | [0.918, 1.065] | [0.931, 1.050] | 1.010 | 0.487 / 2.336 | 0.973 | 12/56 | 0/56 |

## Base positions against the positions generated from them

| run | bases: positions | bases: node ratio geo | generated: positions | generated: node ratio geo |
|---|---|---|---|---|
| etc_cut4 | 24 | 0.866 | 67 | 0.982 |
| etc_cut6 | 24 | 0.870 | 67 | 0.980 |
| etc_cut8 | 24 | 0.848 | 67 | 0.946 |

