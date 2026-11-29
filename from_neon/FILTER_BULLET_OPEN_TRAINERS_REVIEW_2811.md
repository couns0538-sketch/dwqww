# Bullet & Open NNUE Trainers Filtering Review (`FILTER_BULLET_OPEN_TRAINERS_REVIEW_2811.md`)

**Target Scope:** `OPUS-2811-OWNER-NEON-48H-MORE` (Point 2: *"Research known fixes first: nnue-pytorch, Bullet, open trainers, cited exactly"*), `FILTER_V4`, and Server Day `2.0B` preparation  
**Date:** `2026-11-29` (`2026-11-28` local PC)  
**Deliverable Path:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave19\FILTER_BULLET_OPEN_TRAINERS_REVIEW_2811.md`  
**Status:** Literature, Open-Trainer API & Local Pipeline Synthesis — **Zero Elo Claims**

---

## 0. Provenance Key & Mandatory Evidence Rules

1. **Strict Attribution Labels (Only the 5 Labels Below Are Used):**
   - **`Opus verified`** — Independently recounted or confirmed by Opus from raw PGNs, `qc.json`, `r1_summary.json`, `master_gates_quick.json`, or source/config files in `C:\nnue-lab\neon\OPUS_TO_NEON.md`.
   - **`Neon's count`** — Measured by Neon / Teamwork audit scripts (`FILTER_DEEP_AUDIT_R0202_2811.json`, `FILTER_DROPPED_AUDIT_R0202_2811.json`, `ALL_MATCHES_SCOREBOARD.md`, `f_fix_summary.json`, `master_gates_quick.json`) and not yet independently re-executed by Opus or Fable.
   - **`Wave 18 verified`** — Verified against local `C:\nnue-lab\src\nnue-pytorch` (Git HEAD `17cfb7f06c36733f4b26af121595e636676f9b96`) and documented in `C:\nnue-lab\neon\forge_fixes\teamwork_wave18\FILTER_V4_SERVERDAY_HYPOTHESES_2811.md`.
   - **`Wave 19 verified`** — Directly read and cross-checked in Wave 19 against local `C:\nnue-lab\` files, `git rev-parse HEAD`, disk artifacts, or verbatim `search_web` source/documentation snippets.
   - **`HYPOTHESIS`** — Unmeasured filter, datagen, or trainer proposal requiring a declared A/B match (`250k` `SPRT [0, 10]` + independent Seed-2 replicate + idle `6+0.06` clock confirmation) before placement.

2. **Strict Separation of Citation Channels:**
   - **Local Verified Citations:** Exact paths under `C:\nnue-lab\...`, exact line numbers, verbatim quotes, and `git` HEAD SHA `17cfb7f06c36733f4b26af121595e636676f9b96` (`C:\nnue-lab\src\nnue-pytorch`). Note: no local clones of `bullet`, `viridithas`, `viriformat`, `Stormphrax`, `PlentyChess`, `Lynx`, `tcheran`, or `akimbo` exist under `C:\nnue-lab\` (**`Wave 19 verified`**).
   - **Web Verified Citations:** Verbatim identifiers, Rust struct snippets, and documentation retrieved via `search_web` in Wave 19 (explicitly marked `search_web`).
   - **Not Publicly Verified in Raw Source / Web Snippets:** Any struct field, CLI flag, scheduler symbol, or internal engine threshold not observed verbatim in local files or unprimed `search_web` snippets is segregated in Section 2.3 and never guessed.

3. **Non-Elo & SPRT Bias Discipline:**
   - Offline training/validation losses, `net_sanity` (`S1`/`S2`/`S5`), `OB0/OB1` cliff jumps, `heldout_syzygy_4k` MSE, and filtered row/correlation counts are strictly diagnostic — never Elo. Only declared `fastchess` matches decide playing strength.
   - Every `SPRT [0, 10]` match stopped early at `H1` carries upward early-stopping bias and must disclose that bias alongside fixed-horizon results.
   - This review makes no curative or guaranteed outcome claims for any candidate filter or trainer change.

---

## 1. Concise Baseline Summary: Forge Live (`r0202`) & Wave 18 `nnue-pytorch` (`17cfb7f0`)

### 1.1 Wave 18 `nnue-pytorch` (`17cfb7f06c36733f4b26af121595e636676f9b96`) Summary (`Wave 18 verified` / `Wave 19 verified`)

`C:\nnue-lab\neon\forge_fixes\teamwork_wave18\FILTER_V4_SERVERDAY_HYPOTHESES_2811.md` (lines `1–89`, verified against `git -C C:\nnue-lab\src\nnue-pytorch rev-parse HEAD` = `17cfb7f06c36733f4b26af121595e636676f9b96`, **`Wave 19 verified`**) audited Stockfish `nnue-pytorch` (`train.py`, `config.py`, `data_loader/config.py`, `data_loader/cpp/training_data_loader.cpp`, `data_loader/cpp/lib/training_data_entry.h`, `data_loader/cpp/lib/parallel_dataloader.h`, `model/config.py`, `model/lambda_utils.py`, `model/nnue.py`) against Forge Live (`r0202`) across eight axes without duplicating its full line-by-line table here:

| Axis (Wave 18 §2, lines `38–48`) | Forge Live (`r0202`) | Stockfish `nnue-pytorch` (`17cfb7f0`) |
|---|---|---|
| **1. Within-game subsampling** | `0%` random skip; keeps `101.32` quiet rows/game (`corr = 0.99697`) | `random_fen_skipping` (`N/(N+1)` skip) + `ShuffleWindowPool` (`1,048,576` entries) |
| **2a. Captures / promos / check** | `skip_check=True`, `--keep-noisy` live (`18.591%` noisy kept) | `filtered=True` drops `e.isCapturingMove() \|\| e.isInCheck()` |
| **2b. Early-ply filtering** | `random_move_count=8`, `write_min_ply=8`, `min_ply=0` (`9.47%` in `ply 8..19`) | `early_fen_skipping` + `soft_early_fen_skipping=20` (`ply 0->0.10 .. 20->1.00`) |
| **2c. Piece-count & `rule50`** | Hard `min_pieces=4` (`F-06`) + hard `r50 > 80` drop | 5-point Hermite piece spline (`pc=2..32`, `pc=32 -> 0.75`), no hard `r50` drop |
| **2d. Deduplication** | Within-round `hash(parts[:4])` only; `3.145%` cross-round dups remain | HyperLogLog `UniquePositionLogger` + `random_fen_skipping` + multi-billion packs |
| **3a. Extreme score tail** | `eval_limit=2000`; `|score|>=1200` is `6.843%` of quiet rows | No hard `1200` drop; `win_rate_model` clamps `[-2000, 2000]` + `remap_tablebase_score` |
| **3b. Score-vs-result conflicts** | `filterqc.py:109` requires `result != 0 & |score|>=600` (misses draws) | `wld_filtered=True` via ply-dependent `score_result_prob()` (`b *= 1.5`) |
| **3c. `score == 0` runs & 4. WDL/loss** | `232,370` adj `0->0` quiet pairs/round; constant `mix=0.75`, `pow=2.0`, 0 offset | Placeholder-zero skip + `random_fen_skipping`; `LambdaConfig` (`1.0->0.75`), offset `270`, `pow=2.5` |

Wave 18 §3 (`lines 56–79`) grouped the resulting proposals into Ranks `1–6` (`HYPOTHESIS`): `D-01` within-game decorrelation / `random_fen_skipping` + cross-round dedup (Rank 1), `F-03`/`F-03b` & `wld_filtered` (Rank 2), `F-06` `min_pieces=2` + `rule50` decisive recovery (Rank 3), `F-08` `0.25x` soft tail weight vs hard drop (Rank 4), soft early-ply + piece-count spline + `0->0` thinning (Rank 5), and isolated trainer WDL/loss scheduling (Rank 6).

### 1.2 Verified Forge Pipeline Mechanics (`C:\nnue-lab\pipeline\`, `Wave 19 verified`)

- **`C:\nnue-lab\pipeline\nnloop\datagen_uci.py`:**
  - Line `285`: `bm, sc = eng.search(pos_cmd, go_cmd, timeout=move_timeout)` — records only the single best move `bm` and score `sc` (no full PV line / no `pv[1]`).
  - Lines `306–307`: `if ply >= write_min_ply: recs.append((board.fen(), bm, score, ply, white_to_move))`.
  - Lines `353–355` (`_after_game`): writes `fen`, `move {bm}`, `score {score}`, `ply {ply}`, `result {res}`, `e` to `.plain`.
  - Lines `425–428` (`play_game_sg`): `sg <ply> <score> <bm> <fen>` — likewise emits only single `bm`, omitting `pv[1]`.
- **`C:\nnue-lab\pipeline\forge_parse.py`:**
  - Lines `44–52` (`is_noisy(codes: bytes, move: str) -> bool`): returns `True` only when `bm` itself is a promotion (`len(move) > 4`), capture (`codes[to] != 0`), or diagonal pawn en passant (`codes[frm] in (1, 7) and move[0] != move[2]`). It inspects **1 ply (`bm`) only** and never checks `pv[1]`.
  - Lines `100–132` (`parse_slice`): skips `sc == VALUE_NONE` (`32002`, line `100`), optionally drops `skip_noisy and is_noisy(codes, move)` (`105–107`) and `skip_check and chess.Board(fen).is_check()` (`108–110`), runs `hce_dump.exe` (`119–124`), and stores `codes`, `stm`, `score`, `res`, `hce`, `counts` (`125–132`) — **`ply` and `move` are discarded from `.npz` caches**.
- **`C:\nnue-lab\pipeline\nnloop\filterqc.py`:**
  - Lines `56–62`: reads `max_abs_score`, `min_ply`, `max_ply`, `dedup`, `conflict_score`, `max_halfmove_clock`, `min_pieces`.
  - Lines `103–122`: filters sequentially by `VALUE_NONE` (`103–104`), `abs(score) > max_abs` (`105–106`), `ply < min_ply or ply > max_ply` (`107–108`), `conflict and result != 0 and abs(score) >= conflict and (score > 0) != (result > 0)` (`109–110`, completely omitting `result == 0` draw conflicts), `int(parts[4]) > max_r50` (`111–112`), `pieces < min_pieces` (`114–116`), and within-round `hash(" ".join(parts[:4]))` (`117–122`).
- **`C:\nnue-lab\pipeline\config.forge.toml` (`Opus verified` at `OPUS_TO_NEON.md:3494–3497` + `Wave 19 verified`):**
  - Lines `274–280`: `random_move_count = 8`, `random_move_min_ply = 0`, `random_move_max_ply = 7`, `write_min_ply = 8`, `max_ply = 300`.
  - Lines `313–318`: `adjudicate_tablebase = true`, `tablebase_path = "C:/nnue-lab/tablebases/syzygy345"`, `eval_limit = 2000`, `draw_adj_ply = 80`, `draw_adj_score = 5`, `draw_adj_count = 8`. (`SyzygyPath` is **OFF** in search.)
  - Lines `330–336`: `max_abs_score = 2000`, `min_ply = 0`, `max_ply = 400`, `dedup = true`, `conflict_score = 600`, `max_halfmove_clock = 80`, `min_pieces = 4`.
  - Line `357`: `train_cmd` uses `--keep-noisy --lr-cycles auto --w1-decay 0.3 --mix 0.75 --distill-net C:/nnue-lab/runs/forge/teachers/b_full.pt --distill-weight 0.2 --teacher-once --hidden 768`.

### 1.3 Verified `r0202` Audit Totals & Match / GPU Ground Truth

**`r0202` Audit Counts (`Opus verified` + `Neon's count`):**
- `C:\nnue-lab\runs\forge\r0202\data\qc.json:2–14` (**`Opus verified`** at `OPUS_TO_NEON.md:3522–3524`): `16,005,733` raw records; `15,156,682` kept (`94.7%`); `849,051` dropped (`duplicate`: `526,611`; `rule50`: `206,406`; `few_pieces`: `115,569`; `score_result_conflict`: `465`; `score_limit`/`ply`/`already_none`: `0`); `121,778` games (`qc.json:5`).
- `C:\nnue-lab\neon\to_astra\FILTER_DEEP_AUDIT_R0202_2811.json:8–24,55–62,68–100,116–118,161–172` (**`Neon's count`**): `12,338,956` quiet kept; `2,817,726` noisy kept (`18.591%` of kept); `121,783` games detected (`101.32` quiet/game; `124.46` kept/game — **provenance note:** `qc.json:5` counts `121,778` games via `ply < last_ply` on raw records, whereas `FILTER_DEEP_AUDIT_R0202_2811.json:11` detects `121,783` games on `filtered.plain`). Adjacent quiet pairs (`10,650,131`) have `lag1_score_corr_quiet = 0.99697` and `mean_abs_swing_cp_quiet = 22.78`. Quiet `score == 0`: `364,905` (`2.957%`), `331,658` with `res == 0`, **`232,370`** adjacent exact-zero runs (`63.7%`). Early quiet `ply 8..19`: `381,861 + 398,039 + 388,294 = 1,168,194` (`9.47%` / `9.468%`, sum **`Wave 18 verified`** / **`Wave 19 verified`**). Missed conflicts: `res == 0 & |score| >= 400` = `64,679` (`0.5242%`); `res == 0 & |score| >= 300` = `168,748` (`1.3676%`); `res != 0 & opp >= 300` = `6,319` (`0.0512%`). Extreme tail `|score| >= 1200`: `510,320 + 334,026 = 844,346` (`6.843%`).
- `C:\nnue-lab\neon\to_astra\FILTER_DROPPED_AUDIT_R0202_2811.json:498–566` (**`Neon's count`**): `few_pieces` (`115,569`) = `KRvK 55,940`, `KvKR 36,450`, `KPvK 13,236`, `KvKP 9,499`, `KQvK 244`, `KvKQ 200`; `rule50` (`206,406`) holds `33,537` (`16.25%`) decisive rows; `duplicate` (`526,611`) has `469,107` (`89.08%` / `89.1%`) at `ply 80+`. Cross-round exact duplicates (`r0178..r0202`, `1/64` mod sample): `3.145%` (`186,108 / 5,918,109`), `87.38%` (`87.4%`) at `ply 81+` (`MONDAY_BARS_EVIDENCE_SUMMARY_2811.md:166–167`, `F_FIX_25R_V3_DECLARATION.json:13`, **`Neon's count`**).

**Current Match & GPU Ground Truth:**
- **`R1-skip` vs `R1-keep` (`250k` SPRT `[0, 10]`):**
  - Seed 1 (`OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k`): `1,526g`, `399-796-331`, `ptnml [9,154,368,224,8]`, **`+15.49 [+6.12, +24.88]`** (`LLR +2.97`, Opus `+3.01`), **`H1`** (**`Opus verified`**, `OPUS_TO_NEON.md:3128–3131`). **SPRT early-stopping upward bias disclosed** (Opus estimate `~+10..+15`).
  - Seed 2 (`OPUS_R1_skip_vs_R1_keep_SEED2_SPRT_0_10_250k`): `2,018g` paired (`2,019g` raw PGN), `518-1055-445` (`1,056 D` raw PGN), `ptnml [11,218,484,279,17]`, **`+12.57 [+4.28, +20.88]`** (`LLR +2.99`, Opus `+3.01`), **`H1`** (**`Opus verified`**, `OPUS_TO_NEON.md:3325–3327`). **SPRT early-stopping upward bias disclosed** (Opus two-seed estimate `~+8..+14`).
- **`R1-skip` vs `r0067` & Control (`Opus verified`, zero SPRT bias):**
  - `OPUS_R1_skip_vs_r0067_1000g_250k`: `1,000g`, `277-534-189`, `ptnml [4,90,237,152,17]`, **`+30.65 [+18.59, +42.79]`** (`OPUS_TO_NEON.md:3155`).
  - `OPUS_R1_skip_vs_r0067_2000g_6p006`: `2,000g`, `465-1107-428`, `ptnml [9,220,500,267,4]`, **`+6.43 [-1.47, +14.33]`** — **INCONCLUSIVE** (interval includes `0`; not negative; clock gap `24.2 +/- 7.4` Elo, `z ~ 3.3`, `OPUS_TO_NEON.md:3467–3475`).
  - `OPUS_R1_keep_vs_r0202_1000g_250k`: `1,000g`, `233-538-229`, `ptnml [10,110,252,122,6]`, **`+1.39 [-10.33, +13.11]`** (level control, `OPUS_TO_NEON.md:3428–3431`).
- **`F_FIX_25R_v2` (Finished GPU Training; Awaiting `250k` SPRT):**
  - `C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\f_fix_summary.json:1–20` (**`Neon's count`** + **`Wave 19 verified`** on disk): finished `2026-11-28 17:15:55` (`cand.fnn3` SHA-256 `31f5af1972532a9399643d1ffbe5a796164a787325bad0201603d8c020b60427`), `in_rows=281,241,466`, `kept_rows=261,866,722`, `drop_union=19,374,744` (`6.889%`).
  - `C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\master_gates_quick.json:147–172` (**`Neon's count`**) & `OPUS_TO_NEON.md:3639–3645` (**`Opus verified` note**): `hard_pass=true`, `S1=+36.4 cp`, **`FLAG S2 sum=+42.4 cp`** (`S2 fails by 2.4 cp` against `|sum| <= 40`), **`S5 KNN-K = +44 cp`** (`raw +74`) vs `R1-skip` (`S5 KNN-K +97 raw` / `60 cp` norm, `R2_DECLARATION.json:75`). `F_FIX_25R_v2_vs_R1_skip_SPRT_0_10_250k` has **NOT YET STARTED**.
- **`R2_live768_anchored_skipnoisy` & `F_FIX_25R_v3` (`Wave 19 verified`):** Both remain **QUEUED / NOT YET TRAINED** (no `cand.fnn3`/`cand.pt` weights and no `matches/` directories on disk as of `2026-11-29T02:03Z`; `gpu_runs/R2_live768_anchored_skipnoisy/` holds only staged `_patched_train_v3p.py` (`37,326` bytes, mtime `2026-11-28 17:57:51` local), while `gpu_runs/F_FIX_25R_v3/` is absent on disk; declared in `C:\nnue-lab\neon\to_astra\R2_DECLARATION.json` and `F_FIX_25R_V3_DECLARATION.json`).

---

## 2. Bullet (`jw1912/bullet`) & `viriformat` Review (Local + Web Verified)

### 2.1 Local Verified Bullet Citations (`C:\nnue-lab\survey\`, `Wave 19 verified`)

- **`C:\nnue-lab\survey\owner_study_top_engines.md:52,179–180`:** Cites `https://github.com/jw1912/bullet` as `"Rust trainer with a \"progression\" example (simple net → buckets → multi-layer)"`, quoting CPW NNUE (`"\"most widely adopted\""`), and notes Bullet users apply smooth LR decay to a small floor over more superbatches (`line 179`).
- **`C:\nnue-lab\survey\engine_building_research_opus_1611.md:32–34,59`:** Documents Bullet's `simple.rs` baseline (originally cited via `rust-digger.code-maven.com/src/bullet_lib-1.0.0/examples/simple.rs`, which `search_web` confirms is currently offline, **`Wave 19 verified`**): batch `16,384`, `6,104` batches per superbatch, `ConstantWDL` `0.75` (game result share `0.25`, matching Forge's `mix=0.75`), LR `0.001` dropped `10x` every `4` superbatches, and quotes `simple.rs` verbatim: **`"potentially a lot of elo available by adjusting the wdl and lr schedulers"`**.
- **`C:\nnue-lab\survey\speed_candidates.md:67–70`:** Records Bullet ROCm speed at `4.2 to 4.4 million` pos/s (warm, H256) and `about 2.0 million` for its H512 GPU trainer, compared with Forge's Triton v3 512 trainer at `2.7 to 4.0 million` unloaded (`1.4 to 2.9 million` loaded with teacher).
- **`C:\nnue-lab\survey\fo_read\opus_r13_r15_30h_deepres.md:16`:** Records `P4 (opus-r13-p4-v2nets)` — a prepared Bullet trainer for v2 nets with threat inputs and pawn pairs (`no GPU window`, `idea only`).
- **Licensing Boundary (`C:\nnue-lab\survey\digests\pack_03.md:39` & `pack_32.md:68`, `Wave 19 verified`):** `bullet_lib` links GPL-3.0 `sfbinpack` and AGPL-3.0 `montyformat` (trainer tool only — never link into engine binary).

### 2.2 Web Verified Specifications (`search_web` Verbatim Sources, `Wave 19 verified`)

| Component | Verified Identifiers & Exact Parameters | Verbatim Source (`search_web`) |
|---|---|---|
| **`bullet_lib::value::loader::viribinpack::Filter`** | Six fields confirmed verbatim on `Filter::default()`: `min_ply` (e.g. `16`), `filter_tactical` (`bool`, e.g. `true`), `filter_check` (`bool`, e.g. `true`), `max_eval` (e.g. `10000`), `random_fen_skipping` (`bool`, e.g. `true`), `random_fen_skip_probability` (`f64`/`f32`, e.g. `0.15`). | HuggingFace `wraith1337/ravager-net-ckpt` (`ravager_net.rs`) |
| **`ViriBinpackLoader` & `ViriFilter`** | `ViriFilter::Builtin(f)` passed to `ViriBinpackLoader::new_interleave_multiple(&refs, 2048, threads, ViriFilter::Builtin(f))` for streaming `.vf` files into `ValueTrainerBuilder`; `ViriFilter::Custom(...)` exists in documentation summaries. | HuggingFace `wraith1337/ravager-net-ckpt` (`ravager_net.rs`) + `jw1912/bullet` docs |
| **`TrainingSchedule` (`1_simple.rs`)** | `net_id: String`, `eval_scale: 400.0`, `steps: TrainingSteps { batch_size: 16_384, batches_per_superbatch: 6104, start_superbatch: 1, end_superbatch: superbatches }` (also `TrainingSteps::PerSuperbatch(superbatches)`), `wdl_scheduler`, `lr_scheduler`, `save_rate`, with `DirectSequentialDataLoader`. | `github.com/jw1912/bullet` `examples/progression/1_simple.rs` |
| **Verified Schedulers (`1_simple.rs`)** | `wdl::ConstantWDL { value: wdl_proportion }` (e.g. `0.75`) and `lr::CosineDecayLR { initial_lr, final_lr, final_superbatch: superbatches }` under `bullet_lib::trainer::schedule::{lr, wdl}`. | `github.com/jw1912/bullet` `examples/progression/1_simple.rs` |
| **`bullet-utils` Crate** | Companion workspace crate depending on `bulletformat`, `montyformat`, `viriformat`, `clap`, `anyhow`; documentation summaries reference `viribinpack` tools (`interleave`, `convert`, `shuffle`, `count`, `head`). | `github.com/jw1912/bullet` Cargo / summaries |
| **`cosmobobak/viriformat`** | Lossless game format (`Game`, `PackedBoard`, `Move`, `Score`) storing full games so `ViriFilter` runs dynamically at load time: `PackedBoard` (64-bit occupancy, 32x 4-bit pieces incl. unmoved rooks, 8-bit STM+ep, 8-bit halfmove, 16-bit fullmove, score, result) + alternating 16-bit LE `Move` (6b from, 6b to, 2b promo, 2b type) & `Score` pairs + 4 zero terminator bytes. | `github.com/cosmobobak/viriformat`, `crates.io`, `docs.rs` |

*Note (`Wave 19 verified`):* `Filter` and `ViriFilter` live in `bullet_lib::value::loader::viribinpack`, not in `cosmobobak/viriformat`. Context7 MCP indexes neither `jw1912/bullet` nor `viriformat`.

### 2.3 Explicit Boundary Table: Not Publicly Verified in Raw Source / Web Snippets

To prevent hallucinated API claims, the following items were explicitly tested via unprimed and targeted `search_web` probes and **MUST NOT** be cited as verified Bullet or open-engine source facts:

| Item / Symbol | Verification Outcome (`Wave 19 verified`) | Boundary Rule |
|---|---|---|
| `viribinpack::Filter` fields `max_ply`, `min_pieces`, `wdl_skip`, `zero_score`, eval-vs-result fields; full `pub struct Filter` definition | **Not Publicly Verified in Raw Source / Web Snippets.** Primed search queries elicited un-cited `/* ... */` placeholders, confirming raw source did not expose them. | Cite ONLY the 6 verified `Filter` fields from `ravager_net.rs` (`min_ply`, `filter_tactical`, `filter_check`, `max_eval`, `random_fen_skipping`, `random_fen_skip_probability`). |
| `wdl::LinearWDL` (Bullet Rust struct) | **Not Publicly Verified in Raw Source / Web Snippets.** Exact query `"wdl::LinearWDL" bullet_lib OR "LinearWDL {"` returned **0 results**. | Do NOT cite `wdl::LinearWDL` as a verified Bullet Rust struct. Cite `wdl::ConstantWDL` as Web Verified, and `nnue-pytorch` `LambdaController` + Renegade WDL ramping as `Wave 18 verified` / Local Survey Verified. |
| `bullet-utils` exact `clap` CLI flags & subcommand options | **Not Publicly Verified in Raw Source / Web Snippets.** No `--help` output or `bullet-utils/src/*.rs` verbatim text returned. | Cite crate dependencies & tool names (`interleave`, `convert`, `shuffle`, `count`, `head`) only; do not invent `--max-ply`/`--wdl` CLI flags. |
| `ViriFilter::Custom` closure signature & other `ViriBinpackLoader` constructors | **Not Publicly Verified in Raw Source / Web Snippets.** Only `ViriFilter::Builtin(f)` and `new_interleave_multiple(&refs, 2048, threads, ...)` are verbatim. | Do not specify closure argument types. |
| Internal thresholds of Viridithas, Stormphrax, PlentyChess, Lynx (`vftoepd` full CLI), `tcheran-chess/bullet`, `akimbo` (`filtering-hl512-baseline`) | **Not Publicly Verified in Raw Source / Web Snippets.** Only high-level README/doc/dataset values and `lynx-selfgen.md` snippet values (`MinPly 0`, `MinPieces 4`, `MaxEval 20000`, `FilterCheck`, `FilterCapture`, `Wld`) appeared. | Cite release/doc facts with their exact scope and caveats; do not extrapolate hidden constants. |

---

## 3. Open-Engine Practices & `fb2-j2` 2-Ply PV Filter

### 3.1 Cross-Engine Filtering & Training Comparison (Local Survey + Web Verified)

| Engine / Trainer | Dataset Scale & Opening Diversity | Position Filtering & Target Mix (`Wave 19 verified` Local / `search_web`) | Caveats & Counter-Evidence |
|---|---|---|---|
| **Viridithas** (`cosmobobak/viridithas` + `viriformat`) | Bookless self-play (v7–v8 for variety) + rescored human games (`owner_study_top_engines.md:177,251`; `engine_building_research_opus_1611.md:36–37`); `[features] datagen` Cargo flag (`search_web`). | Lossless `.vf` game stream filtered at load time via `ViriFilter` (`search_web`); deeper-search rescoring with newer net (`speed_candidates.md:76`: `+50 / +25 / +23.9` quoted in digest, HCE `-10.5`). | Internal Viridithas node/ply/filter constants not verified in raw source; activation notes not opened (`owner_study_top_engines.md:261`). |
| **Stormphrax** (`Ciekce/Stormphrax`) | Zero-knowledge self-play bootstrap from random net (`engine_building_research_opus_1611.md:35–36`, `search_web`). | `marlinformat`/`viriformat` self-play trained with `bullet` (`search_web`); pawn-pair inputs (`owner_study_top_engines.md:150`). | Exact internal ply, eval-cap, and tactical filter thresholds not verified in raw source. |
| **PlentyChess** (`Yoshie2000/PlentyChess`) | Large self-play (`15B+` positions across standard + DFRC reported via `search_web`). | Trained via `bullet`; threat inputs (`owner_study_top_engines.md:6,50,149`). | Exact internal datagen thresholds and PR internals not verified (`owner_study_top_engines.md:261`). |
| **Lynx** (`lynx-chess/Lynx`, `eduherminio/lynx-1.0`) | `542M` positions; `~15k` soft nodes/move, `1–4` random half-moves on UHO, no adjudication, `~40` pos/game (`owner_study_top_engines.md:175,223`). | `selfgen.md` & `vftoepd` (`search_web`): `MinPly` (`0`), `MinPieces` (`4`), `MaxEval` (`20000`), `FilterCheck`, `FilterCapture`, `Wld`; `owner_study_top_engines.md:175`: skip noisy best move & early plies, fixed sample/game. | Full `vftoepd` C# flag implementation not observed verbatim; `digests/pack_15.md:54` notes Lynx eval/result mismatch filter is literature-only (`L`) without isolated Forge Elo. |
| **`tcheran`** (`tcheran-chess/tcheran`) | `1B` positions (`+27.05 ± 9.85` 768w), `4 buckets + 2.1B` (`+19.04 ± 7.72`), longer LR schedule (`+14.19 ± 6.56`), Ranger vs AdamW (`+3.54 ± 2.80`) (`owner_study_top_engines.md:33,145–147,179`). | Uses `tcheran-chess/bullet` fork and UCI `'genfens'` for OpenBench datagen (`search_web`). | **Confounded:** `owner_study_top_engines.md:259` warns width gains changed data/length together; `tcheran-chess/bullet` diff unverified. |
| **`akimbo`** (`jw1912/akimbo`) | HCE self-play `<= v1.0.0`, then Lc0 data via `bullet` (`search_web`); `(768->768)x2` on `1.5B` (`+73.01 ± 9.06`, `owner_study_top_engines.md:146,174`). | `filtering-hl512-baseline` branch exists (`search_web`). | **Confounded** with data/schedule (`owner_study_top_engines.md:259`); branch code not exposed verbatim. |
| **Leorik / Renegade / Stockfish** | Leorik: `622M` pos `(768->256)x2` (`owner_study_top_engines.md:174,223`). Stockfish: `100B+` Lc0 pos / `5k` nodes or depth `9` multi-PV (`owner_study_top_engines.md:174,176`). | Renegade: tapered WDL proportion & smooth LR decay (`owner_study_top_engines.md:178–179,233`). Stockfish: `early-fen-skipping 28` (`engine_building_research_opus_1611.md:30,55` — would drop `15.4%` of Forge `r23`), `lambda 1.0 -> 0.7..0.75` (`lines 22–28,53`). | **General Caveats (`owner_study_top_engines.md:257–263`, `digests/pack_15.md:54`):** small OpenBench variance, AI-assisted repo caveats, and **counter-evidence** (`Caissa three-filter -11` in `pack_15.md:54`, `Wave 19 verified`). |

### 3.2 Dedicated Analysis: `fb2-j2` 2-Ply PV Capture/Promotion Filter vs Forge 1-Ply `is_noisy()`

- **Local Verified Origin (`C:\nnue-lab\survey\fo_read\fable_fb2.md:11,26–27`, `fable_ranked_section.md:26`, `fable_opus_branches.md:111`, `Wave 19 verified`):**
  - `fable-fb2-j2` implemented in-engine self-play (`UCI command datagen`, `no Elo claim, no gate was run` at `fable_fb2.md:6`) with filters: `"in check, a capture within the first 2 PV moves, mate scores, score cap"` (`fable_fb2.md:11`).
  - Fable explicitly ranked this filter `#2` in `fable_fb2.md:26–27` and `#5` in `fable_ranked_section.md:26` / `fable_opus_branches.md:111`: *"drop a position when a capture or promotion is within the first TWO moves of the PV | Ours looks at the best move only (and now keeps noisy ones). One training, scored on the fresh hold-out"*.
- **Exact Architectural Gap in Forge (`Wave 19 verified`):**
  - `C:\nnue-lab\pipeline\forge_parse.py:44–52` (`is_noisy(codes, move)`) checks **only 1 ply (`bm`)**: promotion, capture, or en passant on the side-to-move's best move.
  - A position where `bm` (`pv[0]`) is a quiet move that sets up an immediate forcing capture/promotion on the opponent's reply (`pv[1]`, e.g., a fork, discovered attack, or recapturing sequence starting with a quiet move) passes `is_noisy()` as "quiet", even though static NNUE eval before the tactical resolution can diverge sharply from quiet positional structure.
- **Data Logging Constraint (`C:\nnue-lab\pipeline\nnloop\datagen_uci.py:285,306–307,353–355,425–428`, `Wave 19 verified`):**
  - Neither `play_game` (`datagen_uci.py:285`) nor `play_game_sg` (`425–428`) records `pv[1]`; `.plain` stores only `move {bm}` (`355`), and `parse_slice` (`forge_parse.py:125–132`) drops `move` and `ply` from `.cache.npz`.
  - **Two Distinct Implementation Paths:**
    1. **Native Server-Day (`pv[0]` or `pv[1]` at datagen):** Emit `pv[1]` alongside `bm` from `uci.cpp`/`selfgame` (or check `is_noisy(pv[0]) || is_noisy(after_pv0, pv[1])` directly in `datagen` / `.plain` bitflag) so true search-PV 2-ply tactically unstable positions are marked cleanly.
    2. **Offline `.plain` Consecutive-Ply Proxy (`(bm_t, bm_{t+1})`):** On existing un-reordered `.plain` files (such as `r0178..r0202`), consecutive records `(t, t+1)` from the same game carry the opponent's *actually played* move `bm_{t+1}` — an imperfect proxy for `pv[1]` (it misses `pv[1]` when `t+1` was skipped/adjudicated or when a fresh `go softnodes` search at `t+1` switched moves due to search instability).

---

## 4. Actionable Untested Filtering Gaps (`HYPOTHESIS`)

Every proposal below is strictly labeled **`HYPOTHESIS`** (zero Elo claims). All filter candidates must be isolated from trainer changes and proven via declared `250k` `SPRT [0, 10]` + independent Seed-2 replicate + clean idle `2,000g @ 6+0.06` clock confirmation.

### 4.1 **`HYPOTHESIS` Gap 1 — `fb2-j2` 2-Ply PV Capture/Promotion Filter (`pv[0]` or `pv[1]`) vs 1-Ply `is_noisy()`**
- **Gap & Evidence:** Forge's `R1-skip` proved 1-ply `skip_noisy` at `250k` (`+15.49` Seed 1, `+12.57` Seed 2 `H1`, SPRT upward bias disclosed; `+30.65` fixed `1,000g` vs `r0067` at `250k`, and `+6.43 [-1.47, +14.33]` at `6+0.06` vs `r0067`, INCONCLUSIVE, `PLAN-2811-OPUS-JOB2-CLOCK-INCONCLUSIVE`, **`Opus verified`**), but `is_noisy()` (`forge_parse.py:44–52`) ignores `pv[1]` (`datagen_uci.py:285,355,427` never logs `pv[1]`), and neither `F_FIX_25R_v2` nor `F_FIX_25R_v3` tests 2-ply tactical filtering.
- **Hypothesis (`HYPOTHESIS`):** Filtering positions where *either* `pv[0]` or `pv[1]` is a capture, en passant, or promotion removes "quiet-before-forced-tactic" positions whose static target suffers horizon/exchange distortion beyond `R1-skip`.
- **Verification Path:** (a) Cheap offline/replay ablation on existing `25R` `.plain` using the consecutive-ply `(bm_t, bm_{t+1})` proxy vs 1-ply `R1-skip` (or `F_FIX_25R_v3` winner) at `250k` `SPRT [0, 10]`; (b) exact `pv[0..1]` marking in Server-Day datagen (`2.0B`) if proxy or native branch is ready.

### 4.2 **`HYPOTHESIS` Gap 2 — Bullet-Style `random_fen_skipping` (`1/4`–`1/8` Keep at `2.0B`) + `wld_filtered` + Targeted `0->0` Run Thinning**
- **Gap & Evidence:** Forge writes 100% of searched plies `>= 8` (`101.32` quiet rows/game, `lag1_score_corr_quiet = 0.99697`, `232,370` adjacent quiet `0->0` pairs/round out of `364,905` exact zeros, **`Neon's count`**). `F_FIX_25R_v2` tests hard `F-03` (`400`)/`F-03b` (`300`) without decorrelation or `0->0` thinning; `F_FIX_25R_v3` tests `D-01` `50%` keep (`1/2`) on `pieces >= 6` without `wld_filtered` or `0->0` thinning. By contrast, Bullet's `viribinpack::Filter` provides `random_fen_skipping` / `random_fen_skip_probability` (`ravager_net.rs`, **`Wave 19 verified`**), and `nnue-pytorch` uses `random_fen_skipping` + ply-dependent `wld_filtered` (**`Wave 18 verified`**).
- **Hypothesis (`HYPOTHESIS`):** (a) Pairing `wld_filtered` (calibrated to Forge's `eval_scale=400`) with `thin_zero_runs_mask(max_consecutive_zeros=2)` eliminates redundant `0->0` repetition chains and ply-dependent score/result contradictions more smoothly than fixed `F-03/F-03b` cutoffs; (b) on Server Day `2.0B`, Bullet/`nnue-pytorch`-style dynamic load-time `random_fen_skipping` (redrawn each pass via `rng::get_thread_local_rng()`, `training_data_loader.cpp:1067–1070`, keeping `1/4` to `1/8` per pass on `pieces >= 6` and `100%` on `pieces <= 5`) increases the number of distinct games behind a fixed-size epoch when the underlying data pool is `4–8x` bigger than one epoch (skipping adds no unique positions, and VRAM plays no part; dynamic per-pass skipping is a loader change tested separately from fixed-window filter A/Bs).
- **Verification Path:** Benchmark `wld_filtered` + `0->0` run thinning (`FILTER_V4`) against `F_FIX_25R_v3` on `25R` at `250k` `SPRT [0, 10]` + `6+0.06`; evaluate `1/4`–`1/8` keep on `2.0B` Server Day shards.

### 4.3 **`HYPOTHESIS` Gap 3 — Early-Ply Attenuation (`ply 8..19` / `min_ply=16`) & `32`-Piece Shaping (Protecting `OB0` `2..5` Pieces)**
- **Gap & Evidence:** `r0202` keeps `100%` of `ply 8..19` (`1,168,194` quiet rows = `9.47%` immediately after 8 random plies, **`Neon's count`** / **`Wave 18/19 verified`** sum) and `703,759` `32`-piece rows (`qc.json:79`, **`Opus verified`**) at `1.0x`, while `min_pieces=4` (`F-06`) drops `115,569` 3-piece rows/round (`qc.json:12`, **`Opus verified`**). Meanwhile `ravager_net.rs` uses `viribinpack::Filter { min_ply: 16, ... }` (**`Wave 19 verified`**), and `nnue-pytorch` uses `soft_early_fen_skipping=20` plus a piece-count Hermite spline (`pc=32 -> 0.75x` while preserving `2..5` pieces, **`Wave 18 verified`**).
- **Hypothesis (`HYPOTHESIS`):** Softly attenuating `ply 8..19` (or testing `min_ply=16`, subject to `OPUS_TO_NEON`/Opus `r23` warning that `early-fen-skipping 28` drops `15.4%` of data at `25R` scale) and downweighting `32`-piece opening clusters (`~0.75x`) while keeping `2..5`-piece `OB0` rows at `100%` reduces opening-move memorization without starving `OB0`. Note `filterqc.py` / `.plain` holds `ply`, whereas `.cache.npz` (`forge_parse.py:125–132`) drops `ply`, so ply attenuation must run at `.plain`/pre-pack stage.
- **Verification Path:** Pre-pack `filter_v4` ablation on `25R` or `2.0B` (isolating ply/piece shaping from `F-06` recovery) via `250k` `SPRT [0, 10]` + `6+0.06`.

### 4.4 **`HYPOTHESIS` Gap 4 — `F-08` (`|score| > 1200`) `0.25x` Soft Tail Weighting vs Hard Drop**
- **Gap & Evidence:** `F_FIX_25R_v2` hard-dropped `17,872,184` rows with `|score| > 1200` (`f_fix_summary.json:15`, **`Neon's count`**; `6.843%` of `r0202` quiet rows). On `master_gates_quick.json:165` (`OPUS-2811-S5-UNITS-AND-V3-SUBSAMPLE`, **`Opus verified`**): `R1-skip` Seed 1 `KNN-K = +60 cp (raw +97)`, Seed 2 `KNN-K = +68 cp (raw +114)`, `F_FIX_25R_v2` `KNN-K = +44 cp (raw +74)` — a `16–24 cp` shift toward `0` (against an `8 cp` spread from two seeds), while `S7 KQ-K` (`+1129 cp`) stays inside the two-seed spread (`+751` to `+1284 cp`). Thus "the tail drop changed the endgame scale" is only a weakly supported **`HYPOTHESIS`**. Neither `nnue-pytorch` (which clamps `win_rate_model` inputs rather than dropping `|score| > 1200`, **`Wave 18 verified`**) nor `viribinpack::Filter` (`max_eval = 10000` in `ravager_net.rs`, **`Wave 19 verified`**) hard-drops at `1200 cp`.
- **Hypothesis (`HYPOTHESIS`):** Applying `0.25x` soft sample weighting (`32/128` vs `128/128` normal) on `1200 < |score| <= 2000` preserves won-ending magnitude calibration while keeping saturated-gradient dominance `4x` lower than `1.0x`.
- **Verification Path:** Direct 2-arm `25R` test comparing hard drop `|score| > 1200` vs `0.25x` soft tail weighting (`soft_tail_weights_u8`) on identical `v3`-filtered data at `250k` `SPRT [0, 10]` + `6+0.06`.

### 4.5 **`HYPOTHESIS` Gap 5 — Isolated Trainer & Datagen Follow-Ups: Tapered WDL Scheduling (`1.0 -> 0.75`) & Deeper-Search Rescoring**
- **Gap & Evidence:** Forge uses constant `mix=0.75` (`config.forge.toml:357`, **`Wave 19 verified`**), whereas `nnue-pytorch` (`LambdaController` `1.0 -> 0.75`, **`Wave 18 verified`**), Stockfish (`lambda 1.0 -> 0.7..0.75`, `engine_building_research_opus_1611.md:22–28,53`), and Renegade (`owner_study_top_engines.md:178`) taper WDL proportion over training, and Bullet's `simple.rs` explicitly notes `"potentially a lot of elo available by adjusting the wdl and lr schedulers"` (`engine_building_research_opus_1611.md:33–34`). Separately, Viridithas improved target quality by rescoring existing positions with a deeper/stronger search (`owner_study_top_engines.md:177,251`, `speed_candidates.md:76`), whereas Forge `r0178..r0202` uses `2,000`-node self-play labels generated by evolving round nets.
- **Hypothesis (`HYPOTHESIS`):** Annealing `mix` (`1.0 -> 0.75`) across training and rescoring older rounds (or high-value `2.0B` shards) with the current best net at `~8k–16k` nodes may improve target consistency and late-epoch result grounding. **Strict Isolation Rule:** Neither tapered WDL scheduling nor deeper-search rescoring may be bundled inside a data-filtering A/B test; each requires its own frozen-dataset `250k` `SPRT [0, 10]` + `6+0.06` match.

---

## 5. Verification & Citation Integrity Checklist (`Wave 19 verified`)

- **Local Files & Git SHA Directly Verified:**
  - `C:\nnue-lab\src\nnue-pytorch` Git HEAD: `17cfb7f06c36733f4b26af121595e636676f9b96`
  - `C:\nnue-lab\neon\forge_fixes\teamwork_wave18\FILTER_V4_SERVERDAY_HYPOTHESES_2811.md` (`lines 1–89`)
  - `C:\nnue-lab\pipeline\forge_parse.py` (`lines 44–52, 100–132`)
  - `C:\nnue-lab\pipeline\nnloop\datagen_uci.py` (`lines 285, 306–307, 353–355, 425–428`)
  - `C:\nnue-lab\pipeline\nnloop\filterqc.py` (`lines 56–62, 103–122`)
  - `C:\nnue-lab\pipeline\config.forge.toml` (`lines 274–280, 313–318, 330–336, 357`)
  - `C:\nnue-lab\runs\forge\r0202\data\qc.json` (`lines 1–96`)
  - `C:\nnue-lab\neon\to_astra\FILTER_DEEP_AUDIT_R0202_2811.json` (`lines 1–180`)
  - `C:\nnue-lab\neon\to_astra\FILTER_DROPPED_AUDIT_R0202_2811.json` (`lines 495–570`)
  - `C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\f_fix_summary.json` (`lines 1–20`) & `master_gates_quick.json` (`lines 140–180`)
  - `C:\nnue-lab\neon\to_astra\R2_DECLARATION.json` (`lines 1–136`), `F_FIX_25R_V3_DECLARATION.json` (`lines 1–108`), `MONDAY_BARS_EVIDENCE_SUMMARY_2811.md` (`lines 1–180`)
  - `C:\nnue-lab\neon\OPUS_TO_NEON.md` (`lines 3125–3160, 3320–3475, 3615–3655`) & `C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.md` (`lines 1–84`)
  - `C:\nnue-lab\survey\owner_study_top_engines.md` (`lines 1–60, 140–263`), `engine_building_research_opus_1611.md` (`lines 1–63`), `speed_candidates.md` (`lines 60–77`), `fo_read\fable_fb2.md` (`lines 1–30`), `fo_read\fable_ranked_section.md` (`lines 1–39`), `fable_opus_branches.md` (`lines 65–169`), `fo_read\opus_r13_r15_30h_deepres.md` (`lines 1–30`), `digests\pack_03.md` (`lines 30–50`), `digests\pack_15.md` (`lines 40–80`), `digests\pack_32.md` (`lines 60–75`)
- **Web Verified Sources (`search_web`):** `github.com/jw1912/bullet` (`examples/progression/1_simple.rs`, `Cargo.toml` / `bullet-utils`), HuggingFace `wraith1337/ravager-net-ckpt` (`ravager_net.rs`), `github.com/cosmobobak/viriformat` (`crates.io`/`docs.rs`), `github.com/cosmobobak/viridithas`, `github.com/Ciekce/Stormphrax`, `github.com/Yoshie2000/PlentyChess`, `github.com/lynx-chess/Lynx` (`lynx-selfgen.md`), `github.com/tcheran-chess/tcheran`, `github.com/jw1912/akimbo`.
