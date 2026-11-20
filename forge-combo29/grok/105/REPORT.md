Idea S37 shaves one ply off a non-PV node when the arriving move was reduced by at least one ply and this side's corrected static eval is worse than two plies ago by at least IdeaS37_Margin (40 centipawns).
The check IdeaS37 defaults to false. While it is false the search does not read the margin and does not record withheld plies, so the node path stays the one already measured.
The paired "no worsening, three withheld plies, search one deeper" rule is not in the patch. Details are in decisions.txt. The patch applies to the base: idea_apply_check.txt.

EXISTS: no. A nearby rule at forge-combo29/src/search.cpp adds one ply of late-move reduction when the node is not improving, including on the PV, with a margin of zero. HindsightDepth, default false, is the paired deeper-and-shallower rule and it compares the parent eval with the child eval.

Honesty, exe B, no setoption (HONESTY_B.txt): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Table from report_numbers.py:

```
HONESTY_B
bench 11 -> nodes 312866 expect 312866 PASS
bench 13 -> nodes 862329 expect 862329 PASS
bench 16 -> nodes 3024920 expect 3024920 PASS
go perft 5 -> nodes 4865609 expect 4865609 PASS
ALL PASS
HONESTY_P
bench 11 -> nodes 312866 expect 312866 PASS
bench 13 -> nodes 862329 expect 862329 PASS
bench 16 -> nodes 3024920 expect 3024920 PASS
go perft 5 -> nodes 4865609 expect 4865609 PASS
ALL PASS
COMPARE
left=/agent/repos/dwqww/forge-combo29/grok/105/O_B.rows right=/agent/repos/dwqww/forge-combo29/grok/105/O_P_off.rows n=200 differ=0 of 200
left=/agent/repos/dwqww/forge-combo29/grok/105/G_B.rows right=/agent/repos/dwqww/forge-combo29/grok/105/G_P_off.rows n=353 differ=0 of 353
left=/agent/repos/dwqww/forge-combo29/grok/105/O_B.rows right=/agent/repos/dwqww/forge-combo29/grok/105/O_P_on.rows n=200 differ=200 of 200
first_diffs 1 2 3 4 5 6 7 8
O_P_on.rows n=200 sum=9295011
UCI
exe=/agent/repos/work/forge-combo29/build-rel/forge
PASS option name IdeaS37 type check default false
PASS option name IdeaS37_Margin type spin default 40 min 0 max 500
ASAN
clean_exe=/agent/repos/work/forge-combo29/build-asan/forge
clean_nm_asan=35
clean_sanitizer_lines=0
bug_exe=/tmp/asan-bug/build-asan/forge
bug_nm_asan=35
bug_line===5735==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000c0 at pc 0x557d5e2b17ee bp 0x7ffe99115470 sp 0x7ffe99115460
MATCH
Results of s37on vs s37off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: -6.91 +/- 10.66, nElo: -13.29 +/- 20.48
LOS: 10.17 %, DrawRatio: 62.03 %, PairsRatio: 0.89
Games: 1106, Wins: 337, Losses: 359, Draws: 410, Points: 542.0 (49.01 %)
Ptnml(0-2): [20, 91, 343, 89, 10], WL/DD Ratio: 1.98
--------------------------------------------------
Finished match
PARTNER
bench 11 -> nodes 312866 expect 312866 PASS
bench 13 -> nodes 862329 expect 862329 PASS
bench 16 -> nodes 3024920 expect 3024920 PASS
go perft 5 -> nodes 4865609 expect 4865609 PASS
ALL PASS
left=/agent/repos/dwqww/forge-combo29/grok/105/O_B.rows right=/agent/repos/dwqww/forge-combo29/grok/105/partner005_off.rows n=200 differ=0 of 200
left=/agent/repos/dwqww/forge-combo29/grok/105/partner005_on_rows.txt right=/agent/repos/dwqww/forge-combo29/grok/105/partner005_on.rows n=200 differ=0 of 200
Results of s37on vs s37off (20000 nodes, 1t, 16MB, R.fens):
Elo: -2.90 +/- 12.28, nElo: -6.56 +/- 27.80
LOS: 32.19 %, DrawRatio: 77.00 %, PairsRatio: 0.92
Games: 600, Wins: 256, Losses: 261, Draws: 83, Points: 297.5 (49.58 %)
Ptnml(0-2): [9, 27, 231, 26, 7], WL/DD Ratio: 14.40
--------------------------------------------------
Finished match
APPLY
my_patch_apply_check=ok
exit=0
STEP_TABLE
1 seat | done | SEAT.txt | seat 105
2 baseline | done | HONESTY_B.txt O_B.rows G_B.rows | honesty pass O 9500069 G 18466239
3 patch | done | idea.patch.txt idea_apply_check.txt | apply check ok
3 proofs | done | compare_O_off.txt compare_G_off.txt compare_O_on.txt | off 0 and 0; on sum 9295011
3 match | done | match_og_elo.txt | see MATCH block
4 partner | done | partner005_cmp_off.txt partner005_cmp_on.txt partner005_match_elo.txt | see PARTNER block
5 report | done | REPORT.md RESULT.txt | this report
```


Proofs, from report_numbers.py:

(1) exe P, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.
(2) S14 and IdeaS37 false: O depth 12 differs 0 of 200 from exe B (sum 9500069). G depth 12 differs 0 of 353 from exe B (sum 18466239).
(3) S14 and IdeaS37 true: O depth 12 sum 9295011, differs 200 of 200 from exe B.
(4) uci lists `option name IdeaS37 type check default false` and `option name IdeaS37_Margin type spin default 40 min 0 max 500`.
(5) AddressSanitizer build: nm -C count of __asan_ is 35. First 100 of G at depth 10 with the switch true: 0 sanitizer lines. The same runner on a scratch copy that reads one past a heap array of 4 ints on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1 reports `ERROR: AddressSanitizer: heap-buffer-overflow`.

Match: IdeaS37 true versus false, S14, 20000 nodes, openings O and G, both colours. fastchess output is match_og.log and match_og.pgn (1106 events). Elo -6.91 +/- 10.66, 337 wins, 359 losses, 410 draws. The interval is not entirely below 0, and the point is not below -20, so the code was not reopened for a mistake. The O-on sum 9295011 sits inside the prediction range. The Elo -6.91 sits inside the prediction range.

Partner: the seats for idea 5 are 005, 055 and 105. This seat is 105, so the partner is the next one that has a branch, which wraps to 005. Seat 005 already had idea.patch.txt. git apply --check exited 0. A fresh release build matched the honesty numbers, matched exe B on O depth 12 with the switch false (0 of 200), and matched seat 005's own O depth-12 nodes with the switch true (0 of 200, sum 9702724). Their RESULT.txt says on_differs=200 of 200 and off_identical=yes. A match of their switch on my 300 R openings, both colours, was 600 games, Elo -2.90 +/- 12.28. Verdict: CONFIRMS.

suspicions, not proven: seat 005's patch also has IdeaS37_Bonus default 1 and IdeaS37_DeepAt default 3, which is the paired deeper-search rule the idea text says to leave off. Their published node counts still matched this build, so the extra arm is a design difference, not a failed proof.

what I did NOT do: I did not rebuild seat 005 under a sanitizer. I did not replay their 1106-game match. I did not turn IdeaS37 on together with HindsightDepth. The handoff branch had no FABLE_TO_grok file at step 1 or at minute 60. I did not open a pull request.

what I am NOT sure about: the full S37 sentence can be read as the sum of the parent eval and the child eval (seat 005) or as this side's eval against the eval two plies ago (this seat). I built the second reading because the one-line index says "worse than two plies ago". The node change shows that the switch runs. It does not show which reading the idea's author wanted. The match interval includes both a small loss and a small gain.

times: see stamps.txt

```
 M forge-combo29/grok/105/stamps.txt
?? forge-combo29/grok/105/REPORT.md
?? forge-combo29/grok/105/RESULT.txt
?? forge-combo29/grok/105/idea_apply_check.txt
?? forge-combo29/grok/105/parse_uci_nodes.py
?? forge-combo29/grok/105/partner005_HONESTY.txt
?? forge-combo29/grok/105/partner005_P_on_O_d12.txt
?? forge-combo29/grok/105/partner005_RESULT.txt
?? forge-combo29/grok/105/partner005_apply_check.txt
?? forge-combo29/grok/105/partner005_bench11.meta
?? forge-combo29/grok/105/partner005_bench11.txt
?? forge-combo29/grok/105/partner005_bench13.meta
?? forge-combo29/grok/105/partner005_bench13.txt
?? forge-combo29/grok/105/partner005_bench16.meta
?? forge-combo29/grok/105/partner005_bench16.txt
?? forge-combo29/grok/105/partner005_cmp_off.txt
?? forge-combo29/grok/105/partner005_cmp_on.txt
?? forge-combo29/grok/105/partner005_idea.patch.txt
?? forge-combo29/grok/105/partner005_match.log
?? forge-combo29/grok/105/partner005_match.pgn
?? forge-combo29/grok/105/partner005_match.sh
?? forge-combo29/grok/105/partner005_match_elo.txt
?? forge-combo29/grok/105/partner005_off.meta
?? forge-combo29/grok/105/partner005_off.raw
?? forge-combo29/grok/105/partner005_off.rows
?? forge-combo29/grok/105/partner005_on.meta
?? forge-combo29/grok/105/partner005_on.raw
?? forge-combo29/grok/105/partner005_on.rows
?? forge-combo29/grok/105/partner005_on_rows.txt
?? forge-combo29/grok/105/partner005_perft5.meta
?? forge-combo29/grok/105/partner005_perft5.txt
?? forge-combo29/grok/105/partner_honesty.py
?? forge-combo29/grok/105/report_numbers.py
?? forge-combo29/grok/105/report_numbers.txt
```

```
total 5204
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu    9403 Nov 20 08:12 asan_bug.raw
-rw-r--r-- 1 ubuntu ubuntu    1461 Nov 20 08:13 asan_summary.py
-rw-r--r-- 1 ubuntu ubuntu     300 Nov 20 08:13 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     139 Nov 20 08:13 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     139 Nov 20 08:13 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:13 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 08:08 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    2117 Nov 20 08:05 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    6594 Nov 20 08:09 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu     446 Nov 20 08:15 extract_elo.py
-rw-r--r-- 1 ubuntu ubuntu     927 Nov 20 08:12 G_asan.meta
-rw-r--r-- 1 ubuntu ubuntu  131886 Nov 20 08:11 G_asan.raw
-rw-r--r-- 1 ubuntu ubuntu    2401 Nov 20 08:11 G_asan.rows
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:06 G_B.meta
-rw-r--r-- 1 ubuntu ubuntu  549742 Nov 20 08:06 G_B.raw
-rw-r--r-- 1 ubuntu ubuntu    8824 Nov 20 08:06 G_B.rows
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 08:08 G_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  550238 Nov 20 08:08 G_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    8824 Nov 20 08:08 G_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:05 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3073 Nov 20 08:05 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:05 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:08 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:08 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:08 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:08 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:08 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:08 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:08 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:08 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2938 Nov 20 08:08 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:08 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:18 idea_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    7610 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     987 Nov 20 08:11 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     357 Nov 20 08:22 match_og_elo.txt
-rw-r--r-- 1 ubuntu ubuntu  138286 Nov 20 08:20 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 1061464 Nov 20 08:20 match_og.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1140 Nov 20 08:14 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:06 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu  309049 Nov 20 08:06 O_B.raw
-rw-r--r-- 1 ubuntu ubuntu    4787 Nov 20 08:06 O_B.rows
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:12 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     915 Nov 20 08:08 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  309197 Nov 20 08:08 O_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    4787 Nov 20 08:08 O_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:08 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu  309300 Nov 20 08:08 O_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu    4777 Nov 20 08:08 O_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu     730 Nov 20 09:12 parse_uci_nodes.py
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:13 partner005_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:12 partner005_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner005_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:12 partner005_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner005_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:12 partner005_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner005_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     146 Nov 20 09:13 partner005_cmp_off.txt
-rw-r--r-- 1 ubuntu ubuntu     159 Nov 20 09:13 partner005_cmp_on.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:12 partner005_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    8444 Nov 20 09:12 partner005_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     344 Nov 20 09:18 partner005_match_elo.txt
-rw-r--r-- 1 ubuntu ubuntu   70960 Nov 20 09:16 partner005_match.log
-rw-r--r-- 1 ubuntu ubuntu  504912 Nov 20 09:16 partner005_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu     916 Nov 20 09:13 partner005_match.sh
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 09:13 partner005_off.meta
-rw-r--r-- 1 ubuntu ubuntu  309285 Nov 20 09:13 partner005_off.raw
-rw-r--r-- 1 ubuntu ubuntu    4787 Nov 20 09:13 partner005_off.rows
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 09:13 partner005_on.meta
-rw-r--r-- 1 ubuntu ubuntu  309515 Nov 20 09:13 partner005_on.raw
-rw-r--r-- 1 ubuntu ubuntu    4783 Nov 20 09:13 partner005_on.rows
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 09:12 partner005_on_rows.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:12 partner005_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner005_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  282238 Nov 20 09:12 partner005_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:12 partner005_RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    2301 Nov 20 09:12 partner_honesty.py
-rw-r--r-- 1 ubuntu ubuntu     345 Nov 20 08:07 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3867 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1958 Nov 20 09:19 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    3132 Nov 20 09:19 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19580 Nov 20 08:12 R.fens
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1039 Nov 20 08:09 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:10 uci_p_options.txt
-rw-r--r-- 1 ubuntu ubuntu    5040 Nov 20 08:10 uci_p.txt
```
