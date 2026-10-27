# S26 closed net f022 — PASS

Source: `forge_sol_S26_f022_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `f487f04e64519fa6e5a283554204923e538e5dd1082dde77dd689613f0da1cf5`, md5 `4e36411f0fdd5afb9c816f8740110557` |
| verdict (v3) | PASS (v3 qualification passed; no adoption, no Elo/speed claim) |
| bench d11/13/16/20/22 | 291058 / 884859 / 2658642 / 12506971 / 26484975 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 226 solved; documentary ref None; UNKNOWN |
| WAC001 d12 (UCI, Hash 8) | g3g6 mate 2 (documented pin f6h5/661) |
| CTest (v3) | 15/15 cases without failure; PASS |
| CI re-run v4 (Linux) | run 40507421791: PASS; bench equal ref; WAC 285 solved (UNKNOWN); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) | run 40507421791: PASS; bench equal ref; WAC 285 solved (UNKNOWN); WAC001 g3g6 mate 2; forge_tests lines equal to v3 |
| ASan+UBSan (CI run 40507421791) | PASS; 100% tests passed, 0 tests failed out of 15; sanitizer report files 0; bench d11 291058 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
