# Requested source integration and cloud validation

Started 2026-11-14T23:19:40.000Z; Job A deadline 2026-11-15T04:20:00.000Z. Updated 2026-11-15T04:46:33.070Z. Cloud VM only. Branch: `for-fable-and-opus/astra-0011-pc-parity`. Base: `65e600e237ce6cc955abd3dd4637f92defc85f5f`.

The original deadline was 2026-11-15T02:19:40.000Z. [Fable decision0016](tests_astra_parity/inputs/FABLE_ANSWER_0016.md.txt) extended Job A to 2026-11-15T04:20:00.000Z and classified measured short-budget, driver-forced cutoffs for both builds. All original counters, strict audits and the2000-cycle diagnostic remain on record.

Job A closed at 2026-11-15T04:20:00.000Z; accepted sanitizer coverage 846 games / 120313 searches, 12/12 conditions. [Deadline closeout and unverified work](tests_astra_parity/job-a-closeout-0420/REPORT.md). Job B retains its separate deadline 2026-11-15T05:06:50.313Z.

[Shutdown finding0020 at the Job A deadline](tests_astra_parity/job-a-closeout-0020-supplement.md). The closeout does not authorize resuming a paused job.

Job B: HindsightDepth fixed-node match.
Job B B-0009: credited 100 games; cumulative 900, W-L-D 253-232-415, pairs 21,97,192,120,20. 0 blocked batches; 0 raw finished games excluded. Counts only.

| Check | Result |
|---|---|
| Step 1 default pins | 312866 / 862329 / 4865609 |
| Step 1 option bench counts | 16 passed; 0 failed |
| Step 1 hand evaluation | 375354 / 907205; frozen reference and candidate match |
| Step 1 exact corpus | 100000 / 100000 completed; 0 differences; 1 retained operational findings; gate passed |
| Same-clock refinement | d9a8587df8ad4d0ff1231632cb1ac72b590c04bf |
| Step 2 default pins | 312866 / 862329 / 4865609 |
| Step 2 option checks and unit rows | 16/16 option counts; 9 unit rows, 0 failures |
| Step 2 targeted position | a1b2, mate -5, 2566746 nodes; depth9, Threads1 |
| Step 2 exact corpus | 100000/100000; 1 differences; effective gate accepted with listed same-clock attribution; strict audit retained |
| Prescribed shutdown diagnostic | 2000/2000 cycles; candidate/reference timeouts 0/0; max quit-to-exit 16.077182/14.05392 ms; ordinary runs resumed by separate decision |
| Preliminary step 1 sanitizers | 393 games / 52681 searches; 0 findings |
| Preliminary paired UCI check | 132 ordinary / 87 soft-node searches; 8 cap cases; 0 label faults |
| Final-tree original protocol | 5 finished games / 1102 searches observed; 0 accepted batches; 1 historical contract-failure batches retained |
| Earlier strict-v2 protocol | 2 clean batches; 108 accepted games / 15514 searches; 2 historical sampling findings, zero clean credit for those batches |
| Earlier SMP-amended protocol | 2 clean batches; 148 accepted games / 21436 searches; 2 retained deadline-finding batches, zero clean credit for those batches |
| Final-tree0018 continuation | 12/12 distinct conditions covered; 17 clean batches from 18 recorded; 590 accepted games / 83363 searches; 0 diagnostic lines; 1 finding batches |
| Current paired labels | 295 ordinary / 295 soft-node games; soft X 229824203/41812, mean 5496.6087008514305; 5647 hard-cap cases |
| Accepted final-tree totals across protocols | 846 games / 120313 searches; failed batches excluded |
| Current-protocol SMP sampling exception | 454 accepted-clean searches; 454 observed; historical failures unchanged |
| HindsightDepth match | 900 games; W-L-D 253-232-415; pair counts 21,97,192,120,20; Running; completed batches only |
| Match operational findings | 0 crash markers; 0 illegal-move games; 0 disconnect games; 0 stalls; 0 aborts; raw side/process accounting retained separately |
| Response-deadline diagnostics | 40/40 release and 2/2 TSan searches completed before quit; 0 response timeouts, sanitizer reports or abnormal exits; zero soak credit |
| ASan shutdown finding0020 | Seed 202611171101; declared250ms allowance; driver SIGTERM then SIGKILL, reaped signal9; 235.556687ms quit-to-reap; failed batch has zero clean credit; unresolved; release Job B and separate diagnostic authorized by decision0020 |

| Imported source branch | Source commit | Applied commit | Conflicts |
|---|---|---|---|
| grok47/r3-18-lazy-net-accumulator | 8207842201cadf2b7e70948b9845cd4965a184a2 | 4fd62b3a4319d695d986695128d7f77fd92b6f09 | 0 |
| grok47/r3-19-faster-hce | 528ccdf1cbba5366c78b8bc75d89237d783a0171 | d7326b9b94eb06e8863843db893ae36ed8372198 | 0 |
| grok47/r3-20-faster-search-plumbing | decec377588a446e2020a7e3634f6cc2a00533be | c488e88fddc71a7ceadddb15270d3f62f6add8d9 | 0 |

| Current sanitizer group | Passed batches | Ordinary games/searches | Soft-node games/searches | Cap cases | Diagnostic lines / fault rows |
|---|---|---|---|---|---|
| asan/off/t1/n2000/d0 | 1/2 | 27/3940 | 27/4098 | 515 | 0/1 |
| asan/off/t1/n20000/d0 | 2/2 | 22/2900 | 22/3199 | 353 | 0/0 |
| asan/off/t2/n2000/d0 | 1/1 | 43/5621 | 43/5655 | 849 | 0/0 |
| asan/off/t2/n20000/d0 | 2/2 | 32/4844 | 32/4400 | 751 | 0/0 |
| tsan/off/t2/n20000/d0 | 1/1 | 4/533 | 4/463 | 71 | 0/0 |
| tsan/off/t4/n20000/d0 | 1/1 | 6/1139 | 6/1164 | 121 | 0/0 |
| asan/on/t1/n2000/d0 | 2/2 | 58/8316 | 58/7653 | 840 | 0/0 |
| asan/on/t1/n20000/d0 | 2/2 | 20/2978 | 20/2998 | 317 | 0/0 |
| asan/on/t2/n2000/d0 | 1/1 | 41/5361 | 41/5967 | 939 | 0/0 |
| asan/on/t2/n20000/d0 | 2/2 | 30/4251 | 30/4825 | 736 | 0/0 |
| tsan/on/t2/n20000/d0 | 1/1 | 4/649 | 4/474 | 64 | 0/0 |
| tsan/on/t4/n20000/d0 | 1/1 | 8/1019 | 8/916 | 91 | 0/0 |

Game and search counts in that table include only accepted clean batches in the current protocol; diagnostic and fault columns retain every recorded finding. Earlier protocol results remain separate. Both earlier depth64 declarations were unused. The SMP amendment changes the harness check only; the engine bytes remain unchanged.

The current plan reserves72 batches; 54 have not run. Distinct-condition coverage is the12-condition check, not completion of the reserved inventory. Repeated batches: 6.
Cycle 1: 12 clean batches from 12 recorded; 0 failed or incomplete.
Cycle 2: 5 clean batches from 6 recorded; 1 failed or incomplete.


The complete corpus is accepted through a separate, explicit decision for global position36729: unchanged a1b2, mate−6/2565143 before and mate−5/2566746 after, original plus10 fresh pairs. All other positions match. The source proof requires equal capped clocks with an old mate-distance rejection; no runtime TT-entry clock is claimed. The strict audit still lists its original difference and operational findings. [Acceptance evidence](tests_astra_parity/inputs/step2-effective-acceptance-S2-0007.txt).

Each source change has its own commit. The three merges use e04556dd as their per-file ancestor. Full base/ours/theirs/output snapshots are in [merge evidence](tests_astra_parity/merges).

JobB was declared at 2026-11-15T03:06:50.313Z, with deadline 2026-11-15T05:06:50.313Z, seed 202611150011,50000 nodes/move, Threads1/Hash16/OwnBookfalse/MateAlphaGuardfalse; one binary, HindsightDepth on versus off, paired UHO openings and no adjudication. JobA was incomplete and sanitizers pending at declaration; Step2 was accepted. This admission is explicit in [decision0018](tests_astra_parity/inputs/FABLE_ANSWER_0018.md.txt). [Frozen declaration](tests_astra_parity/inputs/job-b-0018-frozen-declaration.txt). Pair bins count0,0.5,1,1.5,2 points for the on side across each two-game opening pair. Counts only.

| Option alone at bench13 | Value | Frozen expected | Step1 | Step2 |
|---|---|---|---|---|
| EvalRule50Damp | true | 1049205 | 1049205 | 1049205 |
| ThreatHistory | true | 643389 | 643389 | 643389 |
| LmrSignedCorrection | true | 862329 | 862329 | 862329 |
| LmrLateParentRelief | true | 818656 | 818656 | 818656 |
| HindsightDepth | true | 840387 | 840387 | 840387 |
| NullThreatVerify | true | 789456 | 789456 | 789456 |
| NullSeeVeto | true | 929140 | 929140 | 929140 |
| AspCappedReopen | true | 850997 | 850997 | 850997 |
| AspArmLate | true | 870398 | 870398 | 870398 |
| EvasionOrdering | true | 772890 | 772890 | 772890 |
| DeadMaterial | true | 862329 | 862329 | 862329 |
| QuietExtinction | true | 632155 | 632155 | 632155 |
| DrawJitter | 8 | 857947 | 857947 | 857947 |
| TmFinishIteration | true | 862329 | 862329 | 862329 |
| TmNodeShare | true | 862329 | 862329 | 862329 |
| SoundMatePruning | true | 980408 | 980408 | 980408 |

The original S1-0001 shutdown allowance occurrence remains under operational findings. Ten fresh candidate/reference pairs returned the same move, score and nodes with 20 normal exits. Fable answer0012 permits continuation from the retained cursors; a second candidate occurrence requires the prescribed diagnostic. The original allowance and elapsed time were not logged. New comparisons measure shutdown timing. [Decision](tests_astra_parity/inputs/FABLE_ANSWER_0012.md.txt), [original finding](tests_astra_parity/faults/shutdown-017629.txt), [repeat results](tests_astra_parity/shutdown-review-017629/REPRODUCTION.txt).

The isolated nine-row same-clock test was first run before the edit: only row5 failed, as expected for the unchanged function. Its expected values are fixed. [Before-edit output](tests_astra_parity/logs/same-clock-table-step1-before-edit.stdout.txt).

The only second-step engine change is inside TTEntry::score_usable. [Exact source diff](tests_astra_parity/inputs/same-clock-source/change.txt). The final release SHA256 is df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56. The guard is compiled in and remains off by default. The independent review shows the Boolean delta is limited to equal capped clocks with an old mate-distance rejection; this alone is not a proof of a mate score's chess-theoretic truth.

The target harness was tightened after review to reject bounded scores and engine stderr. Its repeat passed with unchanged expected values. [Strict transcript](tests_astra_parity/logs/same-clock-position-step2-strict.stdout.txt), [independent review](tests_astra_parity/same-clock-peer-review/REVIEW.md).

The tables above report actual accepted coverage for each final-tree protocol. Earlier failed batches remain retained with zero clean credit. The continuation reserves eight ASan/UBSan conditions and four node-capped TSan conditions; only audited, recorded runs count. JobB is underway under decision0018 and its actual completed-game counts are reported separately.

Actual timing snapshot 2026-11-15T02:28:20.131Z: final-tree batch intervals cover 215.11s of wall time after merging overlaps; their duration sum is 400.062s. Accepted clean batches cover 188.692s. These include startup/protocol/shutdown overhead and are not CPU time. Gaps and preliminary coverage are separate. [Intervals and gaps](tests_astra_parity/soak-time-review-0017/REPORT.md).

The second candidate cutoff occurred with only3 ms total allowance and1 ms graceful wait, followed by driver SIGTERM; observed exit0/signal0 at1.193467 ms. The prescribed2000-cycle diagnostic used the normal250 ms allowance, alternating1000 cycles per build. [Original trigger and diagnostic summary](tests_astra_parity/faults/shutdown-candidate-085545.txt), [all cycle transcripts and reconstruction hashes](tests_astra_parity/shutdown-diagnostic-085545). The continuation question is published in [coordination0016](https://github.com/couns0538-sketch/dwqww/tree/81f22c245a906b3ea59af4404cb8f112a35936a2/forge-combo29/soak_all/ASTRA_QUESTION_0016.md).

The first final-tree paired batch stopped on the literal soft-node item4 contract. At FEN `8/1K6/8/3k4/6R1/8/8/8 b - - 98 130`, the last exact iteration was depth64, cp0, nodes2225; X was2225 and bestmove d5c5 matched the PV. Items2/3 passed. No sanitizer diagnostic appeared. The existing depth ceiling explains termination below2500, but the fixed acceptance rule did not exempt it. No engine fix or expected-value change was made.
[Full original fault and batch output](tests_astra_parity/faults/softnodes-item4-0015.txt). [Independent source/transcript review](tests_astra_parity/softnodes-fault-peer-review/REVIEW.md). The request to Fable and Opus is retained in [0015](tests_astra_parity/inputs/question-0015.txt). Fable explicitly amended item4 to allow a completed exact depth64 iteration, required no engine change or repeats, and directed continuation. The old failure/audit remains unchanged. [Decision and source comparison](tests_astra_parity/inputs/FABLE_ANSWER_0013_0014_0015.md.txt).
Before this stop, two whole pairs completed (4 games,611 searches). Including the interrupted pair, the batch observed545 ordinary searches and557 soft searches, with5 finished games. Observed soft Xsum2856372 /557 =5128.136445;51 reached the hard cap. These are observations from a failed batch and are not credited as a clean passed batch. No repeat frequency is claimed; the immediate-stop instruction took priority.

In those51 capped searches, X was10000 each; the last completed exact iteration averaged1624 nodes (range196–2474) and depth8.627. Those observations include the partial third pair; they do not compare cap factors or establish a strength result. [Per-search transcript-derived values](tests_astra_parity/inputs/soft-cap-observations.txt).

Two later Threads2 batches failed item4: the last exact info line reported fewer than2500 nodes, while final X was above2500 and below10000. Items2/3 passed. Both complete histories and output are retained; no targeted repeats were run and neither batch receives clean credit.
- Seed 202611155203, options off: info depth 4 seldepth 7 score cp -1782 nodes 2418 nps 186000 hashfull 13 time 13 pv e7f8 c2c8 f8g7 a1b2 g7h6; X=2766; bestmove e7f8. [Full fault](tests_astra_parity/faults/softnodes-threads2-item4-0017-2.txt).
- Seed 202611155209, options HindsightDepth+MateAlphaGuard on: info depth 9 seldepth 18 score cp 898 nodes 2379 nps 297375 hashfull 1 time 8 pv h6g7 h4g5 e2a6 g5g7 a6b6 d6e7 b6c7 e7f6 c7g7 f6g7 b3b4 g7f8 f1d2 f8e7 c3c4; X=2887; bestmove h6g7. [Full fault](tests_astra_parity/faults/softnodes-threads2-item4-0017-8.txt).

Fable0017 explicitly permits, for Threads above1 only, an info count belowN when X is at leastN. Threads1 stays strict; items2/3 and all legal/sanitizer/exit checks stay enforced. The engine is unchanged and old failures retain zero clean credit. The intermediate stop count was not instrumented. [Decision](tests_astra_parity/inputs/FABLE_ANSWER_0017.md.txt).
[Question0017](https://github.com/couns0538-sketch/dwqww/blob/64c1624964b684e3ab54b22cf98004f2463850e6/forge-combo29/soak_all/ASTRA_QUESTION_0017.md).

Preliminary sanitizer results test the three-import tree and are recorded separately from final-tree coverage. The old in-process driver reuses a Searcher through successive moves. The new UCI harness pairs usual-limit and softnodes2500 games and checks the exact training-label contract.

The first two clean final-tree batches contain 15406 searches after an earlier search without intervening ucinewgame. This exercises persistent-process warm TT/history and worker-storage reuse. Each root accumulator is nevertheless invalidated/refreshed at every search; neither harness performs an independent per-node incremental-versus-full NNUE value check. [Exact coverage and limitations](tests_astra_parity/warm-coverage-review/REVIEW.md).

Two later TSanThreads2 ordinary depth9 searches exceeded the15second harness response allowance. Neither produced a sanitizer diagnostic, and both responded to quit and exited normally. These are retained deadline findings, not proven hangs or race reports. Both failed batches receive zero clean credit.
- Seed202611160105, FEN 8/8/3k4/8/6P1/1Q3K2/8/8 b - - 0 54; last completed < stdout info depth 8 seldepth 13 score cp -2191 nodes 14812 nps 200162 hashfull 10 time 74 pv d6e7 g4g5 e7d6 f3e4 d6d7 b3d5 d7c7 g5g6 c7c8 e4f4; quit-to-exit 24.00694ms. [Full fault](tests_astra_parity/faults/tsan-response-timeout-0018-4.txt).
- Seed202611160111, FEN 8/B2P4/2K5/P7/8/5k2/8/8 b - - 0 73; last completed < stdout info depth 8 seldepth 13 score cp -2451 nodes 4879 nps 113465 hashfull 4 time 43 pv f3e4 a5a6 e4f5 a7c5 f5f6 a6a7 f6e5 a7a8q e5e6; quit-to-exit 29.126809ms. [Full fault](tests_astra_parity/faults/tsan-response-timeout-0018-10.txt).

[Independent timeout review](tests_astra_parity/tsan-timeout-0018-review/REVIEW.md). [Question0018](https://github.com/couns0538-sketch/dwqww/blob/4a9704895419099a6947c2d1c54694451c1841fe/forge-combo29/soak_all/ASTRA_QUESTION_0018.md).


All five release T2 node counts exceed all five T1 counts for both positions at both depths. This establishes greater search work in these tested SMP ending configurations. Source guard conditions are relevant but were not instrumented; original warm TT/history state and original timeout recurrence were not reproduced. No engine fix, speed or strength claim.

| Ending case | Target depth | Threads1 nodes (five runs) | Threads2 nodes (range of five) |
|---|---:|---:|---:|
| 4 | 9 | 10121–10121 | 992145–3684319 |
| 4 | 12 | 58553–58553 | 3600466–16711738 |
| 10 | 9 | 9596–9596 | 594403–1426601 |
| 10 | 12 | 41173–41173 | 18248572–35892370 |

[Complete diagnostic tables, all completed-depth counts and source conditions](tests_astra_parity/response-diagnostic-records-0018/snapshot-01/REPORT.md). The original two deadline-finding batches retain zero clean credit. Decision0018 permits the continuation and changes only the ordinary TSan search limit to nodes20000; the soft half remains softnodes2500. No engine source was changed.
[Full ending-workload finding and all 42 diagnostic transcripts](tests_astra_parity/faults/smp-ending-workload-0019.txt); [independent review](tests_astra_parity/response-diagnostic-findings-0018/REVIEW.md).
Fable's [decision0019](tests_astra_parity/inputs/FABLE_ANSWER_0019.md.txt) classifies the original two batches as "response deadline exceeded by real search work (several threads, bare-king ending)" and keeps their zero credit. The source guard was not instrumented here and the original warm-state recurrence remains unverified. The outlined follow-up is JobD after JobC; it has not started.


A later ASan Threads1 batch completed28 pairs (56 games,8291 checked searches) but failed its final shutdown. No sanitizer report appeared. The sibling batch passed58 games/8108 searches. The failed batch remains zero-credit. No targeted repeat had run when the finding was recorded. The declared250ms budget is distinct from graceful wait time: the frozen transport reserves its first150ms for quit before escalating. Observed quit-to-reap235.556687ms does not make this a short assigned-budget cutoff; signal9 also falls outside decision0016. The cause is unknown. [Exact input, command and full output](tests_astra_parity/faults/asan-shutdown-0020.txt).
[Independent shutdown review](tests_astra_parity/asan-shutdown-review-0020/REVIEW.md).
[Request to Fable and Opus](https://github.com/couns0538-sketch/dwqww/blob/412df76d87027b53629f3cb15c6173f40fbe7122/forge-combo29/soak_all/ASTRA_QUESTION_0020.md).

[Fable decision0020](tests_astra_parity/inputs/FABLE_ANSWER_0020.md.txt) resumes the unchanged release match and authorizes a separate replay of all retained UCI inputs on the unchanged ASan binary. The diagnostic gives quit a full five seconds without driver signals; the failed batch retains zero credit. Job A stays closed, Job B keeps its original deadline, and the new shutdown protocol applies only to future sanitizer declarations. The suggested leak-check explanation is a hypothesis; no diagnostic result is implied by this authorization.

The [completed full replay](tests_astra_parity/asan-shutdown-0020-replay-report.md) matched all 8291 searches and exited naturally in 38.103431ms, exit0, without signals, stderr or sanitizer reports. The original failure did not recur in this one replay; its cause remains unresolved. The observed exit did not exceed250ms, so it does not establish the proposed exit-work explanation. Both the original failed batch and this separate diagnostic retain zero soak credit.
[Independent replay-result review](tests_astra_parity/asan-shutdown-result-review-0020/REVIEW.md) verified all retained commands, searches, timing fields and stderr evidence. Original failure recurrence was0/1 in full diagnostic replays.
The actual owner-PC compiler, PGO profile, runtime tuning and active network were not independently tested here. This report covers the specifically requested source changes, cloud builds and recorded options. Fable reports an independent source comparison in answer0012; that is attributed evidence, not a cloud run on the PC.

Detailed state and all command/output files are retained: [state snapshot](tests_astra_parity/STATUS_STATE.txt), [commands and raw output](tests_astra_parity/logs), [progress](tests_astra_parity/PROGRESS.txt). Large raw text logs use immutable chunks with byte counts and SHA256 reconstruction manifests. All published additions are text under this report and tests_astra_parity. Existing tests, expected values, CMake and earlier evidence remain unchanged.

Per-batch accounting, including completed pairs before any failure and partial observations, is retained in the state snapshot and immutable batch audits. Current acceptance and unresolved findings are stated above; preparation checks do not count as engine searches.

No Elo or speed claim is made. Match reporting is counts only; raw unmodified runner output is retained.
Progress pushes: 47, including this checkpoint.
