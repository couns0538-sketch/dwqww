Read-only peer review by /root/see_candidate_review/pin_mask_proof after the
single bounded run:

> Raw evidence supports the causal claim.
>
> Both builds record exactly one depth-1 info line and identical pre-gate
> state: ply1, no check, alpha/static evaluation578, beta32001,
> futility base738.
>
> Source16 fails SEE at -40 and skips b1b8:2 nodes, score-578, PVg8h8.
> Source17 passes, searches b1b8, and returns859:3 nodes, score-859,
> PVg8h8 b1b8.
>
> Both processes exited cleanly within their deadlines. Records show the
> same trace search object in both cores, preserving their respective Board
> objects.
>
> This demonstrates the intended qsearch branch change on one forced
> fixture. It provides no best-move selection, speed, or playing-strength
> evidence.

The same peer reviewed the frozen drivers before execution and found no
instrumentation/execution blocker. The runner collected depth1 info lines
without asserting their count; post-run raw inspection and
POST-RUN-VERIFY.json close that reporting gap with exactly one per build.
