# Holdout skill review

2026-11-03 13:57 Vienna. The owned copy of npt-data-holdout-check now links a
bounded-chain evidence reference and respects explicit protected-runtime import
restrictions. It does not create export permission or alter the original R13 copy.

Independent read-only review verified that links resolve and exercised a case
with full position-key coverage, no position overlap, inferred IDs and a thirty-
ply endpoint gap checked only through eight plies. The review correctly kept
training BLOCKED/UNVERIFIED and identified the missing historical producer and
authentic game-row bindings.

Review found one imprecise sentence about exhausted negatives. It now explicitly
distinguishes an exact endpoint gap within the search bound, where exhaustion
rules out continuation, from a larger endpoint gap that remains UNKNOWN. Longer
paths cannot retain the same fullmove number and side-to-move endpoint.

The standard skill validator was attempted with the owned runtime; it could not
start because its YAML dependency is absent. Log:
D:/a14/evidence/test_logs/r14/skill-validator01.log. No runtime package was
installed during the ongoing pinned audit. Frontmatter is unchanged. Syntax and
all reference targets were checked read-only; do not call the standard validator
passed. A focused recheck of the corrected sentence remains pending.
