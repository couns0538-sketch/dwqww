# Carbon2 — Job 46 Report (`REPORT_carbon2_job46.md`)

1. **(1) Step 0 (`forge-combo29/carbon2/job46/step0_raw.txt` & `builds.txt`):** **`PASS (1 == 1)`**. Nothing new was built in Job 46: reused Job 44's `bundle9` executable (`/tmp/carbon2_job44/bld_bundle9/forge`, executable `sha256` = `9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `IdeaB8_Fast=false` throughout) and Job 44's plain `r15d + v3` executable (`/tmp/carbon2_job44/bld_base_v3/forge`, executable `sha256` = `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c == 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`). Verified all 4 `r15d + v3` source hashes (`0 == 0` CRLF), no-option `312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, all `PC20` OFF numbers (`278024 == 278024`, `587276 == 587276`, `Set A line L 26741 == 26741 / 107124743 == 107124743 / d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`, `n[1..60] 8449 == 8449 / 8482 == 8482 / 36688357 == 36688357 / b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`, `O` `8315168 == 8315168` on `200 == 200`, `G` `17611204 == 17611204` on `353 == 353`), non-`PC20` `HindsightDepth` `bench 13` (`840387 == 840387` `true`, `862329 == 862329` `false`), `IdeaB8b` alone on `O` (`8483711 == 8483711`, `200 == 200` vs `job41/P7_bundle7_only_B8b_O_d12.rows.txt`), `IdeaS13 + IdeaS13_Hoist` (`O` `9069588 == 9069588`, `200 == 200`; `G` `18700461 == 18700461`, `353 == 353`), and **NEW Step 0 known answers on `O` depth 12 (`PC20`)**:
   - `IdeaS10` alone (`step0_bundle9_only_IdeaS10_O_d12.rows.txt`): sum **`PASS (8314153 == 8314153)`**, position-by-position vs `job41/P7_bundle7_only_S10_O_d12.rows.txt` **`PASS (200 == 200)`**, node diffs vs all off **`PASS (17 == 17)`**, bestmove diffs vs all off **`PASS (2 == 2)`**.
   - `IdeaS13` alone, no hoist (`step0_bundle9_only_IdeaS13_O_d12.rows.txt`): sum **`PASS (8077984 == 8077984)`**, position-by-position vs `job41/P7_bundle7_only_S13_O_d12.rows.txt` **`PASS (200 == 200)`**, node diffs vs all off **`PASS (200 == 200)`**.
2. **(2) Prediction Graded (`forge-combo29/carbon2/job46/prediction_job46.txt`, `sha256` = `fac1773b80328375b58dd9bb48950ca4ffced987b3a2a66a68df6332bd57c5bd`, committed alone in `487d62320` at `20:55:08 UTC` before `M13` liveness at `20:56:58 UTC` and `M13`'s first game at `20:57:03 UTC`):** **`3` of `3` `TRUE`**.
   - **Item (1) (`M13`, bundle vs all off at `nodes=2000` under `S14`):** Predicted `+15.5` Elo, range **`[+9.0, +22.0]` Elo**. Observed = **`+16.21 +/- 5.96` Elo** (inside `[+9.0, +22.0]`). -> **`TRUE`**.
   - **Item (2) (`M11`, `IdeaS10` on top of bundle at `nodes=20000` under `PC20`):** Predicted `-3.0` Elo, range **`[-11.5, +5.5]` Elo**. Observed = **`-0.69 +/- 6.94` Elo** (inside `[-11.5, +5.5]`). -> **`TRUE`**.
   - **Item (3) (`M12`, `IdeaS13` no hoist on top of bundle at `nodes=20000` under `PC20`):** Predicted `-5.5` Elo, range **`[-14.0, +3.0]` Elo**. Observed = **`-0.23 +/- 8.25` Elo** (inside `[-14.0, +3.0]`). -> **`TRUE`**.
3. **(3) Part M13 (`forge-combo29/carbon2/job46/M13_liveness.txt` & `M13_recount.txt`, bundle under `S14` explicit 5 switches `CuckooRep=false, HistRework=0, TtPruneV2=false, CorrHistV2=false, MateAlphaGuard=false`):**
   - **Liveness (`O` depth 12, `200` positions):** Zero `unknown option` / `invalid value` lines (`PASS (0 == 0)` on handshake, liveness, and `fastchess` stdout). **`S14` `all_off` sum = `9,500,069` nodes** vs `PC20` `all_off` sum = `8,315,168` nodes (`+1,184,901` nodes; **`200` of `200` node counts differ**, `60` of `200` best moves differ, `195` of `200` scores differ; `PASS (True == True)`).
   - **Match (`nodes=2000`, book lines `2,015,501..2,019,500`, `8,000` games / `4,000` pairs `COMPLETE`):** **`2960 - 2587 - 2453`** (`52.3313%`, `0 == 0` non-normal, `4000 == 4000` pairs), pentanomial **`[338, 782, 1520, 889, 471]`**, **`+16.21 +/- 5.96` Elo** (`95% CI [+10.26, +22.17]`, `nElo +20.76 +/- 7.61`, `LOS 100.00%`) — identical to `fastchess`'s own line (`Games: 8000, Wins: 2960, Losses: 2587, Draws: 2453, Points: 4186.5 (52.33 %) | Elo: 16.21 +/- 5.96, nElo: 20.76 +/- 7.61 | Ptnml(0-2): [338, 782, 1520, 889, 471]`).
4. **(4) Part M11 (`forge-combo29/carbon2/job46/M11_liveness.txt` & `M11_recount.txt`, `IdeaS10` on top of `IdeaB8b + HindsightDepth`, `PC20`):**
   - **Liveness (`O` depth 12, `PC20`):** `IdeaB8b + HindsightDepth + IdeaS10` sum = **`8,480,966` nodes** vs `IdeaB8b + HindsightDepth` sum = **`8,481,645` nodes** (`-679` nodes; **`12` of `200` node counts differ**, `2` of `200` best moves differ, `7` of `200` scores differ; `PASS (True == True)`).
   - **Match (`nodes=20000`, book lines `2,019,501..2,021,000`, `3,000` games / `1,500` pairs `COMPLETE`):** **`848 - 854 - 1298`** (`49.9000%`, `0 == 0` non-normal, `1500 == 1500` pairs), pentanomial **`[49, 276, 854, 274, 47]`**, **`-0.69 +/- 6.94` Elo** (`95% CI [-7.63, +6.24]`, `nElo -1.25 +/- 12.43`, `LOS 42.22%`) — identical to `fastchess`'s own line (`Games: 3000, Wins: 848, Losses: 854, Draws: 1298, Points: 1497.0 (49.90 %) | Elo: -0.69 +/- 6.94, nElo: -1.25 +/- 12.43 | Ptnml(0-2): [49, 276, 854, 274, 47]`). Not statistically distinguishable from `0` Elo at `3,000` games (`95% CI` spans `[-7.63, +6.24]`).
5. **(5) Part M12 (`forge-combo29/carbon2/job46/M12_liveness.txt` & `M12_recount.txt`, `IdeaS13` [no hoist; `IdeaS13_Hoist=false`] on top of `IdeaB8b + HindsightDepth`, `PC20`):**
   - **Liveness (`O` depth 12, `PC20`):** `IdeaB8b + HindsightDepth + IdeaS13` sum = **`8,598,282` nodes** vs `IdeaB8b + HindsightDepth` sum = **`8,481,645` nodes** (`+116,637` nodes; **`200` of `200` node counts differ**, `48` of `200` best moves differ, `195` of `200` scores differ; `PASS (True == True)`).
   - **Match (`nodes=20000`, book lines `2,021,001..2,022,500`, `3,000` games / `1,500` pairs `COMPLETE`):** **`815 - 817 - 1368`** (`49.9667%`, `0 == 0` non-normal, `1500 == 1500` pairs), pentanomial **`[67, 383, 612, 361, 77]`**, **`-0.23 +/- 8.25` Elo** (`95% CI [-8.48, +8.02]`, `nElo -0.35 +/- 12.43`, `LOS 47.81%`) — identical to `fastchess`'s own line (`Games: 3000, Wins: 815, Losses: 817, Draws: 1368, Points: 1499.0 (49.97 %) | Elo: -0.23 +/- 8.25, nElo: -0.35 +/- 12.43 | Ptnml(0-2): [67, 383, 612, 361, 77]`). Also flat (`-0.23 +/- 8.25` Elo; `0` sits right at the center of `[-8.48, +8.02]`).

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 8,000 games carry about +/- 6 Elo and 3,000 games about +/- 9, so M13 can tell +16 from +9 only roughly and M11 / M12 can say whether an idea clearly hurts on top of the bundle, not how large a small gain is; M13 changes five switches at once, so it cannot say which of them does it.

---

## 1. Named Hashes (`forge-combo29/carbon2/job46/builds.txt`, `step0_raw.txt`, `M13_recount.txt`, `M11_recount.txt`, `M12_recount.txt`)

- Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp`: `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` (`0 == 0` CRLF)
- Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp`: `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` (`0 == 0` CRLF)
- Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp`: `2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf` (`0 == 0` CRLF)
- Source file `sha256` of `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp`: `5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77` (`0 == 0` CRLF)
- Patch file `sha256` of `forge-combo29/carbon2/job41/bundle_grok7.patch.txt`: `b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 == b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146`
- Patch file `sha256` of `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt`: `16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 == 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326`
- Patch file `sha256` of `forge-combo29/carbon2/job43/P9_B8_fast.patch.txt`: `bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395 == bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395`
- Reused plain `r15d + v3` executable `sha256` of `/tmp/carbon2_job44/bld_base_v3/forge`: `09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c == 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`
- Reused `bundle9` executable `sha256` of `/tmp/carbon2_job44/bld_bundle9/forge` (used across Step 0, M13, M11, M12): `9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`
- Official `fastchess` executable `sha256` of `/tmp/carbon2_job40/fastchess`: `a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
- Opening book `sha256` of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)
- `O` set `sha256` of `/tmp/carbon2_job39/sets/first200.fens`: `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (`200` FENs)
- `G` set `sha256` of `/tmp/carbon2_job39/sets/set_G.epd`: `af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d` (`353` FENs)
- Prediction file `sha256` of `forge-combo29/carbon2/job46/prediction_job46.txt`: `fac1773b80328375b58dd9bb48950ca4ffced987b3a2a66a68df6332bd57c5bd`
- `M13` per-game TSV `sha256` of `forge-combo29/carbon2/job46/M13_games.tsv`: `127b5d8432d1ef58a14ddea35e26ddff58eefa0f95376bf05468db1317c2f025`; `fastchess` stdout `sha256` of `forge-combo29/carbon2/job46/M13_fastchess.txt`: `ac5661f728acd31d80f66e63a47e584757dc24b07e9c1d6a264f0c6448066163`
- `M11` per-game TSV `sha256` of `forge-combo29/carbon2/job46/M11_games.tsv`: `3da76d22c3c066e4b535d322b116df506d43fed78db29b4cddc756a503fcf5c4`; `fastchess` stdout `sha256` of `forge-combo29/carbon2/job46/M11_fastchess.txt`: `9a49fd9e03c900a9c272b769649be376b1a55a15e5857939085c9d86ca52ab70`
- `M12` per-game TSV `sha256` of `forge-combo29/carbon2/job46/M12_games.tsv`: `bca63f653593bf60c638f9359fb8b4c4d8b4940128600533419be7745eb9e6c0`; `fastchess` stdout `sha256` of `forge-combo29/carbon2/job46/M12_fastchess.txt`: `8771669207af123b60cc492a42f3f302c88be08176235948d5c2381d420f35ee`

---

## 2. Summary Table Across Liveness & Matches (`M13`, `M11`, `M12`)

### 2a. Liveness Table (`O` depth 12, `200` FENs, `ucinewgame + isready` per search)

| Part | Base Options | Side A Switches (`sum_nodes`) | Side B Switches (`sum_nodes`) | `sum_A - sum_B` | `nodes_diff / 200` | `bestmove_diff / 200` | `score_diff / 200` | Status |
|---|---|---|---|---|---|---|---|---|
| `M13` | `S14` vs `PC20` | `S14 all_off` (`9,500,069`) | `PC20 all_off` (`8,315,168`) | `+1,184,901` | `200` | `60` | `195` | `PASS (True == True)` |
| `M11` | `PC20` | `bundle + IdeaS10` (`8,480,966`) | `bundle` (`8,481,645`) | `-679` | `12` | `2` | `7` | `PASS (True == True)` |
| `M12` | `PC20` | `bundle + IdeaS13` (`8,598,282`) | `bundle` (`8,481,645`) | `+116,637` | `200` | `48` | `195` | `PASS (True == True)` |

### 2b. Match Table (`bundle9` `/tmp/carbon2_job44/bld_bundle9/forge`, built-in evaluation, `-concurrency 4`)

| Match | Setting & Nodes | Book Slice (`UHO_Lichess_4852_v1.epd`) | Games (Pairs) | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Recounted Elo (`95% CI`) | `fastchess` Elo | `LOS` |
|---|---|---|---|---|---|---|---|---|
| **`M13`** | `S14`, `nodes=2000` (`bundle` vs `all_off`) | `2,015,501..2,019,500` | `8,000` (`4,000`) | **`2960 - 2587 - 2453`** (`52.33%`) | `[338, 782, 1520, 889, 471]` | **`+16.21 +/- 5.96`** (`[+10.26, +22.17]`) | `+16.21 +/- 5.96` | `100.00%` |
| **`M11`** | `PC20`, `nodes=20000` (`bundle+S10` vs `bundle`) | `2,019,501..2,021,000` | `3,000` (`1,500`) | **`848 - 854 - 1298`** (`49.90%`) | `[49, 276, 854, 274, 47]` | **`-0.69 +/- 6.94`** (`[-7.63, +6.24]`) | `-0.69 +/- 6.94` | `42.22%` |
| **`M12`** | `PC20`, `nodes=20000` (`bundle+S13` vs `bundle`) | `2,021,001..2,022,500` | `3,000` (`1,500`) | **`815 - 817 - 1368`** (`49.97%`) | `[67, 383, 612, 361, 77]` | **`-0.23 +/- 8.25`** (`[-8.48, +8.02]`) | `-0.23 +/- 8.25` | `47.81%` |

- Every `PASS` check inside `M13_recount.txt`, `M11_recount.txt`, and `M12_recount.txt` passed side by side (`0 == 0` non-normal terminations; `4000 == 4000` / `1500 == 1500` / `1500 == 1500` opening FEN pairs in exact book order; `0 == 0` `unknown option` / `invalid value` lines; W-L-D, pentanomial, Elo, and 95% error identical to `fastchess`'s own line).

---

## 3. Facts, Suspicions (Apart), Read and Not Tested (Apart), What I Did Not Do, What I Am Not Sure About

### Facts (Proven from Committed Files in `forge-combo29/carbon2/job46/`)
1. **Why the Bundle Gained Less Under `PC20` Than Under `S14` (`M13` vs `M9`):** Running the **exact same `bundle9` binary** (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524d...`) at `nodes=2000` with only the five `PC20` search switches (`CuckooRep`, `HistRework`, `TtPruneV2`, `CorrHistV2`, `MateAlphaGuard`) explicitly set to `false / 0` (`S14`) produced **`+16.21 +/- 5.96` Elo** (`[+10.26, +22.17]`, `8,000` games), right in line with the 30-seat Grok `S14` result (`+15.93 +/- 1.06` in `260,000` games) and `+7.52` Elo higher than Job 44's `M9` under `PC20` (`+8.69 +/- 8.53` in `4,000` games). Therefore, the gap between `+16` and `+9` comes from the five `PC20` switches, **not** from the `r15d + v3` tree.
2. **`IdeaS10` on Top of the Bundle (`M11`):** On `O` at depth 12 (`PC20`), adding `IdeaS10` to `IdeaB8b + HindsightDepth` alters node counts on `12` of `200` positions (`8,480,966` vs `8,481,645` = `-679` nodes; vs `17` of `200` alone). Over `3,000` games at `nodes=20000`, `IdeaB8b + HindsightDepth + IdeaS10` vs `IdeaB8b + HindsightDepth` scored `848 - 854 - 1298` (`-0.69 +/- 6.94` Elo, `95% CI [-7.63, +6.24]`, `LOS 42.22%`): no sign of positive synergy, and `WL/DD = 1.28` (`854` `WL+DD` pairs of `1,500`) reflects how infrequently `IdeaS10` diverges games.
3. **`IdeaS13` (No Hoist) on Top of the Bundle (`M12`):** Whereas `IdeaS13` alone lowered `O` depth-12 nodes by `-237,184` (`8,077,984` vs `8,315,168`), adding `IdeaS13` (`IdeaS13_Hoist=false`) on top of `IdeaB8b + HindsightDepth` **increased** `O` depth-12 nodes by **`+116,637`** (`8,598,282` vs `8,481,645`, differing on `200` of `200` positions and `48` best moves). Over `3,000` games at `nodes=20000`, it scored `815 - 817 - 1368` (`-0.23 +/- 8.25` Elo, `95% CI [-8.48, +8.02]`, `LOS 47.81%`).

### Suspicions (Apart from Facts)
1. **Which of the Five `PC20` Switches Compresses the Bundle's Gain:** Among `CuckooRep`, `HistRework 2`, `TtPruneV2`, `CorrHistV2`, and `MateAlphaGuard`, **`HistRework 2`** ("threat-keyed quiet history twin + pawn x material correction") is the prime suspect for overlapping with `IdeaB8b` (`ThreatRoleHistoryB`), while `CorrHistV2` could also slightly interact with `HindsightDepth`'s eval-bounce signal. A single ablation match (`PC20` with *only* `HistRework=0`, or testing `IdeaB8b + IdeaB8b_Fast` vs `HistRework=2` head-to-head at wall clock) would isolate whether `HistRework 2` accounts for most of the `~7` Elo difference and whether `IdeaB8b` complements or partially replaces `HistRework`'s threat-quiet twin.
2. **Why Neither `IdeaS10` Nor `IdeaS13` Lost `-3.5` / `-5.5` Full Points in `3,000` Games on Top of `PC20 + Bundle`:** With `+/- 6.94` and `+/- 8.25` Elo 95% intervals, `-3.5` and `-5.5` Elo both lie well inside `M11` (`[-7.63, +6.24]`) and `M12` (`[-8.48, +8.02]`); additionally, under `PC20 + IdeaB8b`, `IdeaS13`'s fixed ordering weight competes against three active quiet-history tables (`main_history`, `HistRework` threat twin, `ThreatRoleHistoryB`), diluting both its damage and any independent effect while still adding per-node cost (`IdeaS13` without `IdeaS13_Hoist` added `+12.6%` per-node time in Job 42).

### Read and Not Tested (Apart)
- Read File 46's recount of Job 44 (including the note on `partT2_summary.txt` line 7 typing `26856` instead of reading `26867` from the A runs — fixed in all Job 46 scripts so every summary number is read directly from the runs) and the 30-seat Grok `S14` bundle totals (`+15.93` at `2k` nodes in `260k`g, `+16.75` at `20k` in `55.5k`g, `+13.14` at `60k` in `15.4k`g) and Grok-2 solo results for `IdeaS10` (`-3.50` in `80k`g) and `IdeaS13` (`-5.50` in `75k`g); not re-run here beyond `M13`, `M11`, and `M12`.

### What I Did Not Do
- Did not build any new engine executable in Job 46 (reused `/tmp/carbon2_job44/bld_bundle9/forge` and `/tmp/carbon2_job44/bld_base_v3/forge`, verified in Step 0).
- Did not edit any repository engine source file or any previously committed raw file.
- Did not commit any binary, `.pgn`, `.pyc`, profile data, or archive file.
- Did not create any pull request or touch any branch other than `for-fable-and-opus/carbon2-work`.
- Did not decompose `M13`'s five `S14` switches one by one (not requested in File 46).

### What I Am Not Sure About
- How much of the `~7.5` Elo gap between `M13` (`+16.21 +/- 5.96` under `S14`) and `M9` (`+8.69 +/- 8.53` under `PC20`) comes specifically from `HistRework 2` vs `CorrHistV2`, `TtPruneV2`, `CuckooRep`, or `MateAlphaGuard` (and sampling noise between `M13` and `M9`, whose difference `+7.52` has combined 95% CI `+/- 10.40` Elo, though comparing `M13` `+16.21 +/- 5.96` and Grok `+15.93 +/- 1.06` against pooled `PC20` `M6+M6b+M9` `~ +9.5 +/- 4.8` strongly supports genuine overlap).
- Whether `IdeaS10` or `IdeaS13` on top of the bundle is truly `~0` Elo or `-2` to `-4` Elo under `PC20` (`3,000` games cannot resolve effects smaller than `~7–8` Elo, though neither shows evidence of helping on top of the bundle).

---

## 4. Model Name, Timestamps (`stamps.txt`), and Final Pre-Commit `git status` + `ls -R`

- **Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job46/stamps.txt`):**
  - `job46_claimed`: `Fri Nov 20 08:48:51 PM UTC 2026` (Minute 80 hard stop = `22:08:51 UTC`)
  - `step0_done`: `Fri Nov 20 08:54:21 PM UTC 2026`
  - `prediction_job46.txt` (`commit 487d62320`, inline `stamp_utc`): `Fri Nov 20 08:55:08 PM UTC 2026` (committed alone before `M13`'s first game at `20:57:03 UTC`)
  - `partM13_done`: `Fri Nov 20 09:03:26 PM UTC 2026`
  - `partM11_done`: `Fri Nov 20 09:22:19 PM UTC 2026`
  - `partM12_done`: `Fri Nov 20 09:40:55 PM UTC 2026`
- **Output of `git status --short && ls -R forge-combo29/carbon2/job46` immediately before the report commit:**

```text
?? forge-combo29/carbon2/job46/REPORT_carbon2_job46.md
forge-combo29/carbon2/job46:
builds.txt
j46_lib.py
M11_fastchess.txt
M11_fastchess.txt.meta
M11_games.tsv
M11_liveness_bundle_only_O_d12.rows.txt
M11_liveness_bundle_only_O_d12.rows.txt.meta
M11_liveness_bundle_plus_S10_O_d12.rows.txt
M11_liveness_bundle_plus_S10_O_d12.rows.txt.meta
M11_liveness.txt
M11_recount.txt
M12_fastchess.txt
M12_fastchess.txt.meta
M12_games.tsv
M12_liveness_bundle_plus_S13_O_d12.rows.txt
M12_liveness_bundle_plus_S13_O_d12.rows.txt.meta
M12_liveness.txt
M12_recount.txt
M13_fastchess.txt
M13_fastchess.txt.meta
M13_games.tsv
M13_liveness_S14_all_off_O_d12.rows.txt
M13_liveness_S14_all_off_O_d12.rows.txt.meta
M13_liveness.txt
M13_recount.txt
prediction_job46.txt
REPORT_carbon2_job46.md
run_partM11.py
run_partM12.py
run_partM13.py
run_step0.py
stamps.txt
step0_bundle9_all_off_G_d12.rows.txt
step0_bundle9_all_off_G_d12.rows.txt.meta
step0_bundle9_all_off_O_d12.rows.txt
step0_bundle9_all_off_O_d12.rows.txt.meta
step0_bundle9_only_IdeaB8b_O_d12.rows.txt
step0_bundle9_only_IdeaB8b_O_d12.rows.txt.meta
step0_bundle9_only_IdeaS10_O_d12.rows.txt
step0_bundle9_only_IdeaS10_O_d12.rows.txt.meta
step0_bundle9_only_IdeaS13_O_d12.rows.txt
step0_bundle9_only_IdeaS13_O_d12.rows.txt.meta
step0_bundle9_S13_and_Hoist_G_d12.rows.txt
step0_bundle9_S13_and_Hoist_G_d12.rows.txt.meta
step0_bundle9_S13_and_Hoist_O_d12.rows.txt
step0_bundle9_S13_and_Hoist_O_d12.rows.txt.meta
step0_raw.txt
```
