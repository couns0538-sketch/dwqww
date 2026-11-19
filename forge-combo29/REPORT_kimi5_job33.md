# kimi5 job 33 report — the history-prune test taken apart: which part decides, and was it carried in

Asked: on the job-30 split build add one counting copy that, at every reached history-prune test
(lmr_depth <= HistoryPruneDepth), recounts M / W / C1 / C2 from the same entries the engine just
read, verifies h == blend(M, W, 3) + C1 + C2, and counts which part is pivotal for each prune and
whether that part was written in this search or carried in (staleness stamps per entry of the main
and twin tables). Known answers A (rework0), B (main0), C33 (a no-twin-stamp control) first, a
prediction, then the default table at soft and hard.
Answer: at the default the prune is decided by a SHARED front with the twin dominant — pivotal W
0.8978 (soft) / 0.8311 (hard) of fired, but pivotal M 0.4352 / 0.4243 (the declared THE-TWIN bar
wants M and C each below 0.25) — and the deciding twin entries are CARRIED at both budgets (0.6694 /
0.6063 of pivotal-W prunes read a W written in an earlier search). Prediction 8 of 10 cells inside
my stated ranges (both misses survive the job's 1.5 band on the range edges).
How sure: high on the measurement — every known answer passed exactly (0 differing rows of 1,200 on
all five comparisons; fired == hp27 summed in all seven runs; h == B + C1 + C2 at all
2,401,588 + 11,728,546 + (A/B/C33) eligible tests, 0 mismatches); the pivotal/stale counts are
counters at the decision line itself.

## The job's required first lines

(1) Step 0 MET: 8 of 8 on the split build (6b98f217 + pc_r15 + history_age + count27 + age_split,
-DFORGE_MATE_ALPHA_GUARD=1, g++ 13 Release), a fresh process per line, raw files in
`tests_kimi5_job33/step0/`: none 312866 / 862329 / 3024920 / 4865609
(none_bench11/13/16.txt, none_perft5.txt), S14 242796 / 656517 (s14_bench11/13.txt),
PC20 278024 / 587276 (pc20_bench11/13.txt). exe sha256 in step0/exe.sha256 =
7a956e98cbf1b6b93c3af3e50fe63aa66f513d5e7283fc95161841ac6f810575 — BIT-IDENTICAL to job 30's split
build (its ka_all1024_soft.meta carries the same hash). setoption lines in the *_input.log files.

(2) Step 1: `tests_kimi5_job33/step1_reading.md` (committed before Step 2 in "kimi5 job 33 step 0 +
step 1 reading"). K1, K2, K3 all CONFIRMED on my chain; the matching line pairs: r15d 2235/2294 =
my chain's 2110 (h computed) / 2169 (the test), the same 59-line layout. h's parts:
M = main_history_[side][from][to] (search.hpp:395, read via quiet_history_sum search.cpp:351-360,
the FORGE_SEARCH_SPEED2=1 branch of quiet_history search.cpp:1477-1487); W = rework_entry
(search.cpp:1507-1513, the lesser-threat bits of this node); blend(M, W, 3) with
threat_quarters(2) = 3 (b4.hpp:28) and blend = (M + 3W)/4 truncated toward zero (b4.hpp:65-67);
C1/C2 = (ss-1)/(ss-2)->continuation[piece][to], 0 when null; under PC20 no 4-ply term
(ContHist4PlyRead off, search.cpp:165), no threat bonus (ThreatHistory off, search.cpp:169), no
pawn history (compiled out, FORGE_PAWN_HISTORY=0). t: search.cpp:2154-2156 = −2220·depth·3/4 =
−1665·depth (TtPruneV2 on, not improving) else −2220·depth, int arithmetic. K3's gate:
search.cpp:2122-2123 (block), 2118-2121 (sound_mate_case), 2083 (has_material), 2152/2157
(quiet, no check, not the TT move), after the futility test 2158-2167; HistoryPruneDepth = 3
(search.cpp:116, not set by pc20.opt).

(3) Known answers (`tests_kimi5_job33/ka/`, evidence summary ka33_evidence.txt):
- A (HistoryAgeRework 0 alone, counting build): rows equal job 30 s4_rework0 — 0 differing of 1,200
  soft and hard (depth/nodes/bestmove/hp27/hp27_nodes); fired summed = hp27 summed = 1,372 soft and
  50,850 hard; eligible reads of a stale nonzero W = 0 at both budgets. PASS.
- B (HistoryAgeMain 0 alone): rows equal s4_main0 — 0 of 1,200 soft and hard; fired = 5,184 and
  168,299; stale nonzero M reads = 0. PASS.
- C33 (the scratch copy whose twin updates do NOT set the twin stamp, job33/c33_nostamp_control.patch.txt,
  HistoryAgeRework 0, soft): stale nonzero W reads = 754,005 > 0 (the same run on the counting build
  gave exactly 0); fired 1,372 and every pivotal share identical to the counting build's A run — the
  control changes only the stamp reads. PASS. (One budget: the ask was "above 0".)
- The h == B + C1 + C2 check held at EVERY eligible test of every run (mismatch 0 in all 7 runs).
  Options proven to arrive: the setoption lines are quoted from the input logs in ka33_evidence.txt;
  the refusal scan of all 7 input logs finds no `unknown option` / `invalid value` / `ERROR` line.

(4) The prediction, graded cell by cell (prediction.txt unchanged since its 12:06:38Z commit, after
A/B/C33 and before Step 3). Primary grading: measured inside my stated range. The job's
[g/1.5, g·1.5] band applied to the nearest range edge is given in parentheses where it differs.
SOFT: pivM 0.4352 vs [0.35, 0.60] HIT · pivW 0.8978 vs [0.82, 0.95] HIT · pivC 0.2891 vs
[0.35, 0.60] MISS (inside the edge band: 0.35/1.5 = 0.233 ≤ 0.2891, survives) · none 0.0394 vs
[0.005, 0.04] HIT · pivW-with-stale-W 0.6694 vs [0.60, 0.85] HIT → 4/5.
HARD: pivM 0.4243 vs [0.35, 0.62] HIT · pivW 0.8311 vs [0.82, 0.97] HIT · pivC 0.3980 vs
[0.33, 0.60] HIT · none 0.0748 vs [0.005, 0.05] MISS (edge band: 0.05·1.5 = 0.075 ≥ 0.0748,
survives) · pivW-with-stale-W 0.6063 vs [0.55, 0.85] HIT → 4/5.
TOTAL 8 of 10 (10 of 10 with the 1.5 edge band). My structural guess held (twin dominant, carried
majority, none small); the two strict misses were the continuation's smallness at soft (0.289 vs my
0.35 floor) and none's growth at hard (0.0748 vs my 0.05 ceiling).

(5) Step 3 (all four HistoryAge* 1024, HistoryAgeKeep 1024; counting build; rows and counters in
`tests_kimi5_job33/s3/`, table file step3_table.txt):
KNOWN ANSWER: rows equal job 30 ka_all1024 — 0 differing of 1,200 soft and hard; fired summed =
11,633 soft and 313,423 hard, each equal to the run's hp27 sum. PASS.

| measure | soft (go softnodes 2000) | hard (go nodes 20000) |
|---|---|---|
| eligible | 2,401,588 | 11,728,546 |
| fired | 11,633 | 313,423 |
| fired per 1,000 eligible | 4.84 | 26.72 |
| pivotal M (share of fired) | 5,063 (0.4352) | 132,994 (0.4243) |
| pivotal W | 10,444 (0.8978) | 260,490 (0.8311) |
| pivotal C | 3,363 (0.2891) | 124,748 (0.3980) |
| none | 458 (0.0394) | 23,440 (0.0748) |
| fired with M < 0 | 11,098 (0.9539) | 294,516 (0.9397) |
| fired with W < 0 | 11,397 (0.9796) | 302,269 (0.9644) |
| fired with C1+C2 < 0 | 5,684 (0.4885) | 207,684 (0.6627) |
| mean M over fired | −3,164.38 | −4,878.62 |
| mean W over fired | −3,390.43 | −5,087.50 |
| mean C1+C2 over fired | −619.21 | −1,380.88 |
| fired with stale M | 7,269 (0.6249) | 172,694 (0.5510) |
| fired with stale W | 7,580 (0.6516) | 183,827 (0.5865) |
| pivotal W with stale W | 6,991 (0.6694 of pivW) | 157,938 (0.6063 of pivW) |
| pivotal M with stale M | 3,408 (0.6731 of pivM) | 82,232 (0.6183 of pivM) |
| eligible reads of a stale nonzero W | 906,656 (377.5 per 1,000 eligible) | 3,817,075 (325.5) |
| eligible reads of a stale nonzero M | 1,010,817 (420.9) | 4,026,232 (343.3) |

THE READINGS (the job's declared rule, printed for both budgets):
- WHO DECIDES, soft: pivotal W 0.8978 ≥ 0.50 but pivotal M 0.4352 and pivotal C 0.2891 are NOT each
  below 0.25 → **SHARED** (the twin is the largest part, the bar for THE TWIN is not met).
- WHO DECIDES, hard: pivotal W 0.8311 ≥ 0.50, pivotal M 0.4243, pivotal C 0.3980 → **SHARED**.
- CARRIED, soft: 0.6694 ≥ 1/2 of pivotal-W prunes read a stale W → **CARRIED**.
- CARRIED, hard: 0.6063 ≥ 1/2 → **CARRIED**.
(The same rule printed for hard: identical thresholds, applied to the hard column.)

## What this check cannot see (written into the report as it is)

The PC's net (your runs use the built-in evaluation), the PC's engine build, budgets other than
these two, more than one thread, and whether any ageing plays better: that is a match on the PC
after its tune.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Step 0, the 8 numbers | done | step0/ (8 raw files + input logs) | 8/8, build bit-identical to job 30's |
| Step 1 reading K1/K2/K3 | done | step1_reading.md (own commit before Step 2) | all confirmed, file:line |
| Step 2 the counting copy | done | job33/split_counter.patch.txt (289 lines, diff -u of two trees, -F0 roundtrip TREES-IDENTICAL) | h == B + C1 + C2 at every test, 0 mismatch in 7 runs |
| Known answer A (rework0) | done | ka/ka_rework0_{soft,hard}.*, ka/ka33_evidence.txt | 0/1,200 both budgets; fired 1,372/50,850 = hp27; stale-nzW 0 |
| Known answer B (main0) | done | ka/ka_main0_{soft,hard}.* | 0/1,200; fired 5,184/168,299; stale-nzM 0 |
| C33 control (no twin stamp) | done | ka/c33_rework0_soft.*, job33/c33_nostamp_control.patch.txt | stale-nzW 754,005 > 0; decisions identical to A |
| Prediction | done | prediction.txt (own commit, 12:06:38Z) | 8/10 strict (10/10 with the edge band) |
| Step 3 known answer | done | s3/step3_table.txt | 0/1,200 both budgets; fired 11,633/313,423 |
| Step 3 table + readings | done | s3/step3_table.txt | SHARED + CARRIED at both budgets |

## Findings (each with file:line of the source and a command that shows it again)

1. THE TWIN IS THE LARGEST SINGLE PART BUT DOES NOT DECIDE ALONE. pivotal W 0.8978 (soft) / 0.8311
   (hard) of fired, yet pivotal M 0.4352 / 0.4243 — the shares overlap (they sum to 1.62 / 1.65
   with C): for 43 % of fired prunes, zeroing M alone (blend(0, W, 3) + C1 + C2) lifts h back to t.
   The overlap is structural in h = blend(M, W, 3) + C1 + C2 with blend = (M + 3W)/4
   (src/search.cpp:2110 computes h; :2169 the test; b4.hpp:65-67 the 3:1 weights). Show again:
   `python3 agg_hp33.py s3/s3_all1024_soft.jsonl` (the shares line).
2. THE DECIDING ENTRIES ARE CARRIED, AND MORE SO THAN THE AVERAGE ENTRY. Fired tests read a stale W
   in 0.6516 (soft) / 0.5865 (hard) of cases and a stale M in 0.6249 / 0.5510, while over ALL
   eligible tests a stale nonzero W is read only 377.5 / 325.5 per 1,000 (stale nzM 420.9 / 343.3).
   The entries that decide prunes are roughly 1.7× more often carried-in than the average tested
   entry. This is the counting-level mechanism behind job 27's collapse (ageing to 7/8 per search
   removed 86 % / 80 % of HP): ageing can only change what was carried in, and the deciding entries
   mostly are. Stamps: set at every history update of the entry (the 8 write sites listed in
   split_counter.patch.txt: update_quiet_stats 2, update_rework_history 2, TtCutoffHistory,
   EvalSwing, the PV-bonus pair), never by the search-start ageing (search.cpp:2512-2520 in the
   split tree); the search number increments once per search next to hp27_taken_ = 0.
3. THE TWIN'S ENTRIES ARE BOTH MORE OFTEN NEGATIVE AND MORE NEGATIVE. Over fired tests W < 0 in
   0.9796 / 0.9644 (M: 0.9539 / 0.9397), mean W −3,390 / −5,088 vs mean M −3,164 / −4,879 (C1+C2
   mean −619 / −1,381, negative in only 0.4885 / 0.6627). With the 3:1 blend weight this explains
   the twin's pivotal lead without any appeal to update volumes.
4. NONE IS SMALL BUT REAL, AND GROWS WITH BUDGET: 0.0394 soft → 0.0748 hard of fired prunes still
   fire with any one of the three parts zeroed (over-determined prunes). My prediction under-called
   the hard value (0.05 ceiling). The class exists because t scales with depth
   (search.cpp:2154-2156) while the parts' magnitudes saturate near HistoryLimit (b4.hpp:20).
5. JOB 30'S "WHICH TABLE" ANSWER VS THIS JOB'S. Job 30's removal-effect share named the twin at
   0.7990 (soft); this job's decision-presence share names it at 0.8978. The two formulas measure
   different things (what ageing removes vs what un-fires the test); both put the twin first, and
   this job adds the missing piece job 30 could not see: M is pivotal too often (0.44) for the
   prune to be the twin's alone. The declared reading lands SHARED, not THE TWIN.

Suspicions, not proven:
- Continuation entries decide rarely partly because they are re-written inside the search more
  often than main/twin entries (update_continuation fires at every quiet cutoff, search.cpp:1607,
  1616, 1883, 2388). The counter has no C stamps (the job scoped stamps to main + twin), so this
  is plausible, not measured.
- The none-class's growth soft→hard (0.039 → 0.075) may be depth-scaling of t against saturated
  entries; two budgets cannot prove the mechanism.

## From my colleagues

- deepseek5 (branch tip 731fc808): read NOTES_deepseek5.md tail and REPORT_deepseek5_job30. Their
  corrected stage rates (CounterMove 298-302 per 1,000 worse than Killer2 170-206) and the
  HistExempt patch target glmflash5's chain, not this job. What I APPLIED: their "read the state
  variable at the moment the event happens" rule — this job's counter reads M/W/C1/C2 at the test
  line itself (search.cpp:2169), and the stamps at the write sites, never reconstructed after.
  Their one-late stage bug (two jobs mislabeled) is exactly the failure mode that rule avoids.
- glmflash5: the branch for-fable-and-opus/glmflash5-work does not exist (fetch: "couldn't find
  remote ref") — fourth run noting this. Nothing to read.
- sol (data): games.txt (job3, first 20 games) from sol-work cc0951ac, the same file job 27/30 used.

## What I did NOT do

- No match, no strength measurement, no PC net, no multi-thread (all runs Threads 1, Hash 16,
  pc20-derived option files; parallel processes used: 1, sequential).
- C33 ran at soft only (the ask was "above 0"; fired there equals the counting build's 1,372 exactly).
- No stamps for the continuation tables (the job scoped staleness to the main table and the twin).
- No reruns of job 30's rows; they were used as committed read-only references.

## What I am NOT sure about

- Whether "reached with lmr_depth <= HistoryPruneDepth" should count tests in excluded-move
  (singular-extension) searches: the hook counts them (they pass through the same line); they are a
  tiny minority of nodes and the h-check held there too. If Opus wants them excluded, one more
  counter field splits them out.
- The 1.5-band grading of range-valued predictions is my reading of the job's rule for point
  guesses; the strict inside-the-range grading (8/10) is the primary one reported.

## A better way

The three "without" tests zero ONE part at a time, so doubly-pivotal prunes (M and W each pivotal)
are invisible in the marginals (the shares sum to 1.62, but the joint count is not derivable from
them). Three more int tests per fired prune — the pairwise removals noMW = C1 + C2 < t,
noMC = blend(0, W, 3) < t, noWC = blend(M, 0, 3) < t — would give a full attribution of each prune
at trivial cost (three int blends per fired test). Check that it is better: with the pairwise
counts, the doubly-pivotal population is measured directly (a prune pivotal for both M and W has
noM false, noW false, noMW true), where today it is only bounded by the sum of marginals; and the
none class must equal "all three pairwise removals still fire", a built-in cross-check. A second,
cheaper improvement: one more stamp array over ContinuationHistory (2.7 MB per worker) would test
suspicion 1 with the same machinery.

## Times

See tests_kimi5_job33/stamps.txt (start of the run first; every line names its source).

## Model

Kimi K3 (the runtime's model name), run name kimi5.

## Final command output (git status --short + ls -R of the job folder, run before the report commit)

See the commit's sibling file tests_kimi5_job33/final_ls.txt.
