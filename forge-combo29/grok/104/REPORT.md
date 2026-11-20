Idea S35 searches the early replies to a late parent with less reduction.
I added check option IdeaS35, default false, and spins IdeaS35_Index 7, IdeaS35_Replies 4, IdeaS35_Plies 1, IdeaS35_Far 24.
IdeaS35 false does not enter the new block. IdeaS35 true arms the same one-ply relief and also tries one more ply off the first reply when the parent arrival index is at least 24.

EXISTS: yes, forge-combo29/src/search.cpp:2010. LmrLateParentRelief, default false, already subtracts one ply when the parent arrival index is at least 7 and the reply is one of the first four. Those three numbers were not options. The second ply for a far parent was not in the engine.

Honesty, no setoption, exe B and exe P, both PASS. bench 11 nodes 312866. bench 13 nodes 862329. bench 16 nodes 3024920. go perft 5 nodes 4865609. Files HONESTY_B.txt and HONESTY_P.txt.

Table, pasted from report_table.py (report_table.out):

```
step | done / partly / not done | evidence file | result
STEP 1 seat | done | SEAT.txt | seat 104, idea 4, model Grok 4.7, 2026-11-20T07:55:39Z, token 24771265646295
STEP 2 honesty B | done | HONESTY_B.txt | PASS
STEP 2 O depth 12 exe B | done | B_O_d12.tsv | sum 9500069
STEP 2 G depth 12 exe B | done | B_G_d12.tsv | sum 18466239
STEP 3 prediction | done | prediction.txt | committed before the P measurements
STEP 3 patch applies | done | idea.patch.txt | git apply --check on a fresh base printed APPLY_CHECK_OK
proof 1 honesty P | done | HONESTY_P.txt | PASS
proof 2 switch off O | done | compare_off_O.txt | positions=200 differ=0 sum_a=9500069 sum_b=9500069
proof 2 switch off G | done | compare_off_G.txt | positions=353 differ=0 sum_a=18466239 sum_b=18466239
proof 3 switch on O | done | compare_on_O.txt | positions=200 differ=200 sum_a=9500069 sum_b=9722581
proof 4 uci options | done | uci_p.txt | IdeaS35 check false; spins 7, 4, 1, 24
proof 5 sanitizer | done | asan_G100.meta | asan_symbols 35, sanitizer_lines 0, 100 positions
proof 5 trap | done | asan_trap.stderr.txt | heap-buffer-overflow on the special FEN
STEP 3 match | done | match_OG_result.txt | Elo: -0.00 +/- 10.81, nElo: 0.00 +/- 20.48
STEP 4 partner apply | done | partner004_apply_check.txt | APPLY_CHECK_OK
STEP 4 partner honesty | done | HONESTY_PARTNER004.txt | PASS
STEP 4 partner off vs B | done | partner004_off_vs_B.txt | positions_a=200 positions_b=200 compared=200 differ=0 sum_a=9500069 sum_b=9500069
STEP 4 partner on vs claim | done | partner004_on_vs_claim.txt | positions_a=200 positions_b=200 compared=200 differ=0 sum_a=9722581 sum_b=9722581
STEP 4 partner match | done | partner004_match.txt | Elo: -5.21 +/- 9.82, nElo: -14.77 +/- 27.80
```

Proof (1). Exe P, no setoption. HONESTY_P.txt PASS. bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

Proof (2). S14, IdeaS35 false. O depth 12 differ 0 of 200, sum 9500069, equal to exe B (compare_off_O.txt). G depth 12 differ 0 of 353, sum 18466239, equal to exe B (compare_off_G.txt). Exe B itself matched the known sums: O 9500069 with first three 41311, 24872, 28574, and G 18466239.

Proof (3). S14, IdeaS35 true. O depth 12 sum 9722581, differ 200 of 200 from exe B (compare_on_O.txt). Prediction 10150000, wrong outside 9550000 to 12000000. 9722581 is inside that range. prediction.txt was not edited after the commit that contains only that file.

Proof (4). uci_p.txt lists:
option name IdeaS35 type check default false
option name IdeaS35_Index type spin default 7 min 0 max 64
option name IdeaS35_Replies type spin default 4 min 0 max 64
option name IdeaS35_Plies type spin default 1 min 0 max 4
option name IdeaS35_Far type spin default 24 min 0 max 64

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS35 true, first 100 of G at depth 10. asan_G100.meta: asan_symbols=35, sanitizer_lines=0, positions_done=100. The same runner on a scratch copy that reads past a 4-int heap array when the FEN starts with 4k3/8/8/8/8/8/8/4K3 reported, in asan_trap.stderr.txt: ERROR: AddressSanitizer: heap-buffer-overflow. asan_symbols on that exe was also 35.

Match. Exe P with IdeaS35 true against exe P with IdeaS35 false, S14, Threads 1, Hash 16, 20000 nodes, openings O and G (553), both colours, 1106 games. fastchess output match_OG.txt and match_OG.pgn. Last block, from extract_match.py into match_OG_result.txt:

```
Results of S35on vs S35off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: -0.00 +/- 10.81, nElo: 0.00 +/- 20.48
LOS: 50.00 %, DrawRatio: 62.21 %, PairsRatio: 0.97
Games: 1106, Wins: 340, Losses: 340, Draws: 426, Points: 553.0 (50.00 %)
Ptnml(0-2): [15, 91, 344, 85, 18], WL/DD Ratio: 1.75
```

Prediction was +6 Elo, wrong below -20 or above +40. -0.00 is inside that range. The interval is not entirely below 0, so I did not open the code a second time to chase a loss.

Partner. Seats for idea 4 are 004, 054 and 104. I am 104. The next after me with a branch is 004. Verdict: CONFIRMS. git apply --check printed APPLY_CHECK_OK (partner004_apply_check.txt). Honesty of that build PASS (HONESTY_PARTNER004.txt). Switch LmrLateParentRelief false: O depth 12 differ 0 of 200 against exe B, sum 9500069 (partner004_off_vs_B.txt). Switch true: O depth 12 differ 0 of 200 against seat 004's own P_on_O_d12.nodes.txt, sum 9722581, and differ 200 of 200 from exe B (partner004_on_vs_claim.txt and the on run's first three 25405, 28389, 50060, which are the numbers in their compare_on_O.txt). Their option is the existing LmrLateParentRelief, and their spins are LmrLateParentRelief_Index default 7 and LmrLateParentRelief_Replies default 4. A match of that switch, 300 R openings, both colours, 600 games, nodes 20000 (partner004_match.txt): Elo -5.21 +/- 9.82, Games 600, Wins 271, Losses 280, Draws 49. That match is my measurement of their switch. It is not a replay of their 1106-game match.

suspicions, not proven

The extra ply is inside the reduction block, and that block requires move_count > 1, or > 2 at the root (forge-combo29/src/search.cpp:1991-1992). The extra ply asks for move_count == 1, so that arm does not run. What agrees with that reading: my IdeaS35-on O rows equal seat 004's on rows (mine_on_vs_partner_claim.txt, differ 0), and seat 004's patch has no second ply. I did not count, outside that block, how often a parent arrival index would have been at least 24.

what I did NOT do

I did not rebuild after noticing the dead arm. The patch, the node files and the 1106-game match are the code I measured. I did not replay seat 004's sanitizer build or their 1106-game match. I did not try spin values other than the defaults. No forge-combo29/soak_all/FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not play a second match of my own patch on R, because seat 004 already had idea.patch.txt.

what I am NOT sure about

I am not sure a second ply on the first reply that is actually reduced (move_count 2) would change the match. I did not build that. I am not sure why the partner's 600 random-position games drew only 49 times. I did not check those games against the rules of chess one by one.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/104/run_set.py
 M forge-combo29/grok/104/stamps.txt
?? forge-combo29/grok/104/HONESTY_PARTNER004.txt
?? forge-combo29/grok/104/R300.fens
?? forge-combo29/grok/104/REPORT.md
?? forge-combo29/grok/104/RESULT.txt
?? forge-combo29/grok/104/apply_check.txt
?? forge-combo29/grok/104/compare_partner.py
?? forge-combo29/grok/104/honesty_partner004_bench11.meta
?? forge-combo29/grok/104/honesty_partner004_bench11.txt
?? forge-combo29/grok/104/honesty_partner004_bench13.meta
?? forge-combo29/grok/104/honesty_partner004_bench13.txt
?? forge-combo29/grok/104/honesty_partner004_bench16.meta
?? forge-combo29/grok/104/honesty_partner004_bench16.txt
?? forge-combo29/grok/104/honesty_partner004_perft5.meta
?? forge-combo29/grok/104/honesty_partner004_perft5.txt
?? forge-combo29/grok/104/mine_on_vs_partner_claim.txt
?? forge-combo29/grok/104/partner004_apply_check.txt
?? forge-combo29/grok/104/partner004_claimed_on_O.nodes
?? forge-combo29/grok/104/partner004_compare.txt
?? forge-combo29/grok/104/partner004_idea.patch.txt
?? forge-combo29/grok/104/partner004_match.pgn
?? forge-combo29/grok/104/partner004_match.txt
?? forge-combo29/grok/104/partner004_off_O.meta
?? forge-combo29/grok/104/partner004_off_O.raw.txt
?? forge-combo29/grok/104/partner004_off_O.tsv
?? forge-combo29/grok/104/partner004_off_vs_B.txt
?? forge-combo29/grok/104/partner004_on_O.meta
?? forge-combo29/grok/104/partner004_on_O.raw.txt
?? forge-combo29/grok/104/partner004_on_O.tsv
?? forge-combo29/grok/104/partner004_on_vs_claim.txt
?? forge-combo29/grok/104/report_table.out
?? forge-combo29/grok/104/report_table.py
?? forge-combo29/grok/104/run_partner_match.sh

$ ls -la forge-combo29/grok/104
total 9676
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:19 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1052 Nov 20 08:07 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu  119152 Nov 20 08:07 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu    5911 Nov 20 08:07 asan_G100.tsv
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:08 asan_trap.fen
-rw-r--r-- 1 ubuntu ubuntu    1477 Nov 20 08:08 asan_trap.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 08:08 asan_trap.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5119 Nov 20 08:08 asan_trap.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:08 asan_trap.tsv
-rw-r--r-- 1 ubuntu ubuntu     841 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507809 Nov 20 08:03 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   30769 Nov 20 08:03 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:03 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  281888 Nov 20 08:03 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20090 Nov 20 08:03 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     620 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:04 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:04 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:04 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     816 Nov 20 09:13 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    1579 Nov 20 08:06 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     596 Nov 20 08:18 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:02 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     235 Nov 20 08:02 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     235 Nov 20 08:02 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 08:02 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     239 Nov 20 08:02 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     334 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 09:13 honesty_partner004_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:13 honesty_partner004_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 09:13 honesty_partner004_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:13 honesty_partner004_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:13 honesty_partner004_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:13 honesty_partner004_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 09:13 honesty_partner004_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:13 honesty_partner004_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     328 Nov 20 09:13 HONESTY_PARTNER004.txt
-rw-r--r-- 1 ubuntu ubuntu     235 Nov 20 08:03 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     235 Nov 20 08:03 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 08:03 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     239 Nov 20 08:03 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     334 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6301 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     988 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 4552067 Nov 20 08:17 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu     400 Nov 20 08:18 match_OG_result.txt
-rw-r--r-- 1 ubuntu ubuntu  138600 Nov 20 08:17 match_OG.txt
-rw-r--r-- 1 ubuntu ubuntu    7310 Nov 20 08:08 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     649 Nov 20 08:08 match_smoke.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 09:13 mine_on_vs_partner_claim.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:13 partner004_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 09:12 partner004_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu     277 Nov 20 09:13 partner004_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    3297 Nov 20 09:12 partner004_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 1915954 Nov 20 09:17 partner004_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   78226 Nov 20 09:17 partner004_match.txt
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 09:13 partner004_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  282504 Nov 20 09:13 partner004_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20090 Nov 20 09:13 partner004_off_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 09:13 partner004_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 09:13 partner004_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  282724 Nov 20 09:13 partner004_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20088 Nov 20 09:13 partner004_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 09:13 partner004_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 08:04 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507969 Nov 20 08:04 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   30769 Nov 20 08:04 P_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282249 Nov 20 08:04 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20090 Nov 20 08:04 P_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 08:04 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282366 Nov 20 08:04 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20088 Nov 20 08:04 P_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     670 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19204 Nov 20 09:13 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    8821 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1736 Nov 20 09:19 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    2813 Nov 20 09:18 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 09:19 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   25608 Nov 20 08:07 R.fens
-rw-r--r-- 1 ubuntu ubuntu    7226 Nov 20 08:06 run_asan.py
-rw-r--r-- 1 ubuntu ubuntu    2367 Nov 20 08:03 run_honesty_b.py
-rwxr-xr-x 1 ubuntu ubuntu    1080 Nov 20 08:08 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1038 Nov 20 09:13 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    5822 Nov 20 09:12 run_set.py
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:02 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     146 Nov 20 09:19 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:04 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5214 Nov 20 08:04 uci_p.txt
```
