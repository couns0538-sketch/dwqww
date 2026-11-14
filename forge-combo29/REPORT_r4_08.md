# R4-08 Finding 7 — SingularDepth 2 drops into quiescence

Base: `e04556ddc` (`e04556dd`). Branch: `grok47/r4-08-audit-f7`.
Source of the finding: `audit/lock-source` at `302a08a27`, finding 7, proof `forge-combo29/tests_audit/proof_singular_depth2_qsearch.cpp`.

## Bug

`SingularDepth` is advertised with minimum 2 (default 7). At depth 2 the singular verification used

```text
singular_depth = (depth - 1) / 2   // 0
```

`Worker::search` returns `qsearch` when `depth <= 0`. `qsearch` never reads `ss->excluded_move`, so the verification probes the node's own transposition entry, sees a score inside the singular window, and can return `singular_beta` without searching another move. That leaves the seeded depth-1 entry in place.

## Reproduction on the base, before the fix

The audit proof, compiled and run on `e04556ddc` with `-fsanitize=address,undefined`, printed:

```text
SingularDepth=7 (default): child TT depth_after=2 score=1795 (searched normally to depth 2)
SingularDepth=2 (UCI min): child TT depth_after=1 score=1850 (qsearch cut off on child's own unexcluded TT entry -> false multi-cut skipped depth-2 search!)
```

The position is `6k1/5ppp/8/q7/Q7/8/6PP/6K1 w - - 0 1`, root depth 3, searchmoves `h2h3` and `g2g3`, child (after `g2g3`) seeded with move `a5a4`, depth 1, bound lower, score 1850.

## Fix

`forge-combo29/src/search.cpp`: the verification depth is `std::max(1, (depth - 1) / 2)`. Depth 2 stays in `search()`, which skips `excluded_move` and does not cut off on the excluded node's own TT entry.

Singular search only runs when `depth >= SingularDepth`. The default is 7, and `(depth - 1) / 2` is already at least 3 there, so the clamp does not change the default tree. No UCI option was added. `CMakeLists.txt` was not edited. No `FORGE_*` value was changed.

## Checks

`forge-combo29/tests_r4_08/r4_08_test.cpp` was built from the lock definitions in `CMakeLists.txt` (unchanged values) with `-fsanitize=address,undefined`. Failed checks return non-zero.

After the fix, that run printed:

```text
SingularDepth=7 child TT depth=2 score=1795
SingularDepth=2 child TT depth=2 score=1792
pins bench11 312866 bench13 862329 perft5 4865609
PASS pins 312866 862329 4865609
PASS 200 depth-10 searches, every reported move legal
PASS r4_08
```

`SingularDepth=2` now stores a depth-2 child entry (score 1792) instead of leaving the seeded depth-1 score 1850. Each of the 200 depth-10 searches had a legal best move and a legal PV. Bench 11, bench 13, and perft 5 stayed on the pins. AddressSanitizer and UndefinedBehaviorSanitizer reported no error. Exit code 0.
