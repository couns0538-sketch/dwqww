# Requested source integration and cloud validation

Started 2026-11-14T23:19:40.000Z; Job A deadline 2026-11-15T04:20:00.000Z. Updated 2026-11-15T02:18:25.599Z. Cloud VM only. Branch: `for-fable-and-opus/astra-0011-pc-parity`. Base: `65e600e237ce6cc955abd3dd4637f92defc85f5f`.

The original deadline was 2026-11-15T02:19:40.000Z. [Fable decision0016](tests_astra_parity/inputs/FABLE_ANSWER_0016.md.txt) extended Job A to 2026-11-15T04:20:00.000Z and classified measured short-budget, driver-forced cutoffs for both builds. All original counters, strict audits and the2000-cycle diagnostic remain on record.

Stopped on two Threads2 soft-node item4 failures; Fable/Opus decision pending.
Full exact histories and output preserved for both item4 failures. Items2/3 passed; zero sanitizer diagnostics. Earlier clean Threads1 coverage remains108games/15514searches; two failed batches receive zero clean credit. No further engine runs or source changes. Question0017 pushed at64c1624964b684e3ab54b22cf98004f2463850e6; independent source review verifies26sourcepins and explains possible helper-publication sampling, without claiming observed stopbranch.

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
| Prescribed shutdown diagnostic | 2000/2000 cycles; candidate/reference timeouts 0/0; max quit-to-exit 16.077182/14.05392 ms; ordinary runs paused |
| Preliminary step 1 sanitizers | 393 games / 52681 searches; 0 findings |
| Preliminary paired UCI check | 132 ordinary / 87 soft-node searches; 8 cap cases; 0 label faults |
| Final-tree original protocol | 5 finished games / 1102 searches observed; 0 accepted batches; 1 historical contract-failure batches retained |
| Final-tree strict depth64 v2 | 2/12 distinct conditions covered; 2 clean batches from 4 recorded; 108 accepted games / 15514 searches; 0 diagnostic lines; 2 new finding batches |
| Strict-v2 paired labels | 54 ordinary / 54 soft-node games; soft X 42226157/7874, mean 5362.7326644653285; 911 hard-cap cases |
| HindsightDepth match | 0 games; Not started |

| Imported source branch | Source commit | Applied commit | Conflicts |
|---|---|---|---|
| grok47/r3-18-lazy-net-accumulator | 8207842201cadf2b7e70948b9845cd4965a184a2 | 4fd62b3a4319d695d986695128d7f77fd92b6f09 | 0 |
| grok47/r3-19-faster-hce | 528ccdf1cbba5366c78b8bc75d89237d783a0171 | d7326b9b94eb06e8863843db893ae36ed8372198 | 0 |
| grok47/r3-20-faster-search-plumbing | decec377588a446e2020a7e3634f6cc2a00533be | c488e88fddc71a7ceadddb15270d3f62f6add8d9 | 0 |

| Strict-v2 sanitizer group | Passed batches | Ordinary games/searches | Soft-node games/searches | Cap cases | Diagnostic lines / fault rows |
|---|---|---|---|---|---|
| asan/off/t1/n2000/d0 | 1/1 | 26/3563 | 26/4073 | 443 | 0/0 |
| asan/off/t2/n2000/d0 | 0/1 | 0/0 | 0/0 | 0 | 0/1 |
| asan/on/t1/n2000/d0 | 1/1 | 28/4077 | 28/3801 | 468 | 0/0 |
| asan/on/t2/n2000/d0 | 0/1 | 0/0 | 0/0 | 0 | 0/1 |

Game and search counts in that table include only accepted clean batches; diagnostic and fault columns retain every recorded finding. The original failed contract batch is separate. Both earlier depth64 declarations were unused; the extended plan reuses the exact strict-v2 native binary.

The extended plan reserves72 batches across6 cycles; 68 have not run. Distinct-condition coverage is the12-condition check, not completion of all72 reserved batches. Repeated batches: 0.
Cycle 0: 2 clean batches from 4 recorded; 2 failed or incomplete.


The complete corpus is accepted through a separate, explicit decision for global position36729: unchanged a1b2, mate−6/2565143 before and mate−5/2566746 after, original plus10 fresh pairs. All other positions match. The source proof requires equal capped clocks with an old mate-distance rejection; no runtime TT-entry clock is claimed. The strict audit still lists its original difference and operational findings. [Acceptance evidence](tests_astra_parity/inputs/step2-effective-acceptance-S2-0007.txt).

Each source change has its own commit. The three merges use e04556dd as their per-file ancestor. Full base/ours/theirs/output snapshots are in [merge evidence](tests_astra_parity/merges).

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

Half final sanitizer selfplay games softnodes2500; exact UCIlabel checks peranswer0012, capcount andmeanX. Labelcheck3/4failure stops forreport.

The second candidate cutoff occurred with only3 ms total allowance and1 ms graceful wait, followed by driver SIGTERM; observed exit0/signal0 at1.193467 ms. The prescribed2000-cycle diagnostic used the normal250 ms allowance, alternating1000 cycles per build. [Original trigger and diagnostic summary](tests_astra_parity/faults/shutdown-candidate-085545.txt), [all cycle transcripts and reconstruction hashes](tests_astra_parity/shutdown-diagnostic-085545). The continuation question is published in [coordination0016](https://github.com/couns0538-sketch/dwqww/tree/81f22c245a906b3ea59af4404cb8f112a35936a2/forge-combo29/soak_all/ASTRA_QUESTION_0016.md).

The first final-tree paired batch stopped on the literal soft-node item4 contract. At FEN `8/1K6/8/3k4/6R1/8/8/8 b - - 98 130`, the last exact iteration was depth64, cp0, nodes2225; X was2225 and bestmove d5c5 matched the PV. Items2/3 passed. No sanitizer diagnostic appeared. The existing depth ceiling explains termination below2500, but the fixed acceptance rule did not exempt it. No engine fix or expected-value change was made.
[Full original fault and batch output](tests_astra_parity/faults/softnodes-item4-0015.txt). [Independent source/transcript review](tests_astra_parity/softnodes-fault-peer-review/REVIEW.md). The request to Fable and Opus is retained in [0015](tests_astra_parity/inputs/question-0015.txt). Fable explicitly amended item4 to allow a completed exact depth64 iteration, required no engine change or repeats, and directed continuation. The old failure/audit remains unchanged. [Decision and source comparison](tests_astra_parity/inputs/FABLE_ANSWER_0013_0014_0015.md.txt).
Before this stop, two whole pairs completed (4 games,611 searches). Including the interrupted pair, the batch observed545 ordinary searches and557 soft searches, with5 finished games. Observed soft Xsum2856372 /557 =5128.136445;51 reached the hard cap. These are observations from a failed batch and are not credited as a clean passed batch. No repeat frequency is claimed; the immediate-stop instruction took priority.

In those51 capped searches, X was10000 each; the last completed exact iteration averaged1624 nodes (range196–2474) and depth8.627. Those observations include the partial third pair; they do not compare cap factors or establish a strength result. [Per-search transcript-derived values](tests_astra_parity/inputs/soft-cap-observations.txt).

Two later Threads2 batches failed item4: the last exact info line reported fewer than2500 nodes, while final X was above2500 and below10000. Items2/3 passed. Both complete histories and output are retained; no targeted repeats were run and neither batch receives clean credit.
- Seed 202611155203, options off: info depth 4 seldepth 7 score cp -1782 nodes 2418 nps 186000 hashfull 13 time 13 pv e7f8 c2c8 f8g7 a1b2 g7h6; X=2766; bestmove e7f8. [Full fault](tests_astra_parity/faults/softnodes-threads2-item4-0017-2.txt).
- Seed 202611155209, options HindsightDepth+MateAlphaGuard on: info depth 9 seldepth 18 score cp 898 nodes 2379 nps 297375 hashfull 1 time 8 pv h6g7 h4g5 e2a6 g5g7 a6b6 d6e7 b6c7 e7f6 c7g7 f6g7 b3b4 g7f8 f1d2 f8e7 c3c4; X=2887; bestmove h6g7. [Full fault](tests_astra_parity/faults/softnodes-threads2-item4-0017-8.txt).

Further engine work is paused pending Fable/Opus review. No source or acceptance rule was changed.
[Question0017](https://github.com/couns0538-sketch/dwqww/blob/64c1624964b684e3ab54b22cf98004f2463850e6/forge-combo29/soak_all/ASTRA_QUESTION_0017.md).

Preliminary sanitizer results test the three-import tree and are recorded separately from final-tree coverage. The old in-process driver reuses a Searcher through successive moves. The new UCI harness pairs usual-limit and softnodes2500 games and checks the exact training-label contract.

The actual owner-PC compiler, PGO profile, runtime tuning and active network were not independently tested here. This report covers the specifically requested source changes, cloud builds and recorded options. Fable reports an independent source comparison in answer0012; that is attributed evidence, not a cloud run on the PC.

Detailed state and all command/output files are retained: [state snapshot](tests_astra_parity/STATUS_STATE.txt), [commands and raw output](tests_astra_parity/logs), [progress](tests_astra_parity/PROGRESS.txt). Large raw text logs use immutable chunks with byte counts and SHA256 reconstruction manifests. All published additions are text under this report and tests_astra_parity. Existing tests, expected values, CMake and earlier evidence remain unchanged.

Per-batch accounting, including completed pairs before any failure and partial observations, is retained in the state snapshot and immutable batch audits. Current acceptance and unresolved findings are stated above; preparation checks do not count as engine searches.

No Elo or speed claim is made. Match reporting is counts only; raw unmodified runner output is retained.
Progress pushes: 28, including this checkpoint.
