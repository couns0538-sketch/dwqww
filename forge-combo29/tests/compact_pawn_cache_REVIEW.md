# Compact PawnEntry layout experiment

Source freeze: `703562d301d7a52111fa218ce0311141baf3eeb7`.

**Default off. UNPROVEN for speed or playing strength.** The measured footprint change applies to the tested GCC 14 x86-64 ABI, not every platform.

## Change and compatibility

Only `include/forge/eval.hpp` changes. `FORGE_SPD_COMPACT_PAWN_CACHE=1` moves `valid` into the padding after `score`. The `#else` contains the original struct declaration verbatim. No evaluation arithmetic, cache capacity, key/index rule, network, parameter or default value changes.

Enabled layout changes **both the public type's ABI and positional aggregate-initializer order**:

- Off: `key, score, passed, valid`; size 40; valid offset 32.
- On: `key, score, valid, passed`; size 32; valid offset 12.

All translation units and external consumers must use the same macro setting. Previously compiled consumers and positional aggregate initializers are not automatically compatible. The audited repository's source uses named accesses and value initialization (`PawnEntry{}`), not positional nonempty aggregate initialization or serialized layout. This does not establish compatibility with unknown external code.

On this platform, key/score/passed offsets remain 0/8/16 and alignment remains 8. Static assertions verify standard layout, trivial copyability, sizes and offsets in both modes. The unchanged 32,768 entries consume 1,310,720 bytes off and 1,048,576 bytes on: **262,144 bytes less per Evaluator**, excluding vector-object/allocator overhead. This is a storage reduction, not a speed percentage.

## Focused cache contract tests

Both modes pass 4,105 board checks using fixed seed 20261110. Each check compares cached evaluation, a repeated hit, and runtime-PSQT evaluation against the uncached HCE oracle.

Targeted cases cover:

- Valid matching-key hits, established by deliberately changing a cached score and verifying the hit does not rewrite it. Poisoned results are not compared to the oracle.
- Wrong full-key misses at the same index, with score/passed fields poisoned before reconstruction.
- Invalid matching-key entries and clear/value initialization across all entries.
- A real pawnless board with pawn key zero, including invalid zero-key poison and subsequent valid uses.
- A deterministic pair of legal positions with distinct full pawn keys mapping to slot 9376, exercised A→B→A. FENs are in the unit receipts.
- Copy assignment and named-field preservation.
- 4,096 randomized legal positions with repeated invalidation/restarts.

## Reproduce

Requires GCC 14 and x86-64-v4 support:

```sh
CXX=g++-14 bash forge-combo29/tests/compact_pawn_cache_check.sh \
  /workspace/shared/forge-build/compact-pawn-cache
```

The recipe snapshots only `forge-combo29/src` and `forge-combo29/include` from the frozen commit. It builds isolated off/on engines, runs each focused unit and full pin suite, runs the 128-FEN × two NNUE-mode equivalence screen, checks the immutable-lock default-off hash and runs the enabled unit with ASan+UBSan. All other new switches remain off. A separate combined configuration is validated by the parent review.

The standalone test uses a test-only access-control override for private cache internals; no production hook is added. ASan's leak detection is disabled because LeakSanitizer cannot operate under this environment's ptrace. Address/undefined-behavior checks remain enabled and nonrecovering.

## Completed isolated validation

- Both off/on builds passed all ten locked NNUE-on/off depth pins (11, 13, 16, 20, 22), plus start-position perft 5 = **4,865,609**.
- **256/256** fixed-depth comparisons passed across 128 FENs with NNUE both on/off, matching nodes, score, PV, depth and best move.
- Focused off/on units each passed **4,105 checks** and all static layout assertions.
- Enabled ASan+UBSan unit passed **4,105 checks** without diagnostics; leak checking remains unverified.
- The compiled default-off executable was compared directly, byte for byte, to the verified immutable-lock executable and matched. Both SHA-256 hashes are `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.

`compact_pawn_cache_results.json` preserves binary hashes, unit/collision receipts, raw pin outputs and the byte-comparison result. `compact_pawn_cache_equivalence.json` preserves every position result and binary/fixture hashes. `compact_pawn_cache_use_audit.txt` records source-type usages at the frozen commit.

No timing conclusion is drawn from benchmark times retained in raw pin output. The candidate is still **UNPROVEN** as a speed or playing-strength improvement.
