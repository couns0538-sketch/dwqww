# Forge (`carbon2` — Job 8 Report): `Hash 16` Wasted-Work Counts, Fused Direct-Row `MovePicker` + Lazy `HistRework` Threats (`W1` + `W2`), and `bundle4.patch.txt`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job8/`).
- **Job 8 Base:** Job 7's **`bundle3.patch.txt`** on the Job 4 base (`r15d`), run with **all options at the PC's exact list** (`Threads 1`, **`Hash 16`**, `OwnBook false`, `MateAlphaGuard true`, `PC20`, `net768.fnn3`, default `InfoOnce false` — not one move, node count, score, or `info` line changed).
- **Cumulative Self-Contained Deliverable (`bundle4.patch.txt`):** `forge-combo29/carbon2/job8/bundle4.patch.txt` (`2,406` lines) — ONE unified diff against the **Job 4 base (`r15d`)** holding `bundle3 + W1 + W2` (`diff -qr` verified empty against stacked `base_j4 + bundle3 + W1 + W2`).
- **Cloud Machine & Compiler:** `Intel(R) Xeon(R) CPU @ 2.60GHz` (x86_64, AVX-512, 320 MiB L3), `g++ 13.3.0`, `-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`.

---

## 0. Step 0 Verification, Base Taken, Evasion Oracle on `bundle3`, and `Hash 16` Numbers for Job 7's `O1`

- **Step 0 (same machine and base build as Jobs 1–7, re-run today in `forge-combo29/carbon2/job8/step0_job8_raw.txt`):** All bench and perft pins met bit-identically with zero error/warning lines:
  - No settings, no net: `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
  - `PC20`, no net: `bench 11 -> 278024`, `bench 13 -> 587276`
  - `net512.fnn3` only: `bench 11 -> 965454`, `bench 13 -> 4151906`
  - `PC20`, then `net512.fnn3`: `bench 11 -> 625258`, `bench 13 -> 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)
- **Base Taken & Job 6 Audit Follow-up (`evasion_oracle_bundle3_raw.txt`):** Job 7's `bundle3.patch.txt` passed all identity pins in Job 7 (`1ce57014d`) and is our Job 8 base. Closing File 8's audit note on `G3`'s `generate_legal_evasions` change: we ran Job 5's full evasion `MovePicker` oracle on `bundle3` (`forge-combo29/carbon2/job8/evasion_oracle_bundle3_raw.txt`) — **`total_visited = 313,716`, `in_check_positions = 14,238`, `picker_sequences_compared = 55,868`, `mismatches = 0`** (and re-ran it on `W1` and `W2`/`bundle4` as well: `55,868 / 55,868` exact).
- **`Hash 16` Count for Job 7's `O1` (`forge-combo29/carbon2/job8/wasted_work_counts_hash16.txt`):**
  - Across the 60-game `Hash 16` stream (`60` `ucinewgame` calls, `7,670` searches, `25,641,316` nodes, `trace = ee465caeff9c0fcf`, counting-build process CPU `14,855.25 ms` = `247.59 ms/game`; uninstrumented `bundle3` CPU `~13,200 ms` = `~220.0 ms/game`):
    - **`tt_clear_cpu_ns` (`shared_.tt.clear()`, `16 MB` x 60):** **`44,628,594 ns` = `44.629 ms` total = `0.744 ms / game` = `0.300%`** of counting-build engine CPU (`~0.338%` of uninstrumented `220 ms/game` CPU) — almost half of Job 7's `Hash 32` `1.477 ms/game` (`0.669%`).
    - **`worker_clear_cpu_ns` (`Worker::clear()` x 60):** **`23,229,482 ns` = `23.229 ms` total = `0.387 ms / game` = `0.156%`**.
  - Job 7 did not implement or time `O1` because even at `Hash 32` it was below the `>= 1.0%` gate (`0.541%–0.669%`); at the PC's true `Hash 16` (`0.30%–0.34%`, `0.744 ms/game`), skipping `O1` is doubly confirmed.

---

## 1. What We Chose and Why: `Hash 16` Wasted-Work Counts (`forge-combo29/carbon2/job8/wasted_work_counts_hash16.txt`)

Before touching any engine code (`commit 93a09fdf5`), we instrumented a separate counting copy on the 60-game `Hash 16` stream (`7,670` searches, `25,641,316` nodes, `ee465caeff9c0fcf`) to measure exact frequencies and direct thread CPU time of thrown-away / redundant work inside the search:

| Candidate Work Measured (`wasted_work_counts_hash16.txt`) | 60-Game Total (`7,670` searches) | Per-Game Rate | Share of Game Engine CPU & Decision |
| :--- | :--- | :--- | :--- |
| **`MovePicker::generate_quiets()` + `QuietScorer` loop** | `2,700,559` calls; **`64,700,448` quiets generated & scored** (`23.96`/call), of which **`43,336,924` (`66.98%`) are NEVER yielded** (`127,206` calls search `0` quiets); **`1,158.84 ms` thread CPU** | `45,009` calls/game; `1,078,341` quiets/game; **`19.314 ms/game`** | **`7.80%` of counting-build CPU** (`~8.7%` uninstrumented — hidden inside `MovePicker::next` by inlining!) -> **Chosen (`W1` + `W2`)** |
| **`MovePicker::generate_captures()` (`picker_scratch_` + `piece_at` reload)** | `8,382,756` calls; **`14,163,731` captures generated & scored** | `139,713` calls/game; `236,062` captures/game | Est. ~`1.5%` inside `MovePicker::next` -> **Chosen (`W1` + `W2`): fuse directly without `picker_scratch_`** |
| **Non-check `Board::is_legal` + `gives_check` on `QuietMoves`** | `6,443,182` non-check `is_legal` calls in `Worker::search`, of which **`5,893,419` (`91.47%`) are unpinned non-king, non-EP**; `21,363,524` `QuietMoves` yields re-check `is_legal` & `gives_check` after `generate_quiets` already built `KingLines` | `107,386` calls/game (`98,224` unpinned/game) | Est. ~`1.0%` inside `Worker::search` / `MovePicker::next` -> **Chosen (`W1` + `W2`): single-pass pin-legality & `gives_check` inside `QuietMoves`** |
| **Eager `threat_maps_[ply] = b4::lesser_threats(board)` + pre-quiet `quiet_history`** | `7,539,533` full threat-map builds, of which **`1,399,941` (`18.57%`) are NEVER read** before TT/capture cutoff; `14,158,261` pre-quiet `quiet_history` calls only need `by_pawn` for Pawn/Knight/Bishop/King moves | `125,659` builds/game (`23,332` unread/game) | Est. ~`0.8%` pure thrown-away work -> **Chosen (`W1` + `W2`): lazy `ensure_threat_map`, inline `by_pawn` for minor/pawn pre-quiet calls, skip `by_rook`/`by_minor` when `us` lacks Queen/Rook** |
| **Unread `v3_state_->stack[index]` `3,072 B` accumulator stores** | `4,584,067 / 6,354,993` (`72.13%`) in `search` and `2,858,860 / 3,878,775` (`73.71%`) in `qsearch` (`3,088,273` stand-pat cutoffs on `10,326,604` `qsearch` nodes) are overwritten unread | `124,049` unread `3 KB` L1 stores/game | **Rejected:** 48 L1 `ZMM` stores cost ~24 cycles (`0.73 * 24 = 17.5` cycles), whereas replaying parent columns on the 27% that descend costs `0.27 * ~250 = ~67` cycles (net loss). |

**Two-step iteration (`W1 -> W2`):**
- **`W1`** fused `generate_quiets`/`generate_captures`, added single-pass `QuietMoves` pin-legality/`gives_check` and lazy/selective `lesser_threats`, **but** pre-summed all `64` destination squares (`build_base_to`) for every present piece type (`up to 6 * 64 = 384` squares/call to read only `23.96` quiet targets = `93%` wasted pre-sum work!) and inlined `300` lines of move-gen into `MovePicker::next`. `W1` alone measured only `1.0043x` paired CPU (`8/12` faster), killing `prediction_w1.txt`.
- **`W2`** (stacked on `W1`) removed `build_base_to` completely — hoisting only branchless 1D row pointers (`c1`, `c2` defaulting to `kZeroContRow[64]`, `c4`, `chk`) per piece type so **only the `23.96` actual target squares `to` are loaded** — and marked `generate_quiets` / `generate_captures` `[[gnu::noinline]]` to restore `MovePicker::next`'s compact L1i footprint. **`W2` (`bundle4.patch.txt`) met every clause of `prediction_w2.txt` (`851a04d82`).**

---

## 2. Per-Step Summary Table (`W1` on `bundle3`, then `W2` Stacked on `W1`)

| Step | Patch File (`forge-combo29/carbon2/job8/...`) | Lines | Identity & Oracles (What Was Compared, On How Many Positions / Searches) | Self-Play Timing at `Hash 16` (`A = bundle3`, `A1 B1 B2 A2` x 12 rounds x 60 games = 48 runs, `InfoOnce false`: per-round ratios, median, pooled, rounds faster, A/A range) | Prediction (Commit, Met or Killed) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`W1`** | `w1_fused_simd_movepicker_and_lazy_threats.patch.txt` (`b4.hpp`, `search.hpp`, `search.cpp`) | 554 | `PC20` + `net768`/`net512` `bench 11/13/16`, `250` depth-9 rows, `1000` evals, 6-game traces **EXACT** (`w1_identity_and_bench13_raw.txt`); **`2,010 / 2,010`** all-stages `MovePicker` sequences **EXACT** + **`55,868 / 55,868`** evasion sequences **EXACT** (`w1_oracles_and_fault_raw.txt`); **`368,160` searches** across 48 runs (`ee465caeff9c0fcf`) **EXACT**; stack: `MovePicker 2240->2264 B`, `search 4560->4512 B (-48 B)`, `qsearch 2704->2656 B (-48 B)` | **Engine CPU (`getrusage` ns):** `[1.0193, 0.9998, 1.0032, 0.9730, 0.9651, 1.0123, 1.0202, 1.0396, 1.0048, 1.0039, 0.9950, 1.0293]` (`8/12` faster), `paired median 1.0043x` (`[0.9974x, 1.0197x]`), `pooled-median 1.0062x`; A/A: `med(A2)/med(A1)=0.9888` (`[0.9250, 1.0794]`), `med(B2)/med(B1)=0.9986` (`[0.9520, 1.0552]`).<br>**Wall:** `[1.0162, 0.9915, 1.0011, 0.9755, 0.9621, 1.0130, 1.0167, 1.0304, 1.0085, 1.0011, 0.9899, 1.0176]` (`8/12`), `paired median 1.0048x`, `pooled-median 1.0027x`; A/A `[0.9251, 1.0668]` / `[0.9630, 1.0387]` (`w1_selfplay_12x60_hash16_raw.txt`) | `580bcddb0`: **KILLED** (`1.0043x <= 1.015x`, `8/12 < 9/12` due to `384`-sq `build_base_to` waste) | **CAUGHT** at seq 446 (`c1d1` legal pin-ray slide, `w1_oracles_and_fault_raw.txt`) |
| **`W2` (`bundle4`)** | `w2_direct_row_scorer_and_noinline_movegen.patch.txt` (`search.hpp`, `search.cpp`, stacked on `W1`; full diff `bundle4.patch.txt`) | 219 (`2,406` full) | `PC20` + `net768`/`net512` `bench 11/13/16`, `250` depth-9 rows, `1000` evals, 6-game traces **EXACT** (`w2_bundle4_identity_and_bench13_raw.txt`); **`2,010 / 2,010`** all-stages `MovePicker` sequences **EXACT** + **`55,868 / 55,868`** evasion sequences **EXACT** (`w2_oracles_and_fault_raw.txt`); **`368,160` searches** across 48 runs (`ee465caeff9c0fcf`) **EXACT**; stack: `MovePicker 2264 B`, `search 4512 B (-48 B vs bundle3, -2592 B vs r15d)`, `qsearch 2656 B (-48 B vs bundle3, -2592 B vs r15d)` | **Engine CPU (`getrusage` ns):** `[1.0189, 0.9904, 0.9928, 1.0090, 1.0095, 1.0158, 1.0164, 1.0147, 1.0162, 1.0106, 0.9988, 1.0223]` (**`9/12` faster**), **`paired median 1.0127x` (`+1.27%`, 95% CI `[1.0039x, 1.0163x]`)**, **`pooled-median 1.0128x` (`+1.28%`, 95% CI `[1.0003x, 1.0173x]`)**; A/A: `med(A2)/med(A1)=1.0000` (`[0.9711, 1.0406]`), `med(B2)/med(B1)=0.9927` (`[0.9567, 1.0245]`).<br>**Wall:** `[1.0210, 0.9939, 0.9877, 1.0109, 1.0137, 1.0220, 1.0125, 1.0033, 1.0189, 1.0107, 0.9903, 1.0255]` (**`9/12` faster**), **`paired median 1.0117x` (`+1.17%`, 95% CI `[0.9986x, 1.0199x]`)**, `pooled-median 1.0078x`; A/A `1.0003` (`[0.9744, 1.0304]`) / `0.9936` (`[0.9674, 1.0259]`) (`w2_bundle4_selfplay_12x60_hash16_raw.txt`) | `851a04d82`: **MET** (`1.0127x` CPU inside `[1.012x, 1.035x]`, `1.0117x` wall inside `[1.010x, 1.035x]`, `9/12 >= 9/12` faster, 95% CPU CI strictly `> 1.000x`) | **CAUGHT** at seq 0 (`c2[to]` continuation drop, `w2_oracles_and_fault_raw.txt`) |

---

## 3. Bundle 4 (`forge-combo29/carbon2/job8/bundle4.patch.txt` — Self-Contained Diff Against Job 4 Base `r15d`)

- **Patch file:** `forge-combo29/carbon2/job8/bundle4.patch.txt` (`2,406` lines), applying with `patch -p1 --fuzz=0` directly to the **Job 4 base (`r15d` = `6b98f217 + pc_r15.patch + a_speed_pc20_v3.patch.txt + e1_legal_check_evasions.patch.txt`)** and verified byte-identical (`diff -qr` empty) to `base_j4 + job7/bundle3.patch.txt + W1 + W2`.
- **All steps inside `bundle4.patch.txt` (14 steps across Jobs 4–8, zero behavioral or output changes at defaults):**
  - `S1` (cache-tiled refresh + single-add/sub AVX-512 forward fusion)
  - `S2` (AVX-512 `VPERMT2D` `pick_best_scored` + cached picker quiet history + unboxed `is_pseudo_legal`)
  - `S3` (correction-table L1 prefetches + 4-way unrolled `non_pawn_key`)
  - `S4` (slim `MovePicker` `-2,552 B` struct + `qsearch` `odd_idx16` load guard)
  - `S5` (`Board::make_move` precomputed `early_key` reuse WITH `#ifndef NDEBUG` `assert(key_ == dbg_key)` recomputation check + conditional 72B `KingLines` copy on `Undo`)
  - `S6` (`Board::see_ge` unpinned enemy-pawn recapture fast-exit)
  - `S7` Parts 1 & 2 ONLY (zero-allocation `std::string_view` UCI `position`/`go` parsing + persistent `SearchTask` `Board` capacity handoff; **NO `S7` Part 3**)
  - `G1` (cached `corr_mat_idx` `material_key` index on `SearchStack` + inline `has_dead_material_candidates` guard)
  - `G2` (`Board::see_ge` no-recapture fast-exits + unified `FORGE_SDK_SEE_HOIST` king-line cache)
  - `G3` (`known_gives_check` reuse in `Board::make_move` with `assert(compute_checkers() == 0)` + `MovePicker::init_check_squares` `ensure_king_lines` deduplication + ray-free pawn stalemate fast-exit + branchless king-evasion taboo pre-mask)
  - `G4` (per-search `v3_active_net_` / `nnue_active_` snapshot + hoisted `nnue::v3::prepare` `6,464 -> 112 B` + direct `board.king_square` & parent `KingKey` reuse on non-king moves in `Worker::static_evaluate_v3`)
  - `O2` (UCI option `InfoOnce`, `type check default false` — off by default)
  - `W1 + W2` (lazy & piece-type-selective `b4::lesser_threats`, inline `by_pawn` minor/pawn pre-quiet `rework_entry`, outlined `[[gnu::noinline]]` fused `generate_captures` & `generate_quiets` with hoisted branchless per-piece `main`/`rework`/`cont1`/`cont2` rows and zero `picker_scratch_` round-trips, and single-pass `QuietMoves` pin-legality + `gives_check` reuse)
- **Full Identity, Stack, `bench 13`, and 48-Run Self-Play Raw Files:**
  - Identity + 4-round `bench 13` vs `bundle3` (`paired median 1.0068x` wall / `1.0056x` CPU, `pooled-median 1.0100x` wall / `1.0102x` CPU, reaching `2,129,373` wall NPS / `2,029,118` CPU NPS; per-round A2/A1 `[0.9956, 1.0140]` CPU, B2/B1 `[0.9916, 1.0394]` CPU): `forge-combo29/carbon2/job8/w2_bundle4_identity_and_bench13_raw.txt`.
  - All-stages `MovePicker` (`2,010 / 2,010`), Evasion `MovePicker` (`55,868 / 55,868`), and planted-fault raw file: `forge-combo29/carbon2/job8/w2_oracles_and_fault_raw.txt`.
  - Full 48-run 12x60 `Hash 16` self-play log (`A = bundle3`, `B = bundle4`, `fnv1a64 = ee465caeff9c0fcf` on all 48 runs; `580.87 -> 588.29` pooled searches/s CPU [`+1.27%` paired / `+1.28%` pooled]): `forge-combo29/carbon2/job8/w2_bundle4_selfplay_12x60_hash16_raw.txt`.

---

## 4. What To Do Next With Another 90 Minutes (Why Pure Bit-Exact Speed Is Now Near Diminishing Returns, and Ranked Next Targets)

After `E1` (`+4.4%` on PC), `bundle1` (`+3.42%` cloud CPU), `bundle3` (`+1.5%` cloud CPU), and `bundle4` (`+1.27%` cloud CPU — moving this Xeon from `538.8` searches/s on `r15d` to `588.3` searches/s on `bundle4`), **no single remaining bit-exact wasted-work pocket appears to hold `>= 3%` on its own**:
1. **Why no `>= 3%` bit-exact speed step remains (`wasted_work_counts_hash16.txt`):**
   - Outside-search handlers at `Hash 16` are all `< 1%` (`tt.clear()` `0.30%`, `Worker::clear()` `0.16%`, `position` `0.16%`, `go`/`bestmove` `0.35%`; `info` output `1.01%` already has `InfoOnce`).
   - Inside-search NNUE accumulator `3 KB` unread stores (`72–74%` unread) save ~18 cycles in L1 if skipped vs ~67 cycles of parent replay on the 27% that descend.
   - What remains in `MovePicker` (`67%` of generated quiet moves unyielded) cannot be pruned *before* scoring without changing `pick_best_scored()`'s 4-swap tie order unless move-ordering ties are allowed to change (which becomes a strength change, not a bit-exact speed patch).
2. **Ranked next actions if continuing:**
   - **(1) Measure `bundle4.patch.txt` on the PC's Clang 23 ThinLTO + PGO `-march=znver5` build (both default `InfoOnce false` and `InfoOnce true` under 16-worker self-play saturation):** On the saturated 16-worker PC (`6.41` engine cores + `0.71` Python client cores = `10.0%` client CPU), `InfoOnce true` attacks both the `1.01%` engine `info` write/flush time and the `89%` discarded pipe `readline()` traffic in the 16 Python clients without idle-VM wakeup sleep.
   - **(2) Staged quiet move generation behind a default-off UCI option `StagedQuiets` (attacks the `66.98%` = `43.3M / 64.7M` scored-but-never-yielded quiet moves in `wasted_work_counts_hash16.txt`, `~3–4%` speed + strength test required):** Generating & scoring quiet checks / positive-history / piece moves before negative-history pawn/minor moves changes tie/stage order slightly, so it belongs behind a default-off option gated at `50,000` nodes on the PC.
   - **(3) Strength-side search experiments gated on the PC's 768 net (`50,000`-node SPRT):** Testing Job 3's default-off `ZobristNonPawnCorr` (`O(1)` incremental non-pawn correction keys, attacking the remaining `~3%` `non_pawn_key` + `corrected_eval` work) or LMR / correction-history scaling tuned specifically for the stronger 768 net.

---

## 5. Timestamps, Model Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job8/stamps.txt`:**
  `Tue Nov 17 06:14:31 PM UTC 2026 | job 8 received (FABLE_TO_carbon2_8.md); taking identity-proven job 7 bundle3 as base, Hash 16 everywhere`
- **Last line of `forge-combo29/carbon2/job8/stamps.txt`:**
  `Tue Nov 17 07:38:01 PM UTC 2026 | writing REPORT_carbon2_job8.md after opening and verifying all cited raw files`
- **Runtime Model Name & Version:** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job8` Immediately Before Report Commit

```text
 M forge-combo29/carbon2/job8/stamps.txt
?? forge-combo29/carbon2/job8/REPORT_carbon2_job8.md
forge-combo29/carbon2/job8:
bundle4.patch.txt
evasion_oracle_bundle3_raw.txt
prediction_w1.txt
prediction_w2.txt
REPORT_carbon2_job8.md
run_selfplay_hash16_abba.py
stamps.txt
step0_job8_raw.txt
test_w1_movepicker_oracle.cpp
w1_fused_simd_movepicker_and_lazy_threats.patch.txt
w1_identity_and_bench13_raw.txt
w1_oracles_and_fault_raw.txt
w1_planted_fault.patch.txt
w1_selfplay_12x60_hash16_raw.txt
w2_bundle4_identity_and_bench13_raw.txt
w2_bundle4_selfplay_12x60_hash16_raw.txt
w2_direct_row_scorer_and_noinline_movegen.patch.txt
w2_oracles_and_fault_raw.txt
w2_planted_fault.patch.txt
wasted_work_counts_hash16.txt
```
