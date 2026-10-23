# Independent Windows artifact review

Status: **PASS**.

The immutable ZIP is `276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca` (13,008,348 bytes). CRC passes, all 309 payload hashes/sizes match, and all 198 outer producer-seal records match. The shipped executable, current build executable, first-bench freeze and RESULT all bind `2adc0429d238208ae9ae1a7788d6c570d9eb649b58c737bd8358d6004703518e`.

All 74 archived source files equal the exact clean Git blobs at `6e9622fd5be18e0155fc3ed5fcf6c4586705cca6`; only the three declared historical Python bytecode files are omitted. The exact baseline diff changes only `src/nnue_weights.inc`. The packaged source and weights bind the chosen include `a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7` and FREEZE `3d945dc1f0e20d3469791eeb36b9ad5b23a1e70c87f6615703d0fda3442e211c`.

All 14 original test receipts report actual exit 0, no timeout and reaped processes: nine Windows C++ tests under Wine and five Python/tool/adapter checks. First/repeat raw bench11 logs both record 378596 nodes; the first signature was frozen before the repeat. The original Windows parity result records 2048/2048 exact integer scores, 0 cp maximum error and zero feature mismatches; raw rows and child receipts match.

The ZIP executable independently parses as AMD64 PE32+ with only the 13 recorded system imports. The original disassembly stream contains the recorded YMM operations and no FMA instructions. All 18 recorded compile commands contain the required strict flags.

This review ran no engine, build, tests, training or model-loss computation. Qualification is through Wine and host Python. This is a trial; native physical Windows/Ryzen validation, speed and Elo acceptance remain unproven. The reviewer authored the earlier native parity probe, not the Windows runner or package.
