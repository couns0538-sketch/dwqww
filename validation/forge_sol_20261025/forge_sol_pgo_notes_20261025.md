# Pure-PGO scripts — prepared, not executed

Status on 2026-10-25: no engine compile, profile training, test engine, or timing
run was performed by this preparation task. Python AST, Bash syntax, both
PowerShell parses, C# type compilation and synthetic failure fixtures passed.
PowerShell parsing/type compilation ran under Linux PowerShell7 and executed
no Win32 calls. GCC15.2/MSYS2 builds, native controls and Windows/Zen5 speed
remain **UNVERIFIED**. Root must close Job1 before running this job.

The authoritative recipe is the recovered
`01_lock/pc_build/build_h256_e12.ps1`, SHA256
`a5c88c838ff91b778501d913de38dc1286e1958268b78810b0483cea5306bd23`.
Its exact common flags are:

```
-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread
```

No AVX512, alignment, mtune, tunables, LTO, arithmetic or engine-source change
is added. `-Werror` and fatal missing-profile/coverage-mismatch diagnostics are
build checks. No `-fprofile-correction` or partial-training escape is used.
The exact PC compiler is MSYS2 Rev14 GCC15.2.0, default
`C:\msys64\ucrt64\bin\g++.exe`. The Linux worker permits GNU g++ >=13 and
records its actual version and target. Native GCC14.2 evidence is Linux only.

## Deliverables and execution

* `forge_sol_pgo_build_20261025.sh`: Linux full build/lock-bench/CTest pipeline
  by default; `--phase` also exposes its internal stages.
* `forge_sol_pgo_build_20261025.ps1`: public Windows entry dispatches the full
  native orchestrator. `-Phase` is internal to an existing reviewed supervisor.
* `forge_sol_pgo_worker_20261025.py`: common baseline/generate/train/use/validate
  implementation; direct argument arrays, no shell eval.
* `forge_sol_pgo_winqual_script_20261025.ps1`: complete native PC build/check/
  timing orchestrator in one resource envelope.
* `forge_sol_pgo_native_resource_20261025.cs`: shared original Job 1 native
  Session implementation. No kill API or kill-on-job-close behavior.

Use a dedicated 64-bit PowerShell7 process with Python3 and MSYS2 g++/objdump.
CMake/Ninja/CTest are not required by the PC path. Keep helpers together.
The source is an immutable export of
the root-designated exact engine tree. Packaged defaults select
`forge_sol_lock_source_20261025` (exact f491 lock), with
`forge_sol_lock_pc_recipe_20261025.ps1` beside the scripts. Source and output
must be disjoint. The recovered recipe is read/hash-checked, never executed:

```powershell
pwsh -NoProfile -File .\forge_sol_pgo_build_20261025.ps1
```

The PC script requires AuthenticAMD family26 (Zen5) and records the registry
CPU name, vendor and identifier. CPU load samples before/after timing are
mandatory for a native verdict. Native runtime controls remain UNVERIFIED here.
It assigns its dedicated host and all descendants to one job:
CPUs0–3, Idle, 3GiB aggregate private commit (headroom below4GiB), 43-minute new
work admission and 45-minute total observation. TMP/TEMP/TMPDIR and generated
files stay in its own new output folder. It never changes HOME, uses a GPU,
contacts an external service, or stops another process. No process is killed.
A child that does not respond to stop/quit/EOF is reported by PID and leaves
status UNVERIFIED; no success is claimed for an incomplete job.
The output directory must be a new child of the script's own root. Existing
outputs, prefix escapes and reparse-point ancestors are rejected before writes.
A new dated result TXT is created with CreateNew before OS/source/tool checks,
so Linux or missing-tool rejection still leaves one UNVERIFIED result. Invalid
or unwritable output paths can fail on the console alone. PowerShell module
cache and .NET bundle extraction paths are set inside the run folder and
restored on exit; HOME is never changed.

The public Bash entry establishes Linux CPU affinity0–3 with taskset, nice19,
and inherited soft/hard per-process RLIMIT_AS=3GiB with ulimit, then reads back
all three before invoking the unchanged worker. This is a **per-process virtual
address-space** cap; it does not establish the Windows aggregate job-memory
limit. Unsupported Linux controls or missing tools stop before the worker.
It reuses a valid existing admission deadline or sets one at now+2580seconds;
it never resets a deadline per phase. It supplies the internal envelope marker
only after readback succeeds. Normal invocation needs no marker/deadline flags:

```bash
bash forge_sol_pgo_build_20261025.sh --cmake /path/to/cmake
```

The default Bash pipeline runs baseline/first-lock-gates, generate,
declared training/freeze, instrumented post-freeze lock gates, use/final lock
gates, and Linux internal QA CTest using Unix Makefiles (CMake and Make required).
Original `tools/uci_regression.py` calls `process.kill()` on timeout; unchanged
Linux QA therefore has no transitive no-kill guarantee. The strict PC path
never runs it and records native CTest UNVERIFIED_NOT_RUN_KILL_NOTHING_CONTRACT.
The Linux pipeline performs no speed comparison, perft or FMA audit; those
measurements are supplied by the native PC orchestrator. Do not reset the deadline per
phase. Guard variables alone do not establish CPU/memory/priority restrictions.
The public PC entry establishes its separate Windows controls without
user-supplied markers. `--guard-self-test` on the Bash entry reads back actual
Linux controls and exits before GCC. Synthetic readback fixtures validate the
same embedded checks without changing affinity or invoking GCC.

A separately supervised Linux pipeline used the **pre-guard launcher**, preserved
byte-for-byte under `forge_sol_pgo_evidence_20261025/forge_sol_pgo_build_pre_guard_20261025.sh`
(SHA25635d6f90d1b10389bfefb68242b10b7cedf631d32a2a64933a9ad969d3dd5d1a5),
inside an independently verified external envelope. Its worker remains
SHA2561e6249ceeb76e7c10911fa1d5a889a7fb30fcf2fce70093ce90c80891a6774d7.
That run does not establish a new-launcher end-to-end execution result.

## Build integrity and training

All stages use the same source cwd, relative input paths, object output names,
intermediate executable name and explicit profile directory. This avoids GCC
profile-name mismatches between separate generate/use directories. Baseline,
instrumented and final executables are saved separately as
`forge_sol_pgo_baseline_20261025.exe`,
`forge_sol_pgo_instrumented_20261025.exe`, and
`forge_sol_pgo_final_20261025.exe`. Every compiler/linker
exit is checked, previous outputs removed before replacement, warnings fail,
and source/compiler/recipe/profile hashes stay frozen. No retry overwrites an
attempt; use a new output folder. Require eight nonempty gcda files bound to
the eight expected translation-unit names, with immutable profile hashes.

Every new engine's first work is OFF bench11=308972. Baseline/final subsequent
gates check d13=745494, d16=2460422, d20=11901452, d22=31111774, stopping before
starting another test on a mismatch. Instrumented training checks d11 and d16 interactively, so its first bench11 is
explicitly part of training. It then searches six literal FENs at depth8,
waiting for each real bestmove:
startpos, kiwipete, developed middlegame, rook/pawn ending, quiet development,
and king/rook ending. Exact FENs and stdin are in the worker and training receipt.
No external training data is needed. `quit` exits normally to flush libgcov.
That dataset is immediately copied/hash-verified into profile-frozen; use-stage
reads only that copy. Extra instrumented all-five-depth validation happens
after freezing and can update only the separate runtime profile directory.
Bench20/22 validation never enters the used training dataset.

The PC script checks final startpos perft5=4865609 and kiwipete5=193690690,
and audits actual unstripped NNUE symbols for zero FMA with objdump
`-d -t -C --no-show-raw-insn`. A nonempty defined-function COFF inventory, every
defined NNUE body, all three refresh/update/evaluate APIs and decoded bodies
are mandatory; absent/stripped/incomplete code cannot pass. Static runtime
library FMA is separately outside that named scope. **Native CTest is not run**:
the original UCI regression may kill its owned child on timeout, conflicting
with the PC's kill-nothing contract. The native result explicitly keeps full
release acceptance UNVERIFIED even when descriptive NPS exceeds3%.
Linux internal QA CTest builds unchanged test
mains without PGO and links them to imported **actual final PGO core objects**;
it never recompiles the core under a different profile path or suppresses its
missing-profile diagnostics. Its expected lock result is13/14 with forge_tests as the
only failed suite and these exact four FAIL lines:

```
WAC 001 expected g3g6 got f6h5
WAC 001 score 661 below 31997
unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

After gates and one warmup per build, timing is bench20 in eight ABAB blocks:
32 fresh timed processes, eight block ratios and16 adjacent A/B pair ratios.
It logs every value, executable hashes, machine identity, CPUs and load. The primary comparison statistic is the median of **all16 adjacent B/A ratios**
and must be >=1.03. Eight geometric block ratios sqrt((B1/A1)*(B2/A2)) are
supplementary only; below that is DROP. A result at/above3% remains descriptive,
with native CTest and full release acceptance UNVERIFIED. No rows
are removed. Missing gates, invalid rows, exceeded budget, or remaining PIDs
are UNVERIFIED. This establishes no Elo claim.

The authoritative v3b trainer is recovered, but Job3 has not begun. Windows
native unavailability alone is not treated as permission to abandon the valid
Linux PGO implementation path.

The native orchestrator explicitly exits0 after completed descriptive measurements
and exits1 on failure. Focused fresh-process fixtures verified actual public
wrapper forwarding for0/1 and reproduced the old undefined-LASTEXITCODE failure
using the preserved pre-fix trailer; no native Windows execution is implied.
