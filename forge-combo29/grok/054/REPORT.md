Idea S35 searches the first replies to a late parent move with less reduction.
The plain engine already does one ply of that when LmrLateParentRelief is on, for a parent arrival index of at least 7 and one of the first four replies.
I left that switch as it is (check, default false) and made the two fixed numbers into spin options IdeaS35_Index default 7 and IdeaS35_Replies default 4, so the defaults reproduce today's path.

EXISTS: forge-combo29/src/search.cpp:2010

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

The table and the proof numbers below are the pasted output of report_table.py, which reads the raw files.

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt | seat 054 idea 4
STEP 2 honesty B | done | HONESTY_B.txt | bench 11/13/16 and perft 5 match
STEP 2 O and G | done | B_O_d12.meta B_G_d12.meta | O 9500069 G 18466239
3a read | done | decision.txt | EXISTS search.cpp:2010
3b prediction | done | prediction.txt | 10200000 and Elo +5, committed before measuring
3c patch | done | idea.patch.txt apply_check.txt | git apply --check ok
3d (1) honesty P | done | HONESTY_P.txt | same four node counts, no setoption
3d (2) switch off | done | cmp_off_O.txt cmp_off_G.txt | 0 of 200 and 0 of 353
3d (3) switch on | done | cmp_on_O.txt | 200 of 200 differ, sum 9722581
3d (4) uci | done | HONESTY_P_uci.txt | IdeaS35_Index 7, IdeaS35_Replies 4
3d (5) sanitizer | done | asan_G100.meta asan_scratch_lines.txt | nm __asan_ 35, clean, trap reports
3e match | done | match_result.txt match_on_off.pgn | 1106 games, Elo -0.00 +/- 10.81
STEP 4 partner 104 | done | partner104_cmp_off_O.txt partner104_cmp_on_O.txt partner104_match_result.txt | CONFIRMS

--- HONESTY_B ---
label HONESTY_B
exe /agent/repos/base/forge-combo29/build/forge
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench11 nodes 312866 expected 312866 exit 0 OK
bench13 nodes 862329 expected 862329 exit 0 OK
bench16 nodes 3024920 expected 3024920 exit 0 OK
perft5 nodes 4865609 expected 4865609 exit 0 OK
id name Chess Engine Forge 6.4.24 candidate
uci_exit 0
options sent: none
setoption before command: no
--- HONESTY_P ---
label HONESTY_P
exe /agent/repos/work/forge-combo29/build/forge
sha256 325a36090e18281429f0a9034d96d5176e35fc06321a73ef770ca0f6d8a6df27
bench11 nodes 312866 expected 312866 exit 0 OK
bench13 nodes 862329 expected 862329 exit 0 OK
bench16 nodes 3024920 expected 3024920 exit 0 OK
perft5 nodes 4865609 expected 4865609 exit 0 OK
id name Chess Engine Forge 6.4.24 candidate
uci_exit 0
options sent: none
setoption before command: no
--- cmp_off_O ---
positions 200
left_sum 9500069
right_sum 9500069
differ 0 of 200
--- cmp_off_G ---
positions 353
left_sum 18466239
right_sum 18466239
differ 0 of 353
--- cmp_on_O ---
positions 200
left_sum 9500069
right_sum 9722581
differ 200 of 200
first_diffs 1 2 3 4 5 6 7 8 9 10 11 12
--- asan clean ---
file forge-combo29/grok/054/asan_G100.err
stderr_lines 0
sanitizer_lines 0
--- asan trap ---
file forge-combo29/grok/054/asan_scratch.err
stderr_lines 55
sanitizer_lines 3
/tmp/scratch-s35/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
==7485==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000c0 at pc 0x557d07b03c37 bp 0x7ffeda562ef0 sp 0x7ffeda562ee0
SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/scratch-s35/forge-combo29/src/uci.cpp:46 in apply_position
--- match ---
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -0.00 +/- 10.81, nElo: 0.00 +/- 20.48
LOS: 50.00 %, DrawRatio: 62.21 %, PairsRatio: 0.97
Games: 1106, Wins: 340, Losses: 340, Draws: 426, Points: 553.0 (50.00 %)
Ptnml(0-2): [15, 91, 344, 85, 18], WL/DD Ratio: 1.75
--------------------------------------------------
Finished match
Total Time: 00:06:53 (hours:minutes:seconds)
--- partner off vs B ---
positions 200
left_sum 9500069
right_sum 9500069
differ 0 of 200
--- partner on vs their rows ---
positions 200
left_sum 9722581
right_sum 9722581
differ 0 of 200
--- partner on vs B ---
positions 200
left_sum 9500069
right_sum 9722581
differ 200 of 200
first_diffs 1 2 3 4 5 6 7 8 9 10 11 12
--- partner honesty ---
label partner104_HONESTY
exe /agent/repos/partner104/forge-combo29/build/forge
sha256 73b435d6de6b07d51e77fc9039f15e90e72f234283fb2b61312a5361d498e3c7
bench11 nodes 312866 expected 312866 exit 0 OK
bench13 nodes 862329 expected 862329 exit 0 OK
bench16 nodes 3024920 expected 3024920 exit 0 OK
perft5 nodes 4865609 expected 4865609 exit 0 OK
id name Chess Engine Forge 6.4.24 candidate
uci_exit 0
options sent: none
setoption before command: no
--- partner match ---
Results of on vs off (20000 nodes, 1t, 16MB, R.fens):
Elo: 2.90 +/- 9.42, nElo: 8.54 +/- 27.80
LOS: 72.65 %, DrawRatio: 83.00 %, PairsRatio: 1.22
Games: 600, Wins: 270, Losses: 265, Draws: 65, Points: 302.5 (50.42 %)
Ptnml(0-2): [3, 20, 249, 25, 3], WL/DD Ratio: 23.90
--------------------------------------------------
Finished match
Total Time: 00:02:59 (hours:minutes:seconds)
--- apply ---
idea.patch.txt git apply --check: ok
partner104 idea.patch.txt git apply --check: ok
--- stamps ---
2026-11-20T07:54:16Z STEP 1
2026-11-20T08:02:05Z STEP 2
2026-11-20T08:17:47Z STEP 3
2026-11-20T08:26:10Z STEP 4
2026-11-20T08:26:10Z STEP 5
```

Proofs.
(1) Honesty on exe P with no setoption: the four counts above, HONESTY_P.txt.
(2) S14, Threads 1, Hash 16, LmrLateParentRelief left false: O depth 12 differs 0 of 200 from exe B (sum 9500069) and G depth 12 differs 0 of 353 (sum 18466239).
(3) Same settings with LmrLateParentRelief true: O depth 12 differs 200 of 200 from exe B. Sum 9722581. The code runs.
(4) uci lists option name LmrLateParentRelief type check default false, option name IdeaS35_Index type spin default 7 min 1 max 64, option name IdeaS35_Replies type spin default 4 min 1 max 64. See HONESTY_P_uci.txt.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: stderr sanitizer lines 0. asan_G100.meta holds `nm -C <exe> | grep -c __asan_` 35. The same runner on a scratch copy that reads one past the end of a four-int heap array when the FEN is 8/8/8/8/8/8/8/K6k w - - 0 1 reports ERROR: AddressSanitizer: heap-buffer-overflow. See asan_scratch_lines.txt.

Match. exe P with LmrLateParentRelief true against the same exe with it false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games, concurrency 3. fastchess output is match_on_off.out and match_on_off.pgn. Elo -0.00 +/- 10.81, 340 wins, 340 losses, 426 draws. The point estimate is inside the prediction's wrong-range (below -20 or above +40). The interval is not entirely below 0, so the brief's look-once rule did not apply. Prediction for the O sum was 10200000, wrong outside 9600000 to 12000000. Measured 9722581, inside that range.

Partner verdict: CONFIRMS. Partner is seat 104 (next seat with this idea after 054; 004 also has a branch). idea.patch.txt from 27e98be54d7a4404a976fd5497e698665dce4ac6 is byte-identical to the patch I built, which was the patch at da40f5bc9dd79907ca17d52bc801c3cf8679037d. git apply --check ok. Honesty numbers match. Switch IdeaS35 false: O depth 12 equals exe B, 0 of 200. Switch IdeaS35 true: O depth 12 equals their published rows, 0 of 200, and differs from exe B in 200 of 200 (sum 9722581). Their exe sha256 73b435d6de6b07d51e77fc9039f15e90e72f234283fb2b61312a5361d498e3c7 matches the binary I built. My match of their switch, 300 R openings, both colours, 600 games: Elo 2.90 +/- 9.42.

suspicions, not proven. Their published OG match summary (Elo -0.00 +/- 10.81, 340/340/426, Ptnml 15 91 344 85 18) is the same summary as my one-ply match. The PGN result lines are not in the same order, so I do not claim the games were the same. The second ply in their patch (first reply, parent arrival index at least 24) did not change any of these 200 depth-12 node counts.

what I did NOT do. I did not add their second ply. I did not measure G at depth 12 with the switch on. I did not count how often the best move changed. I did not replay their 1106-game match. I started the partner check before minute 75 because my step 3 was pushed and their patch was already on the branch. A handoff fetch at step 1 and again at 2026-11-20T08:24:12Z found no forge-combo29/soak_all/FABLE_TO_grok_<N>.md.

what I am NOT sure about. I am not sure how often LmrLateParentRelief changes the chosen move at 20000 nodes. The node counts all change at depth 12 and the match Elo is 0 within +/- 10.81. I am not sure the far-parent second ply is a no-op outside this O set. On this set it changed no node count.

times: see stamps.txt

git status --short and ls -la follow.

```
 M forge-combo29/grok/054/config.json
 M forge-combo29/grok/054/stamps.txt
?? forge-combo29/grok/054/REPORT.md
?? forge-combo29/grok/054/RESULT.txt
?? forge-combo29/grok/054/apply_check.txt
?? forge-combo29/grok/054/asan_G100_lines.txt
?? forge-combo29/grok/054/asan_scratch_lines.txt
?? forge-combo29/grok/054/ls_la.txt
?? forge-combo29/grok/054/partner104_HONESTY.meta
?? forge-combo29/grok/054/partner104_HONESTY.txt
?? forge-combo29/grok/054/partner104_HONESTY_bench11.err
?? forge-combo29/grok/054/partner104_HONESTY_bench11.txt
?? forge-combo29/grok/054/partner104_HONESTY_bench13.err
?? forge-combo29/grok/054/partner104_HONESTY_bench13.txt
?? forge-combo29/grok/054/partner104_HONESTY_bench16.err
?? forge-combo29/grok/054/partner104_HONESTY_bench16.txt
?? forge-combo29/grok/054/partner104_HONESTY_perft5.err
?? forge-combo29/grok/054/partner104_HONESTY_perft5.txt
?? forge-combo29/grok/054/partner104_HONESTY_uci.err
?? forge-combo29/grok/054/partner104_HONESTY_uci.txt
?? forge-combo29/grok/054/partner104_claimed_on_O.nodes
?? forge-combo29/grok/054/partner104_cmp_off_O.txt
?? forge-combo29/grok/054/partner104_cmp_on_O.txt
?? forge-combo29/grok/054/partner104_cmp_on_vs_B.txt
?? forge-combo29/grok/054/partner104_match.err
?? forge-combo29/grok/054/partner104_match.out
?? forge-combo29/grok/054/partner104_match.pgn
?? forge-combo29/grok/054/partner104_match_result.txt
?? forge-combo29/grok/054/partner104_off_O.err
?? forge-combo29/grok/054/partner104_off_O.meta
?? forge-combo29/grok/054/partner104_off_O.nodes
?? forge-combo29/grok/054/partner104_off_O.raw
?? forge-combo29/grok/054/partner104_on_O.err
?? forge-combo29/grok/054/partner104_on_O.meta
?? forge-combo29/grok/054/partner104_on_O.nodes
?? forge-combo29/grok/054/partner104_on_O.raw
?? forge-combo29/grok/054/partner_match.sh
?? forge-combo29/grok/054/report_table.out
?? forge-combo29/grok/054/report_table.py
?? forge-combo29/grok/054/status_short.txt
```

```
total 8312
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:26 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      85 Nov 20 08:25 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 asan_G100.err
-rw-r--r-- 1 ubuntu ubuntu      75 Nov 20 08:25 asan_G100_lines.txt
-rw-r--r-- 1 ubuntu ubuntu     992 Nov 20 08:06 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu     581 Nov 20 08:06 asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu  131602 Nov 20 08:06 asan_G100.raw
-rw-r--r-- 1 ubuntu ubuntu    3474 Nov 20 08:08 asan_scratch.err
-rw-r--r-- 1 ubuntu ubuntu     476 Nov 20 08:25 asan_scratch_lines.txt
-rw-r--r-- 1 ubuntu ubuntu     981 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 asan_scratch.nodes
-rw-r--r-- 1 ubuntu ubuntu    6212 Nov 20 08:08 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu     834 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:01 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  550680 Nov 20 08:01 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:01 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309025 Nov 20 08:01 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:03 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:03 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:03 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     996 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    6928 Nov 20 08:22 config.json
-rw-r--r-- 1 ubuntu ubuntu    1031 Nov 20 08:08 decision.txt
-rw-r--r-- 1 ubuntu ubuntu     456 Nov 20 08:17 final_elo.py
-rw-r--r-- 1 ubuntu ubuntu    1624 Nov 20 08:05 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 G.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 HONESTY_B_bench11.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 HONESTY_B_bench13.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 HONESTY_B_bench16.err
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:00 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 HONESTY_B_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     430 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 HONESTY_B_uci.err
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:00 HONESTY_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 HONESTY_P_bench11.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 HONESTY_P_bench13.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 HONESTY_P_bench16.err
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:03 HONESTY_P.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 HONESTY_P_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     430 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 HONESTY_P_uci.err
-rw-r--r-- 1 ubuntu ubuntu    5053 Nov 20 08:03 HONESTY_P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    3070 Nov 20 07:59 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    3114 Nov 20 07:59 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:26 ls_la.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 match_on_off.err
-rw-r--r-- 1 ubuntu ubuntu  105770 Nov 20 08:16 match_on_off.out
-rw-r--r-- 1 ubuntu ubuntu 3493004 Nov 20 08:16 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     385 Nov 20 08:17 match_result.txt
-rwxr-xr-x 1 ubuntu ubuntu    1255 Nov 20 08:08 match.sh
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:19 partner104_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:19 partner104_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:19 partner104_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:19 partner104_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_HONESTY_bench11.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:19 partner104_HONESTY_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_HONESTY_bench13.err
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:19 partner104_HONESTY_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_HONESTY_bench16.err
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:19 partner104_HONESTY_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     243 Nov 20 08:19 partner104_HONESTY.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_HONESTY_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:19 partner104_HONESTY_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     445 Nov 20 08:19 partner104_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_HONESTY_uci.err
-rw-r--r-- 1 ubuntu ubuntu    5214 Nov 20 08:19 partner104_HONESTY_uci.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_match.err
-rw-r--r-- 1 ubuntu ubuntu   53198 Nov 20 08:22 partner104_match.out
-rw-r--r-- 1 ubuntu ubuntu 1604488 Nov 20 08:22 partner104_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     380 Nov 20 08:25 partner104_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     857 Nov 20 08:19 partner104_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:19 partner104_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309239 Nov 20 08:19 partner104_off_O.raw
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:19 partner104_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     891 Nov 20 08:19 partner104_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:19 partner104_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309538 Nov 20 08:19 partner104_on_O.raw
-rwxr-xr-x 1 ubuntu ubuntu    1174 Nov 20 08:19 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     834 Nov 20 08:03 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:03 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  550483 Nov 20 08:03 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 08:03 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:03 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309352 Nov 20 08:03 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:03 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:03 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309543 Nov 20 08:03 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     707 Nov 20 07:58 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   18304 Nov 20 08:26 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4670 Nov 20 08:26 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    2817 Nov 20 08:25 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:26 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19162 Nov 20 08:05 R.fens
-rwxr-xr-x 1 ubuntu ubuntu     783 Nov 20 08:06 run_asan.sh
-rw-r--r-- 1 ubuntu ubuntu     690 Nov 20 08:06 sanitizer_lines.py
-rw-r--r-- 1 ubuntu ubuntu     319 Nov 20 08:07 scratch_bug.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:07 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu    6517 Nov 20 08:04 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:26 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1934 Nov 20 08:26 status_short.txt
```
