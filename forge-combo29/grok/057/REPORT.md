# Seat 057, idea 7, S31

IdeaS31 is a check option, default false. With it on, a null-move cutoff is accepted immediately only when no cheaper enemy piece attacks a dearer piece of ours and the static eval is at least beta plus IdeaS31_Margin (default 80). Otherwise the cutoff is kept only if a reduced re-search with null moves disabled also reaches beta, at every depth. The patch is idea.patch.txt. git apply --check on a fresh tree of 6b98f2170 exited 0 (apply_check.txt).

EXISTS: no. The engine already has NullThreatVerify, default false, which re-searches a threatened cutoff only below depth 14, and re-searches every cutoff at depth 14 or more. That gate is forge-combo29/src/search.cpp:1719 in the base commit. S31 asks for the threat gate at every depth and for quiet high-margin cutoffs to skip the re-search, including those at depth 14 or more. Those fixed numbers were not already the options I added.

Honesty, no setoption, fresh process each line. B and P both: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Baseline exe B, S14, Threads 1, Hash 16: O depth 12 sum 9500069 (first three 41311, 24872, 28574), G depth 12 sum 18466239.

```
step | status | evidence | result
honesty B | done | HONESTY_B.txt | info string bench depth 11 nodes 312866 time 163 nps 1919423 | info string bench depth 13 nodes 862329 time 426 nps 2024246 | info string bench depth 16 nodes 3024920 time 1427 nps 2119775 | nodes 4865609
baseline O G | done | B_O.rows.txt B_G.rows.txt | O n 200 sum 9500069; G n 353 sum 18466239
patch applies | done | apply_check.txt idea.patch.txt | git apply --check exit 0
honesty P | done | HONESTY_P.txt | info string bench depth 11 nodes 312866 time 161 nps 1943267 | info string bench depth 13 nodes 862329 time 439 nps 1964302 | info string bench depth 16 nodes 3024920 time 1417 nps 2134735 | nodes 4865609
proof off O | done | compare_off_O.txt | n 200; sum_a 9500069; sum_b 9500069; differ 0; equal 200
proof off G | done | compare_off_G.txt | n 353; sum_a 18466239; sum_b 18466239; differ 0; equal 353
proof on O | done | compare_on_O.txt | n 200; sum_a 9500069; sum_b 9536516; differ 200; equal 0; sum 9536516
uci options | done | honesty_p_bench11.txt | option name IdeaS31 type check default false | option name IdeaS31_Margin type spin default 80 min 0 max 2000
sanitizer G100 | done | asan_g100.meta asan_g100.stderr.txt | nm_asan_count 35; note completed; stderr bytes 0
sanitizer scratch | done | asan_scratch.stderr.txt asan_scratch.meta | note sanitizer reported
match on vs off | done | match_summary.txt match_on_off.log match_on_off.pgn | Elo: -1.26 +/- 9.89, nElo: -2.60 +/- 20.48
partner 007 | done | partner_007_off_vs_B.txt partner_007_on_vs_theirs.txt partner_007_on_vs_B.txt | off n 200; sum_a 9500069; sum_b 9500069; differ 0; equal 200 | on vs theirs n 200; sum_mine 9501877; sum_theirs 9501877; differ 0; equal 200 | on vs B n 200; sum_a 9500069; sum_b 9501877; differ 147; equal 53
partner R match | done | match_partner_summary.txt | Elo: -0.00 +/- 9.63, nElo: 0.00 +/- 27.80
```

That table is the output of report_table.py, saved as report_table.txt.

Proofs. (1) Honesty of P with no setoption matches the four pins above. (2) IdeaS31 false, S14: O depth 12 differs in 0 of 200 positions from exe B, sum 9500069; G depth 12 differs in 0 of 353, sum 18466239. (3) IdeaS31 true and IdeaS31_Margin 80: O depth 12 differs in 200 of 200 positions, sum 9536516. (4) The uci listing contains `option name IdeaS31 type check default false` and `option name IdeaS31_Margin type spin default 80 min 0 max 2000`. (5) AddressSanitizer and UndefinedBehaviorSanitizer build, nm -C count of __asan_ is 35, IdeaS31 true, first 100 of G at depth 10, stderr empty. The same runner on a scratch copy with one heap read past the end of a 4-int array, triggered by the FEN in scratch.fen, reported: `/tmp/scratch-asan/forge-combo29/src/uci.cpp:47:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'`.

Match. exe P with IdeaS31 true against exe P with IdeaS31 false, both S14, Threads 1, Hash 16, IdeaS31_Margin 80, 20000 nodes, openings O then G (553), both colours, 1106 games, fastchess concurrency 3. From match_summary.txt: Elo -1.26 +/- 9.89, games 1106, wins 345, losses 349, draws 412. Counting the Finished game lines from IdeaS31on's side gives the same 345, 349, and 412. The whole interval is not below 0, and the Elo is not below -20, so I did not open the code for a second look.

Partner. Seats for idea 7 are 007, 057, and 107. 107 had no branch at 09:11 UTC. The next seat after 057 that had a branch was 007. I built commit 403668c3fbc37832af9f8c74fb652a09d62105bd. At 09:11 UTC the branch tip was f43b875151486d34bc15af5e865ac75b1ff056f1. The idea.patch.txt blob and the P_on_O.rows.tsv blob are the same in both commits (ccadafe48cb168694c91fba0b45376a9ef09f1ce and a7038de345ced4f6d355cf648a77863721e120ed). The later commit adds their report. Their patch replaces the constant 14 with the spin NullThreatVerify_Depth, default 14, and their measured switch is NullThreatVerify. Their RESULT.txt says off_identical=yes and on_differs=147 of 200. My harness on a fresh tree: apply --check exit 0, honesty pins unchanged, off differs in 0 of 200 from exe B, on matches their published O rows in 200 of 200 and differs from exe B in 147 of 200. A 300-opening R match, both colours, 600 games, of their switch: Elo -0.00 +/- 9.63, wins 269, losses 269, draws 62, and the Finished game lines give the same 269, 269, and 62. Verdict: CONFIRMS.

prediction.txt was not edited. It said the O depth-12 sum with the switch on would be 12200000, and wrong if below 9600000 or above 20000000. The measured sum is 9536516, which is below 9600000, so that prediction is wrong. It said the match Elo would be -15, and wrong if the interval lay entirely above +25 or entirely below -70. The measured interval is -1.26 +/- 9.89, which does not meet either of those conditions.

suspicions, not proven. The partner R-match block also prints DrawRatio 85.00% and Ptnml(0-2) [2, 23, 255, 13, 7]. Those bins do not add up to 269 wins and 62 draws. I did not find a bug in the game results themselves. I am not sure the depth-14 skip of quiet high-margin cutoffs saves nodes, because every measured search was depth 12, where that old path never runs.

what I did NOT do. I did not search G at depth 12 with IdeaS31 on. I did not try a margin other than 80. I did not replay seat 007's 1106-game OG match. I opened their branch at 08:32 UTC, before minute 75, and fetched it again at 09:11 UTC. The patch bytes had not changed. Seat 107 had no branch. At 08:36 UTC and again at 09:11 UTC the handoff branch had no FABLE_TO_grok file.

what I am NOT sure about. The margin uses the corrected static eval minus beta, not the eval after a transposition-table adjustment. I am not sure that is the margin the idea text meant. I am not sure why fastchess printed a draw ratio of 85% beside 62 draws.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/057/HONESTY_B.txt
 M forge-combo29/grok/057/honesty_b_bench11.txt
 M forge-combo29/grok/057/honesty_b_bench13.txt
 M forge-combo29/grok/057/honesty_b_bench16.txt
 M forge-combo29/grok/057/stamps.txt
?? forge-combo29/grok/057/REPORT.md
?? forge-combo29/grok/057/RESULT.txt
?? forge-combo29/grok/057/compare_partner_on.py
?? forge-combo29/grok/057/config.json
?? forge-combo29/grok/057/honesty_any.py
?? forge-combo29/grok/057/match_partner.log
?? forge-combo29/grok/057/match_partner.pgn
?? forge-combo29/grok/057/match_partner.sh
?? forge-combo29/grok/057/match_partner_summary.txt
?? forge-combo29/grok/057/partner_007_P_on_O.rows.tsv
?? forge-combo29/grok/057/partner_007_apply_check.txt
?? forge-combo29/grok/057/partner_007_commit.txt
?? forge-combo29/grok/057/partner_007_honesty.txt
?? forge-combo29/grok/057/partner_007_honesty_bench11.meta
?? forge-combo29/grok/057/partner_007_honesty_bench11.txt
?? forge-combo29/grok/057/partner_007_honesty_bench13.meta
?? forge-combo29/grok/057/partner_007_honesty_bench13.txt
?? forge-combo29/grok/057/partner_007_honesty_bench16.meta
?? forge-combo29/grok/057/partner_007_honesty_bench16.txt
?? forge-combo29/grok/057/partner_007_honesty_perft5.meta
?? forge-combo29/grok/057/partner_007_honesty_perft5.txt
?? forge-combo29/grok/057/partner_007_idea.patch.txt
?? forge-combo29/grok/057/partner_007_off_O.meta
?? forge-combo29/grok/057/partner_007_off_O.raw.txt
?? forge-combo29/grok/057/partner_007_off_O.rows.txt
?? forge-combo29/grok/057/partner_007_off_vs_B.txt
?? forge-combo29/grok/057/partner_007_on_O.meta
?? forge-combo29/grok/057/partner_007_on_O.raw.txt
?? forge-combo29/grok/057/partner_007_on_O.rows.txt
?? forge-combo29/grok/057/partner_007_on_vs_B.txt
?? forge-combo29/grok/057/partner_007_on_vs_theirs.txt
?? forge-combo29/grok/057/report_table.py
?? forge-combo29/grok/057/report_table.txt
```

ls -la

```
total 8536
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:11 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:23 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     926 Nov 20 08:25 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  118885 Nov 20 08:25 asan_g100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7417 Nov 20 08:25 asan_g100.rows.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:25 asan_g100.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu    3671 Nov 20 08:25 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:25 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    5185 Nov 20 08:25 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:25 asan_scratch.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    1155 Nov 20 08:25 asan_scratch.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     820 Nov 20 08:06 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu  502261 Nov 20 08:06 B_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   26513 Nov 20 08:06 B_G.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     819 Nov 20 08:06 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu  276649 Nov 20 08:06 B_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17646 Nov 20 08:06 B_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:23 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:23 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:23 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     857 Nov 20 08:32 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu     798 Nov 20 08:21 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7169 Nov 20 08:35 config.json
-rw-r--r-- 1 ubuntu ubuntu    1194 Nov 20 08:25 design.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 G.epd
-rw-r--r-- 1 ubuntu ubuntu    1778 Nov 20 08:32 honesty_any.py
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:20 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:20 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:20 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:20 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:20 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:20 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     242 Nov 20 08:20 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:20 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1862 Nov 20 08:05 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu   20402 Nov 20 08:20 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:21 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:21 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:21 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:21 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:21 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 08:21 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     242 Nov 20 08:21 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:21 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1872 Nov 20 08:21 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu   20834 Nov 20 08:21 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    9888 Nov 20 08:20 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1509 Nov 20 08:18 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  136659 Nov 20 08:30 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 3645309 Nov 20 08:30 match_on_off.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1248 Nov 20 08:23 match_on_off.sh
-rw-r--r-- 1 ubuntu ubuntu   67609 Nov 20 08:35 match_partner.log
-rw-r--r-- 1 ubuntu ubuntu 1629377 Nov 20 08:35 match_partner.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1271 Nov 20 08:32 match_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     351 Nov 20 08:36 match_partner_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     372 Nov 20 08:31 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     354 Nov 20 08:31 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:23 OG.epd
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 08:32 partner_007_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 08:32 partner_007_commit.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:32 partner_007_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5063 Nov 20 08:32 partner_007_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:32 partner_007_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5063 Nov 20 08:32 partner_007_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:32 partner_007_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5065 Nov 20 08:32 partner_007_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     240 Nov 20 08:32 partner_007_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5284 Nov 20 08:32 partner_007_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   20676 Nov 20 08:32 partner_007_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu    3787 Nov 20 08:32 partner_007_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:32 partner_007_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  276655 Nov 20 08:32 partner_007_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17646 Nov 20 08:32 partner_007_off_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:32 partner_007_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     907 Nov 20 08:32 partner_007_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  276699 Nov 20 08:32 partner_007_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17646 Nov 20 08:32 partner_007_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu      54 Nov 20 08:36 partner_007_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:32 partner_007_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:32 partner_007_P_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     855 Nov 20 08:21 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu  502370 Nov 20 08:21 P_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   26513 Nov 20 08:21 P_off_G.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     854 Nov 20 08:21 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  276677 Nov 20 08:21 P_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17646 Nov 20 08:21 P_off_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 08:21 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  276694 Nov 20 08:21 P_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17645 Nov 20 08:21 P_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     680 Nov 20 08:19 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19624 Nov 20 08:31 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    7090 Nov 20 09:12 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3302 Nov 20 08:37 report_table.py
-rw-r--r-- 1 ubuntu ubuntu    1882 Nov 20 08:37 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:38 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   20002 Nov 20 08:18 R.fens
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 08:24 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:11 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    4485 Nov 20 08:21 suite_depth.py
-rw-r--r-- 1 ubuntu ubuntu    2803 Nov 20 08:05 uci_run.py
```
