# QC candidate for review

Completed implementation: 2026-11-03 12:52 Vienna. Review pending; not accepted.

## Changes

- Production p5 audits require the exact approved source paths. Owned alternate
  sources need explicit fixture=True / --fixture; reports retain the fixture flag.
- Shared qc_core.DuplicateIndex uses exact keys in RAM only. It preserves legacy
  six-field report members and adds four-field and board-plus-side counts, overlap
  row counts and coverage. Empty or incomplete inputs never receive PASS.
- Failed parsing or resource admission remains visible after a caller catches an
  exception. Reports compute valid rows from actual stored keys, including partial
  insertion failure, instead of assuming every attempted row was stored.
- Copied run_policy writes only below D:/a14, enforces D:50 GiB and C:30 GiB floors,
  and blocks the underscore spelling of the protected training runtime.

## Validation

- red01: 9 failed, 1 passed; reproduces the original admission, duplicate reporting,
  disk-index, root, disk-floor and protected-runtime-path defects.
- green01: 10 passed after the initial fixes.
- red02: 1 failed, 11 passed; caught resource refusal could falsely preserve PASS.
- green02: 37 passed and 36 subtests passed after fixing exception accounting.
- red03: 1 failed, 13 passed; legacy overlap member lacked adjacent fill-rate data.
- green03: 39 passed and 36 subtests passed, zero failures, 0.46 seconds.
- git diff --check passed for changed QC code/tests.

Every run retains command.json, output.log and exit.json in its named directory.
Run-QcTests.ps1 invokes the independent interpreter at Idle priority and uses owned
temporary directories. No inherited datafilter conftest or training imports ran.

## Candidate MD5

| Full path | MD5 |
|---|---|
| D:/a14/tools/p5_qc.py | 238813dbdb7482ed066df489ed393af5 |
| D:/a14/tools/qc_core.py | a65abdb2bd8912f03cc859f0595dbadc |
| D:/a14/tools/run_policy.py | d124dae9782a7c791164182e7ddb4958 |
| D:/a14/tests/test_p5_audit.py | 4830d39513906db7e1b78e264104f9ae |
| D:/a14/tests/test_r14_qc_fixes.py | cc5b533b0fc4878bd119c1f83400747e |
| D:/a14/evidence/test_logs/r14/qc/Run-QcTests.ps1 | db0f7139cfc89d697f608093bb1ee7b1 |
| D:/a14/evidence/test_logs/r14/qc/green03/output.log | 961adf629b8a209f036d325abcfb4a0a |

## Limits and next action

This is the focused QC suite, not the inherited full-suite result or data clearance.
The separate inherited datafilter resource_policy module remains outside this
change and retains its historical contract. Large real-data memory qualification
has not been run. The RAM index aborts when observed free RAM is below 8 GiB or
owned process RSS exceeds 2 GiB at admission checkpoints.

Next: independent read-only review, assess all findings, fix confirmed defects,
rerun affected tests, and freeze the resulting candidate for the parent checkpoint.

## Review fixes

The reviewer identified three confirmed defects. All were reproduced in
review-red01 (4 failed, 14 passed) before fixes:

1. Aggregate status used only the six-field result. It now prioritizes any
   incomplete required key as UNVERIFIED, otherwise any key overlap as FAIL.
2. Rejected missing/empty cohort labels were absent from coverage accounting.
   Such unassigned rows now permanently make all cohort reports UNVERIFIED;
   fill rate is null because the true cohort denominator is unknown.
3. An invalid split was counted as a FEN parse failure. Routing failures and
   parsing failures now have distinct counters.

review-green01: 43 tests and 36 subtests passed, zero failures, 0.55 seconds.
No findings rejected. Candidate remains pending reviewer recheck.

Updated hashes superseding the table above:

| Full path | MD5 |
|---|---|
| D:/a14/tools/qc_core.py | 14626033310527bb9c5c61bf1123d6b3 |
| D:/a14/tests/test_r14_qc_fixes.py | d23179dda36b5825e3a4822884cb50c9 |
| D:/a14/evidence/test_logs/r14/qc/review-green01/output.log | 4c672693fdc8e55b82eb5d8248638211 |
