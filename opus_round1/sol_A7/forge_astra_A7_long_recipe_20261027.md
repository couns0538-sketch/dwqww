# Astra A7: long-training recipe for the H256 residual net (e64 / e96) — UNPROVEN

2026-10-27, Opus main session. Design only: no GPU use, nothing queued, no Elo claim. The three queue lines in §6 are
PROPOSED. Numbers come from the PC's finished run logs (read-only, parsed with S30's tool), the gate records in the lock
archive (`LA` = `forge_LOCK_AL1_s198_FULL_20261026_1039`) and the S30/S44 studies; every number names its source.
Tables: `results/a7_tables.md` (generated); dry parse: `logs/step3_dryparse.log`.

## 0. Short answer
- **Recipe.** Keep the e48 production recipe and change one thing, `--epochs`:
  - trainer v3b, H256 residual, batch 8192, peak lr 7.07e-4;
  - 300 warmup steps, then cosine down to a 1% floor;
  - blend 1.0 → 0.6, linear over the whole run.
  Freeze the training set with `--max-train 240000000`, so that the e48 control sees exactly the same positions.
- **Order.**
  1. First run A7-1 (e96) and A7-2 (e48 control, same seed 701, same data): 7.87 GPU-h at 1.22M positions/s.
  2. Run A7-3 (e64) only if A7-1's FINAL FULL HOLDOUT b0.6 beats A7-2's by at least 2.0e-5.
- **Expected effect.** From 43 finished main-recipe runs (log-linear fit, §1), on b0.6:
  - e96 vs e48: −3.3e-5 (95% CI −4.0e-5 … −2.8e-5);
  - e64 vs e48: −1.4e-5;
  - doubling the data at e48: −1.65e-4.
  With S44's 5.0 ± 1.5 Elo per 1e-4 of b0.6 (conc 5), these are about +1.6, +0.7 and +8 Elo. The epoch gains are
  below what a [0,10] gate can resolve.
- **Confidence.**
  - Low that an e64/e96 net passes a gate on length alone.
  - Moderate that a holdout gain of this size is real: the fit extrapolates beyond the measured 16-48 epochs, and
    S30's saturating fit predicts about half of it.
  - High that data is the bigger lever: about 5x per doubling, 43 runs, CIs far apart.
- **The A7 premise does not hold up.** The premise was "length is the biggest lever: e24 +1.85 cap, e32 +10.89 cap,
  e48 +29.44 H1". The games say otherwise:
  - G104 (+29.44) stopped early at 698 games (`GATE_RESULTS_SUMMARY_20261025_1215.md:12`).
  - Its confirm G104c capped at +7.18 ± 8.49 with no decision (`LATEST_GATE_FACTS_20261026.md:10`).
  - Of the later e48 nets against AL1, none locked: G122 +4.86 cap, G123 +9.04 cap, G124 +14.81 H1 but G124c cap,
    G125 cap (`LATEST_GATE_FACTS_20261026.md:11-15`).
  - AL1 itself is an e32 net (G120c, `LATEST_GATE_FACTS_20261026.md:8`).

## 1. What the logs say about length vs data
Inputs: the 43 finished H256 runs with blend-end 0.6, batch 8192 and self-play-only data, 137M-232M training
positions. The rows come from `results/a7_curves.tar.gz` (`final_table.csv`), and each row cites its log `file:line`.

| epochs | runs | mean FINAL full-holdout b0.6 | sd | best (log:line) | train positions | lr |
|---|---|---|---|---|---|---|
| 16 | 8 | 0.014366 | 1.70e-05 | 0.014342 (`resid_h256_e16_f026…_fb8k.log:120`) | 137.4M-161.9M | 8.484e-4, 9.898e-4 |
| 20 | 6 | 0.014352 | 1.80e-05 | 0.014332 (`resid_h256_e20_f021…_fb8k.log:142`) | 137.4M-151.9M | 7.07e-4, 9.898e-4 |
| 24 | 1 | 0.014357 | - | `resid_h256_e24_f005…_fb8k.log:99` | 137.4M | 7.07e-4 |
| 32 | 4 | 0.014327 | 2.94e-05 | 0.014308 (`resid_h256_e32_f025…_fb8k.log:232`) | 127.4M-161.9M | 9.898e-4 |
| 48 | 24 | 0.014252 | 3.05e-05 | 0.014212 (`resid_h256_e48_f069…_fb8k.log:410`) | 137.4M-231.9M | 7.07e-4 |

The e48 rows are better mostly because they have more data. Least squares over all 43 runs, with 4000-sample
bootstrap CIs, `logs/step2_curve_stats.log`:

| model | per doubling of data | per doubling of epochs | per doubling of lr | residual sd |
|---|---|---|---|---|
| b0.6 ~ log2 data + log2 epochs | **−1.65e-4** [−1.79e-4, −1.45e-4] | **−3.28e-5** [−3.96e-5, −2.76e-5] | — | 7.2e-6 |
| + log2 lr | −1.65e-4 [−1.79e-4, −1.45e-4] | −3.25e-5 [−3.98e-5, −2.67e-5] | +1.9e-6 [−1.36e-5, +1.67e-5] | 7.3e-6 |
| e48 runs only, b0.6 ~ log2 data (24 runs) | −1.63e-4 [−1.81e-4, −1.35e-4] | — | — | — |

- The seed sd of FINAL b0.6 is **7.09e-6**, pooled over 14 recipe groups with 22 dof (`seed_spread.csv`; S30 had
  7.1e-6). The fit's residual sd is the same, so the model leaves only seed noise.
- **Predictions at a fixed data size** (b0.6, negative = better):
  - e64 − e48: −1.36e-5 [−1.65e-5, −1.14e-5];
  - e96 − e48: −3.28e-5 [−3.96e-5, −2.76e-5];
  - 1.5x data at e48: −9.7e-5; 2x data at e48: −1.65e-4.
- **Agreement with earlier studies.** These are close to S44's projections (`opus-sol-S44`: e64 +0.3, e96 +0.6,
  1.5x data +4.9, 2x data +8.5 Elo). S30 (`opus-sol-S30`) found the e24 → e48 gap at fixed data to be noise-level
  (−1.6e-5) and fitted an e64 gain of about −6e-6.
- **The CIs above cover sampling noise only, not the model form.** The log-linear epoch term is fitted on 16-48 epochs
  and extrapolated to 64/96. It is also partly confounded: the e48 runs are the later ones (more data, lr 7.07e-4),
  although the data term and the near-zero lr term absorb most of that.

## 2. Learning-rate schedule
- **What v3b does** (trainer lines 602-606, `lr_at`):
  - linear warmup to `--lr` over `--warmup-steps`;
  - then a cosine from `--lr` down to `--lr × --min-lr-frac` over the rest of the run (total = steps/epoch ×
    epochs).
  A longer run therefore stretches the same shape: every LR level gets the same fraction of the run.
- **Peak 7.07e-4.**
  - All 24 e48 runs used it (`queue.txt`, f006 and f029-f074).
  - In the fit the lr term is +1.9e-6 per doubling (CI ±1.5e-5): no evidence that lr matters between 7.07e-4 and
    9.898e-4.
  - The one lr that clearly lost, 2e-3 (auto001), is above this range (`queue.txt:6`).
- **Warmup 300 steps.** That is 0.011% of e96's 2,812,416 steps. It only steadies Adam's first steps, so keep the
  recipe value.
- **Floor 1%** (`--min-lr-frac 0.01`, the default, written out). f070 ends at lr 7.08e-06
  (`resid_h256_e48_f070…_fb8k.log:411`).
- **Decay shape.** v3b has only the cosine. A separate "longer low-LR tail" cannot be built from existing arguments,
  and no run isolates it (S30). That question belongs to S-A3 (new trainer arguments).
- **Batch 8192.**
  - The GPU90 bench shows 16384 reaching 1.62M positions/s, but at memory-junction 80 °C, which is the guard's limit
    (`NETS_snapshot_20261025_1030.md:1485`).
  - Every f-series run since then uses 8192 (the `fb8k` names).
  - Keep 8192 so that a length test changes nothing else.

## 3. Blend schedule
- **What v3b does** (lines 608-610): the blend moves linearly from `--blend-start` 1.0 to `--blend-end` 0.6 over the
  whole run.
- **Keep 0.6.**
  - It is the lock's recipe (AL1 = e32 f003rec b0.6).
  - Blend-end 0.5 was worse (`queue.txt:6`).
  - Teacher loss and game results moved in opposite directions across blend-ends (S30 finding 4).
  - A length test must change one factor only.
- **Expected side effect.** The teacher loss rises at the end of every run while b0.6 stays flat, because the target
  moves toward results. It is not overfitting. Example, f070 epochs 46-48: subset teacher 0.004452 → 0.004513,
  b0.6 0.014203 → 0.014205 (`resid_h256_e48_f070…_fb8k.log:395-413`).

## 4. Data, memory and time
- **Frozen data.** `--max-train N` takes the training files in sorted order and keeps a prefix of the last file
  (v3b `load_set`, the "takes file prefixes" lines 43-52).
  - The supervisor's file list is every sealed `forge_selfplay_NNN.pos` except 013/014, sorted, i.e. generation
    order. So `--max-train 240000000` is the same 240M positions on every launch and resume, until a sealed file
    changes (they don't).
  - 241,913,894 positions are available now (`resid_h256_e48_f074…_fb8k.log:6`).
- **Memory.**
  - The DirectML growth of about 24 KB per step under v2/v3a (`NETS_snapshot_20261025_1030.md:1618`) is what killed
    f006 at the start of epoch 48 (`:1626`).
  - v3b is flat after epoch 1: f070 private memory was 9.97 GB at epoch 1, step 8,774, and 9.99 GB at epoch 48
    (`…f070…log:11, 412`).
  - Private memory scales with data, not epochs: 8.87 GB after load at 222M (`f070:8`), 9.22 GB at 232M
    (`f071:8`), 9.56 GB at 242M (`f074:8`), plus about 1.1 GB once training starts.
  - At 240M expect about 10.6 GB for e48, e64 and e96 alike; free RAM at f070's end was 11.66 GB (`f070:415`).
  - `--mmap-data` (estimate 2.8-3.3 GB private, `NETS_snapshot_20261025_1030.md:1621`) is not needed at 240M. It has
    never run on the PC (no queue line uses it), so smoke it before using it for larger data.
- **Speed.** The 39 finished v3b runs averaged **1,344,201 positions/s** over the whole run, holdout evaluation
  included (min 1,117,850 for f071, max 1,382,279; `results/a7_tables.md`). The spec's 1.22M/s is f006's v3a rate
  (1,226,606, `resid_h256_e48_f006…_fb8k.resume1.log:12`); the estimates below use it, so they are conservative.

## 5. When to stop, and how to read it from the logs
- **Never stop a cosine run early to save time.**
  - In all 43 runs the last quarter of the epochs still improved the subset b0.6, by 1.5e-5 to 3.9e-5 (e48 median
    3.35e-5, about 4.7 seed sds), because the LR anneals there.
  - The subset b0.6 first came within one seed sd of its final value only at 79-88% of the run (median 85%).
  - So a mid-run checkpoint of a long run is not a shorter run (`results/a7_tables.md`, plateau table).
- **The best subset epoch is never the last one**, but it is only 1e-6 to 7e-6 better (≤ 1 sd). That is the blend
  drift from §3, not overfitting.
  - Flag overfitting only if the last epoch is worse than the run's best subset epoch by more than 2 sd (1.4e-5),
    or the subset b0.6 rises for 3 epochs in a row in the last third while train_mse falls.
  - No run shows either.
- **"More epochs stopped helping" can only be read across runs at equal data.** Let Δ = FINAL FULL HOLDOUT b0.6 of
  the longer run minus that of the e48 control (same seed, same `--max-train`). The seed sd is 7.09e-6, so the sd of a
  difference is about 1.0e-5.

  | Δ | reading | next step |
  |---|---|---|
  | Δ ≤ −2.0e-5 (2 sd) | longer helped | run A7-3 (e64) to find the cheaper point |
  | −2.0e-5 < Δ < 0 | indistinguishable from seed noise | stop; put the GPU time into more data (S44: 1.5x data at e48 ≈ +4.9 Elo) |
  | Δ ≥ 0 | longer did not help | stop |
- **Power of this design.** If the true e96 effect is the fitted −3.3e-5, P(Δ ≤ −2e-5) ≈ Φ(1.3) ≈ 0.90. For e64
  alone (−1.4e-5) it would be Φ(−0.64) ≈ 0.26. That is why e96 runs first.
- **Gate rule.** S30 found that holdout gaps under about 0.5% (7e-5) did not predict gates. At S44's slope, 1e-4 of
  b0.6 is about +5 Elo, the smallest effect a [0,10] gate can see.
  - Gate an e64/e96 net on length alone only if Δ ≤ −1e-4. The fit makes that very unlikely.
  - Otherwise carry the winning length into the next data-size run (one factor per gate, test plan rule).

## 6. The three queue lines (PROPOSED, UNPROVEN)
File: `forge_astra_A7_queue_lines_20261027.txt`. Only existing v3b arguments are used. The supervisor adds its
standard arguments: train/holdout lists, `--hce-dir`, `--residual`, `--init-check`, `--final-full-val`,
`--log-every 60`, `--run-dir`.

| line | purpose | epochs | steps/epoch | total steps | positions trained | GPU-h at 1.22M/s | at 1.344M/s (measured) |
|---|---|---|---|---|---|---|---|
| A7-1 `resid_h256_e96_a7x_bs8k_lr707e6_b06_s701_mt240m` | the decisive long run | 96 | 29,296 | 2,812,416 | 23,039,311,872 | **5.25** | 4.76 |
| A7-2 `resid_h256_e48_a7c_bs8k_lr707e6_b06_s701_mt240m` | same-data, same-seed control | 48 | 29,296 | 1,406,208 | 11,519,655,936 | **2.62** | 2.38 |
| A7-3 `resid_h256_e64_a7y_bs8k_lr707e6_b06_s701_mt240m` | only if A7-1 − A7-2 ≤ −2e-5 | 64 | 29,296 | 1,874,944 | 15,359,541,248 | **3.50** | 3.17 |

Common arguments: `--script train_resid_v3b.py --shape 256 --lr 7.07e-4 --min-lr-frac 0.01 --blend-end 0.6
--seed 701 --batch-size 8192 --warmup-steps 300 --val-positions 1000000 --max-train 240000000`.

**Maths** (v3b `main()`: steps/epoch = N // batch, total = steps/epoch × epochs, trained = total × batch):
- steps/epoch = 240,000,000 // 8192 = 29,296;
- positions per epoch = 29,296 × 8192 = 239,992,832;
- e96: 239,992,832 × 96 = 23,039,311,872 positions; / 1.22e6 = 18,884.7 s = 5.25 h;
- e48: 11,519,655,936 positions; / 1.22e6 = 9,442.3 s = 2.62 h;
- e64: 15,359,541,248 positions; / 1.22e6 = 12,589.8 s = 3.50 h.

Evaluation adds a little (ESTIMATE, under 1%): one 1M-position subset forward per epoch, against about 240M
positions trained per epoch, plus the final 16.4M full holdout twice. The measured 1.344M/s already includes it.
Thermal suspends (gpu_guard) lengthen wall time but not GPU hours.

**Dry parse** (`logs/step3_dryparse.log`, `opus_a7_dryparse.py`):
- **The parser.** It is the unchanged v3b parser: the 33 `add_argument` calls of a byte-identical renamed copy (md5
  `b6758004`), extracted with `ast`, so no trainer code runs.
- **Positive control.** f070's own argv parses to exactly the JSON the trainer wrote into its `settings_*.txt`.
- **Supervisor split.** The split of that command into the supervisor's standard part and the queue arguments matches
  `queue.txt`.
- **Result.** All 3 lines parse. Both negative controls are rejected: a v3c-only `--epoch-positions`, and
  `--epochs 6.4e1`.

## 7. Uncertainty
- **Epoch effect.** It is extrapolated from 16-48 epochs with a log-linear model. S30's saturating fit gave about
  half the e64 gain. The true e96 effect could be 0 to −4e-5.
- **One seed per arm.** This is a deliberate trade for GPU time; the power figures are in §5.
- **Elo conversion.** S44's slope has ±30% uncertainty, plus an unexplained +6 Elo offset at conc 8 against AL1.
- **Not tested on the PC:**
  - a 2.8M-step DirectML run (the longest v3b run so far is about 1.42M steps: f074 `steps/epoch=29,530
    total=1,417,440`, log line 9);
  - `--mmap-data`;
  - the e96 thermal profile.
- **What would change this advice:** an isolating run showing that a longer low-LR tail helps (S-A3), or new gates
  showing that loss gaps under 0.5% do predict games.
