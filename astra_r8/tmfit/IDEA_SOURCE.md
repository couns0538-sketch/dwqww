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
