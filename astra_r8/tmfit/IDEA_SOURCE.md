# Idea and licence record — UNPROVEN

Idea: Engine Strength, as relayed by Couns: fit the probability that the final
best move differs from the current completed iteration, then allocate soft time
using that probability. Logistic regression and bounded affine mapping were
specified by Couns. New implementation is original work in this branch.

Existing Forge AL1 soft time allocation and root iteration observables are reused
in place. No external engine source or tuned constants are imported. GPL/AGPL
engines are ideas-only; no GPL code is copied, translated or paraphrased.
NumPy is used as an installed numerical dependency; no NumPy source is copied.

The installed forge-cpp-lab skill supplies qualification guidance and an offline
evidence checker; it does not establish strength or authenticate experimental logs.

Couns clarified that these are off-repo crew patches, not missing dwqww refs:

| Prior variant | Couns's supplied description |
|---|---|
| timepack 1–4, tmdiv18 | Hand-set base-allocation factors, including moves-to-go divisor changes |
| omni_tm | Hand-set combined stability and score-trend multipliers |
| TmOppClock | Scales our allocation using opponent remaining time; idea from Caissa (MIT) |
| TmScoreLoss | Extends allocation after a root-score drop between iterations |

These descriptions supplement source inspection of AL1 and TimeManV2.
TmFitModel is distinct: logistic coefficients are estimated from logged completed
iterations, then the probability mapping is calibrated against measured time.
No Caissa code or licence notice is copied because no Caissa source is imported.

CR's supplied actual-AL1 port, governor patch and port helper are retained
unchanged under cr_fixes/ with full MD5/SHA256 receipts. The authoritative
tmfit-lock.patch is the supplied CR port; it moves the same original model onto
294dbed3 without importing other engine algorithms. The governor matches CR's
80% startup /90% ongoing CPU and8GiB free physical RAM boundary policy, with
fresh-metric validation, recorded waits and regression tests. No third-party
engine source or tuned constant was introduced by these fixes.
