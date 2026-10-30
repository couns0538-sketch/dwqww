# Forge AL1 Bullet exporter — 2026-10-30

**Exporter and native parity qualified. Actual Bullet GPU training remains UNVERIFIED.**

Branch: `astra-bullet-export-20261030`, based on `110f0c4a819756b79a77d88a5ef525b6dafd925b`.
Target: exact AL1 source `294dbed3a15dfd821aaf9d4edc6e5f62832fd460`.
No engine, search, accepted network, or existing trainer source was changed.

The user's clarification selects the lock's shared 768→256 transform, dual SCReLU, and residual output. The lock embeds `nnue_weights.inc`, with int16 storage at scale 4096 and float32 inference. **It has no runtime `.nnue` loader.** This exporter writes its correct include format. No network was installed into a live engine or trainer.

## Deliverables

- [Exporter and reference](../tools/bullet/lock_export.py): checksum-bound Bullet checkpoint manifest, strict tensor layout and quantization, embedded include, exact float32 evaluation.
- [Original MIT-only Bullet graph](../tools/bullet/lock_graph/): graph construction, real Bullet checkpoint serialization, and bounded GPU smoke driver. Actual GPU execution is unverified.
- [Supplemental CPU smoke](../tools/bullet/train_lock_cpu_smoke.py): PyTorch implementation of the same residual architecture and loss; explicitly not Bullet training.
- [Native oracle](../tools/bullet/lock_oracle.cpp): links unchanged AL1 sources and preserves existing files.
- [Commands and format contract](../tools/bullet/README.md); tests in `tests/bullet/`.

## Results

Evidence paths below are under `validation/astra-bullet-export/`.

| Check | Result | Evidence |
|---|---|---|
| Fresh AL1 OFF d11/13/16/20/22 | PASS: 312866 / 862329 / 3024920 / 12389307 / 34048354 | `lock_native/full_engine/qualification.json` |
| Startpos5 / kiwipete5 | PASS: 4865609 / 193690690 | Same qualification and original logs |
| Whole AL1 binary FMA | PASS: 0 | Same qualification |
| Lock network through exporter/reference | PASS: 12,000 exact native residual scores | `lock_native/current_final_comparison.json` |
| Actual Bullet-written initialized checkpoint | PASS: 12,000 exact; initialized, not trained | `lock_native/bullet_initialized_comparison.json` |
| CPU-trained smoke through exporter/native | PASS: 12,000 exact, max difference 0 cp | `lock_native/sample_comparison.json` |
| Selected HCE labels against exact AL1 | PASS: all 8,192 exact | `lock_native/hce_subset_comparison.json` |
| One output weight deliberately corrupted | Negative control PASS: 9,190 mismatches detected | `lock_native/sample_one_weight_comparison.json` |
| ASan/UBSan and leak detection | PASS: 12,000 sample evaluations, no diagnostics | `lock_native/sample_sanitized_untraced_comparison.json` |
| Python and native output-safety tests | PASS: 40, no skips in root run | `final_review/suite/bullet.stderr` |
| Bullet backward graph / CPU input mapper | PASS: 2 Rust tests; 8192 rows / 64 batches; no training | `lock_gpu_driver_backward_tests.log`, `bullet_mapper_backward_smoke.stdout` |
| Supplementary R10 export | PASS: 12,000 exact; corrupted weight fails parity | `r10_parity_retry/` |
| Unchanged R10 CTest | 14/15; four existing forge_tests diagnostics | `native/ctest/` |
| Bullet GPU training, HIP, Windows runtime | UNVERIFIED | No supported GPU exposed here |
| Full private 013/014 position exclusion | UNVERIFIED here | Job 2 command must run on PC |

The sanitizer's first sandbox run failed because LeakSanitizer cannot run under ptrace. The same frozen binary passed outside that restriction with leak detection enabled. Both original results remain saved. Compiler, source, binary and build identities are in `lock_native/README.md` and its JSON receipts.

## CPU smoke scope

One complete epoch covered **8,192 saved rows**, 64 updates, one CPU thread, seed 20261030. These are real rows from filtered shard 003. This was not an epoch over all 10M rows and was not Bullet training.

Training-slice MSE changed from **0.004648477338154236 to 0.002897180728021214**. There was no heldout evaluation. This proves neither generalization nor a training or Elo gain. The objective compares `sigmoid(HCE × 2.25/400 + residual)` with `sigmoid(original STM score × 2.25/400)`, preserving residual semantics.

- Checkpoint SHA256: `8aa6f874e044c851e762ce3f56521dfe173e17d450234d31451c4226b01ad114`
- Exported include SHA256: `72f39cfe891743e27ba79c94fa2dffb0f1025ea36375a04079cb9d08668047c5`

All 8,192 CPU forward bit patterns matched the independent quantized reference. A further 446,618 quantization boundary/random cases matched. Final exporter replay reproduced the checkpoint, include and 12,000 reference outputs byte for byte. Original source, weights, selected FPOS/FHCE/FEN, indices, commands and losses are published under `cpu_smoke/`; see its `EXPORT_REVALIDATION.md`.

## License and format boundaries

Bullet is pinned to `da426a49b2a4b79a55a87031cd51c89bdf1ff030`. Its high-level `bullet_lib` wrapper pulled in GPL/AGPL format dependencies. That approach was rejected; its original attempt and dependency metadata are retained as failure evidence only. The active implementation uses the lower-level MIT compiler/trainer APIs. The reviewed 21-package closure contains no GPL, AGPL or unknown license. No GPL/AGPL source was copied into this repository. GPU SDK runtime qualification is separate.

The earlier R10 K32H3 exporter is preserved as supplementary work. Its synthetic checkpoint came from an existing R10 network, not a new Bullet training run. R10 and AL1 have different architectures and cannot share a runtime format without an explicit loader change.

## Review and continuation

The requested review completed over **24.54 minutes** (2026-10-30T09:24:49.089013+00:00 to 2026-10-30T09:49:21.552640+00:00). Repaired findings include oracle output overwrite/alias protection, quantization boundary handling and manifest validation. Job 2 independently repaired incorrect completion counts, unbound file roles, omitted binpack checks and a source-symlink identity race. Cumulative cross-shard dedup passed an additional independent recovery test. Original reproductions, fixes and rechecks are preserved; see `validation/astra-bullet-export/final_review/review_complete.json`.

The original, pre-QA Job 2 checkpoint is on `astra-fen-convert-20261030`, at **`41d23db076f1b217d90a6f26779deb7125361edc`**, with report `docs/ASTRA_CONVERTER_20261030.md`. It passed exact 1M-row binpack/Bullet-plus-sidecar checks, 45 unit tests, 13 native sanitizer tests and synthetic holdout exclusion (1000 removed, 0 remaining). This checkpoint requires the subsequent QA fixes on the same branch before PC use. Before any new training, independently verify zero overlap against both complete private holdouts using that branch's clearance tool. Only after data clearance and an exclusive GPU-free slot may the HIP smoke be run, followed by export and all 12,000 FENs. Whole-shard 013/014 exclusion follows the user's accepted policy; game IDs are not inferred. Filtered 003 must replace raw 003 in an ablation, not be appended and double-weighted.

Original progress checkpoints remain in [checkpoint history](ASTRA_BULLET_CHECKPOINTS_20261030.md). No playing-strength claim is made.

## QA follow-up: Windows launcher preparation

The old inline PowerShell recipe was replaced by
[`run_hip_smoke.ps1`](../tools/bullet/run_hip_smoke.ps1), targeting 64-bit
PowerShell 5.1. Native stdout and stderr are captured separately through
`System.Diagnostics.Process`, avoiding the PS5.1 `Stop`/native-stderr pipeline
failure. Rust **1.87 or newer** is required; 1.85 fails, and the existing
`Cargo.toml` already declares 1.87.

The launcher requires an explicit CPU affinity mask, inherits Idle priority,
uses Cargo `-j2` and `fetch --locked`, and pins the MSVC x64 target and matching
executable. The venv Python executable is an explicit path plus SHA256. Cargo
target storage, TEMP/TMP, and fresh run directories stay on F: outside the
repository, guarded by at least 20 GiB free. Missing/busy GPU telemetry and
known production processes refuse the run with exit 76. Checks repeat after
compilation immediately before the hashed smoke executable runs. Use only a
**GPU-free scheduled slot, never alongside the live AMD trainer**; snapshots
alone cannot reserve that slot. No other process is stopped or killed.

This follow-up ran **no grok-pc commands**. Windows/PowerShell execution,
priority/affinity inheritance, and HIP/GPU training remain **UNVERIFIED**.
Windows behavioral regressions are supplied but were not run because local
PowerShell is unavailable. Local evidence in
[`qa_windows_fix/`](../validation/astra-bullet-export/qa_windows_fix/) includes
two failing-then-passing portable documentation checks and **42 passing Bullet
Python/native-oracle tests** using the existing torch venv. The initial
system-Python suite failed importing the unavailable `torch`; that log is
retained alongside the successful venv run.

The original include round trip is **tensor-identical, not byte-identical**:
header lines 1–8 differ in comments and static-assert wording/formatting.
All four tensor arrays were rechecked locally. Independent QA reported
identical compiled binaries; this follow-up did not recompile that comparison.
The earlier deterministic exporter replay claim concerns the same exporter
inputs and provenance, not equality to the original include text. No engine
search, training objective, dependency graph, or accepted network changed.

IDEA_SOURCE: user job pack and clarification; Forge AL1/R10 source contracts; MIT Bullet public APIs and checkpoint format. Exporter code is original.

The earlier `final_review/final_manifest.json` is a frozen pre-QA snapshot at
`99f9d769`; it is not a manifest of the updated README/launcher. The QA follow-up
manifest records the current changed files separately. Real private 013/014
clearance remains UNVERIFIED; no new training is authorized by these test logs.


## Process and GPU policy refinement

The launcher now permits unrelated Python and compiler processes. It identifies
production jobs by actual executable basename or the actual Python script
argument: nnue-pytorch `train*.py`, selfplay, fastchess, cutechess, and defined
gate names (`gate.exe`, `gate_*.exe`). Exact `GateExeNames` / `GateExePaths`
options cover arbitrary gate binaries, while `ProductionTrainScriptPaths`
covers explicitly selected trainer scripts elsewhere. Forge/Stockfish binaries
are allowed unless selected as gates. Command-line text mentioning a production
filename is insufficient by itself; see the launcher README for full-path and
missing-command-line limitations.

Each preflight requires five valid WDDM snapshots one second apart, including
all-zero windows. It sums per-process counters only for the same adapter LUID,
physical GPU index, engine index and engine type. A 3D or Compute engine
(including `Compute0` and `Compute_0`) must exceed 2% in any snapshot to refuse;
exactly 2% passes. Separate GPUs/engines and Copy/Video utilization are not added
to that busy decision. Missing or malformed GPU telemetry still refuses.

The expanded Windows behavioral script covers boundary and aggregate cases,
separate GPUs/engines, Copy/Video, command-line false positives, exact gate and
trainer overrides, five-snapshot/four-delay timing, and a busy sample in each
of the five positions. It remains **UNVERIFIED** because local PowerShell is
unavailable. No grok-pc or GPU command was executed. Portable documentation/source
checks and their failure-before-change evidence are saved separately under
[`qa_policy_refinement/`](../validation/astra-bullet-export/qa_policy_refinement/).
Historical QA evidence is unchanged. PS5.1, pinned venv Python, Idle priority,
explicit affinity, F: scratch/target/TEMP, 20 GiB free, `-j2`, locked Cargo fetch
and explicit MSVC x64 build-target constraints remain in force.
