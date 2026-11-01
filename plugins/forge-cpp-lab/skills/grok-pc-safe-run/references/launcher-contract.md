# D-only reviewed-job launcher contract

`Invoke-GrokPcSafeRun.ps1` requires Windows PowerShell 5.1 or compatible PowerShell on Windows. It has no automatic hook or scheduled task. Dot-sourcing loads functions only. Direct invocation requires `-Manifest` and a nonempty complete `-ProtectedRoots` list, supplied before the manifest is read. It never enumerates or terminates other processes.

Schema 1 has exactly these top-level fields; unknown/missing/duplicate fields are refused:

| Field | Meaning |
|---|---|
| `schema` | integer 1 |
| `executable` | Existing absolute D: executable path; also present in read_paths |
| `executable_sha256` | Reviewed 64-hex digest, checked before and after execution |
| `arguments` | String array passed without a shell, Windows CRT quoting |
| `working_directory` | Existing D: directory |
| `output_directory` | New D: directory for temp/manifest/stdout/stderr/result |
| `read_paths` | Nonempty array of all declared existing D: input paths |
| `write_paths` | Nonempty array of every intended D: build/cache/output location |
| `logical_cpus` | One or two unique, available logical CPU indices 0..62; one processor group |
| `worker_threads` | integer 1 or 2 |
| `minimum_free_mib` | integer at least 32768 |
| `required_bytes` | nonnegative integer estimate for all new writes before the next bounded boundary |

The argument vector needs exactly one explicit matching thread setting: `--threads 2`, `--jobs 2`, `--parallel 2`, `-j 2`, corresponding `=2` forms or `-j2`; use 1 when worker_threads=1. Conflicting or repeated settings are refused. A UCI engine has no standard `--threads` argument: use a reviewed adapter that accepts this argument, sends `setoption name Threads value N`, verifies acceptance and records the engine settings. Do not add a fictitious switch to Forge.

Paths use fully qualified D: spelling. Protected roots and any declared path that contains a protected root, queue.txt, queue_state.json, STOP/PAUSE leaves, named NPT/nnue-pytorch/gate directories and reparse-point ancestors are refused before opening them. This rejects a broad directory declaration such as D:\work when D:\work\live-trainer is protected, preventing recursive jobs from inheriting that scope. Declare real production locations via `-ProtectedRoots` even if they use different names. No source permissions or files are changed. All path-like arguments must be absolute D: paths within declared read_paths/write_paths; relative paths, dot components and drive-relative spelling are refused. `--key=D:\path` is checked. An `@D:\response-file` additionally requires an exact existing read_paths entry and prior content review; the helper does not parse response-file syntax. Use files instead of inline FENs or other arguments containing slashes, and use separate `-I D:\include` forms rather than embedded paths. These conservative argument constraints intentionally reject ambiguous cases. The manifest is copied as read-only input evidence; the copy's hash is recorded.

The current process is set to the requested affinity and Idle before native creation, and restored afterward. Children inherit this scheduling. OMP/MKL/OpenBLAS thread environment is set to worker_threads; TEMP/TMP/TMPDIR point into the new D: output. No HOME/CODEX_HOME is changed. Both native pipes drain asynchronously with bounded buffers. A disk sink failure is retained while the pipe continues to drain to EOF; native exit is preserved in the receipt. Result code is the child's exit on a clean capture, 70 for capture/disk-floor failure, or 76 for preflight/unhandled launcher failure. `result.json` can itself fail on a full disk: that is a failed run, never PASS.

The disk floor is checked before launch with the estimated bytes, every second while waiting, and after exit. It cannot prevent another writer from consuming space between checks and does not stop or suspend the child. If the floor drops, finish the bounded/cooperative unit, retain evidence and start no next unit. A job without its own bounded/live disk behavior is unsuitable. All retained outputs count against future free space.

**Limits:** this is a policy preflight for trusted reviewed code, not an OS security sandbox. Declarations cannot prove arbitrary child code never writes outside D: or spawns extra helper threads. No process-tree quota, disk quota or global exclusion lock is claimed. Review adapters, compiler caches/configuration and child behavior before running. Executable hash/metadata checks reduce ordinary drift but do not prevent malicious concurrent replacement. Do not run untrusted commands.

Use a new manifest/output for every attempt; never change or overwrite sealed evidence. The launcher does not delete failed outputs. The supplied Windows regression can be run later with a D: portable Python, explicit spare CPU and new D: evidence directory; it was not executed in the Linux authoring environment.
