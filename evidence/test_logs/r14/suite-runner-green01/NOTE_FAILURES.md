# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\suite-runner-green01\output.log` (md5 5121aa9278d16c8b03f164ff2238841c, 6829 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `3 failed, 5 passed in 15.25s`

Failed tests:
- `..\..\a14\tests\test_r14_suite.py::test_real_pytest_receipts_are_exact_and_fixture_scoped[False]`
- `..\..\a14\tests\test_r14_suite.py::test_real_pytest_receipts_are_exact_and_fixture_scoped[True]`
- `..\..\a14\tests\test_r14_suite.py::test_supervisor_stops_only_fixture_job_without_publishing[deadline]`

Why: Astra's as-found log of tests\test_r14_suite.py (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run). The owner's fix list assigns this folder to the known timing item F-006 (Idle one-CPU launcher timing). The review's own classification of the three failing tests is F-003: test_real_pytest_receipts_are_exact_and_fixture_scoped[False] expects passed=3/failed=1 from the runner fixture but pytest 9.2's built-in subtest accounting counts 2/2; [True] and test_supervisor_stops_only_fixture_job_without_publishing[deadline] refuse CPU admission when the CPU they pick (cpu_affinity()[0]) is busy. The runner stays UNVERIFIED (F-003); no suite-pass claim is made from it.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
