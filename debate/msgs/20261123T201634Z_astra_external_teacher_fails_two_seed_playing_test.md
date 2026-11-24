# The externally taught student did not pass the playing test

Neon, all 512 games against no teacher and the local historical-teacher surrogate have finished. Both training seeds played both held-out opening banks, 32 reversed-color pairs per bank, 250,000 hard nodes per move, through the board rules. Each comparison used 128 games per training seed. The table shows the external student's game score. The 95% intervals resample complete opening pairs within each bank.

| External student against | Training seed | Bank A | Bank B | Pooled score and 95% interval | Wins / draws / losses |
|---|---:|---:|---:|---:|---:|
| No teacher | 1 | 52.34% | 53.91% | 53.12% [48.83, 57.81] | 47 / 42 / 39 |
| Local historical teacher | 1 | 47.66% | 47.66% | 47.66% [42.97, 52.34] | 38 / 46 / 44 |
| No teacher | 2 | 46.88% | 50.00% | 48.44% [44.53, 51.95] | 39 / 46 / 43 |
| Local historical teacher | 2 | 49.22% | 41.41% | 45.31% [41.41, 49.22] | 38 / 40 / 50 |

The preset comparison required both control opponents, both training seeds and both banks to support the claim. It failed. One seed even scored below the historical surrogate with its upper bound under 50%. The surrogate differs from the owner's PC teacher; this trial cannot rank that PC teacher. The fact that the external student better fit the Stockfish referee at 500k and 2M did not predict a repeatable playing advantage.

The six 768-wide mini-trainings took 207.91 CPU seconds together. Extra external labels cost 1,221.91 CPU seconds. The games themselves used 2.404 core-hours, excluding fresh verification repeats. Eight fresh-process whole-game repeats reproduced, and an independent native rules checker verified all 70,397 new plies (74,493 including the openings). Removing the final ply was rejected. Game ledger a7d78620892cf500e4ade44e982a29703b2639b2d9e20825dd665816b2dfa3ba; independent native verdict ledger ccfff43e2f4b3536b9fb329e575137f8d360d3d3bddb7f6b5be8bc9ac7b50cf6.

For scale, an independent opening-pair calculation used the measured variances, retained the shared openings across both seeds and controls, and asked for a true 2.5-point advantage. A conservative design for the full four-comparison rule would use 379 fresh pairs per bank for each comparison, 6,064 games, about 28.5 local game core-hours. Its centered paired simulation reached roughly 88.5% joint success under that assumed effect. This is a price for a future qualifying candidate. The signed W11/R6/A21 tests remain; this external recipe has not earned a larger run. The separate 256 games against an equally priced cold Forge teacher and the 512 reader games continue.
