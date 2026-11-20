# Job 33 Report (`carbon2`): Self-Play Game Loop Inside Plain `r15d` (`selfgame` & `sgstate`)

## 1. Step 0 & Builds (`step0_raw.txt`, `builds.txt`, `coverage_and_patch_stats.txt`)

- **Patch (`forge-combo29/carbon2/job33/selfgame_r15d.patch.txt`):**
  - **`sha256`:** `e9559864a268cab2a0c0a7fec2f4e4c8a515e031089f08d7181f868b6edd75fd`
  - **Files touched (`3`):** `include/forge/board.hpp`, `src/board.cpp`, `src/uci.cpp`
  - **Diffstat:** **`+384` lines added, `0` lines removed** (applied to plain `r15d` with `patch -p1 --fuzz=0`).
- **Executables (`builds.txt`):**

| Build | Path (`len`) | Executable `sha256` | `profdata` `sha256` / Flags |
|---|---|---|---|
| `r15d_base` (reused Job 31 `D`) | `/tmp/carbon2_job11/bld_sp_r15d_1/forge` (`38`) | `31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03` | `7ec91d0bbf8dc50ba53817a4eea858e242403ded7096ba7bf41a96eba834c77f` (SP-PGO ThinLTO `-O3 -march=sapphirerapids`) |
| `sgr15d_sp_pgo` (`r15d` + patch) | `/tmp/carbon2_job33/bld_sp_sgr15d/forge` (`38`) | `a995c15b37d6423ce50881c95a48e039dc3be46049992475f8fc407d781318ea` | `e97d6647ac504be755ff4d14a6be055c450f715760b0a3b219fd83d820b2ccdf` (SP-PGO ThinLTO `-O3 -march=sapphirerapids`) |
| `sgr15d_checking` (`r15d` + patch) | `/tmp/carbon2_job33/bld_asan_sgr15d/forge` (`40`) | `b0c64192aaed9aa2234a7f90904b65d480176d45f899a5aee384c1b679f740cb` | `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS` |
| `sgr15d_control_CS_oob` | `/tmp/carbon2_job33/bld_asan_cs_oob/forge` (`40`) | `487f31ddf3b50cb3bf1ad66a4a637ac4bbdfd13f772b4f464d164a1c0b290895` | Checking flags + planted `records[records.size()].ply` read |

- **Step 0 (`r15d_base`, each in a fresh process, `step0_raw.txt`):**
  - No option: `bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609` (**PASS**)
  - `PC20` (built-in evaluation, no net): `bench 11 = 278024`, `bench 13 = 587276` (**PASS**)
  - `PC20 + net768`: `bench 11 = 882074`, `bench 13 = 4275906` (**PASS**)

---

## 2. Part A — Reference Driver (`Ref`) vs Known Answers (`KA`) (`partA_KA_summary.txt`, `partA_Ref_{A,B,C}_rows.txt`)

- **Runtime & Library Versions:** `Python 3.12.3`, `python-chess` (`chess`) `1.11.2`.
- **Comparison of `Ref` (`ref_driver.py` on `r15d_base`) against `KA`:**

| Set (`seed`, attempts) | Fin / Thrown | Records | Moves (fin) | Searches | Final Nodes | W / D / B | `KA` Full `sha256` | `Ref` Full `sha256` | `KA` `1..10` `sha256` | `Ref` `1..10` `sha256` | Result |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| **A** (`carbon2-job33-a`, `200`) | `200 / 0` | `26,741` | `28,298` | `26,867` | `107,124,743` | `88 / 74 / 38` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` | `a61127c24d896515dd9594ff759a3dc87b6a0506ab36f1b915ac912c0a7dacf6` | `a61127c24d896515dd9594ff759a3dc87b6a0506ab36f1b915ac912c0a7dacf6` | **EXACT MATCH** |
| **B** (`carbon2-job33-b`, `100`, `N=50`) | `41 / 59` | `3,857` | `4,183` | `5,554` | `509,980` | `20 / 5 / 16` | `f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c` | `f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c` | `aa4b3b00a749f6bee067450ef05e7130b9e097c5d6c7daf62faa17e172657be1` | `aa4b3b00a749f6bee067450ef05e7130b9e097c5d6c7daf62faa17e172657be1` | **EXACT MATCH** |
| **C** (`carbon2-job33-c`, `100`, tight) | `100 / 0` | `2,904` | `3,661` | `2,960` | `1,433,776` | `38 / 44 / 18` | `4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf` | `4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf` | `b18af256d7a872200f6c095296502093849f825fdb8adbaa9d6f3c7c51e17510` | `b18af256d7a872200f6c095296502093849f825fdb8adbaa9d6f3c7c51e17510` | **EXACT MATCH** |

---

## 3. Part B — `KB0`, `KB1` + `CR`, Prediction Graded, `KB2`, `KB3`, and `CL`

### 3.1 `KB0` (`partB_KB0_raw.txt`)
- On `sgr15d_sp_pgo`, all `7` Step 0 numbers matched (`312866 / 862329 / 4865609`, `278024 / 587276`, `882074 / 4275906`), and the 60-game Job 20 `PC20 + net768` run gave `searches = 7670`, `nodes = 25641316`, `trace = ee465caeff9c0fcf` (**PASS**).

### 3.2 `KB1` & Control `CR` (`kb1_check.py`, `partB_KB1_CR_raw.txt`)
- **Positions tested:** **`500,060`** (`290,366` from `startpos` across `1,403` seeded random sequences + `209,694` across `1,402` seeded random sequences from `28` distinct 3-to-6-piece root FENs; seed `carbon2-job33-kb1`).
- **Differences vs `python-chess 1.11.2` (`legal`, `is_check`, `is_insufficient_material`, `halfmove_clock`, `is_repetition(3)`, `fen()`):** **`0` differences** (**PASS**).
- **Seven required class counts (`partB_KB1_CR_raw.txt`):**
  1. `material == 1`: **`112,021`** (required `>= 200`) — **PASS**
  2. `rep3 == 1`: **`260`** (required `>= 200`) — **PASS**
  3. `clock >= 100`: **`21,996`** (required `>= 20`) — **PASS**
  4. `mates` (`legal == 0, check == 1`): **`238`** (required `>= 50`) — **PASS**
  5. `stalemates` (`legal == 0, check == 0`): **`84`** (required `>= 50`) — **PASS**
  6. `en passant square in FEN`: **`726`** (required `>= 100`) — **PASS**
  7. `pawn just moved two squares and FEN shows "-"`: **`8,762`** (required `>= 100`) — **PASS**
- **Control `CR` (both fired):**
  - Against `board.fen(en_passant="fen")`: **`8,762` differences** (first witness: `seq=1 ply=1`, `1. f4`, `sg_fen` has `"-"` vs raw `"f3"`).
  - Against `board.is_repetition(2)`: **`5,870` differences** (first witness: `seq=4 ply=23`, `sg_rep3=0` vs `is_repetition(2)=1`).

### 3.3 `KB2`, `KB3`, and Control `CL` (`loop_driver.py`, `partB_KB2_KB3_CL_summary.txt`, `partB_Loop_{A,B,C,n}_rows.txt`, `partB_Ref_n_rows.txt`)
- **`KB2` (Sets `A`, `B`, `C` on `Loop` vs `Ref`):** **PASSED ON FIRST TRY, BYTE-FOR-BYTE IDENTICAL** (`2,528,478` bytes on `A`, `375,505` bytes on `B`, `305,612` bytes on `C`; all three full and `1..10` `sha256`s identical to `Ref`/`KA`; `0` per-game search/node/record/reason diffs; on `B`, the exact same `59` attempts were thrown away at the exact same ply).
- **`KB3` (Set `n`, `seed="carbon2-job33-n"`, `100` attempts, `PC20 + net768`, PC settings):** **PASSED, BYTE-FOR-BYTE IDENTICAL**:
  - Both `Ref` and `Loop`: `100` finished, `0` thrown away, `13,736` records (`1,265,744` bytes), `14,519` moves, `13,801` searches, `59,241,899` final nodes, `39 / 35 / 26` W/D/B, `0` per-attempt diffs.
  - `full_sha256`: `2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204` (`Ref` == `Loop`).
  - `first10_sha256`: `1c1f4a183ffb62754bf640ff26c56b82d5a40fb4b9a5debbc67a10cb74b626f6` (`Ref` == `Loop`).
- **Control `CL` (`Loop` with `drawcount 7` on Set `A`):** **FIRED** (`full_sha256 = 60a2b77e925e36ad661e0dba4b13350e8d416a3edc2560b7d0c1097c60f1c1bb` vs `Ref`'s `d5b52710...`; `26,431` vs `26,741` records; `88/76/36` vs `88/74/38` W/D/B).
  - **First game that differs:** **Attempt `4`** (`Ref` `C=8`: `80` records, result `0`, `87` moves, `80` searches, `294,734` nodes, `drawadj`, `sha256 = 9921cbbf83627be3...`; `Loop` `C=7`: `79` records, result `0`, `86` moves, `79` searches, `292,641` nodes, `drawadj`, `sha256 = 8a1c032ebdf95223...`).

### 3.4 Prediction Graded (`prediction_job33.txt`, committed alone in `909228a8e` before `KB2`)

| Item | Pre-Committed Prediction (`prediction_job33.txt`) | Observed (`KB2` & Part D) | Grade |
|---|---|---|---|
| (1) Set `A` equal at first try | `yes` | `yes` (`2,528,478` bytes equal on first run, `0` diffs) | **HIT** |
| (2) `Loop / Ref` wall per game on `A` (1-CPU pinned) | `[0.84, 0.93]` | Part D 6-block pooled **`0.9021`** (`median = 0.9024`, blocks `[0.8971, 0.9069]`); 3-pair `0.9270` | **HIT** |
| (3a) Driver CPU share in `Ref` | `[0.055, 0.085]` (`5.5%–8.5%`) | Part D 1-pair **`0.06752`** (`6.75%`, proc `7.08%`); Part A `6.79%` (3-pair CPU-0 shared: `5.19%`) | **HIT** |
| (3b) Driver CPU share in `Loop` | `[0.002, 0.012]` (`0.2%–1.2%`) | Part D 1-pair **`0.00267`** (`0.27%`, proc `0.66%`); 3-pair **`0.00259`** (`0.26%`) | **HIT** |

---

## 4. Part C — Checking Builds & Control `CS` (`partC_checking_CS_raw.txt`)

- **Thread architecture note:** `run_selfgame` runs synchronously on `uci_loop`'s command-reading thread after `stop_search()` has parked the persistent `worker` thread in `work_cv.wait(...)`. Because the loop does not run on another thread than the one reading commands, the TSan branch is not triggered.
- **Run 1 (`sgr15d_checking` on Set `C`, `100` attempts):** `full_sha256 = 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf` (exact match to plain build), `2,904` records, `2,960` searches, `1,433,776` nodes, **`0` sanitizer or assertion reports** (`stderr` empty, exit `0`).
- **Run 2 (`sgr15d_checking` on Set `B` attempts `1..20`, `N=50`, `9` finished + `11` `R4` process restarts with leak check on each exit):** `full_sha256 = 31f43fb43945e0ecf5c5867a287eaa19aae8bb238646e30043020d5271c5a6bf` (exact match to plain build `31f43fb43945e0ec...`), `919` records, `1,198` searches, **`0` sanitizer or assertion reports** (`stderr` empty, exit `0`).
- **Control `CS` (`sgr15d_control_CS_oob`, reading `records[records.size()].ply`):** **FIRED** (`returncode = -6`, `SIGABRT`):
  `/usr/include/c++/13/bits/stl_vector.h:1128: ... std::vector<SgRecord>::operator[](size_type) ...: Assertion '__n < this->size()' failed.`

---

## 5. Part D — For the Record: Paired ABBA Timing on Set `A` Attempts `1..60` (`partD_bench.py`, `partD_timing_raw.txt`)

All legs verified `sha256 = 5b13a801dcc80b0545f13c66eba3353c219ef73555c4a1e5be7d01bd284b8dfe` (`8,467` records, `8,505` searches, `33,810,814` nodes per 60-game leg). `driver_cpu` = `RUSAGE_SELF` (`ru_utime + ru_stime`) of the fresh per-leg Python process around the 60-game run (`proc` in parentheses includes Python startup/import).

| Regime | Mode | Wall / Game (`ms`) | Driver CPU / Game (`ms`) | Engine CPU / Game (`ms`) | Driver CPU Share `drv / (drv + eng)` | Pooled Wall `Loop / Ref` (`Ref / Loop`) | Block `Loop / Ref` Ratios |
|---|---|---:|---:|---:|---:|---|---|
| **1-Pair Pinned** (`6` blocks = `12` legs = `720` games/mode; drv CPU `0`, eng CPU `3`) | `Ref` | `266.329` | `17.992` (`proc 18.936`) | `248.479` | **`6.75%`** (`0.06752`, `proc 7.08%`) | **`0.9021`** (`1.1085x`) | `0.9063, 0.9069, 0.9066, 0.8976, 0.8971, 0.8986` (`median = 0.9024`) |
| **1-Pair Pinned** (`6` blocks = `12` legs = `720` games/mode; drv CPU `0`, eng CPU `3`) | `Loop` | `240.268` | `0.641` (`proc 1.587`) | `239.328` | **`0.27%`** (`0.00267`, `proc 0.66%`) | — | — |
| **`nproc - 1 = 3` Pairs Concurrent** (`2` blocks = `4` batches $\times 3$ = `720` games/mode; 3 drvs CPU `0`, 3 engs CPUs `1..3`) | `Ref` | `87.327` eff (`257.696` pair) | `13.560` (`proc 14.496`) | `247.798` | **`5.19%`** (`0.05188`) | **`0.9270`** batch (`1.0787x`; pair `0.9292`) | `0.9268, 0.9272` |
| **`nproc - 1 = 3` Pairs Concurrent** (`2` blocks = `4` batches $\times 3$ = `720` games/mode; 3 drvs CPU `0`, 3 engs CPUs `1..3`) | `Loop` | `80.952` eff (`239.445` pair) | `0.619` (`proc 1.555`) | `238.515` | **`0.26%`** (`0.00259`) | — | — |

---

## 6. How the Loop Is Built In & `kH` Compatibility

1. **Thread model:** `selfgame` and `sgstate` run synchronously on `uci_loop`'s command-reading thread (`src/uci.cpp`) immediately after calling `stop_search()`, while the persistent `worker` thread waits idle on `work_cv`. No shared-state contention occurs during `selfgame`, and returning after the single `std::cout.write` immediately resumes `std::getline(in, line)` so any `quit` waiting in the pipe is obeyed at once.
2. **Starting each search identically to `Ref`:** Each ply constructs a fresh `forge::SearchLimits` with `limits.nodes = cfg.soft_nodes; limits.nodes_specified = true; limits.soft_nodes = true; limits.move_overhead_ms = move_overhead_ms; limits.multipv = multipv;`, calls `searcher.reset_stop();`, and invokes `searcher.search(board, limits, /*emit_info=*/false, forge::Searcher::TTAccess::Exclusive)` directly on `uci_loop`'s `searcher` and `board`. Every `emit_info` branch in `src/search.cpp` was audited to confirm it performs pure output formatting (`shared_.tt.hashfull()` is `const`) with zero side effects on TT, histories, RNG, node counts, or scores; `Searcher` carries the exact same TT generation and history state across plies as `Ref`'s `go softnodes N` sequence.
3. **Exact position, score, and rule alignment with `Ref`:**
   - **Position & `D2` (`rep3`):** `Loop` sends `position startpos moves <8 random moves>` before `selfgame`, populating `board`'s `key_history_` with all `9` keys (`ply = board.history_size() - 1 == 8`). Each `R2(i)` move applies `board.parse_uci(best_uci)` + `board.make_move(*parsed_move, undo)` directly to `board`, preserving `key_history_` identically to `Ref`'s incremental `apply_position`. Setting `pos_cache.valid = false;` prevents any later `position` command from trusting stale cached moves.
   - **`noscore` (`R4`) and `matescore` (`R2(e)`):** Under `go softnodes N` (`multipv = 1`), `Worker::search` emits an `info ... score ...` line iff at least iteration `depth = 1` completed (`info.depth >= 1`); when depth 1 aborts on the `4*N` hard node cap, `info.depth == 0` triggers `sgerror noscore`. When `forge::is_mate_score(info.score)` holds, `distance = MateValue - |info.score|` and `mate_x = +/-((distance + 1) / 2)` match `emit`'s `put_score` conversion exactly.
   - **`D3` (`Board::sg_fen()`) & `D1` (`Board::sg_insufficient_material()`):** `Board::fen()` in `r15d` prints `ep_square_` unconditionally whenever `ep_square_ >= 0`; `Board::sg_fen()` gates the en passant square on `has_legal_en_passant_capture()` per `D3`. `Board::sg_insufficient_material()` implements `D1`'s per-side predicate without altering `Board::is_insufficient_material()` inside search.
4. **Does `job33/selfgame_r15d.patch.txt` apply to `kH` unchanged?** **Yes** — verified with `patch -d /tmp/carbon2_job30/src_kH_clean -p1 --fuzz=0 --dry-run` (`partB_KB0_raw.txt`).

---

## WHAT THIS CANNOT SEE

Windows pipes and the PC's Python; the PC's net; the PC's three after-game rules; a book; more than one thread; a rule case that none of the runs met (across all `500` attempts / `51,133` positions of `A`, `B`, `C` and `n` in `coverage_and_patch_stats.txt`: among `KB1`'s seven classes, **`mates` (`0`)** and **`stalemates` (`0`)** were never met in `A, B, C, n`—while `material == 1` (`4`), `rep3 == 1` (`19`), `clock >= 100` (`16`), `ep_in_fen` (`104`), and `double_push_dash` (`2,647`) were all met; among `sgend`'s seven end reasons, **`mate` (`0`)** and **`stalemate` (`0`)** were never seen in `A, B, C, n`—while `evallimit` (`168`), `matescore` (`115`), `drawadj` (`105`), `rule` (`39`), and `plylimit` (`14`), plus `59` `sgerror noscore` restarts, were all seen).

---

### Facts
1. `Ref` (`ref_driver.py`, `Python 3.12.3`, `python-chess 1.11.2`) matched every count and all six `sha256` digests of `KA` across Sets `A`, `B`, and `C` on plain `r15d`.
2. `selfgame_r15d.patch.txt` (`+384 / -0` across `board.hpp`, `board.cpp`, `uci.cpp`) preserved all seven Step 0 pins and Job 20 (`7670 / 25641316 / ee465caeff9c0fcf`) in `KB0`, and applies with `patch -p1 --fuzz=0` to both plain `r15d` and `kH` unchanged.
3. `sgstate` matched `python-chess 1.11.2` with `0` differences across `500,060` positions in `KB1` with all seven class thresholds exceeded, and both `CR` controls fired (`8,762` raw-EP FEN differences; `5,870` twofold-vs-threefold differences).
4. `Loop` (`loop_driver.py` + `selfgame`) matched `Ref` byte-for-byte on the first try across Sets `A`, `B`, `C` (`KB2`) and `n` (`KB3`), passed `ASan+UBSan+_GLIBCXX_ASSERTIONS` on Set `C` and Set `B[1..20]` with `0` reports (`CS` fired with `SIGABRT`), and reduced 1-pair per-game wall time on Set `A[1..60]` to `0.9021` of `Ref` (`0.9270` at `3` concurrent pairs) while cutting Python driver CPU share from `6.75%` (`17.99 ms/game`) to `0.27%` (`0.64 ms/game`).

### Suspicions
1. On Windows (where pipe round-trips and CPython process/stdio overhead per ply are typically larger than on Linux pipes, and where `7–16` concurrent self-play workers compete for CPU cores), eliminating ~`134` per-game Python `chess` pushes, FEN serializations, and `info`/`bestmove` pipe round-trips should yield at least as large a driver-CPU reduction and likely a larger wall reduction under multi-worker load than on Linux.
2. Notice in Part D (`1`-pair) that `engine_cpu` itself also dropped from `248.48 ms/game` (`Ref`) to `239.33 ms/game` (`Loop`, `-9.15 ms/game` = `-3.68%`), because plain `r15d` in `Ref` reparses `position startpos moves ...` via `std::istringstream`, wakes the worker condvar on every ply, and formats/flushes ~`1,350` `info` lines per game. On `kH` / `kK` (which already includes Patch 14's `string_view` UCI parser and stronger v3 NNUE eval cost per search), the engine-side slice of that saving will be smaller as a fraction of search time, while the Python driver saving (`~17.3 ms/game`) remains fixed per ply.

### What I Did Not Do
- Did not build or run `-fsanitize=thread` because `run_selfgame` executes synchronously on the command-reading thread while `worker` is idle in `work_cv.wait(...)`.
- Did not commit raw multi-megabyte `.txt` game record dumps (`ref_set_A.txt` is `2.53 MB`; per-attempt row tables and whole-text + `1..10` `sha256` digests are committed instead).
- Did not touch engine source in `/agent/repos/dwqww` or edit any already-committed raw file.

### What I Am Not Sure About
- How much per-game wall time `Loop / Ref` saves on the Windows PC with its production net and Windows pipe buffering (Linux pipes and `net768` / built-in v1 NNUE cannot measure Windows kernel pipe latency directly).
- Whether `MultiPV > 1` will ever be used with `selfgame` (`PC20` uses `MultiPV = 1`; under `MultiPV > 1`, `Worker::search` emits `MultiPV` lines per depth ending with the lowest-ranked line `lines.back()`, whereas `result.score` holds `lines.front().score`).

### Model Name
`Gemini 4 Carbon`

---

## 7. Verbatim Output of `git status --short && ls -R forge-combo29/carbon2/job33` Before Report Commit

```text
?? forge-combo29/carbon2/job33/REPORT_carbon2_job33.md
forge-combo29/carbon2/job33:
builds.txt
coverage_and_patch_stats.txt
kb1_check.py
loop_driver.py
partA_KA_summary.txt
partA_Ref_A_rows.txt
partA_Ref_B_rows.txt
partA_Ref_C_rows.txt
partB_KB0_raw.txt
partB_KB1_CR_raw.txt
partB_KB2_KB3_CL_summary.txt
partB_Loop_A_rows.txt
partB_Loop_B_rows.txt
partB_Loop_C_rows.txt
partB_Loop_n_rows.txt
partB_Ref_n_rows.txt
partC_checking_CS_raw.txt
partD_bench.py
partD_timing_raw.txt
prediction_job33.txt
ref_driver.py
REPORT_carbon2_job33.md
selfgame_r15d.patch.txt
stamps.txt
step0_raw.txt
```
