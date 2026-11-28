# NNUE `G3 -> G4` Training Design Note (`FORGENN3-P` + CC0 `.fqs.z`)

- **Target Pipeline:** `C:\nnue-lab\neon\forge_fixes\train_v3p.py` (live `19:13:07`), `forge_v3p.py`, `teamwork_wave2\streamB_nnue\gen_cc0_selfgame_fqs_v2.py` (`train_v3p_g3_flags.patch` for pre-`19:13:07` snapshot)
- **Scope:** Primary-source synthesis (Stockfish `nnue-pytorch` / `Stockfish` / `Stockfish-tools`, Bullet / Viridithas / Stormphrax, Lc0 conversion) reconciled with Forge empirical measurements (`Filter Quest`, `Task 1`, `Stream 3 CC0 Pilot`, `FABLE_TO_OPUS.md`) into an actionable `G3 -> G4` experiment sequence.
- **Verification Basis:** Every formula, gradient, distribution ratio, and CPU core-hour figure below was independently verified on CPU-only Python (`C:\nnue-lab\venv\Scripts\python.exe -B`) against the raw JSON/source files on disk.

---

## Pillar 1: WDL Loss Power (`2.0` vs `2.5 / 2.6`)

### Primary Sources & Local Implementation
- **Stockfish `nnue-pytorch` (`C:\nnue-lab\src\nnue-pytorch`):**
  - `model\nnue.py:50-83` (`calculate_sf_loss`) blends search WDL `pf` and game outcome `t` via `pt = pf * actual_lambda + t * (1 - actual_lambda)`, then minimizes `|pt - qf|^pow_exp`.
  - Git history: `b50c70d` (2021-06-15) introduced `pow_exp = 2.6` with pre-loss lambda blending; **`52fc070`** (2022-07-13, Joost VandeVondele) refined **`2.6 -> 2.5`** (*"refine loss function power: lead to a slightly stronger net"*, Fishtest `62ce5f421dacb46e4d5fd277`). `model\config.py:107` defaults `LossParams.pow_exp = 2.5`; locally, `C:\nnue-lab\src\nnue-pytorch\tests\test_compiled_loss.py:35` tests `params.pow_exp = 2.4340402395048404` alongside `LambdaController` (`model\lambda_utils.py:9-105`, cosine cycle + batch/sample jitter; note `docs\training.md:16` links externally to `github.com/vondele/nettest` rather than storing `threats.yaml` locally).
- **Bullet / Viridithas / Stormphrax:** Bullet defaults to `output.sigmoid().squared_error(target)` (`p = 2.0`) and exposes custom `.abs().powf(p)` (`2.5` / `2.6`, e.g., Viridithas `2.5` tuning).
- **Local Forge Trainers:**
  - `C:\nnue-lab\neon\filter_quest\quest_train_v3_weighted.py:267-275`: implements `(diff.abs() + 1e-12).pow(loss_pow)` (`EXP-W3` / `EXP-W3T` declared in `EXPERIMENTS_DECLARED.md:43-45` for `loss_pow=2.5`, **not yet trained or matched in `fastchess`**).
  - `C:\nnue-lab\neon\forge_fixes\train_v3p.py:332, 575-578` (`19:13:07` live file; `L331, 567-570` prior): **`--loss-pow` is ALREADY wired into `train_v3p.py`** (`default=2.0`):
    ```python
    if abs(args.loss_pow - 2.0) < 1e-6:
        loss = (pred - target).pow(2).mean()
    else:
        loss = (pred - target).abs().clamp(min=1e-7).pow(args.loss_pow).mean()
    ```
    Note `.clamp(min=1e-7)` prevents `0^(p-1)` NaN/Inf gradients at `pred == target` (zeroing gradients inside `|err| < 1e-7`).

### Quantified Gradient Math (`L_p(e) = |e|^p`, `|dL_p/de| = p * |e|^(p-1)`)
Comparing small label-jitter residuals (`|e| = 0.02`, already well-fitted/noisy outcome) against contested/tactical errors (`|e| = 0.30`):

| Exponent `p` | `|grad|` at `|e|=0.02` | `|grad|` at `|e|=0.30` | `g(0.30) / g(0.02)` | Focus Amp vs `p=2.0` | Jitter Damping vs `p=2.0` |
|---:|---:|---:|---:|---:|---:|
| **`2.0` (MSE)** | `0.040000` | `0.600000` | `15.00x` | `1.00x` | `1.000x` |
| **`2.5` (SF default)** | `0.007071` | `0.410792` | `58.09x` | **`3.87x`** | **`0.177x`** (`5.66x` smaller) |
| **`2.6` (SF legacy)** | `0.004973` | `0.378763` | `76.16x` | **`5.08x`** | **`0.124x`** (`8.04x` smaller) |

- **Critical Coupling (`~2.5-3x` Data-Gradient Shrink):** Across typical WDL residuals (`|e| in [0.05, 0.12]`), switching `2.0 -> 2.5` shrinks data gradients by `(2.0*|e|) / (2.5*|e|^1.5) = 0.8 / sqrt(|e|) = 2.31x–3.58x` (`~2.5-3x`). Any fixed-scale regularizer (`--ob-smooth`) becomes `~2.5-3x` stronger relative to the WDL term unless scaled down proportionally.

### Recommendation (Pillar 1)
1. **Keep `G3a` (keep noisy) vs `G3b` (skip noisy) strictly clean at `--loss-pow 2.0 --ob-smooth 2e-6 --mix 0.85`**, so the noisy-flag ablation has zero confounding changes. *(Note: `G2_v3p_1024_pairwise_psqt` status is **pending `G2` completion** — `metrics.json` and `cand.fnn3` are not yet written; `NEON_TO_OPUS.md:354` recorded `--ob-smooth 2e-6` while `AUDIT_V3P_SECOND_READING.md:123` had logged `--ob-smooth 1e-4`.)*
2. **Test `--loss-pow 2.5` as the first isolated `G4` arm (`G4a`)** on the winning `G3` dataset/flag setting, gated by `fastchess` against the `G3` winner (since `EXP-W3` has zero match data yet). Prefer `2.5` over `2.6` per Stockfish `52fc070`. Pin `G4a` strictly to **`--ob-smooth 2e-6`** (`--loss-pow 2.5 --ob-smooth 2e-6`, strictly a single-variable change from `G3`!), and only test `--ob-smooth 1e-6` in a subsequent arm if `OB0` washes out (never `1e-4`; see Pillar 2).

---

## Pillar 2: Phase / Output-Bucket (`OB0..OB7`) Reweighting (`ob_reweight m4`) + `ob_smooth`

### Measured Bucket Shift (`ob = clamp((pieces - 2) // 4, 0, 7)`) & `fq_w_ob_m4`
Sources: `audit_r0202.json:143-152`, `m4_vs_train_shift.json:7-16, 44-53`, `pilot_analysis.json:140-149`, `baseline_r0067_scorecard.json`, `scorecard_fq_w_ob_m4.json`.

| Bucket (Pieces) | `r0202` Self-Play | `M4` Real Games | `r0202 / M4` | `CC0 pilot_k0` | `M4 / CC0_k0` (Recomputed) | `ob_reweight m4` (`quest_train_v3_weighted.py:231`) |
|---|---:|---:|---:|---:|---:|---:|
| **`OB0` (`2-5`)** | **`5.38%`** | **`9.57%`** | **`0.562x`** | `6.65%` | **`1.439x`** | `1.65` |
| **`OB1` (`6-9`)** | `18.36%` | `18.52%` | `0.992x` | `20.36%` | **`0.909x`** | `1.01` |
| **`OB2` (`10-13`)** | `15.82%` | `16.94%` | `0.934x` | `15.97%` | **`1.060x`** | `1.07` |
| **`OB3` (`14-17`)** | `13.23%` | `13.28%` | `0.996x` | `12.69%` | **`1.046x`** | `1.00` |
| **`OB4` (`18-21`)** | `11.71%` | `11.65%` | `1.004x` | `11.33%` | **`1.028x`** | `1.00` |
| **`OB5` (`22-25`)** | `11.31%` | `11.21%` | `1.009x` | `10.95%` | **`1.024x`** | `0.99` |
| **`OB6` (`26-29`)** | `12.36%` | `11.72%` | `1.054x` | `12.20%` | **`0.961x`** | `0.95` |
| **`OB7` (`30-32`)** | **`11.83%`** | **`7.12%`** | **`1.663x`** | `9.85%` | **`0.723x`** | `0.65` |

- **Why `OB0` breaks in `r0067`/`r0202`:** `filterqc.py` `min_pieces=4` drops all `2-3` piece endgames (`KQ-K`, `KR-K`, `KNN-K`), `r0202` under-samples `OB0` (`0.562x`) and holds `3,058` `OB0` draw conflicts (`res=0, |score|>=600`), producing a **`143.5 cp`** median jump across `OB0<->OB1` (`r0067`) and `S5_dead_draws` (`KNN-K = +101 cp`) / `S7_won_endings` under-scoring.
- **`fq_w_ob_m4` Offline Results (Untested in `fastchess` & Confounded Baseline):** Applying `[1.65, 1.01, 1.07, 1.00, 1.00, 0.99, 0.95, 0.65]` (mean-normalized) improved `M4` WDL MSE vs `baseline_r0067_scorecard.json` by **`-4.92%`** (`0.01302 -> 0.01238`), opposite-wing WDL MSE by **`-6.32%`** (`0.01724 -> 0.01615`), and `S7` (`KQ-K 1697->2141, KR-K 442->629`), while reducing the `OB0<->OB1` cliff from **`143.5 -> 116.5 cp`** (still large without `ob_smooth`, and `KNN-K` remained `+123 cp`). **Baseline confound:** `fq_w_ob_m4/metrics.json` was trained on **`12` rounds (`r0191..r0202`) without a teacher**, whereas `baseline_r0067_scorecard.json` is a **`25`-round net trained with `b_full.pt` teacher** (no `r12_noteach` scorecard exists in `forge_fixes\`); against `r12_noteach` in `offline_eval_table.json`, `r0203_quiet_mix60` moved `-0.000041` (`0.012890 -> 0.012849`), and no `fastchess` match (`M_W2`) has been run yet.
- **Stockfish `SFNNv20` Primary Comparison (`C:\nnue-lab\src\nnue-pytorch`):**
  - `model\modules\layer_stacks.py:11-193` + `stack_table.py:31-60`: `192` layer stacks (`piececount:queen:pawnhalf:manyoffi`) use **`FactorizedStackedLinear`** (`group_factor_w/b`, `ls_factors="piececount+queen:pawnhalf:manyoffi"`) + **`ls_remap_min=50`** fallback routing rare stacks to the nearest well-seen stack with same queen/piececount band.
  - `data_loader\cpp\training_data_loader.cpp:941-1174`: 5-point cubic Hermite spline piece-count filter (`pc_y0=0.0, pc_y1=0.4, pc_y2=1.0, pc_y3=1.0, pc_y4=0.75`, `max_pc_skip_rate=0.975`) prevents opening (`30-32` pcs) flooding and balances endgame coverage.

### Exact `ob_smooth_penalty()` Math & `OB0` Washout Risk
In `train_v3p.py:169-182` (`ob_pairs = float(self.out_buckets - 1) = 7.0` for `OB=8`, guarded `0.0` at `OB < 2`):
```text
pen = (sum(w2[1:] - w2[:-1])^2 + sum(b2[1:] - b2[:-1])^2 + sum(pt[:,:,1:] - pt[:,:,:-1])^2) / 7
```
For an adjacent-bucket parameter jump `Delta = p[b+1] - p[b]` (`Delta = 0.1`):
- `|d(lam * pen)/d(param)| = 2 * lam * Delta / 7`:
  - At `lam = 1e-4` (CLI default): `2 * 1e-4 * 0.1 / 7 = 2.857e-6` (**`285.7x` above Adam `eps=1e-8`**).
  - At `lam = 2e-6` (pinned `G3`/`G4a` setting; `G2` final config pending `metrics.json`): `2 * 2e-6 * 0.1 / 7 = 5.714e-8` (**`5.71x` above Adam `eps=1e-8`**).
  - (The old `.mean()` bug divided by `H=1024` or `KB*768=6144`, collapsing gradients to `~1e-11 << 1e-8` and disabling smoothing.)
- **Why `2e-6` + Clean Syzygy Anchors Prevents `OB0` Washout (and Quantifies `OB0` Anchor Oversampling):** `OB0` has `3.4x` fewer rows than `OB1` in `r0202` (`5.38%` vs `18.36%`) and `3.1x` fewer in `CC0_k0` (`6.65%` vs `20.36%`). A strong `ob_smooth` (`1e-4`) — especially when `loss_pow=2.5` shrinks data gradients `~2.5-3x` (and note on *unvisited* `psqt` coordinates where `grad_data == 0`, Adam normalizes `m / (sqrt(v) + eps)` to `~±lr` for both `2e-6` and `1e-6`) — pulls sparse `OB0` weights toward `OB1`, washing out `OB0`-specific endgame scaling. Using **`--ob-smooth 2e-6`** together with **`dead_draws_20k_clean.fqs.z` + `won_endings_syzygy_20k.fqs.z`** (`--anchor-repeat 20`, exact-WDL anchor target in live `train_v3p.py:571-573`) directly injects **`800,000` `100%-OB0` anchor rows** (`20,000 + 20,000 = 40,000` rows, `100%` `OB0`, times `20`), lifting effective `OB0` share to **`33.32%`** at `2M` CC0 rows (`3.48x` *above* M4's `9.57%`) and **`10.24%`** at `20M` CC0 rows (`8.12%` at `50M`, `7.39%` at `100M`) while keeping `|grad| > Adam eps`.

### Recommendation (Pillar 2)
1. **In `G3a/G3b`:** Do **not** add `ob_reweight` yet; measure `G3a/G3b` with `--ob-smooth 2e-6` + both clean Syzygy anchor shards (`dead_draws_20k_clean.fqs.z` + `won_endings_syzygy_20k.fqs.z`), then inspect `ob0_ob1_cliff_median_jump_cp`, `S5`, `S7`, and `m4_wdl_mse` via `eval_net_full.py` and `net_sanity.py` v2.
2. **In `G4b` (only if `OB0` remains under-calibrated or `ob0<->ob1` cliff / `S7` lags):** Port `--ob-reweight` into `train_v3p.py` (analogous to `quest_train_v3_weighted.py:228-248`), **NEVER blindly applying `CC0_k0`-only `[1.44, 0.91, 1.06, 1.05, 1.03, 1.02, 0.96, 0.72]` across anchor rows** (`quest_train_v3_weighted.py:228-248` weights every row uniformly and mean-normalizes, which would double-boost the `800k` `OB0` anchors to `33.32% * 1.44` on a `2M` CC0 run and shift mean normalization). Instead, `G4b` `--ob-reweight` **MUST either**:
   - **(a) Exclude `--anchor-shards` rows from `ob_reweight`**, applying `M4 / actual_G3_CC0_OB` (recomputed post-flag-filter on the winning `G3` CC0 shard, since `1/2` plies and `--skip-fqs-noisy` shift OB shares vs `pilot_k0`) only to non-anchor CC0 rows (`weight = 1.0` on anchors); OR
   - **(b) Recompute weights `M4 / actual_G3_OB` post-filter AND post-anchor-mix** across the combined `G3` dataset (`CC0` + `anchor_shards * anchor_repeat`), where e.g. at `2M` CC0 + `800k` anchors `OB0` would be `0.29x` (`9.57% / 33.32%`), not `1.44x`. *(For reference only, un-anchored `pilot_k0` `M4 / CC0_k0` = `[1.44, 0.91, 1.06, 1.05, 1.03, 1.02, 0.96, 0.72]`.)*

---

## Pillar 3: Deeper Rescoring Cost/Benefit for Fable Lead `(b)` (`4k -> 16k`)

### Empirical Ceiling & High-Swing Targets
- **Label Noise at `2k` (`task1f_train_label_vs_sf19.json:12-13`):** Across `941` non-mate `r0202` rows vs `SF19 @ 200k` nodes: **`34.6%`** differ by **`>= 100 cp`** and **`14.8%`** differ by **`>= 200 cp`** (`MAD = 105.85 cp`).
- **Depth Ceiling (`C:\nnue-lab\teamwork\FABLE_TO_OPUS.md:8644`; `C:\nnue-lab\neon\net_search_probe\TASK1_NET_INVESTIGATION_REPORT.md:20-26, 50`):**
  - `research10x` (`10x` nodes) fixed **`23.7%`** of critical moves (`FABLE_TO_OPUS.md:8644`).
  - `5x` nodes (`50k -> 250k`) cut `r0067` blunders by **`13.4%`** (`31.73 -> 27.48/1k`, leaving `86.6%` intact, `TASK1_NET_INVESTIGATION_REPORT.md:50`).
  - Mutually exclusive partition (`n=274` confirmed blunders, `TASK1_NET_INVESTIGATION_REPORT.md:20-26`): **`65.3%` static net blindness/compression**, `18.3%` search/pruning failure, **`16.4%` horizon/depth failure**. Thus deeper Forge search fixes tactical/horizon errors (`~13–24%`) but cannot fix static net blindness (`65.3%`).
- **Direct `forge.exe` Rescore Curve (`C:\nnue-lab\neon\forge_fixes\rescore_depth_curve.json`, `n=300`):** Measured `4k -> 16k` single-core rescoring increased latency from `2.700 -> 10.603 ms/pos` (`3.93x` cost) while reducing `wdl_mse_all` by `-19.2%` (`0.00770 -> 0.00622`) and `pct_off_ge100cp` from `35.0% -> 30.7%`, corroborating the diminishing-return curve below.
- **Contested High-Swing Rates (`audit_r0202.json:26, 41-102`):** Out of `14,828,519` consecutive kept pairs in `r0202`:
  - `|score| < 500 & swing >= 200` (`|score_t + score_{t+1}| >= 200`): `24,869` (**`0.168%`**).
  - `|score| < 800 & swing >= 200`: `41,207` (**`0.278%`**).
  - All `swing >= 200`: `119,414` (**`0.805%`**).
  - Drawn-game high-score conflicts (`res == 0 & |score| >= 600`): `14,542 / 15,156,682` (**`0.096%`**).

### CPU Core-Hour Cost Table (`4k` CC0 Throughput -> `16k` Rescoring)
Measured `soft_nodes=4000` CC0 `selfgame` rates on `r0067` (`768w` SCReLU, `4` workers; `repeat_summary.json:64-65, 97-98`; `pilot_analysis.json:77, 86`) — note `1024w` Pairwise+PSQT (`G2/G3`) `selfgame` NPS is **pending `G2` completion** (`gen_cc0_selfgame_fqs_v2.py` also defaults to `8` workers):
- **Unthrottled `4k` mean (`k1=1.454M`, `k2=1.473M`):** **`1.464M pos/core-hr`** (`1,463,789`).
- **Sustained thermal-managed (`pilot_k0`):** **`1.278–1.402M pos/core-hr`** (`4w -> 2w` HeatGuard stage rates; **`0.865M pos/core-hr`** overall sustained wall-clock average across `pilot_k0`'s `208.6s` run).
- **Node scaling:** `16k / 4k = 4.00x` search cost per rescored position (consistent with `rescore_depth_curve.json`'s measured `3.93x`; ignoring cold-TT penalty, see caveat below).

| Regime | Extra CPU vs `4k` | Total Factor | `50M` Pos (Core-Hrs, `@1.464M`) | `100M` Pos (Core-Hrs, `@1.464M`) | Sustained `50M / 100M` (`4k` Stage Range) | Rescored Rows (`50M` / `100M`) |
|---|---:|---:|---:|---:|---|---|
| **`4k` CC0 Baseline** | `0.0%` | `1.00x` | **`34.2`** | **`68.3`** | `35.7–39.1` / `71.3–78.3` (`57.8` / `115.6` `@0.865M`) | `0` / `0` |
| **Selective `0.5% @ 16k`** (`swing>=200` / conflicts) | **`+2.0%`** | `1.02x` | **`34.8`** (`+0.68`) | **`69.7`** (`+1.37`) | `36.4–39.9` / `72.8–79.8` | `250k` / `500k` |
| **Selective `5.0% @ 16k`** (broad tactical/endgame) | **`+20.0%`** | `1.20x` | **`41.0`** (`+6.83`) | **`82.0`** (`+13.66`) | `42.8–47.0` / `85.6–93.9` | `2.5M` / `5.0M` |
| **Direct `16k` Datagen** (no `4k` pass) | **`+300.0%`** | `4.00x` | **`136.6`** (`+102.5`) | **`273.3`** (`+205.0`) | `142.7–156.5` / `285.3–313.0` | `50M` / `100M` |
| **`4k` + `100%` `16k` Post-Rescore** | **`+400.0%`** | `5.00x` | **`170.8`** (`+136.6`) | **`341.6`** (`+273.3`) | `178.3–195.7` / `356.6–391.3` | `50M` / `100M` |

- **Cold-TT Sensitivity & Primary-Source Lessons:** Standalone single-FEN `rescore` lacks warm sequential TT reuse from `selfgame`, typically costing **`~1.5–2.0x`** more nodes/time per position (e.g., making `0.5%` cost `+3–4%` instead of `+2%`, and `5%` cost `+30–40%` instead of `+20%`). From `C:\nnue-lab\src\Stockfish-tools\docs\transform.md:23-41` & `nnue-pytorch\scripts\gensfen.sh:13`: use **`PruneAtShallowDepth=false`** (or equivalent reduced-pruning verification) and clear TT between unrelated FENs. Note that `Stockfish-tools`'s `keep_moves=1` applies to `.binpack` move chains; M2's 38-byte `.fqs.z` binary schema (`packed[32], stm, score16, res8, flags, weight_u8`) stores FENs, scores, results, and flags **without moves**, so selective `16k` rescoring on `.fqs.z` is **non-destructive FEN-level relabeling** (overwriting `score16` only on selected rows while preserving `res8` and `flags`), or requires an optional sidecar PGN if full game move history is ever needed.

### Recommendation (Pillar 3)
**Reject full `100% 16k` rescoring (`+300%` to `+400%` CPU)** — `4x–5x` more `4k` CC0 games gives far higher position diversity per core-hour. Instead, implement **selective `0.5%–5.0%` `16k` rescoring** (`+0.68–6.83` core-hrs per `50M`, `+1.37–13.66` per `100M`, or `~1.5–2x` with cold TT) targeting high-swing contested rows (`|score|<500..800 & swing>=200`, `0.17%–0.28%`) and `res==0 & |score|>=600` (`0.096%`).

---

## Pillar 4: Multi-Net Diversity (`Fable Lead c`), `soft800`, and `eval_scale` Margin Alignment

### Reconciling Fable's `19:02` Withdrawal vs Cross-Architecture Diversity
- **Why Intra-Loop V3 Self-Play (`Lead c`) Failed (`FABLE_TO_OPUS.md:8698-8726`, 27 Nov 19:02 PC):**
  - Fable tested `200g @ 10k` nodes (`v3-r15dsg-sp-clang`, `UHO_Lichess_4852_v1`) measuring mover expected-score optimism `O`:
    - `P0 (r0067 vs r0067)`: `O = +0.0015 (SE 0.0003)`
    - `P1 (r0067 vs r0202)`: `O = +0.0035 (SE 0.0005)`, `P1 - P0 = +0.0021 (z = +3.6)`
    - `P2 (r0067 vs r0020, 182 rounds apart)`: `O = +0.0042 (SE 0.0006)`, `P2 - P0 = +0.0027 (z = +3.9)` (`r0067 +0.049`, `r0020 -0.042`).
  - `+0.0021..+0.0027` WDL offset (`~2` net units) fell below `M1` (`>= +0.010`) and triggered `M2` refutation (`< +0.003`): under Forge's `711.11 cp/WDL` scale (`d(cp)/d(wdl)|_0 = 4 * 400 / 2.25`), `P2 - P0 = +0.0027` is `1.92 cp` (**`20.8x`** smaller than `H1`'s `+0.4` pawn / `40 cp`, and `P1 - P0 = +0.0021` is `1.49 cp` = `26.8x` smaller; `FABLE_TO_OPUS.md:8715` slipped in a `~50x` rounding error). Fable formally **withdrew** same-family loop-net self-play as a diversity lead.
- **Why Cross-Architecture / External Diversity Still Matters:**
  - `r0067` (`768w` single-layer SCReLU) and `r0020` (`512w` SCReLU) share the same linear head and 8-random-ply training heritage, causing them to agree on blind spots.
  - **Genuine diversity requires orthogonal inductive bias or search stochasticity:**
    1. **Cross-architecture self-play pool:** Match **`G2`/`G3` (`1024w` Pairwise+PSQT)** against **`r0067` (`768w` SCReLU)** once `G2/G3` is stronger, OR pair distinct training architectures/loss powers (`p=2.0` vs `p=2.5`).
    2. **External teacher / cross-engine diversity:** `M0a` (`r12_noteach vs r12_control`, `summary.json`) showed dropping `b_full.pt` (HCE teacher) lost **`-26.46 ± 13.52 Elo`** (`z=-3.852`) — confirming an independent evaluator's structural bias (`+26.46 Elo` teacher effect) prevents single-family scale drift and endgame optimism.
    3. **Stockfish / Lc0 Primary Pattern:** Stockfish breaks alpha-beta inbreeding via **`gensfen random_multi_pv 4 random_multi_pv_diff 50`** (`gensfen.sh:19`) + **Lc0 `T60/T80` MCTS data** (`lc0-data-converter` + Syzygy 6/7-piece rescoring). In Forge, **`book_cc0_clean.epd` + parity-balanced `1/2` random plies** (`gen_cc0_selfgame_fqs_v2.py`) replaces `8` random plies; external SF19 labels (`Fable Lead a`) remain an owner-gated escalation if `G3/G4` retains static net blindness.

### `score_weight soft800` & `eval_scale` / `K=2.25` Margin Alignment
- **`soft800` (`quest_train_v3_weighted.py:214-217`, `M_W1_soft800_vs_noteach_n50k`):**
  - Weights `|score| < 800 -> 1.0`, `800..1199 -> 0.50`, `>= 1200 -> 0.25` (mean-normalized) to counter sigmoid gradient collapse (`p*(1-p)` drops `0.2427 -> 0.00172 -> 0.00007`).
  - `M_W1` (`1,000g @ 50k`) scored **`+0.69 ± 13.90 Elo`** (`276-274-450`, `z=+0.098`, `LOS=53.91%` — flat). Furthermore, **`CC0 pilot_k0` already cuts `|score| >= 800` from `14.02%` (`r0202`) down to `5.52%`** (`pilot_analysis.json:181-182` vs `audit_r0202.json:131,137`). **Defer `soft800`** for `G3/G4`.
- **`eval_scale = 400`, `K = 2.25`, and `v3_uci_options` Coupling:**
  - `nnue.hpp:24`, `nnue_v3.cpp:766`, `forge_v3p.py:10,39,160`, `train_v3p.py:159,565`:
    `cp = clamp(trunc(out * 400 / (255 * 64)), -30000, 30000)` and `logit = 2.25 * cp / 400 = cp / 177.78` (`d(cp)/d(wdl)|_0 = 4 * 400 / 2.25 = 711.11` cp/WDL; `+100 cp -> 63.70%` WDL).
  - Forge's **`45` `v3_uci_options` keys (`41` ints + `4` bools, containing the `40` Stage-4 tuned `A_FINAL.json` values)** at `pipeline\config.forge.toml:212-214` (`RfpMargin=84`, `RazorBase=182`, `FutilityMultiplier=59`, `ProbcutMargin=168`, `EvalSwingMult=15`, etc.) are calibrated directly to this scale. Inflating output scale without matching `eval_scale` or re-tuning causes collapse (`r12_noteach` `std_ev +34%` lost `-26.46 Elo`; `B2_finetune` `1.52-2.52x` scale inflation lost `-166 Elo`).
  - **`eval_net_full.py:114` Discrepancy & External WDL Rule:** `eval_net_full.py:114` computes `sigmoid_wdl(cp) = 1 / (1 + exp(-cp / 400.0 * 1.15))` (`1.15/400` vs Forge's `2.25/400`, so `+200 cp -> 0.6399` vs `0.7549`, a `1.96x` slope difference!). Compare M4 WDL MSEs strictly within the same script. **Rule:** Never mix raw external cp (e.g., SF19 `win_rate_model` from `Stockfish\src\uci.cpp:527-584`) directly into Forge `score16`; always map external scores through the external engine's own WDL curve into `[0, 1]` probability space first, and verify `eval_net_full.py` OLS piece/slope alignment before running `fastchess`.

---

## Recommended `G3 -> G4` Experiment Order

| Step | Run | Config Delta (One Variable / Gate at a Time) | Gate / Pass Criterion |
|---:|---|---|---|
| **1** | **`G3a` vs `G3b`** | Unified `4k` CC0 `.fqs.z` (`gen_cc0_selfgame_fqs_v2.py`, parity-balanced `1/2` plies) + `dead_draws_20k_clean.fqs.z` + `won_endings_syzygy_20k.fqs.z` (`--anchor-repeat 20`, exact-WDL anchor fix in live `19:13:07` `train_v3p.py:571-573`) + **`--loss-pow 2.0 --ob-smooth 2e-6`**. `G3a`: keep noisy; `G3b`: `--skip-fqs-noisy` (`in_check` bit 1 skipped by default in live `train_v3p.py:313` unless `--keep-fqs-check` is passed; M2 patch `train_v3p_g3_flags.patch` uses `--skip-fqs-in-check`). | `net_sanity.py` v2 (`0` flags), `eval_net_full.py` scale parity, `fastchess` equal-time `6+0.06` vs `G2` (once `G2` completes) & `r0067` (determines noisy policy). |
| **2** | **`G4a` (`loss_pow 2.5`)** | Best `G3` config + **`--loss-pow 2.5 --ob-smooth 2e-6`** (`--loss-pow` already in `train_v3p.py:575-578`; keep `--ob-smooth 2e-6` pinned as a strictly single-variable change, only testing `1e-6` subsequently if `OB0` washes out). | `eval_net_full.py` M4 WDL MSE + `fastchess` `6+0.06` vs `G3` winner (closes unrun `EXP-W3`). |
| **3** | **`G4b` (`ob_reweight_cc0`)** | *Conditional* — run only if `G3`/`G4a` still shows `OB0` starvation, `S5`/`S7` lag, or `ob0<->ob1` cliff `> 40 cp`. Port `--ob-reweight` to `train_v3p.py` **excluding anchor rows OR recomputing `M4 / actual_G3_OB` post-filter and post-anchor-mix** on the winning `G3` dataset (never blindly applying un-anchored `CC0_k0` `[1.44,...,0.72]` across the `800k` `OB0` anchor rows). | `ob0<->ob1` cliff drop (`< 40 cp`), `S5`/`S7` clean, `fastchess` vs `G4a`/winner. |
| **4** | **`G4c` (Selective `16k` + Cross-Arch)** | Add two-pass selective `16k` rescoring (`0.5%–5%` high-swing `|score|<500..800, swing>=200` + `res==0, |score|>=600`, clean TT, non-destructive FEN-level `score16` relabeling preserving `res8`/`flags`, `+2%–20%` base CPU) + cross-architecture self-play (`G3` `1024w` Pairwise+PSQT vs `r0067` `768w` SCReLU if `G3 > r0067`, or `random_multi_pv`). | `fastchess` `6+0.06` + `task1` SF19 blunder-rate check (Moves 01–10 & `ob4..6`). |
| **5** | **Escalation (`Lead a` / `soft800`)** | *Only if `65.3%` static net blindness persists:* (a) owner-gated external SF19 WDL-converted teacher/labels (never raw cp, keep `eval_scale=400, K=2.25` locked to `45` `v3_uci_options` unless re-tuning), or (b) `soft800` re-test atop `G4`. | `eval_net_full.py` slope `~1.0` + `fastchess` `6+0.06` SPRT. |
