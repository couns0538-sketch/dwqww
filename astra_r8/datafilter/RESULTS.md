# Astra R8 Job 2 — UNPROVEN

Base: 9761eb367c3ae4e541fc316380699f78eb493a3c. Isolated branch astra-r8-datafilter.
Implementation in progress; no training readiness or strength claim.

| Success test | Status |
|---|---|
| 1 Legacy identity, 100,000 rows | PENDING |
| 2 Result orientation, 1,000 rows | PENDING |
| 3 Determinism | PENDING |
| 4 Deliberate failures | PENDING |
| 5 Million-row audit | PENDING |
| 6 Sign audit | PENDING |
| 7 Handoff integrity | PENDING |

Capture measurement BLOCKED: production self-play lacks stored best moves.
Qsearch measurement BLOCKED: FD3A5190 exposes no static/root-qsearch oracle.

Initial disk check: C: 174030757888 bytes free; D: 83882475520 bytes free.
Production converter and two helpers copied unchanged into baseline and SHA256 recorded.

## Execution ledger

Source of intent: user-supplied Job 2 plan. No separate spec supplied.
Interfaces: normalization precedes legacy filtering/clipping; metadata follows identical
dedup/shuffle indices; adapter consumes full FEN and signed STM targets, not REC binary.
Ruling: user-required four milestone reviews override executing-plans' one-review default.
Ruling: use supplied plan's policy pending missing separate policy/exclusion text.
Milestone 1 reviewed: result bytes and legacy selection inspected; validation gaps
fixed with four failing regression tests, then green. Lichess/normalized converter
routes added; baseline byte preservation pinned with .gitattributes.
Milestone 2 resource guard fixes under focused recheck before million filtering.
15 CPU tests pass using installed npt native FEN API (no GPU/training).
Frozen cohort: shard001 rows 1..466506, shard002 rows 1..533494.
User enlarged working budget to approximately six hours. User explicitly permits
D-only validation while F has 47.46 GB free; F remains read-only.
Next: legacy100k/orientation audits, two-worker million filter, adapter integration.
