# kimi5 job 30 report — which of the four quiet-history tables carries job 27's effect

Asked: explain job 27's "worst ply group" column, add four per-table aging options
(HistoryAgeMain/Cont/Threat/Rework) on top of job 27's two patches, prove them on three known
answers, then measure each live table alone at 896 and at 0 over the same 1,200-search replay.
Answer: by the job's declared reading the effect is ONE TABLE: the HistRework twin
(rework_history_) — share 0.7990 at softnodes 2000 (Main 0.4695, Cont 0.3018; the shares sum to
1.57, so the tables overlap at the prune threshold); the threat table is exactly 0 (proven).
How sure: high on the measurement (every known answer 0/1,200, two surprise rows rerun and
reproduced exactly); the reading is the job's own formula, and I flag in the findings that its
shares need not sum to 1.

## The job's required first lines

(1) Step 0 MET: 8 of 8 on the base chain build (6b98f217 + pc_r15 + history_age + count27,
-DFORGE_MATE_ALPHA_GUARD=1, g++ 13.3 Release), a fresh process per line, raw files in
`tests_kimi5_job30/step0/`: none 312866 / 862329 / 3024920 / 4865609
(none_bench11/13/16.txt, none_perft5.txt), S14 242796 / 656517 (s14_bench11/13.txt),
PC20 278024 / 587276 (pc20_bench11/13.txt). exe sha256 in step0/exe.sha256; setoption lines in
the *_input.log files.

(2) Step 1: the column was made by the committed command `python3 tests_kimi5_job27/step4_totals_j27.py`
(rerun on the committed rows: `tests_kimi5_job30/step1_rerun_committed_command.txt`; it reproduces
the report's numbers exactly and exits 0, including the sol cross-check 0/1,200 on both budgets).
WHAT IT COUNTS: changed best moves bucketed by `ply = i % 60` (0-based row index; equal to the
row's own ply field on all 1,200 rows, since every game has exactly 60 searches) with boundaries
`ply < 9 / ply < 29 / else` — so the bucket LABELLED "30-59" actually counts plies 29-58 (and
"10-29" counts 9-28). Off by one at both upper bounds. THE CORRECTED COLUMN (plies 30-59 by the
ply field; `step1_plygroup_j30.py`, output `step1_plygroup.txt`): soft 242, 222, 230, 237, 254;
hard 210, 189, 193, 205, 197 — exactly the numbers Opus recomputed. The conclusion stands:
plies 30-59 are the worst group in every non-default row.

(3) Known answers (split build, comparisons on depth/nodes/bestmove/hp27/hp27_nodes against job
27's committed rows2 files; `ka_compare.txt`):
- A (all four new options 1024, HistoryAgeKeep 1024): 0 differing rows of 1,200, soft and hard;
  HP sums 11,633 / 313,423, node sums 4,294,263 / 16,349,279 — the ka2 rows exactly. PASS.
- B (all four at 896): 0 differing rows of 1,200, soft and hard; HP 1,567 / 63,861, nodes
  4,080,162 / 16,285,974 — the keep896 rows exactly. PASS.
- C (HistoryAgeThreat 896 alone): 0 differing rows of 1,200, soft and hard — the ka2 rows
  exactly. PASS (the threat history is off under PC20, so aging it is a no-op; confirmed, no
  read of a live table found — quiet_history adds threat_quiet_bonus at search.cpp:1484 but the
  table stays all-zero with tune::ThreatHistory false).
Every run's options proven to arrive: the `setoption name HistoryAge* value *` lines are quoted
from the *_input.log files in the report body's evidence list; no `unknown option` /
`invalid value` / `ERROR` line appears in any input log (scan in the body).

(4) The prediction, graded row by row (a cell survives when the measured value falls inside my
stated range; prediction.txt unchanged since its commit):
ratios (soft/hard measured vs my range): main896 0.5970/0.6836 vs [0.65,0.95]/[0.70,0.97]
MISS/MISS; cont896 0.7410/0.8516 vs [0.40,0.85]/[0.45,0.90] HIT/HIT; rework896 0.3143/0.3732 vs
[0.70,1.00]/[0.75,1.00] MISS/MISS; main0 0.4768/0.5361 vs [0.45,0.90]/[0.50,0.92] HIT/HIT;
cont0 0.8089/1.0028 vs [0.30,0.75]/[0.35,0.80] MISS/MISS; rework0 0.1243/0.1617 vs
[0.60,0.95]/[0.65,0.97] MISS/MISS → 4 of 12 survive.
best moves changed (soft/hard): main896 474/399 MISS/MISS; cont896 446/379 MISS/MISS; rework896
447/368 MISS/MISS; main0 465/378 MISS/HIT; cont0 457/391 HIT/HIT; rework0 482/397 MISS/MISS
→ 3 of 12 survive. Total 7 of 24. My structural guess was wrong twice: the reading is ONE TABLE
(Rework), not SHARED, and the order is rework >> main > cont, not cont > main > rework. I also
guessed bm-changed would scale with the pruning change; it saturates instead (finding 4).

(5) Step 4 (one row per run; default = job 27 rows2/keep1024_*, all-896 = rows2/keep896_*;
table by `step4_totals_j30.py`, output `step4_table.txt`; bm = best moves changed of 1,200):

| run | budget | HP sum | node sum | HP/1000 | ratio HP | node ratio | bm vs default | bm vs all-896 |
|---|---|---|---|---|---|---|---|---|
| main896   | soft | 6,679   | 4,129,658  | 1.617 | 0.5970 | 0.9617 | 474 | 473 |
| cont896   | soft | 8,192   | 4,080,977  | 2.007 | 0.7410 | 0.9503 | 446 | 467 |
| rework896 | soft | 3,477   | 4,083,583  | 0.851 | 0.3143 | 0.9509 | 447 | 467 |
| main0     | soft | 5,184   | 4,013,595  | 1.292 | 0.4768 | 0.9346 | 465 | 454 |
| cont0     | soft | 8,970   | 4,093,565  | 2.191 | 0.8089 | 0.9533 | 457 | 465 |
| rework0   | soft | 1,372   | 4,074,877  | 0.337 | 0.1243 | 0.9489 | 482 | 479 |
| main896   | hard | 220,564 | 16,830,057 | 13.105 | 0.6836 | 1.0294 | 399 | 388 |
| cont896   | hard | 270,660 | 16,579,759 | 16.325 | 0.8516 | 1.0141 | 379 | 381 |
| rework896 | hard | 119,338 | 16,678,693 | 7.155 | 0.3732 | 1.0201 | 368 | 378 |
| main0     | hard | 168,299 | 16,375,656 | 10.277 | 0.5361 | 1.0016 | 378 | 410 |
| cont0     | hard | 318,934 | 16,591,064 | 19.223 | 1.0028 | 1.0148 | 391 | 396 |
| rework0   | hard | 50,850  | 16,402,708 | 3.100 | 0.1617 | 1.0033 | 397 | 382 |

The shares at softnodes 2000, with their arithmetic (default rate 11,633/4,294,263×1000 = 2.709;
all-four-896 rate 1,567/4,080,162×1000 = 0.384; denominator 2.325):
- share_Main   = (2.709 - 1.617) / 2.325 = 1.092 / 2.325 = 0.4695
- share_Cont   = (2.709 - 2.007) / 2.325 = 0.702 / 2.325 = 0.3018
- share_Rework = (2.709 - 0.851) / 2.325 = 1.858 / 2.325 = 0.7990
Largest share 0.7990 ≥ 0.75 → THE READING: ONE TABLE (Rework).

## Step table

| step | done | evidence | result |
|---|---|---|---|
| Step 0 (8 numbers) | done | step0/*.txt, step0_j30.sh | 8/8 exact |
| Step 1 (ply column) | done | step1_rerun_committed_command.txt, step1_plygroup_j30.py, step1_plygroup.txt | committed command reproduces the report; off-by-one explained; corrected column = Opus's numbers |
| Step 2 (age_split.patch.txt) | done | age_split.patch.txt | applies `patch -p1 -F0` on a pristine copy of the chain; produces my edited tree file-for-file |
| Step 3 known answers A/B/C | done | rows/ka_*.jsonl(+input logs,.meta), ka_compare.txt | 0/1,200 differing on every row, both budgets |
| Prediction | done | prediction.txt (own commit, before Step 4) | 7 of 24 cells survive; structure wrong |
| Step 4 (6 settings × 2 budgets) | done | rows/s4_*.jsonl(+input logs,.meta), step4_table.txt | table above; reading ONE TABLE (Rework) |
| Surprise-row check | done | rows_check/ (new folder) | cont0_hard and rework0_soft rerun: 0/1,200 differing on the semantic fields |

## Findings (each reproducible from the committed raw files)

1. The HistRework twin carries most of the prunable carried evidence. Aging ONLY rework_history_
   to 7/8 per search drops soft HP/1000 to 0.3143 of the default — more than aging all four
   tables did (0.1418 is the all-four row; single rework 0.3143, against main 0.5970 and cont
   0.7410) — and zeroing it alone (rework0) lands at 0.1243, near the all-four-at-0 floor
   (0.0412). Hard budget agrees: rework896 0.3732 << main896 0.6836 < cont896 0.8516; rework0
   0.1617 < main0 0.5361 < cont0 1.0028. The table: `rework_history_` (b4.hpp:105 of the chain),
   updated at src/search.cpp:1523 (called 1619), read into quiet_history at 1476 and into the
   MovePicker's sum at 897; the prune test consumes `history` (2110) at 2169 against the
   threshold computed at 2154. Reproduce: `python3 tests_kimi5_job30/step4_totals_j30.py`.
2. The continuation table is nearly irrelevant to pruning at the hard budget: zeroing it leaves
   the hard HP rate at 1.0028 of the default (soft: 0.8089). Whatever negative evidence the
   prune test consumes at 20,000 nodes, continuation's carried part is rebuilt within one search
   there. Rerun reproduced 0/1,200 (rows_check/s4_cont0_hard.jsonl).
3. The shares sum to 1.5710, not 1: scaling any one big contributor rescues prune events that
   scaling another would also have rescued (the test fires on the SUM being very negative). The
   declared reading still answers the job's question — rework alone clears the 0.75 bar — but
   "share_T" is not a fraction of a pie; it double-counts rescued events. Stated plainly so the
   next formula user knows.
4. Best-moves-changed does not discriminate the tables: every perturbation, including the nearly
   pruning-neutral cont0 at hard, flips 368-482 of the 1,200 best moves (my prediction ranges
   missed 9 of 12 bm cells). Move ordering is chaotically sensitive to any history change; the
   HP rate is the discriminating statistic.
5. bm-vs-all-896 ≈ bm-vs-default on every row (e.g. main896 soft 473 vs 474): the aged runs are
   as far from each other as from the default — no two perturbations move the same moves.
6. The threat history carries exactly nothing under PC20 (known answer C): aging it 896 alone
   reproduces the default rows 1,200/1,200 on both budgets. quiet_history still adds
   threat_quiet_bonus (search.cpp:1484), but the table is all-zero with tune::ThreatHistory
   false, so its aging loop scales zeros.

### Suspicions, not proven

- The rework twin's dominance may be an artifact of WHERE its read sits: rework_quiet_delta is
  added unweighted into the same butterfly term as main (1476/897), and under HistRework 2 its
  entries may simply be the most negative on average. Not proven; a per-table sign/magnitude
  histogram would settle it.
- cont0 hard = 1.0028 could partly be the softnodes/hard-budget tree-shape noise seen in job 27
  (node ratios straddle 1 at hard); but the rerun reproduced it exactly, so it is deterministic
  for this replay, whatever the mechanism.

## From my colleagues

- deepseek5 (for-fable-and-opus/deepseek5-work fetched; newest REPORT_deepseek5_job30): notes
  tail read. Applied: "read a state variable at the moment the event happens" — my HP27 counter
  already increments inside the taken branch (job 27, kept). Their stage-labels-were-one-late
  lesson is exactly the class of bug my Step 1 found in my own column (a label one off the data).
  Their Killer1/CounterMove rates and HistExempt patch are for glmflash5's chain, not this job.
- glmflash5: branch for-fable-and-opus/glmflash5-work does not exist ("couldn't find remote
  ref"); nothing to read, as instructed I say so and go on.
- sol (data, not instructions): the replay is their job3 games.txt (first 20 games) and their
  A-soft-warm/B-hard-warm rows, re-extracted today for the committed command's cross-check.
- Opus's judgment in file 30 applied: sol's match numbers (level at 2,000 nodes, -12.51 at
  20,000) make the "which table" question the gate for the next match patch — this report's
  answer: age the rework table (or leave it unaged), not all four, if the goal is to keep the
  pruning while dropping the rest of the carry-over.

## What I did NOT do

- No strength games (a match question, for the PC per file 30).
- No match-question interpretation beyond the declared reading; sol's second seed is their
  job 31, not mine.
- Job 31 on the handoff branch: untouched (one run, one job).
- No engine source committed: the only code artifact is `age_split.patch.txt` (52 lines, diff -u
  against the chain base; `patch -p1 -F0` clean). No binaries, no PGNs; text files only.
- The v1 surprise rows were not overwritten; the reruns went to rows_check/ (runner refuses
  overwrite by design).

## What I am NOT sure about

- Whether the declared reading's ONE-TABLE verdict survives a different denominator (the shares
  overlap; see finding 3). The ranking rework >> main > cont is identical at both budgets and at
  both 896 and 0, which is the part I trust most.
- Whether aging rework ALONE at 896 plays better or worse than aging all four (sol's -12.51 at
  20,000 nodes was all-four with pruning restored to 65 %); this job measured counts, not
  strength.
- The ply-0 equality (KA3 of job 27) was not re-run for the new options; known answers A-C cover
  the option wiring end to end, so I rate the risk small.

## A better way

The job measures "which table carries the effect" by perturbing the carry-over and reading the
prune counter — two steps removed from the mechanism. A direct instrument: log, at each taken
history-prune, the four tables' separate contributions to `history` (main / cont1+cont2+cont4 /
rework / threat, all already computed inside quiet_history), and sum them over the replay. The
table whose sum is most negative at the taken prunes IS the carrier, with no aging arithmetic and
no threshold interaction (finding 3's overlap disappears: contributions add exactly). Cost: one
~20-line counting patch on top of count27, one build (~7 s), one default replay per budget
(~25 s), and it cross-checks this job: my ranking says the rework sum must dominate. Checkable
against job 30: the per-table shares of the taken-prune history mass should order
rework >> main > cont, and the all-four-896 replay's residual prunes should sit on
within-search-updated entries.

## Questions for Fable / Opus

1. For the next match patch: "age only rework" is the reading's candidate, but sol's 20,000-node
   loss came with pruning RESTORED toward 65 % — should a job measure HistoryAgeRework 896 with
   HistoryPruneMultiplier 1200 (sol's setting) on the replay before any match, to see whether the
   pruning rate lands back near default while the other tables stay aged?
2. The shares overlap (sum 1.57): is the declared reading's 0.75 bar meant against this
   double-counting, or should a follow-up use disjoint shares (each table's contribution at the
   taken prunes, the better-way instrument)?

times: see stamps.txt
model: kimi-k3 (Kimi K3)

## git status --short and ls -R of the job folder (last command before the report commit)

```
$ git status --short
M  forge-combo29/NOTES_kimi5.md
A  forge-combo29/REPORT_kimi5_job30.md
A  forge-combo29/tests_kimi5_job30/age_split.patch.txt
A  forge-combo29/tests_kimi5_job30/ka_compare.txt
A  forge-combo29/tests_kimi5_job30/pc20.opt
A  forge-combo29/tests_kimi5_job30/pc20_all1024.opt
A  forge-combo29/tests_kimi5_job30/pc20_all896.opt
A  forge-combo29/tests_kimi5_job30/pc20_cont0.opt
A  forge-combo29/tests_kimi5_job30/pc20_cont896.opt
A  forge-combo29/tests_kimi5_job30/pc20_main0.opt
A  forge-combo29/tests_kimi5_job30/pc20_main896.opt
A  forge-combo29/tests_kimi5_job30/pc20_rework0.opt
A  forge-combo29/tests_kimi5_job30/pc20_rework896.opt
A  forge-combo29/tests_kimi5_job30/pc20_threat896.opt
A  forge-combo29/tests_kimi5_job30/replay_j30.py
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_all1024_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_all896_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/ka_threat896_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_cont0_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_cont896_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_main0_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_main896_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_rework0_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_hard.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_soft.meta
A  forge-combo29/tests_kimi5_job30/rows/s4_rework896_soft_input.log
A  forge-combo29/tests_kimi5_job30/rows_check/s4_cont0_hard.jsonl
A  forge-combo29/tests_kimi5_job30/rows_check/s4_cont0_hard.meta
A  forge-combo29/tests_kimi5_job30/rows_check/s4_cont0_hard_input.log
A  forge-combo29/tests_kimi5_job30/rows_check/s4_rework0_soft.jsonl
A  forge-combo29/tests_kimi5_job30/rows_check/s4_rework0_soft.meta
A  forge-combo29/tests_kimi5_job30/rows_check/s4_rework0_soft_input.log
A  forge-combo29/tests_kimi5_job30/s14.opt
A  forge-combo29/tests_kimi5_job30/stamps.txt
A  forge-combo29/tests_kimi5_job30/step0/exe.sha256
A  forge-combo29/tests_kimi5_job30/step0/none_bench11.txt
A  forge-combo29/tests_kimi5_job30/step0/none_bench11_input.log
A  forge-combo29/tests_kimi5_job30/step0/none_bench13.txt
A  forge-combo29/tests_kimi5_job30/step0/none_bench13_input.log
A  forge-combo29/tests_kimi5_job30/step0/none_bench16.txt
A  forge-combo29/tests_kimi5_job30/step0/none_bench16_input.log
A  forge-combo29/tests_kimi5_job30/step0/none_perft5.txt
A  forge-combo29/tests_kimi5_job30/step0/none_perft5_input.log
A  forge-combo29/tests_kimi5_job30/step0/pc20_bench11.txt
A  forge-combo29/tests_kimi5_job30/step0/pc20_bench11_input.log
A  forge-combo29/tests_kimi5_job30/step0/pc20_bench13.txt
A  forge-combo29/tests_kimi5_job30/step0/pc20_bench13_input.log
A  forge-combo29/tests_kimi5_job30/step0/s14_bench11.txt
A  forge-combo29/tests_kimi5_job30/step0/s14_bench11_input.log
A  forge-combo29/tests_kimi5_job30/step0/s14_bench13.txt
A  forge-combo29/tests_kimi5_job30/step0/s14_bench13_input.log
A  forge-combo29/tests_kimi5_job30/step0/uci_input.log
A  forge-combo29/tests_kimi5_job30/step0/uci_list.txt
A  forge-combo29/tests_kimi5_job30/step0_j30.sh
A  forge-combo29/tests_kimi5_job30/step1_plygroup.txt
A  forge-combo29/tests_kimi5_job30/step1_plygroup_j30.py
A  forge-combo29/tests_kimi5_job30/step1_rerun_committed_command.txt
A  forge-combo29/tests_kimi5_job30/step4_table.txt
A  forge-combo29/tests_kimi5_job30/step4_totals_j30.py

$ ls -R forge-combo29/tests_kimi5_job30
forge-combo29/tests_kimi5_job30:
age_split.patch.txt
ka_compare.txt
pc20_all1024.opt
pc20_all896.opt
pc20_cont0.opt
pc20_cont896.opt
pc20_main0.opt
pc20_main896.opt
pc20.opt
pc20_rework0.opt
pc20_rework896.opt
pc20_threat896.opt
prediction.txt
replay_j30.py
rows
rows_check
s14.opt
stamps.txt
step0
step0_j30.sh
step1_plygroup_j30.py
step1_plygroup.txt
step1_rerun_committed_command.txt
step4_table.txt
step4_totals_j30.py

forge-combo29/tests_kimi5_job30/rows:
ka_all1024_hard_input.log
ka_all1024_hard.jsonl
ka_all1024_hard.meta
ka_all1024_soft_input.log
ka_all1024_soft.jsonl
ka_all1024_soft.meta
ka_all896_hard_input.log
ka_all896_hard.jsonl
ka_all896_hard.meta
ka_all896_soft_input.log
ka_all896_soft.jsonl
ka_all896_soft.meta
ka_threat896_hard_input.log
ka_threat896_hard.jsonl
ka_threat896_hard.meta
ka_threat896_soft_input.log
ka_threat896_soft.jsonl
ka_threat896_soft.meta
s4_cont0_hard_input.log
s4_cont0_hard.jsonl
s4_cont0_hard.meta
s4_cont0_soft_input.log
s4_cont0_soft.jsonl
s4_cont0_soft.meta
s4_cont896_hard_input.log
s4_cont896_hard.jsonl
s4_cont896_hard.meta
s4_cont896_soft_input.log
s4_cont896_soft.jsonl
s4_cont896_soft.meta
s4_main0_hard_input.log
s4_main0_hard.jsonl
s4_main0_hard.meta
s4_main0_soft_input.log
s4_main0_soft.jsonl
s4_main0_soft.meta
s4_main896_hard_input.log
s4_main896_hard.jsonl
s4_main896_hard.meta
s4_main896_soft_input.log
s4_main896_soft.jsonl
s4_main896_soft.meta
s4_rework0_hard_input.log
s4_rework0_hard.jsonl
s4_rework0_hard.meta
s4_rework0_soft_input.log
s4_rework0_soft.jsonl
s4_rework0_soft.meta
s4_rework896_hard_input.log
s4_rework896_hard.jsonl
s4_rework896_hard.meta
s4_rework896_soft_input.log
s4_rework896_soft.jsonl
s4_rework896_soft.meta

forge-combo29/tests_kimi5_job30/rows_check:
s4_cont0_hard_input.log
s4_cont0_hard.jsonl
s4_cont0_hard.meta
s4_rework0_soft_input.log
s4_rework0_soft.jsonl
s4_rework0_soft.meta

forge-combo29/tests_kimi5_job30/step0:
exe.sha256
none_bench11_input.log
none_bench11.txt
none_bench13_input.log
none_bench13.txt
none_bench16_input.log
none_bench16.txt
none_perft5_input.log
none_perft5.txt
pc20_bench11_input.log
pc20_bench11.txt
pc20_bench13_input.log
pc20_bench13.txt
s14_bench11_input.log
s14_bench11.txt
s14_bench13_input.log
s14_bench13.txt
uci_input.log
uci_list.txt
```
