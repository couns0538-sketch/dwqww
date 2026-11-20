# kimi5 job 37 report — the census finished: ONE spec, two patches, bounds check, proofs, liveness of the 20 new options

## Three lines
- Asked: finish the census — one spec file for 39 of job 35's 40 options plus the 20 of K5, a script that reads only the spec and writes both patches, a bounds check (with two bad-copy controls), the run list and the reading guide; prove K3 on both trees, K4's 26 sums, K6's three options against hand edits, C-DEAD and C-LIVE; predict; then measure every new option at default±1 step on O and G, plus the ImprovingLookback 4 row, and close with the tune list.
- Answer: all of it done and proven, with ONE unfinished cell: Step 0's five pins exact; the spec holds 59 rows (options_spec.tsv, with v2 correcting two line-number cells); C-BOUNDS fails both bad copies and names the row; both patches apply with `patch -p1 -F0` (33 and 36 hunks) and are no-ops at defaults (K3: 553/553 positions identical on both builds); K4 26/26 sums to the node; K6 3/3 hand-edit-equal; C-DEAD and C-LIVE pass with Fable's sums. Step 4: 17 ALIVE, 3 DEAD (TtAgePenalty, NoisyValueWeight, NoisyMoverDiv), 1 NOT SEEN — CheckExtPlies p on G ran away (24M nodes on position 3; killed at ~17 min CPU; its three completed cells are strongly ALIVE). Prediction: 17 of 20 ALIVE/DEAD calls right, 3 of 5 ratio ranges, the best-move count (8 of 20) inside.
- Sure: high on the measurements (every run with ucinewgame+isready, refusal scan, exe sha and command in each .meta; the K6 and K4 cross-checks are independent of the patch generator). Medium on the kF patch beyond the measured window (K3 covers defaults only) and on Step 5's +1.3 % (ranges overlap; the PC measures its own).

## (1) Step 0
r15d, no options: bench 11 = 312866 (`step0/none_bench11.txt`), bench 13 = 862329 (`step0/none_bench13.txt`), go perft 5 = 4865609 (`step0/none_perft5.txt`); with PC20: bench 11 = 278024 (`step0/pc20_bench11.txt`), bench 13 = 587276 (`step0/pc20_bench13.txt`). All five exact. exe sha256 6b52e43e… (`step0/exe.sha256`), identical to job 35's r15d exe — the rebuilt tree is the same tree (search.cpp sha256 174e07a5…, re-verified after the three patches; pc_r15.patch sha256 d6bd72c5… matches the pin).

## (2) The spec
`options_spec.tsv` (committed alone, first Step 1 commit) + `options_spec_v2.tsv` (two corrected cells: DoubleExtPlies lines 2360,2374→2360,2373; QuietCheckBonus 940,1138→940,1142 — both were misread line numbers in v1; v1 stays untouched). 59 rows: 39 of job 35's 40 (ImprovingLookbackFallback removed per K2, its literal 4 stays at r15d:2034; ImprovingLookback max 4 step 2; TtNear50Clock max 120; CuckooRepMinClock class R) + the 20 of K5.
- Rows of K5 I class otherwise: ONE. QuietCheckBonus covers the 12000 at 940 AND the same literal at 1142 (the evasion scorer's dead `#else` branch — one meaning, one option; K5 named only 940). Also noted: the NoisyMoverDiv literal `/ 10` sits at line 1137 (the return wraps two lines); the spec's "1136" is the site's start line for both Noisy options.
- Rows whose "bound by" is not "none" (24): ten divisors — RfpWorseningDiv, FutilityImprovingDiv, SingularDepthDiv, LmrQuietBoostDiv, PvQuietBonusDiv, AspDeltaGrowDiv, LmpNotImprovingDiv, NoisyMoverDiv, CorrectionClampDiv, ContHistBack4Div (all min ≥ 1); one index — ImprovingLookback (stack_[4] bound, max 4); four score — QuietCheckBonus, PromoQueenScore, PromoUnderScore, NoisyValueWeight; six extension — DoubleExtLimit (it is the budget), DoubleExtPlies (max 2: at 3+ the counter of 2373 misses it), SingularExtPlies (max 2), SingularTtCutExt and SingularCutNodeExt (max 0), CheckExtPlies (max 2); three rule — TtNear50Clock (halfmove range), CuckooRepMinClock (K1), AspDeltaGrowAdd (min 1: the aspiration loop must strictly widen).

## (3) C-BOUNDS — both fail as required
Good spec: 59 rows OK (`bounds_check.txt`). Bad copy 1 (TtNear50Clock max 100): exit 1, names the row — "default+step 108 > max 100" (`cbounds/bad1/bounds_check.txt`). Bad copy 2 (ImprovingLookback max 8): exit 1, names the row — "index row max 8 above its bound stack_[4]" (`cbounds/bad2/bounds_check.txt`). The check is `make_from_spec.py --bounds-only`, reading only the spec.

## (4) The two patches and the reading guide
`census_r15d.patch.txt` (33 hunks) and `census_kF.patch.txt` (36 hunks), both verified to apply with `patch -p1 -F0 --dry-run` on fresh trees and both built (exe b96e8895… and ada06e37…; rebuilds reproduce the same hashes). The kF line: kF's near50/TT block carries the rule50-clock rework (`rule50_score_for_this_clock`, `WorkerTTProbe`, kF:2286-2293), so the diff CONTEXT around the TtNear50Clock sites differs from r15d — that is what job 35's hunk 12 hit; the three literal sites themselves are text-identical, and the kF patch is generated from the kF tree, so it applies clean. The kF patch has 3 more hunks than r15d's because kF duplicates the TT probe/store bodies: TtAgePenalty gets 4 sites (511,517,536,757) and TtStoreDepthSlack 4 (599,637,687,781) — the spec's r15d-line check is skipped for kF by construction. Reading guide: `reading_guide_v2.tsv`, 62 rows + header (v1 `reading_guide.tsv` had one row split by a literal newline in the multi-line evasion site; v2 escapes it; v1 stays). The registration rows (decls, table, externs) are rows 1-3; every changed place is in the table and the other way round (script-enforced).

## (5) K3, K4, K6, C-DEAD, C-LIVE
- K3 r15d: patO sum 8,315,168, 0 of 200 node diffs, 0 best-move diffs vs baseO; patG 17,611,204, 0 of 353 (`k3/patO.rows` vs `k3/baseO.rows`, `k3/patG.rows` vs `k3/baseG.rows`). K3 kF: patkFO 8,315,168, 0 of 200; patkFG 17,611,204, 0 of 353 (`k3/patkFO.rows`, `k3/patkFG.rows`). PASS on both trees.
- K4: all 26 O sums of file 35's K5 table reproduced to the node on the regenerated patch (`k4/k4_*.rows`, checked against the 26 known sums; `k4/` also holds the 26 opt files).
- K6 (three rows, O at depth 12, hand edit vs the option at the same value): (a) PromoUnderScore −4000: sums 8,315,247 = 8,315,247, 0 of 200 node diffs, 0 best-move diffs; (b) SingularTtCutExt −1: 8,893,327 = 8,893,327, 0/0; (c) TtStoreDepthSlack 3 (both sites): 8,630,133 = 8,630,133, 0/0 (`k6/hand{A,B,C}.rows` vs `k6/opt{A,B,C}.rows`). No literal site is unreached.
- C-DEAD (LmrDeeperBase 0): 0 of 200 O, 0 of 353 G differ, sums equal to base (`k3/cdeadO.rows`, `k3/cdeadG.rows`). C-LIVE (LmrCutNode 0): sum 8,304,696, 200 of 200 differ (`k3/cliveO.rows`). Both PASS.

## (6) The prediction, graded (`prediction.txt`, own commit "kimi5 job 37 prediction", before Step 4)
- ALIVE/DEAD: 17 of 20 right. Wrong: NoisyValueWeight and NoisyMoverDiv (called ALIVE, measured DEAD — 0 of 553 positions on all four runs each; the evasion noisy scores never move a node at depth 12) and CheckExtPlies (called ALIVE, measured NOT SEEN by the letter — its three completed cells are 0.90/1.20 on O and 0.75 on G, so the substance was right, the fourth cell is unfinished). TtAgePenalty DEAD as called.
- The five movers: LmrFullDepthMoves minus 0.8102 in [0.72, 0.92] RIGHT; SingularTtCutExt plus 1.0695 in [1.05, 1.09] RIGHT (and equal to K6(b)'s 1.0696 to the node); TtStoreDepthSlack minus 1.0379 in [1.02, 1.06] RIGHT (equal to K6(c)'s); LmpNotImprovingDiv minus 1.1927 NOT in [1.25, 1.80] (weaker); SingularExtPlies minus 0.7046 NOT in [0.88, 0.97] (far stronger — and plus is 2.0509 on O, 3.2526 on G: the single strongest knob of the 20).
- Best moves ≥ 50 of 200 on O on either side: 8 of the 20 new (LmpNotImprovingDiv, HistoryBonusOffset, CorrectionClampDiv, ContHistBack4Div, SingularExtPlies, SingularTtCutExt, LmrFullDepthMoves, CheckExtPlies), inside my [4, 9]. RIGHT.

## (7) Step 4's table (PC20, depth 12, Threads 1, Hash 16, ucinewgame+isready before each search; 4 parallel processes = core count)
Base: patched build at defaults, K3-proven (O 8,315,168 / G 17,611,204). chg = positions whose (depth,nodes) differ. Raw: `s4/*.rows` with `.meta`, `s4/*_input.log`, `s4/opt_*.txt`, `grading.tsv`, `classification.txt` (grader: `grade_step4.py`, prints what it reads). The one NA cell: CheckExtPlies p G — the engine ran to 24,087,600 nodes on position 3 (base there ~50k) and was killed at ~17 min CPU at 12:28; its raw files stay in `s4/` (`s4_CheckExtPlies_p_G_full.txt`, `_input.log`, `.log`).

The table itself is `step4_table.md` (sorted by positions changed; the extra row included):

| option | default | step | chg O m/p | chg G m/p | ratio O m/p | ratio G m/p | class |
|---|---|---|---|---|---|---|---|
| LmrFullDepthMoves | 1 | 1 | 200/200 | 353/353 | 0.8102/0.9934 | 0.8009/0.9917 | ALIVE |
| CorrectionClampDiv | 4 | 1 | 200/200 | 349/349 | 1.0116/0.9863 | 0.9436/1.0138 | ALIVE |
| LmpNotImprovingDiv | 2 | 1 | 200/200 | 349/348 | 1.1927/0.9897 | 1.0774/0.9527 | ALIVE |
| TtStoreDepthSlack | 4 | 1 | 199/200 | 349/349 | 1.0379/1.0004 | 0.9856/0.9846 | ALIVE |
| HistoryBonusOffset | 32 | 6 | 200/200 | 348/347 | 1.0078/1.0071 | 0.9816/0.9834 | ALIVE |
| ContHistBack4Div | 2 | 1 | 200/200 | 348/347 | 1.0004/1.0044 | 1.0162/0.9947 | ALIVE |
| SingularExtPlies | 1 | 1 | 200/200 | 347/347 | 0.7046/2.0509 | 0.5363/3.2526 | ALIVE |
| QuietCheckBonus | 12000 | 2400 | 199/198 | 346/344 | 1.0467/1.0215 | 1.0215/1.0242 | ALIVE |
| SingularCutNodeExt | -1 | 1 | 199/199 | 342/343 | 0.9724/1.0572 | 0.9823/1.0044 | ALIVE |
| SingularTtCutExt | -2 | 1 | 200/200 | 332/344 | 0.9773/1.0695 | 0.9959/1.0174 | ALIVE |
| CaptureValueWeight | 10 | 2 | 196/192 | 298/283 | 1.0170/1.0138 | 0.9877/0.9980 | ALIVE |
| CheckExtPlies | 1 | 1 | 200/200 | 351/NA | 0.9006/1.1981 | 0.7536/- | NOT SEEN |
| AspDeltaGrowAdd | 4 | 1 | 48/39 | 243/235 | 1.0186/1.0080 | 0.9976/0.9897 | ALIVE |
| ImprovingLookback (extra row) | 2 | 2 | -/200 | -/352 | -/1.0812 | -/1.0536 | ALIVE |
| LmrFullDepthMovesRoot | 1 | 1 | 14/161 | 35/261 | 1.0048/0.9850 | 0.9907/0.9865 | ALIVE |
| PromoQueenScore | 20000 | 4000 | 0/0 | 24/15 | 1.0000/1.0000 | 0.9958/0.9989 | ALIVE |
| PromoUnderScore | -5000 | 1000 | 2/14 | 7/8 | 1.0000/1.0000 | 0.9995/0.9996 | ALIVE |
| CorrectionWeightCap | 16 | 3 | 0/0 | 4/0 | 1.0000/1.0000 | 1.0000/1.0000 | ALIVE |
| TtAgePenalty | 4 | 1 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| NoisyValueWeight | 10 | 2 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| NoisyMoverDiv | 10 | 2 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |

The extra row (K2's one legal neighbour): ImprovingLookback 4 is ALIVE with a sign flip's worth of tree change — 200 of 200 O positions (ratio 1.0812, 57 best moves) and 352 of 353 G (1.0536, 101 best moves). No run of this job set a value outside its row's "bound by" (the run list is clamped by the generator; DoubleExtPlies is one-sided and was not re-run).

## (8) Step 5 — the speed of the options build
O at depth 12, one process at a time, five runs each in turn (plain, options, alternating), engine-REPORTED time (the `time` field of the last info line summed over the 200 positions; the rusage-based attempt is in `s5/time_*.txt` with a note — see "not sure"). Plain r15d: 4350, 4391, 4358, 4339, 4308 ms → median 4350, range [4308, 4391]. All-options build: 4413, 4413, 4377, 4405, 4382 → median 4405, range [4377, 4413]. Ratio of the medians: 1.0126 (about +1.3 %; the ranges touch). The PC measures its own. Raw: `s5/plain{1-5}_full.txt`, `s5/opts{1-5}_full.txt`, table `s5/speed_table.txt`.

## (9) The list for the next tune (`tune_list.tsv`, generated from the spec and Step 4's classification)
48 options are ALIVE and "yes": job 35's 32 (with RfpWorseningDrop carrying the tuner step 8 from the spec's header note) plus 16 of the 20 new. Left out, each with its reason in the file: the four gated rows (DEAD by gate under PC20), TtNear50Clock (DEAD at depth 12), CuckooRepMinClock (class R, K1), ImprovingLookback (K2: one match's question — its measured row is in the table above), TtAgePenalty / NoisyValueWeight / NoisyMoverDiv (DEAD at depth 12 on O and G), CheckExtPlies (one run unfinished; its three completed cells are strongly ALIVE).

## Step table
| step | done / partly / not done | evidence | result |
|---|---|---|---|
| 0 | done | step0/*.txt | 5 of 5 pins exact |
| 1 spec + script + bounds | done | options_spec.tsv, options_spec_v2.tsv, make_from_spec.py(_v2), bounds_check.txt | 59 rows, check OK |
| C-BOUNDS | done | cbounds/bad1,bad2/bounds_check.txt | both bad copies fail and name the row |
| 2 patches + guide | done | census_r15d.patch.txt (33), census_kF.patch.txt (36), reading_guide_v2.tsv (62) | apply -F0, build, hashes noted |
| 3 K3 | done | k3/base*,pat*,patkF* | 553/553 identical on both builds |
| 3 K4 | done | k4/ | 26/26 sums to the node |
| 3 K6 | done | k6/ | 3/3 hand-edit-equal on 200/200 |
| 3 C-DEAD/C-LIVE | done | k3/cdead*,clive* | 0 diffs; 8,304,696 with 200/200 |
| prediction | done | prediction.txt (own commit) | 17/20, 3/5 ranges, bm count inside |
| 4 | partly (81 of 82 cells) | s4/, grading.tsv, classification.txt, step4_table.md | 17 ALIVE, 3 DEAD, 1 NOT SEEN |
| 5 | done | s5/ | ratio of medians 1.0126 |
| tune list | done | tune_list.tsv | 48 in, 11 out with reasons |

## What this check cannot see (as the job writes it)
The PC's net (the built-in evaluation plays here); go nodes 20000 and soft nodes 2000; more than one thread; the PC's compiler; and strength: ALIVE only says a tune can reach the number. Whether any value gains is a tune and matches on the PC.

## From my colleagues
Read: deepseek5's NOTES (through job 30: the stage-label off-by-one fix and its corrected killer/countermove regret rates; the bare-process control proving the ucinewgame+isready discipline sufficient; the self-play runner of stand5) and its newest report t23 (go-mate pruning and stale TT scores near the fifty-move rule — reading, no bearing on this job's measurements). glmflash5-work still does not exist (fourth run noting this); glmflash4's newest is job 9 (the seven-switch bundle plus W1/W2: both lean negative; MateAlphaGuard absent from 6b98f217's option list — my spec's tree has it under PC20, which matches job 35's reading that it is compiled via -DFORGE_MATE_ALPHA_GUARD=1). Applied: the ucinewgame+isready-before-every-search discipline and the refusal scan live in runner_j37.py; deepseek5's "read the counter at the moment the event happens" is behind the line-level site verification in the generator. Checked: nothing in this job's numbers depends on their new results.

## What I did NOT do
The CheckExtPlies p G cell (killed runaway; raw files kept in s4/). K3 on kF compares the patched kF build against r15d's rows (job 28's kF == r15d bit-equality stands behind that; I did not re-run plain kF rows this job). Job 35's 39 old options were not re-measured (K4 re-proves the 13 K1 ones to the node; the rest stands on job 35's grading).

## What I am NOT sure about
1. Step 5's +1.3 %: engine-reported times, ranges touch; two rusage-based attempts (bash `time`, python `resource`) returned ~0.07 s on most runs against ~4.7 s on a few — an accounting artifact I did not explain (the searches provably ran: .meta windows and full logs). The engine's own `time` sums are the numbers above.
2. PromoQueenScore, PromoUnderScore, CorrectionWeightCap are ALIVE by the letter (2-24 G positions) with O sums exactly base — a depth-12 tune may not reach them on O-heavy openings.
3. Whether the three DEAD options are dead everywhere or only at this depth/table-pressure (job 38's file notes how empty the table stays at these search sizes; TtAgePenalty may wake at longer searches).
4. CheckExtPlies 2's explosion (24M nodes on G position 3) is legal under my bound (the counter of 2373 caps stacking at 6 per path) but makes the plus side practically untestable at depth 12 there — whether that caps its tuner range in practice is the PC's call.

## A better way
1. A per-cell node cap for liveness runs (abort a search at, say, 10× the base position nodes and mark the cell "exploded"): the CheckExtPlies p G cell would have been recorded as ALIVE-by-explosion in ~30 s instead of hanging the batch for 17 minutes; checkable by running the same cap on the base build (no cell may trip it).
2. The bounds check machine-verifies divisor and index rows but only requires prose for score rows; it could carry a numeric band column (e.g. QuietCheckBonus max 926272 derived from HistoryMax×tables) so that a planted over-band score row fails C-BOUNDS the way the two current controls do — worth it if a third score-class option family appears.

## Times (stamps.txt's own lines)
```
2026-11-20T12:04:44Z step1 spec committed
2026-11-20T12:06:25Z step2 committed (spec v2, generator, 33-hunk r15d patch, 36-hunk kF patch, guide 62 rows, runlist 41)
2026-11-20T12:07:32Z step3 K3+C-DEAD+C-LIVE committed
2026-11-20T12:08:58Z prediction committed
2026-11-20T12:28:53Z step4 committed (CheckExtPlies p G unfinished: runaway killed)
2026-11-20T12:31:30Z step5+tune list committed
```
(run claimed 12:01:07 UTC; Step 0 ran 12:02:25 UTC.)

## Model
Kimi K3.

`git status --short` (empty) and `ls -R forge-combo29/kimi5/job37` were run as the last command before this report's commit; the folder holds: bounds_check.txt, cbounds/, census_kF.patch.txt, census_r15d.patch.txt, classification.txt, grade_step4.py, grading.tsv, k3/, k4/, k6/, make_from_spec.py, make_from_spec_v2.py, options_spec.tsv, options_spec_v2.tsv, prediction.txt, reading_guide.tsv, reading_guide_v2.tsv, runlist.tsv, runner_j37.py, s4/, s5/, stamps.txt, step0/, step4_run.sh, step4_table.md, tune_list.tsv.

## Questions for Fable
1. CheckExtPlies p on G: re-run that one cell with a node cap (better way 1) in a later job, or accept the three cells?
2. Is the kF patch's extra TT duplication (4 age sites, 4 store sites) intended to stay as one option covering both copies, or should the worker/owned probe paths get separate knobs?
