# REPORT — `carbon2` Job 18: Consolidated Diff Switch Audit (`Part 0`) and `Board::see_ge` Pawn-Recapture Early Exit (`Part 1`)

- **Agent / Branch:** `carbon2` on `for-fable-and-opus/carbon2-work` (no engine source modified in-tree; no binaries, `.fnn3` nets, or `.profraw`/`.profdata` files committed; **no pull request opened**).
- **Kept stack status after Job 18:** Unchanged at **`job17/stack_r15d_to_final.patch.txt`** (`01..13 + tidy`, `2,450` lines, `sha256=3d2ce0852fe18d9953fb446950aa90fb67dbdb768c2e229a193e918e54beeb63`). Part 1 (`stack/16_see_pawn_exit.patch.txt`, `27` lines) is node/move/eval/SEE-identical (`0` diffs across `188,608` oracle calls and all identity checks; both per-path controls caught), and measured **`0.9943x` (`-0.57%`) CPU (`4/12` blocks faster)** on 12x60 `Hash 16` ABBA -> **killed by our `>= 1.0040x` gate**.

---

## 0. Step 0 & Build Audit (`s16_build_and_step0_raw.txt`)

- **Compiler & Linker:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), ThinLTO (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, linked against GNU `libstdc++.so.6` (`/lib/x86_64-linux-gnu/libstdc++.so.6`).
- **Architecture & Compile Switches:** `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread`.
- **AVX-512 `ZMM` verification:** `objdump -d /tmp/carbon2_job18/bld_sp_s16_1/forge | grep -c '%zmm'` = **`1420`** `ZMM` instructions; runtime active line confirms `kernel avx512`.
- **SP-PGO Profile Protocol (identical across all 4 timed binaries):**
  - **Baseline `A1`, `A2` (`01..13 + tidy`, built in `/tmp/carbon2_job17/bld_sp_tidy_{1,2}/forge`):**
    - `A1` sha256: `6ac9c36ceae1c8c79721b84bd5d395dd967c41723586a0b3e3cdcc1a7b5f7091` (`827,616` bytes)
    - `A2` sha256: `7ef7c7e32820eb30757cdcde8b292860dda4d1f499b842e4537bfbebbd9104de` (`827,592` bytes)
  - **Candidate `B1`, `B2` (`01..13 + tidy + 16_see_pawn_exit`, built in `/tmp/carbon2_job18/bld_sp_s16_{1,2}/forge`):**
    - `B1` sha256: `7b26f5610a741f4f5845d1fbb5c6f2ca3c73708bdc5fdbdf5ca6914d867b3820` (`828,056` bytes)
    - `B2` sha256: `72d23ed9b33331e5118e47abc08120e7b43e984adde8e729329a10d42f57ed34` (`827,992` bytes)
  - **Profile files merged per binary:** **`2` `.profraw` files** merged via `llvm-profdata-18 merge` into `forge.profdata`:
    1. Phase 2a (`bench 11`, `bench 13`, `bench 16` with `net768.fnn3` + 4 speed switches: `1,261,644` / `6,312,262` / `74,843,992` nodes).
    2. Phase 2b (`60` disjoint self-play games, `disjoint_from_timing_60=True`, `go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`): **`games = 60`, `searches = 5,531`, `nodes = 18,059,934`, `trace = 1646ce4566de2f40`**.

---

## 1. Part 0: Switch & Default-`#define` Table of `job17/stack_r15d_to_final.patch.txt` (`part0_switch_table_raw.txt`)

Full 46-row line-by-line audit committed in `forge-combo29/carbon2/job18/part0_switch_table_raw.txt` (`4fbeaf730`, completed in 21 minutes). Both the PC compile line (`-march=znver5`) and our Xeon compile line (`-march=sapphirerapids`) evaluate every preprocessor condition identically (`NDEBUG=1`, `__AVX2__=1`, `__AVX512F__=1`, `__AVX512BW__=1`, `__BMI2__=1`, `__SIZEOF_INT128__=16`, `FORGE_NNUE_V3_AVX512=1`).

### 1A. Complete 46-Row Switch & Changed-Default Table

| # | File | Diff Line(s) | Condition / Changed Default | PC (`znver5`) | Ours (`sapphirerapids`) | Added (`+`) Lines Compiled by PC? |
|---:|---|---|---|---|---|---|
| 1 | `include/forge/board.hpp` | `L57..L62` | `#if FORGE_SPD_KING_LINES` (default `1` at `board.hpp:73`) | `1` | `1` | **YES** (`L58-L61`, `ensure_king_lines()`) |
| 2 | `include/forge/search.hpp` | `L156..L158` | `#if defined(__AVX512F__)` | `1` | `1` | **YES** (`L157`, `#include <immintrin.h>`) |
| 3 | `include/forge/search.hpp` | `L192..L261` | `#if FORGE_SPD_TT_NOTLS` (`-DFORGE_SPD_TT_NOTLS=1`) | `1` | `1` | **YES** (`L199-L237, L259-L260`; `#else` in row 5: **NO**) |
| 4 | `include/forge/search.hpp` | `L215..L237` | `#if defined(__AVX512F__)` (`probe_owned_fast`) | `1` | `1` | **YES** (`L216-L237`) |
| 5 | `include/forge/search.hpp` | `L238..L259` | `#else` (of `#if defined(__AVX512F__)` at `L215`) | `0` | `0` | **NO** (`L239-L258`, 20-line scalar fallback) |
| 6 | `include/forge/search.hpp` | `L280..L287` | `#if defined(__SIZEOF_INT128__)` / `#else` (`cluster_index`) | `#if`=true, `#else`=false | `#if`=true, `#else`=false | `#if` (`L282-L283`): **YES**; `#else` (`L286`, 1 line): **NO** |
| 7 | `include/forge/search.hpp` | `L335..L337` | `#if FORGE_NNUE_V3` (`-DFORGE_NNUE_V3=1`) | `1` | `1` | **YES** (`L336`, `v3_active_net_`) |
| 8 | `include/forge/search.hpp` | `L341..L364` | `#if FORGE_SPD_TT_NOTLS` (`Worker::probe_tt` / `store_tt`) | `1` | `1` | **YES** (`L350-L362`) |
| 9 | `src/board.cpp` | `L414..L426` | `#if FORGE_SPD_KING_LINES` / `#else` (`has_legal_move`) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L419-L421`): **YES**; `#else` (`L425`, 1 line): **NO** |
| 10 | `src/board.cpp` | `L441..L445` | `#if FORGE_SPD_KING_LINES` (`Board::make_move`) | `1` | `1` | **YES** (`L443-L444`) |
| 11–19 | `src/board.cpp` | `L447..L541` (9 blocks) | `#ifndef NDEBUG` (`-DNDEBUG` on compile line) | `0` | `0` | **NO** (`21` `+` lines of `dbg_key` incremental Zobrist assertions; compiled only when `-DNDEBUG` is omitted, as in Job 14 Part 1) |
| 20 | `src/board.cpp` | `L566` | `assert(compute_checkers() == 0);` (`<cassert>` under `-DNDEBUG`) | macro no-op | macro no-op | Line parsed; expands to `((void)0)` under `-DNDEBUG` |
| 21 | `src/board.cpp` | `L584..L608` | `#if FORGE_SPD_KING_LINES` (`unmake_move` / `make_null_move` / `unmake_null_move`) | `1` | `1` | **YES** (`L586-L587, L596-L597, L606-L607`) |
| 22 | `src/board.cpp` | `L631, L638..L649` | **`#if FORGE_SDK_SEE_HOIST` / `#else` (default `1` at `board.cpp:14` — Known Answer ii)** | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | **`#else` (`L638-L648`, 11 lines pawn early exit): NO (uncompiled in all builds!)** |
| 23 | `src/nnue_v3.cpp` | `L667..L917` | Enclosing `#if FORGE_NNUE_V3` (`nnue_v3.cpp:3`) | `1` | `1` | **YES** (except row 25 `#else` and row 26 `#else`) |
| 24 | `src/nnue_v3.cpp` | `L725..L833` | `#if FORGE_NNUE_V3_AVX512` (`apply_one_refresh_one_and_evaluate`) | `1` | `1` | **YES** (`L726-L833`) |
| 25 | `src/nnue_v3.cpp` | `L834..L840` | `#else` (of `#if FORGE_NNUE_V3_AVX512` at `L725`) | `0` | `0` | **NO** (`L835-L839`, 5-line scalar fallback) |
| 26 | `src/nnue_v3.cpp` | `L849..L908` | `#if FORGE_NNUE_V3_AVX512` / `#else` (`refresh_from_pieces`) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L853..L900`): **YES**; `#else` (`L907`, 1 line): **NO** |
| 27 | `src/search.cpp` | `L923..L926` | **`#ifndef FORGE_SDK_BADCAP_PREFIX` default changed `0` -> `1` (Known Answer i)** | `1` | `1` | **YES** (`L925`, activates 4 `r15d` blocks in Section 1B) |
| 28 | `src/search.cpp` | `L929..L1066` | Enclosing `#if FORGE_SPD_TT_NOTLS` (`search.cpp:465`) | `1` | `1` | **YES** (except row 30 `#else`) |
| 29 | `src/search.cpp` | `L986..L993` | `#if defined(__AVX512F__)` (`store_owned_fast`) | `1` | `1` | **YES** (`L987-L993`) |
| 30 | `src/search.cpp` | `L994..L1001` | `#else` (of `#if defined(__AVX512F__)` at `L986`) | `0` | `0` | **NO** (`L995-L1000`, 6-line scalar fallback) |
| 31 | `src/search.cpp` | `L1077..L1086` | `#if FORGE_SPD_KING_LINES` / `#else` (`MovePicker::next` legality) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L1078-L1083`): **YES**; `#else` (`L1085`, 1 line): **NO** |
| 32 | `src/search.cpp` | `L1089..L1096` | `#if FORGE_SPD_KING_LINES` / `#else` (`MovePicker::next` `gives_check`) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L1090-L1093`): **YES**; `#else` (`L1095`, 1 line): **NO** |
| 33 | `src/search.cpp` | `L1133..L1138` | `#if FORGE_SPD_KING_LINES` (`MovePicker` cached fields) | `1` | `1` | **YES** (`L1134-L1137`) |
| 34 | `src/search.cpp` | `L1149..L1165` | `#if FORGE_SPD_KING_LINES` / `#else` (`init_check_squares`) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L1150-L1156`): **YES** (`0` `+` lines in `#else`) |
| 35 | `src/search.cpp` | `L1174` | Enclosing `#if FORGE_SEARCH_SPEED2` (`search.cpp:1054`) | `1` | `1` | **YES** (`L1174`) |
| 36 | `src/search.cpp` | `L1196..L1230` | `#if defined(__AVX512F__)` (`pick_best_scored`) | `1` | `1` | **YES** (`L1197-L1229`) |
| 37 | `src/search.cpp` | `L1258..L1359` | `#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2` / `#else` (`generate_captures`) | `#if`=true, `#else`=false | `#if`=true, `#else`=false | `#if` (`L1259-L1342`): **YES**; `#else` (`L1344-L1346, L1351`, 4 `+` lines): **NO** |
| 38 | `src/search.cpp` | `L1367..L1597` | `#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2` / `#elif FORGE_SPD_NO_ZERO_MOVELISTS >= 2` / `#else` (`generate_quiets`) | `#if`=true, `#elif`/`#else`=false | `#if`=true, `#elif`/`#else`=false | `#if` (`L1368..L1557`): **YES**; `#elif` (`L1559-L1566`, 8 `+` lines) & `#else` (`L1574..L1592`, 5 `+` lines): **NO** |
| 39 | `src/search.cpp` | `L1663..L1665` | `#if FORGE_PAWN_HISTORY` (default `0` at `search.cpp:36`) | `0` | `0` | Context only (`0` `+` lines) |
| 40 | `src/search.cpp` | `L1704..L2044` (6 hunks) | `#if FORGE_NNUE_V3` (`-DFORGE_NNUE_V3=1`) | `1` | `1` | **YES** (`0` `+` lines in `#else` at `L1958`) |
| 41 | `src/search.cpp` | `L1821..L1878` | `#if FORGE_TEST_CLOCK_STOP` (unset -> `0`) | `0` | `0` | Context only (`0` `+` lines) |
| 42 | `src/search.cpp` | `L1827..L1946` | `#if FORGE_SPD_TT_NOTLS` / `#else` (`probe_tt` sites) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L1829, L1884, L1943`): **YES** (`0` `+` lines in `#else`) |
| 43 | `src/search.cpp` | `L1861..L1921` | `#if FORGE_SPD_PREFETCH_EARLY` / `#else` | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L1862, L1915`): **YES**; `#else` (`L1866, L1919`, 2 `+` lines): **NO** |
| 44 | `src/search.cpp` | `L1897` | `#if FORGE_SPD_NO_ZERO_MOVELISTS` (`2` -> true) | `2` (true) | `2` (true) | Context only (adjacent `L1892` outside `#if`: **YES**) |
| 45 | `src/uci.cpp` | `L2249..L2352` | `#if FORGE_FIX_GO_PARSE` / `#else` (default `1` at `uci.cpp:31`) | `#if`=`1`, `#else`=`0` | `#if`=`1`, `#else`=`0` | `#if` (`L2263..L2304`): **YES**; `#else` (`L2315..L2349`, 8 `+` lines): **NO** |
| 46 | `src/uci.cpp` | `L2410..L2441` | `#if FORGE_NNUE_V3` (`-DFORGE_NNUE_V3=1`) | `1` | `1` | Adjacent `+` lines (`L2416, L2443-L2446`) sit outside `#endif`: **YES** |

### 1B. Base-Tree (`r15d`) Blocks Turned On by Changed Default `#define` & Known Answers

- **Only changed default `#define`:** `src/search.cpp:24` (`diff:L924-L925`) `#define FORGE_SDK_BADCAP_PREFIX 0` -> `#define FORGE_SDK_BADCAP_PREFIX 1`.
- **All `r15d` blocks turned on (`4` blocks in `src/search.cpp`):**
  1. `src/search.cpp:725-730` (`MovePicker::next`, `Stage::GoodCaptures`): compiles `moves_[bad_count_++].move = move;` (`L727`) instead of `bad_captures_[bad_count_++] = move;` (`L729`).
  2. `src/search.cpp:769-773` (`MovePicker::next`, `Stage::BadCaptures`): compiles `if (bad_index_ < bad_count_) return moves_[bad_index_++].move;` (`L770`) instead of `bad_captures_[bad_index_++]` (`L772`).
  3. `src/search.cpp:846-854` (`MovePicker` members): selects empty `#if FORGE_SDK_BADCAP_PREFIX` (`L846-L847`), turning off `std::array<Move, MoveList::Capacity> bad_captures_;` (`L848-L854`).
  4. `src/search.cpp:1023-1027` (`MovePicker::quiet_start()`): compiles `return bad_count_;` (`L1024`) instead of `return 0;` (`L1026`).
- **Known Answers:** **(i) MET** (`FORGE_SDK_BADCAP_PREFIX 0 -> 1` and its 4 `r15d` blocks above) and **(ii) MET** (`src/board.cpp` `diff:L638-L648` dead `#else` under `#if FORGE_SDK_SEE_HOIST`, default `1` at `src/board.cpp:14`).
- **Additional findings:** Apart from `(ii)` (an unintended dead `#else` placement), the remaining uncompiled `+` lines under the PC's release flags are intentional debug assertions (`9` `#ifndef NDEBUG` hunks in `src/board.cpp`) and portability/switch-off `#else`/`#elif` fallbacks (non-AVX-512, non-`__int128`, and legacy switch-0 branches listed in rows `5, 6, 9, 25, 26, 30, 31, 32, 37, 38, 43, 45`).

---

## 2. Part 1 (`stack/16_see_pawn_exit.patch.txt`) and Part 2 Budget Decision

### 2A. Part 1: `stack/16_see_pawn_exit.patch.txt` (`27` lines on `01..13 + tidy`)
- **Target function & time share:** `Board::see_ge` (`src/board.cpp:1536-1550`), `11.15%` caller-inclusive self-play CPU (`936 / 8,391` samples in `job13/curated_sp_time_profile_raw.txt`).
- **What it removes:** Deletes the uncompiled `#else` copy of the pawn-recapture early exit (`src/board.cpp:1539-1549`) and places the early exit inside `#if FORGE_SDK_SEE_HOIST`:
  - **Path 1 (`((contact[them_idx] | snipers[them_idx]) & live0) == 0`):** immediately returns `false`, skipping `attacks::bishop(to, occupancy)` (`_pext_u64`), `attacks::rook(to, occupancy)` (`_pext_u64`), `us_contact`, loop entry, and `legal_least_valuable_attacker`.
  - **Path 2 (`((contact[them_idx] | snipers[them_idx]) & live0) != 0`):** sets `prepared = 1U << them_idx;` so step 1 of the exchange loop reuses `contact[them_idx]` and `snipers[them_idx]` without recomputing them.
- **Pre-step counts over 60 `Hash 16` SP games (`part1_see_pawn_exit_counts_raw.txt`, commit `550eaee2e`, `7,670` searches, `25,641,316` nodes, `trace=ee465caeff9c0fcf`):**
  - Total `Board::see_ge` calls: **`28,186,285`** (`1.099` calls/node)
  - Earlier exits: `exit_castle=3,853`, `exit_promo_recap=35,637`, `exit_swap_lt0=278,492`, `exit_atk_le0=8,945,665`, `exit_no_them=10,775,625` (sum `20,039,272` = `71.10%`)
  - **`reaches_point`** (reaches `#if FORGE_SDK_SEE_HOIST`): **`8,147,013`** (**`28.90%`** of all `see_ge` calls)
  - **`pawn_candidate`** (`them_pawns_atk != 0 && SeeValue[Pawn] - swap < 0`): **`1,399,964`** (**`17.18%`** of `8,147,013`)
  - **`pawn_exit_decides_false`** (Path 1 immediate `return false`): **`1,229,301`** (**`15.09%`** of `8,147,013`; **`87.81%`** of pawn candidates)
  - **`pawn_needs_pin_loop`** (Path 2 enters loop with `prepared` bit set): **`170,663`** (**`2.09%`** of `8,147,013`; **`12.19%`** of pawn candidates)
- **Standalone pre-committed prediction (`prediction_16_see_pawn_exit.txt`, commit `6c5c2d6d2`, `1` file changed, stamped immediately at `14:56:30 UTC`):** Predicted `+0.20%` to `+0.55%` (`1.0020x` to `1.0055x`, point `+0.35%`); declared keep gate `>= 1.0040x` CPU and `>= 8/12` blocks with `0` identity/oracle diffs.
- **Identity & differential SEE oracle (`s16_identity_raw.txt`, `s16_see_oracle_and_controls_raw.txt`):**
  - `test_s16_see_pawn_exit_oracle.cpp` (`1,008` FENs x all `Board::pseudo_legal_moves(false)` = `26,944` moves x `7` thresholds `{-350, -100, -1, 0, 1, 100, 350}` = **`188,608` calls**): `r15d`, `01..13 + tidy`, and `+ 16_see_pawn_exit` all give **`HASH=a557282d3d4c5efe` (`0` diffs)**.
  - Full engine identity: `PC20+net512` `bench 11/13/16 = 625,258 / 3,652,372 / 23,891,329`; `PC20+net768` (`B1` & `B2`) `bench 11/13/16 = 882,074 / 4,275,906 / 32,374,943`; `250` depth-9 rows `node_sum = 4,332,153`, `rows_sha256 = 4124a7d4eadfaae4bc811c98f188a814adc26af08cdfe9a669f8e2ecb3816a18` (strict self-stop guard active; row `#088` root checkmate `bestmove=0000 nodes=0 score=mate 0`); `1,000` static evals `net768 sha256 = a702fa75...`, `net512 sha256 = 489220db...`; 6-game traces `4560d7c3afdeba2e` and `9ed22c1193ab96de` (**`0` diffs**).
  - **Per-path controls (`2/2` caught):**
    1. `s16_control1_path1_early_exit.patch.txt` (Path 1 omits `| snipers[them_idx]` in early exit): **`12` oracle move-mask mismatches** (first `246|c4e3|0f` vs `01`) and `PC20+net768 bench 11` shifts `882,074 -> 738,303` (**CAUGHT**).
    2. `s16_control2_path2_prepared_cache.patch.txt` (Path 1 exact, Path 2 leaves `snipers[them_idx] = 0` while setting `prepared = 1U << them_idx`): **`12` oracle move-mask mismatches** (first `246|c4e3|0f` vs `01`) and `PC20+net768 bench 11` shifts `882,074 -> 738,303` (**CAUGHT**).
- **12x60 `Hash 16` ABBA timing (`s16_see_pawn_exit_12x60_hash16_raw.txt`, `48` runs, all `trace=ee465caeff9c0fcf`, `START_UTC: 15:35:27 UTC`, `END_UTC: 15:45:18 UTC`):**
  - **CPU (`rusage_cpu_sps`):** per-round paired ratios `[0.9976, 1.0026, 0.9910, 0.9897, 0.9910, 0.9804, 1.0005, 0.9857, 1.0071, 1.0067, 0.9980, 0.9887]`; **median `0.9943x` (`-0.57%`)**, **`4/12` rounds faster**, 95% CI `[0.9892x, 1.0016x]`; pooled median ratio `0.9935x` (`-0.65%`), 95% CI `[0.9886x, 0.9990x]`; A/A controls `median(A2)/median(A1) = 1.0027` (per-round range `[0.9818, 1.0352]`), `median(B2)/median(B1) = 1.0054` (per-round range `[0.9977, 1.0382]`).
  - **Wall (`wall_sps`):** per-round paired ratios `[0.9971, 1.0025, 0.9969, 0.9891, 0.9793, 0.9776, 0.9917, 0.9882, 1.0062, 1.0025, 1.0044, 0.9894]`; **median `0.9943x` (`-0.57%`)**, **`4/12` rounds faster**, 95% CI `[0.9887x, 1.0025x]`; A/A per-round ranges `A2/A1 [0.9801, 1.0290]`, `B2/B1 [0.9936, 1.0363]`.
  - **Decision & root cause:** **KILLED** (`0.9943x` < `1.0040x` gate). Under `-DFORGE_SPD_SLIDER_PEXT=1`, the two PEXT slider lookups at `src/board.cpp:1552-1553` cost ~`6` cycles, whereas guarding them with a `17.18% / 82.82%` data-dependent branch (`them_pawns_atk != 0 && SeeValue[Pawn] - swap < 0`) plus `king_square(them)`, 5 attack-table loads, and live `contact[2]`/`snipers[2]`/`prepared` across the pre-loop region (`+440` bytes in the SP-PGO binary) loses more in branch mispredictions than the `15.09%` early exit saves.

### 2B. Part 2 (`TranspositionTable::clear` by `std::memset`) — Deferred by Budget Rule
- Part 1's 48-run ABBA completed at `15:45:18 UTC` (`78` minutes after reading `FABLE_TO_carbon2_18.md` at `14:27:09 UTC`, right at the minute-80 report target of the 90-minute cap). Per *"Part 2 (only if time is left)"* and *"the report at minute 80 with what you have"*, we stopped new runs at minute 78 rather than starting a second 2x-PGO + 48-run cycle (~15 minutes) that would overrun minute 90.

---

## 3. Step Summary Scorecard (`1` step tried: `0` kept, `1` killed)

| Step | Patch File | Lines | Identity | Timing (`12x60 Hash 16` CPU) | Prediction (`6c5c2d6d2`) | Controls |
|---|---|---:|---|---|---|---|
| `16` | `stack/16_see_pawn_exit.patch.txt` | `27` | **EXACT** (`0` diffs: bench 11/13/16 both nets, 250 d9 `4332153` / `4124a7d4...`, 1,000 evals both nets, 2x 6-game traces, `188,608`-call SEE oracle `a557282d3d4c5efe`) | **`0.9943x` (`-0.57%`)**, `4/12` blocks, 95% CI `[0.9892x, 1.0016x]` (pooled `0.9935x`) | **KILLED** (predicted `+0.20%..+0.55%`, gate `>= 1.0040x`; rejected) | **`2/2` CAUGHT** (`c1` Path 1 & `c2` Path 2: `12` oracle diffs each + `bench 11` `882074 -> 738303`) |

---

## 4. What We Would Do Next with Another 90 Minutes — and Why We Recommend Stopping Micro-Steps Here

1. **Primary recommendation — STOP micro-steps on `01..13 + tidy` and keep `job17/stack_r15d_to_final.patch.txt` (`sha256=3d2ce0852fe18d9953fb446950aa90fb67dbdb768c2e229a193e918e54beeb63`) as the final candidate stack for the owner's Zen 5 PC:**
   - Four consecutive post-`13` micro-candidates (`14_cuckoo_avx512_parity` `0.9970x`, `14_v3_apply_changes_fast` `0.9980x`, `15_fast_is_pseudo_legal` `0.9923x`, and now `16_see_pawn_exit` `0.9943x`) have all measured slightly negative (`-0.20%` to `-0.77%`) once compiled under Clang 18 ThinLTO + SP-PGO, while the 13-piece + `tidy` consolidated diff has been independently verified at **`+8.9%` to `+9.1%` whole-engine SP speedup** on both Clang 18 SP-PGO (`sapphirerapids`) and `sol2`'s GCC 14 LTO+PGO (`x86-64-v4`, `0.9165` CPU).
2. **If another 90 minutes on Xeon were requested anyway, ranked by code read:**
   - **Rank 1 (pure dead-text cleanup, zero binary change): delete only the 12 uncompiled `#else` lines in `Board::see_ge` (`src/board.cpp:1539-1550`).** Part 0 proved those lines are never compiled when `FORGE_SDK_SEE_HOIST == 1`, and Part 1 proved moving them *into* the compiled branch hurts CPU (`0.9943x`). Deleting `#else ...` alone produces a **byte-identical `.o`** while eliminating Known Answer `(ii)` from the diff.
   - **Rank 2 (`TranspositionTable::clear` by `std::memset`, `src/search.cpp:458-463` & `include/forge/search.hpp:92-138`):** We read `TTEntry` (`search.hpp:92-101`: `key32=0`, `move{}`, `score=0`, `eval=0`, `depth=0`, `gen_bound=0`, `rule50_clock=0`, `padding=0`, `sizeof(TTEntry)==16`) and `TTCluster` (`search.hpp:131-138`: `alignas(64) std::array<TTEntry, 4> entries{}`, `sizeof(TTCluster)==64`), confirming `TTCluster{}` is 64 zero bytes (`std::bit_cast` verifiable via `static_assert`). Disassembly of `bld_sp_tidy_1/forge` (`0xa4ab0`) shows Clang emits a scalar-indexed `2x vmovaps %ymm0` loop reloading `(%rdi)` and `8(%rdi)` per cluster due to potential `this`-aliasing rather than `memset`/ERMSB; replacing line `459` with `std::memset(clusters_.get(), 0, cluster_count_ * sizeof(TTCluster))` removes that alias reload, though `60 * 16 MB = 960 MB` at DRAM/L3 bandwidth (~`16-24 ms` out of `11,100 ms`, `< 0.22%` total CPU) is likely below the `+0.40%` gate at `softnodes 2000`.

---

## 5. Timestamps, Runtime Model, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job18/stamps.txt`:**
  `Wed Nov 18 02:27:09 PM UTC 2026 | job 18 received (FABLE_TO_carbon2_18.md); starting Part 0 switch table of stack_r15d_to_final.patch.txt`
- **Last line of `forge-combo29/carbon2/job18/stamps.txt`:**
  `Wed Nov 18 03:49:01 PM UTC 2026 | Job 18 all runs finished; writing REPORT_carbon2_job18.md within budget`
- **Runtime Model Name & Version:** `Gemini 4 Carbon`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job18` immediately before report commit:**

```text
 M forge-combo29/carbon2/job18/stamps.txt
?? forge-combo29/carbon2/job18/REPORT_carbon2_job18.md
forge-combo29/carbon2/job18:
part0_switch_table_raw.txt
part1_see_pawn_exit_counts_raw.txt
prediction_16_see_pawn_exit.txt
REPORT_carbon2_job18.md
s16_build_and_step0_raw.txt
s16_control1_path1_early_exit.patch.txt
s16_control2_path2_prepared_cache.patch.txt
s16_identity_raw.txt
s16_see_oracle_and_controls_raw.txt
s16_see_pawn_exit_12x60_hash16_raw.txt
stack
stamps.txt
test_s16_see_pawn_exit_oracle.cpp

forge-combo29/carbon2/job18/stack:
16_see_pawn_exit.patch.txt
```
