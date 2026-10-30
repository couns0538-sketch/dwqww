# Independent QA review, 2026-10-30

Review began 10:31:38 UTC. Read-only scope: converter disk/index ownership and resume handling; HIP launcher fail-closed paths, build/run identity and validation claims. No production PC access, native Windows execution, GPU work or worktree edits were performed. Repro/tests/logs are retained outside both worktrees in this directory.

## Findings and resolution

1. **P2, corrected:** A hard-coded `target/release/train_smoke.exe` could run an old binary when Cargo inherited `CARGO_BUILD_TARGET` or global `build.target`. Latest `Get-HipBuildPlan` explicitly passes `--target x86_64-pc-windows-msvc` and uses that target's matching executable path. Source review confirms the prior path mismatch is removed. Runtime remains unverified.
2. **P3, corrected:** Low disk space after training was evaluated during native phase and returned exit 1 despite documented exit 76. Latest source sets preflight phase around this guard. Runtime remains unverified.
3. **P2, corrected:** Converter budget assumed 256 game-ID characters occupied 256 bytes. A real 256-emoji fixture used 1024 UTF-8 bytes; retained output was 1127 B while its estimate was 388 B. `utf8_budget.log` preserves the original repro. Current source budgets the entire game-ID file byte size, and the independent regression confirms retained output now fits the budget. The implementer also added a native probe-log allowance.

## Independent verification

`test_converter_independent.py` passed **9/9** on the final reviewed converter source; `converter_independent_final.log` contains the run. The source hash was identical immediately before and after execution (the two `final_converter_source_*.sha256` receipts).

Checks cover:
- Separate-process output-lock contention is refused.
- Mismatched index ownership refuses pruning.
- An index hardlinked to source is preserved and refused.
- An explicitly protected source path cannot be pruned.
- Valid resume removes owned indexes while preserving native logs and unsealed data.
- Low disk during row processing aborts at the 1024-row guard.
- Low disk during reconstruction of 1024 unique retained keys aborts before remaining work.
- A failed native encoder preserves partial evidence and does not publish COMPLETE.
- UTF-8 game-ID storage fits the corrected output budget.

The separate PowerShell reviewer passed **2/2 portable documentation tests** (hip/documentation-test.log). These test documentation/source text, not PowerShell behavior. Windows-specific behavioral tests are supplied but were not executed because neither Windows PowerShell nor pwsh is available. GPU telemetry/process checks, native stream/quoting behavior, Idle and CPU affinity inheritance, and actual refusal exit traces therefore remain UNVERIFIED. The source uses separate Process stdout/stderr streams rather than PowerShell native `2>&1` conversion. The launcher rechecks the scheduled free slot after compilation and before launching the trainer.

No further concrete defect was found in the reviewed converter ownership/resume/disk scope after corrections. `reviewed_source_hashes.json` identifies the reviewed files. This is a scoped source and Linux regression review, not training clearance; real complete 013/014 data and zero-overlap clearance remain unavailable and unverified here. Root independently owns audit/licence review.
