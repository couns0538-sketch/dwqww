# Runner selection and native identity fixes: validation queued

Recorded: 2026-11-03 15:06:05 Vienna. The parent authorized implementing confirmed
review findings after adding regression fixtures, while actual regression runs
remain queued behind active production scans. No test process ran for these
changes. The runner is still UNVERIFIED and the selected full suite has not run.

Confirmed review defects:

1. Inherited PYTEST_ADDOPTS and discovered configuration could silently reduce
   collection. Rootdir alone does not isolate configuration; python_functions
   can filter tests even without addopts.
2. The supervisor selected the old chain_native.exe rather than the accepted
   r03 executable and did not bind its identity before and after the tests.

Changes:

- Strip inherited PYTEST_* controls in the supervisor and worker, then force
  plugin autoload disabled. Pass -c to a pinned owned configuration containing
  only [pytest] and one newline. Record the configuration identity.
- Select chain_native_r03.exe, require MD5
  91427a99870d6b3775595db55f0a82e8, set the child native path explicitly and record
  its identity before and after supervision. The worker independently checks it.
- Require every selected file to contribute collected nodes, reject unexpected
  files/duplicate node IDs, and record deselections. Missing file coverage cannot
  be hidden by other passing tests.
- Add the accepted jobA tests. Keep boundary and ambiguity tests explicitly
  deferred pending independent acceptance; refresh that list after acceptance.

Regression fixtures were added before these changes. The real subprocess
fixtures now inject both -k test_pass and a nearby python_functions=test_pass
configuration while still requiring all six fixture cases. Pure cases cover
configuration tampering, changed native bytes and a missing selected file.
The subprocess fixtures also require the exact r03 identity in both supervisor
maps. No pure or subprocess regression result is claimed yet for this revision.

The pre-fix worker and supervisor were preserved under
D:\a14\evidence\test_logs\r14\suite-review-before-config for later genuine RED
reproduction. They are source snapshots, not production inputs or executable
training components. Future validation must distinguish actual reproduced RED,
passing GREEN, and CPU-admission refusal.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_suite.py | 682cb61a711a9ec84636caed7e76e2a9 |
| D:\a14\tools\Invoke-R14Suite.ps1 | b72b8fe3bca06d12f65caa21ed346862 |
| D:\a14\tools\r14_suite.ini | b9d12b7f4027e03000d178ccb2a49077 |
| D:\a14\tests\test_r14_suite.py | d223977476a26d68fb4dd2e8749b897a |
| D:\a14\evidence\test_logs\r14\suite-review-before-config\r14_suite.py | 22d946817e6c8dd563f285626555083e |
| D:\a14\evidence\test_logs\r14\suite-review-before-config\Invoke-R14Suite.ps1 | e242a33d1580220d05ac569413a0f66e |

The ambiguity helper, its tests and proof artifacts remain unchanged during
their independent review. No frozen overlap/parser/path-policy files were edited.
No commits were made by this task.
