# etc_probe summary: etc_probe_deep.tsv

Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.
Terms are defined at the top of `tools/etc_probe/summarize.py`.

Positions in the file: 24. Left out: 0 stopped by the node cap, 0 with a board that repeats an earlier position. Used: 24, from 24 base positions.

- endgame: 10 positions from 10 bases
- middlegame: 14 positions from 14 bases

Plain run repeated: identical node counts in 24/24 positions; time ratio of the totals 1.0150; per position the time ratio has standard deviation 4.8 %.

## Counting runs (identical tree)

| rule | group | positions | same nodes as plain | plain nodes | eligible share | hit rate | first proof is the hash move | below-hit share | lookup time | plain search also failed high |
|---|---|---|---|---|---|---|---|---|---|---|
| cut4 | all | 24 | 24/24 | 25461123 | 6.09 % | 15.0 % | 24.5 % | 11.46 % | +12.6 % | 99.9 % |
| cut4 | endgame | 10 | 10/10 | 14303902 | 6.77 % | 21.1 % | 25.0 % | 17.78 % | +11.7 % | 99.9 % |
| cut4 | middlegame | 14 | 14/14 | 11157221 | 5.23 % | 4.7 % | 21.5 % | 3.36 % | +13.2 % | 99.9 % |
| cut6 | all | 24 | 24/24 | 25461123 | 2.37 % | 14.6 % | 27.6 % | 8.46 % | +5.0 % | 100.0 % |
| cut6 | endgame | 10 | 10/10 | 14303902 | 2.93 % | 19.1 % | 27.7 % | 13.22 % | +4.7 % | 100.0 % |
| cut6 | middlegame | 14 | 14/14 | 11157221 | 1.66 % | 4.5 % | 26.6 % | 2.35 % | +5.1 % | 100.0 % |
| cut8 | all | 24 | 24/24 | 25461123 | 0.95 % | 15.2 % | 30.2 % | 6.00 % | +1.7 % | 100.0 % |
| cut8 | endgame | 10 | 10/10 | 14303902 | 1.30 % | 18.4 % | 30.1 % | 9.44 % | +0.2 % | 100.0 % |
| cut8 | middlegame | 14 | 14/14 | 11157221 | 0.49 % | 4.6 % | 31.2 % | 1.59 % | +2.6 % | 100.0 % |
| cut10 | all | 24 | 24/24 | 25461123 | 0.39 % | 16.7 % | 32.4 % | 4.06 % | +0.5 % | 100.0 % |
| cut10 | endgame | 10 | 10/10 | 14303902 | 0.59 % | 18.8 % | 32.1 % | 6.46 % | +0.4 % | 100.0 % |
| cut10 | middlegame | 14 | 14/14 | 11157221 | 0.13 % | 4.7 % | 37.7 % | 0.98 % | +0.6 % | 100.0 % |
| all3 | all | 24 | 24/24 | 25461123 | 13.53 % | 12.0 % | 21.5 % | 14.24 % | +23.9 % | 99.6 % |
| all3 | endgame | 10 | 10/10 | 14303902 | 14.82 % | 16.9 % | 22.0 % | 21.66 % | +19.0 % | 99.5 % |
| all3 | middlegame | 14 | 14/14 | 11157221 | 11.87 % | 4.3 % | 18.3 % | 4.73 % | +26.8 % | 99.7 % |
| nohm4 | all | 24 | 24/24 | 25461123 | 2.30 % | 10.4 % | 0.0 % | 0.83 % | +4.3 % | 99.8 % |
| nohm4 | endgame | 10 | 10/10 | 14303902 | 2.01 % | 16.5 % | 0.0 % | 1.14 % | +0.2 % | 99.8 % |
| nohm4 | middlegame | 14 | 14/14 | 11157221 | 2.68 % | 4.5 % | 0.0 % | 0.43 % | +6.8 % | 99.8 % |
| nohm6 | all | 24 | 24/24 | 25461123 | 0.65 % | 9.9 % | 0.0 % | 0.29 % | -0.6 % | 100.0 % |
| nohm6 | endgame | 10 | 10/10 | 14303902 | 0.62 % | 14.4 % | 0.0 % | 0.37 % | -2.9 % | 100.0 % |
| nohm6 | middlegame | 14 | 14/14 | 11157221 | 0.68 % | 4.7 % | 0.0 % | 0.19 % | +0.7 % | 100.0 % |
| nohm8 | all | 24 | 24/24 | 25461123 | 0.18 % | 10.0 % | 0.0 % | 0.13 % | -1.0 % | 100.0 % |
| nohm8 | endgame | 10 | 10/10 | 14303902 | 0.20 % | 12.6 % | 0.0 % | 0.16 % | -0.2 % | 100.0 % |
| nohm8 | middlegame | 14 | 14/14 | 11157221 | 0.15 % | 5.5 % | 0.0 % | 0.09 % | -1.6 % | 100.0 % |

## Runs that change the search (cutoff taken, variants, placebo)

| run | group | positions | node ratio sum | node ratio geo | 95 % range by position | 95 % range by base | geo without the 2 smallest ratios | smallest / largest ratio | time ratio | best move differs | score moves by 50 or more |
|---|---|---|---|---|---|---|---|---|---|---|---|
| etc_cut4 | all | 24 | 0.989 | 0.866 | [0.697, 1.077] | [0.697, 1.077] | 0.970 | 0.165 / 2.203 | 1.084 | 5/24 | 2/24 |
| etc_cut4 | endgame | 10 | 1.083 | 0.818 | [0.489, 1.370] | [0.489, 1.370] | 1.101 | 0.165 / 2.203 | 1.267 | 2/10 | 2/10 |
| etc_cut4 | middlegame | 14 | 0.867 | 0.902 | [0.813, 1.002] | [0.813, 1.002] | 0.958 | 0.548 / 1.213 | 0.974 | 3/14 | 0/14 |
| etc_cut6 | all | 24 | 0.877 | 0.870 | [0.761, 0.995] | [0.761, 0.995] | 0.940 | 0.299 / 1.482 | 0.945 | 4/24 | 2/24 |
| etc_cut6 | endgame | 10 | 0.812 | 0.771 | [0.619, 0.962] | [0.619, 0.962] | 0.883 | 0.299 / 1.001 | 0.849 | 1/10 | 2/10 |
| etc_cut6 | middlegame | 14 | 0.960 | 0.948 | [0.810, 1.110] | [0.810, 1.110] | 1.034 | 0.467 / 1.482 | 1.002 | 3/14 | 0/14 |
| etc_cut8 | all | 24 | 0.874 | 0.848 | [0.655, 1.099] | [0.655, 1.099] | 0.986 | 0.064 / 1.734 | 0.931 | 2/24 | 2/24 |
| etc_cut8 | endgame | 10 | 0.794 | 0.661 | [0.371, 1.178] | [0.371, 1.178] | 0.939 | 0.064 / 1.661 | 0.835 | 1/10 | 2/10 |
| etc_cut8 | middlegame | 14 | 0.976 | 1.014 | [0.894, 1.149] | [0.894, 1.149] | 1.078 | 0.694 / 1.734 | 0.988 | 1/14 | 0/14 |
| etc_all3 | all | 24 | 0.895 | 0.782 | [0.655, 0.935] | [0.655, 0.935] | 0.855 | 0.295 / 1.620 | 1.149 | 3/24 | 3/24 |
| etc_all3 | endgame | 10 | 0.888 | 0.625 | [0.429, 0.912] | [0.429, 0.912] | 0.754 | 0.295 / 1.620 | 1.123 | 1/10 | 3/10 |
| etc_all3 | middlegame | 14 | 0.905 | 0.918 | [0.843, 0.999] | [0.843, 0.999] | 0.957 | 0.693 / 1.156 | 1.166 | 2/14 | 0/14 |
| etc_nohm4 | all | 24 | 1.099 | 0.993 | [0.837, 1.179] | [0.837, 1.179] | 1.073 | 0.262 / 3.701 | 1.052 | 6/24 | 1/24 |
| etc_nohm4 | endgame | 10 | 1.187 | 0.971 | [0.648, 1.455] | [0.648, 1.455] | 1.194 | 0.262 / 3.701 | 0.990 | 1/10 | 1/10 |
| etc_nohm4 | middlegame | 14 | 0.985 | 1.009 | [0.924, 1.103] | [0.924, 1.103] | 1.047 | 0.758 / 1.336 | 1.089 | 5/14 | 0/14 |
| etc_nohm6 | all | 24 | 1.135 | 1.049 | [0.928, 1.186] | [0.928, 1.186] | 1.122 | 0.484 / 1.494 | 1.176 | 4/24 | 1/24 |
| etc_nohm6 | endgame | 10 | 1.145 | 0.962 | [0.728, 1.271] | [0.728, 1.271] | 1.132 | 0.484 / 1.494 | 1.157 | 0/10 | 1/10 |
| etc_nohm6 | middlegame | 14 | 1.123 | 1.116 | [1.042, 1.195] | [1.042, 1.195] | 1.149 | 0.921 / 1.382 | 1.187 | 4/14 | 0/14 |

## Base positions against the positions generated from them

| run | bases: positions | bases: node ratio geo | generated: positions | generated: node ratio geo |
|---|---|---|---|---|
| etc_cut4 | 24 | 0.866 | 0 | nan |
| etc_cut6 | 24 | 0.870 | 0 | nan |
| etc_cut8 | 24 | 0.848 | 0 | nan |
| etc_all3 | 24 | 0.782 | 0 | nan |
| etc_nohm4 | 24 | 0.993 | 0 | nan |
| etc_nohm6 | 24 | 1.049 | 0 | nan |

