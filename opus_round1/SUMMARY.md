# opus_round1 SUMMARY (Opus 5.5, 2026-10-26)

Base: verbatim AL1 s198 lock tree (commit `294dbed`), reproduced first (`00_baseline/BASELINE.md`).
One branch per job, `opus-<JOB>`; each job folder has REPORT.md, IDEA_SOURCE.md, patch.diff, logs, scripts, SHA256SUMS.
Order: O3, O1, C3, O2, C6, C2, C1, C4, C5, then O1-LTT, O5, O8, O4, O6, O7 (prompt's recommended order).

| job | branch | status | bench x5 (OFF) | perft / kiwipete | FMA | tests | sanitizers | gate |
|---|---|---|---|---|---|---|---|---|
| 00_baseline | (all) | REPRODUCED | exact | exact | 0 | 13/14 + 4 known lines | — | — |
| O3 search.cpp refactor | opus-O3 | DONE | exact | exact | 0 | 16/17 + 4 known lines; 3 new tests | ASan+UBSan 0, TSan 0 (Linux CI); UBSan-trap local 0 | none (no behaviour change) |
| C4 king-bucketed input layer (NNUEKingBuckets + NNUEFile) | opus-C4 | DONE | exact | exact | 0 | 17/18 + 4 known lines (CI); new forge_nnue_v2_tests 78/78 | ASan+UBSan 0, TSan 0 incl. v2 at Threads 2-4 (CI) | G-C1 (only on A1 data), see C4/REPORT.md |

Gate specs:
- G-C1 (C4): candidate = opus-C4 exe with `NNUEFile=<king-bucket net trained on the A1 data>.fnn2` and `NNUEKingBuckets=<its bucket count>` (one behaviour option; the file is its payload) vs AL1 s198, SPRT [0,10] at 10+0.1, srand per the test plan (QA), 40+0.4 confirm on H1; parity PASS and NPS d16/d20 recorded first (C4/REPORT.md).
