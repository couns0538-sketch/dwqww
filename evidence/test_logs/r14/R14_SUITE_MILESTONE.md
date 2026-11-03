# Selected-suite runner candidate: UNVERIFIED

Recorded: 2026-11-03 14:20:00 Vienna. This is a work-in-progress review handoff,
not acceptance or a completed full-suite result. The selected suite has not run.

New files only: tools/r14_suite.py, tools/Invoke-R14Suite.ps1 and
tests/test_r14_suite.py. Existing overlap, scan, path-policy and shared process
control files were not edited. No commits were made by this task.

The Python worker selects an explicit R13/R14 allowlist, including chain-evidence,
group-map, segment, native, qualification and runner tests. It records the actual
pytest argument list, collected node IDs, phase outcomes, separate subtests,
selected-file MD5s before/after and Vienna times. Collect-only receipts are
distinct from executed-suite PASS. Fixture runs carry scope runner_fixture.
Protected imports and Python path mutations are fenced; that is not an OS
sandbox for arbitrary native programs.

The new supervisor reuses R14-OwnedJob.ps1 and R14-ChildGate.ps1 for suspended
assignment and owned-descendant cleanup. It pins its own small source set and
the interpreter instead of fingerprinting all tools while other authors work.
It admits one Idle CPU, monitors deadlines and D:/C:/owned-storage floors, and
uses capped output streams. Each output stream is capped at half the total log
budget. Pytest capture is disabled so ordinary stdout cannot grow an unbounded
capture file. Final REPORT.json publication occurs only after native exit,
bounded capture drain, source identity and resource checks; failed candidates
retain unpublished parts.

Completed test evidence:

- suite-runner-red01: 8 failures in 1.72 seconds. Python worker and supervisor
  did not exist; tests demonstrated the missing implementation. CPU 3, 3% busy,
  Idle and one CPU affinity.
- suite-runner-green01: 5 passed, 3 failed in 15.25 seconds. This was a prior
  candidate, not the current hashes below. One native fixture was refused by
  actual CPU admission; another encountered pytest's canonical NUL path spelling,
  which the literal-only sink rule rejected. The deadline fixture hit its small
  log cap on that same traceback. The log-cap fixture and four unit cases passed.
  CPU 1, 0% admission sample, Idle and one CPU affinity.
- No matching owned suite/gate fixture process remained at the final read-only
  process metadata check. No production workload or protected import was run.

Subsequent changes awaiting tests: allow exactly os.devnull and its OS-canonical
absolute spelling; retain CPU admission diagnostics in a missing-report
assertion; enforce the deadline through capture completion. These changes are
not yet validated.

Known pending defects with newly added regression cases, not yet run:

1. Windows case variants of protected import names currently bypass the
   case-sensitive module-name check. Test cases now include NPT_ADAPTER and
   MODEL.nnue. Run the focused RED before the minimal fix.
2. A post-run selected-file identity exception currently overwrites the actual
   pytest exit code with 2. The new test stubs only the pytest execution boundary
   and injects a subsequent identity error; it requires retention of the actual
   returned exit code alongside UNVERIFIED. Run this RED before fixing.

Boundary fixture checks dispatch real audit events without attempting an outside
filesystem write or protected file read. The exact OS NUL sink is exercised as
an actual sink. The broader suite and production helper are not launched by the
runner's tiny fixture tests.

Scheduling: both computation slots are occupied by production scans. The parent
explicitly queued further test processes until one slot is released. Source is
stable for text review in the meantime. Next action: run the two focused RED
cases, fix confirmed defects, run all runner fixtures in the coordinated slot,
then independent recheck. The full selected suite remains a later coordinated
task. Add accepted tool identities to TOOLS.md after qualification.

Review limitations: the selected tests and runner/helper/interpreter sources are
identified; the worker does not claim that every imported dependency is frozen.
The full native candidate and other code-under-test identities must also remain
bound to the parent task's accepted candidate when the final suite is executed.
This runner must never be described as the inherited complete repository suite.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_suite.py | 121b1d8f13f5d82cdea89329539ee1d2 |
| D:\a14\tools\Invoke-R14Suite.ps1 | e242a33d1580220d05ac569413a0f66e |
| D:\a14\tests\test_r14_suite.py | 26c952903c2a8143533e71b3f9d6359a |
| D:\a14\evidence\test_logs\r14\suite-runner-command.ps1 | b0dd1fd9f62e730d5c8c980580e56aa3 |
| D:\a14\evidence\test_logs\r14\suite-runner-red01\output.log | d07bbaaabb80337390db7e9178b9a856 |
| D:\a14\evidence\test_logs\r14\suite-runner-green01\output.log | 5121aa9278d16c8b03f164ff2238841c |
