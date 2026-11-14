# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z.

Updated 2026-11-14T11:50:52.341Z; elapsed 39.34 minutes; phase Part 1; completed pushes at report generation 4.

Base `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca`; merged source `f27b1971e459581ad4c85b7015f6af83bbfd4af6`; lock `16833ecc03b425586f91f4c8834dea8807bf4c22`. Cloud VM only. Only `integrate/combo29-all` and `soak/combo29-all` are push destinations. The earlier soak branch is preserved.

Default pins: {"bench11":312866,"bench13":862329,"perft5":4865609}.

| Phase | Conditions | Completed counts | Status |
| --- | --- | --- | --- |

Existing test/check results recorded: 58; nonzero exits 5; sanitizer reports 0. See the [full matrix](TEST_MATRIX.md) for classification and output.

Fault files: 1.

- [001.txt](faults/001.txt): t16 options/clamp stale expected advertisements:10/10 each fixture/build;40 clean engine exits, no sanitizer diagnostics

Notes and limitations:

- Release and ASan/UBSan t16 options/clamp exact-output comparisons fail because their unchanged expected fixtures omit MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower advertisements. Both engine runs and search/OwnBook protocol checkers exit 0 with no sanitizer report. Raw diffs are retained; expectations are not edited.
- Full ASan/UBSan KRK40x10 attempt timed out at440seconds under concurrent sanitizer load; no completed results were printed and no pass is claimed. A bounded reduced retry follows.
- Checkpoint cadence exception: the interval from push at11:31:06.960Z to11:43:42.673Z was12min35.713sec, exceeding the requested10min target. Subsequent batch launches force a checkpoint when the preceding push is more than60sec old to bound the next interval.

No Elo or speed conclusion is drawn. Raw node/time measurements and match counts are reported only under their recorded conditions. [Integration and source hashes](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [batch evidence](batches/).
