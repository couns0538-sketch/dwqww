---
name: grok-pc-safe-run
description: Use when preparing or running an authorized Forge CPU build, probe, conversion or benchmark on grok-pc under D-only storage, Idle scheduling, spare-core limits and protection of live NPT training and gate queues.
---

# Grok-PC Safe Run

Run only an explicitly reviewed, bounded CPU job. Installing this skill launches nothing. A request to create skills is not permission to run work on grok-pc.

## Preconditions

Identify the actual spare logical CPUs, complete production roots, frozen executable hash and all intended reads/writes. Use existing scripts when they already satisfy this contract. Read [the launcher contract](references/launcher-contract.md) before preparing its manifest.

All runtime data, portable tools, work directories, temporary files, logs and declared build/cache output belong on **D:**. In this R10 branch, working directories and every declared write path must be under **D:\a10**. A Python executable on C: is refused; use a reviewed D: environment. Never read/write live NPT or gate queues, create STOP/PAUSE files, change another process's priority/affinity, or terminate another process. Supply the complete user-specified protected roots, including C: and F: entries; these are lexical exclusions, never inspected. Default name filters cannot discover arbitrary production locations. Work from independently exported inputs, not a running trainer's directory.

Use one or two explicitly approved spare CPUs and **one or two workers maximum**, Idle priority inherited before creation, and corresponding native thread arguments/environment. These settings do not limit arbitrary OS helper threads or sandbox an untrusted executable. Review the entire command and its adapter; refuse unknown behavior. For builds, propagate the budget into make/CMake jobs, compiler/LTO workers and every child; a wrapper argument alone does not enforce it. No batch or inline shell command bypasses that review.

Reserve at least **51200 MiB on D:**, plus the next job's estimated new bytes, and **30 GiB free on C:**. Total retained **D:\a10** bytes plus the next reservation must not exceed **15,000,000,000 bytes**. Retained logs/indexes, clones, portable tools and failed attempts all count. Check fresh space before every job/shard and any write over 1 GB; floor breaches fail qualification and block new work. The helper scans workspace size at each launch/completion and at most once per minute during a job, while checking drive floors each second. It does not kill a running child on a floor breach: reviewed adapters must honor their bounded write reservation and use cooperative shards/live guards. If that cannot be guaranteed, do not launch it.

## Launch and evidence

Prepare a new schema-1 manifest using the linked contract. In PowerShell, with `$Skills` pointing to the installed skill directory or extracted plugin `skills` folder:

```powershell
& "$Skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1" `
  -Manifest 'D:\forge-runs\reviewed-job.json' `
  -ProtectedRoots @('D:\npt', 'D:\gates')
```

Those roots are examples; include the actual crew-reviewed production roots. Manifest `output_directory` must not exist. Keep its copied manifest, stdout, stderr, native exit receipt and hashes. Native stderr is data under PowerShell 5.1; nonzero child exit or capture failure must fail the run.

Review execution receipts before continuing. Report Linux/static tests separately from native Windows qualification. Missing Windows evidence is **UNVERIFIED**.

## Conflicting workloads

`forge-lock-proof-set` requires a T4 smoke. This policy refuses worker_threads=4 and more than two CPUs. Run T4 on a separate explicitly authorized four-thread test host and attach its original receipt, or leave that proof row UNVERIFIED. Never silently relax the grok-pc policy. A destructive kill/resume test likewise belongs in its own isolated test worker/environment, not this launcher or a live shard job.
