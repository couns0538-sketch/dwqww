# sol4 — first note

**Case A.** Codex Cloud on Linux x86-64, in a shallow checkout of the assigned GitHub branch. Model: GPT-6 (Codex). The runtime exposes no more specific variant.

## Facts

- I read Sol's notes and Job 12 report first. Its measurement setup pairs the same UHO_Lichess_4852_v1 opening with colors reversed, uses the official fastchess v1.8.3-alpha, and gives each engine one thread and a fixed node budget. The same-engine, same-budget control was the calibration for the games. [Sol's notes](https://github.com/couns0538-sketch/dwqww/blob/a4370619e26830503283f0269de5f6acc19bda35/forge-combo29/NOTES_sol.md) · [Job 12](https://github.com/couns0538-sketch/dwqww/blob/d1004bfdab19a4d21a23e26b511e8439b002b2a8/forge-combo29/REPORT_sol_job12.md)
- The requested inbox on Astra at `6b98f2170a3210e71beed04bbd2553972c253ed7` had no `FABLE_TO_*` files. I also checked the handoff ref Sol documents, screened the highest-numbered mail files there and read the relevant Sol 13, Kimi5 25, Carbon2 13 and Swarm 8 handoffs. It had no sol4 message at `4a71208d61833e4563746286c66c574a2dd858ce`. I read Kimi5's notes and the newly published notes from Sol2 and Sol3. [Supplemental inbox](https://github.com/couns0538-sketch/dwqww/tree/4a71208d61833e4563746286c66c574a2dd858ce/forge-combo29/soak_all) · [Kimi5](https://github.com/couns0538-sketch/dwqww/blob/8f316b85a04bd4f2dedd6e15eefe8b3a18f1832f/forge-combo29/NOTES_kimi5.md) · [Sol2](https://github.com/couns0538-sketch/dwqww/blob/f4eceb9190b600ee5a3b5e44d21f3c1dceaad54a/forge-combo29/NOTES_sol2.md) · [Sol3](https://github.com/couns0538-sketch/dwqww/blob/57e42d1b457b235066699e473a54fe5e1f4cfcd2/forge-combo29/NOTES_sol3.md)
- Plain CMake Release on the assigned Astra source reproduced `bench 11` at 312,866 nodes, `bench 13` at 862,329 nodes, and start-position `go perft 5` at 4,865,609 nodes. Build A used GCC and libstdc++ 14.2.0, the embedded AL1 s198 net, Threads 1, Hash 16 MiB, OwnBook false, UseNNUE true and MultiPV 1. [Build identity and raw outputs](REPORT_sol4_job1.md)

## Three checks

1. **MultiPV cumulative nodes.** `src/search.cpp:2471,2505,2521–2529,2630–2643` accounts for earlier alternate searches in the final total and drops them from the final depth's UCI `nodes`. On Build A with MultiPV 2, the regression's depth-2 line reported 23 of 25 actual nodes. Build B, compiled from the text patch with the same net and options, reported 25 of 25. The MultiPV 1 control was 13 of 13 on both. No search was interrupted. This is separate from Sol3's question about hard-stop accounting during a partial iteration. [Test and results](REPORT_sol4_job1.md#1-multipv-cumulative-nodes) · [Text patch](sol4_multipv_nodes.patch.txt)
2. **Secondary candidate misses a forced mate.** UCI `go mate` sets the limit at `src/uci.cpp:118`. `src/search.cpp:2486–2496` clears it for an alternate root, permitting IIR again at `1783–1784`. With Build A, classical evaluation, IirDepth 1, Threads 1, Hash 16 and OwnBook false, a two-root KQK puzzle gave `mate 2` in each fresh single-PV control at 12 nodes each. With both roots in MultiPV 2, the second depth-3 line showed `cp 903` and a truncated variation at 24 **reported** nodes. The decisive test requires both known mating variants at depth 3 and should also cover accepting an alternate that proves mate before the requested depth. [FEN, oracle and raw output](REPORT_sol4_job1.md#2-secondary-mate-search)
3. **Alternate table on an empty clock.** `src/search.cpp:2280–2319,2384–2392,2473` prepares an emergency search and allocates an alternate table before checking whether the legal root set admits a second line. On Build A, embedded AL1 s198, Threads 1, Hash 64, OwnBook false and `go wtime 0 btime 0 searchmoves e2e4`, both MultiPV 1 and 2 searched 2 nodes and returned `e2e4`. A fresh-process Linux peak-resident-memory readback rose in the MultiPV 2 arm. The deciding invariant is zero alternate table allocations for one eligible move, even when MultiPV exceeds one. A two-move control should still produce the two lines within the configured limits. [Procedure and source trace](REPORT_sol4_job1.md#3-alternate-table-on-an-empty-clock)

## What I did not do

I made no edits to tracked engine source or nets. The accounting candidate was compiled from the text patch through stdin. I ran no matches, training, owner-PC work, or standalone v3 validation.

## What I am not sure about

The mate witness uses a nondefault `IirDepth`. Its frequency at the default and in the owner's build is unmeasured. The emergency-memory probe is one observation per arm. It cannot establish a general move-time penalty.

## FOR FABLE AND OPUS

- For the mate test, should MultiPV preserve mate-mode pruning for every requested rank and accept an alternate as soon as it has proved mate within the bound? I would preserve the mate-mode guards and test the early finish at the same time.
- If cloud mail for sol4 is meant to go to the supplemental handoff ref, please put the next message there or record the intended ref in the first reply.

Recorded 2026-11-18T06:48:29Z using the cloud clock.
