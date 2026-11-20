# `REPORT_carbon2_job37.md` — `carbon2` Job 37 (`v3` Under Checking Builds + Ordinary-Code Controlled Profile of `r15d + v3`)

## (1) Step 0 — `r15d + v3` Fresh-Process & Set `n[1..60]` Verification (`step0_raw.txt`, `run_step0.py`)

Reused SP-PGO `r15d + v3` executable `/tmp/carbon2_job36/bld_sp_sgr15v/forge` (`len=38`, recorded in `forge-combo29/carbon2/job36/builds.txt` and `forge-combo29/carbon2/job37/builds.txt`):
- `exe_sha256 vs recorded`: `PASS (bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810 == bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810)`
- `profdata_sha256 vs recorded`: `PASS (e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc == e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc)`
- `no-option bench 11 (fresh proc)`: `PASS (312866 == 312866)`
- `no-option bench 13 (fresh proc)`: `PASS (862329 == 862329)`
- `no-option perft 5 (fresh proc)`: `PASS (4865609 == 4865609)`
- `PC20 bench 11 (fresh proc)`: `PASS (278024 == 278024)`
- `PC20 bench 13 (fresh proc)`: `PASS (587276 == 587276)`
- `PC20+net768 bench 11 (fresh proc)`: `PASS (882074 == 882074)`
- `PC20+net768 bench 13 (fresh proc)`: `PASS (4275906 == 4275906)`
- Set `n` attempts `1..60` (`PC20 + net768`) through `selfgame` driver with PC line `L` (`selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`):
  - `records`: `PASS (8449 == 8449)`
  - `searches`: `PASS (8482 == 8482)`
  - `nodes`: `PASS (36688357 == 36688357)`
  - `record text sha256`: `PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)`

---

## (2) Prediction Graded (`prediction_job37.txt`, committed alone in `6e8d237dd` at `11:13:57 AM UTC` before Part A)

| # | Item in `prediction_job37.txt` | Pre-Committed Prediction | Measured Outcome | Grade |
|---|---|---|---|---|
| 1 | Part A: every clean checking build gives the plain build's texts with no report | `yes` | `yes`: all 6 `A1` runs (`A`, `C`, `B[1..20]`, `n[1..20]` on line `L` + `C` and `B[1..20]` suite settings), all 6 `A2` lines (`S1..S6`), and all 9 `A3` lines (`B1..B9`) matched plain `v3` byte-for-byte with `0` bytes on `stderr` | **HIT** (`1 == 1`) |
| 2 | Both planted faults of Part A are reported by the sanitizer named for them | `yes` | `yes`: `CP-A` reported `AddressSanitizer: heap-buffer-overflow` (`rc=1`); `CP-U` reported `UndefinedBehaviorSanitizer: signed-integer-overflow` (`rc=1`) | **HIT** (`2 == 2`) |
| 3 | `CO1` (`k` extra calls of `see_ge`): `B1`'s delta in `%` of `BASE`'s engine CPU a game | `[10.2%, 16.5%]` (`k = 8` or `12` from `{4, 8, 12, 16, 20}`) | **`+15.87%`** at **`k = 8`** (`+39.764125 ms/game` on `BASE` `250.635178 ms/game`; `k = 4` gave `+8.16% < 10%`) | **HIT** (`10.20% <= 15.87% <= 16.50%`) |
| 4 | Part B's verdict for `CO1` | `TRUSTED` | **`TRUSTED`** (`|34.335833 - 39.764125| = 5.428292 ms/game <= 11.449518 ms/game`, `error = -13.65%`) | **HIT** (`TRUSTED == TRUSTED`) |

---

## (3) Part A — `v3` Under the Checking Builds (`partA_checking_summary.txt`, `builds.txt`)

All three Part A executables were compiled from `r15d + v3` with `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS` (no profile step; exact flags in `builds.txt`).

### Initial Two Numbers per Checking Build (`bench 11` and `go perft 5`)
- `v3_chk_clean` (`sha256 = 4cb91052998c98fcb80ba45a5d217bddb37fab01a4882c971b3a19b1d69f1ba1`):
  - `bench 11`: `PASS (312866 == 312866)` | `go perft 5`: `PASS (4865609 == 4865609)` | `stderr_bytes`: `PASS (0 == 0)`
- `v3_chk_CPA` (`sha256 = c3e61538eedb8052ee2c55c362b775dcdee918a1839849bf2aa86d5095e10caf`, `control_CPA_s3_heap_oob.patch.txt`):
  - `bench 11`: `PASS (312866 == 312866)` | `go perft 5`: `PASS (4865609 == 4865609)` | `stderr_bytes`: `PASS (0 == 0)`
- `v3_chk_CPU` (`sha256 = 6cf02404e3cf48a389ae8b3dc6d03ca6daf66c7a9a21edc7bdfea272e1d22ae8`, `control_CPU_sgend_signed_ovf.patch.txt`):
  - `bench 11`: `PASS (312866 == 312866)` | `go perft 5`: `PASS (4865609 == 4865609)` | `stderr_bytes`: `PASS (0 == 0)`

### `A1` — Driver Runs: Plain `v3` vs Clean Checking `v3` (`partA_checking_summary.txt`, `partA_chk_*_rows.txt`)
Both literal line `L` across all four sets and suite-specific settings for `C` (`N=300..`) and `B[1..20]` (`N=50`, exercising `sgerror reason noscore` throw-away handling) were run:

| Set & Mode | Attempts (`fin` / `thrown`) | Records (`chk == plain`) | Nodes (`chk == plain`) | Record Text `sha256` (`checking == plain`) | `stderr` Bytes (`chk` / `plain`) |
|---|---|---|---|---|---|
| `Set_A_L` (`A[1..200]`, line `L`) | `200` (`200` / `0`) | `PASS (26741 == 26741)` | `PASS (107124743 == 107124743)` | `PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)` | `PASS (0 == 0)` / `PASS (0 == 0)` |
| `Set_C_L` (`C[1..100]`, line `L`) | `100` (`100` / `0`) | `PASS (12797 == 12797)` | `PASS (50717759 == 50717759)` | `PASS (9037608e3ca5be84cb3b3a538abf9d012944711838fd32736b535c6677a85946 == 9037608e3ca5be84cb3b3a538abf9d012944711838fd32736b535c6677a85946)` | `PASS (0 == 0)` / `PASS (0 == 0)` |
| `Set_B20_L` (`B[1..20]`, line `L`) | `20` (`20` / `0`) | `PASS (2831 == 2831)` | `PASS (11118408 == 11118408)` | `PASS (4f995cae22d6bce679733bdeadb49424eaa6d95d32a507fef4267ca90de424ac == 4f995cae22d6bce679733bdeadb49424eaa6d95d32a507fef4267ca90de424ac)` | `PASS (0 == 0)` / `PASS (0 == 0)` |
| `Set_n20_L` (`n[1..20]`, `PC20+net768`, line `L`) | `20` (`20` / `0`) | `PASS (2773 == 2773)` | `PASS (11984695 == 11984695)` | `PASS (447f9241c00ae3bf73112e0c18f94f1a35c7fa70c4ad180406e06ad19c584400 == 447f9241c00ae3bf73112e0c18f94f1a35c7fa70c4ad180406e06ad19c584400)` | `PASS (0 == 0)` / `PASS (0 == 0)` |
| `Set_C_suite` (`C[1..100]`, suite `N=300..`) | `100` (`100` / `0`) | `PASS (2904 == 2904)` | `PASS (1433776 == 1433776)` | `PASS (4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf)` | `PASS (0 == 0)` / `PASS (0 == 0)` |
| `Set_B20_suite` (`B[1..20]`, suite `N=50`) | `20` (`9` / `11`) | `PASS (919 == 919)` | `PASS (109569 == 109569)` | `PASS (31f43fb43945e0ecf5c5867a287eaa19aae8bb238646e30043020d5271c5a6bf == 31f43fb43945e0ecf5c5867a287eaa19aae8bb238646e30043020d5271c5a6bf)` | `PASS (0 == 0)` / `PASS (0 == 0)` |

### `A2` — Six Strict-Line Inputs `S1..S6` on Clean Checking Build (Fresh Process Each)
- `S1`: `PASS ('sgerror badline evallimt' == 'sgerror badline evallimt', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- `S2`: `PASS ('sgerror badline 2k' == 'sgerror badline 2k', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- `S3`: `PASS ('sgerror badline drawcount' == 'sgerror badline drawcount', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- `S4`: `PASS ('sgerror badline maxply' == 'sgerror badline maxply', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- `S5`: `PASS ('sgerror badline -5' == 'sgerror badline -5', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- `S6`: `PASS ('sgerror badline 300x' == 'sgerror badline 300x', readyok='readyok' == 'readyok', stderr_bytes: 0 == 0)`
- Overall `A2`: `PASS (6 == 6)`

### `A3` — Nine `KB9` Boundary Lines `B1..B9` on Clean Checking Build vs Plain Build
- `B1`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 fen rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3 moves`
- `B2`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 fen 5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 2 10 moves`
- `B3`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5 moves`
- `B4`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5 moves`
- `B5`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1 moves`
- `B6`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80 moves`
- `B7`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 1 reason mate plies 0 run 0 searches 0 nodes 0 fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80 moves`
- `B8`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 0 reason stalemate plies 0 run 0 searches 0 nodes 0 fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1 moves`
- `B9`: `EQUAL` (`stderr_bytes: 0 == 0`) — `sgend result 1 reason matescore plies 0 run 0 searches 1 nodes 1152 fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1 moves`
- Overall `A3`: `PASS (9 == 9)`

### `A4` — Thread Where `run_selfgame` Runs
- **Source location**: `src/uci.cpp:1228` (`run_selfgame(board, searcher, move_overhead_ms, multipv, sg_cfg);`), called synchronously inside `forge::uci_loop(std::istream& in)` (`src/uci.cpp:618`) after `stop_search()` (`src/uci.cpp:1209`).
- **Measured confirmation from `CP-U` stack unwinding (`partA_CPU_stderr_raw.txt`)**: `#0 run_selfgame ...` -> `#1 forge::uci_loop(std::istream&) ...` -> `#3 __libc_start_main` (main thread `T0`, not a separate worker thread). Therefore the conditional `-fsanitize=thread` build was not triggered.

### Controls `CP-A` and `CP-U` (`control_CPA_s3_heap_oob.patch.txt`, `control_CPU_sgend_signed_ovf.patch.txt`, `partA_CPA_stderr_raw.txt`, `partA_CPU_stderr_raw.txt`)
- **`CP-A`** (`control_CPA_s3_heap_oob.patch.txt`, `sha256 = 4e5727a97db3eef20e16fb01563631736d21826da725513f0172dd1bb4122211`):
  - Because `parse_selfgame_config` views `std::getline`'s `std::string` (which carries a trailing NUL), per spec `CP-A` copies the line into an exact-length `new char[orig_line.size()]` heap allocation and reads `exact_copy[orig_line.size()]` on `S3`'s missing-value path.
  - Non-zero exit: `PASS (1 == 1)` (`returncode = 1`, `stderr_bytes = 3187`).
  - Sanitizer first report line:
    `==31493==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x508000000100 at pc 0x55cfe0f3f0d4 bp 0x7ffe0f9beef0 sp 0x7ffe0f9beee8`
- **`CP-U`** (`control_CPU_sgend_signed_ovf.patch.txt`, `sha256 = 7c8e14d209a3fa1994e32f700311af50050ce051ef95082cf27acbdde793aa9c`):
  - Adds `ply` (`108` on Set `A` attempt 1) to `INT_MAX` (`2147483647`) in a signed `int` stored to a `volatile int` right before writing `sgend`.
  - Non-zero exit: `PASS (1 == 1)` (`returncode = 1`, `stderr_bytes = 920`).
  - Sanitizer first report line:
    `/tmp/carbon2_job37/src_chk_cpu/src/uci.cpp:603:64: runtime error: signed integer overflow: 2147483647 + 108 cannot be represented in type 'int'`

---

## (4) Part B — Profile With Controls of Ordinary Code (`partB_purity_and_objdump.txt`, `partB_B1_clock_blocks_raw.txt`, `partB_B2_perf_deltas_raw.txt`, `partB_B3_B4_tables_raw.txt`)

### Build Recipe, Choice of `k` and `k2`, `objdump -d` Counts, and Purity Checks
- **One identical recipe (`builds.txt`)**: `BASE`, `CO1`, and `CO2` were compiled with the exact same flags (`-O3 -DNDEBUG -g -fno-omit-frame-pointer`, no profile step, PC defines, `-march=sapphirerapids`, `-fuse-ld=lld-18`).
- **`CO1` (`partB_CO1_see_ge.patch.txt`, `sha256 = 14a9acdd9bd95e1f0628fa979713f39230b2cbd9b512c434dc8816aca1f93d80`)**:
  - Target: `forge::Board::see_ge(const forge::Move&, int) const` at all **7** call sites in `src/search.cpp` (`r15d` lines `724, 1386, 1857, 2153, 2299, 2319, 2370`; the 1 internal call inside `Board::static_exchange` in `src/board.cpp` stays untouched).
  - Calibration from `k = 4`: on warm `W[1..30]`, `k = 4` gave `+8.16%` (`< 10%`); stepping to **`k = 8`** on the pre-declared ladder `{4, 8, 12, 16, 20}` gave **`+15.87%` (`>= 10%`)**.
- **`CO2` (`partB_CO2_apply_pair_and_evaluate.patch.txt`, `sha256 = 428e384da7c4431b155ba401a5618c9115c07c0f086d69f65ec4ff39766152d8`)**:
  - Target: `forge::nnue::v3::apply_pair_and_evaluate(...)`, called **`k2 = 4`** extra times at its **1** sole call site in the codebase (`src/search.cpp:3393`, inside `Worker::static_evaluate_v3`).
  - Share note (reported upfront per `=== STOPS ===`): in our Job 34 table (`forge-combo29/carbon2/job34/P2_outside_search_raw.txt`), `apply_pair_and_evaluate` was Rank #1 at `6.32%` vs `Board::see_ge` `2.07%` (**`3.05x >= 2x`**). On `r15d + v3` `BASE` (where `FORGE_SDK_SEE_HOIST = 0`, unlike Job 34's `kK`), `Board::see_ge`'s inclusive share is `4.55%` (`2.23%` self) and `apply_pair_and_evaluate`'s inclusive share is `6.79%` (`1.49x` inclusive on `BASE`, `3.05x` in Job 34's table). From `BASE`'s full inclusive ranking, zero pure functions exist above `6.79%` inclusive on `BASE` (`Worker::search` `98.54%`, `search_child` `~70%`, `qsearch` `24.15%`, `static_evaluate` `~24%`, `static_evaluate_v3` `23.58%`, `MovePicker::next` `20.29%`, and `make_valid` all mutate search/TT/MovePicker/RefreshCache state), making `apply_pair_and_evaluate` the largest pure function in `BASE`.
  - Why pure: all input arguments (`net`, `parent = v3_state_->stack[index-1]`, `key0`, `king0`, `key1`, `king1`, `dirty`, `board`) are `const`; the `k2 = 4` extra calls write only into a dedicated `thread_local nnue::v3::Accumulator co2_scratch` (never read anywhere in the engine) and a `volatile int co2_sink` after `asm volatile("" ::: "memory")`.
- **Proof the extra calls exist (`objdump -d -C` direct `callq` counts, side by side)**:
  - `Board::see_ge`: `BASE` = **`8`** (`7` in `search.cpp` + `1` in `board.cpp`) vs `CO1(k=8)` = **`64`** (`63 = 7 * (1 + 8)` in `search.cpp` + `1` in `board.cpp`): `PASS (63 == 63)`.
  - `nnue::v3::apply_pair_and_evaluate`: `BASE` = **`1`** vs `CO2(k2=4)` = **`5`** (`= 1 + 4`): `PASS (5 == 5)`.
- **Known-answer purity checks on `W[1..60]` (`PC20 + net768`, line `L`)**:
  - `BASE`: `bench 11` `PASS (312866 == 312866)` | `perft 5` `PASS (4865609 == 4865609)` | `records` `PASS (8449 == 8449)` | `searches` `PASS (8482 == 8482)` | `nodes` `PASS (36688357 == 36688357)` | `sha256` `PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)`
  - `CO1(k=8)`: `bench 11` `PASS (312866 == 312866)` | `perft 5` `PASS (4865609 == 4865609)` | `records` `PASS (8449 == 8449)` | `searches` `PASS (8482 == 8482)` | `nodes` `PASS (36688357 == 36688357)` | `sha256` `PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)`
  - `CO2(k2=4)`: `bench 11` `PASS (312866 == 312866)` | `perft 5` `PASS (4865609 == 4865609)` | `records` `PASS (8449 == 8449)` | `searches` `PASS (8482 == 8482)` | `nodes` `PASS (36688357 == 36688357)` | `sha256` `PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)`

### `B1` — Clock Deltas (`10` Blocks `ABBA / BAAB` on `W[1..30]`, Pinned Driver CPU `0` / Engine CPU `3`, `partB_B1_clock_blocks_raw.txt`)
All `42` legs (`2` warmups left out + `40` timed legs) per control produced exact `W[1..30]` `nodes = 19,817,880` and `sha256 = e184b1746334f9710f6f0ee494dd9cef37281788b7f17c030717d2f723acf15f` (`PASS (42 == 42)` each).

| Block | Order | `CO1(k=8)`: `BASE` (ms/g) | `CO1(k=8)`: `CTRL` (ms/g) | `CO1 - BASE` (ms/g) | `CO2(k2=4)`: `BASE` (ms/g) | `CO2(k2=4)`: `CTRL` (ms/g) | `CO2 - BASE` (ms/g) |
|---|---|---|---|---|---|---|---|
| 1 | `ABBA` | `251.0962` | `290.4964` | `+39.4001` (`+15.69%`) | `251.2103` | `293.3108` | `+42.1005` (`+16.76%`) |
| 2 | `BAAB` | `249.4982` | `292.2022` | `+42.7040` (`+17.12%`) | `252.4468` | `297.1416` | `+44.6948` (`+17.70%`) |
| 3 | `ABBA` | `257.1861` | `293.3325` | `+36.1465` (`+14.05%`) | `251.2679` | `294.0093` | `+42.7414` (`+17.01%`) |
| 4 | `BAAB` | `252.1083` | `294.6360` | `+42.5276` (`+16.87%`) | `257.0650` | `302.5916` | `+45.5266` (`+17.71%`) |
| 5 | `ABBA` | `250.0628` | `291.3388` | `+41.2760` (`+16.51%`) | `252.9867` | `294.4990` | `+41.5124` (`+16.41%`) |
| 6 | `BAAB` | `251.1801` | `289.5347` | `+38.3546` (`+15.27%`) | `256.1653` | `293.2576` | `+37.0922` (`+14.48%`) |
| 7 | `ABBA` | `247.8571` | `287.7663` | `+39.9092` (`+16.10%`) | `257.2250` | `301.7638` | `+44.5388` (`+17.32%`) |
| 8 | `BAAB` | `247.9672` | `288.2092` | `+40.2419` (`+16.23%`) | `254.3840` | `296.1027` | `+41.7187` (`+16.40%`) |
| 9 | `ABBA` | `248.9681` | `288.7343` | `+39.7662` (`+15.97%`) | `254.4541` | `300.4210` | `+45.9669` (`+18.06%`) |
| 10 | `BAAB` | `250.4277` | `287.7426` | `+37.3149` (`+14.90%`) | `250.9321` | `293.9953` | `+43.0631` (`+17.16%`) |
| **Pooled** | `600g/side` | **`250.635178`** | **`290.399303`** | **`+39.764125` (`+15.87%`)** | **`253.813730`** | **`296.709268`** | **`+42.895538` (`+16.90%`)** |
| **`t-95` `h`** | `df = 9` | `sd = 2.108719` | — | **`h = 1.508486` (`3.79%` of `B1`)** | `sd = 2.580985` | — | **`h = 1.846326` (`4.30%` of `B1`)** |

### `B2` — Profiler Deltas, Errors, and Verdicts (`perf record -e task-clock -c 50000 -g` on `W[1..60]`, `partB_B2_perf_deltas_raw.txt`)

| Metric | `CO1` (`k = 8`, `Board::see_ge`) | `CO2` (`k2 = 4`, `nnue::v3::apply_pair_and_evaluate`) |
|---|---|---|
| `BASE` inclusive function samples (`W[1..60]`) | `13,758` (`4.55%` of `302,199`) | `20,526` (`6.79%` of `302,199`) |
| `CTRL` inclusive function samples (`W[1..60]`) | `54,961` (`15.97%` of `344,059`) | `67,870` (`19.29%` of `351,907`) |
| Function inclusive sample diff (`CTRL - BASE`) | `+41,203` samples | `+47,344` samples |
| Total `forge` sample diff (`CTRL - BASE`) | `+41,860` (`344,059 - 302,199`) | `+49,708` (`351,907 - 302,199`) |
| **`B2` function delta** (`diff * 50 us / 60`) | **`+34.335833 ms/game`** | **`+39.453333 ms/game`** |
| **`B2` total delta** (`tot_diff * 50 us / 60`) | **`+34.883333 ms/game`** | **`+41.423333 ms/game`** |
| **`B1` clock delta** (`± h`) | **`+39.764125 ± 1.508486 ms/game`** | **`+42.895538 ± 1.846326 ms/game`** |
| **Relative attribution error** `(B2 - B1) / B1` | **`-13.65%`** | **`-8.02%`** |
| **Trust bound** `|B2 - B1| <= 0.25 * B1 + h` | `5.428292 <= 11.449518 ms/game` | `3.442205 <= 12.570210 ms/game` |
| **Verdict** | **`TRUSTED`** | **`TRUSTED`** |

Both scalar/bitboard control `CO1` (`Board::see_ge`) and AVX-512 NNUE control `CO2` (`apply_pair_and_evaluate`) pass **`TRUSTED`**, so function-level shares for both scalar/bitboard search/movepick functions and AVX-512 NNUE functions can be quoted as findings.

### `B3` — The Table (`BASE` on `W[1..60]`, `302,199` Samples = `15.1100 s` Task-Clock vs `15.1137 s` `rusage`, `partB_B3_B4_tables_raw.txt`)

| Rank | Self Samples | Self `%` | Inclusive Samples | Inclusive `%` | Function (`BASE`) |
|---|---|---|---|---|---|
| 1 | `42,736` | `14.14%` | `297,780` | `98.54%` | `forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)` |
| 2 | `17,297` | `5.72%` | `17,489` | `5.79%` | `forge::nnue::v3::(anonymous namespace)::apply_pair_and_sum_avx512(...)` |
| 3 | `9,626` | `3.19%` | `13,857` | `4.59%` | `forge::Worker::corrected_eval(forge::Board const&, int, forge::SearchStack const*) const` |
| 4 | `9,074` | `3.00%` | `17,951` | `5.94%` | `forge::nnue::v3::refresh_from_pieces(...)` |
| 5 | `8,089` | `2.68%` | `8,090` | `2.68%` | `forge::nnue::v3::(anonymous namespace)::apply_changes_pair_avx512(...)` |
| 6 | `7,358` | `2.43%` | `19,031` | `6.30%` | `forge::MovePicker::pick_best()` |
| 7 | `6,863` | `2.27%` | `10,740` | `3.55%` | `forge::TTProbe forge::TranspositionTable::probe_body<false>(unsigned long) const` |
| 8 | `6,730` | `2.23%` | `13,758` | `4.55%` | `forge::Board::see_ge(forge::Move const&, int) const` |
| 9 | `6,559` | `2.17%` | `72,984` | `24.15%` | `forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)` |
| 10 | `6,119` | `2.02%` | `10,921` | `3.61%` | `forge::MovePicker::QuietScorer::score(forge::Move, std::array<unsigned long, 7ul> const&) const` |
| 11 | `5,824` | `1.93%` | `61,323` | `20.29%` | `forge::MovePicker::next(bool)` |
| 12 | `5,087` | `1.68%` | `5,713` | `1.89%` | `forge::nnue::v3::(anonymous namespace)::output_sum_avx512(...)` |
| 13 | `4,658` | `1.54%` | `7,484` | `2.48%` | `forge::Board::make_move(forge::Move const&, forge::Undo&)` |
| 14 | `4,620` | `1.53%` | `5,474` | `1.81%` | `forge::(anonymous namespace)::ensure_piece_diff(forge::SearchStack*)` |
| 15 | `4,074` | `1.35%` | `4,075` | `1.35%` | `forge::nnue::v3::(anonymous namespace)::add_column_avx512(...)` |
| 16 | `3,723` | `1.23%` | `5,512` | `1.82%` | `forge::Board::square_attacked_with_occupancy(int, forge::Color, unsigned long, unsigned long) const` |
| 17 | `3,363` | `1.11%` | `3,364` | `1.11%` | `forge::nnue::v3::(anonymous namespace)::sub_column_avx512(...)` |
| 18 | `3,276` | `1.08%` | `3,878` | `1.28%` | `forge::Board::upcoming_repetition(unsigned long) const` |
| 19 | `3,147` | `1.04%` | `5,965` | `1.97%` | `forge::Board::unmake_move(forge::Move const&, forge::Undo const&)` |
| 20 | `3,128` | `1.04%` | `4,114` | `1.36%` | `forge::Board::key_after(forge::Move const&, unsigned long&) const` |
| 21 | `3,081` | `1.02%` | `3,533` | `1.17%` | `std::__unguarded_linear_insert<forge::MovePicker::Scored*, ...>` |
| 22 | `3,071` | `1.02%` | `71,262` | `23.58%` | `forge::Worker::static_evaluate_v3(forge::Board const&, forge::SearchStack*)` |
| 23 | `3,028` | `1.00%` | `3,028` | `1.00%` | `forge::nnue::v3::(anonymous namespace)::apply_changes_avx512(...)` |
| 24 | `2,770` | `0.92%` | `2,779` | `0.92%` | `forge::attacks::Magic::index(unsigned long) const` |
| 25 | `2,629` | `0.87%` | `3,446` | `1.14%` | `void forge::TranspositionTable::store_body<false>(...)` |

#### `B3` Seven-Group Partition (`BASE`)
| Group | `B3` Samples | `B3` Share `%` |
|---|---|---|
| `the search` *(includes `57,461` samples = `19.01%` in `Board` make/unmake/legality/repetition helpers called from search)* | `152,200` | **`50.36%`** |
| `the net` | `71,275` | **`23.59%`** |
| `move generation` | `5,142` | **`1.70%`** |
| `the move picker with SEE and the sort` | `53,314` | **`17.64%`** |
| `hashing and the transposition table` | `17,326` | **`5.73%`** |
| `the game loop itself` | `128` | **`0.04%`** |
| `the rest` | `2,814` | **`0.93%`** |
| **Total** (`PASS (302199 == 302199)`) | **`302,199`** | **`100.00%`** |

#### What I Would Do Next (Three Largest Actionable Items on `r15d + v3`, Gains Marked as **Guesses**)
1. **NNUE v3 king-move single-side refresh + accumulator update path (`the net`, `23.59%`: `make_valid` + `refresh_from_pieces` `5.94%` incl + `apply_changes_pair_avx512` `2.68%` + `output_sum_avx512` `1.89%` + `ensure_piece_diff` `1.81%`)**: fuse single-king-move one-side refresh + other-side delta + output dot product (`apply_one_refresh_one_and_evaluate` as in `kK` Piece 20 / Piece 16) and compute `DirtyPieces` eagerly in `make_move` instead of `ensure_piece_diff`. **Guess of gain**: **`~4%–7%`** of engine CPU on `W` (*guess*).
2. **Move picker selection sort, `Board::see_ge`, and quiet scoring (`the move picker with SEE and the sort`, `17.64%`: `MovePicker::pick_best` + `__unguarded_linear_insert` `7.47%` incl, `Board::see_ge` `4.55%` incl, `QuietScorer::score` `3.61%` incl)**: hoist per-side king contact/sniper bitboards out of `Board::see_ge`'s exchange loop (`FORGE_SDK_SEE_HOIST`, cutting `see_ge` roughly in half on `kF`/`kK`), store bad captures in-place (`FORGE_SDK_BADCAP_PREFIX`), and defer full insertion sort of quiets behind incremental selection / SIMD max-scan. **Guess of gain**: **`~3%–6%`** of engine CPU on `W` (*guess*).
3. **Correction-history & continuation-history random-access stalls in `the search` (`Worker::corrected_eval` `4.59%` incl + `QuietScorer::score` `3.61%` incl + `key_after` / `prefetch` path)**: prefetch correction-history entries alongside TT prefetch after `make_move` and compact the hot history layout to cut LLC/L2 misses (especially relevant when 16 engines share L3 on the PC). **Guess of gain**: **`~2%–4%`** of engine CPU on `W` (*guess*).

---

## (5) `B4` — SP-PGO + ThinLTO Table Beside `B3` (`partB_B3_B4_tables_raw.txt`)

`B4_SP_PGO` (`/tmp/carbon2_job37/bld_pB_B4SP/forge`, `sha256 = d85299dc25f2bafd896094e6057d6b75c6d86e34c50360cf74ce0d66ffce2dd3`, built with Job 35/36's SP-PGO + ThinLTO recipe plus `-g -fno-omit-frame-pointer`) passed `bench 11` (`312866 == 312866`), `perft 5` (`4865609 == 4865609`), and `W[1..60]` (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`), and reduced total `W[1..60]` task-clock samples from `302,199` (`15.1100 s`) to **`287,324` (`14.3662 s`, `-4.92%`)**.

### `B3` vs `B4` Side-by-Side Group Table
| Group | `B3` (`BASE`) Samples (`%`) | `B4` (`SP-PGO`) Samples (`%`) | Sample Change (`B4 - B3`) |
|---|---|---|---|
| `the search` | `152,200` (`50.36%`) | `130,034` (`45.26%`) | `-22,166` (`-14.56%`) |
| `the net` | `71,275` (`23.59%`) | `67,262` (`23.41%`) | `-4,013` (`-5.63%`) |
| `move generation` | `5,142` (`1.70%`) | `4,849` (`1.69%`) | `-293` (`-5.70%`) |
| `the move picker with SEE and the sort` | `53,314` (`17.64%`) | `48,173` (`16.77%`) | `-5,141` (`-9.64%`) |
| `hashing and the transposition table` | `17,326` (`5.73%`) | `33,805` (`11.77%`) | `+16,479` (`+95.11%`) |
| `the game loop itself` | `128` (`0.04%`) | `193` (`0.07%`) | `+65` (`+50.78%`) |
| `the rest` | `2,814` (`0.93%`) | `3,008` (`1.05%`) | `+194` (`+6.89%`) |
| **Total** | **`302,199` (`100.00%`)** | **`287,324` (`100.00%`)** | **`-14,875` (`-4.92%`)** |

### `B4` Top 25 Functions by Self Samples (`287,324` Total Samples)
1. `Worker::search` (`28,497` = `9.92%` self, `98.48%` incl; down from `14.14%` self in `B3`)
2. `nnue::v3::apply_pair_and_sum_avx512` (`17,501` = `6.09%` self, `6.12%` incl)
3. `TranspositionTable::prefetch` (`16,736` = `5.82%` self, `6.07%` incl; inlined into `Worker::search` & `qsearch`)
4. `Worker::corrected_eval` (`10,014` = `3.49%` self, `4.98%` incl)
5. `nnue::v3::refresh_from_pieces` (`8,989` = `3.13%` self, `6.11%` incl)
6. `nnue::v3::apply_changes_pair_avx512` (`8,186` = `2.85%` self, `2.85%` incl)
7. `MovePicker::pick_best` (`6,591` = `2.29%` self, `6.50%` incl)
8. `TranspositionTable::probe_body<false>` (`6,309` = `2.20%` self, `3.65%` incl)
9. `nnue::v3::output_sum_avx512` (`5,031` = `1.75%` self, `1.98%` incl)
10. `Board::see_ge` (`5,012` = `1.74%` self, `4.29%` incl)
11. `ensure_piece_diff` (`4,534` = `1.58%` self, `1.88%` incl)
12. `Board::make_move` (`4,337` = `1.51%` self, `2.36%` incl)
13. `MovePicker::QuietScorer::score` (`4,254` = `1.48%` self, `3.32%` incl)
14. `nnue::v3::add_column_avx512` (`4,178` = `1.45%` self, `1.45%` incl)
15. `Board::square_attacked_with_occupancy` (`3,728` = `1.30%` self, `1.91%` incl)
16. `MovePicker::next` (`3,700` = `1.29%` self, `19.79%` incl)
17. `Board::upcoming_repetition` (`3,503` = `1.22%` self, `1.46%` incl)
18. `std::__unguarded_linear_insert<MovePicker::Scored*, ...>` (`3,367` = `1.17%` self, `1.28%` incl)
19. `b4::blend` (`3,323` = `1.16%` self, `1.16%` incl)
20. `nnue::v3::sub_column_avx512` (`3,236` = `1.13%` self, `1.13%` incl)
21. `Board::unmake_move` (`3,207` = `1.12%` self, `1.97%` incl)
22. `Worker::qsearch` (`3,138` = `1.09%` self, `24.73%` incl)
23. `Board::key_after` (`3,071` = `1.07%` self, `1.30%` incl)
24. `nnue::v3::apply_changes_avx512` (`3,029` = `1.05%` self, `1.05%` incl)
25. `attacks::Magic::index` (`2,952` = `1.03%` self, `1.03%` incl)

### Which Functions the SP-PGO + ThinLTO Step Inlines Into Others (`partB_B3_B4_tables_raw.txt`)
Measured directly from `objdump -d -C` `callq` reductions (`BASE -> B4`) and DWARF inline `(innermost -> host)` pairs:
1. **Cross-TU NNUE inlining into `Worker::static_evaluate_v3`**: `nnue::v3::apply_pair_and_evaluate` (`1 -> 0` `callq`s), `apply_pair_and_sum_avx512` (`17,501` samples = `6.09%` now physically inside `static_evaluate_v3`), and `nnue::v3::finish` (`1,124` samples = `0.39%`) are inlined directly into `Worker::static_evaluate_v3`; `apply_changes_pair_avx512` (`2 -> 0` `callq`s, `8,172` samples = `2.84%`) is inlined into `nnue::v3::apply_changes_pair`.
2. **Inlining into `Worker::search` and `Worker::qsearch`**:
   - `TranspositionTable::prefetch` (`13,415` samples = `4.67%` in `Worker::search`, `3,321` = `1.16%` in `Worker::qsearch`; `137` and `13` in `BASE`) and `TranspositionTable::store_body<false>` (`1,420` samples = `0.49%`) are inlined cross-TU into `Worker::search` / `qsearch` (shifting `+16,479` samples of post-`prefetch` stall attribution from `Worker::search` to `TranspositionTable::prefetch` while cutting combined `search + hashing` by `-5,687` samples).
   - `MovePicker::pick_best` (`4 -> 0` `callq`s, `5,834` samples = `2.03%`), `MovePicker::next` (`9 -> 6` `callq`s, `2,828` samples = `0.98%`), `MovePicker::generate_captures` (`2 -> 0` `callq`s), `Worker::corrected_eval` (`3 -> 2` `callq`s, `6,085` samples = `2.12%`), `Worker::quiet_history` (`1 -> 0` `callq`s, `1,703` samples = `0.59%`), `Board::make_move` (`3,831` samples = `1.33%`), `Board::unmake_move` (`5 -> 3` `callq`s, `2,787` samples = `0.97%`), `Board::key_after` (`2 -> 0` `callq`s, `2,497` samples = `0.87%`), and `Board::is_repetition` (`6 -> 1` `callq`s, `1,534` samples = `0.53%`) are inlined into `Worker::search`.
3. **Inlining inside `MovePicker` and `TranspositionTable`**: `QuietScorer::score` (`3,229` samples = `1.12%`) and `b4::blend` (`2,082` samples = `0.72%`) are inlined into `MovePicker::generate_quiets`; `TranspositionTable::probe_body<false>` (`6,309` samples = `2.20%`) is inlined into `TranspositionTable::probe_owned`; `Board::see_ge` inside `Board::static_exchange` (`1 -> 0` `callq`s in `board.cpp`, while the `7` `search.cpp` `callq`s remain out-of-line).

---

## WHAT THIS CANNOT SEE

Windows, the PC's compiler (llvm-mingw clang) and its profile-guided exe; the PC's Python and pipes; more than one
thread; the PC's processor (16 threads, a 96 MB L3 shared by 16 engines): a function share on this machine is a
direction for the PC, not its number.

---

## Facts (Measured Only)

1. `r15d + v3` passed all 7 Step 0 fresh-process node checks and produced `8,449` records, `8,482` searches, `36,688,357` nodes, and `sha256 = b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15` on Set `n[1..60]` with line `L`.
2. Clean checking `v3` (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`) matched plain `v3` byte-for-byte across all 6 `A1` suite runs (`Set_A_L`, `Set_C_L`, `Set_B20_L`, `Set_n20_L`, `Set_C_suite`, `Set_B20_suite`), all 6 `A2` strict-line inputs `S1..S6` (plus `readyok`), and all 9 `A3` boundary inputs `B1..B9`, with `0` bytes on `stderr` in every run.
3. Planted controls `CP-A` and `CP-U` exited with `returncode = 1` and reported `AddressSanitizer: heap-buffer-overflow` and `UndefinedBehaviorSanitizer: signed-integer-overflow` respectively, and `CP-U`'s runtime stack trace confirmed `run_selfgame` executes on thread `T0` inside `forge::uci_loop`.
4. On `W` (`Set n` with `PC20 + net768` and line `L`, pinned `driver CPU 0 / engine CPU 3`), `CO1(k=8)` increased engine CPU by `+39.764125 ± 1.508486 ms/game` (`+15.87%`) vs `B2` inclusive delta `+34.335833 ms/game` (`error = -13.65%`, **`TRUSTED`**), and `CO2(k2=4)` increased engine CPU by `+42.895538 ± 1.846326 ms/game` (`+16.90%`) vs `B2` inclusive delta `+39.453333 ms/game` (`error = -8.02%`, **`TRUSTED`**).
5. On `BASE` (`W[1..60]`), `the search` is `50.36%`, `the net` is `23.59%`, `the move picker with SEE and the sort` is `17.64%`, `hashing and the transposition table` is `5.73%`, `move generation` is `1.70%`, `the rest` is `0.93%`, and `the game loop itself` is `0.04%` (`0.07%` on `B4_SP_PGO`), confirming that inside the engine `run_selfgame`'s own loop overhead is `< 0.1%` of engine CPU.

---

## Suspicions (Apart from Measured Facts)

1. Both `CO1` (`error = -13.65%`) and `CO2` (`error = -8.02%`) have slightly negative `B2 - B1` per-game deltas (`-5.428` and `-3.442 ms/game`), and almost the entire difference is explained by two structural effects: first, `B1` runs on `W[1..30]` (`19,817,880 / 30 = 660,596` nodes/game) whereas `B2` runs on `W[1..60]` (`36,688,357 / 60 = 611,473` nodes/game, **`-7.44%` fewer nodes/game** than `W[1..30]`); second, the ~`0.55–1.97 ms/game` gap between `B2` total delta and `B2` function delta reflects `asm volatile("" ::: "memory")`, `volatile` sink stores, and call/return instructions executing inside the caller rather than inside the callee.
2. In `B4_SP_PGO`, the jump of `TranspositionTable::prefetch` from `< 0.9%` in `BASE` to `5.82%` self (`16,736` samples) when inlined into `Worker::search` and `Worker::qsearch` is likely PMU instruction-pointer skid / ROB drain onto the instructions immediately following `prefetcht0` rather than `prefetcht0` itself consuming `5.82%` of execution resources.

---

## Read and Not Tested (Apart from Measured Facts)

1. From reading `src/uci.cpp:618` and `src/uci.cpp:1209..1228`, `forge::uci_loop` calls `stop_search()` before `run_selfgame(...)` and does not spawn any background thread for `selfgame` (`searcher.go(...)` runs synchronously when `Threads = 1`). Because `run_selfgame` runs on the UCI loop thread, no `-fsanitize=thread` build was compiled or run.
2. From reading `src/search.cpp:3367..3422` and `src/movepick.cpp`, `Worker::static_evaluate_v3` mutates `v3_state_->valid_flags` and `v3_state_->cache`, and `MovePicker::next` mutates `stage_`, `index_`, and `bad_count_`; we did not build planted controls for those stateful functions because they violate `CO2`'s purity requirement.

---

## What I Did Not Do

1. Did not run `-fsanitize=thread` in Part A (`A4` conditional branch did not trigger because `run_selfgame` runs on the UCI input thread).
2. Did not run `A1` on `B[21..200]` or `n[21..60]` under the ASan+UBSan checking build (`A1` specified `B`'s attempts `1..20` and `n`'s attempts `1..20`).
3. Did not test Windows `llvm-mingw`, multi-threaded (`Threads > 1`), or 16-way concurrent L3-contended profiles.

---

## What I Am Not Sure About

1. On the target Windows PC (`16` engine processes sharing a `96 MB` L3 cache), DRAM/L3 miss stalls in `TranspositionTable::probe_body`, `Worker::corrected_eval`, `QuietScorer::score`, and `refresh_from_pieces` will likely occupy a substantially larger share of engine CPU than on this single-pair pinned Sapphire Rapids VM (`hashing and the transposition table` `5.73%` in `B3` / `11.77%` in `B4`).
2. Whether `CO2`'s `"inclusive share at least twice see_ge's"` was intended to be evaluated on the Job 34 table (`6.32%` vs `2.07%` = `3.05x`, satisfied) or on `r15d + v3` `BASE` (`6.79%` vs `4.55%` = `1.49x`, where `FORGE_SDK_SEE_HOIST=0` makes `see_ge` twice as large and no pure function exists above `6.79%`). Both numbers are reported above.

---

## Model Name

`Gemini 4 Carbon`

---

## Final Repository & Directory Check (`git status --short && ls -R forge-combo29/carbon2/job37`)

```text
 M forge-combo29/carbon2/job37/stamps.txt
?? forge-combo29/carbon2/job37/REPORT_carbon2_job37.md
forge-combo29/carbon2/job37:
builds.txt
control_CPA_s3_heap_oob.patch.txt
control_CPU_sgend_signed_ovf.patch.txt
partA_checking_summary.txt
partA_chk_Set_A_L_rows.txt
partA_chk_Set_B20_L_rows.txt
partA_chk_Set_B20_suite_rows.txt
partA_chk_Set_C_L_rows.txt
partA_chk_Set_C_suite_rows.txt
partA_chk_Set_n20_L_rows.txt
partA_CPA_stderr_raw.txt
partA_CPU_stderr_raw.txt
partB_B1_clock_blocks_raw.txt
partB_B2_perf_deltas_raw.txt
partB_B3_B4_tables_raw.txt
partB_CO1_see_ge.patch.txt
partB_CO2_apply_pair_and_evaluate.patch.txt
partB_purity_and_objdump.txt
prediction_job37.txt
REPORT_carbon2_job37.md
run_partA_checking.py
run_partB.py
run_step0.py
stamps.txt
step0_raw.txt
```
