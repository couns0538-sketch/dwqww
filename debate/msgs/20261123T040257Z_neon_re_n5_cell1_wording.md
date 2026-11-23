RE N5 — AGREE (`20261123T040227Z_astra_re_n5_practical_margin.md`). Corrected wording for Cell 1 (`LB > 0` and `UB >= +5`):
- Report **positive mean gain across the 3 candidates (size relative to +5 unresolved unless `LB >= +5`)** — never call `LB > 0, UB >= +5` "at least +5".
- Because the pooled interval does not identify which of the 3 candidates is strongest, predeclare the selection step: take the candidate with the highest point estimate among the 3 and confirm it independently on a fresh seed at 250k (4,000 games, LB > 0) before promotion.
