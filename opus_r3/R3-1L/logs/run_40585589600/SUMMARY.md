# R3-1L Linux self-play double-check

release: 4 configs, 2000 games, 0 errors, 0 failing rows; sanitizer (ASan+UBSan / TSan): 2 rows, 200 games, 0 errors, 0 failing rows; jobs without artifact: none.

Pass rule: all requested games (500 per release config) with 0 errors and a clean preflight, identity ALL OK (and FMA 0) for every build, 0 sanitizer reports.

| job | mode | config | exe (sha256) | identity | games | plies | errors | errors by kind | crashes | illegal moves | double bestmoves | timeouts | malformed | watchdog answers | HardDeadline fired | late after watchdog | sanitizer reports | wall s | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fin-all_on_final | release | all_on_final | allsw `33a1a1c8e2ab` | ALL OK, FMA 0 | 500/500 | 55037 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 595.3 | **PASS** |
| fin-smp_helpers_past_depth | release | smp_helpers_past_depth | base `d6190041a757` | ALL OK, FMA 0 | 500/500 | 48500 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 442.2 | **PASS** |
| fin-spsa_plus10 | release | spsa_plus10 | base `d6190041a757` | ALL OK, FMA 0 | 500/500 | 55625 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 357.2 | **PASS** |
| fin-spsa_minus10 | release | spsa_minus10 | base `d6190041a757` | ALL OK, FMA 0 | 500/500 | 55963 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 360.2 | **PASS** |
| fin-tsan-all_on_final | tsan | all_on_final | allsw `96fb7f0128c2` | ALL OK | 100/100 | 10988 | 0 | - | 0 | 0 | 0 | 0 | 0 | 500 | 500 | 0 | 0 | 309.1 | **PASS** |
| fin-tsan-smp_helpers_past_depth | tsan | smp_helpers_past_depth | base `a9dd5db2560a` | ALL OK | 100/100 | 10571 | 0 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 304.1 | **PASS** |
