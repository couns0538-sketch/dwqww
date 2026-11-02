---
name: grok-pc-safe-run
description: Use when preparing or running an authorized Forge CPU build, probe, conversion or benchmark on grok-pc under D-only storage, Idle scheduling, spare-core limits and protection of live NPT training and gate queues.
---

# Grok-PC Safe Run

Run only an explicitly reviewed, bounded CPU job. Installing this skill launches nothing. A request to create skills is not permission to run work on grok-pc.

## Preconditions

Identify the actual spare logical CPUs, complete production roots, frozen executable hash and all intended reads/writes. Use existing scripts when they already satisfy this contract. Read [the launcher contract](references/launcher-contract.md) before preparing its manifest.

All runtime data, portable tools, work directories, temporary files, logs and declared build/cache output belong on **D:**. In this R10 branch, working directories and every declared write path must be under **D:\a10**. A Python executable on C: is refused; use a reviewed D: environment. Never access live trainer datasets or NPT/gate queues, create STOP/PAUSE files, change another process's priority/affinity, or terminate another process. Supply the complete user-specified protected roots, including C: and F: entries; these are lexical exclusions, never inspected. Default name filters cannot discover arbitrary production locations. Work from independently exported inputs, not a running trainer's directory.

R10's explicit user authorization permits one narrow external CPU-runtime read
exception: pass `-ReadOnlyRuntimeRoots @('D:\grok-pc-data\npt\nnue-pytorch-amd')`
and declare that exact runtime in `read_paths`. The default is an empty list and
continues to reject it. Keep the **entire** protected-roots list, including
`D:\grok-pc-data\npt` and `F:\`; never omit a required read to bypass validation.
Only declared read roles receive this exception. Executables, working/output
directories, writes and command-path arguments retain strict validation.
Ancestors, unrelated or nested protected roots, queue/control paths, ADS and
reparse points remain refused. This is policy preflight, not an OS sandbox:
review import side effects, disable bytecode, keep caches/output on D, and pin
imported external source/DLL identities before and after the bounded CPU check.

For the explicitly authorized R10 CPU Inductor regression only, the separate
`ReadOnlyToolchainRoots` parameter may name the exact MSVC `14.51.36231` root
and Windows SDK `10.0.26100.0` Include/Lib roots listed in the helper. Its
default is empty. This exception applies only to declared reads; writes,
executable/cwd/output fields and command-path arguments keep strict D rules.
Never replace these with C:, Program Files, another SDK, LLVM or another drive.
Bind the selected x64 compiler/linker/DLL/header/library files before and after;
set explicit PATH/INCLUDE/LIB and D caches rather than dumping or inheriting an
unreviewed developer environment. No C installation or edit is authorized.

When dot-sourcing this helper for validation functions, do not store caller
state in its public parameter names (`Manifest`, `ProtectedRoots`,
`ReadOnlyRuntimeRoots`, `ReadOnlyToolchainRoots`): dot-sourcing can overwrite
those variables with parameter defaults. Use distinct names such as
`r10ProtectedRoots`, and verify the full required list survives before use.
Ordinary launches should invoke the script with `&` and explicit parameters.

For a reviewed pytest job under a strict D write guard, set an explicit D
`--log-file`; pytest otherwise opens Windows NUL. Its optional `*current`
convenience symlinks also conflict with the global workspace reparse guard.
Suppress only that optional alias creation in the owned harness, record the
intended aliases, restore the private hook afterward, and prove a real
`tmp_path` fixture still preserves its target bytes. Keep every test assertion
and the normal source/DLL/reparse guards unchanged. Existing owned aliases
require a separately reviewed bounded recovery: exact link/target inventory,
safe nonrecursive unlink, before/after target hashes, full protected roots,
disk floors and fresh admission. Never recursively remove a directory link.
PowerShell5.1 directory symlink recovery uses a validated `DirectoryInfo`
obtained with `Get-Item -LiteralPath` and its parameterless `Delete()` method;
do not rely on historical `Remove-Item` directory-link behavior.
External GPL code stays external; do not vendor it into Forge. No training or
GPU authorization is implied. See the launcher contract and the matching
`tests/Test-ReadOnlyRuntime.ps1` regression tests.

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
