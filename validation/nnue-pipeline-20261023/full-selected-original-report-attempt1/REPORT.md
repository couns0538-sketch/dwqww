# Forge fixed-held-out network comparison

4149 eligible positions from 56 represented held-out games (56 listed game IDs). Every source-line recipe, feature set, score and STM result replayed; prepared arrays and original source/network hashes remained unchanged. HCE values are bound by the prepared NPZ/native-probe provenance and were not reexecuted here.

| Evaluator | Pure search-teacher probability MSE |
|---|---:|
| HCE only | 0.00666053622 |
| Shipped HCE + residual | 0.00608204906 |
| Candidate HCE + residual | 0.00602538104 |
| Shipped residual term only | 0.0756101342 |
| Candidate residual term only | 0.0713846232 |

Prior baseline comparison: PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE.

Candidate versus HCE: absolute reduction 0.000635155171, 95% CI [0.000225042434, 0.00106188188]; relative 9.536%, 95% CI [3.758%, 14.853%].

Candidate versus shipped: absolute reduction 5.66680111e-05, 95% CI [-0.000290669327, 0.000400212537]; relative 0.932%, 95% CI [-5.603%, 5.817%].

Intervals use 2000 paired whole-game resamples, seed20261023, with ratio(sum loss / sum rows) and linear percentile endpoints. Positive reduction means lower loss; no per-position independence is assumed. Empty eligible games are not represented clusters. Full per-row losses and game IDs are retained in `per-row-losses.npz`, SHA256 `923ed794979989399765f21cb433641dfd3cb39cddf50d2991267b09a54c725b`. Full aggregate metrics agree with the trainer within1e-12.

These are conditional held-out loss comparisons, not Elo or independent confirmation after model selection on this holdout. Residual-term-only is diagnostic; the engine deploys HCE plus residual. Search and the shipped network were not modified.
