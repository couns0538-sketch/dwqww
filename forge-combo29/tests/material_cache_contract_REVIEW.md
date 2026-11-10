# S3 default-off source and binary contract

The original S3 experiment changed `corrected_eval` and `update_correction` signatures/call sites even when its switch was off. The unused SearchStack argument violated the requested default-source contract. Source fix `6a945a4` puts both augmented declarations, definitions, and all three calls behind `FORGE_SPD_MATERIAL_CORRECTION_CACHE`; the `#else` branches restore the original signatures/calls exactly. The candidate remains default-off and **UNPROVEN** as an optimization.

## Isolated identity check

`material_cache_contract.sh` archives the pre-S3 source (`25d8bd9^`), builds it, applies only the original S3 production diff plus the signature fix, and builds default-off again. Both builds reuse the same source directory and identical GCC 14 strict-FP x86-64-v4 command, compiler, and output path. All binaries are copied aside before the next build.

Result: **byte-for-byte identical** pre-S3 and fixed-S3-off executables, both SHA-256:

`eb9dfc03aba50d5875300ea378cbb1b06c361f11ed2a330e7da6d740cbca2275`

The enabled fixed-S3 binary retained the original enabled candidate hash:

`59b7b3b619e83020168a83d879bf2717427a195047fc9fb4e3f6e60c2f39b067`

The enabled build also passed **256/256** depth-7 comparisons across 128 FENs with NNUE on/off, matching nodes, score, depth, PV and best move against the pre-S3 binary. Detailed receipts are committed in `material_cache_contract_equivalence.json` and `material_cache_contract_hashes.txt`.

```sh
bash forge-combo29/tests/material_cache_contract.sh /workspace/shared/forge-build/s3-contract
```

This isolates S3 and does **not** establish that all other default-off review changes are byte-identical to the immutable lock. The broader check uses `material_cache_lock_identity.sh FINAL_FROZEN_COMMIT OUTPUT_DIRECTORY`, archives lock `16833ec` and the supplied frozen review commit, and builds them at the same reused path with the same command. That separate result must be reported on its own merits; historical binary hashes from different commands/paths are not substitutes.
