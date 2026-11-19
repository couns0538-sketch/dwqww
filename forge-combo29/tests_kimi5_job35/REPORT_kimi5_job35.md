# kimi5 job 35 report — census options patch, no-op proof, ALIVE/DEAD census of 40 options

## Three lines
- Asked: census the hand-set numbers of r15d's src/search.cpp, make every reachable T/A-class number a spin option (text patch, max 40, K1's thirteen named), prove the patch a no-op (K3), run controls, commit a prediction, then measure every new option at default±1 step on O (200) and G (353), PC20, depth 12, and say ALIVE/DEAD/NOT SEEN for each.
- Answer: patch of 40 options is a proven no-op (553/553 positions identical); all 26 of K5's known O sums reproduced to the node; of the 40 options 35 are ALIVE and 5 are DEAD (0 NOT SEEN); my committed prediction: 25 of 27 ALIVE/DEAD calls right, 3 of 5 ratio ranges right, the held-back G count (320 of 353) inside my 250–330.
- Sure: high on the measurements (every run with ucinewgame+isready, refusal scan, exe sha in each .meta; K5 match is to the node). Medium on the patch's correctness beyond the measured window (dry-run on kF had one failed hunk; see Step 2).

## 1. Step 0 (raw files in step0/)
r15d, no options: bench 11 = 312866 (step0/bench11.txt), bench 13 = 862329 (step0/bench13.txt), go perft 5 = 4865609 (step0/perft5.txt); with PC20: bench 11 = 278024 (step0/pc_bench11.txt), bench 13 = 587276 (step0/pc_bench13.txt). All five pins match. r15d tree: 29 of 29 sha256 lines OK (r15d_sha256sums.txt is in the job folder's build records; tree at /tmp/j35/r15d).

## 2. Step 1 census (census.tsv, committed before Step 2)
- Rows above the R block: 64 — 41 T/A reachable rows (40 options made + 1 inside search() not made), 8 more inside-search() reachable rows not made (cap of 40: the rows inside search() came first), 15 outside-search() reachable rows not made, 11 gated-off T/A rows, 5 S rows, HistoryMax 1.
- K2's floor = 76 places (51 search() lines + 21 outside + 4 named constants): every one is a row in census.tsv or in the R list. Rows beyond the floor: 14 (0/1 amounts and named-value expressions the script cannot see: lines 2409–2415, 2365, 2367, 2371, 2406, 1944, 1477, 1443, 1480).
- Class R rows (50-move 100, formats, sizes, salts, clock numbers 3160–3190) are listed in one block with their lines, per the job's rule.

## 3. Step 2 options patch (census_options.patch.txt, applies with patch -p1 -F0 on r15d)
- Made: 40 options = K1's thirteen (names kept) + 27 new reachable rows inside search(). Names, defaults, mins, maxes, steps: OPTION block at the end of census.tsv (see its honesty note: the block was appended after Step 4 — the pre-Step-4 commit held only the census rows; the values are exactly those the runs used, proven by s4/opt_*.txt).
- Not made: 8 reachable rows inside search() beyond the 40 cap and 15 reachable rows outside search(), each listed in census.tsv with its lines; S-class scales and HistoryMax (static_assert) never options.
- kF dry-run line (`patch -p1 --dry-run` on my kF tree): 22 of 23 search.cpp hunks apply with offsets, hunk #12 (TtNear50Clock, near kF line 2247) FAILED, search.hpp applies with offset — recorded in dryrun_kF.txt. Reported, never a stop.
- INCIDENT (honest): the first committed patch declared TtNear50Clock max 100 < default+step (108). Step 4's run of 108 was refused by the engine ("info string invalid value for option TtNear50Clock"); the runner's refusal scan caught it and wrote no result. Patch corrected to max 120 (one literal; no default/step change), rebuilt (exe 70f2a557 → f9ec5484), re-proven a no-op at defaults (v2base O sum 8315168, G sum 17611204, 0 positions differ vs base; s4/v2base_*.json), then the 108 runs were made on the v2 binary. All other 156 Step 4 runs used the v1 binary; at defaults v1 == v2, and no other run touched TtNear50Clock.

## 4. Step 3 K3 no-op proof — PASS
Patched build at defaults == r15d exactly: O 200/200 positions identical in node count AND best move, sum 8,315,168; G 353/353 identical, sum 17,611,204 (k3/patO.json vs k3/baseO.json, k3/patG.json vs k3/baseG.json; base runs on the r15d binary, pat runs on the patched binary, both with pc20.opt). Step 0 pins re-checked on the patched build.

## 5. Controls — both PASS
- C-DEAD: LmrDeeperBase 0 (from 40), everything else default: 0 of 200 O rows differ (sum 8,315,168), 0 of 353 G rows differ (sum 17,611,204) — k3/cdeadO.json, k3/cdeadG.json. Matches K4's by-reading claim.
- C-LIVE: LmrCutNode 0 (from 2): 200 of 200 O positions differ, sum 8,304,696 — exactly Fable's known sum (k3/cliveO.json). The runner delivers its options.

## 6. K5 side by side (all 26 runs, O sum and differ-count; mine measured this run)
| option | K5 minus: sum, differ | mine | K5 plus: sum, differ | mine |
|---|---|---|---|---|
| LmrTtPv | 5,855,914, 200 | 5,855,914, 200 | 11,365,932, 200 | 11,365,932, 200 |
| LmrNotImproving | 11,034,435, 200 | 11,034,435, 200 | 6,819,675, 200 | 6,819,675, 200 |
| LmrCutNode | 8,443,473, 200 | 8,443,473, 200 | 8,330,214, 200 | 8,330,214, 200 |
| LmrTtCapture | 8,930,826, 200 | 8,930,826, 200 | 7,993,703, 200 | 7,993,703, 200 |
| LmrGiveCheck | 8,058,643, 200 | 8,058,643, 200 | 9,080,784, 200 | 9,080,784, 200 |
| LmrInCheck | 8,133,655, 189 | 8,133,655, 189 | 8,410,321, 189 | 8,410,321, 189 |
| LmrCutoffAdd | 11,638,349, 200 | 11,638,349, 200 | 6,820,425, 200 | 6,820,425, 200 |
| DoubleExtMargin | 8,329,419, 175 | 8,329,419, 175 | 8,123,386, 159 | 8,123,386, 159 |
| DoubleExtLimit | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 |
| LmrDeeperBase (K4) | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 |
| LmrDeeperDepthMul (K4) | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 |
| LmrShallowerBase (K4) | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 |
| LmrShallowerDepthMul (K4) | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 | 8,315,168, 0 |

All 26 match to the node; 0 mismatches (check script: s4/classification.txt build log; raw: s4/k1_*.json). G-side spot checks named by the job: DoubleExtLimit 5 → 48 of 353 differ, 7 → 30 of 353 (both match Fable); the four K4 rows 0 of 353 (sum 17,611,204); DoubleExtMargin 20 on G → 320 of 353 differ, sum 17,370,464; 28 on G → 310 of 353, sum 17,187,683.

## 7. Prediction graded (prediction.txt, own commit "kimi5 job 35 prediction", never edited)
- ALIVE/DEAD, 27 new options: 25 right, 2 wrong. Wrong: NullVerifyDepth (called DEAD; measured ALIVE — 6 of 353 G positions change, 4 on minus 13 and 2 on plus 15; "very few" was right, "none" was wrong) and CuckooRepMinClock (called DEAD; measured ALIVE — plus side 4 changes 200 of 200 O and 350 of 353 G positions; my "rare in these positions" reasoning was wrong, see Findings).
- The five O-sum movers, ratio ranges: 3 of 5 inside. NullGateOffset minus 0.9423 in [0.70, 0.95] RIGHT; SingularDepthDiv minus 1.4662 in [1.05, 1.60] RIGHT; DoubleExtPlies minus 0.9662 in [0.88, 1.00] RIGHT; FutilityImprovingDiv minus 1.0054 NOT in [0.75, 0.98] (wrong, barely above); LmrMinDepth plus 0.9835 NOT in [1.02, 1.25] (wrong, the sum went down not up).
- Held-back count: DoubleExtMargin 20 on G = 320 of 353, inside my 250–330. RIGHT.

## 8. Step 4 table (PC20, depth 12, Threads 1, Hash 16, ucinewgame+isready before each search; 4 parallel processes = core count)
Base sums: O 8,315,168 (200 positions), G 17,611,204 (353 positions). chg = positions whose node count differs from base; ratio = node sum / base sum. Sorted by positions changed. Raw: s4/*.json with .meta (exe sha, UTC times, command), s4/*_input.log (the exact setoption lines), s4/grading.tsv (all 158 rows).

| option | default | step | minus val | plus val | chg O m/p | chg G m/p | ratio O m/p | ratio G m/p | class |
|---|---|---|---|---|---|---|---|---|---|
| LmrTtPv | 1 | 1 | 0 / 2 | 200/200 | 353/353 | 0.7042/1.3669 | 0.7248/1.2613 | ALIVE |
| LmrNotImproving | 1 | 1 | 0 / 2 | 200/200 | 353/352 | 1.3270/0.8201 | 1.2665/0.7941 | ALIVE |
| LmrCutoffAdd | 1 | 1 | 0 / 2 | 200/200 | 353/351 | 1.3997/0.8202 | 1.2148/0.8192 | ALIVE |
| LmrMinDepth | 2 | 1 | 1 / 3 | 200/200 | 350/351 | 1.0458/0.9835 | 0.9823/0.9852 | ALIVE |
| LmrGiveCheck | 1 | 1 | 0 / 2 | 200/200 | 350/350 | 0.9691/1.0921 | 0.8999/1.0619 | ALIVE |
| RfpWorseningDiv | 3 | 1 | 2 / 4 | 200/200 | 350/349 | 1.0017/1.0612 | 0.9743/0.9937 | ALIVE |
| LmrCutNode | 2 | 1 | 1 / 3 | 200/200 | 350/348 | 1.0154/1.0018 | 0.9624/0.9952 | ALIVE |
| SingularDepthDiv | 2 | 1 | 1 / 3 | 200/200 | 349/349 | 1.4662/1.0493 | 1.4548/0.9643 | ALIVE |
| SingularTtDepthMargin | 3 | 1 | 2 / 4 | 200/200 | 348/349 | 1.0025/1.0064 | 0.9242/1.0058 | ALIVE |
| NullGateOffset | 180 | 36 | 144 / 216 | 200/200 | 346/348 | 0.9423/1.0926 | 0.9261/1.0516 | ALIVE |
| LmrQuietBoostDiv | 2 | 1 | 1 / 3 | 200/199 | 348/346 | 1.0294/1.0287 | 0.9725/0.9581 | ALIVE |
| PvQuietBonusDiv | 4 | 1 | 3 / 5 | 200/200 | 348/345 | 1.0225/1.0116 | 0.9812/0.9747 | ALIVE |
| NullGateSlope | 24 | 4 | 20 / 28 | 200/200 | 345/345 | 1.0710/0.9510 | 0.9836/0.9270 | ALIVE |
| DoubleExtPlies | 2 | 1 | 1 / 3 | 200/200 | 344/344 | 0.9662/1.0495 | 0.8761/1.2476 | ALIVE |
| LmrHistoryClamp | 2 | 1 | 1 / 3 | 200/199 | 348/341 | 0.9198/1.0177 | 0.9793/0.9635 | ALIVE |
| HistBonusBetaMargin | 100 | 20 | 80 / 120 | 200/197 | 347/341 | 0.9805/1.0321 | 1.0007/0.9879 | ALIVE |
| TtPruneIirOffset | 2 | 1 | 1 / 3 | 200/200 | 345/340 | 1.0031/1.0641 | 0.9929/1.0198 | ALIVE |
| ImprovingLookbackFallback | 4 | 1 | 3 / 5 | 195/196 | 344/347 | 0.9942/0.9924 | 0.9674/0.9750 | ALIVE |
| ProbcutSearchReduction | 4 | 1 | 3 / 5 | 200/200 | 338/337 | 0.9969/1.0061 | 0.9839/0.9776 | ALIVE |
| LmrTtCapture | 1 | 1 | 0 / 2 | 200/200 | 335/331 | 1.0740/0.9613 | 1.0236/0.9389 | ALIVE |
| LmrInCheck | 1 | 1 | 0 / 2 | 189/189 | 342/343 | 0.9782/1.0114 | 0.9728/1.0108 | ALIVE |
| ProbcutImprovingDiscount | 50 | 10 | 40 / 60 | 192/195 | 330/327 | 1.0239/1.0244 | 0.9905/0.9782 | ALIVE |
| RfpWorseningDrop | 2 | 1 | 1 / 3 | 200/199 | 314/311 | 0.9946/0.9975 | 0.9779/0.9908 | ALIVE |
| ProbcutTtDepthMargin | 3 | 1 | 2 / 4 | 186/186 | 323/307 | 1.0098/1.0155 | 0.9999/0.9945 | ALIVE |
| HistPruneWeakNum | 3 | 1 | 2 / 4 | 188/174 | 328/299 | 1.0047/1.0086 | 0.9823/0.9713 | ALIVE |
| DoubleExtMargin | 24 | 4 | 20 / 28 | 175/159 | 320/310 | 1.0017/0.9769 | 0.9863/0.9760 | ALIVE |
| AspStartDepth | 4 | 1 | 3 / 5 | 133/160 | 290/300 | 0.9896/0.9981 | 0.9868/0.9762 | ALIVE |
| FutilityImprovingDiv | 2 | 1 | 1 / 3 | 148/99 | 290/261 | 1.0054/1.0096 | 0.9819/1.0007 | ALIVE |
| AspDeltaGrowDiv | 2 | 1 | 1 / 3 | 59/58 | 272/258 | 1.0104/1.0001 | 0.9504/1.0011 | ALIVE |
| ImprovingLookback | 2 | 1 | (clamped) / 3 | -/200 | -/352 | -/1.3084 | -/1.0982 | ALIVE |
| CuckooRepMinClock | 3 | 1 | 2 / 4 | 0/200 | 0/350 | 1.0000/0.9961 | 1.0000/0.9956 | ALIVE |
| LmrNoisyMoveCount | 4 | 1 | 3 / 5 | 34/6 | 65/43 | 1.0118/0.9983 | 0.9880/1.0020 | ALIVE |
| DoubleExtLimit | 6 | 1 | 5 / 7 | 0/0 | 48/30 | 1.0000/1.0000 | 0.9824/0.9995 | ALIVE |
| NullEvalReductionCap | 3 | 1 | 2 / 4 | 5/0 | 70/1 | 1.0000/1.0000 | 1.0000/1.0000 | ALIVE |
| NullVerifyDepth | 14 | 1 | 13 / 15 | 0/0 | 4/2 | 1.0000/1.0000 | 1.0002/1.0000 | ALIVE |
| LmrDeeperBase | 40 | 8 | 32 / 48 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| LmrDeeperDepthMul | 2 | 1 | 1 / 3 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| LmrShallowerBase | 0 | 8 | -8 / 8 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| LmrShallowerDepthMul | 1 | 1 | 0 / 2 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |
| TtNear50Clock | 90 | 18 | 72 / 108 | 0/0 | 0/0 | 1.0000/1.0000 | 1.0000/1.0000 | DEAD |

ALIVE 35 of 40; DEAD 5; NOT SEEN 0.

for the next tune (ALIVE, name default min max step):
- LmrTtPv 1 0 4 1
- LmrNotImproving 1 0 4 1
- LmrCutoffAdd 1 0 4 1
- LmrMinDepth 2 1 8 1
- LmrGiveCheck 1 0 4 1
- RfpWorseningDiv 3 1 10 1
- LmrCutNode 2 0 4 1
- SingularDepthDiv 2 1 8 1
- SingularTtDepthMargin 3 0 10 1
- NullGateOffset 180 0 400 36
- LmrQuietBoostDiv 2 1 8 1
- PvQuietBonusDiv 4 1 16 1
- NullGateSlope 24 0 100 4
- DoubleExtPlies 2 1 4 1
- LmrHistoryClamp 2 0 8 1
- HistBonusBetaMargin 100 0 400 20
- TtPruneIirOffset 2 0 10 1
- ImprovingLookbackFallback 4 2 8 1
- ProbcutSearchReduction 4 1 10 1
- LmrTtCapture 1 0 4 1
- LmrInCheck 1 0 4 1
- ProbcutImprovingDiscount 50 0 200 10
- RfpWorseningDrop 2 0 100 1
- ProbcutTtDepthMargin 3 0 10 1
- HistPruneWeakNum 3 0 4 1
- DoubleExtMargin 24 0 400 4
- AspStartDepth 4 1 16 1
- FutilityImprovingDiv 2 1 10 1
- AspDeltaGrowDiv 2 1 8 1
- ImprovingLookback 2 2 8 1
- CuckooRepMinClock 3 0 100 1
- LmrNoisyMoveCount 4 1 16 1
- DoubleExtLimit 6 -1 64 1
- NullEvalReductionCap 3 0 10 1
- NullVerifyDepth 14 2 30 1

DEAD means: all four runs made and no position changes — it does NOT mean the option is worthless (Elo untouched by node counts; an option dead at depth 12 may be alive at other depths; LmrDeeperBase's brothers are the K4 gated-off four, dead by construction under PC20).

## Findings
1. CuckooRepMinClock is strongly ALIVE only upward: minus (2) changes 0 positions, plus (4) changes 200/200 O and 350/353 G (s4/n_CuckooRepMinClock_*.json). Reading: the cuckoo repetition detection with minimum clock 3 vs 4 differs on nearly every position — at clock≥3 some repetition entries are consulted that clock≥4 skips (or vice versa), and that changes node counts almost everywhere. My prediction's premise ("needs high halfmove clock, rare here") was wrong: the gate is the halfmove clock of the CURRENT position's search path, and 3 vs 4 sits exactly on the mass of these searches. Not proven beyond the node counts; worth a reading pass on the cuckoo code (search.cpp may_repeat/cuckoo lines, census.tsv row for CuckooRepMinClock).
2. ImprovingLookback (default 2, range floor 2) at 3: O sum ratio 1.3084, 200/200 changed — the second-largest O mover of the new 27 after SingularDepthDiv minus. The improving flag's lookback depth is a high-leverage knob for the next tune.
3. The four K4 rows are DEAD by measurement on both suites (matches K4's by-reading claim and C-DEAD). TtNear50Clock is DEAD at 72 and 108 on both suites: the near-50 TT distrust never engages at depth 12 from these roots.
4. kF dry-run hunk #12 failure (TtNear50Clock context near kF line 2247) means the kF tree's search.cpp differs from r15d exactly where the near50 clock is read — kF carries another patch there. Anyone applying this patch to kF must place that hunk by hand (dryrun_kF.txt).
5. LmrShallowerBase's patch range is −100000..400; the measured minus step was −8 (default 0, step 8 per the job's default-0 rule). DEAD as K4 says.

### Suspicions, not proven
- NullEvalReductionCap shows changed node counts with sums equal to base to the node (mG 70 changed, ratio 1.0000): it redistributes nodes between positions without moving the total. Coincidence of rounding is possible; not investigated.
- NullVerifyDepth's 6 changed G positions are all on long searches (extensions reach depth 13+): consistent with my "very few" reading, but I did not open those searches to confirm the mechanism.

## From my colleagues
- deepseek5 (for-fable-and-opus/deepseek5-work): NOTES_deepseek5.md read (last 40 lines saved in /tmp during the run); 65 REPORT_ files exist on that branch. Applied: the runner pattern of quoting setoption lines into an input log per run (their warning about options not arriving is why every s4/*_input.log exists and why the TtNear50Clock refusal was caught by scan instead of silently measured at default).
- glmflash5: branch for-fable-and-opus/glmflash5-work does not exist yet ("couldn't find remote ref"); nothing to read. Said here as the template asks.
- Job-file colleagues K1–K5: K4's four confirmed DEAD by measurement; K5's 26 sums reproduced exactly (section 6); K3's target sums (8,315,168 / 17,611,204) reproduced by both base and patched builds.

## What I did NOT do
- No Elo, no matches, no SPRT: the job measures node-count liveness only. ALIVE says a tune can reach the knob, not that any value gains.
- The 8 reachable inside-search() rows beyond the 40 cap and the 15 outside-search() reachable rows: listed, not made into options (the job's cap).
- The kF hunk-#12 failure: reported, not repaired (never a stop per the job).
- full UCI streams of the 158 Step 4 runs (~59 MB) are not committed; the per-position node counts and best moves (the measured quantities) are in s4/*.json, the exact inputs in s4/*_input.log.
- The v1 refusal artifacts (the first n_TtNear50Clock_pO/pG logs) were deleted when the rerun was set up; the refusal line is quoted in section 3 from the run transcript.

## What I am NOT sure about
- Whether the two wrong DEAD calls (NullVerifyDepth, CuckooRepMinClock) would also flip at other depths; both are depth-sensitive by construction.
- Whether v1-vs-v2 binary for the 156 runs matters anywhere: proven identical at defaults (v2base), and only TtNear50Clock's bound differs, which no other run sets. I am sure for these runs; not a general proof.
- The census' outside-search() reachability calls rest on my reading of gates; a missed dynamic gate would move a row between "made" and "not made" lists.

## A better way
- The ±1-step liveness census conflates "knob does something" with "knob moves node counts on THESE roots at THIS depth". A sharper and cheaper pre-filter: run each option only on O first (200 runs → 200), and only run G for options that moved O; G adds information mostly for clock/extension knobs (DoubleExtLimit was O-dead, G-alive). At ~10 s per O run the whole 40-option screen costs ~7 minutes on 4 cores; the G confirmation wave then covers ~35 options anyway, but the saving grows with option count. Check that it is better: verify on this job's data that no option with 0 O-changes on both sides has more than 60 G-changes — holds here except DoubleExtLimit (48/30) and CuckooRepMinClock-minus (0/0 O, but its PLUS side moved O, so the option would still have gone to G).
- Range-bound checking should be mechanical: a two-line script asserting default−step ≥ min and default+step ≤ max for every OPTION row would have caught the TtNear50Clock max-100 bug before any engine run. Next patch job should generate the options table and the bounds check from one spec file (my make_patch.py already is one; the check was missing).

## UTC stamps
See stamps.txt in this folder (start of run first: 2026-11-19 21:04:58 claim; step 0 + census 21:09; patch/K3/controls 21:11; step 4 waves 21:12–21:26 with the TtNear50Clock fix 21:17–21:26; grading 21:30; report after).

## Model
Kimi K3 (runtime: kimi-k3).

## Last command output
git status --short and ls -R of the job folder: see below (appended at commit time).
```
 M forge-combo29/tests_kimi5_job35/census.tsv
 M forge-combo29/tests_kimi5_job35/census_options.patch.txt
 M forge-combo29/tests_kimi5_job35/stamps.txt
?? forge-combo29/tests_kimi5_job35/REPORT_kimi5_job35.md
?? forge-combo29/tests_kimi5_job35/s4/
--- ls -R forge-combo29/tests_kimi5_job35 (dirs + counts)
forge-combo29/tests_kimi5_job35
forge-combo29/tests_kimi5_job35/k3
forge-combo29/tests_kimi5_job35/s4
forge-combo29/tests_kimi5_job35/step0
776
```
