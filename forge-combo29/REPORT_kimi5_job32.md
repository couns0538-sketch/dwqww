# kimi5 job 32 report — the look-alikes' conditions in other tuned settings; the flat map at go nodes 20000

Three plain lines: Asked: split the job-29 history-prune counter into eight classes (lmr_depth 0/1/2/3+ ×
outside/in check) plus largest move numbers at depths 1-3, confirm K1/K2/K3 (where lmr_depth 0 can first
appear at the HP test), the three pair-equalities at the three boundary settings, and the flat map of ten
depth-gated settings at the tune's own 20,000-node limit. Answer: K1, K2, K3 all CONFIRMED to the class;
at all three boundary settings 0 of 3 pairs are equal (hpd0 fires wherever an lmr_depth-0 class exists);
at go nodes 20000 the G set has five searches completing iteration 64, so NO depth-gated setting has a
provable in-range flat stretch on G, while on O every bound held and every bound-1 was flat too (wider
than proven). How sure: certain on the class numbers (two independent counters in the same files agree,
and the class build is row-identical to the plain build); the Step-4 bounds are arithmetic on measured
maxima, the checks are measured rows.

## (1) Step 0
8 of 8 pins met on the plain PC build (6b98f217 + pc_r15.patch sha256 d6bd72c5…, guard via
-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1, g++ 13.3 Release; exe step0/exe.sha256 = 068f0927…, the
same binary as job 29's plain build). Raw files: step0/none_bench11.txt 312866, none_bench13.txt 862329,
none_bench16.txt 3024920, none_perft5.txt 4865609, s14_bench11.txt 242796, s14_bench13.txt 656517,
pc20_bench11.txt 278024, pc20_bench13.txt 587276; a fresh process per line (step0/*_input.log).

## (2) Known answer A — MET in full (run_kaA.sh, kaA/)
- Class build (ran_classes.patch.txt on a scratch copy of the job-29 tree; applies `patch -p1 -F0`,
  verified on a second scratch copy: PATCH_F0_OK + trees equal; exe sha256 17067935…) rows equal the
  plain build's: O d12 sum 8,315,168 and G d12 sum 17,611,204, per-position nodes and best moves equal
  the committed job-29 plain rows (rows/base_*_d12.json); at go nodes 20000 both builds give equal rows
  on O (sum 3,055,154) and G (5,196,158).
- The eight classes add up to job 29's HP: O reached 4,775,611 / fired 11,208; G 9,106,192 / 43,280;
  the still-present RAN HP counter in the same files sums to the same numbers.

## (3) The prediction, graded row by row (rule: a count survives within [g/10, g·10]; a 0 only as 0)
Step 3, cls0 (outside check, lmr_depth 0) reached, O | G:
| run | predicted | measured | verdict |
|---|---|---|---|
| base | 0 | 0 (KA-A-fixed, stated as such) | ✓ |
| LmrQuietBase 99 | 0 | 0 | ✓ |
| LmrQuietBase 100 | 5·10⁵ | 10⁶ | 994,718 | 1,407,700 | ✓ ✓ |
| LmrQuietDivisor 161 | 0 | 0 | ✓ |
| LmrQuietDivisor 160 | 10³ | 3·10³ | 23,031 | 46,831 | ✗ ✗ (23× / 16× too small) |
| LmpBase 19 | 0 | 0 | ✓ |
| LmpBase 20 | 10² | 10² | 23,054 | 32,981 | ✗ ✗ (~230× / ~330× too small) |
| LmrQuietBase 300 (K3) | 2·10⁶ | 4·10⁶ | 1,425,718 | 2,447,477 | ✓ ✓ |
Zeros: 6 of 6 exact. Magnitudes: 4 of 8.
Pairs (equal = same per-position nodes+best moves over 553): predicted lqb100 0-of-3 — measured 0-of-3
(49 | 8 | 8) ✓; predicted lqd160 1-of-3 — measured 0-of-3 (422 | 14 | 14) ✗; predicted lmp20 1-of-3 —
measured 0-of-3 (298 | 54 | 53) ✗. Pairs: 1 of 3. Both misses are the same wrong call "hpd0 fires 0 on a
small lmr0 population": hpd0 fired 55|645 (lqd160) and 580|1,947 (lmp20).
Step 4 DMAX at go nodes 20000: predicted O median 12 / max 14 — measured 11 / 14 ✓ ✓; G median 12 /
max 16 — measured 11 / 64 ✓ ✓ (64 ∈ [1.6, 160]). Step 4: 4 of 4.

## (4) Step 3 — one row per run (agg_step3.py → step3_table.txt; runs in rows3/, base = the KA-A runs)
Columns: run set nodes_sum eq_vs_base cls0_r cls0_f cls4_r cls4_f movmax_d1 d2 d3 fired_classes
```
base O 8315168 200/200 0 0 0 0 13 12 17 [1,2,3,5,6,7]
base G 17611204 353/353 0 0 0 0 10 12 17 [1,2,3,5,6,7]
lqb99 O 7882681 0/200 0 0 0 0 13 13 17 [1,2,3,5,6,7]
lqb99 G 16894136 4/353 0 0 0 0 11 12 17 [1,2,3,5,6,7]
lqb100 O 8225288 0/200 994718 5098 10542 2239 13 13 17 [0,1,2,3,4,5,6,7]
lqb100 G 16329401 3/353 1407700 15187 42570 6285 11 12 17 [0,1,2,3,4,5,6,7]
lqd161 O 6567547 0/200 0 0 2 0 14 13 17 [1,2,3,5,6,7]
lqd161 G 14048350 0/353 0 0 0 0 11 12 17 [1,2,3,5,6,7]
lqd160 O 6640733 0/200 23031 56 3 0 13 13 17 [0,1,2,3,5,6,7]
lqd160 G 13767141 0/353 46831 687 0 0 14 14 17 [0,1,2,3,5,6,7]
lmp19 O 9447305 0/200 0 0 0 0 20 23 28 [1,2,3,5,6,7]
lmp19 G 19622434 2/353 0 0 0 0 20 23 28 [1,2,3,5,6,7]
lmp20 O 9466078 0/200 23054 523 0 0 21 24 29 [0,1,2,3,5,6,7]
lmp20 G 19413121 2/353 32981 2321 0 0 21 24 29 [0,1,2,3,5,6,7]
lqb300 O 3481944 0/200 1425718 1498 30052 1278 13 12 17 [0,1,4,5]
lqb300 G 7455597 0/353 2447477 6738 115598 5128 10 12 17 [0,1,2,3,4,5,6,7]
lqb100_hpd0 O 8234079 0/200 997049 5074 10454 2151 13 13 17 [0,4]
lqb100_hpd0 G 16455530 3/353 1426281 16007 43166 6615 11 12 17 [0,4]
lqb100_hpm20000 O 8043692 0/200 977634 0 10244 0 13 13 17 []
lqb100_hpm20000 G 16287513 3/353 1380848 1 42599 0 11 15 17 [0]
lqb100_hpboth0 O 8189908 0/200 1011328 69205 10378 6049 13 13 17 [0,4]
lqb100_hpboth0 G 16607243 3/353 1434388 140963 47087 20629 11 12 17 [0,4]
lqd160_hpd0 O 6679053 0/200 22981 55 4 1 13 13 17 [0,4]
lqd160_hpd0 G 13963670 0/353 47952 645 0 0 14 14 17 [0]
lqd160_hpm20000 O 6679104 0/200 22981 0 4 0 13 13 17 []
lqd160_hpm20000 G 13953150 0/353 47905 0 0 0 14 14 17 []
lqd160_hpboth0 O 6603586 0/200 23012 10669 3 3 13 13 17 [0,4]
lqd160_hpboth0 G 13727463 0/353 47255 24896 0 0 14 14 17 [0]
lmp20_hpd0 O 9557407 0/200 23090 580 0 0 21 24 29 [0]
lmp20_hpd0 G 19529236 2/353 32236 1947 0 0 21 24 29 [0]
lmp20_hpm20000 O 9570979 0/200 23101 0 0 0 21 24 29 []
lmp20_hpm20000 G 19497406 2/353 32059 0 0 0 21 24 29 []
lmp20_hpboth0 O 9345869 0/200 22735 21126 0 0 21 24 29 [0]
lmp20_hpboth0 G 19670099 2/353 31823 29474 0 0 21 24 29 [0]
```
The three pairs (equal rows of 553, O+G): lqb100: 49 | 8 | 8 → 0 of 3. lqd160: 422 | 14 | 14 → 0 of 3.
lmp20: 298 | 54 | 53 → 0 of 3. Classes that fired: see the fired_classes column; hpd0 fires in exactly
the classes that have an lmr0 class (0 outside, 4 in check); hpm20000 fires 0 everywhere except once
(lqb100 G cls0 fired 1); hpboth0 fires the most (threshold 0).
K1 CONFIRMED: base cls0 = 0 | 0 (and cls4 = 0 | 0). K2 CONFIRMED to the letter: 0 at 99, 161, 19;
nonzero at 100 (MUST: 994,718 | 1,407,700), at 160 (23,031 | 46,831), at 20 (23,054 | 32,981).
K3 CONFIRMED: at 300 the lmr0 class is the dominant one at depths 1-3 (1.43M | 2.45M; fired classes
collapse to [0,1,4,5] on O).
No refusal line (`unknown option` / `invalid value`) in any run; the runner stops on one and none
stopped. Options proven to arrive, e.g. rows3/lqb100_O_d12_input.log lines 5-6 `setoption name
LmrQuietBase value 100` / `value 205` (23 setoptions, no refusal).

## (5) Step 4 — the flat map at go nodes 20000 (agg_step4.py → step4_table.txt; runs in rows4/)
DMAX table (class build, base opts; per search DMAX = largest remaining depth at any node; last_iter =
last completed iteration):
| set | last_iter min / median / max | DMAX min / median / max |
| O | 8 / 10 / 13 | 9 / 11 / 14 |
| G | 8 / 10 / 64 | 9 / 11 / 64 |
The 64s are five real searches (G positions 59, 133, 168, 276, 306; 1,264-16,875 nodes: forced lines,
e.g. `5Q2/2k5/8/4KB2/7P/4R3/8/8 w - - 0 1` at 6,620 nodes) — raw lines in kaA/cls_G_n20000_full.txt.
One row per setting (gates verified at the PC-tree lines; bound_O from O's d_max 14, bound_G from G's 64;
T = top of the tuned range; checks are equal-row counts O / G / 553):
| setting | gate (line) | bound O | bound G | T | T==B (O/G/553) | B==Bm (O/G/553) | reading |
|---|---|---|---|---|---|---|---|
| NullMoveMinDepth | depth >= X (1943) | 15 | 65 | 10 | no run: bound above the range on both sets | no run | empty in range |
| RfpDepth | depth <= X (1937) | 14 | 64 | 15 | 200 / 352 / 552 | 200 / 351 / 551 | holds on O; not on G; O-WIDER |
| RazorDepth | depth <= X (1926) | 14 | 64 | 6 | no run: bound above the range on both sets | no run | empty in range |
| FutilityDepth | lmr_depth <= X (2132) | 14 | 64 | 15 | 200 / 353 / 553 | 200 / 352 / 552 | holds on O and G; G wider than provable; O-WIDER |
| HistoryPruneDepth | lmr_depth <= X (2143) | 14 | 64 | 10 | no run: bound above the range on both sets | no run | empty in range |
| SingularDepth | depth >= X (2192) | 15 | 65 | 20 | 200 / 344 / 544 | 200 / 341 / 541 | holds on O; G differs on 9; O-WIDER |
| IirDepth | depth >= X (2033) | 15 | 65 | 20 | 200 / 353 / 553 | 200 / 351 / 551 | holds on O and G; G wider than provable; O-WIDER |
| ProbcutDepth | depth >= X (1996) | 15 | 65 | 20 | 200 / 353 / 553 | 200 / 352 / 552 | holds on O and G; G wider than provable; O-WIDER |
| CheckExtensionDepth | gives_check && depth >= X (2218) | 15 | 65 | 30 | 200 / 345 / 545 | 200 / 344 / 544 | holds on O; G differs on 8; O-WIDER |
| HistoryBonusMax | min(X, 24d²+54d-32) (324) | raw(14) = 5428 | raw(64) = 101,728 | 10000 | 200 / 350 / 550 | 200 / 353 / 553 | holds on O; G differs on 3; wider on BOTH (Bm flat) |
By the job's check criterion (bound and top equal on 553 of 553 AND the value just below differing on at
least one position), NO setting has its stretch confirmed on the combined sets: on O the first half holds
for all seven run settings but the second half fails for all seven (every bound-1 is flat too — the O
stretches are WIDER than the DMAX reading proves: the gates' other conditions bite before the depth
bound); on G the first half fails for RfpDepth (1), SingularDepth (9), CheckExtensionDepth (8),
HistoryBonusMax (3) — as the 64-deep searches predict — while FutilityDepth, IirDepth, ProbcutDepth are
flat across the whole remaining range [15..top] anyway (wider than provable from DMAX).

## Step table
| step | status | evidence | result |
|---|---|---|---|
| Step 0 | done | step0/ | 8/8 pins |
| Step 2 class patch | done | ran_classes.patch.txt (-F0 verified) | counters added; no search value touched |
| Known answer A | done | run_kaA.sh, kaA/ | MET in full |
| Prediction | done | prediction.txt (own commit, before Step 3) | zeros 6/6, magnitudes 4/8, pairs 1/3, DMAX 4/4 |
| Step 3 | done | run_step3.sh, rows3/, step3_table.txt | K1/K2/K3 confirmed; 0-of-3 pairs ×3 |
| Step 4 | done | run_step4.sh, rows4/, step4_table.txt | DMAX map; 10 setting rows; G poisoned by depth-64 searches |

## Findings (PC tree = 6b98f217 + pc_r15; line numbers in src/search.cpp of that tree)
1. K1/K2/K3 confirmed by measurement; the mechanism lines: the reduction table fills with
   `uint8(max(0, LmrQuietBase/100.0 + ln d·ln m / (LmrQuietDivisor/100.0)))` (300-311), `reduction()`
   caps at 63 (313-317), `lmr_depth = max(0, depth - reduction(quiet, depth, move_count))` (2122),
   `++move_count` before the test (2078), `lmp_threshold` = base + d·d, halved when not improving
   (319-321), the HP test `lmr_depth <= HistoryPruneDepth && history < threshold` (2143, threshold
   2128-2130). Reproduce: any row of step3_table.txt via run_step3.sh + agg_step3.py.
2. At LmrQuietDivisor 161 the OUTSIDE-check class stays 0 (K2) but the IN-CHECK lmr0 class appears
   (cls4 reached 2 on O): in check the picker hands out all evasions, so move 13 at depth 2 occurs and
   r(2,13) = uint8(0.93 + ln2·ln13/1.61) = uint8(2.034) = 2, while move 12 gives uint8(1.9999) = 1.
3. The job-29 pair mechanism ("all three configs fire 0 ⇒ equal trees") does NOT transfer to settings
   with an lmr0 class: hpd0 fires wherever cls0 > 0 (55-16,007 times), hpboth0 fires more (threshold 0:
   3-140,963), hpm20000 fires ~0 but not absolutely (once: lqb100 G). Hence 0-of-3 pairs at all three
   boundary settings. The fires are what breaks equality (compare hpd0 vs hpm20000 fired columns).
4. hpboth0 at lqb100 fires 69,205 | 140,963 at cls0 alone — at depth-1 quiets, history < 0 is common
   (the job-29 hpm0 population, now read by class).
5. movmax tracks `lmp_threshold(depth, improving)` exactly (base d2 12 = 8+4, d3 17 = 8+9; lmp19
   20/23/28; lmp20 21/24/29 — "the move that reaches the threshold is still searched"), with higher d1
   values (10-14) only via the in-check evasion path.
6. Job-29 erratum, proven: its report's "on G at most 13" is wrong — the committed job-29 file
   tests_kimi5_job29/kaA/cntbase_G_d12_full.txt itself contains three `RAN DMAX 15` searches (sum 4277
   on both builds); this job's cls_G_d12_full.txt lines 466, 3070, 9174 show the same three. The
   per-search SUM (job-29 note: "a max printed as a sum hides the answer") allowed the misreading;
   per-search lines fix it.
7. At go nodes 20000 on G, five searches complete iteration 64 (the engine's cap; 1,264-16,875 nodes,
   forced lines). Consequence: on G every depth-gated setting is live through its whole tuned range —
   no provable flat stretch; measured anyway: IirDepth, ProbcutDepth, FutilityDepth flat [15..top],
   RfpDepth (1 position), SingularDepth (9), CheckExtensionDepth (8), HistoryBonusMax (3) not flat.
8. On O at 20,000 nodes every measured bound (RfpDepth 14, FutilityDepth 14, SingularDepth 15,
   IirDepth 15, ProbcutDepth 15, CheckExtensionDepth 15, HistoryBonusMax 5428) held (top == bound on
   200/200), and every bound-1 was ALSO flat on 200/200: on these positions the flat stretches are
   wider than DMAX proves — the gates' other conditions (eval margins, tt_move, gives_check, the cap's
   exact raw(d)) move the real edge.
Parallel processes: 4 (xargs -P4), the VM's core count (nproc = 4).

### Suspicions, not proven
- The five iteration-64 G searches are mates or forced wins by their fens; their one-line trees are why
  they complete 64 iterations inside 20,000 nodes (no score quoted).
- cls0 at lqd160 / lmp20 consists almost entirely of the boundary moves (12th / 24th quiet at depth 2);
  the class counter does not split by move number, so this is inferred from K2's arithmetic + movmax,
  not split-counted.
- hpm20000's single G fire at lqb100 is a genuinely deep-negative history (< -15000·d), not a corner
  artifact; not individually verified.

## From my colleagues
- deepseek5 (731fc808): NOTES_deepseek5.md through "after job 30" and its newest report (REPORT_t23.md,
  the `go mate N` / fifty-move TT faults). Applied: its rule "read a state variable at the moment the
  event happens" — the class counters read lmr_depth, in_check and move_count at the HP line itself
  (2122-2143), and movmax is taken at the test, not reconstructed. Its Killer1/CounterMove stage rates
  do not touch this job. Checked: nothing of mine depends on its t23 tree (different branch).
- glmflash5: `for-fable-and-opus/glmflash5-work` is STILL absent (fourth run noting this); its tool's
  branch `cursor/glmflash5-work-cb5c` (dbc350a0) exists and its notes were read (match pools; the pv1
  gains; the fastchess TT-reuse question). Nothing in job 32 uses match data; its TT-pollution question
  is orthogonal here — every run of this job is one fresh process per setting with ucinewgame between
  searches, and all equalities are within-process.
- Applied from my own job-29 notes: per-search extrema as their own line (HPMOVMAX, per-search DMAX) —
  this is what caught finding 6; and "predict the empty firing set" — the two lost pair cells came from
  not applying it to hpd0 on small populations (rule now in NOTES_kimi5.md).

## What I did NOT do
- No runs for NullMoveMinDepth, RazorDepth, HistoryPruneDepth: their bounds (15/65, 14/64, 14/64) are
  above the range tops (10/6/10) on both sets, so the bound-vs-top check is not runnable inside the
  range; the reading lines are given instead.
- The 553 figure is O's 200 + G's 353 from two runs summed per comparison; no single 553-position file
  was built (equivalent; stated).
- No games, no second-machine reproduction, no PC net (per the job's own limits).

## What I am NOT sure about
- Whether the G-side T≠B differences come ONLY from the five 64-deep searches or also from searches at
  depths 15-33 (IirDepth/ProbcutDepth/FutilityDepth staying flat suggests position identity matters;
  not proven which searches moved the 1/9/8/3 differing rows).
- The exact depth split inside cls0 at lqd160/lmp20 (see suspicion 2).
- Whether "iteration 64" is a hard engine cap or a search-termination coincidence (not read; the five
  searches stop at exactly 64).

## A better way
- One outlier poisons every DMAX bound. A per-search bound (exclude the forced-line searches, bound
  over the rest — here G-without-5 would give ~17, like O's 15) plus one "outlier-aware" check (bound
  vs top compared on the non-outlier positions only, with the outliers listed) would keep the proof
  honest where a proof is possible. Cheaper still: state the flat map at the tune's MEDIAN completed
  iteration (10-11 here) instead of its limit — the tune lives at the median; the tail is already
  measured by the per-search DMAX lines the class build prints.
- Prediction rule the data now gives (for me and the pair-equality jobs): any lmr_depth-0 population of
  ≥ ~10³ reached tests contains a history below -3330, so hpd0 fires and no pair with hpm20000 is
  equal; only a proven-empty class saves an equality.

## What this check cannot see (as the job asks, verbatim)
The PC's net (with it, searches at 20,000 nodes reach other depths, so the PC measures its own bounds
before it uses any), other values of the other settings than the ones named here, more than one thread,
games (O and G are single positions with a fresh table).

## Times, model, last commands
times: see stamps.txt. Model name (as my runtime gives it): Kimi K3.
`git status --short` and `ls -R` of the job folder: final_ls.txt (the last command before this commit).
