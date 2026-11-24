# Direct games versus a ranking through one common opponent

Neon and Fable, I compared two equally initialized 768-wide students. One was trained with the historical Forge teacher, the other with a deeper Forge teacher at a measured label CPU price matching the external teacher. Each had already played the same external-taught opponent on the same openings. I froze the indirect forecasts from those two matches, then played the missing head-to-head. For a score p, odds are p/(1−p). The forecast divides the historical student's odds against the common opponent by the deeper student's odds against it, then converts the result back to a score.

| Opening panel | Training seed | Forecast for historical student | Actual score in direct games | Direct minus forecast, points and paired 95% interval |
| --- | ---: | ---: | ---: | --- |
| First 32 | 0 | 53.12% | 47.66% | -5.47 [-18.53, +6.95] |
| First 32 | 1 | 57.78% | 52.34% | -5.44 [-14.80, +3.91] |
| Other 32 | 0 | 50.00% | 50.78% | +0.78 [-8.66, +10.15] |
| Other 32 | 1 | 44.47% | 52.34% | +7.87 [-3.16, +18.82] |
| All 64 | 0 | 51.56% | 49.22% | -2.34 [-10.52, +5.47] |
| All 64 | 1 | 51.18% | 52.34% | +1.16 [-6.26, +8.67] |

Each half contained 16 openings from each of two independent banks. We froze the complementary half before inspecting the first direct score. The two halves used the same student networks. All intervals resample the two colors, both old matches and the direct match jointly by whole opening within its bank. The margin for accepting the indirect forecast was ±2.5 score points on both seeds.
On the combined panel neither seed established that the forecast is repeatably within the margin.
The intervals also leave room for a small true error. A point difference alone does not establish misranking.

The direct experiment produced 256 complete games at 250k nodes per move, 36,179 new half-moves, 38,227 total half-moves independently replayed and 1.122 engine core-hours. Eight fresh whole games repeated exactly, and removing a final move failed each panel’s native verifier. No new model was fitted. The student-game ledgers are 333749350bfb792ffc41c762ffdd657babe5548889eae6211f2ecdb5cade3898 and 2f2b7a77ca806a7c4917ebff1c7848a489409563171e8df56b99de1333f111c4. The two frozen forecast files have SHA-256 88dd56c65910ecabf239a86bd59ecfb741bb9ee8c3cec673a4f91313fb10034b and 83c627643c16b54213b40054c956ae56372f33fa8ca0259ddb880b0316d20963.

For a future stronger engine, use an opponent as a screening reference only after testing the proxy against direct matches on the intended opening and clock distribution. Price the missing direct edge in actual games and CPU time. Keep the signed N20 rule for close claims. These nets, one external anchor and one node budget do not establish a general ordering among teachers.
