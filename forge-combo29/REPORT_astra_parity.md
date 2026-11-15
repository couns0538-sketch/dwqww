# Requested source integration and cloud validation

Started 2026-11-14T23:19:40.000Z; Job A deadline 2026-11-15T02:19:40.000Z. Updated 2026-11-15T00:49:09.875Z. Cloud VM only. Branch: `for-fable-and-opus/astra-0011-pc-parity`. Base: `65e600e237ce6cc955abd3dd4637f92defc85f5f`.

Step2 exact corpus S2-0001 running.
Step1 100000/100000 identical. Same-clock commit d9a8587df8ad4d0ff1231632cb1ac72b590c04bf passes three default pins,16 option counts,9 unit rows and the required mate -5/2566746 position. Second100000 corpus and final sanitizer workload pending.

| Check | Result |
|---|---|
| Step 1 default pins | 312866 / 862329 / 4865609 |
| Step 1 option bench counts | 16 passed; 0 failed |
| Step 1 hand evaluation | 375354 / 907205; frozen reference and candidate match |
| Step 1 exact corpus | 100000 / 100000 completed; 0 differences; 1 retained operational findings; gate passed |
| Same-clock refinement | d9a8587df8ad4d0ff1231632cb1ac72b590c04bf |
| Preliminary step 1 sanitizers | 393 games / 52681 searches; 0 findings |
| Preliminary paired UCI check | 132 ordinary / 87 soft-node searches; 8 cap cases; 0 label faults |
| Final-tree sanitizers | 0 games / 0 searches; not started |
| HindsightDepth match | 0 games; Not started |

| Imported source branch | Source commit | Applied commit | Conflicts |
|---|---|---|---|
| grok47/r3-18-lazy-net-accumulator | 8207842201cadf2b7e70948b9845cd4965a184a2 | 4fd62b3a4319d695d986695128d7f77fd92b6f09 | 0 |
| grok47/r3-19-faster-hce | 528ccdf1cbba5366c78b8bc75d89237d783a0171 | d7326b9b94eb06e8863843db893ae36ed8372198 | 0 |
| grok47/r3-20-faster-search-plumbing | decec377588a446e2020a7e3634f6cc2a00533be | c488e88fddc71a7ceadddb15270d3f62f6add8d9 | 0 |

Each source change has its own commit. The three merges use e04556dd as their per-file ancestor. Full base/ours/theirs/output snapshots are in [merge evidence](tests_astra_parity/merges).

The original S1-0001 shutdown allowance occurrence remains under operational findings. Ten fresh candidate/reference pairs returned the same move, score and nodes with 20 normal exits. Fable answer0012 permits continuation from the retained cursors; a second candidate occurrence requires the prescribed diagnostic. The original allowance and elapsed time were not logged. New comparisons measure shutdown timing. [Decision](tests_astra_parity/inputs/FABLE_ANSWER_0012.md.txt), [original finding](tests_astra_parity/faults/shutdown-017629.txt), [repeat results](tests_astra_parity/shutdown-review-017629/REPRODUCTION.txt).

The isolated nine-row same-clock test was first run before the edit: only row5 failed, as expected for the unchanged function. Its expected values are fixed. [Before-edit output](tests_astra_parity/logs/same-clock-table-step1-before-edit.stdout.txt).

Half final sanitizer selfplay games softnodes2500; exact UCIlabel checks peranswer0012, capcount andmeanX. Labelcheck3/4failure stops forreport.

Preliminary sanitizer results test the three-import tree and are recorded separately from final-tree coverage. The old in-process driver reuses a Searcher through successive moves. The new UCI harness pairs usual-limit and softnodes2500 games and checks the exact training-label contract.

The actual owner-PC compiler, PGO profile, runtime tuning and active network were not independently tested here. This report covers the specifically requested source changes, cloud builds and recorded options. Fable reports an independent source comparison in answer0012; that is attributed evidence, not a cloud run on the PC.

Detailed state and all command/output files are retained: [state snapshot](tests_astra_parity/STATUS_STATE.txt), [commands and raw output](tests_astra_parity/logs), [progress](tests_astra_parity/PROGRESS.txt). Large raw text logs use immutable chunks with byte counts and SHA256 reconstruction manifests. All published additions are text under this report and tests_astra_parity. Existing tests, expected values, CMake and earlier evidence remain unchanged.

Step 2 details: {"sourceCommit":"d9a8587df8ad4d0ff1231632cb1ac72b590c04bf","status":"local checks passed; exact corpus and final sanitizers pending","build":"passed","binarySha256":"df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56","pins":{"bench11":312866,"bench13":862329,"perft5":4865609},"options":{"passed":16,"failed":0,"rows":[{"name":"EvalRule50Damp","value":"true","expected":1049205,"got":1049205},{"name":"ThreatHistory","value":"true","expected":643389,"got":643389},{"name":"LmrSignedCorrection","value":"true","expected":862329,"got":862329},{"name":"LmrLateParentRelief","value":"true","expected":818656,"got":818656},{"name":"HindsightDepth","value":"true","expected":840387,"got":840387},{"name":"NullThreatVerify","value":"true","expected":789456,"got":789456},{"name":"NullSeeVeto","value":"true","expected":929140,"got":929140},{"name":"AspCappedReopen","value":"true","expected":850997,"got":850997},{"name":"AspArmLate","value":"true","expected":870398,"got":870398},{"name":"EvasionOrdering","value":"true","expected":772890,"got":772890},{"name":"DeadMaterial","value":"true","expected":862329,"got":862329},{"name":"QuietExtinction","value":"true","expected":632155,"got":632155},{"name":"DrawJitter","value":"8","expected":857947,"got":857947},{"name":"TmFinishIteration","value":"true","expected":862329,"got":862329},{"name":"TmNodeShare","value":"true","expected":862329,"got":862329},{"name":"SoundMatePruning","value":"true","expected":980408,"got":980408}]},"unit":{"cases":9,"failures":0,"expectedValuesUnchanged":true},"targetPosition":{"fen":"8/8/2n2r2/3qN1k1/8/8/8/K7 w - - 90 141","depth":9,"threads":1,"move":"a1b2","scoreKind":"mate","score":-5,"nodes":2566746,"normalExit":true}}.
Final soak details: {"status":"not started"}.
Match details: {"status":"not started"}.

No Elo or speed claim is made. Match reporting is counts only; raw unmodified runner output is retained.
Progress pushes: 13, including this checkpoint.
