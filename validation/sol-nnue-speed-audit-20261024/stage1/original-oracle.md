# Unchanged original native snapshot comparison

Both unchanged drivers were linked to the frozen actual OFF/ON cores. The existing OFF binaries were reused read-only after confirmation from million_oracle; only ON counterparts were compiled here. Compiler: g++ (Debian 14.2.0-19) 14.2.0. Flags: `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread` (ON additionally `-DFORGE_AVX512=1`). Compilation, execution and comparison were sequential, one process at a time.

| Original driver | OFF/ON cmp | Bytes per output | Identical SHA-256 |
| --- | --- | ---: | --- |
| `nnue_snapshot.cpp` | exit 0 | 41903752 | `c084e1f2c0115a5cbd19a9d9083ef1faf93c3174024ecc01c7863f70ab32df13` |
| `nnue_update_snapshot.cpp` | exit 0 | 8132420 | `e19ca668172c80b9f11bf16844805df53c8b2a683f7ef6a31337cc22bd5e219d` |

`nnue_snapshot.cpp`: 20,226 complete accumulator/evaluation records, plus 100,000 finite synthetic activation evaluations. Count is derived from the unchanged driver format and output byte length; this driver does not print a stderr coverage summary.

`nnue_update_snapshot.cpp` stderr, identical OFF/ON and independently verified against the serialized coverage trailer:

```text
cases=1644 snapshots=3940 parent_checks=1644 in_place_checks=1644 synthetic_cases=992 all_dirty_masks=31 special_move_coverage=both_colors
```

The update stream contains 3,940 snapshots: 1,644 distinct updates, 1,644 in-place updates, 10 starting refreshes and 642 post-move refreshes. Every serialized accumulator valid flag is 1. Both colors exercise king- and queen-side castling, en passant, all four quiet promotions and all four capturing promotions. Every one of the 31 dirty-count/flag patterns has at least 32 synthetic cases. Recorded nonsticky MXCSR is 8064 (`0x1f80`, round-to-nearest with FTZ/DAZ disabled). These results cover finite values and the default recorded rounding mode; no NaN or alternate-rounding claim is made.

Exact commands, zero return codes, source hashes, both core archive hashes, reused and compiled binary hashes, and output hashes are in `receipt.json` and `commands.json`. Driver source hashes, executable hashes and core hashes were unchanged before/after. Both frozen-driver files also byte-match the production-tree originals. All four original binary streams are retained losslessly as read-only deterministic gzip archives; driver stderr and empty successful cmp stdout/stderr remain uncompressed. Original logical paths in receipts resolve through the storage mapping described below.

No production files, Git state, core libraries or reused OFF binaries were modified. No NPS or Elo result is inferred.

Storage update: large closed raw representations are now losslessly archived after full gzip roundtrip SHA-256/size and duplicate byte proofs. Original logical paths in the receipts map to read-only `.gz` archives through `/workspace/forge-sol-nnue-speed-audit-20261024/avx512-agent/closed-evidence-restore-map.json`. See `/workspace/forge-sol-nnue-speed-audit-20261024/avx512-agent/COMPRESSED_EVIDENCE.md` for exact restoration instructions.
