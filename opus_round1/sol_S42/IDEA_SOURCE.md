# IDEA_SOURCE (S42 higher-variance opening book study)

IDEA_SOURCE: a slightly unbalanced opening book (exits at about |eval| 0.6-1.2, both colours per pair) to cut
games-to-decision in SPRT gates, as specified in Sol's S42 task (`forge_sol_all_jobs_inventory_20261026.json`, job S42,
spec line 222). Ideas only; no engine code changes, no outside engine evaluations.

- Unbalanced test books in general: the public practice of engine testing frameworks that moved to "unbalanced human
  openings" books (idea only; no such book or its evaluations is used here, every eval comes from OUR AL1 lock exe).
- Game-outcome model: an ordered-logistic win/draw/loss model with a draw width, in the style of Coulom's BayesElo (idea).
- Power estimates: Sol's S33 planner and its S06 statistics dependency, copied unchanged from `17aa0cae`
  (`sol_S33/`, sha256-pinned), with Sol's frozen six-cell validation receipt.
- SciPy shim (`scipy_shim/`): `brentq` follows Brent's method as written in SciPy's C `brentq` (BSD-3-Clause), re-typed in
  Python so roots agree to the last bit; the Gauss-Kronrod 7/15 nodes and weights are the standard published tables
  (QUADPACK `qk15`); `logsumexp` and `log_ndtr` are textbook stable forms. No SciPy file is copied.
- Data: the gate book `8moves_v3.pgn` (sha256 `5835239f…`, the G119 book), the G119 PGN and RESULT (read-only copies).
- python-chess (GPL-3.0) and numpy (BSD) from the PC's read-only NNUE venv, as libraries.
