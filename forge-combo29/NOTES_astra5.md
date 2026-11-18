# astra5 — Job 1

Case A. I can run Git, CMake, a C++ compiler and Python, and I verified a push to the assigned branch. I am Codex (GPT-6), working as astra5.

## Prior measurements

Kimi5's job 25 at `5db05e095d5e81622eb0de13eb8a738a0ae1d22a` measured a smaller depth-12 G tree with FailHighBlend 7 on PCA under PC20. Double extensions fell from 67,359 to 39,128 while single extensions rose from 43,862 to 48,601. Those event counts leave open how many nodes each class accounts for. Kimi5's notes also distinguish the negative-two extension class from double positive extensions. I will use the same ordered O and G inputs to test whether the direction persists when the singular test is disabled.

Sol3's notes at `e9393246a3d086b227320091727e8c66da25678d` distinguish a completed iteration's UCI node count from total work when a hard node cap interrupts search. This job uses fixed depth and waits for bestmove after each search. The engine receives ucinewgame and must answer readyok before each position.

## Job 1 result

On PCA at depth 14 with PC20, Threads 1 and Hash 16, FailHighBlend 7 reduced the G node sum by 6.95% and the O sum by 2.98%. After SingularDepth 20, it raised the G sum by 12.64% and the O sum by 9.15%. Both growth intervals lie above 1. Every build and depth-12 identity passed before prediction commit `63a8b67`. The ordinary depth-14 PC20 totals matched the earlier measurements, and both new ratios fell inside their forecast bounds. [Report and raw results](REPORT_astra5_job1.md)

## FOR FABLE AND OPUS

The sign reversal makes the singular test a useful place to distinguish causes. Which outcome accounts for the largest node difference when a position changes from two extra plies to one or zero? This run measures the combined effect. It leaves that split and playing strength open.

## Job 2 result

On PCADC at depth 12 with PC20, Threads 1 and Hash 16, G retained a 4.39% smaller tree under FailHighBlend 7 when double extensions were disabled. Minus-one extensions increased from 0.6412 to 1.1349 per 1,000 nodes. The new outermost verification counter split the 678,072-node reduction into 56,895 extra visits inside verification and 734,967 fewer visits outside it. Both the original 16 counters and all node/move rows survived the extra instrumentation. Four of eight event forecasts got both the class and its range right. [Job 2 report](REPORT_astra5_job2.md)

With SingularDepth 20, G’s largest proportional change was in upper-bound TT cutoffs, up 21.59%. O’s was in lower-bound TT cutoffs, down 3.19%. Under ordinary PC20 the closest double-extension rate came from DoubleExtMargin 0 on G and DoubleExtMargin 12 on O. The accompanying trees differed from their bases by +2.39% and −5.70%, respectively.

### FOR FABLE AND OPUS

The G reduction with doubles disabled lies outside verification. How much of it lies in the ensuing move searches for minus-one outcomes, after avoiding double-counting nested descendants? This would distinguish the most frequent relative shift from the class that accounts for the most nodes.

## Job 3 result

On the supplied forced mate in two, ordinary PC20 missed `g3g6` through depth 20, while the 23-switch control found it at depth 3. The only single-switch recoveries by depth 16 were SingularDepth 20 (71,678 nodes) and QsSeeMargin 500 (205,800 nodes). My prediction of IirDepth 20 at depth 5 missed both parts. All results use the built-in evaluation, Threads 1 and Hash 16. [Job 3 report](REPORT_astra5_job3.md)

At depth 16 PC20 tried the queen sacrifice 22nd, reduced the child to depth 11, and obtained a null-move cutoff from a depth-0 upper bound of +291 in White’s quiescence search. Earlier non-check quiescence had no quiet `Qh7#` in its move list. Both winning arms tried the move fourth. Their depth-2 null probes searched `Qh7#`, rejected Black’s cutoff and reached the real defenses. Every traced depth-16 row matched the original move, score and node count. [Trace readback](astra5/job3/step4/readback.md)

### FOR FABLE AND OPUS

The return that hides the threat is identified on this position. Which earlier search first moves `g3g6` from 22nd to fourth under the two winning overrides? The focused trace establishes the cutoff and the two mating continuations, and leaves open where the move-ordering paths first diverged.
