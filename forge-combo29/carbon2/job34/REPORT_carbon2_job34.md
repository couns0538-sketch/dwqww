# REPORT — `carbon2` Job 34: Handoff Map (`kF -> kK`), Leave-One-Out (`B21..B23`, `BG`), and Profile `P2` (`CP2`)

1. **Step 0 (`step0_raw.txt`, `builds.txt`):** Reused Job 30/32 SP-PGO binaries `X_1` (`/tmp/carbon2_job30/bld_sp_stkH_1/forge`, `sha256 = 41f147ec4482904557dddfc0089378a3fd7e0af6104ca661981d8db7fbe57140`) and `kK_1` (`/tmp/carbon2_job32/bld_sp_stkK_1/forge`, `sha256 = 985b8dbd2dfeae587b8aeb29f1a17c2054e6afa89e30a7223258d582e6995108`); both passed in fresh processes (`bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609`; `PC20 + net768` `bench 11 = 882074`, `bench 13 = 4275906`).
2. **A1 (`partA_A1_kF_check.txt`):** **`EQUAL`** (`29 of 29` files of `kF` match `forge/r15f`'s 16-hex SHA-256 prefixes).
3. **A2 (`stack_kF_to_kK.patch.txt`, `kK_tree.sha256`, `partA_A2_verify.txt`):** **`1,921` lines** (`+820` / `-365` across `7` files), `sha256 = b9b15021b60e5958fecc1397b0ff52313a65ad4268749caee766305dd7f6d596`, **`29 of 29 files equal`** (`A2` applied to `kF` with `patch -p1 --fuzz=0` equals `kK`; no rebuild of `kK` needed).
4. **A3 (`stack_map.md`):** **`82` hunks** total; hunks per piece: **`14`: `7`**, **`15`: `15`**, **`16`: `5`**, **`17`: `8`**, **`18`: `8`**, **`19`: `5`**, **`20`: `6`**, **`21`: `6`**, **`22`: `13`**, **`23`: `13`** (`3` shared hunks `#6, #8, #56` = `86` piece-hunk incidences); hunks with `none`: **`8`** (`#10, #15, #40, #46, #47, #73, #74, #75`).
5. **Part B (`prediction1.txt` [commit `4d3f643b4`], `partB_builds_verify.txt`, `row_B21_raw.txt`, `row_B22_raw.txt`, `row_B23_raw.txt`, `row_BG_raw.txt`, `partB_summary.txt`):** Prediction 1 **`2/3` HIT** (`B21` `[1.0040, 1.0130] | SEEN` **MISS**; `B22` `[1.0035, 1.0120] | SEEN` **HIT**; `B23` `[0.9990, 1.0075] | NOT SEEN` **HIT**). Rows (`6` blocks `ABBA/BAAB`, `0` dropped): **`B21`: pooled CPU `1.0031` (`6/6 > 1`), reading `NOT SEEN`**; **`B22`: pooled CPU `1.0104` (`6/6 > 1`), reading `SEEN`**; **`B23`: pooled CPU `1.0030` (`5/6 > 1`), reading `NOT SEEN`**; **`BG`: pooled CPU `1.0278` (`6/6 > 1`), reading `SEEN`** (`B21 * B22 * B23 = 1.0166` beside `K1 / J1 = 1.0203 / 1.0044 = 1.0158`).
6. **Part C (`prediction2.txt` [commit `ed90c29e0`], `partC_builds_verify.txt`, `partC_CP2_runs_raw.txt`, `P2_outside_search_raw.txt`, `P2_groups_and_CP2_raw.txt`):** Prediction 2 **`3/4` HIT** (`apply_one_refresh_one_and_evaluate` `[4.8%, 7.2%]` $\to$ `5.72%`/`6.05%` **HIT**; `screlu_dot_pair_avx512` `[4.0%, 7.5%]` $\to$ **MISS**, superseded by Piece `16`'s fused `apply_pair_and_evaluate` `#1` at `6.32%`/`6.49%` while standalone `output_sum_avx512` is `0.13%`; `Board::see_ge` `[1.8%, 3.3%]` $\to$ `2.07%`/`2.10%` **HIT**; `the net` `[18.5%, 22.5%]` $\to$ **`21.00%`/`21.42%` HIT**). `P2` groups (`J34` paired / `J32` same-run): **`(1) the net` `21.00%` / `21.42%`** (`accumulator update` `11.64%` / `11.69%`, `refresh` `4.21%` / `4.40%`, `forward pass` `5.16%` / `5.32%`), **`(2) move generation` `11.98%` / `11.96%`**, **`(3) the quiescence search` `1.96%` / `2.03%`**, **`(4) make and undo outside Worker::search` `0.56%` / `0.63%`**, **`(5) the hash table` `2.45%` / `2.42%`**, **`(6) the rest` `15.56%` / `15.62%`** (`Table P 45.92% + P2 54.08% = 100.00%` on `perf_XG.data`, `99.44%` across runs). Control **`CP2`**: **`NOT TRUSTED`** (`2.29%` true cost in `Board::see_ge`; group invariance passed at `max = 6.69% <= 10%`, but function/line attribution over-counted by `+78.26%` raw / `+67.21%` scaled `> 25%`; `NOT TRUSTED` written on `P2`'s source lines and nothing below the function level is used).

---

## WHAT THIS CANNOT SEE

The PC's timing (a VM with 4 CPUs is not a 9850X3D beside 15 busy threads); the PC's read (the map is a guide to it, not a replacement); whether a faster search of the same nodes makes better nets (it makes more positions an hour, nothing else).

---

## 1. Part A — Handoff Package (`kF -> kK`, Pieces `14..23`)

- **`A1` (`partA_A1_kF_check.txt`):** All `29` repository files of `kF` (`/tmp/carbon2_work/src_kF`) match `forge/r15f`'s 16-hex SHA-256 prefixes (**`EQUAL`**, `29 of 29`).
- **`A2` (`stack_kF_to_kK.patch.txt`, `kK_tree.sha256`, `partA_A2_verify.txt`):** Single consolidated unified diff from `kF` to `kK` (`1,921` lines, `+820` added / `-365` removed across `include/forge/{board,nnue_v3,search}.hpp` and `src/{board,nnue_v3,search,uci}.cpp`; `22` of `29` files untouched; `sha256 = b9b15021b60e5958fecc1397b0ff52313a65ad4268749caee766305dd7f6d596`). Applied cleanly (`patch -p1 --fuzz=0`) to a fresh copy of `kF` $\to$ **`29 of 29 files equal`** to `kK` (`kK_tree.sha256`).
- **`A3` (`stack_map.md`):** Complete 82-row hunk map (`#1..#82`) in patch order. Every hunk reads **NO** on search/score/move-order/output change. The `8` hunks with **`none`** (human read only on the PC) are:
  - **`#10`** (`include/forge/nnue_v3.hpp`, Piece `16`): `nnue::v3::make_valid` has zero callers once `#79` switches `static_evaluate_v3` to `make_valid_through`.
  - **`#15`** (`src/board.cpp`, Piece `23`): `candidate.key_history_.reserve(2048)` capacity-only reservation in `Board::set_fen`.
  - **`#40, #46, #47`** (`src/search.cpp`, Piece `22`): `#else`/`#elif` compile branches (`!FORGE_SPD_KING_LINES`, uncalled `MovePicker::direct_check`, `!FORGE_SEARCH_SPEED2`, `FORGE_SPD_NO_ZERO_MOVELISTS < 2`).
  - **`#73`** (`src/search.cpp`, Piece `17`): `std::fill_n(root_move_nodes_..., root_effort_count_, 0)` — `root_move_nodes_` is read only in `time_managed_` clock searches (`src/search.cpp:3780, 3803`), never in `depth` / `nodes` / `softnodes` runs.
  - **`#74`** (`src/search.cpp`, Piece `15`): `#if FORGE_FIX_ABORT_PUBLISH` (`0` in all builds).
  - **`#75`** (`src/search.cpp`, Piece `15`): partial-iteration root PV publish under `!stopped_by_nodes_`, reached only on clock/external-`stop` aborts.

### `A4` — What Needs What (`partA_A4_A5.md`, empirically verified with `patch -p1 --fuzz=0` + `clang++-18 -fsyntax-only` across all `9` TUs)

| Piece | Patch File | Standalone on `kF` | Cannot Stand Without | Can Be Dropped Alone? |
|---:|---|---|---|---|
| `14` | `job26/14_search_lazy_history_hoist.patch.txt` | `OK` | None (`#61–#67`) | **YES** |
| `15` | `job28/15_slim_search_stack.patch.txt` | `OK` | None (`#11, #12, #51–#56, #58, #68, #71, #72, #74–#76`) | **YES** |
| `16` | `job28/16_v3_null_and_fused_tail.patch.txt` | `OK` | None (required by `20` via `#8`) | **NO while `20` stays** (`{16, 20}` drops as a pair) |
| `17` | `job30/17_uci_stdio_and_search_setup.patch.txt` | `OK` | None (`#14, #70, #73, #77, #78, #80–#82`) | **YES** |
| `18` | `job30/18_fast_upcoming_repetition.patch.txt` | `OK` | None (`#5, #6, #26–#30, #69`) | **YES in `A2`** (`19`/`23` share context-only `#6` in `.patch.txt`) |
| `19` | `job31/19_fast_has_legal_move.patch.txt` | Context `#6` | Semantic: None (`18` context-only in `board.hpp` `#6`) | **YES** |
| `20` | `job31/20_v3_fast_refresh_and_pair.patch.txt` | Needs `16` | **`16`** (`replay_ply_from` in `nnue_v3.hpp` `#8`) | **YES** |
| `21` | `job32/21_corr_prefetch_and_fast_keys.patch.txt` | `OK` | None (`#13, #50, #56, #57, #59, #60`) | **YES** |
| `22` | `job32/22_movepicker_branchless_push_and_zerocopy_checks.patch.txt` | `OK` | None (`#37–#49`) | **YES** |
| `23` | `job32/23_compact_undo_kinglines_and_fast_draw_gates.patch.txt` | Context `#6` | Semantic: None (`18` context-only in `board.hpp` `#6`) | **YES** |

- **Recommended PC reading order:** **(1)** `search.cpp` node/move-loop pieces `21 -> 14 -> 22`; **(2)** `Board` pieces `18 -> 23 -> 19` (reading shared declaration Hunk `#6` once); **(3)** coupled `nnue_v3` pair `16 -> 20` strictly in that order (checking `#10`); **(4)** stack & UCI plumbing `15 -> 17` (checking `#73, #74, #75, #82`).

### `A5` — The Machine List (`partA_A4_A5.md`, Target: `9850X3D` / `16` Engines / Windows Clang 23 + MinGW `libstdc++`)

| `#` | Hunks & Piece | Site & Assumption | PC Fit (`9850X3D` / Windows Clang 23) | Sign If Unfit | Covered by KA? |
|---:|---|---|---|---|---|
| `1` | `#13, #56, #57, #59, #60` (`21`) | `5x __builtin_prefetch(addr, 0, 1)` (read, `locality=1` $\to$ `PREFETCHT2` across `5 * 128 KiB = 640 KiB` correction tables before `static_evaluate`). | `640 KiB` > `48 KiB` L1d (`24 KiB`/SMT thread), competes in `1 MiB` L2, fits `96 MiB` V-Cache; hides L2/L3 latency if Zen 5 AGU cost is small. | `the same` / `slower` | Safety: YES; Worth: NO |
| `2` | `#11, #12` (`15`) | `alignas(64) SearchStack` + `static_assert(sizeof(SearchStack) == 128)` (`2` cache lines vs `2,880` B = `45` lines); splits `pv_stack_` (`70 KiB`) & `v1_stack_` (`297 KiB`). | Keeps `20–30` active plies (`2.5–3.8 KiB`) inside `48 KiB` L1d under 2-way SMT; LLP64 Windows x86_64 field sizes match (`static_assert` guards layout). | `the same` / `slower` (or compile error on ABI change) | YES (`static_assert`, `V2` ASan/UBSan + `CA`) |
| `3` | `#1–#3, #19–#23` (`23`), `#39` (`22`) | `SavedKingLines` (`56` B vs `80` B in `Undo`/`NullUndo`) + `MovePicker::check_squares_` (`8` B pointer vs `56` B copy). | Reduces stack L1d bandwidth under SMT at cost of `1` `chk_b | chk_r` OR on `unmake` and `1` L1-hot pointer load. | `the same` / `slower` | Safety: YES; Worth: NO |
| `4` | `#26–#29` (`18`) | `alignas(16) CuckooSlot` (`16` B) in `alignas(64) constexpr CuckooMoves` (`128 KiB` `.rodata`, `1` line/probe vs `2`). | Shared read-only physical pages across `16` processes; `0.13%` of `96 MiB` V-Cache. | `the same` / `slower` | YES (`static_assert`, `PC20+net768`, `T`) |
| `5` | `#15` (`23`), `#70` (`17`) | `key_history_.reserve(2048)` (`16 KiB` in `set_fen`) & `result.pv.reserve(64)` (`256` B/search). (`Board` value-copy copies `size()`, not `capacity()`.) | Once per `ucinewgame` (`set_fen`) on Windows UCRT LFH heap; no OS page-size assumption. | `the same` / `slower` | `none` (capacity-only) |
| `6` | `#31–#35` (`16, 20`) | `AVX-512F + AVX-512BW` (`vmovdqa64` aligned `64`-byte loads/stores; requires `hidden % 32 == 0` and `64`-byte heap alignment of `WorkerState` / `Net`). | Native 512-bit Zen 5 pipes (same ISA as `r15d`). Must verify MinGW C++20 `operator new(..., align_val_t{64})` honors `64`-byte alignment. | **`wrong` (immediate `ACCESS_VIOLATION`)** if unaligned; `slower` if no `-mavx512bw` | Linux: YES (`KV1a/b`, `V2`); Windows MinGW `new`: NO (`Step 0` tests immediately) |
| `7` | `#12, #16, #19, #29, #30, #42, #44, #62` | `[[gnu::noinline]]`, `[[gnu::always_inline]]`, `[[unlikely]]`, and branchless `push_scored` (`#38, #41, #42`). | Native in Clang 23 on Windows; worth depends on Zen 5 TAGE predictor + Clang 23 codegen. | `the same` / `slower` | Safety: YES; Worth: NO |
| `8` | `#1–#3, #19–#23, #31–#48, #55, #56, #62, #65, #72, #74, #79, #82` | `#if` defines (`FORGE_SPD_KING_LINES`, `FORGE_SEARCH_SPEED2`, `FORGE_SPD_NO_ZERO_MOVELISTS`, `FORGE_PAWN_HISTORY`, `FORGE_FIX_ABORT_PUBLISH`, `FORGE_NNUE_V3`). | Matches `r15f` production defines; flipping inactive defines enters unexercised `#if`/`#else` code (`#40, #46, #47, #74`). | **`wrong` / compile error** only if defines change | Active: YES; Inactive: `none` |
| `9` | `#14, #77, #78` (`17`), `#11, #12` (`15`) | `Searcher` cached worker pointer vectors (`workers_` mutated only in `set_threads`); `16` processes sharing Zen 5 L1d/L2/L3 (`16 * ~18.7 MiB ≈ 300 MiB` at `Hash 16`). | Safe for `Threads 1..256`; smaller stack/undo helps 2-way SMT L1d sharing (`16` engines on `8` cores). | `the same` / `slower` | `Threads 4`: YES (`V3`); `16`-proc SMT: NO |
| `10` | `#81, #82` (`17`) | `sync_with_stdio(false)` + `cin.tie(nullptr)` in `main()` (`#82`) and stack-buffered `cout.write + flush` for `bestmove` (`#81`). | Forge has zero `<cstdio>` calls and flushes every UCI response. Verify MinGW `basic_filebuf::underflow` over Windows anonymous pipes returns on `\n` without waiting to fill `BUFSIZ`. | `the same`, or **`wrong` (pipe hang)** if CRT `underflow` blocks | Linux pipes: YES; Windows MinGW pipes: NO (test interactive UCI first) |

---

## 2. Part B — Leave-One-Out on `kK` (`B21, B22, B23`) and Warm Whole-Game Search (`BG`)

### Build Floor & Pre-Timed Builds (`partB_builds_verify.txt`, `partB_summary.txt`)
- **Build floor from Job 32:** `K1` (`X_1 / kK_1` = `1.0203`, `12/12 > 1`; 6-block prefix `1.0203`, `6/6 > 1`) vs `K2` (`X_2 / kK_2` = `1.0140`, `12/12 > 1`; 6-block prefix `1.0155`, `6/6 > 1`) gives a **`~0.62%` (`1.0062`) SP-PGO build-to-build spread** (`sum(kK_2)/sum(kK_1) = 1.0056`).
- **New SP-PGO leave-one-out builds (all `len = 38`, verified on `312866/862329/4865609`, `882074/4275906`, and `T = 6070/26711499/937e1660561173af` before `prediction1.txt`):**
  - `kK-21` (`/tmp/carbon2_job34/bld_sp_kKm21a/forge`): `exe_sha256 = 2860c60edd59262a1ac7b0811bffab77f5f99285b85901388752f52e7f8494c8`, `profdata_sha256 = 17fb63ba9980e5c3a24336c7672a13da86482c86039a1ecab9b4dfc6890dbfda`
  - `kK-22` (`/tmp/carbon2_job34/bld_sp_kKm22a/forge`): `exe_sha256 = 285db265749c4405acdbe144e526e7707b15f5b70e1e77dbe03821f02c689630`, `profdata_sha256 = a9a3187f7d07f06a8617976ddb24cf45b321dc64f5d1d53f091cb8d0b51e7879`
  - `kK-23` (`/tmp/carbon2_job34/bld_sp_kKm23a/forge`): `exe_sha256 = f93799d9502d23d4eaf01b73779be15d582ef5e8c7e26306bfe0e21732c28746`, `profdata_sha256 = bf6e43c9cfe40dce718a65f704d07ad6bada2c0020b55c7f198137a8850e9dfe`

### Part B Timing Table (`row_B21_raw.txt`, `row_B22_raw.txt`, `row_B23_raw.txt`, `row_BG_raw.txt`, `partB_summary.txt`)

| Row | `A` vs `B` (`B / A`) | Workload & Signature | `6` Block CPU Ratios (`B / A`) | CPU Median | CPU Pooled (`sumB / sumA`) | `95%` `t`-CI (`df=5`) | Blocks `> 1` | Wall Pooled | Reading | Pred. 1 (`prediction1.txt`) |
|---|---|---|---|---:|---:|---|---:|---:|---|---|
| **`B21`** | `kK_1` vs `kK-21` | `T` (`6070/26711499/937e1660561173af`) | `1.0010 1.0025 1.0041 1.0038 1.0037 1.0033` | `1.0035` | **`1.0031`** (`90.4944/90.2188`) | `[1.0018, 1.0043]` | `6/6` | `1.0039` (`6/6`) | **`NOT SEEN`** | `[1.0040, 1.0130]` `SEEN` (**MISS**) |
| **`B22`** | `kK_1` vs `kK-22` | `T` (`6070/26711499/937e1660561173af`) | `1.0143 1.0031 1.0093 1.0083 1.0175 1.0099` | `1.0096` | **`1.0104`** (`91.1209/90.1833`) | `[1.0051, 1.0157]` | `6/6` | `1.0109` (`6/6`) | **`SEEN`** | `[1.0035, 1.0120]` `SEEN` (**HIT**) |
| **`B23`** | `kK_1` vs `kK-23` | `T` (`6070/26711499/937e1660561173af`) | `1.0065 1.0036 0.9981 1.0026 1.0067 1.0008` | `1.0031` | **`1.0030`** (`90.4208/90.1465`) | `[0.9996, 1.0065]` | `5/6` | `1.0023` (`4/6`) | **`NOT SEEN`** | `[0.9990, 1.0075]` `NOT SEEN` (**HIT**) |
| **`BG`** | `kK_1` vs `X_1` | Job 20 `60` whole warm-TT games (`7670/32864906/482831105f59dcec` = info `25641316/ee465caeff9c0fcf`) | `1.0281 1.0261 1.0280 1.0296 1.0286 1.0265` | `1.0281` | **`1.0278`** (`125.6879/122.2874`) | `[1.0264, 1.0292]` | `6/6` | `1.0285` (`6/6`) | **`SEEN`** | *(n/a)* |

- **Additivity check:** `B21 * B22 * B23 = 1.0031 * 1.0104 * 1.0030 =` **`1.0166`** (unrounded `1.0166`), right beside **`K1 / J1 = 1.0203 / 1.0044 = 1.0158`** (difference `0.08%`, well inside the `0.62%` build floor). Piece `22` (`MovePicker` branchless `push_scored` + zero-copy `check_squares_` pointer) carries two-thirds of `{21, 22, 23}`'s speedup (`+1.04%`, **`SEEN`**), while Pieces `21` (`+0.31%`, `6/6 > 1`) and `23` (`+0.30%`, `5/6 > 1`) are individually below the `0.50%` `SEEN` floor (**`NOT SEEN`**) and sum cleanly to the remaining `+0.61%`.
- **Warm whole-game search (`BG` vs `K1`):** In `carbon2`, `T` itself already plays `60` whole self-play games with `U = 60` `ucinewgame`s across `6,070` plies (`Hash 16` warm across plies; `K1` 6-block prefix = **`1.0203`**, `6/6 > 1`, **`SEEN`**). Row **`BG`** tests an independent second `60`-whole-game warm-TT suite (Job 20's `60` book games, `U = 60` `ucinewgame`s across `7,670` plies) and measures **`1.0278` (`+2.78%`, `6/6 > 1`, `SEEN`)**, confirming `kK_1`'s gain over `X_1` holds strongly in warm whole-game play.

---

## 3. Part C — Profile `P2` Outside `Worker::search`, Warm vs Cold Groups, and Control `CP2`

### `P2` Groups, Sum Check with Job 32 `Table P`, Warm/Cold Comparison, and `CP2` (`P2_groups_and_CP2_raw.txt`, `partC_CP2_runs_raw.txt`, `partC_builds_verify.txt`)

- **Builds:** Reused `XG` (`/tmp/carbon2_job32/bld_sp_stXG_1/forge`, `sha256 = 373abed99598c60f3900da33737550b965ef449cf2ec2003943e7af5557657d5`, `KP0 = 1.0015`) and built SP-PGO `-gline-tables-only` **`CP2`** (`/tmp/carbon2_job34/bld_sp_stCP2a/forge`, `sha256 = 02d576ac177440754e4855a401aede7ab9112dc6318b5c4b139ce0ed54690cb3`, `profdata_sha256 = 7beb0b7e28282e1da2de20191aa3004d969ba5fd29a31d0a24da170c7014c054`) adding `CP2_planted_see_ge_muls.patch.txt` (`sha256 = 06c690d5cc838d231db4e7338ae7eb9121d85c56e91f7c80a855323aa576b199`, `28`-step `volatile` multiply loop at `src/board.cpp:1492` in `Board::see_ge`).

| `P2` Group (Outside `Worker::search`) | `J32` `XG` (`perf_XG.data`) | `J34` `XG` (`T` warm, `U=60`) | `CP2` vs `J34` `XG` | `BG` Warm (`j20`, `U=60`) | `T` Cold (`1200`, raw) | `T` Cold (excl. `TT::clear`) |
|---|---:|---:|---:|---:|---:|---:|
| `1a. the net — accumulator update` | `11.69%` (`18,873`) | **`11.64%`** (`18,861`) | `-1.20%` | `13.19%` | `9.13%` | `13.08%` |
| `1b. the net — refresh` | `4.40%` (`7,104`) | **`4.21%`** (`6,816`) | `+1.97%` | `5.20%` | `3.28%` | `4.70%` |
| `1c. the net — forward pass` | `5.32%` (`8,593`) | **`5.16%`** (`8,358`) | `+1.76%` | `5.64%` | `3.83%` | `5.49%` |
| **`1. the net (subtotal = 1a + 1b + 1c)`** | **`21.42%`** (`34,570`) | **`21.00%`** (`34,035`) | **`+0.16%`** | **`24.04%`** | **`16.24%`** | **`23.27%`** |
| **`2. move generation`** | `11.96%` (`19,307`) | **`11.98%`** (`19,418`) | `-0.40%` | `13.26%` | `8.10%` | `11.61%` |
| **`3. the quiescence search`** | `2.03%` (`3,273`) | **`1.96%`** (`3,174`) | `+5.45%` | `3.00%` | `1.38%` | `1.98%` |
| **`4. make and undo outside Worker::search`** | `0.63%` (`1,014`) | **`0.56%`** (`910`) | `-0.44%` | `0.94%` | `0.64%` | `0.92%` |
| **`5. the hash table`** | `2.42%` (`3,905`) | **`2.45%`** (`3,975`) | `+3.07%` | `4.00%` | `32.11%` | `2.73%` |
| **`6. the rest`** | `15.62%` (`25,202`) | **`15.56%`** (`25,216`) | `-6.69%` | `14.38%` | `17.98%` | `25.76%` |
| **SUM `P2` Groups** | **`54.08%`** (`87,271`) | **`53.52%`** (`86,728`) | `-1.64%` | `59.61%` | `76.46%` | `66.27%` |
| **`Worker::search` (`Table P` = `45.92%`)** | **`45.92%`** (`74,110`) | **`46.48%`** (`75,318`) | `-1.20%` | `40.39%` | `23.54%` | `33.73%` |

- **Sum check (`Table P + P2`):** On Job 32's `perf_XG.data` recording (`161,381` samples), `Table P` (`74,110 = 45.9224%`) + `P2` (`87,271 = 54.0776%`) = **`100.00%`** (`diff = 0.00% <= 0.50%`). Across independent recordings (`J32 Table P 45.92% + J34 P2 53.52%`), the sum is **`99.44%`** (`diff = 0.56%`, while `J34 WS 46.48% + J34 P2 53.52% = 100.00%`).
- **Control `CP2` (`partC_CP2_runs_raw.txt`, `P2_groups_and_CP2_raw.txt`):**
  - **True cost (`6` paired runs):** Mean `CPU(XG) = 7.679308 s`, Mean `CPU(CP2) = 7.855141 s` $\to$ **`+0.175834 s` (`+2.29%` of `T`, median pair `+0.188465 s` = `+2.46%`)**.
  - **Group invariance (`<= 10%` bar):** **PASSES** — maximum group shift across all `6` groups and `8` sub-lines is **`6.69%`** (`-6.69%` on `6. the rest`, `+5.45%` on `3. qsearch`, `+3.07%` on `5. hash`, `+0.16%` on `1. the net`, `-0.40%` on `2. move generation`, `-0.44%` on `4. make/undo`).
  - **Planted-cost size (`<= 25%` bar):** **FAILS** — `Board::see_ge` jumped from `3,358` to `9,627` samples (`+6,269` samples = `0.313450 s` at `50 us`/sample = **`+78.26%`** raw, or `0.294013 s` = **`+67.21%`** scaled; planted line `src/board.cpp:1492` got `7,765` samples = `+120.80%` raw / `+107.11%` scaled) because the serial `volatile` RMW loop at `Board::see_ge` entry absorbed ~`4,000` samples of pending ROB/skid from the surrounding `see_ge` body (`-1,496` samples), `6. the rest` (`-1,688`), and `Worker::search` (`-901`).
  - **Declared `CP2` verdict:** **`NOT TRUSTED`**. `NOT TRUSTED` is written on `P2`'s source-line table (`P2_outside_search_raw.txt`), and nothing below the function level is used.

### Functions Outside `Worker::search` Above `0.50%` of `T` (`P2_outside_search_raw.txt`)

| Rk | `J34` `%T` (`Samp`) | `J32` `%T` (`Samp`) | Function (inlined code counted at source function) | Rk | `J34` `%T` (`Samp`) | `J32` `%T` (`Samp`) | Function |
|---:|---:|---:|---|---:|---:|---:|---|
| `1` | `6.32%` (`10,241`) | `6.49%` (`10,469`) | `forge::nnue::v3::apply_pair_and_evaluate` | `15` | `0.78%` (`1,257`) | `0.78%` (`1,263`) | `forge::MovePicker::generate_movies_lambda` |
| `2` | `5.72%` (`9,265`) | `6.05%` (`9,768`) | `forge::nnue::v3::apply_one_refresh_one_and_evaluate` | `16` | `0.77%` (`1,255`) | `0.78%` (`1,261`) | `forge::Worker::static_evaluate_v3` |
| `3` | `2.07%` (`3,358`) | `2.10%` (`3,397`) | `forge::Board::see_ge` | `17` | `0.75%` (`1,209`) | `0.77%` (`1,240`) | `forge::MovePicker::QuietScorer::extra` |
| `4` | `1.96%` (`3,184`) | `1.90%` (`3,074`) | `forge::nnue::v3::apply_changes_pair_avx512` | `18` | `0.74%` (`1,204`) | `0.73%` (`1,186`) | `forge::MovePicker::push_scored` |
| `5` | `1.68%` (`2,721`) | `1.62%` (`2,607`) | `forge::(anon)::square_attacked_with_occupancy` | `19` | `0.69%` (`1,126`) | `0.69%` (`1,115`) | `forge::MovePicker::generate_evasions` |
| `6` | `1.67%` (`2,706`) | `1.62%` (`2,620`) | `forge::Board::upcoming_repetition` | `20` | `0.68%` (`1,108`) | `0.66%` (`1,073`) | `forge::nnue::v3::finish` |
| `7` | `1.65%` (`2,673`) | `1.60%` (`2,575`) | `forge::Worker::ensure_piece_diff` | `21` | `0.62%` (`1,004`) | `0.63%` (`1,020`) | `forge::MovePicker::generate_captures` |
| `8` | `1.50%` (`2,426`) | `1.51%` (`2,430`) | `forge::Board::has_legal_move` | `22` | `0.60%` (`968`) | `0.54%` (`878`) | `forge::attacks::bishop` |
| `9` | `1.45%` (`2,351`) | `1.52%` (`2,450`) | `std::__introsort_loop<MovePicker::Scored*>` | `23` | `0.59%` (`948`) | `0.61%` (`984`) | `_raw_spin_unlock_irqrestore` (`[kernel]`) |
| `10` | `1.31%` (`2,129`) | `1.34%` (`2,168`) | `forge::MovePicker::generate_quiets()::lambda` | `24` | `0.58%` (`932`) | `0.52%` (`834`) | `forge::Board::generate_legal_evasions` |
| `11` | `0.97%` (`1,569`) | `0.99%` (`1,605`) | `forge::TranspositionTable::probe_owned_fast` | `25` | `0.56%` (`915`) | `0.57%` (`924`) | `forge::nnue::v3::hsum_epi32_pair_avx512` |
| `12` | `0.97%` (`1,566`) | `0.96%` (`1,550`) | `forge::nnue::v3::refresh_from_pieces` | `26` | `0.53%` (`863`) | `0.55%` (`887`) | `forge::Board::pieces` |
| `13` | `0.86%` (`1,389`) | `0.92%` (`1,477`) | `forge::Worker::qsearch` | `27` | `0.52%` (`837`) | `0.49%` (`786`) | `forge::Board::is_pseudo_legal` |
| `14` | `0.85%` (`1,382`) | `0.87%` (`1,399`) | `forge::Worker::corrected_eval` | | | | |

### Three Hottest Source Lines of the Five Largest Functions — **`NOT TRUSTED`** (`P2_outside_search_raw.txt`)
*(Marked **`NOT TRUSTED`** because `CP2` failed the `<= 25%` planted-size check; reported as required, never used below the function level.)*
1. **`forge::nnue::v3::apply_pair_and_evaluate` (`6.32%`):** `src/nnue_v3.cpp:933` (`1.20%`, `sum1 = _mm512_add_epi32(...)`), `src/nnue_v3.cpp:924` (`0.77%`, `_mm512_store_si512(destination0 + h, v0)`), `src/nnue_v3.cpp:929` (`0.63%`, `_mm512_store_si512(destination1 + h, v1)`).
2. **`forge::nnue::v3::apply_one_refresh_one_and_evaluate` (`5.72%`):** `src/nnue_v3.cpp:1088` (`1.05%`, `for (; a < n_add; ++a)`), `src/nnue_v3.cpp:1078` (`0.54%`, `for (; s < n_sub; ++s)`), `src/nnue_v3.cpp:1050` (`0.38%`, `for (int h = 0; h < hidden; h += 32)`).
3. **`forge::Board::see_ge` (`2.07%`):** `src/board.cpp:1508` (`0.34%`, `int swap = SeeValue[...] - threshold;`), `src/board.cpp:1553` (`0.18%`, `r_atk = attacks::rook(...) & lines`), `src/board.cpp:1552` (`0.13%`, `b_atk = attacks::bishop(...) & diagonals`).
4. **`forge::nnue::v3::apply_changes_pair_avx512` (`1.96%`):** `src/nnue_v3.cpp:390` (`0.51%`, `_mm512_store_si512(destination0 + h, v0)`), `src/nnue_v3.cpp:395` (`0.46%`, `_mm512_store_si512(destination1 + h, v1)`), `src/nnue_v3.cpp:386` (`0.23%`, `const __m512i v0 = _mm512_add_epi16(`).
5. **`forge::(anon)::square_attacked_with_occupancy` (`1.68%`):** `src/board.cpp:427` (`0.69%`, `attacks::rook(square, occupancy) & ...`), `src/board.cpp:426` (`0.66%`, `attacks::bishop(square, occupancy) & ...`), `src/board.cpp:422` (`0.21%`, `attacks::pawn(opposite(by), square) & ...`).

---

## 4. Facts, Suspicions, What I Did Not Do, and What I Am Not Sure About

- **Facts:**
  1. `kF` equals `forge/r15f` (`29/29` files), and `stack_kF_to_kK.patch.txt` (`1,921` lines, `82` hunks) applied to `kF` equals `kK` (`29/29` files).
  2. `8` of the `82` hunks (`#10, #15, #40, #46, #47, #73, #74, #75`) have `none` coverage under `depth`/`nodes`/`softnodes` known answers and require direct human review on the PC (especially `#73` `root_move_nodes_` for clocked play and `#75` abort PV publish).
  3. On `kK`, `B22` (`1.0104`, `6/6 > 1`, `SEEN`) is the dominant piece in `{21, 22, 23}`, while `B21` (`1.0031`, `6/6 > 1`, `NOT SEEN`) and `B23` (`1.0030`, `5/6 > 1`, `NOT SEEN`) sit below the single-build floor individually; `B21 * B22 * B23 = 1.0166` matches `K1 / J1 = 1.0158` within `0.08%`.
  4. On warm whole-game play, `kK_1` beats `X_1` on both 60-game suites: `K1 = 1.0203` (`T`) and `BG = 1.0278` (`6/6 > 1`, `SEEN`, Job 20's 60 whole games).
  5. Outside `Worker::search` (`53.52%` / `54.08%` of `T`), **the net** is `21.00%` / `21.42%` of `T` (`11.64%` accumulator update, `4.21%` refresh, `5.16%` forward pass), **the rest** is `15.56%` / `15.62%`, and **move generation** is `11.98%` / `11.96%`.
- **Suspicions:**
  1. Software timer `perf -e task-clock` (without PEBS precise-IP hardware counters on this VM) systematically over-attributes serial `volatile` dependency loops (`CP2` `+67%` to `+78%`) because out-of-order memory/ROB stalls immediately preceding the loop retire and get sampled while the serial loop drains the pipeline, even when macro-group totals remain invariant (`max = 6.69% <= 10%`).
  2. On the `9850X3D` (`96 MiB` V-Cache, `16` concurrent self-play processes), `BG`'s larger warm-game gain (`+2.78%` vs `+2.03%`) suggests `kK`'s reduced per-ply stack/undo footprint (`15, 22, 23`) and branchless `MovePicker` (`22`) help more in deeper middle-game move lists (`7,670` plies) than in opening-heavy positions.
- **What I did not do:**
  - Did not rebuild `kK` or `XG` (reused verified binaries per Step 0 / Part A2 / Part C rules).
  - Did not profile `kK` itself in Part C (`P2` was run on `XG = X + -gline-tables-only` so `Table P + P2` partitions the exact same `X` baseline as Job 32's `Table P`; note Pieces `19..23` already target several `P` and `P2` functions on `X`).
- **What I am not sure about:**
  - Whether `Piece 21`'s `5x PREFETCHT2` (`__builtin_prefetch(..., 0, 1)`) helps, is neutral (`+0.31%` on Sapphire Rapids was below `0.50%`), or hurts under `16`-thread SMT on Zen 5's `48 KiB` L1d / `1 MiB` L2.
  - How MinGW `libstdc++` `basic_filebuf::underflow` behaves with `sync_with_stdio(false)` (`Hunk #82`) over Windows anonymous pipes — interactive UCI must be smoke-tested immediately on the PC.

---

## WHAT I WOULD DO NEXT

*(At most five pieces; selected strictly at the function / group level because both `CP` and `CP2` read `NOT TRUSTED` below the function level; no code.)*

1. **Eliminate full `std::sort` tail fallback in `MovePicker` (`pick_best_scored` / `sort_moves`):**
   - **Group touched:** `Table P` `#5 move scoring and history reads` (`11.24%` of `T`) + `P2` `(2) move generation` (`11.98%` of `T`, specifically `std::__introsort_loop<MovePicker::Scored*>` at `1.45%`–`1.52%` outside `Worker::search` plus `2.90%` inside `Worker::search`).
   - **Max share of `T` at best:** **`~4.4%` of `T`** (all `std::sort` / introsort time across `P` and `P2`, since most nodes cut off long before exhausting the quiet move list after the first `4` selection picks).
   - **Lines the PC would have to read:** **`~35` lines**.
   - **Needs the machine (`A5`'s sense)?** **YES (mild)** — the optimal cutoff `K` between SIMD argmax selection picks and full sorting depends on Zen 5's AVX-512 `vpmaxsd`/`vpcmpeqd` latency vs scalar swap throughput.
2. **Pre-pack / quantize `nnue::v3` L2 output weights (`w2`) for `VPMADDWD` (`int8` or paired `int16`) forward pass:**
   - **Group touched:** `P2` `(1c) the net — forward pass` (`5.16%`–`5.32%` of `T` across `apply_pair_and_evaluate`, `apply_one_refresh_one_and_evaluate`, `output_sum_avx512`, `hsum_epi32_pair_avx512`, and `finish`).
   - **Max share of `T` at best:** **`~5.2%` of `T`**.
   - **Lines the PC would have to read:** **`~90` lines** (plus proving exact integer overflow bounds so no `int16`/`int32` lane can wrap differently from `r15f`).
   - **Needs the machine (`A5`'s sense)?** **YES** — relies on 512-bit `AVX-512BW` (or `AVX-512VNNI` on Zen 5, which has native 512-bit `vpdpbusd` / `vpmaddwd` pipes) and `64`-byte alignment.
3. **Defer `Worker::ensure_piece_diff` / `DirtyPieces` construction until an evaluation actually runs:**
   - **Group touched:** `P2` `(1a) the net — accumulator update` (`ensure_piece_diff` `1.60%`–`1.65%` of `T`) + `Table P` `#6` (`record_move` stack writes).
   - **Max share of `T` at best:** **`~1.7%` of `T`**.
   - **Lines the PC would have to read:** **`~55` lines**.
   - **Needs the machine (`A5`'s sense)?** **NO** — pure node-keeping work deferral (computing piece diffs only on evaluated paths or storing compact move/piece metadata already in `SearchStack`).
4. **Fast-path `Board::see_ge` and `square_attacked_with_occupancy` for uncontested / single-recapture exchanges:**
   - **Group touched:** `P2` `(6) the rest` (`Board::see_ge` `2.07%`–`2.10%` + `square_attacked_with_occupancy` `1.62%`–`1.68%` of `T`).
   - **Max share of `T` at best:** **`~3.7%` of `T`**.
   - **Lines the PC would have to read:** **`~70` lines**.
   - **Needs the machine (`A5`'s sense)?** **NO** (aside from `BMI2` `PEXT` slider lookups already active in `r15f`).
5. **Shrink self-play `Hash` per worker on the PC (config test on the `16`-engine loop, not an engine patch):**
   - **Group touched:** `Table P` `#1/#2` (`hash probe` + `hash store`, `5.33%` of `T`) + `P2` `(5) the hash table` (`2.45%`–`4.00%` of `T`) + cross-core LLC misses across all memory-touching groups.
   - **Max share of `T` at best:** **`~3.4%–4.1%` of `T`** (measured directly in Job 32 Part Q at `Hash 2`–`4` MB vs `Hash 16` MB; note this **changes search nodes**, unlike items 1–4, so on `9850X3D` with `96 MiB` V-Cache where `16 * 4 MiB = 64 MiB` fits inside L3 while `16 * 16 MiB = 256 MiB` spills L3, it must be Elo-checked on the PC).
   - **Lines the PC would have to read:** **`0` engine lines** (`1` driver option line).
   - **Needs the machine (`A5`'s sense)?** **YES (strongly)** — governed directly by `9850X3D`'s `96 MiB` shared 3D V-Cache capacity across `16` concurrent self-play processes.

---

**Model:** `Gemini 4 Carbon`
