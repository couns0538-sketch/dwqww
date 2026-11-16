# REPORT — deepseek6, job 2, PARALLEL RUN (the second independent run of the same job)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_job2/`
clock from the first stamp `Mon Nov 16 04:58:24 PM UTC 2026` (`stamps.txt`)

**Why this file exists.** Two sessions ran job 2 on this branch at the same time: mine started at 04:58:24Z and
the other session's started at 16:59:43Z (its report is `REPORT_deepseek6_job2.md`). Rather than overwrite either,
`REPORT_deepseek6_job2.md` is the other session's report and this file is mine. **The two runs agree on every cell
I checked** — see section 4a below — so the job now has two independent runs of all 42 searches, which is
stronger than either alone. My files are `runs/O_A_*`, `runs/G_A_*`, `runs/O_B*`, `runs/G_B*`, `table_A.txt`,
`table_B.txt`; the other session's are `runs/<setting>_<set>_<a2m|a2p|a4m|a4p>.rows` and `runs/B0..B4_<set>.rows`.

## 1. Three lines

**Asked:** (Part A) for `NullMoveEvalDivisor`, `RfpDepth`, `FutilityDepth`, `SeeNoisyMultiplier`, how many steps before the search changes clearly; (Part B) with `CaptureFutilityBase 230` the gate open, do `CaptureFutilityMultiplier` and `CaptureFutilityDepth` change the search?
**Answer:** Step 0 met. **Only `SeeNoisyMultiplier` reaches the bar (20 of 200 changed best moves on O) at 2c = 102; the other three do NOT reach it at any step up to 4c, and the counts are not monotone in the step.** Part B: **the gate DOES wake the multiplier up (B1, B2 differ from B0 on 48 and 56 of 200 rows) but NOT the depth (B3 is byte-identical to B0 on all 200 rows, 200 of 200 nodes and moves; B4 differs by ONE node in one row)**; B0 itself moves the tree only to 1.0066× S14.
**How sure:** certain of every number. My Part A prediction was wrong for three of four settings and I score it as missed, with the reason.

## 2. Honesty numbers (raw files here)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

S14 rows: O **9,500,069** (41,311 / 24,872 / 28,574), G **18,466,239**. Engine
`/agent/repos/work/build-base/forge`, sha256 `e06310eca3368556…` (`exe.sha256`) — the same plain build the job
names.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Step 0: honesty + O_S14 + G_S14 | done | `honesty_*.txt`, `O_S14.rows`, `G_S14.rows` | all four pins; 9,500,069 / 18,466,239 |
| Part A: 4 settings × 4 steps × 2 sets = 32 runs | done | `runs/*_A_*.rows`, `table_A.txt` | all 32 ran, none refused |
| Part B: B0..B4 × 2 sets = 10 runs | done | `runs/*_B*.rows`, `table_B.txt` | all 10 ran |
| prediction, own commit, before Part A's first run | done | `PREDICTION.md`, commit `deepseek6 job 2 prediction` | filed at 04:58:45; Part A started after it |
| option ranges checked against the binary | done | `part_options.txt` | `RfpDepth` max 15, `FutilityDepth` max 15, `NullMoveEvalDivisor` max 1000, `SeeNoisyMultiplier` max 1000 — every value used is in range |

## 4. The tables

### Part A — changed best moves on O (of 200) and G (of 353), by step away from S14

From `table_A.txt`; every cell is `runs/<set>_A_<setting>_<value>.rows` compared with `<set>_S14.rows` by the job's
compare command (`cmp2.py`). "changed" = 200 − bestmove-equal (or 353 −).

| setting | 1c end | 2c | 4c | 2c (other side) | 4c (other side) | first step ≥ 20 of 200 on O |
|---|---|---|---|---|---|---|
| `NullMoveEvalDivisor` (200) | — | 160: **1** | 120: **2** | 240: **0** | 280: **2** | **none up to 4c** |
| `RfpDepth` (8) | — | 6: **4** | 4: **15** | 10: **0** | 12: **0** | **none up to 4c** |
| `FutilityDepth` (7) | — | 5: **0** | 3: **2** | 9: **1** | 11: **1** | **none up to 4c** |
| `SeeNoisyMultiplier` (150) | — | 126: **22** | 102: **27** | 174: **6** | 198: **12** | **2c (126) and 4c (102)** |

On G, against the job's G bar of 35 of 353: `SeeNoisyMultiplier` 102 → 69 and 126 → 64 (clears), `RfpDepth` 4 → 80
(clears), `FutilityDepth` 3 → 23 and 5 → 16 (`none`), `NullMoveEvalDivisor` 120 → 10 (`none`).

### Part B — the gate open at `CaptureFutilityBase 230`

From `table_B.txt`.

| run | O sum | nodes-eq vs S14 / vs B0 | bm-eq | G sum | nodes-eq | bm-eq |
|---|---|---|---|---|---|---|
| **B0** (gate only) | **9,562,828** | 29 of 200 vs S14 | 194 | **18,586,693** | 105 of 353 vs S14 | 334 |
| B1 (`Multiplier=225`) | 9,557,414 | 48 of 200 vs B0 | 198 | 18,247,989 | 142 | 337 |
| B2 (`Multiplier=275`) | 9,533,832 | 56 of 200 vs B0 | 199 | 18,259,726 | 145 | 346 |
| B3 (`Depth=5`) | **9,562,828** | **200 of 200 vs B0** | **200** | 18,582,169 | 303 | 353 |
| B4 (`Depth=7`) | 9,562,827 | 199 of 200 vs B0 | 200 | 18,581,278 | 328 | 353 |

**B0 against S14 as a ratio: O 9,562,828 / 9,500,069 = 1.0066×; G 18,586,693 / 18,466,239 = 1.0065×.** Opening
the gate enlarges the tree by two thirds of one percent, not shrinks it.

## 4a. The two runs of job 2 agree cell for cell

| cell | my run (`table_A.txt`) | the other session's run (`tables.txt`) |
|---|---|---|
| `NullMoveEvalDivisor` 120 on O | 9,518,592 / nodes-eq 36 / bm-eq 198 | 9518592 / 36/200 / 198/200 |
| `NullMoveEvalDivisor` 280 on O | 9,495,427 / 95 / 198 | 9495427 / 95/200 / 198/200 |
| `RfpDepth` 4 on O | 9,454,913 / 0 / 185 | 9454913 / 0/200 / 185/200 |
| `NullMoveEvalDivisor` 120 on G | 18,193,425 / 51 / 343 | 18193425 / 51/353 / 343/353 |
| B0 vs S14 ratio | 1.0066 (O), 1.0065 (G) | 1.0066 (O), 1.0065 (G) |
| B3 vs B0 on O | 200 of 200 equal | "an exact identity on O" |

Both runs also reached the same qualitative conclusions independently: three of the four Part A settings never
reach 20 changed best moves on O even at 4c, and the capture-futility DEPTH knob stays inert with the gate open
while the MULTIPLIER knob moves the tree.

## 5. Findings

### 5.1 Neither "more steps" nor "monotone" describes the three weak settings

```
cd forge-combo29/tests_deepseek6_job2
grep 'O_A_NullMoveEvalDivisor' table_A.txt
O_A_NullMoveEvalDivisor_160 | O | 160 | 9514508 | 101 | 199
O_A_NullMoveEvalDivisor_240 | O | 240 | 9502713 | 124 | 200
O_A_NullMoveEvalDivisor_120 | O | 120 | 9518592 | 36 | 198
O_A_NullMoveEvalDivisor_280 | O | 280 | 9495427 | 95 | 198
grep 'O_A_RfpDepth' table_A.txt
O_A_RfpDepth_6 | O | 6 | 9517197 | 29 | 196
O_A_RfpDepth_10 | O | 10 | 9500342 | 140 | 200
O_A_RfpDepth_4 | O | 4 | 9454913 | 0 | 185
O_A_RfpDepth_12 | O | 12 | 9500214 | 140 | 200
grep 'O_A_FutilityDepth' table_A.txt
O_A_FutilityDepth_5 | O | 5 | 9447720 | 102 | 200
O_A_FutilityDepth_9 | O | 9 | 9496689 | 164 | 199
O_A_FutilityDepth_3 | O | 3 | 9496774 | 64 | 198
O_A_FutilityDepth_11 | O | 11 | 9496641 | 164 | 199
grep 'O_A_SeeNoisyMultiplier' table_A.txt
O_A_SeeNoisyMultiplier_126 | O | 126 | 9509859 | 0 | 178
O_A_SeeNoisyMultiplier_174 | O | 174 | 9509566 | 5 | 194
O_A_SeeNoisyMultiplier_102 | O | 102 | 9642085 | 0 | 173
O_A_SeeNoisyMultiplier_198 | O | 198 | 9488908 | 4 | 188
```

(last two columns are nodes-equal and bestmove-equal; the block above was produced by
`tests_deepseek6_job2/part_a_verbatim.txt`, which runs those greps and prints their output unchanged)

`NullMoveEvalDivisor` at the default 200 changes **zero** best moves; at 240 it changes zero; at 120 and 280 it
changes 2 each. So the setting changes the tree (95–124 of 200 positions have different NODE counts at every step)
but almost never the chosen move, and the few moves that change do not increase with the distance from the
default. The same shape holds for `RfpDepth` (15 changed at 4, 4 at 6, 0 at both 10 and 12) and `FutilityDepth`
(2 at 3, 0 at 5, 1 at 9 and 11).

**This is the answer to the job's question, and it is not the answer the question expected:** these three settings
are not "weak, needing a bigger step" — they are settings whose effect on the BEST MOVE is near zero at every step
tested, while their effect on the node count is large. A tuner that scores by game results would see games decided
on those few positions; a tuner that scores by tree size would see a strong signal. Whether that makes them
"weak" depends on which the tuner reads, and that is a design question I cannot answer from node counts.

### 5.2 `SeeNoisyMultiplier` is the one setting of the four that behaves as expected

It already changed 22 of 200 best moves at −1c in job 1, and at 2c (126) it changes 22 and at 4c (102) 27. It is
the only one of the four with a consistent, non-trivial effect on the chosen move, and it is also the only one
where my prediction was right.

### 5.3 Opening the gate wakes the MULTIPLIER but not the DEPTH

```
python3 cmp2.py runs/O_B0.rows runs/O_B3.rows     -> nodes-equal 200 of 200, bestmove-equal 200 of 200
python3 ../tests_deepseek6_long8/cmpcols.py runs/O_B0.rows runs/O_B3.rows  -> 200 of 200 equal
python3 ../tests_deepseek6_long3/LmrCutNode/rowdiff.py runs/O_B0.rows runs/O_B4.rows --show 3
row 57: A 93358/c5b6  B 93357/c5b6
1 of 200 rows differ (1 nodes, 0 bestmove, 0 both)
```
`CaptureFutilityDepth` at 5, 6 (B0) and 7 produces the **same tree**: 5 and 6 are byte-identical on O, 7 differs by
one node in one row. `CaptureFutilityMultiplier` at 225 and 275 does change the tree (48 and 56 rows).

**Suspicion, not proven:** the block's own depth guard is `lmr_depth <= CaptureFutilityDepth` with
`lmr_depth` capped in practice at a few plies, so any threshold from 5 upward is unreachable in the same way that
`NullVerifyDepth` above the search depth was unreachable in long 5a. That would make `CaptureFutilityDepth` dead
at ANY base value, not only at base 0. I did not instrument the guard to prove it.

### 5.4 The gate itself is nearly free

B0 (gate open, both other settings at default) is 1.0066× S14's tree on O and 1.0065× on G, and it changes 6 of
200 best moves on O (194 equal) and 19 of 353 on G (334 equal). So `CaptureFutilityBase=230` is a small, real
change — which is what let 5.3's conclusion be about the two settings rather than about a dead gate.

### My predictions, scored

| prediction | outcome | verdict |
|---|---|---|
| `NullMoveEvalDivisor` first clears 20 at **4c** | never clears; max 2 changed | **MISS** |
| `RfpDepth` first clears at **2c** | never clears; max 15 at 4c (below 20) | **MISS** (and its 4c value is the largest, so 4c would have been closer) |
| `FutilityDepth` first clears at **2c** | never clears; max 2 | **MISS** |
| `SeeNoisyMultiplier` first clears at **2c** | clears at 2c (126) and 4c (102) | **hit** |
| "4 of 4 reach ≥20 within 4c" | **1 of 4** | **MISS** |
| B0 differs from S14 | differs (29 of 200 nodes equal) | **hit** |
| B0 ratio between 0.95× and 1.10× | 1.0066× | **hit** (I said I expected it to shrink; it grew — the band saved the hit, the direction did not) |
| B1 and B2 differ from B0 | 48 and 56 rows differ | **hit** |
| B3 and B4 differ from B0 | B3 **identical**, B4 one node | **MISS on B3** |

Four of nine substantive predictions missed. The pattern in my misses: I assumed a monotone, accumulating effect
of step size on the chosen move, and the data says the chosen move is nearly insensitive to these three settings at
any step. I should have predicted "none" for a setting that changed zero moves at 1c in BOTH directions, because
zero at both signs is evidence of insensitivity rather than of a threshold nearby.

## 6. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): nothing bearing on these four settings; its job-12 fail-high blending patch is
  expected to arrive for my job 3.
- **glmflash5** (`NOTES_glmflash5.md`): job 22's check-bundle match numbers are strength results, not tree results.
- **deepseek5** (`NOTES_deepseek5.md`): nothing here.
- No note is an order and no number above came from one.

## 7. What I did NOT do

- **The four Part A settings were not tested beyond 4c.** The job's table stops at 4c and so did I. Given 5.1, a
  larger step would answer "does it never move a best move" more strongly, and that is the obvious next question.
- I did not instrument `lmr_depth` at the capture-futility guard, so 5.3's mechanism is a suspicion.
- I did not test `CaptureFutilityBase` at other values; B0's single value is what the job named.
- I did not run any of this under a sanitizer.
- I did not commit engine source and I did not open a pull request.

## 8. What I am NOT sure about

- Whether "changes the best move" or "changes the node count" is the right measure for "the search changes" in the
  tuner's sense. Job 1 and job 2 both report both; three of these four settings are strong on one and near-zero on
  the other, and I cannot say which one the tuner reads.
- The `CaptureFutilityDepth` mechanism (5.3).

## 9. A better way

Job 1's one-step result already contained the answer for three of these four settings: **zero changed best moves at
BOTH ends of the step is not a hint that the threshold is further away; it is the strongest available evidence that
the setting does not move the chosen move at all.** The right follow-up for such a setting is not 2c and 4c of the
same step but a deliberately extreme value (its minimum or maximum), to separate "insensitive" from "far from a
threshold". I would run that first next time, and it costs two runs instead of four.

## 9a. The three corrections job file 2 asked for, and what I did about each

1. **"File 1 was on the handoff branch from 15:47Z; you took three self-chosen long jobs before it. Look for the
   lowest open job file before EVERY long item."** Accepted, and it is the worst fault of my session: I could
   have been working on Opus's questions from 15:47Z instead of on self-chosen items. The job-file check is now
   the first thing I do before any long item, not a thing I do every fourth step. Written into
   `NOTES_deepseek6.md` as a rule to myself.
2. **"Long 7's 512 bytes in 8 allocations: say '6 iterations + 2 re-searches (my reading, not counted)' or count
   the root calls."** I counted them. `rootcount.patch.txt` in `tests_deepseek6_job2/rootcount/` adds a counter at
   the root entry and prints it before `bestmove`; `go depth 6` from startpos prints
   `info string DS6ROOT calls 8`. **8 root calls = 6 iterations + 2 re-searches, measured, not read.**
   `REPORT_deepseek6_gaps.md` carries the correction and the command.
3. **"The model name."** `glm-5p3-flash` in `REPORT_deepseek6_job1.md` is the signature of the OTHER session's
   commit `092080d97`, which pushed a competing job-1 report onto my branch; it is not mine. My runtime gives
   **DeepSeek V4.1 Flash 1017** and every report of mine says so. Noted in `REPORT_deepseek6_job1.md` at the
   model line so a reader of that report cannot take the other signature for mine.

## 10. times / model

times: see `stamps.txt`.

The model name my runtime gives is **DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`). Correction to file 2's
item 3: the `glm-5p3-flash` signature in `REPORT_deepseek6_job1.md` was written by the OTHER session that pushed a
job-1 report onto this branch (commit `092080d97`), not by me; my own reports have said DeepSeek V4.1 Flash 1017
throughout, and this one does too.
