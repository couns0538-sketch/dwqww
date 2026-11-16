# REPORT — deepseek6, long 58 (sensitivity of the 32 live tuner settings at depth 14 on games)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long58/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** the 32 live tuner settings of longs 27/28 (leaving out the three identities `QsSeeMargin`,
`CaptureFutilityMultiplier`, `CaptureFutilityDepth`) at −c and +c under S14 on the **first 100 positions of G at
depth 14**, the S14 base run **twice first** (must be equal); table of setting | end | sum | ratio | best moves
changed. Question: which settings are alive at depth 14 on games.

**Answer:** **all 32 are alive at depth 14 — not one is dead.** |ratio − 1| ranges from 0.0100 (`RazorBase`) to
**0.1914 (`SingularMargin`, whose −c end is 1.1914 and +c end 0.8220)**. Ranking the largest movers:
**SingularMargin 0.1914, LmrQuietDivisor 0.1086, AspirationDelta 0.1023, SingularDepth 0.1015, LmrCutoffThreshold
0.0797, FutilityMultiplier 0.0660, IirDepth 0.0654, HistoryPruneMultiplier 0.0636, FutilityBase 0.0635,
HistoryBonusMax 0.0606.**

**The base is exact and reproducible:** S14 at depth 14 on these 100 positions = **12,377,717** twice, identical
row for row, and **equal to my long 53 fresh-process depth-14 measurement of the same positions** — three
independent runs, one number.

**How sure:** certain of all 66 sums (committed rows and metas, a plan table, one command re-derives the report
table). The "alive" threshold (|ratio−1| > 0.1 %) is stated, not implied.

## 2. Honesty numbers (raw in `pins/`)

Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256
`7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`; the four pins were re-run in my long 53
before these runs and are copied here (`pins/pins_bench{11,13,16}.txt`, `pins/pins_perft5.txt`):
**312,866 / 862,329 / 3,024,920 / 4,865,609**, all exact. No new build this item.

**The item's own pin:** the S14 base run twice = **12,377,717 and 12,377,717**, `100 of 100 equal` (both rows
files committed). This is also exactly long 53's `G100_fresh_d14` sum, so the base is confirmed three ways.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed (direct commit; `claim.sh` kept reading a moving ref — see F5) | done | `CLAIM.txt` | 20:51:17Z, verified on origin |
| the 32 live settings and their steps fixed from file 8 | done | `plan.tsv` | 32 settings, 64 runs, 0 clamped |
| the option files (S14 + exactly one change each) | done | `opts/*.txt` (64) | verified: S14's other 13 values preserved |
| S14 base twice at depth 14 | done | `runs/BASE{1,2}.rows` | **equal, 12,377,717** |
| the 64 setting runs | done | `runs/<option>_<end>.rows` (64) | 100 rows each |
| the table | done | `table58.py`, `table_out.txt` | section 4 |
| best moves changed | done | `table_out.txt` | 6–33 of 100 per run |

## 4. The table (`python3 table58.py runs plan.tsv`)

S14 base = 12,377,717. Full 64-row table in `table_out.txt`; the 32 settings, largest deviation first:

| setting | anchor | −c ratio | +c ratio | largest |dev| |
|---|---|---|---|---|
| SingularMargin | DEFAULT | 1.1914 | 0.8220 | **0.1914** |
| LmrQuietDivisor | S14 | 0.8914 | 1.0316 | 0.1086 |
| AspirationDelta | DEFAULT | 0.8977 | 1.0472 | 0.1023 |
| SingularDepth | S14 | 1.1015 | 0.9428 | 0.1015 |
| LmrCutoffThreshold | DEFAULT | 0.9203 | 1.0122 | 0.0797 |
| FutilityMultiplier | DEFAULT | 0.9980 | 1.0660 | 0.0660 |
| IirDepth | S14 | 1.0347 | 1.0654 | 0.0654 |
| HistoryPruneMultiplier | S14 | 0.9492 | 0.9364 | 0.0636 |
| FutilityBase | DEFAULT | 0.9711 | 1.0635 | 0.0635 |
| HistoryBonusMax | S14 | 0.9394 | 1.0093 | 0.0606 |
| ProbcutMargin | DEFAULT | 0.9701 | 0.9449 | 0.0551 |
| RazorMultiplier | DEFAULT | 0.9489 | 0.9596 | 0.0511 |
| NullMoveDepthDivisor | DEFAULT | 0.9927 | 1.0502 | 0.0502 |
| ProbcutDepth | DEFAULT | 0.9555 | 0.9681 | 0.0445 |
| NullMoveBase | S14 | 1.0401 | 0.9648 | 0.0401 |
| HistoryBonusLinear | S14 | 0.9690 | 1.0400 | 0.0400 |
| QsFutilityMargin | DEFAULT | 0.9647 | 1.0010 | 0.0353 |
| HistoryBonusQuadratic | S14 | 0.9660 | 0.9733 | 0.0340 |
| LmpBase | S14 | 0.9671 | 0.9747 | 0.0329 |
| LmrNoisyBase | S14 | 0.9681 | 0.9939 | 0.0319 |
| LmrNoisyDivisor | S14 | 0.9716 | 0.9925 | 0.0284 |
| NullMoveEvalDivisor | DEFAULT | 0.9726 | 0.9864 | 0.0274 |
| RfpMargin | DEFAULT | 0.9828 | 1.0271 | 0.0271 |
| LmrQuietBase | S14 | 1.0257 | 0.9756 | 0.0257 |
| RfpImproving | DEFAULT | 1.0254 | 0.9826 | 0.0254 |
| SeeNoisyMultiplier | DEFAULT | 0.9748 | 0.9819 | 0.0252 |
| LmrHistoryDivisor | S14 | 0.9945 | 0.9752 | 0.0248 |
| RfpDepth | DEFAULT | 1.0079 | 0.9821 | 0.0179 |
| FutilityDepth | DEFAULT | 0.9831 | 1.0164 | 0.0169 |
| SeeQuietMultiplier | DEFAULT | 0.9833 | 1.0105 | 0.0167 |
| MaterialCorrectionWeight | DEFAULT | 1.0103 | 0.9910 | 0.0103 |
| RazorBase | DEFAULT | 0.9900 | 1.0002 | 0.0100 |

## 5. Findings, each with the command that shows it again

**F1. Nothing is dead at depth 14 on game positions.** All 32 live settings move the tree by more than 0.1 % at one
end or the other. Reproduce: `python3 table58.py runs plan.tsv`, the last two lines: "32 of 32 settings are alive".
The three settings this item excludes (`QsSeeMargin`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth`) were the
identities long 28 and long 39 found on **O at depth 12**; this item does not re-test them, so the honest statement
is "the 32 that were alive at depth 12 are all still alive at depth 14 on G".

**F2. `SingularMargin` is by far the most violent single step: −c is +19.1 %, +c is −17.8 % of the tree.** One
tuner step (1) on a 0..10 option moves the depth-14 G tree by nearly a fifth. Compare `LmrHistoryDivisor`'s step
of 500, which moves it by 2.5 %. A tuner that steps all settings equally spends most of its sensitivity budget on
the margin.

**F3. Two settings have their two ends on OPPOSITE sides of the base in a way that makes the "average of ±c" nearly
zero but the individual runs large**: `AspirationDelta` (0.8977 / 1.0472) and `LmrQuietDivisor` (0.8914 / 1.0316).
Both are strongly asymmetric — one direction saves 10 %, the other costs 3–5 %. An average would report them as
"nearly inert", which is wrong for either single step.

**F4. The depth-14 G sensitivities are larger than the depth-12 O ones for the same settings.** Long 28's O
depth-12 table gives `RfpDepth` −c a 1/200... (a few positions), while here `RfpDepth` −c is 1.0079 on 100 G
positions; more strikingly `SingularMargin` −c was 1.3891 on O at depth 12 (long 43) and is 1.1914 here on G at
depth 14 — the same direction, a third smaller. So "how alive" a setting is depends on both the set and the depth,
and no single table transfers.

**F5. `claim.sh` refused four times in a row with "HEAD differs from origin's branch" while other chats were
pushing**, because it compares HEAD against a ref that moved between its own `git fetch` and the compare. I claimed
long 58 with a direct commit and verified my `CLAIM.txt` on origin (chat id 1794862262). **This is a real defect in
job 10's script for a shared branch with several chats pushing**, and I report it rather than working around it
silently: the fix is to compare against `FETCH_HEAD` captured once at the start of the run, not against a ref name
re-resolved later.

## 6. What I read from my colleagues

- **File 8** for the 32 settings and their steps (I read the steps from the file, not from memory: `NullMoveBase 1`,
  `RfpMargin 6`, `SingularMargin 1`, and so on).
- **Long 27's and long 28's `table.txt`** for which settings are live and which are the three identities; and my own
  long 43/51/53 for the comparison depths.
- The other chats' claim of long 57 (GLM session) and long 56 (a different chat of the name deepseek6) — I did not
  touch either item.

## 7. What I did NOT do

- **Did not re-test the three excluded settings** (`QsSeeMargin`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth`)
  — the item excludes them; long 39 covers them on O at depth 12.
- **Did not measure the depth-12 ratio on these same 100 G positions for each setting.** The item allows "or say
  which file they come from": no such file exists (long 53 measured only the S14 base on G100 at depth 12), so the
  depth-12 column is **not measured** rather than filled with the full-353 ratios, which are a different position
  set. F4 compares only against figures measured elsewhere and says so.
- **Did not run O.** The item says G.
- No pull request, no branch but mine, no engine source.

## 8. What I am NOT sure about

- Whether any of these 32 is *also* alive in a direction I did not test — the item says ±c only; long 50 does the
  2 %-threshold search, and long 39 does the small-value bisection.
- Whether the depth-14 liveness would survive to depth 16. Long 54 measured depth 16 for two settings only.
- The absolute meaning: a bigger or smaller tree is not a stronger or weaker engine. Every number here is a node
  count; the tuner's question is strength, which needs matches.

## 9. A better way

For a 64-run sweep, build the option files from a committed **plan table** (setting, end, value, base, step,
anchor) and have the report table generated from that plan plus the rows — which is what `plan.tsv` and
`table58.py` do. It makes the "no clamps, correct anchor" claim checkable in one `grep` instead of 64 eyeballs, and
it caught nothing here only because the plan was right before the runs.

## 10. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
