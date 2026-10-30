# Windows recipe QA fix — 2026-10-30

Prepared locally on Linux; **no grok-pc execution**. Windows PowerShell 5.1,
native inheritance, Cargo HIP build and GPU execution remain **UNVERIFIED**.
`runtime_availability.json` records unavailable local PowerShell commands.

The failure mechanism is native stderr routed through PowerShell 5.1's error
stream under `$ErrorActionPreference = 'Stop'`. The new standalone launcher
captures both native streams concurrently without that pipeline and retains
command/exit receipts. Preflight rejects unavailable telemetry, busy GPUs,
known production/build workers, insufficient space, unspecified CPU affinity,
and an unconfirmed GPU-free slot. CPU restrictions are set on the parent before
native creation. The HIP build is separate from execution so GPU checks repeat
after compilation. Its explicit MSVC x64 target matches the executable path.
It never stops or kills other work. All runtime checks still need Windows
qualification in a separately scheduled GPU-free slot.

Evidence:

- `documentation_red.log`: two expected failures before the launcher/README fix.
- `documentation_green.log`: two portable documentation checks pass; this does
  **not** execute or validate PowerShell behavior.
- `bullet_tests.log`: first system-Python run, 35 passing checks plus an import
  error for `test_cpu_smoke` because `torch` is unavailable in that interpreter.
- `bullet_tests_venv.log`: all 42 tests pass, no skips, using
  `/tmp/astra-a1-torch-cpu-env/bin/python` and
  `FORGE_LOCK_ORACLE=/tmp/astra-al1-native/current_final/lock_oracle`.
- `include_roundtrip.json`: original AL1 include SHA256 and generated include
  SHA256 differ, while all four parsed tensor arrays are equal. The first eight
  header lines are saved. An initial ad-hoc replay passed flat arrays to the
  writer and raised its expected shape guard; replay was corrected to the
  writer's documented physical shapes. No production/exporter change was
  needed. Compiled-binary identity is independent QA's reported result and was
  not recompiled in this follow-up.

The Windows-only test script `tests/bullet/test_hip_launcher.ps1` was written
before its launcher and covers empty/invalid/busy GPU samples, production
processes, scratch locations, disk budget, CPU mask, inherited foreign Cargo
target, native stderr success under `Stop`, argument quoting, original nonzero
exit preservation, exclusive evidence preservation, and top-level exit 76 for
an unscheduled slot or missing affinity. **It has not been run here.** It does
not invoke Cargo, HIP, or a GPU even when later executed on Windows.

No Cargo dependency graph or engine/search changes. `rust-version = "1.87"`
was already present; README now states that minimum and that 1.85 fails.

The exact local suite command was:

```sh
FORGE_LOCK_ORACLE=/tmp/astra-al1-native/current_final/lock_oracle \
  /tmp/astra-a1-torch-cpu-env/bin/python -m unittest discover -s tests/bullet -v
```
