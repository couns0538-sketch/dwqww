# Original datafilter regression qualification — UNPROVEN

The existing 73-test suite is copied from frozen `d8982bc0`. `SOURCE_COPY.json`
binds every original/copied file and the reviewed full-state overlays. Test
assertions are unchanged. The owned copy changes only receipt locations,
`ARTIFACT_ROOT` to `D:/a10`, and child scheduling from BelowNormal to Idle.
The deterministic historical fixture seeds are retained as test inputs, not
reused as new experimental or training seeds.

The external NPT source and loader DLL remain read-only at
`D:/grok-pc-data/npt/nnue-pytorch-amd`. No GPL source is copied, edited or
translated. Its current type-alias syntax requires Python 3.12 or newer; the
earlier private Python 3.10 runtime was not used for a knowingly incompatible
full-suite attempt. A separate CPU-only runtime is assembled at
`D:/a10/job3/runtime312`, preserving the earlier runtime/evidence.
The final73 replay uses the separate `runtime312np254` with historical
NumPy2.5.4; the first runtime and both unsuccessful attempts remain intact.

`run_regression.py` requires the assembled runtime manifest's SHA256 and binds
all declared private runtime files before and after execution. It separately
hashes external NPT root Python sources, the data_loader/ddp_utils/model/trainer
trees and native DLL before imports, refuses imported files absent from that
binding, and rechecks the full source set afterward. A fresh private bytecode
cache prefix avoids preexisting external cached bytecode. No bytecode is written.

The installed x64 MSVC compiler/linker/DLL/header/library inputs are also hashed
before and after. The adapter configures explicit compiler PATH/INCLUDE/LIB;
all generated code, DLLs, temporary files, test data and caches stay outside Git
under `D:/a10/job3/regression-runs/<fresh-tag>`. External runtime generated code
is execution evidence, never Forge source. Torch/interop/BLAS and Inductor compile
threads are one; the unchanged filter tests exercise at most two worker processes.
Training-loop entry and optimizer updates are prohibited. The Python audit hook
is a local fail-safe, not an inherited child guard or an OS sandbox; reviewed
child commands inherit D-only cache/output and bytecode-disabled environment.

The matching launcher now has separate, default-empty exact read-only opt-ins
for the NPT runtime and the installed MSVC/SDK roots. All protected roots remain
declared. Writes, executable/cwd/output fields and command-path arguments retain
strict D validation. No C installation or edit, GPU work, training, gate or match
is authorized.

Verification so far:

- Original19, NPT29 and toolchain28 launcher policy checks: PASS, Idle CPU2,
  native exits0; see `safety-fixtures02`. Temporary owned junctions were removed.
- Thirteen local NPT/private-runtime binding fixtures: PASS, no skips or errors,
  native exit0; see `binding-fixtures01-launch` and
  `D:/a10/job3/regression-runs/binding-fixtures01/RESULT.json`.
- Native `preflight01`: PREFLIGHT_PASS, native exit0, 42.8 seconds, CPU2 Idle,
  Torch/interop1, CUDA/HIP null. The external NPT source/DLL, all18,686 private
  runtime files and installed toolchain snapshots remained unchanged. Result
  SHA256 `C48A7CCE0302CC0E92DD8D212F29B79B95785856EB841B418A979AD817640F32`.
- Final `suite03`:73 collected/73 passed/0 failed/0 skipped; native0, clean
  capture/disk/reparse checks and unchanged source/runtime/toolchain identities.
  Result SHA256 `DF6058CB1CA6FE41580056384CE756CD021A744B0F50DE12BAA36E847900338B`.
  One existing scheduler-order warning is preserved. See `ATTEMPTS.md` for all
  failed attempts, exact archived source identities, recovery and final scope.

For a later independent replay, use a fresh tag after reviewing the inputs:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job3\regression\prepare_native_attempt.ps1 -Tag crew-preflight01 -Mode preflight -PreflightCpu 2
```

Preparation never launches. Inspect the generated manifest/wrapper and obtain a
fresh separately inspected quiet pair before running it. The full suite must run
alone with both CPUs2/3 quiet; prepare another fresh tag with `-Mode suite`.
Keep every failed/refused attempt and all admission observations. Never replace
the original receipts or infer a PASS from skips, missing dependencies or an
unexecuted suite.
