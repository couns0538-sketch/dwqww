# REPORT: carbon2 — Job 2

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; no engine source files modified in-tree; all Job 2 files are text-only under `forge-combo29/carbon2/job2/`). Note: Job 1's `REPORT_carbon2_job1.md` and the `git rm` removal of `__pycache__/selfplay_driver.cpython-312.pyc` were already committed and pushed in commit `779730333` before Job 2 began.
- **Stacking order:** Every piece `Pk` (`P1` through `P6`) is a clean unified diff applying with `patch -p1 --fuzz=0` onto `6b98f217` (`forge-combo29`) + `pc_r15.patch` + `P1 .. P(k-1)`.

---

## 0. Step 0: Same Machine and Builds as Job 1 (Re-Verified Today)

Machine: `Intel(R) Xeon(R) Processor` (4 vCPUs, AVX-512 enabled, `-march=x86-64-v4`, `g++ 13.3.0 -O3 -ffp-contract=off -fno-fast-math`). Fresh single-process runs re-executed in Job 2 (`forge-combo29/carbon2/job2/step0_job2_raw.txt`):

1. **No settings, no net:** `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
2. **PC20, no net:** `bench 11 -> 278024`, `bench 13 -> 587276`
3. **512 test net only (`net512.fnn3`, checksum `fdff70de72e4ca82`):** `bench 11 -> 965454`, `bench 13 -> 4151906`
4. **PC20, then 512 test net:** `bench 11 -> 625258`, `bench 13 -> 3652372`; `eval` on startpos / Ruy Lopez / rook endgame -> `nnue 968` / `nnue 1176` / `nnue 31`

Committed 1,000-position baseline `eval` row files for `positions_1000.txt`: `job2/eval_1000_net768_rows.txt` and `job2/eval_1000_net512_rows.txt`.

---

## 1. Stacked Pieces (`P1` .. `P6`), Proofs, Gains, and Safety Tests

All timing runs in `prove_piece.py` used `selfplay_driver_v2.py` in **FEN-root mode** (`position fen <book position> moves <all moves so far>` + `go softnodes 2000`, 6 games = `745` searches / `2,481,101` nodes per run, `PC20` + **768** net `net768.fnn3`, logging `NNUE v3 active:` and post-setup `eval` in every run), 2 independent builds per side in strict **`A1 B1 B2 A2`** order across **8 rounds** (16 runs/side), recording both wall time and engine process CPU time (`utime + stime` from `/proc/<pid>/stat`), plus 4 `A1 B1 B2 A2` rounds on `bench 13` (`4,275,906` nodes). Across the full stack `base -> P1..P6`, total 16-run self-play engine CPU time dropped from **`28,530 ms` (`A` of P1) to `22,700 ms` (`B` of P6) = `1.2568x` (`+25.68%`)**.

| Piece (touched files & functions) | Patch file | Lines | Identity (what was compared, on how many positions, equal or not) | Gain (paired ratio/round, rounds faster, median w/ 95% CI, A/A control, engine CPU time) | Safety test and its planted fault (caught or not) |
| :--- | :--- | ---: | :--- | :--- | :--- |
| **P1: Persistent UCI search thread** (`src/uci.cpp`: `uci_loop`, `stop_search`, `WorkerShutdownGuard`) | `job2/p1_persistent_uci_thread.patch.txt` (raw: `p1_proof_raw.txt`) | 148 | **100% EQUAL** vs base: `bench 11/13/16` under PC20 + **768** (`882074` / `4275906` / `32374943`) & **512** (`625258` / `3652372` / `23891329`); **250** positions at `depth 9` (move, nodes, score, `hashfull`); **1,000** `eval` rows on `positions_1000.txt` (768 & 512); 6-game `startpos` trace (`4560d7c3afdeba2e`, 846 searches) & 6-game `positions_250.txt` FEN-root trace (`9ed22c1193ab96de`, 745 searches). | **Self-play (`A = base`, `B = base+P1`, MEASURED):**<br>- **Engine CPU s/s:** paired `[1.1239, 1.1707, 1.1245, 1.2078, 1.1947, 1.2099, 1.1291, 1.1769]`, **`8/8` faster**, median **`1.1672x` (`+16.72%`), 95% CI `[1.1381x, 1.2060x]`**, A/A `A2/A1=1.0169`, `B2/B1=1.0099` (max spread `1.69%`). Total engine CPU (16 runs): `28,530 ms -> 24,450 ms` (`1.1669x`).<br>- **Wall s/s:** paired `[1.1130 .. 1.1985]`, **`8/8` faster**, median **`1.1648x` (`+16.48%`), 95% CI `[1.1263x, 1.1934x]`**, A/A `1.0227 / 1.0111`.<br>- `bench 13`: `0.9943x` cpu (`not measured`, expected 0 effect). | `job2/test_p1_uci_stress.py` (`p1_stress_raw.txt`): normal Release **AND** `-fsanitize=thread` (TSan), `Threads 1` & `Threads 4`: `go infinite->stop`, clocked & unclocked `go ponder->ponderhit->stop`, mid-search `isready`/`setoption`/`ucinewgame`/`quit`, and 1,000 fast `position + go softnodes 200` cycles w/ random `stop` every 3rd (`1007/1007` `bestmove`s, `0` TSan reports, `0` hangs).<br>**Planted fault** (`p1_planted_fault.patch.txt`: omit `done_cv.notify_all()`): **CAUGHT (FAILED w/ 2.0s `TimeoutError`)**. |
| **P2: Incremental `PositionCache` + direct $O(1)$ `parse_uci`** (`src/uci.cpp`: `PositionCache`, `apply_position`, `uci_loop`; `src/board.cpp`: `Board::parse_uci`) | `job2/p2_position_cache_and_parse_uci.patch.txt` (raw: `p2_proof_raw.txt`) | 181 | **100% EQUAL** vs P1 across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows, **1,000** `eval` rows (768 & 512), 6-game `startpos` trace (`4560d7c3afdeba2e`), and 6-game FEN-root trace (`9ed22c1193ab96de`). | **Self-play (`A = P1`, `B = P1+P2`, MEASURED):**<br>- **Engine CPU s/s:** paired `[1.0567, 1.0434, 1.0441, 1.0527, 1.0256, 1.1298, 0.9621, 0.9846]`, **`6/8` faster**, median **`1.0391x` (`+3.91%`), 95% CI `[1.0000x, 1.0596x]`**, A/A `A2/A1=0.9906`, `B2/B1=1.0032` (max spread `0.94%` < half of `3.91%`). Total engine CPU: `25,710 ms -> 24,820 ms` (`1.0359x`).<br>- **Wall s/s:** paired `[1.0479 .. 0.9820]`, **`6/8` faster**, median **`1.0260x` (`+2.60%`), 95% CI `[1.0004x, 1.0519x]`**, A/A `0.9973 / 1.0052` (max spread `0.52%`, **MEASURED**).<br>- `bench 13`: `not measured` (`3.62%` A/A spread). | `job2/test_p2_parse_and_cache.cpp` (`p2_property_and_parse_raw.txt`): (c) **1,000** random sequences (`8,408` stateful `position` commands: `1,082` extend, `1,066` repeat, `921` shorter, `877` same-len diff, `1,065` diff-root same-moves, `1,039` mid-list illegal token, `1,021` `ucinewgame`, `7,688` FEN roots) verified after every command vs fresh oracle + **100** fresh OS processes (`0` mismatches); (d) `parse_uci` vs old oracle on all `21,832` legal moves of `positions_1000.txt` (+4 edge FENs) & `85,340` malformed/random tokens (`e7e8`, `e1e2q`, `e7e8k`, illegal castle, ep-less diagonal pawn, `from==to`, out-of-range; `0` mismatches).<br>**Planted fault** (`p2_planted_fault.patch.txt`: omit `std::equal` prefix check): **CAUGHT at `seq=0 step=1`**. |
| **P3: Once-per-search setup** (`include/forge/search.hpp`, `src/search.cpp`: `ExclusiveLease` `stripes_dirty_` fast path, $O(1)$ `sample_gen_counts_` `hashfull()`, buffered `emit()`, bounded `stack_dirty_limit_`; `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`: 136-byte `WorkerState::valid_flags`) | `job2/p3_per_search_setup.patch.txt` (raw: `p3_proof_raw.txt`) | 411 | **100% EQUAL** vs P2 across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows (including exact `hashfull` values), **1,000** `eval` rows (768 & 512), 6-game `startpos` trace (`4560d7c3afdeba2e`), and 6-game FEN-root trace (`9ed22c1193ab96de`). | **Self-play (`A = P1..P2`, `B = P1..P3`, `not measured` due to A/A build spread):**<br>- **Engine CPU s/s:** paired `[1.0097, 1.0455, 1.0100, 1.0252, 1.0129, 1.0498, 1.1402, 1.0278]`, **`8/8` faster**, median `1.0346x` (`+3.46%`), 95% CI `[1.0062x, 1.0633x]`, but A/A `A2/A1=1.0309`, `B2/B1=1.0063` (spread `3.09%` -> **not measured**). Total engine CPU: `26,700 ms -> 25,640 ms` (`1.0413x`).<br>- **Wall s/s:** `7/8` faster, median `1.0235x`, 95% CI `[1.0071x, 1.0438x]`, A/A `1.0157 / 1.0056` (**not measured**).<br>- `bench 13`: `0.9999x` (**not measured**). | `job2/test_p3_setup_safety.cpp` (`p3_safety_raw.txt`): compiled under **TSan (`-fsanitize=thread`)**, runs 80 consecutive searches on 1 MB hash (wrapping 5-bit `generation_` 2.5x) across `Threads 1 <-> Threads 4` (`stripes_dirty_` + `ExclusiveLease`), `clear_hash()`, and `resize_hash()`, verifying `hashfull()` == brute-force 1,000-cluster scan at every step (`0` mismatches, `0` TSan races).<br>**Planted fault** (`p3_planted_fault.patch.txt`: omit occupied `fetch_sub` on overwrite): **CAUGHT at `step=0` (`fast=13 != brute_force=10`)**. |
| **P4: Non-polluting bitboard `Board::has_legal_move()`** (`src/board.cpp`: `single_blockers`, `Board::has_legal_move`) | `job2/p4_fast_has_legal_move.patch.txt` (raw: `p4_proof_raw.txt`) | 92 | **100% EQUAL** vs P3 across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows, **1,000** `eval` rows (768 & 512), 6-game `startpos` trace (`4560d7c3afdeba2e`), and 6-game FEN-root trace (`9ed22c1193ab96de`). | **Self-play (`A = P1..P3`, `B = P1..P4`, `not measured` due to `A2/A1` build alignment spread):**<br>- **Engine CPU s/s:** paired `[1.0267, 1.0335, 1.1018, 1.0528, 1.0492, 1.0031, 1.0176, 1.0158]`, **`8/8` faster**, median `1.0306x` (`+3.06%`), 95% CI `[1.0000x, 1.0708x]`, A/A `A2/A1=1.0609`, `B2/B1=0.9833` (**not measured**). Total engine CPU: `24,550 ms -> 23,640 ms` (`1.0385x`).<br>- **Wall s/s:** **`8/8` faster**, median `1.0171x`, 95% CI `[0.9983x, 1.0615x]` (**not measured**).<br>- `bench 13`: `0.9963x` (**not measured**). | `job2/test_p4_has_legal_move.cpp` (`p4_safety_raw.txt`): compares `has_legal_move()` vs `!legal_moves().empty()` across **`115,956` positions** (`positions_1000.txt` + all depth-1 & sampled depth-2 children + `107` terminal checkmates/stalemates including pinned-piece stalemates, along-pin sole moves, and ep pins; `0` mismatches).<br>**Planted fault** (`p4_planted_fault.patch.txt`: omit `& ~pinned` on `Knight`): **CAUGHT (`fast=1 != ref=0` on pinned-knight stalemate)**. |
| **P5: NNUE v3 AVX-512/AVX2 kernels & lazy diff** (`include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`: register-reduced 2x-unrolled `output_sum`, branch-free `count=2/3` `apply_changes_pair`, fused `apply_pair_and_evaluate`, 4-col batched `refresh_from_pieces`; `src/search.cpp`: `record_move` lazy diff, `static_evaluate_v3`) | `job2/p5_nnue_v3_kernels.patch.txt` (raw: `p5_proof_raw.txt`) | 476 | **100% EQUAL** vs P4 across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows, **1,000** `eval` rows (768 & 512), 6-game `startpos` trace (`4560d7c3afdeba2e`), and 6-game FEN-root trace (`9ed22c1193ab96de`). | **Deep search `bench 13` (`A = P1..P4`, `B = P1..P5`, MEASURED):**<br>- **Engine CPU nps:** paired `[1.0397, 1.0193, 1.0221, 1.0140]`, **`4/4` faster**, median **`1.0356x` (`+3.56%`), 95% CI `[1.0059x, 1.0499x]`**, A/A `A2/A1=1.0135`, `B2/B1=1.0039` (spread `1.35%` -> **MEASURED**; wall **`1.0324x`**, CI `[1.0068x, 1.0510x]`, **MEASURED**).<br>**Self-play (warm TT -> fewer fresh NNUE evals):** wall `0.9941x` (`not measured`), cpu `0.9862x`, CI `[0.9600x, 1.0213x]` (`23,240 -> 23,430 ms`, neutral within cloud noise). | `job2/test_p5_nnue_kernels.cpp` (`p5_safety_raw.txt`): checks `Scalar == Avx2 == Avx512`, fused `apply_pair_and_evaluate`, and batched refresh vs `evaluate_reference` across `22,825` positions (`19,050` fused pair evals, including ep & castling) + worst-case loader-bound saturation (`hidden=1024`, all units `255`, `w2=+-127`: zero `int32` overflow; `0` mismatches).<br>**Planted fault** (`p5_planted_fault.patch.txt`: swap `w2` `us/them` perspective): **CAUGHT on first move (`got=2003 != ref=239`)**. |
| **P6: PC20 search hotpaths** (`include/forge/search.hpp`, `src/search.cpp`: inline non-cold `search_child`/`qsearch_child`, remove inverted `[[unlikely]]`s on B4, hoisted single-load `QuietScorer` & `quiet_history`, `SearchStack` `corr_valid` non-pawn/material cache) | `job2/p6_pc20_search_hotpaths.patch.txt` (raw: `p6_proof_raw.txt`) | 348 | **100% EQUAL** vs P5 across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows, **1,000** `eval` rows (768 & 512), 6-game `startpos` trace (`4560d7c3afdeba2e`), and 6-game FEN-root trace (`9ed22c1193ab96de`). | **Self-play (`A = P1..P5`, `B = P1..P6`, MEASURED):**<br>- **Wall s/s:** paired `[1.0672, 1.0687, 1.0781, 1.0022, 1.0264, 1.0841, 0.9760, 0.9924]`, **`6/8` faster**, median **`1.0248x` (`+2.48%`), 95% CI `[1.0015x, 1.0896x]`**, A/A `A2/A1=1.0100`, `B2/B1=0.9903` (spread `1.00%` < half of `2.48%` -> **MEASURED**).<br>- **Engine CPU s/s:** paired `[1.0771 .. 0.9757]`, **`6/8` faster**, median **`1.0214x` (`+2.14%`), 95% CI `[0.9930x, 1.0961x]`**, A/A `1.0069 / 0.9963` (spread `0.69%` -> **MEASURED**). Total engine CPU: `23,480 ms -> 22,700 ms` (`1.0344x`).<br>- `bench 13`: `4/4` faster (`+3.05%` wall / `+2.84%` cpu, `not measured` vs `3.1%` A/A). | `job2/test_p6_pc20_safety.cpp` (`p6_safety_raw.txt`): injects per-evaluation runtime assertions inside `corrected_eval` verifying `ss->corr_np_idx[White/Black]` == fresh `non_pawn_key` and `ss->corr_mat_mix` == fresh `b4::joint_key` across `81,830` promotion/underpromotion/capture/null-move tactical nodes (`0` mismatches).<br>**Planted fault** (`p6_planted_fault.patch.txt`: omit `move.is_promotion()` invalidation): **CAUGHT immediately (`CORR_NP_CACHE MISMATCH`)**. |

---

## 2. What We Would Do Next With Another 90 Minutes (Ranked)

1. **Test `P1` + `P2` + `P3` + `P4` + `P6` + `P5` directly under the PC's Clang 23.1.5 ThinLTO + PGO `znver5` build:** On Windows 11 with 16 concurrent processes at 5,000 `go softnodes 2000`/s, `P1` avoids Win32 `CreateThread` + `DLL_THREAD_ATTACH`/`DETACH` loader-lock contention across 16 processes, and `P3`/`P4`/`P6` should register cleanly once cloud A/A variance (`3–6%` vs the PC's `<=1.5%`) is gone; `P5` specifically accelerates the 50k/250k match gate where TT eval hit rates drop and 768-wide NNUE dominates.
2. **Bit-exact legal check-evasion generator (Deliverable A piece `P7`, ~+6–9% pure search speed):** `MovePicker::generate_evasions()` still generates, scores, and sorts ~34.5 pseudo-legal moves per in-check node for ~2.2 legal moves (~9.5% of search CPU). Preserving `MovePicker::pick_best()`'s exact 4-slot selection/introsort tie boundary when `count > 4` (or match-testing Job 1's `FastLegalEvasions` UCI option on the PC, which already measured `+17.8%` `bench 13` nps) unlocks the single largest remaining search speedup.
3. **Single-instruction Zen 5 AVX-512 VNNI `_mm512_dpwssd_epi32` in `output_sum_avx512` & `apply_pair_and_sum_avx512`:** Because `|a * w2| <= 255 * 127 = 32,385 <= 32,767` fits signed `int16` without overflow and `a in [0, 255]` fits signed `int16`, `_mm512_dpwssd_epi32(sum, _mm512_mullo_epi16(a, w), a)` is 100% bit-exact with `_mm512_add_epi32(sum, _mm512_madd_epi16(_mm512_mullo_epi16(a, w), a))` while fusing `vpmaddwd` + `vpaddd` into one instruction on Zen 5.
4. **Match-test Job 1's `NoisyHistoryLmr` (`b_strength_bundle.patch.txt`) at 2,000 and 50,000 nodes with the PC's 768 net.**

---

## 3. Times, Runtime Model, and Pre-Commit Status

- **First line of `forge-combo29/carbon2/job2/stamps.txt`:**
  `Tue Nov 17 11:00:19 AM UTC 2026 | job 2 received (FABLE_TO_carbon2_2.md) and job2 directory initialized`
- **Last line of `forge-combo29/carbon2/job2/stamps.txt`:**
  `Tue Nov 17 12:02:03 PM UTC 2026 | writing REPORT_carbon2_job2.md after reading all P1..P6 proof and safety files`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job2` before report commit

```text
$ git status --short
 M forge-combo29/carbon2/job2/stamps.txt
?? forge-combo29/carbon2/job2/REPORT_carbon2_job2.md
?? forge-combo29/carbon2/job2/p5_nnue_v3_kernels.patch.txt
?? forge-combo29/carbon2/job2/p5_planted_fault.patch.txt
?? forge-combo29/carbon2/job2/p5_proof_raw.txt
?? forge-combo29/carbon2/job2/p5_safety_raw.txt
?? forge-combo29/carbon2/job2/p6_pc20_search_hotpaths.patch.txt
?? forge-combo29/carbon2/job2/p6_planted_fault.patch.txt
?? forge-combo29/carbon2/job2/p6_proof_raw.txt
?? forge-combo29/carbon2/job2/p6_safety_raw.txt
?? forge-combo29/carbon2/job2/test_p5_nnue_kernels.cpp
?? forge-combo29/carbon2/job2/test_p6_pc20_safety.cpp

$ ls -R forge-combo29/carbon2/job2
forge-combo29/carbon2/job2:
eval_1000_net512_rows.txt
eval_1000_net768_rows.txt
p1_persistent_uci_thread.patch.txt
p1_planted_fault.patch.txt
p1_proof_raw.txt
p1_stress_raw.txt
p2_planted_fault.patch.txt
p2_position_cache_and_parse_uci.patch.txt
p2_proof_raw.txt
p2_property_and_parse_raw.txt
p3_per_search_setup.patch.txt
p3_planted_fault.patch.txt
p3_proof_raw.txt
p3_safety_raw.txt
p4_fast_has_legal_move.patch.txt
p4_planted_fault.patch.txt
p4_proof_raw.txt
p4_safety_raw.txt
p5_nnue_v3_kernels.patch.txt
p5_planted_fault.patch.txt
p5_proof_raw.txt
p5_safety_raw.txt
p6_pc20_search_hotpaths.patch.txt
p6_planted_fault.patch.txt
p6_proof_raw.txt
p6_safety_raw.txt
prove_piece.py
REPORT_carbon2_job2.md
selfplay_driver_v2.py
stamps.txt
step0_job2_raw.txt
test_p1_uci_stress.py
test_p2_parse_and_cache.cpp
test_p3_setup_safety.cpp
test_p4_has_legal_move.cpp
test_p5_nnue_kernels.cpp
test_p6_pc20_safety.cpp
```
