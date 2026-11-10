# Default-off binary identity: diagnosis and restoration

This audit checks actual binary bytes, not just search nodes. Source fixes preserve enabled behavior while restoring the locked default build.

## S3 signature correction

Source commit `6a945a4` gates the added SearchStack parameters and all call sites behind `FORGE_SPD_MATERIAL_CORRECTION_CACHE`. The exact isolated pre-S3 versus fixed-S3-off binary check and enabled 256-comparison regression are recorded in `material_cache_contract_REVIEW.md`. That isolated result alone was not proof that the entire reviewed default matched the lock.

## Remaining discrepancy identified

Rebuilt immutable lock `16833ec` and reviewed freeze `31c5d202e6662c159976a70de5803d220acee2e1` with identical compiler, flags, source directory, output path and command. The lock hash reproduced the historical `1371770e...` value, but the reviewed default was `eb9dfc03...`.

This was not merely metadata: `.text` and `.rodata` differed. Size-changing symbols were concentrated in UCI:

- New `option_name_equal`: 70 bytes.
- `main`: 15,999 → 15,925 bytes.
- `main.cold`: 1,351 → 1,281 bytes.
- `parse_limits`: 3,976 → 4,008 bytes.
- Specialized `from_chars<int>` clone: 255 → 271 bytes.

Compiling each translation unit separately at the same reused path isolated the discrepancy: **seven of eight objects were byte-identical**, including `search.o`; only `uci.o` differed. Object hashes, section hashes and symbol sizes are preserved in the `default_lock_identity_*_before.json` files. `default_lock_identity_objects.sh` reproduces the object comparison against that specific pre-F6-fix freeze.

The F6 comparison wrapper changed default-off string operators/code generation even though its result remained case-sensitive. A snapshot experiment gated the helper entirely behind F6 and used the original string comparisons through a default-off macro. That alone restored the full lock hash, including all sections and metadata. Source commit `f1e6fbcf843ceddbf6e6a70f60ec9794c629ec8b` applies this proven guard after the F4 searchmoves fallback correction, without modifying its region.

## Scope

The identity claim applies to the recorded GCC 14 strict-FP x86-64-v4 Linux build with all new switches left at their default off values. It is not a claim of Windows/Clang binary parity or equality when a candidate switch is enabled. Candidate speed and strength remain UNPROVEN.

## Final result

Fresh exact-path rebuild of immutable lock and final source freeze `f1e6fbc` **passed byte-for-byte comparison**, including the F4 restricted-root fallback fix. Both full executable SHA-256 hashes are:

`1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`

`default_lock_identity_results.json` records the revisions, hash, byte-comparison result and scope. Compiler/command provenance is in `default_lock_identity_provenance.txt`. The command template lists the source glob; the reproduction script expands `src/*.cpp` identically in the same reused source directory for both builds.

```sh
bash forge-combo29/tests/material_cache_lock_identity.sh \
  f1e6fbcf843ceddbf6e6a70f60ec9794c629ec8b \
  /workspace/shared/forge-build/final-lock-identity-fixed
```

F6-enabled regression also passed. Rebuilt the final snapshot with the same strict-FP flags plus `-DFORGE_FIX_UCI_OPTION_CASE=1`, then ran `uci_option_case.py` against final default-off and F6-on executables. Default-off ignored noncanonical option names; F6-on recognized mixed-case NNUE, multiword options, tunables, Hash and Threads. Full check output is in `default_lock_identity_f6_check.log`; its enabled binary hash is recorded in the final result receipt. S3-enabled behavior remains covered by the separate 256-comparison receipt above.
