# Carbon2 — Job 43 Report (`REPORT_carbon2_job43.md`)

1. **(1) Step 0 (`forge-combo29/carbon2/job43/step0_raw.txt`):** **`PASS (1 == 1)`**. Verified `r15d + v3` (`/tmp/carbon2_job36/tpl_r15d_v3`, all 4 file hashes + `0 == 0` CRLF), plain `r15d + v3` (`/tmp/carbon2_job43/bld_base_v3/forge`, executable `sha256` = `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`), and fresh `bundle8` (`/tmp/carbon2_job43/bld_bundle8/forge`, executable `sha256` = `73b20f3009afe87742b43b022eac127518791dbe85ff52e90eb809633aba6507`, built from `r15d + v3` + `forge-combo29/carbon2/job41/bundle_grok7.patch.txt` + `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`, with `hoisted_s13_prep` read directly before `board.make_move(move, undo)` in `Worker::search`, AFTER the singular-extension search). Passed every OFF number (default off and explicit 8 `false`), non-`PC20` `HindsightDepth` `bench 13` (`862329 == 862329` false, `840387 == 840387` true), `IdeaB8b` alone on `O` (`8483711 == 8483711`, `200 == 200`), `IdeaS13_Hoist` alone (`IdeaS13=false`) = OFF on `O` (`8315168 == 8315168`, `200 == 200`) and `G` (`17611204 == 17611204`, `353 == 353`), `IdeaS13` alone (`IdeaS13_Hoist=false`) = Job 39 `P4` on `O` (`8077984 == 8077984`, `200 == 200`) and `G` (`17460346 == 17460346`, `353 == 353`), and the PC's independent known answers for `IdeaS13 + IdeaS13_Hoist`: **`O` sum `9069588 == 9069588`** (first five `[20032, 17387, 38324, 18248, 22728] == [20032, 17387, 38324, 18248, 22728]`, differs from `S13` alone on `200 == 200`) and **`G` sum `18700461 == 18700461`** (first five `[69963, 64050, 83616, 47203, 25100] == [69963, 64050, 83616, 47203, 25100]`, equal to `S13` alone on `11 == 11`).
2. **(2) Prediction Graded (`forge-combo29/carbon2/job43/prediction_job43.txt`, committed alone in `c4ad2dad7` at `18:10:07 UTC` before `M6b`'s first game):** **`2` of `3` `TRUE`**.
   - **Item (1) (`M6b` Elo and inside `M6`'s 95% CI):** Predicted `+9.5` Elo, range **`[+1.0, +18.0]` Elo**, inside `M6`'s 95% CI (`[+0.27, +16.64]`): **`YES`**. Observed `M6b` = **`+11.47 +/- 8.31` Elo** (inside `[+1.0, +18.0]` and inside `[+0.27, +16.64]`). -> **`TRUE`**.
   - **Item (2) (`P9` `(IdeaB8 + IdeaB8_Fast) / IdeaB8_alone` time per `1,000` nodes):** Predicted `0.970`, range **`[0.948, 0.990]`**. Observed = **`0.959944`** (`0.534423 / 0.556724` ms per `1,000` nodes, inside `[0.948, 0.990]`, with `0` node differences on `O`, `G`, and `Set A line L`). -> **`TRUE`**.
   - **Item (3) (`M7` `IdeaS13 + IdeaS13_Hoist` vs `all_off` Elo):** Predicted `-3.0` Elo, range **`[-13.5, +7.5]` Elo**. Observed (at clean Minute-80 safety `CUT`, `729` games / `364` pairs) = **`-17.19 +/- 16.48` Elo** (same negative sign as predicted, but `< -13.5` Elo lower bound). -> **`FALSE`**.
3. **(3) Part M6b and `M6 + M6b` Pooled (`IdeaB8b=true + HindsightDepth=true` vs `all_off`, `nodes=20000`, `PC20`, built-in eval):**
   - **`M6b` (`COMPLETE`, `3,000` games / `1,500` pairs, `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,009,001..2,010,500`, `forge-combo29/carbon2/job43/M6b_recount.txt`):** Committed recount: **`886 - 787 - 1327`** (`51.65%`, `0` unpaired, `0` non-normal), pentanomial **`[65, 340, 614, 393, 88]`**, **`+11.47 +/- 8.31` Elo** (`95% CI [+3.15, +19.78]`, exact `[+3.16, +19.79]`, `nElo +17.17 +/- 12.43`, `LOS 99.66%`) — identical to `fastchess`'s own line (`Games: 3000, Wins: 886, Losses: 787, Draws: 1327, Points: 1549.5 (51.65 %) | Elo: 11.47 +/- 8.31, nElo: 17.17 +/- 12.43 | Ptnml(0-2): [65, 340, 614, 393, 88]`).
   - **`M6 + M6b` Pooled (`COMPLETE`, `6,000` games / `3,000` pairs, `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,007,501..2,010,500`, recounted directly from `forge-combo29/carbon2/job42/M6_games.tsv` + `forge-combo29/carbon2/job43/M6b_games.tsv` in `forge-combo29/carbon2/job43/M6_M6b_pooled_recount.txt`):** **`1743 - 1571 - 2686`** (`51.43%`, `0` unpaired, `0` non-normal, `3000 == 3000` book-line pairs), pentanomial **`[133, 674, 1245, 784, 164]`**, **`+9.96 +/- 5.83` Elo** (`95% CI [+4.13, +15.80]`, exact `[+4.13, +15.80]`, `nElo +15.03 +/- 8.79`, **`LOS 99.96%`**). *(Note: `fastchess` has no pooled line across separate Job 42 and Job 43 runs; Job 42 `M6`'s own `fastchess` line was `857 - 784 - 1359`, `[68, 334, 631, 391, 76]`, `8.46 +/- 8.18` Elo on lines `2,007,501..2,009,000`.)*
4. **(4) Part P9 (`IdeaB8` (`078`) Counters, Profiles, `IdeaB8_Fast` Identity Proofs, and Part T Timing):**
   - **Counters (`forge-combo29/carbon2/job43/P9a_counter_summary.txt`, summed over ALL `searches_summed = 200` `O` depth-12 searches, `total_nodes = 8,262,696`, `200 == 200` row-equal to clean `IdeaB8` `O`):** `ensure_role_threat` = **`35,883,443`** calls (`4.343 / node`), of which `find_role_threat` ran **`2,514,947`** times (`7.01%` misses; `threat.present == true` on only **`230,896` = `9.18%`**) and the 1-slot per-`Worker` cache answered **`33,368,496`** (`92.99%`); `quiet_threat_role` ran **`4,753,914`** times (`4,688,901` bonus + `65,013` update), returning `role = -1: 0`, `0: 942,239 (19.82%)`, `1: 41,772 (0.88%)`, `2: 313,536 (6.60%)`, `3: 61,331 (1.29%)`, **`4: 3,395,036 (71.42%)`**; `note_threat_swing` ran **`4,938,069`** times (`gained >= 48` on `36,831` = `0.75%`, table updates from swing = **`12,790`** = `0.26%`, total `ThreatRoleHistory` updates = **`65,013`**).
   - **Profiles (`forge-combo29/carbon2/job43/P9b_profile_summary.txt`):** Side-by-side Top-10 `perf` CPU-clock self shares (`2x O` depth 12, pinned core 1) show `QuietScorer::score` rising from `4.01%` (Rank 8, `all_off`) to `4.80%` (Rank 5, `IdeaB8` alone), plus `find_role_threat = 1.78%`, `Worker::threat_role_bonus = 1.37%`, `quiet_threat_role = 0.52%`, and `Worker::update_threat_role = 0.07%` (full Top-10 table in Section 4.2 below).
   - **`IdeaB8_Fast` Variant (`forge-combo29/carbon2/job43/P9_B8_fast.patch.txt`, `286` lines, LF `0 == 0` CRLF, patch file `sha256` = `bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395`):** Covers `IdeaB8` (`078`) only (`IdeaB8_Fast=true` with `IdeaB8=false` matches OFF `O` on `200 == 200` positions, `8315168 == 8315168`). `IdeaB8 + IdeaB8_Fast` equals `IdeaB8` alone position-by-position on **`O` (`8262696 == 8262696`, `200 == 200` equal)**, **`G` (`17342378 == 17342378`, `353 == 353` equal)**, and **`Set A line L` (`25818 == 25818` records, `25946 == 25946` searches, `105263539 == 105263539` nodes, `record_text sha256` `36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8 == 36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8`)**.
   - **Part T Times per `1,000` Nodes (`forge-combo29/carbon2/job43/P9d_timing_summary.txt`, forward + reverse, pinned core 1, `O` d12, `PC20`):** `all_off` mean (4 runs) = **`0.520901` ms** (`520.901` us; `1.000000x`); `IdeaB8` alone = **`0.556724` ms** (`556.724` us; `1.068770x`); `IdeaB8 + IdeaB8_Fast` = **`0.534423` ms** (`534.423` us; `1.025959x`); `IdeaB8b` alone = **`0.554719` ms** (`554.719` us; `1.064921x`). Ratio **`(IdeaB8 + IdeaB8_Fast) / (IdeaB8 alone) = 0.959944`**, cutting **`62.25%`** of `IdeaB8`'s incremental per-node overhead with `0` node changes.
5. **(5) Part M7 (`IdeaS13=true + IdeaS13_Hoist=true` vs `all_off`, `nodes=20000`, `PC20`, built-in eval, `forge-combo29/carbon2/job43/M7_recount.txt`):** **`CUT`** cleanly before Minute 80 (`was_cut: True`, `exit_code: 1` in `forge-combo29/carbon2/job43/M7_fastchess.txt.meta`) after **`729` games** (`364` complete pairs on `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,010,501..2,010,864` plus `1` unpaired game on line `2,010,865`, `0 == 0` non-normal endings, `364 == 364` book-pair matches). Committed recount: **`180 - 216 - 333`** (`47.53%`), pentanomial **`[22, 96, 154, 80, 12]`** (`364` pairs), **`-17.19 +/- 16.48` Elo** (`95% CI [-33.68, -0.71]`, exact `[-33.71, -0.75]`, `nElo -26.40 +/- 25.24`, `LOS 2.02%`) beside `fastchess`'s last `25`-round interval line at `700` games (`Games: 700, Wins: 172, Losses: 211, Draws: 317, Points: 330.5 (47.21 %) | Elo: -19.38 +/- 16.82, nElo: -29.73 +/- 25.74 | Ptnml(0-2): [22, 93, 148, 76, 11]`).

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 6 Elo; a result with the built-in evaluation does not say what a switch does with the PC's net; a time per node on your machine is not the PC's (its evaluation is a net, so B8's share of a node is smaller there).

---

## 1. Step 0 Details (`forge-combo29/carbon2/job43/step0_raw.txt` & `builds.txt`)

- **Tree recipe:** `r15d + v3` (`/tmp/carbon2_job36/tpl_r15d_v3`) + `forge-combo29/carbon2/job41/bundle_grok7.patch.txt` + `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`.
- **Hoist placement in `Worker::search`:** `const int hoisted_s13_prep = (tune::IdeaS13 && tune::IdeaS13_Hoist && is_quiet) ? break_prep_order(board, move) : 0;` is placed **directly before `board.make_move(move, undo)`**, **AFTER** the singular-extension search (`singular_beta` recursive `search(...)` call).
- **Named hashes (`forge-combo29/carbon2/job43/builds.txt` & `step0_raw.txt`):**
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp`: `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp`: `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp`: `2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp`: `5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77` (`0 == 0` CRLF)
  - Patch file `sha256` of `forge-combo29/carbon2/job41/bundle_grok7.patch.txt`: `b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 == b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146`
  - Patch file `sha256` of `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`: `16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 == 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326`
  - Executable `sha256` of `/tmp/carbon2_job43/bld_base_v3/forge`: `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`
  - Executable `sha256` of `/tmp/carbon2_job43/bld_bundle8/forge`: `73b20f3009afe87742b43b022eac127518791dbe85ff52e90eb809633aba6507`
  - Executable `sha256` of `/tmp/carbon2_job40/fastchess`: `a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
  - Opening book `sha256` of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)
- **Column-diff breakdown (`S13 + Hoist` vs `S13` alone, `col 2 = bestmove`, `col 3 = score`, with sample rows from `step0_raw.txt`):**
  - `O` (`200` FENs): `any = 200 / nodes = 200 / bestmove = 47 / score = 192`
    - Sample `bestmove` diff (pos 4): `S13+Hoist_O=(nodes=18248, bestmove=e1g1, score=cp 42)` vs `S13_alone_O=(nodes=32841, bestmove=c1e3, score=cp 20)`
    - Sample `score`-only diff (pos 1): `S13+Hoist_O=(nodes=20032, bestmove=f1e2, score=cp 84)` vs `S13_alone_O=(nodes=12749, bestmove=f1e2, score=cp 97)`
  - `G` (`353` FENs): `any = 342 / nodes = 342 / bestmove = 79 / score = 314` (`equal = 11 == 11`)
    - Sample `bestmove` diff (pos 19): `S13+Hoist_G=(nodes=53021, bestmove=d8d7, score=cp 186)` vs `S13_alone_G=(nodes=73145, bestmove=d8d6, score=cp 214)`
    - Sample `score`-only diff (pos 1): `S13+Hoist_G=(nodes=69963, bestmove=g7g6, score=cp -313)` vs `S13_alone_G=(nodes=45480, bestmove=g7g6, score=cp -280)`

---

## 2. Prediction Audit (`forge-combo29/carbon2/job43/prediction_job43.txt`)

- Prediction file `sha256` of `forge-combo29/carbon2/job43/prediction_job43.txt`: `2ae173252aa235fd81d1f0260446736ba29cf3bd9f76718a33b682144ecd8dea` (committed alone in commit `c4ad2dad7` at `Fri Nov 20 06:10:07 PM UTC 2026`; `M6b` started at `06:10:15 PM UTC`).

| # | Target | Point Prediction | Predicted Range | Observed | Grade |
|---|---|---|---|---|---|
| `(1)` | `M6b` Elo (`3,000`g) & inside `M6`'s 95% CI `[+0.27, +16.64]` | `+9.5` Elo (`YES`) | `[+1.0, +18.0]` Elo (`YES`) | **`+11.47 +/- 8.31` Elo** (`YES`, inside `[+0.27, +16.64]`) | **`TRUE`** |
| `(2)` | `P9` `(IdeaB8 + IdeaB8_Fast) / IdeaB8_alone` time per `1,000` nodes | `0.970` | `[0.948, 0.990]` | **`0.959944`** (`0.534423 / 0.556724`) | **`TRUE`** |
| `(3)` | `M7` Elo (`IdeaS13 + IdeaS13_Hoist` vs `all_off`) | `-3.0` Elo | `[-13.5, +7.5]` Elo | **`-17.19 +/- 16.48` Elo** (`CUT` at `729`g / `364` pairs) | **`FALSE`** (`-17.19 < -13.5`) |

---

## 3. Part M6b, `M6 + M6b` Pooled, and Part M7 (`M6b_recount.txt`, `M6_M6b_pooled_recount.txt`, `M7_recount.txt`)

| Match | Status | Book Lines (`UHO_Lichess_4852_v1.epd`) | Games (Pairs, Unpaired) | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Committed Recount Elo (95% CI) | `fastchess` Own Line |
|---|---|---|---|---|---|---|---|
| `M6` (Job 42 ref) | `COMPLETE` | `2,007,501..2,009,000` (`1500 == 1500`) | `3000` (`1500`, `0`) | `857 - 784 - 1359` | `[68, 334, 631, 391, 76]` | `+8.46 +/- 8.18` (`[+0.27, +16.64]`, `LOS 97.87%`) | `8.46 +/- 8.18`, `[68, 334, 631, 391, 76]` (`3000`g) |
| **`M6b`** | **`COMPLETE`** | **`2,009,001..2,010,500`** (`1500 == 1500`) | **`3000`** (`1500`, `0`) | **`886 - 787 - 1327`** | **`[65, 340, 614, 393, 88]`** | **`+11.47 +/- 8.31`** (`[+3.15, +19.78]`, `LOS 99.66%`) | **`11.47 +/- 8.31`**, `[65, 340, 614, 393, 88]` (`3000`g) |
| **`M6 + M6b` Pooled** | **`COMPLETE`** | **`2,007,501..2,010,500`** (`3000 == 3000`) | **`6000`** (`3000`, `0`) | **`1743 - 1571 - 2686`** | **`[133, 674, 1245, 784, 164]`** | **`+9.96 +/- 5.83`** (`[+4.13, +15.80]`, **`LOS 99.96%`**) | *(pooled from 2 `.tsv` files; no single `fastchess` run)* |
| **`M7`** (`S13+Hoist` vs `all_off`) | **`CUT`** (`Minute 80` safety) | `2,010,501..2,010,864` (`364 == 364` pairs; +1g on `2,010,865`) | **`729`** (`364`, `1`) | **`180 - 216 - 333`** | **`[22, 96, 154, 80, 12]`** | **`-17.19 +/- 16.48`** (`[-33.68, -0.71]`, `LOS 2.02%`) | `-19.38 +/- 16.82`, `[22, 93, 148, 76, 11]` (at `700`g) |

- **Match file hashes:**
  - `M6` per-game TSV `sha256` of `forge-combo29/carbon2/job42/M6_games.tsv`: `ef972bf80fbb795b111bb0afc3ffaf124366dd938793bb370576515106c4716d`
  - `M6b` per-game TSV `sha256` of `forge-combo29/carbon2/job43/M6b_games.tsv`: `1b7b29e18b440b88c594c66aacf5d66297eb0735abc4127fd101ad455e6b8586`
  - `M6b` `fastchess` stdout `sha256` of `forge-combo29/carbon2/job43/M6b_fastchess.txt`: `1c89adff2e1cc5789cadfc40dbdb7d705e9964ca20a714af458e02ae0a5c4823`
  - `M7` per-game TSV `sha256` of `forge-combo29/carbon2/job43/M7_games.tsv`: `90b70d9d50845940b485a508051fd57a70da16ccf8a5b802a5108af1532608c2`
  - `M7` `fastchess` stdout `sha256` of `forge-combo29/carbon2/job43/M7_fastchess.txt`: `9b1989edf64cdb40a7992f01fd4f68fffa3ad4d0cbad28b9f9099c20e8e121e3`

---

## 4. Part P9 Details (`P9a_counter_summary.txt`, `P9b_profile_summary.txt`, `P9cde_summary.txt`, `P9d_timing_summary.txt`)

### 4.1 `P9a`: `IdeaB8` (`078`) Counters Summed Over All `200` `O` Depth-12 Searches (`sum_p9_counters.py`)
- Scratch counter executable `/tmp/carbon2_job43/bld_p9_counter/forge` (`sha256` = `ccf171451cd63b299fc48ddb593cde7f99e5d2dc485d6bdce7c241d96a2dbb67`); raw file `forge-combo29/carbon2/job43/P9a_B8_counters_O_d12.raw.txt` (`sha256` = `5e7aa1d1ebbb7cfd8377ff6f15ba6362a0f40ad749d88711dac19b048949d6c6`), verified `200 == 200` row-equal (`8262696 == 8262696` nodes) to clean `forge-combo29/carbon2/job43/P9_bundle8_only_IdeaB8_O_d12.rows.txt` (`sha256` = `7812ced3a10349fe1af896310b9f412480673afcfcc472fcd045df696ba0b056`).
- **`searches_summed = 200`** (`PASS (200 == 200)`), `total_nodes = 8,262,696`:
  - `ensure_role_threat` total calls: **`35,883,443`** (`4.343 / node`) = `2,514,947` `find_role_threat` runs (`7.01%`) + `33,368,496` 1-slot cache hits (`92.99%`) (`PASS (35883443 == 35883443)`). Of the `2,514,947` `find_role_threat` runs, **`threat.present == true` on only `230,896` (`9.18%`)** (`90.82%` have no cheaper-attacker threat).
  - `quiet_threat_role` total runs: **`4,753,914`** (`0.575 / node`) = `4,688,901` from `threat_role_bonus` (`98.63%`) + `65,013` from `update_threat_role` (`1.37%`) (`PASS (4753914 == 4753914)`). Role counts: `role -1 = 0`, `role 0 = 942,239 (19.82%)`, `role 1 = 41,772 (0.88%)`, `role 2 = 313,536 (6.60%)`, `role 3 = 61,331 (1.29%)`, **`role 4 = 3,395,036 (71.42%)`** (`PASS (4753914 == 4753914)`).
  - `note_threat_swing` total runs: **`4,938,069`** (`0.598 / node`); `gained >= 48` on **`36,831`** (`0.75%`); table updates from swing (non-capture/non-promo with `threat.present`) = **`12,790`** (`0.26%`); all-callers `ThreatRoleHistory` updates = **`65,013`**.

### 4.2 `P9b`: Side-by-Side Top-10 Function Shares (`P9b_profile_summary.txt`, `perf record -e cpu-clock:u -F 4999`, `2x O` d12, `/tmp/carbon2_job43/bld_p9_prof/forge`, `sha256` = `bcefa1d39d373e32433576004fb37c26ce43cd30f9871d0c55f2a760ee267c10`)

| Rank | `IdeaB8` Alone ON (`16,525,392` nodes) | `All OFF` (`16,630,336` nodes) |
|---|---|---|
| 1 | `16.89%` `evaluate_position<false>` | `17.83%` `evaluate_position<false>` |
| 2 | `13.93%` `Worker::search` | `14.58%` `Worker::search` |
| 3 | `10.73%` `nnue::apply_and_evaluate` | `11.15%` `nnue::apply_and_evaluate` |
| 4 | `5.26%` `Board::see_ge` | `5.39%` `Board::see_ge` |
| 5 | `4.80%` `MovePicker::QuietScorer::score` | `4.98%` `MovePicker::pick_best` |
| 6 | `4.58%` `MovePicker::pick_best` | `4.70%` `Worker::corrected_eval` |
| 7 | `4.41%` `Worker::corrected_eval` | `4.02%` `Worker::static_evaluate` |
| 8 | `3.88%` `Worker::static_evaluate` | `4.01%` `MovePicker::QuietScorer::score` |
| 9 | `2.95%` `MovePicker::next` | `3.16%` `Worker::qsearch` |
| 10 | `2.77%` `Worker::qsearch` | `3.15%` `MovePicker::next` |

- `IdeaB8`-specific symbols in the `IdeaB8`-alone profile: `find_role_threat` = **`1.78%`**, `Worker::threat_role_bonus` = **`1.37%`**, `quiet_threat_role` = **`0.52%`**, `Worker::update_threat_role` = **`0.07%`** (plus `+0.79%` caller overhead inside `QuietScorer::score`).

### 4.3 `P9c` & `P9e`: `IdeaB8_Fast` Design, Identity Proofs, and Patch (`P9_B8_fast.patch.txt`)
- **Executable `sha256` of `/tmp/carbon2_job43/bld_bundle9/forge`:** `dd3396801f23390a60f97b8e46255b443a4f851ad969da89d7a59baceb9366d2`.
- **Three node-identical optimizations in `P9_B8_fast.patch.txt` (gated by `tune::IdeaB8 && tune::IdeaB8_Fast`; covers `IdeaB8` (`078`) only):**
  1. **Per-`MovePicker` `QuietScorer` precomputation (`prepare_b8_fast_scorer`):** Resolves the position's threat once per `QuietScorer`; on the `90.82%` of positions with `!present`, `b8_fast_entry == nullptr` skips all per-move calls inside `QuietScorer::score`. On the `9.18%` with `present == true`, pre-scales all 5 role bonuses (`row[0..4] * IdeaB8_Weight / 1024`) once per `MovePicker` and classifies `role` inline using `piece` already loaded in `QuietScorer::score`. *(Note: during development, an initial C++ member-declaration order bug where `std::array<int, 5> b8_fast_scaled{}` was declared after `b8_fast_entry` zeroed `b8_fast_scaled` and failed our `O` node-identity check `8267993 != 8262696`; moving initialization into the constructor body fixed it immediately before any commit.)*
  2. **256-slot direct-mapped per-`Worker` `B8FastEntry` cache (`b8_fast_cache_[key & 255]`, verified by `key`, `occ_w`, `occ_b`, invalidated in `Worker::clear()`):** Prevents child subtrees from evicting a parent ply's threat entry across `MovePicker`, `note_threat_swing`, and `update_quiet_stats`.
  3. **Value-tiered `make_b8_fast_entry` + bitmask `quiet_threat_role_fast`:** Checks `Queen` (`900`) -> `Rook` (`500`) -> `(Knight | Bishop)` (`300`, via a single `pawn_attacks_bb(them, enemy_pawns)` mask since only `Pawn` [`100`] is `< 300`), returning immediately on the dearest/lowest-square victim, and precomputes `between_bb`, `attacker_bb`, and `dearer_enemy_bb` (turning `quiet_threat_role`'s piece-type loop on `71.42%` of calls into a single `(hits & e.dearer_enemy_bb) != 0`).
- **Identity checks (`P9cde_summary.txt`):**
  - All 9 `Idea*` switches off (default and explicit `false`) passed every OFF number (`bench 11 = 312866 == 312866`, `bench 13 = 862329 == 862329`, `perft 5 = 4865609 == 4865609`, `PC20 bench 11 = 278024 == 278024`, `PC20 bench 13 = 587276 == 587276`, `Set A line L = 26741 / 107124743 / d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`, `n[1..60] line L = 8449 / 8482 / 36688357 / b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`, non-`PC20` `HindsightDepth` `bench 13` `862329 == 862329` / `840387 == 840387`).
  - `IdeaB8_Fast=true` (`IdeaB8=false`) vs OFF `O`: `PASS (8315168 == 8315168)`, `PASS (200 == 200)`.
  - `IdeaB8 + IdeaB8_Fast` vs `IdeaB8` alone on `O`: `PASS (8262696 == 8262696)`, `PASS (200 == 200)`.
  - `IdeaB8 + IdeaB8_Fast` vs `IdeaB8` alone on `G`: `PASS (17342378 == 17342378)`, `PASS (353 == 353)`.
  - `IdeaB8 + IdeaB8_Fast` vs `IdeaB8` alone on `Set A line L`: `PASS (25818 == 25818)` records, `PASS (25946 == 25946)` searches, `PASS (105263539 == 105263539)` nodes, `PASS (36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8 == 36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8)` (`record_text` `sha256`).

### 4.4 `P9d`: Part T Times per `1,000` Nodes (`P9d_timing_summary.txt`, Forward `01..05` + Reverse `06..10`, Pinned Core 1, `O` d12, `PC20`)

| Setting | `node_sum` (`200 == 200` pos) | Forward `ms / 1k` | Reverse `ms / 1k` | Paired Mean `ms / 1k` (`us / 1k`) | Ratio vs `all_off` (4-run mean `0.520901`) |
|---|---|---|---|---|---|
| `all_off_1` | `8,315,168` | `0.524107` | `0.514553` | `0.519330` (`519.330` us) | `0.996983` |
| `all_off_2` | `8,315,168` | `0.524907` | `0.520038` | `0.522473` (`522.473` us) | `1.003017` |
| `only_B8` | `8,262,696` | `0.556745` | `0.556703` | **`0.556724`** (`556.724` us) | **`1.068770`** (`+6.88%`) |
| **`B8_and_B8_Fast`** | **`8,262,696`** | **`0.531665`** | **`0.537182`** | **`0.534423`** (`534.423` us) | **`1.025959`** (`+2.60%`) |
| `only_B8b` | `8,483,711` | `0.549360` | `0.560078` | `0.554719` (`554.719` us) | `1.064921` (`+6.49%`) |

- **`(IdeaB8 + IdeaB8_Fast) / (IdeaB8 alone)` = `0.534423 / 0.556724` = `0.959944`** (`62.25%` of `IdeaB8`'s incremental cost removed; `rev/fwd` `all_off` drift = `0.986251`).

---

## 5. Facts, Suspicions, Read and Not Tested, What I Did Not Do, What I Am Not Sure About

### Facts (Measured and Verified in Committed Files)
- Across `6,000` paired fixed-node (`20,000` nodes, `PC20`, built-in eval) games on `UHO_Lichess_4852_v1.epd` lines `2,007,501..2,010,500`, `IdeaB8b + HindsightDepth` (`M6 + M6b` pooled) scored `1743 - 1571 - 2686` (`+9.96 +/- 5.83` Elo, `95% CI [+4.13, +15.80]`, `LOS 99.96%`), with `M6b` independently confirming `M6` (`+11.47 +/- 8.31` Elo vs `+8.46 +/- 8.18` Elo).
- `IdeaS13 + IdeaS13_Hoist` matched the PC's independent node counts on both `O` (`9,069,588`) and `G` (`18,700,461`, `11` equal to `S13` alone), and in `M7` (`CUT` at `729` games / `364` pairs) scored `180 - 216 - 333` (`-17.19 +/- 16.48` Elo, `95% CI [-33.68, -0.71]`).
- On `O` depth 12, `IdeaB8` (`078`) has `threat.present == true` on only `9.18%` (`230,896 / 2,514,947`) of `find_role_threat` misses and returns `role = 4` on `71.42%` (`3,395,036 / 4,753,914`) of `quiet_threat_role` calls. `IdeaB8_Fast` (`P9_B8_fast.patch.txt`) preserves exact node, move, score, and selfgame record identity on `O`, `G`, and `Set A line L` while lowering `(IdeaB8 + IdeaB8_Fast) / (IdeaB8 alone)` time per `1,000` nodes to `0.959944`.

### Suspicions (Apart from Facts)
- **Suspicion 1 (`M7` negative fixed-node Elo):** Because `credit_break_prep` applies only positive bonuses and never applies maluses on failed pawn breaks, hoisting `break_prep_order` before `make_move` turns an ever-growing positive table into frequent `r -= 1` LMR shortenings (`580,757` across `O` d12 in Job 42 `P8c`), spending the `20,000`-node budget shallower at the root.
- **Suspicion 2 (`IdeaB8b` fast path):** Applying the exact same 3 techniques (`QuietScorer` constructor hoist + 256-slot `Worker` cache + value-tiered `King -> Queen -> Rook -> Minor` bitmask threat finder) to `IdeaB8b` (`028`) would likely cut a comparable fraction of `IdeaB8b`'s `+6.49%` built-in-eval node-time overhead without changing a single node.

### Read and Not Tested (Apart from Facts and Suspicions)
- Read `Worker::role_b8b_threat` and `Worker::threat_role_b8b_of` in `src/search.cpp` (`lines 1998-2090`) while scoping `P9c`; kept `IdeaB8_Fast` strictly scoped to `IdeaB8` (`078`) so `IdeaB8_Fast` satisfies `"does nothing unless IdeaB8 is on"` without ambiguity.

### What I Did Not Do
- Did not extend `IdeaB8_Fast` to `IdeaB8b` (`028`); `IdeaB8b` was timed alone in `P9d` as instructed when the variant covers `IdeaB8` only.
- Did not finish all `2,000` games of `M7`: `M7` was cleanly stopped (`CUT`, `was_cut: True`) at `19:18:51 UTC` (`729` games = `364` complete pairs + `1` unpaired) so `M7` and `REPORT_carbon2_job43.md` could be committed and pushed before Minute 80 (`19:22:43 UTC`).
- Did not test with the PC's private NNUE net or on Windows.

### What I Am Not Sure About
- Whether `IdeaB8b + HindsightDepth`'s `+9.96 +/- 5.83` Elo gain with the built-in evaluation transfers to time-controlled games with the PC's NNUE net (though `HindsightDepth`'s ~`+2%` node cost and a `P9`-style fast path for `IdeaB8b` would keep time overhead small, especially under NNUE where search/ordering is a smaller share of node time).
- Whether `M7`'s true 2,000-game fixed-node effect sits closer to `-17` Elo or `-5` Elo given `729`-game `+/- 16.48` Elo bars, though `+7.5` Elo or higher is already strongly disfavored.

---

## 6. Model Name, Timestamps (`stamps.txt`), and Final Pre-Commit `git status --short && ls -R forge-combo29/carbon2/job43`

- **Model name:** `Gemini 4 Carbon`
- **`forge-combo29/carbon2/job43/stamps.txt`:**

```text
job43_claimed: Fri Nov 20 06:02:43 PM UTC 2026 (Minute 80 = +80m from this stamp)
step0_done: Fri Nov 20 06:08:44 PM UTC 2026
partM6b_done: Fri Nov 20 06:35:38 PM UTC 2026
partP9ab_done: Fri Nov 20 06:45:01 PM UTC 2026
partP9_done: Fri Nov 20 07:12:25 PM UTC 2026
partM7_done: Fri Nov 20 07:18:51 PM UTC 2026
```

- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job43` immediately before committing `REPORT_carbon2_job43.md`:**

```text
?? forge-combo29/carbon2/job43/REPORT_carbon2_job43.md
forge-combo29/carbon2/job43:
builds.txt
j43_lib.py
M6b_fastchess.txt
M6b_fastchess.txt.meta
M6b_games.tsv
M6b_recount.txt
M6_M6b_pooled_recount.txt
M7_fastchess.txt
M7_fastchess.txt.meta
M7_games.tsv
M7_recount.txt
P9a_B8_counters_O_d12.raw.txt
P9a_B8_counters_O_d12.raw.txt.meta
P9ab_summary.txt
P9a_counter_summary.txt
P9_B8_fast.patch.txt
P9b_profile_summary.txt
P9_bundle8_only_IdeaB8_O_d12.rows.txt
P9_bundle8_only_IdeaB8_O_d12.rows.txt.meta
P9c_B8_and_B8_Fast_G_d12.rows.txt
P9c_B8_and_B8_Fast_G_d12.rows.txt.meta
P9c_B8_and_B8_Fast_O_d12.rows.txt
P9c_B8_and_B8_Fast_O_d12.rows.txt.meta
P9c_B8_and_B8_Fast_SetA_L.rows.txt
P9c_B8_and_B8_Fast_SetA_L.rows.txt.meta
P9cde_summary.txt
P9c_only_B8_G_d12.rows.txt
P9c_only_B8_G_d12.rows.txt.meta
P9c_only_B8_O_d12.rows.txt
P9c_only_B8_O_d12.rows.txt.meta
P9c_only_B8_SetA_L.rows.txt
P9c_only_B8_SetA_L.rows.txt.meta
P9c_only_IdeaB8_Fast_B8_off_O_d12.rows.txt
P9c_only_IdeaB8_Fast_B8_off_O_d12.rows.txt.meta
P9d_partT_01_fwd_all_off_1.rows.txt
P9d_partT_01_fwd_all_off_1.rows.txt.meta
P9d_partT_02_fwd_all_off_2.rows.txt
P9d_partT_02_fwd_all_off_2.rows.txt.meta
P9d_partT_03_fwd_only_B8.rows.txt
P9d_partT_03_fwd_only_B8.rows.txt.meta
P9d_partT_04_fwd_B8_and_B8_Fast.rows.txt
P9d_partT_04_fwd_B8_and_B8_Fast.rows.txt.meta
P9d_partT_05_fwd_only_B8b.rows.txt
P9d_partT_05_fwd_only_B8b.rows.txt.meta
P9d_partT_06_rev_only_B8b.rows.txt
P9d_partT_06_rev_only_B8b.rows.txt.meta
P9d_partT_07_rev_B8_and_B8_Fast.rows.txt
P9d_partT_07_rev_B8_and_B8_Fast.rows.txt.meta
P9d_partT_08_rev_only_B8.rows.txt
P9d_partT_08_rev_only_B8.rows.txt.meta
P9d_partT_09_rev_all_off_2.rows.txt
P9d_partT_09_rev_all_off_2.rows.txt.meta
P9d_partT_10_rev_all_off_1.rows.txt
P9d_partT_10_rev_all_off_1.rows.txt.meta
P9d_timing_summary.txt
prediction_job43.txt
REPORT_carbon2_job43.md
run_partM.py
run_partP9ab.py
run_partP9cde.py
run_step0.py
stamps.txt
step0_bundle8_only_Hoist_S13_off_G_d12.rows.txt
step0_bundle8_only_Hoist_S13_off_G_d12.rows.txt.meta
step0_bundle8_only_Hoist_S13_off_O_d12.rows.txt
step0_bundle8_only_Hoist_S13_off_O_d12.rows.txt.meta
step0_bundle8_only_IdeaB8b_O_d12.rows.txt
step0_bundle8_only_IdeaB8b_O_d12.rows.txt.meta
step0_bundle8_only_S13_G_d12.rows.txt
step0_bundle8_only_S13_G_d12.rows.txt.meta
step0_bundle8_only_S13_O_d12.rows.txt
step0_bundle8_only_S13_O_d12.rows.txt.meta
step0_bundle8_S13_and_Hoist_G_d12.rows.txt
step0_bundle8_S13_and_Hoist_G_d12.rows.txt.meta
step0_bundle8_S13_and_Hoist_O_d12.rows.txt
step0_bundle8_S13_and_Hoist_O_d12.rows.txt.meta
step0_raw.txt
sum_p9_counters.py
```
