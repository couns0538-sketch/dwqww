# O8 [test plan G-C5] Correction-history extensions (UCI CorrExt, default 0) — DONE

Branch `opus-O8` = `opus-O3` (`0d99f02`) + [O8] commits:
- `5f6879a` engine: UCI option, extension rule with per-path budget, second instance of the main search
- `a7df3bd` tests: `tests/corr_ext_tests.cpp` (+ CMake/CTest)
- `70b663a`, `f19697f` evidence only: scripts, logs, TSan hook, quiet-runner NPS workflow, CI logs, SHA256SUMS

`patch.diff` = `git diff 294dbed HEAD`; `patch_o8_only.diff` = O8 on top of `0d99f02`. Ideas: `IDEA_SOURCE.md`
(OPUS_TOP_ENGINES_2025_2026; Stockfish PR #5767 "Correction History Quad Extensions"; CPW; concepts only, own
code and constants). UNPROVEN until gated; no Elo claim. Independent of O5 (it does not contain O5).

## What it does
- **Measure:** `|correction| = |static_eval - raw_eval|`, as in O5 (0 in check).
- **Rule** (`include/forge/corr_ext.hpp`), applied when the TT move is singular (`singular_score < singular_beta`):

  | | AL1 s198 | CorrExt 1 |
  |---|---|---|
  | double (2) | `!pv && ss < sb - 24 && path <= 6` | `!pv && ss < sb - max(0, 24 - \|c\|*CorrExtDoublePct/100) && room >= 1` |
  | triple (3) | — | `!pv && \|c\| >= CorrExtTripleCorr && ss < sb - CorrExtTripleMargin && room >= 2` |
  | path count | `path + (ext == 2)` | `path + max(0, ext - 1)` |

  `room = CorrExtBudget - path`. Defaults: CorrExtDoublePct 12, CorrExtTripleCorr 48 (0 = no triple),
  CorrExtTripleMargin 100, CorrExtBudget 7.
- **The triple** is Forge's analogue of the report's "quad" level, because Forge has no triple extension.
- **Per-path budget:**
  - In the CorrExt instance `SearchStack::double_extensions` counts the extra plies on the path; a double costs 1,
    a triple costs 2.
  - An extension e > 1 is granted only while the count plus e - 1 stays within CorrExtBudget.
  - The default 7 is AL1 s198's allowance of 7 doubles per path, so the added depth along any path is bounded
    exactly as in AL1 s198.
  - With |correction| 0, or every weight 0 (budget 7), the rule is AL1 s198's.
- **Tunables** are defined before the AL1 block, as in O5.
- **UCI:** `option name CorrExt type spin default 0 min 0 max 1`.
- **Code layout:** the same as O5. alphabeta.inc is compiled twice (`Worker::search` = AL1 s198,
  `Worker::search_corr_ext` last in the unit), with root dispatch once per iteration and its own `lmp_threshold`
  copy (`src/search/corr_ext.inc`). The default search's GIMPLE, SSA versions included, is identical to O3's
  (`logs/codegen_second_instance.log`).

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS** (PC recipe and Linux CI): 312866/862329/3024920/12389307/34048354, perft 4865609, kiwipete 193690690, FMA 0 |
| 2 | extension-budget unit test (never exceeds cap) | **PASS**: rule-level, random-path, node-level and whole-search checks (below); 19/19 planted bugs caught |
| 3 | ON bench differs at d13 | **PASS**: d13 838790 vs 862329 |
| 4 | gate primary at 40+0.4 | gate spec below (QA runs gates) |
| §3 | ASan+UBSan / ctest known failures only / TSan | **PASS**: CI run 40475294927, all three jobs; TSan 0 reports incl. CorrExt Threads 2/4 hook |
| §3 | Threads=1 determinism | **PASS**: ON bench x5 twice identical; the test also checks ON twice |
| brief 5 | OFF hot code / layout | **PASS** on the PC recipe: every hot function instruction-identical at the same address mod 64 (only the driver changed); data notes below |

### 1. OFF identity (`logs/identity_pc_recipe.log`)
```
$ build_pc.sh <opus-O8 tree> forge_o8.exe      FMA count: 0
$ python 2_build/uci_check.py forge_o8.exe --full
bench d11 nodes 312866 ref 312866 OK
bench d13 nodes 862329 ref 862329 OK
bench d16 nodes 3024920 ref 3024920 OK
bench d20 nodes 12389307 ref 12389307 OK
bench d22 nodes 34048354 ref 34048354 OK
perft5 startpos 4865609 ref 4865609 OK
perft5 kiwipete 193690690 ref 193690690 OK
ALL OK
```
Linux CI (40475294927, release, g++-14.2): the same, ALL OK, FMA 0.

### 2. ON bench pins (`logs/on_bench_run1.log`, `run2.log`, identical; Threads 1, Hash 16, OwnBook false)
```
$ python on_bench.py forge_o8.exe 11,13,16,20,22 CorrExt=1
bench d11 nodes 312961   (+0.03%)
bench d13 nodes 838790   (-2.73%)
bench d16 nodes 2891507  (-4.41%)
bench d20 nodes 12313394 (-0.61%)
bench d22 nodes 33298237 (-2.20%)
```
Pins: **d11 312961, d13 838790, d16 2891507, d20 12313394, d22 33298237.** With CorrExt 1 and every weight 0
(DoublePct 0, TripleCorr 0, Budget 7) the bench equals the lock's at all 5 depths (`logs/on_bench_zero_weights.log`).

### 3. Unit tests (`tests/corr_ext_tests.cpp`, `logs/corr_ext_tests.log`)
- **Rule vs the AL1 s198 rule** written out in the test:
  - identical at |correction| 0, and with all weights 0 for every |correction|;
  - path accounting equals AL1's for extensions -2..2;
  - extensions in {1,2,3}; PV nodes get 1;
  - monotonic in |correction|, in the singular margin and in the budget used;
  - a triple only with a large correction and margin;
  - double-margin and triple boundaries (margin 24 at c 0, 18 at c 50; triple needs |c| >= 48 and margin > 100;
    budget 7: a triple needs 2 plies of room, a double 1);
  - over the defaults, budgets 0..12 and 12 random weight sets: **8,809,020 rule decisions**.
- **Budget:**
  - for every input the path never exceeds CorrExtBudget, and above the budget there is no extra ply;
  - 20,000 random paths (up to MaxPly plies, random weights) never exceed it, and the path count equals the sum of
    extra plies granted (55,549 doubles, 30,139 triples, 1,121,405 plies at the cap).
- **Node decisions** through `SearcherTestProbe` (10 cases):
  - Setup: a planted TT entry makes exd5 a hugely singular TT move that fails high; a correction is planted in the
    pawn table; RFP, null move and ProbCut are disabled via tunables; SearchStack::double_extensions is read back
    after the search.
  - Default instance: double (+1); with 7 already used, +0.
  - CorrExt: |c| 0 -> +1; |c| 47 -> +1; |c| 50 -> triple (+2).
  - Room 2 -> +2 (up to the cap); room 1 -> +1; budget used up -> +0; triple off -> +1; budget 2 with 1 used -> +1.
  - No stack frame ends above the budget.
- **Whole searches** (bench FENs, depth 11):
  - CorrExt 0 gives 312866;
  - CorrExt 1 with all weights 0 equals the default search;
  - double alone, triple alone and budget 0 alone each change the search;
  - aggressive settings with budgets 0..3 leave every stack frame within the budget;
  - the weights are inert with CorrExt 0, and ON is deterministic.
```
corr_ext: checks=137 rule decisions evaluated=8809020 failures=0
PASS corr_ext_tests
```
- **Planted bugs** (`mutation_check.sh`, `logs/mutation_check.log`): the control passes and **19/19 are caught**:
  - triple room off by one, double room off by one, budget ignored;
  - a triple counted as 1 ply, negative extensions counted;
  - double-margin sign, its lock constant 25, no floor at 0;
  - triple threshold ignored, strict instead of >=, triple margin inclusive;
  - PV not excluded, correction size computed in check;
  - the search using AL1 accounting, a zero correction, or the path budget from the root;
  - the lmp_threshold copy differing;
  - dispatch ignored, dispatch inverted.

### 4. CI (`logs/ci/RUN.log`)
- opus-ci **40475294927** (commit 70b663a; engine 5f6879a): success.
  - release: identity ALL OK, ctest 17/18 with only the 4 known lines;
  - asan: the same, no report (`forge_corr_ext_tests` 29.1 s);
  - tsan: the same, TSan 0 reports; `tsan_extra.sh` (CorrExt 1, Threads 2 and 4, depth 8) gave 8/8 legal
    bestmoves.
- opus-o8-nps **40475295034**: success.
- Local ctest (g++ 15.2): 17/18 with only the 4 known lines.

### 5. OFF codegen, data layout, NPS
- **Codegen** (`logs/codegen_compare.log`), PC recipe, lock vs O8:
  - alpha-beta 2413 = 2413, **0 differing**, start 32 = 32 mod 64;
  - every listed hot function identical at the same address mod 64 (MovePicker::next: the known 32 padding lines);
  - the driver `Worker::search(Board, ...)` changes (2119 -> 2125 instructions, start 48 -> 16 mod 64; once per
    iteration).
- **Data layout** (`logs/data_layout_check.log`):
  - hot tables keep their offset mod 4096 (DistanceMasks keeps mod 64);
  - the two zero-initialised AL1 tunables move 4 bytes within the same 64-byte line;
  - the search unit's copy of `SeePieceValue` (28 bytes, read by capture_value) moves from 48 to 16 mod 64,
    because the second instance adds read-only data before it; it now fits in one cache line instead of two;
  - the std::thread lambda typeinfo/vtable also moved (not hot).
- **PC NPS** (`logs/nps_ab_lock_vs_o8_pc.log`, 10 ABBA runs, busy PC), node counts equal:
  - d16 wall +3.01% [+0.29, +5.72] (cpu +3.06%);
  - d20 wall +3.89% [+1.36, +6.42] (cpu +2.88%);
  - O8 measured faster on the loaded machine. The hot code is identical, so no speed claim: no slowdown.
- **Quiet runner** (40475295034, g++-14):
  - lock vs O8: d16 -0.74% [-1.54, +0.06], d20 +0.95% [-0.55, +2.46];
  - O3 vs O8: d16 +0.04% [-0.68, +0.76], d20 +0.09% [-0.54, +0.71];
  - no measurable change.
- **Linux g++-14 codegen**, O3 vs O8: alpha-beta 2500 vs 2501 instructions, 3 lines, same start mod 64; everything
  else identical. This is the same 3 lines as O5; g++ 15.2 gives 0.

### 6. Calibration: how the defaults were chosen (`logs/singular_extension_distribution.log`, `logs/calibration_*.log`)
- **Singular tests are rare but compound:** 3,367 at d13, 15,645 at d16, 92,597 at d20. The median |c| at singular
  tests is 6, 26 and 50 cp.
- **Probe estimates:**
  - a double margin of 24 - |c|*25/100 adds 6%, 18% and 25% doubles at d13/16/20;
  - a triple at |c| >= 32 with margin > 100 would fire on 4.1-7.6% of singular extensions.
- **Node sweeps** (50 positions at d13/d16, 20 positions at d20; ratio of total nodes, geomean in brackets):

  | setting (DoublePct/TripleCorr/TripleMargin) | d13 | d16 | d20 |
  |---|---|---|---|
  | 25/32/100 | 0.974 | 1.056 (1.059) | **1.470 (1.255)** |
  | double 25 alone | — | 1.135 | 1.282 |
  | **chosen 12/48/100 (budget 7)** | 0.987 | 1.061 (1.024) | 1.097 (1.118) |

  25/32/100 grew the d20 tree too much. The chosen defaults keep the fixed-depth node count inside the +10% band at
  d13/d16 on the 50 positions and on bench (bench d11 +0.03%, d13 -2.73%, d16 -4.41%, d20 -0.61%, d22 -2.20%).

## Proposed gate (one option)
- **G-C5:** candidate opus-O8 exe (PC recipe) with `option.CorrExt=1` vs the AL1 s198 lock exe.
  - **Primary gate 40+0.4** (test plan: the idea "lost at STC"), SPRT [0,10] nElo, Threads 1, Hash 16, OwnBook
    false, 8moves_v3, cap 1500.
  - srand from the test plan (113016036) or as QA assigns.
  - A 10+0.1 run is informational only. An H1 needs a confirm (new openings order, new srand).
- **Sub-gates without a rebuild:** `CorrExtTripleCorr=0` (double-margin part only) or `CorrExtDoublePct=0`
  (triple part only).

## Open issues / notes
- **Depth growth:** extensions compound with depth (d20 +10% total, +12% geomean on 20 positions). In games the
  correction tables stay warm, so |correction| and the extension rate will be higher than in bench. QA may prefer
  to screen at d20/d22 as well.
- **Linux g++-14:** 3-line alpha-beta difference vs O3 (see above).
- **Data placement:** the SeePieceValue copy now sits at 16 instead of 48 mod 64 (see above).
- **Merge:** the same as O5. One options instance with runtime tests and its own lmp_threshold copy; the
  `double_extensions` meaning (extra plies) holds only in that instance; options and uci.cpp merge as a union.
- **Related history:** E28 (SingularMargin 1, more extensions everywhere) lost; P22 proposed rarer doubles. O8
  extends more only where |correction| is large, with the path budget unchanged.
- **Housekeeping:** early O8 builds are under `D:\...\worktrees\b\o8_v1`, `o8_final`, `o8_cm`, `o8_mut` (before
  the F: rule); later ones under `F:\opus_scratch\build\o8_*`; nothing was deleted.

## Files
- Engine and tests: `include/forge/corr_ext.hpp`, `include/forge/search_options.hpp`, `include/forge/search.hpp`,
  `include/forge/search_tune.hpp`, `src/search.cpp`, `src/search/alphabeta.inc`, `src/search/corr_ext.inc`,
  `src/search/iterative.inc`, `src/search/options.inc`, `src/search/tune.inc`, `src/uci.cpp`,
  `tests/corr_ext_tests.cpp`, `CMakeLists.txt`; `.github/workflows/opus-o8-nps.yml`.
- `opus_round1/O8`: `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_o8_only.diff`, `on_bench.py`,
  `node_sweep.py`, `smp_smoke.py`, `tsan_extra.sh`, `mutation_check.sh`, `data_layout_check.py`, `fn_extract.py`,
  `correction_size_probe/` (probe diff, analyze.py, analyze_se.py), `logs/` (incl. `logs/ci/`), `SHA256SUMS`.
  SHA256SUMS currently covers everything except REPORT.md and needs regenerating after REPORT.md is added.

## Review by the main session (2026-10-27)
The implementation was done by a sub-agent. The main session rebuilt `opus-O8` with the PC lock recipe and
re-checked:
- the OFF identity at all 5 depths, perft, kiwipete and FMA 0;
- the ON bench d13 pin;
- `codegen_compare.sh` against the lock exe: every listed hot function, alpha-beta included, is identical at
  the same address mod 64, apart from the per-iteration driver and the known `MovePicker::next` padding.

All match the evidence above (`logs/review_main_session.log`).
