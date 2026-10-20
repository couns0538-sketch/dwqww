# Production integration addendum

**No implementation blocker found in the reviewed one-line candidate. Full native/Windows gates remain pending.** This is a feedback/regularization/range strength ablation, not a proven EMA bug repair or accepted strength improvement.

Read-only scope: compared the current CMake, `src/`, `include/`, `tests/` and `bench/` bytes with `validation/promotion-see-20261020/native/frozen-source-47f0560.tar`; inspected the new regression against the actual-method probe. No engine, build, test, match or Git command was run. Root identifies `b5908f0` as the integration base with the same engine bytes as47f0560; this review independently checks those frozen engine bytes, not Git ancestry/index cleanliness.

Across27 existing scoped files, the only changes are:

- `src/search.cpp`: precisely the approved assignment, `entry = clamp(entry + diff * weight / 256, ...)`, matching the probed candidate hash. Residual calculation, table keys, material coefficient, caller guards, depth gain and both written clamps are untouched.
- `src/uci.cpp`: candidate version17→18 only.
- `CMakeLists.txt`: version17→18 plus the new core-linked correction-history executable and CTest registration.
- One added file, `tests/correction_history_tests.cpp`; no scoped deletion or unrelated engine change.

The test calls the actual private correction methods through the existing `SearcherTestProbe` friendship. Its expectation code is the candidate-only specialization of the54-check arithmetic probe; it removes the selectable EMA mode instead of changing engine logic for testing. It retains signed/one-two-table/weight/clipping/rounding/side-isolation/shared-material/saturation/unequal-entry controls. There is no copied correction implementation as the tested system. CMake links `forge_core` and `Threads::Threads`, inheriting the public C++20 and sanitizer requirements, and adds one test to the existing nine when Python suites are available.

**Small nonblocking test robustness issue:** `find_material` records `check(count == 1)` but continues. If a future regression produces zero material writes, it returns `CorrectionSize`; later `material(..., index)` may index out of bounds. Fail/throw immediately when the index-discovery invariant fails before using that index. Current valid-fixture checks are unaffected; this is a test diagnostic-path improvement, not another engine change. Root was notified; this review does not edit the test.

The regression specifies the selected arithmetic semantics. Passing it cannot establish superiority over the EMA, production guard coverage, reliable timed play or Elo. Its full-search consequences still require the pending exact-source regression/UCI/Windows gates and a separately authorized fresh paired experiment. Changed search nodes/scores are expected. Preserve the old source17 and failed hosted attempt; do not treat version18 alone as authorization to retry that attempt.

Reviewed SHA256 identities:

| File | SHA256 |
|---|---|
| `src/search.cpp` | `5cba75f2227d4e69cff8769a18785c2c55c899d5e6bd96c0c58b5368b6322225` |
| `tests/correction_history_tests.cpp` | `ed59bc0163b07aa459148c9f1ae30ea4f3e15fabd3dc026be3383f8454314b27` |
| `CMakeLists.txt` | `74370919e516674b3bc839bf5bd5b73b0e15a02f28d5cde76b3ca614ccc20011` |
| `src/uci.cpp` | `a7cb09c22fbcd4ca2f0ad63c64c5208fd18a1b5d01b64edeb3e6f878da6d6fa8` |

These identities delimit the review; a later test-only early-failure guard needs its own recorded hash/check, without reopening the unchanged engine assessment.

## Final child review: fc51e43

Root reports final source pin `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`, preserving the initial integration commit. Independently inspected the new guard:

```cpp
if (count != 1) throw std::runtime_error("material-slot discovery failed");
```

It executes after the recorded invariant check and before returning/using the discovered index, so both zero-write and multiple-write discovery failures now stop safely. Removing exactly this added line from the current test bytes reproduces the previously reviewed test SHA256 `ed59bc0163b07aa459148c9f1ae30ea4f3e15fabd3dc026be3383f8454314b27`. The final test SHA256 is `3f5523ac462cde0a36ce3df4f5bfb99e59dbe34a08c9e2d06dcb9ecad5dad66d`; production search remains `5cba75f2227d4e69cff8769a18785c2c55c899d5e6bd96c0c58b5368b6322225`.

**The test robustness finding is resolved. Final disposition: no remaining implementation/test-review blocker for this pinned candidate; full exact-source native/Windows validation and strength qualification remain separate and pending.** This was a read-only byte/guard check, not a test execution or independent Git ancestry verification.
