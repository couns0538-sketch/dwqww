# dot first-job notes

Started 2026-11-18 10:47 UTC (execution environment date -u).

## Capability
Case A provisionally: shell/git/G++ available, GitHub branch creation verified. CMake is not preinstalled; checking installation before claiming build capability. Model identifier is not exposed reliably to this task; not inferred.

## Facts
Opened LOCK.md and README.md on lock/combo29-20261110. Lock SHA verified by git ls-remote: 16833ecc03b425586f91f4c8834dea8807bf4c22. Helper base verified: 6b98f2170a3210e71beed04bbd2553972c253ed7. This branch created from that exact helper base.

## Not done yet
No native build, pin test, or code findings yet. No engine source edits. No performance or strength claims.

## FOR FABLE AND OPUS
First-job verification and source review underway. Only text reports/patches will be committed to this branch; no PR.

## Job 1 outcome
Case A confirmed. Plain untouched lock Release build matched bench 11=312866, bench 13=862329, perft5=4865609. Helper base separately built and identified; two parser candidate patches reproduced their intended differences in an isolated copy and retained those pins. All source in the repository is unchanged.

Read latest sol3 and kimi5 notes, complete UCI handling and clock helpers, and search implementation with an independent internal reader. Full evidence, exact lines, tests, build identities, raw output, uncertainty and questions are in REPORT_dot_job1.md.

Three places: uci.cpp:104-113 softnodes mode stays set after trailing nodes; uci.cpp:275-286 complete overflowing integers reject rather than documented clamp; search.cpp:242-248 and :1374-1393 admitted zero history coefficients reverse reward/penalty signs (native function probe, whole-search event test pending). Mixed-selector semantics and intended signed tuning remain explicit questions, not assumed product decisions.

Dedup lesson: DrawJitter literal-zero comment looked wrong, but REPORT_r3_14.md expressly intends fifty-move precedence. Withdrew exploratory behavior patch; do not report that as a new correctness bug. Mixed clock+depth TmNodeShare behavior likewise calls for comment clarification, not removal of clock safety.

## FOR FABLE AND OPUS
Job 1 ready for review. Please decide selector precedence, spin overflow contract, and whether zero coefficient history rewards should be allowed to turn negative. Two text-only candidate patches published; neither applied to repository source. Per updated owner instruction, monitor FABLE_TO_dot_2.md every two minutes for 30 minutes after publication, continue on a job, STOP stops; no one-hour global stop.
