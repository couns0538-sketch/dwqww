# Forge (`carbon2` — Job 6 Report): Post-Bundle-1 Profile, Stacked Work-Removal Steps `G1..G4`, and `bundle2.patch.txt`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job6/`).
- **Job 4 Base Tree (target of `bundle2.patch.txt`):** `6b98f217` + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` (`forge/r15c`) + `forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt` (`E1`).
- **Job 6 Step Base (`bundle1`):** Job 4 base + `forge-combo29/carbon2/job5/bundle.patch.txt` (`S1..S7`).
- **Cloud Machine & Compiler:** `Intel(R) Xeon(R) CPU @ 2.60GHz` (x86_64, AVX-512), `g++ 13.3.0`, `-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`.
- **Answer to File 6's question on `S2`'s `odd_idx16` load:** Yes — Job 5's Step `S4` (`job5/s4_slim_movepicker_and_vpermt2d_hoist.patch.txt`, included in `job5/bundle.patch.txt` and `job6/bundle2.patch.txt`) already moved `odd_idx16` inside the `if (i + 8 <= n)` vector loop in `score_quiets`.

---

## 0. Step 0 Verification and Task 0 State of Job 5 Bundle

- **Task 0 (state of Job 5 bundle when Job 6 started):** Job 5's `forge-combo29/carbon2/job5/bundle.patch.txt` (`S1 + S2 + S3 + S4 + S5 + S6 + S7`) was **already finished, 100% identity-proven, 12x60-game self-play timed (`12/12` rounds faster over Job 4 base: `median_of_paired_round_ratios = 1.0342x` CPU / `1.0266x` wall, `ratio_of_pooled_medians = 1.0366x` CPU / `1.0313x` wall), and pushed** in commit `f81dc8bbc` before `FABLE_TO_carbon2_6.md` was read.
- **Step 0 (same machine and base build as Job 5, re-run today in `forge-combo29/carbon2/job6/step0_job6_raw.txt`):** All 10 `bench`/`perft` pins and 3 `eval` pins met 100% bit-identically with zero `unknown option` / `invalid value` / `ERROR` lines:
  - No settings, no net: `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
  - `PC20`, no net: `bench 11 -> 278024`, `bench 13 -> 587276`
  - `net512.fnn3` only: `bench 11 -> 965454`, `bench 13 -> 4151906`
  - `PC20`, then `net512.fnn3`: `bench 11 -> 625258`, `bench 13 -> 3652372`
  - `PC20` + `net512.fnn3` `eval`: `968` / `1176` / `31` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)

---

## 1. Task 1 Profile of Job 5 `bundle1` (`forge-combo29/carbon2/job6/profile_bundle1.txt`)

Collected before any Job 6 step (`commit 5d0b22d78`) using the identical Job 3 / Job 4 driver (`job2/selfplay_driver_v2.py --mode fen --fen-file positions_250.txt --games 24`, `PC20 + net768.fnn3`, `3,391` searches, `11,320,109` nodes, `trace_fnv1a64 = 22e72db9682af7ef`). Total `gprof` self samples dropped from **`5.27 s`** in Job 4 post-`E1` (`job4/base_r15c_e1_profile.txt`) to **`4.71 s`** in Job 5 `bundle1` (**`-10.63%` total self samples** on the identical `11,320,109`-node search):

| Attacked Subsystem / Group (Jobs 3–5 Steps) | Before (`job4/base_r15c_e1_profile.txt`, total `5.27 s`) | After (`job5/bundle.patch.txt`, total `4.71 s`) | Call-Count / Work-Removed Verification |
| :--- | :--- | :--- | :--- |
| **In-Check Evasions (`Job 3 E1` + `Job 5 S4`)** *(Job 3 pre-`E1` was `8.48%`, `14.25M` `is_legal_complete` calls)* | `0.20s` (`3.80%`: `generate_evasions` `0.11s`, `generate_legal_evasions` `0.02s`, `is_legal_complete` `0.07s`) | `0.13s` (`2.76%`: `generate_evasions` `0.06s`, `generate_legal_evasions` `0.02s`, `is_legal_complete` `0.05s`) | `E1` cut `is_legal_complete` calls `14.25M -> 4.19M` (`-70.6%`); `S4` removed `512 B` `legal_to_by_from_[64]` per evasion node. |
| **NNUE v3 Refresh + Accumulator Update + Forward (`Job 4/5 S1`)** | `1.21s` (`22.96%`) | `1.00s` (`21.23%`, **`-17.4%` self samples**) | Standalone `nnue::v3::evaluate` / `output_sum_avx512` calls dropped **`2,320,555 -> 1,295,546` (`-44.2%`)** via `1,025,009` fused `refresh_one_and_evaluate` calls. |
| **Quiet History Scoring, Deduplication & `MovePicker` (`Job 4 S2 + Job 5 S4`)** | `1.85s` (`35.10%`: `Worker::search` `1.13s`, `next` `0.38s`, `pick_best` `0.21s`, `quiet_history` `0.07s`, `lesser_threats` `0.02s`, `is_pseudo_legal` `0.04s`) | `1.60s` (`33.97%`, **`-13.5%` self samples**) | **`Worker::quiet_history` calls cut `12,276,628 -> 6,378,939` (`-48.0%`)**; **`b4::lesser_threats` calls cut `3,915,688 -> 547,696` (`-86.0%`)**; `Worker::search` frame cut `7,104 -> 4,496 B` (`-2,608 B/ply`). |
| **Static-Eval Correction History + Prefetch (`Job 4 S3`)** | `0.44s` (`8.35%`) | `0.48s` (`10.19%`: `corrected_eval` `0.38s` [`8.07%`], `update_correction` `0.05s`, `record_move` `0.05s`) | `non_pawn_key` unrolled, but `material_key(board)` (`MaterialCorrectionWeight == 100`) was still uncached (`10.88M` calls) -> attacked by **`G1`** below. |
| **Board Move Transition & Key (`Job 5 S5`)** | `0.32s` (`6.07%`) | `0.26s` (`5.52%`, **`-18.8%` self samples**) | **`has_legal_en_passant_capture` calls cut `301,858 -> 173,848` (`-42.4%`)** via `precomputed_key`; remaining `checkers_` recomputation attacked by **`G3`** below. |
| **Static Exchange Evaluation (`Job 5 S6`)** | `0.24s` (`4.55%`, `12,300,134` calls) | `0.28s` (`5.94%`, `12,300,134` calls) | Unpinned pawn recapture fast-exit in place; no-recapture quiet calls (`~70%` of `8.97M` search calls) attacked by **`G2`** below. |
| **UCI Dispatch & `ucinewgame` Clear (`Job 5 S7`)** | `26` `Evaluator::clear()` calls across 24 games | **`1` `Evaluator::clear()` call across 24 games (`-96.2%`)** | Zero-allocation `std::string_view` `position`/`go` parsing + dirty-tracked `Worker::clear()`. |

*(Full Top-25 function table with call counts and complete raw `gprof` flat profile are committed in `forge-combo29/carbon2/job6/profile_bundle1.txt`; note Ranks #2 `#MovePicker::next` tie-breaking in `pick_best_scored` [#6, `4.46%`] and `#4/#7/#11/#13` NNUE dot products were skipped per the job rules.)*

---

## 2. Job 6 Stacked Work-Removing Steps (`G1..G4`, Applied in Order on `job5/bundle.patch.txt`)

Every patch applies cleanly in sequence (`bundle.patch.txt -> G1 -> G2 -> G3 -> G4`) on the Job 4 base with `patch -p1 --fuzz=0`. All predictions were committed as standalone commits before each step's first timed run and never edited.

| Step | Patch File (`forge-combo29/carbon2/job6/...`) & Touched Files/Functions | Lines | Identity (`PC20` + `net768` & `net512`: `bench 11/13/16`, `250` depth-9 rows, `1000` evals, 6-game `startpos` `4560d7c3afdeba2e` & `fen` `9ed22c1193ab96de` + unit oracle) | `bench 13` Timing (`A1 B1 B2 A2` x 4 rounds, `net768`: paired ratios, `paired median`, `pooled-median`, A/A) | `sizeof(MovePicker)` / `Worker::search` / `Worker::qsearch` (`bundle1/prev -> step`) | Prediction (Commit, Met or Killed) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- | :--- |
| **`G1`** | `g1_cached_material_corr_and_inline_dead_mat.patch.txt` (`eval.hpp`, `search.hpp`, `search.cpp`: `has_dead_material_candidates`, `record_move`, `record_null_move`, `prefetch_correction`, `corrected_eval`, `update_correction`) | 115 | All pins **EXACT** (`g1_proof_raw.txt`) | rusage CPU: `[1.0054, 0.9295, 0.9912, 0.9234]` (`1/4`), `paired median 0.9604x` (`[0.9234x, 1.0054x]`), `pooled-median 0.9663x`, A/A `3.56%`; Wall: `[1.0076, 0.9299, 0.9911, 0.9206]` (`1/4`), `paired median 0.9605x`, `pooled-median 0.9677x`, A/A `3.87%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / `4496 -> 4496 B` (`+0 B`) / `2704 -> 2704 B` (`+0 B`) | `4186c9b83`: **KILLED** (`0.9604x <= 1.005x`, `3.56%` B2/B1 layout swing); kept in `bundle2` | **CAUGHT** (`g1_planted_fault.patch.txt`: `bench 11 = 874575 != 882074`, `g1_planted_fault_raw.txt`) |
| **`G2`** | `g2_see_fast_no_recapture_and_hoist_unify.patch.txt` (`board.cpp`: `Board::see_ge` no-recapture fast-exits + unified `FORGE_SDK_SEE_HOIST` king-line cache) | 80 | All pins **EXACT** + `152,488 / 152,488` two-binary `Board::see_ge` calls `0` mismatches (`g2_proof_raw.txt`, `g2_oracle_and_fault_raw.txt`) | rusage CPU: `[0.9877, 1.0188, 0.9614, 0.9544]` (`1/4`), `paired median 0.9745x` (`[0.9544x, 1.0188x]`), `pooled-median 0.9744x`, A/A `2.46%`; Wall: `[0.9895, 1.0157, 0.9654, 0.9535]` (`1/4`), `paired median 0.9775x`, `pooled-median 0.9708x`, A/A `2.48%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / `4496 -> 4496 B` (`+0 B`) / `2704 -> 2704 B` (`+0 B`) | `cd10d12f8`: **KILLED** (`0.9745x <= 1.004x`, `2.46%` A/A spread); kept in `bundle2` | **CAUGHT** (`g2_planted_fault.patch.txt` at call `261` `g7g5`, `g2_oracle_and_fault_raw.txt`) |
| **`G3`** | `g3_known_gives_check_kinglines_and_stalemate.patch.txt` (`board.hpp`, `board.cpp`, `search.cpp`: `Board::make_move(..., known_gives_check)`, `ensure_king_lines`, `has_legal_move`, `generate_legal_evasions`, `MovePicker::init_check_squares`) | 165 | All pins **EXACT** + `1,005` positions / `21,765` moves Board oracle `0` mismatches (`g3_proof_raw.txt`, `g3_oracle_and_fault_raw.txt`) | rusage CPU: `[1.0411, 1.0007, 0.9990, 0.9982]` (`2/4`), `paired median 0.9999x` (`[0.9982x, 1.0411x]`), `pooled-median 1.0050x`, A/A `1.16%`; Wall: `[1.0453, 1.0009, 1.0024, 0.9994]` (`3/4`), `paired median 1.0017x`, `pooled-median 1.0092x`, A/A `1.18%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / `4496 -> 4496 B` (`+0 B`) / `2704 -> 2704 B` (`+0 B`) | `8e9ff2766`: **KILLED** (`1.0017x <= 1.006x`, inside `1.18%` A/A spread); kept in `bundle2` | **CAUGHT** (`g3_planted_fault.patch.txt` on pinned-pawn stalemate FEN, `g3_oracle_and_fault_raw.txt`) |
| **`G4`** | `g4_snapshot_v3_net_hoist_prepare_and_king_sq.patch.txt` (`nnue_v3.hpp`, `nnue_v3.cpp`, `search.hpp`, `search.cpp`: inline `king_key`, `nnue::v3::prepare`, `Worker::search`, `static_evaluate`, `record_move`, `record_null_move`, `static_evaluate_v3`) | 220 | All pins **EXACT** (`g4_proof_raw.txt`) | rusage CPU: `[0.9964, 1.0389, 1.0111, 1.0220]` (`3/4`), `paired median 1.0165x` (`[0.9964x, 1.0389x]`), `pooled-median 1.0155x`, A/A `3.76%` (`B2/B1 = 1.0036`); Wall: `[0.9984, 1.0397, 1.0081, 1.0234]` (`3/4`), `paired median 1.0158x`, `pooled-median 1.0158x`, A/A `4.00%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / `4496 -> 4560 B` (`+64 B`) / `2704 -> 2704 B` (`+0 B`); **`nnue::v3::prepare`: `6464 -> 112 B` (`-6352 B`)** | `3601b77b9`: magnitude `+1.65%` CPU / `+1.58%` wall matched `+0.8%..+2.5%`, **KILLED** by `3.76%` `A2/A1` noise gate (`not measured`); kept in `bundle2` | **CAUGHT** (`g4_planted_fault.patch.txt`: `bench 11 = 792624 != 882074`, `g4_planted_fault_raw.txt`) |

---

## 3. Bundle 2 (`forge-combo29/carbon2/job6/bundle2.patch.txt`) vs Job 5 `bundle1`

- **Patch file:** `forge-combo29/carbon2/job6/bundle2.patch.txt` (`1,847` lines), ONE unified diff against the **Job 4 base** (`6b98f217 + pc_r15.patch + a_speed_pc20_v3.patch.txt + e1_legal_check_evasions.patch.txt`), applying cleanly with `patch -p1 --fuzz=0`.
- **Steps included (all 11 proven-identical steps from Jobs 4, 5, and 6):** `S1 + S2 + S3 + S4 + S5 + S6 + S7 + G1 + G2 + G3 + G4`.
- **Empirical work-removal check on 24-game `gprof` (`bundle1 -> bundle2`):** `corrected_eval` self time dropped `0.38s (8.07%) -> 0.29s (6.11%)` (`-23.7%`), `update_correction` `0.05s -> 0.02s`, `Board::see_ge` `0.28s (5.94%) -> 0.21s (4.42%)` (`-25.0%`), `nnue::v3::loaded()` calls `25,928,470 -> 3,397` (`-99.99%`), `nnue::v3::prepare()` calls `5,842,844 -> 3,392` (`-99.94%`), and `square_attacked_with_occupancy` calls `11,423,087 -> 10,910,991` (`-512,096` calls).
- **Pre-committed prediction:** `forge-combo29/carbon2/job6/prediction_bundle2.txt` (standalone commit **`250c9bfcf`**): predicted `+1.2%` to `+3.5%` (`1.012x` to `1.035x`) self-play `median_of_paired_round_ratios` over `bundle1` and `+1.5%` to `+4.0%` on `bench 13`; killed if `<= 1.008x` or inside the A/A build-noise spread (`not measured`).

### 3a. Bundle 2 Identity Proof, Stack Frame Sizes, and Planted-Fault Check
Raw files: `forge-combo29/carbon2/job6/bundle2_proof_and_bench13_raw.txt` and `forge-combo29/carbon2/job6/bundle2_planted_fault_raw.txt`.
- **`PC20 + net512.fnn3` (`fdff70de72e4ca82`):** `bench 11 = 625258`, `bench 13 = 3652372`, `bench 16 = 23891329` (**EXACT**), `1,000/1,000` `eval` rows **EXACT**.
- **`PC20 + net768.fnn3` (`30ab43b4ba5db5f3`):** `bench 11 = 882074`, `bench 13 = 4275906`, `bench 16 = 32374943` (**EXACT**), `250/250` depth-9 `(bestmove, nodes)` rows **EXACT**, `1,000/1,000` `eval` rows **EXACT**.
- **6-game self-play traces (`net768`):** `startpos = 4560d7c3afdeba2e` (**EXACT**), `fen = 9ed22c1193ab96de` (**EXACT**).
- **Planted fault (`bundle2.patch.txt + g4_planted_fault.patch.txt`):** **CAUGHT** (`bench 11 = 792624 != 882074`, `bundle2_planted_fault_raw.txt`).
- **Stack Frame Sizes:**
  - `bundle1 -> bundle2`: `sizeof(MovePicker): 2240 -> 2240 B (+0 B)`, `Worker::search: 4496 -> 4560 B (+64 B)`, `Worker::qsearch: 2704 -> 2704 B (+0 B)`, `nnue::v3::prepare: 6464 -> 112 B (-6352 B)`.
  - Cumulative vs **Job 4 base**: `sizeof(MovePicker): 4792 -> 2240 B (-2552 B)`, `Worker::search: 7104 -> 4560 B (-2544 B/ply, -325.6 KB over 128 plies)`, `Worker::qsearch: 5248 -> 2704 B (-2544 B/ply)`.

### 3b. Bundle 2 vs Bundle 1 Self-Play Timing (`A = bundle1`, `B = bundle2`, `A1 B1 B2 A2` x 12 Rounds x 60 Games = 48 Runs)
- **Driver:** `forge-combo29/carbon2/job5/run_bundle_selfplay_12x60.py` (60 distinct book FEN roots from `positions_250.txt` via `select_book_fens(positions_250.txt, 60)`, `go softnodes 2000`, `ucinewgame` + `isready` per game, zero untimed warmup inside any measured process).
- **Raw log (all 48 run lines + `NNUE v3 active:` lines):** `forge-combo29/carbon2/job6/bundle2_selfplay_12x60_raw.txt`.
- **Single bit-exact trace across all 48 runs (`368,160` searches, `1,230,783,168` nodes):**
  - Every one of the 48 runs produced **`searches = 7,670`**, **`nodes = 25,641,316`**, and **`fnv1a64 = ee465caeff9c0fcf`**.

| Metric (`A = bundle1`, `B = bundle2`, 12 rounds x 60 games) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..12`) | Rounds Faster | `median_of_paired_round_ratios` (`median_r(B_r/A_r)`) + 95% CI | `ratio_of_pooled_medians` (`median(B)/median(A)`) + 95% CI | A/A Control (`A2/A1`, `B2/B1`, max spread) | Verdict |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **Engine CPU (`getrusage` ns, searches/s)** | `A1=560.58`, `A2=570.02` (`A=563.58`) \| `B1=563.87`, `B2=575.88` (`B=570.62`) | `[1.0218, 1.0006, 1.0118, 0.9987, 0.9916, 1.0184, 1.0168, 0.9854, 1.0386, 1.0213, 1.0155, 1.0271]` | **`9 / 12`** | **`1.0161x` (`+1.61%`)**, 95% CI `[0.9996x, 1.0215x]` | **`1.0125x` (`+1.25%`)**, 95% CI `[0.9950x, 1.0276x]` | `A2/A1 = 1.0168` (`+1.68%`), `B2/B1 = 1.0213` (`+2.13%`), max **`2.13%`** | `not measured` (`+1.61% < 2.13%` cloud A/A spread) |
| **Wall Clock (`perf_counter_ns`, searches/s)** | `A1=510.72`, `A2=517.19` (`A=514.05`) \| `B1=513.18`, `B2=525.19` (`B=521.01`) | `[1.0196, 0.9948, 1.0022, 0.9933, 0.9939, 1.0190, 1.0115, 0.9928, 1.0254, 1.0150, 1.0225, 1.0173]` | **`8 / 12`** | **`1.0133x` (`+1.33%`)**, 95% CI `[0.9943x, 1.0193x]` | **`1.0135x` (`+1.35%`)**, 95% CI `[0.9950x, 1.0283x]` | `A2/A1 = 1.0127` (`+1.27%`), `B2/B1 = 1.0234` (`+2.34%`), max **`2.34%`** | `not measured` (`+1.33% < 2.34%` cloud A/A spread) |

### 3c. Bundle 2 vs Bundle 1 `bench 13` Timing (`A = bundle1`, `B = bundle2`, `A1 B1 B2 A2` x 4 Rounds, `net768`)
Raw file: `forge-combo29/carbon2/job6/bundle2_proof_and_bench13_raw.txt`.

| Metric (`A = bundle1`, `B = bundle2`, 4 ABBA rounds) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..4`) | Rounds Faster | `median_of_paired_round_ratios` + 95% CI | `ratio_of_pooled_medians` + 95% CI | A/A Control | Verdict |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **`bench 13` Engine CPU (`getrusage` ns, NPS)** | `A1=1,939,734`, `A2=1,847,064` (`A=1,901,998`) \| `B1=1,962,297`, `B2=1,933,138` (`B=1,955,054`) | `[1.0540, 1.0166, 1.0034, 1.0161]` | **`4 / 4`** | **`1.0163x` (`+1.63%`)**, 95% CI `[1.0034x, 1.0540x]` | **`1.0279x` (`+2.79%`)**, 95% CI `[0.9879x, 1.0515x]` | `A2/A1 = 0.9522`, `B2/B1 = 0.9851` (max `4.78%`) | `not measured` (`+1.63% < 4.78%` cloud A/A spread) |
| **`bench 13` Wall Clock (NPS)** | `A1=2,038,162`, `A2=1,942,787` (`A=1,998,095`) \| `B1=2,064,060`, `B2=2,025,547` (`B=2,060,433`) | `[1.0529, 1.0170, 0.9997, 1.0196]` | **`3 / 4`** | **`1.0183x` (`+1.83%`)**, 95% CI `[0.9997x, 1.0529x]` | **`1.0312x` (`+3.12%`)**, 95% CI `[0.9912x, 1.0537x]` | `A2/A1 = 0.9532`, `B2/B1 = 0.9813` (max `4.68%`) | `not measured` (`+1.83% < 4.68%` cloud A/A spread) |

- **Bundle 2 Prediction Verdict (`250c9bfcf`):** Point estimates matched our predicted range on every metric (`+1.61%` paired / `+1.25%` pooled self-play CPU [`9/12` faster, `B1 > A1` and `B2 > A2`], `+1.33%` paired / `+1.35%` pooled self-play wall [`8/12` faster], and `+1.63%` paired / `+2.79%` pooled `bench 13` CPU [`4/4` faster]), **but the prediction is KILLED on this cloud machine by the A/A build-spread gate** (`+1.61%` vs `2.13%` max B2/B1 code-alignment spread on non-PGO GCC -> `not measured` here; ready for the PC's PGO build to time directly against Job 4 base / `bundle1`).

---

## 4. What To Do Next With Another 90 Minutes (Ranked, With Profile Share Attacked)

1. **Incremental `Board` non-pawn keys + material key maintained in `make_move` / `unmake_move` with exact bit-identical `non_pawn_key` / `material_key` parity, OR precomputed `MovePicker` pin mask skipping `Board::is_legal` on unpinned non-king/non-EP moves (attacks `MovePicker::next` `9.26%` + `Worker::search` `21.26%` + `is_legal_complete` `1.47%` + `refresh_king_lines` `0.63%` in post-`bundle2` profile):**
   When `MovePicker` yields from `GoodCaptures` or `QuietMoves` and `!board.in_check()`, calling `ensure_king_lines()` once per node allows `MovePicker` (or `Worker::search`) to tag unpinned non-king, non-en-passant moves as `known_legal = true` (`(pinned & square_bb(from)) == 0`), skipping per-move `is_legal` branches across ~85% of yielded moves.
2. **Dirty-cluster / generation-epoch `TranspositionTable::clear()` on `ucinewgame` (attacks per-game `16 MB` TT `memset` across `60` games/run — amortized inside self-play wall/CPU time):**
   In 2,000-node self-play (~125 searches/game), a game stores at most ~100,000 TT entries out of `2,097,152` slots (`524,288` clusters in `Hash 16`). Tracking a `uint16_t clear_epoch` per cluster (or clearing only clusters touched since the previous `ucinewgame` via a compact `8 KB` dirty-page bitmap of `256-cluster` blocks) removes ~85–90% of the `16 MB` `memset` on every `ucinewgame` while remaining 100% bit-exact.
3. **Eliminate redundant `Worker::quiet_history` calls on `MainTT`, `Killer1`, `Killer2`, and `CounterMove` when `GenerateQuiets` is subsequently reached (`Worker::quiet_history` is still `2.95%` self, `6,378,939` calls in post-`bundle2` profile):**
   Of the remaining `6.38M` calls to `Worker::quiet_history`, ~5.0M are killers/countermove/TT quiet moves scored at line 2367 before `GenerateQuiets` runs, plus `MovePicker::QuietScorer` scalar fallback on `HistRework` twin blends (`rework_side`). Vectorizing the `rework_side` twin lookup inside `score_quiets` with AVX-512 `VPERMT2D` / `VGATHERDD` attacks both `MovePicker::next` (`9.26%`) and `quiet_history` (`2.95%`).

---

## 5. Timestamps, Model Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job6/stamps.txt`:**
  `Tue Nov 17 03:29:33 PM UTC 2026 | job 6 received (FABLE_TO_carbon2_6.md); job 5 bundle.patch.txt already finished and identity-proven at f81dc8bbc`
- **Last line of `forge-combo29/carbon2/job6/stamps.txt`:**
  `Tue Nov 17 04:48:11 PM UTC 2026 | writing REPORT_carbon2_job6.md after verifying all cited raw files`
- **Runtime Model Name & Version:** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job6` Immediately Before Report Commit

```text
 M forge-combo29/carbon2/job6/stamps.txt
?? forge-combo29/carbon2/job6/REPORT_carbon2_job6.md
forge-combo29/carbon2/job6:
bundle2.patch.txt
bundle2_planted_fault_raw.txt
bundle2_proof_and_bench13_raw.txt
bundle2_selfplay_12x60_raw.txt
g1_cached_material_corr_and_inline_dead_mat.patch.txt
g1_planted_fault.patch.txt
g1_planted_fault_raw.txt
g1_proof_raw.txt
g2_oracle_and_fault_raw.txt
g2_planted_fault.patch.txt
g2_proof_raw.txt
g2_see_fast_no_recapture_and_hoist_unify.patch.txt
g3_known_gives_check_kinglines_and_stalemate.patch.txt
g3_oracle_and_fault_raw.txt
g3_planted_fault.patch.txt
g3_proof_raw.txt
g4_planted_fault.patch.txt
g4_planted_fault_raw.txt
g4_proof_raw.txt
g4_snapshot_v3_net_hoist_prepare_and_king_sq.patch.txt
prediction_bundle2.txt
prediction_g1.txt
prediction_g2.txt
prediction_g3.txt
prediction_g4.txt
profile_bundle1.txt
REPORT_carbon2_job6.md
stamps.txt
step0_job6_raw.txt
test_g3_board_oracle.cpp
```
