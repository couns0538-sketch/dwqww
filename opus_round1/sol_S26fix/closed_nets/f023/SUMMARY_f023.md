# S26 closed net f023 — FAIL

Source: `forge_sol_S26_f023_native_result_20261026.json` (Sol frozen-v3 native first attempt, tool sha256 275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0; byte copy). Advice only; no net adopted.

| item | value |
|---|---|
| net | sha256 `4c5936ebcfd399508ba13032050a186733bcc6089c50b1645e94accf85b215e1`, md5 `ca088f49384a71749e2848e267176b3b` |
| verdict (v3) | FAIL — ValueError: unallowlisted test diagnostic: PIN_MISMATCH: WAC 001 documented f6h5/661/d12/PV=f6h5, observed f6h5/620/d12/PV=f6h5; re-record Job C pins in a reviewed change if the lock changed |
| bench d11/13/16/20/22 | 357687 / 836742 / 2877734 / 12036229 / 30243429 |
| frozen bench reference | equal |
| FMA (exe / NNUE object) | 0 / 0 |
| WAC300 @1000 ms (v3 box) | 238 solved; documentary ref None; UNKNOWN |
| WAC001 d12 (UCI, Hash 8) | f6h5 cp 620 (documented pin f6h5/661) |
| CTest (v3) | return code 8; check FAIL (no per-case list recorded; reason in the verdict line) |
| CI re-run v4 (Linux) | run 40507421791: FAIL; bench equal ref; WAC 284 solved (UNKNOWN); WAC001 f6h5 cp 620; forge_tests lines equal to v3 |
| CI re-run v4 (Linux) failure | ValueError: CTest case was not run: forge_tests |
| CI re-run v5 (Linux) | run 40507421791: FAIL; bench equal ref; WAC 284 solved (UNKNOWN); WAC001 f6h5 cp 620; forge_tests lines equal to v3 |
| CI re-run v5 (Linux) failure | ValueError: unallowlisted test diagnostic: PIN_MISMATCH: WAC 001 documented f6h5/661/d12/PV=f6h5, observed f6h5/620/d12/PV=f6h5; re-record Job C pins in a reviewed change if the lock changed |
| ASan+UBSan (CI run 40507421791) | PASS; 93% tests passed, 1 tests failed out of 15; sanitizer report files 0; bench d11 357687 |

WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).
