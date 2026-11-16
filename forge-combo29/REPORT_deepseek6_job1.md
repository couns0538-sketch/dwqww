# REPORT — deepseek6, job 1 (the 35 tuner settings, each moved by its own step under S14)

for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_job1/` · job clock from the first stamp
`Mon Nov 16 04:20:48 PM UTC 2026` in `stamps.txt`

## 1. Three lines

**Asked:** for each of the 35 settings the tuner moves, do the searches at value−c and value+c differ from S14 at all (Step 0, controls, Part 0, Parts 1–3)?
**Answer:** Step 0 met (four pins, O 9,500,069 with 41,311/24,872/28,574, G 18,466,239); **all three controls reproduced their known answers exactly, including the first three rows of the 100 run**; Part 0 met (release depth 10 = sanitizer depth 10, 200/200 both ways, so the sign flip was DEPTH, not build). Part 1/2: **the settings whose two runs equal S14 in nodes on ALL positions: on O exactly 3, on G the same 3, on both the same 3 — `QsSeeMargin`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth`. 64 of 70 runs differ on O; 64 of 70 on G.** Part 3: all three inert settings are STILL exact identities at +4c.
**How sure:** certain — every cell is a committed rows file with its `.meta`, compared by one committed command (`cmp2.py`); and my prediction (exactly these three, count 3) was MET.

## 2. Honesty numbers (raw files in this folder)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

Engine: `/agent/repos/work/build-base/forge`, sha256 `e06310eca3368556…` (the plain build of 6b98f217), except
Part 0 which uses the NodeLiterals release build `/agent/repos/work/build-l5a/forge`.

**A note the job reader must have:** another agent pushed a completed job-1 report onto this same branch while I
was running (commit `092080d97`, signed `glm-5p3-flash`). I rebased onto it rather than overwrite it; both runs
exist under different file names. Our numbers agree where they overlap (see section 5.1). My files are the
`*_base.rows`, `runs/`, `table_*.txt`, `C_qsm*.rows`, `P0_*`, `P3_*`; theirs are `O_S14.rows`, `p1_*`, `p2_*`,
`ctl_*`, `part0_*`. I did not delete any of theirs.

## 3. Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Step 0: honesty + S14 base rows | done | `honesty_*.txt`, `O_S14_base.rows`, `G_S14_base.rows` | four pins met; O **9,500,069** (41,311/24,872/28,574), G **18,466,239** |
| controls: `QsSeeMargin` 0, 99, 100 | done | `C_qsm0.rows`, `C_qsm99.rows`, `C_qsm100.rows` | 0 and 99: **nodes 200/200, bestmove 200/200**, sum 9,500,069. 100: **nodes 1/200, bestmove 173/200**, sum **9,768,507**, first three **41,356 / 23,935 / 28,720** — every known answer exact |
| Part 0: NodeLiterals release at depth 10, default and `NullStaticSlope=48` | done | `P0_nodef_d10.rows`, `P0_nss48_d10.rows` | **3,809,466** and **3,640,772**; vs my sanitizer rows **200 of 200 nodes AND bestmove equal both ways** |
| Part 1: 70 runs on O | done | `runs/O_*.rows` (70), `table_O.txt` | 32 of 35 settings differ (64 of 70 runs) |
| Part 2: 70 runs on G | done | `runs/G_*.rows` (70), `table_G.txt` | 32 of 35 settings differ (64 of 70 runs) |
| Part 3: +4c for the settings inert on both sets | done | `P3_QsSeeMargin_64.rows`, `P3_CaptureFutilityMultiplier_350.rows`, `P3_CaptureFutilityDepth_10.rows` | all three **9,500,069, nodes 200/200, bestmove 200/200** |
| prediction, own commit, before any measuring | done | `PREDICTION.md`, commit `deepseek6 job 1 prediction` | predicted exactly these 3, count 3, kill-range "fewer than 2 or more than 4" — **met** |

## 4. The table

One row per setting. "nodes-eq" is the count of positions whose NODES field equals S14's, from `cmp2.py`; the
bestmove counts are in the last two columns. Every cell comes from
`runs/O_<setting>_<value>.rows` and `runs/G_<setting>_<value>.rows` (each with a `.meta` naming the exe, its
sha256, `id name`, and every option line sent).

### On O (200 positions, S14 base sum 9,500,069)

| setting | value | c | -c | O -c sum | nodes-eq | bm-eq | +c | O +c sum | nodes-eq | bm-eq |
|---|---|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | 93 | 8 | 85 | 10,081,111 | 0 | 145 | 101 | 9,314,278 | 0 | 151 |
| LmrQuietDivisor | 205 | 12 | 193 | 9,035,329 | 0 | 148 | 217 | 10,708,626 | 0 | 150 |
| LmrNoisyBase | 13 | 6 | 7 | 9,627,099 | 39 | 191 | 19 | 9,615,327 | 53 | 194 |
| LmrNoisyDivisor | 333 | 20 | 313 | 9,671,551 | 41 | 194 | 353 | 9,519,342 | 1 | 184 |
| NullMoveBase | 5 | 1 | 4 | 9,912,856 | 0 | 162 | 6 | 9,906,893 | 0 | 179 |
| NullMoveDepthDivisor | 3 | 1 | 2 | 9,820,878 | 0 | 176 | 4 | 9,713,417 | 0 | 173 |
| NullMoveEvalDivisor | 200 | 20 | 180 | 9,527,676 | 131 | 200 | 220 | 9,537,690 | 144 | 200 |
| RfpDepth | 8 | 1 | 7 | 9,507,038 | 79 | 200 | 9 | 9,502,499 | 140 | 200 |
| RfpMargin | 72 | 6 | 66 | 9,390,679 | 0 | 139 | 78 | 9,872,233 | 0 | 154 |
| RfpImproving | 40 | 6 | 34 | 9,894,461 | 0 | 143 | 46 | 9,180,404 | 0 | 154 |
| RazorBase | 150 | 20 | 130 | 9,534,804 | 38 | 189 | 170 | 9,479,323 | 54 | 195 |
| RazorMultiplier | 350 | 25 | 325 | 9,433,562 | 19 | 181 | 375 | 9,461,510 | 44 | 195 |
| FutilityDepth | 7 | 1 | 6 | 9,439,695 | 133 | 200 | 8 | 9,496,927 | 164 | 199 |
| FutilityBase | 100 | 12 | 88 | 9,507,227 | 1 | 195 | 112 | 9,434,509 | 1 | 190 |
| FutilityMultiplier | 110 | 10 | 100 | 9,537,156 | 1 | 194 | 120 | 9,508,597 | 1 | 190 |
| LmpBase | 8 | 1 | 7 | 9,523,884 | 0 | 144 | 9 | 9,828,280 | 0 | 150 |
| HistoryPruneMultiplier | 2220 | 200 | 2020 | 9,530,219 | 35 | 192 | 2420 | 9,579,620 | 45 | 191 |
| SeeQuietMultiplier | 24 | 3 | 21 | 9,421,151 | 0 | 164 | 27 | 9,224,685 | 0 | 155 |
| SeeNoisyMultiplier | 150 | 12 | 138 | 9,556,070 | 1 | 178 | 162 | 9,517,963 | 13 | 196 |
| SingularDepth | 6 | 1 | 5 | 9,732,613 | 0 | 144 | 7 | 9,163,603 | 0 | 146 |
| SingularMargin | 2 | 1 | 1 | 13,196,949 | 0 | 148 | 3 | 8,186,451 | 0 | 153 |
| IirDepth | 2 | 1 | 1 | 10,189,982 | 0 | 147 | 3 | 10,450,178 | 0 | 141 |
| ProbcutDepth | 5 | 1 | 4 | 9,837,966 | 0 | 167 | 6 | 9,578,147 | 0 | 169 |
| ProbcutMargin | 180 | 15 | 165 | 9,295,556 | 2 | 191 | 195 | 9,472,152 | 5 | 188 |
| QsFutilityMargin | 160 | 14 | 146 | 9,647,884 | 0 | 160 | 174 | 9,582,390 | 0 | 159 |
| QsSeeMargin** | 40 | 6 | 34 | 9,500,069 | 200 | 200 | 46 | 9,500,069 | 200 | 200 |
| AspirationDelta | 18 | 2 | 16 | 9,636,048 | 0 | 151 | 20 | 9,678,831 | 0 | 144 |
| HistoryBonusQuadratic | 24 | 3 | 21 | 9,358,128 | 0 | 154 | 27 | 9,502,882 | 0 | 165 |
| HistoryBonusLinear | 54 | 6 | 48 | 9,674,952 | 0 | 150 | 60 | 9,525,119 | 0 | 152 |
| HistoryBonusMax | 2212 | 180 | 2032 | 9,522,214 | 10 | 182 | 2392 | 9,745,469 | 13 | 178 |
| LmrHistoryDivisor | 5643 | 500 | 5143 | 9,632,276 | 0 | 158 | 6143 | 9,746,633 | 0 | 154 |
| LmrCutoffThreshold | 3 | 1 | 2 | 9,208,581 | 0 | 146 | 4 | 10,344,054 | 0 | 146 |
| MaterialCorrectionWeight | 100 | 10 | 90 | 9,702,725 | 0 | 153 | 110 | 9,635,865 | 0 | 157 |
| CaptureFutilityMultiplier** | 250 | 25 | 225 | 9,500,069 | 200 | 200 | 275 | 9,500,069 | 200 | 200 |
| CaptureFutilityDepth** | 6 | 1 | 5 | 9,500,069 | 200 | 200 | 7 | 9,500,069 | 200 | 200 |

settings equal at both ends on O: 3

### On G (353 positions, S14 base sum 18,466,239)

Same 35 rows, generated by the same command. The three settings that are inert on O are inert here
too (**353 of 353** nodes and best moves at both ends), and 32 of 35 differ.

| setting | value | c | -c | G -c sum | nodes-eq | bm-eq | +c | G +c sum | nodes-eq | bm-eq |
|---|---|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | 93 | 8 | 85 | 19,725,735 | 1 | 267 | 101 | 17,427,644 | 1 | 268 |
| LmrQuietDivisor | 205 | 12 | 193 | 17,160,467 | 0 | 278 | 217 | 19,450,187 | 1 | 262 |
| LmrNoisyBase | 13 | 6 | 7 | 18,362,777 | 72 | 337 | 19 | 18,614,238 | 60 | 338 |
| LmrNoisyDivisor | 333 | 20 | 313 | 18,063,353 | 55 | 334 | 353 | 18,121,025 | 59 | 319 |
| NullMoveBase | 5 | 1 | 4 | 19,045,006 | 11 | 294 | 6 | 18,414,218 | 17 | 304 |
| NullMoveDepthDivisor | 3 | 1 | 2 | 18,494,286 | 17 | 298 | 4 | 19,364,553 | 11 | 288 |
| NullMoveEvalDivisor | 200 | 20 | 180 | 18,391,225 | 152 | 351 | 220 | 18,322,842 | 157 | 350 |
| RfpDepth | 8 | 1 | 7 | 18,510,893 | 20 | 331 | 9 | 18,218,066 | 62 | 338 |
| RfpMargin | 72 | 6 | 66 | 18,034,478 | 5 | 264 | 78 | 19,511,712 | 4 | 259 |
| RfpImproving | 40 | 6 | 34 | 18,843,404 | 4 | 261 | 46 | 18,508,937 | 5 | 275 |
| RazorBase | 150 | 20 | 130 | 18,613,571 | 13 | 315 | 170 | 18,062,059 | 19 | 330 |
| RazorMultiplier | 350 | 25 | 325 | 18,439,788 | 11 | 307 | 375 | 18,166,031 | 13 | 325 |
| FutilityDepth | 7 | 1 | 6 | 18,334,639 | 147 | 345 | 8 | 18,400,644 | 188 | 348 |
| FutilityBase | 100 | 12 | 88 | 18,504,425 | 16 | 333 | 112 | 18,176,944 | 21 | 332 |
| FutilityMultiplier | 110 | 10 | 100 | 18,622,251 | 16 | 331 | 120 | 18,277,647 | 21 | 326 |
| LmpBase | 8 | 1 | 7 | 17,952,112 | 2 | 254 | 9 | 18,525,529 | 2 | 270 |
| HistoryPruneMultiplier | 2220 | 200 | 2020 | 18,303,533 | 55 | 326 | 2420 | 18,176,819 | 65 | 324 |
| SeeQuietMultiplier | 24 | 3 | 21 | 18,477,370 | 80 | 307 | 27 | 19,337,299 | 26 | 277 |
| SeeNoisyMultiplier | 150 | 12 | 138 | 17,734,587 | 30 | 302 | 162 | 18,262,025 | 194 | 346 |
| SingularDepth | 6 | 1 | 5 | 21,159,646 | 4 | 276 | 7 | 16,788,624 | 4 | 266 |
| SingularMargin | 2 | 1 | 1 | 21,442,517 | 6 | 269 | 3 | 16,091,515 | 6 | 274 |
| IirDepth | 2 | 1 | 1 | 18,543,479 | 1 | 261 | 3 | 19,499,403 | 2 | 268 |
| ProbcutDepth | 5 | 1 | 4 | 18,055,158 | 6 | 284 | 6 | 18,493,307 | 8 | 290 |
| ProbcutMargin | 180 | 15 | 165 | 18,314,055 | 19 | 302 | 195 | 18,432,463 | 19 | 314 |
| QsFutilityMargin | 160 | 14 | 146 | 18,835,039 | 23 | 285 | 174 | 18,325,198 | 23 | 288 |
| QsSeeMargin** | 40 | 6 | 34 | 18,466,239 | 353 | 353 | 46 | 18,466,239 | 353 | 353 |
| AspirationDelta | 18 | 2 | 16 | 18,630,084 | 7 | 273 | 20 | 18,552,538 | 7 | 267 |
| HistoryBonusQuadratic | 24 | 3 | 21 | 18,088,051 | 5 | 267 | 27 | 18,530,826 | 2 | 264 |
| HistoryBonusLinear | 54 | 6 | 48 | 18,500,349 | 5 | 276 | 60 | 18,481,629 | 3 | 274 |
| HistoryBonusMax | 2212 | 180 | 2032 | 18,155,655 | 21 | 304 | 2392 | 18,133,398 | 15 | 310 |
| LmrHistoryDivisor | 5643 | 500 | 5143 | 18,469,150 | 4 | 280 | 6143 | 18,080,730 | 6 | 287 |
| LmrCutoffThreshold | 3 | 1 | 2 | 17,310,733 | 1 | 281 | 4 | 19,288,590 | 1 | 266 |
| MaterialCorrectionWeight | 100 | 10 | 90 | 18,329,033 | 8 | 279 | 110 | 18,492,683 | 6 | 283 |
| CaptureFutilityMultiplier** | 250 | 25 | 225 | 18,466,239 | 353 | 353 | 275 | 18,466,239 | 353 | 353 |
| CaptureFutilityDepth** | 6 | 1 | 5 | 18,466,239 | 353 | 353 | 7 | 18,466,239 | 353 | 353 |

settings equal at both ends on G: 3

## 5. Findings

### 5.1 Part 0 answers the claim: the sign flip was DEPTH, not BUILD

```
cd forge-combo29/tests_deepseek6_job1
python3 sumrows.py P0_nodef_d10.rows    -> rows 200 sum 3809466
python3 sumrows.py P0_nss48_d10.rows    -> rows 200 sum 3640772
python3 cmp2.py ../tests_deepseek6_long8/runs/NodeLiterals_O_def.rows   P0_nodef_d10.rows
   -> nodes-equal 200 of 200, bestmove-equal 200 of 200
python3 cmp2.py ../tests_deepseek6_long8/runs/NodeLiterals_O_nss48.rows P0_nss48_d10.rows
   -> nodes-equal 200 of 200, bestmove-equal 200 of 200
```
**One sentence, as asked: the build does not change the tree — a release depth-10 search and an ASan+UBSan
depth-10 search are bit-identical row for row on all 200 positions, twice — so the `NullStaticSlope=48` sign
flip is a matter of DEPTH, and from now on I write "depth", not "depth or build".**

### 5.2 Exactly three settings are invisible to the tuner, on both sets, at both ends and four steps away

```
python3 cmp2.py O_S14_base.rows P3_CaptureFutilityDepth_10.rows
   -> nodes-equal 200 of 200, bestmove-equal 200 of 200
```
`QsSeeMargin` (34/46/64), `CaptureFutilityMultiplier` (225/275/350) and `CaptureFutilityDepth` (5/7/10) are
exact identities of S14 on all 200 positions of O and all 353 of G. Two mechanisms, both visible in the source:

- `QsSeeMargin`: `board.cpp:24` `SeeValue{0, 100, 300, 300, 500, 900, 0}` — every SEE result is a multiple of
  100, so any margin in 0..99 is the same comparison. My controls at 0 and 99 confirming equality and 100
  differing is the direct demonstration, with the job's own known answers.
- `CaptureFutilityMultiplier` / `CaptureFutilityDepth`: the block at `search.cpp:1893` runs only when
  `CaptureFutilityBase > 0`, and that option is **not** in S14, so it holds its default **0** (verified in the
  plain build's own `uci` output, `cap_uci.txt`) and the block never executes.

**This is the job's question answered: for these three settings the tuner reads pure noise, at every step size I
tested.**

### 5.3 `SingularMargin` is the most sensitive setting per step, by a wide margin

±1 around its value of 2 moves the O tree from 9,500,069 to **13,196,949** (+38.9 %) or **8,186,451** (−13.8 %),
and the G tree by ±16 %. No other one-step move comes within a third of it (next: `LmrQuietDivisor` ±12.7 %, then
`IirDepth` ±10.0 % on O; `SingularDepth` ±14.6 % on G). A tuner step of 1 on a setting whose whole range is 0..10
is a very coarse probe; whether that is good or bad for tuning is a question for the tuner's design, not for me.

### 5.4 Six runs change the node count but not one best move on O

`NullMoveEvalDivisor` (both ends), `RfpDepth` (both ends), `FutilityDepth` −c, and the three inert settings.
The first three are the interesting kind: the tree changes size, but at 12 plies the chosen move is the same on
all 200 positions. `FutilityDepth` +c is the only setting in the whole job that changed exactly ONE best move
(199/200) while its nodes changed almost everywhere.

### Suspicions, not proven

- That `QsSeeMargin` is inert up to exactly 99 and live at 100. I measured 0, 34, 46, 64, 99, 100; the boundary
  is bracketed between 99 and 100, and the `SeeValue` lattice explains why, but I did not test 98 or 100.5-style
  middle values.
- That `CaptureFutilityMultiplier`/`Depth` are inert at EVERY base value > 0 too. I only know the base is 0 here;
  if the tuner ever moves `CaptureFutilityBase` off 0 these two come alive, and the job's table does not move it.

## 6. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`, job-10 block): the `QsSeeMargin` control and the `CaptureFutilityBase` gate are
  both its findings, passed to me through Opus's job file. Both are confirmed on my tree by measurement.
- **glmflash5** (`NOTES_glmflash5.md`, cross 2): 353 of 353 equal to kimi5's rows for S14 (18,466,239) and for
  S14+`NullStaticSlope 48` (16,773,579 on its build). My long-8-addendum G figure for the same setting was
  6,400,760 at **depth 10**; its 16,773,579 is a depth-12 number, so the two are not in conflict.
- **deepseek5** (`NOTES_deepseek5.md`): nothing bearing on job 1.
- **A live conflict I must report:** another session pushed a completed job-1 report (`092080d97`, signed
  `glm-5p3-flash`) onto MY branch while I was running the same job. I did not overwrite it; I rebased my work on
  top and kept both. Where our tables overlap they agree exactly, e.g. `SingularMargin` −c/+c =
  13,196,949 / 8,186,451 with nodes-eq 0/0 and bm-eq 148/153 in both. Two independent runs of the same 140
  searches landing on the same 140 sums is the strongest agreement in this report, but it is also a duplicate
  job and the owner should know it happened.

## 7. What I did NOT do

- I did not rerun Part 0's sanitizer side; I compared against the rows already committed from long 8 (the job
  says "your sanitizer build gave 3,809,466 and 3,640,772", i.e. use them).
- I did not test the three inert settings at values beyond +4c, or between 99 and 100 for `QsSeeMargin`.
- I did not test any setting on G at a depth other than 12.
- I did not delete or rewrite the other agent's job-1 files on this branch.
- I did not commit engine source and I did not open a pull request.

## 8. What I am NOT sure about

- Whether the duplicate run (mine and `glm-5p3-flash`'s) should have been avoided by checking the branch before
  starting. The job file appeared at 04:20 and the other report was committed at 04:44; I had by then run 140
  searches. I did not look at the remote branch between those moments, which is the mistake.
- The exact `QsSeeMargin` boundary (5.3).

## 9. A better way

The 70-run sweep is dominated by the HARNESS: each run is 200 fresh processes at 12 plies. Two settings' worth of
that time would have found the three inert settings if I had started from the source gates (the `SeeValue`
lattice and the `CaptureFutilityBase > 0` guard) and tested only the settings whose code path can execute. The
measurement is the proof; the source is the map. For the NEXT sweep, read each setting's guard first and put the
guarded ones at the front — they are the ones likely to be dead, and the tuner most needs to know about them.

## 9a. A correction I made to this report before committing it

My first draft of the O table was typed from memory of the log, and 17 of its 35 rows carried wrong numbers
(e.g. `NullMoveBase` −c as 9,912,856 when the file says the same, but `NullMoveBase` +c bm-eq as 143 when the
file says 179; `LmrNoisyDivisor` +c as 9,633,879 when the file says 9,519,342). I caught it by diffing the
typed table against `job1table.py`'s output and **replaced both tables with the generated ones**. Every number
in the tables above now comes from `python3 job1table.py O` and `python3 job1table.py G`, which read the rows
files directly, and I claim nothing that is not in those two files. This is the same fault class glmflash5
reported against itself (a table written without running the command); the fix is the same: the table must be
the output of a committed command, not a transcription.

## 10. times

see `stamps.txt`. Model: **DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

**On the `glm-5p3-flash` signature (job file 2, item 3).** That name appears in this report only where I quote the
OTHER session's commit `092080d97`, which pushed a competing job-1 report onto this branch; it is not my model
name and never was. Every report I have written — long 1 through long 8b and this one — says DeepSeek V4.1 Flash
1017, which is what my runtime gives.
