# Runtime inventory containment fix

Recorded: 2026-11-03 13:38:07 Vienna.

Scope: `D:\a14\tools\r14_overlap.py` and
`D:\a14\tests\test_r14_overlap.py`. No global path-policy or parser changes.
No production data scan was launched by this task.

Confirmed finding: a caller-supplied runtime root was checked only for safe
reading. That permitted the special installed dependency marker exception to
apply outside the owned root. Production CLI callers used the fixed owned
runtime, but the helper did not enforce its claimed boundary.

Fix: `verify_runtime` now checks its runtime root with
`safe_path(runtime_root, write=True)` before inventory access. This flag applies
owned-root containment; the verifier still performs read-only hashing. The
exact dependency marker exception, parent/leaf reparse checks, pinned inventory
and complete file-set comparison are unchanged. All neighboring locks continue
through the unchanged global refusal policy.

Regression evidence:

- `runtime-containment-red02`: 2 failed and 32 passed in 0.40 seconds. The
  external-marker fixture was accepted, and the external-root case reached the
  inventory read instead of refusing the root. The fixture temporarily narrows
  the owned-root policy to an owned temporary subdirectory, so the otherwise
  external marker is also physically below D:\a14.
- `runtime-containment-green01`: all 34 overlap/parser tests passed in 0.16
  seconds. Coverage includes early external-root refusal, the narrowed-boundary
  marker reproduction, both neighboring-lock spellings and the previously
  allowed exact marker.
- Both actual runs used CPU 2, Idle priority and one CPU affinity. Admission
  samples were 33% and 4% busy. Several earlier CPU samples refused admission;
  no tests launched on those attempts.
- `runtime-containment-red01` is a harness error, not regression evidence:
  enabling the inherited audit fence rejected pytest's default log sink before
  collection. The command was corrected to use the existing quick-fixture
  runner configuration, retaining all temporary output below D:\a14 and all
  CPU, disk and owned-storage admission checks.

The command runs only the explicit overlap and parser test files; no inherited
datafilter test collection or protected training imports were used. A complete
project regression and independent review remain the parent's responsibility.
Self-review checked the only production caller and both runtime-path callers;
all runtime marker access from verification follows the new owned-root check.
The candidate is frozen for focused independent recheck before a full scan.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_overlap.py | f1b30456ab2ea68799e09805d05ccc74 |
| D:\a14\tests\test_r14_overlap.py | af8e0701e8d4b22e68e6d506c202d66a |
| D:\a14\tools\run_policy.py | d124dae9782a7c791164182e7ddb4958 |
| D:\a14\tools\r14_scan.py | c5d56b1ee5de5db65f64d1ba14dbd7ca |
| D:\a14\evidence\test_logs\r14\runtime-containment-command.ps1 | a9e33aede7d62a220313a17167493b54 |
| D:\a14\evidence\test_logs\r14\runtime-containment-red01\output.log | bcf11b898d79f573438d83ea157911f3 |
| D:\a14\evidence\test_logs\r14\runtime-containment-red02\output.log | e401e76e4e0c6c1ba2956515089d4af4 |
| D:\a14\evidence\test_logs\r14\runtime-containment-green01\output.log | d42c28ea560d5db8840ac4014ae03d76 |

Final free-space sample: D: 61,520,334,848 bytes; C: 134,545,137,664 bytes.
No commits were made by this task.
