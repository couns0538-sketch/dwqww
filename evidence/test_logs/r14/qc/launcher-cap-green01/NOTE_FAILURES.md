# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\qc\launcher-cap-green01\output.log` (md5 a735e9bf0157ec8e037e137fd441fd4d, 6852 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `2 failed, 3 passed in 6.38s`

Failed tests:
- `tests/test_r14_launcher.py::test_owned_cap_after_child_never_allocates_receipt[during]`
- `tests/test_r14_launcher.py::test_owned_cap_after_child_never_allocates_receipt[after]`

Why: Astra's as-found QC log (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run). Two failures of tests\test_r14_launcher.py::test_owned_cap_after_child_never_allocates_receipt[during]/[after]; not re-run or triaged by the R14 finish; the name "green" is Astra's. See full-suite-r14cont02 for the current outcome of these tests at the tip.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
