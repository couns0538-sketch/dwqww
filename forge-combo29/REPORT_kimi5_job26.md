# REPORT_kimi5_job26 (kimi5, 2026-11-18 UTC): the 40 tuned search settings at the ends of their ranges

(1) **Step 0: met.** All eight pins of file 17 on the PC build (raw: step0/): none 312866 / 862329 /
3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276. **No declared range differs from the job
table**: all 40 tuned ranges equal, all five untuned defaults equal the PC values
(step0/range_check.txt over step0/uci_list.txt; the exe advertises the tunables, FORGE_EXPOSE_TUNABLES=1
is set by CMakeLists.txt:31).

(2) **Prediction, graded row by row** (prediction.txt, committed alone before any Step 2 run):
- **P1** "no tuned setting changes nothing under PC20": **survives.** 73 of 76 corner runs moved the
  node sum away from base (ratios 0.40 to 1.63). Three corners equal base to the node (DrawJitter max,
  CaptureFutilityBase max, HistoryPruneDepth max): consistent with "code live, nothing to do on these
  40 positions at depth 9", but they do not CONFIRM that the code ran (see "not sure").
- **P2** "no end is undefined behaviour or a wrap, by reading": **survives so measured.** 0 sanitizer
  lines in 77 runs, with the harness proven by the planted overflow (P2's bounds are in prediction.txt).
- **P3** "0 of 77 corner runs show a sanitizer line": **survives exactly** (0 of 77).

(3) **Step 1 table** (all line numbers in the PC build, $HOME build tree = 6b98f217 + pc_r15.patch,
sha256 d6bd72c5…; "gate" = what must hold for the code to run at all; magnitudes bounded with
MaxPly = 128, CorrectionLimit = 8192, HistoryMax = 16384, apply_spin clamps to the declared range,
uci.cpp:410-419):

| setting (decl) | read at | (a) at min / at max | (b) largest value, type, verdict | (c) gate |
|---|---|---|---|---|
| DrawJitter (search.cpp:95, global; option uci.cpp:347, setter 3049-3054 clamps [0,8] and clears the hash) | draw_leaf_score 1439-1445, chosen at qsearch 1627 and search 1778 | min 0 = PC: literal 0 at draw leaves / max 8: repetition & fifty-move leaves score nodes % 17 - 8 in [-8,8] | width = 2*8+1 = 17, result int in [-8,8]: defined | is_draw() true; DrawJitter > 0. Root shortcut 2584-2587 is compiled OUT (FORGE_FIX_ROOT_DRAWN=1, 35-36) |
| LmrQuietBase (98) | reduction table fill 304 | min 0: base term 0 (less reduction) / max 300: +3.00 to every quiet cell | double max 3.00+ln(63)^2/1.00 = 20.17 -> uint8_t: in range, defined | always live; table rebuilt by tune::refresh() (392) on every tune setoption (uci.cpp:424-427) |
| LmrQuietDivisor (99) | 304 | min 100: divisor 1.00 (most reduction) / max 500: divisor 5.00 (least) | same cell bound 20.17 -> uint8_t: defined | as above |
| LmrNoisyBase (100) | 306 | min 0 / max 300: +3.00 to every noisy cell | as above, defined | as above |
| LmrNoisyDivisor (101) | 306 | min 100: divisor 1.00 / max 800: divisor 8.00 | as above, defined | as above |
| NullMoveMinDepth (102) | null gate 1943 | min 1: null allowed from depth 1 / max 10: only depth >= 10 | comparison only | the 1923-1924 block (!pv_node, !in_check, !excluded, !mate beta, mate_moves_==0, halfmove+depth<100), !bare_king, eval >= beta, static_eval >= beta-24d+180, null allowed, non-pawn material, not (tt upper < beta) |
| NullMoveBase (103) | reduction 1950 | min 1: R one smaller / max 6: R one larger | R <= 6+depth+3 int: defined | as above |
| NullMoveDepthDivisor (104) | 1950 | min 1: +depth/1 (R > depth: null search enters qsearch, 1762) / max 10: +depth/10 | depth/1 <= 128: defined; divisor >= 1, no zero division | as above |
| NullMoveEvalDivisor (105) | 1951 | min 50: (eval-beta)/50 capped at 3 by min() / max 1000: term usually 0 | (eval-beta) >= 0 <= 63744; /50 = 1274 -> min(...,3): defined | as above |
| RfpDepth (106) | RFP gate 1937 | min 0: RFP off (depth <= 0 never in search()) / max 15: to depth 15 | comparison only | the 1923 block, !bare_king, eval < MateInMaxPly |
| RfpMargin (107) | margin 1938; also worsening 1935-1936 (/3 under TtPruneV2, ON in PC20) | min 10: tightest / max 300: widest | 300*15 = 4500 int: defined | as above |
| RfpImproving (108) | 1938 | min 0: improving no help / max 200: -200 when improving | 200*1 int: defined | as above |
| RazorDepth (109) | razor gate 1926 | min 0: razor off / max 6: to depth 6 | comparison only | the 1923 block, !bare_king; fires only if the qsearch falls below alpha |
| RazorBase (110) | 1926 | min 0 / max 1000: +1000 to the margin | 1000 + 1000*6 = 7000 int: defined | as above |
| RazorMultiplier (111) | 1926 | min 0 / max 1000: +1000 per depth | 1000*6 = 6000: defined | as above |
| FutilityDepth (112) | quiet futility 2132; tight margin 2184 (QuietExtinction off in PC20) | min 0: still fires at lmr_depth == 0 (2123 makes lmr_depth >= 0)! / max 15 | comparison only | move loop, quiet, !gives_check, prunable (2126: not the TT move under TtPruneV2), !in_check |
| FutilityBase (113) | margin 2136; improving half 2127 (TtPruneV2); tight 2185 | min 0 / max 500 | static_eval <= 31872 + 500 + 250 + 500*128 = 98122 int: defined | as above |
| FutilityMultiplier (114) | 2136, 2185 | min 0 / max 500: +500 per lmr_depth | 500*128 = 64000: defined | as above |
| LmpBase (115) | lmp_threshold 320, gate 2122 | min 0: skip quiets from move_count >= depth^2 (or /2) / max 20: +20 | 20 + 128^2 = 16404 int: defined | quiet && !skip_quiets |
| HistoryPruneDepth (116) | gate 2143 | min 0: prune only at lmr_depth == 0 / max 10: to lmr_depth 10 | comparison only | quiet, !gives_check, prunable |
| HistoryPruneMultiplier (117) | threshold 2128-2130 (3/4 when not improving under TtPruneV2) | min 0: threshold 0 (prune every negative history) / max 20000: nearly never | -20000*128 = -2.56M int: defined | as above |
| SeeQuietMultiplier (118) | SEE prune 2148 | min 0: see_ge(move, 0) / max 200: -200*lmr_depth^2 | 200*128^2 = 3.28M int: defined | quiet block as above |
| SeeNoisyMultiplier (119) | SEE prune 2166-2167 | min 0: threshold 0 (skip see_ge when picker proves >= 0) / max 1000: -1000*depth | 1000*128 = 128000: defined | capture block (prunable) |
| SingularDepth (120) | singular gate 2192 | min 2: from depth 2; (depth-1)/2 = 0 -> max(1,...) = 1 keeps it in search() (2198, the r4-08 fix) / max 20 | comparison only | mate_moves_==0, !root, move == tt_move, tt bound/depth/score conditions |
| SingularMargin (121) | singular_beta 2194 | min 0: beta = tt_score / max 10: -10*depth | 10*128 = 1280: defined | as above |
| IirDepth (122) | IIR 2033; TtPruneV2 branch 2036 (+2) | min 1: --depth from depth 1 (depth 0 nodes search at new_depth -1 -> qsearch 1762) / max 20 | comparison only | mate_moves_==0, !in_check, tt_move none, (pv or cut); the 2036 branch: cut node, tt upper, !tt_pv |
| ProbcutDepth (123) | probcut gate 1996 | min 1: from depth 1, depth-4 as low as -3 -> qsearch (1762) / max 20 | comparison only | the 1923 block, !is_mate_score(beta), tt guard |
| ProbcutMargin (124) | probcut_beta 1995 | min 0: beta - 50*improving / max 1000: +1000 | 32001+1000 = 33001 int comparison only: defined | as above |
| QsFutilityMargin (125) | qsearch futility_base 1685, used 1702 | min 0: tightest / max 1000: +1000 | 31872+1000 int: defined | qsearch, mate_moves_==0, !in_check, best_score > -MateInMaxPly (1699) |
| AspirationDelta (127) | root windows 2743, 2750-2751, 2785, 2794, growth 2799 | min 4: tight windows / max 200: wide | delta += delta/2+4 exits once the window is full (~65k): defined | root iterations depth >= 4; AspArmLate off in PC20 |
| HistoryBonusQuadratic (128) | history_bonus 324 | min 0 / max 100: +100*depth^2 | 100*128^2 = 1.64M int, then min() with HistoryBonusMax <= 10000: defined; at quad=lin=0 the bonus is the constant -32 (a malus, not UB) | every quiet history update (2350-2358, 2363, update sites of main/continuation/threat/pawn/rework) |
| HistoryBonusLinear (129) | 324 | min 0 / max 500: +500*depth | as above: defined | as above |
| HistoryBonusMax (130) | 324 (cap) | min 100: cap 100 / max 10000: cap 10000 | apply_history clamps to +/-16384; entry*abs(bonus) <= 16384^2 = 2.7e8 int: defined (329) | as above |
| LmrHistoryDivisor (131) | LMR history term 2265 | min 1000: strongest / max 30000: weakest | history/1000, clamped to [-2,2]; divisor >= 1000: defined | LMR block 2254-2256 (move_count > 1 etc.), quiet |
| CheckExtensionDepth (132) | check extension 2218 | min 1: every check (SEE >= 0) extends / max 30 | comparison only | gives_check, !root, mate_moves_==0 |
| LmrCutoffThreshold (133) | 2264 | min 0: term off / max 20: nearly never +1 | comparison only | LMR block; > 0 gate |
| MaterialCorrectionWeight (134) | correction read 1298-1299, update 1334 | min 0: material table unused (gate > 0) / max 300: entry*3 | entry <= 8192 * 300 / 100 = 24576 int32: defined; index masked & (CorrectionSize-1) | corrected_eval/update_correction, > 0 gate |
| CaptureFutilityBase (145) | gate+margin 2156-2162 | min 0 = PC: block OFF / max 1000: ON with +1000 | 31872 + 1000 + 250*128 + ~10000 + hist/8 int: defined | capture, !in_check, !gives_check, prunable, lmr_depth <= CaptureFutilityDepth |
| FailLowContinuationBonus (148) | gate+update 2359-2363 | min 0 = PC: OFF / max 300: x3 the bonus to the parent's continuation | history_bonus <= 10000 * 300 / 100 = 300000 int: defined | all moves failed low, parent quiet move, ply > 0 |
| EvalSwingMult (152) | gate+update 1890-1897 | min 0 = PC: OFF / max 64: swing*4 into the parent's butterfly | swing clamped to +/-400 (1894) * 64 / 16 = 1600 int: defined | !in_check, !excluded, parent static evals known, parent move quiet |

The five untuned (decl, option line, use):
- **QsSeeMargin** (126; 205): read at 1706 in the qsearch move loop under the 1699 gate, which PC20
  satisfies (mate_moves_ == 0). **It is LIVE under PC20** — the only one of the five that is; the job
  file's "why each one changes nothing" has no answer for it. At 40 it prunes captures losing more
  than a pawn-and-a-bit in qsearch.
- **CaptureFutilityMultiplier** (146; 218) and **CaptureFutilityDepth** (147; 219): used only inside
  the capture-futility block, gated by `tune::CaptureFutilityBase > 0` (2156); PC20 has 0: dead.
- **EvalSwingMax** (153; 221): read only inside the EvalSwing block, gated by
  `tune::EvalSwingMult != 0` (1890); PC20 has 0: dead.
- **AspFailHighMaxReduce** (151; 220): read only in the true arm of
  `tune::AspFailHighReduce != 0 && ...` (2766-2767); PC20 has the default 0: dead.

(4) **The positive control** (scratch build $HOME/build/job26/plant, one planted line
`volatile int bt26_plant = tune::HistoryBonusMax * 250000;` at the root entry, search.cpp:2460;
compile lines: step2/compile_line.txt):
- HistoryBonusMax 10000, first 5 O positions, go depth 6, PC20: exit 1, zero bestmoves, line 2 of
  control/ctrl_10000.txt: `.../search.cpp:2460:53: runtime error: signed integer overflow:
  10000 * 250000 cannot be represented in type 'int'` — the run stops, as required.
- HistoryBonusMax 2212, same: exit 0, five bestmoves, no sanitizer line (control/ctrl_2212.txt).
The harness sees planted UB and passes a clean run: not blind.

(5) **Step 2 table and count**: step2/table.txt, built by a committed command over **77 files read
(77 of 77)**: 76 corners + base, each 40 searches (O[0:20], G[0:20], go depth 9, ucinewgame + isready
before each, one fresh process per corner, Threads 1, Hash 16, the settings sent in each
step2/<tag>.input.log). **Every row: searches 40, bestmoves 40, exit 0, sanitizer lines 0, no hang,
no refusal.** Node sums and ratios to base in the table; extremes: RfpMargin min 0.4041,
LmrQuietBase min 1.6270, SingularDepth min 1.6086; flat: DrawJitter max, CaptureFutilityBase max,
HistoryPruneDepth max (all 1.0000 to the node). Curiosity, not an anomaly: NullMoveBase max and
NullMoveDepthDivisor min give the same sum 405179, and HistoryPruneDepth min and
HistoryPruneMultiplier max give 405370; the input logs (spot-checked, quoted in step2/) show the
right option in each, so these are configuration coincidences, not tag mix-ups.

## The standing form

**Three plain lines.** Asked: what each end of the 40 tuned search settings does in the PC build's
code, and whether any end is undefined behaviour, checked under sanitizers. Answer: every end is
defined; all 40 are live in the code (four only at their max, being gated on/off switches at 0);
0 sanitizer lines in 77 corner runs, the harness proven on a planted overflow. How sure: the reading
is complete for the 45 names (every use site quoted); the measurement covers depth-9 searches on 40
positions, not the whole space the tuner walks.

**Step table.**
| step | done? | evidence | result |
|---|---|---|---|
| Step 0 pins | done | step0/*.txt, step0/range_check.txt | 8/8 met; 0 range diffs |
| Step 1 reading | done | section (3) above | 45 settings, all use sites, bounds |
| prediction | done | prediction.txt (own commit) | P1/P2/P3 all survive |
| positive control | done | control/ | abort+line at 10000, clean at 2212 |
| Step 2 corners | done | step2/ (77 raw files) | 77/77 clean, table.txt |

**Findings.**
1. QsSeeMargin is live under PC20 (search.cpp:1706; gate 1699 true in PC20): the only one of the five
   untuned that is not gated off. Show again: `grep -n "QsSeeMargin" src/search.cpp`.
2. FutilityDepth min 0 does NOT switch futility off: lmr_depth is max(0, ...) (2123), so
   `lmr_depth <= 0` (2132) still holds wherever the reduction eats the depth. Show: lines 2123, 2132.
3. HistoryBonusQuadratic = HistoryBonusLinear = 0 makes history_bonus a constant -32 (324): a small
   malus at every quiet update, not a zero.
4. The r4-08 singular fix (2198) is what keeps SingularDepth 2 defined; ProbcutDepth 1, IirDepth 1 and
   NullMoveDepthDivisor 1 all land in the defined `depth <= 0 -> qsearch` path (1762).
5. DrawJitter's setter (3049-3054) clears the hash on every change; the tuner changing it mid-run
   restarts the TT. Its root shortcut (2584-2587) is compiled out under FORGE_FIX_ROOT_DRAWN=1.
Suspicions, not proven: the three flat corners (DrawJitter max, CaptureFutilityBase max,
HistoryPruneDepth max) may not have EXECUTED their code on these 40 positions at depth 9 (no counter
was run); NullMoveBase max = NullMoveDepthDivisor min and HistoryPruneDepth min =
HistoryPruneMultiplier max node sums look like coincidences, input logs checked, not re-derived.

**From my colleagues.** Read: deepseek5's NOTES (tail: the stage-label fix and the corrected
killer/countermove regret rates) and REPORT_deepseek5_job30.md (its mode 4 = identity: the TT move is
never history-pruned — matches the PC build's `prunable = !tt_prune_v2_ || move != tt_move` at 2126,
which my Step 1 rows rely on; its stand5 self-play runner protocol note). Applied: the TT-move
exemption reading in the HistoryPrune rows; the known-right build line from my own notes (pins met
first try). glmflash5: no branch exists (`git fetch` finds nothing) — nothing to read.
Not checked further: deepseek5's cross4 rows (not needed here).

**What I did NOT do.** No counter build to prove the three flat corners execute their code. No runs
deeper than 9 or on positions beyond the first 20 of each set. The five untuned settings were read,
not run. Job 27's file was read (its "do the lowest open job first" rule applied: job 26 had no
report) but none of its content is this job.

**What I am NOT sure about.** (a) The three exact-1.0000 corners: code live but idle, or never
reached. (b) The bounds in (3) are by reading against MaxPly = 128 and the declared ranges; a
sanitizer run at depth 9 exercises less. (c) The aspiration delta bound (loop exits at full window)
is argued, not measured.

**A better way.** (1) Run the four skipped ends (min == PC value) as identity corners: 4 extra runs
cost ~8 s and PROVE the harness sets options correctly (their node sums must equal base to the node)
instead of trusting the skip rule. (2) A one-line "ran" counter behind a scratch option for
gate-proved features would turn P1's "consistent" into "confirmed" for flat corners; it is the same
pattern as job 23's counting build, and step 2 already proves the build harness in 15 s.
(3) xargs -P4 cut 77 runs to 33 s wall; future corner jobs should state the allowed parallelism so a
helper neither serializes nor guesses.

**Times:** see stamps.txt. **Model:** Kimi K3 (this runtime names itself so), run name kimi5.
`git status --short` and `ls -R` of the job folder: final_ls.txt (the last command before this commit).
