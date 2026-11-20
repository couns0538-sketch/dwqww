Idea 34, IdeaA3: a checking move is extended only when its static exchange is not losing.
The plain engine already does that, so the patch adds IdeaA3 (check, default false), IdeaA3_Threshold (spin, default 0), and IdeaA3_Extension (spin, default 1).
Off keeps the original gate. On uses the two spins. Both defaults are today's numbers, so the switch at its defaults does not change the search.

EXISTS: forge-combo29/src/search.cpp:1955
CheckExtensionDepth is already a spin (default 2). The SEE floor 0 and the one-ply extension were fixed numbers. They are now IdeaA3_Threshold and IdeaA3_Extension.

Honesty, no setoption, exe B and exe P, from HONESTY_B.txt and P_HONESTY.txt:
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. All four match on both builds.

step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 084 idea 34
STEP 2 honesty B | done | HONESTY_B.txt | ok bench11, bench13, bench16, perft5
STEP 2 O depth 12 | done | B_O.txt | sum 9500069 first 41311 24872 28574 n 200
STEP 2 G depth 12 | done | B_G.txt | sum 18466239 first 37203 70845 144383 n 353
3c patch applies | done | apply_check.txt idea.patch.txt | APPLY_EXIT:0
3d (1) honesty P | done | P_HONESTY.txt | ok bench11, bench13, bench16, perft5
3d (2) off O | done | cmp_off_O.txt | differ 0 of 200
3d (2) off G | done | cmp_off_G.txt | differ 0 of 353
3d (3) on O defaults | done | cmp_on_O.txt | differ 0 of 200
3d (3) on Extension 0 | done | cmp_on_ext0_O.txt | differ 200 of 200
3d (4) uci options | done | P_uci.txt | IdeaA3 false, Threshold 0, Extension 1
3d (5) asan clean | done | asan_clean_count.txt P_asan_G100.meta | sanitizer_lines 0
3d (5) asan can report | done | scratch_sanitizer.txt | sanitizer_lines 3 heap-buffer-overflow
3e match | done | match_summary.txt pair_moves.txt | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan | openings 553 same_moves 553 differ_moves 0 missing_side 0 games 1106
STEP 4 partner 034 | done | partner034_off_vs_B.txt partner034_on_vs_claim.txt partner034_match_summary.txt | off differ 0 of 200; on differ 0 of 200; Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan

The table above is the output of report_table.py.

Proofs on exe P:
(1) Honesty with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. P_HONESTY.txt.
(2) S14 and IdeaA3 false: O depth 12 differs in 0 of 200 from exe B (both sums 9500069). G depth 12 differs in 0 of 353 (both sums 18466239). cmp_off_O.txt, cmp_off_G.txt.
(3) S14 and IdeaA3 true, spins at default: O depth 12 differs in 0 of 200 from exe B, sum 9500069. That is the predicted sum. The reason is EXISTS: the default floor 0 and extension 1 are the gate already at search.cpp:1955, and see_ge(move, 0) matches the GoodCaptures shortcut on this set. The on branch does run: IdeaA3 true and IdeaA3_Extension 0 differs in 200 of 200, sum 8984130. cmp_on_O.txt, cmp_on_ext0_O.txt.
(4) uci lists `option name IdeaA3 type check default false`, `option name IdeaA3_Threshold type spin default 0 min -2000 max 2000`, `option name IdeaA3_Extension type spin default 1 min 0 max 4`. P_uci.txt.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaA3 true, first 100 of G at depth 10: sanitizer_lines 0. P_asan_G100.meta has `nm_asan_count: 35`. A scratch copy with one heap read past the end of a 4-int array, on the FEN in scratch.fen, built the same way and run through depth_search.py, reported AddressSanitizer heap-buffer-overflow. scratch_sanitizer.txt.

Match: exe P IdeaA3 true versus exe P IdeaA3 false, S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess: Elo -0.00 +/- 0.00, Games 1106, Wins 336, Losses 336, Draws 434, Ptnml(0-2) [0, 0, 553, 0, 0]. pair_moves.py grouped by FEN: 553 openings, same_moves 553, differ_moves 0. The equal win and loss counts are the same games with the colours swapped. Prediction of Elo 0 is inside [-10, +10]. match_summary.txt, pair_moves.txt, match.log, match.pgn.

Partner: seat 034 (idea 34; 134 has no branch, so the wrap is 034). git apply --check on a fresh base printed nothing and APPLY_EXIT:0 (partner_apply_check.txt). Honesty of that build matches the four known numbers (partner034_HONESTY.txt). IdeaA3 false versus exe B O depth 12: differ 0 of 200. IdeaA3 true versus seat 034's own O depth-12 rows: differ 0 of 200 (both sums 9500069), which is what 034 claims. Match of 034's switch on 300 R openings, both colours, 600 games: Elo -0.00 +/- 0.00, and pair_moves.py reports same_moves 300. Verdict: CONFIRMS.

suspicions, not proven
fastchess prints nElo and LOS as -nan when every opening pair scores one point. The game results themselves are in the PGN and were counted by parse_match.py.

what I did NOT do
I did not re-run seat 034's IdeaA3_SeeFloor 100 search, and I did not rebuild 034 under a sanitizer.
I did not play the official match with a non-default spin. The required match is the switch at its defaults.
I did not play a second R match of my own patch. Partner 034 already had idea.patch.txt.
I did not fetch fable/50-agent-engine-ideas. Idea 34 is one of ideas 32 to 50, which are specified in the brief.

what I am NOT sure about
I am not sure seat 034's SeeFloor 100 figure (200 of 200 changed, first three 19960/17388/46301) is right, because I did not search that setting.
make_r.py dropped 0 games before ply 80, so the "games that end are dropped" branch was not exercised. The 300 FENs are non-terminal positions at ply 8, 15, 22, and so on.
I did not measure IdeaA3_Threshold at a value other than 0. Extension 0 is the spin I used to show the on branch runs.

times: see stamps.txt

git status --short and ls -la follow.

```
$ git status --short
 M forge-combo29/grok/084/stamps.txt
?? forge-combo29/grok/084/REPORT.md
?? forge-combo29/grok/084/RESULT.txt
?? forge-combo29/grok/084/parse_partner_log.py
?? forge-combo29/grok/084/partner034.patch.txt
?? forge-combo29/grok/084/partner034_HONESTY.txt
?? forge-combo29/grok/084/partner034_O_on.txt
?? forge-combo29/grok/084/partner034_O_on_rows.txt
?? forge-combo29/grok/084/partner034_bench11.meta
?? forge-combo29/grok/084/partner034_bench11.txt
?? forge-combo29/grok/084/partner034_bench13.meta
?? forge-combo29/grok/084/partner034_bench13.txt
?? forge-combo29/grok/084/partner034_bench16.meta
?? forge-combo29/grok/084/partner034_bench16.txt
?? forge-combo29/grok/084/partner034_match.log
?? forge-combo29/grok/084/partner034_match.pgn
?? forge-combo29/grok/084/partner034_match_summary.txt
?? forge-combo29/grok/084/partner034_off_O.log
?? forge-combo29/grok/084/partner034_off_O.meta
?? forge-combo29/grok/084/partner034_off_O.txt
?? forge-combo29/grok/084/partner034_off_vs_B.txt
?? forge-combo29/grok/084/partner034_on_O.log
?? forge-combo29/grok/084/partner034_on_O.meta
?? forge-combo29/grok/084/partner034_on_O.txt
?? forge-combo29/grok/084/partner034_on_vs_claim.txt
?? forge-combo29/grok/084/partner034_pair_moves.txt
?? forge-combo29/grok/084/partner034_perft5.meta
?? forge-combo29/grok/084/partner034_perft5.txt
?? forge-combo29/grok/084/partner_apply_check.txt
?? forge-combo29/grok/084/partner_match.sh
?? forge-combo29/grok/084/report_table.py

$ ls -la forge-combo29/grok/084
total 10668
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu     537 Nov 20 08:07 append_nm.py
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:12 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 08:08 asan_clean_count.txt
-rw-r--r-- 1 ubuntu ubuntu  508238 Nov 20 08:03 B_G.log
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:03 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:03 B_G.txt
-rw-r--r-- 1 ubuntu ubuntu  282066 Nov 20 08:03 B_O.log
-rw-r--r-- 1 ubuntu ubuntu     847 Nov 20 08:03 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:03 B_O.txt
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:06 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:06 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     347 Nov 20 08:06 cmp_on_ext0_O.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:06 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1251 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     489 Nov 20 08:07 count_sanitizer.py
-rw-r--r-- 1 ubuntu ubuntu    6613 Nov 20 08:02 depth_search.py
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G.epd
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2892 Nov 20 08:01 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2917 Nov 20 08:05 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu    5303 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1412 Nov 20 08:07 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  108066 Nov 20 08:18 match.log
-rw-r--r-- 1 ubuntu ubuntu 4630176 Nov 20 08:18 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     610 Nov 20 08:09 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu   37870 Nov 20 08:09 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     426 Nov 20 08:24 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1184 Nov 20 08:24 pair_moves.py
-rw-r--r-- 1 ubuntu ubuntu      69 Nov 20 08:24 pair_moves.txt
-rw-r--r-- 1 ubuntu ubuntu     732 Nov 20 08:12 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 09:12 parse_partner_log.py
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 09:12 partner034_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 09:12 partner034_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 09:12 partner034_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 09:12 partner034_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 09:12 partner034_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:12 partner034_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 09:12 partner034_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   53417 Nov 20 09:15 partner034_match.log
-rw-r--r-- 1 ubuntu ubuntu 2031706 Nov 20 09:15 partner034_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     422 Nov 20 09:16 partner034_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu  281996 Nov 20 09:12 partner034_off_O.log
-rw-r--r-- 1 ubuntu ubuntu     853 Nov 20 09:12 partner034_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:12 partner034_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 09:12 partner034_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu  282222 Nov 20 09:12 partner034_on_O.log
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 09:12 partner034_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:12 partner034_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 09:12 partner034_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:12 partner034_O_on_rows.txt
-rw-r--r-- 1 ubuntu ubuntu  552731 Nov 20 09:12 partner034_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:16 partner034_pair_moves.txt
-rw-r--r-- 1 ubuntu ubuntu    5342 Nov 20 09:12 partner034.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 09:12 partner034_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5316 Nov 20 09:12 partner034_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 09:12 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1114 Nov 20 08:24 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu  119142 Nov 20 08:07 P_asan_G100.log
-rw-r--r-- 1 ubuntu ubuntu     900 Nov 20 08:08 P_asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    6382 Nov 20 08:07 P_asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:05 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 08:05 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:05 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 08:05 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:05 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 08:05 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:05 P_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu  507616 Nov 20 08:05 P_off_G.log
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:05 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:05 P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu  282042 Nov 20 08:05 P_off_O.log
-rw-r--r-- 1 ubuntu ubuntu     847 Nov 20 08:05 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:05 P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu  280819 Nov 20 08:06 P_on_ext0_O.log
-rw-r--r-- 1 ubuntu ubuntu     920 Nov 20 08:06 P_on_ext0_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15758 Nov 20 08:06 P_on_ext0_O.txt
-rw-r--r-- 1 ubuntu ubuntu  281924 Nov 20 08:05 P_on_O.log
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:05 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:05 P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:05 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5380 Nov 20 08:05 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     543 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:05 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5106 Nov 20 08:05 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7247 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2705 Nov 20 09:17 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19244 Nov 20 08:07 R.fens
-rw-r--r-- 1 ubuntu ubuntu    1123 Nov 20 08:09 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 08:09 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu    9250 Nov 20 08:09 scratch_run.log
-rw-r--r-- 1 ubuntu ubuntu     566 Nov 20 08:09 scratch_sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     285 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1963 Nov 20 08:05 uci_options.py
```
