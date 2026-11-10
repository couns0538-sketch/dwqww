# Pawn ending (Fine 70) under placebo-size changes

Baseline plus 10 perturbed copies. Each copy changes one history constant of the replica by a small
amount and is run plain and with every setting of the mechanism, at depths 24, 26, 28, 30, 32, 34, 36 and 40.
The winning move is 1.Kb1 (`a1b1`). Terms: `tools/etc_probe/summarize.py`.

| Setting | Baseline | Perturbed copies with Kb1 at every depth | Copies with another move at some depth | Copies with another move at depth 40 | Nodes at depth 40: smallest to largest over the copies |
|---|---|---|---|---|---|
| plain | Kb1 at every depth | 10 of 10 | 0 of 10 | 0 of 10 | 3.90 M to 41.38 M |
| cut4 | Kb1 at every depth | 6 of 10 | 4 of 10 | 0 of 10 | 1.02 M to 6.57 M |
| cut6 | Kb1 at every depth | 10 of 10 | 0 of 10 | 0 of 10 | 0.98 M to 17.88 M |
| cut6, no store | Kb1 at every depth | 9 of 10 | 1 of 10 | 0 of 10 | 0.61 M to 4.24 M |
| cut6, return beta | Kb1 at every depth | 10 of 10 | 0 of 10 | 0 of 10 | 1.92 M to 5.25 M |
| cut8 | other move at depth 24, 26, 28, 30, 32, 34, 36, 40 | 4 of 10 | 6 of 10 | 2 of 10 | 0.18 M to 3.21 M |
| cut8, no store | Kb1 at every depth | 5 of 10 | 5 of 10 | 0 of 10 | 0.51 M to 3.93 M |
| cut8, return beta | other move at depth 24, 26, 28, 30, 32, 34, 36 | 4 of 10 | 6 of 10 | 1 of 10 | 0.46 M to 8.30 M |
| all3 | other move at depth 24 | 1 of 10 | 9 of 10 | 0 of 10 | 0.52 M to 11.64 M |

