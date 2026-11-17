# Forge (`carbon2` — Job 10 Report): Clang 18 ThinLTO + PGO Verification, Standalone `bundle 1` Step Isolation (`S1..S7`), `SIGPROF` Time Profile, and Curated `PGO1`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job10/`, zero binaries, net files, or `.profraw`/`.profdata` files committed).
- **PC-Matched Compiler, Linker, Target & PGO Pipeline (`forge-combo29/carbon2/job10/build_pgo_raw.txt`):**
  - **Compiler & C++ runtime:** `clang++-18` (`Ubuntu clang version 18.1.3 (1ubuntu1)`) with GCC 13.3's `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`); `lld-18` (`Ubuntu LLD 18.1.3`), `llvm-18` (`llvm-profdata-18`), and `libclang-rt-18-dev` (`1:18.1.3-1ubuntu1`) installed from Ubuntu's official archive (nothing else installed).
  - **Why `-march=sapphirerapids` instead of `-march=znver5`:** Clang 18 predates `-march=znver5` (`error: unknown target CPU 'znver5'`) and this cloud host is an Intel Sapphire Rapids Xeon (`4` cores, `48 KiB` L1d, `2 MiB` L2/core, `320 MiB` L3), not AMD Zen 5. Clang 18's `-march=native` resolves to **`-march=sapphirerapids`**, which enables the full native `AVX-512F/BW/DQ/VL`, `AVX512-VNNI`, `AVX512-VBMI2`, and `BMI2` (`PEXT`) instruction set matching Zen 5's `FORGE_SPD_SLIDER_PEXT=1` and `FORGE_SPD_NNUE_ZMM=1` paths.
  - **Compile & link switches:** All explicit switches of File 10 item `(c)` (`-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread`, linked with `-fuse-ld=lld-18 -flto=thin`), two-phase `-fprofile-instr-generate` -> File 10 item `(b)` exact stdin (`net768.fnn3`, `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`, `bench 11 / 13 / 16`) -> `llvm-profdata-18 merge` -> `-fprofile-instr-use`. *(Note on File 10 item `(c)`: `CMakeLists.txt` lines 32–39 also defined those six `FORGE_SPD_*` / `FORGE_SEARCH_SPEED2` macros in Jobs 1–9, so the GCC-vs-PC gap came specifically from `g++ -O3` non-LTO/non-PGO `-march=x86-64-v4` vs `clang++` ThinLTO + PGO.)*

---

## 0. Step 0 on the Clang 18 ThinLTO + PGO Build (`forge-combo29/carbon2/job10/step0_pgo_raw.txt`)

All Step 0 pins on the Clang 18.1.3 + `libstdc++` + ThinLTO + PGO (`-march=sapphirerapids`) build of `pc_r15` matched bit-for-bit with zero error/warning lines:
- **No settings, no net:** `bench 11 -> 312866` (`172 ms`), `bench 13 -> 862329` (`539 ms`), `bench 16 -> 3024920` (`1668 ms`), `go perft 5 -> 4865609`
- **`PC20`, no net:** `bench 11 -> 278024` (`162 ms`), `bench 13 -> 587276` (`323 ms`)
- **`net512.fnn3` only:** `bench 11 -> 965454` (`477 ms`), `bench 13 -> 4151906` (`1990 ms`)
- **`PC20`, then `net512.fnn3`:** `bench 11 -> 625258` (`327 ms`), `bench 13 -> 3652372` (`2007 ms`, `1,819,816 nps` vs `1,660,169 nps` on Job 9's GCC build; `checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)
- **`PC20` + `net512.fnn3` `eval`:** `startpos -> nnue 968`, `r1bqkbnr/... -> nnue 1176`, `8/5pk1/... -> nnue 31`.

---

## 1. Clang 18 ThinLTO + PGO Timings: `r15d` vs `bundle 1` and `r15d` vs `bundle 4`

Each tree was built **twice independently** (`A1, A2` and `B1, B2` — separate `-fprofile-instr-generate`, profile run, `llvm-profdata-18 merge`, and `-fprofile-instr-use` ThinLTO link) and timed over `12` rounds of `A1 B1 B2 A2` x `60` games (`48` runs = `368,160` searches, `Hash 16`, `Threads 1`, `PC20 + net768.fnn3`, `go softnodes 2000`; trace `ee465caeff9c0fcf` bit-identical across all runs). Baseline `r15d` rose from `~527` cpu_sps (GCC 13 non-PGO) to **`603.6–608.2` cpu_sps (`+14.5%`)** under Clang 18 ThinLTO + PGO.

| Comparison on Clang 18 ThinLTO + PGO (`Hash 16`, 12x60 ABBA) | Raw File | Engine CPU (`getrusage` ns): Per-Round Ratios, Paired Median, Pooled Median, Rounds Faster, A/A Range | Wall Clock (`perf_counter_ns`): Per-Round Ratios, Paired Median, Rounds Faster, A/A Range | Prediction (`98934d0d0`) Graded |
| :--- | :--- | :--- | :--- | :--- |
| **`r15d` vs `bundle 1` (`r15e`: Job 5 `bundle1` minus `S7p3`)** | `pgo_r15d_vs_bundle1_12x60_hash16_raw.txt` | `[1.0047, 1.0205, 0.9955, 1.0096, 1.0312, 1.0220, 1.0193, 1.0245, 1.0073, 1.0038, 1.0335, 1.0294]`<br>**Paired median: `1.0199x` (`+1.99%`, 95% CI `[1.0060x, 1.0270x]`)**, pooled: `1.0204x` (`+2.04%`), **`11/12` faster**<br>A/A: `med(A2)/med(A1)=0.9977` (**`[0.9615, 1.0431]`**), `med(B2)/med(B1)=1.0035` (**`[0.9496, 1.0246]`**) | `[1.0037, 1.0129, 0.9896, 1.0155, 1.0321, 1.0177, 1.0164, 1.0123, 1.0037, 1.0086, 1.0203, 1.0252]`<br>**Paired median: `1.0142x` (`+1.42%`, 95% CI `[1.0062x, 1.0190x]`)**, **`11/12` faster**<br>A/A: `1.0019` (`[0.9464, 1.0381]`), `1.0072` (`[0.9492, 1.0230]`) | **`>= 1.0%` Keep Gate MET** (`1.0199x >= 1.0100x` & `11/12 >= 9/12`; slightly above `[1.003x, 1.018x]` upper edge, confirming compression from GCC's `+3.42%`) |
| **`r15d` vs `bundle 4` (Job 8 `bundle4.patch.txt`)** | `pgo_r15d_vs_bundle4_12x60_hash16_raw.txt` | `[1.0235, 1.0314, 1.0160, 1.0216, 1.0253, 1.0045, 1.0212, 1.0135, 1.0036, 1.0035, 1.0080, 1.0035]`<br>**Paired median: `1.0147x` (`+1.47%`, 95% CI `[1.0041x, 1.0226x]`)**, pooled: `1.0104x` (`+1.04%`), **`12/12` faster**<br>A/A: `med(A2)/med(A1)=1.0055` (**`[0.9372, 1.0788]`**), `med(B2)/med(B1)=0.9962` (**`[0.9825, 1.0227]`**) | `[1.0100, 1.0228, 1.0122, 1.0169, 1.0069, 1.0021, 1.0158, 1.0073, 1.0053, 1.0054, 1.0063, 1.0042]`<br>**Paired median: `1.0071x` (`+0.71%`, 95% CI `[1.0053x, 1.0140x]`)**, **`12/12` faster**<br>A/A: `1.0082` (`[0.9298, 1.0485]`), `0.9917` (`[0.9780, 1.0325]`) | **Part 2 KILLED** (`1.0147x < 1.0150x` CPU and `1.0071x < 1.0120x` wall: on Clang PGO, `bundle 4` is **`-0.52%` slower** than `bundle 1`!) |

---

## 2. What We Chose Next and Why: Standalone Step Isolation (`S1..S7`) + `SIGPROF` CPU-Time Profile of the PGO Build

Because `bundle 1` kept `>= 1.0%` (`+1.99%`, `11/12` faster), we followed File 10's exact rule:
1. **Tested all 7 steps of `bundle 1` (`S1..S7`) ALONE on `r15d` on the Clang 18 ThinLTO + PGO build** (`6` palindromic rounds x `9` builds x `60` games = `54` runs at `Hash 16`, `forge-combo29/carbon2/job10/pgo_bundle1_steps_alone_6x60_hash16_raw.txt`, `A/A` `r15d_2/r15d_1` CPU median `0.9983`, range `[0.9738, 1.0198]`):
   - **`S1` alone:** **`0.9822x` (`-1.78%`, `1/6` faster)** — **REGRESSION on Clang PGO!**
   - **`S2` alone:** **`0.9908x` (`-0.92%, 1/6` faster)** — **REGRESSION on Clang PGO!**
   - **`S3` alone:** **`0.9835x` (`-1.65%, 1/6` faster)** — **REGRESSION on Clang PGO!**
   - **`S4` alone:** **`1.0077x` (`+0.77%`, `5/6` faster; wall `1.0090x`, `5/6`)** — **CARRIES GAIN** (`MovePicker` `4,792 -> 2,224 B`, `-2.56 KB/ply`).
   - **`S5` alone:** **`1.0042x` (`+0.42%`, `4/6` faster; wall `1.0071x`, `5/6`)** — **CARRIES GAIN** (`make_move` `precomputed_key` + slim `Undo`).
   - **`S6` alone:** **`1.0003x` (`+0.03%`, `3/6` faster)** — **NEUTRAL (`0%`)**.
   - **`S7` (parts 1 & 2) alone:** **`1.0109x` (`+1.09%`, `6/6` faster!)** — **LARGEST PGO GAIN** (zero-alloc `string_view` `position` parser in PGO-cold `uci.cpp` + `memset` `Worker::clear()`).
   **Root cause of the PC's `+0.78%` result:** In `bundle 1`, `S1 + S2 + S3` actively fought Clang ThinLTO + PGO, cancelling most of `S4 + S5 + S7`!
2. **Captured an `ITIMER_PROF` (`SIGPROF`) instruction-pointer CPU-TIME profile on the unmodified PGO binaries (`r15d` and `bundle 1`)** over the 60-game `Hash 16` stream (`forge-combo29/carbon2/job10/pgo_time_profile_raw.txt`, `3,341` and `3,330` CPU-time RIP samples):
   - **Why `S1` regressed `-1.78%` on Clang PGO:** In `r15d` (`216.34 ms/game`), Clang ThinLTO + PGO inlined `MovePicker::next` directly into `Worker::search` (`MovePicker::next` self = `0.93%` / `2.01 ms/game`), and `refresh_from_pieces` (`5.12%`) + `evaluate` (`2.33%`) = **`7.45%`** (`16.12 ms/game`). In `bundle 1`, `S1` bloated `MovePicker::next` out of `Worker::search` (`10.33%` / `21.71 ms/game`) and replaced `refresh_from_pieces + evaluate` with `refresh_one_and_evaluate` (`6.25% + 2.13% + 1.62% = 10.00%` / `21.01 ms/game`, losing `-2.55%`!).
   - **Why `S5` helped:** `Board::make_move` dropped from **`2.87%` (`6.216 ms/game`)** in `r15d` to **`1.71%` (`3.597 ms/game`)** in `bundle 1` (`-2.62 ms/game`).
   - **Remaining PGO time-profile targets in `r15d` selected for Step `PGO1`:**
     1. `TranspositionTable::probe_owned`: **`4.19%` (`9.066 ms/game`)** -> packed 56B `TTProbe`, `EmptyLock`, no-copy miss fast-path (`46.75%` misses), empty-slot-0 exit.
     2. `Board::has_legal_move` (**`1.56%` / `3.367 ms/game`**) + `Board::make_move` checker scan (`2.87%`) + `Board::is_legal_complete` (`1.02%` / `2.202 ms/game`) -> off-king-ray pawn push/capture fast-return, `known_gives_check == 0` checker skip, `ensure_king_lines()` reuse, and `(moving != WK && moving != BK)`.
     3. `Worker::should_stop_with`: **`0.54%` (`1.166 ms/game` self; `0.75%` / `1.577 ms/game` in `bundle 1`)** + caller overhead (`0.097%` cold in `bench` PGO vs `100%` hot in `go softnodes 2000`) -> `[[gnu::always_inline]]` `check_node_or_periodic_stop()` + `[[gnu::hot]]` on `apply_position_sv`.

---

## 3. Step Table (`PGO1`: Curated `S4 + S5 + S7` Winners + PGO Time-Profile Targets on `r15d`)

| Step | Patch File (`forge-combo29/carbon2/job10/...`) | Lines | Identity & Oracles (`pgo1_identity_and_bench13_raw.txt`, `pgo1_oracles_and_fault_raw.txt`) | Clang 18 ThinLTO + PGO Self-Play Timing vs `r15d` at `Hash 16` (`12` rounds x `60` games = `48` runs, `pgo_r15d_vs_pgo1_12x60_hash16_raw.txt`) | Prediction (`c4cf0089c`) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`PGO1`** | `pgo1_curated_pgo_winners_and_hot_stop_tt_stalemate.patch.txt` *(unified diff directly against `r15d`; zero `S1/S2/S3/S6/O2/W1/W2`)* | 1,060 | `PC20` + `net768`/`net512` `bench 11/13/16`, `250/250` depth-9 rows, `1,000` evals (both nets), 6-game traces (`4560d7c3afdeba2e`, `9ed22c1193ab96de`), `500,000`-op TT+stop oracle (`fd8c91bbb184a08b`), `55,868/55,868` evasion sequences, `-UNDEBUG` `S5` `compute_key()` assert, and `368,160` self-play searches (`ee465caeff9c0fcf`) **ALL EXACT**; stack `7104 -> 4544 B (-2560 B)` | **Engine CPU (`getrusage` ns):** `[1.0152, 1.0340, 1.0283, 1.0144, 1.0287, 1.0290, 1.0245, 1.0046, 1.0320, 1.0295, 1.0097, 1.0249]`<br>**Paired median: `1.0266x` (`+2.66%`, 95% CI `[1.0148x, 1.0292x]`)**, **pooled: `1.0255x` (`+2.55%`, 95% CI `[1.0149x, 1.0305x]`)**, **`12/12` faster** (`613.50 -> 629.16` cpu_sps)<br>A/A: `med(A2)/med(A1)=0.9964` (**`[0.9788, 1.0133]`**), `med(B2)/med(B1)=0.9957` (**`[0.9835, 1.0169]`**)<br>**Wall:** `[1.0161, 1.0331, 1.0184, 0.9974, 1.0239, 1.0287, 1.0162, 1.0113, 1.0220, 1.0185, 1.0091, 1.0170]`<br>**Paired median: `1.0177x` (`+1.77%`, 95% CI `[1.0137x, 1.0230x]`)**, pooled `1.0176x`, **`11/12` faster**; A/A `1.0010` (`[0.9834, 1.0148]`), `1.0017` (`[0.9851, 1.0299]`) | **MET** (`1.0266x` CPU inside `[1.020x, 1.045x]`, `12/12 >= 10/12` faster; `1.0177x` wall inside `[1.015x, 1.045x]`, `11/12 >= 10/12` faster; exceeds `A/A` max `1.0169`) | **CAUGHT** (`fd8c91bbb184a08b` vs `79219bb2501b9ff2` + `-UNDEBUG` `S5` assert abort, `pgo1_oracles_and_fault_raw.txt`) |

---

## 4. What We Would Do Next With Another 90 Minutes (Ranked)

1. **Test `PGO1` directly on the PC (`r15d + pgo1_curated_pgo_winners_and_hot_stop_tt_stalemate.patch.txt`):** Because `S1`, `S2`, and `S3` were responsible for dragging `bundle 1` down under Clang ThinLTO + PGO (`-1.78%`, `-0.92%`, `-1.65%`), `PGO1` ships **only** the verified Clang-PGO-positive steps (`S4 + S5 + S7`) plus the PGO time-profile targets (`TT` miss fast-path, `has_legal_move` + `known_gives_check`, and PGO-proof inline `check_node_or_periodic_stop`), in `1,060` clean lines against `r15d`.
2. **Eliminate the `3.24%` (`7.0 ms/game`) `std::sort` in `MovePicker::pick_best()` behind an off-by-default UCI option `LazyQuietPick` (`type check default false`):** In `pgo_time_profile_raw.txt` on `r15d`, `std::__final_insertion_sort` (`2.07%`) + `std::__introsort_loop` (`1.17%`) consume **`3.24%` of total PGO engine CPU** sorting all remaining quiet moves after 4 selection passes even though `67%` of quiet moves are never yielded. Because `std::sort` (`introsort`) changes equal-score tie-breaking relative to pure linear selection, replacing `std::sort` with on-demand SIMD argmax selection is a move-order change on equal scores and must be gated behind an off-by-default option and verified with a `>= 4,000`-game `20,000`-node `net768` match (`0` Elo loss + `~2.5%` speed gain).
3. **Include `go softnodes 2000` (5–10 short games) in the PC's PGO training stdin alongside `bench 11/13/16`:** Adding ~500 `position ... moves ...` + `go softnodes 2000` commands (~0.1s) to the PC's PGO profile run gives LLVM accurate non-zero branch weights for `node_limit_specified_`, `uci.cpp` (`position` / `info`), and short-search iteration exit without changing one line of engine C++.

---

## 5. Times, Runtime Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job10/stamps.txt`:**
  `Tue Nov 17 09:06:28 PM UTC 2026 | job 10 received (FABLE_TO_carbon2_10.md); starting Clang+libstdc++ ThinLTO+PGO setup and Step 0`
- **Last line of `forge-combo29/carbon2/job10/stamps.txt`:**
  `Tue Nov 17 10:27:42 PM UTC 2026 | finalizing REPORT_carbon2_job10.md and pushing branch`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon`

### Verbatim Pre-Commit Check (`git status --short && ls -R forge-combo29/carbon2/job10`)

```text
?? forge-combo29/carbon2/job10/REPORT_carbon2_job10.md
forge-combo29/carbon2/job10:
build_pgo_raw.txt
pgo1_curated_pgo_winners_and_hot_stop_tt_stalemate.patch.txt
pgo1_identity_and_bench13_raw.txt
pgo1_oracles_and_fault_raw.txt
pgo1_planted_fault.patch.txt
pgo_bundle1_steps_alone_6x60_hash16_raw.txt
pgo_r15d_vs_bundle1_12x60_hash16_raw.txt
pgo_r15d_vs_bundle4_12x60_hash16_raw.txt
pgo_r15d_vs_pgo1_12x60_hash16_raw.txt
pgo_time_profile_raw.txt
prediction_pgo1.txt
prediction_pgo_bundles.txt
REPORT_carbon2_job10.md
run_pgo_bundle1_steps_alone.py
stamps.txt
step0_pgo_raw.txt
```
