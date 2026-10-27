# S26 closed net B_lock — PASS

Source: `forge_sol_S26_B_lock_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`, md5 `6d22f612c855e17c62d396d32da99ea4` |
| verdict (v3) | PASS (v3 qualification passed; no adoption, no Elo/speed claim) |
| bench d11/13/16/20/22 | 308972 / 745494 / 2460422 / 11901452 / 31111774 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 268 solved; documentary ref None; UNKNOWN |
| WAC001 d12 (UCI, Hash 8) | f6h5 cp 661 (documented pin f6h5/661) |
| CTest (v3) | 15/15 cases without failure; PASS |
| CI re-run v4 (Linux) | run 40507421791: PASS; bench equal ref; WAC 282 solved (UNKNOWN); WAC001 f6h5 cp 661; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) | run 40507421791: PASS; bench equal ref; WAC 284 solved (UNKNOWN); WAC001 f6h5 cp 661; forge_tests lines equal to v3 |
| ASan+UBSan (CI run 40507421791) | PASS; 100% tests passed, 0 tests failed out of 15; sanitizer report files 0; bench d11 308972 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
