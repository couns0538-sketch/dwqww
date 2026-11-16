# REPORT — deepseek6, long 43 (the singular grid)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long43/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** `SingularMargin` 0,1,2,3,4 x `SingularDepth` 5,6,7,8 (20 settings, rest S14), O at depth 12; G for
the four corners and S14's own cell; the grid of ratios. Known: margin 2 × depth 6 = S14 = **9,500,069**.

**Answer:** both pins **EXACT** (O 9,500,069; G 18,466,239) and the grid is strongly anisotropic:
**`SingularMargin` is a 3.1× knob and `SingularDepth` is a 1.05× knob inside this window.** At depth 6 the O ratio
runs 2.4340 (margin 0) → 1.3891 (1) → 1.0000 (2) → 0.8617 (3) → 0.7863 (4); at margin 2 the depth axis runs only
1.0245 → 1.0000 → 0.9646 → 0.9762. **The cheapest cell is (margin 4, depth 5) at 0.7689, not (4,8)** — the depth
axis is not monotone at small margins (depth 8 costs more than depth 7 at margins 2, 3 and 4), and the two axes do
**not** multiply (worst cell off by 13.4 %).

**How sure:** certain of all 25 sums (committed rows and metas, one command re-derives the grid); the anisotropy
and the non-multiplication are measured, not interpreted.

## 2. Honesty numbers (raw in `raw/`)

Build: the plain 6b98f217 release build used throughout this chat, `/tmp/ds6/build-release/forge`, sha256
`7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`, `id name Chess Engine Forge 6.4.24
candidate`. Its four pins were exact at the start of this chat (`raw/` of my long 23, same binary).

**The item's own pins, met on the first run:**
| pin | required | measured | file |
|---|---|---|---|
| O (margin 2, depth 6) | 9,500,069 | **9,500,069** | `runs/O_m2_d6.rows` |
| G (margin 2, depth 6) | 18,466,239 | **18,466,239** | `runs/G_m2_d6.rows` |

Option ranges verified on the actual binary before the first run: `SingularDepth` default **7** min 2 max 20,
`SingularMargin` default 2 min 0 max 10. **The plain default of SingularDepth is 7, not 6** — S14 sets it to 6, so
the S14 cell of this grid is (2,6) and the *default* cell (2,7) is a different cell of the same grid.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed with `claim.sh` (its output is stamps.txt's first line) | done | `stamps.txt` line 1 | exit 0, 20:23:02Z |
| prediction as its own commit | done | `PREDICTION.md` (80252ca8e) | 8 predictions with kill ranges |
| 20 O cells at depth 12 | done | `runs/O_*.rows` (20), `opts/m*_d*.txt` | S14 cell exact |
| 5 G cells | done | `runs/G_*.rows` (5) | S14 cell exact |
| grid + marginals + interaction | done | `grid43.py`, `grid_out.txt` | section 4 |
| prediction scorecard | done | `scorecard.txt` | 4 held, 1 half, 3 killed |

Every rows file has a `.meta` beside it with the exe path, its sha256, the `id name`, the FEN set and count, the
depth and every setoption line in order. 200 rows on O, 353 on G, in every file.

## 4. The grid (from `grid_out.txt`; `python3 grid43.py runs`)

**O node sums, ratio to S14 in brackets:**

| margin | depth 5 | depth 6 | depth 7 | depth 8 |
|---|---|---|---|---|
| 0 | 24,570,190 (2.5863) | 23,123,178 (2.4340) | 20,514,854 (2.1594) | 19,556,349 (2.0585) |
| 1 | 14,345,004 (1.5100) | 13,196,949 (1.3891) | 12,698,069 (1.3366) | 11,531,769 (1.2139) |
| 2 | 9,732,613 (1.0245) | **9,500,069 (1.0000)** | 9,163,603 (0.9646) | 9,273,898 (0.9762) |
| 3 | 8,241,169 (0.8675) | 8,186,451 (0.8617) | 7,768,700 (0.8178) | 8,396,951 (0.8839) |
| 4 | **7,304,352 (0.7689)** | 7,469,959 (0.7863) | 7,381,877 (0.7770) | 7,714,548 (0.8121) |

**G corners:**

| cell | G sum | G ratio |
|---|---|---|
| margin 0, depth 5 | 31,368,020 | 1.6987 |
| margin 0, depth 8 | 21,741,249 | 1.1774 |
| margin 2, depth 6 (S14) | 18,466,239 | 1.0000 |
| margin 4, depth 5 | 16,120,691 | 0.8730 |
| margin 4, depth 8 | 12,571,186 | 0.6808 |

## 5. Findings, each with the command that shows it again

**F1. The two axes are not on the same scale at all: margin 3.1×, depth 1.05×.**
`grid_out.txt`, the two marginal tables: margin span at depth 6 = 2.4340/0.7863 = **3.0955**; depth span at
margin 2 = 1.0245/0.9762 = **1.0495**. A tuner that moves both by one step will spend its budget on the wrong
axis: margin 2→1 is +39 % on the O tree, margin 2→3 is −14 %, while depth 6→5 is +2.5 % and 6→7 is −3.5 %.

**F2. The depth axis stops being monotone once the margin is at or above the S14 value.** At margins 0 and 1 the
O ratios are strictly ordered d5 > d6 > d7 > d8; at margins 2, 3 and 4 the depth-8 run costs MORE than depth 7
(1.0245→1.0000→0.9646→**0.9762** at margin 2; 0.8675→0.8617→0.8178→**0.8839** at margin 3;
0.7689→0.7863→0.7770→**0.8121** at margin 4). So "deeper singular search is cheaper" is true only where the
margin is small enough that singular search actually fires often.

**F3. The cheapest cell of the grid is (margin 4, depth 5) = 0.7689, not (4,8) = 0.8121.** My P6 predicted (4,8)
and is half killed; the reason is F2 — at margin 4 the depth-5 cell is the cheapest, and depth 8 is the most
expensive of the margin-4 row.

**F4. The product of the singles does not predict the grid.** Worst cell: (margin 0, depth 8) measures 2.0585
against 2.3761 predicted by ratio(0,6) × ratio(2,8), i.e. **13.4 % off**; five of nineteen cells exceed 5 %
(`grid_out.txt`, the P5 table). This is the same question long 36 asked and answered wrong by mismatching values;
here every single was measured at the value it is used at, so the failure is real interaction, not bookkeeping.

**F5. G's ordering swaps one pair against O's.** O cheapest-first: (4,5), (4,8), (0,8), (0,5). G cheapest-first:
**(4,8), (4,5)**, (0,8), (0,5). On G the depth-8 corner of the margin-4 pair is cheaper; on O it is not. Small,
but it is the same F2 effect appearing in the corners and it kills my P7 rank-correlation prediction.

**F6. Best-move churn is high across the grid and flat.** Against the S14 cell, the other 19 cells change 45–58
of 200 best moves each (`grid_out.txt`, last table). The S14 cell itself changes 0 by definition. Margin 2 × depth
7 changes 54, margin 0 × depth 5 changes 55 — node totals spanning 2.6× to 0.79× but the same order of move
churn. Node count is a poor proxy for how much a setting changes the search's choices.

## 6. What I read from my colleagues

Nothing new this item (about 15 minutes of work; the colleague read is on the four-hour clock). No advice from a
note was used. The one colleague input I did use is my own long-34 measurement of the same two options' extremes,
which is what made me predict a steeper margin axis; it was right about the direction and far too timid about the
size.

## 7. What I did NOT do

- **Did not run G for the sixteen interior cells** — the item asks for the four corners and S14's own cell only.
- **Did not test margins above 4 or depths above 8** — the item names this window; long 34 covers the option
  extremes (margin 10, depth 20) at depth 8 on a different position subset.
- **Did not run any match.** These are node counts; nothing here says a smaller tree is a stronger engine.
- No pull request, no branch but mine, no engine source.

## 8. What I am NOT sure about

- Whether F2's non-monotonicity at high margins is a depth-8 artefact of *this* position set (200 openings). G's
  margin-4 corner behaves the other way (F5), so the effect may be set-dependent rather than general.
- Why the product fails (F4). I can show the numbers do not multiply; I have not instrumented which sites change.
- The 45–58 best-move churn (F6) says the settings matter for move choice at every cell, but churn is not
  strength; only a match can say which side of these cells is better.

## 9. A better way

For a two-option grid, measure the two marginals **at the S14 value of the other option** (which this item did)
and then report the interaction table as the primary result rather than the ratio grid — F4 is the finding, and a
ratio grid alone invites exactly the "product of singles" reasoning that fails by 13 %. I put the interaction
table in the report for that reason.

## 10. Times and the folder

times: see `stamps.txt` (its first line is `claim.sh`'s output, as file 12 requires).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
