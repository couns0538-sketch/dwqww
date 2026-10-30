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
| Python and native output-safety tests | PASS: 40 at this review checkpoint | `final_review/suite/bullet.stderr` |
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

The requested 20-minute review is still open at this checkpoint. Repaired findings include oracle output overwrite/alias protection, quantization boundary handling and manifest validation. Job 2 independently repaired incorrect completion counts, unbound file roles, omitted binpack checks and a source-symlink identity race.

Job 2 is on `astra-fen-convert-20261030`, with report `docs/ASTRA_CONVERTER_20261030.md`. Next: finish review, run the isolated HIP smoke on the PC, export its checkpoint and check all 12,000 FENs, then run position dedup against the complete private holdouts. Whole-shard 013/014 exclusion follows the user's accepted policy; game IDs are not inferred. Filtered 003 must replace raw 003 in an ablation, not be appended and double-weighted.

Original progress checkpoints remain in [checkpoint history](ASTRA_BULLET_CHECKPOINTS_20261030.md). No playing-strength claim is made.

IDEA_SOURCE: user job pack and clarification; Forge AL1/R10 source contracts; MIT Bullet public APIs and checkpoint format. Exporter code is original.
