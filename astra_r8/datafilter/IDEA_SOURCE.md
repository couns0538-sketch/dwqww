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
312866/862329/3024920/12389307/34048354. The follow-up ran only a bounded native
UCI handshake on the exact FD3A5190 executable (no search, evaluation or bench).
These bench pins are supplied constraints rather than newly measured results.

The separate capture audit uses completed owned Forge gate PGNs under
`F:/forge_push/`: uhoT2_sf26b14, uhoSF26bit1_razor_e417_vs_AL1lp,
uhoE3a_evalmatscale12_vs_AL1lp, uhoE3b_evaloptimism40_vs_AL1lp and
uhoE3c_evalrule50damp30_vs_AL1lp. Their original RUN_INFO/RESULT receipts,
UHO opening provenance, entire source hashes and source-row identities are
retained in the new capture manifest. Only exact-baseline searched moves qualify;
no external corpus is imported and these positions are not training inputs.

Fastchess's local MIT-licensed source was inspected to establish that stored
bestmove/score/depth describe the position before the played move. No Fastchess
implementation was copied. `audit_capture_cohort.py` records source paths and
SHA256 values for match.cpp, pgn_builder.cpp, uci_engine.cpp and LICENSE under
`C:/Users/Administrator/grok-pc/tools/fastchess`. This source inspection does not
relicense other datasets or authorize copying GPL/AGPL implementations.
