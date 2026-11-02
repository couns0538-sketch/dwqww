---
name: forge-lock-proof-set
description: Use when qualifying a Forge candidate against a frozen lock, checking two reproducible LTO+PGO builds, OFF pins and active ON behavior, perft, T1/T4 smoke tests, or executed ASan/UBSan results for a QA handover.
---

# Forge Lock Proof Set

Produce one run directory and a PASS/FAIL/UNVERIFIED table with original evidence. This qualifies a specific build contract, not Elo. Recover the latest accepted source/net and current pins; never promote a historical bench vector into a new lock.

## Prepare the actual native recipes

Read the current build script and test targets. Freeze source archive/commit, baseline binary, network, compiler and every adapter/script by SHA-256. Reuse reviewed build/perft/UCI/sanitizer tools; do not invent Forge options. Describe their actual argv and outputs in the [contract](references/contract.md). Native adapters must preserve original child logs and exit codes, emit the specified metrics, and use the exact passed result path. Review the adapter code: JSON claims alone do not prove execution.

Use two **new, independent** build directories. Each adapter must instrument/train/use its PGO profiles with LTO, record compiler commands/profile hashes and emit the final binary. Missing or mismatched profiles must be compiler errors, never a silent fallback. Keep source/net/flags/profile corpus identical, controlling timestamps, paths, random seeds and PGO nondeterminism. Equal bench counts do not replace byte-identical binaries. The helper currently validates GCC flag witnesses; qualify another compiler family with a separately reviewed adapter/checker change.

Executing the full set needs a host explicitly authorized for four worker threads. `grok-pc-safe-run` normally permits at most two and **cannot run the full set**. Never report T4 from a T2 invocation. If T4 cannot run, set only `stages.smoke_t4` to `{"skip_reason":"specific reason"}`. The runner records UNVERIFIED without launching T4 and continues independent sanitizer checks; overall qualification remains UNVERIFIED. This does not grant permission for extra threads or override the launcher. All other stages remain mandatory and an actual failed stage still stops later execution.

## Run once

```powershell
python.exe '<skill-folder>\scripts\run_proof_set.py' `
  'D:\forge-qa\lock-contract.json' --out 'D:\forge-qa\proof-new-001'
```

Choose an unused output directory; use the reviewed compiler-specific recipes. This command is for an approved qualification host, not permission to run on grok-pc. All inputs/recipes remain read-only. Output contains CONTRACT.json, REPORT.json, TABLE.md and per-stage command/stdout/stderr/exit/receipt evidence.

Required checks: build_a, build_b, reproducible_builds, off_pins, on_active, perft, smoke_t1, smoke_t4, asan_ubsan. OFF nodes on both candidate builds must equal the explicit current pins. ON must match the requested options and report a positive integer active counter. The default `identity_mode="behavior-changing"` requires ON to differ at at least one pinned depth. A reviewed exact-speed contract must explicitly set `identity_mode="exact"`; then ON must equal every supplied pin, including the same complete depth set. Unknown modes fail before execution. Neither mode relaxes option, binary, source or network binding. The standard ON receipt binds build_a; if the task requires ON on both builds, the reviewed adapter must execute and preserve the additional build_b evidence too.

Startpos perft5=4865609; canonical Kiwipete perft5=193690690. T1/T4 smoke means completed native legal searches with no crash, illegal move or time forfeit. ASan/UBSan must execute real tests in an instrumented binary; a successful compile or unsupported sanitizer startup is insufficient. Preserve known failures explicitly.

## Review and hand off

Confirm native adapters ran, examine the raw logs, source/network/binary/options binding and sanitizer coverage. The runner stops after a failed stage, retaining later checks as UNVERIFIED. Fixture tests only prove orchestration; `evidence_scope=fixture` must never be accepted by `gate-handover-pack`. Use that skill only after native PASS and independent review. No NPS or Elo claim follows from this proof set.

The R10 contract-mode regression suite is `scripts/test_contract_modes.py`; it runs synthetic adapters only and preserves its temporary evidence. Set TEMP/TMP to a new approved D: directory and disable Python bytecode before invoking it. Its PASS is not native qualification. The kit v2.3 uses fatal post-build profile-log validation rather than the runner's required GCC `-Werror` flags; that compatibility issue remains unresolved here and must not be hidden by fabricated compiler witnesses.
