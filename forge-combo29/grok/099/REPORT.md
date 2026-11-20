# REPORT seat 099

IdeaK10 gives a quiet hash move one more ply when the remaining depth is at least 8 and the sum of the two continuation-history tables behind the node is at least 12000.
The check `IdeaK10` defaults to false. The spins are `IdeaK10_MinDepth` (default 8) and `IdeaK10_Threshold` (default 12000), and they are read only when the check is true.
The extra ply is applied after the double-extension counter. With the check false the extension value is left as it was, so `new_depth` matches the plain engine.

EXISTS: no. In `forge-combo29/src/search.cpp` the extension block only does a singular extension and a SEE-non-losing check extension. Continuation history is read for quiet ordering and late-move reduction, not to add a ply.

Honesty, a fresh process per line, no setoption. Exe B and the final exe P both printed bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Raw files: `HONESTY_B.txt`, `P12000_HONESTY.txt`.

`git apply --check` of `idea.patch.txt` on a fresh copy of `6b98f2170` exited 0 (`apply_check.txt`).

The tables below are the full output of `report_tables.py`.

----- step table -----
step	status	evidence	result
1 seat	done	SEAT.txt stamps.txt	seat 099, idea 49, model Grok 4.7, 2026-11-20T07:55:29Z, token 57972632320751
2 builds and baseline	done	HONESTY_B.txt B_sums.txt	file	positions	sum	first3 | forge-combo29/grok/099/B_O_d12.rows.txt	200	9500069	41311/24872/28574 | forge-combo29/grok/099/B_G_d12.rows.txt	353	18466239	37203/70845/144383 |
3 idea	done	idea.patch.txt compare_on_O.txt match_result.txt san_G100_d10.san.txt	off differ 0; on differ 198; Elo: -6.60 +/- 9.55, nElo: -14.16 +/- 20.48; Games: 1106, Wins: 320, Losses: 341, Draws: 445, Points: 542.5 (49.05 %)
4 partner 049	done	partner_compare_on.txt partner_match_result.txt	CONFIRMS; differ 0; Elo: -9.85 +/- 10.29, nElo: -26.62 +/- 27.80; Games: 600, Wins: 256, Losses: 273, Draws: 71, Points: 291.5 (48.58 %)
5 report	done	REPORT.md RESULT.txt	this file

----- B_sums.txt -----
file	positions	sum	first3
forge-combo29/grok/099/B_O_d12.rows.txt	200	9500069	41311/24872/28574
forge-combo29/grok/099/B_G_d12.rows.txt	353	18466239	37203/70845/144383

----- P_sums.txt -----
file	positions	sum	first3
forge-combo29/grok/099/P_on_O_d12.rows.txt	200	16294055	80821/53410/29950
forge-combo29/grok/099/P_off_O_d12.rows.txt	200	9500069	41311/24872/28574
forge-combo29/grok/099/P_off_G_d12.rows.txt	353	18466239	37203/70845/144383

----- compare_off_O.txt -----
left forge-combo29/grok/099/B_O_d12.rows.txt n=200
right forge-combo29/grok/099/P_off_O_d12.rows.txt n=200
compared 200
equal 200
differ 0

----- compare_off_G.txt -----
left forge-combo29/grok/099/B_G_d12.rows.txt n=353
right forge-combo29/grok/099/P_off_G_d12.rows.txt n=353
compared 353
equal 353
differ 0

----- compare_on_O.txt -----
left forge-combo29/grok/099/B_O_d12.rows.txt n=200
right forge-combo29/grok/099/P_on_O_d12.rows.txt n=200
compared 200
equal 2
differ 198
pos 0 left 41311 f1e2 right 80821 f1e2
pos 1 left 24872 f1c4 right 53410 f1c4
pos 2 left 28574 e5d4 right 29950 e5d4
pos 3 left 27838 e1g1 right 45810 e1g1
pos 4 left 18020 c8e6 right 43177 c8e6
pos 5 left 43043 g1f3 right 31420 g1f3
pos 6 left 56414 d2d4 right 117246 d2d4
pos 7 left 32317 g1f3 right 39067 g1f3
pos 8 left 37995 f1d3 right 41056 f1d3
pos 9 left 53959 c5b4 right 98104 c5b6
pos 10 left 26257 d5e6 right 127732 d5e6
pos 11 left 58746 h2h3 right 160763 h2h3

----- match_result.txt -----
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -6.60 +/- 9.55, nElo: -14.16 +/- 20.48
LOS: 8.77 %, DrawRatio: 66.18 %, PairsRatio: 0.82
Games: 1106, Wins: 320, Losses: 341, Draws: 445, Points: 542.5 (49.05 %)
Ptnml(0-2): [10, 93, 366, 76, 8], WL/DD Ratio: 1.65
--------------------------------------------------
Finished match
result_headers 56
started_games 1106

----- partner_compare_off.txt -----
left forge-combo29/grok/099/B_O_d12.rows.txt n=200 sum=9500069
right forge-combo29/grok/099/partner_off_O.rows.txt n=200 sum=9500069
compared 200
equal 200
differ 0

----- partner_compare_on.txt -----
left forge-combo29/grok/099/partner_049_o_on.nodes n=200 sum=31066517
right forge-combo29/grok/099/partner_on_O.rows.txt n=200 sum=31066517
compared 200
equal 200
differ 0

----- partner_compare_off_G.txt -----
left forge-combo29/grok/099/B_G_d12.rows.txt n=353 sum=18466239
right forge-combo29/grok/099/partner_off_G.rows.txt n=353 sum=18466239
compared 353
equal 353
differ 0

----- partner_match_result.txt -----
Results of on vs off (20000 nodes, 1t, 16MB, R.epd):
Elo: -9.85 +/- 10.29, nElo: -26.62 +/- 27.80
LOS: 3.03 %, DrawRatio: 81.33 %, PairsRatio: 0.65
Games: 600, Wins: 256, Losses: 273, Draws: 71, Points: 291.5 (48.58 %)
Ptnml(0-2): [7, 27, 244, 20, 2], WL/DD Ratio: 19.33
--------------------------------------------------
Finished match
result_headers 31
started_games 600

----- partner_apply_check.txt -----
APPLY_CHECK_OK

----- equal positions B_O_d12.rows.txt vs P_on_O_d12.rows.txt -----
n 200 equal 2 indices [30, 129]

----- san_G100 meta lines -----
exe: /tmp/forge-asan/forge
nm -C | grep -c __asan_: 35
sanitizer lines: 0
----- scratch sanitizer lines -----
/tmp/applybase/forge-combo29/src/uci.cpp:48:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
==5923==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000d0 at pc 0x561ede028fd7 bp 0x7fff5b0e1730 sp 0x7fff5b0e1720
SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/applybase/forge-combo29/src/uci.cpp:48 in apply_position
----- uci options -----
option name IdeaK10 type check default false
option name IdeaK10_MinDepth type spin default 8 min 1 max 64
option name IdeaK10_Threshold type spin default 12000 min -32768 max 32767


## Proofs

(1) Honesty with no setoption, final exe P: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. `P12000_HONESTY.txt`.

(2) S14, Threads 1, Hash 16, IdeaK10 false. O depth 12: 200 positions equal to exe B, sum 9500069. G depth 12: 353 positions equal to exe B, sum 18466239. `compare_off_O.txt`, `compare_off_G.txt`.

(3) S14 and IdeaK10 true, MinDepth 8, Threshold 12000. O depth 12 sum 16294055. 198 of 200 positions differ from exe B. The two that match are indices 30 and 129. `compare_on_O.txt`. An earlier default of 3000 changed all 200 and summed to 64848074 (`P_on_O_d12_t3000.rows.txt`); that default chained because a +1 extension keeps depth from falling. 12000 is the shipped default. The prediction file still says 10100000 with a wrong-band of 9200000 to 12500000. 16294055 is outside that band, so the node prediction is wrong. It was not edited.

(4) `uci` lists `IdeaK10` check default false, `IdeaK10_MinDepth` spin default 8, `IdeaK10_Threshold` spin default 12000. `P_uci.txt`.

(5) AddressSanitizer + UndefinedBehaviorSanitizer build, switch true, Threshold 12000, first 100 of G at depth 10: 0 sanitizer lines. `nm -C` count of `__asan_` is 35. The same runner on a scratch copy that reads `heap[8]` of a 4-int array when the FEN is `8/8/8/8/8/8/8/K6k w - - 13 40` printed `ERROR: AddressSanitizer: heap-buffer-overflow`. `san_G100_d10.raw.txt.meta`, `san_scratch.san.txt`.

## Match

Exe P with the switch true against exe P with the switch false. S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours, 1106 games. fastchess concurrency 3.

Elo: -6.60 +/- 9.55. Wins 320, losses 341, draws 445. `match.txt`, `match.pgn`, `match_result.txt`.

The Elo prediction was +5, wrong if the point is below -25 or above +40. -6.60 is inside that band. The whole interval is not below 0, and the point is not below -20, so the match did not trigger the one look for a mistake. The look that changed the threshold happened earlier, when the 3000 run failed to keep depth decreasing.

## Partner

Partner is seat 049 (same idea, the next seat after 099 that has a branch; 149 does not exist). Verdict: CONFIRMS.

Their patch applies to a fresh base (`partner_apply_check.txt`). Honesty numbers match. Switch false: O 200 equal to exe B, G 353 equal to exe B. Switch true: all 200 O depth-12 node counts equal their `o_p_on_d12.nodes`, sum 31066517. A match of their switch on my 300 R openings, both colours, 600 games: Elo -9.85 +/- 10.29. That match is mine; they did not claim an R result. `partner_compare_off.txt`, `partner_compare_on.txt`, `partner_compare_off_G.txt`, `partner_match_result.txt`.

## suspicions, not proven

A +1 extension on a quiet hash move makes `new_depth = depth` whenever it hits and no other extension is negative. At threshold 3000 that chained and the depth-12 sum was about 6.8 times the baseline. Threshold 12000 still changes 198 positions and about 1.7 times the nodes. I did not prove that 12000 is the right bar on the owner's net. The match interval includes both a small loss and a small gain.

## what I did NOT do

I did not replay seat 049's 1106-game OG match. I did not finish the sanitizer run at threshold 3000; that run was stopped by a 300-second timeout on one position and is filed as `san_G100_d10_t3000_partial`. I did not try a cap on how many times the extra ply may stack. I did not open a pull request. At minute 60 the handoff branch had no `FABLE_TO_grok_<N>.md`.

## what I am NOT sure about

I am not sure why positions 30 and 129 kept the same node count with the switch on. I am not sure the -6.60 Elo will keep its sign on the owner's net. I am not sure seat 049's different rule (they refuse the extra ply when the extension is already positive, and their threshold is 3072) is better or worse than mine beyond the node counts I reproduced.

times: see stamps.txt


## git status --short

```
AM forge-combo29/grok/099/REPORT.md
A  forge-combo29/grok/099/RESULT.txt
A  forge-combo29/grok/099/apply_check.txt
A  forge-combo29/grok/099/compare_node_col.py
A  forge-combo29/grok/099/partner_049_idea.patch.txt
A  forge-combo29/grok/099/partner_049_o_on.nodes
A  forge-combo29/grok/099/partner_apply_check.txt
A  forge-combo29/grok/099/partner_compare_off.txt
A  forge-combo29/grok/099/partner_compare_off_G.txt
A  forge-combo29/grok/099/partner_compare_on.txt
A  forge-combo29/grok/099/partner_h_HONESTY.txt
A  forge-combo29/grok/099/partner_h_bench11.txt
A  forge-combo29/grok/099/partner_h_bench11.txt.meta
A  forge-combo29/grok/099/partner_h_bench13.txt
A  forge-combo29/grok/099/partner_h_bench13.txt.meta
A  forge-combo29/grok/099/partner_h_bench16.txt
A  forge-combo29/grok/099/partner_h_bench16.txt.meta
A  forge-combo29/grok/099/partner_h_perft5.txt
A  forge-combo29/grok/099/partner_h_perft5.txt.meta
A  forge-combo29/grok/099/partner_match.pgn
A  forge-combo29/grok/099/partner_match.sh
A  forge-combo29/grok/099/partner_match.txt
A  forge-combo29/grok/099/partner_match_result.txt
A  forge-combo29/grok/099/partner_off_G.raw.txt
A  forge-combo29/grok/099/partner_off_G.raw.txt.meta
A  forge-combo29/grok/099/partner_off_G.rows.txt
A  forge-combo29/grok/099/partner_off_O.raw.txt
A  forge-combo29/grok/099/partner_off_O.raw.txt.meta
A  forge-combo29/grok/099/partner_off_O.rows.txt
A  forge-combo29/grok/099/partner_on_O.raw.txt
A  forge-combo29/grok/099/partner_on_O.raw.txt.meta
A  forge-combo29/grok/099/partner_on_O.rows.txt
A  forge-combo29/grok/099/report_tables.py
A  forge-combo29/grok/099/report_tables.txt
M  forge-combo29/grok/099/stamps.txt
?? config.json
```

## ls -la

```
total 9652
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:17 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  548359 Nov 20 08:01 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     776 Nov 20 08:01 B_G_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 08:01 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   10301 Nov 20 08:01 B_O_d12_probe.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     776 Nov 20 08:01 B_O_d12_probe.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:01 B_O_d12_probe.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308094 Nov 20 08:01 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     776 Nov 20 08:01 B_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:01 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:02 B_sums.txt
-rw-r--r-- 1 ubuntu ubuntu    1047 Nov 20 09:17 compare_node_col.py
-rw-r--r-- 1 ubuntu ubuntu     139 Nov 20 08:19 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     139 Nov 20 08:19 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     621 Nov 20 08:06 compare_on_O_t3000.txt
-rw-r--r-- 1 ubuntu ubuntu     611 Nov 20 08:19 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     942 Nov 20 08:04 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    2119 Nov 20 08:18 design.txt
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:01 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:01 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:01 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:01 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    2649 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu   20397 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2571 Nov 20 08:04 honesty_exe.py
-rw-r--r-- 1 ubuntu ubuntu    5922 Nov 20 08:18 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1757 Nov 20 08:21 make_r.py
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:26 match.nohup
-rw-r--r-- 1 ubuntu ubuntu 3594985 Nov 20 08:26 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     376 Nov 20 08:28 match_result.txt
-rwxr-xr-x 1 ubuntu ubuntu    1326 Nov 20 08:20 match.sh
-rw-r--r-- 1 ubuntu ubuntu  124815 Nov 20 08:26 match.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:21 openings
-rw-r--r-- 1 ubuntu ubuntu    5176 Nov 20 08:18 P12000_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:18 P12000_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5176 Nov 20 08:18 P12000_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:18 P12000_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5178 Nov 20 08:18 P12000_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:18 P12000_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   21125 Nov 20 08:18 P12000_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    5389 Nov 20 08:18 P12000_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:18 P12000_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     648 Nov 20 08:28 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    5127 Nov 20 09:12 partner_049_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    2050 Nov 20 09:12 partner_049_o_on.nodes
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:12 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     167 Nov 20 09:17 partner_compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 09:17 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:17 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 09:12 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_h_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 09:12 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_h_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5172 Nov 20 09:12 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_h_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   21101 Nov 20 09:12 partner_h_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    5383 Nov 20 09:12 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:12 partner_h_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 1604877 Nov 20 09:16 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     373 Nov 20 09:16 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1276 Nov 20 09:13 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   63787 Nov 20 09:16 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu  548222 Nov 20 09:16 partner_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     813 Nov 20 09:16 partner_off_G.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 09:16 partner_off_G.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308022 Nov 20 09:12 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     813 Nov 20 09:12 partner_off_O.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 09:12 partner_off_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  316924 Nov 20 09:12 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 09:12 partner_on_O.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15888 Nov 20 09:12 partner_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    5175 Nov 20 08:05 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:05 P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5175 Nov 20 08:05 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:05 P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5177 Nov 20 08:05 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:05 P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   21121 Nov 20 08:05 P_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu  548236 Nov 20 08:18 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     811 Nov 20 08:18 P_off_G_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 08:18 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308193 Nov 20 08:18 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     811 Nov 20 08:18 P_off_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:18 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  311503 Nov 20 08:18 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 08:18 P_on_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15797 Nov 20 08:18 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  322160 Nov 20 08:06 P_on_O_d12_t3000.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 08:06 P_on_O_d12_t3000.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15939 Nov 20 08:06 P_on_O_d12_t3000.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:06 P_on_O_sum_t3000.txt
-rw-r--r-- 1 ubuntu ubuntu    5388 Nov 20 08:05 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:05 P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     821 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 08:19 P_sums.txt
-rw-r--r-- 1 ubuntu ubuntu    5115 Nov 20 08:18 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:18 P_uci.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   11394 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3296 Nov 20 09:18 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu    4640 Nov 20 09:18 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    6390 Nov 20 08:01 run_depth.py
-rw-r--r-- 1 ubuntu ubuntu    7323 Nov 20 08:07 san_depth.py
-rw-r--r-- 1 ubuntu ubuntu  131912 Nov 20 08:19 san_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     945 Nov 20 08:19 san_G100_d10.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    6398 Nov 20 08:19 san_G100_d10.rows.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 san_G100_d10.san.txt
-rw-r--r-- 1 ubuntu ubuntu   31981 Nov 20 08:17 san_G100_d10_t3000_partial.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     944 Nov 20 08:17 san_G100_d10_t3000_partial.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:17 san_G100_d10_t3000_partial.san.txt
-rw-r--r-- 1 ubuntu ubuntu    9626 Nov 20 08:08 san_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 08:08 san_scratch.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     393 Nov 20 08:08 san_scratch.san.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:08 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     710 Nov 20 08:02 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1213 Nov 20 08:04 uci_dump.py
```
