# etc_probe summary: etc_probe_wide_variants.tsv

Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.
Terms are defined at the top of `tools/etc_probe/summarize.py`.

Positions in the file: 95. Left out: 0 stopped by the node cap, 4 with a board that repeats an earlier position. Used: 91, from 24 base positions.

- endgame: 35 positions from 10 bases
- middlegame: 56 positions from 14 bases

## Runs that change the search (cutoff taken, variants, placebo)

| run | group | positions | node ratio sum | node ratio geo | 95 % range by position | 95 % range by base | geo without the 2 smallest ratios | smallest / largest ratio | time ratio | best move differs | score moves by 50 or more |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off_p | all | 91 | 1.080 | 0.984 | [0.900, 1.075] | [0.878, 1.080] | 1.021 | 0.080 / 3.271 | 1.078 | 18/91 | 3/91 |
| off_p | endgame | 35 | 1.102 | 0.962 | [0.808, 1.145] | [0.754, 1.174] | 1.053 | 0.080 / 2.160 | 1.053 | 7/35 | 2/35 |
| off_p | middlegame | 56 | 1.054 | 0.998 | [0.907, 1.098] | [0.913, 1.090] | 1.025 | 0.431 / 3.271 | 1.094 | 11/56 | 1/56 |
| etc_cut6_ns | all | 91 | 0.954 | 0.900 | [0.813, 0.997] | [0.790, 1.003] | 0.941 | 0.101 / 2.523 | 1.162 | 16/91 | 7/91 |
| etc_cut6_ns | endgame | 35 | 0.931 | 0.795 | [0.636, 0.995] | [0.606, 1.019] | 0.890 | 0.101 / 2.523 | 1.337 | 7/35 | 6/35 |
| etc_cut6_ns | middlegame | 56 | 0.981 | 0.973 | [0.895, 1.058] | [0.910, 1.040] | 0.999 | 0.428 / 2.384 | 1.047 | 9/56 | 1/56 |
| etc_cut6_fh | all | 91 | 0.905 | 0.924 | [0.855, 0.999] | [0.821, 1.027] | 0.955 | 0.160 / 2.664 | 1.115 | 16/91 | 7/91 |
| etc_cut6_fh | endgame | 35 | 0.851 | 0.862 | [0.730, 1.019] | [0.666, 1.100] | 0.937 | 0.160 / 2.664 | 1.271 | 6/35 | 4/35 |
| etc_cut6_fh | middlegame | 56 | 0.968 | 0.965 | [0.900, 1.035] | [0.898, 1.037] | 0.985 | 0.527 / 1.688 | 1.013 | 10/56 | 3/56 |
| etc_cut8_ns | all | 91 | 0.956 | 0.931 | [0.858, 1.011] | [0.822, 1.041] | 0.963 | 0.117 / 2.336 | 1.060 | 18/91 | 3/91 |
| etc_cut8_ns | endgame | 35 | 0.976 | 0.878 | [0.731, 1.056] | [0.662, 1.146] | 0.958 | 0.117 / 2.336 | 0.904 | 7/35 | 3/35 |
| etc_cut8_ns | middlegame | 56 | 0.933 | 0.966 | [0.902, 1.033] | [0.910, 1.024] | 0.990 | 0.430 / 1.950 | 1.163 | 11/56 | 0/56 |
| etc_cut8_fh | all | 91 | 0.999 | 0.950 | [0.859, 1.051] | [0.840, 1.059] | 1.005 | 0.058 / 2.036 | 0.935 | 20/91 | 5/91 |
| etc_cut8_fh | endgame | 35 | 1.022 | 0.879 | [0.699, 1.106] | [0.672, 1.132] | 1.017 | 0.058 / 1.601 | 0.894 | 7/35 | 5/35 |
| etc_cut8_fh | middlegame | 56 | 0.973 | 0.997 | [0.921, 1.079] | [0.929, 1.070] | 1.023 | 0.492 / 2.036 | 0.962 | 13/56 | 0/56 |
| etc_cut6 | all | 91 | 1.003 | 0.950 | [0.870, 1.037] | [0.829, 1.072] | 0.989 | 0.079 / 1.995 | 1.035 | 20/91 | 4/91 |
| etc_cut6 | endgame | 35 | 0.999 | 0.884 | [0.727, 1.075] | [0.652, 1.177] | 0.983 | 0.079 / 1.995 | 1.054 | 7/35 | 3/35 |
| etc_cut6 | middlegame | 56 | 1.009 | 0.993 | [0.924, 1.068] | [0.924, 1.068] | 1.020 | 0.467 / 1.856 | 1.023 | 13/56 | 1/56 |
| etc_cut8 | all | 91 | 0.937 | 0.919 | [0.831, 1.016] | [0.806, 1.030] | 0.970 | 0.064 / 2.498 | 1.370 | 15/91 | 5/91 |
| etc_cut8 | endgame | 35 | 0.919 | 0.818 | [0.650, 1.029] | [0.617, 1.070] | 0.940 | 0.064 / 2.498 | 1.110 | 3/35 | 5/35 |
| etc_cut8 | middlegame | 56 | 0.958 | 0.989 | [0.918, 1.065] | [0.931, 1.050] | 1.010 | 0.487 / 2.336 | 1.541 | 12/56 | 0/56 |

## Base positions against the positions generated from them

| run | bases: positions | bases: node ratio geo | generated: positions | generated: node ratio geo |
|---|---|---|---|---|
| off_p | 24 | 1.068 | 67 | 0.955 |
| etc_cut6_ns | 24 | 0.811 | 67 | 0.934 |
| etc_cut6_fh | 24 | 0.928 | 67 | 0.923 |
| etc_cut8_ns | 24 | 0.788 | 67 | 0.988 |
| etc_cut8_fh | 24 | 0.899 | 67 | 0.969 |
| etc_cut6 | 24 | 0.870 | 67 | 0.980 |
| etc_cut8 | 24 | 0.848 | 67 | 0.946 |

## Each run against the placebo, position by position

Node count of the run divided by the node count of the placebo run on the same position.

| run | group | positions | geo | 95 % range by base |
|---|---|---|---|---|
| etc_cut6_ns | all | 91 | 0.915 | [0.827, 1.011] |
| etc_cut6_ns | endgame | 35 | 0.827 | [0.692, 1.010] |
| etc_cut6_ns | middlegame | 56 | 0.975 | [0.882, 1.078] |
| etc_cut6_fh | all | 91 | 0.939 | [0.858, 1.036] |
| etc_cut6_fh | endgame | 35 | 0.897 | [0.777, 1.066] |
| etc_cut6_fh | middlegame | 56 | 0.967 | [0.859, 1.089] |
| etc_cut8_ns | all | 91 | 0.946 | [0.845, 1.069] |
| etc_cut8_ns | endgame | 35 | 0.913 | [0.726, 1.181] |
| etc_cut8_ns | middlegame | 56 | 0.968 | [0.865, 1.082] |
| etc_cut8_fh | all | 91 | 0.966 | [0.873, 1.075] |
| etc_cut8_fh | endgame | 35 | 0.914 | [0.765, 1.124] |
| etc_cut8_fh | middlegame | 56 | 0.999 | [0.888, 1.124] |
| etc_cut6 | all | 91 | 0.965 | [0.874, 1.073] |
| etc_cut6 | endgame | 35 | 0.919 | [0.783, 1.108] |
| etc_cut6 | middlegame | 56 | 0.996 | [0.876, 1.131] |
| etc_cut8 | all | 91 | 0.934 | [0.841, 1.041] |
| etc_cut8 | endgame | 35 | 0.850 | [0.697, 1.071] |
| etc_cut8 | middlegame | 56 | 0.991 | [0.898, 1.092] |

