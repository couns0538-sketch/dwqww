# MovePicker self-swap guard experiment

Source freeze: `fccd2c79c8367f577ebe4ed6d54b556555f94cce`.

**Default off; UNPROVEN for speed or strength.** The earlier 37.53–39.20% source-level self-swap frequency motivates a testable guard, not automatic acceptance.

## Source change

`FORGE_SPD_PICKER_SELF_SWAP_GUARD=1` guards only the existing `std::swap` in the first-four selection path with `best != index_`. The default-off branch retains the original statement. The strict greater-than scan, tie policy, std::sort comparator/call, sorted-tail transition, returned move and index increment are unchanged. No score calculation, field layout, sorting policy, constant or network changes.

Scored entries contain a trivial four-byte Move and four-byte int on the tested platform. There are no custom move/assignment side effects to preserve when swapping an object with itself. The source change adds eight lines in the picker region only; unrelated TT work was separately committed before this freeze and remains disabled in isolated builds.

## Adversarial ordering/data test

Each of four configurations passes **36,474 fixtures and 1,060,531 pick calls**, comparing the actual implementation with the locked unconditional-swap algorithm after every selection. Every returned move bit, index, sorted flag and all bytes of the entire 256-entry scored array must match, including untouched prefixes/suffixes.

Fixtures include exhaustive scores {-1,0,1} for lengths 1–8, all-equal scores, ascending/descending values, alternating INT_MIN/INT_MAX, tie-heavy/random values, prefixes 0/7/128 and randomized prefixes, consumed offsets through five, the fourth-selection-to-sort transition, already-sorted state, singleton lists and lists up to full capacity. Random seed: 20261110.

Configurations:

- SPEED2=1, BADCAP_PREFIX=0, NO_ZERO_MOVELISTS=2.
- SPEED2=0, BADCAP_PREFIX=0, NO_ZERO_MOVELISTS=2.
- SPEED2=1, BADCAP_PREFIX=1, NO_ZERO_MOVELISTS=2.
- SPEED2=0, BADCAP_PREFIX=1, NO_ZERO_MOVELISTS=0.

A test-only access override exposes the implementation-local MovePicker; no production hook is added. The engine integrations below exercise the two SPEED2 scoring paths in real search, beyond the direct selection fixtures.

## Reproduction

```sh
CXX=g++-14 bash forge-combo29/tests/picker_self_swap_check.sh \
  /workspace/shared/forge-build/picker-self-swap
```

Requires GCC 14 and x86-64-v4. The script explicitly snapshots only `forge-combo29/src` and `forge-combo29/include` from the frozen commit and uses strict floating-point flags. The unit includes that snapshot's search.cpp via its explicit include path; it does not accidentally compile the current working-tree implementation. No Windows executable or bundled input is used.

The isolated engines change only the guard switch within each SPEED2 configuration. All other new candidate/fix switches remain at their default off settings. Timing is not measured in this correctness script.

## Completed isolated validation

- Four picker configurations passed the final fixture source, including explicit full-256-element and last-slot singleton cases. Each passed **36,474 fixtures / 1,060,531 calls**.
- SPEED2=1 off/on engines each passed all ten locked depth pins (11/13/16/20/22, NNUE both modes), plus start-position perft5 = **4,865,609**.
- SPEED2=1 guard off/on passed **256/256** depth7 position/configuration comparisons; SPEED2=0 guard off/on independently passed **256/256**. Both compare nodes, score, depth, PV and best move across the same 128 FENs and both NNUE modes.
- Default-off SPEED2=1 executable compared directly byte-for-byte equal to the immutable lock, SHA-256 `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Enabled ASan+UBSan with SPEED2=1/BADCAP_PREFIX=1/NO_ZERO_MOVELISTS=2 passed the final **36,474 fixtures / 1,060,531 calls**, with no diagnostics. Leak detection was disabled because LeakSanitizer cannot operate under this environment's ptrace; leak checking remains unverified.

`picker_self_swap_results.json` preserves final unit/source/binary hashes, pin receipts, the direct byte-comparison result and sanitizer receipt. Two `picker_self_swap_equivalence_speed*.json` files retain all position results and per-build hashes. Earlier fixture runs were extended with explicit boundary cases before these final receipts; all four unit configurations and the sanitizer ran the final fixture source.

No speed conclusion follows from the correctness results or timings incidentally printed by pin checks. A guarded branch can cost more than a trivial self-swap; any diagnostic timing must be separately coordinated and interpreted conservatively. No automatic promotion is authorized.
