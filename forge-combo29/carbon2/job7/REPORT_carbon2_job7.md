# Forge (`carbon2` — Job 7 Report): Outside-Search CPU Counts at `Hash 32`, UCI `InfoOnce` (`O2`), and `bundle3.patch.txt`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job7/`).
- **Job 4 Base Tree (target of `bundle3.patch.txt`):** `6b98f217` + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` (`forge/r15c`) + `forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt` (`E1`).
- **Cloud Machine & Compiler:** `Intel(R) Xeon(R) CPU @ 2.60GHz` (x86_64, AVX-512, 320 MiB L3), `g++ 13.3.0`, `-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`.
- **Job 5 Note Acknowledged:** For Job 5's `S6`, the `bench 13` paired median was `0.9948x` wall / `0.9962x` CPU, which was **killed** by its own pre-committed prediction range (`1.006x..1.025x`, killed `<= 1.005x`); per File 7's correction, an A/A spread label does not turn a loss/tie into a gain, and every table below prints the **per-round A/A `[min, max]` range** right beside the median A/A ratio.

---

## 0. Step 0 Verification and Task 0 Base Taken

- **Step 0 (same machine and base build as Jobs 1–6, re-run today in `forge-combo29/carbon2/job7/step0_job7_raw.txt`):** All bench and perft pins met bit-identically with zero error/warning lines:
  - No settings, no net: `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
  - `PC20`, no net: `bench 11 -> 278024`, `bench 13 -> 587276`
  - `net512.fnn3` only: `bench 11 -> 965454`, `bench 13 -> 4151906`
  - `PC20`, then `net512.fnn3`: `bench 11 -> 625258`, `bench 13 -> 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)
- **Task 0 Base Taken:** Job 6's **`bundle2.patch.txt`** (`S1..S7 + G1..G4`) passed 100% of its identity proof in Job 6 (`7f49a59e6`), so we took **`bundle2.patch.txt` as the Job 7 base**, immediately applying the cleanup diff `forge-combo29/carbon2/job7/o0_drop_s7p3_and_s5_assert.patch.txt` (`225` lines stacked on `job6/bundle2.patch.txt`) before Task 1 counting so that:
  1. **`S7` Part 3 (`threat_history_dirty_` / `v1_eval_dirty_`) is completely removed** (`Worker::clear()` unconditionally clears every table and `SearchStack` entry, so Task 1 measures the real unconditional `Worker::clear()`).
  2. **`S5`'s debug-only key recomputation check is restored** under `#ifndef NDEBUG` (`assert(key_ == dbg_key)` inside `Board::make_move`, verified in a `-UNDEBUG` build in `bundle3_debug_and_fault_raw.txt` where `bench 11 == 882074` passes and `child_key ^ 1ULL` aborts immediately with `Assertion 'key_ == dbg_key' failed`).

---

## 1. Task 1 Outside-Search Engine CPU Counts at `Hash 32` (`forge-combo29/carbon2/job7/outside_search_counts.txt`)

Measured in a separate instrumented copy (not the timed builds) before any new step (`commit f460b5067`), using `clock_gettime(CLOCK_THREAD_CPUTIME_ID)` per handler and `clock_gettime(CLOCK_PROCESS_CPUTIME_ID)` over the 60-game FEN-root stream at **`Hash 32`** (`PC20`, `Threads 1`, `MultiPV 1`, `net768.fnn3`, `go softnodes 2000`; `7,645` searches = `127.42` searches/game, `25,564,637` nodes, `trace_hash32 = afc8237d71719c40`):

- **`info depth ...` lines and bytes per search:** **`9.2234` `info` lines/search** (`70,513` lines across `7,645` searches; `8.2234` intermediate lines/search = `89.16%` discarded unused by the PC client) and **`914.15` bytes/search** (`6,988,700` bytes across `7,645` searches, `99.11` B/line), plus `1.000` `info string softnodes nodes ...` line/search (`~34` B/search).
- **Total engine CPU per game (`Hash 32`):** **`220.649 ms/game`** (`13,238.96 ms` over 60 games in Run 2; `219.943 ms/game` = `13,196.55 ms` in Run 1).

| Part | Handler / Component (`Hash 32`, 60 games, `7,645` searches) | Engine CPU / Game (`ms`) | Share of Game Engine CPU (`%`) | Task 2 `>= 1.0%` Gate Verdict |
| :--- | :--- | ---: | ---: | :--- |
| **(a1)** | `ucinewgame`: Transposition table fill (`shared_.tt.clear()`, `32 MB` x 60) | **`1.477 ms`** *(Run 1: `1.190 ms`)* | **`0.669%`** *(Run 1: `0.541%`)* | **Below `1.0%` -> `O1` skipped** |
| **(a2)** | `ucinewgame`: `Worker::clear()` (unconditional clear of all histories, corrections, `SearchStack`) | **`0.341 ms`** *(Run 1: `0.310 ms`)* | **`0.154%`** *(Run 1: `0.141%`)* | **Below `1.0%`** |
| **(a3)** | `ucinewgame`: `Board::set_fen(StandardStartFen)` + `PositionCache` reset | **`0.014 ms`** *(Run 1: `0.013 ms`)* | **`0.006%`** *(Run 1: `0.006%`)* | **Below `1.0%`** |
| **(a) Subtotal** | **All `ucinewgame` handler work (`a1 + a2 + a3`)** | **`1.831 ms`** *(Run 1: `1.513 ms`)* | **`0.830%`** *(Run 1: `0.688%`)* | **Below `1.0%`** |
| **(b)** | **`position` handler (`apply_position_sv`, `7,645` calls; `S7` Part 1 active)** | **`0.359 ms`** *(Run 1: `0.340 ms`)* | **`0.162%`** *(Run 1: `0.155%`)* | **Below `1.0%`** |
| **(c1)** | `info` output: building each line (`buf` formatting + `hashfull()`, `70,513` lines) | **`0.437 ms`** *(Run 1: `0.466 ms`)* | **`0.198%`** *(Run 1: `0.212%`)* | Part of `(c)` |
| **(c2)** | `info` output: writing + flushing (`std::cout.write` + `std::cout.flush()`, `70,513` lines) | **`1.789 ms`** *(Run 1: `1.780 ms`)* | **`0.811%`** *(Run 1: `0.809%`)* | Part of `(c)` |
| **(c) Subtotal** | **All `info` output (`c1 + c2`, `9.22` lines & `914.15` B / search)** | **`2.226 ms`** *(Run 1: `2.246 ms`)* | **`1.009%`** *(Run 1: **`1.021%`**)* | **`>= 1.0%` MET -> Execute `O2` (`InfoOnce`)** |
| **(d)** | **Everything else** (`go`/`bestmove`/condvar dispatch `0.770 ms` [`0.349%`] + `isready` `0.006 ms` [`0.003%`] + tree search `215.458 ms` [`97.647%`]) | **`216.234 ms`** *(Run 1: `215.843 ms`)* | **`97.999%`** *(Run 1: `98.136%`)* | Sub-handlers outside search `< 1.0%` -> `O3` skipped |

---

## 2. Task 2 Step Summary (`O2`: UCI Option `InfoOnce`)

Per Task 2 (*"Steps, largest first, each only if its count in task 1 is 1 % of a game's engine CPU or more"*), **`O2` (`InfoOnce`)** was the only outside-search item at `>= 1.0%` (`1.009%`–`1.021%`). `O1` (`0.541%`–`0.669%` TT fill on this single-worker 320 MiB-L3 VM) and `O3` (`0.162%` `position`, `0.349%` `go`/`bestmove`) were below `1.0%` and skipped.

| Step | Patch File (`forge-combo29/carbon2/job7/...`) | Lines | Identity & Stream Proofs | Self-Play Timing at `Hash 32` (`A1 B1 B2 A2` x 8 rounds x 60 games, `B` with `InfoOnce true`: paired ratios, `paired median`, `pooled-median`, median A/A + per-round A/A range) | Prediction (Commit, Met or Killed) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`O2`** | `o2_uci_option_info_once.patch.txt` (`search.hpp`, `search.cpp`, `uci.cpp`: `tune::InfoOnce` `type check default false`, `SavedInfoLine` + `InfoOnceFlushGuard` in `Worker::search`) | 177 | All `PC20` + `net768`/`net512` `bench 11/13/16`, `250` depth-9 rows, `1000` evals, 6-game traces **EXACT** (`o2_identity_proof_raw.txt`); **60-game `Hash 32` stream (`7,723` searches)**: `InfoOnce` absent `90,823 / 90,823` lines **EXACT**, `InfoOnce true` **`7,723 / 7,723` searches** print strictly 1 `info` line (`7,645` lines in timed set) with `bestmove`, `nodes`, and masked line **BYTE-FOR-BYTE EQUAL** to the PC client's rule (`o2_stream_oracle_and_fault_raw.txt`); stack unchanged (`2240 / 4560 / 2704 B`) | **Engine CPU (`getrusage` ns):** `[1.0030, 0.9893, 1.0040, 1.0366, 1.0043, 1.0306, 0.9828, 0.9875]` (`5/8`), `paired median 1.0035x` (`[0.9875x, 1.0306x]`), `pooled-median 1.0028x`; A/A: `med(A2)/med(A1)=0.9914` (per-round `[0.9597, 1.0435]`), `med(B2)/med(B1)=0.9904` (per-round `[0.9782, 1.0288]`).<br>**Idle-VM Wall:** `[0.9765, 0.9595, 0.9760, 0.9885, 0.9689, 0.9853, 0.9470, 0.9472]` (`0/8`), `paired median 0.9724x`, `pooled-median 0.9679x`; A/A per-round `[0.9538, 1.0520]` / `[0.9758, 1.0182]` (`o2_selfplay_8x60_hash32_raw.txt`) | `b50720750`: **KILLED** (`1.0035x <= 1.005x` CPU and `0.9724x <= 1.010x` wall on 1-worker idle VM; see scheduler note below) | **CAUGHT** at search 46 (`nodes 1725` vs post-abort `nodes 8000`, `o2_stream_oracle_and_fault_raw.txt`) |

- **Why `wall_ns - rusage_cpu_ns` grew by `~520 ms` (`~68 us/search`) on the 1-worker idle VM while engine `rusage_cpu_ns` improved (`+0.35%`):** In `o2_selfplay_8x60_hash32_raw.txt`, `A` emits `info depth 1` ~20 us into every search, waking the sleeping Python driver vCPU out of `pipe_read` block *while* the engine is still computing depths 2..8 (`wall - cpu = 1,434 ms`). With `InfoOnce true`, stdout stays silent for the full `~1.8 ms` search so the idle client vCPU sleeps until `info + bestmove` is flushed (`wall - cpu = 1,797 ms`), adding cross-core wakeup latency to 1-worker wall time without spending CPU cycles.

---

## 3. Bundle 3 (`forge-combo29/carbon2/job7/bundle3.patch.txt`) vs Job 5 `bundle1` at `Hash 32`

- **Patch file:** `forge-combo29/carbon2/job7/bundle3.patch.txt` (`1,976` lines), ONE unified diff against the **Job 4 base** (`6b98f217 + pc_r15.patch + a_speed_pc20_v3.patch.txt + e1_legal_check_evasions.patch.txt`), applying with `patch -p1 --fuzz=0` and producing a byte-identical tree (`diff -qr` empty) to `Job 4 base + job6/bundle2.patch.txt + o0_drop_s7p3_and_s5_assert.patch.txt + o2_uci_option_info_once.patch.txt`.
- **Included steps (12 steps across Jobs 4–7):**
  - `S1` (cache-tiled refresh + single-add/sub AVX-512 forward fusion)
  - `S2` (AVX-512 `VPERMT2D` quiet history scoring + cached picker quiet history + unboxed `is_pseudo_legal`)
  - `S3` (correction-table L1 prefetches + 4-way unrolled `non_pawn_key`)
  - `S4` (slim `MovePicker` `-2,552 B` struct + `qsearch` `odd_idx16` load guard)
  - `S5` (`Board::make_move` precomputed `early_key` reuse **WITH restored `#ifndef NDEBUG` `assert(key_ == dbg_key)` recomputation check** + conditional 72B `KingLines` copy on `Undo`)
  - `S6` (`Board::see_ge` unpinned enemy-pawn recapture fast-exit)
  - `S7` **Parts 1 & 2 ONLY** (zero-allocation `std::string_view` UCI `position`/`go` parsing + persistent `SearchTask` `Board` capacity handoff; **`S7` Part 3 dirty-tracked `Worker::clear()` REMOVED**)
  - `G1` (cached `corr_mat_idx` `material_key` index on `SearchStack` + inline `has_dead_material_candidates` guard)
  - `G2` (`Board::see_ge` no-recapture fast-exits + unified `FORGE_SDK_SEE_HOIST` king-line cache)
  - `G3` (`known_gives_check` reuse in `Board::make_move` with `assert(compute_checkers() == 0)` + `MovePicker::init_check_squares` `ensure_king_lines` deduplication + ray-free pawn stalemate fast-exit + branchless king-evasion taboo pre-mask)
  - `G4` (per-search `v3_active_net_` / `nnue_active_` snapshot + hoisted `nnue::v3::prepare` `6,464 -> 112 B` + direct `board.king_square` & parent `KingKey` reuse on non-king moves in `Worker::static_evaluate_v3`)
  - `O2` (UCI option `InfoOnce`, `type check default false`; `B` runs below execute with `InfoOnce true`)
- **Pre-committed prediction:** `forge-combo29/carbon2/job7/prediction_bundle3.txt` (standalone commit **`b7cf5398d`**): predicted `+1.2%` to `+3.5%` (`1.012x` to `1.035x`) `Hash 32` engine `getrusage` CPU gain over Job 5 `bundle1` with `>= 9/12` paired rounds faster, `0.975x` to `1.005x` 1-worker idle-VM wall, and `+1.0%` to `+3.5%` on `bench 13`; killed if engine CPU paired median `<= 1.008x` OR `< 9/12` paired rounds faster.

### 3a. Bundle 3 Identity Proof, Restored `S5` Debug-Assert Check, Stack Sizes, and Planted Fault
Raw files: `forge-combo29/carbon2/job7/bundle3_proof_and_bench13_raw.txt` and `forge-combo29/carbon2/job7/bundle3_debug_and_fault_raw.txt`.
- **`PC20 + net512.fnn3` (`fdff70de72e4ca82`):** `bench 11 = 625258`, `bench 13 = 3652372`, `bench 16 = 23891329` (**EXACT**), `1,000/1,000` `eval` rows **EXACT**.
- **`PC20 + net768.fnn3` (`30ab43b4ba5db5f3`):** `bench 11 = 882074`, `bench 13 = 4275906`, `bench 16 = 32374943` (**EXACT**), `250/250` depth-9 `(bestmove, nodes)` rows **EXACT**, `1,000/1,000` `eval` rows **EXACT**.
- **6-game self-play traces (`net768`, `Hash 16`):** `startpos = 4560d7c3afdeba2e` (**EXACT**), `fen = 9ed22c1193ab96de` (**EXACT**).
- **`-UNDEBUG` S5 key recomputation assert (`bundle3_debug_and_fault_raw.txt`):** Clean `-UNDEBUG` build passes `bench 11 == 882074`; corrupted `child_key ^ 1ULL` triggers `Assertion 'key_ == dbg_key' failed`.
- **Planted fault (`o2_planted_fault.patch.txt`):** **CAUGHT** at search 46 (`bundle3_debug_and_fault_raw.txt`).
- **Stack Frame Sizes (`Job 5 bundle1 -> Bundle 3` / vs `Job 4 base`):**
  - `sizeof(MovePicker)`: `2,240 -> 2,240 B` (`-2,552 B` vs Job 4 base `4,792 B`)
  - `Worker::search`: `4,496 -> 4,560 B` (`-2,544 B/ply` vs Job 4 base `7,104 B`)
  - `Worker::qsearch`: `2,704 -> 2,704 B` (`-2,544 B/ply` vs Job 4 base `5,248 B`)
  - `nnue::v3::prepare`: `6,464 -> 112 B` (`-6,352 B`)

### 3b. Bundle 3 (`InfoOnce true`) vs Job 5 `bundle1` Self-Play Timing at `Hash 32` (`A1 B1 B2 A2` x 12 Rounds x 60 Games = 48 Runs)
- **Driver:** `forge-combo29/carbon2/job7/run_selfplay_hash32_abba.py`
- **Raw log (every run's line + `info_lines` + `NNUE v3 active:`):** `forge-combo29/carbon2/job7/bundle3_selfplay_12x60_hash32_raw.txt`
- **Single bit-exact trace across all 48 runs (`366,960` searches, `1,227,102,576` nodes at `Hash 32`):**
  - Every one of the 48 runs produced **`searches = 7,645`**, **`nodes = 25,564,637`**, and **`fnv1a64 = afc8237d71719c40`** (`info_lines = 70,513` on all 24 `A` runs vs **`info_lines = 7,645`** [`1.000` line/search] on all 24 `B` runs).

| Metric (`A = Job 5 bundle1`, `B = Bundle 3 + InfoOnce true`, `Hash 32`, 12x60) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..12`) | Rounds Faster | `median_of_paired_round_ratios` + 95% CI | `ratio_of_pooled_medians` + 95% CI | A/A Control (Medians + Per-Round `[min, max]` Range) |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **Engine CPU (`getrusage` ns, searches/s)** | `A1=534.07`, `A2=519.82` (`A=528.81`) \| `B1=543.73`, `B2=541.26` (`B=541.49`) | `[1.0226, 0.9881, 1.0132, 1.0098, 1.0590, 1.0165, 1.0803, 0.9951, 1.0343, 0.9932, 1.0224, 0.9880]` | **`8 / 12`** | **`1.0148x` (`+1.48%`)**, 95% CI `[0.9942x, 1.0284x]` | **`1.0240x` (`+2.40%`)**, 95% CI `[0.9960x, 1.0616x]` | `med(A2)/med(A1)=0.9733` (`[0.9533, 1.0287]`); `med(B2)/med(B1)=0.9955` (`[0.9626, 1.0702]`) |
| **1-Worker Idle-VM Wall (`perf_counter_ns`, searches/s)** | `A1=487.61`, `A2=476.53` (`A=483.56`) \| `B1=477.22`, `B2=476.82` (`B=477.22`) | `[0.9729, 0.9425, 0.9692, 0.9632, 1.0132, 0.9768, 1.0419, 0.9637, 0.9942, 0.9619, 0.9911, 0.9569]` | `2 / 12` | `0.9710x` (`-2.90%`), 95% CI `[0.9625x, 0.9927x]` | `0.9869x` (`-1.31%`), 95% CI `[0.9531x, 1.0170x]` | `med(A2)/med(A1)=0.9773` (`[0.9591, 1.0302]`); `med(B2)/med(B1)=0.9991` (`[0.9649, 1.0582]`) |

### 3c. Bundle 3 vs Job 5 `bundle1` `bench 13` Timing (`A1 B1 B2 A2` x 4 Rounds, `PC20 + net768`)
Raw file: `forge-combo29/carbon2/job7/bundle3_proof_and_bench13_raw.txt`.

| Metric (`A = Job 5 bundle1`, `B = Bundle 3`, 4 ABBA rounds) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..4`) | Rounds Faster | `median_of_paired_round_ratios` + 95% CI | `ratio_of_pooled_medians` + 95% CI | A/A Control (Medians + Per-Round `[min, max]` Range) |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **`bench 13` Engine CPU (`getrusage` ns, NPS)** | `A1=1,962,027`, `A2=1,989,316` (`A=1,980,163`) \| `B1=2,013,712`, `B2=2,003,056` (`B=2,010,119`) | `[1.0135, 1.0424, 1.0109, 1.0111]` | **`4 / 4`** | **`1.0123x` (`+1.23%`)**, 95% CI **`[1.0109x, 1.0424x]`** | **`1.0151x` (`+1.51%`)**, 95% CI `[1.0030x, 1.0274x]` | `med(A2)/med(A1)=1.0139` (`[1.0092, 1.0536]`); `med(B2)/med(B1)=0.9947` (`[0.9842, 1.0022]`) |
| **`bench 13` Wall Clock (NPS)** | `A1=2,067,309`, `A2=2,084,396` (`A=2,075,502`) \| `B1=2,109,387`, `B2=2,104,065` (`B=2,109,387`) | `[1.0116, 1.0453, 1.0131, 1.0108]` | **`4 / 4`** | **`1.0124x` (`+1.24%`)**, 95% CI **`[1.0108x, 1.0453x]`** | **`1.0163x` (`+1.63%`)**, 95% CI `[1.0061x, 1.0252x]` | `med(A2)/med(A1)=1.0083` (`[1.0036, 1.0545]`); `med(B2)/med(B1)=0.9975` (`[0.9840, 1.0063]`) |

- **Bundle 3 Prediction Verdict (`b7cf5398d`):** Every median ratio matched our predicted ranges (`1.0148x` paired / `1.0240x` pooled self-play engine CPU inside `[1.012x, 1.035x]`, and `bench 13` **`4/4` rounds faster** at `1.0123x` paired / `1.0151x` pooled CPU inside `[1.010x, 1.035x]`), **but `prediction_bundle3.txt` is graded KILLED by its own `>= 9/12` rounds-faster clause on self-play (`8/12` faster)**.

---

## 4. What To Do Next With Another 90 Minutes (Ranked, With Share Attacked)

1. **Inline `go` execution option (`SyncGo`, default `false`) or spin-then-park worker handoff for single-game self-play processes (attacks `0.349%` engine dispatch CPU + `~1.4–1.8 s / 60 games` [`~10%` of 1-worker wall time] spent in `uci_loop <-> std::thread worker` `condition_variable` + pipe round-trips):**
   In self-play (`go softnodes 2000`), `stop` and `ponderhit` are never sent mid-search, yet every search wakes a separate `std::thread worker` via `work_cv.notify_one()` and parks `uci_loop`. Running bounded non-ponder `go softnodes` synchronously on the UCI thread under a default-off option removes two kernel futex context switches per search (`15,290` context switches per 60 games) and combines the `InfoOnce` line + `bestmove` into **one single `std::cout.write` + `flush()` syscall**.
2. **Precomputed `MovePicker` pin mask skipping `Board::is_legal` on unpinned non-king, non-EP moves (attacks `MovePicker::next` `9.26%` + `Worker::search` `21.26%` + `is_legal_complete` `1.47%` in the `97.65%` tree-search share):**
   When `!board.in_check()`, `ensure_king_lines()` already gives `pinned`; tagging `MovePicker` moves whose `from` bit is outside `pinned` (and not `King` or `EnPassant`) as `known_legal` skips per-move `is_legal` checks on ~85% of yielded captures and quiets.
3. **Concurrent 16-worker check of `O1` (`TTEntry::padding` 1-byte epoch for `TranspositionTable::clear()`, `0.54%–0.67%` single-worker L3 share in Task 1):**
   On this VM a single 32 MB table stayed inside the 320 MiB L3 (`< 1%`), so Task 2 rightly skipped `O1`. Whether 16 concurrent 32 MB tables (`512 MB` total) raise `tt.clear()` above `1%` under DRAM bandwidth contention is a measurement question on a saturated multi-worker host; `TTEntry::padding` (`1` unused byte in the 16-byte `TTEntry`) can hold an 8-bit clear epoch (full `memset` only once every 255 games = `< 0.003%`) if multi-worker counting ever justifies it.

---

## 5. Timestamps, Model Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job7/stamps.txt`:**
  `Tue Nov 17 04:53:51 PM UTC 2026 | job 7 received (FABLE_TO_carbon2_7.md); taking identity-proven job 6 bundle2 as base (dropping S7 part 3 and restoring S5 debug key assert)`
- **Last line of `forge-combo29/carbon2/job7/stamps.txt`:**
  `Tue Nov 17 06:03:30 PM UTC 2026 | writing REPORT_carbon2_job7.md after verifying all cited raw files`
- **Runtime Model Name & Version:** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job7` Immediately Before Report Commit

```text
 M forge-combo29/carbon2/job7/stamps.txt
?? forge-combo29/carbon2/job7/REPORT_carbon2_job7.md
forge-combo29/carbon2/job7:
bundle3_debug_and_fault_raw.txt
bundle3.patch.txt
bundle3_proof_and_bench13_raw.txt
bundle3_selfplay_12x60_hash32_raw.txt
o0_drop_s7p3_and_s5_assert.patch.txt
o2_identity_proof_raw.txt
o2_planted_fault.patch.txt
o2_selfplay_8x60_hash32_raw.txt
o2_stream_oracle_and_fault_raw.txt
o2_uci_option_info_once.patch.txt
outside_search_counts.txt
prediction_bundle3.txt
prediction_o2.txt
prove_o2_stream_oracle.py
REPORT_carbon2_job7.md
run_selfplay_hash32_abba.py
stamps.txt
step0_job7_raw.txt
```
