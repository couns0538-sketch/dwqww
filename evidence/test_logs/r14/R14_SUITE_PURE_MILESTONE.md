# Runner pure-regression fixes

Recorded: 2026-11-03 14:38:46 Vienna. This supplements R14_SUITE_MILESTONE.md.
The overall runner remains UNVERIFIED pending its subprocess fixtures and review.
The selected full suite has not run.

The parent admitted only two short unit regressions while production jobs kept
CPUs 1 and 2. The reviewer held its test process during these checks; the slot
was released afterward. No subprocess fixture or native test ran here.

- RED suite-pure-red01: 2 failed, 7 deselected, 0.07 seconds. NPT_ADAPTER was not
  refused, and the post-run identity-error fixture recorded pytest exit 2 after
  the execution boundary had returned 0. CPU 3 admission was 46% busy.
- Fix: case-fold protected import names. Initialize the actual pytest result as
  null and change it only when pytest returns; later identity failures retain
  that returned result. The report remains UNVERIFIED on incomplete identity.
- GREEN suite-pure-green01: 2 passed, 7 deselected, 0.04 seconds. CPU 0 admission
  was 15% busy. Both processes were Idle and pinned to one CPU.

The red shell invocation returned zero through the inherited wrapper's outer
shell behavior; its retained pytest output explicitly records both failures.
The new evidence command now propagates the pytest exit and the green tool
invocation explicitly exits with it. No red test result is represented as a pass.

Only tools/r14_suite.py changed among runner candidates. The supervisor and test
file stayed stable. The previous NUL spelling fix, capture/deadline changes and
all subprocess behavior still await the coordinated full runner-fixture rerun.
No protected import, outside write, source-data read or production change ran.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_suite.py | 22d946817e6c8dd563f285626555083e |
| D:\a14\tools\Invoke-R14Suite.ps1 | e242a33d1580220d05ac569413a0f66e |
| D:\a14\tests\test_r14_suite.py | 26c952903c2a8143533e71b3f9d6359a |
| D:\a14\evidence\test_logs\r14\suite-pure-command.ps1 | d7e2de841113a0696df4c33af9e3a36a |
| D:\a14\evidence\test_logs\r14\suite-pure-red01\output.log | 596a5184028604c186fd9a53698e526c |
| D:\a14\evidence\test_logs\r14\suite-pure-green01\output.log | db0bd4ce8fc600becdabe8473e12aa44 |

Candidate frozen for text review. No commits were made by this task.
