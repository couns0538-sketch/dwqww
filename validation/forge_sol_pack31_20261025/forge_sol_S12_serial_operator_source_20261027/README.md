# S12 serial operator checkpoint — source only, 2026-10-27

Status: PREPARED; no S12 compiler/native invocation is authorized or executed. All actual S12 builds, FIRST/Std/ASAN/ON, RED/GREEN/counter/alias/parity, speed, Elo, Windows and adoption remain UNVERIFIED. Root designated `/root/s12_publication_prep` to own S12 native work after a fresh grant following actual S11 closure/publication.

The existing S11 operator pattern is usable: invoke each frozen CLI as its own process and preserve the exact grant/argv plus parent start/close captures. There is no new generic controller or scheduler in this folder. `ONE_STAGE_LAUNCH_METHOD_20261027.md` gives the concrete one-stage launch and closure method. No loop or implicit queue launches the stage sequence.

`OPERATOR_STAGE_SEQUENCE_20261027.json` contains all 52 exact argv templates, their canonical hashes, original CLI source hashes, output paths, endpoint statuses, finite budgets and serial dependency IDs:26 stages/base,42 compiler/runtime invocations and10 read-only bindings. Four baseline bindings are already closed read-only PASS; six candidate bindings require native evidence. `OPERATOR_STAGE_LEDGER_INITIAL_20261027.jsonl` is the immutable initial state. Later launch/close records must be NEW files; do not rewrite this initial ledger.

The four exact baseline bindings verify pristine LP77/B78 source maps, actual main/core/compiler/flags/net, original FIRST/full current Std/raw JUnit/UCI/FMA and owned closure. Their original CLI outputs are at `/tmp/forge_sol_S12_native_20261027/*_baseline_*_arm.json`, with byte-identical copies under `source_binding_proofs/`. Each reports `REUSE_NOT_NEW_RUN`, zero engine executions/new main/FIRST/Std/JUnit, and no S11 candidate/material-key producer reuse. `source_only_binding_captures/` retains authorization, actual argv/hash, empty parent stdin, stdout/stderr and started/closed receipts. Do not rerun these binding commands into their existing paths. Later frozen consumers independently reverify the underlying evidence.

## Earliest native stage

Lprime-03 Release OFF build, then separate Lprime-04 FIRST bare11, then Lprime-05 FULL runtime-OFF Std. Budgets are900/120/600s respectively. Each invocation is selected and launched separately within the root's explicit finite grant. The stage table is a ledger, not permission to execute its later entries. B native begins only after Lprime-26 closes and under its own grants.

The exact first three argv templates are:

### Lprime-03: candidate_Release_OFF_build

```bash
taskset -c 2 nice -n 19 python -B /tmp/forge_sol_S12_native_prep_20261027/forge_sol_S12_build_native_20261027.py --execute --authorization-reference ROOT_NEW_S12_STAGE_GRANT --s11-published-commit VERIFIED_S11_40HEX --base Lprime --role candidate --feature OFF --profile Release --out /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build --cpu 2 --max-seconds 900
```

Endpoint: `/tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build/forge_sol_S12_build_result_20261027.json`; required status `PASS_BUILD_ONLY`. Template argv SHA256 `e6de02e050eafcaa4ac4c3ec3829ac470f193aba5433fc39a6ee44ff8295cb35`.

### Lprime-04: candidate_Release_OFF_FIRST_bare11

```bash
taskset -c 2 nice -n 19 python -B /tmp/forge_sol_S12_native_prep_20261027/forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference ROOT_NEW_S12_STAGE_GRANT --mode FIRST --build-receipt /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build/forge_sol_S12_build_result_20261027.json --out /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build_FIRST --max-seconds 120
```

Endpoint: `/tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build_FIRST/forge_sol_S12_runtime_result_20261027.json`; required status `PASS`. Template argv SHA256 `ea059addb6da959e690f453d8dd58ea24461e36174abac7204d33e6364474bf8`.

### Lprime-05: candidate_Release_OFF_FULL_runtime_OFF

```bash
taskset -c 2 nice -n 19 python -B /tmp/forge_sol_S12_native_prep_20261027/forge_sol_S12_qualify_native_20261027.py --execute --authorization-reference ROOT_NEW_S12_STAGE_GRANT --mode FULL --build-receipt /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build/forge_sol_S12_build_result_20261027.json --first-runtime-receipt /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build_FIRST/forge_sol_S12_runtime_result_20261027.json --out /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build_FULL --max-seconds 600
```

Endpoint: `/tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build_FULL/forge_sol_S12_runtime_result_20261027.json`; required status `PASS`. Template argv SHA256 `19b524a43ad098c214433f72b5bb616bfa5ddb132a52f1b227cd351dfe3a1747`.

Only `ROOT_NEW_S12_STAGE_GRANT` and `VERIFIED_S11_40HEX` are replaced when applicable. The actual grant text, exact S11 closure/publication reference and resulting actual argv/hash must be captured before launch. The known S12 prep commit `5e5f9294dd2acbdd5cb67276e5f476e55e5dafb0` is a source-preparation reference; it is not the still-required actual S11 closure/publication reference.

Only two original preregistered calls are superseded: Release ON and ASAN ON feature qualification use `/tmp/forge_sol_S12_ONframing_successor_20261027/forge_sol_S12_feature_qualify_successor_20261027.py`. The old strict-OFF-parser ON qualifier remains frozen failure history and is not launched. All other argv preserve the original preregistration.

## Resource and failure rules

Every compiler and runtime is a separate process, CPU2/nice19; compilation jobs1. Compiler-only CLIs set both hard and soft address-space limits at most4GiB. Never call their `main()` from the operator. ASAN FIRST/FULL/feature/helper runtime must start fresh from an owner with unlimited soft and hard RLIMIT_AS; known qualified escaped runtime is required from FIRST onward, with leak detection ON and no EPERM sandbox retry. They set `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`, clear LSAN/loader overrides and retain existing4GiB owned-RSS guards. Do not weaken leak or FP settings. Fresh FIRST is bare `bench 11` then `quit`, with no earlier native run of that main.

Stop on the first unexpected exit/status, missing endpoint, parser/hash/binding mismatch, timeout/resource/root stop or open owned group. Preserve the complete failed directory and raw captures; no automatic retry, replacement FIRST, timeout increase, known-failure change, fixture repair or continuation. Baseline RED is expected only through exact outer PASS, child rc1 and the approved17 alias/copy failures with zero waived parity failures. Candidate GREEN requires zero failures and child rc0. Five-depth counters require all five nested pair checks; bounded parity requires all three exact closed raw arms, complete byte comparisons and measured accounting. Timing and Elo are outside this lease.

`SOURCE_PREFLIGHT_20261027.json` records byte-only checks of both frozen packet manifests, all registered dependencies, complete pristine LP/B source maps, v2 engine patch, original compressed corpus and independent chess source. No test replay, compiler or engine was used. Full raw corpus inflation/sealing remains enforced by the unchanged native parity loader; it was not unnecessarily repeated here.

Root owns all Git mutations/publication/readback. All files here are local source/metadata and have mode0644. Do not alter the frozen44/32 packets or existing publication view.
