# Carbon2 Job 48 Report: Leave-One-Out Across the Five `PC20` Switches on `IdeaB8b + HindsightDepth` (`2,000` Nodes)

## 1. Step 0 — `bundle9` Pins, Known Answers, and Planted `IdeaB8bb=true` Stop Check

- **Executable reused (identical to Job 46 `M13`):** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Planted misspelt option check (`IdeaB8bb=true`):** `run_epd_depth12_strict` sent `setoption name IdeaB8bb value true` followed by `isready`, read every reply line before `readyok`, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`info string unknown option IdeaB8bb`**
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job48/step0_raw.txt`):**
- `src/search.cpp CRLF count                   : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp): PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)`
- `src/uci.cpp CRLF count                      : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp): PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)`
- `src/board.cpp CRLF count                    : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp): PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)`
- `include/forge/board.hpp CRLF count          : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp): PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)`
- `bundle9 exe sha256(/tmp/carbon2_job44/bld_bundle9/forge): PASS (9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef)`
- `planted IdeaB8bb=true stopped runner via EngineReplyStopError: PASS (True == True)`
- `planted stop marker                         : PASS (unknown option == unknown option)`
- `planted search rows file not written (0 searches run): PASS (False == False)`
- `bundle9 no-option bench 11                  : PASS (312866 == 312866)`
- `bundle9 no-option bench 13                  : PASS (862329 == 862329)`
- `bundle9 no-option perft 5                   : PASS (4865609 == 4865609)`
- `bundle9 PC20 (default off) bench 11         : PASS (278024 == 278024)`
- `bundle9 PC20 (default off) bench 13         : PASS (587276 == 587276)`
- `bundle9 PC20 (explicit 10 false) bench 11   : PASS (278024 == 278024)`
- `bundle9 PC20 (explicit 10 false) bench 13   : PASS (587276 == 587276)`
- `bundle9 PC20 all_off O d12 sum              : PASS (8315168 == 8315168)`
- `bundle9 PC20 all_off O d12 equal vs job46 Step 0 O: PASS (200 == 200)`
- `bundle9 PC20 all_off G d12 sum              : PASS (17611204 == 17611204)`
- `bundle9 PC20 all_off G d12 equal vs job46 Step 0 G: PASS (353 == 353)`
- `bundle9 S14 all_off O d12 sum               : PASS (9500069 == 9500069)`
- `bundle9 S14 all_off O d12 equal vs job46 M13 S14 O: PASS (200 == 200)`
- `book lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (2632036 == 2632036)`
- `book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a)`
- `STEP 0 OVERALL                              : PASS (1 == 1)`

---

## 2. Prediction Graded (`forge-combo29/carbon2/job48/prediction_job48.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `c1d47480b` after Part L (`partL_done` in `stamps.txt`) and before the first game of `M15-0`:

```text
c1d47480b carbon2 job48: commit prediction_job48.txt alone after Part L and before M15 (2026-11-20 23:07:01 +0000)

 forge-combo29/carbon2/job48/prediction_job48.txt | 22 ++++++++++++++++++++++
 1 file changed, 22 insertions(+)
```

- **Per-match Elo predictions (`6 / 6` `TRUE`):**

| Match | Predicted Point | Falsification Range | Observed Elo +/- 95% (`[CI]`) | Grade |
| --- | --- | --- | --- | --- |
| `M15-0` (`PC20 (as sent by the PC)`) | `+9.5` Elo | outside `[+2.5, +16.5]` | **`+11.09 +/- 4.93`** (`[+6.17, +16.02]`) | **`TRUE (HELD)`** (`+2.5 <= +11.09 <= +16.5`) |
| `M15-2` (`L2 (HistRework 0)`) | `+14.5` Elo | outside `[+7.5, +21.5]` | **`+19.10 +/- 4.92`** (`[+14.18, +24.02]`) | **`TRUE (HELD)`** (`+7.5 <= +19.10 <= +21.5`) |
| `M15-4` (`L4 (CorrHistV2 false)`) | `+10.5` Elo | outside `[+3.5, +17.5]` | **`+9.38 +/- 4.92`** (`[+4.46, +14.31]`) | **`TRUE (HELD)`** (`+3.5 <= +9.38 <= +17.5`) |
| `M15-1` (`L1 (CuckooRep false)`) | `+9.5` Elo | outside `[+2.5, +16.5]` | **`+9.76 +/- 4.89`** (`[+4.87, +14.65]`) | **`TRUE (HELD)`** (`+2.5 <= +9.76 <= +16.5`) |
| `M15-3` (`L3 (TtPruneV2 false)`) | `+11.0` Elo | outside `[+4.0, +18.0]` | **`+9.38 +/- 4.91`** (`[+4.47, +14.29]`) | **`TRUE (HELD)`** (`+4.0 <= +9.38 <= +18.0`) |
| `M15-5` (`L5 (MateAlphaGuard false)`) | `+9.5` Elo | outside `[+2.5, +16.5]` | **`+6.78 +/- 4.81`** (`[+1.96, +11.59]`) | **`TRUE (HELD)`** (`+2.5 <= +6.78 <= +16.5`) |

- **Switch-attribution prediction (`TRUE` / `HELD`):**
  - Predicted in `prediction_job48.txt`: **`HistRework`** (`HistRework = 2` in `PC20` vs `HistRework = 0` in `L2`, tested by `M15-2`) takes the primary share of the `S14`-to-`PC20` bundle difference, with falsification if `(a)` `M15-2 - M15-0 <= 0.0` Elo while another leave-one-out match exceeds `M15-0` by `>= +7.0` Elo, or `(b)` `M15-0 >= +14.0` Elo with every `(M15-k - M15-0)` inside `[-3.0, +3.0]` Elo.
  - Observed: `M15-0 = +11.09 +/- 4.93` Elo and **`M15-2 - M15-0 = +8.01 +/- 6.96 [+1.05, +14.97]`** (95% CI strictly above `0.0`), while the other four leave-one-out matches (`M15-4`, `M15-1`, `M15-3`, `M15-5`) are `-1.71 +/- 6.96 [-8.67, +5.25]`, `-1.33 +/- 6.94 [-8.27, +5.61]`, `-1.71 +/- 6.96 [-8.67, +5.25]`, and `-4.32 +/- 6.89 [-11.21, +2.57]` relative to `M15-0`. **Grade: `TRUE` (`True`).**

---

## 3. Part L — Leave-One-Out Liveness of Each `PC20` Switch (`O` `200` + `G` `353` at Depth `12`)

- **Reference (`PC20` all off, Job 46 Step 0 rows):** `O` sum = `8,315,168` (`/agent/repos/dwqww/forge-combo29/carbon2/job46/step0_bundle9_all_off_O_d12.rows.txt`), `G` sum = `17,611,204` (`/agent/repos/dwqww/forge-combo29/carbon2/job46/step0_bundle9_all_off_G_d12.rows.txt`).
- **Whole-set known answer (all 5 switches at `S14` values = `S14` all off on `O`):** `PASS (9500069 == 9500069)`.
- **Dead bases (`equal to PC20 all off on all 553 positions`):** **`none (0 of 5 dead)`**. Live bases played in Part M15: `['L1', 'L2', 'L3', 'L4', 'L5']`.
- **Ten sums and differences vs `PC20` all off (`forge-combo29/carbon2/job48/partL_summary.txt` & `partL_status.json`):**

| Base | Switch Set to `S14` Value | `O` Sum (`200`) | `O` Delta vs `PC20` | `O` Node Diffs | `O` BM Diffs | `O` Score Diffs | `G` Sum (`353`) | `G` Delta vs `PC20` | `G` Node Diffs | `G` BM Diffs | `G` Score Diffs | Equal / `553` | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L1` | `CuckooRep false` | `8,303,790` | `-11,378` | `200/200` | `36/200` | `144/200` | `17,780,473` | `+169,269` | `352/353` | `91/353` | `315/353` | `1/553` | **LIVE** |
| `L2` | `HistRework 0` | `8,658,059` | `+342,891` | `200/200` | `58/200` | `187/200` | `17,155,595` | `-455,609` | `350/353` | `86/353` | `322/353` | `3/553` | **LIVE** |
| `L3` | `TtPruneV2 false` | `9,288,166` | `+972,998` | `200/200` | `57/200` | `193/200` | `18,634,930` | `+1,023,726` | `351/353` | `99/353` | `326/353` | `2/553` | **LIVE** |
| `L4` | `CorrHistV2 false` | `8,311,780` | `-3,388` | `200/200` | `54/200` | `191/200` | `17,236,316` | `-374,888` | `348/353` | `75/353` | `324/353` | `5/553` | **LIVE** |
| `L5` | `MateAlphaGuard false` | `8,315,168` | `+0` | `0/200` | `0/200` | `0/200` | `17,514,976` | `-96,228` | `15/353` | `3/353` | `6/353` | `538/553` | **LIVE** |

---

## 4. Part M15 — Six Leave-One-Out Matches (`2,000` Nodes, `12,000` Games / `6,000` Pairs Each, `72,000` Games Total)

- **Common match settings:** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`), built-in evaluation, `nodes=2000`, `Threads=1`, `Hash=16`, `OwnBook=false`, sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,024,001..2,060,000`, `36,000` pairs), `concurrency=4`. Side A = `IdeaB8b=true, HindsightDepth=true` (all other 8 Idea switches `false`); Side B = all 9 Idea switches and `HindsightDepth` `false`; both sides on the same base.

| Match | Base | UHO Lines | Games | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Bundle Elo +/- 95% (`[CI]`) | Difference vs `M15-0` +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M15-0` | `PC20 (as sent by the PC)` | `2,024,001..2,030,000` | `12,000` | `4328-3945-3727` | `[553, 1231, 2188, 1336, 692]` | **`+11.09 +/- 4.93`** (`[+6.17, +16.02]`) | **`baseline (0.00)`** | `TRUE (pred +9.5, [+2.5, +16.5])` |
| `M15-2` | `L2 (HistRework 0)` | `2,030,001..2,036,000` | `12,000` | `4454-3795-3751` | `[505, 1196, 2159, 1415, 725]` | **`+19.10 +/- 4.92`** (`[+14.18, +24.02]`) | **`+8.01 +/- 6.96 [+1.05, +14.97]`** | `TRUE (pred +14.5, [+7.5, +21.5])` |
| `M15-4` | `L4 (CorrHistV2 false)` | `2,036,001..2,042,000` | `12,000` | `4311-3987-3702` | `[572, 1188, 2283, 1258, 699]` | **`+9.38 +/- 4.92`** (`[+4.46, +14.31]`) | **`-1.71 +/- 6.96 [-8.67, +5.25]`** | `TRUE (pred +10.5, [+3.5, +17.5])` |
| `M15-1` | `L1 (CuckooRep false)` | `2,042,001..2,048,000` | `12,000` | `4272-3935-3793` | `[549, 1228, 2232, 1319, 672]` | **`+9.76 +/- 4.89`** (`[+4.87, +14.65]`) | **`-1.33 +/- 6.94 [-8.27, +5.61]`** | `TRUE (pred +9.5, [+2.5, +16.5])` |
| `M15-3` | `L3 (TtPruneV2 false)` | `2,048,001..2,054,000` | `12,000` | `4311-3987-3702` | `[587, 1168, 2237, 1350, 658]` | **`+9.38 +/- 4.91`** (`[+4.47, +14.29]`) | **`-1.71 +/- 6.96 [-8.67, +5.25]`** | `TRUE (pred +11.0, [+4.0, +18.0])` |
| `M15-5` | `L5 (MateAlphaGuard false)` | `2,054,001..2,060,000` | `12,000` | `4272-4038-3690` | `[542, 1247, 2257, 1343, 611]` | **`+6.78 +/- 4.81`** (`[+1.96, +11.59]`) | **`-4.32 +/- 6.89 [-11.21, +2.57]`** | `TRUE (pred +9.5, [+2.5, +16.5])` |

### `M15-0` — Base `PC20 (as sent by the PC)` (UHO lines `2,024,001..2,030,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `471.091s`, `start_utc`: `Fri Nov 20 11:08:30 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:16:21 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-0_recount.txt`):** `W-L-D = 4328-3945-3727`, pentanomial `[553, 1231, 2188, 1336, 692]`, **`+11.09 +/- 4.93` Elo (`[+6.17, +16.02]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-0_fastchess.txt`):** `Games: 12000, Wins: 4328, Losses: 3945, Draws: 3727, Points: 6191.5 (51.60 %) | Elo: 11.09 +/- 4.93, nElo: 14.01 +/- 6.22 | Ptnml(0-2): [553, 1231, 2188, 1336, 692], WL/DD Ratio: 2.77`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`baseline (0.00)`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-0_games.tsv`):** `sha256 = 822098fe47aca97316cd330da58a14c7952e49fcb413a0e8fff03e7135ed44f1`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-0_fastchess.txt`):** `sha256 = d1c913df9b9d78c4601bf14ae6accc0807801f3299800260a0cd3617b0dd8d78`
- **Command (`M15-0_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2024001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-0.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-0 non-normal terminations               : PASS (0 == 0)`
  - `M15-0 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-0 finished games vs target              : PASS (12000 == 12000)`
  - `M15-0 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-0 recount W vs fastchess                : PASS (4328 == 4328)`
  - `M15-0 recount L vs fastchess                : PASS (3945 == 3945)`
  - `M15-0 recount D vs fastchess                : PASS (3727 == 3727)`
  - `M15-0 recount ptnml vs fastchess            : PASS ([553, 1231, 2188, 1336, 692] == [553, 1231, 2188, 1336, 692])`
  - `M15-0 recount Elo vs fastchess              : PASS (+11.09 == +11.09)`
  - `M15-0 recount +/-95% vs fastchess           : PASS (4.93 == 4.93)`
  - `M15-0 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M15-2` — Base `L2 (HistRework 0)` (UHO lines `2,030,001..2,036,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `467.081s`, `start_utc`: `Fri Nov 20 11:16:25 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:24:12 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-2_recount.txt`):** `W-L-D = 4454-3795-3751`, pentanomial `[505, 1196, 2159, 1415, 725]`, **`+19.10 +/- 4.92` Elo (`[+14.18, +24.02]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-2_fastchess.txt`):** `Games: 12000, Wins: 4454, Losses: 3795, Draws: 3751, Points: 6329.5 (52.75 %) | Elo: 19.10 +/- 4.92, nElo: 24.20 +/- 6.22 | Ptnml(0-2): [505, 1196, 2159, 1415, 725], WL/DD Ratio: 2.79`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`+8.01 +/- 6.96 [+1.05, +14.97]`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-2_games.tsv`):** `sha256 = 8029b6171f6cb5baba0cafda12d0975c1bba5dbea4fa36bc34ee07ac4a837617`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-2_fastchess.txt`):** `sha256 = 32d98ab1c5fbe5f3e55bcafbe9608b51ed1633b52e1f58a8de5cd65778f32747`
- **Command (`M15-2_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L2 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L2 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=0 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2030001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-2.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-2 non-normal terminations               : PASS (0 == 0)`
  - `M15-2 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-2 finished games vs target              : PASS (12000 == 12000)`
  - `M15-2 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-2 recount W vs fastchess                : PASS (4454 == 4454)`
  - `M15-2 recount L vs fastchess                : PASS (3795 == 3795)`
  - `M15-2 recount D vs fastchess                : PASS (3751 == 3751)`
  - `M15-2 recount ptnml vs fastchess            : PASS ([505, 1196, 2159, 1415, 725] == [505, 1196, 2159, 1415, 725])`
  - `M15-2 recount Elo vs fastchess              : PASS (+19.10 == +19.10)`
  - `M15-2 recount +/-95% vs fastchess           : PASS (4.92 == 4.92)`
  - `M15-2 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M15-4` — Base `L4 (CorrHistV2 false)` (UHO lines `2,036,001..2,042,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `474.086s`, `start_utc`: `Fri Nov 20 11:24:15 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:32:09 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-4_recount.txt`):** `W-L-D = 4311-3987-3702`, pentanomial `[572, 1188, 2283, 1258, 699]`, **`+9.38 +/- 4.92` Elo (`[+4.46, +14.31]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-4_fastchess.txt`):** `Games: 12000, Wins: 4311, Losses: 3987, Draws: 3702, Points: 6162.0 (51.35 %) | Elo: 9.38 +/- 4.92, nElo: 11.86 +/- 6.22 | Ptnml(0-2): [572, 1188, 2283, 1258, 699], WL/DD Ratio: 2.64`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`-1.71 +/- 6.96 [-8.67, +5.25]`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-4_games.tsv`):** `sha256 = 605776d9e52af0a11960239f87ac1dc5925c5e010e654906f0e80ceb8e71bbde`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-4_fastchess.txt`):** `sha256 = edf4a12051fe08cffdce67618eaeab1ea56d832d9c81fbd7b7b554b2d9738c45`
- **Command (`M15-4_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L4 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L4 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=false option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2036001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-4.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-4 non-normal terminations               : PASS (0 == 0)`
  - `M15-4 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-4 finished games vs target              : PASS (12000 == 12000)`
  - `M15-4 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-4 recount W vs fastchess                : PASS (4311 == 4311)`
  - `M15-4 recount L vs fastchess                : PASS (3987 == 3987)`
  - `M15-4 recount D vs fastchess                : PASS (3702 == 3702)`
  - `M15-4 recount ptnml vs fastchess            : PASS ([572, 1188, 2283, 1258, 699] == [572, 1188, 2283, 1258, 699])`
  - `M15-4 recount Elo vs fastchess              : PASS (+9.38 == +9.38)`
  - `M15-4 recount +/-95% vs fastchess           : PASS (4.92 == 4.92)`
  - `M15-4 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M15-1` — Base `L1 (CuckooRep false)` (UHO lines `2,042,001..2,048,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `457.082s`, `start_utc`: `Fri Nov 20 11:32:12 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:39:49 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-1_recount.txt`):** `W-L-D = 4272-3935-3793`, pentanomial `[549, 1228, 2232, 1319, 672]`, **`+9.76 +/- 4.89` Elo (`[+4.87, +14.65]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-1_fastchess.txt`):** `Games: 12000, Wins: 4272, Losses: 3935, Draws: 3793, Points: 6168.5 (51.40 %) | Elo: 9.76 +/- 4.89, nElo: 12.41 +/- 6.22 | Ptnml(0-2): [549, 1228, 2232, 1319, 672], WL/DD Ratio: 2.58`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`-1.33 +/- 6.94 [-8.27, +5.61]`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-1_games.tsv`):** `sha256 = 3094122aa83d061f4787d26fb7fb02c98aa897a39405de3d5872fe645b6630cd`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-1_fastchess.txt`):** `sha256 = e8266d70691461e566239ca319709afe8991cd34664d056e8a17befa0af6d827`
- **Command (`M15-1_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L1 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L1 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=false option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2042001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-1.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-1 non-normal terminations               : PASS (0 == 0)`
  - `M15-1 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-1 finished games vs target              : PASS (12000 == 12000)`
  - `M15-1 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-1 recount W vs fastchess                : PASS (4272 == 4272)`
  - `M15-1 recount L vs fastchess                : PASS (3935 == 3935)`
  - `M15-1 recount D vs fastchess                : PASS (3793 == 3793)`
  - `M15-1 recount ptnml vs fastchess            : PASS ([549, 1228, 2232, 1319, 672] == [549, 1228, 2232, 1319, 672])`
  - `M15-1 recount Elo vs fastchess              : PASS (+9.76 == +9.76)`
  - `M15-1 recount +/-95% vs fastchess           : PASS (4.89 == 4.89)`
  - `M15-1 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M15-3` — Base `L3 (TtPruneV2 false)` (UHO lines `2,048,001..2,054,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `475.087s`, `start_utc`: `Fri Nov 20 11:39:52 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:47:47 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-3_recount.txt`):** `W-L-D = 4311-3987-3702`, pentanomial `[587, 1168, 2237, 1350, 658]`, **`+9.38 +/- 4.91` Elo (`[+4.47, +14.29]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-3_fastchess.txt`):** `Games: 12000, Wins: 4311, Losses: 3987, Draws: 3702, Points: 6162.0 (51.35 %) | Elo: 9.38 +/- 4.91, nElo: 11.88 +/- 6.22 | Ptnml(0-2): [587, 1168, 2237, 1350, 658], WL/DD Ratio: 2.78`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`-1.71 +/- 6.96 [-8.67, +5.25]`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-3_games.tsv`):** `sha256 = 2f48ed4610504e6548d89f2db987bce757f95eaebe071f37f4688afc9ba53eab`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-3_fastchess.txt`):** `sha256 = d7514374097b37e6b46f6a24d35b238725f8aa05011dd458ad3cfd7683448cb1`
- **Command (`M15-3_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L3 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L3 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=false option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2048001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-3.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-3 non-normal terminations               : PASS (0 == 0)`
  - `M15-3 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-3 finished games vs target              : PASS (12000 == 12000)`
  - `M15-3 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-3 recount W vs fastchess                : PASS (4311 == 4311)`
  - `M15-3 recount L vs fastchess                : PASS (3987 == 3987)`
  - `M15-3 recount D vs fastchess                : PASS (3702 == 3702)`
  - `M15-3 recount ptnml vs fastchess            : PASS ([587, 1168, 2237, 1350, 658] == [587, 1168, 2237, 1350, 658])`
  - `M15-3 recount Elo vs fastchess              : PASS (+9.38 == +9.38)`
  - `M15-3 recount +/-95% vs fastchess           : PASS (4.91 == 4.91)`
  - `M15-3 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M15-5` — Base `L5 (MateAlphaGuard false)` (UHO lines `2,054,001..2,060,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `472.083s`, `start_utc`: `Fri Nov 20 11:47:50 PM UTC 2026`, `end_utc`: `Fri Nov 20 11:55:42 PM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job48/M15-5_recount.txt`):** `W-L-D = 4272-4038-3690`, pentanomial `[542, 1247, 2257, 1343, 611]`, **`+6.78 +/- 4.81` Elo (`[+1.96, +11.59]`)**
- **Fastchess own line (`forge-combo29/carbon2/job48/M15-5_fastchess.txt`):** `Games: 12000, Wins: 4272, Losses: 4038, Draws: 3690, Points: 6117.0 (50.98 %) | Elo: 6.78 +/- 4.81, nElo: 8.75 +/- 6.22 | Ptnml(0-2): [542, 1247, 2257, 1343, 611], WL/DD Ratio: 3.10`
- **Beside `M15-0` (`+11.09 +/- 4.93`):** **`-4.32 +/- 6.89 [-11.21, +2.57]`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-5_games.tsv`):** `sha256 = 3ef76d5ef4351dd4df35ffa477e413a4510cba4873bdade59c4723fe0aecc46d`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-5_fastchess.txt`):** `sha256 = ea78685bf24515f11e4e3645c3cc5c0f854296022f05ba191c38715964326753`
- **Command (`M15-5_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L5 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L5 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=false option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2054001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M15-5.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M15-5 non-normal terminations               : PASS (0 == 0)`
  - `M15-5 opening FEN pairs matching book slice : PASS (6000 == 6000)`
  - `M15-5 finished games vs target              : PASS (12000 == 12000)`
  - `M15-5 finished pairs vs target              : PASS (6000 == 6000)`
  - `M15-5 recount W vs fastchess                : PASS (4272 == 4272)`
  - `M15-5 recount L vs fastchess                : PASS (4038 == 4038)`
  - `M15-5 recount D vs fastchess                : PASS (3690 == 3690)`
  - `M15-5 recount ptnml vs fastchess            : PASS ([542, 1247, 2257, 1343, 611] == [542, 1247, 2257, 1343, 611])`
  - `M15-5 recount Elo vs fastchess              : PASS (+6.78 == +6.78)`
  - `M15-5 recount +/-95% vs fastchess           : PASS (4.81 == 4.81)`
  - `M15-5 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; 12,000 games carry about +/- 5 Elo and a difference of
two matches about +/- 7, so a switch that takes 3 or 4 Elo of the gain cannot be told from none; leave-one-out sees
one switch at a time (if two switches each take part of the gain, each shows only its part); 2,000 nodes only (the
PC20 gain was the same at 20,000 in M6 + M6b).

---

## Facts

1. **All Step 0 pins, known answers, and the planted stop check passed on `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`):** No-option `bench 11 = 312,866`, `bench 13 = 862,329`, `perft 5 = 4,865,609`; `PC20` `bench 11 = 278,024`, `bench 13 = 587,276`; `PC20` all off `O = 8,315,168` (`200/200` position-by-position equal to Job 46 Step 0) and `G = 17,611,204` (`353/353` equal); `S14` all off `O = 9,500,069` (`200/200` equal to Job 46 `M13` liveness); and the planted `IdeaB8bb=true` check stopped the runner immediately before any search on `info string unknown option IdeaB8bb`.
2. **All five `PC20` switches are live on `O + G` at depth 12 (`0` of `5` bases dead):** `L1` (`CuckooRep false`), `L2` (`HistRework 0`), `L3` (`TtPruneV2 false`), and `L4` (`CorrHistV2 false`) change all `200/200` `O` node counts and `348..352` of `353` `G` node counts (`36..58` `O` best moves and `75..99` `G` best moves). `L5` (`MateAlphaGuard false`) equals `PC20` all off on all `200/200` `O` positions (`8,315,168 == 8,315,168`) and `338/353` `G` positions (`538/553` total), changing `15/353` `G` node counts and `3/353` `G` best moves (`G = 17,514,976`, `-96,228` nodes).
3. **Under full `PC20` at `nodes=2000` (`M15-0`, `12,000` games, lines `2,024,001..2,030,000`), `IdeaB8b + HindsightDepth` gains `+11.09 +/- 4.93` Elo (`[+6.17, +16.02]`) over `PC20` all off.** Every match in `M15-0..M15-5` has its own 95% confidence interval strictly above `0` Elo (`0` unpaired games, `0` non-normal endings, `6,000 == 6,000` opening pairs verified per match, `0` fastchess error/unknown/invalid/illegal lines).
4. **Setting `HistRework = 0` alone (`L2`, `M15-2`) increases the bundle's `2,000`-node gain over its base by `+8.01 +/- 6.96 [+1.05, +14.97]` Elo (`excl_zero = ['M15-2']`):** In `M15-2` (`12,000` games, lines `2,030,001..2,036,000`), `IdeaB8b + HindsightDepth` scores `4454-3795-3751`, pentanomial `[505, 1196, 2159, 1415, 725]`, **`+19.10 +/- 4.92` Elo (`[+14.18, +24.02]`)**. The difference `M15-2 - M15-0 = +8.01 +/- 6.96 [+1.05, +14.97]` has a 95% confidence interval (`[+1.05, +14.97]`) that excludes `0`.
5. **For the other four switches (`['M15-4', 'M15-1', 'M15-3', 'M15-5']`), none of the differences to `M15-0` excludes `0` at 95% confidence:** `M15-4` (`CorrHistV2 false`) gives `+9.38 +/- 4.92` (`-1.71 +/- 6.96 [-8.67, +5.25]` vs `M15-0`), `M15-1` (`CuckooRep false`) gives `+9.76 +/- 4.89` (`-1.33 +/- 6.94 [-8.27, +5.61]`), `M15-3` (`TtPruneV2 false`) gives `+9.38 +/- 4.91` (`-1.71 +/- 6.96 [-8.67, +5.25]`), and `M15-5` (`MateAlphaGuard false`) gives `+6.78 +/- 4.81` (`-4.32 +/- 6.89 [-11.21, +2.57]`).

---

## Suspicions

1. **`HistRework = 2` appears to account for essentially all of the `S14`-vs-`PC20` compression of the `IdeaB8b + HindsightDepth` bundle at `2,000` nodes:** At `nodes=2000` with built-in evaluation on `bundle9`, `M15-2` (`HistRework 0`, other four `PC20` switches on) gives `+19.10 +/- 4.92` Elo, compared with `+16.21 +/- 5.96` Elo (`[+10.26, +22.17]`, `2960 - 2587 - 2453` in `8,000` games) in Job 46 `M13` (`S14`, all five `PC20` switches off); their difference `M15-2 - M13 = +2.89 +/- 7.73` Elo (`[-4.84, +10.62]`) crosses `0`, as does `M13 - M15-0 = +5.12 +/- 7.73` Elo (`[-2.62, +12.85]`) and `M15-0 - M9 = +2.40 +/- 9.85` Elo (`[-7.45, +12.25]`, where Job 44 `M9` at `nodes=2000` gave `+8.69 +/- 8.53`). (Quoted apart at `nodes=20000` under `PC20`: Job 42 `M6` gave `+8.46 +/- 8.18` and Job 43 `M6b` gave `+11.47 +/- 8.31`.)
2. **The negative point differences on `L1`, `L3`, `L4`, and especially `L5` (`M15-5 - M15-0 = -4.32 +/- 6.89 [-11.21, +2.57]`) are likely book-slice / sampling noise rather than genuine synergy between `MateAlphaGuard` and the bundle:** In Part L, `MateAlphaGuard false` (`L5`) was identical to `PC20` all off on `538` of `553` `O + G` positions (`0/200` on `O` and `15/353` on `G`), so `MateAlphaGuard` alters very few searches outside mate-distance alpha windows; a `-4.32` swing on a `+/- 6.89` 95% half-width (`z = -1.23`) is well within normal variance across 6 comparisons.
3. **Why `HistRework = 2` overlaps `IdeaB8b` rather than `HindsightDepth`:** Because `HistRework = 2` replaces `3/4` (`75%`) of the butterfly quiet-history term with `LesserThreatHistory` (`[side][from_attacked_by_lesser][to_attacked_by_lesser][from][to]`), quiet moves that evacuate a piece attacked by a cheaper enemy piece already get a dedicated history bucket in `PC20` before `IdeaB8b`'s role-1 ("step away") bucket in `role_b8b_history_` is added, leaving mainly `IdeaB8b`'s non-evacuation roles (blocking a slider, attacking the attacker, counter-attacking a dearer enemy piece) and `IdeaB8b`'s static-eval swing bonus (`note_role_b8b_swing`) as non-redundant signal under `PC20`.

---

## Read and Not Tested

1. **`HistRework` spin levels `1..3` in `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/b4.hpp` (`lines 20–66`) and `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp` (`lines 1446–1502`, `1612–1655`, `1744`):**
   - `HistRework` (`0..3`, `PC20` value `2`) simultaneously controls **two** mechanisms via `level`:
     1. **Quiet-move history blend (`src/search.cpp:1612–1616`, `b4.hpp:27–28, 65–67`):** `threat_quarters(level) = clamp_level(level) + 1`, blending `(plain * (4 - q) + twin * q) / 4` from `rework_history_` (`LesserThreatHistory`), so `HistRework = 1, 2, 3` takes `50%`, `75%`, `100%` of the butterfly term from the lesser-threat twin (`0%` at `HistRework = 0`).
     2. **Pawn x non-pawn-material `joint_correction_` (`src/search.cpp:1446–1459, 1496–1502`, `b4.hpp:29–30, 71–75`):** `joint_weight(level) = 25 * clamp_level(level) + 25` (`50%`, `75%`, `100%` for `level = 1, 2, 3`, updated with self-damping `b4::gravity`).
   - We did **not** test whether the `+8.01 +/- 6.96 [+1.05, +14.97]` Elo interaction in `M15-2` comes from `LesserThreatHistory` (the `3/4` quiet-history twin overlapping `IdeaB8b` in `forge-combo29/carbon2/job41/bundle_grok7.patch.txt:615–736`) or from `joint_correction_`, nor did we test `HistRework = 1` (`50%` blend / `50%` joint weight) or `bundle_on(HistRework=0 or 1)` directly against `bundle_on(PC20: HistRework=2)`.
2. **Absolute strength of `bundle_on_L2` vs `bundle_on_PC20`:** `M15-2` measured `bundle_on_L2` against `all_off_L2` (`+19.10 +/- 4.92`), not `bundle_on_L2` against `bundle_on_PC20`. Because `HistRework = 2` was adopted into `PC20` for its own positive Elo over `HistRework = 0`, dropping `HistRework` to `0` would give back `HistRework = 2`'s standalone contribution on `all_off` unless `IdeaB8b + HindsightDepth` more than replaces it (or unless retuning `HistRework = 1` or `IdeaB8b_Weight` preserves both gains).

---

## What I Did Not Do

- Did **not** build any new binary in Job 48 (reused `/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, as instructed in `FABLE_TO_carbon2_48.md`).
- Did **not** skip any of `M15-1..M15-5` because `0` of `5` bases were dead in Part L (`L5` differed on `15/353` `G` positions).
- Did **not** run `20,000`-node leave-one-out matches, pairwise leave-two-out matches, `HistRework = 1` / `HistRework = 3` retuning matches, or direct `bundle_on_L2` vs `bundle_on_PC20` matches (not in Job 48's scope).
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **Exact size of `HistRework = 2`'s overlap with the bundle (`+8.01 +/- 6.96 [+1.05, +14.97]` Elo):** While `M15-2 - M15-0` excludes `0` at 95% confidence (`z = +2.25`), its `+/- 6.96` half-width spans from `+1.05` to `+14.97` Elo, and `M15-2` was selected as our pre-registered primary candidate out of 5 switches. Whether the true compression under built-in eval is closer to `+5.12 +/- 7.73` Elo (`M13 +16.21` minus `M15-0 +11.09`) or `+8.01 +/- 6.96` Elo (`M15-2 - M15-0`) cannot be pinned tighter than `+/- 7` Elo without more games or common-opening pairing.
2. **Whether `TtPruneV2`, `CorrHistV2`, `CuckooRep`, or `MateAlphaGuard` takes `2–4` Elo in either direction:** At `+/- 6.96` Elo for a two-match difference, a `3` or `4` Elo interaction on any of the other four switches cannot be distinguished from `0`.
3. **Whether `IdeaB8b` alone or `HindsightDepth` alone drives the `HistRework` overlap, and how the PC's NNUE net changes it:** All `M15` matches tested the `IdeaB8b + HindsightDepth` bundle together with built-in evaluation on Linux.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job48/builds.txt`)

```text
=== JOB 48 BUILDS.TXT ===
1. r15d + v3 source tree: /tmp/carbon2_job36/tpl_r15d_v3
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77

2. Bundle9 executable (same as Job 46 M13): /tmp/carbon2_job44/bld_bundle9/forge
   provenance = reused /tmp/carbon2_job44/bld_bundle9/forge with matching sha256
   exe sha256(/tmp/carbon2_job44/bld_bundle9/forge) = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef
   id_name = id name Chess Engine Forge 6.4.24 candidate
   patch 1 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/bundle_grok7.patch.txt) = b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 (expected b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146)
   patch 2 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt) = 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 (expected 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326)
   patch 3 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job43/P9_B8_fast.patch.txt) = bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395 (expected bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395)

3. Official fastchess executable: /tmp/carbon2_job40/fastchess
   git_commit(/tmp/carbon2_job40/fastchess_repo) = d6e3a7a71f8437a39836856ae78a3dcdc9bf934c
   exe sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007

4. Official opening book: /tmp/carbon2_job40/UHO_Lichess_4852_v1.epd
   lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 2632036
   book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
```

### Row File Hashes (`forge-combo29/carbon2/job48/*.rows.txt`)

- Step 0 bundle9 PC20 all_off O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/step0_bundle9_PC20_all_off_O_d12.rows.txt`): `467d7a8cc6c2efa2e41f4d7fef047147abc12738755cacd5537021909a63d1e3`
- Step 0 bundle9 PC20 all_off G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/step0_bundle9_PC20_all_off_G_d12.rows.txt`): `911707ffe231d564533d1eb34550beb6b4ea9c6b9ddfd24a33f9dc3a16e7095e`
- Step 0 bundle9 S14 all_off O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/step0_bundle9_S14_all_off_O_d12.rows.txt`): `c41946a642b8c121d28fa317b3595963f33fb805122af356b504b1f1e9e665a0`
- Part L L1 (CuckooRep false) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L1_all_off_O_d12.rows.txt`): `33e87f9de7bb0a8d23666dd57f063bff1320d5d5d81a5bc8b07e2a8bbfa2081e`
- Part L L1 (CuckooRep false) G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L1_all_off_G_d12.rows.txt`): `36c0e0647790535f5f4cb615a1182fcf141d93b00c62176d219f3bb8937441d0`
- Part L L2 (HistRework 0) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L2_all_off_O_d12.rows.txt`): `1993e5cac134e4bf4970a8635a6b94133c4276fdb5fcf38b78e31ec12161360a`
- Part L L2 (HistRework 0) G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L2_all_off_G_d12.rows.txt`): `ef0e7bd17818906fdeeff56cc51b553a5f040f5a0d4f3da1f56546ede8a83d6b`
- Part L L3 (TtPruneV2 false) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L3_all_off_O_d12.rows.txt`): `9dc44eb59184de4e5a89e6a954e5eb6b40288b8adbc81fdbcb275122dce93eec`
- Part L L3 (TtPruneV2 false) G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L3_all_off_G_d12.rows.txt`): `a9ec9422ac016cd6482b30daa12c661a721b045475d9949c7dca2b4ed64241da`
- Part L L4 (CorrHistV2 false) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L4_all_off_O_d12.rows.txt`): `4ccea97da95c625becd31ebe6f6e617d283591e886ddc3cbbb257743af9b300f`
- Part L L4 (CorrHistV2 false) G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L4_all_off_G_d12.rows.txt`): `712f4437f2e43e0920e90fd1fb20e4c3b2bdd7fac936b3c6e928169a6003438e`
- Part L L5 (MateAlphaGuard false) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L5_all_off_O_d12.rows.txt`): `467d7a8cc6c2efa2e41f4d7fef047147abc12738755cacd5537021909a63d1e3`
- Part L L5 (MateAlphaGuard false) G d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job48/partL_L5_all_off_G_d12.rows.txt`): `ca4c5255ebe7aeeaf7458b6e8dff45a0773dba2b9f0ffc1024244a07abb42df1`

### UTC Timestamps (`forge-combo29/carbon2/job48/stamps.txt`)

```text
job48_claimed: Fri Nov 20 11:01:20 PM UTC 2026
step0_done: Fri Nov 20 11:05:39 PM UTC 2026
partL_done: Fri Nov 20 11:06:21 PM UTC 2026
prediction_committed: Fri Nov 20 11:07:01 PM UTC 2026
M15-0_done: Fri Nov 20 11:16:22 PM UTC 2026
M15-2_done: Fri Nov 20 11:24:13 PM UTC 2026
M15-4_done: Fri Nov 20 11:32:10 PM UTC 2026
M15-1_done: Fri Nov 20 11:39:50 PM UTC 2026
M15-3_done: Fri Nov 20 11:47:48 PM UTC 2026
M15-5_done: Fri Nov 20 11:55:43 PM UTC 2026
report_done: Sat Nov 21 12:06:03 AM UTC 2026
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job48`)

```text
 M forge-combo29/carbon2/job48/stamps.txt
?? forge-combo29/carbon2/job48/REPORT_carbon2_job48.md
?? forge-combo29/carbon2/job48/build_report.py
forge-combo29/carbon2/job48:
build_report.py
builds.txt
j48_lib.py
M15-0_fastchess.txt
M15-0_fastchess.txt.meta
M15-0_games.tsv
M15-0_recount.txt
M15-1_fastchess.txt
M15-1_fastchess.txt.meta
M15-1_games.tsv
M15-1_recount.txt
M15-2_fastchess.txt
M15-2_fastchess.txt.meta
M15-2_games.tsv
M15-2_recount.txt
M15-3_fastchess.txt
M15-3_fastchess.txt.meta
M15-3_games.tsv
M15-3_recount.txt
M15-4_fastchess.txt
M15-4_fastchess.txt.meta
M15-4_games.tsv
M15-4_recount.txt
M15-5_fastchess.txt
M15-5_fastchess.txt.meta
M15-5_games.tsv
M15-5_recount.txt
M15_results.json
M15_summary.txt
partL_L1_all_off_G_d12.rows.txt
partL_L1_all_off_G_d12.rows.txt.meta
partL_L1_all_off_O_d12.rows.txt
partL_L1_all_off_O_d12.rows.txt.meta
partL_L2_all_off_G_d12.rows.txt
partL_L2_all_off_G_d12.rows.txt.meta
partL_L2_all_off_O_d12.rows.txt
partL_L2_all_off_O_d12.rows.txt.meta
partL_L3_all_off_G_d12.rows.txt
partL_L3_all_off_G_d12.rows.txt.meta
partL_L3_all_off_O_d12.rows.txt
partL_L3_all_off_O_d12.rows.txt.meta
partL_L4_all_off_G_d12.rows.txt
partL_L4_all_off_G_d12.rows.txt.meta
partL_L4_all_off_O_d12.rows.txt
partL_L4_all_off_O_d12.rows.txt.meta
partL_L5_all_off_G_d12.rows.txt
partL_L5_all_off_G_d12.rows.txt.meta
partL_L5_all_off_O_d12.rows.txt
partL_L5_all_off_O_d12.rows.txt.meta
partL_status.json
partL_summary.txt
prediction_job48.txt
REPORT_carbon2_job48.md
run_partL.py
run_partM15.py
run_step0.py
stamps.txt
step0_bundle9_PC20_all_off_G_d12.rows.txt
step0_bundle9_PC20_all_off_G_d12.rows.txt.meta
step0_bundle9_PC20_all_off_O_d12.rows.txt
step0_bundle9_PC20_all_off_O_d12.rows.txt.meta
step0_bundle9_S14_all_off_O_d12.rows.txt
step0_bundle9_S14_all_off_O_d12.rows.txt.meta
step0_raw.txt
```

---

## Model Name

`Gemini 4 Carbon`
