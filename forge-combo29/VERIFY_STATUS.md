# VERIFY_STATUS

Base: `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Checked: 2026-11-14. `review/verify-grok47` did not exist at the start of the first run, so every `grok47/t*` tip then was new. Second check, 2026-11-14 07:06Z: `t12`, `t15`, and `t18` were new, and `t19` moved from `d133b998` to `d5e60c9d`. Third check, 2026-11-14 10:16Z: `t9` is new. `t1`, `t2`, `t4`, `t5`, `t6`, `t7`, `t8`, `t10`, `t12`, `t13`, `t14`, `t15`, `t16`, `t17`, `t18`, `t19`, and `t20` moved. `t3` (`5e7fda216e1c03981ede2955f9cf14866f6c992a`) and `t11` (`f00b8ef5f4e0adcc67dfe4ce1295a36b28a9432c`) still match their rows and were not rebuilt. Every moved tip except `t9` changed report text only; the engine and tests were built and run again anyway.

Host compiler: `/usr/bin/c++` is Clang 18.1.3 and the stated cmake line fails in the compiler test with `cannot find -lstdc++`. Every build below was reconfigured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0). `/proc/cpuinfo` has `avx512f`, so `-DFORGE_PORTABLE` and `-DFORGE_MARCH=x86-64-v3` were not added. ASan/UBSan runs set `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. LeakSanitizer was off, so this run does not speak to leaks.

Release pins, Threads 1, Hash 16, OwnBook false, every branch below and the lock, including `t19` built with `-DFORGE_NNUE_HIDDEN=512`: bench 11 nodes 312866, bench 13 nodes 862329, `position startpos` / `go perft 5` nodes 4865609.

| branch | commit | verdict | reason | UTC date |
| --- | --- | --- | --- | --- |
| grok47/t1-capture-overflow | 59480d0461c55629321b1741dce74b3bec76c06a | PASS | Widens the 64-slot losing-capture array; ASan dies at search.cpp:469 on the lock and the branch search returns a legal move. | 2026-11-14 |
| grok47/t2-badcap-bound | 19195ffaf323303e5a025ff23e6dd323b784882c | PASS | Same overflow fix, and a finite search finishes after stdin EOF. Better than t1: the lock UCI path returns h2f1 without reaching the crash, and this branch returns b4a3. | 2026-11-14 |
| grok47/t3-clock-parse | 5e7fda216e1c03981ede2955f9cf14866f6c992a | PASS | 64-bit clocks keep wtime 3000000000 searching and accept movetime +80. depth +8 still stops at depth 1. | 2026-11-14 |
| grok47/t4-clock-parse | a72b477095b70c0cc99d57caf98901a0c5891fce | PASS | Also accepts a leading plus on depth. Better than t3: the clock checker printed pass on all 23 searches, and depth +8 reaches depth 8. | 2026-11-14 |
| grok47/t5-krk-mate | 7f824bd0ab8f84a83d659980a92b04da31d01e96 | PASS | The KRK test FAILED 6 on the lock and printed ok here, including the 30000-node two-thread check. | 2026-11-14 |
| grok47/t6-fixed-node-score | 920a20c939d201dd08523044f7b0e8aba8eeb6ea | PASS | Fixed-node score and move agreed on 176 checks here and failed 27 on the lock. Bench does not set a node limit, and the pins match. | 2026-11-14 |
| grok47/t7-nnue-file | 417f021f1ab98dbbbd2ba12b4dd061ab3e70199f | PASS | NnueFile defaults to empty and the pins stay put. Better engine change than t8: a successful load calls Searcher::clear(). | 2026-11-14 |
| grok47/t8-nnue-file | 7d3b7dfc1a3ac2d345a033743d7e1edc2542d465 | PASS | NnueFile loads the converted net and bench 11 stays 312866. A successful load only clears the hash. | 2026-11-14 |
| grok47/t9-eval | ff4d8498c6d77b3e53a899fd3a88ab984748ee77 | PASS | eval prints hce, nnue, and their sum. The test does not compile on the lock, and the pins stay on the lock counts. | 2026-11-14 |
| grok47/t10-multipv | f6de2baa0d6efbdf69c87ba2f155067afab4219d | PASS | MultiPV defaults to 1, the pins match, and the test does not compile on the lock. Better than t15. | 2026-11-14 |
| grok47/t11-integrate | f00b8ef5f4e0adcc67dfe4ce1295a36b28a9432c | FIX NEEDED | The bundled t1, t3, t6 and t8 tests passed and the pins match, but the branch also adds those other tasks' reports and tests, outside tests_t11/ and REPORT_t11.md. | 2026-11-14 |
| grok47/t12-krk-root-cause | 0d928468f48805ef8ff25c8b9c682d5d66898ad6 | PASS | Two-thread depth-14 KRK test missed 0 of 400 here. The same 40 by 10 run on the lock also missed 0. Pins match. The report's single-position 400-repeat was not re-run. | 2026-11-14 |
| grok47/t13-thread-sanitizer | 87228469411670ea5ccfc7154ce181dd55d599df | FIX NEEDED | Concurrent first Board use SEGV on the lock under ASan/UBSan and passes here, but WHAT_WAS_WRONG_t13.md is outside the allowed paths. | 2026-11-14 |
| grok47/t14-eval-command | 26f450b684178a7241bcab3b9a2a6b8886420daf | FIX NEEDED | eval and the 30-position test pass, but CMakeLists.txt and README.md are outside the allowed paths. | 2026-11-14 |
| grok47/t15-multipv | e2d4e1a6a13026cdb295a296631f141818bef70e | PASS | MultiPV test printed RESULT passed with the option left at 1, and it does not compile on the lock. t10 is better: this branch clears nodes, movetime, and the clock for each extra line. | 2026-11-14 |
| grok47/t16-option-handling | 0b329db6d99961ea2b4797fec066d6a80da854f8 | PASS | Option, clamp, book and search transcripts match this branch and fail on the lock. | 2026-11-14 |
| grok47/t17-rules-suite | 7afa73cc4c34ea857b65077b697a51a568851d1c | PASS | Rules suite printed RESULT PASS fails=0, including the six published perft counts. It does not compile on the lock. | 2026-11-14 |
| grok47/t18-uci-fuzz | e73c7e6febaaf1f5794ceb3f229766ae80b20e00 | PASS | Default-off UCI fuzz passed 193 hand-written cases and 200000 generated lines under ASan/UBSan, and the test does not compile on the lock. | 2026-11-14 |
| grok47/t19-wide-net-parity | 29b90257924de9947ce17486ae4e4f876b74b9d4 | FIX NEEDED | 100000 evals still match, including against the lock's 256 objects, and the 512 build kept the pins. CMakeLists.txt and KRK_FINDINGS.md are outside the allowed paths, and nnue.cpp includes tests_t19. | 2026-11-14 |
| grok47/t20-repeatable-search | a788bd149eada38a3147033a4d5c0838436771ef | PASS | No engine diff. The repeatability test printed t20 result PASS on this commit and on the lock. | 2026-11-14 |

Pairs: t2 is the better capture fix, t4 is the better clock fix, t7 is the better NNUE-file fix. t10 is the better MultiPV change: t15 clears nodes, movetime, and the clock for each extra line. t9 adds `eval` and does not overlap those pairs.
