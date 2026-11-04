# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\qc\setup-pipe-green01\output.log` (md5 7aa58c49082bbd024f3a7bf184e3ed64, 1295 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `1 failed, 7 passed in 10.57s`

Failed tests:
- `tests/test_r14_runtime_setup.py::test_direct_exit_cannot_leave_descendant_holding_capture`

Why: Astra's as-found QC log (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run). One failure: tests\test_r14_runtime_setup.py::test_direct_exit_cannot_leave_descendant_holding_capture; not re-run or triaged by the R14 finish; the name "green" is Astra's. See full-suite-r14cont02 for the current outcome at the tip.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
