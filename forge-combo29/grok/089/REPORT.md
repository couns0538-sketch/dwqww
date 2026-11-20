Idea 39 is IdeaA8: in quiescence, after N captures that did not raise alpha, skip later captures that are not recaptures, and only when the side to move is not in check.
I built a check option IdeaA8, default false, and a spin IdeaA8_Captures, default 2, minimum 0, maximum 16.
A recapture is a capture onto the square the parent move landed on. A futility skip and a static-exchange skip also count as misses. With IdeaA8 false those branches are not taken.

EXISTS: no. `forge-combo29/src/search.cpp` quiescence already has a futility margin and a static-exchange skip. It does not count misses and it does not drop the remaining non-recaptures.

Honesty, no setoption, fresh process each time. Exe B and exe P and the partner build all printed bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. See HONESTY_B.txt, HONESTY_P.txt, HONESTY_PARTNER.txt.

The table below is the output of `report_table.py` (the TABLE section).

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 089 idea 39
2 honesty B | done | HONESTY_B.txt | info string bench depth 11 nodes 312866 time 166 nps 1884734 ; nodes 4865609
2 base O G | done | B_O_sum.txt | file=B_O_d12.txt n=200 sum=9500069 first3=41311/24872/28574 ; file=B_G_d12.txt n=353 sum=18466239 first3=37203/70845/144383
3 prediction | done | prediction.txt | committed before measuring P
3 patch applies | done | idea.patch.txt | git apply --check on the seat tree returned 0 before this report
3 proof off | done | proof_off_O.txt | a=B_O_d12.txt sum=9500069 b=P_off_O_d12.txt sum=9500069 n=200 differ=0 ; a=B_G_d12.txt sum=18466239 b=P_off_G_d12.txt sum=18466239 n=353 differ=0
3 proof on | done | proof_on_O.txt | a=B_O_d12.txt sum=9500069 b=P_on_O_d12.txt sum=9779075 n=200 differ=200
3 uci options | done | uci_P.txt | IdeaA8 check false, IdeaA8_Captures spin 2
3 sanitizer | done | asan_summary.txt | nm_asan_count=35 | g100_stderr_bytes=0 | g100_stderr_empty=True | scratch_has_heap_buffer_overflow=True | scratch_stderr_bytes=5091
3 match | done | match_summary.txt | 1106 games, see match_summary.txt
4 partner | done | partner_on_vs_claim.txt | a=B_O_d12.txt sum=9500069 b=partner_off_O_d12.txt sum=9500069 n=200 differ=0 ; measured=forge-combo29/grok/089/partner_on_O_d12.txt claimed=forge-combo29/grok/089/partner039_on_O.nodes n=200 differ=0 measured_sum=9328352 claimed_sum=9328352
4 partner match | done | partner_match_summary.txt | 600 games
5 report | done | REPORT.md | this file
```

Proof (1). Exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Proof (2). S14, Threads 1, Hash 16, IdeaA8 false. O depth 12 differ 0, sum 9500069. G depth 12 differ 0, sum 18466239. Position by position equal to exe B.

Proof (3). S14 and IdeaA8 true, IdeaA8_Captures left at 2. O depth 12 sum 9779075, differ 200 of 200 against exe B.

Proof (4). `uci` lists `option name IdeaA8 type check default false` and `option name IdeaA8_Captures type spin default 2 min 0 max 16`.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaA8 true, first 100 of G at depth 10: stderr empty (0 bytes). `nm -C` of that exe counted 35 `__asan_` symbols. The same `measure_depth.py` runner on a scratch copy, which reads one past a 4-int heap array only for the two-kings FEN in asan_special.fen, reported `heap-buffer-overflow`.

`git apply --check` of idea.patch.txt on this seat tree exited 0 (apply_check.txt).

Match. IdeaA8 true versus IdeaA8 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games. From match_summary.txt: Elo -12.26 +/- 10.17, 327 wins, 366 losses, 413 draws, points 533.5. The point is not below -20, so I did not open the code for the required second look. The whole interval is below 0.

Prediction in prediction.txt said O depth 12 sum 8200000, wrong outside 6500000 to 9450000. The measured sum is 9779075, so that prediction is wrong. It said Elo -2, wrong below -40 or above +30. -12.26 is inside that band.

Partner is seat 039 (idea 39; 139 has no branch). Verdict: CONFIRMS. Their idea.patch.txt applied with `git apply --check` exit 0 on this seat tree (partner_apply_check.txt) and was built from a fresh base worktree. Honesty numbers match. IdeaA8 false matches exe B on O depth 12, differ 0. IdeaA8 true matches their P_on_O_d12.nodes on all 200 positions (sum 9328352) and differs from exe B on 200 of 200, which is what their RESULT.txt says. I then played their switch on my 300 R openings, both colours, 600 games: Elo -0.00 +/- 12.33, 245 wins, 245 losses, 110 draws. I did not re-run their sanitizer and I did not replay their 1106-game match.

suspicions, not proven. Counting futility skips and static-exchange skips as misses makes N=2 fire early, and that may be why the tree grew (9779075 against 9500069) and why the match is negative. Their patch counts only searched misses and uses N=1, and their O sum fell (9328352). I have not shown which reading is the stronger one.

What I did NOT do. I did not re-run seat 039's sanitizer. I did not replay seat 039's 1106-game match. I did not edit prediction.txt after measuring. I did not change idea.patch.txt after the match. I did not open a pull request. The minute-60 fetch of the handoff branch found no FABLE_TO_grok_<N>.md (minute60.txt).

What I am NOT sure about. I am not sure the node rise is only from missed cutoffs. I am not sure seat 039's patch is stronger than this one; the 600-game R match is Elo 0 with an error of 12.33.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/089/stamps.txt
?? config.json
?? forge-combo29/grok/089/HONESTY_PARTNER.txt
?? forge-combo29/grok/089/REPORT.md
?? forge-combo29/grok/089/RESULT.txt
?? forge-combo29/grok/089/apply_check.txt
?? forge-combo29/grok/089/compare_partner_nodes.py
?? forge-combo29/grok/089/honesty_PARTNER_bench11.meta
?? forge-combo29/grok/089/honesty_PARTNER_bench11.txt
?? forge-combo29/grok/089/honesty_PARTNER_bench13.meta
?? forge-combo29/grok/089/honesty_PARTNER_bench13.txt
?? forge-combo29/grok/089/honesty_PARTNER_bench16.meta
?? forge-combo29/grok/089/honesty_PARTNER_bench16.txt
?? forge-combo29/grok/089/honesty_PARTNER_perft5.meta
?? forge-combo29/grok/089/honesty_PARTNER_perft5.txt
?? forge-combo29/grok/089/minute60.txt
?? forge-combo29/grok/089/partner039_idea.patch.txt
?? forge-combo29/grok/089/partner039_on_O.nodes
?? forge-combo29/grok/089/partner_apply.sh
?? forge-combo29/grok/089/partner_apply_check.txt
?? forge-combo29/grok/089/partner_match.log
?? forge-combo29/grok/089/partner_match.pgn
?? forge-combo29/grok/089/partner_match.sh
?? forge-combo29/grok/089/partner_match_summary.txt
?? forge-combo29/grok/089/partner_off_O_d12.txt
?? forge-combo29/grok/089/partner_off_O_d12.txt.log
?? forge-combo29/grok/089/partner_off_O_d12.txt.meta
?? forge-combo29/grok/089/partner_off_O_d12.txt.stderr
?? forge-combo29/grok/089/partner_off_vs_B.txt
?? forge-combo29/grok/089/partner_on_O_d12.txt
?? forge-combo29/grok/089/partner_on_O_d12.txt.log
?? forge-combo29/grok/089/partner_on_O_d12.txt.meta
?? forge-combo29/grok/089/partner_on_O_d12.txt.stderr
?? forge-combo29/grok/089/partner_on_vs_B.txt
?? forge-combo29/grok/089/partner_on_vs_claim.txt
?? forge-combo29/grok/089/report_table.out
?? forge-combo29/grok/089/report_table.py

$ ls -la forge-combo29/grok/089
total 9060
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu       5 Nov 20 09:17 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    7283 Nov 20 08:05 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu  135595 Nov 20 08:05 asan_G100_d10.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1095 Nov 20 08:08 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 asan_G100_d10.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu     640 Nov 20 08:08 asan_scratch_note.txt
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 08:06 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    6509 Nov 20 08:07 asan_scratch.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1026 Nov 20 08:06 asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5091 Nov 20 08:07 asan_scratch.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     926 Nov 20 08:08 asan_summary.py
-rw-r--r-- 1 ubuntu ubuntu     124 Nov 20 08:08 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   26067 Nov 20 07:59 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  566056 Nov 20 07:59 B_G_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu     994 Nov 20 07:59 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      62 Nov 20 08:01 B_G_sum.txt
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 07:59 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  318344 Nov 20 07:59 B_O_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 07:59 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:01 B_O_sum.txt
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 09:12 compare_partner_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1265 Nov 20 08:03 design.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 07:58 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1794 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     414 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:12 honesty_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 honesty_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:12 honesty_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 honesty_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:12 honesty_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 honesty_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 09:12 honesty_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 honesty_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     417 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:03 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:03 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:04 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 08:04 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     414 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    8051 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1100 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  152065 Nov 20 08:15 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 3621093 Nov 20 08:15 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu    1227 Nov 20 08:08 match_on_off.sh
-rw-r--r-- 1 ubuntu ubuntu     482 Nov 20 08:17 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     373 Nov 20 08:17 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    6592 Nov 20 08:07 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:56 minute60.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    6548 Nov 20 09:11 partner039_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 09:11 partner039_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      11 Nov 20 09:13 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     570 Nov 20 08:46 partner_apply.sh
-rw-r--r-- 1 ubuntu ubuntu   64189 Nov 20 09:16 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 1915289 Nov 20 09:16 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1081 Nov 20 08:17 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     350 Nov 20 09:16 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 09:12 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  318518 Nov 20 09:12 partner_off_O_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1042 Nov 20 09:12 partner_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_off_O_d12.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 09:12 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   17555 Nov 20 09:12 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  318634 Nov 20 09:12 partner_on_O_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1041 Nov 20 09:12 partner_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_on_O_d12.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 09:12 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 09:12 partner_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu   26067 Nov 20 08:04 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  566261 Nov 20 08:04 P_off_G_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1035 Nov 20 08:04 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_G_d12.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:04 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  318439 Nov 20 08:04 P_off_O_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1039 Nov 20 08:04 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_O_d12.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu   17558 Nov 20 08:04 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  318973 Nov 20 08:04 P_on_O_d12.txt.log
-rw-r--r-- 1 ubuntu ubuntu    1038 Nov 20 08:04 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_on_O_d12.txt.stderr
-rw-r--r-- 1 ubuntu ubuntu     570 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:04 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 08:04 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      72 Nov 20 08:04 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    7393 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4234 Nov 20 09:17 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    3259 Nov 20 09:17 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 set_G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu   19916 Nov 20 08:09 set_R.epd
-rw-r--r-- 1 ubuntu ubuntu     254 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1363 Nov 20 08:01 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     970 Nov 20 08:03 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:04 uci_P.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 08:04 uci_P.txt.meta
```
