# REPORT — `carbon2` Job 21: `kF` Stack Floor, Held-Out SP-PGO Comparison (`Part A`), and Top-Gain Leave-One-Out (`Part B`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job21/`; **no pull request opened**).

---

## 1. Step 0, Exact SP-PGO Build Recipe, Held-Out Workload `T`, and `A0` Known Answers (`step0_and_A0_known_answers_raw.txt`, `workload_T_60_roots.txt`)

- **Compiler, Linker, and Runtime:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, GNU `libstdc++.so.6`, `-march=sapphirerapids`.
- **Exact Build Recipe Commands (identical across `bld_sp_r15d_{1,2}`, `kF_sp_{1,2}`, and Part B LOO builds):**
  1. **Phase 1 (`-fprofile-instr-generate`):**
     ```bash
     clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -std=c++20 -O3 -DNDEBUG \
       -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS="$SRC/src/nnue_weights.inc" \
       -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
       -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 \
       -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 \
       -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread \
       -I"$SRC/include" -fprofile-instr-generate -c "$SRC/src/<tu>.cpp" -o "$BLD/obj_gen/<tu>.o"
     clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -O3 -march=sapphirerapids \
       -flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1 -fprofile-instr-generate -pthread \
       "$BLD/obj_gen"/*.o -o "$BLD/forge_prof"
     ```
  2. **Phase 2a (bench profile run -> `prof_<pid1>.profraw`):** Runs `bench 11`, `bench 13`, `bench 16` with `NNUEArchFile=/tmp/carbon2_work/net768.fnn3`, `NNUEArch=true`, and **only** the four options `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true` (**no other options set**).
  3. **Phase 2b (60-game self-play profile run -> `prof_<pid2>.profraw`):** `run_sp_profile_60games.py` (`PC20 + net768.fnn3`, `Hash 16`, `Threads 1`, `go softnodes 2000`, `60` profile roots `sp_candidates[-60:]`: `searches=5,531`, `nodes=18,059,934`, `trace=1646ce4566de2f40`). *(Note: Phase 2a and Phase 2b run as two separate `forge_prof` processes whose raw counter arrays are summed unweighted by `llvm-profdata-18 merge`, applied identically to every `r15d`, `kF`, and LOO build.)*
  4. **Phase 3 & 4 (`merge` + `-fprofile-instr-use`):**
     ```bash
     llvm-profdata-18 merge -output="$BLD/forge.profdata" "$BLD"/prof_*.profraw
     clang++-18 ... [same flags] -fprofile-instr-use="$BLD/forge.profdata" -Wno-profile-instr-unprofiled ... -o "$BLD/forge"
     ```
- **Held-Out Workload `T` (`workload_T_60_roots.txt`):** Out of `250` unique roots in `positions_250.txt`, `60` are Job 20's roots and `60` are the SP-PGO profile roots, leaving `130` untouched roots. `T` selects `60` evenly strided roots from those `130` (`L007, L009, L011, L013, L015, L022, L025, L027, L029, L031, ..., L158, L160, L162, L169`; full list in `workload_T_60_roots.txt`), verified `|T ∩ profile_60| = 0` and `|T ∩ job20_60| = 0`. Every `T` run produces `searches = 6,070`, `softnodes_sum = 26,711,499`, and `(bestmove, final_nodes)` `trace = 937e1660561173af`.
- **Pinned CPU Timing Setup:** 4 physical Xeon Sapphire Rapids cores (`0..3`, `1` thread/core); every timed engine process runs pinned alone on **CPU `3`** while the Python harness runs pinned on **CPU `1`**.
- **`A0` Known Answers on All Four Builds (fresh process per check, `step0_and_A0_known_answers_raw.txt`):**

| Build | Binary `sha256` (prefix) | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games (`searches` / `trace`) |
|---|---|---|---|---|
| `bld_sp_r15d_1` | `794589082e8a63f5...` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| `bld_sp_r15d_2` | `00b44d65d596a889...` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| `kF_sp_1` | `6ac9c36ceae1c8c7...` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| `kF_sp_2` | `7ef7c7e32820eb30...` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |

---

## 2. Standalone Prediction Graded (`prediction_partA.txt`, commit `e8596b2d8`)

Committed alone and pushed after `A0` and before `A1` (unmodified since commit; no time or commit id inside):
- **`A1` floor pooled CPU ratio:** predicted `[0.9930, 1.0070]` -> measured **`1.0016`** (**MET**).
- **`A2` (`kF_sp_1 / bld_sp_r15d_1`) pooled CPU ratio:** predicted `[0.9100, 0.9550]` -> measured **`0.9289`** (**MET**).
- **`A3` (`kF_sp_2 / bld_sp_r15d_2`) pooled CPU ratio:** predicted `[0.9100, 0.9550]` -> measured **`0.9296`** (**MET**).
- **Expected reading:** predicted **`GAINS`** -> measured **`GAINS`** (**MET**).

---

## 3. Part A: Floor and Stack Comparisons on Held-Out `T` (`partA1_...`, `partA2_...`, `partA3_...`)

Across all `3 x 60 = 180` runs (`3 x 48 = 144` timed runs + `36` left-out warmups), **every single run matched `searches=6,070`, `softnodes_sum=26,711,499`, `trace=937e1660561173af` (`0` dropped runs)**. Ratio per block = `B / A` (`< 1` means `B` uses less time than `A`).

### Table A1 — Floor: `B = bld_sp_r15d_2` vs `A = bld_sp_r15d_1` (`partA1_floor_r15d2_vs_r15d1_T_raw.txt`)
- **CPU (`B/A`) 12 block ratios:** `1.0021 1.0108 1.0249 0.9911 0.9896 1.0006 0.9860 1.0020 1.0068 0.9959 1.0107 0.9997`
  - **Median:** `1.0013` | **Pooled (`sumB/sumA`):** **`1.0016`** (`208.9736s / 208.6313s`) | **Mean:** `1.0017`, **95% $t$-CI ($\text{df}=11$):** `[0.9948, 1.0085]` | **Blocks $< 1$:** `5 / 12`
- **Wall (`B/A`) 12 block ratios:** `1.0032 1.0104 1.0225 0.9950 0.9888 1.0028 0.9857 1.0037 1.0043 1.0012 1.0130 0.9976`
  - **Median:** `1.0030` | **Pooled:** `1.0023` (`217.9101s / 217.4014s`) | **Mean:** `1.0024`, **95% $t$-CI ($\text{df}=11$):** `[0.9959, 1.0088]` | **Blocks $< 1$:** `4 / 12`

### Table A2 — Stack Arm 1: `B = kF_sp_1` vs `A = bld_sp_r15d_1` (`partA2_kF1_vs_r15d1_T_raw.txt`)
- **CPU (`B/A`) 12 block ratios:** `0.9285 0.9277 0.9263 0.9278 0.9292 0.9318 0.9306 0.9303 0.9272 0.9320 0.9284 0.9269`
  - **Median:** `0.9285` | **Pooled (`sumB/sumA`):** **`0.9289`** (`191.1654s / 205.8028s`, **`-7.11%` CPU time / `+7.65%` speedup**) | **Mean:** `0.9289`, **95% $t$-CI ($\text{df}=11$):** **`[0.9277, 0.9301]`** | **Blocks $< 1$:** **`12 / 12`**
- **Wall (`B/A`) 12 block ratios:** `0.9312 0.9290 0.9284 0.9276 0.9285 0.9342 0.9335 0.9335 0.9308 0.9340 0.9323 0.9287`
  - **Median:** `0.9310` | **Pooled:** `0.9310` (`199.7404s / 214.5484s`) | **Mean:** `0.9310`, **95% $t$-CI ($\text{df}=11$):** `[0.9294, 0.9325]` | **Blocks $< 1$:** **`12 / 12`**

### Table A3 — Stack Arm 2: `B = kF_sp_2` vs `A = bld_sp_r15d_2` (`partA3_kF2_vs_r15d2_T_raw.txt`)
- **CPU (`B/A`) 12 block ratios:** `0.9281 0.9308 0.9249 0.9294 0.9223 0.9274 0.9198 0.9340 0.9274 0.9451 0.9295 0.9367`
  - **Median:** `0.9288` | **Pooled (`sumB/sumA`):** **`0.9296`** (`191.6831s / 206.1949s`, **`-7.04%` CPU time / `+7.57%` speedup**) | **Mean:** `0.9296`, **95% $t$-CI ($\text{df}=11$):** **`[0.9254, 0.9339]`** | **Blocks $< 1$:** **`12 / 12`**
- **Wall (`B/A`) 12 block ratios:** `0.9300 0.9358 0.9264 0.9287 0.9237 0.9319 0.9217 0.9402 0.9278 0.9446 0.9319 0.9416`
  - **Median:** `0.9309` | **Pooled:** `0.9320` (`200.0843s / 214.6829s`) | **Mean:** `0.9320`, **95% $t$-CI ($\text{df}=11$):** `[0.9274, 0.9366]` | **Blocks $< 1$:** **`12 / 12`**

### Part A Declared Reading: **`GAINS`**
- Gate threshold: $\min(A1_{\text{pooled}}, 1 / A1_{\text{pooled}}) - 0.01 = \min(1.0016, 0.9984) - 0.01 =$ **`0.9884`**.
- Both `A2` (`0.9289 < 0.9884`, `12/12` blocks $< 1$) and `A3` (`0.9296 < 0.9884`, `12/12` blocks $< 1$) clear the gate by **`~5.9` percentage points**.

---

## 4. Part B: Leave-One-Out Against `kF_sp_1` on `T` (`partB_loo_identity_raw.txt`, `partB1_...`, `partB2_...`)

Ordered largest-measured-gain first (`13_tt_avx512_fast_probe` `+2.49%` in Job 16; `11_stop_hot` `+1.92%` in Job 14), built by the identical SP-PGO recipe, verified on all `6` `A0` known answers before timing (`partB_loo_identity_raw.txt`), and completed before minute 70 (`0` dropped runs; all `120` runs `trace=937e1660561173af`). Here `B = kF minus piece` and `A = kF_sp_1`, so **pooled CPU ratio $> 1.0000$ means the piece still pays under the SP-PGO recipe**:

| Piece (`kF` minus piece = `B` vs `kF_sp_1` = `A`) | Switch / Hunks Removed from `kF` | Pooled CPU Ratio (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ |
|---|---|---:|---:|---|---:|
| **`13_tt_avx512_fast_probe`** (`sha256=704fde90...`) | `include/forge/search.hpp` (`probe_owned_fast`), `src/search.cpp` (`store_owned_fast`, `Worker::probe_tt`/`store_tt` sites) | **`1.0100`** (`194.9814s / 193.0543s`) | `1.0133` | `1.0101` **`[1.0025, 1.0176]`** | **`11 / 12`** *(wall pooled `1.0098`, `11/12`)* |
| **`11_stop_hot`** (`sha256=dfae260b...`) | `include/forge/search.hpp` & `src/search.cpp` (`check_node_or_periodic_stop`, `fast_single_node_stop_`), `src/uci.cpp` (`[[gnu::hot]] apply_position_sv`) | **`1.0033`** (`196.1918s / 195.5438s`) | `1.0064` | `1.0034` **`[0.9977, 1.0091]`** | **`8 / 12`** *(wall pooled `1.0036`, `9/12`)* |

---

## 5. What This Check Cannot See

The PC's clang 23 for Windows, its processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings (8 random plies from the start position).

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. On a dedicated pinned physical Xeon Sapphire Rapids core (`CPU 3`, harness on `CPU 1`), `r15d` SP-PGO build-to-build floor `A1` is **`1.0016`** (`95% t-CI [0.9948, 1.0085]`), and both independent `kF` SP-PGO builds beat `r15d` by **`-7.11%` (`A2 = 0.9289`, `12/12`)** and **`-7.04%` (`A3 = 0.9296`, `12/12`)** CPU time on completely held-out roots `T` (`6,070` searches, `26,711,499` softnodes/run).
  2. Under leave-one-out on `kF` with the full SP-PGO recipe, **Piece `13` (`13_tt_avx512_fast_probe`)** unequivocally still pays (**`1.0100` pooled, `1.0133` median, `95% t-CI [1.0025, 1.0176]`, `11/12` blocks $> 1$**).
  3. **Piece `11` (`11_stop_hot`)** shows a smaller positive point estimate (`1.0033` pooled, `1.0064` median, `8/12` blocks $> 1$, wall `9/12` $> 1$), with its `95%` $t$-interval `[0.9977, 1.0091]` crossing `1.0000` (blocks `06, 07, 10` experienced minor host frequency drift across both `A` and `B` legs around `8.2-8.4s`).
- **Suspicions:**
  - Why `kF` holds `-7.1%` CPU (`~0.929`) under SP-PGO on AVX-512 Sapphire Rapids (`zmm_count: 1096 -> 1420`) while `sol2` saw `~0.969` under Clang 19 `-march=x86-64-v4` on a contended 5-core VM: (a) unpinned shared-core scheduling added `~12%` floor span (`0.9301..1.0510`) on `sol2`'s VM versus `[0.9860, 1.0249]` (`A1` SD `0.0108`, `A2` SD `0.0019`) on our pinned single core, and (b) pieces `08_G4`, `09_W1`, `12_v3_refresh_fuse`, and `13_tt_avx512_fast_probe` are explicit `512`-bit `ZMM` / `BMI2` `PEXT` transformations whose advantage scales with native `512`-bit execution (`sapphirerapids` and Zen 5 both have full-width `512`-bit pipelines).
- **What I did not do:**
  - Stopped Part B after LOO #2 (`11_stop_hot`) completed at `18:50:53 UTC` (`minute 70` from `17:40:48 UTC`), so LOO builds/timings for the remaining pieces of `kF` (`04_S7`, `09_W1`/`10_W2`, `05_G1..08_G4`, `01_S4`, `12_v3_refresh_fuse`, `02_S5`, and debug-only `03_S5_assert`) were **not done** due to the minute-70 Part B cutoff.
  - Did not alter `kF`, touch engine source in-tree, or run strength matches.
- **What I am not sure about:**
  - Whether `11_stop_hot`'s `+0.33%` pooled / `+0.64%` median LOO delta on Xeon expands or shrinks when 16 single-thread self-play engines run concurrently on the PC's Zen 5 (where L3/atomic coherence traffic is higher, though `nodes_` is unshared per-worker).
  - How much of `01..10`'s remaining `~5.5%` SP-PGO gain (`0.929` vs `~0.987` accounted by `13 + 11`) sits in `08_G4 + 12_v3_refresh_fuse` (NNUE v3 ZMM fusion) versus `06_G2..10_W2` (fused `MovePicker` + `SEE`) on Zen 5 Clang 23.
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job21/stamps.txt`):**
  - First line: `Wed Nov 18 05:40:48 PM UTC 2026 | job 21 received (FABLE_TO_carbon2_21.md); starting Step 0 & A0`
  - Last line: `Wed Nov 18 06:58:40 PM UTC 2026 | Job 21 all runs finished before minute 70; writing REPORT_carbon2_job21.md before minute 80`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job21` immediately before report commit:**

```text
 M forge-combo29/carbon2/job21/stamps.txt
?? forge-combo29/carbon2/job21/REPORT_carbon2_job21.md
forge-combo29/carbon2/job21:
partA1_floor_r15d2_vs_r15d1_T_raw.txt
partA2_kF1_vs_r15d1_T_raw.txt
partA3_kF2_vs_r15d2_T_raw.txt
partB1_loo13_tt_vs_kF1_T_raw.txt
partB2_loo11_stop_hot_vs_kF1_T_raw.txt
partB_loo_identity_raw.txt
prediction_partA.txt
REPORT_carbon2_job21.md
stamps.txt
step0_and_A0_known_answers_raw.txt
workload_T_60_roots.txt
```
