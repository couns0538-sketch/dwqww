# REPORT: carbon2 — Job 4

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; no engine source files modified in-tree; all Job 4 files are text-only under `forge-combo29/carbon2/job4/`).

---

## 0. File-3 Questions Recap, Step 0, and `nproc` / `lscpu`

Both questions from File 3 were already answered in full in `forge-combo29/carbon2/job3/REPORT_carbon2_job3.md` (commit `f8bf2fce9`); brief recap:
1. **`parse_uci` `Promotion` bit in Job 2 `P2` vs Job 1:** Neither any `Move` nor any `Board` differs between Job 1's `parse_uci` and the old engine. Any 5-char castling (`e1g1q`) or en-passant (`e5d6q`) token leaves `candidate.promotion != 0`, which `Board::is_pseudo_legal` immediately rejects (`move.promotion != 0` on castling; `!move.is_promotion() && move.promotion != 0` on pawns).
2. **Partial `SearchStack` reset (`stack_dirty_limit_`):** Sound because `index = ply + 4`, singular/null verifications reuse `ss`, `qsearch`/null/ProbCut/main child setups and `record_move`/`record_null_move` write at most `ss + 1` (`<= seldepth_ + 5` even if the child immediately returns on `aborted_`), the furthest write anywhere is `(ss + 2)->killers = {}` (`line 1889` of `forge/r15c` `src/search.cpp`, executed after `seldepth_ = std::max(seldepth_, ply)`, reaching `<= seldepth_ + 6`), `stack_dirty_limit_` resets `0 .. seldepth_ + 8`, and early root returns execute before the `stack_` reset loop.

### Step 0 (Same Machine and Builds as Job 3, Re-Run Today) + `nproc` and `lscpu`
Full raw output in `forge-combo29/carbon2/job4/step0_job4_raw.txt`:
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

## 1. Base Used for Job 4

- **Job 3 `E1` (`forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt`)** was already finished to its full proof in Job 3 commit `3888d1fa6` (100% identity on 768 & 512 nets across `bench 11/13/16`, 250 depth-9 rows, 1,000 evals, both 6-game FNV traces, and `14,238` in-check MovePicker move+order oracle positions; planted tie-reversal fault caught; **`8/8` self-play rounds faster: `+4.77%` paired-median / `+5.34%` pooled-median engine CPU `MEASURED`; `4/4` `bench 13` rounds faster: `+14.85%` paired-median / `+14.51%` pooled-median engine CPU `MEASURED`**). Per File 4's note, `E2` was not included.
- **Exact Base for `S1`, `S2`, and `S3`:** `6b98f217` (`forge-combo29`) + `pc_r15.patch` + `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` (Job 1) + `forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt` (Job 3 `E1`). Each of `S1`, `S2`, and `S3` is an independent unified diff applying with `patch -p1 --fuzz=0` onto that exact base (`job4/base_r15c_e1_profile.txt` holds the post-`E1` 24-game FEN-root self-play profile from which `S1`, `S2`, and `S3` were selected in descending order of profile share).

---

## 2. Results (`S1`, `S2`, `S3`)

- **Touched files & functions:**
  - **`S1` (`s1_tiled_refresh_and_single_fuse.patch.txt`):** `include/forge/board.hpp` (`Board::piece_bitboards`), `include/forge/nnue_v3.hpp` (`replay_ply`, `refresh_one_and_evaluate`), `src/nnue_v3.cpp` (`refresh_from_pieces` 8-ZMM 256-int16 tiled register-resident update + `diff == 0` skip, `refresh_one_and_evaluate`, `refresh_cached`), `src/search.cpp` (`Worker::static_evaluate_v3` 1-ply single-king-refresh + kept-perspective fused evaluation).
  - **`S2` (`s2_movepicker_avx512_qhist.patch.txt`):** `include/forge/board.hpp` (`Board::cached_king_lines`), `include/forge/search.hpp` (`Worker::quiet_hist_epoch_`), `src/search.cpp` (`MovePicker::next`, `MovePicker::has_cached_quiet_history`, `MovePicker::cached_quiet_history`, `MovePicker::init_check_squares`, `MovePicker::pick_best_scored` 16-wide AVX-512 `VPERMT2D` + 8-wide AVX-512 selection scan, `MovePicker::generate_quiets`, `Worker::update_continuation`, `Worker::update_quiet_stats`, `Worker::search`). Note: on pure `qsearch` capture lists (`<= 4` moves), hoisting the `odd_idx16` constant load inside `if (i + 8 <= n)` is an easy 2-line refinement if combining with deep-search builds.
  - **`S3` (`s3_correction_prefetch_and_unroll.patch.txt`):** `include/forge/search.hpp` (`Worker::prefetch_correction`), `src/search.cpp` (`non_pawn_key` compile-time-constant 5-piece unroll, `Worker::prefetch_correction` issuing `__builtin_prefetch` on the four 128 KiB correction tables right after `make_move`/`make_null_move` in `Worker::qsearch` and `Worker::search`).

| Step | Patch file | Lines | Identity (what was compared, on how many positions, equal or not) | Gain (paired ratio/round, rounds faster, median of paired ratios w/ 95% CI, pooled-median ratio, A/A control, engine CPU time) | Prediction (its commit, met or killed) | Planted fault (caught or not) |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **S1** (Tiled register-resident king refresh + 1-ply single-refresh fuse) | `job4/s1_tiled_refresh_and_single_fuse.patch.txt` (raw: `s1_proof_raw.txt`, `s1_oracle_and_fault_raw.txt`) | 315 | **100% EQUAL** vs base (`r15c+E1`): `bench 11/13/16` on **768** (`882074` / `4275906` / `32374943`) & **512** (`625258` / `3652372` / `23891329`); **250** `depth 9` rows; **1,000** `eval` rows (768 & 512); both 6-game FNV traces (`startpos` `4560d7c3afdeba2e`, `fen` `9ed22c1193ab96de`); accumulator+eval oracle (`test_s1_refresh_oracle.cpp`): `1,002` root refreshes + `2,770` single-king bucket transitions (`0` mismatches across all `2 * 768` int16 lanes). | **Self-play (`not measured` due to `B2/B1=0.9630` build spread):**<br>- **Wall s/s:** paired `[1.0348, 0.9903, 1.0765, 1.0245, 0.9988, 1.0059, 0.9976, 0.9999]`, `4/8` faster; **median of paired ratios `1.0029x` (`+0.29%`), 95% CI `[0.9976x, 1.0348x]`**; **pooled-median ratio `1.0043x`** (`B1=533.26`, `B2=513.51` vs `A1=515.85`, `A2=522.95`); A/A `1.0138 / 0.9630` (`3.70%` -> **not measured**).<br>- **Engine CPU s/s:** paired `[1.0415 .. 1.0082]`, **`6/8` faster**; **median of paired ratios `1.0137x` (`+1.37%`), CI `[0.9848x, 1.0332x]`**; **pooled-median ratio `1.0038x`**; A/A `1.0194 / 0.9736` (**not measured**). Total 16-run engine CPU: `21,060 ms -> 20,840 ms` (`1.0106x`).<br>- **`bench 13`:** **`4/4` faster**; engine CPU paired median **`1.0202x`** (`1.909M -> 1.952M` nps, pooled `1.0228x`), A/A `1.55%` (**not measured**). | `job4/prediction_s1.txt` (commit **`45f284110`**, predicted paired wall `1.020x..1.045x`, kill `< 1.010x`): **KILLED** on self-play wall (`1.0029x`, confounded by `B2`'s `-3.7%` binary layout drop while `B1` hit `533.3 s/s` and `bench 13` was `4/4` faster `+2.02%`). | `job4/s1_planted_fault.patch.txt` (skip writing refreshed ZMM tile to child accumulator): **CAUGHT** immediately (`SINGLE_REFRESH_FUSE MISMATCH` on move `e1d2`). |
| **S2** (AVX-512 16-wide `VPERMT2D` `pick_best` + cached `quiet_history` + shared `check_squares`) | `job4/s2_movepicker_avx512_qhist.patch.txt` (raw: `s2_proof_raw.txt`, `s2_oracle_and_fault_raw.txt`) | 195 | **100% EQUAL** vs base (`r15c+E1`): `bench 11/13/16` on **768** & **512** nets; **250** `depth 9` rows; **1,000** `eval` rows (768 & 512); both 6-game FNV traces; MovePicker + epoch oracle (`test_s2_movepicker_oracle.cpp`): `44,210` picked moves (`4,786` cached quiet-history checks + mid-loop epoch invalidation checks across warmed & all-zero tied histories, `0` mismatches). | **Self-play (MEASURED on both wall and engine CPU):**<br>- **Wall s/s:** paired `[1.0056, 1.0191, 1.0363, 0.9876, 1.0517, 1.0428, 1.0121, 1.0084]`, **`7/8` faster**; **median of paired ratios `1.0156x` (`+1.56%`), 95% CI `[1.0056x, 1.0428x]`**; **pooled-median ratio `1.0215x` (`+2.15%`, CI `[0.9937x, 1.0551x]`)**; A/A `A2/A1=1.0023`, `B2/B1=1.0053` (max spread **`0.53%`** < half of `1.56%`/`2.15%` -> **MEASURED**).<br>- **Engine CPU s/s:** paired `[1.0177, 1.0367, 1.0153, 0.9961, 1.0423, 1.0226, 1.0343, 0.9906]`, **`6/8` faster**; **median of paired ratios `1.0201x` (`+2.01%`), CI `[0.9961x, 1.0367x]`**; **pooled-median ratio `1.0307x` (`+3.07%`)**; A/A `1.0075 / 1.0116` (spread **`1.16%`** -> **MEASURED**). Total 16-run engine CPU: `21,480 ms -> 21,060 ms` (`1.0199x`).<br>- `bench 13`: `0.9852x` paired (`not measured`; short capture lists in `qsearch` load `odd_idx16` before checking `i + 8 <= n`). | `job4/prediction_s2.txt` (commit **`fed59e36a`**, predicted paired wall `1.015x..1.045x`, kill `< 1.008x`): **MET** (`1.0156x` paired median, `1.0215x` pooled median, `7/8` faster, A/A `0.53%` **MEASURED**). | `job4/s2_planted_fault.patch.txt` (omit subtracting `12000` direct-check bonus from `last_quiet_history_`): **CAUGHT** by both `test_s2_movepicker_oracle` (`got=12000 != ref=0`) and `bench 11` (`299404 != 312866`). |
| **S3** (Early correction-table prefetch + unrolled `non_pawn_key`) | `job4/s3_correction_prefetch_and_unroll.patch.txt` (raw: `s3_proof_raw.txt`, `s3_oracle_and_fault_raw.txt`) | 93 | **100% EQUAL** vs base (`r15c+E1`): `bench 11/13/16` on **768** & **512** nets; **250** `depth 9` rows; **1,000** `eval` rows (768 & 512); both 6-game FNV traces; key oracle (`test_s3_correction_oracle.cpp`): `45,494` `non_pawn_key` evaluations (`0` mismatches). | **Self-play (`not measured` on Xeon 8 MiB L2):**<br>- **Wall s/s:** paired `[1.0309, 1.0014, 0.9763, 1.0036, 0.9840, 0.9605, 1.0106, 1.0125]`, `5/8` faster; **median of paired ratios `1.0025x` (`+0.25%`), CI `[0.9763x, 1.0125x]`**; **pooled-median ratio `0.9966x`**; A/A `1.0062 / 1.0099` (**not measured**).<br>- **Engine CPU s/s:** `3/8` faster, paired median `0.9922x`, pooled `0.9924x`, A/A `3.07%` (**not measured**; `20,980 ms` vs `21,090 ms`).<br>**Deep search `bench 13` (MEASURED on both wall and engine CPU):**<br>- **Wall nps:** paired `[1.0038, 0.9986, 1.0303, 1.0209]`, **`3/4` faster**; **median of paired ratios `1.0124x` (`+1.24%`)**; **pooled-median ratio `1.0238x` (`+2.38%`, `1.947M -> 1.994M` nps, peak `2.026M`)**; A/A `0.9943 / 1.0057` (spread **`0.57%`** -> **MEASURED**; engine CPU **`1.0210x`** pooled / **`1.0126x`** paired, A/A `0.94%` -> **MEASURED**). | `job4/prediction_s3.txt` (commit **`288160546`**, predicted paired self-play wall `1.010x..1.035x`, kill `< 1.007x`): **KILLED** on Xeon 2k-node self-play (`1.0025x`, where Xeon's 8 MiB L2 holds all 512 KiB of correction tables warm), while **MEASURED `+2.38%` on `bench 13`** (relevant to Zen 5's smaller 1 MB L2 shared across 2 SMT threads and 50k/250k matches). | `job4/s3_planted_fault.patch.txt` (wrong `King` constant in unrolled `non_pawn_key`): **CAUGHT** by both `test_s3_correction_oracle` and `NonPawnCorrection` `bench 11` (`296690 != 312866`). |

---

## 3. What We Would Do Next With Another 90 Minutes (Ranked, With Post-`E1` Profile Share Attacked)

1. **Test `E1` + `S2` (with `odd_idx16` hoisted inside `if (i + 8 <= n)`) + `S1` + `S3` on the PC's Zen 5 Clang ThinLTO+PGO build (`~33%` combined post-`r15c` share):** `E1` (`+5.3%` self-play CPU, `+14.5%` `bench 13` nps) and `S2` (`+2.0%` paired / `+3.1%` pooled self-play CPU, `MEASURED`) already win cleanly on Linux `g++`, while `S1` (`+2.0%` `bench 13`) and `S3` (`+2.4%` `bench 13`, `MEASURED`) specifically reduce L1/L2 memory pressure that hits Zen 5's 1 MB L2 (with 2 SMT threads/core) harder than this cloud Xeon's 8 MiB single-thread L2.
2. **`Board::see_ge` fast non-pinned contact resolution (`4.55%` of post-`E1` self-play CPU, `12.30M` calls):** When `swap = attacker_value - swap > 0` requires testing opponent recaptures, `see_ge` immediately builds all 6 piece-type `attackers_to_fast` bitboards (2 PEXT slider lookups) even when an unpinned enemy pawn (`attacks::pawn(us, to) & pieces(them, Pawn)`) already recaptures and forces `SeeValue[Pawn] - swap < 1` (terminating the exchange on ply 1 whenever the mover was a minor/rook/queen and no x-ray is needed).
3. **`Board::make_move` / `unmake_move` + `Board::key_after` (`2.85% + 1.90% + 1.33% = 6.08%` of post-`E1` self-play CPU, `14.13M` calls):** `make_move` already knows `early_key` (`child_key`) was computed two lines earlier in `key_after` on `>90%` of moves (`ep_square_ < 0`, non-ep, non-contested double push), yet `make_move` recomputes all 6 `piece_key` + `Z.castling` + `Z.side` XORs from scratch instead of accepting the precomputed `child_key` (and `Undo` copies 72-byte `KingLines` by value on every `make_move` and `unmake_move` even when `king_lines_.valid == false`, which is `71%` of nodes!). Only saving/restoring `king_lines_` when `king_lines_.valid` is true saves copying `64` bytes x 2 on `10M` nodes per 24 games.
4. **Bitboard move generation `fill_pseudo_legal<Captures>` & `<Quiets>` (`1.71% + 1.33% = 3.04%` of post-`E1` self-play CPU):** Packing `Move` creation as a single `uint32_t` store `(flags << 24) | (to << 8) | from` and loop-unrolling quiet target extraction with `_blsr_u64`.

---

## 4. Times, Runtime Model, and Pre-Commit Status

- **First line of `forge-combo29/carbon2/job4/stamps.txt`:**
  `Tue Nov 17 01:00:16 PM UTC 2026 | job 4 received (FABLE_TO_carbon2_4.md); base set to r15 + a_speed_pc20_v3 + e1_legal_check_evasions`
- **Last line of `forge-combo29/carbon2/job4/stamps.txt`:**
  `Tue Nov 17 01:48:11 PM UTC 2026 | writing REPORT_carbon2_job4.md after inspecting all S1, S2, S3, and prediction files`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2/job4` before report commit

```text
$ git status --short
 M forge-combo29/carbon2/job4/stamps.txt
?? forge-combo29/carbon2/job4/REPORT_carbon2_job4.md
?? forge-combo29/carbon2/job4/s3_correction_prefetch_and_unroll.patch.txt
?? forge-combo29/carbon2/job4/s3_oracle_and_fault_raw.txt
?? forge-combo29/carbon2/job4/s3_planted_fault.patch.txt
?? forge-combo29/carbon2/job4/s3_proof_raw.txt
?? forge-combo29/carbon2/job4/test_s3_correction_oracle.cpp

$ ls -R forge-combo29/carbon2/job4
forge-combo29/carbon2/job4:
base_r15c_e1_profile.txt
prediction_s1.txt
prediction_s2.txt
prediction_s3.txt
REPORT_carbon2_job4.md
s1_oracle_and_fault_raw.txt
s1_planted_fault.patch.txt
s1_proof_raw.txt
s1_tiled_refresh_and_single_fuse.patch.txt
s2_movepicker_avx512_qhist.patch.txt
s2_oracle_and_fault_raw.txt
s2_planted_fault.patch.txt
s2_proof_raw.txt
s3_correction_prefetch_and_unroll.patch.txt
s3_oracle_and_fault_raw.txt
s3_planted_fault.patch.txt
s3_proof_raw.txt
stamps.txt
step0_job4_raw.txt
test_s1_refresh_oracle.cpp
test_s2_movepicker_oracle.cpp
test_s3_correction_oracle.cpp
```
