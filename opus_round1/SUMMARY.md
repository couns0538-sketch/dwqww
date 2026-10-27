# opus_round1 SUMMARY (Opus 5.5, 2026-10-26)

Base: verbatim AL1 s198 lock tree (commit `294dbed`), reproduced first (`00_baseline/BASELINE.md`).
One branch per job, `opus-<JOB>`; each job folder has REPORT.md, IDEA_SOURCE.md, patch.diff, logs, scripts, SHA256SUMS.
Order: O3, O1, C3, O2, C6, C2, C1, C4, C5, then O1-LTT, O5, O8, O4, O6, O7 (prompt's recommended order).

| job | branch | status | bench x5 (OFF) | perft / kiwipete | FMA | tests | sanitizers | gate |
|---|---|---|---|---|---|---|---|---|
| 00_baseline | (all) | REPRODUCED | exact | exact | 0 | 13/14 + 4 known lines | — | — |
| O3 search.cpp refactor | opus-O3 | DONE | exact | exact | 0 | 16/17 + 4 known lines; 3 new tests | ASan+UBSan 0, TSan 0 (Linux CI); UBSan-trap local 0 | none (no behaviour change) |

Gate specs: none yet (O3 changes no behaviour).
