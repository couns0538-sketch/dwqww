# Forge fixed-held-out network comparison

8881 eligible positions from 109 represented held-out games (111 listed game IDs). Every source-line recipe, feature set, score and STM result replayed; prepared arrays and original source/network hashes remained unchanged. HCE values are bound by the prepared NPZ/native-probe provenance and were not reexecuted here.

| Evaluator | Pure search-teacher probability MSE |
|---|---:|
| HCE only | 0.00674117069 |
| Shipped HCE + residual | 0.0059709202 |
| Candidate HCE + residual | 0.00599108003 |
| Shipped residual term only | 0.0743468253 |
| Candidate residual term only | 0.0699406992 |

Prior baseline comparison: PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE.

Candidate versus HCE: absolute reduction 0.00075009066, 95% CI [0.000375229602, 0.0011534596]; relative 11.127%, 95% CI [5.858%, 16.472%].

Candidate versus shipped: absolute reduction -2.0159829e-05, 95% CI [-0.000338886058, 0.000268717228]; relative -0.338%, 95% CI [-5.783%, 4.286%].

Intervals use 2000 paired whole-game resamples, seed20261023, with ratio(sum loss / sum rows) and linear percentile endpoints. Positive reduction means lower loss; no per-position independence is assumed. Empty eligible games are not represented clusters. Full per-row losses and game IDs are retained in `per-row-losses.npz`, SHA256 `4a66e20daeaa54a0acd61326e77a61fa62ede752227efd489d3649323033ab7c`. Full aggregate metrics agree with the trainer within1e-12.

These are conditional held-out loss comparisons, not Elo or independent confirmation after model selection on this holdout. Residual-term-only is diagnostic; the engine deploys HCE plus residual. Search and the shipped network were not modified.
