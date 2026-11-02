# Restart proof recipe and limits

`resume_fixture.py` is a deterministic **disposable fixture**. It transforms each original input line into its SHA-256 digest plus LF, keeps one sealed output per input shard, and retains per-shard source/output hashes. It is not an FPOS/HCE/NPT converter and is never a substitute for replaying the real pipeline.

From a permitted D: spare-core job, run through the `grok-pc-safe-run` launcher. The direct argv is:

```powershell
$Python = 'D:\forge-tools\venv\Scripts\python.exe'
$SkillRoot = 'D:\forge-tools\plugins\forge-cpp-lab\skills\resumable-shard-job'
$ProofOut = Join-Path 'D:\forge-evidence' ('resume_fixture_' + [Guid]::NewGuid().ToString('N'))
& $Python (Join-Path $SkillRoot 'scripts\resume_fixture.py') selftest --out $ProofOut
if ($LASTEXITCODE -ne 0) { throw 'Restart fixture did not PASS; keep every artifact.' }
```

The helper refuses an existing proof directory, creates three original fixture shards, completes an uninterrupted run, starts **one owned child** with Python's Popen, waits for a sealed first-shard checkpoint and bytes from the next shard, terminates that child, then resumes into its own interrupted output. It never searches for or terminates a process by name/PID supplied by the caller. A bounded timeout kills only that same owned fixture child when needed. Idle/affinity are inherited from the safety launcher; the helper creates no worker pool.

`RESTART_PROOF.json` contains both final MD5/SHA-256s and actual termination/retained-partial evidence. A nonzero owned-child exit, absence of the second checkpoint, and a genuinely incomplete second-shard stage are mandatory; a normal-completion race cannot count as interruption. Separate logs, exact argv, exit status, source files, checkpoints, output shards and incomplete stages remain. Resume uses an OS-owned exclusive lock released by process exit. Hash/link failures block; there is no silent rename-over-existing fallback. NTFS hard-link support and native Windows termination behavior remain to be tested on the target platform. Never use this technique to stop a real trainer or gate.

For the real pipeline, adapt its existing fault-injection/test entry point to the same protocol on copied small shards. Keep all roles and actual record/serialization bytes. Produce a table with fault point, baseline MD5, resumed MD5, match, original worker exit and scope. Test data-before-checkpoint interruption, checkpoint-before-next-shard interruption, source/tool changes and corruption. The fixture's PASS cannot fill those real-job rows; mark them UNVERIFIED until executed.

The implementation intentionally retains temporary linked files as evidence. It is a tiny proof harness, not a disk-optimized production job. Budget retained bytes, check free space before larger tests and never adopt its fixture layout as a new 305M-position storage system.
