# Final independent suite audit

Evidence integrity checks passed for all 118 planned runtime commands and all 100 builds. The test suite retains five completed failures and one incomplete timeout; it is not a clean test pass.

| Mode | Attempted | Completed | Passed | Failed | Incomplete |
|---|---:|---:|---:|---:|---:|
| Release | 59 | 59 | 56 | 3 | 0 |
| ASAN/UBSAN | 59 | 58 | 56 | 2 | 1 |

Release failures are the original t12 KRK miss (1/400 main tests, with 0/100 T1 preflight misses) and the two literal options/clamp fixture comparisons. ASAN retains the two literal fixture failures and its t12 timeout: exit 124 after the unchanged 440-second command bound, with both raw streams empty. No KRK search or preflight count is credited to that incomplete invocation; empty buffered output does not establish how much work occurred internally. All six immutable fault files match their original metadata and full streams byte-for-byte.

All 118 stdout/stderr pairs, execution argv/cwd/environment/input/plan pins, recorded exit/signal statuses, perft checks and state rows agree. Independent broader scanning classified all 76 matching diagnostic/error/failure words and found no additional hidden failure or sanitizer diagnostic. All 31 runtime batch records agree with their executor results. All 34 published packages reconstruct exactly: 696 source files, including build logs, plans and runtime evidence.

All 99 original source/test/input/CMake fingerprints remain unchanged. All 100 build artifact hashes and sizes match the retained build manifest. Every test build uses final -UNDEBUG, with no direct test-source NDEBUG override. The frozen Release and ASAN engine object builds retain -DNDEBUG: test-driver assertions are enabled, core-engine assertions are compiled out. ASAN/UBSAN instrumentation remains a separate check.

The 40 earlier fixture repetitions were independently compared again. All 20 ASAN repetitions now match their corresponding original ASAN outputs byte-for-byte, as do all 20 Release repetitions. Each options output differs from the unchanged literal expected file only by 44 added advertised-option lines; each clamp output by 66. All 40 literal failures remain failures. The earlier observation that original ASAN outcomes were unavailable at repetition start is preserved; this is a later comparison against those now-finalized outputs.

The audit ran at 2026-11-14 22:55:11–22:55:15 UTC, using only read-only access to original evidence. Follow-up focused KRK repeats, manual clock cases and alternating KRK rate trials are excluded from these 118 runtime entries. No tests, searches or engines were executed by this audit, and no source, state or Git data was edited.

See summary.txt, build-audit.txt, runtime-audit.txt, source-fingerprints.txt, publication-audit.txt, fault-audit.txt, marker-lines.txt and fixture-retrospective-comparison.txt. The exact verifier and inert twin, actual stdout/stderr and command are retained alongside them.
