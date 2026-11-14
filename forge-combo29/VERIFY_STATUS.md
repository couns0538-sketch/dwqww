# VERIFY_STATUS

Base: `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Checked: 2026-11-14. `review/verify-grok47` did not exist at the start of the first run, so every `grok47/t*` tip then was new. Second check, 2026-11-14 07:06Z: `t12`, `t15`, and `t18` were new, and `t19` moved from `d133b998` to `d5e60c9d`. Every other `grok47/t*` tip still matched its row and was not rebuilt.

Host compiler: `/usr/bin/c++` is Clang 18.1.3 and the stated cmake line fails in the compiler test with `cannot find -lstdc++`. Every build below was reconfigured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0). `/proc/cpuinfo` has `avx512f`, so `-DFORGE_PORTABLE` and `-DFORGE_MARCH=x86-64-v3` were not added. ASan/UBSan runs set `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. LeakSanitizer was off, so this run does not speak to leaks.

Release pins, Threads 1, Hash 16, OwnBook false, every branch below and the lock: bench 11 nodes 312866, bench 13 nodes 862329, `position startpos` / `go perft 5` nodes 4865609.

| branch | commit | verdict | reason | UTC date |
| --- | --- | --- | --- | --- |
| grok47/t1-capture-overflow | 48644054dd67fd5abf547cd00de1c9943411baf9 | PASS | Widens the 64-slot losing-capture array; ASan dies at search.cpp:469 on the lock and the branch search returns a legal move. | 2026-11-14 |
| grok47/t2-badcap-bound | ad702bf619532194df10c6f643c9dada9e4b8c55 | PASS | Same overflow fix, and a finite search finishes after stdin EOF. Better than t1: the lock UCI path returns h2f1 without reaching the crash, and this branch returns b4a3. | 2026-11-14 |
| grok47/t3-clock-parse | 5e7fda216e1c03981ede2955f9cf14866f6c992a | PASS | 64-bit clocks keep wtime 3000000000 searching and accept movetime +80. depth +8 still stops at depth 1. | 2026-11-14 |
| grok47/t4-clock-parse | 0ccc839bd9c4c2c73070b1fa5048cbd8009e9eb9 | PASS | Also accepts a leading plus on depth. Better than t3: depth +8 prints the depth-8 line the lock and t3 do not, and a huge wtime still reaches the depth-12 line. | 2026-11-14 |
| grok47/t5-krk-mate | 143edfb6e85ed5c8bc83c58aa786ac7dbad61f32 | PASS | The KRK test FAILED 6 on the lock and passed here, including the 30000-node two-thread check, on both the sanitizer link and a release link. | 2026-11-14 |
| grok47/t6-fixed-node-score | 9b0e6ae1176fa875a89e6cf15d4208a1656fa020 | PASS | Fixed-node score and move agreed on 176 checks here and failed 27 on the lock. | 2026-11-14 |
| grok47/t7-nnue-file | b56c6328a43fee23eaa7d9b9435ff5b029f343fc | PASS | NnueFile loads a converted lock net and the pins stay put. Better engine change than t8: a successful load calls Searcher::clear(), not only clear_hash(). | 2026-11-14 |
| grok47/t8-nnue-file | 62997d98344c5cbacb289512b77d88025abcce8a | PASS | NnueFile loads the converted net and bench 11 stays 312866. A successful load only clears the hash. The rejection test is stricter than t7. | 2026-11-14 |
| grok47/t10-multipv | 935b359e528cd1cbf188af6be26d5a906c53d5b0 | PASS | MultiPV test passed with the new option left at default, and the test does not compile on the lock. | 2026-11-14 |
| grok47/t11-integrate | f00b8ef5f4e0adcc67dfe4ce1295a36b28a9432c | FIX NEEDED | The bundled t1, t3, t6 and t8 tests passed and the pins match, but the branch also adds those other tasks' reports and tests, outside tests_t11/ and REPORT_t11.md. | 2026-11-14 |
| grok47/t12-krk-root-cause | 5485588b3b6147340d82a2a10059dc473645c821 | PASS | Two-thread depth-14 KRK test missed 1 of 400 on the lock and 0 of 400 here, and bench 11, bench 13, and perft 5 stayed on the lock counts. | 2026-11-14 |
| grok47/t13-thread-sanitizer | a847f23765d9404725449a9c8f3fe3c7c78685f2 | PASS | Concurrent first Board use SEGV on the lock under ASan/UBSan and passes here. race_driver passed on both. ThreadSanitizer was not run. | 2026-11-14 |
| grok47/t14-eval-command | ed31021d6d3ea68e7dc626f21eb3d8379e23e653 | FIX NEEDED | eval and the 30-position test pass, but CMakeLists.txt and README.md are outside the allowed paths. | 2026-11-14 |
| grok47/t15-multipv | 28ee8b54e2dc44423aafe9f28eac62f4e684fe98 | PASS | MultiPV test printed RESULT passed with the option left at 1, and it does not compile on the lock. t10 is better: this branch clears the node and time limits on every extra line. | 2026-11-14 |
| grok47/t16-option-handling | c3468fc9262edbd8068d2b9ac5244379e055f756 | PASS | Option, clamp, book and search transcripts match this branch and fail on the lock. | 2026-11-14 |
| grok47/t17-rules-suite | 3438c19e92b3f3919b1cd089b2e7e3162bbeee45 | PASS | Rules suite printed RESULT PASS fails=0, including the six published perft counts. It does not compile on the lock. | 2026-11-14 |
| grok47/t18-uci-fuzz | d1d10b3efa267de6e17f3bcb10b9564d714a4c05 | PASS | Default-off UCI fuzz passed 193 hand-written cases and 200000 generated lines under ASan/UBSan, and the test does not compile on the lock. | 2026-11-14 |
| grok47/t19-wide-net-parity | d5e60c9dcbabff4fe6a16a095f5ed0bb8d9bc92e | FIX NEEDED | 100000 evals still match, including against the lock's 256 objects, and the 512 build kept the pins. CMakeLists.txt is outside the allowed paths and nnue.cpp includes tests_t19. | 2026-11-14 |
| grok47/t20-repeatable-search | 9f48a760552c385e98a18f29b6733c36c067cbdf | PASS | No engine diff. The repeatability test printed t20 result PASS on this commit and on the lock. | 2026-11-14 |

There is no `grok47/t9*` branch. Pairs: t2 is the better capture fix, t4 is the better clock fix, t7 is the better NNUE-file fix. t10 is the better MultiPV change: t15 clears nodes, movetime, and the clock for each extra line.
