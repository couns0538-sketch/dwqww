# S26 closed net f019 — FAIL

Source: `forge_sol_S26_f019_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `88486104a9f553f64f0c8f6e897ad6dc373f1e1d28efd5e676d061280699fa82`, md5 `560c1fcc96362cc3d5584f26b4175ace` |
| verdict (v3) | FAIL — ValueError: WAC differs from documentary reference by more than3; pin/CTest evidence retained |
| bench d11/13/16/20/22 | 436412 / 1053482 / 3392913 / 9497467 / 25814067 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 260 solved; documentary ref 286; FAIL |
| WAC001 d12 (UCI, Hash 8) | g3g6 mate 2 (documented pin f6h5/661) |
| CTest (v3) | 15/15 cases without failure; PASS |
| CI re-run v4 (Linux) | run 40507421791: PASS; bench equal ref; WAC 283 solved (PASS); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) | run 40507421791: PASS; bench equal ref; WAC 285 solved (PASS); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| ASan+UBSan (CI run 40507421791) | PASS; 100% tests passed, 0 tests failed out of 15; sanitizer report files 0; bench d11 436412 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
