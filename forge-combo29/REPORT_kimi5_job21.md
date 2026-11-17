# kimi5 job 21 report — A4 (d): LmrCaptureHistDiv (capture history in the reduction of a capture) on the PC build

(1) **Step 0: MET** — all eight numbers exact on the LmrD build with every new option at its
default, and the `uci` list shows `LmrCaptureHistDiv` with the job's range next to job 20's two
names. (2) **Prediction graded row by row** (file `tests_kimi5_job21/prediction.txt`, own commit
"kimi5 job 21 prediction" at 18:06:12Z before the first Step 1 run at 18:06:19Z, never edited):

| row | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1 lmr2048/base nodes, G, d14 | 0.970 | [0.945, 0.995] | 1.0314 | **KILLED** (it shrank G −0.8 % at d12, GREW it +3.1 % at d14) |
| P2 share of eligible captures with t != 0, base, G, d12 | 0.35 | [0.20, 0.50] | 0.4030 | survives |
| P3 above-alpha per 1,000 at t = −2, base, G, d12 | 70 | [40, 110] | 18.1 | **KILLED** (far lower) |
| P4 above-alpha per 1,000 at t = +2, base, G, d12 | 170 | [110, 250] | 42.7 | **KILLED** (far lower) |

(3) **Step 1: every known answer met** (sums and first-three below; per-position checker
`check_s1.py`, output `check_s1.txt`): base 8,315,168 / 17,611,204; lmr2048 8,381,569 /
17,463,984; lmr8192 8,528,011 / 17,771,770; cap4 8,552,076 / 17,070,198 — each with its exact
first-three rows, on O (200) and G (353). Identities: LmrCaptureHistDiv SENT at 0 equals base on
**200 of 200 O and 353 of 353 G** (nodes AND best move); job 20's three options at the all3
values equal my job-20 all3 rows on **200 of 200 O and 353 of 353 G**. Positions whose node
count changes vs base: lmr2048 198/200 O, 330/353 G; lmr8192 167/200 O, 296/353 G; cap4
200/200 O, 339/353 G (all well over half). One harness fault of mine ran three settings at
default (non-PC20) options first; caught by the lmr0 sum not being base's known sum, fixed,
rerun — details in "What I am NOT sure about".
(4) Step 2 table below. (5) Step 3 tables below, 200 (O) and 353 (G) searches summed per run.
(6) **Step 4: skipped (done in job 20).**

Three plain lines: I was asked to port the research answer's A4(d) — in the late-move reduction,
when an option is on and the move is a capture, lower r by the clamped capture-history quotient —
onto the PC build on top of job 20's patch, prove the port against Opus's own rows, scale it in
depth, and count what the term does inside the reduction. The port is proven the same code as
theirs (every given known answer exact, plus both identities per position), and the counting
build is proven observe-only position by position. How sure: identities exact on all given
answers; three of four predictions died (the depth-14 direction of the node change, and the
level — not the ORDER — of the above-alpha rates).

## Step 0 (raw files in `tests_kimi5_job21/step0/`; a fresh process per line)

Base: 6b98f217 + `pc_r15.patch` (sha256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`,
re-extracted from swarm file 5 lines 56–2374 and re-verified) + job 20's
`CaptureA4.pc.patch.txt` + this job's `CaptureLmrD.pc.patch.txt`; g++ (Release,
`-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, `-DCMAKE_CXX_COMPILER=g++`), AVX-512+BMI2
machine (no FORGE_PORTABLE). LmrD exe sha256
`669fa824d6dd8dc724604aebcc6c1ca170ccf1ec36351f16285781a0c7426411` (`step0/exe.sha256`),
`id name Chess Engine Forge 6.4.24 candidate`, exe `ls -l` stamp 18:05:54.842194671.

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | file |
|---|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ | `step0/none_*.txt` |
| S14 | 242796 ✓ | 656517 ✓ | – | – | `step0/s14_*.txt` |
| PC20 | 278024 ✓ | 587276 ✓ | – | – | `step0/pc20_*.txt` |

`step0/uci_list.txt`: `option name LmrCaptureHistDiv type spin default 0 min 0 max 16384`,
`option name SeeNoisyHistDiv type spin default 0 min 0 max 1024`,
`option name GoodCaptureHistDiv type spin default 0 min 0 max 1024`. Every `setoption` line in
`step0/*_input.log`. At the defaults the patched engine computes exactly today's numbers.

## The port (`CaptureLmrD.pc.patch.txt`, sha256 `87bef4655158f6709f504f57a7ba82de11a6f1765f7f85870de66a6baf890770`)

Applies with `patch -p1 -F0`, zero fuzz, on 6b98f217 + pc_r15 + CaptureA4, in that order
(verified on a fresh copy: the applied tree is byte-identical to the built one). Three hunks,
all in `src/search.cpp` (line numbers in the delivered tree, base+r15+A4+LmrD; the pre-patch
tree's numbers were 2 less below line 122 and 1 less between 122 and 207):
- `int LmrCaptureHistDiv = 0;` after `GoodCaptureHistDiv` (line 122);
- `{"LmrCaptureHistDiv", &LmrCaptureHistDiv, 0, 16384},` in the option table (line 207);
- after the job's line `if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);`
  (**line 2285** in the delivered tree, 2283 before the patch): 
  `if (tune::LmrCaptureHistDiv > 0 && capture) r -= std::clamp(history / tune::LmrCaptureHistDiv, -2, 2);`.
`capture` is the move loop's own `const bool capture = move.is_capture();` (line 2099; `quiet =
!capture && !move.is_promotion()` line 2100), so a promotion that captures counts and a
promotion onto an empty square does not. `history` (line 2103) holds
`capture_history_value(board, move)` for a capture. At 0 the term is skipped and the engine
computes exactly what it computes today (Step 0 and the lmr0 identity).
The two capture-history places the job asked for: tried non-quiet moves (captures AND
promotions onto empty squares) are recorded into `captures_tried` at **line 2355** and
`update_capture_stats` (**line 1615**) applies the bonus only `if (best.is_capture())`
(**line 1617**) while every other tried capture gets `-bonus` (the loop right after) — so a
promotion onto an empty square is recorded with the tried captures and gets their penalty, but
can never earn the bonus: its entry can only fall.

## Step 1 (rows in `rows/*_d12.json`, `.meta` beside each; checker `check_s1.py` → `check_s1.txt`)

| setting | O sum | O first three | G sum | G first three | known answer |
|---|---|---|---|---|---|
| base | 8,315,168 | 21,812 / 26,844 / 35,173 | 17,611,204 | 31,779 / 46,086 / 84,457 | ✓ exact |
| lmr2048 | 8,381,569 | 21,812 / 27,220 / 34,991 | 17,463,984 | 31,048 / 36,837 / 61,486 | ✓ exact |
| lmr8192 | 8,528,011 | 21,812 / 26,844 / 35,184 | 17,771,770 | 30,759 / 33,508 / 128,372 | ✓ exact |
| cap4 | 8,552,076 | 21,140 / 21,321 / 31,209 | 17,070,198 | 43,472 / 54,279 / 69,993 | ✓ exact |

Identities (no number of theirs): lmr0 (SENT 0) == base per position, nodes AND best move,
200/200 O and 353/353 G; all3 (job 20's three at 230/32/32) == my job-20 all3 rows per
position, 200/200 O and 353/353 G.

## Step 2 (`step2_j21.py` → `step2_table.txt`; bootstrap 95 % over positions, 2,000 resamples, seed 12)

| set | depth | setting | nodes | ratio | boot95 | bm != base |
|---|---|---|---|---|---|---|
| O | 12 | base | 8,315,168 | 1.0000 | – | 0 |
| O | 12 | lmr2048 | 8,381,569 | 1.0080 | [0.9659, 1.0449] | 30 |
| O | 12 | lmr8192 | 8,528,011 | 1.0256 | [0.9970, 1.0509] | 19 |
| O | 12 | cap4 | 8,552,076 | 1.0285 | [0.9765, 1.0772] | 54 |
| O | 14 | base | 19,377,109 | 1.0000 | – | 0 |
| O | 14 | lmr2048 | 19,178,796 | 0.9898 | [0.9468, 1.0272] | 29 |
| O | 14 | lmr8192 | 19,200,599 | 0.9909 | [0.9506, 1.0244] | 29 |
| O | 14 | cap4 | 20,849,511 | 1.0760 | [1.0155, 1.1259] | 37 |
| G | 12 | base | 17,611,204 | 1.0000 | – | 0 |
| G | 12 | lmr2048 | 17,463,984 | 0.9916 | [0.9553, 1.0239] | 52 |
| G | 12 | lmr8192 | 17,771,770 | 1.0091 | [0.9789, 1.0346] | 35 |
| G | 12 | cap4 | 17,070,198 | 0.9693 | [0.9270, 1.0058] | 85 |
| G | 14 | base | 41,052,503 | 1.0000 | – | 0 |
| G | 14 | lmr2048 | 42,342,046 | 1.0314 | [0.9813, 1.0750] | 74 |
| G | 14 | lmr8192 | 44,000,826 | 1.0718 | [1.0262, 1.1144] | 50 |
| G | 14 | cap4 | 43,180,993 | 1.0518 | [0.9799, 1.1145] | 77 |

The depth-14 sums differ from the depth-12 sums (right files). lmr2048 flips sign with depth on
BOTH sets, in opposite directions: O 1.0080 → 0.9898, G 0.9916 → 1.0314. lmr8192 grows both
sets at both depths and the most at d14 on G (+7.2 %, one-sided).

## Step 3 (`CaptureLmrDCount.pc.patch.txt`, FORGE_LMRD_CHECK=1 build; totals `sum_lmrd.py` → `step3_table.txt`)

Arm on ELIGIBILITY: every capture entering the LMR block is counted whatever the option's
value, with t = clamp(history/2048, −2, 2) computed at D = 2048 itself (observe-only). Counters
per t class: moves / reduced search's score above alpha / re-searches run / re-searches then
failing alpha / same reduced depth despite t != 0. Known answers: **the counting build equals
the plain build per position on 553 of 553 at both settings** (nodes AND best move, O and G;
the sums are Step 1's). Classes add up: moves sum = eligible captures on every run;
above >= research >= refail per class. Under base the t classes describe what the option WOULD
change: moves with t != 0 are the first-visit reductions whose r changes (O 99,642, G 256,103),
and the same-depth ones are counted apart (O 51,307, G 115,598).

**Base** (200 O and 353 G searches summed; rates = above-alpha per 1,000 moves of the class):

| set | quiet in block | eligible caps | t=−2 m,above,res,refail,sd | t=−1 | t=0 | t=+1 | t=+2 | t != 0 share |
|---|---|---|---|---|---|---|---|---|
| O | 3,131,227 | 367,321 | 7,034 / 138 (19.6) / 76 / 19 / 5,193 | 6,053 / 177 (29.2) / 86 / 18 / 4,353 | 267,679 / 5,873 (21.9) / 2,240 / 253 / 0 | 30,066 / 1,244 (41.4) / 529 / 52 / 17,527 | 56,489 / 2,089 (37.0) / 937 / 95 / 29,234 | 0.2713 |
| G | 7,210,050 | 635,442 | 27,533 / 497 (18.1) / 258 / 87 / 18,240 | 11,917 / 295 (24.8) / 161 / 41 / 7,755 | 379,339 / 9,471 (25.0) / 4,395 / 452 / 0 | 62,474 / 2,607 (41.7) / 1,351 / 150 / 30,329 | 154,179 / 6,589 (42.7) / 3,661 / 512 / 59,274 | 0.4030 |

**LmrCaptureHistDiv 2048** (same runs, option ON):

| set | quiet in block | eligible caps | t=−2 | t=−1 | t=0 | t=+1 | t=+2 | t != 0 share |
|---|---|---|---|---|---|---|---|---|
| O | 3,164,827 | 367,047 | 6,914 / 121 (17.5) / 67 / 17 / 6,413 | 5,805 / 176 (30.3) / 98 / 21 / 4,940 | 266,757 / 5,984 (22.4) / 2,285 / 258 / 0 | 31,016 / 1,363 (43.9) / 417 / 42 / 23,097 | 56,555 / 2,310 (40.8) / 301 / 37 / 46,670 | 0.2732 |
| G | 7,153,207 | 640,468 | 27,010 / 471 (17.4) / 287 / 90 / 24,218 | 12,550 / 252 (20.1) / 134 / 24 / 9,987 | 381,943 / 9,472 (24.8) / 4,390 / 429 / 0 | 65,504 / 2,670 (40.8) / 1,041 / 104 / 43,562 | 153,461 / 6,607 (43.1) / 1,188 / 181 / 120,391 | 0.4037 |

**The question the counters answer: yes, capture history predicts which reduced captures beat
alpha.** Under base on G the rate per 1,000 climbs with t: 18.1 / 24.8 / 25.0 / 41.7 / 42.7
(t = −2 … +2); on O: 19.6 / 29.2 / 21.9 / 41.4 / 37.0. The level is far lower than I guessed
(18–43 per 1,000, not 70–170) but the order is monotone on G and near-monotone on O. The two
counts the job said would differ most at t = +2 do: under base on G, 6,589 reduced searches
beat alpha at t = +2 but only 3,661 re-searches ran — 44 % of them had no reduction left
(reduced_depth == new_depth), against 8 % at t = −2 (497 vs 258). Under the option the t = +2
re-searches collapse (3,661 → 1,188 on G) exactly where same_depth rises (59,274 → 120,391):
the option removes their reduction, so their reduced search IS the full-depth search.

## Step 4

Skipped (done in job 20: T1 equals job 11's rows on 200/200 O and 341/341 G of the a0 mask,
C1 on 200/200 O — see REPORT_kimi5_job20.md).

## From my colleagues

Read this run (both stopped by the owner this morning, per file 21): glmflash5 =
`cursor/glmflash5-work-cb5c` (notes tail + REPORT_glmflash5_job27 head): the check-extension
ladder's 20,000-node pools are all level, the 2,000-node capped variants gain; the fastchess
TT-pollution question for fixed-node matches is open (not applicable here: my runs are
single-process fixed-depth searches, one engine per run, `ucinewgame` before every search).
deepseek6 = `for-fable-and-opus/deepseek6-work` (notes tail + REPORT_deepseek6_long78 head):
bench goes over stdin (my step0 already drives it that way, a fresh process per line); G
position 193's depth-12 defect is a known answer of the owner's exe — my job-17 note says r15
repairs it, and my G rows equal Opus's rows including position 193, so no conflict; the
plant-rule lessons (a checker proves itself on a planted fault) are satisfied here by the
identity rows (lmr0 vs base 553/553) and the counting build's per-position equality.
Applied: none of their measured numbers; the harness and the PC recipe come from my own job
20's folder.

## What I did NOT do

- Step 4 (done in job 20, skipped per the job file).
- No cap4 counter run (Step 3 asks for base and lmr2048 only).
- No matches, no Elo (not asked).
- The wrong-options first pass of Step 1 left no raw files: the runner refuses to overwrite, so
  I deleted those six outputs before the rerun (their DONE lines are quoted below). Kept
  nothing else back.

## What I am NOT sure about

- My first lmr0/lmr2048/lmr8192 `.opt` files held ONLY the one new option, not the PC20 block,
  so those runs ran at default settings (DONE lines: lmr0 O 12,573,318 / G 22,545,999; lmr2048
  O 12,363,160 / G 23,284,892; lmr8192 O 12,443,112 / G 22,361,613). Caught because the lmr0
  sum was not base's known 8,315,168; the fix (prepend `pc20.opt`) gave every known answer
  exact. The bad numbers are consistent with a non-PC20 run, but I did not verify that
  independently — they are only evidence of my harness fault, nothing more.
- `same_depth` under lmr2048 answers a different counterfactual than under base (r already
  holds the term, so it tests removing the term again); only the base row is the job's
  known-answer reading. The option-ON table is descriptive.
- Whether the O-set t=+1/t=+2 rate order (41.4 vs 37.0) is noise: no resampling over searches
  was done on the rates.

## A better way

The harness fault of this run is structural: `.opt` files mix the PC20 base block and the
per-setting override by hand. Make the batch script take ONE base file plus (name, value)
pairs and compose the sent options itself, so a setting can never drop the base block; the
runner already logs every sent `setoption` line into `*_input.log`, and the `.meta` lists
them, so a composed run stays auditable. Cheaper than the fault: one bad lmr0 sum cost a
delete-and-rerun; a composed base would make that class of mistake impossible. Check: run
base-vs-base composed and plain on one set; sums must be equal.

## Suspicions, not proven

- The t = +2 class is the biggest non-zero class (154,179 of 635,442 eligible captures on G
  under base, 24 %): positive entries dominate the eligible captures. The d14 G growth under
  lmr2048 (+3.1 %) is consistent with "less reduction on the big positive class outweighs more
  reduction on the negative classes at depth", but the counters do not prove the mechanism.
- Eligible captures are ~8 % of the moves entering the block (G: 635k vs 7.2M quiets): the
  term touches a small slice, which fits the small node ratios.

## Times

times: see stamps.txt (run start 18:04:08Z; claim 18:04:32Z; build 18:05:48–18:05:54Z; step 0
18:06:00Z; prediction 18:06:12Z; step 1 18:06:19–18:07:07Z; step 2 18:07:14–18:07:59Z; count
build 18:08:41Z; step 3 18:08:45–18:08:54Z; tables 18:09:10Z; all UTC 2026-11-17).

## Model

Kimi K3 (the model name my runtime gives).

`git status --short` → `final_status.txt`; `ls -R` of the job folder → `final_ls.txt` (the last
command before the report commit).
