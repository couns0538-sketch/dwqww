| gate | games | book (format, order, start) | TC / margin | threads / hash / conc | adjudication in config | endings (log) | plies mean / median / p90 / max | engine s per game |
|---|---|---|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | 1500 | 8moves_v3.pgn (fmt 1, order 0, start 495001) | 10+0.1 / 1000 ms | 2 / 16 / 4 | none | {'3-fold': 962, 'mate': 341, 'fifty': 103, 'insufficient': 92, 'stalemate': 2} | 140.7 / 127.0 / 230 / 640 | 28.5 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | 6000 | UHO_Lichess_4852_v1.epd (fmt 0, order 0, start 1132001) | 10+0.1 / 1000 ms | 2 / 16 / 4 | none | {'mate': 2598, '3-fold': 2434, 'insufficient': 412, 'fifty': 544, 'stalemate': 12} | 154.6 / 146.0 / 238 / 748 | 32.8 |
| gate_stB_lmrttcapall1_vs_AL1 | 3000 | 8moves_v3.pgn (fmt 1, order 0, start 516001) | 10+0.1 / 1000 ms | 2 / 16 / 4 | none | {'3-fold': 1881, 'fifty': 200, 'insufficient': 231, 'mate': 678, 'stalemate': 10} | 142.6 / 129.0 / 231 / 769 | 28.8 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | 2529 | UHO_Lichess_4852_v1.epd (fmt 0, order 0, start 1219001) | 10+0.1 / 1000 ms | 2 / 16 / 4 | none | {'3-fold': 989, 'mate': 1142, 'fifty': 227, 'insufficient': 166, 'stalemate': 5} | 158.7 / 148 / 247 / 850 | 33.2 |
| gateR5A_1_corrhistplus4_vs_r5aoff | 3000 | 8moves_v3.pgn (fmt 1, order 0, start 387001) | 10+0.1 / 1000 ms | 1 / 16 / 8 | none | {'3-fold': 1871, 'insufficient': 203, 'mate': 734, 'fifty': 184, 'stalemate': 8} | 141.6 / 131.0 / 231 / 553 | 28.6 |

| gate | rule set | games ended early | plies saved (share) | engine s saved (share) | disagreements (adjudicated result != played) |
|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | draw34/8/20 | 953 (63.5 %) {'draw': 953} | 28062 (13.3 %) | 4100.8 (9.6 %) | 12 |
| gate_sf26bundle14_vs_AL1 | draw34/8/10 | 926 (61.7 %) {'draw': 926} | 20451 (9.7 %) | 3044.9 (7.1 %) | 7 |
| gate_sf26bundle14_vs_AL1 | draw40/16/5 | 560 (37.3 %) {'draw': 560} | 7645 (3.6 %) | 1116.9 (2.6 %) | 0 |
| gate_sf26bundle14_vs_AL1 | resign3/600 | 343 (22.9 %) {'resign': 343} | 15033 (7.1 %) | 1624.6 (3.8 %) | 2 |
| gate_sf26bundle14_vs_AL1 | resign3/600two | 343 (22.9 %) {'resign': 343} | 14761 (7.0 %) | 1587.2 (3.7 %) | 2 |
| gate_sf26bundle14_vs_AL1 | resign5/1000two | 339 (22.6 %) {'resign': 339} | 8139 (3.9 %) | 684.9 (1.6 %) | 0 |
| gate_sf26bundle14_vs_AL1 | fishtest-like (resign3/600two + draw34/8/20) | 1282 (85.5 %) {'draw': 951, 'resign': 331} | 42343 (20.1 %) | 5645.4 (13.2 %) | 14 |
| gate_sf26bundle14_vs_AL1 | maxmoves200 | 14 (0.9 %) {'maxmoves': 14} | 1413 (0.7 %) | 144.3 (0.3 %) | 1 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | draw34/8/20 | 3167 (52.8 %) {'draw': 3167} | 84413 (9.1 %) | 11144.5 (5.7 %) | 52 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | draw34/8/10 | 3087 (51.4 %) {'draw': 3087} | 63284 (6.8 %) | 8420.1 (4.3 %) | 35 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | draw40/16/5 | 1742 (29.0 %) {'draw': 1742} | 22534 (2.4 %) | 3018.4 (1.5 %) | 4 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | resign3/600 | 2599 (43.3 %) {'resign': 2599} | 109701 (11.8 %) | 11980.5 (6.1 %) | 1 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | resign3/600two | 2598 (43.3 %) {'resign': 2598} | 105558 (11.4 %) | 11398.0 (5.8 %) | 0 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | resign5/1000two | 2589 (43.1 %) {'resign': 2589} | 60717 (6.5 %) | 5128.6 (2.6 %) | 0 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | fishtest-like (resign3/600two + draw34/8/20) | 5713 (95.2 %) {'resign': 2546, 'draw': 3167} | 187973 (20.3 %) | 22350.8 (11.4 %) | 52 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | maxmoves200 | 53 (0.9 %) {'maxmoves': 53} | 4088 (0.4 %) | 413.7 (0.2 %) | 1 |
| gate_stB_lmrttcapall1_vs_AL1 | draw34/8/20 | 1984 (66.1 %) {'draw': 1984} | 62570 (14.6 %) | 9113.9 (10.5 %) | 32 |
| gate_stB_lmrttcapall1_vs_AL1 | draw34/8/10 | 1927 (64.2 %) {'draw': 1927} | 45845 (10.7 %) | 6769.1 (7.8 %) | 20 |
| gate_stB_lmrttcapall1_vs_AL1 | draw40/16/5 | 1140 (38.0 %) {'draw': 1140} | 16197 (3.8 %) | 2335.2 (2.7 %) | 4 |
| gate_stB_lmrttcapall1_vs_AL1 | resign3/600 | 679 (22.6 %) {'resign': 679} | 29377 (6.9 %) | 3197.5 (3.7 %) | 1 |
| gate_stB_lmrttcapall1_vs_AL1 | resign3/600two | 679 (22.6 %) {'resign': 679} | 28719 (6.7 %) | 3102.7 (3.6 %) | 1 |
| gate_stB_lmrttcapall1_vs_AL1 | resign5/1000two | 677 (22.6 %) {'resign': 677} | 16773 (3.9 %) | 1435.6 (1.7 %) | 0 |
| gate_stB_lmrttcapall1_vs_AL1 | fishtest-like (resign3/600two + draw34/8/20) | 2630 (87.7 %) {'draw': 1983, 'resign': 647} | 90169 (21.1 %) | 12113.0 (14.0 %) | 33 |
| gate_stB_lmrttcapall1_vs_AL1 | maxmoves200 | 26 (0.9 %) {'maxmoves': 26} | 2347 (0.5 %) | 238.8 (0.3 %) | 3 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | draw34/8/20 | 1286 (50.9 %) {'draw': 1286} | 34494 (8.6 %) | 4486.3 (5.3 %) | 22 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | draw34/8/10 | 1255 (49.6 %) {'draw': 1255} | 25391 (6.3 %) | 3342.8 (4.0 %) | 13 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | draw40/16/5 | 710 (28.1 %) {'draw': 710} | 8947 (2.2 %) | 1178.0 (1.4 %) | 1 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | resign3/600 | 1148 (45.4 %) {'resign': 1148} | 52793 (13.2 %) | 5853.7 (7.0 %) | 6 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | resign3/600two | 1145 (45.3 %) {'resign': 1145} | 50392 (12.6 %) | 5554.7 (6.6 %) | 3 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | resign5/1000two | 1139 (45.0 %) {'resign': 1139} | 28211 (7.0 %) | 2453.0 (2.9 %) | 0 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | fishtest-like (resign3/600two + draw34/8/20) | 2406 (95.1 %) {'draw': 1283, 'resign': 1123} | 83961 (20.9 %) | 9957.1 (11.9 %) | 25 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | maxmoves200 | 37 (1.5 %) {'maxmoves': 37} | 3230 (0.8 %) | 328.2 (0.4 %) | 1 |
| gateR5A_1_corrhistplus4_vs_r5aoff | draw34/8/20 | 1928 (64.3 %) {'draw': 1928} | 56597 (13.3 %) | 8156.4 (9.5 %) | 38 |
| gateR5A_1_corrhistplus4_vs_r5aoff | draw34/8/10 | 1861 (62.0 %) {'draw': 1861} | 41022 (9.7 %) | 5959.4 (7.0 %) | 24 |
| gateR5A_1_corrhistplus4_vs_r5aoff | draw40/16/5 | 1098 (36.6 %) {'draw': 1098} | 12892 (3.0 %) | 1852.6 (2.2 %) | 3 |
| gateR5A_1_corrhistplus4_vs_r5aoff | resign3/600 | 738 (24.6 %) {'resign': 738} | 31463 (7.4 %) | 3464.7 (4.0 %) | 4 |
| gateR5A_1_corrhistplus4_vs_r5aoff | resign3/600two | 738 (24.6 %) {'resign': 738} | 30571 (7.2 %) | 3340.5 (3.9 %) | 4 |
| gateR5A_1_corrhistplus4_vs_r5aoff | resign5/1000two | 726 (24.2 %) {'resign': 726} | 16796 (4.0 %) | 1474.1 (1.7 %) | 0 |
| gateR5A_1_corrhistplus4_vs_r5aoff | fishtest-like (resign3/600two + draw34/8/20) | 2624 (87.5 %) {'draw': 1925, 'resign': 699} | 85492 (20.1 %) | 11334.6 (13.2 %) | 41 |
| gateR5A_1_corrhistplus4_vs_r5aoff | maxmoves200 | 16 (0.5 %) {'maxmoves': 16} | 929 (0.2 %) | 94.1 (0.1 %) | 0 |
