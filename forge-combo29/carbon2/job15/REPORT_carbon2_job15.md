# Carbon2 — Job 15 Report (`REPORT_carbon2_job15.md`)

**Branch:** `for-fable-and-opus/carbon2-work` (no engine source files modified in-tree; no binaries, `.fnn3` nets, or `.profraw`/`.profdata` files committed; **no pull request opened**).

---

## 0. Step 0 Across All Job 15 Builds, Compiler & `-march`, and SP Profile Parameters

- **Compiler, linker, and C++ standard library (`forge-combo29/carbon2/job15/build_pgo_raw.txt` lines 4–8, 150–155, 317–342):**
  - `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18`, `llvm-profdata-18`)
  - `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`)
  - GCC 13 `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`)
- **Architecture & speed switches:**
  - `-march=sapphirerapids` (`Intel(R) Xeon(R) CPU @ 2.60GHz`, x86-64 AVX-512 + VNNI + BMI2 `PEXT`)
  - `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -pthread`
- **Profiled builds (`sp_s11_1`, `sp_s11_2`, `sp_s12_1`, `sp_s12_2` in `build_pgo_raw.txt` lines 306–316, 330–332):**
  - **Profile files merged per build:** **`2`** `.profraw` files merged via `llvm-profdata-18 merge`:
    1. Phase 2a `bench 11` (`1,261,644` nodes), `bench 13` (`6,312,262` nodes), `bench 16` (`74,843,992` nodes) with `net768.fnn3` + 4 bench switches.
    2. Phase 2b self-play profile run: **`60` games** (`disjoint_from_timing_60=True`), **`5,531` searches**, **`18,059,934` nodes**, `go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`, `trace=1646ce4566de2f40`.
- **Step 0 verified on every build (engine's own lines in `forge-combo29/carbon2/job15/step0_job15_raw.txt` lines 1–110):**
  - `sp_pcr15` (`step0_job15_raw.txt` lines 1–18): default `bench 11/13/16 = 312,866 / 862,329 / 3,024,920`, `go perft 5 = 4,865,609`; `PC20` no net `bench 11/13 = 278,024 / 587,276`; `net512` only (`fdff70de72e4ca82`, `avx512`) `bench 11/13 = 965,454 / 4,151,906`; `PC20 + net512` `bench 11/13 = 625,258 / 3,652,372`, `eval = 968 / 1176 / 31`.
  - All 7 Job 15 builds (`plain_r15d`, `plain_curated`, `part2_cnt`, `sp_s11_1`, `sp_s11_2`, `sp_s12_1`, `sp_s12_2` in `step0_job15_raw.txt` lines 20–110 & `part2_refresh_counters_raw.txt` lines 4–15):
    - `go perft 5 = nodes 4865609` (**EXACT** on all 7)
    - `PC20 + net512.fnn3` (`fdff70de72e4ca82`, `avx512`): `bench 11 = 625,258`, `bench 13 = 3,652,372` (`bench 16 = 23,891,329`), `eval = 968 / 1176 / 31` (**EXACT** on all 7)
    - `PC20 + net768.fnn3` (`30ab43b4ba5db5f3`, `avx512`): `bench 11 = 882,074`, `bench 13 = 4,275,906` (`bench 16 = 32,374,943`) (**EXACT** on all 7)

---

## 1. Part 1 — Protocol Identity Test of `04_S7` (`apply_position_sv`, `parse_limits_sv`)

Generated and executed by `forge-combo29/carbon2/job15/run_part1_protocol_identity.py` (`seed = 15001` for every random choice; single command stream `/tmp/carbon2_job15/protocol_stream.txt`, `23,719` synchronous `readyok`-terminated blocks, `sha256 = b89c88c7da3655fcde68ee237ca1a9df23f6dc1083fbb7da1471890cff954806`) on plain no-PGO `-O3 -DNDEBUG` builds of `r15d` and `curated` (`r15d + 01_S4..10_W2`) with `PC20 + net512.fnn3`, `Threads 1`, `Hash 16` (`forge-combo29/carbon2/job15/part1_protocol_identity_raw.txt` lines 1–37):

| Category | Description | Position Commands Sent |
|---|---|---:|
| **`(a)`** | Every prefix growing (`startpos` & `<game's start>` FEN across the 60 SP driver games + 2 `startpos` SP games) | `15,605` |
| **`(b)`** | Same prefixes shrinking, and in seeded-random order (`seed = 15001`) | `5,106` |
| **`(c)`** | Root changing between consecutive commands (`game A -> game B -> game A`) | `240` |
| **`(d)`** | Non-canonical whitespace (`"  "`, `"\t"`, trailing spaces/tabs between moves & after `"moves"`, empty `"moves"`) | `243` |
| **`(e)`** | Illegal/malformed mid-list token (move from another game, `"e2e9"`, `"e2e4q"` / `<move>q`) + continuation past bad token | `485` |
| **`(f)`** | 4-field and 5-field FEN roots (bare and with `moves ...`) | `240` |
| **`(g)`** | `ucinewgame` interleaved between `position` commands | `180` |
| **`(h)`** | `parse_limits_sv` `go` lines (`depth`, `nodes` incl. `0`, `softnodes`, `searchmoves` 2..5, `>32`-token `go` line up to `52` tokens after `go`, unknown word between known ones) | `130` |
| **Total** | **All position commands (`>= 20,000` required)** | **`22,229`** |

- **Probes executed (`part1_protocol_identity_raw.txt` lines 17–20):**
  - Per-position probes (`go perft 2`, `eval`, `isready`): **`22,229`**
  - Every-50th-position probes (`ucinewgame`, `go depth 6` at `Threads 1, Hash 16`, `isready` — alternating re-applied 50th position after `ucinewgame` and bare `ucinewgame` since `src/uci.cpp:577` resets `board` to `StandardStartFen` on `ucinewgame`, identical in the single stream sent to both exes): **`444`**
  - Kind-`(h)` `go` probes (`isready`-synchronized after `bestmove`): **`130`** (maximum tokens after `go` = **`52`** > `32`, exercising `heap_tokens` spillover in `parse_limits_sv`).
- **Line-for-line comparison (`time`, `nps`, `hashfull` stripped from `info` lines; `part1_protocol_identity_raw.txt` lines 22–26):**
  - `r15d` emitted lines: **`540,889`**
  - `curated` emitted lines: **`540,889`**
  - **Lines compared:** **`540,889`**
  - **Lines that differ:** **`0`**
- **Planted fault (`forge-combo29/carbon2/job15/part1_s7_ws_planted_fault.patch.txt`: `moves_sv[canon.size()]` whitespace-boundary test removed; `part1_protocol_identity_raw.txt` lines 28–36):**
  - Previous block position: `position startpos moves e2e4`
  - Faulting block position: `position startpos moves e2e4q e7e5 g1f3`
  - **First differing line (`line #510,154`, block `#22,254`, out of `30,275` differing lines total):**
    - Clean `r15d` & clean `curated`: `info string illegal move e2e4q`
    - Planted-fault `curated_fault`: **`info string illegal move q`**

---

## 2. Part 2 — NNUE v3 Refresh & `make_valid` Counter Tables and Share-by-Share Prediction Scorecard

Pre-committed standalone prediction: `forge-combo29/carbon2/job15/prediction_part2_refresh_shares.txt` (committed alone in `e0010cda4`).
All counts below are copied from `forge-combo29/carbon2/job15/part2_refresh_counters_raw.txt` on the scratch counter copy of `curated` (whose own engine `bench 11/13/16` lines in `part2_refresh_counters_raw.txt` lines 4–15 match `curated` identically: `net512 = 625,258 / 3,652,372 / 23,891,329`, `net768 = 882,074 / 4,275,906 / 32,374,943`), over the 60 `Hash 16` `softnodes 2000` `PC20 + net768.fnn3` self-play games (`searches = 7,670`, `nodes = 25,641,316`, `trace = ee465caeff9c0fcf`):

### Table 2A — `Worker::static_evaluate_v3` Calls (`total = 13,172,445`)

| Path in `Worker::static_evaluate_v3` | Calls | Share of `13,172,445` | Predicted Range (`prediction_part2_refresh_shares.txt`) | Verdict |
|---|---:|---:|---|---|
| **`apply_pair_and_evaluate`** (`same_king_sq = 6,834,074` + `same_king_key = 1,010,187`) | `7,844,261` | **`59.55%`** | `62.0%` to `84.0%` | **KILLED** (`-2.45 pp` below `62.0%` because `already_valid` took `3.48%`) |
| **`make_valid` + `evaluate`** (`valid_parent_key_change = 2,389,507` + `invalid_parent = 2,480,642`) | `4,870,149` | **`36.97%`** | `15.5%` to `37.5%` | **MET** |
| **Already valid at `index`** (`valid_flags[index] != 0` -> `evaluate` only) | `458,035` | **`3.48%`** | `0.05%` to `2.0%` | **KILLED** (`+1.48 pp` above `2.0%`) |

### Table 2B — `nnue::v3::make_valid` Calls by Number of Plies Replayed (`total = 4,870,149`; `9,076,787` `replay_ply` calls, `max_plies = 33`)

| Plies Replayed (`index - ancestor`) | Calls | Share of `4,870,149` | Predicted Range (`prediction_part2_refresh_shares.txt`) | Verdict |
|---|---:|---:|---|---|
| **`0` (`ancestor < 4`, root `refresh_cached`)** | `7,623` | **`0.16%`** | `0.05%` to `1.0%` | **MET** |
| **`1` ply** | `2,389,507` | **`49.06%`** | `12.0%` to `42.0%` | **KILLED** (`+7.06 pp` above `42.0%`: nearly half of all `make_valid` calls are 1-ply king-key changes from a valid parent!) |
| **`2` plies** | `1,689,898` | **`34.70%`** | `30.0%` to `60.0%` | **MET** |
| **`3` plies** | `386,900` | **`7.94%`** | `10.0%` to `28.0%` | **KILLED** (`-2.06 pp` below `10.0%`, shifted into `1` ply) |
| **`4 to 7` plies** (`4: 165,493`, `5: 99,880`, `6: 52,600`, `7: 31,420`) | `349,393` | **`7.17%`** | `4.0%` to `22.0%` | **MET** |
| **`8 or more` plies** (`max = 33`) | `46,828` | **`0.96%`** | `0.05%` to `6.0%` | **MET** |

### Table 2C — `nnue::v3::refresh_from_pieces` Calls by Cause and Placement (`total = 4,187,656`)

| Cause | At Evaluated Ply (`k == index` / root) | Inside Replay Below It (`k < index`) | Cause Total | Share of `4,187,656` | Predicted Range | Verdict |
|---|---:|---:|---:|---:|---|---|
| **King changed bucket** *(incl. `355,405` at-eval + `61,410` below = `416,815` that also flipped mirror side)* | `3,150,226` (`75.23%`) | `581,068` (`13.88%`) | `3,731,294` | **`89.10%`** | `65.0%` to `90.0%` | **MET** |
| **King changed flip only** *(same bucket, crossed `d`/`e` mirror boundary)* | `363,568` (`8.68%`) | `77,548` (`1.85%`) | `441,116` | **`10.53%`** | `8.0%` to `32.0%` | **MET** |
| **No valid ancestor** *(`ancestor < 4` root `refresh_cached`)* | `15,246` (`0.36%`) | `0` (`0.00%`) | `15,246` | **`0.36%`** | `0.3%` to `4.0%` | **MET** |
| **Placement Total** | **`3,529,040` (`84.27%`)** *(pred `55.0%..88.0%`: **MET**)* | **`658,616` (`15.73%`)** *(pred `12.0%..45.0%`: **MET**)* | **`4,187,656`** | **`100.00%`** | — | **5 / 5 MET** |

### Table 2D — `RefreshCache` Columns (`n_sub + n_add`) per `refresh_from_pieces` Call (`4,187,656` refreshes, `20,640,147` columns)

| Statistic (`part2_refresh_counters_raw.txt` line 26) | Observed | Predicted Range (`prediction_part2_refresh_shares.txt`) | Verdict |
|---|---:|---|---|
| **Mean columns / refresh** | **`4.9288`** | `4.0` to `12.0` | **MET** |
| **50th percentile (median)** | **`4`** | `2` to `9` | **MET** |
| **90th percentile** | **`9`** | `8` to `20` | **MET** |
| **99th percentile** | **`15`** (`min = 0` [`239,190` calls], `max = 45`) | `14` to `34` | **MET** |

*(Overall Part 2 prediction scorecard: **12 MET, 4 KILLED** — and our biggest surprise, `1`-ply `make_valid` being **`49.06%`** = `2,389,507` calls alongside `both_lt4 = 3,019,249` = **`72.10%`** of refreshes having `n_sub < 4 && n_add < 4`, directly pinpointed Part 3's winning step!)*

---

## 3. Part 3 — `stack/12_v3_refresh_fuse.patch.txt` on Top of `curated + 11_stop_hot`

- **Counts from Part 2 (`part2_refresh_counters_raw.txt`) that decided the design:**
  1. **`3,019,249 / 4,187,656` (`72.10%`)** of `refresh_from_pieces` calls have `n_sub < 4 && n_add < 4` (`n_sub <= 3` on `78.60%`; `n_add <= 3` on `78.91%`). Because the old AVX-512 kernel looped `for (; s + 4 <= n_sub; s += 4)` outside `h` and fell back to separate `sub_column_avx512` / `add_column_avx512` calls plus `std::copy_n(acc, hidden, destination)`, it made ~`5.9` full `1,536`-byte passes per refresh instead of one `h`-outer-loop pass!
  2. **`2,389,507`** `static_evaluate_v3` calls (`49.06%` of all `make_valid` calls and `57.06%` of all `4,187,656` refreshes; `two_rfp = 0`) have an already-valid parent (`valid_flags[index - 1] != 0`) where one king kept its key and the other refreshed, and immediately evaluated `w2` SCReLU by reloading all `3,072` bytes of `child.values[0..1]` in `nnue::v3::evaluate()`.
  3. **`3,529,040 / 4,187,656` (`84.27%`)** of refreshes occur at the evaluated ply (`k == top` or root), where `board.piece_bitboards()` can be read by `const` reference without copying `104` bytes via `pieces_of(board)`.
- **What `forge-combo29/carbon2/job15/stack/12_v3_refresh_fuse.patch.txt` (`278` lines, `patch -p1 -F0` on `curated + 11_stop_hot`) does:**
  - Rewrites `refresh_from_pieces` with a single outer loop over `h = 0 .. hidden - 32` (with a zero-column copy short-circuit for the `239,190` exact cache hits), updating `acc + h` and `destination + h` in one ZMM register pass without `sub_column_avx512`/`add_column_avx512` tail passes or `std::copy_n`.
  - Adds `nnue::v3::apply_one_refresh_one_and_evaluate` for the `2,389,507` valid-parent single-king-key-change `static_evaluate_v3` calls, fusing the unchanged perspective's incremental `apply_changes`, the changed perspective's `RefreshCache` update, and both perspectives' SCReLU `w2` dot products in ZMM registers in one `h` pass without reloading `child.values[0..1]`, and passes `board.piece_bitboards()` by `const` reference whenever `k == top` or in `refresh_cached`.
- **Pre-committed standalone prediction:** `forge-combo29/carbon2/job15/prediction_12_v3_refresh_fuse.txt` (committed alone in `d3e317208`): predicted `1.0050x..1.0280x` (`+0.50%..+2.80%`) paired `getrusage` CPU and `>= 8/12` faster (declared gate `>= 1.0050x` AND `>= 8/12`).
- **Identity suite, `-DFORGE_NNUE_V3_VERIFY=1` oracle, and planted fault (`forge-combo29/carbon2/job15/s12_v3_refresh_identity_and_fault_raw.txt` lines 1–41):**
  - Engine's own `bench 11/13/16` lines on `/tmp/carbon2_job15/bld_sp_s12_1/forge`: `net512 = 625,258 / 3,652,372 / 23,891,329`, `net768 = 882,074 / 4,275,906 / 32,374,943` (**EXACT**).
  - `250` depth-9 rows (`PC20 + net768.fnn3`): `node_sum = 4,332,153` and `rows_sha256 = 4124a7d4eadfaae4bc811c98f188a814adc26af08cdfe9a669f8e2ecb3816a18` (**EXACT** match between `bld_sp_s11_1` and `bld_sp_s12_1`).
  - `1,000` static evals (`positions_1000.txt`): `net768 sha256 = a702fa7547a8dc5a60d93cfa19dd5c6e0186aea78957ce8ea41c6f559200f690`, `net512 sha256 = 489220db0011108261352eedb885660ff2d46ad74243f4df433bd43c68e4dd3d` (**EXACT**).
  - Both 6-game traces: `startpos = 4560d7c3afdeba2e` (`846` searches, `2,916,466` nodes), `fen = 9ed22c1193ab96de` (`745` searches, `2,481,101` nodes) (**EXACT**).
  - `-DFORGE_NNUE_V3_VERIFY=1` per-node `evaluate_reference` oracle: **PASS** (`exit_code = 0` across `875,955` `net768` + `965,454` `net512` `bench 11` nodes).
  - Planted fault (`s12_v3_refresh_planted_fault.patch.txt`: `_mm512_sub_epi16` in place of `_mm512_add_epi16` on tail `adds`): **CAUGHT** (`exit_code = 3`, `info string V3 VERIFY FAILED at ply 3: search path 1430, reference 801, fen rnbqkbnr/ppppp1pp/5p2/8/3P4/8/PPPKPPPP/RNBQ1BNR b kq - 1 2`).
- **12x60 `Hash 16` ABBA Timing (`forge-combo29/carbon2/job15/s12_v3_refresh_fuse_12x60_hash16_raw.txt`, opening with `START_UTC: Wed Nov 18 10:37:37 AM UTC 2026` and closing with `END_UTC: Wed Nov 18 10:47:54 AM UTC 2026`):**
  - `A = curated + 11_stop_hot` SP-profile (`bld_sp_s11_1`, `bld_sp_s11_2`) vs `B = curated + 11_stop_hot + 12_v3_refresh_fuse` SP-profile (`bld_sp_s12_1`, `bld_sp_s12_2`); all `48` runs hit ONE trace `ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes).
  - **`getrusage` engine CPU:**
    - Per-round paired ratios (`r=1..12`): `[1.0019, 1.0036, 0.9790, 1.0199, 1.0077, 1.0094, 1.0060, 1.0053, 1.0094, 1.0119, 1.0051, 1.0093]`
    - **`median_of_paired_round_ratios = 1.0068x` (`+0.68%`), 95% CI `[1.0043x, 1.0094x]`, `11/12` rounds faster**
    - `ratio_of_pooled_medians = 1.0109x` (`+1.09%`), 95% CI `[0.9901x, 1.0148x]`
    - `A/A` control: `median(A2)/median(A1) = 1.0033` (per-round range `[0.9896, 1.0574]`), `median(B2)/median(B1) = 0.9957` (per-round range `[0.9825, 1.0438]`).
  - **Wall clock:**
    - Per-round paired ratios (`r=1..12`): `[0.9981, 1.0039, 0.9742, 1.0214, 1.0090, 1.0114, 1.0063, 1.0038, 1.0098, 1.0063, 1.0059, 1.0102]`
    - **`median_of_paired_round_ratios = 1.0063x` (`+0.63%`), 95% CI `[1.0039x, 1.0100x]`, `10/12` rounds faster** (`A/A` `median(A2)/median(A1) = 1.0019` `[0.9870, 1.0651]`, `median(B2)/median(B1) = 1.0012` `[0.9820, 1.0448]`).
  - **Decision:** **MET & PASSED THE DECLARED GATE** (`1.0068x >= 1.0050x`, `11/12 >= 8/12`); on paired round ratios its 95% CI `[1.0043x, 1.0094x]` lies strictly above `1.0000x` (**carries** on paired round ratios, while the pooled-median 95% CI `[0.9901x, 1.0148x]` reaches below `1.0000x`).

---

## 4. Step Summary Table

| Step | Patch File (`forge-combo29/carbon2/job15/...`) | Lines | Identity Suite & Oracles | 12x60 `Hash 16` SP-PGO Timing (`getrusage` CPU / Wall) | Prediction (`met` or `killed`) | Planted Fault (`caught` or `not`) |
|---|---|---:|---|---|---|---|
| **Part 3: `12_v3_refresh_fuse`** (on `curated + 11_stop_hot`) | `stack/12_v3_refresh_fuse.patch.txt` (`-F0`) | `278` | **EXACT** (engine lines `net512 625258/3652372/23891329`, `net768 882074/4275906/32374943`, `250` d9 rows `node_sum=4332153` `sha256=4124a7d4...`, `1000` evals `sha256` exact both nets, `4560d7c3afdeba2e`, `9ed22c1193ab96de`, `-DFORGE_NNUE_V3_VERIFY=1` `0` mismatches, `48/48` runs `ee465caeff9c0fcf`) | **CPU `1.0068x` (`+0.68%`, `11/12`, paired 95% CI `[1.0043x, 1.0094x]`, pooled 95% CI `[0.9901x, 1.0148x]`)**; **Wall `1.0063x` (`+0.63%`, `10/12`, paired 95% CI `[1.0039x, 1.0100x]`)** (`s12_v3_refresh_fuse_12x60_hash16_raw.txt`) | **MET** (passed declared `>= 1.0050x` & `>= 8/12` gate; paired round-ratio 95% CI > `1.0000x` **carries**) | **CAUGHT** (`s12_v3_refresh_planted_fault.patch.txt` -> `V3 VERIFY FAILED at ply 3: search path 1430, reference 801`, `exit_code=3`, `s12_v3_refresh_identity_and_fault_raw.txt`) |

---

## 5. Answers to `(a)` and `(b)` of "Wrong or Not Shown" From File 15

- **Answer to `(a)` (how and when Job 13's 10-piece identity checks ran, and why `stamps.txt` was 16–17 s apart):**
  - First, the 10 plain ThinLTO binaries `/tmp/carbon2_job13/exes/forge_01 .. forge_10` were compiled 4-way in parallel in three batches *before* the verification loop (`ls --time-style=full-iso /tmp/carbon2_job13/exes` shows `forge_01..04` finished at `07:14:25–07:14:26Z`, `forge_05..08` at `07:14:40–07:14:41Z`, and `forge_09..10` at `07:14:55Z`).
  - Then, between `07:14:56Z` and `07:17:39Z`, the verification script looped `01..10`, and **within each piece** spawned the `net512` `bench 11/13/16` process (~`10.1 s`), the `net768` `bench 11/13/16` process (~`15.6 s`), and the `250`-position depth-9 process (~`5 s`) **in parallel** on separate cores, so each piece's wall wait was `max(10.1 s, 15.6 s, 5 s) ≈ 16.3 s` (`07:15:12Z, 07:15:29Z, ..., 07:17:39Z`), and the script emitted only the parsed `"EXACT"` summary line into `stack_identity_raw.txt`. Starting in Job 15, every identity file keeps the engine's own verbatim `bench` lines plus the 250-row `node_sum` and `rows_sha256`.
- **Answer to `(b)` (what happened to the Valgrind check named in Job 13's first stamp):**
  - At `06:51:29Z` we intended to try `valgrind --tool=callgrind` for the caller-inclusive profile. When we actually ran `valgrind --tool=callgrind /tmp/carbon2_job13/bld_sp_cur13/forge` at `07:26:40Z` (`/tmp/carbon2_job13/callgrind.curated.10games`, `creator: callgrind-3.22.0`), Valgrind 3.22.0 terminated after only `summary: 2787885` instructions (`Ir`) upon hitting `-march=sapphirerapids` AVX-512 instructions unsupported by Valgrind 3.22's VEX decoder. No usable profile came out of Valgrind; we replaced it with the `RBP` frame-pointer `SIGPROF` call-stack walker (`07:31Z–07:36Z`) and neglected to note the aborted Callgrind attempt in `REPORT_carbon2_job13.md`.

---

## 6. Ranked Next Steps With Another 90 Minutes

1. **Tidy the 10-piece base stack's 2 minor review items noted by the PC (`FABLE_TO_carbon2_15.md` lines 70–74) if requested for final merge:**
   - Remove the uncalled `has_cached_quiet_history()` / `cached_quiet_history()` / `quiet_hist_epoch_` / `last_quiet_history_` leftovers from `01_S4` & `09_W1`, and fold the ~35 transient lines in `09_W1` superseded by `10_W2` plus the 3 whitespace-only lines so `01..10` + `11_stop_hot` (`+1.92%` CPU `9/12`) + `12_v3_refresh_fuse` (`+0.68%` CPU `11/12`) form a zero-dead-code 12-piece review stack for the Zen 5 PC.
2. **Fused 2-ply `make_valid` (`p2 = 1,689,898` calls = `34.70%` of `make_valid` in `part2_refresh_counters_raw.txt`):**
   - When `ancestor == index - 2` and neither king changed key across the 2 plies (`pair_ok` on `54.03%` of `replay_ply` calls), `stack[index - 1]` and `stack[index]` can be updated + `w2`-evaluated without reloading `stack[index]` from memory.
3. **`Board::see_ge` (`3.74%` / `7.412 ms/game` in `job13/curated_sp_time_profile_raw.txt` line 65):**
   - Early threshold exit (`SeeValue[captured] < threshold` when non-promoting) before building king-pin and full `attackers_to` bitboards.

---

## 7. Timestamps (`stamps.txt`), Runtime Model, and Final Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job15/stamps.txt`:**
  `Wed Nov 18 09:35:19 AM UTC 2026 | job 15 received (FABLE_TO_carbon2_15.md); starting Part 1 protocol identity setup`
- **Last line of `forge-combo29/carbon2/job15/stamps.txt`:**
  `Wed Nov 18 10:49:51 AM UTC 2026 | Part 3 12_v3_refresh_fuse 12x60 Hash16 timing DONE: CPU 1.0068x (+0.68%, 95% CI [1.0043x, 1.0094x], 11/12) wall 1.0063x (+0.63%, 10/12); writing REPORT_carbon2_job15.md`
- **Runtime model name and version:** `Gemini 4 Carbon`
- **Pull request check:** No pull request was opened.
- **Output of `git status --short && ls -R forge-combo29/carbon2/job15` immediately before committing this report:**

```text
?? forge-combo29/carbon2/job15/REPORT_carbon2_job15.md
forge-combo29/carbon2/job15:
build_pgo_raw.txt
part1_protocol_identity_raw.txt
part1_s7_ws_planted_fault.patch.txt
part2_refresh_counters_raw.txt
prediction_12_v3_refresh_fuse.txt
prediction_part2_refresh_shares.txt
REPORT_carbon2_job15.md
run_part1_protocol_identity.py
s12_v3_refresh_fuse_12x60_hash16_raw.txt
s12_v3_refresh_identity_and_fault_raw.txt
s12_v3_refresh_planted_fault.patch.txt
stack
stamps.txt
step0_job15_raw.txt

forge-combo29/carbon2/job15/stack:
12_v3_refresh_fuse.patch.txt
```
