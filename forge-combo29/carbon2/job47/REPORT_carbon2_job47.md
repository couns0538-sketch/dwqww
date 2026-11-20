# Carbon2 Job 47 Report — K4b (Seat 043) Ported and Tested on Top of the Bundle, and Bundle Self-Play Cost With Fast IdeaB8b

## First Lines (Summary in Requested Order)

1. **(1) Step 0 (`PASS (1 == 1)`):** Rebased `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt` (built on `bundle8`, `git apply --check` `rc=1` on `bundle9` due to `P9_B8_fast.patch.txt`'s adjacent `IdeaB8_Fast` context lines) onto `bundle9` as `forge-combo29/carbon2/job47/P10_on_bundle9.patch.txt` (`CRLF count: PASS (0 == 0)`, `git apply --check -p1: PASS (0 == 0)` on `bundle9`, only 7 context hunks changed) and built `bundle10` (`/tmp/carbon2_job47/bld_bundle10/forge`). Enforced the strict Job 47 harness rule across all runners (every option sent is verified in the executable's own `uci` list; every line before `readyok` is kept in `.meta` and checked to stop immediately on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, or `ERROR`). Every no-option pin (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`), `HindsightDepth` pin (`840387 == 840387` / `862329 == 862329`), `PC20` OFF sweep (`O: 8315168 == 8315168` on `200 == 200`; `G: 17611204 == 17611204` on `353 == 353`), `IdeaB8b` alone (`8483711 == 8483711`, `200 == 200`), `IdeaB8b + IdeaB8b_Fast` (`8483711 == 8483711`, `200 == 200` vs `IdeaB8b` alone and Job 45 `P10c`), and `IdeaB8 + IdeaB8_Fast` (`8262696 == 8262696`, `200 == 200` vs `IdeaB8` alone and Job 43 `P9c`) passed on `bundle9` and `bundle10`.
2. **(2) Prediction Graded (`3 / 3` `TRUE`, committed alone at `Fri Nov 20 10:00:14 PM UTC 2026` in commit `03f43f6b6` before Part P11's first search):**
   - **Prediction (1) — P11(d) `O` node-count diffs with `IdeaK4b` alone (`PC20`, depth 12):** Predicted `199 / 200`, falsification range outside `[180, 200]`. Measured **`200 / 200`** (`inside [180, 200]`) -> **`TRUE` (`HELD`)**.
   - **Prediction (2) — M14 `IdeaK4b` Elo on top of the bundle (`PC20`, `nodes=20000`, `3,000` games):** Predicted `-5.0` Elo, falsification range outside `[-14.0, +4.0]`. Measured **`-9.50` Elo** (`-9.50 +/- 8.30 (95% CI [-17.80, -1.20]; exact [-17.81, -1.20])`, `inside [-14.0, +4.0]`) -> **`TRUE` (`HELD`)**.
   - **Prediction (3) — T3 `B / A` wall-time ratio on `Set A line L` with `IdeaB8b_Fast` (`bundle10`, 12 runs):** Predicted `1.090`, falsification range outside `[1.068, 1.115]`. Measured **`1.103246`** (`inside [1.068, 1.115]`) -> **`TRUE` (`HELD`)**.
3. **(3) Part P11 (`PASS (1 == 1)`):**
   - **Known answer on `6b98f217` (`S14`, built-in eval, `O` depth 12):** Seat `043` patch applied AS IT IS (`git apply --check: PASS (0 == 0)`); `IdeaK4=false` sum `PASS (9500069 == 9500069)` (`200 == 200` vs `job38/043_off_O_d12.nodes.txt` and `job38/B_O_d12.nodes.txt`); `IdeaK4=true` sum **`PASS (8983632 == 8983632)`** (`200 == 200` vs `job38/043_on_O_d12.nodes.txt`).
   - **Search stack line & entries below root (verified before build):** `include/forge/search.hpp` line `585` (`585 == 585`) declares `std::array<SearchStack, MaxPly + 8> stack_{};`; `src/search.cpp` lines `3930-3953` initialize `stack_[0..init_limit]` with `entry.static_eval = ValueNone` (`line 3937 == 3937`) and set root `SearchStack* ss = &stack_[4];` (`line 3953 == 3953`). **`4` entries (`stack_[0..3]`, `4 == 4`) lie below the root's entry (`stack_[4]`)**, so `(ss - 3)` is `stack_[1]` at root (`ply 0`), `stack_[2]` at `ply 1`, and `stack_[3]` at `ply 2` (all in-bounds with `static_eval == ValueNone`).
   - **Port & OFF identity (`forge-combo29/carbon2/job47/P11_K4b.patch.txt` -> `bundle11`):** Added `IdeaK4b` (`check`, default `false`) and `IdeaK4b_Shrink` (`spin`, default `32`, `0` to `200`). With `IdeaK4b=false` under `PC20`, `bundle11` OFF rows equal `O` `PASS (8315168 == 8315168)` (`200 == 200`) and `G` `PASS (17611204 == 17611204)` (`353 == 353`).
   - **Liveness (`IdeaK4b` alone, `PC20`, `O` depth 12):** Sum = **`7491020`** (`-824148` nodes vs OFF `8315168`); **`200 / 200`** node counts, **`56 / 200`** best moves, and **`193 / 200`** scores differ from OFF.
4. **(4) Part M14 (`IdeaK4b` on top of `IdeaB8b + IdeaB8b_Fast + HindsightDepth`, `PC20`, `nodes=20000`, UHO lines `2,022,501..2,024,000`, `3,000` games / `1,500` pairs):**
   - **Recounted W-L-D (`bundle_plus_IdeaK4b` vs `bundle_only`):** `781 - 863 - 1356 (score=0.486333)`; **Pentanomial:** `[96, 364, 625, 356, 59] (pairs=1500)`.
   - **Recounted Elo:** **`-9.50 +/- 8.30 (95% CI [-17.80, -1.20]; exact [-17.81, -1.20])`** (`-14.23 +/- 12.43 | LOS: 1.24%`).
   - **fastchess's own line:** `Games: 3000, Wins: 781, Losses: 863, Draws: 1356, Points: 1459.0 (48.63 %) | Elo: -9.50 +/- 8.30, nElo: -14.23 +/- 12.43 | Ptnml(0-2): [96, 364, 625, 356, 59], WL/DD Ratio: 0.97`.
5. **(5) Part T3 (Self-Play Cost With Fast `IdeaB8b` on `Set A line L`, `bundle10`, 12 runs `fwd` + `rev` pinned Core 1):**
   - **Known answers met on all 12 runs before time counts:** Every `A` (`all_off`) run equaled `T2`'s `A` (`26741 == 26741` records, `26867 == 26867` searches, `107124743 == 107124743` nodes, `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`), and every `B` (`IdeaB8b + IdeaB8b_Fast + HindsightDepth`) run equaled `T2`'s `B` (`27817 == 27817` records, `27939 == 27939` searches, `112503041 == 112503041` nodes, `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d`, `204 == 204` attempt lines).
   - **Wall time & records/sec in words beside `T2`'s `1.137204`:**
     * B takes 1.103246 times A's wall time (beside T2's 1.137204 without IdeaB8b_Fast).
     * B produces 0.942903 times A's records per second (beside T2's 0.914732 without IdeaB8b_Fast).
     * Split into nodes times time per node: `B / A wall time = 1.050206 (nodes_B / nodes_A) * 1.050505 (time_per_node_B / time_per_node_A) = 1.103246 (beside T2's 1.050206 * 1.082839 = 1.137204).`

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 9 Elo, so M14 can say whether K4b clearly hurts on top of the bundle, not how large a small gain is; with the built-in evaluation a node is cheap, so a per-node cost is larger on your tree than with the PC's net.

---

## Detailed Verbatim Artifacts

### 1. Step 0 (`forge-combo29/carbon2/job47/step0_raw.txt`)

```text
=== JOB 47 STEP 0: r15d + v3, Bundle9, and Bundle10 (bundle9 + P10_on_bundle9.patch.txt) ===
start_utc: Fri Nov 20 09:56:06 PM UTC 2026
harness_policy: Every runner checks that every sent option is in the exe's uci list, keeps every line before readyok, and STOPS on unknown option, invalid value, illegal, invalid FEN, and ERROR.

--- 1. r15d + v3 Source Tree & Plain Release Executable ---
  src/search.cpp CRLF count                   : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp): PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)
  src/uci.cpp CRLF count                      : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp): PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)
  src/board.cpp CRLF count                    : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp): PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)
  include/forge/board.hpp CRLF count          : PASS (0 == 0)
  tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp): PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)
  plain r15d+v3 sha256(/tmp/carbon2_job44/bld_base_v3/forge): PASS (09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c == 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c)
  bld_base_v3 uci declares HindsightDepth (check=false): PASS (True == True)
  bld_base_v3 HindsightDepth pre-readyok lines: PASS (0 == 0)
[plain_r15d_v3] exe=/tmp/carbon2_job44/bld_base_v3/forge | sha256=09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c | id name Chess Engine Forge 6.4.24 candidate
  plain_r15d_v3 no-option bench 11            : PASS (312866 == 312866)
  plain_r15d_v3 no-option bench 13            : PASS (862329 == 862329)
  plain_r15d_v3 no-option perft 5             : PASS (4865609 == 4865609)
  plain_r15d_v3 PC20 bench 11                 : PASS (278024 == 278024)
  plain_r15d_v3 PC20 bench 13                 : PASS (587276 == 587276)
  plain_r15d_v3 Set A line L records          : PASS (26741 == 26741)
  plain_r15d_v3 Set A line L searches         : PASS (26867 == 26867)
  plain_r15d_v3 Set A line L nodes            : PASS (107124743 == 107124743)
  plain_r15d_v3 Set A line L sha256           : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  plain_r15d_v3 Set A pre-readyok lines       : PASS (0 == 0)
  plain_r15d_v3 n[1..60] line L records       : PASS (8449 == 8449)
  plain_r15d_v3 n[1..60] line L searches      : PASS (8482 == 8482)
  plain_r15d_v3 n[1..60] line L nodes         : PASS (36688357 == 36688357)
  plain_r15d_v3 n[1..60] line L sha256        : PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  plain_r15d_v3 n[1..60] bad pre-readyok lines (kept=2): PASS (0 == 0)
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 loaded: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 active: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
  plain_r15d_v3 no-PC20 HindsightDepth=false bench 13: PASS (862329 == 862329)
  plain_r15d_v3 no-PC20 HindsightDepth=true bench 13: PASS (840387 == 840387)

--- 2. Bundle9 Verification & git apply --check of job45/P10_B8b_fast.patch.txt ---
  bundle9 exe sha256(/tmp/carbon2_job44/bld_bundle9/forge): PASS (9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef == 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef)
  fresh_bundle9_source_apply                  : bundle_grok7 + P8_S13_hoist + P9_B8_fast git apply --check -p1 PASS (0 == 0)
  git apply --check job45/P10_B8b_fast.patch.txt on bundle9: rc=1 (expected non-zero due to P9_B8_fast context; rebasing onto bundle9 as job47/P10_on_bundle9.patch.txt)
  P10_on_bundle9.patch.txt CRLF count         : PASS (0 == 0)
  git apply --check P10_on_bundle9 on bundle9 : PASS (0 == 0)
  patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/P10_on_bundle9.patch.txt): b72e4c953571f708c016beba9e7dc164a63b5f1b849e5a4e2197a6c4e95b88fe
# Context lines changed relative to job45/P10_B8b_fast.patch.txt (all due to job43/P9_B8_fast.patch.txt in bundle9):
#   1. include/forge/search.hpp hunk 1: context above `extern bool IdeaB8b;` has `extern bool IdeaB8_Fast;` (line 316).
#   2. include/forge/search.hpp hunk 2: line offset +15 (`@@ -704,6 +705,26 @@`) below `B8FastEntry`.
#   3. src/search.cpp hunk 1: context above `bool IdeaB8b = false;` has `bool IdeaB8_Fast = false;` (line 176).
#   4. src/search.cpp hunk 2-3 (`QuietScorer`): context around fields and constructor body includes `b8_fast_entry` / `b8_fast_scaled` / `prepare_b8_fast_scorer` (constructor `{ ... }` already opened by P9_B8_fast).
#   5. src/search.cpp hunk 4 (`QuietScorer::score`): context above `if (tune::IdeaB8b)` is the multi-line `if (tune::IdeaB8)` fast block.
#   6. src/search.cpp hunk 5 (`Worker::clear`): context above `*role_b8b_history_` has `for (auto& e : b8_fast_cache_) e.occ_w = ~0ULL;`.
#   7. src/uci.cpp hunks 1-2: context above `IdeaB8b` option listing (line 762) and handler (lines 983-985) includes `IdeaB8_Fast`.

--- 3. Build Bundle10 (/tmp/carbon2_job47/bld_bundle10/forge) & Verify Pins + Fast Paths ---
  bundle10 exe path                           : /tmp/carbon2_job47/bld_bundle10/forge
  bundle10 exe sha256(/tmp/carbon2_job47/bld_bundle10/forge): cb49d8824518cf392cf0763ac79e389febd3f6156f063145ef5cbe5cee6daee5
  bundle10 id name                            : id name Chess Engine Forge 6.4.24 candidate
  bld_bundle10 uci declares HindsightDepth (check=false): PASS (True == True)
  bld_bundle10 HindsightDepth pre-readyok lines: PASS (0 == 0)
  bld_bundle10 uci declares IdeaB8b (check=false): PASS (True == True)
  bld_bundle10 IdeaB8b pre-readyok lines      : PASS (0 == 0)
  bld_bundle10 uci declares IdeaB8b_Fast (check=false): PASS (True == True)
  bld_bundle10 IdeaB8b_Fast pre-readyok lines : PASS (0 == 0)
  bld_bundle10 uci declares IdeaB8 (check=false): PASS (True == True)
  bld_bundle10 IdeaB8 pre-readyok lines       : PASS (0 == 0)
  bld_bundle10 uci declares IdeaB8_Fast (check=false): PASS (True == True)
  bld_bundle10 IdeaB8_Fast pre-readyok lines  : PASS (0 == 0)
  bld_bundle10 uci declares IdeaS13 (check=false): PASS (True == True)
  bld_bundle10 IdeaS13 pre-readyok lines      : PASS (0 == 0)
  bld_bundle10 uci declares IdeaS13_Hoist (check=false): PASS (True == True)
  bld_bundle10 IdeaS13_Hoist pre-readyok lines: PASS (0 == 0)
  bld_bundle10 uci declares IdeaS10 (check=false): PASS (True == True)
  bld_bundle10 IdeaS10 pre-readyok lines      : PASS (0 == 0)
  bld_bundle10 uci declares IdeaK4 (check=false): PASS (True == True)
  bld_bundle10 IdeaK4 pre-readyok lines       : PASS (0 == 0)
[bundle10_default_off] exe=/tmp/carbon2_job47/bld_bundle10/forge | sha256=cb49d8824518cf392cf0763ac79e389febd3f6156f063145ef5cbe5cee6daee5 | id name Chess Engine Forge 6.4.24 candidate
  bundle10_default_off no-option bench 11     : PASS (312866 == 312866)
  bundle10_default_off no-option bench 13     : PASS (862329 == 862329)
  bundle10_default_off no-option perft 5      : PASS (4865609 == 4865609)
  bundle10_default_off PC20 bench 11          : PASS (278024 == 278024)
  bundle10_default_off PC20 bench 13          : PASS (587276 == 587276)
  bundle10_default_off Set A line L records   : PASS (26741 == 26741)
  bundle10_default_off Set A line L searches  : PASS (26867 == 26867)
  bundle10_default_off Set A line L nodes     : PASS (107124743 == 107124743)
  bundle10_default_off Set A line L sha256    : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  bundle10_default_off Set A pre-readyok lines: PASS (0 == 0)
  bundle10_default_off n[1..60] line L records: PASS (8449 == 8449)
  bundle10_default_off n[1..60] line L searches: PASS (8482 == 8482)
  bundle10_default_off n[1..60] line L nodes  : PASS (36688357 == 36688357)
  bundle10_default_off n[1..60] line L sha256 : PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  bundle10_default_off n[1..60] bad pre-readyok lines (kept=2): PASS (0 == 0)
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 loaded: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 active: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
[bundle10_explicit_11_false] exe=/tmp/carbon2_job47/bld_bundle10/forge | sha256=cb49d8824518cf392cf0763ac79e389febd3f6156f063145ef5cbe5cee6daee5 | id name Chess Engine Forge 6.4.24 candidate
  bundle10_explicit_11_false no-option bench 11: PASS (312866 == 312866)
  bundle10_explicit_11_false no-option bench 13: PASS (862329 == 862329)
  bundle10_explicit_11_false no-option perft 5: PASS (4865609 == 4865609)
  bundle10_explicit_11_false PC20 bench 11    : PASS (278024 == 278024)
  bundle10_explicit_11_false PC20 bench 13    : PASS (587276 == 587276)
  bundle10_explicit_11_false Set A line L records: PASS (26741 == 26741)
  bundle10_explicit_11_false Set A line L searches: PASS (26867 == 26867)
  bundle10_explicit_11_false Set A line L nodes: PASS (107124743 == 107124743)
  bundle10_explicit_11_false Set A line L sha256: PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  bundle10_explicit_11_false Set A pre-readyok lines: PASS (0 == 0)
  bundle10_explicit_11_false n[1..60] line L records: PASS (8449 == 8449)
  bundle10_explicit_11_false n[1..60] line L searches: PASS (8482 == 8482)
  bundle10_explicit_11_false n[1..60] line L nodes: PASS (36688357 == 36688357)
  bundle10_explicit_11_false n[1..60] line L sha256: PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  bundle10_explicit_11_false n[1..60] bad pre-readyok lines (kept=2): PASS (0 == 0)
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 loaded: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
    kept_n60_pre_readyok: [selfgame_options] info string NNUE v3 active: v3 /tmp/carbon2_work/net768.fnn3 hidden 768 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum 30ab43b4ba5db5f3 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512
  bundle9 no-PC20 HindsightDepth=false bench 13: PASS (862329 == 862329)
  bundle9 no-PC20 HindsightDepth=true bench 13: PASS (840387 == 840387)
  bundle10 no-PC20 HindsightDepth=false bench 13: PASS (862329 == 862329)
  bundle10 no-PC20 HindsightDepth=true bench 13: PASS (840387 == 840387)

--- 4. O and G Depth-12 Known-Answer Sweeps on Bundle9 and Bundle10 (PC20) ---
  bundle9 OFF O d12 sum                       : PASS (8315168 == 8315168)
  bundle9 OFF O d12 equal vs J39 OFF_O        : PASS (200 == 200)
  bundle9 OFF G d12 sum                       : PASS (17611204 == 17611204)
  bundle9 OFF G d12 equal vs J39 OFF_G        : PASS (353 == 353)
  bundle9 IdeaB8b O d12 sum                   : PASS (8483711 == 8483711)
  bundle9 IdeaB8b O d12 equal vs J41 P7_B8b   : PASS (200 == 200)
  bundle9 IdeaS10 O d12 sum                   : PASS (8314153 == 8314153)
  bundle9 IdeaS10 O d12 equal vs J41 P7_S10   : PASS (200 == 200)
  bundle9 IdeaS10 vs OFF node diffs           : PASS (17 == 17)
  bundle9 IdeaS10 vs OFF bestmove diffs       : PASS (2 == 2)
  bundle9 IdeaS13 (no hoist) O d12 sum        : PASS (8077984 == 8077984)
  bundle9 IdeaS13 O d12 equal vs J41 P7_S13   : PASS (200 == 200)
  bundle9 IdeaS13 vs OFF node diffs           : PASS (200 == 200)
  bundle10 OFF O d12 sum                      : PASS (8315168 == 8315168)
  bundle10 OFF O d12 equal vs J39 OFF_O       : PASS (200 == 200)
  bundle10 OFF G d12 sum                      : PASS (17611204 == 17611204)
  bundle10 OFF G d12 equal vs J39 OFF_G       : PASS (353 == 353)
  bundle10 B8b+B8b_Fast O sum                 : PASS (8483711 == 8483711)
  bundle10 B8b+B8b_Fast equal to B8b alone    : PASS (200 == 200)
  bundle10 B8b+B8b_Fast equal to J45 P10c     : PASS (200 == 200)
  bundle10 B8+B8_Fast O sum                   : PASS (8262696 == 8262696)
  bundle10 B8+B8_Fast equal to B8 alone       : PASS (200 == 200)
  bundle10 B8+B8_Fast equal to J43 P9c        : PASS (200 == 200)

--- 5. fastchess & UHO Book Prerequisites ---
  book lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (2632036 == 2632036)
  book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd): PASS (7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a == 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a)

  STEP 0 OVERALL                              : PASS (1 == 1)
done_utc: Fri Nov 20 09:58:54 PM UTC 2026
```

### 2. Prediction (`forge-combo29/carbon2/job47/prediction_job47.txt`)

```text
=== CARBON2 JOB 47 PREDICTION (COMMITTED ALONE BEFORE FIRST SEARCH OF PART P11) ===
prediction_utc: Fri Nov 20 10:00:14 PM UTC 2026

1. Part P11 (d) — Number of O positions (out of 200) changing node count with IdeaK4b alone under PC20 at depth 12:
   - Point prediction: 199 of 200 positions change node count.
   - Range that would prove me wrong: outside [180, 200] (i.e., < 180 of 200 positions changing node count).
   - Basis: IdeaK4b subtracts IdeaK4b_Shrink = 32 cp from rfp_margin at non-PV, non-check nodes with depth <= RfpDepth (8) whenever (ss - 1)->static_eval < (ss - 3)->static_eval (both != ValueNone, which holds from ply >= 3 onward whenever the opponent had static evals two plies apart). Every depth-12 root search on the 200 balanced/UHO-like O openings traverses thousands of ply >= 3, depth <= 8 non-PV nodes, so shifting the RFP threshold by 32 cp alters pruning decisions in virtually every tree.

2. Part M14 — IdeaK4b Elo on top of the bundle (IdeaB8b + IdeaB8b_Fast + HindsightDepth + IdeaK4b vs IdeaB8b + IdeaB8b_Fast + HindsightDepth, PC20, built-in evaluation, nodes=20000, 3,000 games on UHO lines 2,022,501..2,024,000):
   - Point prediction: -5.0 Elo (for the +IdeaK4b side).
   - Range that would prove me wrong: outside [-14.0, +4.0] Elo (i.e., measured Elo < -14.0 or > +4.0).
   - Basis: Alone on 6b98f217 under S14 (TtPruneV2=false), K4b (Shrink=32) lost -4.53 +/- 1.58 Elo [-6.11, -2.95] over 82,000 games from over-aggressive reverse futility pruning. Under PC20, TtPruneV2=true already subtracts RfpMargin/3 (24 cp) on opponent-worsening nodes, and neither IdeaB8b (quiet move history ordering after RFP) nor HindsightDepth (ply-boundary depth adjustment) rescues refutations pruned before move generation by an additional 32-cp RFP margin cut. Stacking -32 cp onto TtPruneV2's -24 cp compounds RFP over-pruning.

3. Part T3 — B / A wall-time ratio on Set A line L with the fast path (B = IdeaB8b + IdeaB8b_Fast + HindsightDepth, A = all off, on bundle10, 12 runs fwd + rev):
   - Point prediction: 1.090 (B takes 1.090 times A's wall time).
   - Range that would prove me wrong: outside [1.068, 1.115] (i.e., B / A wall-time ratio < 1.068 or > 1.115).
   - Basis: Because IdeaB8b_Fast changes zero nodes, T3 has the exact deterministic node ratio measured in Job 44 Part T2: nodes_B / nodes_A = 112,503,041 / 107,124,743 = 1.050206. In T2 (without IdeaB8b_Fast), B / A wall time was 1.137204, implying a per-node time ratio of 1.137204 / 1.050206 = 1.082839 (+8.284%). In Job 45 Part P10(d), IdeaB8b_Fast removed 56.34% of IdeaB8b's extra per-node time (1.088499 -> 1.038636). Retaining ~44% of T2's +8.284% per-node overhead yields an expected per-node time ratio of ~1.0375, and 1.050206 * 1.0375 = 1.0896 (~1.090).
```

### 3. Part P11 (`forge-combo29/carbon2/job47/partP11_summary.txt`)

```text
=== JOB 47 PART P11: K4b (SEAT 043) PORTED, KNOWN ANSWER, STACK PROOF, OFF IDENTITY, LIVENESS ===
start_utc: Fri Nov 20 10:07:11 PM UTC 2026

--- (a) Seat 043 Patch Read-Only Inspection ---
  grok-043 idea.patch.txt line count          : PASS (90 == 90)
  grok-043 idea.patch.txt CRLF count          : PASS (0 == 0)
  read_only_copy_sha256(/tmp/carbon2_job47/grok_043_idea.patch.txt): b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81 (from for-fable-and-opus/grok-043:forge-combo29/grok/043/idea.patch.txt)
  mechanism: adds IdeaK4 (check, default false) and IdeaK4_Shrink (spin, default 32, 0..200); in Worker::search reverse futility pruning, when (ss - 1)->static_eval != ValueNone && (ss - 3)->static_eval != ValueNone && (ss - 1)->static_eval < (ss - 3)->static_eval, subtracts IdeaK4_Shrink (32) from rfp_margin (whereas seat 093 K4a in bundle uses Shrink = 24).

--- (b) Known Answer on Helpers' Tree 6b98f217 (S14, Built-In Eval, O Depth 12) ---
  git apply --check grok-043 on 6b98f217      : PASS (0 == 0)
  exe_path: /tmp/carbon2_job47/bld_043_base/forge
  exe_sha256(/tmp/carbon2_job47/bld_043_base/forge): 56a73dc402d07e94344aa1953b5a50e303be29b0bf6dfec1effca93ec1a3b655
  bld_043_base uci declares IdeaK4 (check=false): PASS (True == True)
  bld_043_base IdeaK4 pre-readyok lines       : PASS (0 == 0)
  bld_043_base uci declares IdeaK4_Shrink (spin=32): PASS (True == True)
  bld_043_base IdeaK4_Shrink pre-readyok lines: PASS (0 == 0)
  6b98+043 no-option bench 11                 : PASS (312866 == 312866)
  6b98+043 no-option bench 13                 : PASS (862329 == 862329)
  6b98+043 no-option perft 5                  : PASS (4865609 == 4865609)
  6b98+043 IdeaK4=false O d12 sum             : PASS (9500069 == 9500069)
  6b98+043 IdeaK4=false nodes equal vs job38/043_off_O_d12: PASS (200 == 200)
  6b98+043 IdeaK4=false nodes equal vs job38/B_O_d12: PASS (200 == 200)
  6b98+043 IdeaK4=true O d12 sum              : PASS (8983632 == 8983632)
  6b98+043 IdeaK4=true nodes equal vs job38/043_on_O_d12: PASS (200 == 200)

--- (c) Search Stack Safety Check (Before Build), Port P11_K4b.patch.txt, and OFF Identity ---
  include/forge/search.hpp stack_ declaration line: PASS (585 == 585)
  src/search.cpp entry.static_eval = ValueNone line: PASS (3937 == 3937)
  src/search.cpp root ss = &stack_[4] line    : PASS (3953 == 3953)
  entries below root entry (&stack_[4])       : PASS (4 == 4)
  stack_proof: stack_ has MaxPly + 8 entries (include/forge/search.hpp:585); Worker::search_root initializes stack_[0..init_limit] with static_eval = ValueNone (src/search.cpp:3930-3952) and sets root SearchStack* ss = &stack_[4] (src/search.cpp:3953, ply=0). 4 entries (stack_[0..3]) lie below root: (ss - 3) is stack_[1] at root (ply 0), stack_[2] at ply 1, and stack_[3] at ply 2 (all in-bounds with static_eval == ValueNone), and stack_[4 + ply - 3] for ply >= 3.
  P11_K4b.patch.txt CRLF count                : PASS (0 == 0)
  git apply --check -p1 P11_K4b.patch.txt on bundle10: PASS (0 == 0)
  patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/P11_K4b.patch.txt): 60209ff7852b5b2d8bd217579744242d3350f4e6e155a1fc0d4e388b165d3548
  bundle11 exe path: /tmp/carbon2_job47/bld_bundle11_k4b/forge
  bundle11 exe sha256(/tmp/carbon2_job47/bld_bundle11_k4b/forge): 7499b3e1b8b589606e46d227e48f06b7cc481a75cac1dfa67ddc19197ab47c2e
  bundle11 id name: id name Chess Engine Forge 6.4.24 candidate
  bld_bundle11_k4b uci declares IdeaK4b (check=false): PASS (True == True)
  bld_bundle11_k4b IdeaK4b pre-readyok lines  : PASS (0 == 0)
  bld_bundle11_k4b uci declares IdeaK4b_Shrink (spin=32): PASS (True == True)
  bld_bundle11_k4b IdeaK4b_Shrink pre-readyok lines: PASS (0 == 0)
  bld_bundle11_k4b uci declares IdeaK4 (check=false): PASS (True == True)
  bld_bundle11_k4b IdeaK4 pre-readyok lines   : PASS (0 == 0)
  bld_bundle11_k4b uci declares IdeaK4_Shrink (spin=24): PASS (True == True)
  bld_bundle11_k4b IdeaK4_Shrink pre-readyok lines: PASS (0 == 0)
  bundle11 no-option bench 11                 : PASS (312866 == 312866)
  bundle11 no-option bench 13                 : PASS (862329 == 862329)
  bundle11 no-option perft 5                  : PASS (4865609 == 4865609)
  bundle11 OFF O d12 sum                      : PASS (8315168 == 8315168)
  bundle11 OFF O d12 equal vs bundle10 OFF O  : PASS (200 == 200)
  bundle11 OFF O d12 equal vs job39 OFF_O     : PASS (200 == 200)
  bundle11 OFF G d12 sum                      : PASS (17611204 == 17611204)
  bundle11 OFF G d12 equal vs bundle10 OFF G  : PASS (353 == 353)
  bundle11 OFF G d12 equal vs job39 OFF_G     : PASS (353 == 353)

--- (d) Liveness: IdeaK4b Alone (IdeaK4b_Shrink=32) Under PC20 on O at Depth 12 ---
  IdeaK4b alone PC20 O d12 sum                : 7491020 (OFF = 8315168, delta = -824148 nodes)
  IdeaK4b vs OFF node-count diffs (of 200)    : 200 / 200
  IdeaK4b vs OFF best-move diffs  (of 200)    : 56 / 200
  IdeaK4b vs OFF score diffs      (of 200)    : 193 / 200
  IdeaK4b liveness (at least 1 node diff > 0) : PASS (True == True)
  PREDICTION (1) CHECK: node_diffs = 200 / 200 (predicted 199, falsification range outside [180, 200] -> TRUE)

  PART P11 OVERALL                            : PASS (1 == 1)
done_utc: Fri Nov 20 10:08:01 PM UTC 2026
```

### 4. Part M14 (`forge-combo29/carbon2/job47/M14_liveness.txt`, `M14_recount.txt`, `M14_fastchess.txt.meta`)

```text
=== JOB 47 PART M14 LIVENESS (PC20, O depth 12: bundle+IdeaK4b vs bundle, IdeaB8b_Fast=true on both) ===
exe_path: /tmp/carbon2_job47/bld_bundle11_k4b/forge
  M14 SideB (bundle+IdeaB8b_Fast) O d12 sum vs J46 bundle_only: PASS (8481645 == 8481645)
  M14 SideB equal positions vs J46 M11_liveness_bundle_only: PASS (200 == 200)
  sideA_rows_file                             : /agent/repos/dwqww/forge-combo29/carbon2/job47/M14_liveness_bundle_plus_IdeaK4b_O_d12.rows.txt
  sideB_rows_file                             : /agent/repos/dwqww/forge-combo29/carbon2/job47/M14_liveness_bundle_only_O_d12.rows.txt
  bundle_plus_IdeaK4b_O_d12_sum_nodes         : 8044931
  bundle_only_O_d12_sum_nodes                 : 8481645
  node_sum_delta ((bundle+IdeaK4b) - bundle)  : -436714
  equal_positions_of_200                      : 0
  nodes_diff_positions_of_200                 : 200
  bestmove_diff_positions_of_200              : 56
  score_diff_positions_of_200                 : 192
  M14 liveness (bundle+K4b vs bundle nodes_diff >= 1): PASS (True == True)
liveness_done_utc: Fri Nov 20 10:12:11 PM UTC 2026

=== M14 RECOUNT FROM PER-GAME LIST (COMPLETE) ===
games_tsv_path: /agent/repos/dwqww/forge-combo29/carbon2/job47/M14_games.tsv
games_tsv_sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/M14_games.tsv): faa30150d720b6bac51eabaa6a35c0de7d44eeff72de6c3a37d6c18da0e4f76b
fastchess_stdout_path: /agent/repos/dwqww/forge-combo29/carbon2/job47/M14_fastchess.txt
fastchess_stdout_sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/M14_fastchess.txt): 60e8f0b1a3eb0e079748ecfdd88afe796558db4db6e2d1b8c61cdcd18e84a543
book_slice: /tmp/carbon2_job40/UHO_Lichess_4852_v1.epd lines 2022501..2024000 (1500 openings)
status: COMPLETE
engines: bundle_plus_IdeaK4b vs bundle_only
games_finished: 3000 (unpaired=0, mean_plies=142.26)
recounted_WLD (bundle_plus_IdeaK4b vs bundle_only): 781 - 863 - 1356 (score=0.486333)
recounted_pentanomial [LL, LD, WL+DD, WD, WW]: [96, 364, 625, 356, 59] (pairs=1500)
recounted_Elo: -9.50 +/- 8.30 (95% CI [-17.80, -1.20]; exact [-17.81, -1.20])
recounted_nElo: -14.23 +/- 12.43 | LOS: 1.24%
fastchess_own_line: Games: 3000, Wins: 781, Losses: 863, Draws: 1356, Points: 1459.0 (48.63 %) | Elo: -9.50 +/- 8.30, nElo: -14.23 +/- 12.43 | Ptnml(0-2): [96, 364, 625, 356, 59], WL/DD Ratio: 0.97
fastchess_own_elo_ptnml: Elo=-9.50 +/- 8.30, Ptnml=[96, 364, 625, 356, 59]
checks:
  M14 non-normal terminations                 : PASS (0 == 0)
  M14 opening FEN pairs matching book slice   : PASS (1500 == 1500)
  M14 finished games vs target                : PASS (3000 == 3000)
  M14 finished pairs vs target                : PASS (1500 == 1500)
  M14 recount W vs fastchess                  : PASS (781 == 781)
  M14 recount L vs fastchess                  : PASS (863 == 863)
  M14 recount D vs fastchess                  : PASS (1356 == 1356)
  M14 recount ptnml vs fastchess              : PASS ([96, 364, 625, 356, 59] == [96, 364, 625, 356, 59])
  M14 recount Elo vs fastchess                : PASS (-9.50 == -9.50)
  M14 recount +/-95% vs fastchess             : PASS (8.30 == 8.30)
utc_recounted: Fri Nov 20 10:28:54 PM UTC 2026
  M14 fastchess error/unknown/invalid/illegal lines: PASS (0 == 0)
tsv_sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/M14_games.tsv): faa30150d720b6bac51eabaa6a35c0de7d44eeff72de6c3a37d6c18da0e4f76b
fastchess_txt_sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/M14_fastchess.txt): 60e8f0b1a3eb0e079748ecfdd88afe796558db4db6e2d1b8c61cdcd18e84a543
PREDICTION (2) CHECK: M14 Elo = -9.50 (predicted -5.0, falsification range outside [-14.0, +4.0] -> TRUE)
```

### 5. Part T3 (`forge-combo29/carbon2/job47/partT3_summary.txt`)

```text
=== JOB 47 PART T3: SELF-PLAY COST WITH FAST IdeaB8b ON SET A LINE L (12 Runs: A B A B A B, then B A B A B A, Pinned Core 1) ===
start_utc: Fri Nov 20 10:46:52 PM UTC 2026
exe_path: /tmp/carbon2_job47/bld_bundle10/forge
exe_sha256(/tmp/carbon2_job47/bld_bundle10/forge): cb49d8824518cf392cf0763ac79e389febd3f6156f063145ef5cbe5cee6daee5

--- 1. Known Answers Checked Before Any Time Counts ---
A (all_off)     invariant across all 6 runs: records=26741, searches=26867, nodes=107124743, record_text_sha256=d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
B (bundle_fast) invariant across all 6 runs: records=27817, searches=27939, nodes=112503041, record_text_sha256=bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
B / A deterministic structural ratios: records=1.040238, nodes=1.050206
  T3_01_fwd_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_01_fwd_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_01_fwd_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_01_fwd_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_01_fwd_A_all_off pre-readyok lines       : PASS (0 == 0)
  T3_02_fwd_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_02_fwd_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_02_fwd_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_02_fwd_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_02_fwd_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_02_fwd_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_03_fwd_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_03_fwd_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_03_fwd_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_03_fwd_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_03_fwd_A_all_off pre-readyok lines       : PASS (0 == 0)
  T3_04_fwd_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_04_fwd_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_04_fwd_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_04_fwd_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_04_fwd_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_04_fwd_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_05_fwd_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_05_fwd_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_05_fwd_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_05_fwd_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_05_fwd_A_all_off pre-readyok lines       : PASS (0 == 0)
  T3_06_fwd_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_06_fwd_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_06_fwd_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_06_fwd_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_06_fwd_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_06_fwd_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_07_rev_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_07_rev_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_07_rev_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_07_rev_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_07_rev_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_07_rev_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_08_rev_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_08_rev_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_08_rev_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_08_rev_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_08_rev_A_all_off pre-readyok lines       : PASS (0 == 0)
  T3_09_rev_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_09_rev_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_09_rev_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_09_rev_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_09_rev_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_09_rev_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_10_rev_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_10_rev_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_10_rev_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_10_rev_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_10_rev_A_all_off pre-readyok lines       : PASS (0 == 0)
  T3_11_rev_B_bundle_fast records vs T2 B     : PASS (27817 == 27817)
  T3_11_rev_B_bundle_fast searches vs T2 B    : PASS (27939 == 27939)
  T3_11_rev_B_bundle_fast nodes vs T2 B       : PASS (112503041 == 112503041)
  T3_11_rev_B_bundle_fast sha256 vs T2 B      : PASS (bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d == bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d)
  T3_11_rev_B_bundle_fast attempt rows equal vs T2_02_fwd_B: PASS (204 == 204)
  T3_11_rev_B_bundle_fast pre-readyok lines   : PASS (0 == 0)
  T3_12_rev_A_all_off records vs T2 A         : PASS (26741 == 26741)
  T3_12_rev_A_all_off searches vs T2 A        : PASS (26867 == 26867)
  T3_12_rev_A_all_off nodes vs T2 A           : PASS (107124743 == 107124743)
  T3_12_rev_A_all_off sha256 vs T2 A          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  T3_12_rev_A_all_off pre-readyok lines       : PASS (0 == 0)

--- 2. All 12 Runs in Execution Order ---
  run_id                    | pass | arm | records | searches |     nodes | wall_s  | records/s | records/hour | record_text_sha256
  --------------------------+------+-----+---------+----------+-----------+---------+-----------+--------------+-----------------------------------------------------------------
  T3_01_fwd_A_all_off       | fwd  |  A  |   26741 |    26867 | 107124743 | 44.2408 |    604.44 |    2175993.7 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
  T3_02_fwd_B_bundle_fast   | fwd  |  B  |   27817 |    27939 | 112503041 | 48.6345 |    571.96 |    2059057.3 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_03_fwd_A_all_off       | fwd  |  A  |   26741 |    26867 | 107124743 | 44.0385 |    607.22 |    2185988.9 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
  T3_04_fwd_B_bundle_fast   | fwd  |  B  |   27817 |    27939 | 112503041 | 48.9646 |    568.10 |    2045175.8 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_05_fwd_A_all_off       | fwd  |  A  |   26741 |    26867 | 107124743 | 44.5149 |    600.72 |    2162595.0 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
  T3_06_fwd_B_bundle_fast   | fwd  |  B  |   27817 |    27939 | 112503041 | 48.9410 |    568.38 |    2046163.6 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_07_rev_B_bundle_fast   | rev  |  B  |   27817 |    27939 | 112503041 | 48.6915 |    571.29 |    2056644.4 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_08_rev_A_all_off       | rev  |  A  |   26741 |    26867 | 107124743 | 43.9969 |    607.79 |    2188054.9 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
  T3_09_rev_B_bundle_fast   | rev  |  B  |   27817 |    27939 | 112503041 | 48.9318 |    568.49 |    2046546.8 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_10_rev_A_all_off       | rev  |  A  |   26741 |    26867 | 107124743 | 44.2044 |    604.94 |    2177782.0 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2
  T3_11_rev_B_bundle_fast   | rev  |  B  |   27817 |    27939 | 112503041 | 48.1455 |    577.77 |    2079968.0 | bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d
  T3_12_rev_A_all_off       | rev  |  A  |   26741 |    26867 | 107124743 | 43.9581 |    608.33 |    2189987.2 | d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2

--- 3. Means, Direction in Words, Split Into Nodes * Time-Per-Node, Beside Job 44 T2 ---
  A (all_off)     mean wall_s (all 6 runs)  : 44.1589 s (SD=0.2081 s) | mean records/s = 605.57 (2180066.9 / hr) | 0.412220 ms / 1k nodes
  B (bundle_fast) mean wall_s (all 6 runs)  : 48.7182 s (SD=0.3136 s) | mean records/s = 571.00 (2055592.7 / hr) | 0.433039 ms / 1k nodes
  DIRECTION IN WORDS (wall time)            : B takes 1.103246 times A's wall time (beside T2's 1.137204 without IdeaB8b_Fast).
  DIRECTION IN WORDS (records per second)   : B produces 0.942903 times A's records per second (beside T2's 0.914732 without IdeaB8b_Fast).
  DECOMPOSITION (nodes * time_per_node)     : B / A wall time = 1.050206 (nodes_B / nodes_A) * 1.050505 (time_per_node_B / time_per_node_A) = 1.103246 (beside T2's 1.050206 * 1.082839 = 1.137204).
  FORWARD WALL-TIME RATIO (B / A, runs 1..6): 1.103513 (B_fwd=48.8467 s / A_fwd=44.2647 s; +10.35%)
  REVERSE WALL-TIME RATIO (B / A, runs 7..12): 1.102978 (B_rev=48.5896 s / A_rev=44.0531 s; +10.30%)
  FORWARD RECORDS/SEC RATIO (B / A, runs 1..6): 0.942651 (B_fwd=569.48 / A_fwd=604.13)
  REVERSE RECORDS/SEC RATIO (B / A, runs 7..12): 0.943155 (B_rev=572.51 / A_rev=607.02)
  NOISE LINE (two A means: A_fwd=44.2647s vs A_rev=44.0531s): diff=0.2116 s (0.479% of A mean; ratio A_rev/A_fwd=0.995220)
  NOISE LINE (interleaved A[1,3,5]=44.3200s vs A[2,4,6]=43.9978s): diff=0.3222 s (0.730% of A mean; ratio=0.992730)

  PREDICTION (3) CHECK: B / A wall-time ratio = 1.103246 (predicted 1.090, falsification range outside [1.068, 1.115] -> TRUE)
  PART T3 OVERALL                             : PASS (1 == 1)
done_utc: Fri Nov 20 10:56:10 PM UTC 2026
```

### 6. Builds & Hashes (`forge-combo29/carbon2/job47/builds.txt`) and Timestamps (`stamps.txt`)

```text
=== JOB 47 BUILDS.TXT ===
1. r15d + v3 source tree: /tmp/carbon2_job36/tpl_r15d_v3
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf
   tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77

2. Step 0 plain r15d + v3 Release executable (reused): /tmp/carbon2_job44/bld_base_v3/forge
   exe sha256(/tmp/carbon2_job44/bld_base_v3/forge) = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c
   id_name = id name Chess Engine Forge 6.4.24 candidate

3. Step 0 bundle9 executable (reused from Job 44): /tmp/carbon2_job44/bld_bundle9/forge
   exe sha256(/tmp/carbon2_job44/bld_bundle9/forge) = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef
   id_name = id name Chess Engine Forge 6.4.24 candidate
   patch 1 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/bundle_grok7.patch.txt) = b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146
   patch 2 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt) = 16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326
   patch 3 sha256(/agent/repos/dwqww/forge-combo29/carbon2/job43/P9_B8_fast.patch.txt) = bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395

4. Step 0 + Part T3 bundle10 executable (bundle9 + /agent/repos/dwqww/forge-combo29/carbon2/job47/P10_on_bundle9.patch.txt): /tmp/carbon2_job47/bld_bundle10/forge
   exe sha256(/tmp/carbon2_job47/bld_bundle10/forge) = cb49d8824518cf392cf0763ac79e389febd3f6156f063145ef5cbe5cee6daee5
   id_name = id name Chess Engine Forge 6.4.24 candidate
   rebased patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/P10_on_bundle9.patch.txt) = b72e4c953571f708c016beba9e7dc164a63b5f1b849e5a4e2197a6c4e95b88fe
   original bundle8 patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt) = 47c4f2e84d67f3f507c6000ba43ec40a5b0a157eba8c54659da7ed02aba74c6e
   compile_flags = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS="/tmp/carbon2_job47/src_bundle10/src/nnue_weights.inc" -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread -I/tmp/carbon2_job47/src_bundle10/include
   link_flags    = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -O3 -march=sapphirerapids -flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=4 -pthread /tmp/carbon2_job47/bld_bundle10/obj/bitboard.o /tmp/carbon2_job47/bld_bundle10/obj/board.o /tmp/carbon2_job47/bld_bundle10/obj/book.o /tmp/carbon2_job47/bld_bundle10/obj/eval.o /tmp/carbon2_job47/bld_bundle10/obj/eval_params.o /tmp/carbon2_job47/bld_bundle10/obj/nnue.o /tmp/carbon2_job47/bld_bundle10/obj/nnue_v3.o /tmp/carbon2_job47/bld_bundle10/obj/search.o /tmp/carbon2_job47/bld_bundle10/obj/uci.o -o /tmp/carbon2_job47/bld_bundle10/forge

5. Official fastchess executable: /tmp/carbon2_job40/fastchess
   version = fastchess alpha 1.8.3 20261115-d6e3a7a
   git_commit(/tmp/carbon2_job40/fastchess_repo) = d6e3a7a71f8437a39836856ae78a3dcdc9bf934c
   exe sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007

6. Official opening book: /tmp/carbon2_job40/UHO_Lichess_4852_v1.epd
   lines(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 2632036
   book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a

7. Part P11(b) 6b98f217 + grok-043 Release executable: /tmp/carbon2_job47/bld_043_base/forge
   exe sha256(/tmp/carbon2_job47/bld_043_base/forge) = 56a73dc402d07e94344aa1953b5a50e303be29b0bf6dfec1effca93ec1a3b655
   patch sha256(/tmp/carbon2_job47/grok_043_idea.patch.txt) = b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81

8. Part P11(c-d) + Part M14 bundle11 executable (bundle10 + /agent/repos/dwqww/forge-combo29/carbon2/job47/P11_K4b.patch.txt): /tmp/carbon2_job47/bld_bundle11_k4b/forge
   exe sha256(/tmp/carbon2_job47/bld_bundle11_k4b/forge) = 7499b3e1b8b589606e46d227e48f06b7cc481a75cac1dfa67ddc19197ab47c2e
   id_name = id name Chess Engine Forge 6.4.24 candidate
   patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job47/P11_K4b.patch.txt) = 60209ff7852b5b2d8bd217579744242d3350f4e6e155a1fc0d4e388b165d3548
   compile_flags = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS="/tmp/carbon2_job47/src_bundle11_k4b/src/nnue_weights.inc" -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=sapphirerapids -flto=thin -pthread -I/tmp/carbon2_job47/src_bundle11_k4b/include
   link_flags    = clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -O3 -march=sapphirerapids -flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=4 -pthread /tmp/carbon2_job47/bld_bundle11_k4b/obj/bitboard.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/board.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/book.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/eval.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/eval_params.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/nnue.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/nnue_v3.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/search.o /tmp/carbon2_job47/bld_bundle11_k4b/obj/uci.o -o /tmp/carbon2_job47/bld_bundle11_k4b/forge

=== STAMPS ===
job47_claimed: Fri Nov 20 09:45:39 PM UTC 2026
step0_done: Fri Nov 20 09:59:15 PM UTC 2026
prediction_committed: Fri Nov 20 10:00:15 PM UTC 2026
partP11_done: Fri Nov 20 10:08:25 PM UTC 2026
partM14_done: Fri Nov 20 10:29:24 PM UTC 2026
partT3_done: Fri Nov 20 10:57:28 PM UTC 2026
report_done: Fri Nov 20 10:59:12 PM UTC 2026
```

---

## Analysis Sections

### Facts (Measured Directly in Job 47)

1. **Strict Option & Pre-`readyok` Verification:** Across Step 0, Part P11, Part M14 preflight, and Part T3, every engine session verified `100%` of sent `setoption` names against the executable's own `uci` declaration list, kept every line before `readyok` in `.meta`, and recorded `0` error/unknown/invalid/illegal lines (`PASS (0 == 0)` on all built-in-eval runs, and `0` bad lines alongside the 2 expected `info string NNUE v3 loaded/active` lines on `n[1..60]`).
2. **Orthogonality of Fast Paths (`bundle10`):** On `bundle10`, `IdeaB8b + IdeaB8b_Fast` matched `IdeaB8b` alone and Job 45 `P10c` on `200 == 200` `O` positions (`8,483,711` nodes), `IdeaB8 + IdeaB8_Fast` matched `IdeaB8` alone and Job 43 `P9c` on `200 == 200` `O` positions (`8,262,696` nodes), and `Set A line L` with `IdeaB8b + IdeaB8b_Fast + HindsightDepth` matched Job 44 `T2` (`IdeaB8b + HindsightDepth` without `IdeaB8b_Fast`) on `6 / 6` runs (`27,817` records, `27,939` searches, `112,503,041` nodes, `bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d`).
3. **Seat `043` (`K4b`) Known Answer & Regression on Top of Bundle (`M14`):** Seat `043` (`IdeaK4_Shrink = 32`) reproduced `9,500,069` (`OFF`) and `8,983,632` (`ON`) on `6b98f217` (`200 == 200` vs Job 38). Ported as `IdeaK4b` / `IdeaK4b_Shrink` (`32`) onto `bundle10` (`bundle11`), adding `IdeaK4b=true` on top of `IdeaB8b + IdeaB8b_Fast + HindsightDepth` under `PC20` at `nodes=20000` scored **`-9.50 +/- 8.30 (95% CI [-17.80, -1.20]; exact [-17.81, -1.20])`** (`781 - 863 - 1356 (score=0.486333)`, `LOS 1.24%`) across `3,000` games (`1,500` UHO pairs `2,022,501..2,024,000`), confirming `K4b` hurts on top of the bundle as well as alone (`-4.53 +/- 1.58` in `82,000` games).
4. **Self-Play Cost Reduction From `IdeaB8b_Fast` (`T3` vs `T2`):** On `Set A line L`, `IdeaB8b_Fast` lowered `B / A` wall time from `1.137204` (`+13.72%`, Job 44 `T2`) to **`1.103246`** (`+10.32%`, forward `1.103513`, reverse `1.102978`) and raised `B / A` records per second from `0.914732` (`-8.53%`) to **`0.942903`** (`-5.71%`). Because `nodes_B / nodes_A = 1.050206` is unchanged, `time_per_node_B / time_per_node_A` dropped from `1.082839` (`+8.284%`) in `T2` to **`1.050505`** (`+5.051%`) in `T3` (eliminating `39.03%` of the bundle's per-node time overhead in `softnodes=2000` self-play).

### Suspicions (Apart from Facts)

1. **Double-Counting Opponent Worsening in Reverse Futility Pruning (`TtPruneV2` + `IdeaK4b`):** Under `PC20`, `TtPruneV2=true` already subtracts `RfpMargin / 3` (`24` cp) when `ss->static_eval + (ss - 1)->static_eval > 2`. When `IdeaK4b` (`-32` cp when `(ss - 1)->static_eval < (ss - 3)->static_eval`) also triggers, the combined `-56` cp margin cut prunes non-PV nodes nearly a full depth step earlier (`RfpMargin = 72`), explaining why `M14` (`-9.50 +/- 8.30` Elo under `PC20`) is at least as negative as `K4b` alone under `S14` (`-4.53 +/- 1.58` Elo, where `TtPruneV2=false`).
2. **Why `IdeaB8b_Fast` Saves `39.0%` of Per-Node Extra Time in `T3` vs `56.3%` in `P10(d)`:** At `softnodes=2000` (`~4,000` nodes/search average on `Set A line L` vs `~42,400` nodes/search at depth 12 on `O`), each `selfgame` attempt executes `Worker::clear()` (`memset`/clearing history tables plus invalidating the 256-entry `b8b_fast_cache_`) on `ucinewgame` every `~134` searches (`~536k` nodes), and shallower trees spend a slightly higher fraction of `IdeaB8b`'s remaining time in `update_threat_role_b8b` / `note_role_b8b_swing` (which still call `role_b8b_threat(board)` on beta cutoffs / eval swings rather than `b8b_fast_cache_`). Routing `update_threat_role_b8b` and `note_role_b8b_swing` through `ensure_b8b_fast(board)` as well could likely remove most of the remaining `+5.05%` per-node overhead without changing any node count.

### Read and Not Tested (Apart)

1. Read seat `093` (`K4a`, `IdeaK4` / `IdeaK4_Shrink = 24`) side-by-side in `/tmp/carbon2_job47/src_bundle10/src/search.cpp` lines `3056-3062` while porting `K4b` (`IdeaK4b_Shrink = 32`); did not run an Elo match of `K4a` in Job 47 (`IdeaK4` remained `false` on both sides of `M14` and `T3`).
2. Read the `TtPruneV2` `rfp_worsening` formula in `/tmp/carbon2_job47/src_bundle10/src/search.cpp` lines `3052-3055`; did not test `IdeaK4b` with `TtPruneV2=false` on top of the bundle because `M14` specifies `PC20`.

### What I Did Not Do

- Did not modify repository engine source files in-place (`git status` outside `forge-combo29/carbon2/job47/` is completely clean).
- Did not check out, modify, or delete any `grok*` or handoff branch, and did not open any pull request.
- Did not commit any binaries, nets, PGNs, `.pyc` files, or archives.
- Did not edit `prediction_job47.txt` or any committed raw `.rows.txt` / `.tsv` / `fastchess.txt` file after commit.

### What I Am Not Sure About

- With `+/- 8.30` Elo half-width in `M14` (`95% CI [-17.80, -1.20]`), `M14` establishes with `98.76%` one-sided confidence (`1 - LOS`) that `IdeaK4b` hurts on top of the bundle under `PC20` with built-in evaluation, but the exact magnitude between `-2` Elo and `-17` Elo (and whether the `768`-unit v3 net shifts RFP eval-delta distributions) cannot be pinned down at `3,000` games.
- With built-in `256`-hidden NNUE evaluation (`~0.412 ms / 1k nodes` on `Set A line L`), per-node overhead is magnified relative to the PC's heavier `768x8` v3 net, where `IdeaB8b` + `IdeaB8b_Fast`'s remaining `+5.05%` built-in per-node cost will shrink as a fraction of total node time.

### Model Name

`Gemini 4 Carbon`

---

## Final Repository Status and Directory Listing Before Report Commit

Command: `git status --short && ls -R forge-combo29/carbon2/job47`

```text
 M forge-combo29/carbon2/job47/stamps.txt
?? forge-combo29/carbon2/job47/REPORT_carbon2_job47.md
?? forge-combo29/carbon2/job47/build_report.py
forge-combo29/carbon2/job47:
build_report.py
builds.txt
j47_lib.py
M14_fastchess.txt
M14_fastchess.txt.meta
M14_games.tsv
M14_liveness_bundle_only_O_d12.rows.txt
M14_liveness_bundle_only_O_d12.rows.txt.meta
M14_liveness_bundle_plus_IdeaK4b_O_d12.rows.txt
M14_liveness_bundle_plus_IdeaK4b_O_d12.rows.txt.meta
M14_liveness.txt
M14_recount.txt
P10_on_bundle9.patch.txt
P11b_6b98f217_043_off_O_d12.rows.rows.txt.meta
P11b_6b98f217_043_off_O_d12.rows.txt
P11b_6b98f217_043_on_O_d12.rows.rows.txt.meta
P11b_6b98f217_043_on_O_d12.rows.txt
P11c_bundle11_all_off_G_d12.rows.rows.txt.meta
P11c_bundle11_all_off_G_d12.rows.txt
P11c_bundle11_all_off_O_d12.rows.rows.txt.meta
P11c_bundle11_all_off_O_d12.rows.txt
P11d_bundle11_only_IdeaK4b_O_d12.rows.rows.txt.meta
P11d_bundle11_only_IdeaK4b_O_d12.rows.txt
P11_K4b.patch.txt
partP11_summary.txt
partT3_summary.txt
prediction_job47.txt
REPORT_carbon2_job47.md
run_partM14.py
run_partP11.py
run_partT3.py
run_step0.py
stamps.txt
step0_bundle10_all_off_G_d12.rows.txt
step0_bundle10_all_off_G_d12.rows.txt.meta
step0_bundle10_all_off_O_d12.rows.txt
step0_bundle10_all_off_O_d12.rows.txt.meta
step0_bundle10_B8_and_B8_Fast_O_d12.rows.txt
step0_bundle10_B8_and_B8_Fast_O_d12.rows.txt.meta
step0_bundle10_B8b_and_B8b_Fast_O_d12.rows.txt
step0_bundle10_B8b_and_B8b_Fast_O_d12.rows.txt.meta
step0_bundle10_only_IdeaB8b_O_d12.rows.txt
step0_bundle10_only_IdeaB8b_O_d12.rows.txt.meta
step0_bundle10_only_IdeaB8_O_d12.rows.txt
step0_bundle10_only_IdeaB8_O_d12.rows.txt.meta
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
step0_raw.txt
T3_01_fwd_A_all_off_SetA_L.rows.txt
T3_01_fwd_A_all_off_SetA_L.rows.txt.meta
T3_02_fwd_B_bundle_fast_SetA_L.rows.txt
T3_02_fwd_B_bundle_fast_SetA_L.rows.txt.meta
T3_03_fwd_A_all_off_SetA_L.rows.txt
T3_03_fwd_A_all_off_SetA_L.rows.txt.meta
T3_04_fwd_B_bundle_fast_SetA_L.rows.txt
T3_04_fwd_B_bundle_fast_SetA_L.rows.txt.meta
T3_05_fwd_A_all_off_SetA_L.rows.txt
T3_05_fwd_A_all_off_SetA_L.rows.txt.meta
T3_06_fwd_B_bundle_fast_SetA_L.rows.txt
T3_06_fwd_B_bundle_fast_SetA_L.rows.txt.meta
T3_07_rev_B_bundle_fast_SetA_L.rows.txt
T3_07_rev_B_bundle_fast_SetA_L.rows.txt.meta
T3_08_rev_A_all_off_SetA_L.rows.txt
T3_08_rev_A_all_off_SetA_L.rows.txt.meta
T3_09_rev_B_bundle_fast_SetA_L.rows.txt
T3_09_rev_B_bundle_fast_SetA_L.rows.txt.meta
T3_10_rev_A_all_off_SetA_L.rows.txt
T3_10_rev_A_all_off_SetA_L.rows.txt.meta
T3_11_rev_B_bundle_fast_SetA_L.rows.txt
T3_11_rev_B_bundle_fast_SetA_L.rows.txt.meta
T3_12_rev_A_all_off_SetA_L.rows.txt
T3_12_rev_A_all_off_SetA_L.rows.txt.meta
```
