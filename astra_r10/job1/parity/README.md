# R10 raw-bit diagnostic — UNPROVEN

These files prepare independent diagnostic binaries, never production/timing executables. `eval_components.cpp` is based on Forge's own R9 harness. It evaluates OFF and ON for every inspected state, compares fresh/incremental accumulator bits, all 16 output-lane float bits, pre-conversion output float bits, NNUE integer, HCE integer and the combined/clamped integer evaluation. It retains all legal first moves/unmakes, null moves/unmakes and 64 seeded playouts of up to 128 plies. Root traces contain exactly the pinned 12,000 FENs in original order; each OFF evaluation must increment the actual wide-path counter by zero and each ON by one.

`parity_adapter.py` binds original raw TSV rows to executable, options, weight image and corpus SHA256s; it preserves original stdout/stderr, argv and exit receipts. The seed is explicit and must be reserved in the run ledger. Proposed seed 3771096103 is pending the main agent's historical check; the identical seed in good/negative diagnostic arms is a replay of one experiment, not a new random experiment. No native run has been performed by this implementation task.

## Scheduled invocation

Use the main agent's `astra_r10/launch.ps1` with new schema-1 safe manifests and the complete protected-root list. Interpreter is `D:/a10/python/python.exe`; prepend `-B` and these adapter arguments (each an argv element, no shell nesting):

1. `parity_adapter.py --threads 1 prepare --source D:/a10/c1 --source-manifest D:/a10/wt/astra_r9/evidence/c1-source.json --negative-source D:/a10/parity-negative --fens D:/a10/inputs/fens_12k.txt --out D:/a10/parity-r1 --seed 3771096103`
2. `parity_adapter.py --threads 1 build --prepared D:/a10/parity-r1/prepared.json --compiler-config D:/a10/wt/astra_r10/job1/parity/compiler.json --tag retry02`
3. `parity_adapter.py --threads 1 run --prepared D:/a10/parity-r1/prepared.json`
4. `skills/eval-exact-simd-port/scripts/check_eval_parity.py D:/a10/parity-r1/eval-parity.json --threads 1`

Use absolute script paths in manifests. Declare source, corpus, scripts, D Python, prepared outputs and negative source appropriately. The original C: kit compiler is read-only and hash-pinned in `compiler.json`, per the main agent's ruling. It receives one serial diagnostic compilation at a time and uses the launcher's D-only TEMP/TMP. Do not schedule alongside kit builds or timing. The launcher enforces storage reserves; reserve at least 150 MiB for prepared sources, two diagnostics, root traces and retained logs. Native compile failure or parity failure remains FAIL/UNVERIFIED; no fallback corpus or production binary substitution is allowed.

## Embedded negative control

The prepare step copies only frozen source/include into a new `D:/a10/parity-negative`, changes exactly `NnueW2[0]` by +4096 (or -4096 if required to remain int16), and records its source-token span, tensor/index and original/new values. Complete W1/B1/W2/B2 tensors are serialized into a documented little-endian int16 image. Only that coefficient's two-byte range may differ. Original source, source include snapshot and both images remain available; source manifests bind both builds. A separate negative diagnostic executable incorporates the changed source.

Before creating any output, preparation compares the complete source tree to the recovered R9 manifest with independently pinned SHA256 `EB0CE6937C9C63BE40AC8F8D3C59AADA7C0EE4BAAA172746D920A4246F5D173A`. It preserves the exact manifest bytes and binds them in prepared/build provenance. Every later build/run rechecks this authoritative source binding. Stored FEN/harness paths pass the D:/a10 ownership checks before any hash read. Use `prepare-launch02-manifest.json`; `prepare-launch01` is superseded before execution.

The new checker mode explicitly binds the negative trace to that different executable and compares it with **good OFF**, requiring at least one component mismatch. Negative OFF/ON equality alone does not pass the negative control. Final trace/receipt consistency PASS still requires review of original native execution and build provenance. No Elo or Windows qualification follows from fixture tests.

## Compiler startup diagnosis

The first native build failed immediately before compilation because the inherited PATH omitted the kit's UCRT bin directory. Bounded probes preserved in `D:/a10/parity-compiler-probe01` show cc1plus startup exit `0xC0000135` and driver syntax-probe exit1 with inherited PATH, versus exit0 for both when only `C:\msys64\ucrt64\bin` is prepended. The adapter now supplies this child-only environment and records PATH/TEMP/thread settings in each command receipt. It does not change system/user PATH. `--tag retry02` creates new `build-good-retry02` and `build-negative-retry02` directories without overwriting the failed `build-good` evidence. Use `build-launch02-manifest.json`; the old build manifest is preserved and superseded.
