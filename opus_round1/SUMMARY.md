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
| C3 hard deadline | opus-C3 (`c1748a9`) | DONE (+ 2026-10-27: watchdog fallback obeys searchmoves; DebugSearchDelayMs only in debug/test builds; CI incl. TSan hook green) | exact | latency_test.py, hard_deadline_regression (CTest) | ASan+UBSan 0, TSan 0 | HardDeadline=10 (expected neutral; decide by the WAC300 harness at nice 19) |
| O2 NNUE kernels | opus-O2 (`82282b0`) | DONE, +10% NPS target NOT reached | exact, bit-identical NNUE | nnue_parity_tests: 1.3M-1.6M positions on scalar/SSE2/AVX2/AVX-512 targets, same digest; 7 planted bugs caught | ASan+UBSan 0, TSan 0 | none (speed only): +3.3% bench NPS on a quiet runner |
| C6 cuckoo repetition | opus-C6 (`be33b83`) | DONE (+ own lmp_threshold copy for the CuckooRep instance) | exact | cuckoo_tests 312k checks, 15/15 planted bugs | ASan+UBSan 0, TSan 0 | CuckooRep=true, SPRT [0,10] 10+0.1 |
| C2 correction history plus | opus-C2 (`59c982e`) | DONE | exact | 29,227 checks, 14/14 planted bugs | ASan+UBSan 0, TSan 0; T1/T8 260/260 | G-B1 CorrHistPlus=1, G-B2 CorrHistPlus=2 (+ optional =4) |
| C1 Syzygy probing | opus-C1 (`ad61284`) | DONE (+ review fix: TB scores keep their distance in the TT) | exact | syzygy_tests 36,825 checks; 17/17 + 2 planted bugs | ASan+UBSan 0, TSan 0 (with real tables, T4) | G-B6 SyzygyPath=<3-4-5 set> |
| C4 king buckets | opus-C4 (`23750a7`) | DONE (+ review fixes: fail loudly with exit 2, file size checked before reading, "NNUE v2: active:" line) | exact | nnue_v2_tests 101, UCI fail-loud 17/17, 13/13 planted bugs | ASan+UBSan 0, TSan 0 | G-C1 (net on A1 data) |
| C5 output buckets | opus-C5 (`57066d2`) | DONE (C4 review fixes merged) | exact | 141 unit checks (bucket at every piece count 2..32), UCI 26/26, 8/8 planted bugs; parity 10000/10000 | ASan+UBSan 0, TSan 0 | G-C6 NNUEOutputBuckets=8 |
| O1-LTT lockless TT | opus-O1-LTT (`da677d7`) | DONE (+ 2026-10-27: "info string LocklessTT active" on setoption true) | exact; ON Threads=1 also exact | 28 TT groups (both modes) + stress; planted bug caught | CI running | G-B5 LocklessTT (SMP-only) |
| O5 correction-size margins | opus-O5 (`e9ff3f4`) | DONE | exact; default alpha-beta instruction-identical | corr_margins_tests 55,390 checks, 20/20 planted bugs; ON pins d11 343365 d13 858019 d16 2522546 d20 12894582 d22 22287047 | ASan+UBSan 0, TSan 0 | G-B3 CorrMargins=1, 10+0.1 (confirm 40+0.4) |
| O8 correction extensions | opus-O8 (`3ef4ded`) | DONE | exact; default alpha-beta instruction-identical | corr_ext_tests 8.8M rule decisions, 19/19 planted bugs; ON pins d11 312961 d13 838790 d16 2891507 d20 12313394 d22 33298237 | ASan+UBSan 0, TSan 0 | G-C5 CorrExt=1, primary 40+0.4 |
| O4 pure NNUE | opus-O4 (`348d860`) | DONE (UCI PureNnue, default 0; see its REPORT) | exact | see REPORT | see REPORT | G-A5 |
| O6 threat inputs | opus-O6 (`aaaf425`) | DONE (UCI NNUEThreats, default 0; see its REPORT) | exact | see REPORT | see REPORT | G-C2 (40+0.4 primary) |
| O7 pawn-pair inputs | opus-O7 (`f422a48`) | DONE (UCI NNUEPawnPairs, default 0; see its REPORT) | exact | see REPORT | see REPORT | G-C3 |

After the OPUS jobs: `SOL_LEFTOVERS_FOR_CLAUDE.md` (Sol's queue), on branches `opus-sol-<job>`. Progress is in
`SOL_LEFTOVERS_PROGRESS.md` on this branch.

## Added 2026-10-27 (user jobs outside the Opus plan)
| job | branch (head) | status | OFF identity | new tests | sanitizers / speed |
|---|---|---|---|---|---|
| S29 step 8: one FORGE_SPEEDSTACK build on the PC | opus-sol-S29 (`81a8031`) | DONE | ON node-exact (all 5 depths, perft, kiwipete) | — | PC NPS under load −0.4..+0.3% (inside noise); quiet runner +0.2/+0.5% |
| S-IT intended threefold (FIDE 9.2.1, issue #7) | opus-sol-SIT (`fc3bd2a`) | DONE | exact (bench, perft) | intended_threefold_tests 67 checks (11,720-position brute-force cross-check), uci_regression; 6/6 planted bugs | ASan/UBSan/TSan 0; quiet runner: off vs lock +0.06/+0.59%, on vs off 0.00/−0.25% |

## Sol queue (`SOL_LEFTOVERS_FOR_CLAUDE.md`), one branch per job `opus-sol-<JOB>`; one line each in `SOL_LEFTOVERS_PROGRESS.md`
- **Section 2, Sol's numbered jobs:** S11-S50 DONE; S22 COVERED by opus-O1.
  - Engine changes (all default OFF, OFF = lock binary, CI green): S11, S13, S29, S32 (datagen), S37 (microbench), S41 (NetScale), S08fix (profile counters),
    S04fix (ON cold-init).
  - The rest are tools, studies and evidence (`[skip ci]`).
- **Section 2, Astra:**
  - A1 `HistRework` (engine, OFF = lock, CI 40515121020 green, gate `HistRework=2` first);
  - A2 king-bucket doc (C4 covers the implementation);
  - A3 full-NNUE pipeline without engine integration;
  - A7 long-training recipe.
- **Section 2, test-plan jobs:**
  - S-A1 more-data recipe;
  - S-A3 v3d trainer (LR schedules);
  - S-A6 SPSA plan;
  - S-C4 hidden 768-1024 plan with a measured width cost;
  - S-A2 `NnueInt16` + trainer weight clip and S-A4 H512 build flags (engine, OFF = lock, CI green).
- **Section 3, fix-ups:** S04-S10, S25-S28, S33, S48 DONE (Linux CI green where the fix-up has a workflow).
- **Gates:** none were run by us. Every gate-ready candidate names its option, value, SPRT and srand in its REPORT.
