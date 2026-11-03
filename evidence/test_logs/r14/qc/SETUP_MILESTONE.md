# Runtime setup candidate for review

Completed 2026-11-03 13:00:23 Vienna. Independent review pending; not accepted.

## Changes

- Child-only environment for native installation/download programs. Snapshot and
  restore caller environment and priority in finally, including absent variables.
- PowerShell 7 requirement is explicit. It permits killing only the newly owned
  process and its descendants when the live guard or timeout refuses continuation.
- Every child inherits Idle priority and one-thread CPU settings, hidden GPUs,
  owned temporary/cache paths, and disabled user package/config discovery.
- D:50 GiB, C:30 GiB and owned-storage <5,000,000,000 bytes checked before phases,
  with expected allocation reserves, and every child-monitor cycle. Tree counting
  does not follow reparse entries. No source datasets are copied.
- Downloads and pip children have timeout/capture/error propagation. Exact known
  MD5s pin the embedded archive, bootstrap and interpreter; installed packages use
  tools/requirements-r14.txt with no unpinned dependency resolution.
- Explicit fixture entrypoint runs an owned Python probe through the same guarded
  child launcher. Fixture-only resource failure injection can tighten admission,
  never bypass the real guards or invoke installation without the explicit switch.

## Evidence

- setup-red01: two failures reproduce caller environment/priority leakage on both
  native success and native failure. Baseline fixture redirects paths into its own
  temporary root and replaces pip invocations with a native Python probe; it never
  installs packages or accesses the network.
- setup-green01: both initial regression cases passed.
- setup-green02 and setup-red02: absent variables were wrongly restored as empty
  variables; one failed and six passed in each retained run.
- setup-green03: seven tests passed, zero failures, 5.76 seconds. Checks caller
  success/failure restoration, unset values, Idle native child priority, resource-
  refusal and timeout termination of owned descendants, explicit fixture gating,
  numeric disk-floor boundaries and the owned-storage cap.
- git diff --check passed. No actual runtime reinstallation was performed.

| Full path | MD5 |
|---|---|
| D:/a14/tools/Setup-R14Runtime.ps1 | d61f0cf6409ae7747f33afa1e095ead3 |
| D:/a14/tests/test_r14_runtime_setup.py | afe00e5baf16d562530784603391b9cf |
| D:/a14/evidence/test_logs/r14/qc/setup-green03/output.log | 85b3add9dd115592b6f10bd05aee043c |

The setup script and its tests are now stable for read-only review. Existing
successful installation evidence remains the runtime receipt; mocked installation
tests do not claim a fresh production installation or whole-environment proof.
