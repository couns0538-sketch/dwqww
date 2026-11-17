# Forge (`carbon2` — Job 9 Report): `Hash 16` PGO-Proof Node-Stop + TT Miss Fast-Path (`P1`), and Clean Production `bundle5` vs `r15e` (`12/12` Faster)

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job9/`).
- **Cloud Machine & Compiler:** `Intel(R) Xeon(R) CPU @ 2.60GHz` (x86_64, AVX-512, 320 MiB L3), `g++ 13.3.0`, `-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`.
- **Clean Production Deliverables (zero `O2` `InfoOnce`, zero `S7` part 3, debug `S5` assert restored):**
  1. `forge-combo29/carbon2/job9/bundle5.patch.txt` (`2,388` lines) — single unified diff against the live PC tree **`r15d`** (`6b98f217 + pc_r15.patch + r15c + E1`), matching the convention of `bundle1..bundle4`.
  2. `forge-combo29/carbon2/job9/delta_r15e_to_bundle5.patch.txt` (`1,331` lines) — single unified diff directly against **`r15e`** (`r15d + bundle1 without S7 part 3`, currently queued on the PC), producing a **byte-for-byte identical** source tree (`diff -ruN` = `0` lines, `--fuzz=0` verified).

---

## 0. Step 0 Verification and Base Taken

- **Step 0 (same machine and base build as Job 8, re-run today in `forge-combo29/carbon2/job9/step0_job9_raw.txt`):** All four configurations and pins met bit-identically with zero error/warning lines:
  1. **No settings, no net:** `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
  2. **`PC20`, no net:** `bench 11 -> 278024`, `bench 13 -> 587276`
  3. **`net512.fnn3` only:** `bench 11 -> 965454`, `bench 13 -> 4151906`
  4. **`PC20`, then `net512.fnn3`:** `bench 11 -> 625258`, `bench 13 -> 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)
- **Base Taken (`base_j9`):** Job 8's identity-proven **`bundle4.patch.txt`** (`r15e + G1..G4 + S5 assert + O2 + W1 + W2`), immediately cleaned via `forge-combo29/carbon2/job9/p0_drop_unused_o2_from_bundle4.patch.txt` (`177` lines, commit `a332dbb14`) to strip Job 7's unused `O2` (`InfoOnce`) per File 9's verdict before counting or coding. Step `P1` is timed directly against unstripped Job 8 `bundle4` (`A = bundle4`, `B = base_j9 + P1`), and the final production bundle `bundle5` (`base_j9 + P1`) is then timed **head-to-head against `r15e`** (`A = r15e`, `B = bundle5`).

---

## 1. What We Chose and Why: `Hash 16` Counts on `base_j9` (`forge-combo29/carbon2/job9/counts_hash16.txt`)

Before writing `P1` (`commit a332dbb14`), we instrumented a separate counting copy on the 60-game FEN-root stream at **`Hash 16`** (`PC20`, `Threads 1`, `OwnBook false`, `MateAlphaGuard true`, `net768.fnn3` checksum `30ab43b4ba5db5f3`, `go softnodes 2000`; `7,670` searches = `127.83`/game, `25,641,316` nodes, `trace = ee465caeff9c0fcf`, counting-build process CPU `13,582.29 ms` = `226.371 ms/game`):

| Work Item Measured at `Hash 16` (`counts_hash16.txt`) | How Often (`60` games / per game) | Share of a Game & Decision |
| :--- | :--- | :--- |
| **Per-node `Worker::should_stop() -> should_stop_with() -> total_nodes()` (`node_limit_specified_ == true`)** | **`32,930,134` calls** (`22,539,233` `search` + `10,326,949` `qsearch` + `63,952` root) = **`548,836` calls/game** (`~1,646,507` nested calls/game); **`100.00%` (`32,930,134 / 32,930,134`)** single-worker node-bounded (`Threads 1`, `MultiPV 1`, no clock) | **Est. `~1.0%–2.0%` on GCC, and PGO-critical on the PC:** the PC's Clang ThinLTO + PGO profile (`bench 11/13/16`) runs with `node_limit_specified_ == false` (`should_stop()` entered `1/1024 = 0.097%` of nodes -> laid out as cold code!), whereas `go softnodes 2000` and `go nodes 50000/250000` run with `node_limit_specified_ == true` (`100%` of nodes!). -> **Chosen (`Step P1`): inline `check_node_or_periodic_stop()` eliminates `99.90%` (`32,897,975`) of `should_stop()` chains.** |
| **`TranspositionTable::probe_owned` (`probe_body<false>`) misses & handle layout** | **`31,963,180` probes** (`532,720`/game), of which **`14,942,337` (`46.75%`, `249,039`/game) are misses** copying an unread 16-byte `*replace` `TTEntry` into a 64-byte `TTProbe` and re-testing `entries[0]` in a second loop; `14,666,813` stores (`244,447`/game) | **`4.03%` self share (`2.76%` probe + `1.27%` store)** -> **Chosen (`Step P1`): pack `TTProbe` (`64 -> 56 B`), elide `!TakeLock` `std::unique_lock` via `EmptyLock`, skip copying unread `16 B` `TTEntry` on all `14.94M` misses, and fast-exit empty `entries[0]` before scanning `entries[1..3]`.** |
| **Remaining `Board::is_legal(move)` calls outside `QuietMoves` (File 9 Item 2)** | **`16,525,641` calls** (`9,459,999` `search` non-quiet + `6,647,110` `qsearch` + `418,532` `ProbCut`) = **`275,427` calls/game**, of which **`12,515,716` (`75.73%`, `208,595`/game) are unpinned non-king, non-EP** (`6,265,331` `search` + `5,893,419` `qsearch` + `356,966` `ProbCut`) | **Est. `~0.5%`:** inline `Board::is_legal` (`board.hpp`) already fast-paths `!in_check` pin rays when `king_lines_.valid`, so adding a second pin precheck at call sites would duplicate `king_lines_.valid`; instead replace `PieceTypeTable[moving]` loads in `Board::is_legal` / `is_legal_complete` with table-free `(moving != WK && moving != BK)` (**Chosen in `Step P1`**). |
| **File 9 Item 1 (`SyncGo` condvar handoff) & Item 3 (`O1` TT clear at `Hash 16`)** | From committed Job 7/8 counts: `go`/`bestmove` condvar dispatch = **`0.770 ms/game`** (`127.83`/game); `shared_.tt.clear()` at `Hash 16` = **`0.744 ms/game`** (`1`/game) | **`0.35%` and `0.30%–0.34%` of engine CPU** (`< 0.4%` each) -> **Skipped per File 9.** |

---

## 2. Per-Step Table (`Step P1` and Clean Production `bundle5`)

| Step | Patch File (`forge-combo29/carbon2/job9/...`) | Lines | Identity & Oracles (What Was Compared, On How Many Searches / Sequences) | Self-Play Timing at `Hash 16` (`A1 B1 B2 A2` x 12 rounds x 60 games = 48 runs = `368,160` searches: per-round ratios, median, pooled, rounds faster, A/A range) | Prediction (Commit, Met or Killed) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`P1`** *(vs Job 8 `bundle4`)* | `p1_inline_node_stop_tt_miss_fastpath_and_king_islegal.patch.txt` *(stacked on `base_j9`; `p0` = `177` lines)* | 181 | `PC20` + `net768`/`net512` `bench 11/13/16` (`96` bench searches), `250/250` depth-9 rows, `1,000` evals (both nets), 6-game startpos (`4560d7c3afdeba2e`) & FEN (`9ed22c1193ab96de`) traces **EXACT** (`p1_identity_and_bench13_raw.txt`); **`500,000`-op collision TT + `9`-cap stop-boundary oracle** (`cab4d385b07d0fef`), **`2,010 / 2,010`** all-stages `MovePicker` sequences, **`55,868 / 55,868`** check-evasion sequences **EXACT** (`p1_oracles_and_fault_raw.txt`); **`368,160` self-play searches** across 48 runs (`ee465caeff9c0fcf`) **EXACT**; `Worker::search` frame `4512 -> 4496 B (-16 B)` | **Engine CPU (`getrusage` ns):** `[1.0018, 0.9771, 1.0080, 1.0298, 1.0111, 1.0053, 1.0133, 1.0371, 1.0004, 1.0216, 1.0025, 1.0350]`, **`paired median 1.0095x` (`+0.95%`, 95% CI `[1.0021x, 1.0257x]`)**, `pooled-median 1.0124x` (`+1.24%`, 95% CI `[1.0017x, 1.0248x]`), **`11/12` faster**; A/A: `med(A2)/med(A1)=0.9990` (range **`[0.9388, 1.0324]`**), `med(B2)/med(B1)=1.0086` (range **`[0.9860, 1.0668]`**).<br>**Wall:** `[0.9966, 0.9801, 1.0109, 1.0203, 1.0098, 1.0061, 1.0086, 1.0341, 0.9976, 1.0184, 0.9951, 1.0309]`, **`paired median 1.0092x` (`+0.92%`, 95% CI `[0.9971x, 1.0193x]`)**, `pooled-median 1.0090x`, `8/12` faster; A/A `1.0013` (`[0.9388, 1.0285]`) / `1.0091` (`[0.9807, 1.0617]`) (`p1_selfplay_12x60_hash16_raw.txt`) | `8f0a17e52`: **MET** (`1.0095x` CPU inside `[1.008x, 1.025x]`, `11/12 >= 9/12` faster, `1.0092x` wall inside `[1.006x, 1.025x]`, 95% CPU CI strictly `> 1.0000x`) | **CAUGHT** (`cab4d385b07d0fef` vs `79e74771cc65cfd6` on slot-1 TT victim skip, `p1_oracles_and_fault_raw.txt`) |
| **`bundle5`** *(head-to-head vs **`r15e`**)* | `bundle5.patch.txt` *(vs `r15d`, `2,388` lines)* & `delta_r15e_to_bundle5.patch.txt` *(vs `r15e`, `1,331` lines)* | 2,388 / 1,331 | `PC20` + `net768`/`net512` `bench 11/13/16`, `250/250` depth-9 rows, `1,000` evals, 6-game traces **EXACT** (`bundle5_identity_and_bench13_raw.txt`); **`500,000`-op TT + stop oracle**, **`2,010 / 2,010`** `MovePicker` sequences, **`55,868 / 55,868`** evasion sequences, **`-UNDEBUG` `S5` `precomputed_key` assert** **PASS** (`bundle5_oracles_debug_and_fault_raw.txt`); **`368,160` self-play searches** across 48 runs (`ee465caeff9c0fcf`) **EXACT**; stack vs `r15e`: `MovePicker 2240->2264 B (+24 B)`, `search 4560->4496 B (-64 B)`, `qsearch 2704->2672 B (-32 B)` | **Engine CPU (`getrusage` ns):** `[1.0162, 1.0322, 1.0580, 1.0434, 1.0165, 1.0874, 1.0097, 1.0667, 1.0609, 1.0403, 1.0273, 1.0123]`, **`paired median 1.0362x` (`+3.62%`, 95% CI `[1.0163x, 1.0594x]`)**, **`pooled-median 1.0364x` (`+3.64%`, 95% CI `[1.0191x, 1.0559x]`)**, **`12/12` faster**; A/A: `med(A2)/med(A1)=1.0188` (range **`[0.9709, 1.0744]`**), `med(B2)/med(B1)=1.0095` (range **`[0.9624, 1.0552]`**).<br>**Wall:** `[1.0197, 1.0384, 1.0447, 1.0452, 1.0153, 1.0946, 1.0087, 1.0618, 1.0669, 1.0475, 1.0309, 1.0152]`, **`paired median 1.0415x` (`+4.15%`, 95% CI `[1.0175x, 1.0546x]`)**, **`pooled-median 1.0354x` (`+3.54%`, 95% CI `[1.0201x, 1.0556x]`)**, **`12/12` faster**; A/A `1.0170` (`[0.9823, 1.0845]`) / `1.0097` (`[0.9768, 1.0488]`) (`bundle5_vs_r15e_selfplay_12x60_hash16_raw.txt`) | `d1e028b59`: **KILLED** by its own `< 1.045x` bound (`1.0362x < 1.045x`: `prediction_bundle5` multiplied `1.0423 * 1.0159 * 1.0095 = 1.0689x` instead of the true step product `1.0149 * 1.0127 * 1.0095 = 1.0376x`; `12/12 >= 11/12` clause met, real gain **`+3.62%` CPU / `+4.15%` wall** over `r15e`) | **CAUGHT** (`cab4d385b07d0fef` vs `79e74771cc65cfd6` + `-UNDEBUG` `S5` assert abort on `k ^= 1ULL`, `bundle5_oracles_debug_and_fault_raw.txt`) |

---

## 3. Clean Production Bundle `bundle5` — Exact Contents, Identity Proof, and Full Timing vs `r15e`

### 3.1 Steps Included in `bundle5`
- **Against `r15d`** (`bundle5.patch.txt`, `2,388` lines):
  1. **Job 5 `bundle1` minus `S7` part 3** (`r15e`): `S1..S6` + `S7` parts 1–2 (`string_view` `position` parsing + `memset` in unconditional `Worker::clear()`, **zero** `threat_history_dirty_` / `v1_eval_dirty_`).
  2. **Job 6 `G1..G4`**: cached `material_corr_key` + inline `dead_material_score` (`G1`), `see_ge` fast no-recapture + unified slider xray (`G2`), `known_gives_check` in `make_move` + `KingLines` reuse + lazy terminal stalemate check (`G3`), per-search `v3_active_net_` snapshot + hoisted `prepare_position_v3` + cached `king_sq_` (`G4`).
  3. **Job 7 `S5` Debug Assert ONLY (`O2` `InfoOnce` completely excluded)**: `#ifndef NDEBUG` `assert(key_ == dbg_key)` and `assert(compute_checkers() == 0)` in `Board::make_move`.
  4. **Job 8 `W1 + W2`**: fused `MovePicker::generate_quiets` / `generate_captures` without `picker_scratch_`, single-pass pin-legality & `gives_check` for `QuietMoves`, lazy/selective `b4::lesser_threats`, direct 1D continuation/check-bonus row pointers (`kZeroContRow`), and `[[gnu::noinline]]` cold stage generation.
  5. **Job 9 `P1`**: `[[gnu::always_inline]]` single-worker node-cap stop fast-path (`Worker::check_node_or_periodic_stop`), packed 56-byte `TTProbe` + `EmptyLock` + no-copy miss fast-path + empty-slot-0 fast exit in `TranspositionTable::probe_body`, and table-free `(moving != WK && moving != BK)` in `Board::is_legal` / `is_legal_complete`.
- **Against `r15e`** (`delta_r15e_to_bundle5.patch.txt`, `1,331` lines): items **2 + 3 + 4 + 5** above (`diff -ruN` verified `0` lines against `r15d + bundle5.patch.txt`).

### 3.2 Identity & Oracle Summary (`bundle5_identity_and_bench13_raw.txt` & `bundle5_oracles_debug_and_fault_raw.txt`)
- **`net512.fnn3` + `PC20`:** `bench 11 = 625258`, `bench 13 = 3652372`, `bench 16 = 23891329` (**EXACT**).
- **`net768.fnn3` + `PC20`:** `bench 11 = 882074`, `bench 13 = 4275906`, `bench 16 = 32374943` (**EXACT**).
- **Position & trace suites:** `250/250` depth-9 `(nodes, bestmove)` rows **EXACT**; `1,000` static evals on both `net768` and `net512` **EXACT**; 6-game startpos trace `4560d7c3afdeba2e` **EXACT**; 6-game FEN trace `9ed22c1193ab96de` **EXACT**; 48-run x 60-game (`368,160` searches) `Hash 16` self-play trace `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes/run) **EXACT**.
- **Differential & debug oracles:** `500,000`-op collision TT + `9`-cap stop-boundary oracle `cab4d385b07d0fef` (`mismatches=0`; planted fault caught at `79e74771cc65cfd6`); `2,010/2,010` all-stages `MovePicker` sequences (`mismatches=0`); `55,868/55,868` in-check evasion sequences across `313,716` visited positions (`mismatches=0`); `-UNDEBUG` `S5` assert clean on valid `precomputed_key` and aborts immediately on `k ^= 1ULL`.

### 3.3 Full Timing of `bundle5` vs `r15e`
- **48-run `Hash 16` Self-Play (`bundle5_vs_r15e_selfplay_12x60_hash16_raw.txt`, every run line committed in full):**
  - **Engine CPU (`getrusage` sps):** `r15e` build medians `A1 = 540.09`, `A2 = 550.22` (pooled `544.67`) -> `bundle5` build medians `B1 = 561.53`, `B2 = 566.89` (pooled `564.48`); **`12 / 12` rounds faster** (`min = 1.0097x`, `max = 1.0874x`), **`median_of_paired_round_ratios = 1.0362x` (`+3.62%`, 95% CI `[1.0163x, 1.0594x]`)**, **`ratio_of_pooled_medians = 1.0364x` (`+3.64%`, 95% CI `[1.0191x, 1.0559x]`)**.
  - **Wall clock (`perf_counter_ns` sps):** `r15e` build medians `A1 = 492.62`, `A2 = 500.99` (pooled `496.05`) -> `bundle5` build medians `B1 = 512.43`, `B2 = 517.42` (pooled `513.61`); **`12 / 12` rounds faster** (`min = 1.0087x`, `max = 1.0946x`), **`median_of_paired_round_ratios = 1.0415x` (`+4.15%`, 95% CI `[1.0175x, 1.0546x]`)**, **`ratio_of_pooled_medians = 1.0354x` (`+3.54%`, 95% CI `[1.0201x, 1.0556x]`)**.
- **`bench 13` (`PC20 + net768`, 4 ABBA rounds, `bundle5_identity_and_bench13_raw.txt`):**
  - **Engine CPU nps:** **`4 / 4` rounds faster** (`[1.0163, 1.0192, 1.0594, 1.0525]`), `paired median = 1.0358x` (`+3.58%`), `pooled-median = 1.0536x` (`+5.36%`).
  - **Wall nps:** **`4 / 4` rounds faster** (`[1.0170, 1.0193, 1.0631, 1.0426]`), `paired median = 1.0310x` (`+3.10%`), `pooled-median = 1.0474x` (`+4.74%`).
- **Expected PC ThinLTO + PGO bonus:** On the PC, `P1`'s inline `check_node_or_periodic_stop()` additionally removes the `bench`-trained PGO profile inversion where `should_stop()` (`0.097%` hot in `bench`, `100%` hot in `go softnodes 2000` and `go nodes 50000`) was laid out as cold code across `32.93M` calls per 60 games.

---

## 4. What We Would Do Next With Another 90 Minutes (Why Pure Bit-Exact Speed Should Stop Here -> Switch to Off-By-Default Strength Options)

1. **Stop bit-exact microarchitectural speed work after `bundle5` (`< 1.0%` remaining):** Across `E1` (`+4.17%` CPU on the PC), `r15e` (`bundle1` without `S7p3`, `+10.94%` cloud CPU), and `bundle5` on top of `r15e` (`+3.62%` CPU / `+4.15%` wall, `12/12` rounds faster), every hot wasted-work pocket above `1%` has been counted and harvested:
   - `NNUE v3` AVX-512 forward + paired `ZMM` updates (`~19%` self): already hand-vectorized with hoisted `vpermt2d` indices (`S4`) and `v3_active_net_` snapshot (`G4`).
   - `Worker::search` / `qsearch` control skeleton (`~28%` self): `should_stop()` PGO-cold chain eliminated (`P1`), stack frames shrunk by `> 2.6 KB`, `CorrHistV2` / `HistRework` / `CuckooRep` / `TtPruneV2` / `MovePicker` / `SEE` / `make_move` / `TT` miss paths all tightened.
   - Outside-search handlers at `Hash 16`: `tt.clear()` (`0.30%`), `Worker::clear()` (`0.16%`), `position` (`0.16%`), `go`/`bestmove` (`0.35%`) are each `< 0.4%`.
   No remaining bit-exact change can credibly clear `>= 3%` (or even `>= 1.5%`).
2. **Next 90 minutes — Pivot to File 8/9's second track (off-by-default UCI strength options with `>= 4,000`-game `20,000`-node `net768` screening):**
   - **Rank 1 (attacks ~`35%` of LMR re-searches and shallow futility pruning):** An off-by-default UCI option `CorrUncertaintyScale` scaling `TtPruneV2` static futility / RFP margins and LMR reduction by `|static_eval - raw_eval|` (the magnitude of `CorrHistV2` + pawn/material/non-pawn correction), so volatile positions where static eval needed a large correction prune less aggressively and calm positions prune tighter.
   - **Rank 2 (attacks ~`21.4M` quiet LMR reductions per 60 games):** An off-by-default UCI option `LmrContBonusDivisor` separating 1-ply/2-ply continuation history weight from main/threat butterfly history in the LMR history divisor (`HistRework 2` currently sums them 1:1 before dividing by `LmrHistoryDivisor = 5643`).

---

## 5. Times, Runtime Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job9/stamps.txt`:**
  `Tue Nov 17 07:48:42 PM UTC 2026 | job 9 received (FABLE_TO_carbon2_9.md); taking identity-proven job 8 bundle4 as base (stripping unused O2 InfoOnce per file 9)`
- **Last line of `forge-combo29/carbon2/job9/stamps.txt`:**
  `Tue Nov 17 09:02:48 PM UTC 2026 | writing REPORT_carbon2_job9.md before minute 80 and pushing branch`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon`

### Verbatim Pre-Commit Check (`git status --short && ls -R forge-combo29/carbon2/job9`)

```text
?? forge-combo29/carbon2/job9/REPORT_carbon2_job9.md
forge-combo29/carbon2/job9:
bundle5_identity_and_bench13_raw.txt
bundle5_oracles_debug_and_fault_raw.txt
bundle5.patch.txt
bundle5_vs_r15e_selfplay_12x60_hash16_raw.txt
counts_hash16.txt
delta_r15e_to_bundle5.patch.txt
p0_drop_unused_o2_from_bundle4.patch.txt
p1_identity_and_bench13_raw.txt
p1_inline_node_stop_tt_miss_fastpath_and_king_islegal.patch.txt
p1_oracles_and_fault_raw.txt
p1_planted_fault.patch.txt
p1_selfplay_12x60_hash16_raw.txt
prediction_bundle5.txt
prediction_p1.txt
REPORT_carbon2_job9.md
stamps.txt
step0_job9_raw.txt
test_p1_tt_and_stop_oracle.cpp
```
