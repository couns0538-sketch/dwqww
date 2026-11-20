# Job 40 Report — `carbon2` (`THE BUNDLE'S FIRST GAMES ON THE PC'S SEARCH`)

## Executive First Lines (`(1)` Step 0, `(2)` Prediction Graded, `(3)` Part T, `(4)` Part M)

- **(1) Step 0 (`78d2a6126`, `forge-combo29/carbon2/job40/step0_raw.txt`, `forge-combo29/carbon2/job40/builds.txt`):**
  - `r15d + v3` source tree (`/tmp/carbon2_job36/tpl_r15d_v3`, LF line endings): CRLF count PASS (`0 == 0` in all four files); source file `sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp)` PASS (`174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4`), `sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp)` PASS (`2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013`), `sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp)` PASS (`2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf`), `sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp)` PASS (`5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77`).
  - Plain `r15d + v3` Release executable (`/tmp/carbon2_job40/bld_base_v3/forge`, executable `sha256(/tmp/carbon2_job40/bld_base_v3/forge) = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`): no-option `bench 11` PASS (`312866 == 312866`), `bench 13` PASS (`862329 == 862329`), `perft 5` PASS (`4865609 == 4865609`); `PC20` `bench 11` PASS (`278024 == 278024`), `bench 13` PASS (`587276 == 587276`).
  - Fresh copy `/tmp/carbon2_job40/src_bundle` patched with `forge-combo29/carbon2/job39/bundle_grok.patch.txt` (patch blob `sha256(/agent/repos/dwqww/forge-combo29/carbon2/job39/bundle_grok.patch.txt)` PASS `d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec == d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec`) -> Release executable `/tmp/carbon2_job40/bld_bundle/forge` (executable `sha256(/tmp/carbon2_job40/bld_bundle/forge) = e011af0f15569290aa7431d0b53c384cdfc59763ba0fdd94bc33971b9aa5cd63`):
    - **All switches OFF:** `312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `PC20` `278024 == 278024`, `587276 == 587276`, `Set A line L` `26741 == 26741` / `107124743 == 107124743` / game-record stream `sha256` PASS (`d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`), `n[1..60] line L` `8449 == 8449` / `8482 == 8482` / `36688357 == 36688357` / game-record stream `sha256` PASS (`b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`), and `O` d12 off (`step0_bundle_all_off_O_d12.rows.txt`) sum PASS (`8315168 == 8315168`) and equal positions vs `forge-combo29/carbon2/job39/OFF_O_d12.rows.txt` PASS (`200 == 200`).
    - **All six switches ON (`PC20`, built-in eval):** `O` d12 (`step0_bundle_all_on_O_d12.rows.txt`) sum PASS (`8035170 == 8035170`) and position-by-position equality vs `forge-combo29/carbon2/job39/BUNDLE_ALL_ON_O_d12.rows.txt` PASS (`200 == 200`); `Set A line L` (`step0_bundle_all_on_SetA_L.rows.txt`) records PASS (`27991 == 27991`), searches PASS (`28117 == 28117`), nodes PASS (`111242459 == 111242459`), game-record stream `sha256` PASS (`c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce == c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce`).
    - **`fastchess` & official book:** `/tmp/carbon2_job40/fastchess` (`alpha 1.8.3 20261115-d6e3a7a`, repo commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`, executable `sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007`); `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` line count PASS (`2632036 == 2632036`) and book file `sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd)` PASS (`7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`).
- **(2) Prediction Graded (`forge-combo29/carbon2/job40/prediction_job40.txt`, committed ALONE in `4695aaf9f09a7733fc5847d572f594b5ffa733c5`, `1 file changed`, `Fri Nov 20 02:21:28 PM UTC 2026`, before Part T's first run at `02:22:54 PM UTC`, never edited):**
  - **(1) M1 (bundle all on vs all off, 3,000 games):** Predicted `+5.0` Elo (`[-8.0, +20.0]`); **NOT GRADED / NOT DONE** (the initial run ended at a session boundary in Part M at `14:28 UTC`, and per owner resume instructions M1 and M2 were not replayed).
  - **(2) M0 (`20,000`-node `FULL` vs `10,000`-node `HALF`, 400 games):** Predicted `+80.0` Elo (wrong outside `[+45.0, +120.0]`); observed **`+182.83 +/- 27.34` Elo** (`228 - 35 - 137`) -> **FALSE** (outside `[+45.0, +120.0]`; under `UHO_Lichess_4852_v1.epd` unbalanced openings with built-in evaluation and **zero draw/resign adjudication**, the draw rate is only `34.25%` (`137/400`), expanding standard logistic Elo per doubling far above typical adjudicated `~55-65%`-draw NNUE self-play!).
  - **(3) Part T (`all_on / all_off` time per `1,000` nodes):** Predicted `1.10` (wrong outside `[1.01, 1.25]`); observed **`1.119705`** (`0.583349 ms / 0.520985 ms`, inside `[1.01, 1.25]`) -> **TRUE**.
  - **Graded score on completed items: `1` of `2` TRUE (`1` ungraded because M1 was not run).**
- **(3) Part T Summary (`forge-combo29/carbon2/job40/partT_summary.txt`, commit `2a438e39d`):**
  - Paired forward + reverse (`18` runs total = `9` forward `01..09` + `9` reverse `10..18`, `O` set `200` FENs at depth 12, `PC20`, built-in eval, `Threads 1`, `Hash 16`, pinned to core `2`):
    - Mean of the 4 `all_off` runs = **`0.520985 ms / 1,000 nodes`** (`520.985 us / 1,000 nodes`); forward-to-reverse drift = **`1.000310`** (`0.03%`).
    - Paired setting ratios vs mean of all 4 `all_off` runs: `all_off_1 = 1.005097`, `all_off_2 = 0.994903`, `only_K4 = 0.997231`, `only_S32 = 0.991440`, `only_B1 = 1.048607` (`+4.86%`), `only_S13 = 0.999207`, `only_S10 = 0.995142`, `only_B8 = 1.058384` (`+5.84%`), **`all_on = 1.119705` (`+11.97%`)**.
- **(4) Part M Summary (`M0` completed in commit `137417d83`; initial run ended at `14:28 UTC` in Part M; `M1` and `M2` NOT DONE per owner resume instructions):**
  - **`M0` Control (`FULL` `nodes=20000` vs `HALF` `nodes=10000`, all switches off, lines `2,100,001..2,100,200`, `400` games):**
    - Recounted from `forge-combo29/carbon2/job40/M0_games.tsv` (`recount_pgn.py`): **`228 - 35 - 137`** (`score = 0.741250`), pentanomial **`[0, 14, 37, 91, 58]`** (`200` pairs), **`+182.83 +/- 27.34` Elo** (`95% CI [+155.49, +210.17]`, exact asymmetric `[+156.53, +211.21]`, `nElo = +273.06 +/- 34.05`, `LOS = 100.00%`).
    - `fastchess`'s own final line (`forge-combo29/carbon2/job40/M0_fastchess.txt`): `Games: 400, Wins: 228, Losses: 35, Draws: 137, Points: 296.5 (74.12 %) | Elo: 182.83 +/- 27.34, nElo: 273.06 +/- 34.05 | Ptnml(0-2): [0, 14, 37, 91, 58]` (`PASS: 228 == 228`, `35 == 35`, `137 == 137`, `[0, 14, 37, 91, 58] == [0, 14, 37, 91, 58]`, `+182.83 == +182.83`, `27.34 == 27.34`; `M0 PASS check (+182.83 > +20.00): PASS (True == True)`).
  - **`M1` (3,000-game bundle match) and `M2` (six 1,000-game singles):** **NOT DONE** — the initial run ended at a session boundary in Part M (`14:28 UTC`), and on resume (`15:53 UTC`) the owner instructed us to push `REPORT_carbon2_job40.md` without replaying `M1` or `M2` and proceed directly to Job 41 (`FABLE_TO_carbon2_41.md`).

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 6 Elo and 1,000 about +/- 15;
a result with the built-in evaluation does not say what the bundle does with the PC's net.

---

## 1. Step 0 — `r15d + v3`, Fresh Bundle Build, OFF & Job 39 Known Answers (`step0_raw.txt`, `builds.txt`)

```text
  src/search.cpp CRLF count                   : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp): PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)
  src/uci.cpp CRLF count                      : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp): PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)
  src/board.cpp CRLF count                    : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp): PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)
  include/forge/board.hpp CRLF count          : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp): PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)
  plain_r15d_v3 no-option bench 11            : PASS (312866 == 312866)
  plain_r15d_v3 no-option bench 13            : PASS (862329 == 862329)
  plain_r15d_v3 no-option perft 5             : PASS (4865609 == 4865609)
  plain_r15d_v3 PC20 bench 11                 : PASS (278024 == 278024)
  plain_r15d_v3 PC20 bench 13                 : PASS (587276 == 587276)
  patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job39/bundle_grok.patch.txt): PASS (d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec == d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec)
  bundle_default_off no-option bench 11       : PASS (312866 == 312866)
  bundle_default_off no-option bench 13       : PASS (862329 == 862329)
  bundle_default_off no-option perft 5        : PASS (4865609 == 4865609)
  bundle_default_off PC20 bench 11            : PASS (278024 == 278024)
  bundle_default_off PC20 bench 13            : PASS (587276 == 587276)
  bundle_default_off Set A line L records     : PASS (26741 == 26741)
  bundle_default_off Set A line L nodes       : PASS (107124743 == 107124743)
  bundle_default_off Set A line L sha256      : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  bundle_default_off n[1..60] line L records  : PASS (8449 == 8449)
  bundle_default_off n[1..60] line L searches : PASS (8482 == 8482)
  bundle_default_off n[1..60] line L nodes    : PASS (36688357 == 36688357)
  bundle_default_off n[1..60] line L sha256   : PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  bundle_all_off O d12 sum vs Job 39 OFF      : PASS (8315168 == 8315168)
  bundle_all_off O d12 equal positions vs J39 : PASS (200 == 200)
  bundle_all_on O d12 sum vs Job 39 ALL_ON    : PASS (8035170 == 8035170)
  bundle_all_on O d12 equal positions vs J39  : PASS (200 == 200)
  bundle_all_on Set A line L records vs J39   : PASS (27991 == 27991)
  bundle_all_on Set A line L searches vs J39  : PASS (28117 == 28117)
  bundle_all_on Set A line L nodes vs J39     : PASS (111242459 == 111242459)
  bundle_all_on Set A line L sha256 vs J39    : PASS (c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce == c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce)
  book lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (2632036 == 2632036)
  book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a)
```

---

## 2. Part T — Cost per Node (`partT_summary.txt`, `partT_01..18_*.rows.txt`)

- **Executable:** `/tmp/carbon2_job40/bld_bundle/forge` (`exe sha256(/tmp/carbon2_job40/bld_bundle/forge) = e011af0f15569290aa7431d0b53c384cdfc59763ba0fdd94bc33971b9aa5cd63`), `O` set (`/tmp/carbon2_job39/sets/first200.fens`, `set sha256(/tmp/carbon2_job39/sets/first200.fens) = ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`), depth 12, `PC20`, built-in evaluation, `Threads 1`, `Hash 16`, `ucinewgame` + `isready` completed before every `go depth 12` wall-clock window.

### 2.1 The All-Off Runs Side by Side (`mean_all_off_4_runs = 0.520985 ms / 1,000 nodes`)

| Run ID | Pass | Setting | Node Sum | Wall Sum (`s`) | `ms / 1,000 nodes` | `us / 1,000 nodes` | Ratio vs Mean of 4 All-Off |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `partT_01_fwd_all_off_1` | `fwd` | `all_off_1` | `8,315,168` | `4.3534` | `0.523551` | `523.551` | `1.004927` |
| `partT_02_fwd_all_off_2` | `fwd` | `all_off_2` | `8,315,168` | `4.3094` | `0.518256` | `518.256` | `0.994763` |
| `partT_17_rev_all_off_2` | `rev` | `all_off_2` | `8,315,168` | `4.3106` | `0.518402` | `518.402` | `0.995044` |
| `partT_18_rev_all_off_1` | `rev` | `all_off_1` | `8,315,168` | `4.3549` | `0.523729` | `523.729` | `1.005267` |

- Forward all-off mean = `0.520904 ms / 1k nodes`; reverse all-off mean = `0.521065 ms / 1k nodes`; **drift (`rev / fwd`) = `1.000310`**.

### 2.2 All 18 Runs (Forward `01..09` and Reverse `10..18`) & Paired Means per Setting

| Setting | Node Sum (PASS in both passes) | Fwd Wall (`s`) | Rev Wall (`s`) | Mean Wall (`s`) | Fwd `ms/1k` | Rev `ms/1k` | Mean `ms/1k` (`us/1k`) | Ratio vs All-Off Mean |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`all_off_1`** | `8,315,168 == 8,315,168` | `4.3534` | `4.3549` | `4.3542` | `0.523551` | `0.523729` | `0.523640` (`523.640`) | `1.005097` |
| **`all_off_2`** | `8,315,168 == 8,315,168` | `4.3094` | `4.3106` | `4.3100` | `0.518256` | `0.518402` | `0.518329` (`518.329`) | `0.994903` |
| **`only_K4`** | `8,080,229 == 8,080,229` | `4.1831` | `4.2130` | `4.1980` | `0.517694` | `0.521391` | `0.519542` (`519.542`) | `0.997231` |
| **`only_S32`** | `8,339,315 == 8,339,315` | `4.2755` | `4.3395` | `4.3075` | `0.512688` | `0.520362` | `0.516525` (`516.525`) | `0.991440` |
| **`only_B1`** | `8,548,042 == 8,548,042` | `4.6411` | `4.6986` | `4.6699` | `0.542945` | `0.549671` | `0.546308` (`546.308`) | **`1.048607`** |
| **`only_S13`** | `8,077,984 == 8,077,984` | `4.1926` | `4.2178` | `4.2052` | `0.519010` | `0.522133` | `0.520571` (`520.571`) | `0.999207` |
| **`only_S10`** | `8,314,153 == 8,314,153` | `4.2984` | `4.3226` | `4.3105` | `0.516995` | `0.519913` | `0.518454` (`518.454`) | `0.995142` |
| **`only_B8`** | `8,262,696 == 8,262,696` | `4.5540` | `4.5581` | `4.5561` | `0.551154` | `0.551649` | `0.551402` (`551.402`) | **`1.058384`** |
| **`all_on`** | `8,035,170 == 8,035,170` | `4.6687` | `4.7060` | `4.6873` | `0.581027` | `0.585671` | `0.583349` (`583.349`) | **`1.119705`** |

---

## 3. Part M — Games (`M0` Completed; `M1` & `M2` Not Done)

- **`M0` Control (`forge-combo29/carbon2/job40/M0_games.tsv`, `sha256(/agent/repos/dwqww/forge-combo29/carbon2/job40/M0_games.tsv) = 0c095ae31bb6f60884d37ce944eea9fabb712c3475eb432058273042803e73b0`; `forge-combo29/carbon2/job40/M0_fastchess.txt`, `sha256(/agent/repos/dwqww/forge-combo29/carbon2/job40/M0_fastchess.txt) = f09297883fdc6ec8f88f01d107777835072f2c6b369f0c366bdf712f31019d1c`; `M0_recount.txt`):**
  - Engines: `FULL` (`nodes=20000`, all 6 switches `false`, `PC20`) vs `HALF` (`nodes=10000`, all 6 switches `false`, `PC20`), book lines `2,100,001..2,100,200` (`400` games, `200` pairs, no adjudication, `concurrency = 3`).
  - Recounted from `M0_games.tsv`: `W-L-D = 228 - 35 - 137` (`0.741250`), pentanomial `[0, 14, 37, 91, 58]`, **`+182.83 +/- 27.34` Elo** (`95% CI [+155.49, +210.17]`, exact `[+156.53, +211.21]`, `nElo = +273.06 +/- 34.05`, `LOS = 100.00%`).
  - `fastchess` own final line: `Games: 400, Wins: 228, Losses: 35, Draws: 137, Points: 296.5 (74.12 %) | Elo: 182.83 +/- 27.34, nElo: 273.06 +/- 34.05 | Ptnml(0-2): [0, 14, 37, 91, 58], WL/DD Ratio: 1.31`.
  - Side-by-side checks: non-normal terminations PASS (`0 == 0`), book FEN pairs PASS (`200 == 200`), games PASS (`400 == 400`), pairs PASS (`200 == 200`), `W` PASS (`228 == 228`), `L` PASS (`35 == 35`), `D` PASS (`137 == 137`), pentanomial PASS (`[0, 14, 37, 91, 58] == [0, 14, 37, 91, 58]`), Elo PASS (`+182.83 == +182.83`), `+/- 95%` PASS (`27.34 == 27.34`), **`M0` threshold (`+182.83 > +20.00`) PASS (`True == True`)**.
- **`M1` (`bundle_on` vs `bundle_off`, lines `2,000,001..2,001,500`, `3,000` games):** **NOT DONE** (session ended at `14:28 UTC` in Part M; per owner resume prompt, M1 was not replayed).
- **`M2` (`K4`, `S32`, `B1`, `S13`, `S10`, `B8` singles, lines `2,001,501..2,004,500`, `6 x 1,000` games):** **NOT DONE** (session ended at `14:28 UTC` in Part M; per owner resume prompt, M2 was not replayed here, and `B8` (`078`) moves to Job 41's `M5`).

---

## 4. Facts, Suspicions, Read and Not Tested, What I Did Not Do, What I Am Not Sure About

### Facts
1. **Exact cross-job determinism:** A fresh copy of `r15d + v3` patched with `forge-combo29/carbon2/job39/bundle_grok.patch.txt` reproduced every Step 0 OFF number and reproduced Job 39's all-on `O` depth-12 rows (`8,035,170`, `200 == 200` positions) and `Set A line L` (`27,991` records, `111,242,459` nodes, `c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce`) bit-for-bit across all `18` timed runs of Part T.
2. **Per-node cost decomposition (`Part T`):** Under built-in AVX-512 evaluation (`520.985 us / 1,000 nodes` off, `0.03%` forward-to-reverse drift), **almost the entire `+11.97%` (`1.119705x`) all-on per-node time cost comes from two switches**: `IdeaB1` (`+4.86%`, `fading_board_prior` per quiet move) and `IdeaB8` (`+5.84%`, `find_role_threat` + `quiet_threat_role` + per-quiet `note_threat_swing`). The remaining four switches (`IdeaK4 = 0.9972x`, `IdeaS32 = 0.9914x`, `IdeaS13 = 0.9992x`, `IdeaS10 = 0.9951x`) have zero measurable per-node wall-time overhead on `O`.
3. **Node-limit control (`M0`):** Official `fastchess` (`alpha 1.8.3`, `d6e3a7a`) cleanly honors per-engine `nodes=20000` vs `nodes=10000` with zero non-normal terminations (`0 == 0`), matching `UHO_Lichess_4852_v1.epd` lines `2,100,001..2,100,200` (`200 == 200`) and yielding `+182.83 +/- 27.34` Elo (`PASS: +182.83 > +20.00`), recounted identically from `M0_games.tsv`.

### Suspicions (Apart)
1. **Why per-node % cost will shrink under the PC's v3 net:** Built-in 768->256->1 evaluation takes only `~521 ns/node` total; with the PC's larger v3 net (`net768`/stand-alone v3 takes several microseconds per evaluated node), the fixed `~25-30 ns/node` integer/bitboard cost of `IdeaB1` and `IdeaB8` should represent a much smaller fraction (`~1-3%`) of total wall time per node than `+4.9%` / `+5.8%`.

### Read and Not Tested (Apart)
1. **`fastchess` `pgn_builder.cpp` (`min=true` flag):** Read `/tmp/carbon2_job40/fastchess_repo/app/src/game/pgn/pgn_builder.cpp:67-84` and found that passing `min=true` suppresses `[PlyCount]` and `[Termination]` headers; we therefore ran `-pgnout file=... notation=uci` without `min=true` so every game's `plies` and `termination` are written natively.

### What I Did Not Do
1. **Did not run `M1` (`3,000` games) or `M2` (`6 x 1,000` games):** Our earlier turn hit a session boundary `20s` into `M0` at `14:28 UTC`; upon resume (`15:53 UTC`), we completed and committed `M0` (`400` games) and followed the owner's explicit instruction not to replay `M1` or `M2` before moving to Job 41.
2. **Did not commit any `.pgn`, binary, or archive file** (`/tmp/carbon2_job40/tmp_M0.pgn` was unlinked immediately after generating `M0_games.tsv`).

### What I Am Not Sure About
1. **Whether the bundle's `0.9663x` `O`-set node reduction (`8,035,170 / 8,315,168`) offsets its `1.1197x` per-node time under clock TC with built-in evaluation** (`0.9663 * 1.1197 = 1.082x` depth-12 wall time on `O`: `4.6873s` vs `4.3321s`, whereas on `G` the node ratio was `0.9288x`).

---

## 5. Final Repository Status & Directory Listing (`git status --short && ls -R forge-combo29/carbon2/job40`)

```text
 M forge-combo29/carbon2/job40/stamps.txt
?? forge-combo29/carbon2/job40/REPORT_carbon2_job40.md
forge-combo29/carbon2/job40:
builds.txt
j40_lib.py
M0_fastchess.txt
M0_fastchess.txt.meta
M0_games.tsv
M0_recount.txt
partT_01_fwd_all_off_1.rows.txt
partT_01_fwd_all_off_1.rows.txt.meta
partT_02_fwd_all_off_2.rows.txt
partT_02_fwd_all_off_2.rows.txt.meta
partT_03_fwd_only_K4.rows.txt
partT_03_fwd_only_K4.rows.txt.meta
partT_04_fwd_only_S32.rows.txt
partT_04_fwd_only_S32.rows.txt.meta
partT_05_fwd_only_B1.rows.txt
partT_05_fwd_only_B1.rows.txt.meta
partT_06_fwd_only_S13.rows.txt
partT_06_fwd_only_S13.rows.txt.meta
partT_07_fwd_only_S10.rows.txt
partT_07_fwd_only_S10.rows.txt.meta
partT_08_fwd_only_B8.rows.txt
partT_08_fwd_only_B8.rows.txt.meta
partT_09_fwd_all_on.rows.txt
partT_09_fwd_all_on.rows.txt.meta
partT_10_rev_all_on.rows.txt
partT_10_rev_all_on.rows.txt.meta
partT_11_rev_only_B8.rows.txt
partT_11_rev_only_B8.rows.txt.meta
partT_12_rev_only_S10.rows.txt
partT_12_rev_only_S10.rows.txt.meta
partT_13_rev_only_S13.rows.txt
partT_13_rev_only_S13.rows.txt.meta
partT_14_rev_only_B1.rows.txt
partT_14_rev_only_B1.rows.txt.meta
partT_15_rev_only_S32.rows.txt
partT_15_rev_only_S32.rows.txt.meta
partT_16_rev_only_K4.rows.txt
partT_16_rev_only_K4.rows.txt.meta
partT_17_rev_all_off_2.rows.txt
partT_17_rev_all_off_2.rows.txt.meta
partT_18_rev_all_off_1.rows.txt
partT_18_rev_all_off_1.rows.txt.meta
partT_summary.txt
prediction_job40.txt
recount_pgn.py
REPORT_carbon2_job40.md
run_partM.py
run_partT.py
run_step0.py
stamps.txt
step0_bundle_all_off_O_d12.rows.txt
step0_bundle_all_off_O_d12.rows.txt.meta
step0_bundle_all_on_O_d12.rows.txt
step0_bundle_all_on_O_d12.rows.txt.meta
step0_bundle_all_on_SetA_L.rows.txt
step0_bundle_all_on_SetA_L.rows.txt.meta
step0_raw.txt
```

---

**Model:** `Gemini 4 Carbon` (`carbon2`)
