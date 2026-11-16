# deepseek6 long 43 — PREDICTION (written before the first measuring command)

Item (file 12, long 43): **THE SINGULAR GRID.** `SingularMargin` 0, 1, 2, 3, 4 x `SingularDepth` 5, 6, 7, 8
(20 settings, the rest S14), O at depth 12; G for the four corners and S14's own cell. The table is the grid of
ratios. Known: `SingularMargin 2 x SingularDepth 6` = S14 = **9,500,069**.

Model: DeepSeek V4.1 Flash 1017. Time: `stamps.txt`, first line is the claim line, then a line before each run group.

## Fixed now

- Build: the plain 6b98f217 release build already used in this session, `/tmp/ds6/build-release/forge`, sha256
  `7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`; its four pins were exact at the start of
  this chat. Both options are in the plain build's own `uci` list (`SingularMargin` default 2 min 0 max 10,
  `SingularDepth` default 7 min 2 max 20), which I check before the first run rather than trusting memory.
  **Note the default of SingularDepth is 7, not 6** — S14 sets it to 6. So the S14 cell of the grid is
  (margin 2, depth 6) and the *default* cell is (2, 7), which is a different run in the same grid.
- 20 cells on O at depth 12 + 5 cells on G (the four corners and (2,6)) = **25 runs**, 200 and 353 positions.
- Harness: the committed `rows.py` from my long 32 (persistent stdin, because this engine aborts a search when
  stdin closes — my long-25 and long-34 lesson), one fresh process per position, `ucinewgame` + `isready` before
  every `go`, Threads 1, Hash 16, `.meta` beside every rows file, stops on `unknown option` / `invalid value`.

## Predictions, each with the range that kills it

**P1 — the S14 cell reproduces the known sum.** (margin 2, depth 6) on O = **9,500,069** exactly, and the same
setting on G = **18,466,239** exactly. Kill range: any other number, and the whole item stops (wrong build).

**P2 — `SingularDepth` 5 is the cheap corner and 8 is the expensive one.** Long 34 measured on the same build:
`SingularDepth 2` = 1.297x and `SingularDepth 20` = 0.908x of the depth-8 baseline — i.e. *lower* depth values
cost *more* nodes (singular search runs more often). Prediction: at margin 2, O ratios
depth5 > depth6 > depth7 > depth8, all four ordered with no inversion. Kill range: any inversion.

**P3 — `SingularMargin` is monotone at fixed depth: larger margin = smaller tree.** Long 34 measured
`SingularMargin 0` = 1.355x and `10` = 0.881x. Prediction: at depth 6, ratios for margin 0 > 1 > 2 > 3 > 4. Kill
range: any inversion.

**P4 — the margin axis is STEEPER than the depth axis inside this window.** Long 34's single-option extremes
suggested margin 0→10 spans 1.355→0.881 (a 1.54x span) while depth 2→20 spans 1.297→0.908 (1.43x). Over the
narrower grid (margin 0..4, depth 5..8) I predict the margin's span is still the larger: (ratio at margin 0,
depth 6) / (ratio at margin 4, depth 6) > (ratio at depth 5, margin 2) / (ratio at depth 8, margin 2).
Kill range: the depth span being larger kills P4.

**P5 — the interaction is weak.** The product of the two single-axis ratios predicts each cell to within 5 %:
for every (m, d), measured_ratio / (ratio(m, d=6) x ratio(m=2, d) / ratio(2,6)) ∈ [0.95, 1.05]. This is the same
"do they add up" question long 36 asked and got wrong by using mismatched singles; here every single is measured
at the value it is used at. Kill range: any cell outside ±5 % kills P5.

**P6 — the cheapest cell of the grid is (margin 4, depth 8)** and the most expensive is (margin 0, depth 5).
Kill range: any other pair.

**P7 — G agrees with O on the corners' ordering**: the four G corner ratios stand in the same order as the O
corners (rank correlation 1.0). Kill range: any inversion on G.

**P8 — budget.** 25 runs at depth 12, about 30–40 s each on this VM at 4-way parallelism: **10–20 minutes**.
Kill range: if a single run exceeds 600 s I report the cells done and name the rest.

## What would make me report "not done"
A build whose S14 cell misses the known sum (stop, commit raw, say so). An option refusal (that cell says
"refused" with the engine's line, and the item goes on).
