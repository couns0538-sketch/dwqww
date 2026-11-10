# Direct transposition-table contract screen, 2026-11-10

## Results

Both `FORGE_SPD_TT_NOTLS=0` and `=1` pass the ordinary contract suite under
GCC 14 ThreadSanitizer. Each executes four threads × 5,000 probe/store
iterations against colliding keys, with zero incoherent payloads and no
sanitizer diagnostics. The recorded runs observed 18,620 and 18,566 hits;
misses from concurrent eviction are legitimate and the exact counts vary.

A separate UBSan edge probe **fails in both modes**: an occupied same-key
non-exact store with `depth=INT_MAX` overflows before clamping. This is a
**LOW public-API edge**, not a demonstrated normal-search defect. No production
change was made in this task.

## Ordinary suite coverage

- Default handles, foreign-table handles and mismatched-key stores rejected.
- Stale handles rejected across clear, resize and new_search, with all lifecycle
  operations performed while accessors are quiescent.
- Probe snapshots remain unchanged after subsequent stores.
- 64 generation transitions verify wrapping, hit refresh and rejection of an
  old handle even when its generation number wraps back to the original.
- Four occupied entries in one cluster; depth and age replacement; storing via
  a probe whose replacement slot was displaced by an intervening store.
- Rule-50 usability matrix for stored/current clocks 0–110; capped high clock.
- Score/eval clamping at INT_MIN/INT_MAX, depth clamping at -1000/1000, bound/PV
  fields, shallow rejected-score updates and preservation of an existing move
  when an admitted same-key store supplies Move::none().
- Concurrent exact stores plus probes validate coherent score/eval/move/depth,
  rule50, bound, PV and generation payloads. Occasional hashfull readers run
  concurrently too. No clear/resize/new_search runs during the concurrency test.

An initial test-marker generator sometimes created `from==to` moves. Forge
correctly treats those as Move::none() and preserves an older move for the
same key, invalidating the test's whole-payload assertion. The generator was
corrected to always produce non-none markers. The partial-update behavior is
explicitly tested separately; that initial failure was not an engine race.

## Confirmed API-edge overflow

Minimal sequence: construct TT; store key K at depth 100; obtain a fresh probe
for K; store K with BoundLower and depth INT_MAX. The replacement predicate
contains `depth + 4 > entry->depth` before depth is clamped to [0,255].

UBSan reports signed overflow and exits 1 at search.cpp:403 (NOTLS=0) and
search.cpp:334 (NOTLS=1), in the source tested here. Optimized diagnostics print
`2147483647 + 3`; the source predicate is `depth + 4 > entry->depth`.

Confidence: high for the public API reproduction. Normal engine search depths
are bounded; no UCI route to INT_MAX depth at this call was demonstrated.
A minimal prospective correction is
`depth > static_cast<int>(entry->depth) - 4`, which retains the comparison for
ordinary inputs without overflowing. Both duplicated store implementations
would need the same opt-in change. Fix implementation is deferred to review.

## Build and commands

Engine source last modifying commit at this screen:
`25d8bd9cc1832d72e27893c998d8f576b0006ff7`; TT code is unchanged from the lock.
All review fix switches remain default-off in these focused builds. Public
probe/store calls are exercised in both NOTLS implementations; private owned
calls are not forced through unsupported APIs. Full-engine lease coverage is
recorded separately in the SMP TSan screen.

GCC 14.2, C++20, O1, debug symbols, pthread, frame pointers, strict FP,
NNUE hidden 256, portable slider/NNUE paths. The TSan builds use non-PIE.

```sh
# From forge-combo29; expected exit 0 in both NOTLS modes:
tests/tt_contract_check.sh /tmp/tt-contract
# Separate known edge reproduction; expected nonzero before a fix:
tests/tt_contract_extreme_check.sh /tmp/tt-extreme
```

Raw logs are `tt_contract_notls{0,1}_tsan.log` and
`tt_contract_extreme{0,1}_ubsan.log`; hashes are in `tt_contract_results.json`.
Finite sanitizer checks are not a proof of all interleavings or all integer
inputs, and make no speed or strength claim.
