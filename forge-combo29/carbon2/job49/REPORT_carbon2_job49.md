# Carbon2 Job 49 Report: Switch `k* = 2` (`HistRework 0` vs `PC20`'s `HistRework 2`), With and Without `IdeaB8b + HindsightDepth` (`2,000` and `20,000` Nodes)

## 1. Step 0 — `bundle9` Pins, `PC20` & `L2` Known Answers, Planted `HistReworkk=0` Stop Check, and `K4` Equivalence

- **Executable reused (identical to Jobs 46 & 48):** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Planted misspelt option check (`HistReworkk=0`):** `run_epd_depth12_strict` sent `setoption name HistReworkk value 0` followed by `isready`, read every reply line before `readyok`, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`info string unknown option HistReworkk`**
- **File 49 one-line bonus check (`lines 38–40`):** On `/tmp/carbon2_job47/bld_bundle11_k4b/forge` (`PC20`), `IdeaK4=true, IdeaK4_Shrink=32, IdeaK4b=false` sums to `7,491,020` on `O` at depth `12` and equals Job 47 `P11(d)` (`IdeaK4b=true` alone) on `200 == 200` positions.
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job49/step0_raw.txt`):**
- `src/search.cpp CRLF count                   : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp): PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)`
- `src/uci.cpp CRLF count                      : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp): PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)`
- `src/board.cpp CRLF count                    : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp): PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)`
- `include/forge/board.hpp CRLF count          : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp): PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)`
- `bundle9 exe sha256(/tmp/carbon2_job44/bld_bundle9/forge): PASS (9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef)`
- `planted HistReworkk=0 stopped runner via EngineReplyStopError: PASS (True == True)`
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
- `bundle9 PC20 all_off O d12 nodes+bestmove equal vs job46 Step 0 O: PASS (200 == 200)`
- `bundle9 PC20 all_off O d12 full-row equal vs job46 Step 0 O: PASS (200 == 200)`
- `bundle9 L2 all_off O d12 sum vs job48 Part L: PASS (8658059 == 8658059)`
- `bundle9 L2 all_off O d12 nodes+bestmove equal vs job48 Part L: PASS (200 == 200)`
- `bundle9 L2 all_off O d12 full-row equal vs job48 Part L: PASS (200 == 200)`
- `bundle11 IdeaK4(Shrink=32) O d12 sum vs job47 P11(d) IdeaK4b: PASS (7491020 == 7491020)`
- `bundle11 IdeaK4(Shrink=32) O d12 position-by-position equal vs P11(d): PASS (200 == 200)`
- `book lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (2632036 == 2632036)`
- `book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a)`
- `STEP 0 OVERALL                           : PASS (1 == 1)`

---

## 2. Selection of `k*` From Committed Job 48 Numbers (`forge-combo29/carbon2/job49/kstar.txt`)

- **Committed before Step 0 and before `prediction_job49.txt` (`f1f1921cf`):**
  - **`k* = 2`**
  - **Base `L_k*` in words:** `L2 (HistRework 0): PC20 with that ONE switch set to its S14 value (HistRework = 0 instead of PC20's HistRework = 2), every other PC20 option unchanged.`
  - **Baseline `M15-0`:** `+11.09 +/- 4.93` Elo (`forge-combo29/carbon2/job48/M15_summary.txt:12`).

| `k` | Base `L_k` | Job 48 Part L Status (`file:line`) | Job 48 `M15-k` Status (`Elo`) | `D_k = Elo(M15-k) - Elo(M15-0)` (`file:line`) | Selected `k*`? |
| --- | --- | --- | --- | --- | --- |
| `1` | `L1` (`CuckooRep false`) | `LIVE` (`forge-combo29/carbon2/job48/partL_summary.txt:12`) | `COMPLETE` (`+9.76`) | **`-1.33 +/- 6.94 [-8.27, +5.61]`** (`forge-combo29/carbon2/job48/M15_summary.txt:15`) | no |
| `2` | `L2` (`HistRework 0`) | `LIVE` (`forge-combo29/carbon2/job48/partL_summary.txt:13`) | `COMPLETE` (`+19.10`) | **`+8.01 +/- 6.96 [+1.05, +14.97]`** (`forge-combo29/carbon2/job48/M15_summary.txt:13`) | **YES (`k* = 2`)** |
| `3` | `L3` (`TtPruneV2 false`) | `LIVE` (`forge-combo29/carbon2/job48/partL_summary.txt:14`) | `COMPLETE` (`+9.38`) | **`-1.71 +/- 6.96 [-8.67, +5.25]`** (`forge-combo29/carbon2/job48/M15_summary.txt:16`) | no |
| `4` | `L4` (`CorrHistV2 false`) | `LIVE` (`forge-combo29/carbon2/job48/partL_summary.txt:15`) | `COMPLETE` (`+9.38`) | **`-1.71 +/- 6.96 [-8.67, +5.25]`** (`forge-combo29/carbon2/job48/M15_summary.txt:14`) | no |
| `5` | `L5` (`MateAlphaGuard false`) | `LIVE` (`forge-combo29/carbon2/job48/partL_summary.txt:16`) | `COMPLETE` (`+6.78`) | **`-4.32 +/- 6.89 [-11.21, +2.57]`** (`forge-combo29/carbon2/job48/M15_summary.txt:17`) | no |

---

## 3. Prediction Graded (`forge-combo29/carbon2/job49/prediction_job49.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `fed1243fa` after `kstar.txt` and Step 0, and before `M16`'s liveness search and first game:

```text
fed1243fa carbon2 job49: commit prediction_job49.txt alone after kstar.txt and Step 0, before M16 (2026-11-21 00:12:07 +0000)

 forge-combo29/carbon2/job49/prediction_job49.txt | 22 ++++++++++++++++++++++
 1 file changed, 22 insertions(+)
```

- **Per-match Side A (`L2: HistRework = 0` vs `PC20: HistRework = 2`) predictions (`3 / 4` `TRUE`):**

| Match | Predicted Side A Elo | Falsification Range | Observed Side A Elo +/- 95% (`[CI]`) | Grade |
| --- | --- | --- | --- | --- |
| `M16-2k` (`nodes=2000`, `IdeaB8b+HindsightDepth ON`) | `-2.0` Elo | outside `[-9.5, +5.5]` | **`-10.48 +/- 4.84`** (`[-15.33, -5.64]`) | **`FALSE (MISSED)`** (`-10.48` outside `[-9.5, +5.5]`) |
| `M17-2k` (`nodes=2000`, `all Idea & HindsightDepth OFF`) | `-8.5` Elo | outside `[-16.0, -1.0]` | **`-12.17 +/- 4.89`** (`[-17.05, -7.28]`) | **`TRUE (HELD)`** (`-16.0 <= -12.17 <= -1.0`) |
| `M16-20k` (`nodes=20000`, `IdeaB8b+HindsightDepth ON`) | `-3.5` Elo | outside `[-13.5, +6.5]` | **`-4.52 +/- 8.24`** (`[-12.75, +3.72]`) | **`TRUE (HELD)`** (`-13.5 <= -4.52 <= +6.5`) |
| `M17-20k` (`nodes=20000`, `all Idea & HindsightDepth OFF`) | `-10.0` Elo | outside `[-20.0, +0.0]` | **`-7.64 +/- 8.11`** (`[-15.76, +0.47]`) | **`TRUE (HELD)`** (`-20.0 <= -7.64 <= +0.0`) |

---

## 4. The Four Matches (`M16-2k`, `M17-2k`, `M16-20k`, `M17-20k`) and `M16 - M17` at Each Node Count

- **Common match settings:** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`), built-in evaluation, `Threads=1`, `Hash=16`, `OwnBook=false`, sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,060,001..2,075,000`), `concurrency=4`. In all four matches, **Side A = base `L2` (`HistRework=0`)** and **Side B = base `PC20` (`HistRework=2`)**, with the other 21 `PC20` options identical on both sides.
- **Depth-12 liveness on `O` (`200` positions, `forge-combo29/carbon2/job49/liveness_M16_M17.txt`):**
  - `M16 Side B (PC20 + bundle) O d12 known-answer sum: PASS (8481645 == 8481645)`
  - `M16` (with bundle `IdeaB8b + HindsightDepth`): Side A (`L2`) `O = 8,599,303` vs Side B (`PC20`) `O = 8,481,645` (`+117,658` nodes; `200/200` node diffs, `57/200` best-move diffs, `194/200` score diffs).
  - `M17` (all Idea & `HindsightDepth` off): Side A (`L2`) `O = 8,658,059` vs Side B (`PC20`) `O = 8,315,168` (`+342,891` nodes; `200/200` node diffs, `58/200` best-move diffs, `187/200` score diffs).

### Summary of the Four Matches

| Match | Nodes | Bundle State on Both Sides | UHO Lines | Status (`Games`) | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Side A (`L2`) vs Side B (`PC20`) Elo +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M16-2k` | `2,000` | `IdeaB8b+HindsightDepth ON` | `2,060,001..2,066,000` | `COMPLETE` (`12,000`) | `3944-4306-3750` | `[653, 1338, 2258, 1220, 531]` | **`-10.48 +/- 4.84`** (`[-15.33, -5.64]`) | `FALSE (pred -2.0, [-9.5, +5.5])` |
| `M17-2k` | `2,000` | `all Idea & HindsightDepth OFF` | `2,066,001..2,072,000` | `COMPLETE` (`12,000`) | `3929-4349-3722` | `[672, 1363, 2222, 1199, 544]` | **`-12.17 +/- 4.89`** (`[-17.05, -7.28]`) | `TRUE (pred -8.5, [-16.0, -1.0])` |
| `M16-20k` | `20,000` | `IdeaB8b+HindsightDepth ON` | `2,072,001..2,073,500` | `COMPLETE` (`3,000`) | `801-840-1359` | `[76, 383, 612, 362, 67]` | **`-4.52 +/- 8.24`** (`[-12.75, +3.72]`) | `TRUE (pred -3.5, [-13.5, +6.5])` |
| `M17-20k` | `20,000` | `all Idea & HindsightDepth OFF` | `2,073,501..2,075,000` | `COMPLETE` (`3,000`) | `781-847-1372` | `[82, 365, 651, 341, 61]` | **`-7.64 +/- 8.11`** (`[-15.76, +0.47]`) | `TRUE (pred -10.0, [-20.0, +0.0])` |

### `M16 - M17` at Each Node Count (Quoted Strictly Apart; `se = sqrt(se_16^2 + se_17^2)`, `se = hw95 / 1.96`)

| Nodes / Move | `M16` (With Bundle: `L2` vs `PC20`) | `M17` (Without Bundle: `L2` vs `PC20`) | `M16 - M17` +/- 95% (`[CI]`) | 95% CI Excludes `0`? |
| --- | --- | --- | --- | --- |
| `2,000` | `M16-2k`: `-10.48 +/- 4.84` | `M17-2k`: `-12.17 +/- 4.89` | **`+1.68 +/- 6.88 [-5.20, +8.56]`** | `NO (crosses 0)` |
| `20,000` | `M16-20k`: `-4.52 +/- 8.24` | `M17-20k`: `-7.64 +/- 8.11` | **`+3.13 +/- 11.56 [-8.43, +14.69]`** | `NO (crosses 0)` |

### `M16-2k` — `nodes=2,000`, `IdeaB8b+HindsightDepth ON`, Side A `bundle_on_L2` vs Side B `bundle_on_PC20` (UHO `2,060,001..2,066,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `495.083s`, `start_utc`: `Sat Nov 21 12:15:40 AM UTC 2026`, `end_utc`: `Sat Nov 21 12:23:55 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job49/M16-2k_recount.txt`):** `W-L-D = 3944-4306-3750`, pentanomial `[653, 1338, 2258, 1220, 531]`, **`-10.48 +/- 4.84`** (`[-15.33, -5.64]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job49/M16-2k_fastchess.txt`):** `Games: 12000, Wins: 3944, Losses: 4306, Draws: 3750, Points: 5819.0 (48.49 %) | Elo: -10.48 +/- 4.84, nElo: -13.46 +/- 6.22 | Ptnml(0-2): [653, 1338, 2258, 1220, 531], WL/DD Ratio: 2.79`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16-2k_games.tsv`):** `sha256 = 8e11cd35f3280280f60833cdd899af452445c8a4f035bbe545190f481be7e085`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16-2k_fastchess.txt`):** `sha256 = 0f57f53b40d0eb41bf30c12710eb6a18d9f8eae9f782f10f077fd6e8c442e85b`
- **Command (`M16-2k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L2 nodes=2000 option.HistRework=0 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_PC20 nodes=2000 option.HistRework=2 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2060001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M16-2k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M16-2k non-normal terminations              : PASS (0 == 0)`
  - `M16-2k opening FEN pairs matching book slice: PASS (6000 == 6000)`
  - `M16-2k finished games vs target             : PASS (12000 == 12000)`
  - `M16-2k finished pairs vs target             : PASS (6000 == 6000)`
  - `M16-2k recount W vs fastchess               : PASS (3944 == 3944)`
  - `M16-2k recount L vs fastchess               : PASS (4306 == 4306)`
  - `M16-2k recount D vs fastchess               : PASS (3750 == 3750)`
  - `M16-2k recount ptnml vs fastchess           : PASS ([653, 1338, 2258, 1220, 531] == [653, 1338, 2258, 1220, 531])`
  - `M16-2k recount Elo vs fastchess             : PASS (-10.48 == -10.48)`
  - `M16-2k recount +/-95% vs fastchess          : PASS (4.84 == 4.84)`
  - `M16-2k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M17-2k` — `nodes=2,000`, `all Idea & HindsightDepth OFF`, Side A `all_off_L2` vs Side B `all_off_PC20` (UHO `2,066,001..2,072,000`)
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `452.084s`, `start_utc`: `Sat Nov 21 12:26:25 AM UTC 2026`, `end_utc`: `Sat Nov 21 12:33:57 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job49/M17-2k_recount.txt`):** `W-L-D = 3929-4349-3722`, pentanomial `[672, 1363, 2222, 1199, 544]`, **`-12.17 +/- 4.89`** (`[-17.05, -7.28]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job49/M17-2k_fastchess.txt`):** `Games: 12000, Wins: 3929, Losses: 4349, Draws: 3722, Points: 5790.0 (48.25 %) | Elo: -12.17 +/- 4.89, nElo: -15.49 +/- 6.22 | Ptnml(0-2): [672, 1363, 2222, 1199, 544], WL/DD Ratio: 2.83`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M17-2k_games.tsv`):** `sha256 = be0eda7fbd5c48a968f6db0b4e8d44868a7169a2090ea27a41e569506fde3fe9`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M17-2k_fastchess.txt`):** `sha256 = b47e7b7bf2a59baf7673f195779a19723c95607a955b0e3d5394a29b1c1d9822`
- **Command (`M17-2k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L2 nodes=2000 option.HistRework=0 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_PC20 nodes=2000 option.HistRework=2 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2066001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M17-2k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M17-2k non-normal terminations              : PASS (0 == 0)`
  - `M17-2k opening FEN pairs matching book slice: PASS (6000 == 6000)`
  - `M17-2k finished games vs target             : PASS (12000 == 12000)`
  - `M17-2k finished pairs vs target             : PASS (6000 == 6000)`
  - `M17-2k recount W vs fastchess               : PASS (3929 == 3929)`
  - `M17-2k recount L vs fastchess               : PASS (4349 == 4349)`
  - `M17-2k recount D vs fastchess               : PASS (3722 == 3722)`
  - `M17-2k recount ptnml vs fastchess           : PASS ([672, 1363, 2222, 1199, 544] == [672, 1363, 2222, 1199, 544])`
  - `M17-2k recount Elo vs fastchess             : PASS (-12.17 == -12.17)`
  - `M17-2k recount +/-95% vs fastchess          : PASS (4.89 == 4.89)`
  - `M17-2k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M16-20k` — `nodes=20,000`, `IdeaB8b+HindsightDepth ON`, Side A `bundle_on_L2` vs Side B `bundle_on_PC20` (UHO `2,072,001..2,073,500`)
- **Status:** `COMPLETE` (`3,000` games, `1,500` pairs, wall `1004.362s`, `start_utc`: `Sat Nov 21 12:34:00 AM UTC 2026`, `end_utc`: `Sat Nov 21 12:50:45 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job49/M16-20k_recount.txt`):** `W-L-D = 801-840-1359`, pentanomial `[76, 383, 612, 362, 67]`, **`-4.52 +/- 8.24`** (`[-12.75, +3.72]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job49/M16-20k_fastchess.txt`):** `Games: 3000, Wins: 801, Losses: 840, Draws: 1359, Points: 1480.5 (49.35 %) | Elo: -4.52 +/- 8.24, nElo: -6.82 +/- 12.43 | Ptnml(0-2): [76, 383, 612, 362, 67], WL/DD Ratio: 0.99`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16-20k_games.tsv`):** `sha256 = 00a248127a87c9cb84862618632941cb01c8e9af0dad3b30312a78ffc6a13abf`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16-20k_fastchess.txt`):** `sha256 = f1c363509b05b05acbb5d72396980e296f1cb3f157941093b0c618edee9b3037`
- **Command (`M16-20k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_L2 nodes=20000 option.HistRework=0 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=bundle_on_PC20 nodes=20000 option.HistRework=2 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2072001 -rounds 1500 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M16-20k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M16-20k non-normal terminations             : PASS (0 == 0)`
  - `M16-20k opening FEN pairs matching book slice: PASS (1500 == 1500)`
  - `M16-20k finished games vs target            : PASS (3000 == 3000)`
  - `M16-20k finished pairs vs target            : PASS (1500 == 1500)`
  - `M16-20k recount W vs fastchess              : PASS (801 == 801)`
  - `M16-20k recount L vs fastchess              : PASS (840 == 840)`
  - `M16-20k recount D vs fastchess              : PASS (1359 == 1359)`
  - `M16-20k recount ptnml vs fastchess          : PASS ([76, 383, 612, 362, 67] == [76, 383, 612, 362, 67])`
  - `M16-20k recount Elo vs fastchess            : PASS (-4.52 == -4.52)`
  - `M16-20k recount +/-95% vs fastchess         : PASS (8.24 == 8.24)`
  - `M16-20k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M17-20k` — `nodes=20,000`, `all Idea & HindsightDepth OFF`, Side A `all_off_L2` vs Side B `all_off_PC20` (UHO `2,073,501..2,075,000`)
- **Status:** `COMPLETE` (`3,000` games, `1,500` pairs, wall `919.299s`, `start_utc`: `Sat Nov 21 12:50:47 AM UTC 2026`, `end_utc`: `Sat Nov 21 01:06:06 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job44/bld_bundle9/forge`):** `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef` (`id name Chess Engine Forge 6.4.24 candidate`)
- **UCI preflight checks:** Side A `32` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job49/M17-20k_recount.txt`):** `W-L-D = 781-847-1372`, pentanomial `[82, 365, 651, 341, 61]`, **`-7.64 +/- 8.11`** (`[-15.76, +0.47]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job49/M17-20k_fastchess.txt`):** `Games: 3000, Wins: 781, Losses: 847, Draws: 1372, Points: 1467.0 (48.90 %) | Elo: -7.64 +/- 8.11, nElo: -11.72 +/- 12.43 | Ptnml(0-2): [82, 365, 651, 341, 61], WL/DD Ratio: 0.95`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M17-20k_games.tsv`):** `sha256 = b87a08944495e57a99ff710a879e21f4352d0efae38d65ab27b07d44ad48e740`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M17-20k_fastchess.txt`):** `sha256 = a93a7513fcf5e3ba798e438ccb501746ea627d7ccb15676a599d5cdc38ff97fe`
- **Command (`M17-20k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_L2 nodes=20000 option.HistRework=0 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -engine cmd=/tmp/carbon2_job44/bld_bundle9/forge name=all_off_PC20 nodes=20000 option.HistRework=2 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=false option.HindsightDepth=false -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2073501 -rounds 1500 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job48/tmp_M17-20k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M17-20k non-normal terminations             : PASS (0 == 0)`
  - `M17-20k opening FEN pairs matching book slice: PASS (1500 == 1500)`
  - `M17-20k finished games vs target            : PASS (3000 == 3000)`
  - `M17-20k finished pairs vs target            : PASS (1500 == 1500)`
  - `M17-20k recount W vs fastchess              : PASS (781 == 781)`
  - `M17-20k recount L vs fastchess              : PASS (847 == 847)`
  - `M17-20k recount D vs fastchess              : PASS (1372 == 1372)`
  - `M17-20k recount ptnml vs fastchess          : PASS ([82, 365, 651, 341, 61] == [82, 365, 651, 341, 61])`
  - `M17-20k recount Elo vs fastchess            : PASS (-7.64 == -7.64)`
  - `M17-20k recount +/-95% vs fastchess         : PASS (8.11 == 8.11)`
  - `M17-20k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; 12,000 games carry about +/- 5 Elo and 3,000 about
+/- 9; one switch only (k*), at its S14 value only (no level in between); M16 and M17 measure k* on the bundle's tree
with the built-in evaluation, so a lean here is a question for the PC, never an answer.

---

## Facts

1. **Step 0 pins, known answers, and the planted `HistReworkk=0` stop check passed on `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`):** No-option pins `312,866 / 862,329 / 4,865,609`; `PC20` `bench 11 / 13 = 278,024 / 587,276`; `PC20` all off `O = 8,315,168` (`200 == 200` position-by-position equal to Job 46 Step 0); `L2` (`HistRework 0`) all off `O = 8,658,059` (`200 == 200` equal to Job 48 Part L); and the planted `HistReworkk=0` check stopped the runner immediately before any search on `info string unknown option HistReworkk`.
2. **Bonus equivalence check from File 49 (`lines 38–40`):** On `/tmp/carbon2_job47/bld_bundle11_k4b/forge` (`PC20`), `IdeaK4=true` with `IdeaK4_Shrink=32` and `IdeaK4b=false` gives `O = 7,491,020` and matches Job 47 `P11(d)` (`IdeaK4b=true` alone) on `200 == 200` positions (nodes, best move, and score).
3. **`k* = 2` (`L2: HistRework 0`) selected from Job 48's five completed live bases:** `D_2 = Elo(M15-2) - Elo(M15-0) = +8.01 +/- 6.96 [+1.05, +14.97]` (`forge-combo29/carbon2/job48/M15_summary.txt:13`), strictly the largest `D_k` across `k = 1..5` (`D_1 = -1.33`, `D_3 = -1.71`, `D_4 = -1.71`, `D_5 = -4.32`).
4. **Depth-12 liveness on `O` (`200` positions) confirms `HistRework = 0` vs `HistRework = 2` is live both with and without the bundle, with smaller tree-size expansion when the bundle is on:** Without the bundle (`M17`), `L2` searches `8,658,059` vs `PC20`'s `8,315,168` (`+342,891` nodes = `+4.12%`, `200/200` node diffs, `58/200` best-move diffs). With the bundle (`M16`), `L2` searches `8,599,303` vs `PC20`'s `8,481,645` (`+117,658` nodes = `+1.39%`, `200/200` node diffs, `57/200` best-move diffs).
5. **In `M16-2k` (`nodes=2,000`, `12,000` games, `IdeaB8b+HindsightDepth ON`), setting `HistRework = 0` (`L2`) loses to `PC20` (`HistRework = 2`) with 95% confidence excluding zero:** Side A (`bundle_on_L2`) vs Side B (`bundle_on_PC20`) scored `3944-4306-3750`, pentanomial `[653, 1338, 2258, 1220, 531]`, **`-10.48 +/- 4.84` Elo (`[-15.33, -5.64]`)**.
6. **In `M17-2k` (`nodes=2,000`, `12,000` games, `all Idea & HindsightDepth OFF`), setting `HistRework = 0` (`L2`) loses to `PC20` (`HistRework = 2`) with 95% confidence excluding zero:** Side A (`all_off_L2`) vs Side B (`all_off_PC20`) scored `3929-4349-3722`, pentanomial `[672, 1363, 2222, 1199, 544]`, **`-12.17 +/- 4.89` Elo (`[-17.05, -7.28]`)**.
7. **In `M16-20k` (`nodes=20,000`, `3,000` games, `IdeaB8b+HindsightDepth ON`), the 95% confidence interval crosses zero:** Side A (`bundle_on_L2`) vs Side B (`bundle_on_PC20`) scored `801-840-1359`, pentanomial `[76, 383, 612, 362, 67]`, **`-4.52 +/- 8.24` Elo (`[-12.75, +3.72]`)**.
8. **In `M17-20k` (`nodes=20,000`, `3,000` games, `all Idea & HindsightDepth OFF`), the 95% confidence interval crosses zero:** Side A (`all_off_L2`) vs Side B (`all_off_PC20`) scored `781-847-1372`, pentanomial `[82, 365, 651, 341, 61]`, **`-7.64 +/- 8.11` Elo (`[-15.76, +0.47]`)**.
9. **At `nodes=2,000` (quoted apart), `Elo(M16-2k) - Elo(M17-2k) = +1.68 +/- 6.88 [-5.20, +8.56]`, whose 95% interval crosses zero.**
10. **At `nodes=20,000` (quoted apart), `Elo(M16-20k) - Elo(M17-20k) = +3.13 +/- 11.56 [-8.43, +14.69]`, whose 95% interval crosses zero.**

---

## Suspicions

1. **Directional lean in `M16-20k` (`-4.52 +/- 8.24` Elo, `[-12.75, +3.72]`):** The point estimate leans against `HistRework = 0` at `nodes=20,000` (`IdeaB8b+HindsightDepth ON`), consistent with the `2,000`-node direction, while its `3,000`-game 95% interval crosses `0`.
2. **Directional lean in `M17-20k` (`-7.64 +/- 8.11` Elo, `[-15.76, +0.47]`):** The point estimate leans against `HistRework = 0` at `nodes=20,000` (`all Idea & HindsightDepth OFF`), consistent with the `2,000`-node direction, while its `3,000`-game 95% interval crosses `0`.
3. **Interaction `Elo(M16-2k) - Elo(M17-2k) = +1.68 +/- 6.88 [-5.20, +8.56]` at `nodes=2,000`:** The positive point difference leans in the same direction as Job 48's `D_2 = +8.01 +/- 6.96 [+1.05, +14.97]` (the 4-corner closure difference `(M15-2 - M15-0) - (M16-2k - M17-2k)` across the four independent `12,000`-game matches is `+6.33 +/- 9.79` Elo, crossing `0`), indicating partial overlap between `HistRework = 2` and the bundle (`~+2` to `+5` Elo if one averages the two orthogonal ways of measuring the same interaction) while `M16-2k - M17-2k` alone lies inside `+/- 6.88` Elo.
4. **Interaction `Elo(M16-20k) - Elo(M17-20k) = +3.13 +/- 11.56 [-8.43, +14.69]` at `nodes=20,000`:** The positive point estimate (`+3.13`) also leans toward partial overlap at `20,000` nodes, while its `3,000`-game combined 95% interval (`[-8.43, +14.69]`) crosses `0`.
5. **Why switching `HistRework` all the way to `0` (`L2`) loses even with the bundle on (`M16-2k = -10.48 +/- 4.84`, `M16-20k = -4.52 +/- 8.24`):** `HistRework = 2` carries two features that `IdeaB8b` does not replace — `(a)` the destination-square bit `to_attacked_by_lesser` in `LesserThreatHistory` (penalizing quiet moves that step *onto* squares attacked by cheaper enemy pieces even when no friendly piece is currently threatened) and `(b)` the `75%`-weighted `joint_correction_` table (`pawn_key ^ non_pawn_material`). Thus `IdeaB8b` recovers part of `from_attacked_by_lesser` (depth-12 `O` node growth drops from `+4.12%` to `+1.39%`), yet losing `to_attacked_by_lesser` and `joint_correction_` leaves `bundle + HistRework=0` weaker than `bundle + HistRework=2`.

---

## Read and Not Tested

1. **Intermediate `HistRework = 1` (`50%` blend / `50%` joint weight) and `HistRework = 3` (`100%` blend / `100%` joint weight) in `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/b4.hpp` (`lines 20–30, 65–75`):** Job 49 tested only `HistRework = 0` (`S14` value) against `HistRework = 2` (`PC20` value). Because `HistRework = 0` discards both `joint_correction_` (`src/search.cpp:1446–1459`) and the `to_attacked_by_lesser` axis of `LesserThreatHistory` (`src/search.cpp:1612–1616`), an intermediate setting (`HistRework = 1`) or separating `threat_quarters` from `joint_weight` was read in `b4.hpp` and not tested.
2. **Total gain of `(bundle + PC20)` vs `(all_off + PC20)` vs `(bundle + L2)`:** Combining `M15-0` (`bundle_on_PC20` vs `all_off_PC20`: `+11.09 +/- 4.93` at `2,000` nodes in Job 48) with `M16-2k` (`bundle_on_L2` vs `bundle_on_PC20`: `-10.48 +/- 4.84`) shows `bundle_on_PC20` sits at the top of the 4-corner square on built-in evaluation, ahead of both `all_off_PC20` and `bundle_on_L2`; we did not play a direct `bundle_on_L2` vs `all_off_PC20` match.

---

## What I Did Not Do

- Did **not** build any new binary in Job 49 (reused `/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, and `/tmp/carbon2_job47/bld_bundle11_k4b/forge` for the 1-line `K4` equivalence check).
- Did **not** test `HistRework = 1` or `HistRework = 3`, nor any of the other four `PC20` switches (`k = 1, 3, 4, 5`).
- Did **not** pool `2,000`-node and `20,000`-node matches together.
- Did **not** edit `prediction_job49.txt` after committing it alone in `fed1243fa`.
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **Exact magnitude of `M16 - M17` (`HistRework = 0` interaction with the bundle):** At `12,000` games per match (`nodes=2000`), `M16-2k - M17-2k` carries a 95% half-width of `+/- 6.88` Elo (and at `3,000` games per match at `nodes=20000`, `+/- 11.56` Elo), so a true overlap of a few Elo between `HistRework = 2` and `IdeaB8b` can sample at `+8.01 +/- 6.96 [+1.05, +14.97]` in `M15-2 - M15-0` and `+1.68 +/- 6.88 [-5.20, +8.56]` in `M16-2k - M17-2k` across independent book slices.
2. **Why `M16-2k` (`-10.48 +/- 4.84`) fell `0.98` Elo below our `-9.5` lower bound:** In `prediction_job49.txt`, we underestimated `HistRework = 2`'s standalone strength at `nodes=2000` (`-8.5` predicted vs `-12.17 +/- 4.89` observed in `M17-2k`) and assumed a larger `M16-2k - M17-2k` recovery than `+1.68 +/- 6.88 [-5.20, +8.56]`.
3. **Behavior with the PC's NNUE net:** `joint_correction_` corrects static evaluation residuals, whose scale and variance differ substantially between the built-in evaluation and the PC's NNUE net.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job49/builds.txt`)

```text
=== JOB 49 BUILDS.TXT ===
1. r15d + v3 source tree: /tmp/carbon2_job36/tpl_r15d_v3
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77

2. Bundle9 executable (same as Jobs 46 & 48): /tmp/carbon2_job44/bld_bundle9/forge
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

### Row File Hashes (`forge-combo29/carbon2/job49/*.rows.txt`)

- Step 0 bundle9 PC20 all_off O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job49/step0_bundle9_PC20_all_off_O_d12.rows.txt`): `467d7a8cc6c2efa2e41f4d7fef047147abc12738755cacd5537021909a63d1e3`
- Step 0 bundle9 L2 all_off O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job49/step0_bundle9_L2_all_off_O_d12.rows.txt`): `1993e5cac134e4bf4970a8635a6b94133c4276fdb5fcf38b78e31ec12161360a`
- Step 0 bundle11 IdeaK4(Shrink=32) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job49/step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt`): `82565956a70e47cbe18bad91ecfd24cb1059acf71a4f0eaf10a76ddf75811bb9`
- M16 liveness Side A (L2 + bundle) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16_liveness_SideA_L2_bundle_O_d12.rows.txt`): `8fdc4ea6ed3616594ce476dba32e51958abfa8df8a37d16ac3bb7ff151f0456b`
- M16 liveness Side B (PC20 + bundle) O d12 rows (`/agent/repos/dwqww/forge-combo29/carbon2/job49/M16_liveness_SideB_PC20_bundle_O_d12.rows.txt`): `f5c33d8d4f10e12dc67ca8201ae7cec736c659d316d05aed16e33c0648f0c172`

### UTC Timestamps (`forge-combo29/carbon2/job49/stamps.txt`)

```text
job49_claimed: Sat Nov 21 12:08:15 AM UTC 2026
kstar_done: Sat Nov 21 12:09:12 AM UTC 2026
step0_done: Sat Nov 21 12:11:13 AM UTC 2026
prediction_committed: Sat Nov 21 12:12:07 AM UTC 2026
M16-2k_done: Sat Nov 21 12:26:23 AM UTC 2026
M17-2k_done: Sat Nov 21 12:33:58 AM UTC 2026
M16-20k_done: Sat Nov 21 12:50:45 AM UTC 2026
M17-20k_done: Sat Nov 21 01:06:07 AM UTC 2026
report_done: Sat Nov 21 01:09:53 AM UTC 2026
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job49`)

```text
 M forge-combo29/carbon2/job49/stamps.txt
?? forge-combo29/carbon2/job49/REPORT_carbon2_job49.md
?? forge-combo29/carbon2/job49/build_report.py
forge-combo29/carbon2/job49:
build_report.py
builds.txt
j49_lib.py
kstar.json
kstar.txt
liveness_M16_M17.json
liveness_M16_M17.txt
M16-20k_fastchess.txt
M16-20k_fastchess.txt.meta
M16-20k_games.tsv
M16-20k_recount.txt
M16-2k_fastchess.txt
M16-2k_fastchess.txt.meta
M16-2k_games.tsv
M16-2k_recount.txt
M16_liveness_SideA_L2_bundle_O_d12.rows.txt
M16_liveness_SideA_L2_bundle_O_d12.rows.txt.meta
M16_liveness_SideB_PC20_bundle_O_d12.rows.txt
M16_liveness_SideB_PC20_bundle_O_d12.rows.txt.meta
M17-20k_fastchess.txt
M17-20k_fastchess.txt.meta
M17-20k_games.tsv
M17-20k_recount.txt
M17-2k_fastchess.txt
M17-2k_fastchess.txt.meta
M17-2k_games.tsv
M17-2k_recount.txt
matches_results.json
matches_summary.txt
prediction_job49.txt
REPORT_carbon2_job49.md
run_kstar.py
run_matches.py
run_step0.py
stamps.txt
step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt
step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt.meta
step0_bundle9_L2_all_off_O_d12.rows.txt
step0_bundle9_L2_all_off_O_d12.rows.txt.meta
step0_bundle9_PC20_all_off_O_d12.rows.txt
step0_bundle9_PC20_all_off_O_d12.rows.txt.meta
step0_raw.txt
```

---

## Model Name

`Gemini 4 Carbon`
