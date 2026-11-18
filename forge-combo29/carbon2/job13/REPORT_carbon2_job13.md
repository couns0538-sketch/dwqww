# Forge (`carbon2` — Job 13 Report): 10-Piece Zero-Fuzz Review Stack of `curated_sp_bundle` (`01_S4 .. 10_W2`) and Caller-Inclusive `ms/game` Time Profile of SP-Profiled `curated`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job13/`, zero binaries, net files, or `.profraw`/`.profdata` files committed).
- **Job 12 Completed First:** Upon resuming, `REPORT_carbon2_job12.md` (`commit d5cdc5020`) was finalized from the completed `168`-run raw file `job12/pgo1_loo6_12x60_hash16_raw.txt` (zero new runs needed) and pushed before starting Job 13.

---

## 0. Step 0, Toolchain, `-march`, Merged Profile Files, and SP Profile Run Counts

- **Compiler, linker & `-march` (`forge-combo29/carbon2/job13/build_pgo_raw.txt` lines 4–8, 136–145):**
  - `clang++-18` (`Ubuntu clang version 18.1.3 (1ubuntu1)`) with GCC 13.3's `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `-flto=thin -fuse-ld=lld-18` (`Ubuntu LLD 18.1.3`), `llvm-profdata-18`.
  - **`-march=sapphirerapids`** (Clang 18's native `AVX-512` + `AVX512-VNNI` + `BMI2` `PEXT` target on this Intel Sapphire Rapids Xeon; Clang 18 predates `-march=znver5`).
  - All six speed switches of File 10 fact `(c)` explicitly present on every compile line (`-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1`).
- **Profile files merged & SP profile run counts (`build_pgo_raw.txt` lines 123–133):**
  - **`2` `.profraw` files merged per SP-profile build**:
    1. Process 1 (`bench 11 / 13 / 16` with `net768.fnn3` and `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`): `1,261,644` / `6,312,262` / `74,843,992` nodes (`1` `.profraw`).
    2. Process 2 (SP profile run on the last `60` unique roots of `positions_250.txt`, `disjoint_from_timing_60 = True`): **`games = 60`, `searches = 5,531`, `nodes = 18,059,934`, `trace = 1646ce4566de2f40`** (`1` `.profraw`).
- **Step 0 across each build (`forge-combo29/carbon2/job13/step0_job13_raw.txt`):**
  - **SP-profiled `pc_r15` (`2` `.profraw` merged):** no-settings `bench 11/13/16 = 312866 / 862329 / 3024920`, `go perft 5 = 4865609`; `PC20` no-net `278024 / 587276`; `net512` only `965454 / 4151906`; `PC20 + net512` `625258 / 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`); `evals = nnue 968 / 1176 / 31` (**ALL EXACT**).
  - **SP-profiled `r15d` (`2` `.profraw` merged) and Job 13 SP-profiled `curated` (`2` `.profraw` merged):** `go perft 5 = 4865609`; `PC20 + net512` `bench 11/13/16 = 625258 / 3652372 / 23891329`, `evals = 968 / 1176 / 31`; `PC20 + net768` `bench 11/13/16 = 882074 / 4275906 / 32374943` (`checksum 30ab43b4ba5db5f3`) (**ALL EXACT**).

---

## 1. Part 1: 10-Piece Zero-Fuzz Review Stack (`forge-combo29/carbon2/job13/stack/`)

- **Per-piece documentation:** `forge-combo29/carbon2/job13/stack/README.txt` holds one block per piece (`01_S4` through `10_W2`) giving `+added / -removed` lines, touched functions/structs, the exact invariant relied on, the named differential oracles and identity suites that catch a fault in it, and the exact comparison against earlier job patch files (`job5/bundle.patch.txt` [`r15e`], `job5/s4..s7`, `job7/o0`, `job6/g1..g4`, `job8/w1..w2`).

| Order | Piece | Stack File (`forge-combo29/carbon2/job13/stack/...`) | Patch Lines (`+add / -rem`) | Cumulative Identity After Piece (`forge-combo29/carbon2/job13/stack_identity_raw.txt`) |
| :---: | :--- | :--- | ---: | :--- |
| 1 | `S4` | `01_S4.patch.txt` | `282` (`+85 / -38`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 2 | `S5` | `02_S5.patch.txt` | `171` (`+39 / -25`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 3 | `S5_assert` | `03_S5_assert.patch.txt` | `95` (`+35 / -0`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 4 | `S7` | `04_S7.patch.txt` | `459` (`+171 / -85`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 5 | `G1` | `05_G1.patch.txt` | `100` (`+28 / -5`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 6 | `G2` | `06_G2.patch.txt` | `56` (`+33 / -3`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 7 | `G3` | `07_G3.patch.txt` | `165` (`+47 / -19`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 8 | `G4` | `08_G4.patch.txt` | `217` (`+64 / -42`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 9 | `W1` | `09_W1.patch.txt` | `579` (`+375 / -38`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |
| 10 | `W2` | `10_W2.patch.txt` | `219` (`+41 / -53`) | `net512` `625258 / 3652372 / 23891329` **EXACT**; `net768` `882074 / 4275906 / 32374943` **EXACT**; `250/250` depth-9 **EXACT** |

### Verbatim Zero-Fuzz Replay & Byte-for-Byte `diff -r` Check (`forge-combo29/carbon2/job13/stack_byte_for_byte_diff_raw.txt`)

```text
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/01_S4.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/02_S5.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/03_S5_assert.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/04_S7.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/05_G1.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/06_G2.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/07_G3.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/08_G4.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/09_W1.patch.txt
$ patch -d stack_replayed -p1 -F0 < forge-combo29/carbon2/job13/stack/10_W2.patch.txt
$ diff -r stack_replayed/src curated_direct/src && diff -r stack_replayed/include curated_direct/include
```
*(Empty output, exit code `0`.)*

---

## 2. Part 2: Caller-Inclusive & `ms/game` Time Profile of the SP-Profiled `curated` Build (`forge-combo29/carbon2/job13/curated_sp_time_profile_raw.txt`)

Because Job 12 took the `>= 1%` leave-one-out branch (`PGO1` `+2.38%`) and made no time profile, we followed File 13 Part 2's second branch: we profiled the SP-profiled `curated` build at `Hash 16` (`PC20 + net768.fnn3`, `go softnodes 2000`, `5` passes x `60` games = `300` games = `38,350` searches, `ee465caeff9c0fcf` on every pass) using `ITIMER_PROF` (`SIGPROF` CPU-time sampling, `16,016` samples on the unmodified binary at `203.166 ms/game` and `15,630` full `RBP` call-stack backtraces at `198.375 ms/game` using the identical `forge.profdata`, recursion-deduplicated so every function is credited **together with everything it calls** and annotated with its callers; note that Valgrind 3.22's LibVEX rejects Sapphire Rapids EVEX AVX-512 `0x62` instructions at startup):

### 2.1 Inlining-Invariant Subsystem Breakdown on Unmodified SP-Profiled `curated` (`203.166 ms/game`, `16,016` CPU-time samples)

| Subsystem (Caller + Outlined Callees Grouped, `curated_sp_time_profile_raw.txt` lines 12–19) | Samples | Share of Engine CPU (`%`) | Engine CPU (`ms/game`) |
| :--- | ---: | ---: | ---: |
| **Search Control, Pruning & History Updates** (`Worker::search` + `qsearch` + `should_stop` + corr/history) | `7,172` | `44.78%` | `90.978` |
| **NNUE v3 Evaluation** (`static_evaluate_v3` + `refresh_from_pieces` + `apply_pair` + `evaluate` + `apply_changes`) | `3,582` | `22.37%` | `45.438` |
| **Move Generation, Ordering & Threat Maps** (`MovePicker` + `generate_quiets/captures/evasions` + `introsort`) | `1,849` | `11.54%` | `23.455` |
| **Transposition Table** (`probe_owned` `12.850 ms` + `clear` `1.522 ms` + inlined `store_owned`) | `1,133` | `7.07%` | `14.372` |
| **Board State, Legality & Repetition** (`has_legal_move` `4.237 ms` + `upcoming_repetition` `2.956 ms` + `is_legal_complete` `1.522 ms` + `is_pseudo_legal` `1.497 ms` + `make/unmake`) | `977` | `6.10%` | `12.393` |
| **C/C++ Runtime & Syscalls** (`libc` / `libstdc++` / `stdio` / `futex` / `memset`) | `677` | `4.23%` | `8.588` |
| **Static Exchange Evaluation** (`Board::see_ge`) | `616` | `3.85%` | `7.814` |
| **UCI Protocol & I/O** (`uci_loop` + `apply_position_sv`, in-binary self) | `10` | `0.06%` | `0.127` |

### 2.2 Caller-Inclusive Function Table (`198.375 ms/game`, `15,630` RBP Call-Stack Samples, `curated_sp_time_profile_raw.txt` lines 55–76)

| Rank | Function (SP-Profiled `curated` Build) | Inclusive `%` (`ms/game`) | Self `%` (`ms/game`) | Primary Callers (Sample Counts) |
| :---: | :--- | ---: | ---: | :--- |
| 1 | `Worker::search(Board&, SearchStack*, ...)` | **`95.09%` (`188.628 ms`)** | `37.16%` (`73.715 ms`) | `Worker::search` root/rec (`14,849`), `search_child` (`83`) |
| 2 | `Worker::qsearch(Board&, SearchStack*, int, int)` | **`25.86%` (`51.301 ms`)** | `7.01%` (`13.898 ms`) | `Worker::search` (`4,042`) |
| 3 | `Worker::static_evaluate_v3(const Board&, SearchStack*)` | **`23.66%` (`46.935 ms`)** | `13.84%` (`27.453 ms`) | `Worker::search` (`1,851`), `Worker::qsearch` (`1,839`) |
| 4 | `nnue::v3::refresh_from_pieces(...)` | **`5.87%` (`11.639 ms`)** | `5.87%` (`11.639 ms`) | `Worker::static_evaluate_v3` (`913`) |
| 5 | `MovePicker::generate_evasions()` *(incl. `generate_legal_evasions`)* | **`4.06%` (`8.047 ms`)** | `1.89%` (`3.744 ms`) | `Worker::search` (`322`), `Worker::qsearch` (`312`) |
| 6 | `TranspositionTable::probe_owned(uint64_t)` | **`3.81%` (`7.552 ms`)** *(unmod: `12.850 ms`)* | `3.81%` (`7.552 ms`) | `Worker::search` (`381`), `Worker::qsearch` (`214`) |
| 7 | `Board::see_ge(const Move&, int)` | **`3.74%` (`7.412 ms`)** *(unmod: `7.814 ms`)* | `3.74%` (`7.412 ms`) | `Worker::search` (`517`), `Worker::qsearch` (`67`) |
| 8 | `MovePicker::generate_quiets()` *(incl. `emit_quiets_from` lambda)* | **`3.50%` (`6.942 ms`)** | `1.27%` (`2.513 ms`) | `Worker::search` (`546`) |
| 9 | `uci_loop(std::istream&)` *(main UCI thread incl. `libc`/pipe/`clear`)* | **`3.21%` (`6.371 ms`)** | `0.01%` (`0.013 ms`) | `_start` / `libc` (`502`) |
| 10 | `MovePicker::generate_captures()` | **`2.92%` (`5.800 ms`)** | `2.91%` (`5.775 ms`) | `Worker::qsearch` (`230`), `Worker::search` (`227`) |
| 11 | `Board::has_legal_move()` | **`2.48%` (`4.924 ms`)** *(unmod: `4.237 ms`)* | `2.47%` (`4.899 ms`) | `Worker::search` (`306`), `Worker::qsearch` (`82`) |
| 12 | `nnue::v3::evaluate(...)` *(non-paired fallback)* | **`2.44%` (`4.836 ms`)** | `2.44%` (`4.836 ms`) | `Worker::static_evaluate_v3` (`340`), `Worker::qsearch` (`35`) |
| 13 | `MovePicker::generate_quiets()::emit_quiets_from` lambda | **`2.18%` (`4.315 ms`)** | `2.18%` (`4.315 ms`) | `MovePicker::generate_quiets` (`333`) |
| 14 | `Board::generate_legal_evasions(MoveList&)` | **`1.86%` (`3.681 ms`)** | `1.86%` (`3.681 ms`) | `MovePicker::generate_evasions` (`288`) |
| 15 | `Board::upcoming_repetition(size_t)` | **`1.75%` (`3.465 ms`)** | `1.75%` (`3.465 ms`) | `Worker::search` (`261`) |
| 16 | `std::__introsort_loop<MovePicker::Scored*>` | **`1.36%` (`2.703 ms`)** | `1.36%` (`2.703 ms`) | `Worker::search` (`206`), `Worker::qsearch` (`7`) |
| 17 | `nnue::v3::apply_changes(...)` | **`1.12%` (`2.221 ms`)** | `1.12%` (`2.221 ms`) | `Worker::static_evaluate_v3` (`173`) |

---

## 3. Step Table

Per File 13 Part 2 (*"If job 12 made no time profile: make one of the SP-profiled curated build ... and stop after its table"*), no new engine code step was executed in Job 13 after completing the 10-piece stack and the SP-profiled `curated` time profile:

| Step | Patch File | Lines | Identity | Timing | Prediction | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **Part 1 Stack (`01_S4 .. 10_W2`)** | `forge-combo29/carbon2/job13/stack/01_S4.patch.txt` .. `10_W2.patch.txt` | `2,343` stacked (`1,857` flat in `job11/curated_sp_bundle.patch.txt`) | All `10` pieces `patch -p1 -F0` clean; `diff -r` **0 bytes** vs `curated_sp_bundle`; `net512` & `net768` `bench 11/13/16` + `250/250` depth-9 **EXACT** after every piece (`stack_identity_raw.txt`) | Timed in Job 11 Timing (3) (`job11/timing3_sp_r15d_vs_curated_12x60_hash16_raw.txt`: CPU `1.0366x` `+3.66%` `12/12`, wall `1.0336x` `+3.36%` `12/12`) | N/A (review split; Job 11 `5d5b42642` MET) | Caught per piece in `stack/README.txt` (`job11/curated_oracles_and_fault_raw.txt`) |
| **Part 2 Profile** | `forge-combo29/carbon2/job13/curated_sp_time_profile_raw.txt` | N/A (stopped after profile table per File 13) | `600` profiled games (`10 x 60`) all `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes/pass) | Unmodified `203.166 ms/game`; call-stack `198.375 ms/game` (`31,646` total CPU-time samples) | N/A | N/A |

---

## 4. What We Would Do Next With Another 90 Minutes (Ranked From `curated_sp_time_profile_raw.txt` & `job12/pgo1_loo6_12x60_hash16_raw.txt`)

1. **Eliminate pre-TT `Board::has_legal_move()` (`2.48%` inclusive = `4.924 ms/game` in `curated_sp_time_profile_raw.txt` line 70: `306` samples from `Worker::search`, `82` from `Worker::qsearch`):** Currently `Worker::search` and `Worker::qsearch` call `board.has_legal_move()` at non-check nodes *before* probing the TT or running `MovePicker` solely to return `0` immediately on stalemate, even though stalemate occurs on `< 0.01%` of non-check nodes and `Worker::search` already detects `move_count == 0 && !in_check -> return 0` at the end of the move loop! Deferring stalemate detection until either `move_count == 0` (in `search`) or when a static/TT cutoff is about to return on a position with no verified legal move yet attacks **`2.09%–2.48%` (`4.2–4.9 ms/game`)** bit-identically (provided node increment / TT cutoff semantics on terminal stalemates are preserved identically!).
2. **Add `Worker::check_node_or_periodic_stop()` onto `curated_sp_bundle` (`+1.14%` marginal CPU [`1.0114x`, `9/12` rounds faster] already measured in `job12/pgo1_loo6_12x60_hash16_raw.txt` line 254):** Inside `Worker::search` + `Worker::qsearch` self (`73.715 + 13.898 = 87.613 ms/game` in `curated_sp_time_profile_raw.txt` lines 59–60), `curated_sp_bundle` does not yet have `check_node_or_periodic_stop()` (which Job 11 dropped together with `P1`'s `TT` part, and Job 12 then isolated at `+1.14%` on SP-profile while `TT` was `0.9996x`).
3. **Single-king-move `nnue::v3::refresh_from_pieces` incremental cache update (`5.87%` inclusive = `11.639 ms/game` in `curated_sp_time_profile_raw.txt` line 62):** Check how many `refresh_from_pieces` calls in `static_evaluate_v3` miss or rebuild multiple piece bitboards on king bucket transitions, or fuse `apply_changes` (`1.12%` = `2.221 ms/game`, line 76) on single-perspective updates without altering `MovePicker::next` inlining.

---

## 5. Times, Runtime Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job13/stamps.txt`:**
  `Wed Nov 18 06:51:29 AM UTC 2026 | job 13 received (FABLE_TO_carbon2_13.md); starting Step 0, SP-profiled curated build, and valgrind check`
- **Last line of `forge-combo29/carbon2/job13/stamps.txt`:**
  `Wed Nov 18 07:36:10 AM UTC 2026 | Writing REPORT_carbon2_job13.md before minute 80 and pushing branch`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon`

### Verbatim Pre-Commit Check (`git status --short && ls -R forge-combo29/carbon2/job13`)

```text
?? forge-combo29/carbon2/job13/REPORT_carbon2_job13.md
forge-combo29/carbon2/job13:
build_pgo_raw.txt
curated_sp_time_profile_raw.txt
REPORT_carbon2_job13.md
stack
stack_byte_for_byte_diff_raw.txt
stack_identity_raw.txt
stamps.txt
step0_job13_raw.txt

forge-combo29/carbon2/job13/stack:
01_S4.patch.txt
02_S5.patch.txt
03_S5_assert.patch.txt
04_S7.patch.txt
05_G1.patch.txt
06_G2.patch.txt
07_G3.patch.txt
08_G4.patch.txt
09_W1.patch.txt
10_W2.patch.txt
README.txt
```
