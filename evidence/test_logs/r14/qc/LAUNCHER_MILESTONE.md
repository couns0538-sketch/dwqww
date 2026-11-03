# Launcher resource and descendant-capture candidate

Frozen 2026-11-03 13:20:52 Vienna. Independent review pending; not accepted.

## Confirmed defects and fixes

1. A post-child owned-storage-cap exception was caught as SOURCE_CHANGED, followed
   by another receipt write while the cap was refused. Resource handling is now
   separate: OWNED_STORAGE_CAP is retained, reported to stdout, and no receipt is
   allocated. The reserve is checked again immediately before receipt writing.
2. CopyToAsync.GetResult could wait indefinitely after the direct child exited
   while a descendant retained stdout/stderr handles. The setup regression showed
   a one-second timeout bypassed for 6.66 seconds.
3. Assigning only a waiting gate to a job did not prove payload membership on this
   host. A native diagnostic reported gate_in_job=True, payload_in_job=False. This
   intermediate implementation was rejected rather than relying on inheritance.

The final shared helper uses a named owned Windows job and a trusted waiting gate.
The gate creates each payload suspended, explicitly verifies/assigns its job
membership, then resumes it. Payloads cannot spawn descendants before assignment.
The supervisor terminates the owned job on refusal or completion, covering orphaned
pipe holders even after direct exit. Pipe drains have a five-second bound and never
call GetResult on unfinished tasks. The native diagnostic then reported both gate
and payload membership True, both exited on job closure, and captured stdout.

Only processes created through this owned gate are assigned or terminated. No
production process, queue, network or dataset was modified. The native helper is
original code; no external engine code was used.

## Retained validation

- launcher-cap-red01: two fixture-adapter failures before reaching the child;
  retained as an unsuccessful test harness attempt, not product defect evidence.
- launcher-cap-red02: two failures reproduce the real storage-cap misclassification
  and forbidden receipt allocation; three pre-existing tests passed.
- launcher-cap-green01: new cases were blocked by real CPU admission. No bypass.
- setup-pipe-red01: one failure and seven passes; captures the 6.66-second orphan
  pipe delay despite a one-second child timeout.
- setup-pipe-green01/02: intermediate gate-only job designs rejected by descendant
  and pipe-drain checks. They are retained and do not qualify the final helper.
- setup-pipe-green03: eight tests passed in 13.13 seconds, covering native success,
  failure, environment restoration, unset variables, guard/timeout cleanup of
  owned descendants, detached pipe holders, fixture gating and numeric reserves.
- launcher-cap-green02: five tests passed, including environment/argument quoting,
  genuine stdout/stderr capture and both storage-cap timing cases. The pipe case
  failed an overbroad total-wall threshold that included source hashing.
- launcher-cap-green03: five tests passed including the corrected direct-descendant
  lifetime check. The initial environment/quoting case was refused by real CPU
  admission (100% busy); its earlier pass is retained separately.

The corrected pipe test measures the descendant's lifetime from its monotonic
spawn marker, requiring termination within three seconds. It excludes source
hashing performed before and after payload execution. All behavior cases have
passed on the final wrapper implementation, but no all-six launcher suite is yet
claimed. A full stable, admitted suite remains for final validation.

No matching test gate or payload remained at the final process metadata inspection
(the inspection command itself matched its own search text). git diff --check
passed for the wrapper/helper/test scope. No fresh installation/network access or
production workload ran through this candidate.

## Frozen candidate MD5

| Full path | MD5 |
|---|---|
| D:/a14/tools/Invoke-R13.ps1 | 2e74bd68d752a47b5d65930ae08d412d |
| D:/a14/tools/Setup-R14Runtime.ps1 | ba70499c47cd026489a5a82948e7ecd9 |
| D:/a14/tools/R14-OwnedJob.ps1 | 278f38548f241dcd1c584e84ff81d2c6 |
| D:/a14/tools/R14-ChildGate.ps1 | 7f3cb2bcdad114af9ac7a3ffc71e4ba4 |
| D:/a14/tests/test_r14_launcher.py | 05f9092dd5b9120df88ffd784a4da629 |
| D:/a14/tests/test_r14_runtime_setup.py | b0bd4395040f7dd12f75d86bd4dc2943 |

| Full log path | MD5 |
|---|---|
| D:/a14/evidence/test_logs/r14/qc/setup-pipe-green03/output.log | 81bcb02c78e79a03c4e0630581997deb |
| D:/a14/evidence/test_logs/r14/qc/launcher-cap-green02/output.log | 05f7bacc3eb86f76ff003b4669841eb1 |
| D:/a14/evidence/test_logs/r14/qc/launcher-cap-green03/output.log | adc6e15cd48d7c56d17c8778a2b6b6a8 |
| D:/a14/evidence/test_logs/r14/qc/launcher-cap-red02/output.log | 2fa2c41d527c23a9b1baf4d8eb111a12 |
| D:/a14/evidence/test_logs/r14/qc/setup-pipe-red01/output.log | 58388514f439b92bd5b5d1059c525e6f |

Next: focused review of explicit native assignment, handle lifetime, argument
quoting, resource-failure identity, caller restoration and bounded capture; then
assess findings and rerun the full suite when fresh CPU admission permits.
