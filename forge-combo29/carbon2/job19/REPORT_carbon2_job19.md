# REPORT — `carbon2` Job 19: Self-Play Time Map (`r15d` vs `01..13 + tidy`) and `TranspositionTable::clear` Share Audit

- **Agent / Branch:** `carbon2` on `for-fable-and-opus/carbon2-work` (no engine source modified in-tree; text files only under `forge-combo29/carbon2/job19/`; **no pull request opened**).
- **Final Stack Status:** Unchanged at **`job17/stack_r15d_to_final.patch.txt`** (`01..13 + tidy`, `2,450` lines, `sha256=3d2ce0852fe18d9953fb446950aa90fb67dbdb768c2e229a193e918e54beeb63`). In Part A, no piece is written; in Part B, `TranspositionTable::clear()` measured **`0.4128%`** (`< 0.50%` threshold) of 60-game engine CPU (`0.38%` in `SIGPROF`), so per Part B's rule we stopped with the counts.

---

## 0. Step 0: Builds, Compiler, and Profiler Settings (`step0_job19_raw.txt`)

- **Compiler, Linker, and Runtime:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18` (`18.1.3`), GNU `libstdc++.so.6` (`/lib/x86_64-linux-gnu/libstdc++.so.6`).
- **Compile Switches (`-march=sapphirerapids`):** `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread`.
- **SP-PGO Binaries Audited in Step 0:**
  1. **`r15d` unmodified SP-PGO (`/tmp/carbon2_job11/bld_sp_r15d_1/forge`):** `799,928` bytes, `sha256=79458908...`, `zmm_count=1096`, `2` `.profraw` merged into `forge.profdata` (`sha256=9a8d5e27...`; `bench 11/13/16` + `60` disjoint SP games: `searches=5,531`, `nodes=18,059,934`, `trace=1646ce4566de2f40`).
  2. **`01..13 + tidy` unmodified SP-PGO (`/tmp/carbon2_job17/bld_sp_tidy_1/forge`, `A1` of Job 18):** `827,616` bytes, `sha256=6ac9c36c...`, `zmm_count=1420`, `2` `.profraw` merged into `forge.profdata` (`sha256=84b1d317...`; `bench 11/13/16` + `60` disjoint SP games: `searches=5,531`, `nodes=18,059,934`, `trace=1646ce4566de2f40`).
  3. **Phase-4 frame-pointer companions for caller-inclusive call-stack walks (same `forge.profdata`, adding `-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer`):**
     - `/tmp/carbon2_job19/bld_sp_r15d_1_fp/forge` (`797,056` bytes, `sha256=03409731...`, `zmm_count=1098`, from `bld_sp_r15d_1/forge.profdata`).
     - `/tmp/carbon2_job19/bld_sp_tidy_1_fp/forge` (`824,912` bytes, `sha256=2a52e9bb...`, `zmm_count=1422`, from `bld_sp_tidy_1/forge.profdata`).
- **Profiler & Settings (identical to Job 13 `curated_sp_time_profile_raw.txt`):**
  - `LD_PRELOAD=/tmp/carbon2_job13/libprof_stack.so` (`sha256=d7e7f947...`, compiled from `libprof_stack.c` `sha256=cb9aff90...`).
  - Installs `SIGPROF` (`SA_SIGINFO | SA_RESTART`) armed via `setitimer(ITIMER_PROF, it_interval = 200 us)` (pure CPU-time sampling; idle/pipe wait is never sampled).
  - Each `SIGPROF` records `REG_RIP` (`pcs[0]` -> self leaf) and walks the bounded `8`-byte-aligned `RBP` chain within `[rsp, rsp + 8 MiB]` up to depth `40` (`pcs[1..d-1]` -> recursion-deduplicated caller-inclusive attribution). Symbols resolved against each PIE binary's ELF `.symtab` (`nm -nSC --defined-only`, `LOAD[0]` `VirtAddr = 0x0`).
  - **Method:** `5` sequential passes x `60` `Hash 16` SP games (`300` games/binary, one process at a time, zero concurrency) on `PC20 + net768.fnn3`, `go softnodes 2000`, the `60` roots of `positions_250.txt`.

---

## 1. Part A: Where Self-Play Time Goes (`partA_r15d_vs_stack_time_profile_raw.txt`, `partA_top3_calls_per_node_raw.txt`)

### 1.1 Known Answer (Verified Before Any Table)
Every single 60-game pass across all `4` profiled binaries (`20/20` passes) and all `4` counter/timer runs produced the exact known answer:
- **`searches = 7,670`, `nodes = 25,641,316`, `trace = ee465caeff9c0fcf`**.
- Mean engine CPU under the profiler (`5 x 60` games):
  - Unmodified SP-PGO: `r15d` **`198.826 ms/game`** (`15,751` samples) -> `01..13 + tidy` (`A1`) **`184.510 ms/game`** (`14,583` samples), **`-14.316 ms/game` (`1.0776x`)**.
  - Frame-pointer Phase-4 SP-PGO: `r15d_fp` **`198.378 ms/game`** (`15,643` samples) -> `tidy_fp` **`187.088 ms/game`** (`14,811` samples), **`-11.290 ms/game` (`1.0603x`)**.

### 1.2 Top 25 Functions by Self Time — Unmodified SP-PGO `r15d` vs `01..13 + tidy` (`A1`) (`partA_r15d_vs_stack_time_profile_raw.txt` Table A1)

*(Ranked `1..25` by `01..13 + tidy` self samples; followed by the `7` functions from `r15d`'s Top-25 that dropped to `0` samples in `01..13 + tidy` because the stack inlined, fused, or replaced them.)*

| Rk | `r15d` Smp | `r15d` Self% | `r15d` ms/g | Stack Smp | Stack Self% | Stack ms/g | $\Delta$ Share (pp) | $\Delta$ ms/g | Function |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `5,533` | `35.13%` | `69.843` | `5,796` | `39.74%` | `73.333` | `+4.62%` | `+3.490` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` *(absorbs inlined `probe_owned_fast`, `store_owned_fast`, `corrected_eval`)* |
| 2 | `1,677` | `10.65%` | `21.169` | `1,888` | `12.95%` | `23.888` | `+2.30%` | `+2.719` | `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` *(absorbs inlined `apply_pair_and_sum_avx512`)* |
| 3 | `761` | `4.83%` | `9.606` | `1,199` | `8.22%` | `15.170` | `+3.39%` | `+5.564` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` *(absorbs inlined `probe_owned_fast`, `store_owned_fast`, `corrected_eval`)* |
| 4 | `0` | `0.00%` | `0.000` | `759` | `5.20%` | `9.603` | `+5.20%` | `+9.603` | `forge::nnue::v3::apply_one_refresh_one_and_evaluate(...)` *(new in `12_v3_refresh_fuse`; replaces `refresh_from_pieces` + `apply_changes` + `evaluate`)* |
| 5 | `623` | `3.96%` | `7.864` | `581` | `3.98%` | `7.351` | `+0.03%` | `-0.513` | `forge::Board::see_ge(const Move&, int) const` |
| 6 | `773` | `4.91%` | `9.758` | `574` | `3.94%` | `7.262` | `-0.97%` | `-2.495` | `[libc / libstdc++ / kernel]` *(`04_S7` zero-alloc `string_view` UCI + `11_stop_hot`)* |
| 7 | `0` | `0.00%` | `0.000` | `423` | `2.90%` | `5.352` | `+2.90%` | `+5.352` | `forge::MovePicker::generate_captures()` *(outlined in `06_G2`, replacing `fill_pseudo_legal<Captures>` + scoring loop)* |
| 8 | `893` | `5.67%` | `11.272` | `398` | `2.73%` | `5.036` | `-2.94%` | `-6.237` | `forge::nnue::v3::refresh_from_pieces(...)` *(cut `-55.4%` by `12_v3_refresh_fuse`)* |
| 9 | `300` | `1.90%` | `3.787` | `306` | `2.10%` | `3.872` | `+0.19%` | `+0.085` | `forge::Board::has_legal_move() const` |
| 10 | `613` | `3.89%` | `7.738` | `287` | `1.97%` | `3.631` | `-1.92%` | `-4.107` | `forge::MovePicker::generate_quiets()` *(fused in `07_G3`)* |
| 11 | `314` | `1.99%` | `3.964` | `286` | `1.96%` | `3.619` | `-0.03%` | `-0.345` | `forge::MovePicker::generate_evasions()` |
| 12 | `268` | `1.70%` | `3.383` | `271` | `1.86%` | `3.429` | `+0.16%` | `+0.046` | `forge::Board::generate_legal_evasions(MoveList&) const` |
| 13 | `0` | `0.00%` | `0.000` | `256` | `1.76%` | `3.239` | `+1.76%` | `+3.239` | `forge::MovePicker::generate_quiets()::{lambda(...)#1}::operator()` *(`07_G3` piece quiet emitter)* |
| 14 | `256` | `1.63%` | `3.232` | `247` | `1.69%` | `3.125` | `+0.07%` | `-0.106` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 15 | `330` | `2.10%` | `4.166` | `215` | `1.47%` | `2.720` | `-0.62%` | `-1.445` | `forge::nnue::v3::evaluate(const Net&, const Board&, const Accumulator&)` |
| 16 | `0` | `0.00%` | `0.000` | `207` | `1.42%` | `2.619` | `+1.42%` | `+2.619` | `std::__introsort_loop<..., MovePicker::pick_best_scored()::...>` *(deferred sort in `09_W1`, down from `7.195 ms/g` in `pick_best` sorts)* |
| 17 | `185` | `1.17%` | `2.335` | `119` | `0.82%` | `1.506` | `-0.36%` | `-0.830` | `forge::Board::is_legal_complete(const Move&) const` *(`09_W1` `MovePicker` king-lines legality fast path)* |
| 18 | `99` | `0.63%` | `1.250` | `111` | `0.76%` | `1.404` | `+0.13%` | `+0.155` | `forge::Board::is_pseudo_legal(const Move&) const` |
| 19 | `209` | `1.33%` | `2.638` | `101` | `0.69%` | `1.278` | `-0.63%` | `-1.360` | `forge::MovePicker::next(bool)` *(`09_W1`)* |
| 20 | `0` | `0.00%` | `0.000` | `96` | `0.66%` | `1.215` | `+0.66%` | `+1.215` | `forge::nnue::v3::apply_pair_and_evaluate(...)` *(`08_G4`, non-inlined remainder)* |
| 21 | `122` | `0.77%` | `1.540` | `81` | `0.56%` | `1.025` | `-0.22%` | `-0.515` | `forge::Board::refresh_king_lines() const` |
| 22 | `195` | `1.24%` | `2.461` | `73` | `0.50%` | `0.924` | `-0.74%` | `-1.538` | `forge::nnue::v3::apply_changes(...)` *(cut `-62.5%` by `12_v3_refresh_fuse`)* |
| 23 | `70` | `0.44%` | `0.884` | `56` | `0.38%` | `0.709` | `-0.06%` | `-0.175` | `forge::TranspositionTable::clear()` |
| 24 | `0` | `0.00%` | `0.000` | `51` | `0.35%` | `0.645` | `+0.35%` | `+0.645` | `forge::Board::make_move(const Move&, Undo&, const unsigned long*, int)` *(`02_S5` `known_gives_check` overload)* |
| 25 | `0` | `0.00%` | `0.000` | `45` | `0.31%` | `0.569` | `+0.31%` | `+0.569` | `forge::Worker::ensure_threat_map(const Board&, int) const` |
| — | `552` | `3.50%` | `6.968` | `0` | `0.00%` | `0.000` | `-3.50%` | `-6.968` | *(r15d Top-25 eliminated)* `forge::TranspositionTable::probe_owned(unsigned long) const` -> inlined `probe_owned_fast` (`13`) |
| — | `495` | `3.14%` | `6.248` | `0` | `0.00%` | `0.000` | `-3.14%` | `-6.248` | *(r15d Top-25 eliminated)* `forge::nnue::v3::apply_changes_pair(...)` -> fused `apply_pair_and_evaluate` (`08_G4`) |
| — | `360` | `2.29%` | `4.544` | `0` | `0.00%` | `0.000` | `-2.29%` | `-4.544` | *(r15d Top-25 eliminated)* `std::__final_insertion_sort<..., pick_best()::...>` -> `09_W1` AVX-512 linear scan |
| — | `286` | `1.82%` | `3.610` | `0` | `0.00%` | `0.000` | `-1.82%` | `-3.610` | *(r15d Top-25 eliminated)* `forge::Worker::corrected_eval(...)` -> branchless table lookup (`05_G1`, `10_W2`) |
| — | `237` | `1.50%` | `2.992` | `0` | `0.00%` | `0.000` | `-1.50%` | `-2.992` | *(r15d Top-25 eliminated)* `forge::fill_pseudo_legal<Captures>(...)` -> fused `generate_captures` (`06_G2`) |
| — | `210` | `1.33%` | `2.651` | `0` | `0.00%` | `0.000` | `-1.33%` | `-2.651` | *(r15d Top-25 eliminated)* `std::__introsort_loop<..., pick_best()::...>` -> `09_W1` `pick_best_scored` |
| — | `149` | `0.95%` | `1.881` | `0` | `0.00%` | `0.000` | `-0.95%` | `-1.881` | *(r15d Top-25 eliminated)* `forge::fill_pseudo_legal<Quiets>(...)` -> fused `generate_quiets` (`07_G3`) |

### 1.3 Top 25 Functions by Time Including Callees — `r15d_fp` vs `tidy_fp` (`partA_r15d_vs_stack_time_profile_raw.txt` Table A2)

| Rk | `r15d` Smp | `r15d` Incl% | `r15d` ms/g | Stack Smp | Stack Incl% | Stack ms/g | $\Delta$ Share (pp) | $\Delta$ ms/g | Function (Recursion-Deduplicated Caller-Inclusive) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `15,611` | `99.80%` | `197.972` | `14,783` | `99.81%` | `186.734` | `+0.02%` | `-11.238` | `[libc / libstdc++ / kernel]` *(thread entry + runtime)* |
| 2 | `15,091` | `96.47%` | `191.378` | `14,285` | `96.45%` | `180.443` | `-0.02%` | `-10.934` | `forge::uci_loop(std::istream&)::$_9::operator()() const` *(search worker thread)* |
| 3 | `15,007` | `95.93%` | `190.312` | `14,247` | `96.19%` | `179.963` | `+0.26%` | `-10.349` | `forge::Searcher::search(Board, const SearchLimits&, bool, TTAccess)` |
| 4 | `15,007` | `95.93%` | `190.312` | `14,243` | `96.17%` | `179.913` | `+0.23%` | `-10.400` | `forge::Worker::search(Board, const SearchLimits&, bool, const vector<Worker*>&)` *(ID loop)* |
| 5 | `14,816` | `94.71%` | `187.890` | `14,061` | `94.94%` | `177.614` | `+0.22%` | `-10.276` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 6 | `3,855` | `24.64%` | `48.887` | `3,780` | `25.52%` | `47.748` | `+0.88%` | `-1.140` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 7 | `3,610` | `23.08%` | `45.780` | `3,406` | `23.00%` | `43.023` | `-0.08%` | `-2.757` | `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` |
| 8 | `0` | `0.00%` | `0.000` | `703` | `4.75%` | `8.880` | `+4.75%` | `+8.880` | `forge::nnue::v3::apply_one_refresh_one_and_evaluate(...)` |
| 9 | `590` | `3.77%` | `7.482` | `643` | `4.34%` | `8.122` | `+0.57%` | `+0.640` | `forge::MovePicker::generate_evasions()` |
| 10 | `616` | `3.94%` | `7.812` | `633` | `4.27%` | `7.996` | `+0.34%` | `+0.184` | `forge::MovePicker::next(bool)` |
| 11 | `655` | `4.19%` | `8.306` | `573` | `3.87%` | `7.238` | `-0.32%` | `-1.068` | `forge::Board::see_ge(const Move&, int) const` |
| 12 | `789` | `5.04%` | `10.006` | `547` | `3.69%` | `6.910` | `-1.35%` | `-3.096` | `forge::MovePicker::generate_quiets()` |
| 13 | `523` | `3.34%` | `6.632` | `494` | `3.34%` | `6.240` | `-0.01%` | `-0.392` | `_start` *(main UCI thread)* |
| 14 | `518` | `3.31%` | `6.569` | `492` | `3.32%` | `6.215` | `+0.01%` | `-0.354` | `forge::uci_loop(std::istream&)` *(main UCI thread incl. `clear`/`position`/pipe)* |
| 15 | `908` | `5.80%` | `11.515` | `433` | `2.92%` | `5.470` | `-2.88%` | `-6.045` | `forge::nnue::v3::refresh_from_pieces(...)` |
| 16 | `0` | `0.00%` | `0.000` | `408` | `2.75%` | `5.154` | `+2.75%` | `+5.154` | `forge::MovePicker::generate_captures()` |
| 17 | `304` | `1.94%` | `3.855` | `324` | `2.19%` | `4.093` | `+0.24%` | `+0.237` | `forge::Board::has_legal_move() const` |
| 18 | `311` | `1.99%` | `3.944` | `309` | `2.09%` | `3.903` | `+0.10%` | `-0.041` | `forge::Board::generate_legal_evasions(MoveList&) const` |
| 19 | `0` | `0.00%` | `0.000` | `256` | `1.73%` | `3.234` | `+1.73%` | `+3.234` | `forge::MovePicker::generate_quiets()::{lambda(...)#1}::operator()` |
| 20 | `259` | `1.66%` | `3.285` | `236` | `1.59%` | `2.981` | `-0.06%` | `-0.303` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 21 | `0` | `0.00%` | `0.000` | `233` | `1.57%` | `2.943` | `+1.57%` | `+2.943` | `std::__introsort_loop<..., MovePicker::pick_best_scored()::...>` |
| 22 | `353` | `2.26%` | `4.477` | `226` | `1.53%` | `2.855` | `-0.73%` | `-1.622` | `forge::nnue::v3::evaluate(const Net&, const Board&, const Accumulator&)` |
| 23 | `155` | `0.99%` | `1.966` | `146` | `0.99%` | `1.844` | `-0.01%` | `-0.121` | `forge::Worker::search(root)::$_1::operator()` *(root aspiration window body)* |
| 24 | `188` | `1.20%` | `2.384` | `122` | `0.82%` | `1.541` | `-0.38%` | `-0.843` | `forge::Board::is_legal_complete(const Move&) const` |
| 25 | `104` | `0.66%` | `1.319` | `116` | `0.78%` | `1.465` | `+0.12%` | `+0.146` | `forge::Worker::search_child(Board&, SearchStack*, int, int, int, bool)` |
| — | `526` | `3.36%` | `6.671` | `0` | `0.00%` | `0.000` | `-3.36%` | `-6.671` | *(r15d Top-25 eliminated)* `forge::TranspositionTable::probe_owned(unsigned long) const` |
| — | `489` | `3.13%` | `6.201` | `0` | `0.00%` | `0.000` | `-3.13%` | `-6.201` | *(r15d Top-25 eliminated)* `forge::nnue::v3::apply_changes_pair(...)` |
| — | `365` | `2.33%` | `4.629` | `0` | `0.00%` | `0.000` | `-2.33%` | `-4.629` | *(r15d Top-25 eliminated)* `std::__final_insertion_sort<..., pick_best()::...>` |
| — | `256` | `1.64%` | `3.246` | `0` | `0.00%` | `0.000` | `-1.64%` | `-3.246` | *(r15d Top-25 eliminated)* `forge::fill_pseudo_legal<Captures>(...)` |
| — | `244` | `1.56%` | `3.094` | `0` | `0.00%` | `0.000` | `-1.56%` | `-3.094` | *(r15d Top-25 eliminated)* `forge::Worker::corrected_eval(...)` |
| — | `212` | `1.36%` | `2.688` | `0` | `0.00%` | `0.000` | `-1.36%` | `-2.688` | *(r15d Top-25 eliminated)* `std::__introsort_loop<..., pick_best()::...>` |

### 1.4 The Three Largest Shares of `01..13 + tidy`: Calls per Node and What One Call Does (`partA_top3_calls_per_node_raw.txt`)

Both self-time (`Table A1` Ranks `1..3`) and recursive engine caller-inclusive time (`Table A2` Ranks `5..7`, beneath the 1-call-per-search outer entry wrappers `[libc] -> uci_loop::$_9 -> Searcher::search -> Worker::search(root)` at `7,670` calls = `0.0003` calls/node) identify the **exact same three engine functions**. *(Note: under `InfoOnce=false` + `go softnodes 2000`, completed ID iterations report `25,641,316` total `info depth` nodes across `7,670` searches, while partial ID iterations that abort on the node cap execute an additional `7,223,590` `++local_nodes_`, bringing total executed `local_nodes_` to `32,864,906 = 22,538,302 search + 10,326,604 qsearch`; both denominators are given below.)*

1. **`forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` (`src/search.cpp:2400-3100`) — `39.74%` self (`73.333 ms/g`), `94.94%` incl (`177.614 ms/g`):**
   - **Calls:** **`28,164,976` entries** (`1.0984` / reported node | `0.8570` / executed node).
     - `5,625,743` entries (`0.2194` / info node) have `depth <= 0` and immediately tail-handoff to `qsearch_child`.
     - **`22,538,302` interior nodes** (`0.8790` / info node | `68.58%` of executed nodes) increment `local_nodes_`; `4,403,372` (`0.1717` / info node) return on a non-PV TT cutoff; the remaining nodes run static eval + pruning (RFP, razoring, null-move, ProbCut `93,507` child moves) and the main `MovePicker` loop (`27,263,100` child moves made = `1.210` moves/interior node).
   - **What one interior call does:** Checks periodic stop (`check_node_or_periodic_stop`), repetition/50-move/mate-distance bounds (`upcoming_repetition`), probes the `64`-byte TT cluster via inlined AVX-512 `probe_owned_fast`, evaluates `static_evaluate_v3` + table `corrected_eval` (unless `in_check` or cached in `tte.eval`), applies hindsight/RFP/razoring/null-move/ProbCut/IIR, iterates `MovePicker::next` with SEE/futility/history/LMR pruning, prefetches child TT clusters (`key_after`), makes/unmakes moves (`known_gives_check`), updates quiet/capture/continuation/correction histories on fail-high, and writes back via `store_owned_fast`.

2. **`forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` (`src/search.cpp:3874-3940`) — `12.95%` self (`23.888 ms/g`), `23.00%` incl (`43.023 ms/g`):**
   - **Calls:** **`13,172,445` calls** (`0.5137` / reported node | `0.4008` / executed node).
     - **`59.55%` (`7,844,261` calls = `6,834,074` same king sq + `1,010,187` same king key, `0.3059` / info node):** executes inlined `apply_pair_and_sum_avx512` (`08_G4`), updating both `768`-wide `int16` accumulators from `parent` (`c0.count, c1.count in {2,3}`) and accumulating the `QA=255` SCReLU `w2` dot product in a single `24`-iteration `ZMM` pass (`accounted inside static_evaluate_v3 self`).
     - **`18.14%` (`2,389,507` calls, `0.0932` / info node):** calls `apply_one_refresh_one_and_evaluate` (`12_v3_refresh_fuse`, Rank 4 self at `5.20%` = `9.603 ms/g`), incrementally updating the unchanged king's perspective while Finny-cache-diffing the moved king's bucket and computing both SCReLU dot products in one `ZMM` pass.
     - **`18.83%` (`2,480,642` calls, `0.0967` / info node):** parent ply `index - 1` has `valid_flags == 0` (after check, null-move, or TT `raw_eval` hit), so it runs multi-ply `make_valid` (`refresh_from_pieces` `2.73%` + `apply_changes` `0.50%`) followed by `nnue::v3::evaluate` (`1.47%`).
     - **`3.48%` (`458,035` calls, `0.0179` / info node):** accumulator at `index` is already valid; runs `nnue::v3::evaluate` directly.

3. **`forge::Worker::qsearch(Board&, SearchStack*, int, int)` (`src/search.cpp:2255-2395`) — `8.22%` self (`15.170 ms/g`), `25.52%` incl (`47.748 ms/g`):**
   - **Calls:** **`10,326,949` calls** (`0.4027` / reported node | `0.3142` / executed node; `10,326,604` counted `++local_nodes_` = `31.42%` of executed nodes).
   - **What one call does:** Checks stop/draw/max-ply, probes TT via inlined `probe_owned_fast` (`1,749,060` non-PV TT cutoffs = `16.94%` of qs entries), computes stand-pat `static_evaluate_v3` + `corrected_eval` when not in check (`3,088,273` stand-pat beta cutoffs = `29.91%`, storing to TT on miss), then runs `MovePicker` in `Mode::Quiescence` (`generate_captures` or `generate_evasions`), filtering moves with `gives_check`, delta futility, and `Board::see_ge(move, -QsSeeMargin)` (`4,197,666` child moves made = `0.406` moves/qs node), and stores the result via `store_owned_fast`.

---

## 2. Part B: `TranspositionTable::clear` Counts, Per-Clear Times, and Gate Decision (`partB_tt_clear_counts_raw.txt`)

Measured on `01..13 + tidy` compiled with `bld_sp_tidy_1/forge.profdata` (`/tmp/carbon2_job19/bld_pb_cnt/forge`), timing `TranspositionTable::clear()` (`src/search.cpp:458-463`) with `CLOCK_PROCESS_CPUTIME_ID` and `CLOCK_MONOTONIC`:

- **Clears per 60-game `Hash 16` SP run:** **`63` calls** = **`60` `ucinewgame` clears** (`Searcher::clear()`, `src/uci.cpp:576`) + **`3` initial UCI `setoption` setup clears** before game 1 (`MateAlphaGuard=true` at `src/uci.cpp:790`, `NNUEArchFile` at `L715`, and `NNUEArch=true` at `L688`).
- **Time one `clear` takes:**
  - **At `Hash 16` (`262,144` clusters = `16.0 MiB`):**
    - Across the `3 x 60` SP runs (`189` clears, `ee465caeff9c0fcf` on all 3 runs): **`0.7300 ms` CPU mean** (`0.6581 ms` median, `0.7285 ms` wall mean).
    - Dedicated `33`-clear benchmark (each `ucinewgame` preceded by `go softnodes 2000`): **`0.6690 ms` CPU mean**, **`0.5718 ms` CPU median** (`[0.5470, 3.4394] ms`; wall mean `0.6675 ms`, median `0.5705 ms`).
  - **At `Hash 256` (`4,194,304` clusters = `256.0 MiB`, `16.0x` bytes):**
    - Dedicated `33`-clear benchmark (each `ucinewgame` preceded by `go softnodes 2000`): **`14.0983 ms` CPU mean**, **`12.5089 ms` CPU median** (`[4.0017, 32.5634] ms`; wall mean `14.0968 ms`, median `12.5071 ms`) — **`21.07x` mean / `21.87x` median** vs `Hash 16` because `16 MiB` stays largely inside Xeon L3 while `256 MiB` streams to DRAM (`~20.5 GB/s`).
- **Share of the 60 `Hash 16` games' engine CPU (`3` sequential 60-game runs):**
  - Run 1: `46.640 ms / 11,164.22 ms` = **`0.4178%`**
  - Run 2: `46.809 ms / 11,117.05 ms` = **`0.4211%`**
  - Run 3: `44.528 ms / 11,147.16 ms` = **`0.3995%`**
  - **3-run mean share:** **`0.4128%`** across all `63` clears (~**`0.393%`** across the `60` `ucinewgame` clears alone; `0.38%` in `SIGPROF` Table A1).
- **Part B Gate Decision:** **`0.4128% < 0.50%` -> STOPPED WITH THE COUNTS per Part B rule** (no piece written). *(Note: at `Hash 256` with short 60-game self-play at `softnodes 2000`, `60 * 14.1 ms ≈ 846 ms` would be `~7%` of CPU, though self-play uses `Hash 16` and long TC games clear only once per full game.)*

---

## 3. What a Further Speed Job Would Aim At — and Why Nothing Left Under Node-Identical Rules Is Worth `>= 1%`

Every pre-stack hotspot above `2%` has already been either fused/vectorized/inlined in `01..13 + tidy` or empirically tested and bounded below `+0.4%` in Jobs 14–19:
- **Already captured in `01..13 + tidy`:** TT `probe_owned_fast` / `store_owned_fast` (`13`), NNUE v3 `apply_pair_and_evaluate` (`08_G4`) and `apply_one_refresh_one_and_evaluate` (`12`), fused `generate_captures` (`06_G2`) and `generate_quiets` (`07_G3`), AVX-512 linear-scan `pick_best_scored` + king-lines `MovePicker` legality (`09_W1`), table `corrected_eval` (`05_G1`, `10_W2`), `known_gives_check` in `make_move` (`02_S5`), `string_view` UCI (`04_S7`), and `check_node_or_periodic_stop` (`11`).
- **Already bounded `< +0.4%` (`-0.77%` to `+0.17%`) on `01..13 + tidy`:** `Board::has_legal_move` (`2.10%` self, Job 14 `1.0017x`), `Board::upcoming_repetition` AVX-512 (`1.69%` self, Job 16 `0.9970x`), `nnue::v3::apply_changes` unroll (`0.50%` self, Job 17 `0.9980x`), `Board::is_pseudo_legal` (`0.76%` self, Job 17 `0.9923x`), `Board::see_ge` pawn exit (`3.98%` self, Job 18 `0.9943x`), and `TranspositionTable::clear` (`0.4128%` CPU share, Job 19 Part B).

**Why nothing left in node-identical single-thread code is worth `>= 1.0%`:**
1. **Sub-1% Rank 1 — Fuse `make_valid`'s final ply with `output_sum_avx512` (`src/search.cpp:3913-3927`, `src/nnue_v3.cpp:810-875, 1040-1098`):** In Part A (`partA_top3_calls_per_node_raw.txt`), `2,480,642` of `13,172,445` `static_evaluate_v3` calls (`18.83%`) fall into `make_valid` + separate `nnue::v3::evaluate` (`1.47%` self = `2.720 ms/g`) when `ply - 1` skipped eval (in check, null-move, or TT `raw_eval` hit). Fusing the final accumulator step of `make_valid` with the SCReLU `w2` dot product avoids re-loading `2 x 768 x 2 = 3 KiB` from L1 (`48` `ZMM` loads x `2.48M` calls), which is bounded at **`~0.25%–0.45%`** (`< 1%`) because those `3 KiB` lines sit hot in L1D.
2. **Sub-1% Rank 2 — Fuse evasion scoring into `MovePicker::generate_evasions` (`src/search.cpp:1350-1385`, `src/board.cpp:695-790`):** `generate_evasions` (`1.96%` self) + `Board::generate_legal_evasions` (`1.86%` self) total `3.82%` self (`7.048 ms/g`). Scoring evasions directly on emission (eliminating the intermediate `MoveList` round-trip, as `06_G2` did for captures) can only remove the `MoveList` write/read loop (~`10%–15%` of `3.82%` = **`~0.4%–0.6%`**, `< 1%`).
3. **Where a future `>= 1%` speedup would actually come from (outside node-identical / current-net rules, for a later R-cycle):**
   - **L1->L2 `int8` VNNI (`vpdpbusd`) output layer in `nnue_v3.cpp:470-474, 1019-1028`:** Currently `hidden=768` SCReLU computes `int16` `vpmullw + vpmaddwd` (`2` instructions + `3 KiB` `int16` `w2` load per eval across `13.17M` evals = `~18%` of total engine CPU inside `static_evaluate_v3` + `apply_one_refresh_one_and_evaluate` + `evaluate`). Halving `w2` bandwidth to `1.5 KiB` (`int8`) with `vpdpbusd` targets **`~3%–5%` whole-engine CPU**, at the cost of `QA`/quantization format adjustments in a future net/eval cycle.
   - **2D King-Bucket + King-Side Finny Cache (`nnue_v3.cpp:1040-1064`):** `refresh_from_pieces` (`2.73%`) + the refresh half of `apply_one_refresh_one_and_evaluate` (`~3.5%` of `5.20%`) spend **`~6.2%`** diffing `12` piece bitboards and applying `subs[]`/`adds[]` columns on bucket transitions (`2.39M` + fallback refreshes); doubling `RefreshCache` entries partitioned by pawn-half/castling quadrant reduces average `n_sub + n_add` columns per refresh (`node-identical`, realistic ceiling **`~0.6%–0.9%`**, still right under `1%`).

---

## 4. Timestamps, Runtime Model, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job19/stamps.txt`:**
  `Wed Nov 18 04:01:12 PM UTC 2026 | job 19 received (FABLE_TO_carbon2_19.md); starting Step 0 & Part A`
- **Last line of `forge-combo29/carbon2/job19/stamps.txt`:**
  `Wed Nov 18 04:31:23 PM UTC 2026 | Job 19 all runs finished; writing REPORT_carbon2_job19.md within budget`
- **Runtime Model Name & Version:** `Gemini 4 Carbon`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job19` immediately before report commit:**

```text
 M forge-combo29/carbon2/job19/stamps.txt
?? forge-combo29/carbon2/job19/REPORT_carbon2_job19.md
forge-combo29/carbon2/job19:
partA_r15d_vs_stack_time_profile_raw.txt
partA_top3_calls_per_node_raw.txt
partB_tt_clear_counts_raw.txt
REPORT_carbon2_job19.md
stamps.txt
step0_job19_raw.txt
```
