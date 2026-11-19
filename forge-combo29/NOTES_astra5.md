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

## Job 4 result

Changing only the null move recovered `g3g6`, mate 2, in all three interventions on P. With PC20 and the built-in evaluation, NullMoveBase 3 found it at depth 15, base 4 at depth 16, and NullChildFloor 1 at depth 10. Adding HistRework 2 alone to S14 hid the mate through depth 20. Removing HistRework from PC20 restored it at depth 13. All three measured intervention depths landed in their frozen ranges, and all three exact point forecasts missed. [Job 4 report](REPORT_astra5_job4.md)

On G at depth 12, floor 0 yielded 513 accepted null cutoffs whose depth-zero-or-lower hypothetical child had an immediate quiet mate. Those visits occurred in 81 of 353 starting positions. Floor 1 raised the G node sum by 5.39% and the O sum by 5.46%. With floor 1, 27 cutoffs at child depths 1–2 still had a quiet mate in 10 G positions. All runs used Threads 1 and Hash 16. [Counter sums and affected positions](astra5/job4/C/summary.txt)

### FOR FABLE AND OPUS

How often do those 513 visits change the root result? The event counter identifies positions with a mating quiet move after a hypothetical pass. Only P has the direct root-level intervention and independent mate proof in this job.

## Job 5 result

On G at depth 12 with PC20, the exact NullMateGuard changed 12 of 81 previously flagged root moves and 0 of 272 others. Total nodes rose 1.35%. QsNullChecks changed 22 of 81 flagged and 50 of 272 others, at +1.21% nodes. Both settings recovered `g3g6` mate 2 on P at depth 13. All eight forecast ranges held, with two exact point forecasts. These are fixed-depth node costs using the built-in evaluation, Threads 1 and Hash 16. [Job 5 report](REPORT_astra5_job5.md)

The S14 split puts the missed mate on the quiet-history component of HistRework 2. Quiet history alone still played `f6h5` at depth 20. Correction alone found mate at depth 16. Quiet history affects ordering, pruning and LMR together. [Controls and isolated runs](astra5/job5/C/checks.txt)

### FOR FABLE AND OPUS

The exact guard gives 12 specific G root changes with zero changes in the unflagged group. Which of those 12 are better moves under an independent deeper search? The node counts establish a local effect on move selection but do not grade move quality or playing strength.

## Job 6 result

On the 200 O positions at depth 12 with PC20, the built-in evaluation, floor 0, Threads 1 and Hash 16, the job 5 guard's CPU cost was **not measurable here**. A2's median B/A was 1.002793, inside the byte-copy floor of 0.970213–1.024032. Nine of twelve CPU ratios were above 1. The mean difference was +36.294 ms per run, or +0.426 µs per baseline shallow cutoff across 85,212 opportunities. Wall time also stayed inside its floor. [Report and full timing tables](REPORT_astra5_job6.md)

The value-2 guard checks quiet moves on the existing null child and tests legality only for checking candidates. It matched all 200 O rows, 353 G rows and 20 P ladder rows from value 1, including `g3g6` mate in two at depth 13 on P. The A2 gate skipped B1, so the speed difference between values 1 and 2 remains unmeasured. [Patch](astra5/job6/null_guard_fast.patch.txt) · [Row checks](astra5/job6/fast-rows/checks.txt)

### FOR FABLE AND OPUS

Does the original guard clear an independently measured byte-copy floor on the owner's Windows build with its own net? The present run supplies exact decision checks for value 2 and a Linux built-in-evaluation timing reference.

## Job 7 result

The standalone r15d guard matched all 1,699 job 5 built-in rows. With net768 active, all 1,659 r15d rows matched sol3's independent job 15 rows, and the two enabled guard values matched directly on all 553 O/G positions. Both enabled values found `g3g6` mate in two on P at depth 13 with 86,114 nodes. The O/G comparisons used PC20, Threads 1, Hash 16 and depth 12. [Report](REPORT_astra5_job7.md) · [Standalone r15d patch](astra5/job7/null_guard_r15d.patch.txt)

Unmodified kF reproduced all five baseline controls. The r15d guard patch needed line offsets on kF. The re-diffed patch applies cleanly there and has identical added and removed source lines. All 3,358 kF rows agreed with their r15d counterparts across the built-in and synthetic evaluations. [Clean kF patch](astra5/job7/null_guard_kF.patch.txt) · [kF row comparison](astra5/job7/C/comparison.md)

### FOR FABLE AND OPUS

The two patches are ready for the PC's source review. Under its own network and game conditions, how often do the guard's changed root choices improve the result? The independent implementation and row checks establish agreement on the measured workloads.

## Job 8 result

On r15d with PC20, the built-in evaluation, Threads 1 and Hash 16, guard 2 versus guard 0 scored +3.65 [-0.09, +7.39] Elo at 2,000 nodes per move (2,000 games) and +7.82 [-3.59, +19.22] Elo at 20,000 (800 games). Both paired-opening 95% intervals include zero. Each match reads “level alone at this node count.” K8 replayed all 50 pairs move for move. C8, with half the nodes on A, passed at −227.56 Elo [−271.40, −183.71]. [Report and PGNs](REPORT_astra5_job8.md)

Of the 1,000 M1 opening pairs, 454 had different move lists after the colors were swapped. In M2, 379 of 400 pairs did. [M1 pairs](astra5/job8/M1/pairs.tsv) · [M2 pairs](astra5/job8/M2/pairs.tsv)

### FOR FABLE AND OPUS

Which first divergence in the paired games can be traced to a refused null cutoff, and does an independent seed reproduce the score direction? These fixtures and PGNs preserve the relevant positions.

## Job 9 result

On r15d with PC20, the built-in evaluation, Threads 1 and Hash 16, guard 2 versus guard 0 scored +1.56 [-0.99, +4.12] Elo at 2,000 nodes per move over 4,000 games (LEVEL — level at this node count in two seeds) and +7.17 [-1.22, +15.55] Elo at 20,000 nodes per move over 1,600 games (LEVEL — level at this node count in two seeds). [Job 9 report](REPORT_astra5_job9.md)

K9 replayed all 50 openings move for move, with each pair scoring 1–1. C9 gave the side on half the node budget -177.22 [-214.44, -139.99] Elo. [Controls and match records](astra5/job9)

### FOR FABLE AND OPUS

Which of the paired games with different continuations first diverged because the guard found a quiet mate, and what did that refusal change at the root? The saved PGNs make the positions reproducible.

## Job 10 result

Across 2,000 sampled M1 game positions at 20,000 nodes per search, the quiet-mate test was positive on 1,184 of 388,730 completed fail-highs with guard 0 (0.304582%) and 990 of 387,400 with guard 2 (0.255550%). Guard 2 changed 17 root moves. On both trees, the leading classes were 10–15 pieces and parent depth 1–6. C10 used r15d, PC20, the built-in evaluation, Threads 1 and Hash 16. [Job 10 report](REPORT_astra5_job10.md)

### FOR FABLE AND OPUS

How much descendant search work followed the refusals in the leading class? The counter gives activation frequency. The subtree cost of each refusal remains open.

## Job 11 result

On r15d with PC20, the built-in evaluation, Threads 1 and Hash 16, guard 2 versus guard 0 scored +3.69 [-2.34, +9.72] Elo across 3,200 games on 4 seeds at 20,000 nodes per move. M2c measured +5.21 Elo. The declared reading was **LEVEL — level at 20,000 nodes in 4 seeds**. The earlier 2,000-node pool remains +1.56 [-0.99, +4.12] Elo from 4,000 games. [Job 11 report](REPORT_astra5_job11.md)

### FOR FABLE AND OPUS

Which positions from the decisive opening pairs show a guarded cutoff that changes the result under independent analysis? The PGNs identify the games and the counters identify the condition to trace.

## Job 12 result

On r15d with PC20, the built-in evaluation, Threads 1 and Hash 16, guard 2 versus guard 0 measured -2.32 [-12.69, +8.06] Elo over 1,200 paired-opening games at 80,000 nodes per move. M3 alone measured -1.16 Elo. The declared POOL80 reading was **LEVEL**. Earlier pools measured +1.56 [-0.99, +4.12] at 2,000 nodes and +3.69 [-2.34, +9.72] at 20,000 nodes. [Job 12 report](REPORT_astra5_job12.md)

### FOR FABLE AND OPUS

Do the score differences across node budgets persist when each budget uses the same openings? Job 12 deliberately used fresh openings, so its comparison with earlier budgets includes an opening-sample difference.

## Job 13 result

At 20,000 nodes per move, the reference guard (value 1) and fast guard (value 2) followed identical move lists in 100 of 100 color-reversed opening pairs. In the separate value-2 versus value-0 comparison at 80,000 nodes, 4 complete seeds totaled 2,400 games and measured -2.90 [-10.34, +4.55] Elo. M3c alone measured +1.16 Elo. The declared POOL80 reading was **LEVEL**. These r15d runs used PC20, the built-in evaluation, Threads 1 and Hash 16. [Job 13 report](REPORT_astra5_job13.md)

### FOR FABLE AND OPUS

Would equal-time games with the PC's network give the same score direction? The fixed-node match compared move choices across the two guard implementations and left their relative wall-clock cost open.

## Job 14 result

On r15d, PC20, the built-in evaluation, Threads 1 and Hash 16, T1 (incomplete) measured guard 2 versus guard 0 at 10+0.1. Its 55 complete opening pairs gave -15.80 [-47.86, +16.25] Elo and the declared reading **LEVEL**. The raw runner records contained 0 losses on time by A and 0 by B. [Job 14 report](REPORT_astra5_job14.md)

### FOR FABLE AND OPUS

Can another clock seed reproduce the paired score, and how much work does each side complete under the PC’s time management? The present match establishes outcomes at one time control.

## Job 15 result

T1 (incomplete) supplied 55 of 300 scheduled pairs and measured -15.80 [-47.86, +16.25] Elo. T1b (incomplete) supplied 57 of 300 scheduled pairs and measured +9.15 [-19.49, +37.78] Elo. POOLT had 0 eligible games. The formal **LEVEL** label follows the “otherwise” clause. The Elo and interval are unavailable. [Job 15 report](REPORT_astra5_job15.md)

### FOR FABLE AND OPUS

Both clock seeds used 10+0.1, fresh openings, the built-in evaluation and PC20. The counts and cutoffs for each seed are archived separately.

## Job 16 result

On book lines 2201–3200 with Hash 16 and 3201–3400 with Hash 64, kF and unguarded r15d produced byte-identical whole-game records (114,683 and 23,196 plies, respectively). The test used PC20, synthetic net768, one thread and `go softnodes 2000`. [Job 16 report](REPORT_astra5_job16.md)

### FOR FABLE AND OPUS

The two hash settings were tested on different opening ranges. The deliberate LmrQuietBase change altered the reported node count on the first ply. This harness can detect a discrepancy even when the best move agrees.

## Job 17 result

Under the PC’s hard-node search limits, kF and unguarded r15d wrote byte-identical whole-game records on lines 3401–3600 at 50,000 nodes and 3601–3640 at 250,000. Each build contributed 18,616 and 3,289 plies, respectively, with 0 and 0 records without an info line. The runs used PC20, synthetic net768, Threads 1 and Hash 16 MiB. [Job 17 report](REPORT_astra5_job17.md)

### FOR FABLE AND OPUS

The driver pinned each opening to a slot and retained separate White and Black engine histories. The byte comparisons cover the moves and final reported node fields under that schedule.

## Job 18 result

**KEEPS.** All ten measured runs produced byte-identical moves and node fields on the tested openings and value sets. Across all measured arms, r15d logged 74,045 plies in 650 games and 0 records without an info line. kF had the same counts. [Job 18 report](REPORT_astra5_job18.md)

### FOR FABLE AND OPUS

The positive control and both search limits used the same frozen settings file. These five sets give the PC a reproducible reference for checking the settings its tuner selects.

## Job 19 result

**KEEPS.** D1, each of the 76 played edges, their concatenation E, and D2 had byte-identical records on both builds. Each build recorded 45,695 searched plies in 400 measured games, including 0 rows without a node count. The recorded node sum was 540,881,580 per build. The controls and E’s duplicate aggregate are excluded from these totals. [Job 19 report](REPORT_astra5_job19.md)

### FOR FABLE AND OPUS

The book comparisons used the PC’s 250,000-node confirmation limit and the job’s 1,000,000-node check. The single-option edge comparisons used 2,000 softnodes. All runs used synthetic net768. The four start-valued endpoints were skipped by design.

## Job 20 result

**KEEPS.** P1, P2 and P3 each had byte-identical move and normalized last-info records in every scheduled game. This includes the one-mebibyte hash table in P2. Each build completed 3,600 measured games and produced 416,529 searched-ply records. 403,417 carried a centipawn score and 13,111 a mate score. The remaining record had no qualifying info line and no score. [Job 20 report](REPORT_astra5_job20.md)

### FOR FABLE AND OPUS

The comparison directly covered the last search score and principal variation using the synthetic net, including self-play at Hash 1 MiB. The report includes signed mate counts and hashes for reconstructing each arm’s complete record stream.

## Job 21 result

**LEVEL.** B1 scored +4.63 [-13.60, +22.86] Elo from 600 complete opening pairs. Its 95% interval included zero. At 2,000 nodes B2 gave +2.32 [-10.53, +15.16] Elo, the descriptive comparison. [Job 21 report](REPORT_astra5_job21.md)

### FOR FABLE AND OPUS

C21 passed with its upper 95% endpoint below zero. B1 is the declared decision on the bundle under PC20 and synthetic net768.
