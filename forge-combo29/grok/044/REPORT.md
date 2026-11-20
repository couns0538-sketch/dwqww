IdeaK5 adds the quiet move's history, divided by IdeaK5_Divisor (default 48), to the quiet futility margin at the low depths the engine already uses for that prune.
The check is off by default. Off adds zero, so the comparison is today's margin. On, positive history prunes less and negative history prunes more.
The same term is added to the QuietExtinction tight margin. S14 leaves QuietExtinction off, so that second site is not in the measured searches.

EXISTS: no. Quiet futility in src/search.cpp did not read history. Capture futility can add history/8, and only when CaptureFutilityBase is above 0. That default is 0, so it is off, and it is not this idea.

Honesty, no setoption, fresh process each line. Plain exe B and patched exe P both printed the known counts. The lines below are the script output.

```
step | status | evidence | result
STEP 1 | done | SEAT.txt stamps.txt | seat 044 idea 44
STEP 2 | done | HONESTY_B.txt B_SUMS.txt | plain engine matches the known sums
STEP 3 proofs | done | P_COMPARE.txt honesty_p_bench11.txt | switch off identical, switch on differs
STEP 3 match | done | match/fastchess.log match/games.pgn | 1106 games
STEP 4 | done | partner_compare.txt partner_match/fastchess.log | partner 094
STEP 5 | done | REPORT.md RESULT.txt | this report
--- honesty B ---
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 439 nps 1964302
info string bench depth 16 nodes 3024920 time 1420 nps 2130225
nodes 4865609
--- honesty P ---
info string bench depth 11 nodes 312866 time 171 nps 1829625
info string bench depth 13 nodes 862329 time 447 nps 1929147
info string bench depth 16 nodes 3024920 time 1566 nps 1931621
nodes 4865609
--- my switch ---
off_O differ 0 of 200 sum 9500069
off_G differ 0 of 353 sum 18466239
on_O differ 200 of 200 sum 9524101
asan_clean_lines 0 nm_asan_count=35
asan_scratch_heap 2
--- my match ---
Results of K5on vs K5off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: 3.14 +/- 10.49, nElo: 6.14 +/- 20.48
LOS: 72.15 %, DrawRatio: 62.75 %, PairsRatio: 1.04
Games: 1106, Wins: 344, Losses: 334, Draws: 428, Points: 558.0 (50.45 %)
Ptnml(0-2): [11, 90, 347, 88, 17], WL/DD Ratio: 1.78
--------------------------------------------------
--- partner ---
partner_off_O differ 0 of 200 sum 9500069
partner_off_G differ 0 of 353 sum 18466239
partner_on_vs_claim differ 0 of 200 sum 9725707
partner_on_vs_B differ 200 of 200
Results of K5on vs K5off (20000 nodes, 1t, 16MB, R.epd):
Elo: 0.58 +/- 9.01, nElo: 1.79 +/- 27.80
LOS: 55.01 %, DrawRatio: 87.00 %, PairsRatio: 1.05
Games: 600, Wins: 272, Losses: 271, Draws: 57, Points: 300.5 (50.08 %)
Ptnml(0-2): [4, 15, 261, 16, 4], WL/DD Ratio: 19.08
--------------------------------------------------
```

That block is the output of `python3 report_table.py`, also saved as report_table.txt.

Proof (1). Patched exe, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Same four counts as exe B.

Proof (2). S14 and IdeaK5 false. O depth 12 differs from exe B in 0 of 200 positions, sum 9500069. G depth 12 differs in 0 of 353, sum 18466239. The first three O rows on exe B are 41311, 24872, 28574.

Proof (3). S14 and IdeaK5 true, divisor left at 48. O depth 12 differs in 200 of 200 positions, sum 9524101, which is 24032 nodes above the off sum. The code runs. prediction.txt said 9100000, wrong outside 7000000..11500000 or if equal to 9500069. 9524101 is inside that range and is not the off sum. prediction.txt was not edited after it was pushed.

Proof (4). `uci` on exe P lists `option name IdeaK5 type check default false` and `option name IdeaK5_Divisor type spin default 48 min 1 max 1024`. Saved in P_uci.txt.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK5 true, first 100 of G at depth 10: 2065630 nodes, no AddressSanitizer line in asan_G100_depth10.raw. The meta line is nm_asan_count=35. A scratch copy with one heap read past the end of a 4-int array, on the FEN `7k/8/8/8/8/8/8/K7 w - - 0 1`, run by the same uci_harness.py, printed `ERROR: AddressSanitizer: heap-buffer-overflow` (the phrase occurs twice in asan_scratch_depth10.raw, the error line and the summary). sanitizer=clean.

The patch is idea.patch.txt. `git apply --check` on a clean checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0. Why these numbers: DECISIONS.txt.

Match. exe P with IdeaK5 true against exe P with IdeaK5 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games, fastchess concurrency 3. Elo of the on side: 3.14 +/- 10.49. Games 1106, wins 344, losses 334, draws 428. The interval is not entirely below 0, and the point is not below -20, so I did not open the code a second time for a bug. prediction.txt said +6 Elo, wrong outside -40..40. 3.14 is inside that range. Whole output: match/fastchess.log and match/games.pgn.

Partner verdict: CONFIRMS. Partner is seat 094 (idea 44; 144 has no branch). Their patch applies with git apply --check. Their honesty counts match. Their switch false matches exe B on O (0 of 200) and on G (0 of 353). Their switch true matches their own O_P_on.nodes on all 200 positions, sum 9725707, and differs from exe B on 200 of 200. Their uci list is IdeaK5 default false, IdeaK5_Divisor default 64, IdeaK5_Depth default 5. My test of their switch, 300 of my R openings, both colours, 600 games: Elo 0.58 +/- 9.01. Their own 1106-game figure, which I did not replay, is Elo -9.74 +/- 9.89 in their match_summary.txt.

suspicions, not proven. The +24032 nodes and +3.14 Elo can both be noise; the match interval crosses 0. The R match drew 87 percent, so 0.58 Elo there is a weak signal. I did not measure the QuietExtinction margin because that option stays off.

what I did NOT do. I did not replay seat 094's 1106-game match. I did not build their binary under a sanitizer. I did not try any IdeaK5_Divisor except 48. I did not run G depth 12 with my switch on. I did not play my patch against theirs.

what I am NOT sure about. I am not sure 48 is a better divisor than their 64 with a depth cap of 5. I am not sure the first R sample should have been ply 8 instead of ply 15. No generated game ended before ply 80, so the "drop a finished game" rule was not exercised. I did not recompute fastchess's error bar.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/044/stamps.txt
?? config.json
?? forge-combo29/grok/044/REPORT.md
?? forge-combo29/grok/044/RESULT.txt
?? forge-combo29/grok/044/partner094_O_on.nodes
?? forge-combo29/grok/044/partner094_idea.patch.txt
?? forge-combo29/grok/044/partner_compare.txt
?? forge-combo29/grok/044/partner_honesty_bench11.meta
?? forge-combo29/grok/044/partner_honesty_bench11.txt
?? forge-combo29/grok/044/partner_honesty_bench13.meta
?? forge-combo29/grok/044/partner_honesty_bench13.txt
?? forge-combo29/grok/044/partner_honesty_bench16.meta
?? forge-combo29/grok/044/partner_honesty_bench16.txt
?? forge-combo29/grok/044/partner_honesty_perft5.meta
?? forge-combo29/grok/044/partner_honesty_perft5.txt
?? forge-combo29/grok/044/partner_match/
?? forge-combo29/grok/044/partner_off_G_depth12.meta
?? forge-combo29/grok/044/partner_off_G_depth12.nodes
?? forge-combo29/grok/044/partner_off_G_depth12.raw
?? forge-combo29/grok/044/partner_off_O_depth12.meta
?? forge-combo29/grok/044/partner_off_O_depth12.nodes
?? forge-combo29/grok/044/partner_off_O_depth12.raw
?? forge-combo29/grok/044/partner_on_O_depth12.meta
?? forge-combo29/grok/044/partner_on_O_depth12.nodes
?? forge-combo29/grok/044/partner_on_O_depth12.raw
?? forge-combo29/grok/044/partner_uci.txt
?? forge-combo29/grok/044/report_table.py
?? forge-combo29/grok/044/report_table.txt

$ ls -la
total 3372
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu    886 Nov 20 08:04 asan_G100_depth10.meta
-rw-r--r-- 1 ubuntu ubuntu    872 Nov 20 08:04 asan_G100_depth10.nodes
-rw-r--r-- 1 ubuntu ubuntu 115451 Nov 20 08:04 asan_G100_depth10.raw
-rw-r--r-- 1 ubuntu ubuntu    879 Nov 20 08:04 asan_scratch_depth10.meta
-rw-r--r-- 1 ubuntu ubuntu   4165 Nov 20 08:04 asan_scratch_depth10.raw
-rw-r--r-- 1 ubuntu ubuntu    828 Nov 20 07:59 B_G_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   3430 Nov 20 07:59 B_G_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 508347 Nov 20 07:59 B_G_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 07:59 B_O_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 07:59 B_O_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 280094 Nov 20 07:59 B_O_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 07:59 B_O_first3_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu     24 Nov 20 07:59 B_O_first3_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu   4089 Nov 20 07:59 B_O_first3_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 07:59 B_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu   1265 Nov 20 08:03 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu   1372 Nov 20 08:03 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    243 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 08:01 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:01 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 08:01 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:01 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 08:01 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:01 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 08:01 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:01 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   6452 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1818 Nov 20 08:06 make_r.py
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:05 match
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:05 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu   4962 Nov 20 09:09 partner094_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1203 Nov 20 09:09 partner094_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    178 Nov 20 09:10 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 09:10 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:10 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 09:10 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:10 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 09:10 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:10 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 09:10 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 09:10 partner_honesty_perft5.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:10 partner_match
-rw-r--r-- 1 ubuntu ubuntu    884 Nov 20 09:10 partner_off_G_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   3430 Nov 20 09:10 partner_off_G_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 508624 Nov 20 09:10 partner_off_G_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    890 Nov 20 09:10 partner_off_O_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 09:10 partner_off_O_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 279926 Nov 20 09:10 partner_off_O_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    889 Nov 20 09:10 partner_on_O_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   1893 Nov 20 09:10 partner_on_O_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 279713 Nov 20 09:10 partner_on_O_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu   5098 Nov 20 09:10 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    373 Nov 20 08:03 P_COMPARE.txt
-rw-r--r-- 1 ubuntu ubuntu    862 Nov 20 08:01 P_off_G_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   3430 Nov 20 08:01 P_off_G_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 508563 Nov 20 08:01 P_off_G_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    868 Nov 20 08:01 P_off_O_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 08:01 P_off_O_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 280081 Nov 20 08:01 P_off_O_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    867 Nov 20 08:01 P_on_O_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu   1892 Nov 20 08:01 P_on_O_depth12.nodes
-rw-r--r-- 1 ubuntu ubuntu 279966 Nov 20 08:01 P_on_O_depth12.raw
-rw-r--r-- 1 ubuntu ubuntu    789 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   5040 Nov 20 08:01 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu  19336 Nov 20 08:06 R.epd
-rw-r--r-- 1 ubuntu ubuntu   7757 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   3718 Nov 20 09:15 report_table.py
-rw-r--r-- 1 ubuntu ubuntu   1941 Nov 20 09:15 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu    186 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    136 Nov 20 08:06 R_meta.txt
-rwxr-xr-x 1 ubuntu ubuntu   1165 Nov 20 08:05 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu     79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    208 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   9780 Nov 20 08:02 uci_harness.py
```
