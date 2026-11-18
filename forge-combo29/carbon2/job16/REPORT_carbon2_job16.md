# Carbon2 — Job 16 Report (`REPORT_carbon2_job16.md`)

**Branch:** `for-fable-and-opus/carbon2-work` (no engine source files modified in-tree; no binaries, `.fnn3` nets, or `.profraw`/`.profdata` files committed; **no pull request opened**).

---

## 0. Step 0 Across All Job 16 Builds, Compiler & `-march`, and SP Profile Parameters

- **Compiler, linker, and C++ standard library (`forge-combo29/carbon2/job16/build_pgo_raw.txt` lines 4–8, 307–312):**
  - `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18`, `llvm-profdata-18`)
  - `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`)
  - GCC 13 `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`)
- **Architecture & speed switches (`build_pgo_raw.txt` lines 440–449):**
  - `-march=sapphirerapids` (`Intel(R) Xeon(R) CPU @ 2.60GHz`, x86-64 AVX-512 + VNNI + BMI2 `PEXT`)
  - `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -pthread`
- **Profiled builds (`sp_s12_1`, `sp_s12_2`, `sp_s13_1`, `sp_s13_2`, `sp_s14_1`, `sp_s14_2` in `build_pgo_raw.txt` lines 292–294, 427–437, 451–453):**
  - **Profile files merged per build:** **`2`** `.profraw` files merged via `llvm-profdata-18 merge`:
    1. Phase 2a `bench 11` (`1,261,644` nodes), `bench 13` (`6,312,262` nodes), `bench 16` (`74,843,992` nodes) with `net768.fnn3` + 4 bench switches.
    2. Phase 2b self-play profile run: **`60` games** (`disjoint_from_timing_60=True`), **`5,531` searches**, **`18,059,934` nodes**, `go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`, `trace=1646ce4566de2f40`.
- **Step 0 verified on every build (engine's own lines in `forge-combo29/carbon2/job16/step0_job16_raw.txt` lines 1–94):**
  - `sp_pcr15` (`step0_job16_raw.txt` lines 1–18): default `bench 11/13/16 = 312,866 / 862,329 / 3,024,920`, `go perft 5 = 4,865,609`; `PC20` no net `bench 11/13 = 278,024 / 587,276`; `net512` only (`fdff70de72e4ca82`, `avx512`) `bench 11/13 = 965,454 / 4,151,906`; `PC20 + net512` `bench 11/13 = 625,258 / 3,652,372`, `eval = 968 / 1176 / 31`.
  - All 6 timed SP-profile builds (`sp_s12_1`, `sp_s12_2`, `sp_s13_1`, `sp_s13_2`, `sp_s14_1`, `sp_s14_2` in `step0_job16_raw.txt` lines 20–94):
    - `go perft 5 = nodes 4865609` (**EXACT** on all 6)
    - `PC20 + net512.fnn3` (`fdff70de72e4ca82`, `avx512`): `bench 11 = 625,258`, `bench 13 = 3,652,372` (`bench 16 = 23,891,329`), `eval = 968 / 1176 / 31` (**EXACT** on all 6)
    - `PC20 + net768.fnn3` (`30ab43b4ba5db5f3`, `avx512`): `bench 11 = 882,074`, `bench 13 = 4,275,906` (`bench 16 = 32,374,943`) (**EXACT** on all 6)

---

## 1. Part 1 and Part 2 — Target Function, Exclusive Share, What Each Step Removes, and the Counts That Decided It

### Part 1: `stack/13_tt_avx512_fast_probe.patch.txt` on Top of `01..12` (`curated + 11_stop_hot + 12_v3_refresh_fuse`)
- **Target function & exclusive share (untouched by `01..11` and untouched by Job 15 `12_v3_refresh_fuse`):**
  - `forge::TranspositionTable::probe_owned(std::uint64_t key) const` (with its private `Worker::probe_tt` / `Worker::store_tt` boundary in `include/forge/search.hpp` and `src/search.cpp`).
  - Exclusive share in `forge-combo29/carbon2/job13/curated_sp_time_profile_raw.txt`: **`6.32%` exclusive (`12.850 ms/game`, `1,013 / 16,016` samples)** on unmodified SP-profiled `curated` (line 26, the largest untouched exclusive function in the profile) and **`3.81%` exclusive (`7.552 ms/game`, `595 / 15,630` samples)** on frame-pointer SP-profiled `curated` (line 64).
- **Pre-step counts (`forge-combo29/carbon2/job16/probe_counts_tt_and_cuckoo_raw.txt`, `60` games, `Hash 16`, `searches = 7,670`, `nodes = 25,641,316`, `trace = ee465caeff9c0fcf`):**
  - `probe_owned = 31,963,180` calls: `hit = 17,020,843` (`53.25%`; only `hit_gen_upd = 3,642,638` refresh generation), `miss_empty = 14,907,833` (`46.64%`), and `miss_full = 34,504` (`0.11%`).
  - `store_owned = 14,666,813` (`probes_without_store = 17,296,367` = **`54.11%`** of probes never call `store_tt`).
- **Pre-committed standalone prediction:** `forge-combo29/carbon2/job16/prediction_13_tt_avx512_fast_probe.txt` (committed alone in `f2303b42a`): predicted `1.0040x..1.0200x` (`+0.40%..+2.00%`) paired `getrusage` CPU and `>= 8/12` faster (declared gate `>= 1.0040x` AND `>= 8/12`).
- **What `stack/13_tt_avx512_fast_probe.patch.txt` (`346` lines, `patch -p1 -F0` on `01..12`) removes:**
  1. Moves hot `clusters_`, `cluster_count_`, `epoch_`, `generation_` to offset `0` of `TranspositionTable` instead of `+0x100b0` (`+65,712` bytes behind `1,024` `Stripe` mutexes).
  2. Replaces the out-of-line `probe_owned` call and 64-byte stack-`sret` `TTProbe` (including dead `owner_`, `epoch_`, `key_` writes on all `17,296,367` non-storing probes) at `Worker`'s 3 `probe_tt` / 4 `store_tt` sites with compact inline `WorkerTTProbe` + `[[gnu::always_inline]] probe_owned_fast(key)` (leaving public `TranspositionTable::probe` / `store` untouched).
  3. Replaces both 4-slot scalar loops and the wasted `replace_score` calculation on all `17,020,843` hits and `14,907,833` empty-slot misses (`99.89%` of all `31,963,180` probes) with one aligned 64-byte `_mm512_load_si512` + `_mm512_mask_cmpeq_epi32_mask(0x1111, ...)` + `_mm512_mask_test_epi32_mask(0x8888, ...)` (`tzcnt` picks the lowest matching or empty slot in registers; only the `34,504` = `0.11%` full-cluster misses call `[[gnu::noinline]] replace_full_cluster_slot`), plus the same 4-slot AVX-512 match mask in `store_owned_fast`.
- **Proofs (`forge-combo29/carbon2/job16/s13_tt_identity_and_fault_raw.txt` lines 1–37):**
  - Engine's own `bench 11/13/16` lines: `net512 = 625,258 / 3,652,372 / 23,891,329`, `net768 = 882,074 / 4,275,906 / 32,374,943` (**EXACT**).
  - `250` depth-9 rows: `node_sum = 4,332,153`, `rows_sha256 = 4124a7d4eadfaae4bc811c98f188a814adc26af08cdfe9a669f8e2ecb3816a18` (**EXACT**).
  - `1,000` evals `sha256` exact on both nets; 6-game traces `4560d7c3afdeba2e` and `9ed22c1193ab96de` (**EXACT**).
  - `500,000`-op collision-heavy differential TT oracle (`test_s13_tt_fast_probe_oracle.cpp`): **PASS** (`final_hashfull=64`, `mismatches=0`).
  - Planted fault (`s13_tt_planted_fault.patch.txt`: `key_eq << 2U` instead of `<< 3U`): **CAUGHT** at `step=57` (`ref=1 fast=0`, `exit_code=1`).
- **12x60 `Hash 16` ABBA Timing (`forge-combo29/carbon2/job16/s13_tt_avx512_fast_probe_12x60_hash16_raw.txt`, opening with `START_UTC: Wed Nov 18 11:37:01 AM UTC 2026` and closing with `END_UTC: Wed Nov 18 11:46:59 AM UTC 2026`):**
  - `A = 01..12` SP-profile (`bld_sp_s12_1`, `bld_sp_s12_2`) vs `B = 01..12 + 13_tt_avx512_fast_probe` SP-profile (`bld_sp_s13_1`, `bld_sp_s13_2`); all `48` runs hit ONE trace `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes).
  - **`getrusage` engine CPU:**
    - Per-round paired ratios (`r=1..12`): `[1.0280, 1.0241, 1.0422, 1.0271, 1.0209, 1.0258, 1.0318, 1.0108, 1.0152, 1.0606, 1.0179, 1.0121]`
    - **`median_of_paired_round_ratios = 1.0249x` (`+2.49%`), 95% CI `[1.0165x, 1.0299x]`, `12/12` rounds faster**
    - **`ratio_of_pooled_medians = 1.0250x` (`+2.50%`), 95% CI `[1.0189x, 1.0304x]`**
    - `A/A` control: `median(A2)/median(A1) = 1.0001` (per-round range `[0.9709, 1.0191]`), `median(B2)/median(B1) = 1.0009` (per-round range `[0.9835, 1.0179]`).
  - **Wall clock:** `median_of_paired_round_ratios = 1.0253x` (`+2.53%`), 95% CI `[1.0149x, 1.0279x]`, **`12/12` rounds faster** (`A/A` `median(A2)/median(A1) = 0.9991` `[0.9822, 1.0091]`, `median(B2)/median(B1) = 0.9975` `[0.9809, 1.0113]`).
  - **Decision:** **PASSED THE DECLARED GATE (`>= 1.0040x` & `>= 8/12`) AND CARRIES** (both paired `[1.0165x, 1.0299x]` and pooled `[1.0189x, 1.0304x]` 95% CIs lie strictly above `1.016x`; note transparently that `+2.49%` exceeded our pre-committed `+0.40%..+2.00%` upper estimate by `+0.49%`). Part 2 therefore built on `01..13`.

### Part 2: `stack/14_cuckoo_avx512_parity.patch.txt` on Top of `01..13`
- **Target function & exclusive share (untouched by `01..13`):**
  - `forge::Board::upcoming_repetition(std::size_t root_index) const` (`1.45%` exclusive / `2.956 ms/game` unmodified [line 36] and `1.75%` exclusive / `3.465 ms/game` frame-pointer [line 74] in `job13/curated_sp_time_profile_raw.txt`).
- **Pre-step counts (`probe_counts_tt_and_cuckoo_raw.txt` line 4):**
  - `calls = 10,629,168` (`span_lt4 = 128,059`, of which `plies_from_null_lt3 = 121,983`), `loop_iters = 140,992,020` (`opp_zero = 1,925,446` = `1.37%`, `cuckoo_hit = 1,166,391`, `returns_true = 793,484`).
- **Pre-committed standalone prediction:** `forge-combo29/carbon2/job16/prediction_14_cuckoo_avx512_parity.txt` (committed alone in `db10c01c2`): predicted `1.0040x..1.0140x` (`+0.40%..+1.40%`) CPU and `>= 8/12` faster; declared kill gate `< 1.0040x` or `< 8/12`.
- **What `stack/14_cuckoo_avx512_parity.patch.txt` (`293` lines, `patch -p1 -F0` on `01..13`) changed & its proofs (`s14_cuckoo_identity_and_fault_raw.txt`):**
  - Added `plies_from_null() >= 3 && history_size() >= 4` to inline `may_repeat(board)`, `constexpr` co-located 16-byte `CuckooSlot` table, and parity prefix-XOR vectors `opp_prefix_[2]` scanned 8 plies at a time with `_mm512_cmpeq_epi64_mask`.
  - Full engine-line identity (`bench 11/13/16` both nets, `250` d9 rows `node_sum = 4,332,153` `sha256 = 4124a7d4...`, `1,000` evals `sha256`, both traces): **EXACT**.
  - `77,945`-state brute-force legal-move oracle (`test_s14_upcoming_rep_oracle.cpp`): **PASS** (`true_hits=4263`, `mismatches=0`); planted parity fault (`s14_cuckoo_planted_fault.patch.txt`) **CAUGHT** at `hist=4 ri=0 got=0 exp=1` (`exit_code=1`).
- **12x60 `Hash 16` ABBA Timing (`forge-combo29/carbon2/job16/s14_cuckoo_avx512_parity_12x60_hash16_raw.txt`, opening with `START_UTC: Wed Nov 18 12:07:07 PM UTC 2026` and closing with `END_UTC: Wed Nov 18 12:17:00 PM UTC 2026`):**
  - All `48` runs hit `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes).
  - **`getrusage` engine CPU:** `median_of_paired_round_ratios = 0.9970x` (`-0.30%`), 95% CI `[0.9910x, 1.0009x]`, `3/12` faster (`pooled = 0.9967x`, `A/A` `median(A2)/median(A1) = 1.0021` `[0.9756, 1.0193]`, `median(B2)/median(B1) = 0.9978` `[0.9760, 1.0068]`).
  - **Wall clock:** `median_of_paired_round_ratios = 0.9984x` (`-0.16%`), 95% CI `[0.9904x, 1.0061x]`, `4/12` faster.
  - **Decision:** **KILLED** (`0.9970x < 1.0040x`, `3/12 < 8/12`). Maintaining two extra `std::vector<uint64_t>` buffers in `Board` paid `push_back`/`pop_back` overhead on `31,561,883` `make_move`/`unmake_move` pairs (plus null moves and larger `Board` copies) — `3x` as often as `upcoming_repetition`'s `10,629,168` calls — costing more than the AVX-512 history scan saved. Thus Job 16's surviving tree is **`01..13`** (`01..10` + `11_stop_hot` + `12_v3_refresh_fuse` + `13_tt_avx512_fast_probe`).

---

## 2. Step Summary Table

| Step | Patch File (`forge-combo29/carbon2/job16/...`) | Lines | Identity Suite & Oracles | 12x60 `Hash 16` SP-PGO Timing (`getrusage` CPU / Wall) | Prediction (`met` or `killed`) | Planted Fault (`caught` or `not`) |
|---|---|---:|---|---|---|---|
| **Part 1: `13_tt_avx512_fast_probe`** (on `01..12`) | `stack/13_tt_avx512_fast_probe.patch.txt` (`-F0`) | `346` | **EXACT** (engine lines `net512 625258/3652372/23891329`, `net768 882074/4275906/32374943`, `250` d9 `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256` exact both nets, `4560d7c3afdeba2e`, `9ed22c1193ab96de`, `500k` TT oracle `mismatches=0`, `48/48` runs `ee465caeff9c0fcf`) | **CPU `1.0249x` (`+2.49%`, `12/12`, paired 95% CI `[1.0165x, 1.0299x]`, pooled `1.0250x` 95% CI `[1.0189x, 1.0304x]`)**; **Wall `1.0253x` (`+2.53%`, `12/12`, 95% CI `[1.0149x, 1.0279x]`)** (`s13_tt_avx512_fast_probe_12x60_hash16_raw.txt`) | **MET GATE & CARRIES** (`1.0249x >= 1.0040x`, `12/12 >= 8/12`; exceeded `+2.00%` upper prediction bound by `+0.49%`) | **CAUGHT** (`s13_tt_planted_fault.patch.txt` -> `MISMATCH (hit) at step=57 ref=1 fast=0`, `exit_code=1`, `s13_tt_identity_and_fault_raw.txt`) |
| **Part 2: `14_cuckoo_avx512_parity`** (on `01..13`) | `stack/14_cuckoo_avx512_parity.patch.txt` (`-F0`) | `293` | **EXACT** (engine lines exact both nets, `250` d9 `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256`, both traces, `77,945`-state brute-force `upcoming_rep` oracle `0` mismatches, `48/48` runs `ee465caeff9c0fcf`) | CPU **`0.9970x` (`-0.30%`, `3/12`, 95% CI `[0.9910x, 1.0009x]`)**; Wall **`0.9984x` (`-0.16%`, `4/12`, 95% CI `[0.9904x, 1.0061x]`)** (`s14_cuckoo_avx512_parity_12x60_hash16_raw.txt`) | **KILLED** (`0.9970x < 1.0040x`, `3/12 < 8/12`) | **CAUGHT** (`s14_cuckoo_planted_fault.patch.txt` -> `MISMATCH (dance) hist=4 ri=0 got=0 exp=1`, `exit_code=1`, `s14_cuckoo_identity_and_fault_raw.txt`) |

---

## 3. Ranked Next Steps With Another 90 Minutes (Each With the Exact Code Read for It)

1. **Rank 1 — Zero-Copy Null-Move Accumulator Reuse in `Worker::record_null_move` & `Worker::static_evaluate_v3` (code read: `src/search.cpp` lines 1875–1892 & lines 3755–3800):**
   - In `Worker::record_null_move(SearchStack* ss)` (`src/search.cpp:1882–1889`), a null move sets `child->entered_null = true; child->diff_known = true; child->dirty.count = 0;` and then unconditionally clears **`v3_state_->valid_flags[ss->ply + 5] = 0;`**. Because `dirty.count == 0` and neither king moved, `stack[index]` after a null move has the **exact same `[White, Black]` accumulators, `keys`, and `king_sq` as `stack[index - 1]`**; yet clearing `valid_flags[ss->ply + 5]` forces `static_evaluate_v3` (or a child's `make_valid`) to run a full `3,072`-byte `apply_pair` / `replay_ply` with `c0.count == 0, c1.count == 0`! Evaluating directly against `stack[index - 1]` when `entered_null` holds (or forwarding the valid ancestor index past consecutive null plies) saves `3,072`-byte accumulator copies after every null move with zero change to `Board`.
2. **Rank 2 — Restore the `them_pawns_atk` Early Exit Inside `#if FORGE_SDK_SEE_HOIST` in `Board::see_ge` (code read: `src/board.cpp` lines 14–16 & lines 1512–1575):**
   - Reading `Board::see_ge` (`src/board.cpp:1553–1571`, `3.85%` / `3.74%` exclusive in `job13/curated_sp_time_profile_raw.txt`) revealed that `FORGE_SDK_SEE_HOIST` defaults to `1` at `src/board.cpp:15`, and `06_G2` placed the pawn-recapture short-circuit `if (them_pawns_atk != 0 && SeeValue[Pawn] - swap < 0)` inside the `#else` branch (`lines 1560–1571`), so **it is compiled out in all timed builds**! Hoisting that exact check into the `#if FORGE_SDK_SEE_HOIST` branch (caching `contact[them]` / `snipers[them]` into `prepared |= (1U << them)` if non-zero so work is reused if pinned!) skips both `attacks::bishop(to, occupancy)` and `attacks::rook(to, occupancy)` PEXT lookups plus the exchange loop whenever an unpinned enemy pawn already refutes a high-piece capture (`Q/R/B/N x defended-by-pawn`).
3. **Rank 3 — Zero-`Board`-Touch `upcoming_repetition` Guard + `constexpr CuckooSlot` Only (code read: `src/search.cpp` line 2915 & `src/board.cpp` lines 1700–1827):**
   - Part 2 proved that adding `opp_prefix_` vectors to `Board` lost `-0.30%` because `make_move` runs `3x` more often than `upcoming_repetition`. Testing *only* the zero-maintenance changes (`may_repeat` checking `plies_from_null() >= 3 && history_size() >= 4` at `src/search.cpp:2915`, `constexpr` 16-byte `CuckooSlot` table, and pointer-walked 2x-unrolled `key_history_` XOR scan with **zero edits to `make_move`/`Board` layout**) isolates any positive Cuckoo gain without `make_move` tax.

---

## 4. Timestamps (`stamps.txt`), Runtime Model, and Final Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job16/stamps.txt`:**
  `Wed Nov 18 11:01:32 AM UTC 2026 | job 16 received (FABLE_TO_carbon2_16.md); inspecting Job 13 exclusive profile and untouched functions`
- **Last line of `forge-combo29/carbon2/job16/stamps.txt`:**
  `Wed Nov 18 12:20:43 PM UTC 2026 | Part 2 DONE: 14_cuckoo_avx512_parity 12x60 Hash16 CPU 0.9970x (-0.30%, 3/12) < 1.0040x gate -> KILLED; writing REPORT_carbon2_job16.md`
- **Runtime model name and version:** `Gemini 4 Carbon`
- **Pull request check:** No pull request was opened.
- **Output of `git status --short && ls -R forge-combo29/carbon2/job16` immediately before committing this report:**

```text
?? forge-combo29/carbon2/job16/REPORT_carbon2_job16.md
forge-combo29/carbon2/job16:
build_pgo_raw.txt
prediction_13_tt_avx512_fast_probe.txt
prediction_14_cuckoo_avx512_parity.txt
probe_counts_tt_and_cuckoo_raw.txt
REPORT_carbon2_job16.md
s13_tt_avx512_fast_probe_12x60_hash16_raw.txt
s13_tt_identity_and_fault_raw.txt
s13_tt_planted_fault.patch.txt
s14_cuckoo_avx512_parity_12x60_hash16_raw.txt
s14_cuckoo_identity_and_fault_raw.txt
s14_cuckoo_planted_fault.patch.txt
stack
stamps.txt
step0_job16_raw.txt
test_s13_tt_fast_probe_oracle.cpp
test_s14_upcoming_rep_oracle.cpp

forge-combo29/carbon2/job16/stack:
13_tt_avx512_fast_probe.patch.txt
14_cuckoo_avx512_parity.patch.txt
```
