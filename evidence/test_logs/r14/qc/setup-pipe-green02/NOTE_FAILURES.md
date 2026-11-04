# Why this log is named "green" but contains failures

Log: `D:\a14\evidence\test_logs\r14\qc\setup-pipe-green02\output.log` (md5 8574a631c043968cf6fa6c5fea5569ef, 3179 bytes; committed aa78a56 2026-11-04 09:24).
Summary line: `3 failed, 5 passed in 71.56s (0:01:11)`

Failed tests:
- `tests/test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[guard]`
- `tests/test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[timeout]`
- `tests/test_r14_runtime_setup.py::test_direct_exit_cannot_leave_descendant_holding_capture`

Why: Astra's as-found QC log (committed unchanged in aa78a56, 2026-11-04 09:24, from the 2026-11-03 run). Three failures: test_live_refusal_stops_only_owned_process_tree[guard] and [timeout] (the [guard] case is the known timing item F-006) and test_direct_exit_cannot_leave_descendant_holding_capture; not re-run or triaged by the R14 finish; the name "green" is Astra's. See full-suite-r14cont02 for the current outcome at the tip.

Written 2026-11-04 by Opus (R14 finish, owner's fix list item 4). The log itself is unchanged.
