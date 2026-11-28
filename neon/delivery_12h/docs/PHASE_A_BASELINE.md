# Filter Quest — Phase A: Verified Actual Baseline

- **Frozen At (PC):** 2026-11-27 14:26 PC
- **Author:** Gemini 4 Neon (`C:\nnue-lab\neon\filter_quest\`)
- **Audit Scope:** Strictly read-only inspection of `C:\nnue-lab\runs\forge\`, `pipeline\`, `forge\r15dsg\`, `D:\nnue folder2\`, and `F:\nnuelabs  3\`.
- **Provisional Claim Isolation:** The previously reported `+11 Elo` improvement is recorded strictly as **provisional** pending Fable's independent validation and is NOT mixed into this baseline.

---

## 1. Exact Current Source, Binary & Network Identifiers

| Component | Exact Path | Size (Bytes) | SHA256 (first 16 hex) |
|---|---|---|---|
| **Best Live Net** | `runs/forge/r0067/train/cand.fnn3` | `9,463,528` | `737F197808FEF489` |
| **Live Engine Binary** | `runs/forge/engines/v3-r15dsg-sp-clang/forge.exe` | `2,390,528` | `CEF2F21589102392` |
| **Engine Source Tree** | `forge/r15dsg/` (`src/uci.cpp`, `selfgame` enabled) | — | verified live tag `r15dsg-sp-clang` |
| **HCE Dump Binary** | `forge/build/hce_dump.exe` | `3,599,794` | `B915F9B8F7FEA227` |
| **Residual Teacher** | `runs/forge/teachers/b_full.pt` | `791,911` | `52BE981D04CC92CA` |
| **Legacy Validation Set** | `runs/forge/val/val.plain` | `10,123,499` | `4A9F57407CFE2A38` |
| **Live Filter Script** | `pipeline/nnloop/filterqc.py` | `9,442` | `D48FA8A358BBC6B1` |
| **Live Datagen Script** | `pipeline/nnloop/datagen_uci.py` | `58,740` | `58A69BD651E50D6A` |
| **Live Trainer (v3)** | `pipeline/forge_train_v3.py` | `35,639` | `62D63F1B72D79863` |
| **Shared Loader/Cache** | `pipeline/forge_train.py` | `48,553` | `37A884018C8EAF61` |
| **Parallel Slice Parser** | `pipeline/forge_parse.py` | `6,769` | `1C4684449551B23F` |
| **Live Loop Config** | `pipeline/config.forge.toml` | `54,328` | `D3C4F4EEC16EEDA7` |

- **Current NNUE Architecture (`FORGENN3`):** Standalone king-bucket net, `hidden = 768`, `8` mirrored king buckets (`× 768` inputs per perspective, factoriser `w1 + fac`, SCReLU `clamp(0..1)^2`), `8` output buckets by piece count `ob = clamp((pieces - 2) // 4, 0, 7)`, `QA = 255`, `QB = 64`, `eval_scale = 400`, WDL scaling `K = 2.25`.
- **Current Live Training Recipe (`config.forge.toml`):** `40` epochs, `batch_size = 8192`, `lr = 5e-4`, cosine `lr_cycles = auto` (`6, 12, 24, 40`), `w1_decay = 0.3`, target `mix = 0.75` (`75%` sigmoid search score + `25%` game result), `--keep-noisy` (`skip_noisy = false`, `skip_check = true`), residual teacher `b_full.pt` at weight `0.2` (`--teacher-once`), `FORGE_COMPACT=1` (`44 B/pos` on GPU including teacher + pass order), `max_window_positions = 388,000,000` (newest 25 rounds `r0178..r0202`).

---

## 2. Actual Dataset Size, Provenance & Storage Inventory (`audit_val_and_r0203_raw.json`)

- **Completed Filtered Rounds (`r0001..r0202`, 202 rounds):**
  - Total raw generated records: **`3,201,265,055`** (`3.201 billion`)
  - Total filter-kept records: **`3,039,943,727`** (**`94.9607%`**)
  - Total marked `VALUE_NONE`: **`161,321,328`** (`5.0393%`)
- **Untouched Raw Early-Selfplay Round (`r0203/data/raw/`, 517 files, NEVER filtered/trained):**
  - **`16,013,745`** raw records, **`121,387`** games (`early_selfplay.json`: `123,088` reported games, `7,287.4 pos/s` over `2,197.5s` on 16 workers with `r0067` net).
- **Current 25-Round Active Training Window (`r0178..r0202`):**
  - Raw records: **`400,209,897`** -> filter-kept: **`378,856,831`** (`94.6645%`) -> trained after `8.47%` in-check drop: **`~346.8M`** positions.
- **Measured On-Disk Storage Footprint (Across C:, D:, F:):**
  - **All 202 rounds in `raw_selfplay.binpack`:** **`5.971 GiB`** (**`1.999 bytes/raw record`** — `48×` smaller than `.plain`!)
  - **25 active rounds in `filtered.plain`:** **`35.417 GiB`** (`95.03 bytes/record`)
  - **25 active rounds in `filtered.plain.cache-n0c1.npz`:** **`24.879 GiB`** (`77.00 bytes/trained position`)
  - **43 archived `.plain.gz` on `C:`:** `11.569 GiB` (~20% of `.plain`, `~19 B/rec`)
  - **134 overflow `.plain.gz` on `F:\nnuelabs  3`:** `35.517 GiB` (`D:\nnue folder2` has marker only, `0.0 GiB`).

---

## 3. Data Formats & Evaluation-Label Conventions
- **Self-play generator (`forge/r15dsg/src/uci.cpp:run_selfgame` + `pipeline/nnloop/datagen_uci.py`):**
  - Starts from `startpos` (`book = ""`), plays **`8` uniformly random legal moves** (`plies 0..7`), then runs `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`.
  - Post-game rules (`_after_game`): `adjudicate_tablebase = true` (`syzygy345`, `<=5` pieces), `adjudicate_bare_king = true` (`bare_king_exact = false`, any mating material vs lone king), `ply_limit_skip_score = 300` (`6` plies).
  - `.plain` ASCII format: 6 lines/record (`fen`, `move`, `score`, `ply`, `result`, `e`), `95.03 B/record`.
  - **Label convention:** Both `score` (centipawns from `go softnodes 2000`, mean depth `~8.56`, mean `~3,517` nodes) and `result` (`-1`, `0`, `+1`) are **side-to-move (STM) perspective**.
  - `score = 32002 (VALUE_NONE)` marks a filtered-out record in `filtered.plain`.

---

## 4. Current Filtering Algorithm & Exact Rejection Accounting

Live `filterqc.py` runs single-threaded Python in rule order:
1. `score == VALUE_NONE` (`already_none`)
2. `abs(score) > 2000` (`score_limit`)
3. `ply < 0 or ply > 400` (`ply`)
4. `result != 0 and abs(score) >= 600 and (score > 0) != (result > 0)` (`score_result_conflict`)
5. `halfmove_clock > 80` (`rule50`)
6. `pieces < 4` (`few_pieces`)
7. `hash(" ".join(parts[:4])) in seen` (`duplicate` — **within-round only!**)

| Rejection Reason | All 202 Rounds (`3.201B` raw) | % of Raw | Window `r0178..r0202` (`400.2M` raw) | % of Raw | Untouched `r0203` Raw (`16.01M`) | % of Raw |
|---|---:|---:|---:|---:|---:|---:|
| **`duplicate` (within-round)** | `96,773,269` | `3.0230%` | `13,322,145` | `3.3288%` | `539,894` | `3.3714%` |
| **`rule50` (`> 80`)** | `35,709,121` | `1.1155%` | `5,173,554` | `1.2927%` | `205,853` | `1.2855%` |
| **`few_pieces` (`< 4`)** | `28,711,019` | `0.8969%` | `2,842,246` | `0.7102%` | `116,183` | `0.7255%` |
| **`score_result_conflict`** | `127,919` | `0.0040%` | `15,121` | `0.0038%` | `579` | `0.0036%` |
| **`score_limit` (`> 2000`)** | **`0`** | **`0.0000%`** | **`0`** | **`0.0000%`** | **`0`** | **`0.0000%`** |
| **`ply` (`<0` or `>400`)** | **`0`** | **`0.0000%`** | **`0`** | **`0.0000%`** | **`0`** | **`0.0000%`** |
| **Post-filter `in_check` (dropped in `forge_parse.py`)** | `~257M` (est) | `~8.0%` | `~32.1M` (est) | `~8.0%` (`8.47%` of kept) | `8.469%` of kept | `~8.01%` |

---

## 5. Measured Generation, Filtering & Parsing Throughput
- **Self-play (`r0178..r0202`, 16 threads, `selfgame`, `soft_nodes=2000`):** Mean **`7,694.2 pos/s`** (range `5,823..8,379 pos/s` under heat/share throttling; **`129.89 pos/game`**).
- **`filterqc.py` (1-thread Python):** Mean **`173,642 rec/s`** (`92.19 s` for 16M records -> **`~3.2 hours`** at Server Day `2.0B`!).
- **Stockfish `.binpack` conversion (`r0202/data/convert.log`):** **`~840,000 pos/s`** (`~19 s` for 16M -> `~40 min` at `2.0B`).
- **`forge_parse.py` (`chess.Board(fen).is_check()` + `hce_dump.exe`):** `~131 s` for 5M records in 1 process (`~38k pos/s/core` -> **`~14 core-hours`** at `2.0B`!).

---

## 6. Cross-Round Duplication & Target Variance (`cross_round_dedup_r0178_r0202_m64.json`)
Exact deterministic `blake2b` `1/64` hash-partitioned scan across all **25 rounds (`378,856,831` filter-kept positions)**:
- **Cumulative cross-round duplication:** **`3.145%`** (`~11,910,912` duplicate rows = `0.78` rounds wasted in 25 rounds).
- **Marginal duplication curve:** Rises monotonically from `0.741%` (`r0179`) -> `2.969%` (`r0187`) -> `4.837%` (`r0202`).
- **Concentration by ply band:** `08_12: 0.815%`, `13_20: 0.853%`, `21_40: 0.675%`, `41_80: 0.659%`, **`81+: 6.385%`** (**`87.4%` of all cross-round duplicates are recurring endgames**, up to `25/25` rounds!).
- **Target variance across duplicates (`102,291` sampled dup groups):** `mean_within_fen_score_sd = 15.42 cp`, `mean_within_fen_result_sd = 0.0253`, `opposite_win_and_loss = 0.11%` (highly consistent labels, low conflict).
- **Server-Day Warning:** Opening dup rate is artificially low (`0.8%`) ONLY because of `8` uniform random moves; switching to realistic opening books on Server Day will sharply increase opening duplication unless cross-round deterministic dedup or target averaging is enabled.

---

## 7. Score Saturation, Phase/Material Distribution & Shift vs Real Games (`audit_r0202.json` & `m4_vs_train_shift.json`)
- **Q4 Sigmoid Gradient Saturation (`r0202`):**
  - `0_99`: `34.96%` (`mean_grad 0.2427`, `corr 0.258`)
  - `100_249`: `23.20%` (`mean_grad 0.1862`, `corr 0.666`)
  - `250_499`: `17.33%` (`mean_grad 0.0786`, `corr 0.925`)
  - `500_799`: `10.49%` (`mean_grad 0.0160`, `corr 0.983`)
  - **`800_1199`: `7.52%` (`mean_grad 0.00172`, `141×` down, `corr 0.991`)**
  - **`1200_2000`: `6.50%` (`mean_grad 0.00007`, `3,466×` down, `corr 0.989`)**
  - Total `|score| >= 800`: **`14.015%` (`2.12M`/round = `~280M` at Server Day 2B)** with near-zero learning gradient!
- **Q5 Distribution Shift (`r0202` training vs `M4 c100` 1,279,332 real game moves):**
  - `ob0` (`<= 5` pieces TB): `5.38%` train vs `9.57%` M4 (**`0.562×`, `-44%` under-represented**)
  - `ob7` (`29..32` pieces opening): `11.83%` train vs `7.12%` M4 (**`1.663×`, `+66%` over-represented**)
  - `0_99 cp` (balanced chess): `34.96%` train vs `47.32%` M4 (**`0.739×`, `-26%` under-represented**)
  - `250_499 cp` (lopsided openings): `17.33%` train vs `9.81%` M4 (**`1.766×`, `+77%` over-represented**)
  - `shield_broken` (confirmed blind-held-out weakness `z=+5.47`): `17.97%` train vs `21.87%` M4 (**`0.822×`, `-18%` under-represented**)
  - `bishop_pair_imbalance` (`14.97%` vs `15.02%`) and `queens_off` (`49.74%` vs `49.85%`) are well matched (`1.00×`).

---

## 8. Validation Set Defects & Verified Pipeline Weaknesses (`audit_val_and_r0203_raw.json`)
1. **Legacy `val.plain` is obsolete, unfiltered, and leaky:** Generated `2026-11-14 01:52:39` (Day 1, lock net `AL1 s198`, pre-`soft_nodes`/TB/`selfgame`), `820` games (`78,954` quiet pos used by `forge_train_v3.py`), `marked=0`, **`1.861%` internal duplicates**, and **`501` unique FENs (`0.477%`) overlap `r0202` alone**! Replaced in Phase C by untouched whole-game `eval_sets/final_eval_r0203_w14_w15.plain` (`204,180` records, `1,555` games).
2. **`selfgame` discards `st.check` computed on line 467 (`uci.cpp`):** Forces `8.47%` in-check records onto disk and into slow `python-chess` `is_check()` parsing (`patches/selfgame_skipcheck_optin.patch` ready).
3. **Target 149 (`pipeline/forge_train.py` lines 87 & 503):** BOTH `_load_one` AND `_count_one` omit `hce_dump.exe` identity from the cache key (`patches/cache_key_t149.patch` verified PASS).
4. **`filterqc.py` defects:** Stale docstring; omits `in_check`/`noisy` telemetry; writes `849k` `VALUE_NONE` rows into `filtered.plain` (`80.7 MB`/round wasted); dead `score_limit` & `ply` rules (`0` hits in 3.20B); `ply < last_ply` undercounts games (`121,778` vs `121,783` in `r0202`); process-randomized `hash()`; no corrupt FEN/result validation (`patches/filterqc_integrity_telemetry.patch` ready).
5. **Within-band tactical horizon swings (`Q3`) & drawn-game conflicts (`Q2`):** Unfiltered `swing >= 400` in `100_249 cp` collapses `corr` by `-34%` (`0.669 -> 0.438`); `14,542`/round `res == 0, |score| >= 600` conflicts (`81.3%` endgames) largely reflect unconverted winning endgames (`K+Q vs K+N`) drawn by repetition/50-move.
6. **Unnecessary `hce_dump.exe` invocation:** `forge_parse.py` invokes `hce_dump.exe` on every position even when training standalone nets without a residual teacher.
