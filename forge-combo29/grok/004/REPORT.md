S35, fuller replies to a late parent. The plain engine already takes one ply of reduction off the first four replies when the parent arrival index is at least 7, behind the check LmrLateParentRelief, default false.
I did not add a second search change. The fixed numbers 7 and 4 are now the spins LmrLateParentRelief_Index (default 7) and LmrLateParentRelief_Replies (default 4).
With the check false those spins are not read. With the check true and the defaults, the predicate is the one the engine already used, and the reduction is still one ply.

EXISTS: forge-combo29/src/search.cpp:2010
The line, from exists_line.txt, is `if (tune::LmrLateParentRelief && ss->arrival_index >= 7 && move_count <= 4) --r;`
The check was already a UCI option. The numbers 7 and 4 were not.

Honesty, no setoption, exe B (HONESTY_B.txt) and exe P (HONESTY_P.txt):
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both PASS.
Exe B, S14, depth 12 (B_sums.txt): O 200 positions sum 9500069, first three 41311 24872 28574. G 353 positions sum 18466239.

```
step | status | evidence | result
1 seat | done | 004/SEAT.txt | seat 004, idea 4, model Grok 4.7, 2026-11-20T07:52:15Z, token 17571287299283
2 honesty B | done | 004/HONESTY_B.txt | bench11 nodes 312866 expected 312866 match true bench13 nodes 862329 expected 862329 match true bench16 nodes 3024920 expected 3024920 match true perft5 nodes 4865609 expected 4865609 match true PASS
2 O and G | done | 004/B_sums.txt | B_O_d12.nodes.txt positions 200 sum 9500069 first 41311 24872 28574 | B_G_d12.nodes.txt positions 353 sum 18466239 first 37203 70845 144383
3 apply | done | 004/apply_check.txt | git apply --check: ok
3 proof 1 honesty P | done | 004/HONESTY_P.txt | bench11 nodes 312866 expected 312866 match true bench13 nodes 862329 expected 862329 match true bench16 nodes 3024920 expected 3024920 match true perft5 nodes 4865609 expected 4865609 match true PASS
3 proof 2 off O | done | 004/compare_off_O.txt | differ 0 of 200
3 proof 2 off G | done | 004/compare_off_G.txt | differ 0 of 353
3 proof 3 on O | done | 004/compare_on_O.txt | right_sum 9722581 differ 200 of 200
3 proof 4 uci | done | 004/uci_options.txt | option name LmrLateParentRelief type check default false | option name LmrLateParentRelief_Index type spin default 7 min 0 max 64 | option name LmrLateParentRelief_Replies type spin default 4 min 0 max 64
3 proof 5 sanitizer | done | 004/asan_sanitizer_lines.txt | forge-combo29/grok/004/asan_G100_d10.raw.txt sanitizer_lines 0 | forge-combo29/grok/004/asan_bug_special.raw.txt sanitizer_lines 1 | /tmp/asan_scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
3 asan symbols | done | 004/asan_G100_d10.meta | nm_asan_count 35
3 match | done | 004/match_summary.txt | finished_lines 1106 | Elo: -0.00 +/- 10.81, nElo: 0.00 +/- 20.48 | Games: 1106, Wins: 340, Losses: 340, Draws: 426, Points: 553.0 (50.00 %)
3 pgn | done | 004/pgn_counts.txt | pgn_games 1106 | partner_pgn_games 600
4 partner off | done | 004/partner054_cmp_off_O.txt | differ 0 of 200
4 partner on vs claim | done | 004/partner054_cmp_on_vs_claim.txt | differ 0 of 200
4 partner on vs B | done | 004/partner054_cmp_on_vs_B.txt | differ 200 of 200
4 partner honesty | done | 004/partner054_HONESTY.txt | bench11 nodes 312866 expected 312866 match true bench13 nodes 862329 expected 862329 match true bench16 nodes 3024920 expected 3024920 match true perft5 nodes 4865609 expected 4865609 match true PASS
4 partner match | done | 004/partner_match_summary.txt | finished_lines 600 | Elo: 5.79 +/- 10.51, nElo: 15.32 +/- 27.80 | Games: 600, Wins: 270, Losses: 260, Draws: 70, Points: 305.0 (50.83 %)
```

That table is the output of report_table.py, saved as report_table.out.

Proofs on exe P:
(1) No setoption. Same four honesty numbers as exe B. HONESTY_P.txt PASS.
(2) S14 and LmrLateParentRelief false. O depth 12 differs from exe B in 0 of 200 positions (compare_off_O.txt). G depth 12 differs in 0 of 353 (compare_off_G.txt). Both sums match the known sums.
(3) S14 and LmrLateParentRelief true. O depth 12 sum 9722581. 200 of 200 positions differ from exe B (compare_on_O.txt).
(4) uci lists LmrLateParentRelief check default false, LmrLateParentRelief_Index spin default 7 min 0 max 64, LmrLateParentRelief_Replies spin default 4 min 0 max 64 (uci_options.txt).
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: 0 sanitizer lines (asan_sanitizer_lines.txt). asan_G100_d10.meta has nm_asan_count 35. A scratch copy with one read past the end of a 4-int heap array, on the FEN 8/8/8/3k4/8/8/3K4/8 w - - 0 1, built the same way and run through search_set.py, reports one sanitizer line: runtime error, load with insufficient space for an object of type int. That scratch meta also has nm_asan_count 35 (asan_bug_special.meta).

Match: exe P switch true against exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O and G (553), both colours. match_summary.txt: Elo -0.00 +/- 10.81, 1106 games, 340 wins, 340 losses, 426 draws. pgn_counts.txt says 1106 games in the pgn. The whole fastchess log is match_on_vs_off.log and the games are match_on_vs_off.pgn. Prediction was +4 Elo, wrong if the point estimate was outside -30 to +40. -0.00 is inside that range. It is not below -20.

Partner is seat 054 (same idea, the next seat after 004 that has a branch). Verdict: CONFIRMS.
git apply --check of partner054.patch.txt on a fresh base worktree succeeded (partner054_apply_check.txt). Honesty PASS (partner054_HONESTY.txt). Switch false matches exe B on O depth 12, 0 of 200 differ. Switch true matches the partner's own O depth-12 file, 0 of 200 differ, sum 9722581, and 200 of 200 differ from exe B, which is what the partner claims. Their uci output lists IdeaS35_Index default 7 and IdeaS35_Replies default 4. My 300 R openings, both colours, 600 games (partner_match_summary.txt): Elo 5.79 +/- 10.51.

suspicions, not proven
The 1106-game match landed on 340 wins and 340 losses. The Ptnml line in the log is not all draws, so the games are not one repeated draw. I did not dig further.
Seat 054's RESULT says option=IdeaS35. The check that changes the search is still LmrLateParentRelief. The new spins are IdeaS35_Index and IdeaS35_Replies. Their decision.txt says that. The node rows still match, so the name is not a failed proof.
Seat 054's reported elo and error (-0.00 +/- 10.81, 1106 games) match my match exactly, and their on-nodes match mine exactly. That is what identical on-path code and the same opening order produce. I remeasured the nodes. I did not prove they copied a log.
fastchess wrote config.json into this folder and the partner run overwrote it. config.json is the first match again. partner_config.json is the R match.
The partner match log prints DrawRatio 81.33% while the Games line says 70 draws out of 600. I quote the Games line and the Elo line.

what I did NOT do
I did not add the second ply on the first reply when the parent is far past the first threshold. That sentence is in the idea text and it is not in this engine. Adding it would have changed today's on-path.
I did not re-run seat 054's sanitizer or their 1106-game match.
I did not review seat 104. The partner rule picks 054.
I did not open a pull request.
The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 found no FABLE_TO_grok file. The minute-1 fetch found none either.

what I am NOT sure about
Whether a second ply for a very late parent would have been stronger than exposing the existing numbers. The order for an idea that already exists is to expose today's numbers.
The R file uses seed 401, then 402, and so on, ply cap 64, and drops a game that ends before the cap. make_r.py reported games_used 34 and games_dropped 0. None of those games ended by ply 64, so the drop rule never fired.
Step 4 started when seat 054's patch and RESULT were already on the branch, at 08:54 UTC. Minute 75 from the first stamp is 09:07 UTC.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/004/run_partner_match.sh
 M forge-combo29/grok/004/stamps.txt
?? forge-combo29/grok/004/HONESTY_P.txt
?? forge-combo29/grok/004/REPORT.md
?? forge-combo29/grok/004/RESULT.txt
?? forge-combo29/grok/004/exists_line.txt
?? forge-combo29/grok/004/partner054.patch.txt
?? forge-combo29/grok/004/partner054_HONESTY.txt
?? forge-combo29/grok/004/partner054_apply_check.txt
?? forge-combo29/grok/004/partner054_claimed_off_O.nodes
?? forge-combo29/grok/004/partner054_claimed_on_O.nodes
?? forge-combo29/grok/004/partner054_cmp_off_O.txt
?? forge-combo29/grok/004/partner054_cmp_on_vs_B.txt
?? forge-combo29/grok/004/partner054_cmp_on_vs_claim.txt
?? forge-combo29/grok/004/partner054_honesty/
?? forge-combo29/grok/004/partner054_off_O.meta
?? forge-combo29/grok/004/partner054_off_O.nodes.txt
?? forge-combo29/grok/004/partner054_off_O.raw.txt
?? forge-combo29/grok/004/partner054_on_O.meta
?? forge-combo29/grok/004/partner054_on_O.nodes.txt
?? forge-combo29/grok/004/partner054_on_O.raw.txt
?? forge-combo29/grok/004/partner_config.json
?? forge-combo29/grok/004/partner_match.log
?? forge-combo29/grok/004/partner_match.pgn
?? forge-combo29/grok/004/partner_match_summary.txt
?? forge-combo29/grok/004/partner_verdict.txt
?? forge-combo29/grok/004/pgn_counts.txt
?? forge-combo29/grok/004/report_table.out
?? forge-combo29/grok/004/report_table.py

$ ls -la forge-combo29/grok/004
total 4972
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 09:00 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:06 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     252 Nov 20 08:06 asan_bug_special.meta
-rw-r--r-- 1 ubuntu ubuntu    7282 Nov 20 08:05 asan_bug_special.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1090 Nov 20 08:05 asan_bug_special.stdout
-rw-r--r-- 1 ubuntu ubuntu     691 Nov 20 08:05 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     581 Nov 20 08:05 asan_G100_d10.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  131587 Nov 20 08:05 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:05 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     278 Nov 20 08:06 asan_sanitizer_lines.txt
-rw-r--r-- 1 ubuntu ubuntu     627 Nov 20 08:00 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:00 B_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  549976 Nov 20 08:00 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     630 Nov 20 08:00 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:00 B_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309154 Nov 20 08:00 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     138 Nov 20 08:00 B_sums.txt
-rw-r--r-- 1 ubuntu ubuntu    1265 Nov 20 08:06 bug_meta.py
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:02 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:02 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:02 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     299 Nov 20 08:02 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    6976 Nov 20 09:00 config.json
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:06 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     479 Nov 20 09:00 exists_line.txt
-rw-r--r-- 1 ubuntu ubuntu     245 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     245 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     247 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     249 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3152 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     386 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_uci.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:01 honesty_p
-rw-r--r-- 1 ubuntu ubuntu     386 Nov 20 09:00 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    3297 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1348 Nov 20 08:07 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  156975 Nov 20 08:13 match_on_vs_off.log
-rw-r--r-- 1 ubuntu ubuntu 1077433 Nov 20 08:13 match_on_vs_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     136 Nov 20 08:15 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     805 Nov 20 08:05 note_asan.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     715 Nov 20 08:07 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:54 partner054_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:54 partner054_claimed_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:54 partner054_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:54 partner054_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     299 Nov 20 08:54 partner054_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:54 partner054_cmp_on_vs_claim.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:54 partner054_honesty
-rw-r--r-- 1 ubuntu ubuntu     381 Nov 20 09:00 partner054_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     658 Nov 20 08:54 partner054_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:54 partner054_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309202 Nov 20 08:54 partner054_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:54 partner054_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:54 partner054_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309379 Nov 20 08:54 partner054_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    3114 Nov 20 08:54 partner054.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    6955 Nov 20 09:00 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu   83276 Nov 20 08:57 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu  527935 Nov 20 08:57 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     133 Nov 20 09:00 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     261 Nov 20 09:00 partner_verdict.txt
-rw-r--r-- 1 ubuntu ubuntu      37 Nov 20 09:00 pgn_counts.txt
-rw-r--r-- 1 ubuntu ubuntu     660 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:02 P_off_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  549972 Nov 20 08:02 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     663 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 P_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309114 Nov 20 08:02 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     662 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:02 P_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309308 Nov 20 08:02 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     366 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19545 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu    9536 Nov 20 09:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2678 Nov 20 09:00 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    2926 Nov 20 09:00 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     231 Nov 20 09:00 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1404 Nov 20 08:06 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1265 Nov 20 08:16 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     653 Nov 20 08:06 san_lines.py
-rw-r--r-- 1 ubuntu ubuntu    7145 Nov 20 08:16 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     626 Nov 20 07:59 smoke_B_O.meta
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 07:59 smoke_B_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   10349 Nov 20 07:59 smoke_B_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     569 Nov 20 08:00 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1238 Nov 20 08:02 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5077 Nov 20 08:02 uci_options.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:02 uci_options.txt
```
