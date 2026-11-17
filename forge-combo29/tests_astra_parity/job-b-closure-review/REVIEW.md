# Independent Job B closure helper review

READY as tooling; this does not mean the current experiment is eligible to close. Reviewed close.mjs and closure-model.mjs with their pinned protocol, accounting and evidence-integrity dependencies. Verified all 7 frozen source/external pins. Independently reran 13 pure/history checks and three syntax checks; all passed. Exact command and actual output are retained in VALIDATION.txt. No close or check command was executed by this reviewer.

Closure requires 6000 credited games, or actual Date.now() strictly later than the declared deadline minus 470 seconds (2026-11-15T04:59:00.313Z). Reaching a target or passing that threshold never overrides native activity, an occupied root active slot, an incomplete recorded match batch, or unreceipted raw batch artifacts. Merely prepared unused plans are identified separately and contribute no games.

The helper checks receipt order and hashes, declaration/source/tool/input pins, prior receipt links, retained summary-derived counts, immutable proof equality, and both text package reconstructions for every row. It verifies non-overlapping native process windows and reconciles reconstructed totals to root matchTotals. It checks state/declaration hashes again before emitting closure evidence, while root must continue to serialize scheduling and state updates.

The only proposed state key is jobBClosure; it is written as a proposed patch file, never applied by this helper. Existing closure cannot be overwritten. No sanitizer acceptance, raw failure, global stop or other experiment state is modified. Fault observations remain separated by side and category rather than conflating a disconnect with its associated process death.

Timing fields distinguish last native completion, sum of native batch process wall times, declaration-to-native-stop elapsed time and declaration-to-closure elapsed time. The report explicitly makes no claim of two continuous hours of play, reports the game shortfall and optional unrun leg, and makes no strength or speed conclusion.

Limits: package-check logic was reviewed; this reviewer did not execute the full closure checker, real evidence close, native program or engine. The validation read current recorded match rows and reconstructed counts only. Run-time eligibility must be checked again against the actual clock, active processes and state when root chooses to close.
