# Carbon2 — Job 44 Report (`REPORT_carbon2_job44.md`)

1. **(1) Step 0 (`forge-combo29/carbon2/job44/step0_raw.txt`):** **`PASS (1 == 1)`**. Tree used: `r15d + v3` (`/tmp/carbon2_job36/tpl_r15d_v3`) + `forge-combo29/carbon2/job41/bundle_grok7.patch.txt` + `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt` + `forge-combo29/carbon2/job43/P9_B8_fast.patch.txt` (`/tmp/carbon2_job44/bld_bundle9/forge`, executable `sha256` = `9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`; per File 44 lines `10–11`, `IdeaB8_Fast` is included in the build and stays `false` everywhere in Job 44). Verified all 4 `r15d + v3` file hashes (`0 == 0` CRLF), plain `r15d + v3` (`/tmp/carbon2_job44/bld_base_v3/forge`, executable `sha256` = `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`), every OFF number (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `PC20 278024 == 278024 / 587276 == 587276`, `Set A line L 26741 == 26741 / 107124743 == 107124743 / d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`, `n[1..60] 8449 == 8449 / 8482 == 8482 / 36688357 == 36688357 / b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`), non-`PC20` `HindsightDepth` `bench 13` (`862329 == 862329` false, `840387 == 840387` true), `IdeaB8b` alone on `O` (`8483711 == 8483711`, `200 == 200`), and `IdeaS13 + IdeaS13_Hoist` (`O` `9069588 == 9069588`, `200 == 200`; `G` `18700461 == 18700461`, `353 == 353`).
2. **(2) Prediction Graded (`forge-combo29/carbon2/job44/prediction_job44.txt`, committed alone in `d8a88803a` at `19:29:35 UTC` before Part L's first search):** **`2` of `3` `TRUE`**.
   - **Item (1) (Part L `O` node-count changes at `go nodes 2000`):** Predicted `194` of `200`, range **`[175, 200]`**. Observed = **`178` of `200`** (inside `[175, 200]`). -> **`TRUE`**.
   - **Item (2) (Part M9 Elo at `nodes=2000` & above/below `M6 + M6b`):** Predicted `+5.5` Elo, range **`[-3.0, +14.0]` Elo**, **`BELOW`** `M6 + M6b` pooled (`+9.96` Elo). Observed = **`+8.69 +/- 8.53` Elo** (inside `[-3.0, +14.0]` and below `+9.96` Elo). -> **`TRUE`**.
   - **Item (3) (Part T2 `B / A` `Set A line L` wall-time ratio):** Predicted `1.065`, range **`[1.020, 1.115]`**. Observed = **`1.137204`** (`> 1.115`: per-node time ratio was `1.082839`, close to `~1.080`, while `B` deterministically played `+4.02%` more records [`27,817` vs `26,741`] and `+5.02%` more nodes [`112,503,041` vs `107,124,743`] on `Set A`; `records/sec` ratio = `0.914732`). -> **`FALSE`**.
3. **(3) Part L Table (`forge-combo29/carbon2/job44/partL_summary.txt`, `O` set = UHO book lines `1..200`, `200 == 200`, `go nodes 2000`, `PC20`, built-in eval):**

| Code | Setting (`L_<setting>_O_n2000.rows.txt`) | `sum_nodes` | Mean Finished Depth | `node_diff` vs `(a)` | `bestmove_diff` vs `(a)` | `score_diff` vs `(a)` | `equal_pos` vs `(a)` |
|---|---|---|---|---|---|---|---|
| `(a)` | `all_off_a` | `283,823` | `5.96` | `0 / 200` | `0 / 200` | `0 / 200` | `200 / 200` |
| `(b)` | `all_off_b` (determinism check) | `283,823` | `5.96` | **`0 / 200`** (`PASS 200 == 200`) | `0 / 200` | `0 / 200` | `200 / 200` |
| **`(c)`** | **`bundle_B8b_HindsightDepth`** | **`281,182`** | `5.93` | **`178 / 200`** | **`19 / 200`** | `60 / 200` | `22 / 200` |
| `(d)` | `only_IdeaB8b` | `279,912` | `5.92` | `125 / 200` | `16 / 200` | `51 / 200` | `75 / 200` |
| `(e)` | `only_HindsightDepth` | `287,214` | `5.99` | `148 / 200` | `2 / 200` | `9 / 200` | `52 / 200` |

4. **(4) Part M9 (`forge-combo29/carbon2/job44/M9_recount.txt`, `IdeaB8b=true + HindsightDepth=true` vs `all_off`, `nodes=2000`, `PC20`, built-in eval, `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` lines `2,011,501..2,013,500`, `4,000` games / `2,000` pairs `COMPLETE`):** Committed recount: **`1440 - 1340 - 1220`** (`51.25%`, `0 == 0` non-normal, `2000 == 2000` book-line pairs), pentanomial **`[195, 407, 716, 467, 215]`**, **`+8.69 +/- 8.53` Elo** (`95% CI [+0.15, +17.22]`, exact `[+0.16, +17.23]`, `nElo +10.97 +/- 10.77`, `LOS 97.71%`) — identical to `fastchess`'s own line (`Games: 4000, Wins: 1440, Losses: 1340, Draws: 1220, Points: 2050.0 (51.25 %) | Elo: 8.69 +/- 8.53, nElo: 10.97 +/- 10.77 | Ptnml(0-2): [195, 407, 716, 467, 215]`). Beat `all_off` (`LOS 97.71%`); whether the two parts add up at `2,000` nodes or whether `nodes=2000` Elo truly differs from `nodes=20000` Elo (`+9.96 +/- 5.83`) is not resolved within `+/- 8.53` Elo.
5. **(5) Part T2 (`forge-combo29/carbon2/job44/partT2_summary.txt`, `Set A line L`, `12` runs `A B A B A B` then `B A B A B A`, pinned core 1, `PC20`, built-in eval):**
   - **Determinism:** Every `A` (`all_off`) run (`6 / 6`) gave `26741 == 26741` records, `107124743 == 107124743` nodes, and `record_text` `sha256` = `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`. Every `B` (`IdeaB8b + HindsightDepth`) run (`6 / 6`) gave `27817 == 27817` records (`1.040238x` `A`), `27939 == 27939` searches, `112503041 == 112503041` nodes (`1.050206x` `A`), and `record_text` `sha256` = **`bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d`**. *(Arm `C` omitted: Job 43's `IdeaB8_Fast` met every identity row on `O`, `G`, and `Set A line L`, and covers `IdeaB8` [`078`] only, not `IdeaB8b` [`028`].)*
   - **Means & Ratios:** `A` mean = `44.5137` s (`600.78` rec/s = `2,162,799.3` rec/hr); `B` mean = `50.6212` s (`549.55` rec/s = `1,978,382.1` rec/hr). **Wall-time `B / A`:** overall = **`1.137204`** (`+13.72%`), forward (`runs 1..6`) = **`1.138074`** (`50.9871 / 44.8012` s), reverse (`runs 7..12`) = **`1.136323`** (`50.2553 / 44.2262` s). **`records/sec` `B / A`:** overall = **`0.914732`** (`-8.53%` positions/hr, i.e., `1.0932x` seconds/record), forward = **`0.914021`** (`545.57 / 596.89` rec/s), reverse = **`0.915434`** (`553.53 / 604.66` rec/s). **Noise line (two `A` means):** `A_fwd = 44.8012` s vs `A_rev = 44.2262` s -> spread = **`0.5750` s (`1.292%` of `A` mean, `A_rev / A_fwd = 0.987166`)**; interleaved `A[1,3,5] = 44.4104` s vs `A[2,4,6] = 44.6170` s -> spread = **`0.2066` s (`0.464%` of `A` mean)**. Implied per-node time ratio `B / A` = **`1.082839`** (`+8.28%`). (Full 12-run table in Section 5 below.)

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; nodes=2000 in fastchess is a hard limit, while the PC's self-play stops when a depth is finished after 2,000 nodes (soft); 4,000 games carry about +/- 5 Elo; with the built-in evaluation a node is cheap, so B8's share of a node's time is larger on your tree than with the PC's net, and Part T2 over-states the cost there.

---

## 1. Step 0 & Named Hashes (`forge-combo29/carbon2/job44/step0_raw.txt` & `builds.txt`)

- **Source & patch hashes:**
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp`: `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp`: `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp`: `2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf` (`0 == 0` CRLF)
  - Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp`: `5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77` (`0 == 0` CRLF)
  - Patch file `sha256` of `forge-combo29/carbon2/job41/bundle_grok7.patch.txt`: `b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 == b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146`
  - Patch file `sha256` of `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`: `16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 == 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326`
  - Patch file `sha256` of `forge-combo29/carbon2/job43/P9_B8_fast.patch.txt`: `bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395 == bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395`
  - Executable `sha256` of `/tmp/carbon2_job44/bld_base_v3/forge`: `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`
  - Executable `sha256` of `/tmp/carbon2_job44/bld_bundle9/forge`: `9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`
  - Executable `sha256` of `/tmp/carbon2_job40/fastchess`: `a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
  - Opening book `sha256` of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)
  - Prediction file `sha256` of `forge-combo29/carbon2/job44/prediction_job44.txt`: `30840da5090f776db1617c4308fdd4cbdea144db29872a5ea5dd50d756746e76`

---

## 2. Prediction Audit (`forge-combo29/carbon2/job44/prediction_job44.txt`)

| # | Target | Point Prediction | Predicted Range | Observed | Grade |
|---|---|---|---|---|---|
| `(1)` | Part L: `O` positions changing node count at `go nodes 2000` (`bundle` vs `all_off`) | `194` of `200` | `[175, 200]` | **`178` of `200`** | **`TRUE`** |
| `(2)` | Part M9: `bundle` Elo at `nodes=2000` (`4,000`g) & above/below `M6 + M6b` (`+9.96` Elo) | `+5.5` Elo (`BELOW`) | `[-3.0, +14.0]` Elo (`BELOW`) | **`+8.69 +/- 8.53` Elo** (`BELOW` `+9.96`) | **`TRUE`** |
| `(3)` | Part T2: `Set A line L` wall time `B / A` (`bundle / all_off`) | `1.065` | `[1.020, 1.115]` | **`1.137204`** (`1.0828x` per node × `1.0502x` nodes) | **`FALSE`** (`> 1.115`) |

---

## 3. Part L Sample Rows (`forge-combo29/carbon2/job44/partL_summary.txt`)

- `O` set verified identical to lines `1..200` of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` (`PASS (200 == 200)`), `set_sha256` (`/tmp/carbon2_job39/first200.fens`) = `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`.
- Sample differing rows against `(a) all_off_a` (`col 2 = bestmove`, `col 3 = score`):
  - **`(c) bundle_B8b_HindsightDepth`:**
    - `bestmove` diff (pos 8): `bundle_B8b_HindsightDepth=(nodes=929, bestmove=f2f4, score=cp 249)` vs `all_off_a=(nodes=1634, bestmove=g1f3, score=cp 50)`
    - `score`-only diff (pos 1): `bundle_B8b_HindsightDepth=(nodes=1928, bestmove=f1e2, score=cp 84)` vs `all_off_a=(nodes=1505, bestmove=f1e2, score=cp 94)`
  - **`(d) only_IdeaB8b`:**
    - `bestmove` diff (pos 8): `only_IdeaB8b=(nodes=929, bestmove=f2f4, score=cp 249)` vs `all_off_a=(nodes=1634, bestmove=g1f3, score=cp 50)`
    - `score`-only diff (pos 1): `only_IdeaB8b=(nodes=1934, bestmove=f1e2, score=cp 84)` vs `all_off_a=(nodes=1505, bestmove=f1e2, score=cp 94)`
  - **`(e) only_HindsightDepth`:**
    - `bestmove` diff (pos 46): `only_HindsightDepth=(nodes=1988, bestmove=d8d4, score=cp -80)` vs `all_off_a=(nodes=1673, bestmove=d8e7, score=cp -90)`
    - `score`-only diff (pos 23): `only_HindsightDepth=(nodes=1980, bestmove=d1h5, score=cp -46)` vs `all_off_a=(nodes=965, bestmove=d1h5, score=cp 29)`

---

## 4. Part M9 Details (`forge-combo29/carbon2/job44/M9_recount.txt` & `M9_fastchess.txt.meta`)

- `M9` per-game TSV `sha256` of `forge-combo29/carbon2/job44/M9_games.tsv`: `489d44955396fb86691e89a2939b7366ddc6863bfc646e5698a114503f2c8a65`
- `M9` `fastchess` stdout `sha256` of `forge-combo29/carbon2/job44/M9_fastchess.txt`: `50ec28a88b9d68ea9053586f92e5c7d79096f747edf91c29c63abfa20ea52d08`
- Checks (`M9_recount.txt`):
  - `M9 non-normal terminations`: `PASS (0 == 0)`
  - `M9 opening FEN pairs matching book slice` (`lines 2,011,501..2,013,500`): `PASS (2000 == 2000)`
  - `M9 finished games vs target`: `PASS (4000 == 4000)`
  - `M9 finished pairs vs target`: `PASS (2000 == 2000)`
  - `M9 recount W / L / D vs fastchess`: `PASS (1440 == 1440)`, `PASS (1340 == 1340)`, `PASS (1220 == 1220)`
  - `M9 recount ptnml vs fastchess`: `PASS ([195, 407, 716, 467, 215] == [195, 407, 716, 467, 215])`
  - `M9 recount Elo / +/-95% vs fastchess`: `PASS (+8.69 == +8.69)`, `PASS (8.53 == 8.53)`

---

## 5. Part T2 Full 12-Run Table & Ratios (`forge-combo29/carbon2/job44/partT2_summary.txt`)

| Run ID | Pass | Arm | Records | Searches | Nodes | Wall `s` | `records / s` | `records / hr` | `record_text` `sha256` |
|---|---|---|---|---|---|---|---|---|---|
| `T2_01_fwd_A_all_off` | `fwd` | `A` | `26,741` | `26,856` | `107,124,743` | `44.7952` | `596.96` | `2,149,061.0` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `T2_02_fwd_B_bundle` | `fwd` | `B` | `27,817` | `27,939` | `112,503,041` | `51.0108` | `545.32` | `1,963,138.0` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_03_fwd_A_all_off` | `fwd` | `A` | `26,741` | `26,856` | `107,124,743` | `45.0423` | `593.69` | `2,137,272.3` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `T2_04_fwd_B_bundle` | `fwd` | `B` | `27,817` | `27,939` | `112,503,041` | `51.1083` | `544.28` | `1,959,392.4` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_05_fwd_A_all_off` | `fwd` | `A` | `26,741` | `26,856` | `107,124,743` | `44.5662` | `600.03` | `2,160,104.9` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `T2_06_fwd_B_bundle` | `fwd` | `B` | `27,817` | `27,939` | `112,503,041` | `50.8422` | `547.12` | `1,969,648.8` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_07_rev_B_bundle` | `rev` | `B` | `27,817` | `27,939` | `112,503,041` | `50.5699` | `550.07` | `1,980,254.6` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_08_rev_A_all_off` | `rev` | `A` | `26,741` | `26,856` | `107,124,743` | `44.3031` | `603.59` | `2,172,930.1` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `T2_09_rev_B_bundle` | `rev` | `B` | `27,817` | `27,939` | `112,503,041` | `49.9192` | `557.24` | `2,006,065.8` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_10_rev_A_all_off` | `rev` | `A` | `26,741` | `26,856` | `107,124,743` | `43.8699` | `609.55` | `2,194,387.1` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `T2_11_rev_B_bundle` | `rev` | `B` | `27,817` | `27,939` | `112,503,041` | `50.2769` | `553.28` | `1,991,793.1` | `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d` |
| `T2_12_rev_A_all_off` | `rev` | `A` | `26,741` | `26,856` | `107,124,743` | `44.5057` | `600.84` | `2,163,040.5` | `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |

- **Summary ratios (`partT2_summary.txt`):**
  - Wall-time `B / A`: overall = **`1.137204`** (`50.6212 / 44.5137` s), forward (`runs 1..6`) = **`1.138074`** (`50.9871 / 44.8012` s), reverse (`runs 7..12`) = **`1.136323`** (`50.2553 / 44.2262` s).
  - Throughput (`records / s`) `B / A`: overall = **`0.914732`** (`549.55 / 600.78` rec/s = `-8.53%`), forward = **`0.914021`** (`545.57 / 596.89` rec/s), reverse = **`0.915434`** (`553.53 / 604.66` rec/s).
  - Noise line (two `A` means): `A_fwd = 44.8012` s vs `A_rev = 44.2262` s -> spread = **`0.5750` s (`1.292%` of `A` mean, `A_rev / A_fwd = 0.987166`)**; interleaved `A[1,3,5] = 44.4104` s vs `A[2,4,6] = 44.6170` s -> spread = **`0.2066` s (`0.464%` of `A` mean)**.

---

## 6. Facts, Suspicions, Read and Not Tested, What I Did Not Do, What I Am Not Sure About

### Facts (Measured and Verified in Committed Files)
- At `go nodes 2000` on `O` (`200` FENs, `PC20`, built-in eval), `all_off` repeated identically on `200 == 200` positions (`sum_nodes = 283,823`). `IdeaB8b + HindsightDepth` changed the last finished iteration's node count on `178 / 200` positions and best move on `19 / 200`; `IdeaB8b` alone changed `125 / 200` node counts and `16 / 200` best moves; `HindsightDepth` alone changed `148 / 200` node counts and `2 / 200` best moves.
- In `M9` (`4,000` games / `2,000` pairs at `nodes=2000`, UHO book lines `2,011,501..2,013,500`, `PC20`, built-in eval), `IdeaB8b + HindsightDepth` beat `all_off` `1440 - 1340 - 1220` (`+8.69 +/- 8.53` Elo, `95% CI [+0.15, +17.22]`, `LOS 97.71%`).
- Across `12` `Set A line L` runs (`A B A B A B`, then `B A B A B A`), every `A` (`all_off`) run produced `26,741` records (`107,124,743` nodes, `sha256` `d5b52710...`) and every `B` (`bundle`) run produced `27,817` records (`112,503,041` nodes, `sha256` `bd9112cd...`), with wall-time ratio `B / A = 1.137204` (`+13.72%`, decomposed into `1.050206x` total nodes × `1.082839x` time per node) and positions-per-second ratio `B / A = 0.914732` (`-8.53%`, i.e., `+9.32%` wall time per training position).

### Suspicions (Apart from Facts)
- **Suspicion 1 (`IdeaB8b` drives most `2,000`-node best-move changes):** Because `HindsightDepth` alone changed only `2 / 200` best moves at `go nodes 2000` while `IdeaB8b` alone changed `16 / 200`, `IdeaB8b`'s quiet-move ordering may account for a larger share of the bundle's `2,000`-node activity than `HindsightDepth` (though `200` root searches do not resolve which arm contributes more Elo across `4,000` full games where `Hash` and `ThreatRoleHistoryB` persist across plies).
- **Suspicion 2 (`IdeaB8b_Fast` would cut most of Part T2's per-record cost):** Of the `+8.28%` per-node time cost on built-in eval, Job 43 `P9d` showed `IdeaB8b` accounts for `~+6.5%` and `HindsightDepth` `~+2.0%`; porting Job 43's 3-part fast path (`QuietScorer` constructor hoist + 256-slot `Worker` cache + value-tiered bitmask threat finder) to `IdeaB8b` (`028`) would likely cut ~60% of `IdeaB8b`'s per-node overhead with zero node changes, and with the PC's NNUE net the percentage overhead per self-play position will be much smaller still.

### Read and Not Tested (Apart from Facts and Suspicions)
- Read `Worker::search` node-limit stopping lines (`src/search.cpp:1545, 1918, 3027-3052, 3154`) in `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp` to confirm how `go nodes 2000` (hard stop, keeping the last finished iteration without emitting a partial `info` line) differs from `selfgame softnodes 2000` (finishes the iteration that crosses `2,000` nodes, capped at `8,000` nodes).

### What I Did Not Do
- Did not add arm `C` in Part T2 because Job 43's `IdeaB8_Fast` covers `IdeaB8` (`078`) only and does not cover `IdeaB8b` (`028`).
- Did not run single-switch `nodes=2000` matches (`IdeaB8b` alone or `HindsightDepth` alone at `nodes=2000`); only the requested bundle match `M9` was played.
- Did not test with the PC's private NNUE net or on Windows.

### What I Am Not Sure About
- Whether the `+4.02%` extra records per 200 attempts (`27,817` vs `26,741`) on `Set A` is a systematic tendency toward slightly longer self-play games under the bundle or specific to `Set A`'s 200 seeds (`records/sec` `0.914732x` vs wall-time `1.137204x` separates per-position throughput from per-game length).
- How much of `M9`'s `+8.69 +/- 8.53` Elo at hard `nodes=2000` carries over to `softnodes 2000` with the PC's NNUE net.

---

## 7. Model Name, Timestamps (`stamps.txt`), and Final Pre-Commit `git status --short && ls -R forge-combo29/carbon2/job44`

- **Model name:** `Gemini 4 Carbon`
- **`forge-combo29/carbon2/job44/stamps.txt`:**

```text
job44_claimed: Fri Nov 20 07:23:33 PM UTC 2026 (Minute 80 = +80m from this stamp)
step0_done: Fri Nov 20 07:28:40 PM UTC 2026
partL_done: Fri Nov 20 07:30:36 PM UTC 2026
partM9_done: Fri Nov 20 07:36:01 PM UTC 2026
partT2_done: Fri Nov 20 07:46:02 PM UTC 2026
```

- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job44` immediately before committing `REPORT_carbon2_job44.md`:**

```text
?? forge-combo29/carbon2/job44/REPORT_carbon2_job44.md
forge-combo29/carbon2/job44:
builds.txt
j44_lib.py
L_all_off_a_O_n2000.rows.txt
L_all_off_a_O_n2000.rows.txt.meta
L_all_off_b_O_n2000.rows.txt
L_all_off_b_O_n2000.rows.txt.meta
L_bundle_B8b_HindsightDepth_O_n2000.rows.txt
L_bundle_B8b_HindsightDepth_O_n2000.rows.txt.meta
L_only_HindsightDepth_O_n2000.rows.txt
L_only_HindsightDepth_O_n2000.rows.txt.meta
L_only_IdeaB8b_O_n2000.rows.txt
L_only_IdeaB8b_O_n2000.rows.txt.meta
M9_fastchess.txt
M9_fastchess.txt.meta
M9_games.tsv
M9_recount.txt
partL_summary.txt
partT2_summary.txt
prediction_job44.txt
REPORT_carbon2_job44.md
run_partL.py
run_partM9.py
run_partT2.py
run_step0.py
stamps.txt
step0_bundle9_only_IdeaB8b_O_d12.rows.txt
step0_bundle9_only_IdeaB8b_O_d12.rows.txt.meta
step0_bundle9_S13_and_Hoist_G_d12.rows.txt
step0_bundle9_S13_and_Hoist_G_d12.rows.txt.meta
step0_bundle9_S13_and_Hoist_O_d12.rows.txt
step0_bundle9_S13_and_Hoist_O_d12.rows.txt.meta
step0_raw.txt
T2_01_fwd_A_all_off_SetA_L.rows.txt
T2_01_fwd_A_all_off_SetA_L.rows.txt.meta
T2_02_fwd_B_bundle_SetA_L.rows.txt
T2_02_fwd_B_bundle_SetA_L.rows.txt.meta
T2_03_fwd_A_all_off_SetA_L.rows.txt
T2_03_fwd_A_all_off_SetA_L.rows.txt.meta
T2_04_fwd_B_bundle_SetA_L.rows.txt
T2_04_fwd_B_bundle_SetA_L.rows.txt.meta
T2_05_fwd_A_all_off_SetA_L.rows.txt
T2_05_fwd_A_all_off_SetA_L.rows.txt.meta
T2_06_fwd_B_bundle_SetA_L.rows.txt
T2_06_fwd_B_bundle_SetA_L.rows.txt.meta
T2_07_rev_B_bundle_SetA_L.rows.txt
T2_07_rev_B_bundle_SetA_L.rows.txt.meta
T2_08_rev_A_all_off_SetA_L.rows.txt
T2_08_rev_A_all_off_SetA_L.rows.txt.meta
T2_09_rev_B_bundle_SetA_L.rows.txt
T2_09_rev_B_bundle_SetA_L.rows.txt.meta
T2_10_rev_A_all_off_SetA_L.rows.txt
T2_10_rev_A_all_off_SetA_L.rows.txt.meta
T2_11_rev_B_bundle_SetA_L.rows.txt
T2_11_rev_B_bundle_SetA_L.rows.txt.meta
T2_12_rev_A_all_off_SetA_L.rows.txt
T2_12_rev_A_all_off_SetA_L.rows.txt.meta
```
