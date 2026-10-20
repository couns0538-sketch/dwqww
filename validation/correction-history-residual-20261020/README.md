# Correction-history residual-update arithmetic probe

**Build/CPU status: DONE.** All probe builds and processes ended at 2026-10-20 20:52:20 UTC. No engine searches, chess matches or speed measurements were run. Root owns source integration and further testing.

| Actual core and expectation | Checks | Failures | Meaning |
| --- | ---: | ---: | --- |
| Current EMA, Release | 54 | 0 | Current behavior reproduced |
| Residual increment, Release | 54 | 0 | Proposed arithmetic contract passes |
| Current EMA, ASan/UBSan | 54 | 0 | No runtime diagnostics |
| Residual increment, ASan/UBSan | 54 | 0 | No runtime diagnostics |
| Current EMA, incremental expectation | 54 | 17 | Expected RED difference; not an existing defect claim |

The four passing runs total 216 checks. Runtime stderr is empty in all four. Both tested source trees are unchanged before/after execution. Baseline and candidate differ only in the single update assignment in `candidate.patch`; network bytes and all constants/guards are unchanged.

The fixed 6 cp target error yields current corrections of 3 cp with one table and 4 cp with both; increment reaches 6 cp in both controls. The same one-line change also removes table-disparity decay and expands reachable corrections to the existing clamp: 32 cp per table, 64 cp combined at default material weight. Treat this as an **unaccepted regularization/range ablation**, not a demonstrated correctness repair or strength gain.

Read [RESULTS.md](RESULTS.md), [PROTOCOL.md](PROTOCOL.md), and [IMPLEMENTATION-RECOMMENDATION.md](IMPLEMENTATION-RECOMMENDATION.md). `RESULTS.json` contains all selected actual states. `commands.json` and raw stdout/stderr files preserve exact execution; `source-before.json` and `source-after.json` establish exported source identity. `binary-sha256.json` identifies saved probe binaries.

`INTEGRITY.json` hashes this task's stable artifacts; it excludes itself and the independently owned `independent-review/` directory, whose reviewer may still be writing. The executed driver and runner are frozen. Attempt 1 failed before compilation due to a missing CMake PATH entry and is preserved in `ATTEMPT1.md` and `attempt1-commands.json`. Attempt 2 completed within the declared monitored 600-second cap; its runner's lack of internal subprocess timeouts is recorded honestly in `execution-guard-note.json`.
