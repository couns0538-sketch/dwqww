# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\preflight-green01\output.log` (md5 439c5f5c8300af7628e4bcf00dd16d7a, 1716 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `1 failed, 3 passed in 10.35s`

Failed tests:
- `..\..\a14\tests\test_r14_preflight.py::test_observation_has_monotonic_clock_on_ps51`

Why: Astra's as-found log (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run). The one failure, test_observation_has_monotonic_clock_on_ps51, is an environment check of the PowerShell 5.1 observation path; it was not re-run or triaged by the R14 finish and the name "green" is Astra's. See the final R14-scope run at the tip (full-suite-r14cont02) for the current outcome of this test.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
