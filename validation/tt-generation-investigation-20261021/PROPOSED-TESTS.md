# Proposed TT generation-refresh regressions

Unapplied test-only patch against actual `tests/tt_coherence_tests.cpp`; no engine implementation, CMake change, compilation or execution. The existing eight groups remain unchanged. The production policy is an intentional replacement/admission/hashfull change, not a proven playing-strength gain.

## Inputs and static validation

- Base test SHA256: `a9aebd7b41c3acfcd7cb3b044cbc7811aa6bf963d7b86499fb9f51b45d42a127`.
- Proposed test patch SHA256: `130191680bdfbf947c0284a1d8ff8f39e1e831f11f480ccc321ed66dcc6b1b7d`.
- Expected resulting test SHA256: `cc2fe3e9fb0059f409876345e8cfb3c008ede401751a4dad76b022f743238fd5`.
- `patch --dry-run --fuzz=0 -p1 < validation/tt-generation-investigation-20261021/proposed-test.patch`: exit0, `checking file tests/tt_coherence_tests.cpp`; no offsets/fuzz. This checks applicability only. Source/static review checked every TTEntry field, the real store guard and the two collision-index paths.
- All test APIs are the public real TT APIs. No private exposure, fake table, raw pointer, engine interface/layout change or concurrent lifecycle mutation.

## Added groups (planned, not observed)

1. `test_generation_refresh_payload_and_handles`: all six occupied bound/PV combinations; old hit updates generation while retaining key, move, score, eval, depth, rule50 context, padding and lower three flags; prior local snapshot remains old; repeated current hit is stable. A shallow nonexact same-key store with no move retains the old move and admitted payload; with a nonempty move it changes only the move. A pre-new_search handle and a refreshed handle paired with another key remain rejected.
2. `test_generation_refresh_misses_and_zero_key`: empty zero-tag probe stays empty/unrefreshed; genuinely occupied key0 refreshes; a matching BoundNone tag remains a miss and retains its old generation and payload. Two consecutive occupied-victim misses must return the same unchanged first victim. This detects miss-refresh even when a single refreshed entry would be hidden by integer hashfull rounding.
3. `test_generation_refresh_replacement_hashfull_and_wrap`: old depth12 A initially ties three current depth8 entries under depth-minus-four-age. A miss initially selects A. Reusing A makes all four current (hashfull0→1 permille), and the next miss selects B; storing through that handle evicts B and retains A/C/D. Generation31→0 refresh preserves the payload/flags and old snapshot; the old lifecycle handle remains rejected.

4. `test_generation_refresh_concurrent_aged_hits`: four generation0 correlated entries are aged quiescently to generation1. Two readers refresh disjoint initial keys before a barrier releases the writer, proving all four old-hit paths execute before any overwrite. Then one writer and two readers perform 10,000 iterations each while a fourth thread samples hashfull128 times; tuples and returned generation1 are checked, final hashfull is1 and the saved old snapshot remains generation0. No lifecycle operation occurs concurrently. All original concurrent stress remains unchanged.

The proposed main invokes twelve groups and prints exactly `All12 TT coherence/regression groups passed\n` on success. Future pipeline parsers must expect12 after integration; frozen22 receipts correctly retain8. There is no new CTest target/count change.

## Existing expected-policy audit (base source line numbers)

- Lines137–144: retain existing old-entry eviction expectation. The old key is never hit between new_search and replacement, so it must still age and be evicted.
- Lines203–214: retain existing hashfull/wrap expectations. Immediately after new_search there were no hits, so hashfull stays0 (line208). The later helper stores are BoundExact and remain admitted even though their probes now refresh first (lines209–210).
- Lines147–181: retain default/foreign/mismatched and lifecycle-handle rejection cases. A generation refresh cannot revive an old epoch or change private owner/key/slot metadata.
- Line273: retain concurrent tuple expectation generation0. This group never calls new_search; adding generation-refresh policy does not change its generation. All existing tuple/coherence stress remains intact.
- Line303: only the success-summary count changes8→12; no old assertions are weakened or removed.

The historical actual baseline `table_fixture.cpp` intentionally demonstrated repeated old hits remaining old and age-only admission. Preserve that executed evidence unchanged: those are precisely the old policy observations the new groups intentionally reverse. This proposal does not alter old receipts or infer speed/Elo from those observations.

## Execution boundary

Only static patch applicability was checked. Parent owns integration and first actual baseline/candidate tests, Release/sanitizer suites, source freeze and any strength experiment. No actual result is claimed for these additions. Test failure under the old policy is expected at the first old-hit refresh assertion, but has not been executed here.
