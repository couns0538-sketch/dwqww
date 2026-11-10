# BoundNone disproves occupied-prefix early termination

**Classification: disproved optimization premise, not a new engine bug.**
Production behavior and public API semantics are unchanged. The existing probe
correctly finds occupied entries after a hole. Stopping the hit scan at the
first unoccupied slot would break that behavior.

## Executed counterexample

The new `boundnone_hole_preserves_later_hit()` test in `tt_contract_test.cpp`
uses only public TT operations, with valid fresh handles and no concurrency:

1. Construct a 1 MB table. Keys A/B/C are chosen to share cluster 0 with distinct
   verification tags on both multiply-high and modulo-indexing targets.
2. Store A with BoundExact at depth 5; it occupies slot 0.
3. Store B with BoundExact at depth 5; it occupies slot 1.
4. Probe A and store it with BoundNone at the same depth. Its admitted payload
   makes slot 0 unoccupied while slot 1 remains occupied.
5. Verify A is a miss with an unoccupied first-slot snapshot and that actual
   probe(B) is still a hit, preserving B's score/eval/move.
6. Model first-empty termination over those first two observed entries: it
   returns a miss before reaching B. This is a test-side hypothetical scan,
   not a modified engine probe.
7. Verify a miss for C still selects the first hole; refill it and verify
   both B and C remain hits.

Both NOTLS builds printed exactly:

```
PASS BoundNone hole: first_slot_occupied=0 later_B_hit=1 hypothetical_first_empty_hit=0 refill_preserves_B=1
```

The complete contract suite also passed in both modes, including the existing
four-thread × 5000-iteration concurrent payload test. No TSan diagnostic was
reported. Raw logs are `tt_contract_boundnone_notls0.log` and
`tt_contract_boundnone_notls1.log`.

## Source locations

At audit tree `63875630fc3c30b58866818f23a4296fb0703963` (these TT regions
remain unchanged in the subsequent documentation-only tree):

- `include/forge/search.hpp:97`: BoundNone is a declared enum value.
- `include/forge/search.hpp:113`: occupied means bound != BoundNone.
- `src/search.cpp:367–377` and `440–450`: same-depth store admission succeeds;
  assigning BoundNone clears the occupancy-defining low bits.
- `src/search.cpp:327` and `408`: hit scans correctly inspect all four entries.
- `src/search.cpp:342` and `423`: only after no hit does the replacement scan
  return the first empty slot.

The store API does not reject BoundNone or document a nonzero-bound-only
precondition. A closed-world nonzero-store invariant may describe internal
search usage, but public callers can create holes before even an exclusive
search begins. It cannot justify changing the exposed probe semantics.

## Reproduction and provenance

From `forge-combo29`:

```sh
tests/tt_contract_check.sh /tmp/tt-boundnone-hole
```

GCC 14, C++20, O1, ThreadSanitizer, assertions enabled, strict FP, pthread,
non-PIE and portable slider/NNUE paths; full flags are in the existing script.
Both FORGE_SPD_TT_NOTLS=0 and =1 were executed with review switches default-off.

- NOTLS 0 binary SHA-256: `2e003557bc566f0c0e7a0b9a7ce40cf9079f947b6ee9a907fd6ff381c1c5fbb8`
- NOTLS 1 binary SHA-256: `71b87f6cd136343d701f479c69b753d230dc907b07f2606a087d7b9254e02a6d`

This finite sanitizer run supports the test execution; the sequential
counterexample itself is sufficient to disprove the proposed universal
invariant. No timing, strength benefit, production optimization or new flag
is claimed or implemented.
