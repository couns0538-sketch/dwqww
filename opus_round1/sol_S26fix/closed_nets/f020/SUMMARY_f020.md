# S26 closed net f020 — FAIL

Source: `forge_sol_S26_f020_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `887a64c2e22694e46264c71a0b7670969880f5fdbc961f4a54d4ac6f5c5f5ba1`, md5 `9f4ffb22b6579187e82968c0628339d7` |
| verdict (v3) | FAIL — ValueError: WAC differs from documentary reference by more than3; pin/CTest evidence retained |
| bench d11/13/16/20/22 | 363303 / 799290 / 2818664 / 11474211 / 36089996 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 238 solved; documentary ref 279; FAIL |
| WAC001 d12 (UCI, Hash 8) | g3g6 mate 2 (documented pin f6h5/661) |
| CTest (v3) | 15/15 cases without failure; PASS |
| CI re-run v4 (Linux) | run 40507421791: FAIL; bench equal ref; WAC 287 solved (FAIL); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| CI re-run v4 (Linux) failure | ValueError: WAC differs from documentary reference by more than3; pin/CTest evidence retained |
| CI re-run v5 (Linux) | run 40507421791: FAIL; bench equal ref; WAC 287 solved (FAIL); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) failure | ValueError: WAC differs from documentary reference by more than3; pin/CTest evidence retained |
| ASan+UBSan (CI run 40507421791) | PASS; 100% tests passed, 0 tests failed out of 15; sanitizer report files 0; bench d11 363303 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
