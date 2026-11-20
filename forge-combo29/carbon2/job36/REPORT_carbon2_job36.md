# `REPORT_carbon2_job36.md` — Job 36: The Game Loop `v3` for the PC's Client & Closing the Stack Map's `none` Rows

**Reported First (per `=== STOPS ===`: *"A known answer or a control failing is reported first and stops nothing after it."*):**
- **Part A `CONTROL CK` (`drawply 20` on `n`'s first 30 attempts, `partA_KB9_CS_CK_raw.txt`):** Changing `drawply` alone from `L` (`80 -> 20`) changed **record text on `0` of `30` attempts** of `n[1..30]` (`FAIL (6 != 7)` on `n[1..30]` record text alone; the other 6 keys changed record text on `30, 29, 27, 30, 7, 19` of `30`). However, `drawply 20` **DID act and change `sgend` on `2` of `30` attempts** (`attempts 4` and `22` -> `PASS (7 == 7)` keys changing record text or `sgend` on `n[1..30]`): on both `attempt 4` and `attempt 22`, `drawply 20` adjudicated at ply `54` (`reason drawadj plies 54 run 8`), whereas `L` (`drawply 80`) played one move further into 3-fold repetition at ply `55` (`reason rule plies 55 run 0`). Because both runs write records for `plies 8..54` (`47` records) with `result 0`, their record texts are byte-identical (`sha256` equal) even though `drawply 20` terminated the game earlier. Diagnostic checks recorded in `partA_KB9_CS_CK_raw.txt` confirm `drawply` changes record text on **`5` of `100`** attempts of `n[1..100]` (`[33, 39, 58, 60, 97]`, `PASS (5 >= 1)`) under `drawply 20`, and on **`5` of `30`** attempts of `n[1..30]` (`[6, 15, 20, 23, 29]`, `PASS (5 >= 1)`) under `drawply 200`. Every known answer (`Step 0`, `KB0`, `KA3`, `KF`, `KB9`, `Part C`) and every other control (`CS`, `CP`, and `6/7` keys of `CK` on `n[1..30]` record text) passed (`CS: PASS (6 == 6)`, `CP: PASS (200 == 200)` & `PASS (1000 == 1000)`).

---

## First Lines (Summary in Exact Spec Order)

### (1) Step 0 (`step0_raw.txt`, `builds.txt` — 7 Fresh Processes per Exe; Reused Recorded SP-PGO Exes Verified by `sha256`)

- **`plain_r15d`** (reused `/tmp/carbon2_job11/bld_sp_r15d_1/forge`, `len=38`, recorded in `job31/builds.txt`, `job33/builds.txt`, `job35/builds.txt`):
  - `exe_sha256 vs recorded`: `PASS (31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03 == 31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03)`
  - `profdata_sha256 vs recorded`: `PASS (7ec91d0bbf8dc50ba53817a4eea858e242403ded7096ba7bf41a96eba834c77f == 7ec91d0bbf8dc50ba53817a4eea858e242403ded7096ba7bf41a96eba834c77f)`
  - no-option `bench 11`: `PASS (312866 == 312866)` | `bench 13`: `PASS (862329 == 862329)` | `perft 5`: `PASS (4865609 == 4865609)`
  - `PC20` `bench 11`: `PASS (278024 == 278024)` | `bench 13`: `PASS (587276 == 587276)`
  - `PC20 + net768` `bench 11`: `PASS (882074 == 882074)` | `bench 13`: `PASS (4275906 == 4275906)`
- **`r15d_v2`** (reused `/tmp/carbon2_job35/bld_sp_sgr15v/forge`, `len=38`, recorded in `job35/builds.txt`):
  - `exe_sha256 vs recorded`: `PASS (e9abc795b8b281ccc5453537a96fd11a5bc6e44df288007cfe0bbfd087bf1785 == e9abc795b8b281ccc5453537a96fd11a5bc6e44df288007cfe0bbfd087bf1785)`
  - `profdata_sha256 vs recorded`: `PASS (a8783ccbb2dfae9224e4a0073de2a65f3a39deb5fe566bf9635c5249f5192c52 == a8783ccbb2dfae9224e4a0073de2a65f3a39deb5fe566bf9635c5249f5192c52)`
  - no-option `bench 11`: `PASS (312866 == 312866)` | `bench 13`: `PASS (862329 == 862329)` | `perft 5`: `PASS (4865609 == 4865609)`
  - `PC20` `bench 11`: `PASS (278024 == 278024)` | `bench 13`: `PASS (587276 == 587276)`
  - `PC20 + net768` `bench 11`: `PASS (882074 == 882074)` | `bench 13`: `PASS (4275906 == 4275906)`
- **`kK`** (reused `/tmp/carbon2_job32/bld_sp_stkK_1/forge`, `len=38`, recorded in `job32/builds.txt` & `job34/builds.txt`):
  - `exe_sha256 vs recorded`: `PASS (985b8dbd2dfeae587b8aeb29f1a17c2054e6afa89e30a7223258d582e6995108 == 985b8dbd2dfeae587b8aeb29f1a17c2054e6afa89e30a7223258d582e6995108)`
  - `profdata_sha256 vs recorded`: `PASS (abc3c4696963759491026948e04c81674b863bf066adde414d2a60a8b8517985 == abc3c4696963759491026948e04c81674b863bf066adde414d2a60a8b8517985)`
  - no-option `bench 11`: `PASS (312866 == 312866)` | `bench 13`: `PASS (862329 == 862329)` | `perft 5`: `PASS (4865609 == 4865609)`
  - `PC20` `bench 11`: `PASS (278024 == 278024)` | `bench 13`: `PASS (587276 == 587276)`
  - `PC20 + net768` `bench 11`: `PASS (882074 == 882074)` | `bench 13`: `PASS (4275906 == 4275906)`
- **Step 0 Overall:** `PASS (3 == 3)`

---

### (2) Prediction Graded (`prediction_job36.txt`, committed ALONE in `a3969f91f` at `10:29:14 AM UTC` before Part A's first comparison at `10:37:28 AM UTC`, never edited)

- **Overall Score: `3 / 4` HIT**
  1. **`(1)` `v3` leaves every `sg` line, and every `sgend` field but the new one, as `v2` wrote them on `A, B, C` and `n`:** Predicted **`yes`** -> **HIT** (`sg` equal: `26741 == 26741`, `3857 == 3857`, `2904 == 2904`, `13736 == 13736`; `sgend` equal without `fen`: `200 == 200`, `41 == 41`, `100 == 100`, `100 == 100`).
  2. **`(2)` On every finished game of `A, B, C` and `n`, `fen` equals `python-chess`'s board after the moves:** Predicted **`yes`** -> **HIT** (`441 == 441` exact match to `python-chess 1.11.2`'s `board.fen()`, `0 == 0` differing).
  3. **`(3)` Part B: of `200` searches of `go movetime 30`, how many take hunk 75's branch:** Predicted **`[4, 24]`** -> **MISS** (observed **`1` of `200`** on `kK_cp` at `go movetime 30`, and `5` of `1,000` at `go movetime 30`; with `PC20` + built-in `v1`, `kK` reaches `depth 11..14` in `20 ms` where root move #1 already matches the previous completed PV almost every time, triggering the `< 10` escalation rule where `1,000` searches at `go movetime 10` took the branch **`12`** times).
  4. **`(4)` The planted break of `CONTROL CP` fails the check at least once:** Predicted **`yes`** -> **HIT** (`kK_plant` failed **`18` of `200`** at `go movetime 30`, and **`86` of `1,000`** at `go movetime 10`).

---

### (3) Part A (`selfgame_r15d_v3.patch.txt`, `v2_to_v3.diff.txt`, `partA_KB0_raw.txt`, `partA_KA3_KF_summary.txt`, `partA_KB9_CS_CK_raw.txt`, `partA_v2_{A,B,C,n}_rows.txt`, `partA_v3_{A,B,C,n}_rows.txt`)

- **Patches (`selfgame_r15d_v3.patch.txt` `sha256 = 2ab0000d6357f1780fd3140bf3c884c894d5d47020522dfe1887e0e18600e39d`, `457` lines; `v2_to_v3.diff.txt` `sha256 = 1246b5b0a1eada29f4c9ba123f4d6809a13835a5baaa5c2bd0910a32d82e1109`, `189` lines):**
  - **A1 (`sgend ... nodes <n> fen <FEN> moves ...`):** Inserts `" fen " + board.sg_fen()` immediately after `nodes <total_nodes>` and before `" moves"` in `run_selfgame` (`src/uci.cpp`); `sgerror` lines unchanged.
  - **A2 (strict `selfgame` line):** `parse_selfgame_config(line, sg_cfg, bad_word)` validates all tokens after `selfgame` in `<key> <value>` pairs before any search or `NNUE v3` check: `<key>` must be one of the 7 keys (`softnodes`, `evallimit`, `maxply`, `writeminply`, `drawply`, `drawscore`, `drawcount`) not seen earlier in the line, and `<value>` must be a non-empty ASCII digit string (`0..9` only, whole number `>= 0` fitting in `uint64_t` for `softnodes` / `int` for the other 6 keys, with no sign or trailing characters). On the first offending word (or `<key>` if no `<value>` follows), prints solely `sgerror badline <word>`, runs zero searches, emits no `sg` or `sgend` line, and stays alive (`isready` -> `readyok`). Bare `selfgame` with no words uses defaults.

- **`KB0` on `r15d_v3` (`/tmp/carbon2_job36/bld_sp_sgr15v/forge`, `len=38`, `exe_sha256 = bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810`, `profdata_sha256 = e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc`, `partA_KB0_raw.txt`):**
  - no-option `bench 11`: `PASS (312866 == 312866)` | `bench 13`: `PASS (862329 == 862329)` | `perft 5`: `PASS (4865609 == 4865609)`
  - `PC20` `bench 11`: `PASS (278024 == 278024)` | `bench 13`: `PASS (587276 == 587276)`
  - `PC20 + net768` `bench 11`: `PASS (882074 == 882074)` | `bench 13`: `PASS (4275906 == 4275906)`
  - Job 20 signature: searches `PASS (7670 == 7670)` | nodes `PASS (25641316 == 25641316)` | trace `PASS (ee465caeff9c0fcf == ee465caeff9c0fcf)`

- **`KA3` (`v3` vs `v2` Side by Side Across Sets `A`, `B`, `C`, and `n`, `partA_KA3_KF_summary.txt`):**

| Set | `v2` Record `sha256` | `v3` Record `sha256` | Record `sha256` (`v3 == v2`) | `sg` Lines Equal (`v3` of `v2`) | `sgend` Equal w/o `fen` (`v3` of `v2`) | `sgerror` Equal (`v3` of `v2`) | Searches (`v3 == v2`) | Nodes (`v3 == v2`) |
|---|---|---|---|---|---|---|---|---|
| **A** (`200` fin) | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` | `PASS (d5b52710... == d5b52710...)` | `PASS (26741 == 26741)` (`26741 of 26741`) | `PASS (200 == 200)` (`200 of 200`) | `PASS (0 == 0)` | `PASS (26867 == 26867)` | `PASS (107124743 == 107124743)` |
| **B** (`41` fin, `59` thr) | `f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c` | `f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c` | `PASS (f19e8b1f... == f19e8b1f...)` | `PASS (3857 == 3857)` (`3857 of 3857`) | `PASS (41 == 41)` (`41 of 41`) | `PASS (59 == 59)` | `PASS (5554 == 5554)` | `PASS (509980 == 509980)` |
| **C** (`100` fin) | `4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf` | `4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf` | `PASS (4d65540c... == 4d65540c...)` | `PASS (2904 == 2904)` (`2904 of 2904`) | `PASS (100 == 100)` (`100 of 100`) | `PASS (0 == 0)` | `PASS (2960 == 2960)` | `PASS (1433776 == 1433776)` |
| **n** (`100` fin) | `2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204` | `2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204` | `PASS (2ed18a2a... == 2ed18a2a...)` | `PASS (13736 == 13736)` (`13736 of 13736`) | `PASS (100 == 100)` (`100 of 100`) | `PASS (0 == 0)` | `PASS (13801 == 13801)` | `PASS (59241899 == 59241899)` |

- **`KF` (`sgend` `fen` vs `python-chess 1.11.2`, `partA_KA3_KF_summary.txt`):**
  - Finished games compared: **`441`** (`Set A: 200`, `Set B: 41`, `Set C: 100`, `Set n: 100`).
  - Equal to `python-chess 1.11.2` default `board.fen()`: **`441`** (`PASS (441 == 441)` — `Set A: PASS (200 == 200)`, `Set B: PASS (41 == 41)`, `Set C: PASS (100 == 100)`, `Set n: PASS (100 == 100)`).
  - Differing: **`0`** (`PASS (0 == 0)`).
  - **En-passant convention written by `Board::sg_fen()`:** **legal en passant** (`python-chess` default `board.fen()`, i.e. `en_passant="legal"`, which prints the en-passant target square iff a legal en-passant capture exists; across the `10` finished games in `A, B, C, n` that ended immediately after a non-capturable double pawn push — `A: 1, B: 1, C: 6, n: 2` — `board.fen()` matched `441/441` whereas `board.fen(en_passant="fen")` matched `431/441`).

- **`KB9` (`B1..B9` as printed on `r15d_v3`, `partA_KB9_CS_CK_raw.txt` — `PASS (9 == 9)`):**
  - `B1` (`EQUAL`): `sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 fen rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3 moves`
  - `B2` (`EQUAL`): `sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 fen 5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 2 10 moves`
  - `B3` (`EQUAL`): `sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5 moves`
  - `B4` (`EQUAL`): `sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5 moves`
  - `B5` (`EQUAL`): `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1 moves`
  - `B6` (`EQUAL`): `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80 moves`
  - `B7` (`EQUAL`): `sgend result 1 reason mate plies 0 run 0 searches 0 nodes 0 fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80 moves`
  - `B8` (`EQUAL`): `sgend result 0 reason stalemate plies 0 run 0 searches 0 nodes 0 fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1 moves`
  - `B9` (`EQUAL`, plain `r15d` ref `nodes = 1152 == 1152`): `sgend result 1 reason matescore plies 0 run 0 searches 1 nodes 1152 fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1 moves`

- **`CONTROL CS` (Strict `selfgame` Line, `partA_KB9_CS_CK_raw.txt` — `PASS (6 == 6)`):**
  - `S1` (`L` with `evallimt`): printed `sgerror badline evallimt`, then `readyok` (`PASS ('sgerror badline evallimt' == 'sgerror badline evallimt')`)
  - `S2` (`L` with `softnodes 2k`): printed `sgerror badline 2k`, then `readyok` (`PASS ('sgerror badline 2k' == 'sgerror badline 2k')`)
  - `S3` (`L` ending in `drawcount`): printed `sgerror badline drawcount`, then `readyok` (`PASS ('sgerror badline drawcount' == 'sgerror badline drawcount')`)
  - `S4` (`selfgame softnodes 2000 maxply 300 maxply 60`): printed `sgerror badline maxply`, then `readyok` (`PASS ('sgerror badline maxply' == 'sgerror badline maxply')`)
  - `S5` (`L` with `drawscore -5`): printed `sgerror badline -5`, then `readyok` (`PASS ('sgerror badline -5' == 'sgerror badline -5')`)
  - `S6` (`L` with `maxply 300x`): printed `sgerror badline 300x`, then `readyok` (`PASS ('sgerror badline 300x' == 'sgerror badline 300x')`)
  - `L` (`selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`) on `n` attempt 1 vs `v2`:
    - `PASS (b430054c2a3c8b56a0fc4f73565f9ac64f57b09f7c42360f9f20969a1ee362bb == b430054c2a3c8b56a0fc4f73565f9ac64f57b09f7c42360f9f20969a1ee362bb)` (`records: 109 == 109`, `searches: 110 == 110`, `nodes: 460588 == 460588`).

- **`CONTROL CK` (One Key Changed Alone from `L` on `n`'s First 30 Attempts, `partA_KB9_CS_CK_raw.txt`):**
  - Baseline `L` (`30` attempts): `records = 4535`, `searches = 4552`, `nodes = 19817880`, `sha256 = e184b1746334f9710f6f0ee494dd9cef37281788b7f17c030717d2f723acf15f`.
  - `softnodes 1000`: **`30` of `30`** record texts changed (`PASS (30 >= 1)`; `sgend` changed `30 of 30`; `records = 4212`, `nodes = 8899765`).
  - `evallimit 500`: **`29` of `30`** record texts changed (`PASS (29 >= 1)`; `sgend` changed `29 of 30`; `records = 1098`, `nodes = 4454646`).
  - `maxply 60`: **`27` of `30`** record texts changed (`PASS (27 >= 1)`; `sgend` changed `27 of 30`; `records = 1538`, `nodes = 6088920`).
  - `writeminply 12`: **`30` of `30`** record texts changed (`PASS (30 >= 1)`; `sgend` changed `0 of 30`; `records = 4415`, `nodes = 19817880`).
  - `drawply 20`: **`0` of `30`** record texts changed (`FAIL (6 != 7)` on `n[1..30]` record text alone; **`sgend` changed `2 of 30`** on `attempts [4, 22]` -> `PASS (7 == 7)` keys changing record text or `sgend` on `n[1..30]`; `drawply 20` on `n[1..100]` changed record text on **`5` of `100`** `[33, 39, 58, 60, 97]`, `PASS (5 >= 1)`; `drawply 200` on `n[1..30]` changed record text on **`5` of `30`** `[6, 15, 20, 23, 29]`, `PASS (5 >= 1)`).
  - `drawscore 100`: **`7` of `30`** record texts changed (`PASS (7 >= 1)`; `sgend` changed `7 of 30`; `records = 4079`, `nodes = 17780661`).
  - `drawcount 1`: **`19` of `30`** record texts changed (`PASS (19 >= 1)`; `sgend` changed `19 of 30`; `records = 2962`, `nodes = 12374622`).

---

### (4) Part B (`partB_settled_and_CP_summary.txt`, `partB_CP_counter_and_plant.patch.txt`, `partB_CP_{kK,plant,kF}_rows.txt`, `partB_CP_{kK,plant,kF}_1000_mt10_rows.txt`)

- **Seven Settled `none` Rows (Verified Directly Against `kK` Source `/tmp/carbon2_job32/src_kK` — `PASS (7 == 7)`):**
  - **46:** **AGREE** — inside `src/search.cpp:1516` (`#elif FORGE_SPD_NO_ZERO_MOVELISTS >= 2`) of `1333` (`#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2`), not compiled under PC defines (`2` and `1`).
  - **47:** **AGREE** — inside `src/search.cpp:1529` (`#else` of the `1333` chain), not compiled on the PC.
  - **74:** **AGREE** — inside `src/search.cpp:3601` (`#if FORGE_FIX_ABORT_PUBLISH`, default `0` at `src/search.cpp:78`), not compiled on the PC.
  - **40:** **AGREE** — `init_check_squares`'s `#else` (`src/search.cpp:1032`) is under `#if FORGE_SPD_KING_LINES` (`1024`, default `1` at `board.hpp:73`), `direct_check` (`1046`) has only the three callers `1525`, `1546`, `1594` (none compiled on the PC), and `restore_king_lines` (`src/board.cpp:1201`) restores `dst.check_squares[Queen] = src.chk_b | src.chk_r`.
  - **10:** **AGREE** — `make_valid` (`include/forge/nnue_v3.hpp:335`) has zero callers across `include/` and `src/` (never instantiated).
  - **15:** **AGREE** — `candidate.key_history_.reserve(2048)` (`src/board.cpp:364`) is capacity-only; `key_history_.data()` (`src/board.cpp:1849`) is inside `const` `Board::upcoming_repetition` (pushes nothing), and `key_history()` (`include/forge/board.hpp:284`) has zero callers.
  - **73:** **AGREE** — `root_effort_count_` is set at `src/search.cpp:3549` before `std::fill_n` at `3552`, and every read/write of `root_move_nodes_` (`2991`, `3049..3050`, `3779..3783`, `3803..3804`) is bounded by `root_effort_count_`.

- **`CONTROL CP` on Open Row `75` (`src/search.cpp:3650..3658`):**
  - **Position set:** first `200` non-terminal positions of `forge-combo29/carbon2/positions_250.txt` (lines `1..202`, skipping terminal checkmate lines `[88, 176]` which have `0` legal moves), `PC20` + built-in `v1` evaluation, `Hash 16`, `Threads 1`, `ucinewgame` + `isready` before each search.
  - **`go depth 10` Node Identity on First 20 Non-Terminal Positions:**
    - `kK_cp` vs `kK`: `PASS (321964 == 321964)`
    - `kF_cp` vs `kF`: `PASS (321964 == 321964)`
  - **Primary `200` Searches at `go movetime 30` (`partB_CP_{kK,plant,kF}_rows.txt`):**
    - **`kK_cp`:** `searches = 200`, `branch_taken = 1`, `check_passed = 200 of 200` (`PASS (200 == 200)`; `legal = 200/200`, `pv_match = 200/200`).
    - **`kK_plant` (`pv_stack_[4] -> pv_stack_[5]` in `3653..3655`):** `searches = 200`, `branch_taken = 18`, **`check_FAILED = 18 of 200`** (`PASS (18 >= 1)`; `check_passed = 182 of 200`, `legal = 182/200`, `pv_match = 200/200`).
      - **First failure in full (`kK_plant`, `200 / movetime 30`):**
        `idx=8 | fen=k1r2br1/1p2ppp1/3B1nnp/8/2P1P3/3PKNPB/P4P1P/5RR1 b - - 1 22 | abortpub=1 | bestmove='d6b4' (legal=False) | first_pv='d6b4' (pv_match=True) | last_pv_line='info depth 13 seldepth 22 score cp -290 nodes 43008 nps 2150400 hashfull 17 time 20 pv d6b4 e7e6 f1b1 c6a6 a2a3 a8b8 b1b3 f6d7 g1b1 f8b4 a3b4 g8c8'` (White's ply-1 reply `d6b4` published as Black's root `bestmove`!).
    - **`kF_cp` (for the record):** `searches = 200`, `branch_taken = 1`, `check_passed = 200 of 200` (`PASS (200 == 200)`).
  - **Escalation (`branch_taken = 1 < 10` in 200 at `movetime 30` -> ran `1,000` non-terminal searches of `positions_1000.txt` [lines `1..1006`, skipping checkmate lines `234, 480, 622, 624, 926, 949`] at `go movetime 10`, plus `200` at `movetime 10` and `1,000` at `movetime 30`):**
    - **`[1000 pos, movetime 10]` `kK_cp` (`partB_CP_kK_1000_mt10_rows.txt`):** `searches = 1000`, **`branch_taken = 12`** (`>= 10`), **`check_passed = 1000 of 1000`** (`PASS (1000 == 1000)`).
    - **`[1000 pos, movetime 10]` `kK_plant` (`partB_CP_plant_1000_mt10_rows.txt`):** `searches = 1000`, `branch_taken = 86`, **`check_FAILED = 86 of 1000`** (`PASS (86 >= 1)`; `check_passed = 914 of 1000`).
      - **First failure in full (`kK_plant`, `1000 / movetime 10`):**
        `idx=10 | fen=1rbqkb1r/1p2pppp/3p1nn1/2p5/1pP5/NQ1P1N2/P3PPPP/1RB1KBR1 b k - 1 10 | abortpub=1 | bestmove='e2e3' (legal=False) | first_pv='e2e3' (pv_match=True) | last_pv_line='info depth 7 seldepth 12 score cp 456 nodes 2048 nps 2048000 hashfull 1 time 1 pv e2e3 e7e5 f1e2 e5e4 d3e4 f6e4 f8c5'`
    - **`[1000 pos, movetime 10]` `kF_cp` (`partB_CP_kF_1000_mt10_rows.txt`):** `searches = 1000`, `branch_taken = 10`, `check_passed = 1000 of 1000` (`PASS (1000 == 1000)`).
    - *(Also recorded: `[200 pos, movetime 10]` `kK_cp` `branch_taken = 2`, `PASS (200 == 200)`, `kK_plant` failed `14 of 200`, `kF_cp` `branch_taken = 2`, `PASS (200 == 200)`; `[1000 pos, movetime 30]` `kK_cp` `branch_taken = 5`, `PASS (1000 == 1000)`, `kK_plant` failed `80 of 1000`, `kF_cp` `branch_taken = 5`, `PASS (1000 == 1000)`.)*

---

### (5) Part C (`v3` on `kF` — `partC_apply_and_step0_raw.txt`, `partC_kF_v3_summary.txt`, `partC_kF_v3_{A,B,C,n}_rows.txt`)

- **Apply `selfgame_r15d_v3.patch.txt` to `kF` with `patch -p1 --fuzz=0`:** **APPLIES: YES** (`PASS (0 == 0)`; `include/forge/board.hpp` clean, `src/board.cpp` offset `+1`, `src/uci.cpp` offsets `+83 / +84`, `0` failed hunks).
- **SP-PGO Build `kF_v3` (`/tmp/carbon2_job36/bld_sp_sgkFv3/forge`, `len=38`, `exe_sha256 = 7384755020391c6c4b49be2fba879ff6c151cc7d440c08ca7df9d85dfc3589f9`, `profdata_sha256 = dd8de4698eaec399beedd119111f680bd2c51e573bae96f967e5d5cb2f0f05d8`) — Step 0's Seven Numbers (Fresh Processes):**
  - no-option `bench 11`: `PASS (312866 == 312866)` | `bench 13`: `PASS (862329 == 862329)` | `perft 5`: `PASS (4865609 == 4865609)`
  - `PC20` `bench 11`: `PASS (278024 == 278024)` | `bench 13`: `PASS (587276 == 587276)`
  - `PC20 + net768` `bench 11`: `PASS (882074 == 882074)` | `bench 13`: `PASS (4275906 == 4275906)`
  - Job 20 signature: searches `PASS (7670 == 7670)` | nodes `PASS (25641316 == 25641316)` | trace `PASS (ee465caeff9c0fcf == ee465caeff9c0fcf)`
- **Known-Answer Comparison `kF + v3` vs `r15d + v3` Across `A, B, C, n`:**
  - **Set A:** `full_sha256` `PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)` | `sg` equal `PASS (26741 == 26741)` | `sgend` (incl. `fen`) equal `PASS (200 == 200)` | `fen == python-chess` `PASS (200 == 200)` | `searches` `PASS (26867 == 26867)` | `nodes` `PASS (107124743 == 107124743)`
  - **Set B:** `full_sha256` `PASS (f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c == f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c)` | `sg` equal `PASS (3857 == 3857)` | `sgend` (incl. `fen`) equal `PASS (41 == 41)` | `sgerror` equal `PASS (59 == 59)` | `fen == python-chess` `PASS (41 == 41)` | `searches` `PASS (5554 == 5554)` | `nodes` `PASS (509980 == 509980)`
  - **Set C:** `full_sha256` `PASS (4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf)` | `sg` equal `PASS (2904 == 2904)` | `sgend` (incl. `fen`) equal `PASS (100 == 100)` | `fen == python-chess` `PASS (100 == 100)` | `searches` `PASS (2960 == 2960)` | `nodes` `PASS (1433776 == 1433776)`
  - **Set n:** `full_sha256` `PASS (2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204 == 2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204)` | `sg` equal `PASS (13736 == 13736)` | `sgend` (incl. `fen`) equal `PASS (100 == 100)` | `fen == python-chess` `PASS (100 == 100)` | `searches` `PASS (13801 == 13801)` | `nodes` `PASS (59241899 == 59241899)`

---

## WHAT THIS CANNOT SEE

Windows pipes and the PC's Python; the PC's net; the PC's after-game rules; a book; more than one thread; how often
the clock cuts a search on the PC (Part B's counts are this machine's).

---

## Facts, Suspicions, What I Did Not Do, and What I Am Not Sure About

### Facts
1. **Job 35 Part A was already 100% completed and pushed before Job 36 started (`065d6fb52`):** No Part 0 backfill was needed; `v3` (`selfgame_r15d_v3.patch.txt`) was built cleanly on top of `job35/selfgame_r15d_v2.patch.txt`, and `v2_to_v3.diff.txt` isolates the exact delta (`src/uci.cpp` only, `189` lines).
2. **`Board::sg_fen()` writes exact `en_passant="legal"` FENs (`441 == 441` on `r15d_v3` and `kF_v3`, `9 == 9` on `B1..B9`):** Every exit path of `run_selfgame` (`mate`, `stalemate`, `rule`, `plylimit`, `matescore`, `evallimit`, `drawadj`) leaves `board` at the exact post-last-move position (or start position when `plies == 0`, including `B9` where `matescore` exits at ply `0` before `make_move` plays `a1a8`).
3. **Why `drawply 20` on `n[1..30]` changed `sgend` twice (`attempts 4, 22`) without changing record text:** Lowering `drawply` from `80` to `20` only changes `draw_run` in plies `20..79`. On `n[1..30]`, only two games (`attempts 4` and `22`) accumulated `8` consecutive `|cp| <= 5` plies before ply `80`, both reaching `run == 8` at ply `54`. On both games, `L` (`drawply 80`) happened to play a 3-fold repetition move immediately on ply `55` (`reason rule plies 55 run 0`). Since `rule` ends before searching ply `55` and `drawadj` ends after recording ply `54`, both write the exact same `47` records (`plies 8..54`) with `result 0`! Raising `drawply` (`80 -> 200` on `n[1..30]`) or extending `drawply 20` to `n[1..100]` immediately changes `5` games' record texts (`[6, 15, 20, 23, 29]` and `[33, 39, 58, 60, 97]`).
4. **Why `kK_plant` takes hunk 75's branch ~15x more often than `kK_cp` (`18` vs `1` on `200 / movetime 30`; `86` vs `12` on `1000 / movetime 10`):** In `kK_cp`, `!(result.pv.size() > 0 && result.pv[0] == pv_stack_[4][0])` is false whenever the aborted iteration's current best root move `pv_stack_[4][0]` still matches the previous completed iteration's `result.pv[0]` (which happens >90% of the time when `ss->pv_length > 0` at clock abort). In `kK_plant`, the condition compares root move `result.pv[0]` against ply-1 opponent move `pv_stack_[5][0]`, which can never equal a legal root move, so `kK_plant` fires on **every** clock abort where `ss->pv_length > 0`, publishing an opponent move (e.g., `d6b4` or `e2e3` on Black's turn) and failing `python-chess` legality `18/18` (`movetime 30`) and `86/86` (`movetime 10`) times.

### Suspicions
1. **Why the PC's `CK` saw `1` of `30` record-text change under `drawply 20` while `net768` on `n[1..30]` saw `0` of `30` (`2` `sgend` changes, `5` of `100` record-text changes):** Round 67's 768 king-bucket net and the PC's opening book produce different early equal-eval runs (`|cp| <= 5` for `8` plies before ply `80` without immediate 3-fold repetition on the very next ply). If a single bidirectional control for `drawply` is ever wanted on 30 games, `drawply 200` (disabling early draw adjudication up to ply 200) hits `5/30` on `n[1..30]`, whereas `drawply 20` hits `5/100`.
2. **Hunk 75 branch frequency with a real NNUE net vs built-in `v1`:** Built-in `v1` searches ~2M nps (`depth 11..14` in `20 ms`), spending most of its time on root move #1 where `ss->pv_length` is still `0` until move #1 finishes. With a slower NNUE evaluation or tighter bullet clock, root move ordering flips at shallower depths (`depth 6..9`, as seen at `movetime 10` where `kK_cp` hit `12 / 1000`), exercising hunk 75's `pv_stack_[4]` publish path ~2.4x more often per search.

### What I Did Not Do
- Did not modify any engine source file inside `/agent/repos/dwqww`, touch any branch other than `for-fable-and-opus/carbon2-work`, or open any PR.
- Did not rebuild `plain_r15d`, `r15d_v2`, or `kK` from scratch in Step 0 because all three recorded SP-PGO binaries were intact in `/tmp`, matched their recorded `exe_sha256` and `profdata_sha256`, and passed all 7 fresh-process Step 0 checks (`21/21`).
- Did not SP-PGO-train the three Part B scratch binaries (`kK_cp`, `kK_plant`, `kF_cp`); `-O3 -flto=thin` scratch builds were used and verified node-identical to SP-PGO `kK` and `kF` (`321964 == 321964` on 20 depth-10 searches).

### What I Am Not Sure About
- Whether the PC's client parses any leading/trailing whitespace around `selfgame` differently on Windows pipes (`parse_selfgame_config` treats `' '`, `'\t'`, `'\r'`, `'\n'` identically as token delimiters, so CRLF lines work identically to LF lines).
- How often hunk 75's abort-publish branch fires in multi-threaded (`Threads > 1`) clock games on the PC with the round-67 net.

---

## Pre-Commit Repository & Directory Verification (`git status --short && ls -R forge-combo29/carbon2/job36`)

```text
 M forge-combo29/carbon2/job36/stamps.txt
?? forge-combo29/carbon2/job36/REPORT_carbon2_job36.md
forge-combo29/carbon2/job36:
builds.txt
loop_v3_driver.py
partA_KA3_KF_summary.txt
partA_KB0_raw.txt
partA_KB9_CS_CK_raw.txt
partA_v2_A_rows.txt
partA_v2_B_rows.txt
partA_v2_C_rows.txt
partA_v2_n_rows.txt
partA_v3_A_rows.txt
partA_v3_B_rows.txt
partA_v3_C_rows.txt
partA_v3_n_rows.txt
partB_CP_counter_and_plant.patch.txt
partB_CP_kF_1000_mt10_rows.txt
partB_CP_kF_1000_rows.txt
partB_CP_kF_200_mt10_rows.txt
partB_CP_kF_rows.txt
partB_CP_kK_1000_mt10_rows.txt
partB_CP_kK_1000_rows.txt
partB_CP_kK_200_mt10_rows.txt
partB_CP_kK_rows.txt
partB_CP_plant_1000_mt10_rows.txt
partB_CP_plant_1000_rows.txt
partB_CP_plant_200_mt10_rows.txt
partB_CP_plant_rows.txt
partB_settled_and_CP_summary.txt
partC_apply_and_step0_raw.txt
partC_kF_v3_A_rows.txt
partC_kF_v3_B_rows.txt
partC_kF_v3_C_rows.txt
partC_kF_v3_n_rows.txt
partC_kF_v3_summary.txt
prediction_job36.txt
REPORT_carbon2_job36.md
run_partA_all.py
run_partB_cp.py
run_partC_kf_v3.py
selfgame_r15d_v3.patch.txt
stamps.txt
step0_raw.txt
v2_to_v3.diff.txt
verify_seven.py
```

---

**Model Name:** `Gemini 4 Carbon`
