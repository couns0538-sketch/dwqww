# IDEA_SOURCE (S15 SPSA harness v2)

IDEA_SOURCE: SPSA, simultaneous perturbation stochastic approximation (J. C. Spall, "Multivariate stochastic
approximation using a simultaneous perturbation gradient approximation", IEEE Trans. Automatic Control 37(3), 1992;
gain-sequence practice from Spall, "Implementation of the simultaneous perturbation algorithm for stochastic
optimization", IEEE Trans. Aerospace and Electronic Systems 34(3), 1998). Ideas only; the code is original.

- Base: Sol's prepared v1 `forge_sol_S15_spsa_20261027.py` (sha256 `5f1f59785f9272a33ad71d6081e02697c10a77d8d7f68dec0b97dbe8693972f6`)
  and his 13 tests (sha256 `d0eb749f23800712e279e1a9d4444de2fd8ffe26e718afdfcdc76a6ed14e5043`), branch
  `forge/sol-pack31-20261025` @ `17aa0cae`, folder `validation/forge_sol_pack31_20261025/forge_sol_S15_source_prepared_20261027`.
  His normalized two-sided integer probes, projected update and synthetic demo are kept unchanged.
- Parameter names, defaults and ranges: Forge's own `tune::` registry in the AL1 lock `src/search.cpp` (read, not changed).
- Paired-opening conventions (sha256 opening order, reversed colours, restart per game, independent pentanomial
  cross-check against fastchess's report): Forge's own `tools/match/run_match.py`; PGN bookkeeping: Forge's own
  `tools/match/pgn_stats.py` (imported, sha256-pinned, not modified).
- Fastchess (MIT, Disservin) is an external process driven through its documented command line; no code copied.
- No other engine's code, tuned values or tables were used.
