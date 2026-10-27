OFF reference (Sol S07 native WAC300, Lprime build, 1000 ms): **271/300**.

| idea | ON | delta vs OFF | lost (OFF ok, ON fail) | gained (OFF fail, ON ok) |
|---|---:|---:|---|---|
| QuietCheckLmpSurvival | 269 | -2 | WAC.071, WAC.080, WAC.081, WAC.089, WAC.169, WAC.193, WAC.218, WAC.229, WAC.232, WAC.243, WAC.297 | WAC.033, WAC.101, WAC.165, WAC.190, WAC.196, WAC.205, WAC.226, WAC.245, WAC.265 |
| ImprovingRazorGuard | 270 | -1 | WAC.071, WAC.087, WAC.092, WAC.181, WAC.243, WAC.261, WAC.262, WAC.270 | WAC.021, WAC.033, WAC.049, WAC.101, WAC.165, WAC.190, WAC.296 |
| SingularSiblingLmr | 263 | -8 | WAC.046, WAC.081, WAC.082, WAC.119, WAC.180, WAC.191, WAC.193, WAC.194, WAC.218, WAC.229, WAC.236, WAC.238, WAC.264, WAC.297 | WAC.021, WAC.033, WAC.101, WAC.165, WAC.196, WAC.256 |
| CaptureHistoryLmp | 258 | -13 | WAC.071, WAC.081, WAC.180, WAC.181, WAC.193, WAC.229, WAC.231, WAC.232, WAC.239, WAC.243, WAC.250, WAC.282, WAC.288, WAC.289, WAC.297 | WAC.033, WAC.190 |

Cross-idea view (a flip shared by 3-4 of the 4 ideas is more likely run-to-run noise of the single OFF run than an effect of one idea):

| idea | lost | gained | lost only by this idea | lost by >=3 ideas | gained by >=3 ideas | median NPS ON / OFF (final info line) | mean depth ON-OFF |
|---|---:|---:|---|---:|---:|---:|---:|
| QuietCheckLmpSurvival | 11 | 9 | 3: WAC.080, WAC.089, WAC.169 | 6 | 4 | 377,688 / 423,660 | -0.21 |
| ImprovingRazorGuard | 8 | 7 | 5: WAC.087, WAC.092, WAC.261, WAC.262, WAC.270 | 2 | 4 | 458,060 / 423,660 | +0.12 |
| SingularSiblingLmr | 14 | 6 | 8: WAC.046, WAC.082, WAC.119, WAC.191, WAC.194, WAC.236, WAC.238, WAC.264 | 4 | 3 | 460,277 / 423,660 | +0.01 |
| CaptureHistoryLmp | 15 | 2 | 6: WAC.231, WAC.239, WAC.250, WAC.282, WAC.288, WAC.289 | 6 | 2 | 366,391 / 423,660 | -0.69 |

### QuietCheckLmpSurvival: 11 lost, 9 gained; key move of the lost ones: capture 3, capture+check 1, quiet 7

| id | change | bm/am | key move | OFF move (depth, score) | ON move (depth, score) |
|---|---|---|---|---|---|
| WAC.071 | lost | bm b5a7 | capture+check | b5a7 (d18, 620) | h3b3 (d8, -15) |
| WAC.080 | lost | bm d1a1 | quiet | d1a1 (d18, 639) | d4d5 (d13, 99) |
| WAC.081 | lost | bm e7d6 | quiet | e7d6 (d17, 117) | b7e4 (d13, 85) |
| WAC.089 | lost | bm g7g5 | quiet | g7g5 (d15, 1338) | d4d3 (d13, 731) |
| WAC.169 | lost | bm g7h6 | quiet | g7h6 (d18, 799) | f8f7 (d15, -24) |
| WAC.193 | lost | bm b3e3 | capture | b3e3 (d16, 2605) | b3d5 (d15, 385) |
| WAC.218 | lost | bm g5h6 | quiet | g5h6 (d16, 2590) | g4f3 (d15, 949) |
| WAC.229 | lost | bm h5h4 b5b4 | capture | b5b4 (d20, 921) | h5h8 (d18, 181) |
| WAC.232 | lost | bm a6b5 b8e8 | quiet | b8e8 (d18, 492) | a6a7 (d18, 174) |
| WAC.243 | lost | bm f2e2 | quiet | f2e2 (d19, 320) | f2g2 (d15, 293) |
| WAC.297 | lost | bm c6g2 d6h2 | capture | c6g2 (d15, 464) | e7g5 (d14, 0) |
| WAC.033 | gained | bm e4e5 e4f4 | check | a4a5 (d13, 318) | e4e5 (d11, 315) |
| WAC.101 | gained | bm d4c3 | quiet | a7a5 (d15, 101) | d4c3 (d16, 278) |
| WAC.165 | gained | bm e3e2 | quiet | d2f2 (d15, -200) | e3e2 (d14, 577) |
| WAC.190 | gained | bm d7h3 | quiet | d1f2 (d15, 168) | d7h3 (d18, 1425) |
| WAC.196 | gained | bm c6b4 | quiet | b8b6 (d14, -28) | c6b4 (d13, -39) |
| WAC.205 | gained | bm d2g5 | capture | e2d3 (d6, 177) | d2g5 (d15, 852) |
| WAC.226 | gained | bm e5f7 | quiet | d1d8 (d13, 493) | e5f7 (d17, 798) |
| WAC.245 | gained | bm d3g6 | capture+check | c3b5 (d16, 291) | d3g6 (d16, 1358) |
| WAC.265 | gained | bm e5f6 | capture | c2e4 (d16, 42) | e5f6 (d15, 271) |

### ImprovingRazorGuard: 8 lost, 7 gained; key move of the lost ones: capture 2, capture+check 1, quiet 5

| id | change | bm/am | key move | OFF move (depth, score) | ON move (depth, score) |
|---|---|---|---|---|---|
| WAC.071 | lost | bm b5a7 | capture+check | b5a7 (d18, 620) | h3b3 (d12, -57) |
| WAC.087 | lost | bm e6e5 | capture | e6e5 (d16, 1163) | c5b4 (d15, 251) |
| WAC.092 | lost | bm e6g4 | capture | e6g4 (d14, 133) | a8c8 (d11, 13) |
| WAC.181 | lost | bm f6g4 | quiet | f6g4 (d16, 995) | h3f1 (d16, 41) |
| WAC.243 | lost | bm f2e2 | quiet | f2e2 (d19, 320) | f2g2 (d18, 327) |
| WAC.261 | lost | bm f3d4 | quiet | f3d4 (d16, 1808) | a8e8 (d13, 255) |
| WAC.262 | lost | bm g6h6 | quiet | g6h6 (d14, 213) | e7g5 (d11, -197) |
| WAC.270 | lost | bm d4g4 | quiet | d4g4 (d18, 142) | e2e8 (d14, 82) |
| WAC.021 | gained | bm d2h6 | quiet | d2c3 (d14, 182) | d2h6 (d17, 934) |
| WAC.033 | gained | bm e4e5 e4f4 | check | a4a5 (d13, 318) | e4e5 (d15, 944) |
| WAC.049 | gained | bm h5h7 | capture+check | h5h6 (d14, 143) | h5h7 (d23, M6) |
| WAC.101 | gained | bm d4c3 | quiet | a7a5 (d15, 101) | d4c3 (d15, 271) |
| WAC.165 | gained | bm e3e2 | quiet | d2f2 (d15, -200) | e3e2 (d15, 633) |
| WAC.190 | gained | bm d7h3 | quiet | d1f2 (d15, 168) | d7h3 (d20, 1605) |
| WAC.296 | gained | bm d8d4 d8f8 | check | d8d6 (d13, 426) | d8f8 (d16, 728) |

### SingularSiblingLmr: 14 lost, 6 gained; key move of the lost ones: capture 6, check 2, quiet 6

| id | change | bm/am | key move | OFF move (depth, score) | ON move (depth, score) |
|---|---|---|---|---|---|
| WAC.046 | lost | bm c3b5 | quiet | c3b5 (d16, 205) | f1e2 (d15, 32) |
| WAC.081 | lost | bm e7d6 | quiet | e7d6 (d17, 117) | b7e4 (d16, 78) |
| WAC.082 | lost | bm e4h7 | check | e4h7 (d17, 1429) | f1f4 (d14, 0) |
| WAC.119 | lost | bm d8d3 | capture | d8d3 (d17, 743) | d8d4 (d10, 138) |
| WAC.180 | lost | bm f6d5 | capture | f6d5 (d14, 96) | a7a5 (d9, 85) |
| WAC.191 | lost | bm e2c4 | quiet | e2c4 (d64, M3) | e8c8 (d10, 305) |
| WAC.193 | lost | bm b3e3 | capture | b3e3 (d16, 2605) | b3d5 (d13, 415) |
| WAC.194 | lost | bm f5h6 | check | f5h6 (d17, 976) | g3a3 (d12, 52) |
| WAC.218 | lost | bm g5h6 | quiet | g5h6 (d16, 2590) | g4f3 (d16, 992) |
| WAC.229 | lost | bm h5h4 b5b4 | capture | b5b4 (d20, 921) | h5h7 (d21, 189) |
| WAC.236 | lost | bm c3c1 | quiet | c3c1 (d16, 160) | g3e1 (d12, 111) |
| WAC.238 | lost | bm g2b7 | capture | g2b7 (d18, 923) | c5b5 (d9, 128) |
| WAC.264 | lost | bm e7e5 a8b8 | quiet | a8b8 (d15, 417) | e7f6 (d13, 265) |
| WAC.297 | lost | bm c6g2 d6h2 | capture | c6g2 (d15, 464) | e7g5 (d15, -5) |
| WAC.021 | gained | bm d2h6 | quiet | d2c3 (d14, 182) | d2h6 (d18, 1238) |
| WAC.033 | gained | bm e4e5 e4f4 | check | a4a5 (d13, 318) | e4e5 (d14, 855) |
| WAC.101 | gained | bm d4c3 | quiet | a7a5 (d15, 101) | d4c3 (d15, 306) |
| WAC.165 | gained | bm e3e2 | quiet | d2f2 (d15, -200) | e3e2 (d16, 613) |
| WAC.196 | gained | bm c6b4 | quiet | b8b6 (d14, -28) | c6b4 (d12, -77) |
| WAC.256 | gained | bm d4f5 | quiet | g2g3 (d14, 12) | d4f5 (d15, 713) |

### CaptureHistoryLmp: 15 lost, 2 gained; key move of the lost ones: capture 4, capture+check 1, check 4, quiet 6

| id | change | bm/am | key move | OFF move (depth, score) | ON move (depth, score) |
|---|---|---|---|---|---|
| WAC.071 | lost | bm b5a7 | capture+check | b5a7 (d18, 620) | h3d3 (d14, -57) |
| WAC.081 | lost | bm e7d6 | quiet | e7d6 (d17, 117) | b7e4 (d13, 14) |
| WAC.180 | lost | bm f6d5 | capture | f6d5 (d14, 96) | c8d7 (d13, 75) |
| WAC.181 | lost | bm f6g4 | quiet | f6g4 (d16, 995) | h3f1 (d14, 51) |
| WAC.193 | lost | bm b3e3 | capture | b3e3 (d16, 2605) | b3d5 (d15, 393) |
| WAC.229 | lost | bm h5h4 b5b4 | capture | b5b4 (d20, 921) | e4e5 (d21, 170) |
| WAC.231 | lost | bm c1g5 | quiet | c1g5 (d19, 77) | f5d7 (d4, 388) |
| WAC.232 | lost | bm a6b5 b8e8 | quiet | b8e8 (d18, 492) | a6a7 (d15, 217) |
| WAC.239 | lost | bm f2f1 | check | f2f1 (d19, 2370) | f2e2 (d11, 0) |
| WAC.243 | lost | bm f2e2 | quiet | f2e2 (d19, 320) | b4b5 (d14, 314) |
| WAC.250 | lost | bm e3e8 | check | e3e8 (d19, M8) | e3e1 (d9, 80) |
| WAC.282 | lost | bm h1h8 | check | h1h8 (d64, M4) | h1e1 (d13, -337) |
| WAC.288 | lost | bm h5f6 | check | h5f6 (d17, 544) | h5g3 (d8, -117) |
| WAC.289 | lost | bm e6e5 | quiet | e6e5 (d17, 774) | e6h3 (d13, 0) |
| WAC.297 | lost | bm c6g2 d6h2 | capture | c6g2 (d15, 464) | e7g5 (d12, 0) |
| WAC.033 | gained | bm e4e5 e4f4 | check | a4a5 (d13, 318) | e4e5 (d15, 907) |
| WAC.190 | gained | bm d7h3 | quiet | d1f2 (d15, 168) | d7h3 (d18, 1220) |
