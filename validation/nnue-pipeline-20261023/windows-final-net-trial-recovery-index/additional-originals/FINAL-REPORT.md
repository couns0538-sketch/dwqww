# Final frozen-network Windows Zen 5 trial

**PASS, trial only.** Source commit `6e9622fd5be18e0155fc3ed5fcf6c4586705cca6` differs from baseline `1ab50b2d` only in `src/nnue_weights.inc`. All 74 exported source files remained unchanged during qualification. Network SHA256: `a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7`.

All 14 original checks passed: nine C++ test executables through Wine and five host Python, tool, UCI, ponder and OwnBook checks. The only OwnBook adaptation translates Linux-created book paths to Wine Z: paths in an evidence copy. The original script and assertions remain unchanged.

The executable is AMD64 PE with standard Windows system/UCRT imports. Actual vector arithmetic checks passed with no emitted FMA. All 18 compile records contain the strict Zen 5, no-fast-math, no-contraction, no-LTO and C++20 flags.

Selected-network Windows inference parity passed **2,048/2,048 exact integer scores**, with zero feature mismatches and maximum error 0 cp. The separate Linux actual-core parity also passed 2,048/2,048 exact scores; its original proof is in `../final-net-native-parity-attempt1/`.

The first actual Windows bench11 signature was **378,596 nodes**, and the fresh-process repeat matched. No old-network node count was imposed. Post-closure checks confirm the first-bench, final and delivered engine SHA256 are identical. No test or engine was retried.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Tested Windows executable | 1,939,456 | `2adc0429d238208ae9ae1a7788d6c570d9eb649b58c737bd8358d6004703518e` |
| Trial ZIP | 13,008,348 | `276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca` |

Package: `/workspace/forge-nnue-handoff-20261023/forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip`. All 309 payload hashes and archive CRC were verified after creation. It contains the tested executable, selected weights/checkpoint, MIT/runtime notices, exact clean source, tested helper executables/core/objects, original commands/streams/receipts and manifests.

Qualification session 63296 and packaging session 72226 both exited 0; their outer stderr streams are empty. Individual unit-test stderr retains genuine unittest summaries. The live default shipped network remains unchanged. Root owns Git publication; this task performed no Git writes.

These results establish Wine correctness, inference parity and repeatability. There were no timed Wine matches, native Windows/physical Ryzen tests, calibrated speed measurements, Elo results or Stockfish comparisons. Next, root verifies and publishes these exact bytes and evidence, then hands the trial to the user's native and strength QA.

The independent Windows-runner source review is at `../windows-final-net-runner-source-review-attempt1/`. It found no first-run blocker and identified two preservation/identity boundaries: reuse of the same failed-attempt directory could overwrite FAILED.json, so this attempt was never rerun; final executable identity must equal the first bench freeze, which the post-closure checker verified. One pre-execution package patch failed its context match and made no edit. Independent archive inspection is recorded separately.
