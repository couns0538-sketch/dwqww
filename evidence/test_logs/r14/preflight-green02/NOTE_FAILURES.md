# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\preflight-green02\output.log` (md5 3600cf603222f5ed96c562951065d1f0, 2882 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `1 failed, 3 passed in 5.76s`

Failed tests:
- `..\..\a14\tests\test_r14_launcher.py::test_child_environment_and_parent_preserved`

Why: Astra's as-found log (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run, recorded with the CPU 94 % busy). The one failure, tests\test_r14_launcher.py::test_child_environment_and_parent_preserved, is a launcher timing/environment case; not re-run or triaged by the R14 finish; the name "green" is Astra's. See the final R14-scope run at the tip (full-suite-r14cont02) for the current outcome.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
