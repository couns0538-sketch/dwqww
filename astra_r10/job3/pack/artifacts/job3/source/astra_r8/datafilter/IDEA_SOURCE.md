# Idea sources and licence boundary — UNPROVEN

Credit Code Review and Engine Coder for filtering proposals, and Engine NNUE for
result-aware training and the w4/s12 baseline recipe. Couns supplied the acceptance
criteria, execution limits and review/fix/verification policy.

The production converter at `C:/Users/Administrator/grok-pc/nnue/convert_forge.py`
and its two owned helpers were copied under the explicit task authorization.
Their exact original bytes and SHA256 values are preserved in `baseline/` and
`evidence/baseline_hashes.json`. These source files contain no licence notice;
we do not invent a permissive third-party licence for them or authorize external
redistribution. No third-party permissive implementation was copied.

Normalization, filtering, adapter, audit and tests in this directory are original
task code. The installed python-chess, NumPy, PyTorch and npt packages are called
through their APIs, not vendored. In particular, no GPL/AGPL npt, Stockfish,
binpack-tool or Leela/Lc0 implementation was copied into Forge. Native npt feature
extraction, model and loss remain in their separately installed environment.

Data used by the audit is owned Forge self-play text, closed shards 001 then 002.
Holdout sources are the complete owned shards 013 and 014, read only. No external
Lichess corpus is included: handling is demonstrated with authored synthetic
records and unknown outcomes. No Leela/Lc0 data is used; uncertain-licence data
is excluded. No claim is made that an arbitrary Lichess dump is licensed merely
because the parser can read it.

This work neither modifies nor qualifies FD3A5190. The task lock is OFF bench
312866/862329/3024920/12389307/34048354. No engine execution was needed, and these
pins are supplied constraints rather than newly measured results.
