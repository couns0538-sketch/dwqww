# REPORT — `carbon2` Job 26: Workload `T` Time Profiles (`Part P`) and Piece `14_search_lazy_history_hoist` (`Part Q`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job26/`; **no pull request opened**).

---

## 1. Step 0 and Known Answers of Every New Build (`step0_and_kF14_known_answers_raw.txt`)

- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Jobs 21–25 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`, merged with `60` disjoint SP games `5,531` searches, `18,059,934` nodes, `trace=1646ce4566de2f40`).
- **Reference Builds:** `kF_sp_1` (`sha256=6ac9c36c...`), `kF_sp_2` (`sha256=7ef7c7e3...`), `bld_sp_r15d_1` (`sha256=79458908...`).
- **Two New Builds of `kF + 14` (exact `38`-character paths; verified on all `7` known answers, Job 20's 60-game signature, and `T`'s 60-game signature in fresh processes before timing):**

| New Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games | Workload `T` `60` Games (`searches / softnodes / trace`) |
|---|---|---|---|---|---|---|
| **`kF14_1`** | `/tmp/carbon2_job26/bld_sp_kF14_1/forge` | `d3194c30125d076fb77db14f652c76137d4e8363f57aa9b62f16b0b254ba5f1b` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` | `6070` / `26711499` / `937e1660561173af` |
| **`kF14_2`** | `/tmp/carbon2_job26/bld_sp_kF14_2/forge` | `b6b8229a1660696a350a31881e541cef5cd3de3f759ca12897326cd14e25f1ea` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` | `6070` / `26711499` / `937e1660561173af` |

---

## 2. Part P: Self-Time Profiles of `bld_sp_r15d_1` and `kF_sp_1` on `T` (`partP_r15d_vs_kF_T_profile_raw.txt`)

- **Profiler & Real Sampling Rate:** `LD_PRELOAD=/tmp/carbon2_job13/libprof_stack.so` (`ITIMER_PROF` `SIGPROF` CPU-time sampler), `5` sequential passes $\times$ `60` `T` games per binary on pinned `CPU 3` (`searches=6,070`, `softnodes_sum=26,711,499`, `trace=937e1660561173af` on all `10/10` passes):
  - **`bld_sp_r15d_1`:** `42.6927s` CPU (`8.5385s`/run), **`10,906` samples** (**real rate `255.5 Hz` = `3.91 ms/sample`**, kernel-tick bounded).
  - **`kF_sp_1`:** `39.7028s` CPU (`7.9406s`/run), **`10,119` samples** (**real rate `254.9 Hz` = `3.92 ms/sample`**).

### 2.1 Four-Group Self-Time Shares (`r15d` vs `kF`)

| Group | `bld_sp_r15d_1` Samples (`%`) | `kF_sp_1` Samples (`%`) | $\Delta$ Share (pp) |
|---|---:|---:|---:|
| **1. Evaluation and accumulator** | `2,339` (`21.45%`) | `2,062` (`20.38%`) | `-1.07%` |
| **2. Move generation and the move picker** | `1,615` (`14.81%`) | `1,158` (`11.44%`) | `-3.36%` |
| **3. The hash table** *(outlined symbols; `kF` inlines `probe_owned_fast`/`store_owned_fast` into `search`/`qsearch`)* | `403` (`3.70%`) | `42` (`0.42%`) | `-3.28%` |
| **4. Everything else** *(`Worker::search`, `qsearch`, `Board::*`, `[libc/libstdc++/kernel]`, etc.)* | `6,549` (`60.05%`) | `6,857` (`67.76%`) | `+7.71%` |
| **TOTAL** | **`10,906` (`100.00%`)** | **`10,119` (`100.00%`)** | `0.00%` |

### 2.2 Top 25 Functions by Self Time on `bld_sp_r15d_1`

| Rk | Samples | Share | Source File | Function |
|---:|---:|---:|---|---|
| 1 | `4,384` | `40.20%` | `src/search.cpp` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 2 | `1,023` | `9.38%` | `src/search.cpp` | `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` |
| 3 | `508` | `4.66%` | `src/nnue_v3.cpp` | `forge::nnue::v3::refresh_from_pieces(...)` |
| 4 | `473` | `4.34%` | `src/search.cpp` | `forge::MovePicker::generate_quiets()` |
| 5 | `450` | `4.13%` | `[external]` | `[libc / libstdc++ / kernel]` |
| 6 | `360` | `3.30%` | `src/search.cpp` | `forge::TranspositionTable::probe_owned(unsigned long) const` |
| 7 | `350` | `3.21%` | `src/board.cpp` | `forge::Board::see_ge(const Move&, int) const` |
| 8 | `346` | `3.17%` | `src/search.cpp` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 9 | `321` | `2.94%` | `src/search.cpp` | `std::__final_insertion_sort<..., MovePicker::pick_best()::...>` |
| 10 | `312` | `2.86%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_changes_pair(...)` |
| 11 | `296` | `2.71%` | `src/board.cpp` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 12 | `294` | `2.70%` | `src/board.cpp` | `forge::Board::has_legal_move() const` |
| 13 | `249` | `2.28%` | `src/nnue_v3.cpp` | `forge::nnue::v3::evaluate(const Net&, const Board&, const Accumulator&)` |
| 14 | `188` | `1.72%` | `src/search.cpp` | `std::__introsort_loop<..., MovePicker::pick_best()::...>` |
| 15 | `181` | `1.66%` | `src/search.cpp` | `forge::MovePicker::generate_evasions()` |
| 16 | `171` | `1.57%` | `src/board.cpp` | `forge::Board::generate_legal_evasions(MoveList&) const` |
| 17 | `160` | `1.47%` | `src/board.cpp` | `forge::Board::is_legal_complete(const Move&) const` |
| 18 | `118` | `1.08%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_changes(...)` |
| 19 | `112` | `1.03%` | `src/board.cpp` | `forge::fill_pseudo_legal<Quiets>(const Board&, MoveList&)` |
| 20 | `110` | `1.01%` | `src/search.cpp` | `forge::Worker::corrected_eval(const Board&, int, const SearchStack*) const` |
| 21 | `100` | `0.92%` | `src/board.cpp` | `forge::fill_pseudo_legal<Captures>(const Board&, MoveList&)` |
| 22 | `79` | `0.72%` | `src/board.cpp` | `forge::Board::is_pseudo_legal(const Move&) const` |
| 23 | `63` | `0.58%` | `src/board.cpp` | `forge::Board::refresh_king_lines() const` |
| 24 | `62` | `0.57%` | `src/search.cpp` | `forge::MovePicker::next(bool)` |
| 25 | `43` | `0.39%` | `src/search.cpp` | `forge::TranspositionTable::clear()` |

### 2.3 Top 25 Functions by Self Time on `kF_sp_1`

| Rk | Samples | Share | Source File | Function |
|---:|---:|---:|---|---|
| 1 | `4,703` | **`46.48%`** | `src/search.cpp` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 2 | `1,075` | `10.62%` | `src/search.cpp` | `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` |
| 3 | `532` | `5.26%` | `src/search.cpp` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 4 | `453` | `4.48%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_one_refresh_one_and_evaluate(...)` |
| 5 | `391` | `3.86%` | `[external]` | `[libc / libstdc++ / kernel]` |
| 6 | `310` | `3.06%` | `src/board.cpp` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 7 | `301` | `2.97%` | `src/board.cpp` | `forge::Board::see_ge(const Move&, int) const` |
| 8 | `292` | `2.89%` | `src/board.cpp` | `forge::Board::has_legal_move() const` |
| 9 | `243` | `2.40%` | `src/search.cpp` | `forge::MovePicker::generate_quiets()::{lambda(...)#1}::operator()` |
| 10 | `223` | `2.20%` | `src/nnue_v3.cpp` | `forge::nnue::v3::refresh_from_pieces(...)` |
| 11 | `180` | `1.78%` | `src/search.cpp` | `forge::MovePicker::generate_quiets()` |
| 12 | `176` | `1.74%` | `src/search.cpp` | `forge::MovePicker::generate_evasions()` |
| 13 | `170` | `1.68%` | `src/search.cpp` | `std::__introsort_loop<..., MovePicker::pick_best_scored()::...>` |
| 14 | `166` | `1.64%` | `src/board.cpp` | `forge::Board::generate_legal_evasions(MoveList&) const` |
| 15 | `162` | `1.60%` | `src/search.cpp` | `forge::MovePicker::generate_captures()` |
| 16 | `134` | `1.32%` | `src/nnue_v3.cpp` | `forge::nnue::v3::evaluate(const Net&, const Board&, const Accumulator&)` |
| 17 | `114` | `1.13%` | `src/board.cpp` | `forge::Board::is_legal_complete(const Move&) const` |
| 18 | `98` | `0.97%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_pair_and_evaluate(...)` |
| 19 | `85` | `0.84%` | `src/board.cpp` | `forge::Board::is_pseudo_legal(const Move&) const` |
| 20 | `61` | `0.60%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_changes(...)` |
| 21 | `49` | `0.48%` | `src/board.cpp` | `forge::Board::refresh_king_lines() const` |
| 22 | `42` | `0.42%` | `src/search.cpp` | `forge::TranspositionTable::clear()` |
| 23 | `28` | `0.28%` | `src/search.cpp` | `forge::Worker::ensure_threat_map(const Board&, int) const` |
| 24 | `23` | `0.23%` | `src/search.cpp` | `forge::MovePicker::next(bool)` |
| 25 | `21` | `0.21%` | `src/board.cpp` | `forge::Board::make_move(const Move&, Undo&, const unsigned long*, int)` |

### 2.4 Top 10 Functions Whose Self-Time Share Changed Most Between `r15d` and `kF`

| Rk | `r15d` Smp (`%`) | `kF` Smp (`%`) | $\Delta$ Share (pp) | Source File | Function |
|---:|---:|---:|---:|---|---|
| 1 | `4,384` (`40.20%`) | `4,703` (`46.48%`) | `+6.28%` | `src/search.cpp` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 2 | `0` (`0.00%`) | `453` (`4.48%`) | `+4.48%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_one_refresh_one_and_evaluate(...)` |
| 3 | `360` (`3.30%`) | `0` (`0.00%`) | `-3.30%` | `src/search.cpp` | `forge::TranspositionTable::probe_owned(unsigned long) const` |
| 4 | `321` (`2.94%`) | `0` (`0.00%`) | `-2.94%` | `src/search.cpp` | `std::__final_insertion_sort<..., MovePicker::pick_best()::...>` |
| 5 | `312` (`2.86%`) | `0` (`0.00%`) | `-2.86%` | `src/nnue_v3.cpp` | `forge::nnue::v3::apply_changes_pair(...)` |
| 6 | `473` (`4.34%`) | `180` (`1.78%`) | `-2.56%` | `src/search.cpp` | `forge::MovePicker::generate_quiets()` |
| 7 | `508` (`4.66%`) | `223` (`2.20%`) | `-2.45%` | `src/nnue_v3.cpp` | `forge::nnue::v3::refresh_from_pieces(...)` |
| 8 | `0` (`0.00%`) | `243` (`2.40%`) | `+2.40%` | `src/search.cpp` | `forge::MovePicker::generate_quiets()::{lambda(...)#1}::operator()` |
| 9 | `346` (`3.17%`) | `532` (`5.26%`) | `+2.08%` | `src/search.cpp` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 10 | `188` (`1.72%`) | `0` (`0.00%`) | `-1.72%` | `src/search.cpp` | `std::__introsort_loop<..., MovePicker::pick_best()::...>` |

---

## 3. Standalone Prediction Graded (`prediction_job26.txt`, commit `eb100dc2d`)

Committed alone and pushed after `kF14_1`/`kF14_2` known answers and before `Q1` (unmodified since commit; no time or commit id inside):
- **`Q1` (`A = kF_sp_1`, `B = kF14_1`) pooled CPU ratio:** predicted `[0.9885, 1.0010]` -> measured **`0.9901`** (**MET**).
- **`Q2` (`A = kF_sp_2`, `B = kF14_2`) pooled CPU ratio:** predicted `[0.9885, 1.0010]` -> measured **`0.9916`** (**MET**).
- **Expected Part Q reading:** predicted **`NOT SEEN`** -> measured **`NOT SEEN`** (**MET**).

---

## 4. Part Q: Piece `14_search_lazy_history_hoist.patch.txt`, Rows `Q1` & `Q2`, and Reading

- **Three-line explanation (why this function and what the change does):**
  1. `Worker::search` (`src/search.cpp`) is #1 in `kF` self time (`46.48%`), calling `quiet_history` or `capture_history_value` unconditionally on every legal move (`line 2727`) before pruning or LMR gates are checked.
  2. `capture_history_value` is `100%` unused whenever `CaptureFutilityBase == 0` (the default and `PC20`), and `quiet_history` (plus its lazy `LesserThreats` slider build) is unused on TT moves (`move_count == 1`), `depth == 1` moves, and quiet-futility-pruned moves.
  3. `14_search_lazy_history_hoist.patch.txt` (`152` lines on `kF`) hoists node-invariant history/continuation pointers and shallow-pruning thresholds out of the move loop and computes `quiet_history` / `capture_history_value` lazily (before `make_move` / singular extensions) only when history pruning or LMR actually reads it.
- **Timing Verification (`partQ1_...`, `partQ2_...`):** Across all `120` runs (`96` timed + `24` warmups) on held-out `T`, **every single run gave `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped runs)**.
- **Declared Reading Rule (`A = kF`, `B = kF + 14`):** `PAYS` iff both `Q1` and `Q2` read `pooled CPU < 0.9884` with $\ge 10/12$ blocks $< 1$; `COSTS` iff both read `> 1.0116` with $\ge 10/12$ blocks $> 1$; `NOT SEEN` otherwise.

| Row (`A = kF`, `B = kF + 14`) | 12 Block CPU Ratios (`B/A`) | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $< 1$ |
|---|---|---:|---:|---|---:|
| **`Q1`** (`kF_sp_1` vs `kF14_1`) | `0.9870 0.9920 0.9844 0.9871 0.9897 0.9942 0.9935 0.9889 0.9892 0.9894 0.9954 0.9908` | **`0.9901`** (`189.0192s / 190.9062s`) | `0.9895` | `0.9901` **`[0.9881, 0.9922]`** | **`12 / 12`** *(wall `0.9901`, `12/12` $< 1$)* |
| **`Q2`** (`kF_sp_2` vs `kF14_2`) | `0.9943 0.9935 0.9907 0.9906 0.9925 0.9841 0.9910 0.9947 0.9940 0.9888 0.9916 0.9931` | **`0.9916`** (`188.2774s / 189.8810s`) | `0.9920` | `0.9916` **`[0.9897, 0.9934]`** | **`12 / 12`** *(wall `0.9903`, `12/12` $< 1$)* |

- **Part Q Reading:** **`NOT SEEN`** under the declared `< 0.9884` (`-1.16%`) bar (`Q1 = 0.9901` and `Q2 = 0.9916` miss `0.9884` by `0.0017` and `0.0032`), while **both independent SP-PGO builds agree on a real `~0.92%` CPU reduction (`24 / 24` blocks `< 1.0000`, `Q1` 95% $t$-CI `[0.9881, 0.9922]`, `Q2` 95% $t$-CI `[0.9897, 0.9934]`)**!

---

## 5. What This Check Cannot See

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings; gains below about 1 % (two builds can separate them only when both agree).

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. On held-out `T`, `kF` reduced self-time samples in `move generation and the move picker` (`14.81% -> 11.44%`) and outlined `the hash table` (`3.70% -> 0.42%`), leaving `Worker::search` (`46.48%` self) and `Worker::static_evaluate_v3` (`10.62%` self) as `57.10%` of the entire engine.
  2. Piece `14` (`14_search_lazy_history_hoist.patch.txt`, `152` lines on `kF`) preserves every node and trace across all checks and speeds `kF` up across **all `24 / 24` blocks** of two independent SP-PGO build pairs (`Q1 = 0.9901 [0.9881, 0.9922]`, `Q2 = 0.9916 [0.9897, 0.9934]`, wall `0.9901` and `0.9903`), reading `NOT SEEN` solely because `-0.92%` is smaller than the `-1.16%` (`0.9884`) single-build-floor margin.
- **Suspicions:**
  - Because `Q1` and `Q2` are two completely independent SP-PGO build pairs (`kF14_1` vs `kF_sp_1` and `kF14_2` vs `kF_sp_2`) and **both** show `-0.99%` and `-0.84%` with `24/24` blocks `< 1.0`, Piece `14` is a genuine `~0.9%` improvement (not single-build layout luck), mostly from eliminating `100%` of dead `capture_history_value` calls (`CaptureFutilityBase == 0`) and dead `quiet_history` + `LesserThreats` builds on TT moves and futility-pruned quiets.
- **What I did not do:**
  - Did not modify pieces `01..13`, alter engine source in-tree, change any net file, or run strength matches.
- **What I am not sure about:**
  - Whether on Zen 5 (`512` KB -> `1` MB L2 per core, 16 concurrent engines sharing `32`/`96` MB 3D V-Cache) skipping those multi-table history/continuation cache-line loads on TT moves and captures saves slightly more (`> 1%`) or about the same `~0.9%`.
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job26/stamps.txt`):**
  - First line: `Thu Nov 19 12:24:28 AM UTC 2026 | job 26 received (FABLE_TO_carbon2_26.md); starting Step 0 & Part P profiles on T`
  - Last line: `Thu Nov 19 12:58:08 AM UTC 2026 | Writing REPORT_carbon2_job26.md (34 minutes elapsed of 80-minute target)`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job26` immediately before report commit:**

```text
 M forge-combo29/carbon2/job26/stamps.txt
?? forge-combo29/carbon2/job26/REPORT_carbon2_job26.md
forge-combo29/carbon2/job26:
14_search_lazy_history_hoist.patch.txt
partP_r15d_vs_kF_T_profile_raw.txt
partQ1_kF14_1_vs_kF1_T_raw.txt
partQ2_kF14_2_vs_kF2_T_raw.txt
prediction_job26.txt
REPORT_carbon2_job26.md
stamps.txt
step0_and_kF14_known_answers_raw.txt
```
