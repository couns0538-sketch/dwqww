# REPORT — `carbon2` Job 30: Verification of `kG` (`Part V`), Profile on `T` & Pieces `17..18` (`Part R`), and Bundle `kH` Timing (`Part B`, `H1`, `H2`)

**Headline:** Part V (`V1`, `V2`, `V3`) reads **`KEEPS` / `KEEPS` / `KEEPS`** (`0` `V3 VERIFY FAILED` lines on `GV`, `0` masked stdout differences between `GA` and `FA`, `0` sanitizer or `-D_GLIBCXX_ASSERTIONS` reports on `GA`/`FA`/`GT`, and all controls `CV1`, `CV2`, `CA`, plus Job 29's `CC`, fired). Bundle **`kH = kG + 17_uci_stdio_and_search_setup + 18_fast_upcoming_repetition`** reads **`PAYS`** on held-out workload `T` (`H1` pooled CPU **`1.0244`**, `12/12` blocks `> 1`; `H2` pooled CPU **`1.0194`**, `12/12` blocks `> 1`).

---

## 1. Step 0 (Reused Executables) and Part V (`step0_raw.txt`, `builds.txt`, `partV_*_raw.txt`)

### 1.1 Step 0 — Reused SP-PGO Executables Verified in Fresh Processes
All three reference SP-PGO binaries from Job 28 were still present in `/tmp` with matching `sha256` digests and were **reused without rebuilding** (`step0_raw.txt`, `builds.txt`):
- **`kG_1`:** `/tmp/carbon2_job28/bld_sp_stkG_1/forge` (`len=38`, `sha256=32113ff4731e3a55bf2b6ff7dcdae4e05c0de89a38fec1c7bec6f9193a330ae1`) — fresh processes: no-options `bench 11 = 312866`, `bench 13 = 862329`, `go perft 5 = 4865609`; `PC20 + net768` `bench 11 = 882074`, `bench 13 = 4275906`; `T` (`60` games) = `6070/26711499/937e1660561173af` (`T[1..10]` = `1089/4497849/b8af7c43c78aca2c`).
- **`kG_2`:** `/tmp/carbon2_job28/bld_sp_stkG_2/forge` (`len=38`, `sha256=e41a7d1393080c0b95f35f089fade3fb31763101d7c01e82344c73ab48c9adcf`) — identical on all 6 checks (`312866 / 862329 / 4865609`, `882074 / 4275906`, `6070/26711499/937e1660561173af`).
- **`kF_sp_1`:** `/tmp/carbon2_job17/bld_sp_tidy_1/forge` (`len=38`, `sha256=c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e`) — identical on all 6 checks (`312866 / 862329 / 4865609`, `882074 / 4275906`, `6070/26711499/937e1660561173af`).

### 1.2 Part V Summary Table (`V1`, `V2`, `V3`)

| part | builds | runs | known answer holds | reports | control fired | reading |
|---|---|---|---|---|---|---|
| **`V1`** (`-DFORGE_NNUE_V3_VERIFY=1`) | `GV` (`ac8e53c4...`), `CV1` (`c75af668...`), `CV2` (`9105ddd9...`) | `KV1a` (`GV` all `60` games of `T` w/ `net768`), `KV1b` (`GV` `T[1..15]` w/ `PC20+net512`), `CV1` (`T[1]`), `CV2` (`T[1]`) | **YES** (`KV1a`: `rc=0`, `0` `FAILED` lines, `6070/26711499/937e1660561173af`; `KV1b`: `rc=0`, `0` `FAILED` lines, `1309/5875986/9921c3d37fc453d7`) | **`0`** on `GV` (`partV_V1_KV1a_GV_T_raw.txt` [`80,468` lines, `sha256=20438a8c...`], `partV_V1_KV1b_GV_net512_T15_raw.txt`) | **YES** (`CV1`: `rc=3`, `V3 VERIFY FAILED at ply 1: search path 452, reference 490`; `CV2`: `rc=3`, `V3 VERIFY FAILED at ply 4: search path -414, reference -196`) | **`KEEPS`** |
| **`V2`** (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`, `1` thread) | `GA` (`20917530...`), `FA` (`7a76ed05...`), `CA` (`4db44d58...`) | Fresh process per run: `(a)` no-opts `bench 11` (`312866`) & `bench 13` (`862329`), `(b)` `T[1..10]` (`1089/4497849/b8af7c43c78aca2c`), `(c)` 2 deep FENs at `go nodes 3000000` (`max seldepth = 69` and `37` on both `GA` & `FA`), `CA` on `bench 11` | **YES** (`GA` == `FA` masked line-for-line on all 5 runs of `(a)`, `(b)`, `(c)`, with `-D_GLIBCXX_ASSERTIONS` enabled throughout) | **`0`** sanitizer reports and **`0`** `libstdc++` assertions on `GA` and `FA` | **YES** (`CA`: `rc=-6` before `bench 11` ended, `/usr/include/c++/13/array:202: ... std::array<forge::Worker::V1EvalFrame, 136>::operator[](size_type): Assertion '__n < this->size()' failed.`) | **`KEEPS`** |
| **`V3`** (`Threads 4` on Job 29 script `SC`, `LA[1..60]`, `go nodes 20000`) | `GA` (`20917530...`), `GT` (`c81cfb89...`, `-O1 -g -fsanitize=thread`) | `1` 60-round `SC` run on `GA` (`1.92s`), `1` 60-round `SC` run on `GT` (`8.75s`) | **YES** (`60/60` `python-chess`-legal `bestmove`s on both `GA` and `GT`, `0` timeouts) | **`0`** ASan/UBSan/assertion reports on `GA` and **`0`** TSan reports on `GT` | **YES** (Job 29 `CC` fired `ThreadSanitizer: data race` in `job29/partC_CC_raw.txt`) | **`KEEPS`** |

- **First difference or report in `V1`, `V2`, `V3`:** **None** on `GV`, `GA`, `FA`, or `GT`. Both deep FENs in `V2(c)` were verified legal via `python-chess` (`8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1` reached `max seldepth = 69` on `GA` and `69` on `FA`; `8/8/8/4k3/8/8/8/R3K3 w - - 0 1` reached `max seldepth = 37` on `GA` and `37` on `FA`; `partV_V2_ac_and_CA_raw.txt`).

---

## 2. Part R (Profile on `T` & Pieces `17`, `18`) and Part B (`kH_1`, `kH_2`, `C30`)

### 2.1 Top 10 Functions by Self Time on `kG_1` Playing `T` (`profile_kG_T.txt`)
Profiled unmodified `kG_1` across `5` sequential 60-game passes of `T` on pinned `CPU 3` (`perf record -e task-clock -F 4000 --no-children`, raw `perf.data` kept in `/tmp` only; `total_wall = 42.1761s`, **`160,288` samples**, effective rate `3,800.4 Hz`; all `5/5` passes matched `6070/26711499/937e1660561173af`; full top 25 + ranks `26..80` committed in `profile_kG_T.txt`):

| Rk | Samples | Share | DSO | Function |
|---:|---:|---:|---|---|
| 1 | `73,004` | `45.55%` | `forge` | `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 2 | `14,289` | `8.91%` | `forge` | `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` |
| 3 | `10,291` | `6.42%` | `forge` | `forge::nnue::v3::apply_one_refresh_one_and_evaluate(...)` |
| 4 | `8,887` | `5.54%` | `forge` | `forge::Worker::qsearch(Board&, SearchStack*, int, int)` |
| 5 | `4,856` | `3.03%` | `forge` | `forge::Board::has_legal_move() const` |
| 6 | `4,653` | `2.90%` | `forge` | `forge::Board::see_ge(const Move&, int) const` |
| 7 | `4,497` | `2.81%` | `forge` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 8 | `3,839` | `2.40%` | `forge` | `forge::MovePicker::generate_quiets()::{lambda(...)#1}::operator()` |
| 9 | `3,391` | `2.12%` | `forge` | `forge::nnue::v3::apply_changes_pair(...)` |
| 10 | `2,919` | `1.82%` | `forge` | `forge::Board::generate_legal_evasions(MoveList&) const` |

- **Once-per-`go` / once-per-search self-time sum in `profile_kG_T.txt` (`> 1%` rule triggered):** Ranks `#17` `libc.so.6 _IO_getc` (`1,687` = `1.05%`), `#22` `libc.so.6 ungetc` (`874` = `0.55%`), `#31` `Worker::search::$_1` `emit` (`134` = `0.08%`), `#33` `Worker::search` root driver (`115` = `0.07%`), `#40` `std::getline` (`86` = `0.05%`), `#44` `getc@plt` (`68` = `0.04%`), `#46` `apply_position_sv` (`56` = `0.03%`), `#47` `_IO_sputbackc` (`56` = `0.03%`), `#50` `malloc` (`50` = `0.03%`), and `#53` `__gnu_cxx::stdio_sync_filebuf::underflow` (`45` = `0.03%`) sum to **`3,171 / 160,288` samples (`1.98%`)** before counting pipe/mutex wakeups.

### 2.2 Two New Node-Keeping Pieces on `kG` (`partR_pieces_known_answers_raw.txt`)
Neither piece touches any hunk of pieces `01..16`, net files, or option defaults:
1. **`17_uci_stdio_and_search_setup.patch.txt`** (`sha256=7bb9df1a563e4e90865ff5158944583b7966bf4d4118b65dd8e0493a8767d6d2`):
   - **Functions & share (`1.98%` once-per-`go` / once-per-search sum):** `main()` and `uci_loop` `bestmove` emitter in `src/uci.cpp`; `Searcher::set_threads` / `Searcher::search` and `Worker::search` root setup in `include/forge/search.hpp` and `src/search.cpp`.
   - **What it removes & why no node or UCI byte can change:** Calls `std::ios_base::sync_with_stdio(false); std::cin.tie(nullptr);` in `main()` so `std::cin` uses buffered `std::basic_filebuf` instead of `__gnu_cxx::stdio_sync_filebuf` (`getc` + `ungetc` per character; zero `<cstdio>` calls exist in Forge and every UCI write still locks `uci_output_mutex()` and flushes explicitly); formats `bestmove <m>[ ponder <p>]\n` into a stack `char bbuf[40]` instead of `std::string` heap temporaries; pre-builds `all_workers_vec_` / `main_worker_vec_` in `Searcher::set_threads` to avoid allocating `std::vector<Worker*> all` per search; reserves `result.pv.reserve(64)`, aliases `legal` directly when `!root_restricted_`, and zeros `root_move_nodes_[0..root_effort_count_-1]` instead of all `256` slots (the only readers at `search.cpp:3719,3740` bound indices strictly below `root_effort_count_`).
2. **`18_fast_upcoming_repetition.patch.txt`** (`sha256=841d29db78eb7c6bbe9b178801adbccd69cf1f76f752b1126a31717fce641c17`):
   - **Functions & share (`2.81%` self time, rank `#7` — largest untouched function in `kG`):** `Board::upcoming_repetition`, `CuckooTable` (`src/board.cpp`, `include/forge/board.hpp`), and inline `may_repeat` (`src/search.cpp`).
   - **What it removes & why no node or UCI byte can change:** Adds `board.plies_from_null() >= 3 && board.history_size() >= 4` to inline `may_repeat(board)` (mathematically identical to `upcoming_repetition`'s `span < 4` early return, eliding out-of-line calls on the 3 plies after every null move without touching `Board` layout or `make_move`); promotes `CuckooMoves` to a compile-time `alignas(64) constexpr` table of 16-byte co-located `CuckooSlot` entries (`static_assert(complete && entries == 3668)`); outlines the rare `opponent == 0` probe into `[[gnu::noinline]] Board::upcoming_repetition_hit` so the `98.6%` miss path spills zero callee-saved registers; checks `d = 3` immediately (`if (span < 6) return false;`) and walks remaining odd distances 2-at-a-time (`step0 = p[1] ^ p[0]`, `step1 = p[-1] ^ p[-2]`, `opp ^= step0 ^ step1`, exploiting `Z.side ^ Z.side == 0` across paired opponent moves so every tested distance tests the bit-identical `opponent == 0` predicate in the exact same increasing `distance` order).

### 2.3 Known Answers of `p17_1`, `p18_1`, `kH_1`, and `kH_2` (`partR_pieces_known_answers_raw.txt`, `partB_kH_known_answers_raw.txt`)
Bundle **`kH`** includes **both** pieces (`kG + 17_uci_stdio_and_search_setup + 18_fast_upcoming_repetition`). Every build has a `38`-character executable path and passed every check in fresh processes:

| Build | Executable (`len=38`) & `sha256` | No-Opts `b11 / b13 / perft5` | `PC20` No-Net / `net512` / `net768` (`b11 / b13`) | Job 20 `60g` & `T` `60g` | `(n1)` `T[1..3]` Masked UCI (`4,950` lines) | `(n2)` `-DFORGE_NNUE_V3_VERIFY=1` `T[1..10]` |
|---|---|---|---|---|---|---|
| **`p17_1`** | `/tmp/carbon2_job30/bld_sp_pc17_1/forge` (`0e4cf40e...`) | `312866 / 862329 / 4865609` | `278024/587276` \| `625258/3652372` \| `882074/4275906` | `7670/25641316/ee465caeff9c0fcf` \| `6070/26711499/937e1660561173af` | **EXACT** (`0` diffs vs `kG_1`) | `rc=0`, `0` `FAILED`, `1089/4497849/b8af7c43c78aca2c` |
| **`p18_1`** | `/tmp/carbon2_job30/bld_sp_pc18_1/forge` (`316f1078...`) | `312866 / 862329 / 4865609` | `278024/587276` \| `625258/3652372` \| `882074/4275906` | `7670/25641316/ee465caeff9c0fcf` \| `6070/26711499/937e1660561173af` | **EXACT** (`0` diffs vs `kG_1`) | `rc=0`, `0` `FAILED`, `1089/4497849/b8af7c43c78aca2c` |
| **`kH_1`** | `/tmp/carbon2_job30/bld_sp_stkH_1/forge` (`41f147ec...`) | `312866 / 862329 / 4865609` | `278024/587276` \| `625258/3652372` \| `882074/4275906` | `7670/25641316/ee465caeff9c0fcf` \| `6070/26711499/937e1660561173af` | **EXACT** (`0` diffs vs `kG_1`) | `rc=0`, `0` `FAILED`, `1089/4497849/b8af7c43c78aca2c` |
| **`kH_2`** | `/tmp/carbon2_job30/bld_sp_stkH_2/forge` (`66bf6175...`) | `312866 / 862329 / 4865609` | `278024/587276` \| `625258/3652372` \| `882074/4275906` | `7670/25641316/ee465caeff9c0fcf` \| `6070/26711499/937e1660561173af` | **EXACT** (`0` diffs vs `kG_1`) | `rc=0`, `0` `FAILED`, `1089/4497849/b8af7c43c78aca2c` |

### 2.4 Control `C30` (`control_C30_4blocks_raw.txt`)
- `4` blocks (`odd = ABBA`, `even = BAAB`, `+1` warm-up per block left out; harness `CPU 1`, engine `CPU 3`), `A = kG_1` (`go softnodes 2000`, `6070/26711499/937e1660561173af`), `B = kG_1` (`go softnodes 2200`, matching `C28`'s known-answer B signature **`5853/28387596/f37b0151ac18bd56`** on all `10/10` runs):
  - **Engine CPU (`B / A`):** `1.0621, 1.0769, 1.0730, 1.0747` | **`pooled = 1.0717`** (`66.8174s / 62.3497s`) | `median = 1.0739` | `mean = 1.0717`, 95% $t$-CI `[1.0612, 1.0821]` | **`4 / 4` blocks `> 1`** -> **PASSES** (`1.0717 > 1.0116` and `4/4 > 1`).
  - **Wall (`B / A`):** `1.0592, 1.0799, 1.0786, 1.0750` | `pooled = 1.0732` (`69.3282s / 64.6024s`) | `median = 1.0768` | `mean = 1.0732`, 95% $t$-CI `[1.0580, 1.0884]` | `4 / 4` blocks `> 1`.

---

## 3. Standalone Predictions Graded (`prediction1_job30.txt`, `prediction2_job30.txt`)

1. **`prediction1_job30.txt`** (committed alone in `0b36391e4` before Part V ran; unmodified):
   - `KV1`, `KV2`, `KV3` hold: predicted **`HOLDS` / `HOLDS` / `HOLDS`** -> measured **`HOLDS` / `HOLDS` / `HOLDS`** (**`3 / 3` MET**).
   - `CV1`, `CV2`, `CA` fire: predicted **`FIRES` / `FIRES` / `FIRES`** -> measured **`FIRES` / `FIRES` / `FIRES`** (**`3 / 3` MET**).
   - `V1`, `V2`, `V3` readings: predicted **`KEEPS` / `KEEPS` / `KEEPS`** -> measured **`KEEPS` / `KEEPS` / `KEEPS`** (**`3 / 3` MET**).
2. **`prediction2_job30.txt`** (committed alone in `b8305045c` after Part R, Part B, and `C30`, before `H1`; unmodified):
   - **`H1` pooled CPU ratio & reading:** predicted `[1.0140, 1.0450]` and **`PAYS`** -> measured **`1.0244`** and **`PAYS`** (**MET**).
   - **`H2` pooled CPU ratio & reading:** predicted `[1.0140, 1.0450]` and **`PAYS`** -> measured **`1.0194`** and **`PAYS`** (**MET**).
   - **`BUNDLE` (`kH`) reading:** predicted **`PAYS`** -> measured **`PAYS`** (**MET**).
   - **`G20` pooled CPU ratio & reading:** predicted `[1.0116, 1.0340]` and `PAYS` -> **NOT RUN (ungraded)** because `H2` ended at `07:36:56 PM UTC` (`minute 65m 50s` from `06:31:06 PM UTC`), and `FABLE_TO_carbon2_30.md` specifies `G20 (only if H2 ended before minute 65)`.

---

## 4. Timing Rows `H1` and `H2` (`row_H1_12blocks_raw.txt`, `row_H2_12blocks_raw.txt`)

All `60` runs of `H1` (`12` warm-ups + `48` legs) and all `60` runs of `H2` (`12` warm-ups + `48` legs) carried `T`'s exact signature `6070/26711499/937e1660561173af` (`0` dropped blocks). `B` is `kG` and `A` is `kH`, so `B / A > 1` means `kH` uses less time than `kG`:

| Row & Metric (`B / A`) | `12` Block Ratios (`b01 .. b12`) | Pooled (`sumB / sumA`) | Median | Mean & 95% $t$-CI (`df=11`) | Blocks `> 1` | Reading |
|---|---|---:|---:|---|---:|---|
| **`H1` (`kG_1 / kH_1`) — CPU** | `1.0254, 1.0274, 1.0221, 1.0242, 1.0194, 1.0230, 1.0216, 1.0208, 1.0220, 1.0366, 1.0232, 1.0269` | **`1.0244`** (`185.5983s / 181.1793s`) | `1.0231` | `1.0244` `[1.0215, 1.0273]` | **`12 / 12`** | **`PAYS`** |
| **`H1` (`kG_1 / kH_1`) — Wall** | `1.0235, 1.0239, 1.0189, 1.0225, 1.0159, 1.0216, 1.0192, 1.0186, 1.0233, 1.0323, 1.0194, 1.0272` | `1.0222` (`192.6675s / 188.4848s`) | `1.0220` | `1.0222` `[1.0194, 1.0250]` | `12 / 12` | — |
| **`H2` (`kG_2 / kH_2`) — CPU** | `1.0168, 1.0239, 1.0200, 1.0183, 1.0182, 1.0194, 1.0197, 1.0230, 1.0211, 1.0171, 1.0185, 1.0173` | **`1.0194`** (`185.5875s / 182.0492s`) | `1.0190` | `1.0194` `[1.0180, 1.0209]` | **`12 / 12`** | **`PAYS`** |
| **`H2` (`kG_2 / kH_2`) — Wall** | `1.0158, 1.0238, 1.0187, 1.0159, 1.0175, 1.0163, 1.0176, 1.0199, 1.0170, 1.0153, 1.0172, 1.0137` | `1.0174` (`192.8071s / 189.5115s`) | `1.0171` | `1.0174` `[1.0158, 1.0190]` | `12 / 12` | — |
| **`G20` (`kF_sp_1 / kG_1` on `T20`)** | *not done (`H2` ended at minute `65m 50s` $\ge 65$)* | — | — | — | — | *not done* |

- **Row readings:** **`H1 = PAYS`** (`1.0244 > 1.0116`, `12/12 >= 10/12`), **`H2 = PAYS`** (`1.0194 > 1.0116`, `12/12 >= 10/12`).
- **Bundle `kH` reading:** **`PAYS`** (both `H1` and `H2` read `PAYS`, across all `24 / 24` blocks combined).

---

## 5. WHAT THIS CHECK CANNOT SEE

The PC's clang 23 for Windows and its MinGW libstdc++, its Zen 5 processor with 16 engines playing at once, its
trained nets, its own openings, gains below about 1 %. V1 sees only the evaluations these games reached: a null
move followed by a king's change of bucket in a line no game played stays unseen. V2's index check sees operator[]
only, not pointer steps such as vf - back - 1, and (c) may not reach ply 128. V3 sees only the thread schedules it
produced.

---

## 6. Closing Sections

### Facts
1. `GV` (`kG` with `-DFORGE_NNUE_V3_VERIFY=1`) verified every v3 evaluation against `evaluate_reference` across all `6,070` searches / `26,711,499` soft-counted nodes of `T` on `net768` (`KV1a`) and `1,309` searches / `5,875,986` soft-counted nodes of `T[1..15]` on `net512` (`KV1b`) with `rc = 0` and `0` mismatches, while `CV1` failed at ply `1` (`452` vs `490`) and `CV2` failed at ply `4` (`-414` vs `-196`) of `T`'s first game.
2. `GA` and `FA` ran with `-D_GLIBCXX_ASSERTIONS` + ASan/UBSan enabled across `bench 11/13` (v1 built-in net), `T[1..10]` (`net768`), and two `3,000,000`-node endgame searches (`max seldepth = 69` and `37`) with `0` assertions, `0` sanitizer reports, and `0` masked output differences; `CA` aborted immediately on `std::array<V1EvalFrame, 136>::operator[]` (`rc = -6`).
3. In `profile_kG_T.txt` (`160,288` `task-clock` samples at `3,800.4 Hz`), `std::cin`'s default `sync_with_stdio(true)` character-by-character `_IO_getc` (`1.05%`) + `ungetc` (`0.55%`) + `stdio_sync_filebuf` helpers accounted for `1.70%` of engine CPU (`1.98%` including per-search root/emit/alloc symbols), and `Board::upcoming_repetition` accounted for `2.81%` (rank `#7`).
4. Bundle `kH = kG + 17 + 18` preserved every known answer, line-for-line UCI output on `T[1..3]` (`4,950` lines), and `V3_VERIFY` across `T[1..10]`, and measured `H1 = 1.0244` CPU (`12/12 > 1`) and `H2 = 1.0194` CPU (`12/12 > 1`).

### Suspicions
1. On the Windows PC (`MinGW libstdc++`), `std::ios_base::sync_with_stdio(false)` in Piece `17` should likewise bypass synchronized `<cstdio>` `getc`/`ungetc` locking on `std::cin`, though the exact percentage gain depends on how `MinGW`'s `msvcrt`/`ucrt` `getc` locks `stdin` vs `glibc`'s `_IO_getc` (`~1.6%` on Linux).
2. In `V2(c)`, the two `3,000,000`-node searches reached `seldepth = 69` and `37` (`< MaxPly = 128`), confirming the note in Section 5 that `V2(c)` exercises deep endgame trees up to ply `69` rather than the `MaxPly` (`128`) ceiling itself.

### What I did not do
- Did **not** run optional row `G20` (`kG_1` vs `kF_sp_1` on `T20`), because `H2` finished at `07:36:56 PM UTC` = minute `65m 50s` from the `06:31:06 PM UTC` job start, and `FABLE_TO_carbon2_30.md` specifies `G20 (only if H2 ended before minute 65)`.
- Did not touch engine source files in `/agent/repos/dwqww`, commit any binary/`perf.data`/`.profraw`/`.profdata`/`.fnn3` file, touch any other branch, or open any pull request.

### What I am not sure about
- What exact fraction of `kH`'s `~2.2%` pooled CPU reduction on `T` (`1.0244` on `H1`, `1.0194` on `H2`) comes from Piece `17` alone versus Piece `18` alone when timed individually in `12`-block ABBA runs (since Job 30 timed the combined bundle `kH` in `H1` and `H2`), and how much of Piece `17`'s `sync_with_stdio(false)` gain carries over on shorter `position` lines or deeper per-move budgets (`T20`).

### Metadata & Final Pre-Commit Check
- **Model:** `Gemini 4 Carbon`
- **`stamps.txt` first line:** `Thu Nov 19 06:31:06 PM UTC 2026 | job 30 received (FABLE_TO_carbon2_30.md); claim committed`
- **`stamps.txt` last line:** `report_ready: Thu Nov 19 07:38:32 PM UTC 2026`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job30` (literal last command before commit):**

```text
 M forge-combo29/carbon2/job30/stamps.txt
?? forge-combo29/carbon2/job30/REPORT_carbon2_job30.md
forge-combo29/carbon2/job30:
17_uci_stdio_and_search_setup.patch.txt
18_fast_upcoming_repetition.patch.txt
builds.txt
CA_stack_slot_oob.patch.txt
control_C30_4blocks_raw.txt
CV1_swap_s0_a0.patch.txt
CV2_no_par_null_walk.patch.txt
partB_kH_known_answers_raw.txt
partR_pieces_known_answers_raw.txt
partV_summary_raw.txt
partV_V1_controls_CV1_CV2_raw.txt
partV_V1_KV1a_GV_T_raw.txt
partV_V1_KV1b_GV_net512_T15_raw.txt
partV_V2_ac_and_CA_raw.txt
partV_V2_b_FA_T10_raw.txt
partV_V2_b_GA_T10_raw.txt
partV_V3_GA_GT_T4_raw.txt
prediction1_job30.txt
prediction2_job30.txt
profile_kG_T.txt
REPORT_carbon2_job30.md
row_H1_12blocks_raw.txt
row_H2_12blocks_raw.txt
stamps.txt
step0_raw.txt
```
