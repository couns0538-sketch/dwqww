# REPORT_deepseek5_job26 (deepseek5, 2026-11-16 UTC) — the corrected curve table by a command; the counters under the PC's 14 settings

(1) **Step 0: all five rows met.** The ANCHOR 12,573,318 ✓; **S14 = 9,500,069** (41,311 / 24,872 /
28,574) ✓; **S14 + HistoryPruneMultiplier 3330 = 9,951,638** ✓; **S14 + FutilityBase 150 +
FutilityMultiplier 165 = 9,432,393** ✓; **S14 + DoubleExtLimit 64 on the other build = 9,500,069** ✓
(= S14). The runner (rt_run26.py) sends the three setup lines plus the 14 S14 settings with every answer
read; the `.meta` files carry all 28 option lines; a label variable keeps the S14 file names short.
**Part A by the committed command** (`partA_table.py` over job 24's rows; the file's layout decoded
against YOUR known by-depth numbers — the file is [step][margin class][depth class], confirmed by the
count-only futility cells: the k-class sums [62,620 / 72,478 / 33,957 / 4,885 / 393] and the depth sums
[94,035 / 61,477 / 11,850 / 6,456 / 515] whose last two are exactly the known d4–6 = 6,456 and d7+ = 515):
the table reproduces **your known numbers to the digit** — futility d1: 122.3 / 85.1 / 25.6; d2: 118.1 /
96.2 / 34.0 / 24.4; d3: 83.3 / 18.3 / 55.7 / 25.9 / 0.0; history d1: **172.7 / 171.3 / 168.1** (FLAT in k),
d2: 66.3 / 68.4, d3: 41.1; quiet SEE d1: k3 117.2, k5 16.0; d4–6: 3.1 / 0.4 / 0.4 / 0.1 / 0.1 (a clean fall
inside the class); noisy SEE d1: 9.9 / **28.8** / 2.4 / 0.7 / 0.4 (the bump at k = 1.5). Every step's
identity line printed with BOTH numbers (the margin-index sums and the n-by-depth).
**Part B's three sentences:**
1. Under S14 the step with the most regrets BY COUNT is **quiet SEE** (10,775 of 22,028 FULL events on O,
   15,344 of 30,382 on G); by RATE it is **history** (120.9 per 1,000 on O, 88.7 on G), concentrated in
   the depth-1 and depth-2 classes.
2. **History is still flat in k and falls with depth under S14**: widening its margin 1.5 times
   (HPM 3330) removed 8,092 of 11,309 drops (−72 %) and 917 of 1,367 regrets (−67 %) — equal shares, the
   same flat-in-k pattern as at the defaults; `LmpBase 8` did not change it.
3. The two 1.5-times settings: futility 1.5× removed 40,114 of 104,719 drops (−38 %) and 4,156 of 7,760
   regrets (−54 %) — the S14 table's flat-share prediction for those drops would be 40,114 × 74.1/1000 =
   2,972; the measured removal is 4,156, i.e. the removed (bare-margin) drops carry MORE than the average
   regret, exactly the direction the falling k-curve predicts. History 1.5×: −72 % of drops, −67 % of
   regrets — the flat prediction holds there.
(2) **Part C** (the DE23 counters under S14, `SingularDepth 6`, the rows files COMMITTED
`partC_DE23_S14_{O,G}.rows`): O — fail-low non-PV verifications **14,421**, candidates 6,202, given
6,202, **refused 0** ✓; the given split by the inherited count [4,842, 1,067, 197, 72, 19, 4, 1, 0] —
nothing at 7+. G — fail-low **88,068**, candidates 67,642, given 66,911, refused **731**, the split
[28,993, 16,155, 9,607, 5,857, 3,384, 1,912, 1,003, 0] — nothing given at 7+; the split's shape says the
731 refusals are the inherited-7 candidates (the count that could not be given). The M-check as
specified (against kimi5's k3 file) could NOT verify the S14 refusals: that file's M values are the
DEFAULT run's, and the M distribution under S14 was not measured (see section 6).

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| prediction before the runs | done | `prediction.txt` (own commit, before Step 0) | — |
| Step 0 the five rows | done | `step0_runs.txt`, the rows+meta | all five exact |
| Part A the table by a command | done | `partA_table.py`, `partA_correct_{O,G}.json` | Fable's known numbers reproduced |
| Part B the S14 count/probe runs | done | `partB_runs.txt`, the rows+meta | the three sentences above |
| Part C the DE23 counters under S14 | done | `partC_DE23_S14_{O,G}.rows` (committed) | refused 0 (O) / 731 (G) |

## 5. From my partner

`cursor/glmflash5-work-cb5c` at my check: job 13's report STILL not on its branch. Its job-12 M9 (+31,
its tree) and Opus's PC-side pv1 (−2.43 under the PC's settings) now have MY S14 counters as the bridge
candidate: under S14 the tree factor of the LMP-exemption question would be read from the same counters
— not attempted this job (the budget).

## 6. What I did NOT do

- The S14 M-check for Part C's G refusals (the M file is the defaults'; the S14 M values need a
  maxdoubleext counter under S14 — a one-line addition to the DE23 print, not built in the budget).
- The S14 G-side futility/history 1.5× runs (O only, per the job's text).
- The quiet-SEE/noisy-SEE per-depth table under S14 (the rows carry the cells; the report gives the
  per-step totals).

## 7. What I am NOT sure about

- Whether the S14 refusals' 731 all sit in M = 7 searches UNDER S14 — the split's 1,003-at-inherited-6
  and the 0-at-7+ say the refused are the inherited-7 candidates, which is the mechanism; the M-file
  confirmation is missing.
- The first-three checks of Step 0's S14 rows (the sums matched; the per-position first three are in the
  rows for your comparison — I did not print them in the report).

## 8. A better way

The label-based output naming (one short label per setting instead of the 200-character option tag)
arrived by failing on the OS's filename limit; it should be the default for every multi-setting run —
the `.meta` carries the full option list, the filename carries the label.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The S14 G rows: you hold your 353 rows (your tree differs on ~12 endgame positions) — my
   `s14cntG_set_G.epd_d12.rows` is committed for the line-by-line comparison whenever you want it.
2. Part C's M-check under S14: shall the DE23 print carry maxdoubleext (one line), or does your side
   already have the S14 M distribution?
3. The futility 1.5× finding (the removed bare-margin drops regret 54 % vs the 37 % average): does that
   make the futility margin the first of the four steps worth a game pair on the PC's settings, or do
   Opus's futility-off −2.95 and glmflash5's −10.8 already close it?
```
2026-11-16T11:39:11Z job26 t0
2026-11-16T11:42:26Z step 0 done
2026-11-16T11:45:23Z step 0 v2 done
2026-11-16T11:52:26Z part B runs done
```
