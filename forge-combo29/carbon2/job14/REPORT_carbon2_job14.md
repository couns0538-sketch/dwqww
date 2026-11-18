# Carbon2 — Job 14 Report (`REPORT_carbon2_job14.md`)

**Branch:** `for-fable-and-opus/carbon2-work` (no engine source files modified in-tree; no binaries, `.fnn3` nets, or `.profraw`/`.profdata` files committed; **no pull request opened**).

---

## 0. Build Toolchain, SP Profile Parameters, and Step 0 Across All Job 14 Builds

- **Compiler, linker, and C++ standard library (`forge-combo29/carbon2/job14/build_pgo_raw.txt` lines 4–8):**
  - `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18`, `llvm-profdata-18`)
  - `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`)
  - GCC 13 `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`)
- **Architecture & speed switches (`build_pgo_raw.txt` lines 11–20, 136–145):**
  - `-march=sapphirerapids` (x86-64 AVX-512 + VNNI + BMI2 `PEXT` on `Intel(R) Xeon(R) CPU @ 2.60GHz`)
  - `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -pthread`
- **SP profile merged per timed build (`build_pgo_raw.txt` lines 123–133, 270–283, 420–431, 444–446):**
  - **Profile files merged per build:** **`2`** `.profraw` files merged via `llvm-profdata-18 merge`:
    1. Phase 2a `bench 11` (`1,261,644` nodes), `bench 13` (`6,312,262` nodes), `bench 16` (`74,843,992` nodes) with `net768.fnn3` + 4 bench switches.
    2. Phase 2b self-play profile run: **`60` games** (disjoint from the 60 timing roots: `disjoint_from_timing_60=True`), **`5,531` searches**, **`18,059,934` nodes**, `go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`, `trace=1646ce4566de2f40`.
- **Step 0 verified on every build (`forge-combo29/carbon2/job14/step0_job14_raw.txt` lines 1–92 & `debug_identity_and_assert_counts_raw.txt` lines 1–6):**
  - Full Step 0 on SP-profiled `pc_r15` (`step0_job14_raw.txt` lines 1–24):
    - No settings, no net: `bench 11 = 312,866`, `bench 13 = 862,329`, `bench 16 = 3,024,920`, `go perft 5 = 4,865,609`.
    - `PC20`, no net: `bench 11 = 278,024`, `bench 13 = 587,276`.
    - `net512.fnn3` only (`checksum fdff70de72e4ca82`, `kernel avx512`): `bench 11 = 965,454`, `bench 13 = 4,151,906`.
    - `PC20 + net512.fnn3`: `bench 11 = 625,258`, `bench 13 = 3,652,372`, static `eval` = `968 / 1176 / 31`.
  - Step 0 / post-`r15c` pins across **all 7 Job 14 candidate builds** (`bld_dbg` [assert-enabled no-PGO `curated`], `sp_cur_1`, `sp_cur_2`, `sp_s11_1`, `sp_s11_2`, `sp_s12_1`, `sp_s12_2` in `debug_identity_and_assert_counts_raw.txt` lines 1–15 and `step0_job14_raw.txt` lines 26–92):
    - `go perft 5 = 4,865,609` (**EXACT** on all 7)
    - `PC20 + net512.fnn3` (`fdff70de72e4ca82`, `avx512`): `bench 11 = 625,258`, `bench 13 = 3,652,372` (`bench 16 = 23,891,329`), static `eval` = `968 / 1176 / 31` (**EXACT** on all 7)
    - `PC20 + net768.fnn3` (`30ab43b4ba5db5f3`, `avx512`): `bench 11 = 882,074`, `bench 13 = 4,275,906` (`bench 16 = 32,374,943`) (**EXACT** on all 7)

---

## 1. Part 1 — Assert-Enabled `curated` Build (`r15d` + `01_S4 .. 10_W2`, Without `-DNDEBUG`)

- **Exact compile & link line and `grep -c NDEBUG` (`forge-combo29/carbon2/job14/debug_build_raw.txt` lines 1–4):**

```text
clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -std=c++20 -O3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS=\"/tmp/carbon2_job14/curated_10/src/nnue_weights.inc\" -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -fuse-ld=lld-18 -pthread -I/tmp/carbon2_job14/curated_10/include /tmp/carbon2_job14/curated_10/src/bitboard.cpp /tmp/carbon2_job14/curated_10/src/board.cpp /tmp/carbon2_job14/curated_10/src/book.cpp /tmp/carbon2_job14/curated_10/src/eval.cpp /tmp/carbon2_job14/curated_10/src/eval_params.cpp /tmp/carbon2_job14/curated_10/src/nnue.cpp /tmp/carbon2_job14/curated_10/src/nnue_v3.cpp /tmp/carbon2_job14/curated_10/src/search.cpp /tmp/carbon2_job14/curated_10/src/uci.cpp -o /tmp/carbon2_job14/bld_dbg/forge
grep -c NDEBUG: 0
```

- **Identity suite, 6-game traces, and 60-game `Hash 16` self-play vs `-DNDEBUG` `curated` (`forge-combo29/carbon2/job14/debug_identity_and_assert_counts_raw.txt` lines 1–19):**
  - `go perft 5`: `4,865,609` (`exit_code=0`)
  - `net512.fnn3` `bench 11 / 13 / 16`: `625,258` / `3,652,372` / `23,891,329` (`exit_code=0`, **EXACT** match to `-DNDEBUG` `curated`)
  - `net768.fnn3` `bench 11 / 13 / 16`: `882,074` / `4,275,906` / `32,374,943` (`exit_code=0`, **EXACT** match to `-DNDEBUG` `curated`)
  - `250` depth-9 rows (`positions_250.txt`): `250/250` **EXACT** (`exit_code=0`)
  - `1,000` static evals (`positions_1000.txt`, `net768` & `net512`): `1,000/1,000` & `1,000/1,000` **EXACT** (`exit_code=0`)
  - 6-game traces: `startpos = 4560d7c3afdeba2e`, `FEN = 9ed22c1193ab96de` (**EXACT**, `exit_code=0`)
  - 60-game `Hash 16` `softnodes 2000` self-play: `searches = 7,670`, `nodes = 25,641,316`, `trace = ee465caeff9c0fcf` (**EXACT** match to `-DNDEBUG` `curated`, `exit_code = 0`, `assert_lines = 0`)
- **Assert-reached counters across the 60 `Hash 16` self-play games (`debug_identity_and_assert_counts_raw.txt` lines 21–23):**
  - `make_move_calls = 31,561,883`
  - `assert_key_eq_dbg_key = 31,059,800` (`assert(key_ == dbg_key)` at `curated_sp_bundle.patch.txt:L321`, reached on `98.41%` of `make_move` calls; `0` failures)
  - `assert_compute_checkers_eq_0 = 23,674,201` (`assert(compute_checkers() == 0)` at `curated_sp_bundle.patch.txt:L348`, reached on `75.01%` of `make_move` calls; `0` failures)

---

## 2. Part 2 — Comparison Table of `PGO1`'s 6 Parts Against `curated_sp_bundle.patch.txt`

Line numbers below are copied directly from `forge-combo29/carbon2/job14/part2_pgo1_vs_curated_table_raw.txt` comparing `forge-combo29/carbon2/job10/pgo1_curated_pgo_winners_and_hot_stop_tt_stalemate.patch.txt` (`1,060` lines, hunks `P01..P52`) against `forge-combo29/carbon2/job11/curated_sp_bundle.patch.txt` (`1,857` lines, hunks `C01..C74`):

| `PGO1` Part | File | `PGO1` Patch Hunk & Lines | `curated_sp_bundle` Patch Hunk & Lines | Status | Exact Text Relationship |
|---|---|---|---|---|---|
| **1. `S4`** | `include/forge/search.hpp` | `P05` (`L50-L60`) | `C09` (`L128-L162`) | **`changed`** | `picker_scratch_` + `evasion_cand_buf_` kept; merged into adjacent `Worker` member hunk alongside `threat_map_ready_` (`W1`), `root_moves_sort_buf_`, and `v3_active_net_` (`G4`), omitting `fast_single_node_stop_`. |
| **1. `S4`** | `src/search.cpp` | `P18` (`L286-L294`) | `C24` (`L485-L493`) | **`equal`** | `#define FORGE_SDK_BADCAP_PREFIX 1` hunk body identical. |
| **1. `S4`** | `src/search.cpp` | `P23` (`L383-L392`) | `C26` (`L528-L537`) | **`equal`** | `Stage::Evasions` `MovePicker::next()` hunk body identical. |
| **1. `S4`** | `src/search.cpp` | `P24` (`L393-L417`) | `C28` (`L555-L594`) | **`changed`** | Removes `MoveList buffer_;` in both, while `curated` adds `W1` direct-scoring members (`quiet_Filter_` / `Scored` layout) in the same hunk. |
| **1. `S4`** | `src/search.cpp` | `P26-P28` (`L426-L496`) | `C33-C34` (`L681-L1030`) | **`changed`** | `PGO1`'s `picker_scratch_` buffer-swap `generate_captures()`/`generate_quiets()` are superseded in `curated` by `W1+W2` direct bitboard capture/quiet emitters into `moves_`. |
| **1. `S4`** | `src/search.cpp` | `P29` (`L497-L519`) | `C35` (`L1031-L1053`) | **`equal`** | `MovePicker::generate_evasions()` header using `searcher_.evasion_cand_buf_` identical. |
| **1. `S4`** | `src/search.cpp` | `P30` (`L520-L548`) | `C36` (`L1054-L1088`) | **`changed`** | Identical `has_evasion_score_tie` bitmask executable code; `curated` adds 3 comment lines explaining the 4 selection passes. |
| **2. `S5`** | `include/forge/board.hpp` | `P01` (`L4-L12`) | `C02` (`L43-L52`) | **`changed`** | Same 4-parameter `make_move(..., precomputed_key = nullptr, known_gives_check = -1)` signature wrapped across 2 lines in `curated` vs 1 line in `PGO1`. |
| **2. `S5`** | `src/board.cpp` | `P11` (`L133-L141`) | `C13` (`L210-L218`) | **`equal`** | `Board::make_move` definition header identical. |
| **2. `S5`** | `src/board.cpp` | `P12-P14` (`L142-L252`) | `C14-C16` (`L219-L361`) | **`changed`** | Same `king_lines_.valid` guard and `precomputed_key` fast path, except `PGO1` had `assert(key_ == compute_key())` whereas `curated` has the 7-site `#ifndef NDEBUG` incremental `dbg_key` (`assert(key_ == dbg_key)`). |
| **2. `S5`** | `src/board.cpp` | `P15-P17` (`L253-L282`) | `C17-C19` (`L362-L391`) | **`equal`** | `unmake_move`, `make_null_move`, and `unmake_null_move` `undo.king_lines.valid` hunks identical. |
| **2. `S5`** | `src/search.cpp` | `P34` (`L607-L620`) | `C48` (`L1273-L1286`) | **`equal`** | `Worker::qsearch` `board.make_move(move, undo, have_child_key ? &child_key : nullptr, known_gives_check)` hunk identical. |
| **2. `S5`** | `src/search.cpp` | `P36` (`L630-L643`) | `C53` (`L1325-L1339`) | **`changed`** | `Worker::search` `make_move` call: `curated` binds `const int known_gc = gives_check ? 1 : 0;` on a separate line vs inline ternary `gives_check ? 1 : 0` in `PGO1`. |
| **3. `S7`** | `src/search.cpp` | `P31` (`L549-L586`) | `C37` (`L1089-L1127`) | **`changed`** | Same `std::memset` `Worker::clear()` replacement; `curated` adds 1 line `std::memset(threat_map_ready_.data(), ...)` for `W1` (and `C57` `L1373-L1383` moves root `board`). |
| **3. `S7`** | `src/uci.cpp` | `P38` (`L657-L791`) | `C60` (`L1454-L1588`) | **`changed`** | Identical `string_view` incremental `PositionCache` parser except `PGO1:L684` has `[[gnu::hot]] void apply_position_sv(...)` while `curated:L1481` has `void apply_position_sv(...)` without `[[gnu::hot]]`. |
| **3. `S7`** | `src/uci.cpp` | `P39-P52` (`L792-L1060`) | `C61-C74` (`L1589-L1857`) | **`equal`** | All remaining 14 `src/uci.cpp` hunks are line-for-line identical. |
| **4. `TT`** | `include/forge/search.hpp`, `src/search.cpp` | `P04` (`L39-L49`), `P19-P22` (`L295-L382`) | — | **`absent`** | Dropped in Job 12 (`0.9996x` `6/12` in `pgo1_loo6_12x60_hash16_raw.txt`); completely absent from `curated_sp_bundle.patch.txt`. |
| **5. `Legal`** | `include/forge/board.hpp`, `src/board.cpp`, `src/search.cpp` | `P02` (`L13-L26`), `P07-P09` (`L80-L123`), `P14` (`L231-L244`), `P25` (`L418-L425`), `P33` (`L596-L606`) | `C03` (`L53-L66`), `C10-C12` (`L166-L209`), `C16` (`L346-L358`), `C29` (`L595-L602`), `C47` (`L1262-L1272`) | **`equal`** | All `G3` hunks (`ensure_king_lines`, `taboo` king filter, `safe_pawns` `& ~k_rays`, `known_gives_check == 0` skip + `assert(compute_checkers() == 0)`, `MovePicker::init_check_squares`, `qsearch` `known_gives_check`) are identical in text. |
| **5. `Legal`** | `include/forge/board.hpp`, `src/board.cpp` | `P03` (`L27-L35`), `P10` (`L124-L132`) | — | **`absent`** | `P1`'s 2-hunk `moving != WK && moving != BK` check (in place of `piece_type(moving) != King`) in `is_legal` / `is_legal_complete` is absent from `curated_sp_bundle.patch.txt`. |
| **6. `Stop+Hot`** | `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp` | `P05` (`L54`), `P06` (`L61-L76`), `P32` (`L587-L595`), `P35` (`L621-L629`), `P37` (`L644-L653`), `P38` (`L684`) | — | **`absent`** | `fast_single_node_stop_`, `[[gnu::always_inline]] check_node_or_periodic_stop()`, its `qsearch`/`search` calls, its `Worker::search` init, and `[[gnu::hot]]` on `apply_position_sv` are completely absent from `curated_sp_bundle.patch.txt`. |

---

## 3. Part 3 and Part 4 — What We Did and the Counts That Decided Each Step

### Part 3: `stack/11_stop_hot.patch.txt` on Top of `curated` (`01_S4 .. 10_W2`)
- **Pre-committed standalone prediction:** `forge-combo29/carbon2/job14/prediction_11_stop_hot.txt` (committed alone in `506e85de4` before creating or timing `11_stop_hot`).
- **Counts from committed raw files that motivated it:**
  - In `forge-combo29/carbon2/job9/counts_hash16.txt` (line 14), 60 `Hash 16` self-play games (`7,670` searches, `25,641,316` nodes) call `Worker::should_stop()` **`32,930,134` times** (`100.00%` single-worker node-bounded), executing `nodes_.store(local_nodes_, relaxed)` plus `should_stop_with() -> total_nodes()` on every node.
  - `forge-combo29/carbon2/job14/stack/11_stop_hot.patch.txt` (`70` lines, verified `patch -p1 -F0` on `r15d + 01_S4..10_W2`) adds `fast_single_node_stop_` + `[[gnu::always_inline]] Worker::check_node_or_periodic_stop()` (eliminating `32,897,975` = `99.90%` of `should_stop()` calls per 60 games) and `[[gnu::hot]]` on `apply_position_sv` (`7,670` calls per 60 games).
- **Proofs (`forge-combo29/carbon2/job14/s11_identity_and_fault_raw.txt`):**
  - Full identity suite on `bld_sp_s11_1/forge` (`bench 11/13/16` both nets, `250/250` depth-9 rows, `1,000` evals both nets, `4560d7c3afdeba2e`, `9ed22c1193ab96de`): **100% EXACT**.
  - 500,000-op TT + 9-cap stop-boundary oracle: **PASS** (`hash=fd8c91bbb184a08b`, `mismatches=0`).
  - Planted fault (`s11_stop_planted_fault.patch.txt`: `local_nodes_ <= node_limit_`): **CAUGHT** immediately (`got=9bc76d07fefd1c1c != fd8c91bbb184a08b`, nonzero exit).
- **12x60 `Hash 16` ABBA Timing (`forge-combo29/carbon2/job14/s11_stop_hot_12x60_hash16_raw.txt`, opening with `START_UTC: Wed Nov 18 08:13:31 AM UTC 2026` and closing with `END_UTC: Wed Nov 18 08:24:17 AM UTC 2026`):**
  - `A = curated` SP-profile (`bld_sp_cur_1`, `bld_sp_cur_2`) vs `B = curated + 11_stop_hot` SP-profile (`bld_sp_s11_1`, `bld_sp_s11_2`); all `48` runs hit ONE trace `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes).
  - **`getrusage` engine CPU:**
    - Per-round paired ratios (`r=1..12`): `[1.0216, 1.0169, 1.0136, 1.0430, 1.0252, 0.9889, 0.9475, 1.0124, 0.9876, 1.0454, 1.0512, 1.0286]`
    - **`median_of_paired_round_ratios = 1.0192x` (`+1.92%`), 95% CI `[1.0007x, 1.0358x]`, `9/12` rounds faster**
    - `ratio_of_pooled_medians = 1.0205x` (`+2.05%`), 95% CI `[0.9964x, 1.0292x]`
    - `A/A` control: `median(A2)/median(A1) = 0.9969` (per-round range `[0.9669, 1.0596]`), `median(B2)/median(B1) = 1.0001` (per-round range `[0.9692, 1.0279]`).
  - **Wall clock:** `median_of_paired_round_ratios = 1.0201x` (`+2.01%`), 95% CI `[1.0007x, 1.0341x]`, `9/12` rounds faster (`A/A` `median(A2)/median(A1) = 0.9931` `[0.9644, 1.0610]`, `median(B2)/median(B1) = 1.0006` `[0.9740, 1.0336]`).
  - **Decision:** Predicted `1.0040x..1.0200x` and `>= 8/12`; observed **`1.0192x` (`9/12`)** -> **MET & PASSED THE DECLARED GATE** (and on paired round ratios its 95% CI `[1.0007x, 1.0358x]` lies strictly above `1.0000x`, so it **carries** on paired round ratios, though its pooled-median 95% CI `[0.9964x, 1.0292x]` reaches below `1.0000x`). Therefore Part 4 built on `curated + 11_stop_hot`.

### Part 4: First Target of the Job 13 Time Profile — `Board::has_legal_move()` (`stack/12_fast_has_legal_move.patch.txt` on `curated + 11_stop_hot`)
- **Why this target & why we did NOT defer `Worker::is_draw()` past TT/stand-pat:**
  - In `forge-combo29/carbon2/job13/curated_sp_time_profile_raw.txt` (line 70), `Board::has_legal_move() const` is the #1 standalone board/legality helper outside the already-rewritten `search`/`qsearch`/NNUE/`MovePicker` functions at **`2.48%` caller-inclusive CPU (`4.924 ms/game`, `388` samples: `306` from `Worker::search`, `82` from `Worker::qsearch`)**.
  - Deferring `!board.has_legal_move()` in `Worker::is_draw()` past TT cutoffs or `static_evaluate` would violate node-and-score identity (`Worker::qsearch` generates captures only so `move_count == 0` does not catch stalemate, and `EvalSwing` mutates `main_history_` before the move loop). Therefore we optimized `Board::has_legal_move()` itself 100% bit-exactly.
- **Exact branch-frequency counts over 60 `Hash 16` SP games (`forge-combo29/carbon2/job14/part4_has_legal_move_counts_raw.txt`, `trace=ee465caeff9c0fcf`):**
  - `calls = 26,874,501` (`26,749,044` with `checkers_ == 0`; `in_check = 125,457`).
  - Existing code exited on `safe_pawns = pawns & ~k_rays` `16,128,217` times (`60.01%`), leaving `current_reaches_pin = 10,620,827` (`39.52%`) even though `!king_lines_.valid && snipers != 0` occurred only `current_single_blockers = 336,360` times (`1.25%`); `3,353,199` re-ran pawn push/attacks, `2,454,098` (`1,123,245 + 1,330,853`) looped over Bishops/Rooks/Queens with PEXT lookups (`would_exit_safe_knights + would_exit_safe_sliders = 4,153,094`), `4,379,669` (`16.30%`) exited on King steps via `square_attacked_with_occupancy`, and `153,783` reached `generate_pseudo_legal(moves, false)` (`28,159` `false` returns).
- **Pre-committed standalone prediction:** `forge-combo29/carbon2/job14/prediction_12_fast_has_legal_move.txt` (committed alone in `ae5f5ed3f`): predicted `1.0040x..1.0180x` (`+0.40%..+1.80%`) paired CPU and `>= 8/12` faster; declared kill gate `< 1.0040x` or `< 8/12`.
- **Implementation & proofs (`stack/12_fast_has_legal_move.patch.txt`, `163` lines, `patch -p1 -F0` on `curated + 11_stop_hot`; `s12_identity_and_fault_raw.txt`):**
  - Inlined the `checkers_ == 0 && (king_lines_.valid || snipers == 0)` fast path into `include/forge/board.hpp` using 1-pass unpinned pawns + branchless 1-step slider/knight bitshift dilations (`orth_step | diag_step` and 8-way knight shifts, zero PEXT lookups), cached `ensure_king_lines().pinned` on the `336,360` sniper-present calls in `has_legal_move_slow()`, added `taboo` + empty-slider short-circuits on the `4,379,669` King exits, and returned `ep_square_ >= 0 && has_legal_en_passant_capture()` directly when `checkers_ == 0 && pinned == 0`.
  - Exhaustive cold+warm `KingLines` oracle (`test_s12_has_legal_move_oracle.cpp`): **`73,147` positions checked (`146,294` evaluations), `0` mismatches**.
  - Planted fault (`s12_planted_fault.patch.txt`: omitting sniper guard when `!king_lines_.valid`): **CAUGHT** (`ORACLE MISMATCH (cold king_lines) at root#1002 fen='8/8/8/8/6k1/5br1/r3P2K/8 w - - 0 1' got=1 expected=0`, `exit_code=1`).
  - Full identity suite on `bld_sp_s12_1/forge`: **100% EXACT**.
- **12x60 `Hash 16` ABBA Timing (`forge-combo29/carbon2/job14/s12_fast_has_legal_move_12x60_hash16_raw.txt`, opening with `START_UTC: Wed Nov 18 09:07:41 AM UTC 2026` and closing with `END_UTC: Wed Nov 18 09:17:49 AM UTC 2026`):**
  - `A = curated + 11_stop_hot` SP-profile (`bld_sp_s11_1`, `bld_sp_s11_2`) vs `B = curated + 11_stop_hot + 12_fast_has_legal_move` SP-profile (`bld_sp_s12_1`, `bld_sp_s12_2`); all `48` runs hit ONE trace `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes).
  - **`getrusage` engine CPU:**
    - Per-round paired ratios (`r=1..12`): `[0.9886, 1.0145, 1.0023, 1.0018, 1.0036, 0.9952, 1.0010, 1.0015, 1.0138, 0.9887, 1.0048, 1.0009]`
    - **`median_of_paired_round_ratios = 1.0017x` (`+0.17%`), 95% CI `[0.9980x, 1.0042x]`, `9/12` rounds faster**
    - `ratio_of_pooled_medians = 1.0020x` (`+0.20%`), 95% CI `[0.9951x, 1.0097x]`
    - `A/A` control: `median(A2)/median(A1) = 1.0030` (range `[0.9858, 1.0219]`), `median(B2)/median(B1) = 0.9998` (range `[0.9786, 1.0398]`).
  - **Wall clock:** `median_of_paired_round_ratios = 1.0026x` (`+0.26%`), 95% CI `[0.9983x, 1.0064x]`, `7/12` faster (`A/A` `median(A2)/median(A1) = 1.0015` `[0.9851, 1.0243]`, `median(B2)/median(B1) = 0.9989` `[0.9772, 1.0235]`).
  - **Decision:** Although directionally positive (`9/12` rounds faster on CPU, `+0.17%` CPU / `+0.26%` wall), `1.0017x` is **below our pre-declared `1.0040x` (`+0.40%`) gate** -> **KILLED**! Why it missed magnitude: `60.01%` (`16.13M / 26.87M`) of `has_legal_move()` calls already exited in 8 instructions on `safe_pawns` (~1.1 ns/call), and inlining 38 lines of bitwise checks into `Worker::is_draw()` (duplicated into both `Worker::search` and `Worker::qsearch` entry prologues under SP-PGO) traded back part of the board savings in L1i / prologue code layout. Keeping it out of the recommended stack keeps the PC stack small and high-yield (`01_S4 .. 10_W2` + `11_stop_hot`).

---

## 4. Step Summary Table

| Step | Patch File (`forge-combo29/carbon2/job14/...`) | Lines | Identity Suite & Oracles | 12x60 `Hash 16` SP-PGO Timing (`getrusage` CPU / Wall) | Prediction (`met` or `killed`) | Planted Fault (`caught` or `not`) |
|---|---|---:|---|---|---|---|
| **Part 3: `11_stop_hot`** (on `curated` = `r15d + 01..10`) | `stack/11_stop_hot.patch.txt` (`-F0`) | `70` | **EXACT** (`bench 11/13/16` both nets, `250/250` d9, `1000` evals, `4560d7c3afdeba2e`, `9ed22c1193ab96de`, `500k` TT + `9`-cap stop oracle `fd8c91bbb184a08b`, `48/48` runs `ee465caeff9c0fcf`) | **CPU `1.0192x` (`+1.92%`, `9/12`, paired 95% CI `[1.0007x, 1.0358x]`, pooled 95% CI `[0.9964x, 1.0292x]`)**; Wall **`1.0201x` (`+2.01%`, `9/12`, 95% CI `[1.0007x, 1.0341x]`)** (`s11_stop_hot_12x60_hash16_raw.txt`) | **MET** (passed declared `>= 1.0040x` & `>= 8/12` gate; paired round-ratio 95% CI > `1.0000x` **carries**) | **CAUGHT** (`s11_stop_planted_fault.patch.txt` -> `9bc76d07fefd1c1c != fd8c91bbb184a08b`, `s11_identity_and_fault_raw.txt`) |
| **Part 4: `12_fast_has_legal_move`** (on `curated + 11_stop_hot`) | `stack/12_fast_has_legal_move.patch.txt` (`-F0`) | `163` | **EXACT** (`bench 11/13/16` both nets, `250/250` d9, `1000` evals, both traces, `73,147`-pos cold+warm `has_legal_move` oracle `0` mismatches, `48/48` runs `ee465caeff9c0fcf`) | CPU **`1.0017x` (`+0.17%`, `9/12`, 95% CI `[0.9980x, 1.0042x]`)**; Wall **`1.0026x` (`+0.26%`, `7/12`, 95% CI `[0.9983x, 1.0064x]`)** (`s12_fast_has_legal_move_12x60_hash16_raw.txt`) | **KILLED** (`1.0017x < 1.0040x` pre-declared gate in `prediction_12_fast_has_legal_move.txt`) | **CAUGHT** (`s12_planted_fault.patch.txt` -> stalemate mismatch on `root#1002`, `exit_code=1`, `s12_identity_and_fault_raw.txt`) |

---

## 5. Ranked Next Steps With Another 90 Minutes (and Why PC Timing Comes First)

1. **Wait for Zen 5 PC (`clang 23.1.5 -march=znver5` SP-PGO) timing on the 11-piece stack (`job13/stack/01_S4..10_W2` + `job14/stack/11_stop_hot.patch.txt`, `1,927` patch lines total) first:**
   - With `11_stop_hot` adding `+1.92%` CPU (`9/12`, paired 95% CI `[1.0007x, 1.0358x]`) on top of Job 11's `+3.66%` SP-profiled `curated` stack (~`+5.6%` cumulative on Xeon AVX-512 SP-PGO), and Part 4 showing diminishing returns (`+0.17%`) on `Board::has_legal_move()`, the highest-value check is seeing which of the 11 pieces win on Zen 5 (`clang 23.1.5`) before stacking smaller changes.
2. **Ranked engine targets if another 90-minute cloud round is wanted (all on `curated + 11_stop_hot`):**
   - **Rank 1 — `nnue::v3::refresh_from_pieces` (`5.87%` / `11.639 ms/game` in `job13/curated_sp_time_profile_raw.txt` line 62):** multi-register `int16` AVX-512 feature add/sub unrolling (4 feature rows in parallel to hide L1/L2 feature-weight load latency on RefreshCache misses; bit-exact integer `vpaddw`/`vpsubw`).
   - **Rank 2 — Out-of-line-only `Board::has_legal_move()` (`0` header growth in `Worker::search`/`qsearch`):** test keeping `has_legal_move()` out-of-line in `board.cpp` while applying only the 1-pass sniper-free unpinned bitshift dilation + `taboo` king filter inside `board.cpp`, testing whether avoiding `Worker::search`/`qsearch` prologue growth recovers `+0.4%..+0.6%`.
   - **Rank 3 — `Board::see_ge` (`3.74%` / `7.412 ms/game` in `job13/curated_sp_time_profile_raw.txt` line 65):** fast immediate-return when `victim_val - threshold < 0` or undefended capture before constructing full slider attacker sets.

---

## 6. Timestamps (`stamps.txt`), Runtime Model, and Final Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job14/stamps.txt`:**
  `Wed Nov 18 07:47:30 AM UTC 2026 | job 14 received (FABLE_TO_carbon2_14.md v2); starting Part 1 assert-enabled curated build and Part 2 hunk-line table`
- **Last line of `forge-combo29/carbon2/job14/stamps.txt`:**
  `Wed Nov 18 09:25:47 AM UTC 2026 | Step 0 verified across all 7 Job 14 builds; writing REPORT_carbon2_job14.md`
- **Runtime model name and version:** `Gemini 4 Carbon`
- **Pull request check:** No pull request was opened.
- **Output of `git status --short && ls -R forge-combo29/carbon2/job14` immediately before committing this report:**

```text
?? forge-combo29/carbon2/job14/REPORT_carbon2_job14.md
forge-combo29/carbon2/job14:
build_pgo_raw.txt
debug_build_raw.txt
debug_identity_and_assert_counts_raw.txt
part2_pgo1_vs_curated_table_raw.txt
part4_has_legal_move_counts_raw.txt
prediction_11_stop_hot.txt
prediction_12_fast_has_legal_move.txt
REPORT_carbon2_job14.md
run_selfplay_hash16_abba_dated.py
s11_identity_and_fault_raw.txt
s11_stop_hot_12x60_hash16_raw.txt
s11_stop_planted_fault.patch.txt
s12_fast_has_legal_move_12x60_hash16_raw.txt
s12_identity_and_fault_raw.txt
s12_planted_fault.patch.txt
stack
stamps.txt
step0_job14_raw.txt
test_s12_has_legal_move_oracle.cpp

forge-combo29/carbon2/job14/stack:
11_stop_hot.patch.txt
12_fast_has_legal_move.patch.txt
```
