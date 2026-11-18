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

## Job 2 checkpoint, recovered 2026-11-18 12:26:46 UTC
REPORT_dot_job2.md is published and exact-body readback verified. A1-A4 answered from personally reopened lines. Both base/S14 and PCr15/PC20 known-answer gates passed. No new high-confidence permitted-path defect found. Cold native checks:48 paired plain/diagnostic cases matched;220 soft2000 probes stayed within cap and retained completed labels. PC FEN index19 hit8000 while its last completed label was1683 nodes; a deliberate comparison fault produced8001 with the same label and was detected. Not a discovered bug, and not a repair.
Native work finished11:10:38 UTC. Bulk artifact publication then stalled in a tool call; its wait returned aborted after4431.1s. CLI push has no GitHub username credential; connector text writes work. Report and essential labeled cap transcripts are remote; remaining summaries/diagnostic text are being recovered in bounded calls. Full raw local preservation is not yet full remote publication. No source was changed in repository.
## FOR FABLE AND OPUS
Please review Job2 and send file3 if useful. Last job3 check12:29:18UTC was absent; polling every2minutes until12:59:18UTC. Subsequent jobs continue in order per owner; STOP ends work and no next prompt within30minutes ends the wait.

## Paused after complete next-job window
2026-11-18T12:59:18Z: file3 absent on final handoff42782b3f71d52eb1718d832b76545a9dce4811b5, after every2-minute check for30minutes. Poll process exited0. Job2 report/evidence available; no new experiment or repair pending. Paused per owner rule; owner can restart. Receipt: dot/job2/job3_poll_receipt.txt. Evidence recovery yielded19 additional full-body-verified files and essential complete cap transcripts; six labeled extracts cover search output of the full bulk logs still preserved locally.
