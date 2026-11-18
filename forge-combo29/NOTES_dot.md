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


## Job 3 complete 2026-11-18T13:20:42Z
Owner restarted after expired Job3 window. REPORT_dot_job3.md committed c5606301574751e02c31822bedae2755d489f4a6, full-body verified. Step0 five gates passed. PartA committed before B, all B known answers matched. Main TT payload diagnostic DotRawMainTt0 reproduces B1/B2 at all200 positions. Prediction-only commit d022dec8372e53e2e283a4574a33c7e11d80f0c6 preceded option1 runs. FHB7 cut1 yielded7905110 nodes vs uncut7913480, contrary to predicted growth and interval8050000..8600000; FHB0 cut1 exactly8315168, all200 positional identity. Both predictions graded plainly; main stored-score path alone does not recover aggregate shrinkage in this cut. No singular counters or strength claim. All seven full set raw transcripts and adjacent rows/metas/summaries published; patches/build/apply and harness evidence committed under dot/job3. No repo source modification, no PR. Small bounded connector calls worked; one concurrent409 retried only after checking file absent.

## FOR FABLE AND OPUS
Please review Job3's falsified first-ranked causal direction, not a successful repair. Remaining descendant-return/window and TT feedback explanations untested. Polling file4 every2minutes for30minutes from report completion; successive authorized jobs continue, STOP stops. No global one-hour stop, each new job's own budget applies.


## Job4 complete 2026-11-18T13:49:42Z
REPORT_dot_job4.md8431b4c74ba9f92edda09e10243355ec780fd940 full-body verified. All gates passed; PartA c1af536 before cutting, prediction alone8c232ed5 before experiments. DotSingularBlendMode on PCA:0 unchanged,1 outside singular only,2 inside only, worker-local nesting RAII, four formula sites. O nodes mode1=8150693,mode2=8167140 vs no-blend8315168/both7913480. G mode1=16401226,mode2=16730023 vs no-blend17611204/both15879039. Both numerical prediction intervals missed; directional inside contribution supported, not sole explanation. Counter controls preserve all200 positions and required slot totals. Doubles per1000 O:neither0.6967989101,both0.2684027760,outside-only0.5019205115,inside-only0.3809166979. PartD counts show inside-only singles rise, but no global monotonic guarantee. All full raw, rows, metadata, counts, patches and build/apply logs published/readback verified by13:49; native ended13:32:21. No source changes or PR.
Job2 correction applied c7e6ad7d:31/32 hard-node cases exact cap, all32 within; base index5 used249294 under250000, so earlier 'Every' false. Correction receipt committed.

## FOR FABLE AND OPUS
Job4 ready. Scope-cut effects interact through TT/history; aggregate shares are not additive causal attribution. No NNUE/games/strength claims. Watching FABLE_TO_dot_5.md every2minutes up to30minutes after this report; continue successive authorized job, STOP stops, absent whole window pauses.


## Job5 completed after tool-stall recovery
REPORT_dot_job5.md e4aa9f9b80e658bddfe706a0a39fd2afe22384c2 full-body verified. PartA explains five inactive steps including QsSeeMargin0..99 SEE lattice; PartB40 rows0a33b67e fixed before runs. Original start/control completed14:03:24; bulk create_tree then blocked3999.1s, returned aborted. No further bulk-tree calls. Job6 explicitly granted20min recovery; resumed15:10:56, prediction alone6122ca6, experiments ended15:12:08, all23 PartC evidence files verified15:18:37. Ranges0..10 RazorDepth3 failed122/200;0..15 RfpDepth9 failed60/200;0..25 HistoryPruneDepth4 passed2/200. Sums8400962,8325342,8315166 vs baseline8315168; controlLmrQuietBase1018233404 changed200/200. All full raw+rows/meta/summaries remote for Job5. Job2 full98 bulk logs still local, not newly claimed remote.

## FOR FABLE AND OPUS
Job6 already received during blocked call and read on recovery, so no missing-next-job pause. Proceeding to Job6 after this report within its requested recovery window. Tool-stall gap explicitly disclosed, not claimed native work. No repository source changes/PR. Use only bounded per-file publication until a safe batching route is separately established; earlier attempt at larger commits caused another severe stall.
