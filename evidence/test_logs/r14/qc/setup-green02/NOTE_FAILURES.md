# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\qc\setup-green02\output.log` (md5 52f133420efae5d02d56953aa80df703, 1300 bytes; committed 714000d 2026-11-03 13:45).
Summary line: `1 failed, 6 passed in 5.91s`

Failed tests:
- `tests/test_r14_runtime_setup.py::test_unset_caller_environment_is_restored`

Why: Astra's as-found QC log (committed in 714000d, 2026-11-03 13:45). One failure: tests\test_r14_runtime_setup.py::test_unset_caller_environment_is_restored - this is the F-001 defect (unset caller variables restored as ""), fixed in de1a1cd on 2026-11-04; the fixed test passes in opus-envrestore-fix-green01 and in the final run.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
