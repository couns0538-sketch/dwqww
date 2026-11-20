# Carbon2 — Job 45 Report (`REPORT_carbon2_job45.md`)

**Builds used per part:** Step 0 and Part M10 used `bundle8` (`/tmp/carbon2_job45/bld_bundle8/forge`, executable `sha256` = `f714f80f716ef72f792b8b8d4d61fc64333d906dafec750a56e6d7a2182844b9`, built from `r15d + v3` `/tmp/carbon2_job36/tpl_r15d_v3` + `forge-combo29/carbon2/job41/bundle_grok7.patch.txt` + `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`, plus plain `r15d + v3` `/tmp/carbon2_job45/bld_base_v3/forge`, executable `sha256` = `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`). Part P10(a) used a scratch counter copy of `bundle8` (`/tmp/carbon2_job45/bld_p10_counter/forge`, executable `sha256` = `8b4be37c9a4c0e7f562117629fd128db1b49cf47c170b97c600e7fcd50482122`, never used for bundle rows or games). Part P10(b..d) used `bundle8_p10` (`/tmp/carbon2_job45/bld_bundle8_p10/forge`, executable `sha256` = `d0e88a3d658941dc7cbb7891df694181dfce98955d270f5e0a9c43dfb6f0fdd6`, built from `bundle8` + `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt`).

1. **(1) Step 0 (`forge-combo29/carbon2/job45/step0_raw.txt`):** **`PASS (1 == 1)`**. Verified all 4 `r15d + v3` source hashes (`0 == 0` CRLF), plain `r15d + v3` (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `PC20 278024 == 278024 / 587276 == 587276`, `Set A line L 26741 == 26741 / 107124743 == 107124743 / d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`, `n[1..60] 8449 == 8449 / 8482 == 8482 / 36688357 == 36688357 / b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`), and `bundle8`: all switches off = every OFF number plus `O` (`8315168 == 8315168`, `200 == 200` vs `job39/OFF_O_d12.rows.txt`) and `G` (`17611204 == 17611204`, `353 == 353` vs `job39/OFF_G_d12.rows.txt`); `IdeaB8b` alone = Job 41 `P7` rows position by position on `O` (`8483711 == 8483711`, `200 == 200`) and `G` (`17366116 == 17366116`, `353 == 353`); non-`PC20` `HindsightDepth` `bench 13` = `840387 == 840387` (`true`) and `862329 == 862329` (`false`); `IdeaS13 + IdeaS13_Hoist` = `O` `9069588 == 9069588` (`200 == 200`) and `G` `18700461 == 18700461` (`353 == 353`).
2. **(2) Prediction Graded (`forge-combo29/carbon2/job45/prediction_job45.txt`, committed alone in `9e6cb55ba` at `19:57:29 UTC` before `M10`'s first game at `19:58:25 UTC`):** **`2` of `2` `TRUE`**.
   - **Item (1) (Part M10 `IdeaB8b` Elo on top of `HindsightDepth` at `nodes=20000`, `4,000`g):** Predicted `+4.0` Elo, range **`[-4.5, +12.5]` Elo**. Observed = **`+4.95 +/- 7.13` Elo** (inside `[-4.5, +12.5]`). -> **`TRUE`**.
   - **Item (2) (Part P10 `(IdeaB8b + IdeaB8b_Fast) / IdeaB8b` time per 1,000 nodes on `O` d12):** Predicted `0.962`, range **`[0.945, 0.988]`**. Observed = **`0.954191`** (`0.534237 / 0.559885` ms / 1,000 nodes; inside `[0.945, 0.988]`). -> **`TRUE`**.
3. **(3) Part M10 (`forge-combo29/carbon2/job45/M10_recount.txt`, `IdeaB8b=true + HindsightDepth=true` vs `HindsightDepth=true` alone, `bundle8` `/tmp/carbon2_job45/bld_bundle8/forge`, `nodes=20000`, `PC20`, built-in eval, `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,013,501..2,015,500`, `4,000` games / `2,000` pairs `COMPLETE`):** Committed recount: **`1123 - 1066 - 1811`** (`50.7125%`, `0 == 0` non-normal endings, `2000 == 2000` book-line pairs), pentanomial **`[96, 455, 850, 494, 105]`**, **`+4.95 +/- 7.13` Elo** (`95% CI [-2.18, +12.08]`, exact `[-2.17, +12.08]`, `nElo +7.48 +/- 10.77`, `LOS 91.34%`) — identical to `fastchess`'s own line (`Games: 4000, Wins: 1123, Losses: 1066, Draws: 1811, Points: 2028.5 (50.71 %) | Elo: 4.95 +/- 7.13, nElo: 7.48 +/- 10.77 | Ptnml(0-2): [96, 455, 850, 494, 105]`). Side A (`IdeaB8b + HindsightDepth`) finished ahead of `HindsightDepth` alone (`+57` net wins, `LOS 91.34%`), while `0` Elo remains inside the 95% confidence interval (`[-2.18, +12.08]`).
4. **(4) Part P10 (`forge-combo29/carbon2/job45/P10_summary.txt`, `P10a_counter_summary.txt`, `P10_B8b_fast.patch.txt`, `P10d_timing_summary.txt`):** **`PASS (1 == 1)`**.
   - **`P10(a)` Counters (`O` depth 12, `200 == 200` searches, `IdeaB8b` on, `8483711 == 8483711` nodes, `200 == 200` row-equal to clean `bundle8`):** `role_b8b_threat` called **`36,640,558`** times (`4.319 / node`); computed (cache miss) **`2,581,760`** times (`7.05%` of calls, `0.304 / node`); answered by one-key cache **`34,058,798`** times (`92.95%` of calls); `threat.present == true` on **`590,062`** of `2,581,760` computations (`22.86%`) and **`8,737,334`** of `36,640,558` calls (`23.85%`). Across all `8,737,334` `threat_role_b8b_of` calls (`8,613,327` from `threat_role_b8b_bonus`, `124,007` from `update_threat_role_b8b`): **`role 0` = `5,367,504` (`61.43%`)**, **`role 1` = `1,799,338` (`20.59%`)**, **`role 2` = `1,008,644` (`11.54%`)**, **`role 3` = `496,223` (`5.68%`)**, **`role 4` = `65,625` (`0.75%`)** (`sum = 8737334 == 8737334`).
   - **`P10(b)` Patch:** `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt` (`372` lines, `0 == 0` CRLF, `git apply --check -p1` `0 == 0` on `bundle8`, `sha256` = `47c4f2e84d67f3f507c6000ba43ec40a5b0a157eba8c54659da7ed02aba74c6e`), adding UCI check option `IdeaB8b_Fast` (default `false`; inactive unless `IdeaB8b` is on).
   - **`P10(c)` Identity:** `IdeaB8b_Fast` alone (`IdeaB8b=false`) = OFF `O` (`8315168 == 8315168`, `200 == 200`). `IdeaB8b + IdeaB8b_Fast` = `IdeaB8b` alone position by position on `O` (`8483711 == 8483711`, `200 == 200`), `G` (`17366116 == 17366116`, `353 == 353`), and `Set A line L` (`26709 == 26709` records, `26829 == 26829` searches, `106651211 == 106651211` nodes, `full_sha256` `de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31 == de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31`, `200 == 200` attempts vs `job41/P7_bundle7_only_B8b_SetA_L.rows.txt`).
   - **`P10(d)` Times (`O`, depth 12, pinned core 1, forward `01..04` + reverse `05..08`, `200 == 200` equal rows on every run):** `all_off_1 = 0.513672` ms/1k, `all_off_2 = 0.515056` ms/1k (`4`-run `all_off` mean = `0.514364` ms/1k; two-pair spread = `0.27%`); `IdeaB8b` alone = **`0.559885` ms/1k** (`1.088499x` `all_off`); `IdeaB8b + IdeaB8b_Fast` = **`0.534237` ms/1k** (`1.038636x` `all_off`). **Key ratio `(IdeaB8b + IdeaB8b_Fast) / IdeaB8b` alone = `0.534237 / 0.559885 = 0.954191`** (`-4.58%` total search time, eliminating **`56.34%`** of `IdeaB8b`'s incremental per-node overhead).

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 4,000 games carry about +/- 6 Elo, so M10 can say whether IdeaB8b's extra is above 0, not how large it is; with the built-in evaluation a node is cheap, so IdeaB8b's share of a node's time is larger on your tree than with the PC's net.

---

## 1. Step 0 & Named Hashes (`forge-combo29/carbon2/job45/step0_raw.txt` & `builds.txt`)

- **Source, patch, executable, book, and set hashes:**
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp`: `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp`: `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp`: `2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp`: `5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77` (`0 == 0` CRLF)
  - Patch file `sha256` of `forge-combo29/carbon2/job41/bundle_grok7.patch.txt`: `b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 == b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146`
  - Patch file `sha256` of `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`: `16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 == 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326`
  - Patch file `sha256` of `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt`: `47c4f2e84d67f3f507c6000ba43ec40a5b0a157eba8c54659da7ed02aba74c6e` (`372` lines, `0 == 0` CRLF)
  - Executable `sha256` of `/tmp/carbon2_job45/bld_base_v3/forge`: `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`
  - Executable `sha256` of `/tmp/carbon2_job45/bld_bundle8/forge` (Step 0 & M10): `f714f80f716ef72f792b8b8d4d61fc64333d906dafec750a56e6d7a2182844b9`
  - Executable `sha256` of `/tmp/carbon2_job45/bld_p10_counter/forge` (P10a scratch counter build): `8b4be37c9a4c0e7f562117629fd128db1b49cf47c170b97c600e7fcd50482122`
  - Executable `sha256` of `/tmp/carbon2_job45/bld_bundle8_p10/forge` (P10b..d): `d0e88a3d658941dc7cbb7891df694181dfce98955d270f5e0a9c43dfb6f0fdd6`
  - Executable `sha256` of `/tmp/carbon2_job40/fastchess`: `a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
  - Opening book `sha256` of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)
  - `O` set `sha256` of `/tmp/carbon2_job39/sets/first200.fens`: `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (`200` FENs)
  - `G` set `sha256` of `/tmp/carbon2_job39/sets/set_G.epd`: `af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d` (`353` FENs)
  - Prediction file `sha256` of `forge-combo29/carbon2/job45/prediction_job45.txt`: `1714faa83b6976f9ca20405c1e7cc951320ef281c6357542b43c29c3f783bada`

---

## 2. Prediction Audit (`forge-combo29/carbon2/job45/prediction_job45.txt`)

| # | Target | Point Prediction | Predicted Range | Observed | Grade |
|---|---|---|---|---|---|
| `(1)` | Part M10: `IdeaB8b` Elo on top of `HindsightDepth` (`nodes=20000`, `4,000`g) | `+4.0` Elo | `[-4.5, +12.5]` Elo | **`+4.95 +/- 7.13` Elo** (`95% CI [-2.18, +12.08]`, `LOS 91.34%`) | **`TRUE`** |
| `(2)` | Part P10: `(IdeaB8b + IdeaB8b_Fast) / IdeaB8b` alone (`O` d12 ms / 1k nodes) | `0.962` | `[0.945, 0.988]` | **`0.954191`** (`0.534237 / 0.559885` ms / 1k nodes) | **`TRUE`** |

---

## 3. Part M10 Details (`forge-combo29/carbon2/job45/M10_recount.txt`, `M10_games.tsv`, `M10_fastchess.txt`, `M10_fastchess.txt.meta`)

- **Setup:** `/tmp/carbon2_job45/bld_bundle8/forge` (`sha256` = `f714f80f716ef72f792b8b8d4d61fc64333d906dafec750a56e6d7a2182844b9`), `PC20`, built-in evaluation, `nodes=20000`, `Threads=1`, `Hash=16`, `OwnBook=false`, `-concurrency 3`, `-rounds 2000 -games 2 -repeat` (`4,000` games = `2,000` pairs) on `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,013,501..2,015,500` (`1,849.6` s wall time).
  - Side A (`B8b_HindsightDepth_on`): `IdeaB8b=true`, `HindsightDepth=true`, all other 7 `Idea*` switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS13_Hoist`, `IdeaS10`, `IdeaB8`) explicitly `false`.
  - Side B (`only_HindsightDepth`): `IdeaB8b=false`, `HindsightDepth=true`, all other 7 `Idea*` switches explicitly `false`.
- **File Hashes:**
  - `M10_games.tsv` (`forge-combo29/carbon2/job45/M10_games.tsv`): `sha256` = `30e98f380d09faeed71f2654f589d8bb8ede927d2ea2c1aa62605d65157c93e6`
  - `M10_fastchess.txt` (`forge-combo29/carbon2/job45/M10_fastchess.txt`): `sha256` = `95f0b34e594e82d173a94385a9cfeb14de59a927a41686bfa3ddcfcf82a2841b`
- **Side-by-Side Verification Checks (`M10_recount.txt`):**
  - Non-normal terminations: `PASS (0 == 0)`
  - Opening FEN pairs matching UHO book slice `2,013,501..2,015,500` in exact order: `PASS (2000 == 2000)`
  - Finished games vs target: `PASS (4000 == 4000)` (`unpaired = 0`, `mean_plies = 144.66`)
  - Finished pairs vs target: `PASS (2000 == 2000)`
  - Recount W-L-D vs `fastchess`: `PASS (1123 == 1123)`, `PASS (1066 == 1066)`, `PASS (1811 == 1811)` (`2028.5 / 4000 = 50.7125%`)
  - Recount pentanomial `[LL, LD, WL+DD, WD, WW]` vs `fastchess`: `PASS ([96, 455, 850, 494, 105] == [96, 455, 850, 494, 105])`
  - Recount Elo & 95% error vs `fastchess`: `PASS (+4.95 == +4.95)`, `PASS (7.13 == 7.13)` (`95% CI [-2.18, +12.08]`; `LOS 91.34%`)
  - `fastchess` own line: `Games: 4000, Wins: 1123, Losses: 1066, Draws: 1811, Points: 2028.5 (50.71 %) | Elo: 4.95 +/- 7.13, nElo: 7.48 +/- 10.77 | Ptnml(0-2): [96, 455, 850, 494, 105], WL/DD Ratio: 0.97`

---

## 4. Part P10 Details (`forge-combo29/carbon2/job45/P10_summary.txt`)

### 4a. `P10(a)` Counter Summation (`P10a_B8b_counters_O_d12.raw.txt`, `sha256` = `1dfd38900f928fedff353581038693a03211093e1a0e4d3e91a742ff194abecb`)

- **Zero-Node-Change Proof:** Scratch counter build (`/tmp/carbon2_job45/bld_p10_counter/forge`) matched Step 0's clean `bundle8` `step0_bundle8_only_IdeaB8b_O_d12.rows.txt` (`sha256` = `7e53751747817f9670b9446f96d473ad90fb2fdadddd2928ab69e63e3eea8c2c`) and Job 41's `P7_bundle7_only_B8b_O_d12.rows.txt` on **`PASS (200 == 200)`** positions (`PASS (8483711 == 8483711)` nodes).

| Counter (`sum_p10_counters.py`, `200 == 200` `O` depth-12 searches, `8,483,711` nodes) | Total | Share / Rate |
|---|---|---|
| `role_b8b_threat` total calls | **`36,640,558`** | `4.319 / node` |
| `role_b8b_threat` computations (cache misses) | **`2,581,760`** | `7.05%` of calls (`0.304 / node`) |
| One-key cache hits (`role_b8b_key_ == board.key()`) | **`34,058,798`** | `92.95%` of calls (`4.015 / node`) |
| `threat.present == true` on computations | **`590,062`** | `22.86%` of `2,581,760` computations |
| `threat.present == true` across all calls | **`8,737,334`** | `23.85%` of `36,640,558` calls (`76.15%` `false`) |
| `threat_role_b8b_of` total calls (`== call_present`, `PASS 8737334 == 8737334`) | **`8,737,334`** | `1.030 / node` (`8,613,327` bonus + `124,007` update) |
| — `role = 0` (none / other quiet under threat) | **`5,367,504`** | `61.43%` of `threat_role_b8b_of` calls |
| — `role = 1` (attacked piece steps away: `move.from == victim_sq`) | **`1,799,338`** | `20.59%` |
| — `role = 2` (another piece blocks slider ray) | **`1,008,644`** | `11.54%` |
| — `role = 3` (quiet attacks `attacker_sq`) | **`496,223`** | `5.68%` |
| — `role = 4` (quiet creates greater threat / counter-check) | **`65,625`** | `0.75%` |
| `note_role_b8b_swing` calls / `gained >= 40` / total table updates | `595,061` / `22,891` / `124,007` | `3.85%` of swing calls update |

### 4b. `P10(b)` Design of `job45/P10_B8b_fast.patch.txt`

1. **256-slot per-`Worker` `B8bFastEntry` cache (`b8b_fast_cache_[key & 255]`):** Eliminates child-subtree eviction of the parent node's threat lookup when `Worker::search` returns from child moves to `Worker::quiet_history`, `update_quiet_stats`, and `note_role_b8b_swing` (in `P10a`, original `IdeaB8b` recomputed `role_b8b_threat` `2,581,760` times = `0.304 / node`, more than twice `IdeaB8`'s `1,254,672` = `0.152 / node`, because `IdeaB8b` is also read in `Worker::quiet_history`).
2. **Exact lexicographic-tier `make_b8b_fast_entry(board)` + per-mover `role4_mask[7]`:** Checks `King` victim (`worth = 100000`) in one register test via `board.checkers()`, then `Queen` (`900`), `Rook` (`500`), and `Knight|Bishop` (`300`) in strict `(-victim_worth, +attacker_worth, +victim_sq, +attacker_sq)` order using `pawn_attacks_bb(them, enemy_pawns)` bitmasks, and precomputes `between_bb`, `attacker_bb`, and `role4_mask[Pawn..King]` (`enemy_worth > max(victim_worth, mover_worth)`, `0` for `King` movers since `SeePieceValue[King] == 0`).
3. **`QuietScorer` constructor hoist (`prepare_b8b_fast_scorer`), `quiet_history` fast path, and `update_quiet_stats` batch hoist:** On the `76.15%` of calls without a threat, `QuietScorer::score` does zero calls per move and `update_quiet_stats` skips the entire malus loop's B8b updates in one check; when a threat is present, `b8b_fast_scaled[0..4]` is pre-scaled once per `MovePicker` and `role_b8b_fast` classifies roles `0..4` via pure bitmask operations.

### 4c. `P10(c)` Identity Verification (`P10_summary.txt`)

- `IdeaB8b_Fast=true, IdeaB8b=false` on `O` (`P10c_only_IdeaB8b_Fast_B8b_off_O_d12.rows.txt`): `PASS (8315168 == 8315168)`, `PASS (200 == 200)` vs `job39/OFF_O_d12.rows.txt`.
- `IdeaB8b + IdeaB8b_Fast` vs `IdeaB8b` alone (`P10c_B8b_and_B8b_Fast_*.rows.txt` vs `P10c_only_B8b_*.rows.txt` and `job41/P7_bundle7_only_B8b_*.rows.txt`):
  - `O` (`200` FENs, d12): `PASS (8483711 == 8483711)`, `PASS (200 == 200)` equal positions (`nodes`, `bestmove`, `score`).
  - `G` (`353` FENs, d12): `PASS (17366116 == 17366116)`, `PASS (353 == 353)` equal positions (`nodes`, `bestmove`, `score`).
  - `Set A line L` (`200` attempts): `PASS (26709 == 26709)` records, `PASS (26829 == 26829)` searches, `PASS (106651211 == 106651211)` nodes, `PASS (de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31 == de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31)`, `PASS (200 == 200)` equal attempts vs `only_B8b` and vs Job 41 `P7`.

### 4d. `P10(d)` Timing Table (`P10d_timing_summary.txt`, `O` depth 12, `PC20`, built-in eval, pinned core 1)

| Run File (`P10d_partT_*.rows.txt`) | Pass | Setting | `node_sum` (`equal_pos`) | `wall_s` | `ms / 1,000 nodes` | `us / 1,000 nodes` | Ratio vs `all_off` Mean (`0.514364`) |
|---|---|---|---|---|---|---|---|
| `P10d_partT_01_fwd_all_off_1` | `fwd` | `all_off_1` | `8,315,168` (`200 == 200`) | `4.2562` | `0.511855` | `511.855` | `0.995122` |
| `P10d_partT_02_fwd_all_off_2` | `fwd` | `all_off_2` | `8,315,168` (`200 == 200`) | `4.2940` | `0.516410` | `516.410` | `1.003978` |
| `P10d_partT_03_fwd_only_B8b` | `fwd` | `only_B8b` | `8,483,711` (`200 == 200`) | `4.7345` | `0.558067` | `558.067` | `1.084965` |
| `P10d_partT_04_fwd_B8b_and_B8b_Fast` | `fwd` | `B8b_and_B8b_Fast` | `8,483,711` (`200 == 200`) | `4.5331` | `0.534332` | `534.332` | `1.038821` |
| `P10d_partT_05_rev_B8b_and_B8b_Fast` | `rev` | `B8b_and_B8b_Fast` | `8,483,711` (`200 == 200`) | `4.5315` | `0.534141` | `534.141` | `1.038450` |
| `P10d_partT_06_rev_only_B8b` | `rev` | `only_B8b` | `8,483,711` (`200 == 200`) | `4.7653` | `0.561702` | `561.702` | `1.092033` |
| `P10d_partT_07_rev_all_off_2` | `rev` | `all_off_2` | `8,315,168` (`200 == 200`) | `4.2715` | `0.513702` | `513.702` | `0.998712` |
| `P10d_partT_08_rev_all_off_1` | `rev` | `all_off_1` | `8,315,168` (`200 == 200`) | `4.2864` | `0.515490` | `515.490` | `1.002189` |

| Setting | `node_sum` | Forward `ms/1k` | Reverse `ms/1k` | Paired Mean `ms/1k` | Paired Mean `us/1k` | Ratio vs `all_off` (`0.514364`) |
|---|---|---|---|---|---|---|
| `all_off_1` | `8,315,168` | `0.511855` | `0.515490` | `0.513672` | `513.672` | `0.998655` |
| `all_off_2` | `8,315,168` | `0.516410` | `0.513702` | `0.515056` | `515.056` | `1.001345` |
| `only_B8b` | `8,483,711` | `0.558067` | `0.561702` | **`0.559885`** | `559.885` | `1.088499` (`+8.85%`) |
| **`B8b_and_B8b_Fast`** | `8,483,711` | `0.534332` | `0.534141` | **`0.534237`** | `534.237` | **`1.038636`** (`+3.86%`) |

- **Noise / drift:** Forward `all_off` (`0.514132` ms/1k) vs reverse `all_off` (`0.514596` ms/1k) drift = `1.000901`; two `all_off` pairs' spread = `0.27%`.
- **Key speedup ratio:** `(IdeaB8b + IdeaB8b_Fast) / IdeaB8b` alone = `0.534237 / 0.559885` = **`0.954191`** (`56.34%` of `IdeaB8b`'s incremental per-node overhead removed, with zero nodes changed).

---

## 5. Facts, Suspicions (Apart), Read and Not Tested (Apart), What I Did Not Do, What I Am Not Sure About

### Facts (Proven from Committed Files in `forge-combo29/carbon2/job45/`)
1. **Part M10 (`nodes=20000`, `4,000` games):** `IdeaB8b + HindsightDepth` vs `HindsightDepth` alone scored `1123 - 1066 - 1811` (`+4.95 +/- 7.13` Elo, `95% CI [-2.18, +12.08]`, `LOS 91.34%`) on unused UHO book lines `2,013,501..2,015,500`.
2. **Why `IdeaB8b` (`028`) Recomputed Threats Twice as Often as `IdeaB8` (`078`):** `P10a` counters prove `role_b8b_threat` computed `2,581,760` times across `8,483,711` nodes (`0.304 / node`, vs `IdeaB8`'s `1,254,672` = `0.152 / node` in Job 43 `P9a`), because `IdeaB8b` is read inside `Worker::quiet_history` on every searched quiet move in addition to `QuietScorer::score` — and each child subtree search overwrites `role_b8b_key_` in the 1-key cache before the parent ply scores/reduces its next quiet move.
3. **Why `threat.present` Is Higher in `IdeaB8b` (`22.86%` of computations) than `IdeaB8` (`9.18%`):** `IdeaB8b` includes `King` (`KingWorth = 100000`) as a victim (`board.checkers() != 0`), so every in-check position has `threat.present == true` in addition to material-under-cheaper-attack positions.
4. **Exact Identity & Speed of `IdeaB8b_Fast` (`P10_B8b_fast.patch.txt`):** `IdeaB8b + IdeaB8b_Fast` matches `IdeaB8b` alone on `200 / 200` `O`, `353 / 353` `G`, and `200 / 200` `Set A line L` (`26,709` records, `de20b5698c77baab...`), acts as a strict no-op when `IdeaB8b=false` (`200 == 200` vs OFF `O`), and cuts per-node search time to `0.954191x` of `IdeaB8b` alone (`56.34%` of `IdeaB8b` overhead eliminated).

### Suspicions (Apart from Facts)
1. **Why `3.86%` Per-Node Overhead Remains Under `IdeaB8b + IdeaB8b_Fast` (vs `2.60%` for `IdeaB8 + IdeaB8_Fast`):** Because `threat.present` is `true` on `23.85%` of calls (`8.74M` calls across `8.48M` nodes, vs `9.82%` = `3.12M` calls in `IdeaB8`) AND `IdeaB8b` is also read in `Worker::quiet_history` (`~1` slider/leaper attack lookup per searched quiet move on the `23.85%` threat-present visits), `role_b8b_fast` still runs ~`2.8x` as often per node as `IdeaB8_Fast`'s `role_fast`. Passing the already-computed `QuietScorer` role score or caching `B8bFastEntry*` on `SearchStack` at `ss` across the move loop of `Worker::search` would eliminate the hash-slot probe in `quiet_history` and `update_quiet_stats` too.
2. **Patch Portability to the PC's Loop Tree (`r15d + v3 + P7_B8b_028.patch.txt` without `bundle_grok7`):** Per File 45 line 86, `P10_B8b_fast.patch.txt` is diffed on top of `bundle8` (so 4 hunk context lines mention `IdeaB8` / `IdeaS13_Hoist`); on the PC's loop tree (`r15d + v3 + P7_B8b_028.patch.txt`), the `IdeaB8b_Fast` code itself touches zero `IdeaB8`/`IdeaS13` symbols and only needs those 4 context lines matched to `P7_B8b_028`.

### Read and Not Tested (Apart)
- Read File 45's recount of Job 43 (`M6b`, `M6 + M6b` pooled, `M7`, `P9c`, `P9d`) and the report that the PC's loop-tree build with `P7_B8b_028.patch.txt` matched `O` (`8,483,711`) on `200 / 200` and `1,200 / 1,200` off positions with two PC nets; not re-tested here (no PC net on this VM).

### What I Did Not Do
- Did not edit any tracked engine source file in-place (`git diff` on tracked engine files is empty; engine change is `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt` only).
- Did not commit any binary, `.pgn`, `.pyc`, profile data, or archive file.
- Did not create any pull request or touch any branch other than `for-fable-and-opus/carbon2-work`.
- Did not run `Set A line L` wall-time rotation with `IdeaB8b + IdeaB8b_Fast + HindsightDepth` (not requested in File 45; `P10c` ran `Set A line L` for `IdeaB8b` identity and `P10d` timed `O` depth 12 per File 45 line 91).

### What I Am Not Sure About
- Whether `IdeaB8b`'s true marginal Elo on top of `HindsightDepth` with the PC's trained NNUE net is closer to `0`, `+5`, or `+8` Elo (`M10` with built-in evaluation gives `+4.95 +/- 7.13` Elo, `LOS 91.34%`, which favors a positive addition without excluding `0` at 95% confidence).
- What fraction of `IdeaB8b`'s per-node overhead remains once amortized against a full `v3` NNUE evaluation on the PC's Windows build, and whether `IdeaB8b_Fast` brings that net-build overhead below `~1%`.

---

## 6. Model Name, Timestamps (`stamps.txt`), and Final Pre-Commit `git status` + `ls -R`

- **Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job45/stamps.txt`):**
  - `job45_claimed`: `Fri Nov 20 07:50:49 PM UTC 2026` (Minute 80 hard stop = `21:10:49 UTC`)
  - `step0_done`: `Fri Nov 20 07:56:32 PM UTC 2026`
  - `prediction_job45.txt` (`commit 9e6cb55ba`): `Fri Nov 20 07:57:29 PM UTC 2026` (committed alone before `M10`'s first game at `19:58:25 UTC`)
  - `partM10_done`: `Fri Nov 20 08:29:47 PM UTC 2026`
  - `partP10_done`: `Fri Nov 20 08:42:58 PM UTC 2026`
- **Output of `git status --short && ls -R forge-combo29/carbon2/job45` immediately before the report commit:**

```text
?? forge-combo29/carbon2/job45/REPORT_carbon2_job45.md
forge-combo29/carbon2/job45:
builds.txt
j45_lib.py
M10_fastchess.txt
M10_fastchess.txt.meta
M10_games.tsv
M10_recount.txt
P10a_B8b_counters_O_d12.raw.txt
P10a_B8b_counters_O_d12.raw.txt.meta
P10a_counter_summary.txt
P10_B8b_fast.patch.txt
P10c_B8b_and_B8b_Fast_G_d12.rows.txt
P10c_B8b_and_B8b_Fast_G_d12.rows.txt.meta
P10c_B8b_and_B8b_Fast_O_d12.rows.txt
P10c_B8b_and_B8b_Fast_O_d12.rows.txt.meta
P10c_B8b_and_B8b_Fast_SetA_L.rows.txt
P10c_B8b_and_B8b_Fast_SetA_L.rows.txt.meta
P10c_only_B8b_G_d12.rows.txt
P10c_only_B8b_G_d12.rows.txt.meta
P10c_only_B8b_O_d12.rows.txt
P10c_only_B8b_O_d12.rows.txt.meta
P10c_only_B8b_SetA_L.rows.txt
P10c_only_B8b_SetA_L.rows.txt.meta
P10c_only_IdeaB8b_Fast_B8b_off_O_d12.rows.txt
P10c_only_IdeaB8b_Fast_B8b_off_O_d12.rows.txt.meta
P10d_partT_01_fwd_all_off_1.rows.txt
P10d_partT_01_fwd_all_off_1.rows.txt.meta
P10d_partT_02_fwd_all_off_2.rows.txt
P10d_partT_02_fwd_all_off_2.rows.txt.meta
P10d_partT_03_fwd_only_B8b.rows.txt
P10d_partT_03_fwd_only_B8b.rows.txt.meta
P10d_partT_04_fwd_B8b_and_B8b_Fast.rows.txt
P10d_partT_04_fwd_B8b_and_B8b_Fast.rows.txt.meta
P10d_partT_05_rev_B8b_and_B8b_Fast.rows.txt
P10d_partT_05_rev_B8b_and_B8b_Fast.rows.txt.meta
P10d_partT_06_rev_only_B8b.rows.txt
P10d_partT_06_rev_only_B8b.rows.txt.meta
P10d_partT_07_rev_all_off_2.rows.txt
P10d_partT_07_rev_all_off_2.rows.txt.meta
P10d_partT_08_rev_all_off_1.rows.txt
P10d_partT_08_rev_all_off_1.rows.txt.meta
P10d_timing_summary.txt
P10_summary.txt
prediction_job45.txt
REPORT_carbon2_job45.md
run_partM10.py
run_partP10.py
run_step0.py
stamps.txt
step0_bundle8_all_off_G_d12.rows.txt
step0_bundle8_all_off_G_d12.rows.txt.meta
step0_bundle8_all_off_O_d12.rows.txt
step0_bundle8_all_off_O_d12.rows.txt.meta
step0_bundle8_only_IdeaB8b_G_d12.rows.txt
step0_bundle8_only_IdeaB8b_G_d12.rows.txt.meta
step0_bundle8_only_IdeaB8b_O_d12.rows.txt
step0_bundle8_only_IdeaB8b_O_d12.rows.txt.meta
step0_bundle8_S13_and_Hoist_G_d12.rows.txt
step0_bundle8_S13_and_Hoist_G_d12.rows.txt.meta
step0_bundle8_S13_and_Hoist_O_d12.rows.txt
step0_bundle8_S13_and_Hoist_O_d12.rows.txt.meta
step0_raw.txt
sum_p10_counters.py
```
