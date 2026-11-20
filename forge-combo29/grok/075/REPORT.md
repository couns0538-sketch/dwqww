Idea S33: inside a null-move tree, reduce the side that passed by more when the static margin over beta is thin, and by nothing when the margin is large. A probe that still reaches beta is accepted with no second search. A miss of at most 30 centipawns gives the real-move search one extra ply instead of a verification tree.
Built as check option IdeaS33, default false, plus spins IdeaS33_Thin 50, IdeaS33_Large 300, IdeaS33_Extra 2, IdeaS33_Near 30. The extra plies are late-move reduction on the passer only, copied down that null subtree. Off, those branches are not taken.
The patch is idea.patch.txt. git apply --check on a fresh copy of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0 and wrote idea_apply_check.txt of 0 bytes.

EXISTS: no. search.cpp already adds min((eval - beta) / NullMoveEvalDivisor, 3) to the null reduction, which is more reduction when the margin is large, and it still verifies cutoffs at depth 14 and above. That is the opposite scale, and it is not a reduction of the passer's own moves inside the null tree. See design.txt.

Honesty, no setoption, fresh process each line. Exe B and exe P both: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. The partner binary, after its patch, printed the same four node counts.

The block below is the pasted output of report_table.py (report_bits.txt). It reads the raw logs.

```
honesty_b_bench11 info string bench depth 11 nodes 312866 time 184 nps 1700358
honesty_b_bench13 info string bench depth 13 nodes 862329 time 510 nps 1690841
honesty_b_bench16 info string bench depth 16 nodes 3024920 time 1564 nps 1934092
honesty_b_perft5 nodes 4865609
honesty_p_bench11 info string bench depth 11 nodes 312866 time 166 nps 1884734
honesty_p_bench13 info string bench depth 13 nodes 862329 time 446 nps 1933473
honesty_p_bench16 info string bench depth 16 nodes 3024920 time 1491 nps 2028786
honesty_p_perft5 nodes 4865609
partner_bench11 info string bench depth 11 nodes 312866 time 188 nps 1664180
partner_bench13 info string bench depth 13 nodes 862329 time 589 nps 1464056
partner_bench16 info string bench depth 16 nodes 3024920 time 1596 nps 1895313
partner_perft5 nodes 4865609
O_off left 200 9500069 right 200 9500069 differ 0
G_off left 353 18466239 right 353 18466239 differ 0
O_on left 200 9500069 right 200 10838685 differ 200
partner_O_off left 200 9500069 right 200 9500069 differ 0
partner_O_on_vs_their_rows mine 200 11375225 theirs 200 11375225 differ 0
partner_O_on_vs_exe_B differ 200 of 200
asan_g100_positions 100 error_lines 0
nm_asan_count=35
canary /tmp/asan-canary-src/src/uci.cpp:47:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
canary_sanitizer_lines 1
idea_apply_check_bytes 0
partner_apply_check_bytes 0
```

step | status | evidence | result
--- | --- | --- | ---
1 seat | done | SEAT.txt, stamps.txt | seat 075, idea 25, S33
2 honesty and known sums | done | HONESTY_B.txt, o_b_d12.txt, g_b_d12.txt | benches and perft match; O sum 9500069 differ later 0; G sum 18466239
3 patch and proofs | done | idea.patch.txt, report_bits.txt | applies; off differ 0; on differ 200 of 200; sanitizer clean
3 match | done | match_s33.txt, match_final.txt | Elo -3.14 +/- 10.34, 1106 games
4 partner 025 | done | partner_025_idea.patch.txt, partner_025_o_off.txt, partner_025_o_on.txt, partner_025_match_final.txt | CONFIRMS
5 report | done | REPORT.md, RESULT.txt | this file

Proof (1). Exe P, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Same as exe B. Raw files honesty_p_bench11.txt, honesty_p_bench13.txt, honesty_p_bench16.txt, honesty_p_perft5.txt.

Proof (2). S14 and IdeaS33 false. O depth 12: 200 positions, sum 9500069, differ 0 against exe B. G depth 12: 353 positions, sum 18466239, differ 0 against exe B.

Proof (3). S14 and IdeaS33 true. O depth 12 sum 10838685. Differ 200 of 200 against exe B. Prediction was 10400000, wrong outside 6000000 to 16000000. The sum is inside that range.

Proof (4). uci_p.txt lists IdeaS33 check default false, IdeaS33_Thin spin default 50, IdeaS33_Large spin default 300, IdeaS33_Extra spin default 2, IdeaS33_Near spin default 30.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS33 true, first 100 of G at depth 10: 100 positions, 0 lines containing ERROR: or runtime error:. asan_g100_d10.txt.meta has nm_asan_count=35. The same runner on the scratch engine, which reads one int past a 4-int heap array on the FEN in canary.fen, wrote one sanitizer line (runtime error: load of address with insufficient space for an object of type int) in asan_canary.txt. ASAN_OPTIONS was detect_leaks=0:halt_on_error=1:abort_on_error=1.

Match, from match_final.txt, which is the last results block of match_s33.txt:

```
Results of S33on vs S33off (20000 nodes, 1t, 16MB, og_openings.epd):
Elo: -3.14 +/- 10.34, nElo: -6.22 +/- 20.48
LOS: 27.57 %, DrawRatio: 63.65 %, PairsRatio: 0.91
Games: 1106, Wins: 338, Losses: 348, Draws: 420, Points: 548.0 (49.55 %)
Ptnml(0-2): [14, 91, 352, 83, 13], WL/DD Ratio: 1.86
--------------------------------------------------
Finished match
```

Predicted Elo was -15, wrong outside -80 to 40. -3.14 is inside that range. The interval crosses 0, and it is not below -20, so the code was not opened again for a suspected mistake. fastchess from github.com/Disservin/fastchess, concurrency 3. OwnBook was set false. Openings are O then G, 553 positions, both colours.

Partner. Seats for idea 25 are 025, 075, 125. 125 had no branch. The partner is 025. Their idea.patch.txt applies: git apply --check exited 0, partner_025_apply_check.txt is 0 bytes. Their binary's honesty nodes match. IdeaS33 false: O depth 12 differ 0 against exe B. IdeaS33 true with their defaults Max 3, Divisor 80, Near 40: my rows match their O_P_on.rows on all 200 positions (sum 11375225, differ 0) and differ from exe B on 200 of 200, which is what their RESULT.txt claims. A match of their switch on my 300 R openings, both colours, 600 games, from partner_025_match_final.txt: Elo 4.05 +/- 6.70, games 600. Verdict: CONFIRMS.

suspicions, not proven. All 200 O positions changed node counts with the switch on, and the sum rose from 9500069 to 10838685. The near-miss extra ply may be firing on a large share of null tries. I did not count how often. The 300 R positions come from 6 random games that ran to a 400-ply cap (make_r.py); they are legal positions, and they are a narrow sample. Draw endings in the match (fifty moves, threefold, insufficient material) are the rules of chess, not engine faults.

what I did NOT do. I did not rebuild the partner under a sanitizer. I did not replay their 1106-game match. I did not measure G at depth 12 with IdeaS33 true. I did not try spin values other than the defaults. I did not play a second match of my own patch on R, because seat 025 had a patch. No FABLE_TO_grok file existed at step 1 or at minute 60.

what I am NOT sure about. The idea's sentence "reduce the side that passed" can mean the passer's late-move reductions inside the null tree, which is what I built, or the depth of the null probe itself, which is what seat 025 built. I am not sure which reading was intended. I am not sure the +1 ply near-miss is rare enough to be the cheap substitute for verification that the idea describes. The Elo interval includes both a small loss and a small gain.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/075/stamps.txt
?? config.json
?? forge-combo29/grok/075/REPORT.md
?? forge-combo29/grok/075/RESULT.txt
?? forge-combo29/grok/075/compare_partner_nodes.py
?? forge-combo29/grok/075/idea_apply_check.txt
?? forge-combo29/grok/075/partner_025_O_on.nodes
?? forge-combo29/grok/075/partner_025_O_on.rows
?? forge-combo29/grok/075/partner_025_apply_check.txt
?? forge-combo29/grok/075/partner_025_bench11.txt
?? forge-combo29/grok/075/partner_025_bench13.txt
?? forge-combo29/grok/075/partner_025_bench16.txt
?? forge-combo29/grok/075/partner_025_idea.patch.txt
?? forge-combo29/grok/075/partner_025_match.pgn
?? forge-combo29/grok/075/partner_025_match.txt
?? forge-combo29/grok/075/partner_025_match_final.txt
?? forge-combo29/grok/075/partner_025_o_off.txt
?? forge-combo29/grok/075/partner_025_o_off.txt.meta
?? forge-combo29/grok/075/partner_025_o_on.txt
?? forge-combo29/grok/075/partner_025_o_on.txt.meta
?? forge-combo29/grok/075/partner_025_perft5.txt
?? forge-combo29/grok/075/report_bits.txt
?? forge-combo29/grok/075/report_table.py
?? forge-combo29/grok/075/run_partner_match.sh
$ ls -la forge-combo29/grok/075
total 6404
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu    6661 Nov 20 08:09 asan_canary.txt
-rw-r--r-- 1 ubuntu ubuntu     269 Nov 20 08:10 asan_canary.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  225639 Nov 20 08:08 asan_g100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     699 Nov 20 08:08 asan_g100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:08 canary.fen
-rw-r--r-- 1 ubuntu ubuntu     858 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     949 Nov 20 09:11 compare_partner_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1844 Nov 20 08:04 design.txt
-rw-r--r-- 1 ubuntu ubuntu     462 Nov 20 08:18 extract_last_result.py
-rw-r--r-- 1 ubuntu ubuntu  863195 Nov 20 08:03 g_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     623 Nov 20 08:03 g_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  883725 Nov 20 08:05 g_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     644 Nov 20 08:05 g_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:02 g_set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     656 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:08 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:08 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:08 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:08 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     553 Nov 20 08:08 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:16 idea_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   13246 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1161 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     356 Nov 20 08:18 match_final.txt
-rw-r--r-- 1 ubuntu ubuntu 1070223 Nov 20 08:16 match_s33.pgn
-rw-r--r-- 1 ubuntu ubuntu  138608 Nov 20 08:16 match_s33.txt
-rw-r--r-- 1 ubuntu ubuntu    5836 Nov 20 08:07 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu  485998 Nov 20 08:03 o_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     627 Nov 20 08:03 o_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:02 o_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 og_openings.epd
-rw-r--r-- 1 ubuntu ubuntu  497775 Nov 20 08:05 o_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     648 Nov 20 08:05 o_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  497908 Nov 20 08:06 o_p_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     647 Nov 20 08:06 o_p_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_025_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_025_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_025_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_025_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    7841 Nov 20 09:11 partner_025_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     345 Nov 20 09:16 partner_025_match_final.txt
-rw-r--r-- 1 ubuntu ubuntu  380623 Nov 20 09:14 partner_025_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   72262 Nov 20 09:14 partner_025_match.txt
-rw-r--r-- 1 ubuntu ubuntu  498001 Nov 20 09:12 partner_025_o_off.txt
-rw-r--r-- 1 ubuntu ubuntu     665 Nov 20 09:12 partner_025_o_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1211 Nov 20 09:11 partner_025_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu   15764 Nov 20 09:11 partner_025_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu  534029 Nov 20 09:12 partner_025_o_on.txt
-rw-r--r-- 1 ubuntu ubuntu     734 Nov 20 09:12 partner_025_o_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner_025_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     744 Nov 20 08:14 partner_check.py
-rw-r--r-- 1 ubuntu ubuntu     634 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    1921 Nov 20 08:08 print_proofs.py
-rw-r--r-- 1 ubuntu ubuntu    1745 Nov 20 08:09 proofs_table.txt
-rw-r--r-- 1 ubuntu ubuntu   14547 Nov 20 08:09 r_300.fen
-rw-r--r-- 1 ubuntu ubuntu    2143 Nov 20 09:16 report_bits.txt
-rw-r--r-- 1 ubuntu ubuntu    7474 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3259 Nov 20 09:16 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:17 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1085 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1226 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     489 Nov 20 08:02 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    5219 Nov 20 08:05 uci_p.txt
```
