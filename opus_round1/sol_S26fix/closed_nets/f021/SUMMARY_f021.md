# S26 closed net f021 — FAIL

Source: `forge_sol_S26_f021_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `0e565beab8fc1ae39b1f47ac5f27ef5f960b9cb056d7690ab3e72310dcc8a136`, md5 `a3390ab5748d5ed99be91f6ba1ac5578` |
| verdict (v3) | FAIL — ValueError: WAC differs from documentary reference by more than3; pin/CTest evidence retained |
| bench d11/13/16/20/22 | 319575 / 794601 / 3861826 / 15637403 / 24860172 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 242 solved; documentary ref 287; FAIL |
| WAC001 d12 (UCI, Hash 8) | g3g6 mate 2 (documented pin f6h5/661) |
| CTest (v3) | 15/15 cases without failure; PASS |
| CI re-run v4 (Linux) | run 40507421791: PASS; bench equal ref; WAC 287 solved (PASS); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) | run 40507421791: PASS; bench equal ref; WAC 287 solved (PASS); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| ASan+UBSan (CI run 40507421791) | PASS; 100% tests passed, 0 tests failed out of 15; sanitizer report files 0; bench d11 319575 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
