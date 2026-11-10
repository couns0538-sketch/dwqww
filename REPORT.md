# Forge combo29 review checkpoint

Reviewed source: `16833ecc03b425586f91f4c8834dea8807bf4c22`, branch `lock/combo29-20261110`, verified before work. Review branch: `dot/review-20261110`. This is an interim report; no Elo or speed claims. All proposed changes and ideas: **UNPROVEN** pending full acceptance gates on the tester PC.

## Verified cloud baseline

Linux g++ 14, C++20, strict FP, x86-64-v4, all six combo29 speed/build switches from CMake. Clang and CMake not installed here; direct g++ build succeeded. Embedded net SHA-256 must match lock before candidate testing. Windows executable was not fetched.

- Start-position perft 5: 4,865,609.
- Kiwipete perft 4: 4,085,603.
- NNUE on bench 11/13: 312,866 / 862,329 (matches documented pins).
- NNUE off bench 11/13: 375,354 / 907,205 (matches documented pins).
- Independent board-only ASan+UBSan harness: 17,401 positions, 499,310 moves, 100 seeded random games plus corners; no diagnostics. Checks generated legality, gives_check, make/unmake, FEN/hash roundtrip. Harness used default header switches, not full lock switches.

These are this cloud machine's results, not tester-PC validation or a speed result.

## Findings

### F1 HIGH: stale helper node counters (high confidence; source-proven)
`forge-combo29/src/search.cpp:1509-1510,1804-1809`; counters reset inside each worker after dispatch. Main sums counters at 881-886 and tests budget at 896, so a helper not yet scheduled may contribute last search's count. Known issue confirmed, not a new discovery. Minimal fix: synchronously reset all published counters before any helper launch. Regression: seed old helper counts and hold helper admission while main enters small node-budget search. Patch pending. Status UNPROVEN.

### F2 MED: returned SMP nodes omit helper tail (high confidence; source-proven)
`forge-combo29/src/search.cpp:1734-1735,1812-1815`: result.nodes is captured before helper shutdown/join. Minimal fix: sum final counters after joining. Regression: compare SearchInfo.nodes with final worker counters. Patch pending. Status UNPROVEN.

### F3 MED: external stop can be overwritten (high confidence; API-level)
`forge-combo29/src/search.cpp:1811-1814`: stop snapshot/temporary set/restore can overwrite a concurrent stop request made during helper join. UCI's independent stop_requested mitigates CLI consequences. Fix requires separating internal shutdown from external cancellation or explicit latched reset ownership. Regression: inject stop during helper shutdown barrier. Patch pending. Status UNPROVEN.

### F4 MED: helper launch is not exception-safe (high confidence; exceptional path)
`forge-combo29/src/search.cpp:1803-1809`: later thread-construction failure or exception from main search destroys joinable threads and terminates. Helper exceptions likewise terminate. Proposed scoped stop/join and exception transport. Test injected thread creation failure. Patch pending. Status UNPROVEN.

### F5 LOW: first-use attack initialization is not thread-safe (high confidence; latent API issue)
`forge-combo29/src/bitboard.cpp:136-139`: unsynchronized bool marks initialized before shared table construction. Current UCI builds Board before spawning workers, so not demonstrated as current CLI failure. Minimal fix std::call_once. Test synchronized concurrent first Board constructions in a fresh TSan process. Patch pending. Status UNPROVEN.

No TT race established under documented quiescent lifecycle contract. No legal-position move-generation defect established by this audit.

## Corner FENs verified

- Exclude g5f6 EP: `8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1`.
- Include e5d6 EP check evasion: `4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1`.
- Both white castles: `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1`.
- Four a7a8 promotions: `4k3/P7/8/8/8/8/7p/4K3 w - - 0 1`.
- Double-check king evasions e1d1/e1f1/e1f2 only: `4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1`.

## Ideas, UNPROVEN

- Bit-exact root effort move-to-slot mapping instead of linear lookup, search.cpp:1399-1402.
- Bit-exact cache of material-count correction key, search.cpp:800-807,854,867; invalidate for captures/promotions/unmake.
- Search change: helper schedule diversification, only after accounting fixes.
- Eval/search change: non-pawn or continuation correction history beyond current pawn/material contexts (850-867).

## Commit list and remaining work

Initial documentation checkpoint: this commit. Source unchanged. Subsequent report updates will enumerate patch commits. Still pending: deterministic search regressions, small default-off patches, all ten bench pins, UCI edge cases, and additional full-source review. 12k bit-exact, ABBA, SPRT are not run here.
