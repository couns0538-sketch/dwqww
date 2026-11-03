# Overlap report publication fix

Recorded: 2026-11-03 13:41:17 Vienna.

Scope: `D:\a14\tools\r14_overlap.py` and
`D:\a14\tests\test_r14_overlap.py`. The runtime containment fix remains in
place. No global policy, parser, production data or other processes were changed.

Confirmed review finding: direct writing to REPORT.json could leave a complete
PASS document at the published path even when flush, synchronization or close
failed. Only the returned in-memory result was downgraded to UNVERIFIED.

The regression uses real owned temporary files and narrowly injects write,
flush, fsync and context-close failures. The close fixture closes the real file
and then raises OSError, deterministically reproducing the final-path defect.
The retained red close fixture at
`D:\a14\evidence\test_logs\r14\overlap-publication-red01\tmp\test_failed_publication_leaves3\report\REPORT.json`
contains status PASS and complete true. The returned result was UNVERIFIED.
The write-failure fixture retained incomplete JSON; the flush and fsync fixtures
also retained complete PASS documents at the final path.

Fix: refuse an existing final report, write exclusively to REPORT.json.part,
flush and fsync, finish closing the stream, perform a fresh 1 MiB publication
resource admission, recheck output path safety and rename to REPORT.json.
Windows rename refuses replacement of an existing destination. A failure
preserves the unpublished part, returns UNVERIFIED with publication REFUSED,
and emits that refusal to stdout. A part is never a published audit result.

Validation:

- RED `overlap-publication-red01`: 6 failed, 35 passed in 0.27 seconds. All four
  stream-failure cases demonstrated published-file retention; post-close storage
  refusal and rename-failure cases demonstrated the absent publication stages.
- GREEN `overlap-publication-green01`: 42 passed in 0.19 seconds. Added successful
  sealing and existing-final preservation checks alongside the six failures.
- Runs used CPU 1 at 12% busy and CPU 0 at 22% busy respectively, both Idle and
  one-CPU affinity. CPU 3 was excluded. All fixtures and temporary files stayed
  below D:\a14, with disk and owned-storage admission before each short run.
- Scope was the overlap and parser tests only. The full project regression
  remains a later parent task. No protected test collection or imports ran.

Self-review checked exception paths, exclusive partial creation, close ordering,
second storage admission and preservation of existing final files. Candidate
files are frozen for focused independent recheck before expensive execution.
This record does not declare that independent review complete.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_overlap.py | 812fbbbcccbc05ed20f74456bf1ddc80 |
| D:\a14\tests\test_r14_overlap.py | b4888c52eef4ec4a9e9adb48b34adf2f |
| D:\a14\tools\run_policy.py | d124dae9782a7c791164182e7ddb4958 |
| D:\a14\evidence\test_logs\r14\overlap-publication-command.ps1 | e13f065d06ee1c398480bb0162ad4c1a |
| D:\a14\evidence\test_logs\r14\overlap-publication-red01\output.log | dead6f7b2f3a445214ef71bc90d58685 |
| D:\a14\evidence\test_logs\r14\overlap-publication-green01\output.log | 685ff1ac0572f8562cc75ea6f74b958e |

Final free-space sample: D: 61,519,527,936 bytes; C: 136,912,216,064 bytes.
No commits were made by this task.
