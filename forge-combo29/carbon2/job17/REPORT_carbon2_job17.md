# Carbon2 — Job 17 Report (`REPORT_carbon2_job17.md`)

**Branch:** `for-fable-and-opus/carbon2-work` (no engine source files modified in-tree; no binaries, `.fnn3` nets, or `.profraw`/`.profdata` files committed; **no pull request opened**).

---

## 0. Step 0 Across All Job 17 Builds, Compiler & `-march`, and SP Profile Parameters

- **Compiler, linker, and C++ standard library (`forge-combo29/carbon2/job17/build_pgo_raw.txt` lines 4–8, 459–495):**
  - `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18`, `llvm-profdata-18`)
  - `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`)
  - GCC 13 `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`)
- **Architecture & speed switches (`build_pgo_raw.txt` lines 473–482):**
  - `-march=sapphirerapids` (`Intel(R) Xeon(R) CPU @ 2.60GHz`, x86-64 AVX-512 + VNNI + BMI2 `PEXT`)
  - `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -pthread`
- **Profiled builds (`sp_tidy_1`, `sp_tidy_2`, `sp_s14_1`, `sp_s14_2`, `sp_s15_1`, `sp_s15_2` in `build_pgo_raw.txt` lines 460–470, 484–486):**
  - **Profile files merged per build:** **`2`** `.profraw` files merged via `llvm-profdata-18 merge`:
    1. Phase 2a `bench 11` (`1,261,644` nodes), `bench 13` (`6,312,262` nodes), `bench 16` (`74,843,992` nodes) with `net768.fnn3` + 4 bench switches.
    2. Phase 2b self-play profile run: **`60` games** (`disjoint_from_timing_60=True`), **`5,531` searches**, **`18,059,934` nodes**, `go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`, `trace=1646ce4566de2f40`.
- **Step 0 verified on every build (engine's own lines in `forge-combo29/carbon2/job17/step0_job17_raw.txt` lines 1–110):**
  - `sp_pcr15` (`step0_job17_raw.txt` lines 1–18): default `bench 11/13/16 = 312,866 / 862,329 / 3,024,920`, `go perft 5 = 4,865,609`; `PC20` no net `bench 11/13 = 278,024 / 587,276`; `net512` only (`fdff70de72e4ca82`, `avx512`) `bench 11/13 = 965,454 / 4,151,906`; `PC20 + net512` `bench 11/13 = 625,258 / 3,652,372`, `eval = 968 / 1176 / 31`.
  - All 7 Job 17 builds (`plain_tidy`, `sp_tidy_1`, `sp_tidy_2`, `sp_s14_1`, `sp_s14_2`, `sp_s15_1`, `sp_s15_2` in `step0_job17_raw.txt` lines 20–110):
    - `go perft 5 = nodes 4865609` (**EXACT** on all 7)
    - `PC20 + net512.fnn3` (`fdff70de72e4ca82`, `avx512`): `bench 11 = 625,258`, `bench 13 = 3,652,372` (`bench 16 = 23,891,329`), `eval = 968 / 1176 / 31` (**EXACT** on all 7)
    - `PC20 + net768.fnn3` (`30ab43b4ba5db5f3`, `avx512`): `bench 11 = 882,074`, `bench 13 = 4,275,906` (`bench 16 = 32,374,943`) (**EXACT** on all 7)

---

## 1. Part 0 — Base `r15d` Check, `stack/tidy.patch.txt`, and Consolidated `stack_r15d_to_final.patch.txt`

### Part 0(a): Plain `r15d` 29-File `sha256sum -c` Check (`forge-combo29/carbon2/job17/part0a_r15d_sha256_check_raw.txt`)

```text
CMakeLists.txt: OK
include/forge/b4.hpp: OK
include/forge/bitboard.hpp: OK
include/forge/board.hpp: OK
include/forge/book.hpp: OK
include/forge/clock_plan.hpp: OK
include/forge/eval.hpp: OK
include/forge/eval_params.hpp: OK
include/forge/nnue.hpp: OK
include/forge/nnue_v3.hpp: OK
include/forge/search.hpp: OK
include/forge/tm_finish.hpp: OK
include/forge/tm_node_share.hpp: OK
include/forge/uci.hpp: OK
include/forge/uci_clock.hpp: OK
include/forge/uci_output.hpp: OK
src/bitboard.cpp: OK
src/board.cpp: OK
src/book.cpp: OK
src/book_data.inc: OK
src/eval.cpp: OK
src/eval_params.cpp: OK
src/eval_params_table.inc: OK
src/nnue.cpp: OK
src/nnue_v3.cpp: OK
src/nnue_weights.inc: OK
src/polyglot_keys.inc: OK
src/search.cpp: OK
src/uci.cpp: OK
EXIT_CODE=0
```

### Part 0(b): `forge-combo29/carbon2/job17/stack/tidy.patch.txt` (`93` lines, on Top of `01..13`)
Applied onto `r15d` + `01_S4..10_W2` + `11_stop_hot` + `12_v3_refresh_fuse` + `13_tt_avx512_fast_probe` (`patch -p1 -F0`), removing every unused stack addition and every whitespace-only diff hunk:
- **`include/forge/board.hpp` (`class Board`):** removed uncalled `cached_king_lines()` (`1` line, added in `07_G3`).
- **`include/forge/search.hpp` (`class TranspositionTable` & `class Worker`):** removed test-only `friend struct S13TTTestAccess;` (`1` line, added in `13_tt_avx512_fast_probe`) and unused `std::uint64_t quiet_hist_epoch_ = 0;` (`1` line, added in `09_W1`).
- **`src/search.cpp` (`MovePicker::next`, `MovePicker` methods/members, `MovePicker::generate_quiets`, and `Worker::search`):**
  - Removed dead write `last_quiet_history_ = picked.score - (direct_chk ? 12000 : 0);` in `MovePicker::next` (`1` line),
  - Removed uncalled `MovePicker::has_cached_quiet_history(...)` and `MovePicker::cached_quiet_history()` (`4` lines),
  - Removed unused `MovePicker` fields `quiet_gen_epoch_` and `last_quiet_history_` (`2` lines) and dead assignment `quiet_gen_epoch_ = searcher_.quiet_hist_epoch_;` in `MovePicker::generate_quiets()` (`1` line),
  - Reverted all `3` whitespace-only indentation edits in `Worker::search` (the two `apply_history` lines in `EvalSwing` and PV quiet history, plus the `int null_score = -search_child(...)` line) back to `r15d`'s exact indentation (`0` whitespace-only hunks remain between `r15d` and `stacked_tidy`).
- **Build & identity proof (`build_pgo_raw.txt` lines 1–19, `part0b_tidy_identity_raw.txt` lines 1–30):** ThinLTO build succeeded (`0` errors); engine `bench 11/13/16` lines exact on both nets (`net512 = 625,258 / 3,652,372 / 23,891,329`, `net768 = 882,074 / 4,275,906 / 32,374,943`), `250` depth-9 rows `node_sum = 4,332,153` and `rows_sha256 = 4124a7d4eadfaae4bc811c98f188a814adc26af08cdfe9a669f8e2ecb3816a18` (with automatic self-stop guard active), `1,000` evals `sha256` exact on both nets, and 6-game traces `4560d7c3afdeba2e` / `9ed22c1193ab96de` exact.

### Part 0(c): Consolidated Diff `forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt` (`part0c_consolidated_proof_and_sha256_raw.txt`)
- **Consolidated diff size & modified files:** **`2,450` lines** across **`9` modified files** (`include/forge/b4.hpp`, `include/forge/board.hpp`, `include/forge/eval.hpp`, `include/forge/nnue_v3.hpp`, `include/forge/search.hpp`, `src/board.cpp`, `src/nnue_v3.cpp`, `src/search.cpp`, `src/uci.cpp`; the other `20` files of `r15d` are untouched).
- **Commands, exit codes, and 29-file SHA-256 list of the final tree (`part0c_consolidated_proof_and_sha256_raw.txt` lines 5–49):**

```text
$ patch -d /tmp/carbon2_job17/final_from_r15d -p1 -F0 < /agent/repos/dwqww/forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt
patching file include/forge/b4.hpp
patching file include/forge/board.hpp
patching file include/forge/eval.hpp
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
PATCH_EXIT_CODE=0

$ diff -r /tmp/carbon2_job17/stacked_tidy /tmp/carbon2_job17/final_from_r15d
DIFF_EXIT_CODE=0

bfa17f8cb5f2f6358e88951f385fc67ddca279af06301b22945efdcc1ceaca5f *CMakeLists.txt
77a8e348c7943d5bdd477b2b6fd9d5c490881a497a83cea27a7bbce1370142c4 *include/forge/b4.hpp
6e6ee73aa83c902fdd6972b56e2802dea60559b5df9aa7b2c97b5e3176ea42c1 *include/forge/bitboard.hpp
45aaa4f6d7184f7b190645404bfadc6a960dce11b92e157eb95409979d70513f *include/forge/board.hpp
10a283bd0474568c0e378f7117d4869336384599307305c405dac81e1569663e *include/forge/book.hpp
9917f142848a873226fd0bae28bec93d4968eea6d949a951d4854510b8645298 *include/forge/clock_plan.hpp
987e7535fa39994e83ecb796cd13af5f4dca0537b4f4069b848a371aab45a993 *include/forge/eval.hpp
56f6ae706d53dfb6e76169e86d0cf09e74e096b17885f60632a92f080ee77a96 *include/forge/eval_params.hpp
bd4d88f653521fc4096d9363235de8ef376705e3af8d252757c453ccd77e7bb7 *include/forge/nnue.hpp
9d26d7861a0a6928883a02e3e6c109eb87cb1c08f5ca5d280505c184a77843c4 *include/forge/nnue_v3.hpp
15f3d81d9e15a98fb4ef39c473f206707d868e416bcc544165289b17654d7b92 *include/forge/search.hpp
111142f6addd9942c54f9184075b954c881db071f01d6847c442268c7f65ac18 *include/forge/tm_finish.hpp
af86c2e0be87efbe761c02b202c686ad16f8b0312e116a5d39ff0a6ae79a814b *include/forge/tm_node_share.hpp
7168a871238e3bff78c85335d612675229044910184774a7682649fb929e5312 *include/forge/uci.hpp
b9a0839170e3315537f2968f1406f0e0e9b3073dbf661a1b4a843b0a01bc5dc3 *include/forge/uci_clock.hpp
3bc09a099ae04bf6d8972125b0778be342de78ba39fcb8510321238e788dbef3 *include/forge/uci_output.hpp
bd825d5520f98b653a70e4532df616c690dbadd1cc28865d3710eaef428f60b4 *src/bitboard.cpp
75301e2d44ea672dcab6db3e7d4783102d406612883f8289419a82bb6b0fb00b *src/board.cpp
464c91efee889d7cbf5f07c7051f0f741de06f091d9bdc2cda98692cfa63aca5 *src/book.cpp
9209c608ca3f07285c3f8b2739a3399c3385c8ed8ffc739fd16a273eb8190149 *src/book_data.inc
515ecdd9ad8201fc4fa5737f4ce558f1ca3b65bacc59ed829f3506f9b93097c7 *src/eval.cpp
16d54a80edf84dbe43b9b962444bac5dad86085e0f5cae0081826194e1f2508f *src/eval_params.cpp
acfd94c951d5212b3ec095edbe7859fe2707f982741b0afaf1d23be58c91400c *src/eval_params_table.inc
47cf86933024536ddd0bc5d1e4603f69566c5ce163cdfbf633f11e49f94a46ef *src/nnue.cpp
e78a8d78a622ff0c6df6c624d9324523e4ee88d75c10828e038160a90cbe4437 *src/nnue_v3.cpp
a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638 *src/nnue_weights.inc
7deca335907224e422adab41c8238851fba27a72b50ab37d01af7b0dd3b8fbb5 *src/polyglot_keys.inc
07f6b9da12680535a1fcd9ba43d0161a636b0989d568b8ae93f7873c79ff583a *src/search.cpp
a23c871d25341bc25c9429989969654894a292844a04b95eb6cb264140ad1a20 *src/uci.cpp
```

---

## 2. Part 1 and Part 2 — Untouched Exclusive Targets, What Each Step Removed, and the Counts That Decided It

### Part 1: `stack/14_v3_apply_changes_fast.patch.txt` on Top of `01..13 + tidy`
- **Why higher untouched rows were skipped first (after reading their code & `probe_untouched_targets_raw.txt`):**
  - `nnue::v3::evaluate` (`2.37%` / `2.44%` exclusive, `src/nnue_v3.cpp:171–194`) already runs a 2x-unrolled AVX-512 `vpdpwssd` loop.
  - `std::__introsort_loop` (`1.45%` / `1.36%` exclusive, `src/search.cpp:1075`): `probe_untouched_targets_raw.txt` line 3 measured `calls = 2,118,916` with **`has_tie = 582,954` (`27.51%`)**; reading `/usr/include/c++/13/bits/stl_algo.h:1812–1951` and `src/search.cpp:1000` confirmed `libstdc++` `std::__insertion_sort` (`<= 16`) is stable while `std::swap`-selection changes tie order, so replacing `std::sort` risks node divergence on tied scores.
- **Target & exclusive share:** `forge::nnue::v3::apply_changes` (`apply_changes_avx512`, `src/nnue_v3.cpp:347–376`), untouched by `01..13 + tidy`; `1.26%` exclusive (`2.562 ms/game`, line 38) unmodified / `1.12%` (`2.221 ms/game`, line 76) frame-pointer in `job13/curated_sp_time_profile_raw.txt` (~`0.48%..0.55%` remaining ceiling after Job 15 `12_v3_refresh_fuse`).
- **Pre-step counts (`probe_untouched_targets_raw.txt` line 4):** `calls = 1,782,903`, of which `c2_sa = 1,415,741` (`79.41%`, 1 sub + 1 add) and `c3_ssa = 366,476` (`20.55%`, 2 subs + 1 add) = **`99.9615%`** (`other = 686`).
- **Change & proofs (`stack/14_v3_apply_changes_fast.patch.txt`, `65` lines; `prediction_14_v3_apply_changes_fast.txt` committed alone in `4b826f6b5`; `s14_v3_apply_changes_identity_and_fault_raw.txt`):**
  - Added 2x-unrolled (`h += 64`) branch-free AVX-512 fast paths for `c2_sa` and `c3_ssa`.
  - Full identity (`bench 11/13/16` both nets, `250` d9 `node_sum=4,332,153` `sha256=4124a7d4...`, `1,000` evals `sha256`, both traces, `-DFORGE_NNUE_V3_VERIFY=1` `exit_code=0`) **EXACT**; **both per-path planted faults caught** (`s14_fault_path1_c2.patch.txt` -> `V3 VERIFY FAILED at ply 10`, `exit_code=3`; `s14_fault_path2_c3.patch.txt` -> `V3 VERIFY FAILED at ply 11`, `exit_code=3`).
- **12x60 `Hash 16` Timing (`s14_v3_apply_changes_12x60_hash16_raw.txt`, `01:07:03Z` to `01:17:08Z`, `48/48` `ee465caeff9c0fcf`):**
  - **`getrusage` CPU:** `median_of_paired_round_ratios = 0.9980x` (`-0.20%`, `4/12` faster, 95% CI `[0.9883x, 1.0078x]`; `A/A` `0.9978` `[0.9406, 1.0541]` / `0.9992` `[0.9707, 1.0595]`); Wall `0.9989x` (`6/12`).
  - **Verdict:** **KILLED** (`0.9980x < 1.0040x` gate; Clang 18 ThinLTO+PGO already unswitched loop-invariant `count`/`adds` predicates in the 24-step `h` loop).

### Part 2: `stack/15_fast_is_pseudo_legal.patch.txt` on Top of `01..13 + tidy`
- **Target & exclusive share:** `forge::Board::is_pseudo_legal(const Move&)` (`src/board.cpp:955–1025`, untouched by `01..14`; `0.74%` exclusive / `1.497 ms/game` in `job13/curated_sp_time_profile_raw.txt` line 42; **`8,361,908` calls** in `probe_untouched_targets_raw.txt` line 6: `2,089,481` early rejects, `pawn = 660,562`, `piece = 5,611,865` hitting the 5-way indirect jump table `jmpq *%rsi` + `RookMagics`/`BishopMagics`).
- **Change & proofs (`stack/15_fast_is_pseudo_legal.patch.txt`, `48` lines; `prediction_15_fast_is_pseudo_legal.txt` committed alone in `970194717`; `s15_is_pseudo_legal_identity_and_fault_raw.txt`):**
  - Inlined the `special == 0` path in `include/forge/board.hpp` using early capture/target mismatch rejection and `BishopRay`/`RookRay` + `BetweenTable` slider checks.
  - Full identity **EXACT**; `11,270,120`-move differential oracle **PASS (`mismatches=0`)**; **all 3 per-path planted faults caught** (`s15_fault_path1_pawn.patch.txt` at `pos#110`, `s15_fault_path2_knight_king.patch.txt` at `pos#0`, `s15_fault_path3_slider.patch.txt` at `pos#0`).
- **12x60 `Hash 16` Timing (`s15_fast_is_pseudo_legal_12x60_hash16_raw.txt`, `01:43:52Z` to `01:53:55Z`, `48/48` `ee465caeff9c0fcf`):**
  - **`getrusage` CPU:** `median_of_paired_round_ratios = 0.9923x` (`-0.77%`, `1/12` faster, 95% CI `[0.9809x, 0.9953x]`; `A/A` `0.9977` `[0.9596, 1.0257]` / `1.0099` `[0.9774, 1.0615]`); Wall `0.9933x` (`2/12`).
  - **Verdict:** **KILLED** (`0.9923x < 1.0040x` gate; duplicating a 28-line inline check across 6 `MovePicker::next` stages + `Worker::search` bloated L1i and pulled `32 KB` `BetweenTable` lines vs already-warm `RookMagics`/`BishopMagics`).

---

## 3. Step Summary Table

| Step | Patch File (`forge-combo29/carbon2/job17/...`) | Lines | Identity Suite & Oracles | 12x60 `Hash 16` SP-PGO Timing (`getrusage` CPU / Wall) | Prediction (`met` or `killed`) | Planted Faults (`caught` or `not`) |
|---|---|---:|---|---|---|---|
| **Part 0(b): `tidy`** (on `01..13`) | `stack/tidy.patch.txt` (`-F0`; consolidated `stack_r15d_to_final.patch.txt` = `2,450` lines) | `93` | **EXACT** (compile succeeded, engine lines `net512 625258/3652372/23891329`, `net768 882074/4275906/32374943`, `250` d9 `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256`, both traces; `-F0` + `diff -r` `exit 0`) | Not timed (per File 17 Part 0(b): removes dead code & whitespace-only diffs only) | — | Compile check (any live reference fails to compile) |
| **Part 1: `14_v3_apply_changes_fast`** (on `01..13 + tidy`) | `stack/14_v3_apply_changes_fast.patch.txt` (`-F0`) | `65` | **EXACT** (engine lines exact both nets, `250` d9 `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256`, both traces, `-DFORGE_NNUE_V3_VERIFY=1` `exit 0`, `48/48` `ee465caeff9c0fcf`) | CPU **`0.9980x` (`-0.20%`, `4/12`, 95% CI `[0.9883x, 1.0078x]`)**; Wall **`0.9989x` (`-0.11%`, `6/12`)** (`s14_v3_apply_changes_12x60_hash16_raw.txt`) | **KILLED** (`0.9980x < 1.0040x`, `4/12 < 8/12`) | **2 / 2 CAUGHT** (`s14_fault_path1_c2` ply 10 `rc=3`, `s14_fault_path2_c3` ply 11 `rc=3`) |
| **Part 2: `15_fast_is_pseudo_legal`** (on `01..13 + tidy`) | `stack/15_fast_is_pseudo_legal.patch.txt` (`-F0`) | `48` | **EXACT** (engine lines exact both nets, `250` d9 `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256`, both traces, `11,270,120`-move oracle `0` mismatches, `48/48` `ee465caeff9c0fcf`) | CPU **`0.9923x` (`-0.77%`, `1/12`, 95% CI `[0.9809x, 0.9953x]`)**; Wall **`0.9933x` (`-0.67%`, `2/12`)** (`s15_fast_is_pseudo_legal_12x60_hash16_raw.txt`) | **KILLED** (`0.9923x < 1.0040x`, `1/12 < 8/12`) | **3 / 3 CAUGHT** (`s15_fault_path1_pawn`, `path2_knight_king`, `path3_slider`, all `rc=1`) |

---

## 4. Why We Recommend Stopping Here for PC Adoption Timing (Plus Code-Read Remaining Candidates)

- **Primary recommendation — STOP adding cloud micro-steps and time `stack_r15d_to_final.patch.txt` (`01..13 + tidy`, `2,450` lines) on the Zen 5 PC:**
  - Across Jobs 11–17 on SP-profiled Xeon AVX-512, our 13 surviving pieces (`01..10` `+3.66%` `12/12`, `11_stop_hot` `+1.92%` `9/12`, `12_v3_refresh_fuse` `+0.68%` `11/12`, `13_tt_avx512_fast_probe` `+2.49%` `12/12`, tidied in `stack/tidy.patch.txt`) harvested every >2%-ceiling structural bottleneck (`~+8.9%` cumulative on Xeon SP-PGO), whereas **four consecutive sub-1.8%-ceiling untouched targets (`has_legal_move` `1.0017x`, `upcoming_repetition` `0.9970x`, `apply_changes` `0.9980x`, `is_pseudo_legal` `0.9923x`) all failed the `+0.40%` gate**. Further untimed-on-Zen-5 additions carry higher code-layout risk than expected gain.
- **Code-read candidates if another 90 minutes were explicitly requested on already-touched subsystems:**
  1. **Null-move accumulator forwarding (`src/search.cpp` lines 1875–1892 & 3880–3925):** `Worker::record_null_move` sets `child->dirty.count = 0` yet zeroes `v3_state_->valid_flags[ss->ply + 5] = 0`, forcing a `3,072`-byte no-op accumulator copy after null moves.
  2. **`TranspositionTable::clear()` aliasing reload (`src/search.cpp` lines 458–463; disassembly `0xa4ac0–0xa4ad9` in `bld_sp_tidy_1/forge`):** `for (i = 0; i < cluster_count_; ++i) clusters_[i] = TTCluster{};` reloads `this->clusters_` and `this->cluster_count_` on every iteration (`262,144` iterations/clear) instead of `std::memset(clusters_.get(), 0, cluster_count_ * sizeof(TTCluster))` (~`0.25%` ceiling, DRAM-bandwidth bounded).

---

## 5. Timestamps (`stamps.txt`), Runtime Model, and Final Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job17/stamps.txt`:**
  `Wed Nov 18 12:36:01 PM UTC 2026 | job 17 received (FABLE_TO_carbon2_17.md); starting Part 0(a) sha256sum -c on plain r15d`
- **Last line of `forge-combo29/carbon2/job17/stamps.txt`:**
  `Wed Nov 18 02:03:02 PM UTC 2026 | Part 2 DONE: 15_fast_is_pseudo_legal 12x60 Hash16 CPU 0.9923x (-0.77%, 1/12) < 1.0040x gate -> KILLED; writing REPORT_carbon2_job17.md`
- **Runtime model name and version:** `Gemini 4 Carbon`
- **Pull request check:** No pull request was opened.
- **Output of `git status --short && ls -R forge-combo29/carbon2/job17` immediately before committing this report:**

```text
?? forge-combo29/carbon2/job17/REPORT_carbon2_job17.md
forge-combo29/carbon2/job17:
build_pgo_raw.txt
part0a_r15d_sha256_check_raw.txt
part0b_tidy_identity_raw.txt
part0c_consolidated_proof_and_sha256_raw.txt
prediction_14_v3_apply_changes_fast.txt
prediction_15_fast_is_pseudo_legal.txt
probe_untouched_targets_raw.txt
REPORT_carbon2_job17.md
s14_fault_path1_c2.patch.txt
s14_fault_path2_c3.patch.txt
s14_v3_apply_changes_12x60_hash16_raw.txt
s14_v3_apply_changes_identity_and_fault_raw.txt
s15_fast_is_pseudo_legal_12x60_hash16_raw.txt
s15_fault_path1_pawn.patch.txt
s15_fault_path2_knight_king.patch.txt
s15_fault_path3_slider.patch.txt
s15_is_pseudo_legal_identity_and_fault_raw.txt
stack
stack_r15d_to_final.patch.txt
stamps.txt
step0_job17_raw.txt
test_s15_is_pseudo_legal_oracle.cpp

forge-combo29/carbon2/job17/stack:
14_v3_apply_changes_fast.patch.txt
15_fast_is_pseudo_legal.patch.txt
tidy.patch.txt
```
