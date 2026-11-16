# deepseek6 long 51 — PREDICTION (written before the first measuring command)

Item (file 13, long 51): **long 41 and 42 on G at depth 14 for the bundle of four and its best pair (largest G
shrink): do the interactions grow or shrink with depth.**

Model: DeepSeek V4.1 Flash 1017. Time: `stamps.txt`, first line is `claim.sh`'s output, then a line before each run.

## The settings, fixed from the committed long-41 table (not from memory)

The four settings at the ends that shrink G (long 41's table, read from
`tests_deepseek6_long41/table.txt`), with their G ratios at depth 12:

| tag | option value | G ratio at d12 |
|---|---|---|
| SD7 | `SingularDepth 7` | 0.9092 |
| LQD193 | `LmrQuietDivisor 193` | 0.9293 |
| LQB101 | `LmrQuietBase 101` | 0.9438 |
| IIR1 | `IirDepth 1` | 1.0042 (the odd one: nearly inert on G) |

- **The bundle** = all four together. Long 42 measured it on G at d12: **0.8569** against a product of **0.8007**
  (+7.03 %).
- **The best pair** = SD7 + LQD193, the largest G shrink of the six (long 41): **0.8504** against product
  **0.8449** (+0.66 %) at d12.

**Why seven runs and not three:** the item asks whether the interaction grows or shrinks *with depth*, and an
interaction is measured against the product of its own singles. At depth 12 the singles are committed in long 27's
table. At depth 14 they are not, so I must measure them: G at depth 14 for S14 (base), each of the four singles,
the pair, the bundle = **7 runs**, all 353 positions, depth 14.

## Predictions, each with the range that kills it

**P1 — G's S14 sum at depth 14 is between 40 M and 60 M.** G at depth 12 is 18,466,239 and my long-25 O growth
factors were 2.20–2.31 for depth 12→14; on G the factor should be similar or a little higher because G positions
are game positions with more pieces. 18.47 M × 2.1–3.2. Kill range: outside 40–60 M.

**P2 — the four depth-14 singles keep their G ordering at depth 14**: SD7 < LQD193 < LQB101 < IIR1, i.e.
SingularDepth 7 shrinks G most and IirDepth 1 least. Kill range: any inversion among the three that shrink.

**P3 — the bundle's G interaction at depth 14 is SMALLER in percentage than at depth 12.** At d12 the bundle is
+7.03 % over its product; prediction: at d14 it is within +0.0 % to +5.0 %. Reasoning: at greater depth each
setting's saving is a smaller fraction of a much larger tree, so overlapping savings overlap less in absolute
terms and the product approximation should improve. Kill range: above +7.03 % (interaction grows) kills P3;
below 0 % (sub-multiplicative, i.e. the bundle shrinks MORE than the product) also kills it, and would be the
more interesting outcome.
The same prediction for the **pair**: at d12 it is +0.66 %; at d14 I predict **within ±3 %**. Kill range: outside.

**P4 — the pair's interaction and the bundle's move in the same direction between the two depths.** If the bundle
improves, the pair improves too. Kill range: opposite signs.

**P5 — depth 14 leaves the best-move churn high**: every one of the 7 runs changes at least 100 of 353 best moves
against the depth-14 S14 run, the bundle more than any single. Kill range: a run below 100, or the bundle not the
largest.

**P6 — budget.** Seven G runs at depth 14: I predict 25–45 minutes at 3-way parallelism, and I will run them in
two batches (base + four singles, then pair + bundle) so a cut-off loses at most one batch. Kill range: a single
run over 1800 s gets killed and reported as "timeout", not as a result.

## What would make me report "not done"
A depth-14 run I cannot finish inside the budget: the report then names the runs done, gives the interaction for
the pair only if its singles are done, and says plainly which comparison is missing. A product computed from a
single measured at a different value is not a product: every product here is built from the value that was run.
