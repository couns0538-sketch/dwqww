# O5 [test plan G-B3] Correction-size pruning margins (UCI CorrMargins, default 0) — DONE

Branch `opus-O5` = `opus-O3` (`0d99f02`) + [O5] commits:
- `3c171dd` engine: UCI option, margin functions, second instance of the main search
- `6667bbe` tests: `tests/corr_margins_tests.cpp` (+ CMake/CTest)
- `1645eea`, `de74ee1`, `4290bc0` evidence only: scripts, logs, TSan hook, quiet-runner NPS workflow, CI logs,
  SHA256SUMS (no engine change after `3c171dd`)

`patch.diff` = `git diff 294dbed HEAD` (engine tree incl. O3); `patch_o5_only.diff` = O5 on top of `0d99f02`.
Ideas: `IDEA_SOURCE.md` (OPUS_TOP_ENGINES_2025_2026; Stockfish PR #5748 and #5727, CPW "Static Evaluation
Correction History"; concepts only, own code and constants). UNPROVEN until gated; no Elo claim.

## What it does
- **Measure.** `|correction| = |ss->static_eval - ss->raw_eval|`, the correction-history adjustment actually
  applied at the node (pawn + material tables; 0 in check). Both values are already on the stack, so it costs
  nothing. With the default weights it is at most 64 cp (128 cp with MaterialCorrectionWeight 300).
- **Margins** (`include/forge/corr_margins.hpp`). Each is the AL1 s198 formula plus a term that is 0 at
  |correction| 0, monotonic, and 0 when its weight is 0:

  | decision | AL1 s198 | with CorrMargins 1 | weight (default) |
  |---|---|---|---|
  | reverse futility | `eval - (72*d - 40*improving) >= beta` | margin `+ \|c\| * CorrRfpPct / 100` | CorrRfpPct 50 |
  | null-move try | `static_eval >= beta - 24*d + 180` | threshold `+ \|c\| * CorrNullMovePct / 100` | CorrNullMovePct 50 |
  | quiet futility | `static_eval + 100 + 110*lmr_d <= alpha` | margin `+ \|c\| * CorrFutilityPct / 100` | CorrFutilityPct 100 |
  | LMR | `r` (after all AL1 adjustments) | `r - min(r, r*\|c\|*CorrLmrPct/6400)` for r > 0 | CorrLmrPct 25 |

  Larger correction means less trust in the static eval, so the search prunes and reduces less.
- **The LMR term** is a share of the reduction: 25% of it per 64 cp at the default.
  - It therefore only cuts reductions of 4 or more plies, and only at large corrections.
  - This is the "fractional / depth-scaled" rewrite the idea board asked for after P7. P7 used a whole-ply
    `r -= 1` above a threshold; gate G16 ended cap with no decision, and the board noted "+69% nodes at d20".
- **Weights** are tunables (`tune::CorrRfpPct`, `CorrFutilityPct`, `CorrNullMovePct`, `CorrLmrPct`, range
  0..400).
  - Every build accepts them via `setoption`; `FORGE_EXPOSE_TUNABLES` builds advertise them.
  - They are defined before the AL1 s198 tunables. GCC emits a unit's globals in reverse order, so every AL1
    tunable keeps its address.
- **UCI:** `option name CorrMargins type spin default 0 min 0 max 1` (`forge/search_options.hpp`,
  `src/search/options.inc`, `src/uci.cpp`).

### Code layout (option off = AL1 s198 machine code)
- `alphabeta.inc` is compiled twice (C6's technique):
  - `Worker::search` is the AL1 s198 function, token-identical apart from the function-name macro.
  - `Worker::search_corr_margins` is last in the unit; the margin code sits in `#if FORGE_SEARCH_CORR_MARGINS`
    blocks.
  - The root (`iterative.inc`) picks the instance once per iteration, so with the option off no node tests it.
  - qsearch is shared and unchanged.
- **New finding (also applies to C6).** A second instance alone changed the default search: 2413 -> 2409
  instructions and 150 differing lines, exactly C6's numbers.
  - Cause (`logs/codegen_second_instance_investigation.log`, GIMPLE and inliner dumps): the static helper
    `lmp_threshold` has one caller in AL1 s198 and the early inliner inlines it. With a second caller GCC leaves
    it to the IPA inliner. That shifts the SSA numbering of the default search, so one of the eight
    check-extension comparisons gets its operands swapped and the block layout follows.
  - `[[gnu::always_inline]]` perturbs the code differently and was rejected.
  - Fix: the second instance calls its own copy, `lmp_threshold_corr_margins` (`src/search/corr_margins.inc`,
    included just before the second instance).
  - Result: the default search's GIMPLE (SSA versions included) and machine code are identical to AL1 s198.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS** (PC recipe and Linux CI): 312866/862329/3024920/12389307/34048354, perft 4865609, kiwipete 193690690, FMA 0 |
| 2 | ON bench differs at d13 | **PASS**: d13 858019 vs 862329 |
| 3 | unit test: margin function monotonic in \|correction\| and identical to the lock at correction 0 | **PASS**: `forge_corr_margins_tests` 55,390 checks, 0 failures; 20/20 planted bugs caught |
| 4 | ASan/UBSan clean | **PASS**: CI asan job (`-fno-sanitize-recover=all`), 0 reports, only the 4 known lines |
| §3 | ctest only the known failures | **PASS**: 17/18, only `forge_tests` with its 4 known lines (PC; CI release, asan, tsan) |
| §3 | TSan (no threading added; checked anyway) | **PASS**: 0 reports, incl. hook CorrMargins=1 at Threads 2 and 4 |
| §3 | Threads=1 determinism | **PASS**: ON bench x5 twice identical; the test also checks ON twice |
| brief 5 | OFF hot code / layout | **PASS** on the PC recipe: every hot function instruction-identical at the same address mod 64 (only the per-iteration driver changed); see notes for Linux g++-14 |

### 1. OFF identity (`logs/identity_pc_recipe.log`)
```
$ build_pc.sh <opus-O5 tree> forge_o5.exe      (MSYS2 ucrt64 g++ 15.2, exact build_windows.ps1 flags)
FMA (vfmadd/vfmsub/vfnmadd) count: 0
$ python 2_build/uci_check.py forge_o5.exe --full
bench d11 nodes 312866 ref 312866 OK
bench d13 nodes 862329 ref 862329 OK
bench d16 nodes 3024920 ref 3024920 OK
bench d20 nodes 12389307 ref 12389307 OK
bench d22 nodes 34048354 ref 34048354 OK
perft5 startpos 4865609 ref 4865609 OK
perft5 kiwipete 193690690 ref 193690690 OK
ALL OK
```
Linux (CI run 40470507779, release job, g++-14.2 box recipe): the same 7 lines, ALL OK, FMA 0.

### 2. ON bench pins (`logs/on_bench_run1.log`, `on_bench_run2.log`; Threads 1, Hash 16, OwnBook false)
```
$ python on_bench.py forge_o5.exe 11,13,16,20,22 CorrMargins=1        (twice, identical)
bench d11 nodes 343365   (+9.75% vs AL1 s198)
bench d13 nodes 858019   (-0.50%)
bench d16 nodes 2522546  (-16.61%)
bench d20 nodes 12894582 (+4.08%)
bench d22 nodes 22287047 (-34.54%)
```
Pins for QA: **d11 343365, d13 858019, d16 2522546, d20 12894582, d22 22287047.**
With CorrMargins 1 and every weight 0 the bench equals the lock's at all 5 depths (`logs/on_bench_zero_weights.log`).

### 3. Unit tests (`tests/corr_margins_tests.cpp`, `logs/corr_margins_tests.log`)
- **Margin functions** vs the AL1 s198 formulas written out in the test, for |correction| 0..136:
  - identical at |correction| 0;
  - monotonic: margins never shrink; the LMR value never grows, stays in [0, r], and r <= 0 is untouched;
  - inert at every |correction| when the weight is 0, and a strict change when it is not;
  - over the default, zero and 40 random tunable sets, including random RfpMargin, RfpImproving, FutilityBase
    and FutilityMultiplier.
- **Node decisions** through `SearcherTestProbe`: a direct non-PV node search at ply 1 with a correction planted
  in the pawn table.
  - Reverse futility prunes exactly when `eval - margin >= beta` with the widened margin (boundaries 20/25/26/28%
    at 40 cp vs slack 10).
  - The null move is tried exactly when the raised threshold allows (boundaries 12/13 cp).
  - The default instance ignores the correction size.
- **Whole searches** through the public `Searcher`, bench FENs at depth 11:
  - CorrMargins 0 gives the bench d11 total 312866;
  - CorrMargins 1 with all weights 0 is node-for-node (nodes, best move, score) the default search;
  - each weight alone changes the search;
  - the weights are inert while CorrMargins is 0;
  - ON run twice is identical.
```
corr_margins: checks=55390 failures=0
PASS corr_margins_tests
```
- **Planted bugs** (`mutation_check.sh`, `logs/mutation_check.log`): the control passes and **20/20 are caught**:
  - sign flips of the RFP, futility and null-move terms;
  - lock-constant offsets (RFP +1, null-move 181);
  - futility reading the wrong weight;
  - LMR without the cap, LMR touching r <= 0, LMR scale /3200;
  - correction size computed in check, or signed;
  - the search instance using |correction| 0 for RFP, null move or futility;
  - the LMR term skipped, or the correction never computed;
  - the lmp_threshold copy differing, or an extra LMR change at zero weights;
  - dispatch ignored, dispatch inverted.

### 4. Sanitizers and CI (`logs/ci/RUN.log`)
- opus-ci run **40470507779** (commit 1645eea, engine = 3c171dd) and rerun **40472484330** (de74ee1): success.
  - release: identity ALL OK, ctest 17/18 with only the 4 known lines;
  - asan (ASan+UBSan): the same, no report (`forge_corr_margins_tests` 16.9 s);
  - tsan: the same, TSan 0 reports; `tsan_extra.sh` (CorrMargins 1, Threads 2 and 4, 4 positions, depth 8) gave
    8/8 legal bestmoves.
- Local: ctest (CMake Release, g++ 15.2) 17/18 with only the 4 known lines (`logs/ctest_release*.log`).

### 5. OFF codegen, data layout, NPS
- **Codegen** (`logs/codegen_compare.log`, O3's `codegen_compare.sh`, PC recipe), lock vs O5:
  - alpha-beta 2413 = 2413 instructions, **0 differing**, start 32 = 32 mod 64;
  - identical at the same address mod 64: qsearch, MovePicker::next (the known 32 padding lines),
    static_evaluate, TT probe/store, should_stop, is_draw, corrected_eval, update_correction, all history
    functions, record_move, NNUE update/evaluate/refresh, make/unmake, see_ge;
  - only `Worker::search(Board, ...)`, the once-per-iteration driver with the dispatch, differs (2119 -> 2122
    instructions, start 48 = 48 mod 64).
- **Data layout** (`logs/data_layout_check.log`):
  - every hot table keeps its offset mod 4096 (DistanceMasks keeps mod 64);
  - the four new tunables follow the AL1 block;
  - `options::corr_margins` opens the search unit's .bss, so the two zero-initialised AL1 tunables
    (CaptureFutilityBase, FailLowContinuationBonus) move by 4 bytes inside the same 64-byte line, as in C2/C6.
- **PC NPS** (`logs/nps_ab_lock_vs_o5_pc.log`, nps_ab.py, 10 ABBA runs, busy PC, A/A band about +-2%), node
  counts equal:
  - d16 wall -1.64% [-3.81, +0.53] (cpu -1.76%);
  - d20 wall -0.54% [-1.98, +0.91] (cpu -0.93%).
- **Quiet GitHub runner** (`opus-o5-nps.yml`, box recipe g++-14):

  | pair | run | d16 wall | d20 wall |
  |---|---|---|---|
  | lock vs O5 | 40470507851 | +0.84% [-3.09, +4.77] | -0.61% [-3.25, +2.04] |
  | lock vs O5 | 40472484111 | -0.12% [-1.54, +1.31] | +1.54% [+0.40, +2.69] |
  | O3 vs O5 | 40470507851 | -0.26% | -0.84% |
  | O3 vs O5 | 40472484111 | -0.72% | -0.06% |

  No measurable slowdown.

### 6. Calibration: how the defaults were chosen (`logs/calibration_*.log`, `logs/correction_size_distribution.log`)
- **|correction| grows with search length.** Bench clears the tables per position; games keep them. Median /
  90th percentile at main-search nodes: 0/32 cp at d13, 4/42 at d16, 12/62 at d20.
- **Only LMR changes nodes systematically.** The RFP, null-move and futility weights change fixed-depth node
  counts with no consistent sign (bench is chaotic). The LMR weight is the systematic driver, over 50 positions at
  d16:
  - weight 25 alone: +4.2% total nodes;
  - weight 50 alone: +12.7%;
  - weight 100 alone: +118%.
- **Defaults 50/100/50/25** stay inside the history's pre-gate node rule (d13/d16 <= +10%):
  - over 50 positions: d13 +5.8% total (geomean -2.4%), d16 +4.5% (geomean +1.3%);
  - bench: d13 -0.5%, d16 -16.6%;
  - d11 +9.75% (just under the flag), d20 +4.1%, d22 -34.5%.

## Proposed gate (one option)
- **G-B3:** candidate opus-O5 exe (PC lock recipe) with `option.CorrMargins=1` (default weights) vs the AL1 s198
  lock exe (833C47F3...22B3).
  - fastchess per `6_gate/GATE_RULES.md`: 10+0.1, Threads 1, Hash 16, OwnBook false, 8moves_v3 book, SPRT [0,10]
    nElo, cap 1500.
  - srand from the test plan (G-B3: 1162618901) or as QA assigns.
  - An H1 needs the standard confirm gate (new openings order, new srand). The CPW / Stockfish notes say
    correction-based terms gain more at longer TC, so a 40+0.4 confirm is the natural second step.
- **To split it:** each part is a weight (`CorrRfpPct`, `CorrFutilityPct`, `CorrNullMovePct`, `CorrLmrPct`). A
  sub-gate is `CorrMargins=1` with the other three weights at 0, without a rebuild.

## Open issues / notes
- **Linux g++-14 (box recipe):**
  - O3 vs O5 alpha-beta differs by 3 lines (2500 vs 2501 instructions, same start mod 64); every other hot
    function is identical (`logs/ci/de74ee1_run40472484111_o5-nps/codegen_o3_vs_o5_linux.log`).
  - g++ 15.2 (the PC/gate recipe) gives 0 lines, and the quiet-runner NPS shows no change.
  - Separately, O3 itself moved several Linux start addresses mod 64 relative to the lock
    (`codegen_lock_vs_o3_linux.log`).
- **Merge with other option branches:**
  - C6 (CuckooRep) and O8 (CorrExt) also compile alphabeta.inc a second time.
  - A union build should keep the default instance plus ONE "options" instance whose features test their
    options, with its own lmp_threshold copy.
  - The `#if FORGE_SEARCH_CORR_MARGINS` blocks are written so they can become `if (options::corr_margins)` there.
  - `search_options.hpp` / `options.inc` / uci.cpp lines merge as a union.
- The C6 branch can reuse the lmp_threshold-copy fix to remove its 150-line alpha-beta difference.
- Compiler warnings: the same 6 pre-existing -Wconversion warnings; the three in alphabeta.inc appear once per
  instance (`logs/compiler_warnings.log`).
- Housekeeping: scratch builds are under `D:\grok-pc-data\dwqww\.claude\worktrees\b\o5_*` (made before the F: rule)
  and `F:\opus_scratch\build\o5_*`; nothing was deleted.

## Files
- Engine and tests: `include/forge/corr_margins.hpp`, `include/forge/search_options.hpp`,
  `include/forge/search.hpp`, `include/forge/search_tune.hpp`, `src/search.cpp`, `src/search/alphabeta.inc`,
  `src/search/corr_margins.inc`, `src/search/iterative.inc`, `src/search/options.inc`, `src/search/tune.inc`,
  `src/uci.cpp`, `tests/corr_margins_tests.cpp`, `CMakeLists.txt`; `.github/workflows/opus-o5-nps.yml`.
- `opus_round1/O5`: `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_o5_only.diff`, `on_bench.py`,
  `node_sweep.py`, `smp_smoke.py`, `tsan_extra.sh`, `mutation_check.sh`, `data_layout_check.py` (from C6),
  `fn_extract.py`, `correction_size_probe/` (instrumentation diff + analysis), `logs/` (incl. `logs/ci/`),
  `SHA256SUMS`. SHA256SUMS currently covers everything except REPORT.md and needs regenerating after REPORT.md is
  added.

## Review by the main session (2026-10-27)
The implementation was done by a sub-agent. The main session rebuilt `opus-O5` with the PC lock recipe and
re-checked:
- the OFF identity at all 5 depths, perft, kiwipete and FMA 0;
- the ON bench d13 pin;
- `codegen_compare.sh` against the lock exe: every listed hot function, alpha-beta included, is identical at
  the same address mod 64, apart from the per-iteration driver and the known `MovePicker::next` padding.

All match the evidence above (`logs/review_main_session.log`).
