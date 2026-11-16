# kimi5 job 12 report — FailHighBlend: fail-high values blended with beta at three places, one switch with three bits

Step 0, I1, I2: MET. Patched build, no option: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609 (bench 16 = 3,024,920 also met); `uci` lists `FailHighBlend` default 0 min 0 max 7. I1 = 12,573,318 (O) / 22,128,265 (G), I2 = 9,500,069 (O) / 18,466,239 (G); per-position nodes equal the job-8 rows on 200 of 200 and 353 of 353, nodes AND best moves equal the job-10 K rows (best moves do not exist in the job-8 rows; job 11 proved the job-10 K rows node-identical to job 8).
Step 2 (counting build, O under S14, 200 searches summed per run): FHB 0: every count 0 at every place and the node sum 9,500,069 (the counters change nothing). FHB 1: A = 1,965,016 at reverse futility only. FHB 2: A = 1,815,929 stand pat + 734,301 quiescence end only. FHB 4: A = 1,444,832 main search end only. FHB 7: A above 0 at all four places (1,959,912 / 1,777,673 / 711,666 / 1,529,966). In every run L = R = M = 0. Positive control (scratch plant: bit 1 returns `beta - 1`): L at reverse futility = 15,490,054 = A exactly.
Step 3 (plain patched build, ratio to I2, bootstrap 95 % over positions, 2,000 resamples, seed 12): on O — T1 0.9761 [0.9265, 1.0278] 55 best moves changed of 200; T2 1.0084 [0.9568, 1.0691] 58; T4 0.9664 [0.9172, 1.0155] 46; T7 0.9965 [0.9477, 1.0497] 57. On G — T1 0.9878 [0.9413, 1.0368] 83 of 353; T2 0.9854 [0.9388, 1.0358] 87; T4 0.9707 [0.9252, 1.0204] 81; T7 0.9495 [0.9080, 0.9958] 99. No strength claim (the job asks for trees only).

## The patch
`tests_kimi5_job12/FailHighBlend.patch.txt`, sha256 8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a,
a unified diff against 6b98f217 (`diff -ruN` of the pristine tree against the edited tree), applies with
`patch -p1` without fuzz (a `--dry-run` and a real application both clean). One new option `FailHighBlend`
0..7 default 0; bit 1 reverse futility, bit 2 quiescence (stand pat + end), bit 4 main search end, exactly the
lines the job names. The counting patch `FailHighBlendCheck.patch.txt` (on top of the first, active only with
`-DFORGE_FHB_CHECK=1`), sha256 9fedd284596112bcbc5c4a70fb0707c344ddcfd1418fb66604280bfc4603d659.

## Answers (a) to (c) from the code (checked before building)
(a) Every blended value lies in [beta, raw]. Bit 1: `beta + (eval - beta) / 3`; the guard (search.cpp:1689-1690)
gives `eval - margin >= beta` with margin > 0 at the defaults and S14 (6*depth - 6*improving >= 0), so
`eval >= beta`; `eval - beta >= 0` truncates down, result in [beta, eval]. (An extreme tuning could make the
margin negative; then eval < beta is possible and the value lies in [eval, beta] — still between the two.)
Bits 2 and 4 re-test `best_score >= beta` at the blend, so raw >= beta there by construction. `(a + b) / 2` and
`(a*depth + beta) / (depth + 1)` are weighted means of beta and raw; C++ integer division truncates toward
zero, which moves the mean toward 0 by less than 1 and can never cross an endpoint: for same-sign endpoints
floor/ceil stay inside the interval, for mixed signs the truncation moves toward 0, which lies between them.
(b) `best_score * depth` cannot overflow: the blend's guard requires `!is_mate_score(best_score)`, so
|best_score| <= 31,871 (MateInMaxPly = 32,000 - 128, search.hpp:71-78); the root depth is clamped to
[1, 64] (search.cpp:2219) and extensions add at most one per ply with ply <= 128, so depth <= 192 worst case;
|best_score * depth| <= 31,871 * 192 = 6.12M, plus |beta| <= 32,001 — six orders of magnitude below INT_MAX.
(c) `beta` at 2092 CAN be a mate score while `best_score` is not — whenever a parent that already holds a mate
score calls a child with `beta = -MateInMaxPly` (mate scores propagate negated through null-window calls). Then
`best_score >= beta` is true for almost every real score and `!is_mate_score(best_score)` is true too, so only
the `!is_mate_score(beta)` test blocks blending a genuine score toward a mated bound. (For positive mate beta
the `>=` and best-score tests already block; the beta guard is the sole blocker exactly in the negative-mate
case.) The guard then keeps the raw fail-high value, which is what the correction history and the TT store
expect today.

## Step table
| step | done / partly / not done | evidence files | result |
|---|---|---|---|
| 0 pins | done | step0_bench11.txt, step0_bench13.txt, step0_bench16.txt, step0_perft5.txt, step0_uci.txt, exe_sha256.txt | all four numbers met; option listed with default 0 |
| patch | done | FailHighBlend.patch.txt (+sha256), applies `patch -p1` clean | builds, identities hold |
| prediction | done | prediction.txt (own commit before Step 1) | mostly KILLED, see below |
| Step 1 identities | done | rows/i1_*,i2_* .json(+meta,input.log); compare_i.txt | I1: 200/200 (O), 353/353 (G) nodes equal job-8; I2: same; nodes AND best moves equal job-10 K rows 200/200, 200/200, 353/353, 353/353 |
| Step 2 counters | done | FailHighBlendCheck.patch.txt, rows/c_fhb* , counter_sums.txt, sum_fhb.py | every wiring and bound requirement met (above) |
| positive control | done | rows/ctrl_plant_fhb1_O_d12*, ctrl_plant_sum.txt (plant itself in /tmp, never committed) | L == A == 15,490,054 at rfp exactly |
| Step 3 trees | done | rows/t[1247]_* , boot_trees.txt, boot_j12.py | table above |

## Findings (each with file:line in 6b98f217 and the command that shows it again)
1. The four blend sites are exactly where the job file says: reverse futility `return eval;` search.cpp:1691;
   stand pat `if (best_score >= beta) {` :1474; quiescence end bound line :1539; main search end bound :2092,
   correction history :2102-2106. `grep -n "return eval;" forge-combo29/src/search.cpp` etc.
2. Blend-event rates under S14 on O (counting build, per search averages): reverse futility ~9,825 fail-high
   returns; stand pat ~9,080; quiescence end ~3,672; main-search non-PV fail-high ~7,224. Every applied blend
   stayed inside [beta, raw] and off mate scores (L = R = M = 0 over ~41M events across the five runs).
3. The blends MOVE the tree in both directions per position and slightly SHRINK it in sum (all four O ratios
   below or astride 1; on G, T7 is one-sided below 1: 0.9495 [0.9080, 0.9958]). Node-count effects only; no
   strength claim.
4. Prediction KILLED in its direction: I wrote "more nodes, never fewer" (ratios 1.005/1.03/1.02/1.055);
   measured 0.9761/1.0084/0.9664/0.9965 on O — T1, T4, T7 outside their kill ranges, T2 alone inside. The
   "weaker lower bound → fewer TT cutoffs → more nodes" argument misses the net effect; the measured sums say
   the opposite, slightly. "T2 changes the most best moves" held on O (58, vs 57 T7) but not on G (T7 99);
   "T1 fewest" failed (T4 fewest on both sets).
5. Build-level cross-check for free: the counting runs reproduce the plain build's sums to the node
   (c_fhb1 = t1 = 9,272,824; c_fhb2 = t2 = 9,580,168; c_fhb4 = t4 = 9,180,831; c_fhb7 = t7 = 9,466,559),
   a second proof (besides FHB 0 = 9,500,069) that the counters change nothing.

### Suspicions, not proven
- The per-position variance of the ratios is large (every interval ~0.09-0.10 wide); the G-set T7 interval
  being one-sided could still be set composition (G is more tactical) rather than a real interaction of the
  three bits. A second seed or a depth-14 run would say.

## From my colleagues
- deepseek5 (branch for-fable-and-opus/deepseek5-work, newest report job 30): the stage-label fix (read a state
  variable at the moment the event happens) — applied to my counter design: fhbc::note is called at the blend,
  with the values before the assignment. Its job-30 killer/counter-move rates noted for future history work.
- glmflash5 (its work branch is cursor/glmflash5-work-cb5c; the name in my instructions,
  for-fable-and-opus/glmflash5-work, does not exist — noted once here): newest report job 22. Seed-inertness
  under sequential+fixed-nodes, and its cross-3 confirmation of my job-10 QSTEPS on its own build. Nothing of
  mine this job depended on a second seed, so no change.
- File 13's corrections held: .gitignore written before the first `git add`; every control's node sum compared
  with the base run before reading its rates (the FHB 0 run: 9,500,069 = I2).

## What I did NOT do
- No match / Elo (the job says trees only, "no strength claim").
- The plant build and both build trees stay in /tmp (never committed); only the two patch texts are committed.
- Job 13 not touched (next run).

## What I am NOT sure about
- Why the sums shrink slightly instead of growing (my prediction's mechanism is dead; I report the numbers
  without a replacement story).
- Whether the beta-guard's negative-mate case (answer c) ever fires in these sets — M = 0 everywhere says it
  did not fire here at all.

## A better way
The counting patch pattern (job 10's and this job's) re-derives the same harness per job: a counters block, a
reset hook, a print hook. A single shared `FORGE_COUNTERS` frame patch (hooks only, counters registered by
name) would make every future counting job a one-array diff and every cross-check (like glmflash5's 15-minute
re-derivations) a re-run of the same binary flags. Checkable: build the frame with a null counter set; bench
pins and the I1/I2 sums must hold, exactly as the FHB 0 run did here.

times: see stamps.txt

Model: Kimi K3 (the runtime's own name for this session).
