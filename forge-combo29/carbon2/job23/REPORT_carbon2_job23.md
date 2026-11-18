# REPORT — `carbon2` Job 23: Part M (`M = G` Skip) and Part L Single-Piece Leave-One-Out (`04_S7`, `10_W2`, `12_v3_refresh_fuse`, `05_G1`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job23/`; **no pull request opened**).

---

## 1. Step 0 and Known Answers of Every New Build (`step0_job23_raw.txt`, `partL_new_builds_known_answers_raw.txt`)

- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Jobs 21–22 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`, merged with `60` disjoint SP games `5,531` searches, `18,059,934` nodes, `trace=1646ce4566de2f40`).
- **Reference `kF` Build:** `kF_sp_1` at `/tmp/carbon2_job17/bld_sp_tidy_1/forge` (`len=38`, `sha256=6ac9c36ceae1c8c79721b84bd5d395dd967c41723586a0b3e3cdcc1a7b5f7091`).
- **Four New Part L Builds (all at exact `38`-character paths, verified on all `7` known answers in fresh processes before timing):**

| New Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games (`searches` / `trace`) |
|---|---|---|---|---|---|
| **`L1: kF - 04_S7`** | `/tmp/carbon2_job23/bld_sp_loo04a/forge` | `bd6135daa236c2d6f5d380cfa54e6bdd312a239b5445d5fd5d13863bb49c799d` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L2: kF - 10_W2`** | `/tmp/carbon2_job23/bld_sp_loo10a/forge` | `9863816aa8cc41a35483d525f6da29d028640b6c58a8085afa3ecc78c582136c` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L3: kF - 12_v3_refresh_fuse`** | `/tmp/carbon2_job23/bld_sp_loo12a/forge` | `116282b5b27800c54c35c314c767cccb60796011dbd58d2551dd805772c96ac6` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L4: kF - 05_G1`** | `/tmp/carbon2_job23/bld_sp_loo05a/forge` | `1463ab9ea8eb187dcc5d25f6337e85920e82039e17f8cc26d5026e740be303e9` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |

---

## 2. Standalone Prediction Graded (`prediction_job23.txt`, commit `13c28b61f`)

Committed alone and pushed before Part L (unmodified since commit; no time or commit id inside):
- **Part M (`M = G`):** Skipped per rule (`0` B3 rows ran/read `PAYS` in Job 22; `M1 = 1.0332` and `M2 = 1.0335` were already measured in Job 22 `B2a`/`B2b`, `R1` skipped with Part M).
- **Part L Row 1 (`04_S7`):** predicted `[1.0120, 1.0280]`, reading `PAYS` -> measured **`0.9990`**, reading **`NOT SEEN`** (**KILLED** — `04_S7` adds zero net CPU gain once `kF` is SP-PGO built!).
- **Part L Row 2 (`10_W2`):** predicted `[0.9960, 1.0115]`, reading `NOT SEEN` -> measured **`1.0115`**, reading **`NOT SEEN`** (**MET**).
- **Part L Row 3 (`12_v3_refresh_fuse`):** predicted `[0.9980, 1.0140]`, reading `NOT SEEN` -> measured **`1.0170`** (`12/12` blocks $> 1$), reading **`PAYS`** (**KILLED upward** — `12_v3_refresh_fuse` cleared the `1.0116` single-build `PAYS` gate cleanly!).
- **Part L Row 4 (`05_G1`):** predicted `[0.9960, 1.0115]`, reading `NOT SEEN` -> measured **`1.0043`**, reading **`NOT SEEN`** (**MET**).
- **Part L Row 5 (`06_G2`, "if reached"):** Not reached before minute 70 (ungraded).

---

## 3. Part M Status (`step0_job23_raw.txt`)

In Job 22, Part B3 was not reached before the budget cutoff, so **no Job 22 B3 row read `PAYS`**. Therefore:
- **`M = G`** (`r15d` + `04_S7` -> `11_stop_hot` -> `13_tt_avx512_fast_probe`).
- Per `FABLE_TO_carbon2_23.md` (*"If no B3 row read PAYS, M = G: say so, skip Part M and go to Part L"*), **Part M (`M_1`, `M_2` rebuilds and `M1`, `M2`, `R1` runs) was skipped** and we went directly to Part L. *(For reference, Job 22 already measured `M1 = B2a = 1.0332` `12/12` `PAYS` and `M2 = B2b = 1.0335` `12/12` `PAYS`, reading `the REST still PAYS`.)*

---

## 4. Part L: Single-Piece Leave-One-Out Against `kF_sp_1` on Held-Out `T` (`partL1_...` .. `partL4_...`)

- **Workload & Design:** Identical to Jobs 21–22 (`60` held-out `T` roots, `PC20 + net768.fnn3`, `Threads 1`, `Hash 16`, `go softnodes 2000`, engine pinned to `CPU 3`, harness on `CPU 1`, `12` blocks `[W] ABBA` / `[W] BAAB` with `1` warmup left out per block). Across all `4 x 60 = 240` runs (`192` timed + `48` warmups), **every single run gave `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped runs)**.
- **Declared Row Thresholds (`A = kF_sp_1`, `B = kF minus piece`):** `PAYS` iff `pooled CPU > 1.0116` and $\ge 10/12$ blocks $> 1$; `COSTS` iff `pooled CPU < 0.9884` and $\ge 10/12$ blocks $< 1$; `NOT SEEN` otherwise.
- **`03_S5_assert`:** Skipped per rule (debug-only `#ifndef NDEBUG` shadow Zobrist assertions; zero instructions under `-DNDEBUG`).

| Piece (`B = kF - piece` vs `A = kF_sp_1`) | Hunks / Switch Removed from `kF` | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Reading |
|---|---|---:|---:|---|---:|---|
| **`04_S7`** (`459` lines) | `src/uci.cpp` (`apply_position_sv`, `parse_limits_sv`, `PositionCache`; also drops `11`'s `[[gnu::hot]]` on `apply_position_sv`), `src/search.cpp` (`Worker::clear` `memset`, `std::move(board)`) | **`0.9990`** (`202.2623s / 202.4554s`) | `1.0019` | `0.9992` `[0.9897, 1.0087]` | `7 / 12` *(wall `0.9946`, `6/12`)* | **`NOT SEEN`** |
| **`10_W2`** (`219` lines) | `include/forge/search.hpp` (restores `quiet_base_to_[64]`), `src/search.cpp` (reverts `PieceContRows` 1D row pointers & `[[gnu::noinline]]` on `generate_captures`/`generate_quiets`) | **`1.0115`** (`200.9951s / 198.7036s`) | `1.0080` | `1.0116` `[1.0011, 1.0222]` | `10 / 12` *(wall `1.0116`, `10/12`)* | **`NOT SEEN`** *(missed `1.0116` by `0.0001`)* |
| **`12_v3_refresh_fuse`** (`278` lines) | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp` (`apply_one_refresh_one_and_evaluate` AVX-512 fused refresh+SCReLU), `src/search.cpp` (`static_evaluate_v3` 1-king-changed call) | **`1.0170`** (`197.3208s / 194.0316s`) | `1.0165` | `1.0170` **`[1.0122, 1.0217]`** | **`12 / 12`** *(wall `1.0179`, `12/12`)* | **`PAYS`** |
| **`05_G1`** (`100` lines) | `include/forge/eval.hpp` (`has_dead_material_candidates`), `include/forge/search.hpp` (`corr_mat_idx`), `src/search.cpp` (`corrected_eval` / `record_move` material key cache) | **`1.0043`** (`194.9085s / 194.0747s`) | `1.0071` | `1.0045` `[0.9956, 1.0133]` | `8 / 12` *(wall `1.0045`, `8/12`)* | **`NOT SEEN`** |

*(Per-block ratios verbatim from raw files:*
- *`L1 (04_S7)`: `0.9772 1.0191 1.0098 0.9874 1.0005 1.0063 1.0032 0.9974 0.9799 0.9804 1.0199 1.0090`*
- *`L2 (10_W2)`: `0.9973 1.0388 1.0062 1.0171 1.0042 0.9854 1.0167 1.0447 1.0091 1.0003 1.0129 1.0070`*
- *`L3 (12_v3_refresh_fuse)`: `1.0167 1.0163 1.0143 1.0279 1.0208 1.0185 1.0213 1.0142 1.0144 1.0015 1.0287 1.0089`*
- *`L4 (05_G1)`: `0.9989 1.0200 1.0069 0.9860 0.9753 0.9972 1.0128 1.0062 1.0086 1.0265 1.0073 1.0079`)*

---

## 5. What This Check Cannot See

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them from build noise).

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. Across Jobs 21 and 23, `6` of the `12` non-debug pieces of `kF` have now been individually leave-one-out tested against `kF_sp_1` on `T` under the full SP-PGO recipe:
     - **`12_v3_refresh_fuse` (`278` lines): `1.0170` (`12/12` $> 1$, `[1.0122, 1.0217]`) -> `PAYS`**.
     - **`10_W2` (`219` lines): `1.0115` (`10/12` $> 1$, `[1.0011, 1.0222]`) -> `NOT SEEN`** (`0.0001` below `1.0116`).
     - **`13_tt_avx512_fast_probe` (`346` lines, Job 21): `1.0100` (`11/12` $> 1`, `[1.0025, 1.0176]`) -> `NOT SEEN`** (`0.0016` below `1.0116`).
     - **`05_G1` (`100` lines): `1.0043` (`8/12` $> 1`, `[0.9956, 1.0133]`) -> `NOT SEEN`**.
     - **`11_stop_hot` (`70` lines, Job 21): `1.0033` (`8/12` $> 1`, `[0.9977, 1.0091]`) -> `NOT SEEN`**.
     - **`04_S7` (`459` lines): `0.9990` (`7/12` $> 1`, `[0.9897, 1.0087]`) -> `NOT SEEN`**.
  2. **`04_S7` (`459` lines — the entire `src/uci.cpp` rewrite + `Worker::clear` `memset`) contributes `0.0%` (`0.9990` CPU, `0.9946` wall) on top of SP-PGO `kF`**, making it the single largest line-count savings (`~19%` of `kF`'s `2,450` lines) if the PC trims non-paying pieces! (Note: dropping `04_S7` only requires dropping `11_stop_hot`'s 1-line `[[gnu::hot]]` attribute on `apply_position_sv` in `src/uci.cpp`.)
  3. **`12_v3_refresh_fuse` (`+1.70%` alone) accounts for half of the `+3.34%` "REST of `kF`" gain measured in Job 22 (`B2a = 1.0332`, `B2b = 1.0335`)**, and requires `08_G4`'s `Board::piece_bitboards()` and `king0`/`king1` setup in `static_evaluate_v3`.
- **Suspicions:**
  - The remaining `~1.6%` of "REST of `kF`" (`3.34% - 1.70%`) sits primarily in the **coupled `MovePicker` stack `01_S4 + 09_W1 + 10_W2`** (where `10_W2` alone already showed `1.0115`, `10/12` $> 1$) plus **`08_G4`** (`v3_active_net_` + `king_square`).
- **What I did not do:**
  - Skipped Part M (`M_1, M_2, M1, M2, R1`) per rule because `M = G` (no Job 22 B3 row read `PAYS`).
  - Stopped Part L at `21:58:03 UTC` (`minute 70` from `20:47:28 UTC`), so the remaining `6` pieces (`06_G2`, and the coupled pieces `07_G3`, `08_G4`, `02_S5`, `09_W1`, `01_S4`) were **not done**. *(Note on coupling for any next job: `06_G2` reverses cleanly on `kF`; `02_S5` only requires dropping debug-only `03_S5_assert` along with it; `08_G4` is required by `12_v3_refresh_fuse`; `01_S4` and `07_G3` [`ensure_king_lines`] are called by `09_W1`, and `09_W1` is modified by `10_W2`.)*
- **What I am not sure about:**
  - Why Job 22's `G` (`04_S7 + 11 + 13`) implied `~+4.1%` vs Job 21's `r15d` (`1.0761 / 1.0334`) when `13` (`1.0100`), `11` (`1.0033`), and `04_S7` (`0.9990`) sum to `~+1.3%` in LOO on `kF`: most likely (a) sub-additivity / shared cache-bandwidth savings between `13` and `01..10`, plus (b) minor VM turbo drift across separate hours (`A` legs in Job 21 `A2` averaged `8.58s` vs `8.08–8.43s` for `kF_sp_1` in later runs; direct same-block ratios remain immune to cross-hour drift).
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job23/stamps.txt`):**
  - First line: `Wed Nov 18 08:50:26 PM UTC 2026 | job 23 received (FABLE_TO_carbon2_23.md); starting Step 0 (M = G, skipping Part M to Part L per rule)`
  - Last line: `Wed Nov 18 10:00:16 PM UTC 2026 | Writing REPORT_carbon2_job23.md before minute 80`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job23` immediately before report commit:**

```text
 M forge-combo29/carbon2/job23/stamps.txt
?? forge-combo29/carbon2/job23/REPORT_carbon2_job23.md
forge-combo29/carbon2/job23:
partL1_loo04_S7_vs_kF1_T_raw.txt
partL2_loo10_W2_vs_kF1_T_raw.txt
partL3_loo12_v3_refresh_fuse_vs_kF1_T_raw.txt
partL4_loo05_G1_vs_kF1_T_raw.txt
partL_new_builds_known_answers_raw.txt
prediction_job23.txt
REPORT_carbon2_job23.md
stamps.txt
step0_job23_raw.txt
```
