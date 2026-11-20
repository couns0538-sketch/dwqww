# REPORT: `carbon2` Job 41 — The Two Leaders on the PC's Search (`IdeaB8b` Seat `028` Port, `HindsightDepth`, Cost per Node, and Matches)

1. **Step 0 (`PASS`):** `PASS (1 == 1)` (`forge-combo29/carbon2/job41/step0_raw.txt`). Plain `r15d + v3` (`/tmp/carbon2_job36/tpl_r15d_v3`) verified all four source file `sha256`s with `0 == 0` CRLF, listed `HindsightDepth` in `uci` (`True == True`, `0 == 0` invalid/unknown responses, `0 == 0` stderr bytes), and passed every OFF lock (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`; `PC20` `278024 == 278024`, `587276 == 587276`; `Set A line L` `26741 == 26741`, `107124743 == 107124743`, `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`; `n[1..60] line L` `8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`). Applying `forge-combo29/carbon2/job39/bundle_grok.patch.txt` on a fresh copy (`/tmp/carbon2_job41/src_bundle6`) passed every OFF number and matched Job 39 `P6_B8_078_on_O_d12.rows.txt` with `IdeaB8=true` alone on (`8262696 == 8262696`, `200 == 200` positions).
2. **Prediction Graded (`2` of `3` `TRUE`):** Committed alone in `633758f1e` (`1 file changed`, `forge-combo29/carbon2/job41/prediction_job41.txt`, `sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/prediction_job41.txt) = 9eb41e53aa30a47394d18ac97d8c8ce715c6232f8058998b2626d8e364bb5b0f`, stamp `Fri Nov 20 04:05:47 PM UTC 2026`) before Part P7's first build:
   - `(1)` `IdeaB8b` alone on, `O` depth 12 node ratio vs `8,315,168`: predicted `1.008` in `[0.965, 1.055]`; observed `8,483,711 / 8,315,168 = 1.020269` -> **`TRUE`** (`0.965 <= 1.020269 <= 1.055`).
   - `(2)` `M3` (`IdeaB8b` alone vs all off, `2,000` games, `nodes=20000`, `PC20`, built-in eval): predicted `+5.0` Elo in `[-4.0, +14.0]`; observed **`+8.69 +/- 10.21` Elo** -> **`TRUE`** (`-4.0 <= +8.69 <= +14.0`).
   - `(3)` `M4` (`HindsightDepth` alone vs all off, `2,000` games, `nodes=20000`, `PC20`, built-in eval): predicted `+4.0` Elo in `[-4.5, +12.5]`; observed **`+13.73 +/- 10.34` Elo** -> **`FALSE`** (`+13.73 > +12.50` by `+1.23` Elo; `HindsightDepth` exceeded the top of our predicted range).
3. **Part P7 (`PASS`, `1 == 1`):** Hand-ported seat `028`'s `IdeaB8` onto `r15d + v3` as `IdeaB8b` (`IdeaB8b` default `false`, `IdeaB8b_Weight` default `1024` `[0, 4096]`, `IdeaB8b_Swing` default `40` `[0, 500]`) with completely separate per-worker table `ThreatRoleHistoryB`, cache `role_b8b_*`, and `SearchStack` flag `role_b8b_eval_valid`, emitting `P7_B8b_028.patch.txt` (`383` lines), `B8_both.patch.txt` (`616` lines), and `bundle_grok7.patch.txt` (`1,281` lines). On `bundle_grok7` (`/tmp/carbon2_job41/bld_bundle7/forge`), all 7 switches off matched every Step 0 OFF number plus Job 39 `OFF_O_d12` (`8315168 == 8315168`, `200 == 200`) and `OFF_G_d12` (`17611204 == 17611204`, `353 == 353`); each of the 6 old switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS10`, `IdeaB8`) alone on matched its Job 39 `P1..P6` `O` rows position by position (`200 == 200` for all 6); `IdeaB8b` alone on produced `O` sum **`8,483,711`** (`200 / 200` positions differ from OFF `O`; `198 / 200` differ from `078`'s `IdeaB8`), `G` sum **`17,366,116`** (`349 / 353` differ from OFF `G`), and `Set A line L` **`26,709` records / `26,829` searches / `106,651,211` nodes / `sha256 = de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31`**; and `P7_alone` and `B8_both` matched `bundle_grok7` position by position (`200 == 200`).
4. **Part K (`PASS`, `1 == 1`):** On `bundle_grok7` with all 7 `Idea*` switches `false` and `HindsightDepth=true` added to `PC20`: `O` depth-12 `sum_nodes` = **`8,732,910 == 8,732,910`**, first three positions **`12,572 == 12,572` / `30,191 == 30,191` / `29,126 == 29,126`**, **`200 == 200`** positions differ from OFF `O` (exact match to the PC's known answer); `G` depth-12 `sum_nodes` = **`17,555,215`** (`353 / 353` positions differ from OFF `G`); `Set A line L` = **`26,479` records / `26,607` searches / `106,153,887` nodes / `sha256 = 778c35b982cb1899123fc417b02780220c01e4aac0c5843ad98999e02fb66c20`**.
5. **Part T (`PASS`, `10` forward+reverse `O` d12 runs, `200 == 200` row-exact on all 10):** Mean of 4 all-off runs = **`0.514165 ms / 1,000 nodes`** (`rev/fwd` drift = `0.996365`). Paired `ms / 1,000 nodes` ratios vs mean of 4 all-off runs: `all_off_1 = 1.000364`, `all_off_2 = 0.999636`, **`only_B8b = 1.071331`** (`+7.13%`), **`only_HindsightDepth = 1.017575`** (`+1.76%`), **`only_B8 = 1.061543`** (`+6.15%`).
6. **Part M (`bundle_grok7`, `PC20`, built-in eval, zero adjudication):**
   - **`M0` (`COMPLETE`, `400 / 400` games, `FULL` `20k` vs `HALF` `10k`, lines `2,100,001..2,100,200`):** `228 - 35 - 137`, pentanomial `[0, 14, 37, 91, 58]`, **`+182.83 +/- 27.34` Elo** (`PASS: +182.83 > +20.00`; both `fastchess` and recount identical, and `M0_games.tsv` bit-identical to Job 40 `M0_games.tsv`).
   - **`M3` (`COMPLETE`, `2,000 / 2,000` games, `B8b_on` vs `all_off`, lines `2,004,501..2,005,500`):** `573 - 523 - 904`, pentanomial `[45, 230, 415, 250, 60]`, **`+8.69 +/- 10.21` Elo** (recount `+8.69 +/- 10.21` == `fastchess` `8.69 +/- 10.21`). `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller.
   - **`M4` (`COMPLETE`, `2,000 / 2,000` games, `HindsightDepth_on` vs `all_off`, lines `2,005,501..2,006,500`):** `591 - 512 - 897`, pentanomial `[45, 227, 393, 274, 61]`, **`+13.73 +/- 10.34` Elo** (recount `+13.73 +/- 10.34` == `fastchess` `13.73 +/- 10.34`). `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller.
   - **`M5` (`CUT` at Minute-73 safety stop, `1,007 / 2,000` games = `503` complete pairs + `1` unpaired, `B8_on` (`078`) vs `all_off`, lines `2,006,501..2,007,500`):** recounted on all `1,007` games / `503` pairs: `281 - 262 - 464`, pentanomial `[22, 118, 211, 124, 28]`, **`+6.22 +/- 14.23` Elo**; last `fastchess` `-ratinginterval 25` line (`1,002` games / `501` pairs): `278 - 261 - 463`, pentanomial `[22, 118, 210, 123, 28]`, **`+5.90 +/- 14.27` Elo**. `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller (`1,007` games / `503` pairs carry `+/- 14.23` Elo here).

Model: `Gemini 4 Carbon`

---

## WHAT THIS CANNOT SEE

Built-in evaluation, not the v3 net; fixed nodes, not a clock; 2,000 games per single (~+/-7.5 Elo). What survives here is what the PC tests at STC and LTC with the v3 net; what only fails inside +/-7.5 Elo is not dead — only a gross fault is.

---

## Named Hashes & Executables (`builds.txt` & Patch Artifacts)

Every hash below names the exact object hashed beside its path as it exists:

- `r15d + v3` source tree (`/tmp/carbon2_job36/tpl_r15d_v3`, `0 == 0` CRLF on all 4 files):
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp) = 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/uci.cpp) = 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/src/board.cpp) = 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf`
  - `tree file sha256(/tmp/carbon2_job36/tpl_r15d_v3/include/forge/board.hpp) = 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77`
- Upstream & Job 39 input patches:
  - `patch sha256(/tmp/carbon2_job40/grok_028_idea.patch.txt) = f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474` (`361` lines, from `for-fable-and-opus/grok-028` commit `4bf95fd80adf523e97fa250bb8572c946cf0fc75`)
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job39/P6_B8_078.patch.txt) = b8bf053cdd0f8c22c977a07126c7412b689bbbf8b157d15122717282a32d2a92`
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job39/bundle_grok.patch.txt) = d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec`
- Job 41 prediction file:
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/prediction_job41.txt) = 9eb41e53aa30a47394d18ac97d8c8ce715c6232f8058998b2626d8e364bb5b0f`
- Job 41 emitted patches (all `diff -u` against `r15d + v3`, `0 == 0` CRLF, `git apply --check -p1` exit `0 == 0`):
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/P7_B8b_028.patch.txt) = 577302fc5db421ffe8b6b68e4071cc1779a03c3d20e6fbe5c38b770c2f865384` (`383` lines)
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/B8_both.patch.txt) = 7753970bae3541ed8edfbe16543b9f1c92e8c4410cf39ff3915d68ffb913dc9e` (`616` lines)
  - `patch sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/bundle_grok7.patch.txt) = b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146` (`1,281` lines)
- Job 41 Release executables (`clang++-18 -O3 -DNDEBUG -march=sapphirerapids -flto=thin`, `id name Chess Engine Forge 6.4.24 candidate`, full flags in `forge-combo29/carbon2/job41/builds.txt`):
  - `exe sha256(/tmp/carbon2_job41/bld_base_v3/forge) = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`
  - `exe sha256(/tmp/carbon2_job41/bld_bundle6/forge) = 51b02622087b4fb10aa9bd7e2a0455a9c9b5a9ec563fe822a3b12e44161c0cfa`
  - `exe sha256(/tmp/carbon2_job41/bld_p7_alone/forge) = 6c575bd806a3ad00cc2d451f56ace783a34d01e10b5878ff2d1ca7b3f390b6f5`
  - `exe sha256(/tmp/carbon2_job41/bld_b8_both/forge) = bc85a0621ff10cfcfb9eb1f7412bb29f04a28446e5f91914af4c089ce78838c5`
  - `exe sha256(/tmp/carbon2_job41/bld_bundle7/forge) = cee1bfcba5c405017d50bdc16156ddc47ba10b83018c47144611020595420df4`
- Test sets, `fastchess`, and opening book:
  - `set sha256(/tmp/carbon2_job39/sets/first200.fens) = ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (`200` FENs)
  - `set sha256(/tmp/carbon2_job39/sets/set_G.epd) = f2ebacbaefcbffbf16b5be2c01f0df31484d9f1d0cd4c2e1dc02d068cd1bc9e0` (`353` EPDs)
  - `exe sha256(/tmp/carbon2_job40/fastchess) = a3631c3ea944dfe4505d09f642871905e9662d930e9d438c7fb91cd2cb063007` (`fastchess alpha 1.8.3 20261115-d6e3a7a`, commit `d6e3a7a71f8437a39836856ae78a3dcdc9bf934c`)
  - `book sha256(/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd) = 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (`2632036 == 2632036` lines)

---

## Facts

### 1. Part P7 & Part K Deterministic Search Summary (`bundle_grok7`, `PC20`, Built-in Eval)

| Setting on `bundle_grok7` | `O` d12 `sum_nodes` (`200` pos) | `O` Ratio vs OFF | `O` Diff (`any` / `nodes` / `bestmove` / `score`) | `G` d12 `sum_nodes` (`353` pos) | `G` Ratio vs OFF | `G` Diff (`any` / `nodes` / `bestmove` / `score`) | `Set A line L` (`records` / `searches` / `nodes` / `rows sha256`) |
|---|---:|---:|---|---:|---:|---|---|
| All OFF (`7` `Idea*` + `HindsightDepth` `false`) | `8,315,168` (`200 == 200` J39) | `1.000000` | `0 / 0 / 0 / 0` | `17,611,204` (`353 == 353` J39) | `1.000000` | `0 / 0 / 0 / 0` | `26,741` / `26,862` / `107,124,743` / `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2` |
| `IdeaK4` (`093`) alone | `8,080,229` (`200 == 200` J39 `P1`) | `0.971746` | — | — | — | — | — |
| `IdeaS32` (`074`) alone | `8,339,315` (`200 == 200` J39 `P2`) | `1.002904` | — | — | — | — | — |
| `IdeaB1` (`030`) alone | `8,548,042` (`200 == 200` J39 `P3`) | `1.028006` | — | — | — | — | — |
| `IdeaS13` (`016`) alone | `8,077,984` (`200 == 200` J39 `P4`) | `0.971476` | — | — | — | — | — |
| `IdeaS10` (`081`) alone | `8,314,153` (`200 == 200` J39 `P5`) | `0.999878` | — | — | — | — | — |
| `IdeaB8` (`078`) alone | `8,262,696` (`200 == 200` J39 `P6`) | `0.993690` | — | — | — | — | — |
| **`IdeaB8b` (`028`) alone (`P7`)** | **`8,483,711`** | **`1.020269`** | `200 / 200 / 43 / 185` (`198 / 198 / 45 / 185` vs `B8`) | **`17,366,116`** | **`0.986083`** | `349 / 349 / 79 / 322` | `26,709` / `26,829` / `106,651,211` / `de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31` |
| **`HindsightDepth` alone (`Part K`)** | **`8,732,910`** (`== 8,732,910` PC) | **`1.050239`** | `200 / 200 / 50 / 189` | **`17,555,215`** | **`0.996821`** | `353 / 353 / 88 / 323` | `26,479` / `26,607` / `106,153,887` / `778c35b982cb1899123fc417b02780220c01e4aac0c5843ad98999e02fb66c20` |

Cross-build checks (`partP7_summary.txt`):
- `P7_B8b_028.patch.txt` (`bld_p7_alone`) with `IdeaB8b=true` vs `bundle_grok7` with `IdeaB8b=true` on `O` d12: `PASS (8483711 == 8483711)`, `PASS (200 == 200)`.
- `B8_both.patch.txt` (`bld_b8_both`) with `IdeaB8b=true` vs `bundle_grok7` with `IdeaB8b=true` on `O` d12: `PASS (8483711 == 8483711)`, `PASS (200 == 200)`.
- `B8_both.patch.txt` (`bld_b8_both`) with `IdeaB8=true` vs `bundle_grok7` with `IdeaB8=true` on `O` d12: `PASS (8262696 == 8262696)`, `PASS (200 == 200)`.
- `B8_both.patch.txt` (`bld_b8_both`) with BOTH `IdeaB8=true` and `IdeaB8b=true` vs `bundle_grok7` on `PC20 bench 11`: `PASS (255862 == 255862)`.

### 2. Why Seat `028` (`IdeaB8b`) Differs Structurally from Seat `078` (`IdeaB8`)

From reading `/tmp/carbon2_job40/grok_028_idea.patch.txt` and `forge-combo29/carbon2/job39/P6_B8_078.patch.txt`:
1. **`King` (`PieceType == 6`) included as victim and Role-4 target (`KingWorth = 100000`):** Seat `028` includes `King` in `ours` (when in check, the checking piece is a cheaper attacker of `King`, `victim_type == 6 < 7`) and prices enemy `King` at `100000` in Role 4, so when a non-King piece of ours (`Knight..Queen`) is attacked by a cheaper enemy piece, a **quiet counter-check** (`attacks_bb` hits the enemy `King`, `enemy_worth = 100000 > victim_worth`) is classified as Role 4 ("creates a greater threat"). Seat `078` loops `Knight..Queen` only in both places.
2. **Role `0` (`none`) learned and applied:** When `threat.present == true` and a quiet move matches none of Roles `1..4`, `028` updates and reads `(*role_b8b_history_)[side][victim_type][attacker_type][0]` (`role == 0`), penalizing threat-ignoring quiet moves as a shared bucket; wait — `078` also maps `none` to bucket `4` (`0..4`), so both have 5 buckets, while their bucket order differs (`028`: `0=none, 1=step_away, 2=block, 3=attack_attacker, 4=dearer_threat`; `078`: `0=step_away, 1=block, 2=attack_attacker, 3=dearer_threat, 4=none`).
3. **Eval-swing credit on beta cutoff only (`note_role_b8b_swing`):** Seat `028` calls `note_role_b8b_swing` (`IdeaB8b_Swing = 40`, full `history_bonus(depth)`) **only inside `if (best_score >= beta)` on the quiet `best_move` that caused a cutoff**, whereas `078` calls `note_threat_swing` (`IdeaB8_Swing = 48`, `history_bonus(max(1, depth)) / 2`) after **every** quiet move in the move loop regardless of whether that move failed low or cut off.

### 3. Part T — Cost per Node (`10` Runs, `O` Set Depth 12, `PC20`, Built-in Eval, `taskset -c 1`)

- Mean of all 4 `all_off` runs (`01`, `02`, `09`, `10`): **`0.514165 ms / 1,000 nodes`** (`514.165 us / 1,000 nodes`); forward `0.515102`, reverse `0.513229`, `rev / fwd = 0.996365`.

| Setting | `node_sum` (`200 == 200` on fwd & rev) | `fwd_wall_s` | `rev_wall_s` | `mean_wall_s` | `fwd_ms/1k` | `rev_ms/1k` | `mean_ms/1k` | `ratio_vs_all_off` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `all_off_1` | `8,315,168` | `4.2744` | `4.2795` | `4.2769` | `0.514045` | `0.514659` | `0.514352` | **`1.000364`** |
| `all_off_2` | `8,315,168` | `4.2919` | `4.2557` | `4.2738` | `0.516158` | `0.511799` | `0.513978` | **`0.999636`** |
| `only_B8b` (`028`) | `8,483,711` | `4.6587` | `4.6877` | `4.6732` | `0.549130` | `0.552552` | `0.550841` | **`1.071331`** |
| `only_HindsightDepth` | `8,732,910` | `4.5788` | `4.5594` | `4.5691` | `0.524315` | `0.522089` | `0.523202` | **`1.017575`** |
| `only_B8` (`078`) | `8,262,696` | `4.4980` | `4.5217` | `4.5098` | `0.544380` | `0.547237` | `0.545808` | **`1.061543`** |

### 4. Part M — Match Results (`bundle_grok7`, `PC20`, Built-in Eval, `concurrency = 3`, Zero Adjudication)

| Match | Engines (`nodes`) | Book Slice (`UHO_Lichess_4852_v1.epd`) | Status & Games | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Recounted Elo `+/- 95%` | `fastchess` Own Elo `+/- 95%` | Note |
|---|---|---|---|---|---|---|---|---|
| `M0` | `FULL` (`20000`) vs `HALF` (`10000`), all off | `2,100,001..2,100,200` | `COMPLETE` (`400 / 400`) | `228 - 35 - 137` | `[0, 14, 37, 91, 58]` | **`+182.83 +/- 27.34`** | `+182.83 +/- 27.34` | `PASS (+182.83 > +20.00)` |
| `M3` | `B8b_on` (`20000`) vs `all_off` (`20000`) | `2,004,501..2,005,500` | `COMPLETE` (`2,000 / 2,000`) | `573 - 523 - 904` | `[45, 230, 415, 250, 60]` | **`+8.69 +/- 10.21`** | `+8.69 +/- 10.21` | `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller. |
| `M4` | `HindsightDepth_on` (`20000`) vs `all_off` (`20000`) | `2,005,501..2,006,500` | `COMPLETE` (`2,000 / 2,000`) | `591 - 512 - 897` | `[45, 227, 393, 274, 61]` | **`+13.73 +/- 10.34`** | `+13.73 +/- 10.34` | `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller. |
| `M5` | `B8_on` (`078`, `20000`) vs `all_off` (`20000`) | `2,006,501..2,007,500` | `CUT` (`1,007 / 2,000`; `503` pairs + `1` unpaired) | `281 - 262 - 464` (`fc` `@1002g`: `278 - 261 - 463`) | `[22, 118, 211, 124, 28]` (`fc` `@501p`: `[22, 118, 210, 123, 28]`) | **`+6.22 +/- 14.23`** | `+5.90 +/- 14.27` (`@1002g`) | `2,000` games carry about `+/- 7.5` Elo: they show a gross fault or a large effect, nothing smaller (`CUT` at `1,007` games before Minute 80). |

Verbatim `fastchess` final lines and committed file hashes:
- `M0`: `Games: 400, Wins: 228, Losses: 35, Draws: 137, Points: 296.5 (74.12 %) | Elo: 182.83 +/- 27.34, nElo: 273.06 +/- 34.05 | Ptnml(0-2): [0, 14, 37, 91, 58], WL/DD Ratio: 1.31`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M0_fastchess.txt) = f84460b412a77da3fd5adb12a829ebf432669256058fa37c18f1db4c45e8a26d`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M0_games.tsv) = 0c095ae31bb6f60884d37ce944eea9fabb712c3475eb432058273042803e73b0`
- `M3`: `Games: 2000, Wins: 573, Losses: 523, Draws: 904, Points: 1025.0 (51.25 %) | Elo: 8.69 +/- 10.21, nElo: 12.97 +/- 15.23 | Ptnml(0-2): [45, 230, 415, 250, 60], WL/DD Ratio: 0.96`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M3_fastchess.txt) = 38749508778dbab0e905134d9fb796a2bd69ed7dfe3500e501332b8f64d7848a`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M3_games.tsv) = acc4547a65629345be9797b26f90fdf560347bc039c33c047c3bec3c34a0010e`
- `M4`: `Games: 2000, Wins: 591, Losses: 512, Draws: 897, Points: 1039.5 (51.98 %) | Elo: 13.73 +/- 10.34, nElo: 20.25 +/- 15.23 | Ptnml(0-2): [45, 227, 393, 274, 61], WL/DD Ratio: 0.98`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M4_fastchess.txt) = 96635eeb42331de518e47bf73161a9395215e54b3353aef34886db1639d56bb7`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M4_games.tsv) = bd901c0620605ef8f27828fb2c437338b90675650f0719f9a0372874f4714b65`
- `M5` (`CUT` at `17:14:00 UTC` Minute-73 safety stop; `1,007` finished games = `503` complete pairs + `1` unpaired game, `0 == 0` non-normal terminations, `503 == 503` opening FEN pairs matching book lines `2,006,501..2,007,003`):
  - Last `fastchess` `-ratinginterval 25` line (`1,002` games): `Games: 1002, Wins: 278, Losses: 261, Draws: 463, Points: 509.5 (50.85 %) | Elo: 5.90 +/- 14.27, nElo: 8.89 +/- 21.51 | Ptnml(0-2): [22, 118, 210, 123, 28], WL/DD Ratio: 0.89`
  - Recount from `M5_games.tsv` (`1,007` games, `503` pairs): `W-L-D = 281 - 262 - 464`, `Ptnml = [22, 118, 211, 124, 28]`, `Elo = +6.22 +/- 14.23` (`nElo = +9.39 +/- 21.47`, `LOS = 80.42%`)
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M5_fastchess.txt) = 14e7391c4c3075afc5e87c3e83a78ada50ac0d760560bc83a333d469c3f87ea1`
  - `file sha256(/agent/repos/dwqww/forge-combo29/carbon2/job41/M5_games.tsv) = 2231c66e9e0242850db487e46fcaa3e39ba0729541dc1d613b17f160994a98a3`

---

## Suspicions

- **Clock STC/LTC trade-off between `HindsightDepth` and `IdeaB8b`:** At fixed `nodes=20000` (built-in eval), both `HindsightDepth` (`+13.73 +/- 10.34` Elo) and `IdeaB8b` (`+8.69 +/- 10.21` Elo) are positive. Under wall-clock STC/LTC, `HindsightDepth` adds only `+1.76%` time per `1,000` nodes in built-in-eval Part T (and even less fractionally under the heavier `v3` NNUE), whereas `IdeaB8b` adds `+7.13%` time per `1,000` nodes under built-in eval (`~35.6 ns/node` from `board.attackers_to` in `role_b8b_threat` and slider ray generation in `threat_role_b8b_of`, which will shrink in relative percentage under the slower `v3` NNUE eval but still costs ~2-3% nps unless `role_b8b_threat` or per-move `threat_role_b8b_of` is hoisted into `QuietScorer` / `MovePicker` per node).
- **Why `028` (`IdeaB8b`) appears stronger than `078` (`IdeaB8`):** Gating `note_role_b8b_swing` on `best_score >= beta` (`best_move` only) avoids rewarding failed-low quiet moves that merely improved `-(ss+1)->static_eval` tactically by leaving another piece hanging one ply deeper, and pricing `King` at `100000` turns quiet counter-checks under attack into Role-4 ("greater threat") history hits.

---

## Read and Not Tested

- Read `src/uci.cpp` (`lines 748-815`, `885-1065`) in `/tmp/carbon2_job36/tpl_r15d_v3` and confirmed `-DFORGE_EXPOSE_TUNABLES=1` is active in our Release builds, advertising both `IdeaB8b_Weight` and `IdeaB8b_Swing` in `uci`; did not test non-default values of `IdeaB8b_Weight` or `IdeaB8b_Swing`.
- Tested `B8_both` and `bundle_grok7` with BOTH `IdeaB8=true` and `IdeaB8b=true` simultaneously on `PC20 bench 11` (`255862 == 255862`), confirming non-interference when co-enabled, but did not play games with both `IdeaB8` and `IdeaB8b` on together.

---

## What I Did Not Do

- Did not modify any engine source file in `/agent/repos/dwqww`, did not touch any branch other than `for-fable-and-opus/carbon2-work`, did not create any pull request, and did not commit any `.pgn`, binary, or `__pycache__` file.
- Stopped `M5` (`IdeaB8` `078` alone vs `all_off`) cleanly at `1,007 / 2,000` games (`503` complete pairs + `1` unpaired game, marked `CUT`) at `17:14:00 UTC` (`Minute 72.7` from Job 41 claim `16:01:17 UTC`) so `M5` and `REPORT_carbon2_job41.md` are both committed and pushed well before Minute 80 (`17:21:17 UTC`).

---

## What I Am Not Sure About

- **Minor label note in `partP7_summary.txt` and `partK_summary.txt`:** When printing the parenthetical breakdown `(node diffs = ..., bestmove diffs = ...)`, `build_and_verify_p7.py` and `run_partK.py` compared tuple index `3` (`score`) rather than index `2` (`bestmove`) of `read_j39_rows`. Following the rule never to edit a committed summary/raw file, both files were left untouched, and Section "Facts -> 1" above reports all four exact counts (`any` / `nodes` / `bestmove` / `score`) computed directly from the committed `.rows.txt` files (`bestmove` diffs: `43 / 200` for `IdeaB8b` on `O`, `79 / 353` on `G`; `50 / 200` for `HindsightDepth` on `O`, `88 / 353` on `G`).
- **Why `2,000`-game 95% error bars are `+/- 10.2` Elo here vs `~ +/- 7.5` Elo in NNUE matches:** With built-in evaluation on `UHO` openings (`45%` draw rate, `WL/DD ~ 0.97`), pentanomial variance is higher than in NNUE play (`~65%+` draw rate), giving `+/- 10.21` / `+/- 10.34` Elo (`95%` CI) over `1,000` pairs (`2,000` games).

---

## UTC Timestamps (`forge-combo29/carbon2/job41/stamps.txt`)

```text
job41_claimed: Fri Nov 20 04:01:17 PM UTC 2026 (after pushing REPORT_carbon2_job40.md; Minute 80 = +80m from this stamp)
step0_done: Fri Nov 20 04:04:35 PM UTC 2026
partP7_done: Fri Nov 20 04:23:50 PM UTC 2026
partK_done: Fri Nov 20 04:27:12 PM UTC 2026
partT_done: Fri Nov 20 04:32:26 PM UTC 2026
partM0_done: Fri Nov 20 04:35:00 PM UTC 2026
partM3_done: Fri Nov 20 04:50:54 PM UTC 2026
partM4_done: Fri Nov 20 05:06:09 PM UTC 2026
partM5_done: Fri Nov 20 05:14:03 PM UTC 2026
report_done: Fri Nov 20 05:14:04 PM UTC 2026
```

---

## Final `git status --short && ls -R forge-combo29/carbon2/job41` Before Report Commit

```text
 M forge-combo29/carbon2/job41/stamps.txt
?? forge-combo29/carbon2/job41/REPORT_carbon2_job41.md
forge-combo29/carbon2/job41:
B8_both.patch.txt
build_and_verify_p7.py
builds.txt
bundle_grok7.patch.txt
j41_lib.py
M0_fastchess.txt
M0_fastchess.txt.meta
M0_games.tsv
M0_recount.txt
M3_fastchess.txt
M3_fastchess.txt.meta
M3_games.tsv
M3_recount.txt
M4_fastchess.txt
M4_fastchess.txt.meta
M4_games.tsv
M4_recount.txt
M5_fastchess.txt
M5_fastchess.txt.meta
M5_games.tsv
M5_recount.txt
P7_alone_B8b_on_O_d12.rows.txt
P7_alone_B8b_on_O_d12.rows.txt.meta
P7_B8b_028.patch.txt
P7_B8_both_only_B8b_O_d12.rows.txt
P7_B8_both_only_B8b_O_d12.rows.txt.meta
P7_B8_both_only_B8_O_d12.rows.txt
P7_B8_both_only_B8_O_d12.rows.txt.meta
P7_bundle7_all_off_G_d12.rows.txt
P7_bundle7_all_off_G_d12.rows.txt.meta
P7_bundle7_all_off_O_d12.rows.txt
P7_bundle7_all_off_O_d12.rows.txt.meta
P7_bundle7_only_B1_O_d12.rows.txt
P7_bundle7_only_B1_O_d12.rows.txt.meta
P7_bundle7_only_B8b_G_d12.rows.txt
P7_bundle7_only_B8b_G_d12.rows.txt.meta
P7_bundle7_only_B8b_O_d12.rows.txt
P7_bundle7_only_B8b_O_d12.rows.txt.meta
P7_bundle7_only_B8b_SetA_L.rows.txt
P7_bundle7_only_B8b_SetA_L.rows.txt.meta
P7_bundle7_only_B8_O_d12.rows.txt
P7_bundle7_only_B8_O_d12.rows.txt.meta
P7_bundle7_only_K4_O_d12.rows.txt
P7_bundle7_only_K4_O_d12.rows.txt.meta
P7_bundle7_only_S10_O_d12.rows.txt
P7_bundle7_only_S10_O_d12.rows.txt.meta
P7_bundle7_only_S13_O_d12.rows.txt
P7_bundle7_only_S13_O_d12.rows.txt.meta
P7_bundle7_only_S32_O_d12.rows.txt
P7_bundle7_only_S32_O_d12.rows.txt.meta
partK_HindsightDepth_G_d12.rows.txt
partK_HindsightDepth_G_d12.rows.txt.meta
partK_HindsightDepth_O_d12.rows.txt
partK_HindsightDepth_O_d12.rows.txt.meta
partK_HindsightDepth_SetA_L.rows.txt
partK_HindsightDepth_SetA_L.rows.txt.meta
partK_summary.txt
partP7_summary.txt
partT_01_fwd_all_off_1.rows.txt
partT_01_fwd_all_off_1.rows.txt.meta
partT_02_fwd_all_off_2.rows.txt
partT_02_fwd_all_off_2.rows.txt.meta
partT_03_fwd_only_B8b.rows.txt
partT_03_fwd_only_B8b.rows.txt.meta
partT_04_fwd_only_HindsightDepth.rows.txt
partT_04_fwd_only_HindsightDepth.rows.txt.meta
partT_05_fwd_only_B8.rows.txt
partT_05_fwd_only_B8.rows.txt.meta
partT_06_rev_only_B8.rows.txt
partT_06_rev_only_B8.rows.txt.meta
partT_07_rev_only_HindsightDepth.rows.txt
partT_07_rev_only_HindsightDepth.rows.txt.meta
partT_08_rev_only_B8b.rows.txt
partT_08_rev_only_B8b.rows.txt.meta
partT_09_rev_all_off_2.rows.txt
partT_09_rev_all_off_2.rows.txt.meta
partT_10_rev_all_off_1.rows.txt
partT_10_rev_all_off_1.rows.txt.meta
partT_summary.txt
port_notes.txt
prediction_job41.txt
REPORT_carbon2_job41.md
run_partK.py
run_partM.py
run_partT.py
run_step0.py
stamps.txt
step0_bundle6_only_IdeaB8_O_d12.rows.txt
step0_bundle6_only_IdeaB8_O_d12.rows.txt.meta
step0_raw.txt
```
