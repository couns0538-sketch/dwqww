# REPORT_kimi5_job25 (kimi5, 2026-11-18 UTC) — A2+A5 on the PC build: where the tree shrinks

**What was asked:** port FailHighBlend (3 bits) + RfpNoTtPv/RfpTtGuard/RfpCorrMul to the PC build as
`A2A5.pc.patch.txt`, prove it against the file's known rows, then measure depth scaling and, with
observe-only counters, say WHERE the smaller tree comes from (fewer singular extensions, or multi-cut,
TT cutoffs, RFP returns). **The answer:** the port is exact (all 14 depth-12 row sets equal the known
answers, hashes included); the shrink's event signature is the singular outcome redistribution —
positive extensions fall (doubles collapse), negative extensions and "none" rise — while multi-cut,
TT-lower cutoffs and RFP returns all move the GROW direction, so by elimination the shrink lives in
the singular classes. **How sure:** Step 0 exact, Step 1 exact on every hash, closures hold per search
on all 12 counting runs, the counting build reproduces the plain rows to the node; the "mostly" is an
elimination over event counts, not weighed nodes (Suspicion S1).

## (1) Step 0: MET

All eight numbers of file 17 on the port build, every new option at default
(raw files in `tests_kimi5_job25/step0/`): none 312866 / 862329 / 3024920 / 4865609
(`none_bench11.txt`, `none_bench13.txt`, `none_bench16.txt`, `none_perft5.txt`),
S14 242796 / 656517 (`s14_bench11.txt`, `s14_bench13.txt`),
PC20 278024 / 587276 (`pc20_bench11.txt`, `pc20_bench13.txt`) — all exact.
`uci_list.txt` shows `FailHighBlend spin default 0 min 0 max 7`, `RfpNoTtPv 0/0/1`,
`RfpTtGuard 0/0/1`, `RfpCorrMul 0/0/64`. Exe sha256 62789510c3... (`step0/exe.sha256`).

## (2) Prediction, graded row by row (`tests_kimi5_job25/prediction.txt`, own commit before Step 1)

| row | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1 fhb7/base d14 G | 0.89 | [0.84, 0.94] | 0.9305 | survives |
| P2 a2a5/base d14 G | 0.95 | [0.89, 1.01] | 0.9924 | survives |
| P3 extend share, base G d12 | 0.69 | [0.62, 0.76] | 0.6304 (111,221/176,423) | survives |
| P4 fhb7 extensions chg, G d12 | -20 % | [-45 %, -5 %] | -21.1 % (111,221 -> 87,729) | survives |
| P5 bit removing the most extensions on G | bit 4 | bit 4 not the largest | **bit 1** (-12.0 % vs bit 4's -10.0 %) | **KILLED** |

P3 honesty note: my prior mis-assigned job 22's "b2 10,247" to extension 2; job 22's "sing 111,221"
is ext1+ext2 lumped (my ext1 43,862 + ext2 67,359 = 111,221 exactly). The lumped prior still landed
inside the range. P5's reasoning (bit 4 owns the deep stores) was wrong: bit 1's blended RFP returns
reach the parents' stored values and remove the most extensions on G (on O bit 4 does, -19.3 %).

## (3) Step 1: equal on all rows; changed-position counts

Every setting equals the known answers position by position (node count AND best move; checker
`check_s1_j25.py`, raw rows `rows/*_d12.json` + `.meta`): **base 200/200, 353/353; fhb1, fhb2, fhb4,
fhb7, rfp3, a2a5 each 200/200 and 353/353** — all sums, first-three, node hashes and move hashes OK
(full print in `step1_check.txt` via `python3 check_s1_j25.py rows 12`).
Positions with a changed node count against base, and changed best moves:

| setting | O nodes chg | O bm chg | G nodes chg | G bm chg |
|---|---|---|---|---|
| fhb1 | 200/200 | 49 | 350/353 | 91 |
| fhb2 | 200/200 | 56 | 351/353 | 101 |
| fhb4 | 200/200 | 60 | 350/353 | 100 |
| fhb7 | 200/200 | 54 | 351/353 | 98 |
| rfp3 | 200/200 | 57 | 352/353 | 97 |
| a2a5 | 200/200 | 52 | 352/353 | 93 |

## (4) Step 2: depth scaling (`step2_table.txt`, driver `step2_j25.py`; d12 rows are Step 1's)

| set | depth | setting | nodes | ratio | boot 95 % | bm != base |
|---|---|---|---|---|---|---|
| O | 14 | base | 19,377,109 | 1.0000 | — | 0 |
| O | 14 | fhb7 | 18,799,184 | 0.9702 | [0.9161, 1.0181] | 40 |
| O | 14 | a2a5 | 19,329,532 | 0.9975 | [0.9380, 1.0531] | 42 |
| G | 14 | base | 41,052,503 | 1.0000 | — | 0 |
| G | 14 | fhb7 | 38,199,553 | 0.9305 | [0.8713, 0.9836] | 98 |
| G | 14 | a2a5 | 40,741,564 | 0.9924 | [0.9280, 1.0461] | 91 |

(d12 for reference: O fhb7 0.9517 [0.8998, 0.9985] bm 54, a2a5 0.9612 [0.9116, 1.0038] bm 52;
G fhb7 0.9016 [0.8588, 0.9409] bm 98, a2a5 0.9624 [0.9139, 1.0046] bm 93.)
No depth-14 sum equals a depth-12 sum. **The shrink WEAKENS with depth**: fhb7 on G 0.9016 -> 0.9305,
a2a5 0.9624 -> 0.9924 (nearly neutral at d14); same direction on O.

## (5) Step 3: the counters (`step3_sums.txt`, `step3_classes.txt`; 12 full-output files summed)

First known answer: **the counting build's rows EQUAL Step 1's plain rows on all 12 (setting, set)
pairs, nodes and best moves** (`step3_sum_j25.py`). Closures: per run, the six singular outcomes add
to the tests and the four RFP classes add to today's would-returns — OK on all 12. Searches summed:
353 per G run, 200 per O run (printed by the script). Cross-check: my base G classes reproduce job
22's recounted numbers exactly (tests 176,423; ext1+ext2 111,221; mcut 31,604; ext-2 10,247;
ext-1 15,219; none 8,132).

Per-class counts, set G (depth 12) and their change against base:

| class | base | fhb1 | fhb2 | fhb4 | fhb7 |
|---|---|---|---|---|---|
| tests | 176,423 | 173,513 (-1.6) | 171,042 (-3.1) | 170,814 (-3.2) | 164,148 (-7.0) |
| ext1+ext2 | 111,221 | 97,868 (-12.0) | 104,468 (-6.1) | 100,136 (-10.0) | 87,729 (-21.1) |
| — ext1 | 43,862 | 49,094 (+11.9) | 43,254 (-1.4) | 44,427 (+1.3) | 48,601 (+10.8) |
| — ext2 | 67,359 | 48,774 (-27.6) | 61,214 (-9.1) | 55,709 (-17.3) | 39,128 (-41.9) |
| multi-cut | 31,604 | 33,514 (+6.0) | 30,262 (-4.2) | 29,988 (-5.1) | 29,016 (-8.2) |
| ext -2 | 10,247 | 12,406 (+21.1) | 10,644 (+3.9) | 11,756 (+14.7) | 13,779 (+34.5) |
| ext -1 | 15,219 | 20,985 (+37.9) | 17,388 (+14.3) | 20,061 (+31.8) | 24,029 (+57.9) |
| none | 8,132 | 8,740 (+7.5) | 8,280 (+1.8) | 8,873 (+9.1) | 9,595 (+18.0) |
| ttLower | 1,202,904 | 1,136,736 (-5.5) | 1,133,516 (-5.8) | 1,123,477 (-6.6) | 1,041,548 (-13.4) |
| ttUpper | 126,407 | 117,776 (-6.8) | 123,638 (-2.2) | 139,104 (+10.0) | 128,739 (+1.8) |
| ttExact | 31,346 | 30,143 (-3.8) | 29,565 (-5.7) | 31,582 (+0.8) | 30,141 (-3.8) |
| rfp returns | 4,748,667 | 4,425,815 (-6.8) | 4,398,462 (-7.4) | 4,440,620 (-6.5) | 4,134,563 (-12.9) |

Set O (depth 12), changes against base (counts in `step3_classes.txt`): ext1+ext2 -14.3 / -9.1 /
-19.3 / -24.6 % (fhb1/2/4/7); ext2 -48.9 / -20.6 / -33.5 / -63.3 %; multi-cut -3.9 / -12.0 / -17.4 /
-16.9 %; ext-2 and ext-1 rise everywhere (+11.8..+73.2 %); ttLower -2.4 / -1.7 / -7.2 / -8.6 %;
rfp returns -3.3 / -1.5 / -6.3 / -6.0 %.

rfp3 four-way split (at every node where TODAY's step would return): G 4,530,393 = returned
4,160,551 (91.8 %) + refused-by-RfpNoTtPv 13,225 (0.29 %) + refused-by-RfpTtGuard 62,642 (1.38 %) +
refused-only-by-RfpCorrMul 293,975 (6.49 %); O 2,178,928 = 2,088,768 (95.9 %) + 3,070 (0.14 %) +
6,684 (0.31 %) + 80,406 (3.69 %). Closures exact per search.

**The answer to the job's question.** Under every bit, on both sets: positive extensions fall (the
double-extension condition `singular_score < singular_beta - 24` collapses first), the freed tests
land in ext-2 / ext-1 / none (all rise), and multi-cut, TT-lower cutoffs and RFP returns all FALL —
i.e. fewer subtree-savings, which pushes the tree UP. By elimination the shrink lives in the singular
outcome redistribution (the file's hypothesized mechanism, plus its mirror side ext-2/ext-1); the
other three classes cannot be the cause — they are side-effects of the same lowered stored scores
(blended stores -> `tt_score >= beta` fails more; `eval = tt_score` raises eval less -> fewer RFP
returns). Exception: **fhb1 on G, where multi-cut RISES +6.0 %** — there the multi-cut is a co-driver
of bit 1's shrink (the biggest single-bit shrink on G, 0.932).
**Classes that differ between O and G:** multi-cut flips sign under fhb1 (+6.0 % G / -3.9 % O); the
RFP-return fall is ~2x larger on G than O under every bit; the bit that removes the most extensions
is bit 1 on G but bit 4 on O; ext1 rises on G under fhb1/fhb4/fhb7 but falls on O; fhb2 GROWS the O
tree (+0.6 %) while shrinking G's (-5.6 %).

## Step table

| step | done | evidence | result |
|---|---|---|---|
| claim + colleagues | done | `../CLAIM_kimi5_job25.txt`; notes section below | — |
| build recipe + port `A2A5.pc.patch.txt` | done | `A2A5.pc.patch.txt`, `A2A5_places.txt`, roundtrip | applies `patch -p1 -F0`, roundtrip identical |
| Step 0 | done | `step0/` | MET, all eight + uci ranges |
| prediction before Step 1 | done | `prediction.txt` (own commit) | graded above |
| Step 1 identities | done | `rows/`, `check_s1_j25.py`, `step1_check.txt` | 14/14 row sets equal |
| Step 2 depth scaling | done | `rows/*_d14.json`, `step2_table.txt` | table above |
| Step 3 counters | done | `rows_count/`, `A2A5Count.pc.patch.txt`, `step3_sums.txt`, `step3_classes.txt` | node identity EQUAL; closures OK; tables above |
| stamps | done | `stamps.txt` | real `date -u` lines, "not stamped" where not pasted |

## Findings (file:line in the PC build; reproduce with the quoted commands)

1. The port's five places: listed in `A2A5_places.txt` (search.cpp 108/194, search.hpp 257;
   qsearch 1676 + 1745; rfp 1937-1940; main-search end 2366 + correction 2376-2381). At defaults the
   engine computes exactly today's search (base hashes equal files 18-24).
2. The singular mechanism: `singular_beta = tt_score - SingularMargin * depth` (search.cpp:2194) reads
   the stored score the blend lowers (stores at 1678/1747/2369). Extensions fall and negative
   extensions rise exactly as "verification clears singular_beta more often" predicts.
   Reproduce: `python3 step3_sum_j25.py` (closures) and `python3 step3_classes_j25.py`.
3. The double-extension gate `singular_score < singular_beta - 24` (search.cpp:2208) is the first
   casualty of a lowered singular_beta: ext2 -41.9 % at fhb7 G while ext1 RISES +10.8 %.
4. The RFP step (search.cpp:1937-1940) reads `eval`, which the tt-score override can raise
   (search.cpp:1873-1877); blended stores lower that override -> RFP returns fall (-12.9 % fhb7 G).
   rfp3's growth (+2.1 % G) is the refused returns: corr margin refuses 6.5 % of today's (G).
5. Depth weakening: the d14/d12 ratios move toward 1 on both sets (Step 2 table) — the blend's tree
   advantage does not compound with depth.

## Suspicions, not proven

- S1: "Mostly" is an elimination over EVENT counts, not weighed nodes: a removed double extension and
  a removed RFP return are not the same number of nodes. Not weighed (see "A better way"). Uncounted
  classes (futility, LMR, null move, probcut) also move; the elimination assumes no uncounted class
  shrinks the tree.
- S2: that losing 42 % of double extensions is the strength cost behind the PC's -8.92 is consistent
  (singular extensions find forced moves) but tree counts cannot prove a strength claim.
- S3: ext1 RISING on G under fhb1/fhb4/fhb7 while falling on O is noted without an explanation.
- S4: the depth weakening (finding 5) has no measured cause here; a d14 counter run would say whether
  the extension drop itself weakens with depth.

## From my colleagues

- deepseek5 (branch for-fable-and-opus/deepseek5-work, newest report job 30 + notes): the stage-label
  lesson (read a state variable at the moment the event happens — my counters sit at the decision
  points, not after) and "fix the FIRST build error". Applied: counter placement at the exact
  outcome branches; builds clean on first try. Its ucinewgame sufficiency proof (S3) backs the
  runner's per-search `ucinewgame`+`isready` discipline, which the runner already enforces.
- glmflash5 (branch cursor/glmflash5-work-cb5c, newest report job 27; it has stopped, noted in file
  25 — the template's `for-fable-and-opus/glmflash5-work` ref does not exist): its pools say the
  extension CAP's value is depth-dependent (V +1.3 level at 20k nodes, gains at 2k). Consistent with
  my depth-weakening of the blend's shrink; nothing directly applied.

## What I did NOT do

No node-weighted class table (event counts only); no depth-14 counter runs; no strength/match
measurement (not this job); no tuning of any value; no per-position counter breakdown.

## What I am NOT sure about

S1-S4 above; plus: the kill range of P1 was crossed only by luck of the compounding guess (the true
d14 ratio moved TOWARD 1, against the compounding direction) — P1 survives but its reasoning was
wrong-direction.

## A better way

Weigh the classes in NODES, not events: around the child `search_child` of the extension block
(search.cpp:2201's call site and the ordinary move call), accumulate `local_nodes_` deltas per
outcome class (ext1/ext2/ext-2/ext-1/none), and around the RFP/TT-cutoff returns accumulate the
nodes the node did NOT spend (measurable as the sibling-average). One extra array of int64 turns this
job's elimination argument into a direct per-class node budget — the "mostly" question then has a
weighed answer. Cheap to add to `A2A5Count.pc.patch.txt` (same print site). Also: run the same
counters at depth 14 to test finding 5's cause (does the extension drop itself weaken with depth?).

## UTC stamps

See `tests_kimi5_job25/stamps.txt` (run start 12:04:28Z first). Report assembly 12:10:38Z.

## Model name

Kimi K3 (runtime: kimi-k3), running as kimi5.
