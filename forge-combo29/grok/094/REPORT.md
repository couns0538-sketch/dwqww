IdeaK5 adds the quiet move's history, divided by IdeaK5_Divisor (default 64), to the quiet futility margin when the check is on and the reduced depth is at most IdeaK5_Depth (default 5).
The check is off by default, and while it is off that division is not done, so the margin is the sum the engine uses today.
A positive history widens the margin and a negative history narrows it. The QuietExtinction tight margin is unchanged.

EXISTS: no. In src/search.cpp the quiet futility test is static eval plus FutilityBase plus FutilityMultiplier times the reduced depth, and it does not read history. Capture futility can add history/8, and only when CaptureFutilityBase is above 0; that default is 0, so it is a different gate and it is off.

Honesty, no setoption, exe B and exe P, each line a fresh process: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

The table is the output of report_facts.py, which reads the raw files:

```
step | status | evidence | result
honesty B | done | HONESTY_B.txt | bench11 312866 bench13 862329 bench16 3024920 perft5 4865609
honesty P | done | HONESTY_P.txt | bench11 312866 bench13 862329 bench16 3024920 perft5 4865609
baseline O | done | O_B.meta | sum 9500069
baseline G | done | G_B.meta | sum 18466239
apply | done | apply_check.txt | git apply --check: ok
proof off O | done | compare_O_off.txt | left forge-combo29/grok/094/O_B.nodes rows 200 sum 9500069 ; right forge-combo29/grok/094/O_P_off.nodes rows 200 sum 9500069 ; compared 200 ; differ 0
proof off G | done | compare_G_off.txt | left forge-combo29/grok/094/G_B.nodes rows 353 sum 18466239 ; right forge-combo29/grok/094/G_P_off.nodes rows 353 sum 18466239 ; compared 353 ; differ 0
proof on O | done | compare_O_on.txt | left forge-combo29/grok/094/O_B.nodes rows 200 sum 9500069 ; right forge-combo29/grok/094/O_P_on.nodes rows 200 sum 9725707 ; compared 200 ; differ 200
uci | done | UCI_OPTIONS_IDEA.txt | option name IdeaK5 type check default false ; option name IdeaK5_Divisor type spin default 64 min 1 max 1024 ; option name IdeaK5_Depth type spin default 5 min 0 max 15
asan nm | done | asan_nm_count.txt G100_asan.meta | count 35
asan real lines | done | G100_asan.log | AddressSanitizer 0 runtime error 0
asan scratch | done | scratch_asan_report.log | heap-buffer-overflow 2
match | done | match_summary.txt | Elo: -9.74 +/- 9.89, nElo: -20.19 +/- 20.48 ; Games: 1106, Wins: 316, Losses: 347, Draws: 443, Points: 537.5 (48.60 %)
partner apply | done | partner_apply_check.txt | git apply --check: ok
partner honesty | done | partner_honesty.progress | bench11 OK nodes 312866 expected 312866 ; bench13 OK nodes 862329 expected 862329 ; bench16 OK nodes 3024920 expected 3024920 ; perft5 OK nodes 4865609 expected 4865609
partner off | done | partner_compare_off.txt | left forge-combo29/grok/094/O_B.nodes rows 200 sum 9500069 ; right forge-combo29/grok/094/partner_O_off.nodes rows 200 sum 9500069 ; compared 200 ; differ 0
partner on | done | partner_compare_on.txt | partner rows 200 sum 9524101 ; mine rows 200 sum 9524101 ; compared 200 ; differ 0
partner match | done | partner_match.log | Elo: 6.95 +/- 16.64, nElo: 20.13 +/- 48.15 ; Games: 200, Wins: 91, Losses: 87, Draws: 22, Points: 102.0 (51.00 %) ; Elo: 1.74 +/- 11.29, nElo: 5.24 +/- 34.05 ; Games: 400, Wins: 178, Losses: 176, Draws: 46, Points: 201.0 (50.25 %) ; Elo: -1.74 +/- 9.15, nElo: -5.28 +/- 27.80 ; Games: 600, Wins: 263, Losses: 266, Draws: 71, Points: 298.5 (49.75 %) ; MATCH_EXIT:0
```

Proofs on exe P. S14, Threads 1, Hash 16. The release build has AVX-512 and BMI2, so it is the default march, not the portable one.

(1) Honesty with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Same as exe B.
(2) Switch false: O depth 12 differ 0, sum 9500069, against exe B. G depth 12 differ 0, sum 18466239, against exe B. Exe B itself reproduced O 9500069 (first three 41311, 24872, 28574) and G 18466239.
(3) Switch true, divisor 64, depth 5: O depth 12 differ 200 of 200, sum 9725707.
(4) uci lists IdeaK5 check default false, IdeaK5_Divisor spin default 64 min 1 max 1024, IdeaK5_Depth spin default 5 min 0 max 15.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: the log has 0 AddressSanitizer lines and 0 runtime error lines. nm -C of that exe has 35 __asan_ symbols, recorded in G100_asan.meta. The same runner on a scratch copy that reads one past a four-int heap array when given scratch_fen.txt reports heap-buffer-overflow (the line is in scratch_asan_report.log; the count 2 is the error line plus the summary line).

Match: IdeaK5 on versus IdeaK5 off, both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G (553), both colours, 1106 games. parse_match.py on match_on_off.log: Elo -9.74 +/- 9.89, Games 1106, Wins 316, Losses 347, Draws 443, Points 537.5. The point estimate is not below -20, and the interval is not entirely below 0, so I did not open the code a second time for a match bug.

Partner is seat 044 (idea 44; the next seat after 094 is 044). Verdict: CONFIRMS. git apply --check on a clean base exited 0. Honesty numbers match. Switch false O depth 12 matches exe B on all 200 rows. Switch true matches their published P_on_O_depth12.nodes on all 200 rows (sum 9524101) and differs from exe B on 200 rows (partner_compare_on_vs_B.txt), which is what their P_COMPARE.txt says. Their first differing rows (41311/35208, 24872/24531, 28574/28765) are the same rows I measured. A match of their switch, their default divisor 48, on my 300 R openings, both colours, 600 games: the last Elo line is -1.74 +/- 9.15.

suspicions, not proven: the on-tree is larger (9725707 against 9500069), so at a fixed 20000 nodes the search is wider. That can explain a small negative Elo without a logic bug. The off path is node-identical, so the check does gate the term. I am not claiming the divisor is wrong.

what I did NOT do: G depth 12 with my switch on. A sanitizer build of the partner patch. Their QuietExtinction line, which also adds the history term; S14 leaves QuietExtinction false, so that line did not run. No FABLE_TO_grok file existed at step 1 or at minute 60. I did not change the patch after the match.

what I am NOT sure about: whether 64 is a good divisor. The match interval -9.74 +/- 9.89 includes both a loss and a fraction of a gain. prediction.txt, written before any search of exe P, said 9100000 (wrong below 8000000 or above 10500000) and +4 Elo (wrong below -25 or above +35). The measured sum 9725707 and Elo -9.74 sit inside those ranges, and the node count went up rather than down.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/094/stamps.txt
?? forge-combo29/grok/094/HONESTY_PARTNER.meta
?? forge-combo29/grok/094/HONESTY_PARTNER.txt
?? forge-combo29/grok/094/HONESTY_PARTNER_bench11.meta
?? forge-combo29/grok/094/HONESTY_PARTNER_bench11.txt
?? forge-combo29/grok/094/HONESTY_PARTNER_bench13.meta
?? forge-combo29/grok/094/HONESTY_PARTNER_bench13.txt
?? forge-combo29/grok/094/HONESTY_PARTNER_bench16.meta
?? forge-combo29/grok/094/HONESTY_PARTNER_bench16.txt
?? forge-combo29/grok/094/HONESTY_PARTNER_id.txt
?? forge-combo29/grok/094/HONESTY_PARTNER_perft5.meta
?? forge-combo29/grok/094/HONESTY_PARTNER_perft5.txt
?? forge-combo29/grok/094/REPORT.md
?? forge-combo29/grok/094/RESULT.txt
?? forge-combo29/grok/094/compare_partner_on.py
?? forge-combo29/grok/094/partner_044.patch.txt
?? forge-combo29/grok/094/partner_044_O_on.nodes
?? forge-combo29/grok/094/partner_O_off.log
?? forge-combo29/grok/094/partner_O_off.meta
?? forge-combo29/grok/094/partner_O_off.nodes
?? forge-combo29/grok/094/partner_O_off.progress
?? forge-combo29/grok/094/partner_O_on.log
?? forge-combo29/grok/094/partner_O_on.meta
?? forge-combo29/grok/094/partner_O_on.nodes
?? forge-combo29/grok/094/partner_O_on.progress
?? forge-combo29/grok/094/partner_apply_check.txt
?? forge-combo29/grok/094/partner_compare_off.txt
?? forge-combo29/grok/094/partner_compare_on.txt
?? forge-combo29/grok/094/partner_compare_on_vs_B.txt
?? forge-combo29/grok/094/partner_fastchess_config.json
?? forge-combo29/grok/094/partner_honesty.progress
?? forge-combo29/grok/094/partner_match.log
?? forge-combo29/grok/094/partner_match.pgn
?? forge-combo29/grok/094/report_facts.py
?? forge-combo29/grok/094/report_facts.txt
?? forge-combo29/grok/094/run_partner_match.sh

$ ls -la forge-combo29/grok/094
total 5040
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:09 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     382 Nov 20 08:07 asan_nm.py
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:05 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1138 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:05 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     736 Nov 20 08:05 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1119 Nov 20 09:12 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    1727 Nov 20 08:02 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu    7264 Nov 20 08:16 fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu  132209 Nov 20 08:07 G100_asan.log
-rw-r--r-- 1 ubuntu ubuntu    1035 Nov 20 08:08 G100_asan.meta
-rw-r--r-- 1 ubuntu ubuntu     582 Nov 20 08:07 G100_asan.nodes
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:07 G100_asan.progress
-rw-r--r-- 1 ubuntu ubuntu  551545 Nov 20 08:01 G_B.log
-rw-r--r-- 1 ubuntu ubuntu     884 Nov 20 08:01 G_B.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:01 G_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  551188 Nov 20 08:05 G_P_off.log
-rw-r--r-- 1 ubuntu ubuntu     930 Nov 20 08:05 G_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:05 G_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu    6289 Nov 20 08:05 G_P_off.progress
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:00 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:00 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:00 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:00 HONESTY_B_id.txt
-rw-r--r-- 1 ubuntu ubuntu     258 Nov 20 08:00 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 08:00 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2996 Nov 20 08:04 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     545 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:12 HONESTY_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 HONESTY_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:12 HONESTY_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 HONESTY_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:12 HONESTY_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 HONESTY_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5040 Nov 20 09:12 HONESTY_PARTNER_id.txt
-rw-r--r-- 1 ubuntu ubuntu     261 Nov 20 09:12 HONESTY_PARTNER.meta
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 HONESTY_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 HONESTY_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     545 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:05 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:05 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:05 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 08:05 HONESTY_P_id.txt
-rw-r--r-- 1 ubuntu ubuntu     258 Nov 20 08:05 HONESTY_P.meta
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 08:05 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     545 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    4962 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1390 Nov 20 08:09 make_r.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu  132802 Nov 20 08:16 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 1076481 Nov 20 08:16 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:19 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    8176 Nov 20 08:20 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu  309866 Nov 20 08:01 O_B.log
-rw-r--r-- 1 ubuntu ubuntu     889 Nov 20 08:01 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:01 O_B.nodes
-rw-r--r-- 1 ubuntu ubuntu   10348 Nov 20 08:01 O_B_smoke.log
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:01 O_B_smoke.meta
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 08:01 O_B_smoke.nodes
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu  309847 Nov 20 08:05 O_P_off.log
-rw-r--r-- 1 ubuntu ubuntu     935 Nov 20 08:05 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:05 O_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu    3528 Nov 20 08:05 O_P_off.progress
-rw-r--r-- 1 ubuntu ubuntu  309723 Nov 20 08:05 O_P_on.log
-rw-r--r-- 1 ubuntu ubuntu    1008 Nov 20 08:05 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 08:05 O_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    3326 Nov 20 08:05 O_P_on.progress
-rw-r--r-- 1 ubuntu ubuntu     405 Nov 20 08:19 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    1892 Nov 20 09:11 partner_044_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    6452 Nov 20 09:11 partner_044.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 09:12 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 09:12 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 09:13 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     742 Nov 20 09:18 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    7078 Nov 20 09:15 partner_fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 09:12 partner_honesty.progress
-rw-r--r-- 1 ubuntu ubuntu   70214 Nov 20 09:15 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu  470145 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu  309998 Nov 20 09:12 partner_O_off.log
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 09:12 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:12 partner_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu    4734 Nov 20 09:12 partner_O_off.progress
-rw-r--r-- 1 ubuntu ubuntu  309788 Nov 20 09:12 partner_O_on.log
-rw-r--r-- 1 ubuntu ubuntu     936 Nov 20 09:12 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 09:12 partner_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    4531 Nov 20 09:12 partner_O_on.progress
-rw-r--r-- 1 ubuntu ubuntu     664 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3353 Nov 20 09:18 report_facts.py
-rw-r--r-- 1 ubuntu ubuntu    2543 Nov 20 09:18 report_facts.txt
-rw-r--r-- 1 ubuntu ubuntu    8486 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   18944 Nov 20 08:09 R_positions.epd
-rw-r--r-- 1 ubuntu ubuntu    1323 Nov 20 08:09 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1227 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    8477 Nov 20 08:07 scratch_asan.log
-rw-r--r-- 1 ubuntu ubuntu    1998 Nov 20 08:07 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu       1 Nov 20 08:07 scratch_asan.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 scratch_asan.progress
-rw-r--r-- 1 ubuntu ubuntu   11573 Nov 20 08:08 scratch_asan_report.log
-rw-r--r-- 1 ubuntu ubuntu    1294 Nov 20 08:08 scratch_asan_report.meta
-rw-r--r-- 1 ubuntu ubuntu       1 Nov 20 08:08 scratch_asan_report.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 scratch_asan_report.progress
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     153 Nov 20 09:19 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:05 UCI_OPTIONS_IDEA.txt
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 08:05 UCI_OPTIONS.log
-rw-r--r-- 1 ubuntu ubuntu     158 Nov 20 08:05 UCI_OPTIONS.meta
-rw-r--r-- 1 ubuntu ubuntu    1649 Nov 20 08:04 uci_options.py
```
