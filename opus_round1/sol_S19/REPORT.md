# S19 [Sol leftover] Score-to-WDL scale fit per phase — DONE (tool, fitted table, real-volume check; UNPROVEN for strength)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 11. Branch `opus-sol-S19` = `d4f4312` + `0d99f02` cherry-picked + this
commit. Tool job, no engine change, `[skip ci]`. Sol never started S19 (status NOT_STARTED).

**Spec (Sol, verbatim essentials):** fit a per-phase sigmoid scale with CI to map STM score to WDL. Deliver: tool +
fitted table + report. Pass: deterministic; on a held-out split, log-loss is at least as good as the current
constant; the result is clearly marked UNPROVEN on real data volume (916 lines). Crew rework: use the f006 recipe's
settings as the reference constant. **Reference constant:** `k = 2.25` (`train_resid_v3b.py` `K_DEFAULT`; the f006
recipe does not set `--sigmoid-k`), in `sigmoid(clamp(score * k / 400, ±40))`.

## Acceptance
| line | result | evidence |
|---|---|---|
| tool | **PASS** | `forge_sol_S19_wdl_scale_fit.py` + `README.md` |
| fitted table | **PASS** | `forge_sol_S19_fitted_table_production_20261027.md` (real Forge self-play, below); every run's JSON in `logs/s19_results.tar.gz` |
| deterministic | **PASS** | the same run twice gives identical JSON bytes (sha256 `23d11308…`, `logs/step2b_determinism.log`); test `test_deterministic_output_and_no_overwrite` |
| held-out log-loss at least as good as the constant | **PASS** on all three inputs | text sample: table 0.540697 = constant 0.540697 (the table keeps 2.25: no CI excludes it); data32: table 0.693360 vs constant 0.976116; real production holdout 013+014: table **0.426968** vs constant **0.434570** (−0.007602, −1.75%) |
| marked UNPROVEN on the 916-line volume | **PASS** | the tool writes `status: UNPROVEN …` into every result; this report (below) |
| tests + fixtures, planted bugs | **PASS** | 12/12 tests (`logs/step4_tests.log`); 8/8 mutants caught (`logs/step5_mutation_check.log`) |
| real-file run | **PASS** | the 916-line text sample, and a real-volume run on the PC's production shards (read-only) |

## 1. The real 916-line text sample (`logs/step1_text916.log`) — UNPROVEN, far too small
`5_nnue/sample_data/forge_text_sample/forge_selfplay_sample_916lines.txt` (sha256 `ab429836…`): 916 positions from
**12 games**; split by game (frac 0.3, seed `s19`): 635 fit rows (8 games), 281 held-out rows (4 games).
- No bucket has both 200 fit rows and a CI that excludes 2.25, so the delivered table is 2.25 everywhere and its
  held-out log-loss equals the constant's (0.540697).
- Fitting anyway is worse: global k 2.94 (game-bootstrap 95% CI [1.36, 10.18]) gives 0.543668 held-out (+0.0030).
- With 12 games this sample cannot support any change to the constant.
- Cross-check: the sample's `.pos` (converted from the same text) decodes to exactly the same score, phase and
  result arrays as the text path (test `test_real_sample_text_and_pos_paths_agree`).

## 2. The data32 sample (`logs/step2_data32.log`) — synthetic labels
Fit on `t00000`–`t03000` (200,000 rows), held-out `h000` (50,000 rows).
- The fitted k is about 0 in every phase (global −0.0035, CI [−0.0125, 0.0049]): the results of this sample are
  independent of its scores, as expected for a synthetic sample, and held-out log-loss at k ≈ 0 is ln 2 = 0.6931.
- The constant 2.25 scores 0.976 there (worse than a coin flip).
- This is a pipeline check, not evidence about real data.

## 3. Real volume: the PC's production self-play shards (read-only; `logs/step3_real_production.log`)
The production `.pos` files are on this PC (`D:\grok-pc-data\forge_push\nnue_data\pos`, read through read-only
memory maps; nothing written there). Fit: `forge_selfplay_003.pos` + `007.pos` (10M + 10M positions; sha256
`d322089c…`, `a741c265…`). Held-out: the production holdout `013.pos` + `014.pos` (10M + 6.39M; `904e6527…`,
`255afc00…`), which are separate games never used for training. Every 5th row was used (`--stride 5`: 4.0M fit,
3.28M held-out). Bootstrap by row, 50 samples. Run time 106 s at nice 19.

**Fitted table (real Forge self-play, `forge_sol_S19_fitted_table_production_20261027.md`):**

| phase | fit rows | held-out rows | fitted k | 95% CI (row bootstrap) | table k | held-out log-loss k=2.25 | held-out log-loss table |
|---|---:|---:|---:|---|---:|---:|---:|
| 0-3 | 652,152 | 510,818 | 2.2396 | [2.2312, 2.2455] | 2.2396 | 0.377257 | 0.377312 |
| 4-7 | 1,107,257 | 894,624 | 2.7602 | [2.7537, 2.7690] | 2.7602 | 0.350309 | 0.345992 |
| 8-11 | 467,405 | 388,563 | 3.3302 | [3.3157, 3.3431] | 3.3302 | 0.386625 | 0.372731 |
| 12-15 | 326,865 | 273,235 | 3.4559 | [3.4329, 3.4782] | 3.4559 | 0.426298 | 0.411517 |
| 16-19 | 317,824 | 266,822 | 3.3261 | [3.3082, 3.3437] | 3.3261 | 0.420836 | 0.407850 |
| 20-24 | 1,128,497 | 943,653 | 3.3615 | [3.3524, 3.3707] | 3.3615 | 0.571497 | 0.562828 |

- Global fitted k 2.9255 (CI [2.9223, 2.9292]).
- Held-out log-loss (3,277,715 rows): constant 2.25 0.434570; global k 0.428393; per-phase table **0.426968**
  (−0.007602 vs the constant).
- **Reading:** on Forge's own self-play results, 2.25 fits only the late endgame (phase 0-3). From phase 4 up,
  results are more decisive per centipawn than the constant assumes (k ≈ 2.8-3.5).
- The table is a better WDL map on held-out games. Whether training with it (teacher scale, or the blend of teacher
  and result) gives a stronger net is **UNPROVEN**: no training or gate was run.
- **Limits:**
  - The row bootstrap ignores the correlation of positions within a game, so the CIs are too narrow; game ids
    would allow a game bootstrap (S17's split work).
  - Only 2 of the 12 train shards were used for the fit, every 5th row.
  - The 1-ply-of-a-search "score" is Forge's fixed-node search score from the self-play run.

## Files
`forge_sol_S19_wdl_scale_fit.py`, `test_forge_sol_S19_wdl_scale_fit.py`, `mutation_check_s19.py`, `README.md`,
`IDEA_SOURCE.md`, `forge_sol_S19_fitted_table_production_20261027.md`, `REPORT.md`, `FILES`, `SHA256SUMS`;
`logs/step1_text916.log`, `step2_data32.log`, `step2b_determinism.log`, `step3_real_production.log`,
`step4_tests.log`, `step5_mutation_check.log`, `logs/s19_results.tar.gz` (4,053 B: the six result JSON/MD files).
Machine exclusive: no (no timing claims are made).

## UNVERIFIED / left
- Any effect of the table on training or strength (no training, no gate).
- Game-level intervals on the production data (needs game ids).
- A full-volume fit (all 12 train shards, every row).
