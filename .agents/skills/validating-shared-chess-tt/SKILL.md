---
name: validating-shared-chess-tt
description: Use when investigating shared chess-engine transposition-table races, changing TT probe/store interfaces or replacement destinations, considering single-worker lock bypass, or validating search and TT lifecycle changes with ThreadSanitizer.
---

# Validating shared chess TT

Validate coherent entry access, search-policy preservation and storage lifetime separately. A race-free snapshot does not establish history-dependent score eligibility, faster search or stronger play.

## Practical workflow

1. **Recover actual source.** Inspect trees and patches; checkpoint documents or model results are not implementations. Record commits/diffs, callers, compiler/flags and binary provenance. Preserve rejected proposals and original failures.
2. **Synchronize every access.** Audit probe/store, hashfull, generation, diagnostics and prefetch. An escaped `TTEntry*` still exposes shared fields. Return a synchronized coherent copy with an opaque owner/key/slot/lifecycle handle; search reads the copy.
3. **Preserve selection.** Freeze the probe-selected destination through recursion/intervening stores. Apply baseline admission and move-update rules to that slot's **current** contents; never reselect at store. Test tag/empty priority, ties/age, retained moves and delayed writes. Reject default, foreign, mismatched and lifecycle-stale handles; ordinary overwrites preserve destinations.
4. **Choose synchronization by ownership.** Default Shared/SMP access keeps per-entry locks; never retain those locks across recursion or joins. A separately reviewed **explicit opt-in, exactly-one-worker lease** may retain one coarse gate across recursion when table-bound owner TLS bypasses entry locking, all stripes drain sequentially before publication, and foreign callers release their stripe before waiting/retrying. No helper launch/join occurs inside the lease. Require release/acquire publication, exception cleanup and actual-engine tests. Worker count alone permits no bypass. Follow the [ownership protocol and counterexamples](scenarios.md#bounded-owner-lease).
5. **Keep lifecycle quiescent.** Clear/resize/new_search/destruction require **every** search/helper, diagnostic, hashfull and prefetch caller stopped. Lease release or worker join can awaken foreign accessors; neither drains them. Quiesce those too before mutation. UCI uses stop → bestmove → joined worker → mutation → readiness → restart; `isready` alone never joins.
6. **Establish actual-engine evidence.** Reproduce the original race, then validate the candidate with full-engine TSan, real-table tuple stress, default Shared and opted-in/SMP paths, transitions and stop/mutation edges. Models supplement these. Inspect [TT regressions](../../../tests/tt_coherence_tests.cpp) and the [UCI driver](../../../tools/audit/run-full-engine-tt.py):

   ```sh
   python3 -B tools/audit/run-full-engine-tt.py --engine "$TSAN_ENGINE" \
     --output "$NEW_OUTPUT" --tsan-options halt_on_error=1:exitcode=66
   ```

   Use python-chess for legality. Baseline-only `--allow-tsan-exit66` requires an intact race report. Distinguish races, detector-capacity CHECKs, startup failures and deadlines; disabling checks does not validate a candidate.
7. **Validate capture and semantics.** Preserve exact input/stdout/stderr, timestamps, commands, limits, hashes, exits and incomplete stages. Missing capture/bestmove or unjoined readers fail validation. Run driver contracts, relevant complete Release/sanitizer CTests and exact cold/warm one-thread move/score/depth/node parity.
8. **Measure afterward.** Counterbalance repeated Release runs with fixed resources. Mutex-operation counts, NPS/SMP scaling and equal-clock Elo are different evidence. Use [strength validation](../validating-chess-strength/SKILL.md) before strength claims.

See [application scenarios and verification limits](scenarios.md).
