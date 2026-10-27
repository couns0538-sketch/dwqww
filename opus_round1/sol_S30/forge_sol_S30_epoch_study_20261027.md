# S30 Epoch and data-size learning-curve study (2026-10-27)

**Question (Sol's S30 spec):** why did e48 (G104 H1 +29.44) beat e32 (+10.89, cap) and e24 (+1.85, cap), and what to
test next (e64, a longer low-LR tail, or more data), with ranges.

**Short answer:**
- The premise is not established: e48's confirm gate came in at the size of the e32 cap points.
- At a fixed data size, more epochs moved the holdout loss by about one or two seed-spreads (noise level).
- Data size is the only factor whose loss effect is far above the seed spread.
- **Loss alone has not predicted Elo for us**, so none of this decides a gate. It only says which change could be
  big enough to show up in games.
- Every real-data conclusion below is UNVERIFIED until a gate runs. No GPU was used.

**Sources (read-only):**
- `RUNS` = the PC's training logs `F:\forge_nnue_train\runs\` (snapshot 2026-10-27 12:3x PC time; 91 logs, 78 FINAL
  lines, 2,062 EPOCH lines, parsed by `forge_sol_S30_log_curves.py`; table `final_table.csv`).
- `SUM` = `7_history/gate_results/GATE_RESULTS_SUMMARY_20261025_1215.md`.
- `LGF` = `7_history/LATEST_GATE_FACTS_20261026.md`.
- `PLAN` = `5_nnue/docs/NNUE_NEXT_WEEK_PLAN.md` (all in the lock archive `forge_LOCK_AL1_s198_FULL_20261026_1039`).

## 1. The gate premise
| net | gate | result | source |
|---|---|---|---|
| e48 f006 | G104 | **H1 accepted early** at 698 games, Elo +29.44 ±13.23, LLR 2.95 | SUM:12 |
| e48 f006, confirm (new srand) | G104c | 1500 games, **+7.18 ±8.49**, LLR 1.23, cap with no decision | LGF:10 |
| e32 f003 | G100 / G100r | +8.34 ±8.45 cap / +10.89 ±8.38, LLR 2.22 cap | SUM:9, SUM:10 |
| e32 f003rec s197 | G119 | +9.50 ±8.84, cap | SUM:13 |
| e24 f005 | G102 | about +1.85, LLR −0.18, cap | SUM:11 |
| e32 f003rec s198 | G120 / G120c | +23.62 ±11.90 H1 / +14.46 ±8.61 H1, became the AL1 lock | LGF:7, LGF:8 |
| e48 f030 / f031 / f034 / f042 vs AL1 | G122 / G123 / G124 (+G124c) / G125 | +4.86 cap / +9.04 cap / +14.81 H1, then G124c cap, no lock / LLR 0.85 cap | LGF:11-15 |

- **Early stop.** G104 stopped as soon as its LLR crossed the bound, and an early-stopped SPRT overstates the effect.
- **Confirm.** Its confirm G104c (+7.18) is the same size as the e32 cap points. Those points (+8 to +11) may be used
  only as unpooled effect sizes, never pooled and never as evidence (SUM:18; S30 rule note 12:15).
- **AL1.** The recipe that became AL1 is the e32 recipe (G120/G120c).
- **Since then.** Four e48 nets were gated against AL1, and none locked (LGF:11-15).
- **Conclusion:** "e48 beat e32" is not shown by the games. The gates show one early-stopped H1 that its confirm did
  not repeat.

## 2. Seed spread (the noise floor of the FINAL holdout loss)
Runs with the same recipe and the same training-data size, different seeds (13 groups, `fit.json` →
`seed_spread_groups`):
- pooled sd: b0.6 **7.1e-6**, teacher **3.5e-6**;
- ranges up to 2.7e-5 (b0.6) inside one group.
- Example, e48 at 161,913,894 positions: f029 0.014298 (RUNS `resid_h256_e48_f029_bs16k_lr10e4_b06_s329_fb8k.log:344`),
  f030 0.014271 (`…_f030_…_s49_fb8k.log:346`), f031 0.014284 (`…_f031_…_s331_fb8k.log:346`).
- Any gap below about 2 × 7.1e-6 ≈ 1.4e-5, or inside a group's range, is **noise**.

## 3. Epochs at a fixed data size (137,381,087 positions, blend-end 0.6, H256)
| epochs | run | lr | FINAL b0.6 | FINAL teacher | source (RUNS) |
|---:|---|---|---:|---:|---|
| 16 | f007 | 9.898e-4 | 0.014367 | 0.004565 | `resid_h256_e16_f007_bs16k_lr14e4_b06_s26_fb8k.log:66` |
| 16 | f009 | 9.898e-4 | 0.014390 | 0.004576 | `resid_h256_e16_f009_bs16k_lr14e4_b06_s28_fb8k.log:110` |
| 16 | f010 | 8.484e-4 | 0.014389 | 0.004573 | `resid_h256_e16_f010_bs16k_lr12e4_b06_s29_fb8k.log:110` |
| 20 | f011 | 9.898e-4 | 0.014375 | 0.004577 | `resid_h256_e20_f011_bs16k_lr14e4_b06_s30_fb8k.log:134` |
| 20 | f013 | 7.07e-4 | 0.014373 | 0.004561 | `resid_h256_e20_f013_bs16k_lr10e4_b06_s32_fb8k.log:134` |
| 24 | f005 | 7.07e-4 | 0.014357 | 0.004570 | `resid_h256_e24_f005_bs16k_lr10e4_b06_s24_fb8k.log:99` |
| 48 | f006 | 7.07e-4 | 0.014341 | 0.004593 | `resid_h256_e48_f006_bs16k_lr10e4_b06_s25_fb8k.resume1.log:11` |

- **e24 vs e48 (f005/f006, matched except epochs and seed):**
  - b0.6 gap 1.6e-5: 2.3 seed-sds, inside the seed ranges of §2, so **noise-level**;
  - teacher: e48 is *worse* (0.004593 vs 0.004570).
- **e16 runs:** the two runs at the same lr differ by 2.3e-5 among themselves.
- **Fit** `L(E) = Linf + A·E^-α` (`fit.json` → `epoch_curve_fixed_data`):
  - α 0.9, Linf 0.014315;
  - predicted L(64) **0.014335** (leave-one-out range 0.014310–0.014337), against L(48) observed 0.014341.
  - So the predicted e64 gain is about 6e-6, **below one seed-sd**.
  - Caveats: the learning rates differ between points, and there are only 4 epoch levels.
- **e32 is not in this table:** f003 trained on 127,381,087 positions with lr 9.898e-4
  (`resid_h256_e32_f003_bs16k_lr14e4_b06_s22_fb8k.log:122`), so its loss is confounded with data and lr.
- **The plan's own reading agrees:** "24 ep" gave "no gain" over 16 (PLAN:47).

## 4. Data size at a fixed recipe (H256, e48, lr 7.07e-4, blend-end 0.6, batch 8192, warmup 300)
- **Runs:** 23, from 137.4M to 221.9M positions (`fit.json` → `data_curve_e48`). The endpoints are f006 0.014341 at
  137.4M (above) and f066 0.014213, f069 0.014212, f070 0.014214 at 221.9M
  (`…_f066_…_s366_fb8k.log:412`, `…_f069_…_s369_fb8k.log:410`, `…_f070_…_s89_fb8k.log:416`).
- **Fit** `b0.6 = c + s·ln(positions)`: **−1.68e-4 per doubling** (bootstrap 95% CI −1.84e-4 … −1.41e-4). That is
  about 24 seed-sds per doubling: the only effect here far above the noise floor.
- **Predicted b0.6 at 250M positions:** 0.014183 (CI 0.014177–0.014192), −2.9e-5 against the 221.9M runs.
- **Confound:** the data grew with every sealed self-play file (PLAN:49-50), and the holdout is split by file, not
  game, so loss gains are optimistic (PLAN:52).

## 5. Loss alone has not predicted Elo for us
- **Teacher loss is a negative signal across blend-ends.** e12 (b0.6) → h (b0.7) −4.2 → j (b0.8) −11.1 → l (b0.9) −44.5,
  while teacher loss fell 0.004679 → 0.004265 → 0.003968 → 0.003789 (PLAN:36-38). The same FINAL lines are in RUNS:
  `resid_h256_e12_e.log:68`, `resid_h256_e16_h_lr7e4_b07_s5.log:107`, `resid_h256_e16_j_lr7e4_b08_s7.log:183`,
  `resid_h256_e16_l_lr7e4_b09_s9.log:93`.
- **"b0.6 differences of <0.5% do not predict a gate"** (PLAN:41-42).
- **Here:**
  - f006's teacher loss was worse than f005's, yet G104 stopped H1 (and its confirm shrank to +7).
  - The four e48 nets gated against AL1 had a better b0.6 than AL1's own net: f030 0.014271, f031 0.014284, f042
    0.014252 vs f003rec_s198 0.014311 (`resid_h256_e32_f003rec_s198_b06_fb8k.log:232`), i.e. 4-8 seed-sds better.
    None locked (LGF:11-15).

## 6. What to test next (recommendation; UNVERIFIED until gated)
| option | loss evidence | expected loss change | recommendation |
|---|---|---|---|
| e64 (same data, recipe) | L(64) fit, §3 | about −6e-6 (LOO range −3e-5 … −4e-6): below one seed-sd | not worth a gate on loss grounds; if tested, as a single-factor gate e48 vs e64 on identical data and seed |
| longer low-LR tail | no run isolates it (lr and epochs move together, §3) | unknown | needs a dedicated run (same data, same seed, only the tail changed) before any gate |
| more data (same e48 recipe) | §4: −1.68e-4 per doubling, about 24 seed-sds | about −2.9e-5 from 222M to 250M | the only lever with a loss effect above noise; gate a net trained on the newest shards against AL1, one factor changed |

Ranges are loss ranges, not Elo: given §5, any of them can still be ±0 in games.

## 7. Part 2: tiny CPU replicas (pipeline only)
**Setup:** `opus_nnue_smoke_s30_replica.py`:
- a byte-identical copy of the v3b trainer (`opus_nnue_smoke_s30_v3b.py`, sha256 `5cebba4d…`);
- H64, residual, batch 512, lr 7.07e-4, warmup 20, blend-end 0.6, seed 25, one Torch thread, BelowNormal;
- the data32 sample: train = file prefixes of 4,000 / 8,000 / 16,000 / 32,000 positions (2-16% of 200k) × 2 / 4 / 8
  epochs; held-out = h000 (50,000).

**Results:**
- Two complete passes (r1, r2) are **byte-identical**: the epoch artifacts and every FINAL loss.
- The losses move away from the HCE baseline only when there are enough steps, and then they get **worse**, not
  better (32,000 × 8 epochs: b0.6 0.046366 vs HCE 0.045572). That is expected: the data32 sample's results are
  synthetic, so a net can only fit noise.
- This confirms the pipeline and its reproducibility. It says nothing about real data, so no real-data conclusion is
  drawn from it.

## Reproduce
```
python -I -B forge_sol_S30_log_curves.py --runs F:/forge_nnue_train/runs --out <new dir>     # read-only on the runs
python -I -B forge_sol_S30_fit.py --final <new dir>/final_table.csv --out <new dir>/fit.json
<NNUE venv python> -I -B opus_nnue_smoke_s30_replica.py --tag r1 ; ... --tag r2 ; ... --compare r1 r2
```
