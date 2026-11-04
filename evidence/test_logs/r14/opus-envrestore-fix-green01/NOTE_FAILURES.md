# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\opus-envrestore-fix-green01\output.log` (md5 65cc78a98dc11d88d53bbd262ba9a0f7, 1880 bytes; committed de1a1cd 2026-11-04 11:01).
Summary line: `1 failed, 7 passed in 18.10s`

Failed tests:
- `tests/test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[guard]`

Why: Run of tests\test_r14_runtime_setup.py after the F-001 fix (commit de1a1cd, 2026-11-04 11:01). The 7 passed include test_unset_caller_environment_is_restored (the F-001 regression test, the point of the run). The one failure is the known timing item F-006: test_live_refusal_stops_only_owned_process_tree[guard] under the Idle one-CPU launcher (the guard fires after one 500 ms poll before the probe child wrote child.json; parent.json shows the correct refusal and the restored environment). "green" refers to the F-001 test; the folder is kept under its name because this job renames and deletes nothing.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
