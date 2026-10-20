# Pin-aware SEE — isolated 6.4.15 candidate

Baseline is exact 6.4.14 source21538ec, all preserved work through checkpoint
63ec719. Integration356e863 is unchanged. This experiment changes only the
selection of legal hypothetical non-king recapturers in SEE, plus permanent
tests and version labels. Network, evaluation weights and search thresholds
are unchanged. Better tactical pruning/ordering is a hypothesis, not Elo proof.

The source215 actual API misses eight authored legal exchange values: absolute
orthogonal/diagonal pins and newly exposed pins, for both colors. A 304-case
prototype (302 legal, 20 thresholds each) corrects all eight without a new
oracle mismatch. Full prototype/source/core evidence is retained separately.
Independent review found no patch-specific blocker, but per-attacker king
attack queries add unmeasured hot-path work. Generic SEE retains its original
LVA and recapture-promotion approximations; no universal minimax claim.

Permanent regressions add 23 independently checked authored positions, each
mirrored, testing exact exchange, thresholds gain-1/gain/gain+1, legality and
unchanged board state. These tests compiled against the actual frozen215 core
and produced exactly 16 expected failing assertions before production repair.

Next gates: freeze candidate; complete Release/ASanUBSan/TSan CTest; actual API
and legal UCI search checks; deterministic work accounting and a separately
qualified performance screen. Search parity is not expected after this
intentional behavior change. No candidate strength games are run or accepted
at this checkpoint. Prior noisy calibration and invalid TT match stay separate.

One initial apply_patch attempt used an incorrect UCI version string anchor.
Atomic verification failed and left all production files unchanged. The exact
existing anchor was then read and the corrected patch applied. No failed build
or engine execution resulted from that editing attempt.
