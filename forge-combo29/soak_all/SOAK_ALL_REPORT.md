# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z.

Updated 2026-11-14T11:53:33.057Z; elapsed 42.02 minutes; phase Part 1; completed pushes at report generation 5.

Base `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca`; merged source `f27b1971e459581ad4c85b7015f6af83bbfd4af6`; lock `16833ecc03b425586f91f4c8834dea8807bf4c22`. Cloud VM only. Only `integrate/combo29-all` and `soak/combo29-all` are push destinations. The earlier soak branch is preserved.

Default pins: {"bench11":312866,"bench13":862329,"perft5":4865609}.

| Phase | Conditions | Completed counts | Status |
| --- | --- | --- | --- |
| Part1 | Three requested merges; release/ASan+UBSan/TSan builds; all16test folders; defaults pinned; unchanged expected fixtures | {"engine_builds":3,"test_checks":58,"nonzero_checks":5,"sanitizer_reports":0,"clock_cases":14,"fixture_reproduction_runs":40,"release_krk_T1_runs":100,"release_krk_T2_runs":400,"asan_krk_T1_runs":100,"asan_krk_T2_runs":40} | Complete with4 stale fixture comparisons and1 incomplete full-ASan KRK attempt; reduced retry passed |

Existing test/check results recorded: 58; nonzero exits 5; sanitizer reports 0. See the [full matrix](TEST_MATRIX.md) for classification and output.

Fault files: 1.

- [001.txt](faults/001.txt): t16 options/clamp stale expected advertisements:10/10 each fixture/build;40 clean engine exits, no sanitizer diagnostics

Notes and limitations:

- Release and ASan/UBSan t16 options/clamp exact-output comparisons fail because their unchanged expected fixtures omit MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower advertisements. Both engine runs and search/OwnBook protocol checkers exit 0 with no sanitizer report. Raw diffs are retained; expectations are not edited.
- Full ASan/UBSan KRK40x10 attempt timed out at440seconds under concurrent sanitizer load; no completed results were printed and no pass is claimed. A bounded reduced retry follows.
- Checkpoint cadence exception: the interval from push at11:31:06.960Z to11:43:42.673Z was12min35.713sec, exceeding the requested10min target. Subsequent batch launches force a checkpoint when the preceding push is more than60sec old to bound the next interval.
- Part4 reproduction: required UseNNUE=false; both builds report mate17/25568nodes/b3f3 with15-ply PV. Independent KRK oracle confirms selectedmove forcesmatein17plies (within reported33-plybound). Scratch trace proves mate-valuedTT qsearch return with emptyPV. No falsebound demonstrated; no productionfix/switch added. Full report and exactline references in mate_pv_investigation.md.

No Elo or speed conclusion is drawn. Raw node/time measurements and match counts are reported only under their recorded conditions. [Integration and source hashes](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [batch evidence](batches/).
