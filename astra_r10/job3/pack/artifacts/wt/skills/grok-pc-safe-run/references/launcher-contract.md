# D-only reviewed-job launcher contract

The separate `ReadOnlyToolchainRoots` opt-in is empty by default. For the
authorized R10 CPU Inductor regression it accepts only these exact roots:
`C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231`,
`C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0`, and
`C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0`.
Only `read_paths` receives the exception. Executable, cwd, output, writes and
path-like command arguments retain strict D validation. No broad C root, other
version, SDK bin, LLVM or F root is admitted. Protected ancestors/descendants,
ADS, dot paths, queue/control names and reparse ancestors are still refused.
`readonly-toolchain-policy.json` and the receipt expose the opt-in; the adapter
must hash the exact compiler/linker/DLL/header/library input trees before and
after use and keep compiler output/cache on D. This is not an OS sandbox.

R10 supports an explicit external runtime read exception through the optional
`-ReadOnlyRuntimeRoots` parameter. It defaults to empty; schema1 is unchanged.
Only `D:\grok-pc-data\npt\nnue-pytorch-amd` is accepted under Couns's explicit
read-only authorization. Declare the real runtime in `read_paths`, and retain
the full protected-roots list, including its enclosing protected NPT root and
F:. Never omit a required read to evade validation.

This exception applies only to declared read roles. Executable, working/output,
write and command-path arguments keep strict validation. Protected ancestors,
nested protected roots, queue/control files, ADS, traversal and reparse paths
remain refused. The opt-in writes `readonly-runtime-policy.json`; the final
receipt records the read-only roots and `write_exception=false`. Policy
preflight does not sandbox native imports: keep bytecode/caches/temp on D and
pin imported source/DLL identities before and after the bounded CPU check.
External GPL runtime files remain external; no training or GPU is authorized.
Preserve old helper bytes and receipts before updating a used launcher, and use
the immutable archive for any replay bound to the old implementation.

`Invoke-GrokPcSafeRun.ps1` requires Windows PowerShell 5.1 or compatible PowerShell on Windows. It has no automatic hook or scheduled task. Dot-sourcing loads functions only. Direct invocation requires `-Manifest` and a nonempty complete `-ProtectedRoots` list, supplied before the manifest is read. It never enumerates or terminates other processes.

Schema 1 has exactly these top-level fields; unknown/missing/duplicate fields are refused:

| Field | Meaning |
|---|---|
| `schema` | integer 1 |
| `executable` | Existing absolute D: executable path; also present in read_paths |
| `executable_sha256` | Reviewed 64-hex digest, checked before and after execution |
| `arguments` | String array passed without a shell, Windows CRT quoting |
| `working_directory` | Existing directory beneath D:\a10 |
| `output_directory` | New D: directory for temp/manifest/stdout/stderr/result |
| `read_paths` | Nonempty array of all declared existing D: input paths |
| `write_paths` | Nonempty array of every intended build/cache/output location beneath D:\a10 |
| `logical_cpus` | One or two unique, available logical CPU indices 0..62; one processor group |
| `worker_threads` | integer 1 or 2 |
| `minimum_free_mib` | integer at least 51200 (D: floor); C: must independently retain 30 GiB |
| `required_bytes` | nonnegative integer estimate for all new writes before the next bounded boundary |

The argument vector needs exactly one explicit matching thread setting: `--threads 2`, `--jobs 2`, `--parallel 2`, `-j 2`, corresponding `=2` forms or `-j2`; use 1 when worker_threads=1. Conflicting or repeated settings are refused. A UCI engine has no standard `--threads` argument: use a reviewed adapter that accepts this argument, sends `setoption name Threads value N`, verifies acceptance and records the engine settings. Do not add a fictitious switch to Forge.

Paths use fully qualified D: spelling. Protected roots and any declared path that contains a protected root, queue.txt, queue_state.json, STOP/PAUSE leaves, named NPT/nnue-pytorch/gate directories and reparse-point ancestors are refused before opening them. This rejects a broad directory declaration such as D:\work when D:\work\live-trainer is protected, preventing recursive jobs from inheriting that scope. Declare real production locations via `-ProtectedRoots` even if they use different names. No source permissions or files are changed. All path-like arguments must be absolute D: paths within declared read_paths/write_paths; relative paths, dot components and drive-relative spelling are refused. `--key=D:\path` is checked. An `@D:\response-file` additionally requires an exact existing read_paths entry and prior content review; the helper does not parse response-file syntax. Use files instead of inline FENs or other arguments containing slashes, and use separate `-I D:\include` forms rather than embedded paths. These conservative argument constraints intentionally reject ambiguous cases. The manifest is copied as read-only input evidence; the copy's hash is recorded.

The branch-local R10 launcher accepts drive-qualified protected roots on C:, D: or F: (and other drive letters) without opening those excluded roots. Runtime paths remain D:-only; cwd, output_directory and write_paths must stay beneath D:\a10. Supply the user's entire protected-root array unchanged. Workspace enumeration rejects reparse points and counts hidden files, clones, failed attempts and all other retained regular file bytes conservatively; hard links are counted per pathname.

The current process is set to the requested affinity and Idle before native creation, and restored afterward. Children inherit this scheduling. OMP/MKL/OpenBLAS thread environment is set to worker_threads; TEMP/TMP/TMPDIR point into the new D: output. No HOME/CODEX_HOME is changed. Both native pipes drain asynchronously with bounded buffers. A disk sink failure is retained while the pipe continues to drain to EOF; native exit is preserved in the receipt. Result code is the child's exit on a clean capture, 70 for capture/disk-floor failure, or 76 for preflight/unhandled launcher failure. `result.json` can itself fail on a full disk: that is a failed run, never PASS.

Drive floors are checked before launch with the estimated bytes, every second while waiting, and after exit. The workspace cap is 15,000,000,000 bytes including the next reservation. A fresh recursive size check runs before launch and after exit; while waiting it runs no more often than once per minute. These checks cannot prevent another writer from consuming space between checks and do not stop or suspend the child. Review required_bytes as a real upper bound for each unit, including its launcher evidence, and use cooperative bounded jobs. If a floor/cap is breached, retain evidence and start no next unit. All retained outputs count against future free space. PowerShell 5.1 bootstrap regression evidence for this R10 change is in astra_r10/job1/safety-tests.

**Limits:** this is a policy preflight for trusted reviewed code, not an OS security sandbox. Declarations cannot prove arbitrary child code never writes outside D: or spawns extra helper threads. No process-tree quota, disk quota or global exclusion lock is claimed. Review adapters, compiler caches/configuration and child behavior before running. Executable hash/metadata checks reduce ordinary drift but do not prevent malicious concurrent replacement. Do not run untrusted commands.

Use a new manifest/output for every attempt; never change or overwrite sealed evidence. The launcher does not delete failed outputs. The supplied Windows regression can be run later with a D: portable Python, explicit spare CPU and new D: evidence directory; it was not executed in the Linux authoring environment.
