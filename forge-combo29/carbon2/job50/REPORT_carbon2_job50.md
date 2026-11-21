# Carbon2 Job 50 Report: `HindsightDepth`'s Lower Step at Stockfish's Thresholds (`HdLowerWithheld=2`, `HdLowerDepth=2`, `HdLowerLoss=167`, `2,000` and `20,000` Nodes)

## 1. Step 0 — Pins, `K4` (`840,387`), `(a)`/`(b)`/`(c)` `O` & `G` Row-by-Row Checks, and `(d)` Planted `HdLowerLos=167` Stop

- **Executables verified (`forge-combo29/carbon2/job50/builds.txt`):**
  - Base `bundle9`: `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
  - Patched `bundle12` (`bundle9 + P12_hd_lower.patch.txt`): `/tmp/carbon2_job50/bld_bundle12/forge` (`sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Step 0 `(d)` planted misspelt option check (`HdLowerLos=167`):** `run_epd_depth12_strict` sent `setoption name HdLowerLos value 167` followed by `isready`, kept every pre-`readyok` line, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`info string unknown option HdLowerLos`**
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job50/step0_raw.txt`):**
- `bundle9 exe sha256(/tmp/carbon2_job44/bld_bundle9/forge): PASS (9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef)`
- `Step 0 (d) planted HdLowerLos=167 stopped runner via EngineReplyStopError: PASS (True == True)`
- `Step 0 (d) planted stop marker              : PASS (unknown option == unknown option)`
- `Step 0 (d) planted search rows file not written (0 searches run): PASS (False == False)`
- `bundle12 no-option bench 11                 : PASS (312866 == 312866)`
- `bundle12 no-option bench 13                 : PASS (862329 == 862329)`
- `bundle12 no-option perft 5                  : PASS (4865609 == 4865609)`
- `bundle12 PC20 (default off) bench 11        : PASS (278024 == 278024)`
- `bundle12 PC20 (default off) bench 13        : PASS (587276 == 587276)`
- `bundle12 PC20 (explicit 10 false + HdLower defaults) bench 11: PASS (278024 == 278024)`
- `bundle12 PC20 (explicit 10 false + HdLower defaults) bench 13: PASS (587276 == 587276)`
- `Step 0 K4 bundle9 bench 13 (HindsightDepth=true, no other option): PASS (840387 == 840387)`
- `Step 0 K4 bundle12 bench 13 (HindsightDepth=true, implicit defaults): PASS (840387 == 840387)`
- `Step 0 K4 bundle12 bench 13 (HindsightDepth=true, explicit 1/1/100): PASS (840387 == 840387)`
- `Step 0 (a) bundle12 all_off O d12 sum vs known 8315168: PASS (8315168 == 8315168)`
- `Step 0 (a) bundle12 all_off O d12 nodes+bestmove equal vs job48 Step 0: PASS (200 == 200)`
- `Step 0 (a) bundle12 all_off O d12 full-row equal vs job48 Step 0: PASS (200 == 200)`
- `Step 0 (a) bundle12 all_off G d12 sum vs known 17611204: PASS (17611204 == 17611204)`
- `Step 0 (a) bundle12 all_off G d12 nodes+bestmove equal vs job48 Step 0: PASS (353 == 353)`
- `Step 0 (a) bundle12 all_off G d12 full-row equal vs job48 Step 0: PASS (353 == 353)`
- `Step 0 (b) K2 HD=true defaults O d12 sum (bundle12 vs bundle9): PASS (8732910 == 8732910)`
- `Step 0 (b) K2 HD=true defaults O d12 nodes+bestmove equal (bundle12 vs bundle9): PASS (200 == 200)`
- `Step 0 (b) K2 HD=true defaults O d12 full-row equal (bundle12 vs bundle9): PASS (200 == 200)`
- `Step 0 (b) K2 HD=true explicit 1/1/100 O d12 sum vs implicit defaults: PASS (8732910 == 8732910)`
- `Step 0 (b) K2 HD=true explicit 1/1/100 O d12 full-row equal vs implicit: PASS (200 == 200)`
- `Step 0 (b) K2 HD=true defaults G d12 sum (bundle12 vs bundle9): PASS (17555215 == 17555215)`
- `Step 0 (b) K2 HD=true defaults G d12 nodes+bestmove equal (bundle12 vs bundle9): PASS (353 == 353)`
- `Step 0 (b) K2 HD=true defaults G d12 full-row equal (bundle12 vs bundle9): PASS (353 == 353)`
- `Step 0 (c) K3 HD=false (8/16/400) O d12 sum vs (a): PASS (8315168 == 8315168)`
- `Step 0 (c) K3 HD=false (8/16/400) O d12 nodes+bestmove equal vs (a): PASS (200 == 200)`
- `Step 0 (c) K3 HD=false (8/16/400) O d12 full-row equal vs (a): PASS (200 == 200)`
- `Step 0 (c) K3 HD=false (8/16/400) G d12 sum vs (a): PASS (17611204 == 17611204)`
- `Step 0 (c) K3 HD=false (8/16/400) G d12 nodes+bestmove equal vs (a): PASS (353 == 353)`
- `Step 0 (c) K3 HD=false (8/16/400) G d12 full-row equal vs (a): PASS (353 == 353)`
- `STEP 0 OVERALL                              : PASS (1 == 1)`

---

## 2. Part P12 — Diff Summary (`forge-combo29/carbon2/job50/P12_hd_lower.patch.txt`)

- **Patch file:** `forge-combo29/carbon2/job50/P12_hd_lower.patch.txt` (`sha256 = 4b4000cce46dd057c4fabef1984480053164a9a4bac053314c6012d999c9d971`, `0 == 0` CRLF), applied cleanly on `bundle9` (`/tmp/carbon2_job50/src_bundle12`).
- **`SeePieceValue[Pawn]` check (`/tmp/carbon2_job36/tpl_r15d_v3/include/forge/eval.hpp:32`):** `SeePieceValue{0, 100, 300, 300, 500, 900, 0}` -> `SeePieceValue[Pawn] = 100` (`PASS (100 == 100)`), so `HdLowerLoss` defaults to `100`.
- **Exact files and lines changed (against `bundle9` source tree `/tmp/carbon2_job50/src_bundle12`):**
  1. `include/forge/search.hpp` (`lines 321–323` in `bundle12`, after `extern bool HindsightDepth;` at line `320`): declares `extern int HdLowerWithheld;`, `extern int HdLowerDepth;`, `extern int HdLowerLoss;` in `namespace forge::tune`.
  2. `src/search.cpp` (`lines 157–159` in `bundle12`): defines defaults `int HdLowerWithheld = 1;`, `int HdLowerDepth = 1;`, `int HdLowerLoss = 100;`.
  3. `src/search.cpp` (`lines 262–264` in `bundle12`, inside `forge::tune::parameters()`): registers `{"HdLowerWithheld", &HdLowerWithheld, 1, 8}`, `{"HdLowerDepth", &HdLowerDepth, 1, 16}`, `{"HdLowerLoss", &HdLowerLoss, 1, 400}` (automatically advertised by `uci` under `-DFORGE_EXPOSE_TUNABLES=1` and parsed/range-checked by `setoption` in `src/uci.cpp:855–862`).
  4. `src/search.cpp` (`lines 2704–2705` in `bundle12`, replacing single line `2699` of `bundle9` inside `Worker::search`'s `HindsightDepth` block; raise step at line `2706`, hash test at line `2707`, and `qsearch_child` return at lines `2709–2712` untouched):
     `if (withheld >= tune::HdLowerWithheld && depth >= tune::HdLowerDepth && mover_loss >= tune::HdLowerLoss) proposed = depth - 1;`

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -318,6 +318,9 @@
 extern bool LmrSignedCorrection;     // quiet LMR: signed fraction of a ply from correction history (false = off)
 extern bool LmrLateParentRelief;     // one ply less reduction on the first few replies after a late parent (false = off)
 extern bool HindsightDepth;          // off-PV depth step after a reduced move (false = off)
+extern int HdLowerWithheld;          // HindsightDepth lower step minimum withheld plies (default 1, range 1..8)
+extern int HdLowerDepth;             // HindsightDepth lower step minimum depth (default 1, range 1..16)
+extern int HdLowerLoss;              // HindsightDepth lower step minimum mover_loss in cp (default 100, range 1..400)
 extern bool IdeaK4;                  // smaller reverse-futility margin when the opponent worsened (false = off)
 extern int IdeaK4_Shrink;            // centipawns removed from the reverse-futility margin when IdeaK4 fires
 extern bool NullThreatVerify;        // null cutoff needs a reduced non-null search when a cheaper enemy piece attacks a dearer piece (false = off)
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -154,6 +154,9 @@
 int IdeaB8_Swing = 48;
 int IdeaB8b_Weight = 1024;
 int IdeaB8b_Swing = 40;
+int HdLowerWithheld = 1;
+int HdLowerDepth = 1;
+int HdLowerLoss = 100;
 // packc28 (ported into forge/r12 on 2026-11-15, see forge/tools/make_r12_e.py): three ideas, all 0 = off.
 int AspFailHighReduce = 0;      // 1: after a root fail-high the re-search is one ply shallower per fail-high in a row
 int AspFailHighMaxReduce = 3;   //    ... by at most this many plies
@@ -256,6 +259,9 @@
         {"IdeaB8_Weight", &IdeaB8_Weight, 0, 4096},              {"IdeaB8_Swing", &IdeaB8_Swing, 0, 500},
         {"IdeaB8b_Weight", &IdeaB8b_Weight, 0, 4096},
         {"IdeaB8b_Swing", &IdeaB8b_Swing, 0, 500},
+        {"HdLowerWithheld", &HdLowerWithheld, 1, 8},
+        {"HdLowerDepth", &HdLowerDepth, 1, 16},
+        {"HdLowerLoss", &HdLowerLoss, 1, 400},
 #if FORGE_PAWN_HISTORY
         {"PawnHistory", &PawnHistory, 0, 1},                     {"PawnHistoryBits", &PawnHistoryBits, 9, 13},
         {"PawnHistoryWeight", &PawnHistoryWeight, 0, 200},       {"PawnHistoryPvBonus", &PawnHistoryPvBonus, 0, 1},
@@ -2696,7 +2702,8 @@
                 }
                 const int mover_loss = parent_eval + corrected_eval(board, raw, ss);
                 int proposed = depth;
-                if (mover_loss >= SeePieceValue[Pawn]) proposed = depth - 1;
+                if (withheld >= tune::HdLowerWithheld && depth >= tune::HdLowerDepth && mover_loss >= tune::HdLowerLoss)
+                    proposed = depth - 1;
                 else if (mover_loss <= 0 && withheld >= 3) proposed = depth + 1;
                 if (proposed != depth && !(tt_hit && tt_depth >= proposed)) {
                     depth = proposed;
```

- **Part P12 build `PASS` lines (`forge-combo29/carbon2/job50/p12_summary.txt`):**
- `src/search.cpp CRLF count                   : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp): PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)`
- `src/uci.cpp CRLF count                      : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp): PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)`
- `src/board.cpp CRLF count                    : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp): PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)`
- `include/forge/board.hpp CRLF count          : PASS (0 == 0)`
- `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp): PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)`
- `eval.hpp SeePieceValue[Pawn] (index 1)      : PASS (100 == 100)`
- `bundle9 exe sha256(/tmp/carbon2_job44/bld_bundle9/forge): PASS (9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef)`
- `P12_hd_lower.patch.txt CRLF count           : PASS (0 == 0)`
- `git apply --check -p1 P12_hd_lower.patch.txt on bundle9: PASS (0 == 0)`
- `git apply -p1 P12_hd_lower.patch.txt on bundle9: PASS (0 == 0)`
- `bundle12 include/forge/search.hpp CRLF count: PASS (0 == 0)`
- `bundle12 src/search.cpp CRLF count          : PASS (0 == 0)`
- `PART P12 OVERALL                            : PASS (1 == 1)`

---

## 3. Part L2 — Depth-12 Liveness on `O` (`200` Positions, `PC20 + HindsightDepth=true`, `bundle12`)

- **Reference row set (Step 0 `(b)` defaults `1, 1, 100`):** `forge-combo29/carbon2/job50/step0_b_bundle12_HD_defaults_O_d12.rows.txt` (`sha256 = 595de758c240a9aa445ad439816d7f8f73e5c457b7b3272ffa7f8eaac48e1bea`, `O` sum = `8,732,910` nodes).
- **Result:** All three options (`HdLowerWithheld=2`, `HdLowerDepth=2`, `HdLowerLoss=167`) and `all_three` are **`LIVE`** (`0` dead options), so all three are included in `M18` Side A.

| Option Setting (`PC20 + HindsightDepth=true`) | `O` Depth-12 Node Sum | Delta vs Defaults (`%`) | Nodes Differ (`/ 200`) | Best Moves Differ (`/ 200`) | Scores Differ (`/ 200`) | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `Defaults (1, 1, 100)` (Step 0 `(b)` ref) | `8,732,910` | `+0` (`+0.00%`) | `0 / 200` | `0 / 200` | `0 / 200` | baseline |
| `HdLowerWithheld=2` | `8,772,845` | `+39,935` (`+0.46%`) | `183 / 200` | `23 / 200` | `116 / 200` | **`LIVE`** |
| `HdLowerDepth=2` | `8,781,257` | `+48,347` (`+0.55%`) | `100 / 200` | `5 / 200` | `27 / 200` | **`LIVE`** |
| `HdLowerLoss=167` | `8,526,306` | `-206,604` (`-2.37%`) | `200 / 200` | `36 / 200` | `171 / 200` | **`LIVE`** |
| `all_three (2, 2, 167)` | `8,519,678` | `-213,232` (`-2.44%`) | `200 / 200` | `35 / 200` | `171 / 200` | **`LIVE`** |

---

## 4. Prediction Graded (`forge-combo29/carbon2/job50/prediction_job50.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `85b035c8d` after Part L2 and before the first game of `M18` (with our blind pre-L2 `O` node-sum direction note committed even earlier in `1c9b351f1` before `bundle12`, Step 0, or Part L2 ran):

```text
85b035c8d carbon2 job50: commit prediction_job50.txt alone after Part L2 and before M18 (2026-11-21 01:19:57 +0000)

 forge-combo29/carbon2/job50/prediction_job50.txt | 31 ++++++++++++++++++++++++
 1 file changed, 31 insertions(+)
```

- **Grading summary:** Blind pre-L2 `all_three` `O` node-sum direction prediction: **`0 / 1` (`FALSE`)**; per-match Side A Elo predictions: **`1 / 3` `TRUE`** (`M19-2k` `TRUE`, `M18-2k` and `M18-20k` `FALSE`).

| Item | Prediction | Falsification Criterion | Observed | Grade |
| --- | --- | --- | --- | --- |
| Part L2 `all_three` `O` node sum vs defaults (`8,732,910`) | `ABOVE` (blind pre-L2 in `1c9b351f1`) | `<= 8,732,910` (`BELOW` or `EQUAL`) | **`8,519,678`** (`-213,232`, `BELOW`) | **`FALSE (FALSIFIED)`** |
| `M18-2k` (`nodes=2,000`, `HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) | `+2.0` Elo | outside `[-5.0, +9.0]` | **`-6.08 +/- 4.76`** (`[-10.84, -1.32]`) | **`FALSE (MISSED)`** (`-6.08` outside `[-5.0, +9.0]`) |
| `M18-20k` (`nodes=20,000`, `HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) | `+2.5` Elo | outside `[-8.0, +13.0]` | **`-9.50 +/- 8.09`** (`[-17.59, -1.41]`) | **`FALSE (MISSED)`** (`-9.50` outside `[-8.0, +13.0]`) |
| `M19-2k` (`nodes=2,000`, `HdLowerLoss=167`) | `+2.0` Elo | outside `[-5.0, +9.0]` | **`+0.61 +/- 4.71`** (`[-4.10, +5.31]`) | **`TRUE (HELD)`** (`-5.0 <= +0.61 <= +9.0`) |

---

## 5. Parts M18 and M19 — Matches (`bundle12`, Whole Bundle `IdeaB8b + HindsightDepth` on Both Sides Under `PC20`)

- **Common match settings:** `/tmp/carbon2_job50/bld_bundle12/forge` (`sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e`), base options programmatically parsed from `forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta` (`PC20 + IdeaB8b=true + HindsightDepth=true`, `Threads=1`, `Hash=16`, `OwnBook=false`), sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,075,001..2,088,500`), `concurrency=4`. Side B adds nothing (runs defaults `1, 1, 100`).
- **Part M19 25-minute gate check after `M18`:** `44.36 minutes remaining before Minute 80 (>= 25.0 required) and HdLowerLoss=167 LIVE`.

### Summary of Matches (2,000-Node and 20,000-Node Matches Quoted Strictly Apart)

| Match (`Part`) | Nodes | Side A Thresholds Added | UHO Lines | Status (`Games`) | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Side A vs Side B Elo +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M18-2k` (`M18`) | `2,000` | `HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167` | `2,075,001..2,081,000` | `COMPLETE` (`12,000`) | `4024-4234-3742` | `[593, 1290, 2404, 1160, 553]` | **`-6.08 +/- 4.76`** (`[-10.84, -1.32]`) | `FALSE (pred +2.0, [-5.0, +9.0])` |
| `M18-20k` (`M18`) | `20,000` | `HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167` | `2,081,001..2,082,500` | `COMPLETE` (`3,000`) | `779-861-1360` | `[76, 392, 627, 348, 57]` | **`-9.50 +/- 8.09`** (`[-17.59, -1.41]`) | `FALSE (pred +2.5, [-8.0, +13.0])` |
| `M19-2k` (`M19`) | `2,000` | `HdLowerLoss=167` | `2,082,501..2,088,500` | `COMPLETE` (`12,000`) | `4051-4030-3919` | `[517, 1320, 2345, 1261, 557]` | **`+0.61 +/- 4.71`** (`[-4.10, +5.31]`) | `TRUE (pred +2.0, [-5.0, +9.0])` |

### `M18-2k` vs `M19-2k` at `nodes=2,000` (Quoted Strictly at `2,000` Nodes; `se = sqrt(se_18^2 + se_19^2)`)

| Nodes / Move | `M18-2k` (`Withheld=2, Depth=2, Loss=167`) | `M19-2k` (`Loss=167` Only) | `M18-2k - M19-2k` +/- 95% (`[CI]`) | 95% CI Excludes `0`? |
| --- | --- | --- | --- | --- |
| `2,000` | `-6.08 +/- 4.76` | `+0.61 +/- 4.71` | **`-6.69 +/- 6.70 [-13.39, +0.01]`** | `NO (crosses 0)` |

### `M18-2k` (`Part M18`) — `nodes=2,000`, Side A `sf_hd_lower_bundle_PC20` (`HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) vs Side B `ours_hd_lower_bundle_PC20` (defaults `1, 1, 100`), UHO `2,075,001..2,081,000`
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `480.087s`, `start_utc`: `Sat Nov 21 01:21:22 AM UTC 2026`, `end_utc`: `Sat Nov 21 01:29:22 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job50/bld_bundle12/forge`):** `sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e` (`id name Chess Engine Forge 6.4.24 candidate`)
- **Base options copied programmatically from:** `/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta`
- **UCI preflight checks:** Side A `35` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job50/M18-2k_recount.txt`):** `W-L-D = 4024-4234-3742`, pentanomial `[593, 1290, 2404, 1160, 553]`, **`-6.08 +/- 4.76`** (`[-10.84, -1.32]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job50/M18-2k_fastchess.txt`):** `Games: 12000, Wins: 4024, Losses: 4234, Draws: 3742, Points: 5895.0 (49.12 %) | Elo: -6.08 +/- 4.76, nElo: -7.95 +/- 6.22 | Ptnml(0-2): [593, 1290, 2404, 1160, 553], WL/DD Ratio: 2.72`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M18-2k_games.tsv`):** `sha256 = 39486c004c216f9285b85fe5e96369d8452800a09fc7c0d8069d17e0df1dbd92`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M18-2k_fastchess.txt`):** `sha256 = 18f490484cc6d78e3dbcf3f2af74ba0f9a5543dd1a97e8dbaf51d1ddb2d0ac1e`
- **Command (`M18-2k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=sf_hd_lower_bundle_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true option.HdLowerWithheld=2 option.HdLowerDepth=2 option.HdLowerLoss=167 -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=ours_hd_lower_bundle_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2075001 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job50/tmp_M18-2k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M18-2k non-normal terminations              : PASS (0 == 0)`
  - `M18-2k opening FEN pairs matching book slice: PASS (6000 == 6000)`
  - `M18-2k finished games vs target             : PASS (12000 == 12000)`
  - `M18-2k finished pairs vs target             : PASS (6000 == 6000)`
  - `M18-2k recount W vs fastchess               : PASS (4024 == 4024)`
  - `M18-2k recount L vs fastchess               : PASS (4234 == 4234)`
  - `M18-2k recount D vs fastchess               : PASS (3742 == 3742)`
  - `M18-2k recount ptnml vs fastchess           : PASS ([593, 1290, 2404, 1160, 553] == [593, 1290, 2404, 1160, 553])`
  - `M18-2k recount Elo vs fastchess             : PASS (-6.08 == -6.08)`
  - `M18-2k recount +/-95% vs fastchess          : PASS (4.76 == 4.76)`
  - `M18-2k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M18-20k` (`Part M18`) — `nodes=20,000`, Side A `sf_hd_lower_bundle_PC20` (`HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) vs Side B `ours_hd_lower_bundle_PC20` (defaults `1, 1, 100`), UHO `2,081,001..2,082,500`
- **Status:** `COMPLETE` (`3,000` games, `1,500` pairs, wall `1002.331s`, `start_utc`: `Sat Nov 21 01:29:25 AM UTC 2026`, `end_utc`: `Sat Nov 21 01:46:07 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job50/bld_bundle12/forge`):** `sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e` (`id name Chess Engine Forge 6.4.24 candidate`)
- **Base options copied programmatically from:** `/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta`
- **UCI preflight checks:** Side A `35` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job50/M18-20k_recount.txt`):** `W-L-D = 779-861-1360`, pentanomial `[76, 392, 627, 348, 57]`, **`-9.50 +/- 8.09`** (`[-17.59, -1.41]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job50/M18-20k_fastchess.txt`):** `Games: 3000, Wins: 779, Losses: 861, Draws: 1360, Points: 1459.0 (48.63 %) | Elo: -9.50 +/- 8.09, nElo: -14.61 +/- 12.43 | Ptnml(0-2): [76, 392, 627, 348, 57], WL/DD Ratio: 1.02`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M18-20k_games.tsv`):** `sha256 = 6a31eaa9c518e851a937f22897cd5b97767be6b4f73d56d691732d3f0593aae7`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M18-20k_fastchess.txt`):** `sha256 = 5c92e1bedab3ed8f556c8a8b9e51d6e55ab285fe85a46fd1b65f6f13e2fc193f`
- **Command (`M18-20k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=sf_hd_lower_bundle_PC20 nodes=20000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true option.HdLowerWithheld=2 option.HdLowerDepth=2 option.HdLowerLoss=167 -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=ours_hd_lower_bundle_PC20 nodes=20000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2081001 -rounds 1500 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job50/tmp_M18-20k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M18-20k non-normal terminations             : PASS (0 == 0)`
  - `M18-20k opening FEN pairs matching book slice: PASS (1500 == 1500)`
  - `M18-20k finished games vs target            : PASS (3000 == 3000)`
  - `M18-20k finished pairs vs target            : PASS (1500 == 1500)`
  - `M18-20k recount W vs fastchess              : PASS (779 == 779)`
  - `M18-20k recount L vs fastchess              : PASS (861 == 861)`
  - `M18-20k recount D vs fastchess              : PASS (1360 == 1360)`
  - `M18-20k recount ptnml vs fastchess          : PASS ([76, 392, 627, 348, 57] == [76, 392, 627, 348, 57])`
  - `M18-20k recount Elo vs fastchess            : PASS (-9.50 == -9.50)`
  - `M18-20k recount +/-95% vs fastchess         : PASS (8.09 == 8.09)`
  - `M18-20k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`
### `M19-2k` (`Part M19`) — `nodes=2,000`, Side A `sf_hd_loss167_bundle_PC20` (`HdLowerLoss=167`) vs Side B `ours_hd_lower_bundle_PC20` (defaults `1, 1, 100`), UHO `2,082,501..2,088,500`
- **Status:** `COMPLETE` (`12,000` games, `6,000` pairs, wall `482.080s`, `start_utc`: `Sat Nov 21 01:46:10 AM UTC 2026`, `end_utc`: `Sat Nov 21 01:54:12 AM UTC 2026`)
- **Executable (`/tmp/carbon2_job50/bld_bundle12/forge`):** `sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e` (`id name Chess Engine Forge 6.4.24 candidate`)
- **Base options copied programmatically from:** `/agent/repos/dwqww/forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta`
- **UCI preflight checks:** Side A `33` options verified in `uci` list (`0` pre-`readyok` lines); Side B `32` options verified in `uci` list (`0` pre-`readyok` lines)
- **Committed recount (`forge-combo29/carbon2/job50/M19-2k_recount.txt`):** `W-L-D = 4051-4030-3919`, pentanomial `[517, 1320, 2345, 1261, 557]`, **`+0.61 +/- 4.71`** (`[-4.10, +5.31]`) Elo
- **Fastchess own line (`forge-combo29/carbon2/job50/M19-2k_fastchess.txt`):** `Games: 12000, Wins: 4051, Losses: 4030, Draws: 3919, Points: 6010.5 (50.09 %) | Elo: 0.61 +/- 4.71, nElo: 0.80 +/- 6.22 | Ptnml(0-2): [517, 1320, 2345, 1261, 557], WL/DD Ratio: 2.51`
- **Per-game list (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M19-2k_games.tsv`):** `sha256 = 538df59f055522ae4a53be0a695cd8c087c1a011091fef7968656bfb38b52c94`
- **Fastchess stdout (`/agent/repos/dwqww/forge-combo29/carbon2/job50/M19-2k_fastchess.txt`):** `sha256 = 81139a2d56b92a23a5d62ef2c5e415e6a8e80f7da239328349d6d7815d1a487e`
- **Command (`M19-2k_fastchess.txt.meta`):**
  `/tmp/carbon2_job40/fastchess -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=sf_hd_loss167_bundle_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true option.HdLowerLoss=167 -engine cmd=/tmp/carbon2_job50/bld_bundle12/forge name=ours_hd_lower_bundle_PC20 nodes=2000 option.IdeaK4=false option.IdeaS32=false option.IdeaB1=false option.IdeaS13=false option.IdeaS13_Hoist=false option.IdeaS10=false option.IdeaB8=false option.IdeaB8_Fast=false option.IdeaB8b=true option.HindsightDepth=true -each proto=uci option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.MateAlphaGuard=true option.OwnBook=false option.Threads=1 option.Hash=16 -openings file=/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd format=epd order=sequential start=2082501 -rounds 6000 -games 2 -repeat -concurrency 4 -pgnout file=/tmp/carbon2_job50/tmp_M19-2k.pgn notation=uci -ratinginterval 100`
- **Recount `PASS` checks:**
  - `M19-2k non-normal terminations              : PASS (0 == 0)`
  - `M19-2k opening FEN pairs matching book slice: PASS (6000 == 6000)`
  - `M19-2k finished games vs target             : PASS (12000 == 12000)`
  - `M19-2k finished pairs vs target             : PASS (6000 == 6000)`
  - `M19-2k recount W vs fastchess               : PASS (4051 == 4051)`
  - `M19-2k recount L vs fastchess               : PASS (4030 == 4030)`
  - `M19-2k recount D vs fastchess               : PASS (3919 == 3919)`
  - `M19-2k recount ptnml vs fastchess           : PASS ([517, 1320, 2345, 1261, 557] == [517, 1320, 2345, 1261, 557])`
  - `M19-2k recount Elo vs fastchess             : PASS (+0.61 == +0.61)`
  - `M19-2k recount +/-95% vs fastchess          : PASS (4.71 == 4.71)`
  - `M19-2k fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)`

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; Stockfish's exact placement of its step in its own
search (only the three thresholds are tested); levels between ours and Stockfish's; 12,000 games carry about +/- 5
Elo and 3,000 about +/- 9; a lean here is a question for the PC, never an answer.

---

## Facts

1. **Step 0 pins, `K4`, `(a)`/`(b)`/`(c)` row-by-row checks on `O` (`200`) and `G` (`353`), and `(d)` planted `HdLowerLos=167` stop check all passed on `bundle12` (`/tmp/carbon2_job50/bld_bundle12/forge`, `sha256 = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e`):** No-option pins `312,866 / 862,329 / 4,865,609`; `PC20` `bench 11 / 13 = 278,024 / 587,276`; `K4` (`bench 13` with `HindsightDepth=true` and no other option) = `840,387` on both `bundle9` and `bundle12`; `(a)` `bundle12` all off equals Job 48 Step 0 position by position (`O = 8,315,168` on `200 == 200`; `G = 17,611,204` on `353 == 353`); `(b)` `K2` (`HindsightDepth=true` at defaults `1, 1, 100`) on `bundle12` equals `bundle9` position by position (`O = 8,732,910` on `200 == 200`; `G = 17,555,215` on `353 == 353`); `(c)` `K3` (`HindsightDepth=false` with `8, 16, 400`) equals `(a)` position by position (`200 == 200` and `353 == 353`); and `(d)` `HdLowerLos=167` stopped the runner immediately before any search on `info string unknown option HdLowerLos`.
2. **All three Stockfish lower-step thresholds are `LIVE` on `O` (`200` positions, depth `12`, `PC20 + HindsightDepth=true`), and `all_three` (`2, 2, 167`) has a LOWER depth-12 `O` node sum than defaults (`1, 1, 100`):** Relative to defaults (`8,732,910` nodes), `HdLowerWithheld=2` searches `8,772,845` (`+39,935`, `183/200` node diffs, `23/200` best-move diffs), `HdLowerDepth=2` searches `8,781,257` (`+48,347`, `100/200` node diffs, `5/200` best-move diffs), `HdLowerLoss=167` searches `8,526,306` (`-206,604` = `-2.37%`, `200/200` node diffs, `36/200` best-move diffs), and `all_three (2, 2, 167)` searches `8,519,678` (`-213,232` = `-2.44%`, `200/200` node diffs, `35/200` best-move diffs). This falsified our blind pre-L2 direction prediction (`ABOVE` in `1c9b351f1`).
3. **In `M18-2k` (`nodes=2,000`, `12,000` games, `COMPLETE`), Side A (`HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) loses to Side B (defaults `1, 1, 100`) with 95% confidence excluding zero:** `W-L-D = 4024-4234-3742`, pentanomial `[593, 1290, 2404, 1160, 553]`, **`-6.08 +/- 4.76` Elo (`[-10.84, -1.32]`)**.
4. **In `M18-20k` (`nodes=20,000`, `3,000` games, `COMPLETE`), Side A (`HdLowerWithheld=2, HdLowerDepth=2, HdLowerLoss=167`) loses to Side B (defaults `1, 1, 100`) with 95% confidence excluding zero:** `W-L-D = 779-861-1360`, pentanomial `[76, 392, 627, 348, 57]`, **`-9.50 +/- 8.09` Elo (`[-17.59, -1.41]`)**.
5. **In `M19-2k` (`nodes=2,000`, `12,000` games, `COMPLETE`), the 95% confidence interval crosses zero:** Side A (`HdLowerLoss=167`) vs Side B (defaults `1, 1, 100`) scored `4051-4030-3919`, pentanomial `[517, 1320, 2345, 1261, 557]`, **`+0.61 +/- 4.71` Elo (`[-4.10, +5.31]`)**.
6. **At `nodes=2,000` (quoted apart), `Elo(M18-2k) - Elo(M19-2k) = -6.69 +/- 6.70 [-13.39, +0.01]`, whose 95% interval crosses zero (upper bound `+0.01`).**

---

## Suspicions

1. **Near-zero result in `M19-2k` (`+0.61 +/- 4.71` Elo, `[-4.10, +5.31]`, `nodes=2,000`):** Raising `HdLowerLoss` alone from `100` to `167` shows no separated effect at `nodes=2,000` (its 95% interval crosses `0` almost symmetrically), indicating that changing the centipawn threshold `100 -> 167` by itself is not what caused `M18`'s loss.
2. **Attribution of `M18`'s loss to `HdLowerWithheld=2` and/or `HdLowerDepth=2` (`M18-2k - M19-2k = -6.69 +/- 6.70 [-13.39, +0.01]` at `nodes=2,000`, upper bound `+0.01`):** Because `[-13.39, +0.01]` touches `+0.01`, this comparison stays in Suspicions, but its lean points strongly at `HdLowerWithheld=2` and/or `HdLowerDepth=2` rather than `HdLowerLoss=167`. Mechanistically, in `src/search.cpp:2710–2713` (`if (depth <= 0) { --local_nodes_; return qsearch_child(board, ss, alpha, beta); }`), `HdLowerDepth = 2` makes `depth <= 0` **completely unreachable** (`depth >= 2 => proposed = depth - 1 >= 1`), preventing `reduced_depth == 1` blunders (`std::clamp(new_depth - r, 1, new_depth)` at `src/search.cpp:3214`) from dropping directly into `qsearch_child` (and refunding `--local_nodes_`) under a fixed node cap; meanwhile `HdLowerWithheld = 2` disables hindsight pruning on every `1`-ply LMR reduction (`withheld == 1`, `23/200` best-move diffs on `O`).
3. **Why fixed-depth-12 `O` node count (`-213,232`) moved opposite to fixed-node Elo (`M18-2k = -6.08`, `M18-20k = -9.50`):** On fixed-depth `O`, `HdLowerLoss=167` shrinks total nodes (`-206,604`) by letting the child refute `100..166` cp parent concessions at `reduced_depth` instead of `reduced_depth - 1` (avoiding parent fail-highs that trigger unreduced `new_depth` LMR re-searches, `src/search.cpp:3218–3228`), which turned out to be roughly Elo-neutral (`M19-2k = +0.61 +/- 4.71`). By contrast, `HdLowerWithheld=2` (`+39,935` nodes) and `HdLowerDepth=2` (`+48,347` nodes) **increase** nodes spent on `withheld == 1` and `depth == 1` moves that already lost `>= 167` cp, burning fixed-node budget (`2,000` and `20,000` nodes) on bad moves instead of reallocating those nodes to competitive siblings.

---

## Read and Not Tested

1. **Separating `HdLowerDepth = 2` from `HdLowerWithheld = 2` (`src/search.cpp:2704–2713` and `3214`):** `M19-2k` (`+0.61 +/- 4.71`) isolated `HdLowerLoss = 167`, leaving `HdLowerWithheld = 2` and `HdLowerDepth = 2` bundled together in `M18-2k` (`-6.08 +/- 4.76`) and `M18-20k` (`-9.50 +/- 8.09`). In Forge's `Worker::search`, `HdLowerDepth = 1` uniquely triggers `if (depth <= 0) { --local_nodes_; return qsearch_child(board, ss, alpha, beta); }` (`lines 2710–2713`), which both drops `reduced_depth == 1` blunders straight into quiescence and **refunds `--local_nodes_`** under fixed-node limits; testing `HdLowerDepth = 2` vs `HdLowerWithheld = 2` individually (or testing `HdLowerDepth = 1` without `--local_nodes_`) was read and not tested.
2. **TT-cutoff guard inversion on `HindsightDepth`'s lower step (`src/search.cpp:2707` vs `2718` in `/tmp/carbon2_job50/src_bundle12/src/search.cpp`, `lines 1986` vs `1997` in `r15d`):** Forge runs `HindsightDepth` **before** the non-PV TT cutoff (`line 2718: tt_depth >= depth`) and guards `depth = proposed` with `if (proposed != depth && !(tt_hit && tt_depth >= proposed))` (`line 2707`, commented `"A hash entry at least that deep already answers the node, so the depth stays put"`). For the **raise** step (`proposed = depth + 1`), `tt_depth >= depth + 1` implies `tt_depth >= depth`, so `line 2718` can answer from the hash. For the **lower** step (`proposed = depth - 1`), however, when `tt_hit` has `tt_depth == depth - 1` (even with `BoundLower` and `tt_score >= beta`), `tt_depth >= proposed` is `true`, so `depth` stays at `depth` instead of dropping to `depth - 1` — and then `line 2718` checks `tt_depth >= depth` (`depth - 1 >= depth`), which is **`false`**! Thus a `depth - 1` TT hit neither cuts off nor reduces `depth`, searching `1` ply **deeper** than having **no** TT hit at all. Stockfish places hindsight depth adjustment **after** the TT cutoff check, avoiding this inversion; restricting `!(tt_hit && tt_depth >= proposed)` to `proposed > depth` (or moving the step below the TT cutoff) was read and not tested.

---

## What I Did Not Do

- Did **not** pool `2,000`-node and `20,000`-node matches together.
- Did **not** test `HdLowerWithheld=2` or `HdLowerDepth=2` in standalone games (`M19` tested `HdLowerLoss=167` alone per File 50), nor `M19` at `20,000` nodes.
- Did **not** test intermediate thresholds (`HdLowerLoss` between `100` and `167`), nor alter `HindsightDepth`'s placement relative to the TT cutoff or `--local_nodes_`.
- Did **not** edit `prediction_job50.txt` after committing it alone in `85b035c8d`.
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **How much of `M18`'s loss (`-6.08 +/- 4.76` at `2k`, `-9.50 +/- 8.09` at `20k`) is real tree-quality loss vs `--local_nodes_` node-accounting on `depth == 1 -> qsearch_child`:** In `src/search.cpp:2710–2712`, when `depth == 1` is lowered to `proposed == 0`, Forge executes `--local_nodes_` before calling `qsearch_child` (so the aborted `depth == 1` `Worker::search` entry is not double-counted on top of `qsearch_child`'s own `++local_nodes_`). Under `HdLowerDepth = 2`, those positions run `Worker::search` at `depth = 1` instead of `qsearch_child`; both the extra `depth = 1` quiet/pruning work and any difference in node counting affect fixed-node play, whereas wall-clock play weights actual time per node.
2. **Why our `M18-2k` (`+2.0` predicted vs `-6.08` observed) and `M18-20k` (`+2.5` predicted vs `-9.50` observed) predictions missed while `M19-2k` (`+2.0` predicted vs `+0.61` observed) held:** We based all three match predictions on Part L2's net depth-12 `O` node reduction (`-213,232`), which came entirely from `HdLowerLoss = 167` (`-206,604`), and failed to anticipate that `HdLowerWithheld = 2` (`+39,935`) and `HdLowerDepth = 2` (`+48,347`) hurt fixed-node search substantially while `HdLowerLoss = 167` alone is neutral.
3. **Behavior at much higher node counts with the PC's NNUE net:** At `20,000` nodes (`M18-20k = -9.50 +/- 8.09`), `2, 2, 167` still lost with 95% CI excluding zero (`[-17.59, -1.41]`), showing that `20,000` nodes is not deep enough for Stockfish's `(2, 2, 167)` to overtake `(1, 1, 100)` on built-in evaluation; whether `HdLowerLoss = 167` alone (`M19`) behaves differently with the PC's v3 NNUE net remains a question for the PC.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job50/builds.txt`)

```text
=== JOB 50 BUILDS.TXT ===
1. r15d + v3 source tree: /tmp/carbon2_job36/tpl_r15d_v3
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77
   eval.hpp SeePieceValue[Pawn] = 100 (SeePieceValue{0, 100, 300, 300, 500, 900, 0})

2. Base bundle9 executable (same as Jobs 44, 46, 48, 49): /tmp/carbon2_job44/bld_bundle9/forge
   provenance = reused /tmp/carbon2_job44/bld_bundle9/forge with matching sha256
   exe sha256(/tmp/carbon2_job44/bld_bundle9/forge) = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef
   id_name = id name Chess Engine Forge 6.4.24 candidate
   patch 1 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/bundle_grok7.patch.txt) = b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146 (expected b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146)
   patch 2 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt) = 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326 (expected 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326)
   patch 3 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job43/P9_B8_fast.patch.txt) = bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395 (expected bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395)

3. Patched bundle12 executable (bundle12 = bundle9 + P12_hd_lower.patch.txt): /tmp/carbon2_job50/bld_bundle12/forge
   how_built = fresh copy of /tmp/carbon2_job36/tpl_r15d_v3 into /tmp/carbon2_job50/src_bundle12, git apply -p1 of bundle_grok7 + P8_S13_hoist + P9_B8_fast + /agent/repos/dwqww/forge-combo29/carbon2/job50/P12_hd_lower.patch.txt, compiled with Release SapphireRapids ThinLTO clang++-18/lld-18
   patch 4 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job50/P12_hd_lower.patch.txt) = 4b4000cce46dd057c4fabef1984480053164a9a4bac053314c6012d999c9d971
   exe sha256(/tmp/carbon2_job50/bld_bundle12/forge) = 9aa41d9055b487ef2fde2e867f78950c7e5609181d312f5501fe76c25a569a9e
   id_name = id name Chess Engine Forge 6.4.24 candidate
   compile_flags = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS="/tmp/carbon2_job50/src_bundle12/src/nnue_weights.inc" -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread -I/tmp/carbon2_job50/src_bundle12/include
   link_flags    = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -O3 -march=sapphirerapids -flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=4 -pthread /tmp/carbon2_job50/bld_bundle12/obj/bitboard.o /tmp/carbon2_job50/bld_bundle12/obj/board.o /tmp/carbon2_job50/bld_bundle12/obj/book.o /tmp/carbon2_job50/bld_bundle12/obj/eval.o /tmp/carbon2_job50/bld_bundle12/obj/eval_params.o /tmp/carbon2_job50/bld_bundle12/obj/nnue.o /tmp/carbon2_job50/bld_bundle12/obj/nnue_v3.o /tmp/carbon2_job50/bld_bundle12/obj/search.o /tmp/carbon2_job50/bld_bundle12/obj/uci.o -o /tmp/carbon2_job50/bld_bundle12/forge

4. Official fastchess executable: /tmp/carbon2_job40/fastchess
   git_commit(/tmp/carbon2_job40/fastchess_repo) = d6e3a7a71f8437a39836856ae78a3dcdc9bf934c
   exe sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007

5. Official opening book: /tmp/carbon2_job40/UHO_Lichess_4852_v1.epd
   lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 2632036
   book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a (expected 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a)
```

### Row File Hashes (`forge-combo29/carbon2/job50/*.rows.txt`)

- `partL2_HdLowerDepth2_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/partL2_HdLowerDepth2_O_d12.rows.txt`): `552d4986cbea856594b79a3b6661856d3018ff6e082a2518cd551f41e7fc05a5`
- `partL2_HdLowerLoss167_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/partL2_HdLowerLoss167_O_d12.rows.txt`): `3d0f032be8f1fae83484a82a44997b517a29e4a095d91306358e34f33131546a`
- `partL2_HdLowerWithheld2_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/partL2_HdLowerWithheld2_O_d12.rows.txt`): `f9763f6a76b988c86ec6d962ea556377513a9c0c2583cbd5306986edf3c4e842`
- `partL2_all_three_2_2_167_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/partL2_all_three_2_2_167_O_d12.rows.txt`): `1da203f7a460957e453336bd3550bdcf7bbde536a93aed6f9d6a5f50abb89b74`
- `step0_a_bundle12_all_off_G_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_a_bundle12_all_off_G_d12.rows.txt`): `911707ffe231d564533d1eb34550beb6b4ea9c6b9ddfd24a33f9dc3a16e7095e`
- `step0_a_bundle12_all_off_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_a_bundle12_all_off_O_d12.rows.txt`): `467d7a8cc6c2efa2e41f4d7fef047147abc12738755cacd5537021909a63d1e3`
- `step0_b_bundle12_HD_defaults_G_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_b_bundle12_HD_defaults_G_d12.rows.txt`): `216cc7cc02707aa398b8b062510130743a163565489dc1420597752a4bd3dcd7`
- `step0_b_bundle12_HD_defaults_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_b_bundle12_HD_defaults_O_d12.rows.txt`): `595de758c240a9aa445ad439816d7f8f73e5c457b7b3272ffa7f8eaac48e1bea`
- `step0_b_bundle12_HD_explicit_defaults_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_b_bundle12_HD_explicit_defaults_O_d12.rows.txt`): `595de758c240a9aa445ad439816d7f8f73e5c457b7b3272ffa7f8eaac48e1bea`
- `step0_b_bundle9_HD_defaults_G_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_b_bundle9_HD_defaults_G_d12.rows.txt`): `216cc7cc02707aa398b8b062510130743a163565489dc1420597752a4bd3dcd7`
- `step0_b_bundle9_HD_defaults_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_b_bundle9_HD_defaults_O_d12.rows.txt`): `595de758c240a9aa445ad439816d7f8f73e5c457b7b3272ffa7f8eaac48e1bea`
- `step0_c_bundle12_HD_false_max_G_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_c_bundle12_HD_false_max_G_d12.rows.txt`): `911707ffe231d564533d1eb34550beb6b4ea9c6b9ddfd24a33f9dc3a16e7095e`
- `step0_c_bundle12_HD_false_max_O_d12.rows.txt` (`/agent/repos/dwqww/forge-combo29/carbon2/job50/step0_c_bundle12_HD_false_max_O_d12.rows.txt`): `467d7a8cc6c2efa2e41f4d7fef047147abc12738755cacd5537021909a63d1e3`

### UTC Timestamps (`forge-combo29/carbon2/job50/stamps.txt`)

```text
job50_claimed: Sat Nov 21 01:11:10 AM UTC 2026
p12_done: Sat Nov 21 01:15:50 AM UTC 2026
step0_done: Sat Nov 21 01:18:07 AM UTC 2026
partL2_done: Sat Nov 21 01:19:07 AM UTC 2026
prediction_committed: Sat Nov 21 01:21:22 AM UTC 2026
M18-2k_done: Sat Nov 21 01:29:23 AM UTC 2026
M18-20k_done: Sat Nov 21 01:46:08 AM UTC 2026
M19-2k_done: Sat Nov 21 01:54:13 AM UTC 2026
report_done: Sat Nov 21 01:57:05 AM UTC 2026
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job50`)

```text
 M forge-combo29/carbon2/job50/stamps.txt
?? forge-combo29/carbon2/job50/REPORT_carbon2_job50.md
?? forge-combo29/carbon2/job50/build_report.py
forge-combo29/carbon2/job50:
build_report.py
builds.txt
j50_lib.py
M18-20k_fastchess.txt
M18-20k_fastchess.txt.meta
M18-20k_games.tsv
M18-20k_recount.txt
M18-2k_fastchess.txt
M18-2k_fastchess.txt.meta
M18-2k_games.tsv
M18-2k_recount.txt
M19-2k_fastchess.txt
M19-2k_fastchess.txt.meta
M19-2k_games.tsv
M19-2k_recount.txt
matches_results.json
matches_summary.txt
P12_hd_lower.patch.txt
p12_summary.txt
partL2_all_three_2_2_167_O_d12.rows.txt
partL2_all_three_2_2_167_O_d12.rows.txt.meta
partL2_HdLowerDepth2_O_d12.rows.txt
partL2_HdLowerDepth2_O_d12.rows.txt.meta
partL2_HdLowerLoss167_O_d12.rows.txt
partL2_HdLowerLoss167_O_d12.rows.txt.meta
partL2_HdLowerWithheld2_O_d12.rows.txt
partL2_HdLowerWithheld2_O_d12.rows.txt.meta
partL2_status.json
partL2_summary.txt
prediction_job50.txt
pre_L2_nodesum_note.txt
REPORT_carbon2_job50.md
run_matches.py
run_p12.py
run_partL2.py
run_step0.py
stamps.txt
step0_a_bundle12_all_off_G_d12.rows.txt
step0_a_bundle12_all_off_G_d12.rows.txt.meta
step0_a_bundle12_all_off_O_d12.rows.txt
step0_a_bundle12_all_off_O_d12.rows.txt.meta
step0_b_bundle12_HD_defaults_G_d12.rows.txt
step0_b_bundle12_HD_defaults_G_d12.rows.txt.meta
step0_b_bundle12_HD_defaults_O_d12.rows.txt
step0_b_bundle12_HD_defaults_O_d12.rows.txt.meta
step0_b_bundle12_HD_explicit_defaults_O_d12.rows.txt
step0_b_bundle12_HD_explicit_defaults_O_d12.rows.txt.meta
step0_b_bundle9_HD_defaults_G_d12.rows.txt
step0_b_bundle9_HD_defaults_G_d12.rows.txt.meta
step0_b_bundle9_HD_defaults_O_d12.rows.txt
step0_b_bundle9_HD_defaults_O_d12.rows.txt.meta
step0_c_bundle12_HD_false_max_G_d12.rows.txt
step0_c_bundle12_HD_false_max_G_d12.rows.txt.meta
step0_c_bundle12_HD_false_max_O_d12.rows.txt
step0_c_bundle12_HD_false_max_O_d12.rows.txt.meta
step0_raw.txt
```

---

## Model Name

`Gemini 4 Carbon`
