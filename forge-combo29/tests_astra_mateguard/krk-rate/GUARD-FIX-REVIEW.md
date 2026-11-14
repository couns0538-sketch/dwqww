# Read-only ancestor-guard review

The retained correction changes only the process-overlap scan: it derives the caller's own PID ancestry from /proc/PID/stat and excludes that ancestry. The final ')' parsing correctly locates the state and parent-PID fields even when the process name contains spaces or parentheses. The exact independent suite/focused/rate command checks and failure behavior remain unchanged. The prior scan excluded only the current PID, so a timeout parent whose argv retained run-next.mjs could reject its own child before any trial launch.

The captured recurrence's full stdout/stderr match their metadata hashes and its exit is 1. It ended 2026-11-14T22:53:27.294Z, before the first successful schedule at 2026-11-14T22:53:55.385Z. The original failed controller invocation is retained, not counted as a completed native trial. The correction and original source are both preserved.

The current runner exactly matches its inert twin and the immutable schedule pin. The fixed deadline is 2026-11-14T23:23:55.385Z; the start guard remains 465000 ms against a 450000 ms outer bound. Review reconstructed the prior source by reversing only the ancestry change, obtaining byte equality; the exact diff is adjacent. No source/test/engine change or new execution was made for this review. Active rate trials and their statistical interpretation are outside this code review.
