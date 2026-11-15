# Requested source integration and cloud validation

Started 2026-11-14T23:19:40.000Z; Job A deadline 2026-11-15T02:19:40.000Z. Updated 2026-11-15T01:03:51.039Z. Cloud VM only. Branch: `for-fable-and-opus/astra-0011-pc-parity`. Base: `65e600e237ce6cc955abd3dd4637f92defc85f5f`.

Softnodes item4 failure reported; further engine runs paused for team review.
FinalpairedASAN firstbatch stopped after1102 observed searches (545ordinary/557soft),5completed games,2fullpairs;1 literal item4 failure atdepth64/X2225/cp0. Item2/3 pass,0sanitizerdiagnostics. Allraw retained; no further engines launched. Step2 corpus14959/100000,0searchdifferences,reference teardown occurrence retained.

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
| Step 2 exact corpus | 14959/100000; 0 differences; completion/attribution pending |
| Preliminary step 1 sanitizers | 393 games / 52681 searches; 0 findings |
| Preliminary paired UCI check | 132 ordinary / 87 soft-node searches; 8 cap cases; 0 label faults |
| Final-tree sanitizer observations | 5 finished games / 1102 searches; 1 batches with findings |
| Final-tree accepted clean batches | 0; 0 games / 0 searches; STOP: soft-label item3/4 finding |
| HindsightDepth match | 0 games; Not started |

| Imported source branch | Source commit | Applied commit | Conflicts |
|---|---|---|---|
| grok47/r3-18-lazy-net-accumulator | 8207842201cadf2b7e70948b9845cd4965a184a2 | 4fd62b3a4319d695d986695128d7f77fd92b6f09 | 0 |
| grok47/r3-19-faster-hce | 528ccdf1cbba5366c78b8bc75d89237d783a0171 | d7326b9b94eb06e8863843db893ae36ed8372198 | 0 |
| grok47/r3-20-faster-search-plumbing | decec377588a446e2020a7e3634f6cc2a00533be | c488e88fddc71a7ceadddb15270d3f62f6add8d9 | 0 |

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

The first final-tree paired batch stopped on the literal soft-node item4 contract. At FEN `8/1K6/8/3k4/6R1/8/8/8 b - - 98 130`, the last exact iteration was depth64, cp0, nodes2225; X was2225 and bestmove d5c5 matched the PV. Items2/3 passed. No sanitizer diagnostic appeared. The existing depth ceiling explains termination below2500, but the fixed acceptance rule did not exempt it. No engine fix or expected-value change was made.
[Full original fault and batch output](tests_astra_parity/faults/softnodes-item4-0015.txt). [Independent source/transcript review](tests_astra_parity/softnodes-fault-peer-review/REVIEW.md). The request to Fable and Opus is retained in [0015](tests_astra_parity/inputs/question-0015.txt); further engine runs remain paused pending its resolution.
Before this stop, two whole pairs completed (4 games,611 searches). Including the interrupted pair, the batch observed545 ordinary searches and557 soft searches, with5 finished games. Observed soft Xsum2856372 /557 =5128.136445;51 reached the hard cap. These are observations from a failed batch and are not credited as a clean passed batch. No repeat frequency is claimed; the immediate-stop instruction took priority.

Preliminary sanitizer results test the three-import tree and are recorded separately from final-tree coverage. The old in-process driver reuses a Searcher through successive moves. The new UCI harness pairs usual-limit and softnodes2500 games and checks the exact training-label contract.

The actual owner-PC compiler, PGO profile, runtime tuning and active network were not independently tested here. This report covers the specifically requested source changes, cloud builds and recorded options. Fable reports an independent source comparison in answer0012; that is attributed evidence, not a cloud run on the PC.

Detailed state and all command/output files are retained: [state snapshot](tests_astra_parity/STATUS_STATE.txt), [commands and raw output](tests_astra_parity/logs), [progress](tests_astra_parity/PROGRESS.txt). Large raw text logs use immutable chunks with byte counts and SHA256 reconstruction manifests. All published additions are text under this report and tests_astra_parity. Existing tests, expected values, CMake and earlier evidence remain unchanged.

Per-batch accounting, including completed pairs before any failure and partial observations, is retained in the state snapshot and immutable batch audits. Current acceptance and unresolved findings are stated above; preparation checks do not count as engine searches.

No Elo or speed claim is made. Match reporting is counts only; raw unmodified runner output is retained.
Progress pushes: 16, including this checkpoint.
