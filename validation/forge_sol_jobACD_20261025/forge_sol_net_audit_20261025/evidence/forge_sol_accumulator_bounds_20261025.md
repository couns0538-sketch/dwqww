# Forge Job A independently recomputed accumulator bounds — 20261025
Each range is a conservative possible-prefix superset in integer q units (real=q/4096), not an observed or attainable range. All13 manifest hashes match. No speed or strength claim.
| Net | q min32 | q max32 | q min64 | q max64 | abs top32+4dirty | abs all768+4dirty | int32 / float exact-grid |
|---|---:|---:|---:|---:|---:|---:|---|
| lock_e12 | -219282 | 123238 | -379512 | 235351 | 259471 | 1662360 | PASS / PASS |
| e32_f003 | -326161 | 145444 | -509013 | 270955 | 377427 | 1978144 | PASS / PASS |
| e16_f004 | -220295 | 109619 | -383973 | 207779 | 259245 | 1523652 | PASS / PASS |
| e24_f005 | -217319 | 107759 | -331211 | 205526 | 256977 | 1438848 | PASS / PASS |
| e48_f006 | -279224 | 148321 | -506797 | 278156 | 323541 | 2218441 | PASS / PASS |
| e16_f007 | -224719 | 130291 | -351616 | 246650 | 265799 | 1526440 | PASS / PASS |
| e20_f008 | -208489 | 117191 | -355056 | 220166 | 246276 | 1591707 | PASS / PASS |
| e16_f009 | -208162 | 132569 | -341538 | 255103 | 251151 | 1557076 | PASS / PASS |
| e16_f010 | -211525 | 127195 | -318754 | 241531 | 247674 | 1477082 | PASS / PASS |
| e20_f011 | -276371 | 131597 | -516727 | 256340 | 315463 | 1569370 | PASS / PASS |
| e16_f012 | -205125 | 145004 | -345733 | 269875 | 242129 | 1539796 | PASS / PASS |
| e20_f013 | -194591 | 113024 | -331427 | 207626 | 229760 | 1516258 | PASS / PASS |
| e20_f014 | -200185 | 115181 | -303279 | 219089 | 236957 | 1530515 | PASS / PASS |

All full768+dirty4 bounds are below2^24=16777216 and int32_max=2147483647. A refresh-only AVX2 int32 path that converts q to float then divides by4096 exactly can feed the unchanged float output layer without loss. This does not justify output requantization. True int16 accumulators are excluded. Existing float accumulators need not be changed.
