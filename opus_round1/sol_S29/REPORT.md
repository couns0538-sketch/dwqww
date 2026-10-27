# S29 [Sol leftover] Speed stack (FORGE_SPEEDSTACK) — DONE (node-exact; NPS advisory only)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 10. Branch `opus-sol-S29` = `d4f4312` (AL1 lock tree + baseline
evidence + CI recipe) + `0d99f02` cherry-picked (`053a0848`) + [S29] commits:
- `3a2685f8`: the stack (CMake switch, `src/search.cpp`, `include/forge/material_key_table.hpp`, test, CI);
- `b26c7076`: the test's CMake lines moved into their own block, so the patch also applies on base B;
  `forge_sol_S29_speedstack_20261027.patch`, contents, IDEA_SOURCE;
- this commit: evidence and report (`[skip ci]`).

No Elo or speed claim. The spec asks for "ABBA advisory only".

## What it is
Sol's spec: after S11-S14, put every node-exact piece into ONE stack behind one compile switch `FORGE_SPEEDSTACK`
(default OFF), so the speed work costs one [-3, 1] gate instead of four.
- **Switch:** CMake `option(FORGE_SPEEDSTACK ... OFF)` defines `FORGE_SPEEDSTACK=1` for `forge_core`; the PC recipe
  takes `-DFORGE_SPEEDSTACK=1`. There is no UCI option, so the option list is unchanged.
- **Pieces (both node-exact):**
  - S11 material-key table: `material_key()` returns `matkey::table_key(board)` (the same 64-bit key as the Horner
    polynomial, from a 10 × 65 contribution table);
  - S13 child TT prefetch: `shared_.tt.prefetch(board.key())` after `make_null_move` and after the ProbCut
    `make_move` (AL1 already prefetches after the main-search and quiescence makes).
- **Not in the stack** (S12 null-move alias, S14 zero-fill, others): see
  `forge_sol_S29_speedstack_contents_20261027.md`, with reasons.
- Without the switch, the code is the lock code (every change is inside `#ifdef FORGE_SPEEDSTACK`, except the new
  test and its CMake block).

## Acceptance (Sol's pass line + A)
| line | result | evidence |
|---|---|---|
| Std pass OFF: the default build is the lock | **PASS** | PC recipe: default exe vs lock exe differ in 5 bytes (PE timestamp 137-139, checksum 217-218), whole-binary disassembly IDENTICAL, `uci_check.py --full` ALL OK (`logs/step2`, `step3_identity_default`). Linux (CI 40484808127 release): default forge sha256 `6635d4d1…` = lock build, disassembly IDENTICAL; opus-ci 40484808132 release identity ALL OK |
| switch ON: bench equals the refs at all 5 depths, perft and kiwipete exact | **PASS** | PC recipe `-DFORGE_SPEEDSTACK=1`: d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK (`logs/step3_identity_on`); Linux CI release switch-on `uci_check.py --full` ALL OK |
| FMA 0 | **PASS** | PC default and switch-on exes: 0 (`logs/step1_builds.log`); Linux lock/default/on: 0 |
| UCI option list unchanged | **PASS** | switch-on exe vs lock exe, `uci` answer `id`/`option` lines IDENTICAL (12 lines), PC and Linux |
| ASan/UBSan clean | **PASS** | CI 40484808127 asan (switch on): ctest known-only, speed-stack test ALL PASS, identity d11/13/16 + perft OK, "ASan/UBSan: 0 reports"; opus-ci 40484808132 asan (default) PASS |
| TSan (extra) | **PASS** | CI 40484808127 tsan (switch on): ctest known-only, Threads 2 and 4 UCI sessions OK, "TSan: 0 reports" |
| applies on both bases | **PASS** | `git apply --check` + apply of `forge_sol_S29_speedstack_20261027.patch` on base L (lock tree `d4f4312`) and on base B (lock + Sol's node-identical buffix `fc_sol_buffix_h256e12_vs_lock.patch`, sha256 `9ce56b3d…`); base B + stack, PC recipe `-DFORGE_SPEEDSTACK=1`: ALL OK at all 5 depths, perft, kiwipete, FMA 0 (`logs/step7_baseB_on.log`) |
| CTest | **PASS** | PC CMake builds, default and switch on: 14/15, only the 4 known `forge_tests` lines (`logs/step6_ctest_*.log`); `forge_speedstack_tests` 12/12 in both |
| ABBA advisory | **DONE (advisory)** | quiet runner (CI 40484808127 release, `nps_ab.py` lock vs switch-on, 10 runs, interleaved): d16 +0.18% (95% CI −0.53% .. +0.89%), d20 +0.50% (+0.04% .. +0.97%). Nodes identical on every run. Advisory only; no speed claim |
| IDEA_SOURCE, contents, patch | **PASS** | `IDEA_SOURCE.md`, `forge_sol_S29_speedstack_contents_20261027.md`, `forge_sol_S29_speedstack_20261027.patch` |

## Test (`tests/speedstack_tests.cpp`, CTest `forge_speedstack_tests`, both configurations)
1. Count domain (S11): the table equals the Horner polynomial on all 650 single-slot vectors (which proves all
   65^10 count vectors, by linearity) and on 100,000 random vectors.
2. Boards (S11): 200,000 random-walk positions from `tools/openings/forge-10000.epd` plus 6 extreme inventories:
   table key == polynomial key (64 bits), and the material index the search really uses (through
   `Worker::corrected_eval`) equals the polynomial's index.
3. Search (both pieces): the 8 `bench` positions at depth 11 total 312,866 nodes (the AL1 bench).
4. Negative controls: a one-word table change and a one-count key error are caught.

## Codegen of the switch-on build vs the lock (PC, `logs/step5_codegen.log`)
- `Worker::search`: 3 `prefetch` instructions (lock: 1); 2413 → 2448 instructions, start 32 → 16 mod 64.
- `corrected_eval` 99 → 63 and `update_correction` 81 → 71 instructions (the table key replaces the Horner
  chain); `qsearch` 810 → 807; the iterative driver 2119 → 2122.
- MovePicker, TT probe/store, NNUE, make/unmake, SEE: identical.

## PC build with FORGE_SPEEDSTACK ON: bench and NPS (2026-10-27, step 8)
- **Build.** One box-recipe build of `18cb8c03` with `-DFORGE_SPEEDSTACK=1`
  (`F:\opus_scratch\build\S29_on_20261027\forge_s29_on.exe`, sha256 `3d274745…`, FMA 0, 0 warnings).
  It differs from the step-1 switch-on exe only in the PE timestamp and checksum (6 bytes), so the build
  reproduces (`logs/step8_build_on.log`).
- **Bench.** `uci_check.py --full`: d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609,
  kiwipete 193690690, ALL OK: node-exact with the lock (`logs/step8_identity_on.log`).
- **NPS on the PC.** `nps_ab.py`, A = lock exe (copy, sha256 `5d4df7f1…`), B = the switch-on exe. ABBA order, 8
  runs per exe, bench depths 16 and 20, Threads 1, Hash 16. Engines ran at Idle priority (nice 19) on the
  loaded PC, with gates, self-play and NNUE training running. Nodes were identical on all 32 runs
  (`logs/step8_nps_ab_pc.log`).

| depth | A (lock) wall nps | B (stack) wall nps | B/A wall (95% CI) | B/A CPU-time nps (95% CI) |
|---|---:|---:|---|---|
| 16 | 1,757,200 | 1,756,644 | −0.03% (−1.04% .. +0.97%) | −0.21% (−1.53% .. +1.11%) |
| 20 | 1,812,288 | 1,805,288 | −0.39% (−1.78% .. +1.00%) | +0.27% (−0.79% .. +1.34%) |

**Reading.** On the loaded PC the stack is within noise of the lock at both depths; every interval includes 0.
The quiet CI runner measured d16 +0.18% and d20 +0.50% (lower bound +0.04%). Both measurements put the gain
at well under 1%. Advisory only; no speed claim.

## Gate (QA's call)
Sol's design: one non-regression SPRT [−3, 1] at 10+0.1, the switch-on exe vs AL1; QA picks the srand. Neither
piece met the "+2% lower bound" rule on its own (opus-sol-S11, opus-sol-S13); the stack's advisory ABBA is
+0.2% / +0.5% on the quiet runner and −0.4% .. +0.3% (inside noise) on the loaded PC.

## Files
- Engine: `CMakeLists.txt`, `src/search.cpp`, `include/forge/material_key_table.hpp` (new), `tests/speedstack_tests.cpp` (new).
- CI: `.github/workflows/opus-sol-s29-ci.yml`, `opus_round1/sol_S29/ci_s29.sh`, `uci_threads_session.py`,
  `nps_ab.py` and `codegen_compare.sh` (copies from opus-sol-S13 / opus-O3).
- `opus_round1/sol_S29/`: `REPORT.md`, `IDEA_SOURCE.md`, `forge_sol_S29_speedstack_20261027.patch`,
  `forge_sol_S29_speedstack_contents_20261027.md`, `run_s29_evidence.sh` (PC driver), `FILES`, `SHA256SUMS`,
  `logs/` (PC steps 1-8) and `logs/ci_s29_evidence.tar.gz` (CI 40484808127 + 40484808132 logs).
- Machine exclusive: no. Steps 1-7 were identity and codegen only. Step 8 is a PC NPS A/B under gate load,
  advisory only.

## UNVERIFIED / left
- Speed: advisory only; no claim. The PC A/B (step 8) ran under gate load at Idle priority; the quiet runner is
  the cleaner measurement.
- Hardware prefetch effects are not measured (S13's probe counted the requests on its branch).
- The gate itself (QA).
