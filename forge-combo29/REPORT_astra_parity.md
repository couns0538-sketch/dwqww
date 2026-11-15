# Requested source integration and cloud validation

Started 2026-11-14T23:19:40.000Z; job-A deadline 2026-11-15T02:19:40.000Z. Cloud VM only. Branch `for-fable-and-opus/astra-0011-pc-parity`, base `65e600e237ce6cc955abd3dd4637f92defc85f5f`. The owner-PC tree/compiler/tuning/net are not independently verified; this work integrates only the specifically requested source changes.
Current phase: Measured-shutdown corpus continuation preparation. Updated 2026-11-15T00:07:59.255Z.

| Source branch | Source commit | Applied commit | Conflicts |
|---|---|---|---|
| grok47/r3-18-lazy-net-accumulator | 8207842201cadf2b7e70948b9845cd4965a184a2 | 4fd62b3a4319d695d986695128d7f77fd92b6f09 | 0 |
| grok47/r3-19-faster-hce | 528ccdf1cbba5366c78b8bc75d89237d783a0171 | d7326b9b94eb06e8863843db893ae36ed8372198 | 0 |
| grok47/r3-20-faster-search-plumbing | decec377588a446e2020a7e3634f6cc2a00533be | c488e88fddc71a7ceadddb15270d3f62f6add8d9 | 0 |

Same-clock rule not applied; step-1 validation must pass first.

Validation: {"step1":{"build":"passed","pins":{"bench11":312866,"bench13":862329,"perft5":4865609},"options":{"passed":16,"failed":0,"rows":[{"name":"EvalRule50Damp","value":"true","expected":1049205,"got":1049205},{"name":"ThreatHistory","value":"true","expected":643389,"got":643389},{"name":"LmrSignedCorrection","value":"true","expected":862329,"got":862329},{"name":"LmrLateParentRelief","value":"true","expected":818656,"got":818656},{"name":"HindsightDepth","value":"true","expected":840387,"got":840387},{"name":"NullThreatVerify","value":"true","expected":789456,"got":789456},{"name":"NullSeeVeto","value":"true","expected":929140,"got":929140},{"name":"AspCappedReopen","value":"true","expected":850997,"got":850997},{"name":"AspArmLate","value":"true","expected":870398,"got":870398},{"name":"EvasionOrdering","value":"true","expected":772890,"got":772890},{"name":"DeadMaterial","value":"true","expected":862329,"got":862329},{"name":"QuietExtinction","value":"true","expected":632155,"got":632155},{"name":"DrawJitter","value":"8","expected":857947,"got":857947},{"name":"TmFinishIteration","value":"true","expected":862329,"got":862329},{"name":"TmNodeShare","value":"true","expected":862329,"got":862329},{"name":"SoundMatePruning","value":"true","expected":980408,"got":980408}]},"equality":{"completed":16719,"lowClock":16710,"highClock":9,"differences":0,"operationalFindings":1,"gatePassed":false,"operationalClassification":"Shutdown allowance exceeded,1,not reproduced in20freshprocesses; retained operational finding, not engine fault or search difference. Original allowance/duration unknown despite external description250ms."},"binarySha256":"f02cd1cfc2f81b7b2cd3e6306d6b63c3d4afa3d641fdc847da584f89fc6e9569","handEval":{"frozen":[{"depth":11,"nodes":375354},{"depth":13,"nodes":907205}],"candidate":[{"depth":11,"nodes":375354},{"depth":13,"nodes":907205}],"matched":true,"reason":"The imported eval.cpp path is otherwise disabled by default NNUE; this cheap targeted check exercises that changed path."},"sameClockBeforeEdit":{"cases":9,"failures":1,"failedRows":[5],"meaning":"Intended before-edit demonstration: requested row5 is refused by unchanged function; all other requested rows already pass. Expected values fixed for later step2."},"preliminaryAsanBuild":"passed; instrumented core and unchanged driver linked; final-tree coverage not yet started"}}.
Equality: {"step1":{"completed":16719,"lowClock":16710,"highClock":9,"differences":0,"operationalFindings":1,"gatePassed":false}}.
Soak: {"preliminaryStep1":{"batches":4,"games":393,"searches":52681,"faults":0,"excludedAttempts":0},"finalTree":{"status":"not started"}}.
Match: {"status":"not started; declaration required before first game"}.

Every source change is committed separately. Existing tests, expected files, CMake and earlier evidence remain unchanged. New test/report files are confined to tests_astra_parity and this report. No Elo or speed claims; owner counts-only instructions remain in force.

Four preliminary sanitizer batches completed393games/52681searches: ASAN379/51131 and TSan14/1550, zero diagnostics or move/score faults. Fable0012 authorizes corpus continuation retaining one operational shutdown-limit occurrence. New quit timing and later softnodes label checks are being added to test tools only. Source remains step1 c488e88f.

All completed per-file three-way merges returned zero conflicts.

Exact commands, raw output and source merge snapshots are under tests_astra_parity. Git metadata failures from the shared partial clone are retained; no engine workaround was applied. Progress pushes: 7 including this checkpoint.
