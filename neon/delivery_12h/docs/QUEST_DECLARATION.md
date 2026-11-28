# POSITION FILTERING QUEST — DECLARATION & RESEARCH PLAN (Neon, 27 Nov 2026)

- **Owner Mandate (27 Nov 2026, 11:18 & 11:35 PC):** 12h–20h deep investigation of Forge's position filter (`pipeline/nnloop/filterqc.py` + `forge_train_v3.py` data path), finding every way our current filtering lacks, and designing/testing concrete, verified fixes inside `C:\nnue-lab\neon\filter_quest\` (never editing live `pipeline/` or `runs/` files).
- **Start Timing:** Strictly **AFTER** all SF19/M4 c100 discovery, one-shot held-out, Track B2 single-look verdict, and consolidated `NEON_FINAL_100CHUNKS_FINDINGS.md` are complete and delivered to Opus.
- **Safety Boundaries:**
  - All loop data (`runs/forge/r0178..r0202`, `runs/forge/val/val.plain`, `tmp/opus_scratch/sf19_m4/out/*.tsv`) is **100% READ-ONLY**.
  - All scripts, test fixtures, prototype filters, and results live strictly inside `C:\nnue-lab\neon\filter_quest\`.
  - Keep `>= 30 GiB` free on `C:` (target total `filter_quest/` footprint `< 4 GiB`; stream `.plain` files without duplicating multi-GB datasets!).
  - Hard GPU-clear by **`18:30 PC`** (loop restarts `~18:41 PC`). After `18:41 PC`, every CPU job runs strictly behind `tmp/loop_gate.py build` + `mem_room.py` + `CPU < 90 C` (single-process / `<= 2` threads so the loop's self-play and matches are never starved!).
  - **R5 Discipline:** Every data-quality, hold-out-loss, and SF19-calibration finding is strictly a **lead / candidate** — never an Elo claim. Playing strength is proved only by a declared match later under the loop's rules.
  - **Measurement Traps (`measurement-traps-2711.md`) Applied Throughout:** Always separate global baseline shifts from feature excess residuals; never use single-ply steps across STM switches; separate scale compression from offset bias.

---

## Baseline (Verified by Opus Hunt 148, `r0202`, `16,005,733` records)
- Live `[filter]` rules: `max_abs_score = 2000` (DEAD: `0` marked), `min_ply = 0, max_ply = 400` (DEAD: `0` marked), `dedup = true` (per-round only, keeps first game's result: `3.29%`), `conflict_score = 600` (decisive games only: `0.003%`), `max_halfmove_clock = 80` (`1.29%`), `min_pieces = 4` (`0.72%`).
- Trainer (`--keep-noisy`): skips marked `32002` (`5.30%`) + in-check (`8.00%`, uncounted in `qc.json`) -> **`86.70%` train** (`13,876,529` in `r0202`; `346,931,328` across 25-round window `r0178..r0202`, cap `388,000,000` filter-kept).
- Captures/promotions are **KEPT** (`--keep-noisy`, which beat quiet-only by `+15.4 ± 5.9 Elo` at 50k on 14 Nov).

---

## Pre-Declared Investigation Questions (Q1–Q8)

### Q1. Cross-Round Duplication & Target Noise Across the 25-Round Window (`r0178..r0202`)
- **What we measure (read-only streaming pass over `r0191..r0202` and full `r0178..r0202`):**
  1. Exact duplicate rate across `2`, `5`, `12`, and `25` rounds using deterministic 64-bit `blake2b` of FEN fields `1..4` (replacing process-randomized Python `hash()`).
  2. Breakdown of cross-round duplicates by **ply band** (`ply 8..12`, `13..20`, `21..40`, `41+`), **piece count / output bucket `ob0..ob7`**, and **exact repetition multiplicity** (how many times the hottest positions appear in one 25-round window!).
  3. **Target variance across duplicates:** When the same FEN appears in `>= 2` games (within a round OR across rounds), what is the variance of `score` and `result`? How often does keeping the first occurrence's raw `result` (`-1/0/+1`) give an opposing outcome vs the mean outcome?
  4. **Window capacity unlocked:** How many extra rounds of fresh, distinct positions fit inside the `388M` VRAM cap if cross-round duplicates are deduplicated (or merged via score/result averaging)?

### Q2. Drawn-Game Score-Result Conflicts (`result == 0`, `|score| >= T`)
- **What we measure (on `r0198..r0202`):**
  1. Exact count and share of drawn-game kept positions with `|score| >= 300`, `>= 600`, `>= 800`, `>= 1000`, `>= 1500` cp (currently **0%** filtered because line 109 checks `result != 0`!).
  2. Breakdown by piece count (`<= 5`, `6..12`, `13..19`, `20+`), halfmove clock (`r50`), ply, and terminal cause (missed conversion / 3-fold / 50-move / max-ply draw).
  3. Score-vs-result label distortion: how much `0.75 * sigmoid(score) + 0.25 * 0.5` pulls winning positions toward `0.5` (potential contributor to scale compression / endgame bias!).

### Q3. Ply-to-Ply Label Instability / Horizon Spikes (`|score(t) + score(t+1)| >= T`)
- **What we measure (using intact move chains inside `filtered.plain` on `r0198..r0202`):**
  1. Distribution of 1-ply search swing `|score(t) + score(t+1)|` (quiet moves vs captures/promotions vs checks, by `|score(t)|` band and phase).
  2. Compare against **SF19 ground truth** on a stratified sample (and against M4 games!): do high-swing positions (`>= 150`, `>= 250`, `>= 400` cp) have dramatically worse score-vs-result and score-vs-SF19 error?
  3. **Key hypothesis:** Keeping *clean* tactical/capture positions (`--keep-noisy`) helps, while keeping *mis-evaluated horizon-spike* positions (where the 2,000-node search reversed itself by `>= 250 cp` on the very next ply!) injects pure gradient noise.

### Q4. High-Score Saturation & Mop-Up Waste (`|score| >= 800..2000 cp`)
- **What we measure (`r0178..r0202` vs M4 10,000-game real distribution):**
  1. Exact share of trained positions in `|score| < 100`, `100..250`, `250..500`, `500..800`, `800..1200`, `1200..2000`.
  2. Compare against M4 games (where critical blunders happen in `|s0| <= 3.0`, and Move `01–20` in `|s0| <= 1.5`!).
  3. Measure sigmoid gradient magnitude `p*(1-p)` wasted on `|score| >= 1000` mop-up positions, and quantify how much effective VRAM window capacity is freed by probabilistic downsampling of `|score| >= 1000` (e.g., keeping `25%` or `50%` so extreme tails stay anchored without burning 14% of VRAM).

### Q5. Phase, Output-Bucket (`ob0..ob7`), Opening (`ply 8..20`), & Structural Coverage vs M4 Real Games
- **What we measure (comparing `r0198..r0202` training distribution directly against the 100-chunk M4 10,000-game distribution!):**
  1. Output bucket shares (`ob0..ob7`) and king-bucket occupancy (`kb0..kb7` × `ob0..ob7`).
  2. Structural imbalance frequencies directly tied to our SF19/M4 findings (H4 bishop pair, H5 broken king shield `>= 2` missing pawns, early-game `ply 8..16` with `28+` pieces): are Forge's `8`-random-ply self-play games starved of castled king-shield structures, bishop pairs, or realistic opening imbalances compared to real UHO/M4 games?!
  3. Quantify exact **training-to-match distribution shift** (KL / ratio per cell of `(ob, |score|, structure)`).

### Q6. Captures & Promotions Under `--keep-noisy` (Disaggregating Good Noisy vs Bad Noisy)
- **What we measure (on `r0200..r0202`):**
  1. Share of trained positions where played `move` is a capture, en passant, promotion, or gives check (currently `0` skipped under `--keep-noisy`, `0` reported in `qc.json`!).
  2. Separate **quiescent / forcing recaptures** from **hanging-piece / high-swing captures** (`|score(t) + score(t+1)| >= 200` or winning-capture into big reversal), measuring score-result correlation and label noise for each sub-class.

### Q7. Code & Telemetry Bugs in Current `filterqc.py` + Trainer Cache Key (Target 149)
- **Concrete bugs/gaps already identified to fix cleanly in prototype + patch form:**
  1. Stale docstring in `filterqc.py` (claims loader drops captures & in-check; actually `--keep-noisy` keeps captures and `forge_parse` drops in-check).
  2. `qc.json` omits `in_check` count and `noisy_move` count (prints `94.70%` kept when only `86.70%` train!).
  3. Dead rules (`score_limit = 2000`, `max_ply = 400`) & `games` counter edge case (`ply < last_ply` misses consecutive 1-ply games).
  4. Process-randomized `hash()` in `filterqc.py` line 118 prevents deterministic cross-round dedup or reproducible testing.
  5. **Target 149 (`forge_train.py` cache key):** cache key `(size, int mtime, flags, v1)` omits `hce_dump.exe` hash/mtime -> stale teacher evals if `hce_dump.exe` is ever rebuilt!

### Q8. Prototype `filterqc_v2.py` + Rigorous Verification Suite (Strictly Inside `neon/filter_quest/`)
- Build a clean, drop-in, streaming, backward-compatible prototype `neon/filter_quest/filterqc_v2.py` implementing the winning data-backed improvements (modular config flags, every new rule independently toggleable and defaulted OFF until match-proved!), PLUS:
  1. Full unit test suite (`test_filterqc_v2.py`) with known answers, planted faults, determinism checks, parity with `filterqc.py` when new rules are OFF, and throughput benchmark (`pos/s`, RAM peak).
  2. Clean unified diff patches (`patches/filterqc_v2.patch`, `patches/cache_key_t149.patch`) ready for Opus/Fable review (`lab-place-a-change`).
  3. Controlled **Offline Score-Quality & SF19-Alignment Evaluation** (and, ONLY if pre-declared and safely scheduled without touching the loop after `18:41`, a controlled 12-round GPU training diagnostic comparing baseline `filtered.plain` vs `filterqc_v2` filtered `r0191..r0202`, strictly labeled **diagnostic / R5 — games decide**!).
