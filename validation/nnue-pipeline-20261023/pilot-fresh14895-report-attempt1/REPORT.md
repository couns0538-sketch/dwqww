# Forge fixed-held-out network comparison

4149 eligible positions from 56 represented held-out games (56 listed game IDs). Every source-line recipe, feature set, score and STM result replayed; prepared arrays and original source/network hashes remained unchanged. HCE values are bound by the prepared NPZ/native-probe provenance and were not reexecuted here.

| Evaluator | Pure search-teacher probability MSE |
|---|---:|
| HCE only | 0.00666053622 |
| Shipped HCE + residual | 0.00608204906 |
| Candidate HCE + residual | 0.00664974564 |
| Shipped residual term only | 0.0756101342 |
| Candidate residual term only | 0.0812696059 |

Prior baseline comparison: PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE.

Candidate versus HCE: absolute reduction 1.07905804e-05, 95% CI [2.36042775e-06, 1.89419502e-05]; relative 0.162%, 95% CI [0.035%, 0.319%].

Candidate versus shipped: absolute reduction -0.00056769658, 95% CI [-0.0009220445, -0.000217368826]; relative -9.334%, 95% CI [-17.597%, -3.547%].

Intervals use 2000 paired whole-game resamples, seed20261023, with ratio(sum loss / sum rows) and linear percentile endpoints. Positive reduction means lower loss; no per-position independence is assumed. Empty eligible games are not represented clusters. Full per-row losses and game IDs are retained in `per-row-losses.npz`, SHA256 `b0e1a8472ccec3ad6bcd800e7607d11c5aa37bcaee60a71627fef1389dab68b1`. Full aggregate metrics agree with the trainer within1e-12.

These are conditional held-out loss comparisons, not Elo or independent confirmation after model selection on this holdout. Residual-term-only is diagnostic; the engine deploys HCE plus residual. Search and the shipped network were not modified.
