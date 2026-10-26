# S13 source-only handoff — 2026-10-26

Use the dated six-file patch; it adds one opt-in child-TT-prefetch feature. Existing prefetch and bucket-size assertions are retained. Read the source report and native preregistration before execution.

- `forge_sol_S13_source_contract_20261026.py` and `forge_sol_S13_source_tests_20261026.py`: pure source/negative-control checks. Set FORGE_S13_TEST_BASE and FORGE_S13_TEST_CANDIDATE to complete matching source views, then run tests with `python -B`. Ten methods pass locally.
- `forge_sol_S13_apply_matrix_20261026.py`: private-copy source-only application/inventory checks; its result and raw output already exist. It intentionally refuses overwrites. Canonical sources are read-only; no Git refs/index are changed.
- `forge_sol_S13_worker_prefetch_probe_20261026.cpp`: deferred diagnostic, not a measured native result. The exact compile/link recipe is preregistered.
- Before-review checker/matrix source and failed raw captures are history, not alternative workflows to run.

Private complete source views are outside this packet and excluded from its manifest. No full engine source archive, ELF, ZIP, LICENSE, AGENTS or .agents files are delivered. No source is merged, and no speed/Elo improvement is established. Root owns Git publication.
