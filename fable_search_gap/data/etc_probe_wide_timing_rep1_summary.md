# etc_probe summary: etc_probe_wide_timing_rep1.tsv

Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.
Terms are defined at the top of `tools/etc_probe/summarize.py`.

Positions in the file: 95. Left out: 0 stopped by the node cap, 4 with a board that repeats an earlier position. Used: 91, from 24 base positions.

- endgame: 35 positions from 10 bases
- middlegame: 56 positions from 14 bases

Plain run repeated: identical node counts in 91/91 positions; time ratio of the totals 1.0028; per position the time ratio has standard deviation 3.8 %.

## Counting runs (identical tree)

| rule | group | positions | same nodes as plain | plain nodes | eligible share | hit rate | first proof is the hash move | below-hit share | lookup time | plain search also failed high |
|---|---|---|---|---|---|---|---|---|---|---|
| cut6 | all | 91 | 91/91 | 57047775 | 2.17 % | 13.5 % | 29.0 % | 6.85 % | +4.6 % | 100.0 % |
| cut6 | endgame | 35 | 35/35 | 30641405 | 2.80 % | 17.7 % | 29.4 % | 11.07 % | +4.9 % | 100.0 % |
| cut6 | middlegame | 56 | 56/56 | 26406370 | 1.44 % | 4.2 % | 24.6 % | 1.96 % | +4.5 % | 100.0 % |
| cut8 | all | 91 | 91/91 | 57047775 | 0.84 % | 14.2 % | 33.4 % | 4.73 % | +2.1 % | 100.0 % |
| cut8 | endgame | 35 | 35/35 | 30641405 | 1.22 % | 17.1 % | 33.7 % | 7.76 % | +2.2 % | 100.0 % |
| cut8 | middlegame | 56 | 56/56 | 26406370 | 0.41 % | 3.9 % | 29.9 % | 1.21 % | +2.0 % | 100.0 % |

