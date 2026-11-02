---
name: gate-handover-pack
description: Use when preparing a Forge candidate for QA gate handover, packaging binaries and original proof evidence, generating MD5SUMS and gate instructions, or checking proposed start/srand values against fresh crew-provided gate snapshots. Not for editing or launching a live gate queue.
---

# Gate Handover Pack

Deliver a new self-contained pack that QA can review without reconstructing the experiment. Preserve exact source/build/net/option identity and original logs. Packaging is not authority to queue a gate or accept an Elo claim.

## Required inputs

Read the active gate specification and accepted lock. Reuse `forge-lock-proof-set` for a native PASS proof; all nine checks must pass. Fixture results, absent ASan/UBSan, stale pins or another source revision block a handover. Read `grok-pc-safe-run` before any PC execution. This workflow writes only its own new approved D: folder and never opens live `queue.txt`, `queue_state.json`, NPT directories, or another process.

Freeze baseline/candidate binaries, net, source manifest, original build/bench/test logs, lock contract and gate protocol. Record full commit SHAs, compiler/flags and explicit OFF/ON UCI options. Every file needs SHA-256; MD5 is a compatibility manifest, not a security substitute. Include every proof-referenced log, preserving its relative path.

Obtain trusted **copies** of the complete relevant active/archived gate inventory from the crew's approved export route. Require original coverage label, capture UTC, SHA-256 and copy mtime. Do not manufacture a "fresh" timestamp for an older copy. Normalize the known native inventory format into the documented JSON only after verifying no records were lost; keep the original export as an artifact. The helper deliberately does not guess the gate PC's evolving queue format.

## Build and verify

1. Choose proposed start and srand according to the current gate specification. Scan every nominated inventory row; reject reuse of either value. Missing fields or incomplete coverage block the handoff. A copied inventory can become stale after capture: QA must recheck live availability before enqueueing.
2. Prepare a request using [the exact format](references/request-format.md). Require native proof scope, matching revisions/contract, exact tested binary/net hashes and OFF/ON settings, all required PASS rows and their original evidence. Freeze the protocol with the same gate name, start, srand, time control, threads and hash settings.
3. Invoke the helper as an approved worker through `grok-pc-safe-run`, using explicit Python, request and a **new** output directory:

```powershell
& $Python (Join-Path $SkillRoot 'scripts\make_gate_pack.py') $Request --out $NewPack
if ($LASTEXITCODE -ne 0) { throw 'Gate pack blocked; preserve the failure and inputs.' }
```

4. Independently verify MD5SUMS and SHA256SUMS. Review README.md, GATE.md, REQUEST.json, SCAN.json, original logs and source manifests. A partial directory without both completed manifests is not a delivered pack; retain it and select a new output name for another attempt.
5. Save/push to the authorized candidate branch or artifact destination and read back its bytes. Give QA the source SHA, pack SHA-256, scan UTC/coverage, proof result, exact protocol and remaining limitations. Do not update a live queue, notify crew, create STOP/PAUSE files or change other processes without the task's separate authority.

The helper's `READY_FOR_QA_REVIEW` means supplied evidence and snapshot fields were consistent. It does not rerun native tests, establish real-time seed availability or prove the declared source/build provenance. Never relabel that status as live queue clearance.

## R10 evidence-only and data-tool copies

The original strict `make_gate_pack.py` and its gate-readiness contract are unchanged.
When native engine qualification is incomplete, preserve the explicit artifacts
with `scripts/seal_evidence.py --purpose incomplete-engine`; the resulting status
is `SEALED_INCOMPLETE`, always UNPROVEN. This is an evidence handoff, not an engine
gate pack. Record every blocker; do not invent a seed inventory or a PASS proof.

For a data-tool handover, use `--purpose data-tool`. This requires bound actual-
adapter audit/replay PASS reports, complete holdout identities, zero missing IDs,
and independent resumed outputs at all three fault points. Otherwise it blocks
before output creation. Status `SEALED_DATA_TOOL` still grants no training or gate
clearance. The supplied native evidence must be reviewed separately.

When a data-tool handover has unresolved qualification, use the explicit
`--purpose incomplete-data` instead. It still requires exactly one tool, sample,
training command, audit report and replay report, plus nonempty blockers. Audit
or replay status may be PASS, FAIL, UNVERIFIED or BLOCKED; preserve the original
status and list every missing or failed requirement. It always produces
`SEALED_INCOMPLETE`, UNPROVEN, with training clearance BLOCKED. A missing-ID audit
cannot be upgraded by this route. Include a guarded training command that refuses
execution until the missing clearance is supplied. The strict `data-tool` path
and engine gate-readiness requirements remain unchanged.

Read [the evidence-only contract](references/evidence-sealing.md). Run through the
safety launcher with `--threads 1`, the complete protected roots, a fresh output
directory, and all reads/writes declared. Only D:\a10 I/O is accepted. Existing
attempts are never reused or overwritten. Regression fixtures belong to
astra_r10/job1/pack-tests and do not qualify any native data.

## R11 blocked provenance handoff

R11 writes only under D:\a11; never execute the R10 path-pinned sealer unchanged.
If authentic source-game maps or safe CPU admission are missing, a small
SEALED_BLOCKED_EVIDENCE bundle may contain the recovery ledger, inherited input
identities, current metadata observations, unexecuted tooling/tests and exact
resume commands. Include an explicit artifact inventory and independently
verify MD5 and SHA256 for every listed file. Record the checksum-manifest hash
outside the bundle to avoid circular identities. Do not include live data,
weights or queue files. Keep the R10 sealed pack unchanged.

This evidence bundle is NOT the requested qualified data pack. It must state
that full current hashes, row scans, regression runs and overlap proofs are
unrun wherever admission prevented them. Historical counts must be labelled
inherited; unknown game counts and overlap are null, not zero. Never claim
SEALED_DATA_TOOL, training clearance, all-tests-pass or completed R11 based on
this fallback. A checksum PASS certifies only the listed evidence bytes.