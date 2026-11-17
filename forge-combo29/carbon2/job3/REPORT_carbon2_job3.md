# REPORT: carbon2 — Job 3

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; no engine source files modified in-tree; all Job 3 files are text-only under `forge-combo29/carbon2/job3/`).
- **Base tree (`forge/r15c`):** `6b98f217` (`forge-combo29`) + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` exactly as committed in Job 1. Every step (`E1`, `E2` on `base + E1`, and optional `E3` on `base + E1 + E2`) applies with `patch -p1 --fuzz=0`.

---

## 0. Answers to the Two Questions, Step 0, and `nproc` / `lscpu`

### Answer to Question 1 (`parse_uci` `Promotion` flag on castling / en-passant candidates in Job 2 `P2` vs Job 1)
**Neither a `Move` object nor a `Board` ever differs between Job 1's `parse_uci` and the old engine (or Job 2 `P2`'s `parse_uci`).** Every malformed 5-character castling or en-passant token is already rejected identically by `Board::is_pseudo_legal` in Job 1:
- For a 5-character king two-square token such as `e1g1q` (`promo = Queen != 0`): Job 1 sets `flags = KingCastle` (dropping `Promotion`), leaving `candidate.promotion = Queen`. Inside `Board::is_pseudo_legal` (`src/board.cpp`, castling block), `if ((move.flags & Capture) != 0U || move.promotion != 0) return false;` rejects `move.promotion != 0` immediately and returns `std::nullopt`.
- For a 5-character en-passant token such as `e5d6q` when `ep_square_ == d6` (`promo = Queen != 0`): Job 1 sets `flags = Capture | EnPassant` (dropping `Promotion`), leaving `candidate.promotion = Queen`. Inside `Board::is_pseudo_legal` (`src/board.cpp`, pawn block), `if (!move.is_promotion() && move.promotion != 0) return false;` rejects `!move.is_promotion() && move.promotion != 0` immediately and returns `std::nullopt` (and `ep_square_` can only lie on rank 3 or rank 6, never rank 1 or rank 8).
- We wrote `flags |= ...` in Job 2 `P2` purely for local self-evidence while writing the `parse_uci` oracle so `Promotion` in `flags` matched `promo != 0` before calling `is_pseudo_legal`, not because any token failed on Job 1.

### Answer to Question 2 (Soundness of partial `SearchStack` reset `stack_dirty_limit_` in `P3` / `forge/r15c`)
**Confirmed 100% sound — no path writes past `ss + 2` (`index <= seldepth_ + 6`), whereas `stack_dirty_limit_` resets through `std::min(MaxPly + 7, std::max(seldepth_, result.depth) + 8)`.** Exhaustive audit of every `ss` and `stack_` write in `src/search.cpp`:
1. Stack root is `ss = &stack_[4]` (`index = ply + 4`). Singular verification (`search_child(board, ss, ...)`) and null-move verification (`search_child(board, ss, ...)`) reuse `ss` (`ply + 4`).
2. `Worker::qsearch` child setup (`(ss + 1)->ply`), null-move child setup, ProbCut child setup, main `Worker::search` child setup, `record_move`, and `record_null_move` write at most `ss + 1` (`index = ply + 5`, plus `v3_state_->valid_flags[ply + 5]`, which `invalidate()` zeroes in full anyway). Even if a child call returns immediately on `if (aborted_) return 0;` before reaching `seldepth_ = std::max(seldepth_, child_ply)`, its parent already updated `seldepth_ >= parent_ply`, so that aborted child setup wrote at most `4 + parent_ply + 1 <= seldepth_ + 5`.
3. The furthest forward write in the entire codebase is **`(ss + 2)->killers = {};`** inside `Worker::search` (line `1889` of `forge/r15c` `src/search.cpp` / line `1793` of `pc_r15` `src/search.cpp`), executed *after* `seldepth_ = std::max(seldepth_, ply)`, reaching `index = 4 + ply + 2 <= seldepth_ + 6`.
4. All early returns in `Worker::search(Board, const SearchLimits&, ...)` (`root_drawn`, `limits.nodes == 0`, emergency TT move, expired `hard_limit_ms_`) execute *before* the `stack_` reset loop and before `stack_dirty_limit_` is updated, so an early-returning 0-node search never shrinks `stack_dirty_limit_` before the previous search's dirty prefix is cleaned.

### Step 0 (Same Machine and Builds as Job 2, Re-Run Today on `forge/r15c`) + `nproc` and `lscpu`
Full raw output in `forge-combo29/carbon2/job3/step0_job3_raw.txt`:
- **No settings, no net:** `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
- **PC20, no net:** `bench 11 -> 278024`, `bench 13 -> 587276`
- **512 test net only (`net512.fnn3`, checksum `fdff70de72e4ca82`):** `bench 11 -> 965454`, `bench 13 -> 4151906`
- **PC20, then 512 test net:** `bench 11 -> 625258`, `bench 13 -> 3652372`; `eval` -> `nnue 968` / `nnue 1176` / `nnue 31`

```text
$ nproc
4
$ lscpu
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           46 bits physical, 57 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  4
On-line CPU(s) list:                     0-3
Vendor ID:                               GenuineIntel
Model name:                              Intel(R) Xeon(R) Processor
CPU family:                              6
Model:                                   207
Thread(s) per core:                      1
Core(s) per socket:                      4
Socket(s):                               1
Stepping:                                2
BogoMIPS:                                4800.00
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc pebs bts rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq dtes64 vmx ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid avx512f avx512dq rdseed adx smap avx512ifma clflushopt clwb avx512cd sha_ni avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves avx_vnni avx512_bf16 wbnoinvd arat vnmi avx512vbmi umip pku ospke avx512_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg avx512_vpopcntdq rdpid bus_lock_detect cldemote movdiri movdir64b fsrm md_clear serialize tsxldtrk amx_bf16 avx512_fp16 amx_tile amx_int8 flush_l1d arch_capabilities
Virtualization:                          VT-x
Hypervisor vendor:                       KVM
Virtualization type:                     full
L1d cache:                               192 KiB (4 instances)
L1i cache:                               128 KiB (4 instances)
L2 cache:                                8 MiB (4 instances)
L3 cache:                                320 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-3
```

---

## 1. Profile of Base `forge/r15c` on FEN-Root Self-Play (Top 25 Functions)

Profiled on `selfplay_driver_v2.py --mode fen --games 24` (`3,391` `go softnodes 2000` searches, `11,320,109` nodes, `PC20` + 768 test net; Linux `perf` binary is not installed in this container image, so collected with `-O3 -pg -fno-omit-frame-pointer -g` `gprof` flat + call-graph profile in `forge-combo29/carbon2/job3/base_r15c_selfplay_profile.txt`). Note that once-per-search UCI/thread/`hashfull`/`ExclusiveLease` costs from Job 1 have vanished (`0.00%` self), leaving pure tree-search and NNUE functions:

| Rank | Self % | Cumul % | Calls | Function (call-graph notes) |
| ---: | ---: | ---: | ---: | :--- |
| 1 | 17.39% | 17.39% | 51,943 (root) / 11.5M rec | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 2 | 8.90% | 26.29% | 1,836,282 | `forge::nnue::v3::refresh_from_pieces` (king-bucket transitions in long self-play endgames) |
| 3 | 7.66% | 33.95% | 26,052,870 | `forge::MovePicker::pick_best()` |
| 4 | 7.25% | 41.20% | 3,522,289 | `forge::nnue::v3::apply_pair_and_evaluate` (fused 1-ply update + SCReLU output -> **E2**) |
| 5 | 6.00% | 47.20% | 12,300,134 | `forge::Board::see_ge(Move const&, int) const` |
| 6 | 5.59% | 52.79% | 30,290,829 | `forge::MovePicker::next(bool)` |
| 7 | 5.38% | 58.17% | 1,189,213 | `forge::MovePicker::generate_evasions()` (**E1**) |
| 8 | 4.35% | 62.52% | 9,784,391 | `forge::Worker::corrected_eval` (50% remaining `non_pawn_key` scans + table loads -> **E3**) |
| 9 | 3.52% | 66.04% | 2,758,511 | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 10 | 2.69% | 68.73% | 5,842,844 | `forge::Worker::static_evaluate_v3` |
| 11 | 2.07% | 70.80% | 14,130,074 | `forge::Board::make_move(Move const&, Undo&)` |
| 12 | 2.07% | 72.87% | 2,171,791 | `forge::nnue::v3::apply_changes_pair_avx512` (multi-ply ancestor replay) |
| 13 | 1.86% | 74.73% | 14,246,365 | `forge::Board::is_legal_complete(Move const&) const` (~85% from illegal check evasions -> **E1**) |
| 14 | 1.66% | 76.39% | 6,417,927 | `forge::TranspositionTable::store_body<false>` |
| 15 | 1.66% | 78.05% | 2,346,778 | `forge::nnue::v3::output_sum_avx512` (**E2**) |
| 16 | 1.45% | 79.50% | 12,276,628 | `forge::Worker::quiet_history` |
| 17 | 1.45% | 80.95% | 12,020,086 | `forge::Board::has_legal_move() const` |
| 18 | 1.45% | 82.40% | 3,717,276 | `forge::fill_pseudo_legal<GenMode::Captures>` |
| 19 | 1.45% | 83.85% | 1,829,536 | `forge::nnue::v3::apply_changes` (single-perspective update on 1-side king bucket change) |
| 20 | 1.24% | 85.09% | 4,969,680 | `forge::Board::upcoming_repetition(unsigned long) const` (`CuckooRep` history scan) |
| 21 | 1.24% | 86.33% | 4,034,858 | `forge::Board::refresh_king_lines() const` |
| 22 | 1.24% | 87.57% | 1,272,115 | `forge::fill_pseudo_legal<GenMode::All>` (`1.19M` of `1.27M` calls from `generate_evasions` -> **E1**) |
| 23 | 1.04% | 88.61% | 1,553,915 | `std::__introsort_loop<MovePicker::Scored*>` (local `t` symbol at `0x465c0` aliased in `gprof` to `~vector<Parameter>` at `0x46580`; mostly triggered by 35-move evasion lists -> **E1**) |
| 24 | 0.83% | 89.44% | 14,255,451 | `forge::Board::is_repetition(unsigned long) const` |
| 25 | 0.83% | 90.27% | 14,198,903 | `forge::TranspositionTable::probe_body<false>` |

---

## 2. Results (`E1`, `E2`, and Optional Default-Off `E3`)

- **Touched files & functions:**
  - **`E1` (`e1_legal_check_evasions.patch.txt`):** `include/forge/board.hpp`, `src/board.cpp` (`Board::generate_legal_evasions`), `src/search.cpp` (`MovePicker::next`, `MovePicker::last_move_known_legal`, `MovePicker::generate_evasions`, `Worker::qsearch`, `Worker::search`). Generates only legal check evasions directly via bitboards (king steps only in double check; unpinned moves to `between(king, checker) | checker` + legal ep + safe king steps in single check); skips scoring altogether for `<= 1` non-TT legal evasions; returns sorted legal evasions directly whenever their scores are distinct (`!has_tie`), and when two legal evasions tie in score, preserves `pick_best()`/`std::sort`'s exact tie order while filtering illegal moves in $O(1)$ via a 64-entry bitboard mask instead of calling `is_legal_complete`.
  - **`E2` (`e2_avx512_vnni_768.patch.txt`, stacked on `E1`):** `src/nnue_v3.cpp` (`vnni_supported`, `hsum_epi32_pair_vnni`, `output_sum_avx512_vnni`, `output_sum_avx512`, `apply_pair_and_sum_avx512_vnni`, `apply_pair_and_sum_avx512`). Uses non-saturating `_mm512_dpwssd_epi32` (`VPDPWSSD`, 2x-unrolled `h += 64` with 4 accumulators) for `hidden >= 768`, leaving `< 768`, Scalar, and AVX2 untouched. **Why no lane can overflow:** `a_i in [0, QA=255]` and loader-checked `|w2_i| <= 127` give `p_i = a_i * w2_i in [-32385, +32385] subset [-32768, +32767]`, so `_mm512_mullo_epi16(a, w)` is exact signed `int16_t`; each non-saturating `vpdpwssd` adds two exact `p_i * a_i` products (`|term| <= 255^2 * 127 = 8,258,175`) per `int32` lane. Across `hidden <= MaxHidden = 1024` and both perspectives (`sum0+sum2+sum1+sum3`), each of the 16 `int32` lanes sums at most `2 * 2 * (1024 / 32) = 128` terms (`96` for `hidden = 768`), bounding `|lane| <= 1,057,046,400 < 2^30 < INT32_MAX = 2,147,483,647` (`792,784,800` for `768`) before widening to `int64` for horizontal reduction.
  - **`E3` (`e3_zobrist_nonpawn_opt.patch.txt`, stacked on `E1 + E2`, optional item 3):** `include/forge/board.hpp`, `src/board.cpp` (`Board::set_fen`, `Board::make_move`, `Board::unmake_move`, `Board::compute_non_pawn_key`, `Board::non_pawn_zobrist`), `include/forge/search.hpp`, `src/search.cpp` (`tune::ZobristNonPawnCorr`, `Worker::corrected_eval`, `Worker::update_correction`), `src/uci.cpp` (`uci_loop` option `ZobristNonPawnCorr`, default `false`).

| Step | Patch file | Lines | Identity (what was compared, on how many positions, equal or not) | Gain (paired ratio/round, rounds faster, both medians w/ 95% CI, A/A control, engine CPU time) | Planted fault (caught or not) |
| :--- | :--- | ---: | :--- | :--- | :--- |
| **E1** (Bit-exact legal check evasions) | `job3/e1_legal_check_evasions.patch.txt` (raw: `e1_proof_raw.txt`, `e1_oracle_and_fault_raw.txt`) | 288 | **100% EQUAL** vs `forge/r15c`: `bench 11/13/16` on **768** (`882074` / `4275906` / `32374943`) & **512** (`625258` / `3652372` / `23891329`); **250** `depth 9` rows; **1,000** `eval` rows (768 & 512); both 6-game FNV traces (`startpos` `4560d7c3afdeba2e`, `fen` `9ed22c1193ab96de`); **MovePicker evasion oracle** (`test_e1_evasion_oracle.cpp`): **`14,238` in-check positions** (`55,868` picker move-list + exact-order checks across `313,716` visited positions, cold & warmed PC20 histories, `0` mismatches). | **Self-play (`A = r15c`, `B = r15c+E1`, 8 ABBA rounds, Engine CPU MEASURED):**<br>- **Engine CPU s/s:** paired `[1.0390, 1.0679, 1.0494, 1.0460, 1.0619, 1.0303, 1.0962, 1.0191]`, **`8/8` faster**; `ratio_of_pooled_medians` **`1.0534x` (`+5.34%`), 95% CI `[1.0336x, 1.0652x]`**; `median_of_paired_round_ratios` **`1.0477x` (`+4.77%`), 95% CI `[1.0303x, 1.0679x]`**; A/A `A2/A1=1.0073`, `B2/B1=0.9849` (spread `1.51%` -> **MEASURED**). Total 16-run engine CPU: `22,190 ms -> 21,120 ms` (`1.0507x`).<br>- **Wall s/s:** **`8/8` faster**; pooled median ratio `1.0495x` (`[1.0325x, 1.0651x]`), paired median `1.0558x` (`[1.0368x, 1.0639x]`), A/A `1.0141 / 0.9777` (`not measured` by strict 0.45x rule).<br>**`bench 13` (4 ABBA rounds, MEASURED):**<br>- **Engine CPU nps:** paired `[1.1493, 1.1478, 1.1393, 1.1578]`, **`4/4` faster**; pooled median ratio **`1.1451x` (`+14.51%`), 95% CI `[1.1311x, 1.1701x]`** (`1.667M -> 1.909M` nps); paired median **`1.1485x`**; A/A `1.0000 / 0.9867` (spread `1.33%` -> **MEASURED**; wall **`1.1427x`**, **MEASURED**). | `job3/e1_planted_fault.patch.txt` (hand out equal-scored evasion pair in reversed order): **CAUGHT** by both the MovePicker oracle (`ref: e2f3 g2f3 g1f3` vs `got: g2f3 e2f3 g1f3`) and `bench 11` (`366263 != 312866`). |
| **E2** (AVX-512 VNNI output layer, `hidden >= 768`) | `job3/e2_avx512_vnni_768.patch.txt` (raw: `e2_proof_raw.txt`, `e2_oracle_and_fault_raw.txt`; `18` `vpdpwssd` ZMM ops verified via `objdump -d`) | 260 | **100% EQUAL** vs `E1`: `bench 11/13/16` on **768** & **512** nets; **250** `depth 9` rows; **1,000** `eval` rows (768 & 512); both 6-game FNV traces; **VNNI oracle** (`test_e2_vnni_oracle.cpp`): `Scalar == Avx2 == Avx512(VNNI)` across `19,985` sums & fused evals + saturated loader-bound widths `768, 800, 896, 1024` (`0` mismatches). | **Self-play (`A = r15c+E1`, `B = r15c+E1+E2`, `not measured` on cloud Xeon):**<br>- **Engine CPU s/s:** paired `[1.0272, 0.9968, 1.0096, 1.0451, 0.9998, 1.0587, 0.9818, 0.9923]`, `4/8` faster; `ratio_of_pooled_medians` `1.0076x` (`[0.9742x, 1.0454x]`); `median_of_paired_round_ratios` `1.0047x` (`[0.9923x, 1.0451x]`); A/A `1.0077 / 1.0228` (**not measured**). Total 16-run engine CPU: `21,690 ms -> 21,380 ms` (`1.0145x`).<br>- **`bench 13`:** `3/4` faster; engine CPU pooled median ratio `1.0113x`, paired median `1.0156x` (`1.913M -> 1.935M` nps; wall `1.0141x`), A/A `2.71%` (**not measured**). Static compile-time VNNI under `-march=znver5` should be timed directly on the PC's Zen 5. | `job3/e2_planted_fault.patch.txt` (drop lane 0 of 16 `int32` VNNI lanes via `_mm512_maskz_mov_epi32(0xFFFEU, ...)`): **CAUGHT** immediately (`scalar=3537181 != vnni=-1930267`; `bench 11 = 1164515 != 882074`). |
| **E3** (Optional default-OFF `ZobristNonPawnCorr`) | `job3/e3_zobrist_nonpawn_opt.patch.txt` (raw: `e3_identity_and_oracle_raw.txt`) | 217 | **Default OFF (`ZobristNonPawnCorr=false`): 100% EQUAL** vs `E2` across all 6 `bench 11/13/16` pins (768 & 512), **250** `depth 9` rows, **1,000** `eval` rows (768 & 512), and both 6-game FNV traces; Zobrist oracle (`test_e3_zobrist_nonpawn.cpp`): `115,268` make/unmake/null/castle/promo/ep transitions (`0` mismatches). | **Default-OFF:** search-identical; **Active (`ZobristNonPawnCorr=true`, PC20 + 768 net):** changes correction bucket permutation (`bench 11 -> 902068`, `bench 13 -> 4052923`, `-5.21%` nodes) while eliminating all remaining `non_pawn_key` 5-type scans; to be judged by games on the PC. | `job3/e3_planted_fault.patch.txt` (omit rook non-pawn Zobrist XOR on castling): **CAUGHT** immediately by `test_e3_zobrist_nonpawn` (`NON_PAWN_ZOBRIST MISMATCH`). |

---

## 3. What We Would Do Next With Another 90 Minutes (Ranked, With Profile Share Attacked)

1. **Vectorized / register-resident `refresh_from_pieces` + `apply_changes` single-perspective king-bucket refresh (`8.90% + 1.45% = 10.35%` of `forge/r15c` self-play CPU, now the #1 non-`Worker::search` hotspot after `E1`!):** In 24-game self-play (`base_r15c_selfplay_profile.txt`), `refresh_from_pieces` alone is **8.90%** (`1.84M` calls) because long self-play endgames cross king buckets constantly, and after updating `entry.values` it executes a separate `std::copy_n(acc, hidden, destination)` pass over 1.5 KiB plus 8-column/6-column unbatched tails. Keeping `entry.values` in 24 ZMM registers across *all* `subs[]` and `adds[]` in a single load-once / store-twice (`acc` + `destination`) loop over `h = 0 .. 767` eliminates **100% of intermediate `entry.values` L1 round-trips and the trailing `std::copy_n`**, cutting `refresh_from_pieces` memory ops by ~3x while staying 100% bit-exact.
2. **`MovePicker::pick_best()` + `MovePicker::next()` quiet/capture scoring & selection (`7.66% + 5.59% = 13.25%` of self-play CPU):** `pick_best()` runs `26.05M` times; hoisting `lanes = _mm256_setr_epi32(1,3,5,7,0,2,4,6)` / using AVX-512 `_mm512_i32gather` or 8-wide `__m512i` score-max reduction (`_mm512_permutexvar_epi32` + `_mm256_max_epi32` checking 8 moves per step instead of 4 while preserving leftmost tie index via `__builtin_ctz(_mm256_movemask_ps(...))`) cuts the selection scan iterations in half with 100% bit-exact tie order.
3. **`Board::see_ge` fast early-out & attacker update (`6.00%` of self-play CPU, `12.30M` calls):** Over half of `see_ge` calls that survive the initial `swap` check resolve on the very first defender recapture (`stm = opposite(us)`) when the target square has a pawn/minor defender and no own recapture; testing enemy pawn/knight contact before computing full `attackers_to_fast` PEXT sliders (when safe under pins) directly attacks the `6.00%` `see_ge` share bit-exactly.
4. **Compact bloom/parity prefilter on `Board::upcoming_repetition` (`1.24%` of self-play CPU, `4.97M` calls in long games):** In `upcoming_repetition`, the odd-distance loop runs up to `span <= 100` plies (`50` iterations) whenever `halfmove_clock >= 3`; maintaining a running 64-bit Zobrist parity or bounding `span` tightly cuts wasted history walks in drawn endgames.

---

## 4. Times, Runtime Model, and Pre-Commit Status

- **First line of `forge-combo29/carbon2/job3/stamps.txt`:**
  `Tue Nov 17 12:11:34 PM UTC 2026 | job 3 received (FABLE_TO_carbon2_3.md); initializing base_r15c (r15 + a_speed_pc20_v3.patch.txt)`
- **Last line of `forge-combo29/carbon2/job3/stamps.txt`:**
  `Tue Nov 17 12:53:03 PM UTC 2026 | writing REPORT_carbon2_job3.md after inspecting all E1, E2, E3, and profile files`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job3` before report commit

```text
$ git status --short
 M forge-combo29/carbon2/job3/stamps.txt
?? forge-combo29/carbon2/job3/REPORT_carbon2_job3.md
?? forge-combo29/carbon2/job3/e2_avx512_vnni_768.patch.txt
?? forge-combo29/carbon2/job3/e2_oracle_and_fault_raw.txt
?? forge-combo29/carbon2/job3/e2_planted_fault.patch.txt
?? forge-combo29/carbon2/job3/e2_proof_raw.txt
?? forge-combo29/carbon2/job3/e3_identity_and_oracle_raw.txt
?? forge-combo29/carbon2/job3/e3_planted_fault.patch.txt
?? forge-combo29/carbon2/job3/e3_zobrist_nonpawn_opt.patch.txt
?? forge-combo29/carbon2/job3/test_e2_vnni_oracle.cpp
?? forge-combo29/carbon2/job3/test_e3_zobrist_nonpawn.cpp

$ ls -R forge-combo29/carbon2/job3
forge-combo29/carbon2/job3:
base_r15c_selfplay_profile.txt
e1_legal_check_evasions.patch.txt
e1_oracle_and_fault_raw.txt
e1_planted_fault.patch.txt
e1_proof_raw.txt
e2_avx512_vnni_768.patch.txt
e2_oracle_and_fault_raw.txt
e2_planted_fault.patch.txt
e2_proof_raw.txt
e3_identity_and_oracle_raw.txt
e3_planted_fault.patch.txt
e3_zobrist_nonpawn_opt.patch.txt
prove_step.py
REPORT_carbon2_job3.md
stamps.txt
step0_job3_raw.txt
test_e1_evasion_oracle.cpp
test_e2_vnni_oracle.cpp
test_e3_zobrist_nonpawn.cpp
```
