---
name: validating-shared-chess-tt
description: Use when investigating shared chess-engine transposition-table races, changing TT probe/store interfaces or replacement destinations, or validating multithreaded search and TT lifecycle changes with ThreadSanitizer.
---

# Validating shared chess TT

Validate coherent entry access, search-policy preservation and storage lifetime separately. A race-free snapshot does not establish history-dependent score eligibility, faster search or stronger play.

## Practical workflow

1. **Recover actual source.** Inspect fetched trees and patches before reconstructing work. A branch containing `STATUS.md` or model results is not an applied engine implementation. Record full source commits/diffs, API/call-site changes, compiler/flags, binaries and hashes; preserve rejected proposals and failed attempts. Verify source-to-binary provenance, not just two unrelated hashes.
2. **Find every shared access.** Audit probe, store, search callers, hashfull, generation, diagnostics and prefetch. Returning `TTEntry*` after unlocking still exposes shared fields. Copy a coherent value under synchronization; carry an opaque destination handle with private owner/key/slot/lifecycle identity. Search reads the local copy; store reacquires synchronization before accessing storage. Never hold locks across recursion or worker joins.
3. **Preserve probe-time selection.** For a synchronization-only change, freeze the originally selected slot through recursive/intervening stores. At store, apply the baseline admission and move-update rules to that slot's **current** contents. Reselecting a victim at store changes search policy even with one thread. Check matching-tag-before-empty, first-empty, replacement ties/age, retained moves and delayed stores. Reject default, foreign, key-mismatched and lifecycle-stale handles; ordinary slot overwrites do not invalidate the destination.
4. **Keep lifecycle quiescent.** Clear, resize, new_search and destruction require all search/helper, diagnostic, hashfull and prefetch callers stopped. Handles cannot outlive their table. Entry locks do not make arbitrary concurrent resize safe. In UCI, use stop → bestmove → joined-worker barrier → mutation → readiness → restart; `isready` alone does not join. Exercise Hash/Threads changes, Clear Hash, ucinewgame and process restarts.
5. **Establish actual-engine RED/GREEN.** Reproduce the original race in an instrumented full engine, then repeat the workload with the candidate. Real-TT tuple stress supplements full-engine searches; a model-only pass cannot replace them. Use small Hash, Threads=4, OwnBook=false and finite node limits, observing info/hashfull and legal bestmoves. Inspect [TT regressions](../../../tests/tt_coherence_tests.cpp) and the [UCI evidence driver](../../../tools/audit/run-full-engine-tt.py):

   ```sh
   python3 -B tools/audit/run-full-engine-tt.py --engine "$TSAN_ENGINE" \
     --output "$NEW_OUTPUT" --tsan-options halt_on_error=1:exitcode=66
   ```

   Use Python with python-chess installed for legality. Baseline-only `--allow-tsan-exit66` accepts an actual data-race report as partial failing-control evidence, never a completed workload. Startup mapping failure or exit66 alone establishes neither a race nor race freedom.
6. **Validate the validator.** Preserve separate exact stdout/stderr/input bytes, timestamps, command/limits, hashes, exit and incomplete stages. Capture errors, missing bestmove, deadline, unjoined reader or sanitizer report cannot become a pass. Run driver contract checks and the complete relevant CTest suite; compare deterministic Threads=1 scores, moves, depths and nodes against the identical pre-change base.
7. **Measure only after correctness.** Counterbalance repeated Release measurements at 1/2/4 threads with fixed resources. SMP move differences are expected; NPS/scaling and equal-clock Elo are separate results. Use [strength validation](../validating-chess-strength/SKILL.md) for games and acceptance claims.

See [application scenarios and verification limits](scenarios.md).
