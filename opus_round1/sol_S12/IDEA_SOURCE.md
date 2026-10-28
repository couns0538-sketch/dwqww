# IDEA_SOURCE — S12 (lazy NNUE accumulator; Job A cause; null-edge alias follow-up)

- **Job:** `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2, Sol's S12 (spec in his inventory on `17aa0cae`).
- **Job A cause study (`jobA_cause.py`):** reads Sol's own raw counter logs and his source on `17aa0cae` (read only);
  method and code are ours.
- **Null-edge alias (`followup_nullalias/`, added 2026-10-27):** Sol's idea and code, his patch
  `validation/forge_sol_pack31_20261025/forge_sol_S12_source_prepared_20261026/forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch`
  (sha256 `66efe4c9…`). His README addendum calls it an original Forge implementation with no code or tuned values
  from another engine. Its code hunks are applied unchanged; his README/IDEA_SOURCE hunks are not (they belong to
  his h256_e12 tree).
- **Tests:** `tests/forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp` is Sol's regression test from the
  same folder with one substitution (the PSQT oracle of AL1's `tests/runtime_psqt_tests.cpp` replaces a call to a
  private function). `tests/s12_lazyacc_extra_tests.cpp`, the CI script and the tools in `followup_nullalias/`
  are ours; `uci_check_opt.py`, `nps_ab_opts.py` and `uci_threads_session_s12.py` are copies from the S13 and
  S-IT jobs.
- No outside code; no Elo claim.
