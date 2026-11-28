# Filter Quest — Phase C Pre-Declared Experimental Protocol

- **Declared At (PC):** 2026-11-27 14:20 PC (BEFORE launching any Phase C training or match!)
- **Author:** Gemini 4 Neon (Filter Quest, `C:\nnue-lab\neon\filter_quest\`)
- **Strict Rules:**
  - Read-only on `runs/`, `pipeline/`, `forge/`, `tmp/`. All artifacts written strictly inside `C:\nnue-lab\neon\filter_quest\`.
  - **Strict R5:** Lower training loss, lower `val.plain` loss, lower `final_eval_r0203` loss, or lower SF19 MSE are **diagnostic signals ONLY** — **NEVER Elo**. ONLY declared `fastchess` games decide playing strength!
  - **Provisional Claim Isolation:** Reported `+11 Elo` improvement is provisional (pending Fable validation) and is NOT mixed into any baseline here.
  - **Heat / Memory / Disk Safety:** `mem_room` before every run, `--gpu-hot-pause-c 98 --gpu-hot-resume-c 84`, `CPU < 92 C`, `C: >= 30 GiB` free at all times, NEVER run clock matches while GPU trains, NEVER use FF/FFB trainers.

---

## 1. Shared Experimental Controls & Architecture
- **Architecture:** `ForgeNetV3` (`hidden=768`, `king_buckets=8` mirrored, `out_buckets=8`, `QA=255`, `QB=64`, standalone, `FORGENN3` `.fnn3`, `9,463,528` bytes).
- **Training Recipe (matched to `r12_noteach` / `r12_control` baseline on 12 rounds):**
  - `epochs=40`, `batch_size=8192`, `lr=5e-4`, `min_lr_frac=0.05`, `warmup_steps=500`, `lr_cycles=auto` (`6,12,24,40`), `w1_decay=0.3`, `mix=0.75`, `seed=1` (and `seed=2` for top winning arm replication!).
  - **Note on Teacher Isolation:** To cleanly isolate data-filtering / sample-weighting effects without the stale Day-1 residual teacher `b_full.pt` masking signal (and matching our clean no-teacher `.fqs` GPU pipeline), **ALL new Phase C arms use NO residual teacher (`t_weight = 0.0`)** and are compared directly against **`Control-NT` (`r12_noteach`, already trained on `r0191..r0202`, `seed=1` & `seed=2`, 6/6 gates PASS)** AND against **`Control-Live` (`r12_control`, live teacher `b_full.pt`, `seed=1` & `seed=2`)**!
  - Wait: we ALSO verify parity on `Control-NT-FQS` (or exact `r12_noteach` vs `r12_control` match) so there is zero ambiguity between `forge_train_v3.py` and `quest_train_v3_weighted.py`!
- **Base Training Window (`Equal Raw Budget` = 12 rounds):**
  - `r0191..r0202` (`192,068,xxx` raw -> `181,87x,xxx` filter-kept -> `166,4xx,xxx` non-check trained positions).
  - **Equal Retained-Position Budget (`~166.5M` trained positions):** Whenever a filter drops additional positions (e.g., cross-round dedup or high-score downsampling), we ALSO test pulling in immediately preceding rounds (`r0189..r0190`) and capping `--max-rows` to match `Control-NT`'s exact retained position count!
- **Untouched Whole-Game Final Evaluation Set (NEVER trained on, NEVER tuned on):**
  - `eval_sets/final_eval_r0203_w14_w15.plain` (`204,180` raw records, `1,555` complete independent games from untouched `r0203` workers `w14+w15`, SHA256 `b8ff64590bd51158...`).
  - Secondary legacy monitor (disclosed as Day-1 `AL1 s198` unfiltered & leaky): `runs/forge/val/val.plain`.
  - External independent benchmark (100% separate games): SF19 M4 10,000-game blind held-out split (`610` opening pairs, `1,220` games).

---

## 2. Pre-Declared Experiments & Hypotheses

### Track M0 — Immediate Playing-Strength Calibration of Existing Trained Baselines (CPU, once `R10X_PROCS == 0`)
Before comparing new filter variants, measure exact `fastchess` playing strength of our existing `r12_*` controls so we know the exact Elo landscape:
- **M0a:** `r12_noteach` vs `r12_control` (`50,000` nodes, `1,000` games, UHO, concurrency 12). *Question:* Does dropping the stale Day-1 residual teacher `b_full.pt` hurt, match, or help real playing strength?
- **M0b:** `r12_ablate_mix65` vs `r12_control` (`50,000` nodes, `1,000` games, UHO). *Question:* Does the `--mix 0.65` SF19 calibration gain (`-0.00080 MSE, z=-9.59`) translate into real Elo despite `+2.0%` worse legacy `VAL_MIX60`?
- **M0c:** `r12_bundle_r9` vs `r12_control` (`50,000` nodes, `1,000` games, UHO). *Question:* Does the replicated R9 bundle translate to real Elo?

### Track W — Sample Weighting vs Hard Discarding (Zero Extra Disk, Exact `r0191..r0202` Cache!)
Tests the prompt's core research question: *Is soft sample weighting better than permanently discarding positions?*
- **EXP-W1 (`fq_w_soft800`):** Same `r0191..r0202` (`166.5M` pos), no hard drops, **score-saturation downweighting** (`|score| >= 1200 -> 0.25x`, `800..1199 -> 0.50x`, `<800 -> 1.0x`, mean-normalized to `1.0`).
  - *Hypothesis:* Redirecting optimizer variance away from already-decided mop-up positions (`14.0%` of data, `mean_grad = 0.00007..0.00172`) toward contested `<800 cp` positions improves `final_eval_r0203` loss and equal-node/equal-time Elo vs `Control-NT`.
- **EXP-W2 (`fq_w_ob_m4`):** Same `r0191..r0202`, **output-bucket reweighting toward M4 real-game phase distribution** (`ob0: 1.65x`, `ob7: 0.65x`, mean-normalized).
  - *Hypothesis:* Correcting the `0.562x` TB/endgame under-representation and `1.663x` random-opening over-representation improves endgame & overall playing strength vs `Control-NT`.
- **EXP-W3 (`fq_w_pow25`):** Same `r0191..r0202`, **Stockfish-style `|pred - target|^2.5` loss exponent** (implicitly upweighting larger evaluation mistakes — informative-position selection without discarding any data!).
  - *Hypothesis:* `p = 2.5` focuses capacity on high-error / difficult positions (like broken king shield and bishop-pair blind spots) and improves playing strength vs `p = 2.0`.
- **EXP-W4 (`fq_w_close_m4_pow25`):** Justified combination of the best weighting levers (`score_weight=soft800`, `ob_reweight=m4`, `loss_pow=2.5`) — ONLY run/kept if justified by W1–W3!

### Track F — Hard Data Filtering & Deduplication (Compact `.fqs.z` Shards, Both Equal-Raw & Equal-Retained!)
- **EXP-F0 (`fq_min_integrity_r203` — Minimally Filtered Control on Untouched Raw `r0203` vs Baseline Filter):**
  - Because `r0191..r0202` `filtered.plain` already had `filterqc.py` applied, we compare **Minimally Filtered (Tier-1 integrity + `in_check` only, NO dedup/rule50/few_pieces/conflict)** vs **Baseline `filterqc.py`** on `r0203/data/raw` (`w00..w13`, `15.81M` raw records -> `~14.4M` vs `~13.7M` trained, 40 epochs, ~3.5 min GPU each!) — directly measuring what the current production filter contributes vs no quality filter!
- **EXP-F1 (`fq_hard_hs800_eqraw` & `fq_hard_hs800_eqret`):**
  - Hard deterministic downsampling of `|score| >= 800` (keep `25%` of `800..1199` and `10%` of `>=1200`), plus **ply-to-ply swing drop (`|score| < 500 & swing >= 200`)** + **draw conflict drop (`res == 0 & |score| >= 600`)**.
  - Tested BOTH at **Equal Raw Budget (`r0191..r0202`, `~148M` retained, ~11% faster training)** AND at **Equal Retained-Position Budget (`r0189..r0202` capped to exact `Control-NT` row count `166.5M`)** so we directly compare Hard Drop (`F1`) vs Soft Weighting (`W1`) apples-to-apples!
- **EXP-F2 (`fq_xround_dedup` — Cross-Round Deterministic Deduplication):**
  - Exact deterministic 64-bit `blake2b` cross-round dedup across the window (using Audit 2's measured duplication curve!) — tested at Equal Retained-Position Budget (`166.5M` unique positions) vs `Control-NT`!

---

## 3. Acceptance Criteria & Playing-Strength Verification Protocol

### Addendum C.1 (Declared 2026-11-27 15:12 PC, triggered by M0a/M0b/M0c Elo Results)
Following the confirmed Track M0 Elo findings (`r12_noteach -26.46 +/- 13.52`, `r12_mix65 -21.22 +/- 13.61`, `r12_bundle_r9 -40.84 +/- 14.13` vs `r12_control`), we pre-declare three targeted follow-up arms BEFORE running them:
- **EXP-M85 (`fq_mix85_bfull`):** Exact `r12_control` recipe (`r0191..r0202`, `b_full.pt` teacher `0.20`, `seed=1`) with **`--mix 0.85`** (testing the opposite direction of `--mix 0.65`, closer to Stockfish's `0.85–0.90` search-score share!).
  - *Hypothesis:* Since reducing search-score share `0.75 -> 0.65` lost `-21.2 Elo`, raising it `0.75 -> 0.85` reduces WDL outcome noise and improves Elo vs `r12_control`.
- **EXP-SD (`fq_selfdistill_r0067`):** Exact `r12_control` recipe (`r0191..r0202`, `--mix 0.75`, `seed=1`) replacing Day-1 residual teacher `b_full.pt` with **standalone v3 self-distillation teacher `r0067/train/cand.pt` (`t_weight=0.20`)** — requiring **ZERO `hce_dump.exe`** and working natively on `.fqs.z` shards!
  - *Hypothesis:* Distilling from the much stronger `r0067` v3 net provides stronger regularization than Day-1 `b_full.pt` while eliminating the `hce_dump.exe` dependency on Server Day.
- **EXP-W3T (`fq_w_pow25_bfull`):** Exact `r12_control` recipe (`b_full.pt` teacher `0.20`, `r0191..r0202`, `seed=1`) with **Stockfish-style `loss_pow = 2.5`** (online informative-position upweighting without discarding any data!), compared directly against `r12_control`.

## 3. Acceptance Criteria & Playing-Strength Verification Protocol (Continued)
1. **Mandatory Correctness Gates (6/6 PASS required before ANY match):**
   - Exact `.fnn3` byte size (`9,463,528`), valid header/checksum, zero NaN/Inf weights, `net_eval_check` trainer-vs-engine parity `<= 1 cp` on 2,000+ positions, `forge.exe` bench/search smoke pass, zero crashes/illegal moves.
2. **Screening Match (`fastchess`, official `config.forge.toml` + `v3_uci_options` + `UHO_Lichess_4852_v1.epd`):**
   - `1,000` fixed paired games (`500` opening pairs, `-repeat`) at `50,000` nodes/move, `concurrency=12`, `MatchHeatGuard < 92 C`.
   - 95% pentanomial CI half-width `~±11–13 Elo`.
3. **Equal-Time Confirmation Match (for ANY promising winner with screening `Elo >= +5` or clear lead, AND for top Track W vs Track F comparison):**
   - **`2,000` fixed paired games** (or SPRT `[0, 10]`) at **equal-time `6+0.06`, `timemargin=1000`, GPU 100% IDLE!**
   - Reports exact W-L-D, pentanomial `[LL, LD, DD+WL, WD, WW]`, Elo + 95% CI, LOS, time forfeits, illegal moves.
4. **Honesty Rule:** Every negative, flat, or inconclusive arm is preserved in full in `PHASE_C_RESULTS.md` and the Phase F handoff.
