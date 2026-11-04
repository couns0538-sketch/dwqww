# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\output.log` (md5 05f7bacc3eb86f76ff003b4669841eb1, 1974 bytes; committed 714000d 2026-11-03 13:45).
Summary line: `1 failed, 5 passed in 22.62s`

Failed tests:
- `tests/test_r14_launcher.py::test_exited_child_cannot_leave_descendant_holding_pipes`

Why: Astra's as-found QC log (committed in 714000d, 2026-11-03 13:45). One failure: tests\test_r14_launcher.py::test_exited_child_cannot_leave_descendant_holding_pipes; not re-run or triaged by the R14 finish; the name "green" is Astra's. See full-suite-r14cont02 for the current outcome at the tip.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
