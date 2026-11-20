# REPORT: `carbon2` Job 42 — `IdeaS13_Hoist` (`P8` + Counter Build) and the Leaders' Bundle (`Part M6`: `IdeaB8b` + `HindsightDepth`)

1. **Step 0 (`PASS`):** `PASS (1 == 1)` (`forge-combo29/carbon2/job42/step0_raw.txt`). Plain `r15d + v3` (`/tmp/carbon2_job36/tpl_r15d_v3`) verified all four source file `sha256`s with `0 == 0` CRLF, passed every OFF lock (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`; `PC20` `278024 == 278024`, `587276 == 587276`; `Set A line L` `26741 == 26741`, `107124743 == 107124743`, `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`; `n[1..60] line L` `8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`), and passed the non-`PC20` `HindsightDepth` known answer (`Threads 1`, `Hash 16`, `OwnBook false`, no `PC20` options, no `Idea*` switch): `HindsightDepth=false` `bench 13` = **`862329 == 862329`** and `HindsightDepth=true` `bench 13` = **`840387 == 840387`**. Applying Job 41's `forge-combo29/carbon2/job41/bundle_grok7.patch.txt` (`git apply --check -p1` `0 == 0`) on a fresh copy (`/tmp/carbon2_job42/src_bundle7`) passed every OFF lock (default off and explicit 7 `false`), passed the non-`PC20` `HindsightDepth` `bench 13` known answer (`862329 == 862329` off, `840387 == 840387` on), and matched Job 41 `P7_bundle7_only_B8b_O_d12.rows.txt` with `IdeaB8b=true` alone on (`8483711 == 8483711`, `200 == 200` positions).
2. **Prediction Graded (`1` of `2` items `TRUE`; `2` of `3` sub-claims `TRUE`):** Committed alone in `d2b5cb103` (`1 file changed`, `forge-combo29/carbon2/job42/prediction_job42.txt`, `sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/prediction_job42.txt) = e38409397f412ffa2f8a950835a6f322e98b86560011b5a8932996e31d3c86d8`, stamp `Fri Nov 20 05:22:46 PM UTC 2026`) before Part P8's first build:
   - `(1)` **P8 (`O` depth 12 node-differing positions, `IdeaS13=true` + `IdeaS13_Hoist=true` vs `IdeaS13=true` alone):** predicted `194` of `200` in `[150, 200]`; observed **`200` of `200`** positions (`150 <= 200 <= 200`) -> **`TRUE`**.
   - `(2)` **M6 (`IdeaB8b` + `HindsightDepth` vs `all_off`, `3,000` games, `nodes=20000`, `PC20`, built-in eval, lines `2,007,501..2,009,000`):**
     - `(2a)` Elo & killing range: predicted `+14.5` Elo in `[+5.0, +24.0]` Elo; observed **`+8.46 +/- 8.18` Elo** (`+5.00 <= +8.46 <= +24.00`, inside range -> sub-claim `TRUE`).
     - `(2b)` Above `max(Job 41 M3=+8.69, M4=+13.73) = +13.73` Elo?: predicted **`YES` (`> +13.73` Elo)**; observed **`+8.46` Elo <= `+13.73` Elo** (`NO` -> sub-claim **`FALSE`**).
     - Whole-item grade for `(2)`: **`FALSE`** (because sub-claim `(2b)` failed).
3. **Part P8 (`PASS`, `1 == 1`, `forge-combo29/carbon2/job42/partP8_summary.txt` & `P8_counter_summary.txt`):** Emitted `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt` (`58` lines, `diff -u` LF `0 == 0` CRLF against `r15d + v3 + bundle_grok7.patch.txt`, `git apply --check -p1` `0 == 0`) adding UCI check option `IdeaS13_Hoist` (`default false`) that hoists `break_prep_order(board, move)` onto the parent position before `board.make_move(move, undo)` for `IdeaS13`'s LMR reduction step:
   - **OFF numbers (`bundle8`, `/tmp/carbon2_job42/bld_bundle8/forge`):** Both default off and all 8 `Idea*` switches explicitly `false` passed every OFF lock (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`; `PC20` `278024 == 278024`, `587276 == 587276`; `Set A line L` `26741 == 26741`, `107124743 == 107124743`, `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`; `n[1..60] line L` `8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`; non-`PC20` `HindsightDepth` `862329 == 862329` off, `840387 == 840387` on; `OFF O` `8315168 == 8315168` `200 == 200`; `OFF G` `17611204 == 17611204` `353 == 353`).
   - **Old switches' identity & hoist-only guard:** `IdeaS13_Hoist=true` with `IdeaS13=false` matched `OFF O` position by position (`8315168 == 8315168`, `200 == 200`); each of the 7 existing switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS10`, `IdeaB8`, `IdeaB8b`) alone on with `IdeaS13_Hoist=false` matched its Job 39 / Job 41 `O` depth-12 rows (`200 == 200` on all 7).
   - **Hoist's `O`, `G`, and `Set A line L` (`IdeaS13=true` + `IdeaS13_Hoist=true`):** `O` depth-12 `sum_nodes` = **`9,069,588`** (first 3: `20,032 / 17,387 / 38,324`; differs from `IdeaS13` alone `8,077,984` on **`200 / 200`** positions [`any=200`, `nodes=200`, `bestmove=47`, `score=192`] and from `OFF O` `8,315,168` on **`200 / 200`** positions [`any=200`, `nodes=200`, `bestmove=53`, `score=192`]); `G` depth-12 `sum_nodes` = **`18,700,461`** (differs from `IdeaS13` alone `17,460,346` on **`342 / 353`** positions [`any=342`, `nodes=342`, `bestmove=79`, `score=314`] and from `OFF G` `17,611,204` on **`344 / 353`** positions [`any=344`, `nodes=344`, `bestmove=78`, `score=318`]); `Set A line L` = **`27,572` records / `27,702` searches / `112,818,443` nodes / `sha256 = 0df6034f20c1269bc3a3b99bf94d3c6d6d2f51ae345827e2cba7d54a330c7d24`**.
   - **Scratch counter build (`P8c`, `/tmp/carbon2_job42/bld_p8_counter/forge`, summed by committed `forge-combo29/carbon2/job42/sum_p8_counters.py`):**
     - `hoist_off` (`IdeaS13=true, IdeaS13_Hoist=false`): **`searches_summed = 200`** (`200 == 200`), `node_sum = 8,077,984` (`200 == 200` row-equal to Job 39 `P4` `S13` alone), **`total_prep_gt0 = 0`** (`0 == 0` total, `0 == 0` max per position, `0 / 200` positions), **`total_shorten_gt0 = 0`** (`0 == 0`).
     - `hoist_on` (`IdeaS13=true, IdeaS13_Hoist=true`): **`searches_summed = 200`** (`200 == 200`), `node_sum = 9,069,588` (`200 == 200` row-equal to clean `bundle8` `S13 + Hoist`), **`total_prep_gt0 = 1,008,057`** (`200 / 200` positions > `0`), **`total_shorten_gt0 (prep >= 1024) = 580,757`** (`200 / 200` positions > `0`).
4. **Part M6 (`COMPLETE`, `3,000 / 3,000` games = `1,500 / 1,500` pairs, `forge-combo29/carbon2/job42/M6_recount.txt` & `M6_games.tsv`):** Played on Job 41's `bundle_grok7` build (`/tmp/carbon2_job42/bld_bundle7/forge`), `PC20`, built-in evaluation, `nodes=20000`, zero adjudication, after pre-checking Job 40/41's `M0` control passed (`+182.83 +/- 27.34` Elo > `+20.00` Elo, `PASS: True == True` in `forge-combo29/carbon2/job41/M0_recount.txt`). Book lines used: **`2,007,501..2,009,000`** of `/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd` (`1500 == 1500` opening FEN pairs verified; `0 == 0` non-normal terminations). Side A (`B8b_HindsightDepth_on` = `IdeaB8b=true` + `HindsightDepth=true`, other 6 `Idea*` `false`) vs Side B (`all_off`):
   - **Recounted from `M6_games.tsv` (`recount_games_tsv`):** W-L-D **`857 - 784 - 1359`** (`51.22%`), pentanomial **`[68, 334, 631, 391, 76]`** (`1,500` pairs), Elo **`+8.46 +/- 8.18` Elo** (`95% CI [+0.27, +16.64]`; `nElo = +12.86 +/- 12.43`, `LOS = 97.87%`).
   - **`fastchess`'s own final line (`M6_fastchess.txt`):** `Games: 3000, Wins: 857, Losses: 784, Draws: 1359, Points: 1536.5 (51.22 %) | Elo: 8.46 +/- 8.18, nElo: 12.86 +/- 12.43 | Ptnml(0-2): [68, 334, 631, 391, 76], WL/DD Ratio: 0.99` (`857 == 857`, `784 == 784`, `1359 == 1359`, `[68, 334, 631, 391, 76] == [68, 334, 631, 391, 76]`, `+8.46 == +8.46`, `8.18 == 8.18`).

Model: `Gemini 4 Carbon`

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 6 Elo; a result with the built-in evaluation does not say what a switch does with the PC's net.

---

## Named Hashes & Executables (`builds.txt`, Patches, and Raw Artifacts)

Every hash below names the exact object hashed beside its path as it exists:

- `r15d + v3` source tree (`/tmp/carbon2_job36/tpl_r15d_v3`, `0 == 0` CRLF on all 4 files):
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77`
- Input patch & `M0` pre-check artifact from Job 41:
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/bundle_grok7.patch.txt) = b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146` (`1,281` lines)
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M0_recount.txt) = 18c4598e34abfd5066c06f3ce18eacf6d640204824070d4a089d3c00a0123776`
- Job 42 prediction, emitted patch, counter raw files, and match files:
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/prediction_job42.txt) = e38409397f412ffa2f8a950835a6f322e98b86560011b5a8932996e31d3c86d8`
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt) = 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326` (`58` lines, `diff -u` against `r15d + v3 + bundle_grok7.patch.txt`)
  - `raw sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_counter_S13_hoist_off_O_d12.raw.txt) = 5df0bfc6c572c8ebd4c7b6a5f0a3491b1964e4373fe15a88f79cc1f54c367fa7`
  - `raw sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_counter_S13_hoist_on_O_d12.raw.txt) = 2127193685c70d1bdf0a4390f8dccbdd9ed817c314d51fd78c9b997a86a98cff`
  - `tsv sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/M6_games.tsv) = ef972bf80fbb795b111bb0afc3ffaf124366dd938793bb370576515106c4716d` (`3,000` games)
  - `stdout sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/M6_fastchess.txt) = 6564d620cfa30b4c3430e101d4efdcfa7b84fb443827732bca024a1915867741`
- Job 42 Release executables (`clang++-18 -O3 -DNDEBUG -march=sapphirerapids -flto=thin`, `id name Chess Engine Forge 6.4.24 candidate`, full flags in `forge-combo29/carbon2/job42/builds.txt`):
  - `exe sha256(/tmp/carbon2_job42/bld_base_v3/forge) = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c` (Step 0 plain `r15d + v3`)
  - `exe sha256(/tmp/carbon2_job42/bld_bundle7/forge) = 98b9ee865072e1691dac642782a2b70a8010e9f5da16de0df877a1548eeed6de` (Step 0 + Part M6 `bundle_grok7`)
  - `exe sha256(/tmp/carbon2_job42/bld_bundle8/forge) = 3ac5cbb1c7f41616b7f987501ff634180dfa166d5958a484396c5e1ba4a381b4` (Part P8 clean `bundle_grok7 + P8_S13_hoist`)
  - `exe sha256(/tmp/carbon2_job42/bld_p8_counter/forge) = ffbf3daae54a562e804bd30de2c8955ce9ac0dc09542fcd433fee178c52e885b` (Part P8c scratch counter build, never used for bundle rows or games)
- Test sets, `fastchess`, and opening book:
  - `set sha256(/tmp/carbon2_job39/sets/first200.fens) = ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (`200` FENs)
  - `set sha256(/tmp/carbon2_job39/sets/set_G.epd) = af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d` (`353` EPDs)
  - `exe sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
  - `book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)

---

## Facts

### 1. Step 0 & Part P8 Deterministic Search Summary (`bundle8`, `PC20`, Built-in Eval)

| Setting on `bundle8` | `O` d12 `sum_nodes` (`200` pos) | `O` Ratio vs OFF | `O` Diff vs Ref (`any` / `nodes` / `bestmove` / `score`) | `G` d12 `sum_nodes` (`353` pos) | `G` Ratio vs OFF | `G` Diff vs Ref (`any` / `nodes` / `bestmove` / `score`) | `Set A line L` (`records` / `searches` / `nodes` / `rows sha256`) |
|---|---:|---:|---|---:|---:|---|---|
| All 8 `Idea*` `false` (`OFF`) | `8,315,168` | `1.000000` | `200 == 200` vs J39 OFF | `17,611,204` | `1.000000` | `353 == 353` vs J39 OFF | `26,741` / `26,862` / `107,124,743` / `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `IdeaS13_Hoist=true`, `IdeaS13=false` | `8,315,168` | `1.000000` | `200 == 200` vs OFF `O` | — | — | — | — |
| Only `IdeaK4=true` (`Hoist=false`) | `8,080,229` | `0.971746` | `200 == 200` vs J39 `P1` | — | — | — | — |
| Only `IdeaS32=true` (`Hoist=false`) | `8,339,315` | `1.002904` | `200 == 200` vs J39 `P2` | — | — | — | — |
| Only `IdeaB1=true` (`Hoist=false`) | `8,548,042` | `1.028006` | `200 == 200` vs J39 `P3` | — | — | — | — |
| Only `IdeaS13=true` (`Hoist=false`) | `8,077,984` | `0.971476` | `200 == 200` vs J39 `P4` | `17,460,346` | `0.991434` | (Job 39 `P4`) | — |
| Only `IdeaS10=true` (`Hoist=false`) | `8,314,153` | `0.999878` | `200 == 200` vs J39 `P5` | — | — | — | — |
| Only `IdeaB8=true` (`Hoist=false`) | `8,262,696` | `0.993690` | `200 == 200` vs J39 `P6` | — | — | — | — |
| Only `IdeaB8b=true` (`Hoist=false`) | `8,483,711` | `1.020269` | `200 == 200` vs J41 `P7` | — | — | — | — |
| **`IdeaS13=true` + `IdeaS13_Hoist=true`** | **`9,069,588`** | **`1.090728`** | **`200 / 200 / 47 / 192` vs `S13` alone**<br>**`200 / 200 / 53 / 192` vs OFF `O`** | **`18,700,461`** | **`1.061850`** | **`342 / 342 / 79 / 314` vs `S13` alone**<br>**`344 / 344 / 78 / 318` vs OFF `G`** | **`27,572` / `27,702` / `112,818,443` / `0df6034f20c1269bc3a3b99bf94d3c6d6d2f51ae345827e2cba7d54a330c7d24`** |

### 2. Why `IdeaS13`'s LMR Site Was Dead Without `IdeaS13_Hoist`, Verified by the Scratch Counter Build (`P8c`)

- In `src/search.cpp`, `Worker::break_prep_order(const Board& board, Move move)` checks `piece_type(board.piece_at(move.from)) <= Pawn` and indexes `(*break_prep_history_)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to]`.
- In `MovePicker` (`src/search.cpp` lines `1019`, `1159`, `1187`, `1241`), `break_prep_order(board_, move)` is called **before** `board.make_move(move, undo)`, so `board.piece_at(move.from)` holds the moving piece and `board.side_to_move()` is the moving side.
- In `IdeaS13`'s original LMR site (`src/search.cpp` line `3032`), `break_prep_order(board, move)` was called **after** `board.make_move(move, undo)`: at that point `board.piece_at(move.from)` is `Empty` (`piece_type(Empty) <= Pawn` returns `0` immediately) and `board.side_to_move()` has already flipped to the opponent.
- On the separate scratch counter build (`/tmp/carbon2_job42/bld_p8_counter/forge`, summed by committed `forge-combo29/carbon2/job42/sum_p8_counters.py` in `P8_counter_summary.txt`):
  - With `IdeaS13=true, IdeaS13_Hoist=false`: `searches_summed = 200` (`PASS: 200 == 200`), `node_sum = 8,077,984` (`PASS: 200 == 200` equal positions vs Job 39 `P4`), **`total_prep_gt0 = 0`** (`PASS: 0 == 0`), **`max_per_pos prep_gt0 = 0`** (`PASS: 0 == 0`), **`positions_with_prep_gt0 = 0`** (`PASS: 0 == 0`), **`total_shorten_gt0 = 0`** (`PASS: 0 == 0`). Across all `8,077,984` nodes of all `200` searches, the un-hoisted LMR site fired **zero times**.
  - With `IdeaS13=true, IdeaS13_Hoist=true`: `searches_summed = 200` (`PASS: 200 == 200`), `node_sum = 9,069,588` (`PASS: 200 == 200` equal positions vs clean `bundle8`), **`total_prep_gt0 = 1,008,057`** across **`200 / 200`** positions (`PASS: True == True`), and **`total_shorten_gt0 (prep >= 1024) = 580,757`** across **`200 / 200`** positions (`PASS: True == True`).

### 3. Part M6 Match Summary (`bundle_grok7`, `PC20`, Built-in Eval, `nodes=20000`, Zero Adjudication)

| Match | Status | Side A vs Side B | Book Lines (`UHO_Lichess_4852_v1.epd`) | Games (Pairs) | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Recounted Elo (`95%` CI) | `fastchess` Own Line Elo (`95%` CI) | Comparison to Job 41 Singles (`M3 = +8.69`, `M4 = +13.73`) |
|---|---|---|---|---:|---|---|---:|---:|---|
| **`M6`** | `COMPLETE` | `B8b_HindsightDepth_on` vs `all_off` | `2,007,501..2,009,000` (`1500 == 1500`) | `3,000` (`1,500`) | `857 - 784 - 1359` | `[68, 334, 631, 391, 76]` | **`+8.46 +/- 8.18`** (`[+0.27, +16.64]`, `LOS 97.87%`) | **`+8.46 +/- 8.18`** (`Ptnml [68, 334, 631, 391, 76]`) | Below `M4` (`+13.73`) by `-5.27` Elo and `M3` (`+8.69`) by `-0.23` Elo; `95%` CI excludes `0.00` (`+0.27` lower bound) |

---

## Suspicions

- **Noise regression toward the mean vs sub-additivity in `M6` (`+8.46 +/- 8.18` Elo):** Across Job 41 (`2,000`g each, `~ +/- 10.3` Elo `95%` CI with built-in evaluation) and Job 42 (`3,000`g, `+/- 8.18` Elo `95%` CI), `M3 = +8.69 +/- 10.21`, `M4 = +13.73 +/- 10.34`, and `M6 = +8.46 +/- 8.18` have overlapping `95%` confidence intervals (`[+0.27, +16.64]` overlaps both `[-1.52, +18.90]` and `[+3.39, +24.07]`). Two mechanisms could contribute to `M6` landing at `+8.46` rather than `~ +15..+22`: (a) upward sampling noise in Job 41's `M4` (`+13.73 +/- 10.34` vs Grok swarm 2's `+6.75` Elo for `HindsightDepth`), and/or (b) mild sub-additivity between `IdeaB8b` (reshaping quiet move ordering and LMR history via threat-role memory) and `HindsightDepth` (adjusting child depth / history from parent+child static eval sum `-ss->static_eval - (ss+1)->static_eval`), or built-in-eval static eval scale mismatch on `HindsightDepth`'s centipawn thresholds. Built-in-eval fixed-node games at `+/- 8.18` Elo cannot separate sampling variance from true sub-additivity.
- **`IdeaS13_Hoist` (`P8`) LMR aggressiveness (`+9.07%` fixed-depth `O` nodes, `580,757` `r -= 1` shortenings across `200` `O` searches):** Because `credit_break_prep` (`src/search.cpp` lines `1820-1834`) applies only positive `history_bonus(depth)` updates and never applies maluses on failed quiet moves, `break_prep_history_` entries monotonically climb toward saturation; once hoisted, `prep >= 1024` (`IdeaS13_ReduceDivisor = 1024`) triggers `shorten = 1` (`r -= 1`) on `57.6%` (`580,757 / 1,008,057`) of all quiet LMR checks with `prep > 0`, expanding `O` depth-12 trees by `+12.28%` over `IdeaS13` alone (`9,069,588 / 8,077,984`). Whether that `1`-ply LMR reduction relief helps or over-extends quiet moves in game play was not match-tested in Job 42 and may want either a match check or a higher `IdeaS13_ReduceDivisor` / malus test if it over-searches weak quiet moves.

---

## Read and Not Tested

- **Upstream `grok-016` (`IdeaS13`) intent vs implementation:** Read `Worker::break_prep_order` and `Worker::credit_break_prep` (`src/search.cpp` lines `1814-1834`) and the four `MovePicker` call sites (`lines 1019, 1159, 1187, 1241`). `credit_break_prep` only applies positive bonuses (`back = 2, 4` plies earlier on same `pawn_key`) with no negative malus on quiet moves tried before a pawn break, and `IdeaS13_Hoist` was not match-tested (`fastchess`) in Job 42 (`FABLE_TO_carbon2_42.md` scoped Part P8 to patch + known answers + `O`/`G`/`Set A line L` rows + counter build, and Part M6 to `IdeaB8b + HindsightDepth` on Job 41's `bundle_grok7`).
- **Time-controlled (`STC`/`LTC`) and `v3`-net behavior of `IdeaB8b + HindsightDepth`:** In Job 41 Part T (`built-in eval`), `IdeaB8b` had `+7.13%` `ms / 1,000 nodes` overhead and `HindsightDepth` had `+1.76%` `ms / 1,000 nodes` overhead; with the `v3` NNUE net, NNUE evaluation dominates per-node time so `IdeaB8b`'s relative time overhead per node should shrink substantially, while `HindsightDepth`'s static-eval thresholds were tuned/designed around NNUE centipawn scaling. Neither `v3`-net node counts nor clock-based games can be tested in this environment without the PC's net.

---

## What I Did Not Do

- Did **not** play a match (`fastchess`) with `IdeaS13 + IdeaS13_Hoist` (`bundle8`); Part M6 tested `IdeaB8b + HindsightDepth` on Job 41's `bundle_grok7` per specification.
- Did **not** test with the PC's `v3` NNUE weights file or under wall-clock time controls.
- Did **not** modify any tracked engine source file in `/agent/repos/dwqww`, create any pull request, touch any other branch, or commit any binary, `.pgn`, or `.pyc` file.

---

## What I Am Not Sure About

- Whether `IdeaB8b` and `HindsightDepth` combine additively or sub-additively with the PC's `v3` NNUE net (`M6`'s `+8.46 +/- 8.18` Elo with built-in evaluation proves the two-leader bundle has no destructive interaction and beats `all_off` at `97.87%` LOS, but `+/- 8.18` Elo cannot resolve whether true built-in-eval bundle gain is `+8` Elo or `+15` Elo).
- Whether `IdeaS13 + IdeaS13_Hoist` improves playing strength once its `580,757` LMR `r -= 1` shortenings (`O` d12) become live, since Job 39/Grok swarm 2's earlier `IdeaS13` match results only tested `IdeaS13`'s move-ordering path while its LMR path was `0 == 0` dead.

---

## UTC Timestamps (`forge-combo29/carbon2/job42/stamps.txt`)

```text
job42_claimed: Fri Nov 20 05:17:29 PM UTC 2026 (Minute 80 = +80m from this stamp)
step0_done: Fri Nov 20 05:22:07 PM UTC 2026
partP8_done: Fri Nov 20 05:30:36 PM UTC 2026
partM6_done: Fri Nov 20 05:57:50 PM UTC 2026
report_done: Fri Nov 20 05:58:51 PM UTC 2026
```

---

## Final `git status --short && ls -R forge-combo29/carbon2/job42` Before Report Commit

```text
 M forge-combo29/carbon2/job42/stamps.txt
?? forge-combo29/carbon2/job42/REPORT_carbon2_job42.md
forge-combo29/carbon2/job42:
build_and_verify_p8.py
builds.txt
j42_lib.py
M6_fastchess.txt
M6_fastchess.txt.meta
M6_games.tsv
M6_recount.txt
P8_bundle8_all_off_G_d12.rows.txt
P8_bundle8_all_off_G_d12.rows.txt.meta
P8_bundle8_all_off_O_d12.rows.txt
P8_bundle8_all_off_O_d12.rows.txt.meta
P8_bundle8_only_B1_O_d12.rows.txt
P8_bundle8_only_B1_O_d12.rows.txt.meta
P8_bundle8_only_B8b_O_d12.rows.txt
P8_bundle8_only_B8b_O_d12.rows.txt.meta
P8_bundle8_only_B8_O_d12.rows.txt
P8_bundle8_only_B8_O_d12.rows.txt.meta
P8_bundle8_only_Hoist_S13_off_O_d12.rows.txt
P8_bundle8_only_Hoist_S13_off_O_d12.rows.txt.meta
P8_bundle8_only_K4_O_d12.rows.txt
P8_bundle8_only_K4_O_d12.rows.txt.meta
P8_bundle8_only_S10_O_d12.rows.txt
P8_bundle8_only_S10_O_d12.rows.txt.meta
P8_bundle8_only_S13_O_d12.rows.txt
P8_bundle8_only_S13_O_d12.rows.txt.meta
P8_bundle8_only_S32_O_d12.rows.txt
P8_bundle8_only_S32_O_d12.rows.txt.meta
P8_bundle8_S13_and_Hoist_G_d12.rows.txt
P8_bundle8_S13_and_Hoist_G_d12.rows.txt.meta
P8_bundle8_S13_and_Hoist_O_d12.rows.txt
P8_bundle8_S13_and_Hoist_O_d12.rows.txt.meta
P8_bundle8_S13_and_Hoist_SetA_L.rows.txt
P8_bundle8_S13_and_Hoist_SetA_L.rows.txt.meta
P8_counter_S13_hoist_off_O_d12.raw.txt
P8_counter_S13_hoist_off_O_d12.raw.txt.meta
P8_counter_S13_hoist_on_O_d12.raw.txt
P8_counter_S13_hoist_on_O_d12.raw.txt.meta
P8_counter_summary.txt
P8_S13_hoist.patch.txt
partP8_summary.txt
prediction_job42.txt
REPORT_carbon2_job42.md
run_partM6.py
run_step0.py
stamps.txt
step0_bundle7_only_IdeaB8b_O_d12.rows.txt
step0_bundle7_only_IdeaB8b_O_d12.rows.txt.meta
step0_raw.txt
sum_p8_counters.py
```
