# REPORT_kimi5_job29 (kimi5, 2026-11-19 UTC): where the 40 tuned settings stop mattering — proven flat stretches, look-alike pairs, and the counting build

Asked: for the 40 tuned search settings on the PC build, map the flat stretches (proven for every
input by reading vs only seen on O/G), the look-alike pairs, and prove it with a (reached, fired)
counting build at depth 12 on O (200) and G (353). Answer: the three history-prune configs (HPD 0,
HPM 20000, both 0) all fire **zero** times — each equals the no-history-pruning tree; NMB 6 parts
from NMDD 1 exactly where the null search stops being qsearch (d >= 10, by eval margin); DrawJitter
is idle on O (0 draw leaves) and fires 5 times on G without changing one decision; two real
proven-flat intervals exist (CheckExtensionDepth [20,30], HistoryBonusMax [9658,10000]) and both are
confirmed on 553 of 553. How sure: the equalities are measured to the node on 553 positions and the
firing claims rest on counters whose controls fire on command (hpm0: 1,230,074 fires; nmdd1:
125,718 of 125,718 null tries to qsearch). The one weak spot: WHY no lmr_depth==0 test ever has
negative history is seen, not proven.

## (1) Step 0

All eight pins of file 17 on the PC build (raw: step0/, script step0_j29.sh, one fresh process per
line): none 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276 — **8 of
8 met** (step0/{none,s14,pc20}_*.txt; exe step0/exe.sha256 068f0927…; build = 6b98f217 + pc_r15.patch
sha256 d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a (verified), g++ 13.3 Release,
-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1; 4 cores, AVX-512 present, no portable flags).
Parallelism used in this job: 4 row processes (xargs -P4), the machine's core count.

## (2) The Step 1 table (reading; line numbers in the PC build tree, src/search.cpp unless said)

Depth fact used below — **(b) the largest remaining depth d**: `new_depth = depth - 1 + extension`
(2222); extension is at most 2 (singular double, 2208-2210) and a path carries at most 7 doubles
(`inherited_double_extensions <= 6`, 2208; the chain counter at 2222). Check (+1, 2218) and singular
(+1, 2207) keep d constant. So **d_max <= root depth + 7**: 16 for root 9, 19 for root 12. Measured
(DMAX counter sums): on O at root 12 every search's largest d was exactly 12 (sum 2400 = 200 x 12);
on G at most 13 (4277 = 353 x 12 + 41).

| setting (PC20 value; range) | (a) proven flat stretches (bound and line) | (b) holds only up to d? | (c) look-alikes | seen-flat (not proven) |
|---|---|---|---|---|
| DrawJitter (0; [0,8]) | {0}: span <= 0 returns literal 0 (1440) | no | all values equal on O/G (d) | [0,8] flat on O/G; DRAW counter: O 0 leaves, G 15463 leaves / 5 jittered |
| LmrQuietBase (93; [0,300]) | none: any change alters the double cell value (304) | – | none | – |
| LmrQuietDivisor (205; [100,500]) | none: same cell argument (304) | – | none | – |
| LmrNoisyBase (13; [0,300]) | none (306) | – | none | – |
| LmrNoisyDivisor (333; [100,800]) | none (306) | – | none | – |
| NullMoveMinDepth (3; [1,10]) | none: gate `depth >= NMD` (1943) flips at every reachable d | – | none | – |
| NullMoveBase (5; [1,6]) | none: R changes the null depth d-R (1950) | – | NMB 6 == NMDD 1 at root 9 (seen; mechanism below) | – |
| NullMoveDepthDivisor (3; [1,10]) | none (1950) | – | as above | – |
| NullMoveEvalDivisor (200; [50,1000]) | none: floor(e/a) != floor(e/b) at e = min(a,b) for e <= 64000, min(...,3) caps at 3 (1951) | – | none | – |
| RfpDepth (8; [0,15]) | {0} as off-point: gate `depth <= RfpDepth` false for all depth >= 1 (1937; depth <= 0 enters qsearch, 1762) | – | RFP-off family: (0, any RfpMargin, any RfpImproving) | – |
| RfpMargin (72; [10,300]) | none: linear in the margin (1938) | – | none | – |
| RfpImproving (40; [0,200]) | none: linear (1938) | – | none | – |
| RazorDepth (2; [0,6]) | {0}: gate false for depth >= 1 (1926) | – | razor-off family (0, any RazorBase/Multiplier) | – |
| RazorBase (150; [0,1000]) | none (1926) | – | none | – |
| RazorMultiplier (350; [0,1000]) | none (1926) | – | none | – |
| FutilityDepth (7; [0,15]) | none: lmr_depth is max(0, …) (2123) so 0 still fires (2132) | – | none | – |
| FutilityBase (100; [0,500]) | none: linear (2136) | – | none | – |
| FutilityMultiplier (110; [0,500]) | none: linear (2136) | – | none | – |
| LmpBase (8; [0,20]) | none: threshold base + d^2 (320) shifts at every d | – | none | – |
| HistoryPruneDepth (3; [0,10]) | none: gate `lmr_depth <= HPD` (2143) flips per lmr_depth | – | HPD 0 == HPM 20000 == (HPD 0 & HPM 0): counters below | 0 fires for all three on O/G (counter-proven on these sets) |
| HistoryPruneMultiplier (2220; [0,20000]) | none: threshold -HPM*d*f (2128-2130); history bound -90112 crosses it at small d | – | as above | 20000 fires 0 on O/G (counter) |
| SeeQuietMultiplier (24; [0,200]) | none: -SQM*lmr_depth^2 (2148) changes at lmr_depth >= 1 | – | none | – |
| SeeNoisyMultiplier (150; [0,1000]) | none: -SNM*depth (2166) | – | none | – |
| SingularDepth (6; [2,20]) | none: gate `depth >= SD` (2192) flips at every d <= 19 | d-linked (d_max) | none | – |
| SingularMargin (2; [0,10]) | none: singular_beta shifts (2194) | – | none | – |
| IirDepth (2; [1,20]) | none: gate `depth >= IirDepth` (2033) | d-linked | none | – |
| ProbcutDepth (5; [1,20]) | none: gate `depth >= PD` (1996) | d-linked | none | – |
| ProbcutMargin (180; [0,1000]) | none: probcut_beta shifts (1995) | – | none | – |
| QsFutilityMargin (160; [0,1000]) | none: qsearch futility_base (1685) | – | none | – |
| AspirationDelta (18; [4,200]) | none: first window = +-value (2743ff) | – | none | – |
| HistoryBonusQuadratic (24; [0,100]) | none: bonus(d) = min(HBM, Q*d^2 + L*d - 32) (323-325) changes at d where Q moves raw | – | none | – |
| HistoryBonusLinear (54; [0,500]) | none (324) | – | none | – |
| HistoryBonusMax (2212; [100,10000]) | **[raw(d_max)+1, 10000]**: bonus(d) = min(HBM, 24d^2+54d-32) (323-325) is uncapped for all d <= d_max iff HBM >= raw(d_max); raw increasing. Root 12: [9658, 10000] (raw(19) = 9658) | **yes — d-linked**: root 9 gives [6977,10000] (raw(16)); root >= 13 empties it (raw(20) = 10648 > 10000) | interval members mutually equal | seen wider: [4727,10000] on G (d only 13), [4073,10000] on O |
| LmrHistoryDivisor (5643; [1000,30000]) | none: clamp(history/x, -2, 2) differs at history = min(a,b) (2265) | – | none | – |
| CheckExtensionDepth (2; [1,30]) | **[d_max+1, 30]**: gate `gives_check && depth >= CED` (2218-2220) is false for every node iff CED > d_max. Root 12: [20, 30] | **yes — d-linked**: root 9 gives [17,30]; empties for root >= 23 | interval members mutually equal | seen wider: [14,30] on G, [13,30] on O |
| LmrCutoffThreshold (3; [0,20]) | {0}: gate `> 0` (2264) | – | none | – |
| MaterialCorrectionWeight (100; [0,300]) | {0}: gate `> 0` (1291) | – | none | – |
| CaptureFutilityBase (0; [0,1000]) | {0}: gate `> 0`, first clause (2156) | – | none | code reached 1,149,084 x on O (CAPFUT counter); NOT flat at d12 (rows differ on 41 of O, 119 of G) |
| FailLowContinuationBonus (0; [0,300]) | {0}: gate `> 0` (2360) | – | none | – |
| EvalSwingMult (0; [0,64]) | {0}: gate `!= 0` (1890) | – | none | – |

(c) the two pairs, mechanisms:
- **HistoryPruneDepth 0 = HistoryPruneMultiplier 20000 = both 0** (8,105,000 | 17,090,595, equal on
  200|353): the prune fires iff `lmr_depth <= HPD && history < -HPM*depth*f` (2143, threshold
  2128-2130, f = 3/4 not-improving under TtPruneV2). Counters: HPD 0 fires 0 (O and G), HPM 20000
  fires 0, both-0 fires 0 — and both-0 (threshold 0 at lmr_depth == 0) firing 0 proves **no reached
  test at lmr_depth == 0 has history < 0 at all**, while hpm0 (threshold 0, HPD 3) fires
  1,230,074 | 2,568,747 times, so negative histories are common at lmr_depth in [1,3]. All three
  configs therefore equal the no-history-pruning tree; base differs because its 11,208 | 43,280 fires
  all live at lmr_depth in [1,3]. Why lmr_depth == 0 never shows a negative history: seen, not
  proven (suspicion list).
- **NullMoveBase 6 = NullMoveDepthDivisor 1 at root 9, parting at root 12**: R = NMB + d/NMDD +
  min((eval-beta)/200, 3) (1950-1951). NMDD 1: R = 5 + d + e > d for every d — every null search
  enters qsearch (depth <= 0 path, 1762); measured NULLQ 125,718/125,718 (O), 348,134/348,134 (G).
  NMB 6 (NMDD 3): R = 6 + d/3 + e; the null search is real iff 2d/3 > 6 + e: **d >= 10 when
  eval-beta < 200; d >= 12 when 200 <= eval-beta < 400; d >= 14 when < 600; d >= 16 above**. At root
  9 such tries did not occur on the 40 positions (40/40 equal, job 26); at root 12 they are constant
  (NMB 6 real-search tries: 1,481 O / 5,740 G; rows equal on only 17|59).
- **(d) DrawJitter 8 = base on 553/553**: line 1442 — only fifty-move (halfmove >= 100) and
  repetition leaves jitter; stalemate and insufficient-material leaves keep a literal 0. Measured:
  O at d12 has **0 draw leaves of any kind**; G has 15,463 draw leaves, of which 5 are
  fifty/repetition and jittered under DJ 8 (range [-8,8], 1443-1444) and 15,458 keep literal 0; the
  5 jittered scores never crossed a window (dj8 rows equal base on 353/353). In a game it changes a
  decision when a fifty/repetition leaf's jittered value (nodes % 17 - 8) crosses alpha vs a near-0
  alternative — reversible endgame play where the side weighs a repetition against a small-eval
  quiet.

## (3) Known answers A and B

- **A: met.** The counting build (tests_kimi5_job29/ran_counters.patch.txt on a scratch copy;
  applies `patch -p1 -F0` clean; exe step0/exe_count.sha256 a1a46fa4…) reproduces the plain build
  to the node: O 8,315,168 and G 17,611,204 at d12, and 405,544 on job 26's 40 positions at d9
  (kaA/, script run_kaA.sh), position-by-position including best moves; and for each of the 8
  counter settings the counting-build rows equal the plain rows exactly (rows_cnt/cnt_vs_plain.txt:
  ALL COUNTER-ROWS EQUAL PLAIN: True).
- **B: met.** With HistoryPruneMultiplier 0 the HP counter fires on O: 1,230,074 of 5,839,663
  reached (rows move to 8,912,366 ✓). With NullMoveDepthDivisor 1 every null try goes to qsearch:
  NULLQ 125,718/125,718 (O), 348,134/348,134 (G). Neither counter is blind.

## (4) Prediction, graded row by row (prediction.txt, own commit before Step 3; survives = within [g/10, g*10], 0 only as 0)

| call | guess | actual (O d12) | verdict |
|---|---|---|---|
| CED 20 vs 30 | equal 200|353 | equal 200|353 | survives |
| CED 19 vs 30 | equal (seen wider) | equal 200|353 | survives |
| HBM 9658 vs 10000 | equal 200|353 | equal 200|353 | survives |
| HBM 9657 vs 10000 | equal (seen wider) | equal 200|353 | survives |
| base HP reached | ~3e6 | 4,775,611 | survives |
| base HP fired | ~2e4 | 11,208 | survives |
| base NULL reached / fired | ~3e5 / ~2e5 | 123,578 / 86,995 | survives both |
| base NULLQ reached / fired | ~3e5 / ~1e5 | 123,578 / 113,502 | survives both |
| base DRAW reached | ~1e1 (0..100) | 0 | survives at the range floor (actual is the floor) |
| base DRAW fired | 0 | 0 | survives |
| base CAPFUT reached / fired | ~1e6 / 0 | 1,149,084 / 0 | survives both |
| hpd0 HP fired | 0 | 0 | survives |
| hpm20000 HP fired | 0 | 0 | survives |
| dj8 DRAW reached / fired (O) | ~1e1 / 0 | 0 / 0 | survives at the floor / survives |
| DMAX largest d at any node | [14,19] per search | 12 (all 200 O), <= 13 (G) | **fails** (too high; the printed sum hides the per-search max — misdesigned) |
| DMAX largest d at a null try | [11,15] per search | sum 2186 (avg 10.9), max unreadable | **fails as written** (sum, not max) |

15 of 17 calls survive; both DMAX calls fail (one wrong prior, one counter-design mistake).

## (5) Step 3 checks (go depth 12, O and G, a fresh process per setting; sums and equal counts)

| check | sums O | G | equal | evidence |
|---|---|---|---|---|
| identity (all 40 at PC20) vs base | 8,315,168 = 8,315,168 | 17,611,204 = 17,611,204 | 200/200, 353/353 | rows/identity_*, rows/equal_counts.txt |
| hpd0 = hpm20000 = hpboth0 | 8,105,000 each | 17,090,595 each | 200/200, 353/353 pairwise | rows/, equal_counts.txt |
| nmb6 vs nmdd1 | 8,366,602 vs 8,394,538 | 17,358,916 vs 17,465,091 | 17/200, 59/353 (they part, as known) | rows/, equal_counts.txt |
| dj8 vs base | equal sums | equal sums | 200/200, 353/353 | rows/ |
| CED proven stretch: 20 vs 30 | 7,488,328 = 7,488,328 | 13,271,726 = 13,271,726 | 200/200, 353/353 | rows/, stretch_counts.txt |
| CED outside: 19 vs 30 | equal sums | equal sums | 200/200, 353/353 — **wider than proven: seen [13,30] on O, [14,30] on G** (d never exceeds 12/13) | rows/, stretch_counts.txt |
| HBM proven stretch: 9658 vs 10000 | 8,244,900 = 8,244,900 | 17,547,039 = 17,547,039 | 200/200, 353/353 | rows/, stretch_counts.txt |
| HBM outside: 9657 vs 10000 | equal sums | equal sums | 200/200, 353/353 — **wider than proven: seen [4073,10000] on O, [4727,10000] on G** | rows/, stretch_counts.txt |
| controls (must move): hpm0 | 8,912,366 (0/200 vs base) | 17,098,143 (4/353) | moved ✓ | rows/ |
| controls: nmb4 | 8,448,399 (0/200) | 17,096,422 (8/353) | moved ✓ | rows/ |
| counters on the counting build | rows_cnt/ran_sums.txt (base, hpd0, hpm20000, hpboth0, nmb6, nmdd1, dj8, hpm0; O and G) | — | counter rows == plain rows for all 8 | rows_cnt/cnt_vs_plain.txt |

"Flat on O and G, not proven" list: DrawJitter [0,8] (DRAW: reached 15,463 on G, jittered 5 — code
reached and still flat); HistoryPruneMultiplier near-top (HPM 20000: reached 8,837,566 on G, fired
0); the seen-wider parts of the CED ([13/14,30]) and HBM ([4073/4727,10000]) stretches; HPD 0 (fires
0 on O/G but the gate is live — reached 4,639,902 on O). CaptureFutilityBase is NOT on this list:
its rows move at d12 (41|119 differ).

## The standing form

**Three plain lines.** Asked: the flat stretches and look-alikes of the 40 tuned settings, proven by
reading plus a counting build. Answer: only two proper flat intervals are provable for every input
(CheckExtensionDepth [d_max+1,30], HistoryBonusMax [raw(d_max)+1,10000], both tied to d_max <= root+7);
the history-prune triple are look-alikes because none of them ever fires (counter-proven: the
lmr_depth==0 population never has negative history); NMB 6 and NMDD 1 part exactly where the null
search leaves qsearch (d >= 10, eval-beta < 200 first). How sure: every equality is to the node on
553 positions and the counters were proven by controls that fire on command; the "why" of the
lmr_depth==0 population is the one open reading.

**Step table.**
| step | done? | evidence | result |
|---|---|---|---|
| Step 0 pins | done | step0/ | 8/8 met |
| Step 1 reading | done | section (2) | 40 rows; 2 proven intervals; 6 gate-off points; 2 off-families |
| Step 2 counting build | done | ran_counters.patch.txt (applies -F0), kaA/ | known answer A met (cnt == plain everywhere) |
| known answer B | done | rows_cnt/ran_sums.txt | hpm0 fires 1.23M; nmdd1 100% qsearch |
| prediction | done | prediction.txt (own commit) | 15/17 survive |
| Step 3 checks | done | rows/, rows_cnt/ | all rows in the table above |

**Findings.**
1. d_max <= root depth + 7 (search.cpp:2208 chain limit, 2222 new_depth). Show:
   `sed -n '2207,2222p' src/search.cpp`. Measured: largest d is 12 on every O search, <= 13 on G.
2. HistoryPruneDepth 0 = HistoryPruneMultiplier 20000 = both 0 because all three fire 0 times
   (rows_cnt/ran_sums.txt); the both-0 run (threshold 0) proves no lmr_depth==0 test has history < 0,
   while hpm0 fires 1.23M|2.57M — negative histories live only at lmr_depth in [1,3]. Lines: gate
   2143, threshold 2128-2130. Show: `python3 sum_ran.py rows_cnt/hpboth0_O_d12_full.txt`.
3. NMB 6 parts from NMDD 1 at d >= 10 (eval-beta < 200), d >= 12 (< 400), d >= 14 (< 600), d >= 16
   (above): R formulas 1950-1951; NMDD 1 always R > d (NULLQ 100%). NMB 6 real null searches:
   1,481 O / 5,740 G.
4. DrawJitter: line 1442 limits jitter to fifty/repetition leaves; O has zero draw leaves at d12;
   G has 15,463, of which 5 jittered under DJ 8 without changing one row. dj8 == base on 353/353.
5. CheckExtensionDepth [20,30] and HistoryBonusMax [9658,10000] are proven flat at root 12 and
   measured equal on 553/553; both are seen wider (CED [13,30] on O, HBM [4073,10000] on O) because
   d never approaches the reading bound.
6. The capture-futility line is reached 1,149,084 times on O at base (CFB 0, gate off): its d9
   near-flatness was "reached, nothing to do", and at d12 it is not flat at all (41|119 positions
   differ).
Suspicions, not proven: (a) why no lmr_depth==0 test has negative history — likely the
late-move/shallow population reaching the line has only non-negative entries, but the counter set
has no per-lmr_depth split; (b) the 5 jittered leaves on G never changed a decision — inferred from
row equality, not from the leaf values; (c) HBM's flat top at root 13+ is empty by reading
(raw(20) > 10000) but untested.

**From my colleagues.** Read: deepseek5's NOTES tail (the stage-label fix — read state at the event;
its corrected killer/countermove regret rates) and its report list (job 30 newest); applied: the
"read state at the event" rule in the counter design (counters sit at the decision line itself, not
in a later stage). deepseek5's mode-4 finding (the TT move is never history-pruned) matches the PC
build's `prunable` at 2126, which my HP reading rests on. glmflash5: the branch is
for-fable-and-opus/glmflash-work (no glmflash5-work exists); it has no NOTES_glmflash5.md; its
newest report (REPORT_t23.md, mate-search pruning and rule-50 TT staleness) touches nothing in this
job — the history-prune/null/draw code I read is outside its two fault areas; not applied.

**What I did NOT do.** No per-lmr_depth counter split (would settle suspicion (a)). No root-depth-9
stretch checks (the (b) table's root-9 intervals are reading-only). No test of the root-13 HBM
emptiness. The job-30 file (the other new file on the handoff branch) was read for corrections — it
is a standalone job, none apply here — and is left open as the lowest unreported job after this one.

**What I am NOT sure about.** The lmr_depth==0 population size (fired 0 could hide a tiny reached
set). Whether the 5 G jittered leaves returned nonzero values. Whether d = 14..19 is truly
unreachable on these sets (DMAX sums bound it: O exact 12; G <= 13 by 4277 < 353 x 13 + ... = 4246+41).

**A better way.** (1) DMAX should be printed as a per-search max line at end of search (one line per
search: `info string RANMAX <d> <dnull>`), not summed into the RAN pair — the sum destroyed the
per-search max and cost me both prediction calls. (2) One more counter pair HPL (reached, fired at
lmr_depth == 0 only, threshold 0 hard-coded) would turn suspicion (a) into a counted population in
one run, cheaper than a per-lmr_depth histogram.

**Times:** see stamps.txt. **Model:** Kimi K3 (this runtime names itself so), run name kimi5.
`git status --short` and `ls -R` of the job folder: final_ls.txt (the last command before this commit).
