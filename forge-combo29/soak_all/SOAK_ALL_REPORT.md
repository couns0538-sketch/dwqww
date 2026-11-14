# Eight-hour combined Forge integration and soak

Start: 2026-11-14T11:11:32Z. Scheduled end: 2026-11-14T19:11:32Z.

Updated 2026-11-14T11:43:38.993Z; elapsed 32.12 minutes; phase Part 1; completed pushes at report generation 3.

Base `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca`; merged source `f27b1971e459581ad4c85b7015f6af83bbfd4af6`; lock `16833ecc03b425586f91f4c8834dea8807bf4c22`. Cloud VM only. Only `integrate/combo29-all` and `soak/combo29-all` are push destinations. The earlier soak branch is preserved.

Default pins: {"bench11":312866,"bench13":862329,"perft5":4865609}.

| Phase | Conditions | Completed counts | Status |
| --- | --- | --- | --- |

Existing test/check results recorded: 56; nonzero exits 5; sanitizer reports 0. See the [full matrix](TEST_MATRIX.md) for classification and output.

Fault files: 0.


Notes and limitations:

- Release and ASan/UBSan t16 options/clamp exact-output comparisons fail because their unchanged expected fixtures omit MultiPV, NnueFile, ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower advertisements. Both engine runs and search/OwnBook protocol checkers exit 0 with no sanitizer report. Raw diffs are retained; expectations are not edited.

No Elo or speed conclusion is drawn. Raw node/time measurements and match counts are reported only under their recorded conditions. [Integration and source hashes](../INTEGRATION_ALL.md), [progress](PROGRESS.md), [batch evidence](batches/).
