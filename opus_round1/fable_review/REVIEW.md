# fable-review-r3-stack — corrections to the R3 integration head

Base: `opus-r3-stack` head da158149 (final engine head 064af732). Nothing on the opus branches is modified; this
branch carries the corrections found by the Fable review (`FABLE_REVIEW_OPUS.md` on `fable-review-summary`).

## Correction 1: committed Python bytecode

Eight `__pycache__/*.pyc` files were committed on the R3 stack (ctest and the job tools ran with the system Python
inside the source tree): `opus_round1/O1/__pycache__/ucilib.cpython-314.pyc`,
`opus_round1/O2/__pycache__/mutation_check.cpython-314.pyc`, `opus_round1/sol_S12/__pycache__/jobA_cause.cpython-314.pyc`,
`opus_round1/sol_S12/followup_nullalias/__pycache__/mutation_check_alias.cpython-314.pyc`,
`tools/__pycache__/uci_regression.cpython-314.pyc`, `tools/match/__pycache__/{pgn_stats,run_match,windows_validate}.cpython-314.pyc`.
They are build products of one Python version and do not belong in the repository. Fix: `git rm --cached` of the
eight files (the files stay on disk) and `__pycache__/`, `*.pyc` appended to `.gitignore`. No engine or tool source
changed; the engine head stays 064af732.
