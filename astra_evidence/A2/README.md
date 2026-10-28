# A2 native validation (2026-10-29)

Base: `da15814975e224e770f4d25195e0551d02afae48` (`opus-r3-stack`).

The requested `smp_select_result` is named `Searcher::select_best_thread` / `better_thread_result` in this base. Mate protection was already implemented; this patch protects the TB-win band behind `SmpProtectProvenScore=false`. Requires `SmpBestThread=true` to affect result selection. UCI changes options only after stopping/joining search.

Every native bench result from the initial qualification follows. Threads=1, Hash=16, OwnBook=false (bench defaults). The ON run explicitly enables SmpBestThread and SmpProtectProvenScore. Compilation/test load overlapped these runs; timing and NPS are recorded as raw output, not comparable performance evidence.

| Mode | Depth | Nodes | Time ms | NPS |
|---|---:|---:|---:|---:|
| base | 11 | 312866 | 332 | 942367 |
| base | 13 | 862329 | 861 | 1001543 |
| base | 16 | 3024920 | 2861 | 1057294 |
| base | 20 | 12389307 | 11118 | 1114346 |
| base | 22 | 34048354 | 37035 | 919356 |
| OFF | 11 | 312866 | 662 | 472607 |
| OFF | 13 | 862329 | 1458 | 591446 |
| OFF | 16 | 3024920 | 5709 | 529851 |
| OFF | 20 | 12389307 | 18165 | 682042 |
| OFF | 22 | 34048354 | 39447 | 863141 |
| ON | 11 | 312866 | 557 | 561698 |
| ON | 13 | 862329 | 1371 | 628978 |
| ON | 16 | 3024920 | 7258 | 416770 |
| ON | 20 | 12389307 | 18690 | 662884 |
| ON | 22 | 34048354 | 34526 | 986165 |

NNUE object FMA count: **0**. UCI output differs from base by exactly the new default-false option.

Initial full Release CTest: **52/54 passed**, exit 8. `forge_tests` has the four original horizon/underpromotion diagnostics (WAC score 623). `forge_smp_tests` additionally failed its node-overshoot assertion once at 27,398 nodes. All original output is retained. Subsequent serial baseline and candidate SMP suites each pass **133/133**. Focused ASan/UBSan/LeakSanitizer passes **17/17** outside the tracing sandbox. The first sandbox run failed because LeakSanitizer cannot operate under ptrace; retained separately. The original full suite remains recorded as failed, and scheduling causality is not proven.

Focused regression: original production comparator reproducer fails the two TB-overwrite assertions; candidate native test passes 17 assertions, including the actual selector and helper chains. One earlier candidate fixture reused the main best move and failed; its correction uses distinct legal moves without changing engine behavior.

Limits: no tablebase files are installed for an end-to-end Syzygy probe test. Fixtures drive the actual selector with score records. The engine has no per-result proof tag and ordinary evaluation can reach this score band; this is conservative score-band protection. No Windows qualification, speed, adoption or Elo claim.

Build: `cmake -S . -B /tmp/forge-astra-build-j5fix-20261029 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"`; `cmake --build ... -j2`; `ctest --test-dir ... --output-on-failure --timeout 180 -j2`.

IDEA_SOURCE: Owner A2 and Forge source only.

Final qualification: baseline `forge_tests` was run natively; its four diagnostics exactly match the candidate. No expected values were changed. Both perft CTests and the UCI/SMP UCI suites passed in the full run.
