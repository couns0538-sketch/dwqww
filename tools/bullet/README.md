# Forge lock exporter and checkpoint contract

The primary target is AL1 source `294dbed3a15dfd821aaf9d4edc6e5f62832fd460`:
768 features -> shared 256-unit transform -> two SCReLU perspectives -> one
residual output. The exact lock embeds `src/nnue_weights.inc`; it has **no runtime
`.nnue` loader**. `lock_export.py export` writes that include format, with int16
storage at scale4096 and the lock's unchanged float32 inference. It never edits
engine source, installs a net, or touches a live trainer.

The separate `export_forge.py` and `make_checkpoint_fixture.py` preserve the
initial R10 K32H3 work. Those nets have a different architecture and loader;
R10 output must not be called lock-compatible.

## Exact Bullet interchange

Pinned upstream: MIT Bullet `da426a49b2a4b79a55a87031cd51c89bdf1ff030`.
The x64 `optimiser_state/weights.bin` layout is repeated ASCII tensorID+LF,
uint64 little-endian float count, then float32 little-endian data. It does not
store shapes or architecture. A manifest therefore binds its SHA256, roles,
column-major shapes, architecture, scaling and rounding. Unknown or duplicate
tensors, wrong sizes, nonfinite weights, quantization overflow, unsupported
architectures and overwrite attempts are errors. SHA256 covers the actual parsed
stream, not merely a separate earlier read.

For the original lock graph the tensorIDs are:

| ID | Bullet shape | Physical serialized order |
|---|---|---|
| ftw |256x768|768 feature rows of256 weights|
| ftb |256x1|256 biases|
| outw |1x512|256 STM weights then256 opponent weights|
| outb |1x1|one bias|

All four tensors use scale4096 and nearest ties away from zero (Bullet `.round()`),
with the stored float32 promoted to float64 before scaling. The manifest command
requires those four exact IDs. Manually specified manifests may map other IDs,
with the same explicit shapes and semantics. Export does not deduce or silently
convert an arbitrary Bullet architecture.

```bash
python tools/bullet/lock_export.py manifest \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --out NEW_MANIFEST.json \
  --provenance 'Actual training run identifier, source SHA and log path'
python tools/bullet/lock_export.py export \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --manifest NEW_MANIFEST.json \
  --out NEW_nnue_weights.inc
python tools/bullet/lock_export.py reference \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --manifest NEW_MANIFEST.json \
  --fens fens_12k.txt --out NEW_reference.txt
```

Reference columns are residual centipawns and the pre-cp output's float32 bit
pattern. The oracle recreates ascending-square refresh, each separate float32
multiply/add, the16 independent lanes, ordered lane reduction, cp scaling,
clamp and truncation. It does not use NumPy's dot-product reduction for the lock.
The native unchanged-engine oracle verifies centipawns on every FEN.

## Original Bullet graph and license boundary

`lock_graph/` requires Rust **1.87 or newer**; Rust 1.85 fails for this pinned
dependency graph. `Cargo.toml` declares `rust-version = "1.87"`. It uses
**only Bullet's lower-level MIT compiler/trainer crates**.
The ordinary `bullet_lib` wrapper unconditionally depends on `montyformat`
(AGPL-3.0) and `sfbinpack` (GPL-3.0) at the pinned revision. Its initial typecheck
was rejected after dependency auditing. The original attempted wrapper source
and metadata are retained under validation as rejected evidence; it is not the
active build recipe. No GPL/AGPL source was copied into this project.

The active graph takes sparse STM/opponent inputs and training-only `hce_cp` and
`score_cp` auxiliaries. Its loss is:

```
(sigmoid(hce_cp *2.25/400 + residual) - sigmoid(score_cp *2.25/400))²
```

This avoids training full evaluation and then adding HCE again at inference.
The graph's four learned tensors alone are exported. The initializer's seed is
20261030. Run it on CPU to verify graph construction and obtain an actual
Bullet-written checkpoint:

```bash
cargo run --locked --manifest-path tools/bullet/lock_graph/Cargo.toml --bin forge-lock-bullet-graph -- NEW_weights.bin
python tools/bullet/lock_export.py manifest --checkpoint NEW_weights.bin \
  --out NEW_manifest.json --provenance 'Bullet initialization only; NOT TRAINED'
```

**This binary initializes weights and writes a checkpoint; it does not train.**
A separate `train_smoke` binary supplies an original bounded input mapper and
one-epoch optimizer driver using only the lower-level MIT crates. Its CPU mapper
mode can run without a GPU; actual GPU smoke and HIP execution remain unverified.
The separate CPU PyTorch smoke is explicitly labelled PyTorch, never Bullet.

## Fixture status and safety

`lock_export.py include-fixture` creates a synthetic checkpoint from an existing
include. It is useful for validating layout and native parity, and is not a new
training run. Include round trips preserve tensor values, not the entire text:
QA found differences in header lines 1–8 (comments and static-assert text/
formatting), with identical tensors and compiled binaries. This QA fix locally
rechecked tensor identity; compiled-binary identity is the independent QA
result and was not recompiled here. Do not describe that original-include round trip as
byte-identical. The separate deterministic exporter replay uses identical
inputs and provenance and is a different claim. The R10 fixture bridge similarly labels its provenance synthetic.
The R10 planted-corruption command changes one active output weight and verifies
both changed arithmetic and safe bounds. `.nnue`'s format has no weight checksum,
so successful native loading is expected; the original reference comparison must
fail. No engine strength or training-gain conclusion follows from any fixture.

NumPy is required. Tests are under `tests/bullet/`; native oracle tests also
require their explicit binary environment variable. Use the saved validation
logs to distinguish an executed test from a conditional skip.

## Bounded one-epoch Bullet GPU smoke driver

The optional `train_smoke` binary uses the same four tensorIDs and HCE-conditioned
score-only loss. Its input is a bounded original **FBS1 mapper interchange**, not
bulletformat or binpack. This lets the CPU and GPU checks use exactly the saved
A1 slice and true HCE labels; it does not replace the Job2 dataset converters.

Prepare a new input directory, or use the committed `bullet_gpu_input` receipt
and binary. Preparation verifies every selected FEN against FPOS and rechecks
all three original source hashes. The selected8192 rows are one bounded slice,
not an epoch over10M or305M rows.

```bash
python tools/bullet/prepare_lock_smoke_data.py \
  --pos subset.pos --hce subset.hce --fen subset.fen \
  --rows 8192 --out NEW_BULLET_INPUT
cargo run --locked --manifest-path tools/bullet/lock_graph/Cargo.toml \
  --bin train_smoke -- NEW_BULLET_INPUT/input.fbs UNUSED_NEW_DIR 128 --check-input
```

The CPU check compiles the actual backward tensor graph and maps all8192 rows
through Bullet's real `ModelInputsMapper`/`ReadMapLoader`. It does not execute
training kernels. The driver rejects malformed/truncated data, invalid sparse
indices or padding, nonfinite labels, existing output directories and any batch
size that would drop a tail. A no-backend training request exits with an explicit
error and creates no output directory.

The standalone [Windows launcher](run_hip_smoke.ps1) targets **64-bit Windows
PowerShell 5.1 or newer**. Use it only in a **GPU-free scheduled slot**, **never alongside the live AMD trainer**,
self-play, gates, or other production work. Preparing this launcher does not
authorize its execution: **no grok-pc command was run for this QA fix**. A future
operator must schedule the slot and choose genuinely spare logical CPUs.

Configure the installed HIP SDK as Bullet documents (`HIP_PATH`, with
`GCN_ARCH_NAME` verified from `hipinfo`). Supply an existing, explicitly pinned
venv `Scripts\python.exe` with NumPy and its independently recorded SHA256;
there is no fallback to system Python. In a fresh dedicated PowerShell process,
replace every angle-bracket placeholder before using this future command:

```powershell
powershell.exe -NoProfile -NonInteractive -File .\tools\bullet\run_hip_smoke.ps1 `
  -CpuAffinityMask '<EXPLICIT_HEX_MASK_OF_SPARE_LOGICAL_CPUS>' `
  -PythonExe '<ABSOLUTE_VENV_PATH>\Scripts\python.exe' `
  -PythonSha256 '<RECORDED_64_HEX_SHA256>' `
  -GpuFreeSlotConfirmed
```

The mandatory affinity mask is hexadecimal (optional `0x` prefix), with no
assumed spare CPU numbers. The launching process is set to **Idle** with that
mask before any native tool starts; children inherit these restrictions. Cargo
uses **`-j2`**, `CARGO_BUILD_JOBS=2`, and **`cargo fetch --locked`** before the
locked build. The build explicitly uses `--target x86_64-pc-windows-msvc`
and executes that target's matching binary, so inherited `CARGO_BUILD_TARGET`
or Cargo `build.target` cannot redirect the build to a different binary while
an old host executable runs. The launcher checks Rust >=1.87 and the pinned
venv/NumPy.

Fresh GUID run directories live under `F:\astra_bullet_smoke`, outside the
repository. `CARGO_TARGET_DIR` defaults to `F:\astra_bullet_cargo_target`; both
`TEMP` and `TMP` use the run's `temp` directory on **F:**. Custom roots must also
be on F:, outside the repository, without junction/symlink ancestors. The
launcher requires **at least 20 GiB free** before work and rechecks before the
build and export. It never deletes prior evidence to make room.

GPU and production-process prechecks run before work and again immediately
before Cargo builds and, after compilation, immediately before the built HIP
smoke executable starts. Its SHA256 is recorded before execution. Each check
requires **five valid snapshots**, one second apart (four delays), even when all
samples are zero. Process counters on the **same physical GPU and engine** are
summed within each snapshot, using the WDDM adapter LUID, physical GPU index,
engine index and engine type. Only `3D`, `Compute`, `Compute0`/`Compute1` and
`Compute_0`/`Compute_1` (any numeric suffix) count toward busy status. An aggregate
**strictly greater than 2%** in **any** snapshot refuses; exactly 2% is allowed.
Separate GPUs/engines are never added together. Copy/Video utilization does not
mark a GPU busy, but every returned counter must still have a valid WDDM name
and finite utilization between 0 and 100. Empty, unavailable, denied, or malformed
GPU telemetry, a detected production job, and insufficient space **fail closed
with exit 76**.

Production detection uses actual executable names and Python's invoked script
argument. It rejects `fastchess.exe`, `cutechess.exe`, `cutechess-cli.exe`,
`selfplay.exe` / `selfplay_*.exe` / `selfplay-*.exe`, `selfplay.py` and analogous
selfplay script suffixes, and `train*.py` invoked from a path with an
`nnue-pytorch` component. Built-in gate names are exactly `gate.exe` and
`gate_*.exe`. Unrelated Python and all compiler processes are allowed; an editor
opening `nnue-pytorch\train.py` or a script receiving that filename as input is
allowed too. `forge.exe` and `stockfish.exe` are not assumed to be gates.

For a gate with an arbitrary binary name, pass exact basenames with
`-GateExeNames @('forge_gate_candidate.exe')` or exact absolute paths with
`-GateExePaths @('F:\gates\forge.exe')`. For a known trainer outside nnue-pytorch,
use `-ProductionTrainScriptPaths @('F:\forge\tools\nnue\train_resid_v3b.py')`.
To pass multiple values, invoke the script with `& .\tools\bullet\run_hip_smoke.ps1`
from an existing PowerShell session; Windows `powershell.exe -File` cannot pass
array parameters.
Matching is case-insensitive and paths are normalized; wildcards are rejected.
Full paths distinguish a selected binary/script from unrelated copies with the
same name. Launch configured trainer scripts using their full path: CIM does
not expose their working directory, so bare `train.py`, ambiguous relative
script paths, missing per-process command lines, and `-c`/`-m` wrappers cannot
establish a trainer identity. A missing or failed whole process inventory still
refuses the preflight. The configured identity lists are saved in `preflight.json`.

These snapshots cannot reserve the GPU: keep the scheduled slot exclusive for
the entire build and smoke. The launcher never stops, kills, pauses, or changes
another process. If counters are unavailable, diagnose them separately and
leave the smoke blocked.

Native tools run through `System.Diagnostics.Process`, with concurrent raw
stdout/stderr copies into separate `*.stdout.log` / `*.stderr.log`, plus
`*.command.json` and `*.exit` receipts. There is no native stderr-to-PowerShell
error pipeline: Cargo progress on stderr therefore does not become the old
PowerShell 5.1 `NativeCommandError` under `$ErrorActionPreference = 'Stop'`.
Nonzero native exits remain failures with original output retained. Only a
successful training marker followed by both exports produces
`LAUNCHER_COMPLETE.txt`; it does not certify native parity or playing strength.

The non-GPU Windows regression script is
`tests/bullet/test_hip_launcher.ps1`. It exercises refusal cases and actual
native stderr, argument quoting, and nonzero exits without invoking Cargo/HIP.
It has **not been executed here** because neither Windows PowerShell nor `pwsh`
is available. Local portable documentation checks and include tensor replay are
recorded under `validation/astra-bullet-export/qa_windows_fix/`. The later
process/GPU policy refinement has separate portable source/documentation logs
in `validation/astra-bullet-export/qa_policy_refinement/`; those logs do not
execute or establish Windows PowerShell behavior.

Before training on converted data, require the converter branch's independent
clearance receipt against both complete real 013/014 shards, with zero overlapping
keys. That receipt is **UNVERIFIED here**; the synthetic fixture pass does not
clear any real training data. Do not start this smoke before data clearance.

GPU execution/HIP build are **UNVERIFIED here**. Inspect `COMPLETE.txt` only after
successful exit; it records one epoch, row count, batch size and seed. Failures
retain partial outputs without this completion marker. The intended optimizer
is AdamW with zero decay, LR0.0001, fixedseed20261030, sequential source order and
int16/4096 representable-range clipping. This GPU graph does **not** implement
quantization-aware training; the separate PyTorch smoke does. Export quantizes
all tensors; the resulting exported net still needs the native12k parity run.
No GPU throughput, training loss, gain or playing strength is inferred from the
CPU mapper check. The supplied source does not launch itself or change an
existing trainer or gate.
