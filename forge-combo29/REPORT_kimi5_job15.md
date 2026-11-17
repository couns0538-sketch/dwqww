# kimi5 job 15 report — AlphaQs: AlphaRaiseReduce (A7) and QsLateMoves (A8) text patches

Three plain lines: asked were two new text patches behind their own options (default = today's code) on
6b98f217 + FailHighBlend: fewer plies after alpha rises (A7) and a limit on late captures in quiescence (A8),
with identities, counters and trees. Both patches written, every Step 0 / Step 1 known answer met, counters and
trees measured on O and G. Sure: every number below is reproduced by the committed raw files; the two patches
apply with `patch -p1 -F0`, zero fuzz.

(1) Step 0 MET on the patched build (bench 11 = 312,866; bench 13 = 862,329; bench 16 = 3,024,920;
`go perft 5` = 4,865,609; `uci` lists FailHighBlend 0..7 d0, AlphaRaiseReduce 0..2 d0, AlphaRaiseMaxDepth
0..64 d12, QsLateMoves 0..32 d0 — files step0_*.txt). I2 MET: O 9,500,069 / G 18,466,239, per position and best
move equal to job 12's I2 rows (200 of 200, 353 of 353). I3 MET: O 9,272,824 / G 18,240,994, equal to job 12's
T1 rows (200 of 200, 353 of 353). W1 (AlphaRaiseReduce 1 + AlphaRaiseMaxDepth 3) = I2 on every position, nodes
and best moves, O and G. W2 (QsLateMoves 32) = I2 on every position, O and G. Controls DIFFER as required:
S14+AlphaRaiseReduce 1 = 6,360,271 on O (≠ I2), S14+QsLateMoves 1 = 9,163,836 on O (≠ I2).

(2) Counters (tests_kimi5_job15/counter_sums.txt; 200/353 searches summed per run, one ALQ line per search;
counting build's node sums equal the plain build's on all 8 option-set pairs, e.g. cnt_s14 O 9,500,069 / G
18,466,239 = I2). **raised_nonpv = 0 in every one of the 8 runs** (the known answer of (b)). Under S14 every
other new count is 0 except raised (O 63,801 / G 105,001, all PV) and qs_seen. Under AlphaRaiseReduce 1:
reduced 26,184 (O) / 42,438 (G) of raised 52,876 (O) / 82,730 (G) → 49.5 % / 51.3 % of raises reduced, by depth
before the reduction (d=3..11, O): 6,398 / 5,185 / 4,365 / 3,697 / 2,662 / 1,810 / 1,131 / 652 / 284,
reduced_other 0. qs_seen beyond the second move (S14): 755,757 / 3,618,228 = 20.9 % (O), 1,112,028 / 4,786,082
= 23.2 % (G). Under QsLateMoves 2 (O/G): qs_skipped 447,125 / 840,989, qs_kept_recapture 160,235 / 167,843.
Under QsLateMoves 3 (O/G): qs_skipped 172,452 / 362,090, qs_kept_recapture 52,732 / 61,693.

(3) Step 3 trees (plain patched build, ratio to I2, bootstrap 95 % over positions, 2,000 resamples seed 12 —
boot_trees.txt):

| tree | O ratio [interval] | O bestmoves changed | G ratio [interval] | G bestmoves changed |
|---|---|---|---|---|
| T_a1 AlphaRaiseReduce 1 | 0.6695 [0.6336, 0.7078] | 60/200 | 0.6905 [0.6565, 0.7268] | 95/353 |
| T_a2 AlphaRaiseReduce 2 | 0.4522 [0.4268, 0.4783] | 57/200 | 0.5134 [0.4834, 0.5460] | 102/353 |
| T_q2 QsLateMoves 2 | 0.9927 [0.9434, 1.0479] | 43/200 | 1.0172 [0.9743, 1.0649] | 58/353 |
| T_q3 QsLateMoves 3 | 0.9924 [0.9407, 1.0480] | 35/200 | 0.9997 [0.9688, 1.0301] | 29/353 |
| T_aq ARR 1 + QsLateMoves 3 | 0.6569 [0.6255, 0.6916] | 62/200 | 0.6749 [0.6418, 0.7102] | 91/353 |

Trees only, no strength claim. Note T_q2 on G: the tree GROWS 1.7 % under a skip (one more case of "a prune
count does not predict a tree"). T_a1/T_a2/T_aq are far outside my predicted kill ranges (prediction.txt:
0.96/0.93/0.95) — the A7 effect is much larger than I modelled, see "What I am NOT sure about".

## Answers (a) to (d), from the code (`src/search.cpp` at 6b98f217; line numbers of the unpatched file)

(a) Lines AFTER 2056 inside the same node that read `depth` — all see the reduced value: 1960 on every later
loop iteration (`int new_depth = depth - 1 + extension;` — the remaining moves of the node are searched one to
two plies shallower), 1991 (`board.halfmove_clock() + new_depth < 100 && depth >= 2` guard), 1994
(`int r = reduction(quiet, depth, move_count);` — later moves are also reduced LESS by LMR since depth is
smaller... note reduction() reads depth directly), 2029 (`update_continuation(ss, moved, move.to,
history_bonus(depth) / 2);`), and after the loop 2077 (`update_quiet_stats(..., depth + (best_score > beta +
100), ...)`), 2079 (`update_capture_stats(board, best_move, depth, ...)`), 2083/2084 (`history_bonus(depth) /
4`), 2089 (`history_bonus(depth) * tune::FailLowContinuationBonus / 100`), 2095/2097 (the TT store's `depth`
argument) and 2106 (`update_correction(board, depth, best_score, ss->static_eval)`). Show again:
`awk 'NR>=1955 && NR<=2110 && /depth/' src/search.cpp`.

(b) Can a score rise above alpha WITHOUT a cutoff where beta == alpha + 1? NO. At a non-PV node
`score > alpha` implies `score >= beta` (scores are integers, beta = alpha + 1), so the
`if (score >= beta) { ++ss->cutoff_count; break; }` at 2052 to 2055 fires before `alpha = score;` at 2056 is
reached. A7 therefore acts at non-root PV nodes only (the root is excluded by `!root_node`). Measured:
raised_nonpv = 0 in all 8 counter runs (counter_sums.txt), including the S14 runs where no new option acts.

(c) `move_count` at 1492 counts EVERY LEGAL move the picker returned in this quiescence node: it is incremented
after the `board.is_legal` check at 1491 and BEFORE the futility skip (1496 to 1499) and the SEE skip (1500),
so moves those two skips later throw away still count. `QsLateMoves 2` in words: in a quiescence node where the
side is not in check, mate-distance pruning is off and no mate score is at stake, the 3rd and every later legal
move the picker returns is skipped unless it gives check, is a promotion, or captures on the square the
opponent's last move just moved to (a recapture).

(d) `(ss - 1)->current_move`: qsearch entered from the main search at `depth <= 0` (1556) gets the SAME `ss`
the main-search node was called with, so `(ss - 1)->current_move` is the move made at the parent node — the
move that led into this position (set at 1754 or 1967 of the parent). When qsearch calls itself (1520,
`ss + 1`), the child's `(ss - 1)` is the caller's `ss`, whose `current_move` was set at 1507 to the capture just
played. In both cases it is the opponent's last move before this node, and the A8 recapture test compares
`move.to` against its destination square. (At the root's own qsearch frame this cannot occur: the root is
entered with depth >= 1, so qsearch at ply 0 is never reached from 1556.)

## The patches, sha256 and how to apply

- `tests_kimi5_job15/AlphaQs.patch.txt`, sha256
  9f68867c3e14bc159bf50f0ed84f1963ffc07a07817c959838345d557eb52918 — a unified diff against
  6b98f217 + `tests_kimi5_job12/FailHighBlend.patch.txt` (sha256 checked
  8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a before applying). Made with `diff -u` of
  the FHB tree against the edited tree. Options: AlphaRaiseReduce 0..2 d0, AlphaRaiseMaxDepth 0..64 d12,
  QsLateMoves 0..32 d0, defaults = today's code. The option declarations and table rows are anchored at
  CaptureFutilityBase / the TmFallingEvalPercent table row so the patch ALSO applies on top of the job-14
  patch: dry-run `patch -p1 --dry-run -F0` CLEAN on 6b98f217+FHB and on 6b98f217+FHB+RfpGuards (hunks 2-4 at
  offsets 3/5/7 lines there, zero fuzz both).
- Apply order: 6b98f217, `patch -p1 -F0 < FailHighBlend.patch.txt`, `patch -p1 -F0 < AlphaQs.patch.txt`
  (the plain patched build); then `patch -p1 -F0 < AlphaQsCount.patch.txt` and build with
  `-DCMAKE_CXX_FLAGS=-DFORGE_ALQ_CHECK=1` for the counting build.
- `tests_kimi5_job15/AlphaQsCount.patch.txt`, sha256
  379b8ff5882152e0ab9d72115e50461494569f8564e9fcd59f24ab9face7b21a — observe-only counters behind
  FORGE_ALQ_CHECK (default 0 = the code before it), same reset/print placement as job 12's counting patch.
- Builds: g++ 13.3.0, Release, machine has AVX-512+BMI2 (no FORGE_PORTABLE). Exe sha256 in exe_sha256.txt;
  the two exes differ (1b7e1848… plain, 825db9b1… counting). Runs may and did overlap (two parallel batches
  on 4 cores, Threads 1 each; node counts are unaffected).

## Steps table

| step | done | evidence | result |
|---|---|---|---|
| 0 honesty | done | step0_bench11/13/16.txt, step0_perft5.txt, step0_uci.txt | all known numbers met, 4 options listed |
| 1 identities | done | rows/i2_*, i3_*, w1_*, w2_* + cmp vs job 12 rows | I2, I3, W1, W2 met; controls t_a1, c_q1 differ |
| 2 counters | done | rows/cnt_*_full.txt, counter_sums.txt, sum_alq.py | raised_nonpv 0 in 8/8; sums = plain build 8/8 |
| 3 trees | done | rows/t_*.json, boot_trees.txt | table above |
| prediction | done | prediction.txt (own commit, before Step 1) | 2 of 5 ratios, both shares inside kill ranges |

## From my colleagues

Read: deepseek5 NOTES (branch 731fc808: stand5 self-play protocol + job-30 corrected stage rates — its
Killer1/CounterMove history findings are for later history jobs, not this one); glmflash5: NO branch exists
(said plainly: nothing to read); deepseek6 NOTES (ed9ab5649: VmHWM-vs-VmRSS lesson, .pyc hygiene, plant
controls) and the job-15 file's own summary of deepseek6's job 3/3b (FailHighBlend reproduced exactly;
CaptureFutility counters) and glmflash5 job 24. Applied: the harness rule from file 17 (the LAST Threads/Hash
line counts — the runner sends Threads 1 and Hash 16 once, before the option file, and no later Threads line
exists); the standing rule to prove options ARRIVE (the runner stops on any `unknown option`/`invalid value`;
none occurred; the input logs quote every setoption line, e.g. `setoption name AlphaRaiseReduce value 1`);
deepseek6's "a prune count does not predict a tree" — confirmed again by T_q2 on G (1.0172).

## What I did NOT do

No strength measurement (the job says trees only). The 12 G positions where the PC build (r15) differs are not
this job's concern (that is job 17). Job 16's paragraph about my job-3 wiring control belongs to job 16, not
here. No match play, no SAN/ASM review of generated code beyond the dry-runs and the measured identities.

## What I am NOT sure about

- Why A7's tree effect is so large (0.67 / 0.45 on O). The counters show only ~26 k reductions on 52.9 k raises
  (O), most at depth 3 — yet the tree shrinks by a third. My best reading: each reduction at a PV node shortens
  ALL remaining moves of that node (1960) and the node's TT store becomes shallower (2095/2097), so later
  iterations re-search more; the effect compounds along the PV. Not proven from the counters alone; a
  per-node follow-up counter (reductions by ply, or TT-store depth delta) would settle it. My prediction's
  kill ranges for T_a1/T_a2/T_aq fired — recorded as a missed model, not a patch defect: the wiring controls
  W1/W2 and the S14 counter rows prove the option acts only where designed.
- Whether QsLateMoves' near-neutral trees hide a real strength change; q2 grows the tree on G while shrinking
  it on O — set-dependent, like deepseek6's check-extension finding.

## A better way

The job's counter for A7 counts reductions by depth-before; the mechanism question above (why the tree shrinks
so much) would be answered cheaper by ONE more counter: for each reduction, the number of REMAINING legal moves
at the node (move_count vs total) — the expected work removed per reduction. That separates "many reductions
each removing little work" from "few reductions each removing a subtree". Cost: one integer array, no extra
runs (the same 8 counting runs suffice). Checkable: under ARR 2 the removed-work total must be >= ARR 1's on
the same set.

## times: see stamps.txt

Model name my runtime gives: Kimi K3.
