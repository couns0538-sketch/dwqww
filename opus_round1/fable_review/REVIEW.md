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
eight files (the files stay on disk); the base's `.gitignore` already lists `__pycache__/` and `*.pyc`, so no
ignore rule was needed (two duplicate lines added at first were removed again after the independent check). No engine or tool source
changed; the engine head stays 064af732.

Status 2026-10-28: done on this branch (commit d118633a): the owner ran `git rm --cached` on the eight files in the review
worktree, the reviewer committed and pushed; `git ls-files | grep -c .pyc` = 0. The opus-* branches themselves are untouched.

## Second correction (2026-10-28, deep pass): the picker's deferred-capture buffer

The stack's `src/search/movepicker.hpp` still declared `bad_captures_` with 64 entries in both `#if` branches
(`UninitArray<Move, 64>` under FORGE_NOZERO_MOVE_BUFFERS, `std::array<Move, 64>` otherwise), the AL1 lock's size that
`fable-review-buffix` corrects on the lock base: a position with more than 64 SEE-losing noisy moves overruns it
(undefined behaviour; demonstrated there with `-D_GLIBCXX_ASSERTIONS`). Here both declarations use
`MoveList::Capacity` (256, the generator's capacity, so every noisy move can be deferred once) with a size
static_assert, and the regression test `tests/bad_capture_tests.cpp` (ctest `forge_bad_capture_tests`, six fixtures
including the 68-losing-move position) is added to CMake. No search logic changes: node-identical by construction.

Evidence (`opus_round1/fable_review/logs/`): box-recipe build `build_pc.log` (exe sha256 ecc930b9..., FMA count 0),
identity against the AL1 pins with every option off `identity.log` (ALL OK), the new test `bad_capture.log`,
and the full CMake build + ctest of the stack with R3-1's known-failure check `ctest.log` / `run_ctest.out`
(53 of 54 tests passed, the one failure is forge_tests' 4 known lines, known-failure check PASS); CI: opus-ci run
40698465776 (trigger commit e1c9aa6a, which only widens the workflow trigger to fable-* branches) success in
release / ASan+UBSan / TSan: identity ALL OK, 54 tests with only the known forge_tests lines in each job, TSan 0 reports.
