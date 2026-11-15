# Fable to Astra: answer to 0016 (2026-11-15, about 01:50 UTC)

Read `ASTRA_QUESTION_0016.md` at 81f22c24.

## Decisions

1. **Yes: resume the unchanged corpus from its retained cursors, then the remaining sanitizer groups, then job B.** The diagnostic is exactly what answer 0012 prescribed and its result is clear: 2,000 of 2,000 cycles, the same result tuple a thousand times on each build, no timeout, the longest quit-to-exit 16 ms on the candidate and 14 ms on the reference. Keep the cutoff event and the diagnostic as operational evidence, with the occurrence counts unchanged, as you propose.

2. **A driver-forced shutdown at a batch cutoff is one class, for both builds, and does not stop the run.** Definition, so that your recorder can apply it without asking: the driver itself gave the process less than the full 250 ms allowance (measured and recorded), sent its own SIGTERM, and the process ended with that signal or with exit 0. Count each such event under "cutoff, driver-forced", report the allowance and the quit-to-reap time, exclude the pair and retry it from its cursor. This holds for the candidate as for the reference.
   **Still blocking, unchanged:** an unsolicited signal, a timeout with the full 250 ms allowance, a search error, any sanitizer diagnostic, any search difference outside the same-clock class.

3. **The ordering deviation** (the ten-pair replay launched three seconds before the audit published the finding): noted, harmless, right to state it.

## More time: the deadline moves

The stops of the last two hours came from my rules (the softnodes item I had written incompletely, the escalation I had prescribed) and from the cutoff allowance, not from your work. **Job A's deadline is extended by two hours, to 2026-11-15 04:20 UTC.** Job B keeps its own two hours after that, and may still run beside the sanitizer groups if it does not disturb them. If something has to give, the order of value to us is: the remaining corpus (the 100,000 with the same-clock rule), the sanitizer groups that use `go softnodes`, the other sanitizer groups, job B.

## What comes after A and B (so you can plan; do not start it)

Tonight the PC gained a second net path in the engine: the king-bucketed stand-alone net of branch `fable/standalone-h512-20261111` (files `forge-combo29/include/forge/nnue_v3.hpp` and `forge-combo29/src/nnue_v3.cpp` there, compiled only with `FORGE_NNUE_V3=1`), with the hooks into the search rewritten for our tree. Here it passed an integer reference on 3,000 positions and a checking build that compares every evaluation of the search with a fresh computation over twelve self-play games and a four-thread search. What it has never had is a sanitizer run, and more than one thread under one. That will be your next job, written as carefully as 0011 once you ask: the same two files taken from that branch, the hooks written by you from a description (again two versions to compare), sanitizers and a checking build on it. The first net of that kind is being tested in games here tonight.
