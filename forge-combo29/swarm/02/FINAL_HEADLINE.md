# The three-mode summary and the rule — for the FINAL block

Measured on the PC r15 build under PC20, Threads 1, Hash 16, OwnBook false, cold, interactive driver.

| command pair | do they differ on ambiguous positions? | evidence |
|---|---|---|
| `go nodes` vs `go softnodes` (same nominal N) | **YES** — 3 of 12 cells at 9-15 cp gaps (seat 19: 18.4 % at 2-12 cp) | S-C10 |
| `go nodes` vs `go softnodes` on **exactly-tied** positions | **YES for quiet ties** (1 of 6), **no for found mates** (0 of 12) | S-C11, S-C12 |
| `go movetime` vs `go nodes` (at matched DEPTH) | **NO** — at depth 13 all three of `depth`, `nodes`, `movetime` return the same move | S-C13 |

## the rule, in one line
**Across search modes only same-depth results are comparable: `go nodes` and `go softnodes` genuinely pick
different moves at the same nominal budget, while the clock and the node mode agree once they reach the same
depth — so mix no results, and never compare different depths.**
