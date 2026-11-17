# Forge (`carbon2` — Job 5 Report): Stacked Steps `S1..S7`, `-2,608 B/ply` Stack Frame Cut, and 12x60-Game Bundle Timing

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job5/`).
- **Job 4 / Job 5 Base Tree:** `6b98f217` + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` (`forge/r15c`) + `forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt` (`E1`).
- **Cloud Machine & Compiler:** `Intel(R) Xeon(R) CPU @ 2.60GHz` (x86_64, AVX-512), `g++ 13.3.0`, `-O3 -DNDEBUG -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`.
- **Context note on Job 4 continuity:** `FABLE_TO_carbon2_5.md` was written while Job 4 was at commit `fed59e36a` (`prediction_s2.txt`); Job 4 subsequently pushed `S2`, `S3`, and `REPORT_carbon2_job4.md` in `3fc56f0c8`. Here in Job 5, `S1`, `S2`, and `S3` were converted into clean zero-offset stacked diffs (`s1_stacked.patch.txt`, `s2_stacked.patch.txt`, `s3_stacked.patch.txt`), followed by four new stacked Job 5 steps (`S4`, `S5`, `S6`, `S7`), and all seven proven-identical steps (`S1..S7`) were combined into `forge-combo29/carbon2/job5/bundle.patch.txt`.

---

## 0. Step 0 Verification (Same Machine, Re-verified Today on `6b98f217 + pc_r15.patch`)

Met 100% bit-identically (`forge-combo29/carbon2/job5/step0_job5_raw.txt`, fresh engine process per line, `Threads 1`, `Hash 16`, zero `unknown option` / `invalid value` / `ERROR` lines):

| Configuration | Check | Expected | Observed (`job5/step0_job5_raw.txt`) | Status |
| :--- | :--- | ---: | ---: | :--- |
| No settings, no net | `bench 11` / `bench 13` / `bench 16` / `go perft 5` | `312866` / `862329` / `3024920` / `4865609` | `312866` / `862329` / `3024920` / `4865609` | **EXACT** |
| `PC20`, no net | `bench 11` / `bench 13` | `278024` / `587276` | `278024` / `587276` | **EXACT** |
| `net512.fnn3` only | `bench 11` / `bench 13` | `965454` / `4151906` | `965454` / `4151906` | **EXACT** |
| `PC20`, then `net512.fnn3` | `bench 11` / `bench 13` | `625258` / `3652372` | `625258` / `3652372` | **EXACT** |
| `PC20` + `net512.fnn3` `eval` | startpos / `r1bqkbnr/...` / `8/5pk1/...` | `968` / `1176` / `31` (`fdff70de72e4ca82`, `64/96/16`) | `968` / `1176` / `31` (`fdff70de72e4ca82`, `64/96/16`, `avx512`) | **EXACT** |

Note on kernel CPU clock source: `/proc/<pid>/schedstat` returns `0 0 1` on this cloud VM (`CONFIG_SCHEDSTATS` disabled), so all Job 5 proofs and the 48-run bundle timing read engine CPU time in **nanoseconds** via `os.wait4(proc.pid, 0)` (`getrusage` of the reaped child: `int(round((ru.ru_utime + ru.ru_stime) * 1e9))`), eliminating Job 4's 10 ms tick quantization.

---

## 1. Per-Step Summary Table (`E1` Stack Reference + Stacked Steps `S1..S7`)

Every stacked patch in `job5/` applies in sequence (`S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7`) on the Job 4 base with `patch -p1 --fuzz=0` and zero offset/fuzz. All stack frame sizes were measured with `g++ -O3 -march=x86-64-v4 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -fstack-usage`.

| Step | Patch File (`forge-combo29/carbon2/...`) & Touched Files/Functions | Lines | Identity (`PC20` + `net768` & `net512`: `bench 11/13/16`, `250` depth-9 rows, `1000` evals, 6-game `startpos` `4560d7c3afdeba2e` & `fen` `9ed22c1193ab96de` + unit oracle) | `bench 13` Timing (`A1 B1 B2 A2` x 4 rounds, `net768`: paired ratios, paired median, pooled ratio, A/A) | `sizeof(MovePicker)` / `Worker::search` / `Worker::qsearch` (`base -> step`) | Prediction (Commit, Met or Killed) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- | :--- |
| **`E1` (ref)** | `job3/e1_legal_check_evasions.patch.txt` (`board.hpp`, `board.cpp`, `search.cpp`: `generate_evasion_moves`, `MovePicker`) | 288 | All pins **EXACT** + `14,238` in-check `MovePicker` sequences `0` mismatches (`job3/e1_oracle_and_fault_raw.txt`) | Job 3 (`r15c -> E1`): `+14.85%` paired CPU (`4/4` faster, `MEASURED`) | `4280 -> 4792 B` (`+512 B`) / `6528 -> 7104 B` (`+576 B`) / `4752 -> 5248 B` (`+496 B`) | Job 3 **MET** | **CAUGHT** (`job3/e1_planted_fault.patch.txt`) |
| **`S1`** | `job5/s1_stacked.patch.txt` (`board.hpp`, `nnue_v3.hpp`, `nnue_v3.cpp`, `search.cpp`: `refresh_side`, `apply_single_and_evaluate`, `static_evaluate_v3`) | 315 | All pins **EXACT** + `16,000` random fused AVX-512 trials `0` mismatches (`job4/s1_proof_raw.txt`, `job4/s1_oracle_and_fault_raw.txt`) | Wall: `[1.0345, 1.0267, 1.0091, 1.0025]` (`4/4`), paired `1.0179x` (`[1.0025x, 1.0345x]`), pooled `1.0163x`, A/A `1.21%`; CPU: paired `1.0202x`, pooled `1.0228x`, A/A `1.55%` (`job4/s1_proof_raw.txt`) | `4792 -> 4792 B` (`+0 B`) / `7104 -> 7104 B` (`+0 B`) / `5248 -> 5248 B` (`+0 B`) | `45f284110`: **KILLED** on 6-game self-play (`1.0029x` vs `3.70%` A/A); kept in bundle | **CAUGHT** (`job4/s1_planted_fault.patch.txt`) |
| **`S2`** | `job5/s2_stacked.patch.txt` (`board.hpp`, `search.hpp`, `search.cpp`: `score_quiets` AVX-512 `VPERMT2D`, `Board::is_pseudo_legal`) | 195 | All pins **EXACT** + `13,868,355` `(pos, Move)` pairs `0` mismatches (`job4/s2_proof_raw.txt`, `job4/s2_oracle_and_fault_raw.txt`) | Wall: `[0.9730, 0.9973, 0.9720, 1.0088]` (`1/4`), paired `0.9852x` (`[0.9720x, 1.0088x]`), pooled `0.9808x`, A/A `0.88%` (`not measured` on `bench 13`; **6-game self-play `7/8` faster, `1.0156x` paired / `1.0215x` pooled wall, A/A `0.53%` `MEASURED`**) | `4792 -> 4808 B` (`+16 B`) / `7104 -> 7056 B` (`-48 B`) / `5248 -> 5264 B` (`+16 B`) | `fed59e36a`: **MET** on self-play (`1.0156x` wall, `1.0201x` CPU `MEASURED`) | **CAUGHT** (`job4/s2_planted_fault.patch.txt`) |
| **`S3`** | `job5/s3_stacked.patch.txt` (`search.hpp`, `search.cpp`: `prefetch_correction_tables`, `non_pawn_key` 4-way unroll) | 93 | All pins **EXACT** + `1,000` FEN x 2 color `non_pawn_key` `0` mismatches (`job4/s3_proof_raw.txt`, `job4/s3_oracle_and_fault_raw.txt`) | Wall: `[1.0038, 0.9986, 1.0303, 1.0209]` (`3/4`), paired `1.0124x` (`[0.9986x, 1.0303x]`), pooled `1.0238x`, A/A `0.57%` (`MEASURED`); CPU: paired `1.0126x`, pooled `1.0210x`, A/A `0.94%` (`MEASURED`, `job4/s3_proof_raw.txt`) | `4808 -> 4808 B` (`+0 B`) / `7056 -> 7120 B` (`+64 B`) / `5264 -> 5264 B` (`+0 B`) | `288160546`: **KILLED** on Xeon 8 MiB L2 self-play (`1.0025x`), **`bench 13` MEASURED `+1.24%`/`+2.38%`**; kept in bundle | **CAUGHT** (`job4/s3_planted_fault.patch.txt`) |
| **`S4`** | `job5/s4_slim_movepicker_and_vpermt2d_hoist.patch.txt` (`search.hpp`, `search.cpp`: `Worker::picker_scratch_`/`evasion_scratch_`, remove `legal_to_by_from_`, `FORGE_SDK_BADCAP_PREFIX=1`, guard `odd_idx16`) | 248 | All pins **EXACT** + `55,868` in-check `MovePicker` sequences `0` mismatches (`job5/s4_proof_raw.txt`, `job5/s4_oracle_and_fault_raw.txt`) | Wall: `[0.9754, 0.9948, 0.9960, 0.9844]` (`0/4`), paired `0.9896x` (`[0.9754x, 0.9960x]`), pooled `0.9903x`, A/A `3.46%` (`not measured`); rusage CPU: paired `0.9896x` (`[0.9677x, 0.9954x]`), pooled `0.9895x`, A/A `3.21%` (`not measured`) | **`4808 -> 2240 B` (`-2568 B`) / `7120 -> 4560 B` (`-2560 B`) / `5264 -> 2704 B` (`-2560 B`)** | `2ca74f9b5`: stack cut **MET** (`-2560 B/ply` vs `-1536 B` target); `bench 13` speed **KILLED** (`0.9896x` vs `3.46%` A/A); kept in bundle | **CAUGHT** (`job5/s4_planted_fault.patch.txt`) |
| **`S5`** | `job5/s5_make_move_early_key_and_slim_undo.patch.txt` (`board.hpp`, `board.cpp`, `search.cpp`: `Board::make_move(..., precomputed_key)`, conditional 72B `KingLines` copy on `Undo`) | 171 | All pins **EXACT** + `21,823` transition / `king_lines_` oracle checks `0` mismatches (`job5/s5_proof_raw.txt`, `job5/s5_oracle_and_fault_raw.txt`) | Wall: `[0.9962, 1.0288, 0.9699, 0.9931]` (`1/4`), paired `0.9946x` (`[0.9699x, 1.0288x]`), pooled `0.9926x`, A/A `4.58%` (`not measured`); rusage CPU: paired `0.9947x` (`[0.9741x, 1.0275x]`), pooled `0.9960x`, A/A `4.18%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / `4560 -> 4560 B` (`+0 B`) / `2704 -> 2704 B` (`+0 B`) | `29ecd1374`: **KILLED** (`0.9946x` vs `4.58%` A/A build noise); kept in bundle | **CAUGHT** (`job5/s5_planted_fault.patch.txt`) |
| **`S6`** | `job5/s6_see_fast_unpinned_pawn_recapture.patch.txt` (`board.cpp`: `Board::see_ge` unpinned enemy-pawn recapture fast-exit before `attackers_to_fast`) | 24 | All pins **EXACT** + `152,488` two-binary `Board::see_ge` calls across 7 thresholds `0` mismatches (`job5/s6_proof_raw.txt`, `job5/s6_oracle_and_fault_raw.txt`) | Wall: `[0.9909, 0.9987, 0.9660, 1.0027]` (`1/4`), paired `0.9948x` (`[0.9660x, 1.0027x]`), pooled `0.9850x`, A/A `0.52%`; rusage CPU: paired `0.9962x` (`[0.9697x, 1.0022x]`), pooled `0.9852x`, A/A `0.29%` | `2240 -> 2240 B` (`+0 B`) / `4560 -> 4560 B` (`+0 B`) / `2704 -> 2704 B` (`+0 B`) | `936cecff0`: **KILLED** (`0.9962x` <= `1.005x` kill bound); kept in bundle | **CAUGHT** (`job5/s6_planted_fault.patch.txt` at call `39,397` of `positions_1000.txt`) |
| **`S7`** | `job5/s7_uci_zero_alloc_and_selective_clear.patch.txt` (`search.hpp`, `search.cpp`, `uci.cpp`: `apply_position_sv`, `parse_limits_sv`, persistent `SearchTask`, dirty-tracked `Worker::clear`) | 560 | All pins **EXACT** + `146`-line differential UCI / `ThreatHistory` / `PositionCache` edge-case oracle `0` mismatches (`job5/s7_proof_raw.txt`, `job5/s7_oracle_and_fault_raw.txt`) | Wall: `[0.9941, 1.0298, 1.0305, 1.0010]` (`3/4`), paired `1.0154x` (`[0.9941x, 1.0305x]`), pooled `1.0203x`, A/A `2.20%` (`not measured`); rusage CPU: `[0.9912, 1.0251, 1.0290, 0.9983]` (`2/4`), paired `1.0117x` (`[0.9912x, 1.0290x]`), pooled `1.0138x`, A/A `2.07%` (`not measured`) | `2240 -> 2240 B` (`+0 B`) / **`4560 -> 4496 B` (`-64 B`)** / `2704 -> 2704 B` (`+0 B`) | `f30d94af0`: `bench 13` direction positive (`+1.54%` wall / `+1.17%` CPU) but **KILLED** as standalone `bench 13` claim by `2.07%` B2/B1 A/A spread; kept in bundle for 60-game self-play | **CAUGHT** (`job5/s7_planted_fault.patch.txt` on `moves e2e4q`) |

### Stack Headroom Note on Windows 11 (1 MB Search Thread Stack)
- `E1` had grown `sizeof(MovePicker)` from `4,280 B` (`r15c`) to `4,792 B` (`+512 B` for `legal_to_by_from_[64]`), pushing GCC's `Worker::search` recursive frame from `6,528 B` to `7,104 B` (`128 * 7,104 B = 909.3 KB`, perilously close to Windows's `1,048 KB` thread stack).
- `S4 + S7` moves `MovePicker::buffer_` + `non_tt` scratch onto `Worker::picker_scratch_` / `Worker::evasion_scratch_`, removes `legal_to_by_from_[64]` (`512 B`) via `Move::none()` tagging on illegal tie-path evasions, and flips `FORGE_SDK_BADCAP_PREFIX=1` (`-1,024 B`), cutting **`sizeof(MovePicker)` from `4,792 B -> 2,240 B` (`-2,552 B`)**, **`Worker::search` from `7,104 B -> 4,496 B` (`-2,608 B/ply`, `-333.8 KB` across 128 plies -> `575.5 KB` worst-case 128-ply stack)**, and **`Worker::qsearch` from `5,248 B -> 2,704 B` (`-2,544 B/ply`)** — **`2,032 B/ply` smaller than even pre-`E1` `forge/r15c`**.

---

## 2. The Bundle (`forge-combo29/carbon2/job5/bundle.patch.txt`)

- **Patch file:** `forge-combo29/carbon2/job5/bundle.patch.txt` (`1,475` lines), ONE unified diff against the Job 4 base (`6b98f217 + pc_r15.patch + a_speed_pc20_v3.patch.txt + e1_legal_check_evasions.patch.txt`), applying cleanly with `patch -p1 --fuzz=0`.
- **Included steps (all 7 proven-identical steps):** `S1 + S2 + S3 + S4 + S5 + S6 + S7`.
- **Pre-committed bundle prediction:** `forge-combo29/carbon2/job5/prediction_bundle.txt` (standalone commit **`9ffdd50f4`**, committed before any bundle build or timed run): predicted **`+2.5%` to `+5.5%` (`1.025x` to `1.055x`)** self-play gain and **`+2.0%` to `+5.0%` (`1.020x` to `1.050x`)** `bench 13` gain; killed if self-play `median_of_paired_round_ratios <= 1.015x` or inside A/A spread.

### 2a. Bundle Identity Proof, Stack Frame Sizes, and Planted-Fault Check
Raw files: `forge-combo29/carbon2/job5/bundle_proof_and_bench13_raw.txt` and `forge-combo29/carbon2/job5/bundle_planted_fault_raw.txt`.
- **`PC20 + net512.fnn3` (`fdff70de72e4ca82`):** `bench 11 = 625258`, `bench 13 = 3652372`, `bench 16 = 23891329` (**EXACT**), `1,000/1,000` `eval` rows **EXACT**.
- **`PC20 + net768.fnn3` (`30ab43b4ba5db5f3`):** `bench 11 = 882074`, `bench 13 = 4275906`, `bench 16 = 32374943` (**EXACT**), `250/250` depth-9 `(bestmove, nodes)` rows **EXACT**, `1,000/1,000` `eval` rows **EXACT**.
- **6-game self-play traces (`net768`):** `startpos = 4560d7c3afdeba2e` (**EXACT**), `fen = 9ed22c1193ab96de` (**EXACT**).
- **146-line UCI differential oracle vs Job 4 base:** `146/146` lines **EXACT**; planted fault (`s7_planted_fault.patch.txt` on top of `bundle.patch.txt`) **CAUGHT** at line 102 (`bundle_planted_fault_raw.txt`).
- **Bundle Stack Frame Sizes (`Job 4 base -> Bundle`):**
  - `sizeof(MovePicker)`: **`4,792 -> 2,240 bytes` (`-2,552 B`)**
  - `Worker::search` frame: **`7,104 -> 4,496 bytes` (`-2,608 B`)**
  - `Worker::qsearch` frame: **`5,248 -> 2,704 bytes` (`-2,544 B`)**

### 2b. Bundle Self-Play Timing vs Job 4 Base (`A1 B1 B2 A2` x 12 Rounds x 60 Games = 48 Runs)
- **Driver:** `forge-combo29/carbon2/job5/run_bundle_selfplay_12x60.py`
- **Raw log (every run's line + `NNUE v3 active:` confirmation):** `forge-combo29/carbon2/job5/bundle_selfplay_12x60_raw.txt`
- **Workload:** **60 distinct book FEN roots** per run selected deterministically via `select_book_fens(positions_250.txt, 60)` (60 distinct early-game roots with `>= 26` pieces from `positions_250.txt`), up to 300 plies per game at `go softnodes 2000`, `ucinewgame` + `isready` before each game, zero untimed warmup inside any measured child process.
- **Single bit-exact trace across all 48 runs (`368,160` total searches, `1,230,783,168` total nodes):**
  - Every single one of the 48 runs (`A1`, `B1`, `B2`, `A2` across rounds `01..12`) produced **`searches = 7,670`**, **`nodes = 25,641,316`**, and **`fnv1a64 = ee465caeff9c0fcf`**.

| Metric (`PC20 + net768`, 12 rounds x 60 games) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..12`) | Rounds Faster | `median_of_paired_round_ratios` (`median_r(B_r/A_r)`) + 95% CI | `ratio_of_pooled_medians` (`median(B)/median(A)`) + 95% CI | A/A Control (`A2/A1`, `B2/B1`, max spread) | Verdict |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **Engine CPU (`getrusage` ns, searches/s)** | `A1=538.80`, `A2=538.75` (`A=538.80`) \| `B1=559.48`, `B2=557.26` (`B=558.50`) | `[1.0406, 1.0348, 1.0317, 1.0540, 1.0227, 1.0376, 1.0618, 1.0335, 1.0214, 1.0277, 1.0380, 1.0097]` | **`12 / 12`** | **`1.0342x` (`+3.42%`)**, 95% CI **`[1.0252x, 1.0393x]`** | **`1.0366x` (`+3.66%`)**, 95% CI **`[1.0250x, 1.0481x]`** | `A2/A1 = 0.9999` (`-0.01%`), `B2/B1 = 0.9960` (`-0.40%`), max **`0.40%`** | **`MEASURED` (8.5x A/A floor)** |
| **Wall Clock (`perf_counter_ns`, searches/s)** | `A1=494.62`, `A2=492.32` (`A=494.15`) \| `B1=509.37`, `B2=510.31` (`B=509.63`) | `[1.0338, 1.0288, 1.0241, 1.0496, 1.0195, 1.0286, 1.0530, 1.0243, 1.0210, 1.0245, 1.0368, 1.0149]` | **`12 / 12`** | **`1.0266x` (`+2.66%`)**, 95% CI **`[1.0225x, 1.0353x]`** | **`1.0313x` (`+3.13%`)**, 95% CI **`[1.0232x, 1.0433x]`** | `A2/A1 = 0.9954` (`-0.46%`), `B2/B1 = 1.0018` (`+0.18%`), max **`0.46%`** | **`MEASURED` (5.8x A/A floor)** |

### 2c. Bundle `bench 13` Timing vs Job 4 Base (`A1 B1 B2 A2` x 4 Rounds, `net768`)
Raw file: `forge-combo29/carbon2/job5/bundle_proof_and_bench13_raw.txt`.

| Metric (`PC20 + net768`, 4 ABBA rounds) | Build Medians (`A1`, `A2` -> pooled `A` vs `B1`, `B2` -> pooled `B`) | Paired Round Ratios (`r = 1..4`) | Rounds Faster | `median_of_paired_round_ratios` + 95% CI | `ratio_of_pooled_medians` + 95% CI | A/A Control | Verdict |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **`bench 13` Engine CPU (`getrusage` ns, NPS)** | `A1=1,848,411`, `A2=1,821,659` (`A=1,848,411`) \| `B1=1,922,153`, `B2=1,899,984` (`B=1,922,153`) | `[1.0750, 1.0108, 1.0188, 1.0516]` | **`4 / 4`** | **`1.0352x` (`+3.52%`)**, 95% CI **`[1.0108x, 1.0750x]`** | **`1.0399x` (`+3.99%`)**, 95% CI `[0.9994x, 1.0725x]` | `A2/A1 = 0.9855`, `B2/B1 = 0.9885` (max `1.45%`) | **`MEASURED`** |
| **`bench 13` Wall Clock (NPS)** | `A1=1,935,363`, `A2=1,908,705` (`A=1,935,363`) \| `B1=2,026,245`, `B2=1,993,653` (`B=2,026,245`) | `[1.0769, 1.0114, 1.0246, 1.0532]` | **`4 / 4`** | **`1.0389x` (`+3.89%`)**, 95% CI **`[1.0114x, 1.0769x]`** | **`1.0470x` (`+4.70%`)**, 95% CI `[1.0017x, 1.0762x]` | `A2/A1 = 0.9862`, `B2/B1 = 0.9839` (max `1.61%`) | **`MEASURED`** |

- **Bundle Prediction Verdict (`9ffdd50f4`):** **MET** on both self-play (`+3.42%` paired CPU / `+2.66%` paired wall vs `+2.5%..+5.5%` predicted, `12/12` rounds faster, 95% CIs strictly above `1.022x`, A/A `<= 0.46%`) and `bench 13` (`+3.52%` paired CPU / `+3.89%` paired wall vs `+2.0%..+5.0%` predicted, `4/4` rounds faster).

---

## 3. What To Do Next With Another 90 Minutes (Ranked, With Profile Share Attacked)

1. **Epoch-stamped O(1) `TranspositionTable::clear()` for `ucinewgame` (attacks 16 MB x 16 workers = `256 MB` of L3-evicting `memset` per self-play game cycle; ~`3–6%` of 16-process self-play time on Ryzen 7 9850X3D's 96 MB 3D V-Cache):**
   With `S7` skipping unused v1/threat tables in `Worker::clear()`, the remaining per-game `ucinewgame` memory sweep is `shared_.tt.clear()` (`16 MB` per process) plus `continuation_history_` (`1.38 MB`). On the PC's 16 concurrent self-play processes (~40 finished games/sec total), zeroing `16 MB` per new game writes **`~640 MB/s` of zeros** across the shared 96 MB L3 cache. Storing a `uint16_t clear_epoch` per `TTCluster` (in existing padding or high generation bits, or page-dirty tracking of written clusters when a 2,000-node x 125-move game touches only a fraction of the `524,288` clusters) can make `ucinewgame` clear only touched clusters while staying 100% bit-exact.
2. **Vectorized legal quiet move generation (`generate_quiet_moves` + `Board::is_legal` pin-mask prefilter — attacks `12.69% + 4.92% = 17.61%` of post-`E1` engine samples in `job4/base_r15c_e1_profile.txt`):**
   Precomputing `ensure_king_lines()` once when `MovePicker` enters `GenerateQuiets` lets non-king, non-en-passant quiet moves of unpinned pieces (`(from_bb & pinned) == 0`) skip `Board::is_legal()` entirely in the search loop (`is_legal` is guaranteed `true` when `!in_check && piece != King && !is_ep && !(pinned & square_bb(from))`), saving ~85% of quiet `is_legal` calls with bit-exact move order.
3. **Incremental `Board` non-pawn Zobrist keys (`np_key_[2]`) wired directly into `adjust_static_eval` under a default-on bit-exact collision-free replacement or tuned `ZobristNonPawnCorr` match gate (attacks `~4.6%` of remaining `adjust_static_eval` / `non_pawn_key` samples):**
   Job 3's default-off `E3` (`ZobristNonPawnCorr`) eliminates `non_pawn_key()` scanning completely at `O(1)` XOR cost in `make_move`; running a fastchess `50,000`-node gate on the PC can promote it if Elo-neutral/positive.

---

## 4. Timestamps, Model Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job5/stamps.txt`:**
  `Tue Nov 17 01:58:41 PM UTC 2026 | job 5 received (FABLE_TO_carbon2_5.md); initializing job5 workspace and stack-usage checks`
- **Last line of `forge-combo29/carbon2/job5/stamps.txt`:**
  `Tue Nov 17 03:21:26 PM UTC 2026 | writing REPORT_carbon2_job5.md after verifying all raw outputs`
- **Runtime Model Name & Version:** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job5` Immediately Before Report Commit

```text
 M forge-combo29/carbon2/job5/stamps.txt
?? forge-combo29/carbon2/job5/REPORT_carbon2_job5.md
forge-combo29/carbon2/job5:
bundle.patch.txt
bundle_planted_fault_raw.txt
bundle_proof_and_bench13_raw.txt
bundle_selfplay_12x60_raw.txt
prediction_bundle.txt
prediction_s4.txt
prediction_s5.txt
prediction_s6.txt
prediction_s7.txt
prove_step_j5.py
REPORT_carbon2_job5.md
run_bundle_selfplay_12x60.py
s1_stacked.patch.txt
s2_stacked.patch.txt
s3_stacked.patch.txt
s4_oracle_and_fault_raw.txt
s4_planted_fault.patch.txt
s4_proof_raw.txt
s4_slim_movepicker_and_vpermt2d_hoist.patch.txt
s5_make_move_early_key_and_slim_undo.patch.txt
s5_oracle_and_fault_raw.txt
s5_planted_fault.patch.txt
s5_proof_raw.txt
s6_oracle_and_fault_raw.txt
s6_planted_fault.patch.txt
s6_proof_raw.txt
s6_see_fast_unpinned_pawn_recapture.patch.txt
s7_oracle_and_fault_raw.txt
s7_planted_fault.patch.txt
s7_proof_raw.txt
s7_uci_zero_alloc_and_selective_clear.patch.txt
stamps.txt
step0_job5_raw.txt
test_s5_make_move_oracle.cpp
test_s6_see_oracle.cpp
test_s7_uci_oracle.py
```
