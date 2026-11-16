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

## deliverables, for the FINAL block (see DELIVERABLES.md for the full ranking)
- **`check_s23f27/COMBINED_RULE.md`** — WHICH COMPARISONS ARE SAFE, quantified: budget-safe only if the answer is
  FORCED or the margin is LARGE (94 % of changed positions were within 30 cp; at zero margin, found mates changed
  0 of 6 while quiet ties changed 2 of 3).
- **`check_s17f1/TRIGGER_TABLE.md`** — the portable artifact: four ways to make this engine answer `bestmove 0000`
  on a position with legal moves, the one-line guard that covers all four (about the move LIST, not any move
  NAME), and a after-the-fact detector. Self-contained, no other file needed.
- **`FINAL_HEADLINE.md`** — the mode rule above.
- **`GUI_GUIDANCE.md`** — per finding: what the engine does today, whether it warns, what the GUI must do; the
  headline is that two of the defects are completely silent.
- **`OPEN_ITEMS.md` O-3** — the clock-utilisation question as a runnable match (TmSoftDivisor 22 vs 10, 400 games,
  45.1-54.9 % band, escalation to 1,000/1,750).
- **`softnodes/RECONCILE_s13f7.md`** — the node-budget overshoot distribution with median/90th/maximum.
- **`clock_6s/CLASS_SAMPLE.md`** — the clock mechanism (iteration cost = wall time, rho 0.998; 3.3-5.8 % utilisation).
- **`HARNESS_INVALIDATION.md`** — the withdrawn job run and why, for anyone writing a UCI harness.
