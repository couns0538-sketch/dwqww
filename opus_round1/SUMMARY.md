# opus_round1 SUMMARY (Opus 5.5) — status 2026-10-27

**Base.** Verbatim AL1 s198 lock tree (commit `294dbed`), reproduced first (`00_baseline/BASELINE.md`). All job
branches build on O3 (`0d99f02`, the no-op refactor), except where noted.

**Layout.** One branch per job, `opus-<JOB>`. Each job folder `opus_round1/<JOB>/` has REPORT.md, IDEA_SOURCE.md,
patch.diff, logs, scripts and SHA256SUMS.

**Common checks for every DONE job, OFF / defaults:**
- bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0;
- PC recipe build and Linux CI (g++-14);
- ctest: only the 4 known `forge_tests` lines;
- ASan+UBSan and TSan clean (GitHub Actions `opus-ci.yml`).

**Machine.** The PC ran gates, self-play and training throughout (machine exclusive: no). Speed figures are
same-machine A/Bs or quiet-runner A/Bs. No Elo claims.

| job | branch (head) | status | OFF identity | new tests | sanitizers | gate (one option each; QA assigns srand) |
|---|---|---|---|---|---|---|
| 00_baseline | (all) | REPRODUCED | exact | — | — | — |
| O3 search.cpp refactor | opus-O3 (`c7eb247`) | DONE (+ review fix: 64-byte pins, claim reworded) | exact | movepicker/history/timeman, 8/8 planted bugs | ASan+UBSan 0, TSan 0 | none (no behaviour change) |
| O1 Lazy SMP audit | opus-O1 (`c0789e0`) | DONE (+ review fix: SmpBestThread mate ranking) | exact | smp_tests 70 checks; old ranking fails 8/13 | TSan full load 0 reports (200 x d12 at T2/4/8, stress 500); 2,500 self-play games clean | SmpExactNodes, SmpBestThread (SMP-only, 10+0.1) |
| C3 hard deadline | opus-C3 (`737599b`) | DONE | exact | latency_test.py, hard_deadline_regression (CTest) | ASan+UBSan 0, TSan 0 | HardDeadline=10 (expected neutral; decide by the WAC300 harness at nice 19) |
| O2 NNUE kernels | opus-O2 (`82282b0`) | DONE, +10% NPS target NOT reached | exact, bit-identical NNUE | nnue_parity_tests: 1.3M-1.6M positions on scalar/SSE2/AVX2/AVX-512 targets, same digest; 7 planted bugs caught | ASan+UBSan 0, TSan 0 | none (speed only): +3.3% bench NPS on a quiet runner |
| C6 cuckoo repetition | opus-C6 (`e08d66d`) | DONE | exact | cuckoo_tests 312k checks, 15/15 planted bugs | ASan+UBSan 0, TSan 0 | CuckooRep=true, SPRT [0,10] 10+0.1 |
| C2 correction history plus | opus-C2 (`59c982e`) | DONE | exact | 29,227 checks, 14/14 planted bugs | ASan+UBSan 0, TSan 0; T1/T8 260/260 | G-B1 CorrHistPlus=1, G-B2 CorrHistPlus=2 (+ optional =4) |
| C1 Syzygy probing | opus-C1 (`ad61284`) | DONE (+ review fix: TB scores keep their distance in the TT) | exact | syzygy_tests 36,825 checks; 17/17 + 2 planted bugs | ASan+UBSan 0, TSan 0 (with real tables, T4) | G-B6 SyzygyPath=<3-4-5 set> |
| C4 king buckets | opus-C4 | review fixes in progress (fail loudly, file-size check, "NNUE v2: active:") | exact | nnue_v2_tests 78 checks, 10/10 planted bugs | ASan+UBSan 0, TSan 0 | G-C1 (net on A1 data) |
| C5 output buckets | opus-C5 | IN PROGRESS (code, tests, CI done; report pending) | exact (to re-check after the C4 merge) | bucket index at every piece count 2..32 | CI green on 3a2f4fa | G-C6 |
| O1-LTT lockless TT | opus-O1-LTT (`df4d437`) | IN PROGRESS (code, tests, local evidence done; CI running) | exact; ON Threads=1 also exact | 28 TT groups (both modes) + stress; planted bug caught | CI running | G-B5 LocklessTT (SMP-only) |
| O5 correction-size margins | opus-O5 | IN PROGRESS (sub-agent) | — | — | — | G-B3 |
| O8 correction extensions | opus-O8 | IN PROGRESS (sub-agent, after O5) | — | — | — | G-C5 (40+0.4 primary) |
| O4 pure NNUE | — | NOT STARTED (builds on C4's v2 loader) | — | — | — | G-A5 |
| O6 threat inputs | — | NOT STARTED (builds on C4's v2 export) | — | — | — | G-C2 (40+0.4 primary) |
| O7 pawn-pair inputs | — | NOT STARTED (after O6) | — | — | — | G-C3 |

After the OPUS jobs: `SOL_LEFTOVERS_FOR_CLAUDE.md` (Sol's queue), on branches `opus-sol-<job>`. Progress is in
`SOL_LEFTOVERS_PROGRESS.md` on this branch.
