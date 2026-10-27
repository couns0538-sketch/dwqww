"""Minimal numpy/math-only stand-in for the four SciPy functions Sol's S33 planner imports (Opus 5.5, 2026-10-27).

The PC's read-only NNUE venv has numpy but no SciPy, and nothing may be installed into it. Sol's planner
(`forge_sol_S33_sprt_planner_20261026.py`, sha256 008819d5...) is used UNCHANGED; only these imports are satisfied:
  scipy.special.logsumexp, scipy.special.log_ndtr, scipy.optimize.brentq, scipy.integrate.quad
`brentq` transcribes SciPy's C algorithm (Zeros/brentq.c) step by step, so roots agree to the last bit for the same
function values. `logsumexp` and `log_ndtr` use the standard stable forms. `quad` is an adaptive Gauss-Kronrod
(7/15) integrator: same tolerances, not QUADPACK's subdivision. Validation against Sol's frozen six-cell receipt is in
`check_scipy_shim_s42.py` (MC counts must be identical; analytic values agree to the printed tolerance).
"""
SHIM = "opus-s42-scipy-shim-1"
