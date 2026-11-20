# Seat 095, idea 45, IdeaK6

A quiet move that gives check is ordered before the other quiet moves.
I added check option IdeaK6, default false, and spin IdeaK6_Band, default 200000.
When the check is on, generate_quiets adds that band to every quiet for which gives_check is true, so direct and discovered checks sort before the other quiets. Killers stay in their earlier stage.

EXISTS: no. The plain engine adds 12000 only for a direct check, in QuietScorer::score in forge-combo29/src/search.cpp. History can outrank that bonus, and a discovered check gets none of it.

## Honesty numbers

Exe B and exe P, no setoption. Pasted from report_tables.txt, which print_report_tables.py wrote by reading the raw files.

bench 11 nodes 312866. bench 13 nodes 862329. bench 16 nodes 3024920. go perft 5 nodes 4865609. Both builds match. Base S14 sums: O depth 12 = 9500069, first three 41311 24872 28574. G depth 12 = 18466239.

## Step table

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 095 idea 45
2 builds and honesty | done | HONESTY_B.txt B_known_sums.txt | honesty True base sums True
3 idea proofs | done | HONESTY_P.txt cmp_off_O.txt cmp_off_G.txt cmp_on_O.txt asan_summary.txt uci_options_ideak6.txt | off_o True off_g True on_differs_200 True asan_clean True poison_reported True
3e test match | done | match_og.log match_og.pgn match_result.txt | games_1106 True
4 partner | done | partner_cmp_off_O.txt partner_cmp_on_rows.txt partner_match_R.log | off_identical True on_rows_equal True
5 report | done | REPORT.md RESULT.txt | this report
```

## Proofs

(1) Honesty of exe P, no setoption: 312866, 862329, 3024920, 4865609. HONESTY_P.txt ALL_MATCH True.

(2) S14 and IdeaK6 false. O depth 12: DIFFER 0, SAME 200, sum 9500069, equal to exe B. G depth 12: DIFFER 0, SAME 353, sum 18466239, equal to exe B.

(3) S14 and IdeaK6 true. O depth 12 sum 9781037. DIFFER 200 of 200 against exe B. The code runs on every position in the set.

(4) uci lists `option name IdeaK6 type check default false` and `option name IdeaK6_Band type spin default 200000 min 0 max 1000000`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK6 true, first 100 of G at depth 10: CLEAN_SANITIZER_LINES 0. asan_G100_d10.meta has asan_symbols=35. The same runner on a scratch build that reads one past a 4-int heap array on the special FEN reports `/tmp/forge-poison-src/src/uci.cpp:47:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'`.

git apply --check of idea.patch.txt on a fresh base tree succeeded.

## Match

IdeaK6 on versus IdeaK6 off, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours.

```
Results of IdeaK6_on vs IdeaK6_off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -4.08 +/- 10.21, nElo: -8.19 +/- 20.48
Games: 1106, Wins: 323, Losses: 336, Draws: 447, Points: 546.5 (49.41 %)
PGN_EVENTS 1106
PGN_RESULTS 1106
```

The interval includes 0 and is not entirely below 0, and the point is not below -20, so I did not open the code again for a mistake hunt.

Prediction, left as committed: O sum 9100000, wrong outside 8000000 to 10500000. Measured 9781037, inside that range. Elo +4, wrong below -30 or above +45. Measured -4.08, inside that range.

## Partner

Partner is seat 045, commit 1f4a45f2025a57e289dfbf4d6083295ebcbd42e1. Verdict: CONFIRMS.

Their patch applies with git apply --check. Honesty numbers match. IdeaK6 false: O DIFFER 0 of 200 and G DIFFER 0 of 353 against exe B, as they claim. IdeaK6 true: my O rows equal their published rows, DIFFER 0, SAME 200, sum 9705311, and DIFFER 200 of 200 against exe B, as they claim. The assigned R match of their switch, 300 openings and both colours, is 600 games, Elo 1.74 +/- 9.01. I did not replay their 1106-game OG match. Their published OG result was -0.31 +/- 9.99, a different book from the R match.

## Suspicions, not proven

The existing +12000 direct-check bonus already puts most checks near the front, so a hard band may add little strength. Both matches sit inside a few elo of zero, which fits that and does not prove it.

The O node sum rose (9781037 against 9500069) where I had expected a drop. A check that does not cut off is now searched earlier, at a fuller depth. I did not separate those nodes from the cutoff saves.

## What I did NOT do

I did not replay the partner's 1106-game match. I did not run a sanitizer on the partner binary. I did not try IdeaK6_Band at any value except the default 200000. I did not put the band on evasion quiets in my patch. The partner did, and that is why their on-sum is 9705311 and mine is 9781037. I did not play a second R match of my own patch.

## What I am NOT sure about

I am not sure the band belongs only on the quiet list. Leaving it off evasions keeps captures in front, and their patch keeps evasion captures in front too because 200000 is below the capture scores. The elo difference between those two placements was not measured on one book.

I am not sure a negative elo this small is a real loss. -4.08 +/- 10.21 includes a small gain.

## times: see stamps.txt

## Script output

The block below is the full output of print_report_tables.py.

```
HONESTY_B
exe_b=/agent/repos/base/forge-combo29/build/forge
--- meta bench11 ---
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=id name Chess Engine Forge 6.4.24 candidate
options_sent=none
command=bench 11
started=2026-11-20T07:59:16Z
--- meta bench13 ---
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=id name Chess Engine Forge 6.4.24 candidate
options_sent=none
command=bench 13
started=2026-11-20T07:59:16Z
--- meta bench16 ---
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=id name Chess Engine Forge 6.4.24 candidate
options_sent=none
command=bench 16
started=2026-11-20T07:59:18Z
--- meta perft5 ---
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=id name Chess Engine Forge 6.4.24 candidate
options_sent=none
command=go perft 5
started=2026-11-20T07:59:18Z
COMMAND bench 11
LINE info string bench depth 11 nodes 312866 time 168 nps 1862297
GOT 312866
EXPECT 312866
MATCH True
COMMAND bench 13
LINE info string bench depth 13 nodes 862329 time 439 nps 1964302
GOT 862329
EXPECT 862329
MATCH True
COMMAND bench 16
LINE info string bench depth 16 nodes 3024920 time 1442 nps 2097725
GOT 3024920
EXPECT 3024920
MATCH True
COMMAND go perft 5
LINE nodes 4865609
GOT 4865609
EXPECT 4865609
MATCH True
ALL_MATCH True
HONESTY_P
bench11 GOT 312866 EXPECT 312866 MATCH True LINE info string bench depth 11 nodes 312866 time 165 nps 1896157
bench13 GOT 862329 EXPECT 862329 MATCH True LINE info string bench depth 13 nodes 862329 time 444 nps 1942182
bench16 GOT 3024920 EXPECT 3024920 MATCH True LINE info string bench depth 16 nodes 3024920 time 1434 nps 2109428
perft5 GOT 4865609 EXPECT 4865609 MATCH True LINE nodes 4865609
ALL_MATCH True
BASE_SUMS
O_POSITIONS 200
O_SUM 9500069
O_FIRST3 41311 24872 28574
O_EXPECT_SUM 9500069
O_EXPECT_FIRST3 41311 24872 28574
O_MATCH True
G_POSITIONS 353
G_SUM 18466239
G_EXPECT_SUM 18466239
G_MATCH True
UCI
option name IdeaK6 type check default false
option name IdeaK6_Band type spin default 200000 min 0 max 1000000
CMP_OFF_O
LEFT forge-combo29/grok/095/B_O_d12.tsv N 200 SUM 9500069
RIGHT forge-combo29/grok/095/P_off_O_d12.tsv N 200 SUM 9500069
COMPARED 200
DIFFER 0
SAME 200
CMP_OFF_G
LEFT forge-combo29/grok/095/B_G_d12.tsv N 353 SUM 18466239
RIGHT forge-combo29/grok/095/P_off_G_d12.tsv N 353 SUM 18466239
COMPARED 353
DIFFER 0
SAME 353
CMP_ON_O
LEFT forge-combo29/grok/095/B_O_d12.tsv N 200 SUM 9500069
RIGHT forge-combo29/grok/095/P_on_O_d12.tsv N 200 SUM 9781037
COMPARED 200
DIFFER 200
SAME 0
ON_O_POSITIONS 200
ON_O_SUM 9781037
ASAN
CLEAN_SANITIZER_LINES 0
asan_symbols=35
POISON_LINE /tmp/forge-poison-src/src/uci.cpp:47:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
MATCH
Results of IdeaK6_on vs IdeaK6_off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -4.08 +/- 10.21, nElo: -8.19 +/- 20.48
Games: 1106, Wins: 323, Losses: 336, Draws: 447, Points: 546.5 (49.41 %)
PGN_EVENTS 1106
PGN_RESULTS 1106
PARTNER
partner_commit 1f4a45f2025a57e289dfbf4d6083295ebcbd42e1
partner_cmp_off_O.txt
LEFT forge-combo29/grok/095/B_O_d12.tsv N 200 SUM 9500069
RIGHT forge-combo29/grok/095/partner_off_O.tsv N 200 SUM 9500069
COMPARED 200
DIFFER 0
SAME 200
partner_cmp_off_G.txt
LEFT forge-combo29/grok/095/B_G_d12.tsv N 353 SUM 18466239
RIGHT forge-combo29/grok/095/partner_off_G.tsv N 353 SUM 18466239
COMPARED 353
DIFFER 0
SAME 353
partner_cmp_on_vs_B.txt
LEFT forge-combo29/grok/095/B_O_d12.tsv N 200 SUM 9500069
RIGHT forge-combo29/grok/095/partner_on_O.tsv N 200 SUM 9705311
COMPARED 200
DIFFER 200
SAME 0
partner_cmp_on_rows.txt
MINE forge-combo29/grok/095/partner_on_O.tsv N 200 SUM 9705311
THEIRS forge-combo29/grok/095/partner_on_O.rows.txt N 200 SUM 9705311
COMPARED 200
DIFFER 0
SAME 200
Results of IdeaK6_on vs IdeaK6_off (20000 nodes, 1t, 16MB, R.fens):
Elo: 1.74 +/- 9.01, nElo: 5.36 +/- 27.80
LOS: 64.73 %, DrawRatio: 84.00 %, PairsRatio: 1.09
Games: 600, Wins: 267, Losses: 264, Draws: 69, Points: 301.5 (50.25 %)
Ptnml(0-2): [2, 21, 252, 22, 3], WL/DD Ratio: 18.38
--------------------------------------------------
PARTNER_PGN_RESULTS 600
HONESTY_PARTNER
bench11 info string bench depth 11 nodes 312866 time 180 nps 1738144
bench13 info string bench depth 13 nodes 862329 time 501 nps 1721215
bench16 info string bench depth 16 nodes 3024920 time 1499 nps 2017958
perft5 nodes 4865609
STEP_TABLE
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 095 idea 45
2 builds and honesty | done | HONESTY_B.txt B_known_sums.txt | honesty True base sums True
3 idea proofs | done | HONESTY_P.txt cmp_off_O.txt cmp_off_G.txt cmp_on_O.txt asan_summary.txt uci_options_ideak6.txt | off_o True off_g True on_differs_200 True asan_clean True poison_reported True
3e test match | done | match_og.log match_og.pgn match_result.txt | games_1106 True
4 partner | done | partner_cmp_off_O.txt partner_cmp_on_rows.txt partner_match_R.log | off_identical True on_rows_equal True
5 report | done | REPORT.md RESULT.txt | this report
```

## git status and folder listing

```
 M forge-combo29/grok/095/stamps.txt
?? config.json
?? forge-combo29/grok/095/REPORT.md
?? forge-combo29/grok/095/RESULT.txt
?? forge-combo29/grok/095/compare_partner_rows.py
?? forge-combo29/grok/095/honesty_partner_bench11.meta
?? forge-combo29/grok/095/honesty_partner_bench11.txt
?? forge-combo29/grok/095/honesty_partner_bench13.meta
?? forge-combo29/grok/095/honesty_partner_bench13.txt
?? forge-combo29/grok/095/honesty_partner_bench16.meta
?? forge-combo29/grok/095/honesty_partner_bench16.txt
?? forge-combo29/grok/095/honesty_partner_perft5.meta
?? forge-combo29/grok/095/honesty_partner_perft5.txt
?? forge-combo29/grok/095/partner_HONESTY_P.txt
?? forge-combo29/grok/095/partner_cmp_off_G.txt
?? forge-combo29/grok/095/partner_cmp_off_O.txt
?? forge-combo29/grok/095/partner_cmp_on_rows.txt
?? forge-combo29/grok/095/partner_cmp_on_vs_B.txt
?? forge-combo29/grok/095/partner_match_R.log
?? forge-combo29/grok/095/partner_match_R.pgn
?? forge-combo29/grok/095/partner_off_G.meta
?? forge-combo29/grok/095/partner_off_G.raw.txt
?? forge-combo29/grok/095/partner_off_G.tsv
?? forge-combo29/grok/095/partner_off_O.meta
?? forge-combo29/grok/095/partner_off_O.raw.txt
?? forge-combo29/grok/095/partner_off_O.tsv
?? forge-combo29/grok/095/partner_on_O.meta
?? forge-combo29/grok/095/partner_on_O.raw.txt
?? forge-combo29/grok/095/partner_on_O.rows.txt
?? forge-combo29/grok/095/partner_on_O.tsv
?? forge-combo29/grok/095/partner_source.txt
?? forge-combo29/grok/095/print_report_tables.py
?? forge-combo29/grok/095/report_tables.txt
```

```
total 10536
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:10 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  132589 Nov 20 08:10 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    6407 Nov 20 08:10 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu      16 Nov 20 08:10 asan_poison.meta
-rw-r--r-- 1 ubuntu ubuntu    6308 Nov 20 08:10 asan_poison.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      48 Nov 20 08:10 asan_poison.runner.txt
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:10 asan_poison.tsv
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:11 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  552955 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22913 Nov 20 08:02 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:03 B_known_sums.txt
-rw-r--r-- 1 ubuntu ubuntu     878 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  307497 Nov 20 08:02 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15780 Nov 20 08:02 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:11 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:11 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     333 Nov 20 08:11 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1262 Nov 20 09:12 compare_partner_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1212 Nov 20 08:06 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    1569 Nov 20 08:06 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G.epd
-rw-r--r-- 1 ubuntu ubuntu    5708 Nov 20 08:08 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    1215 Nov 20 07:58 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu    1531 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     901 Nov 20 08:06 honesty_exe.sh
-rw-r--r-- 1 ubuntu ubuntu     239 Nov 20 09:12 honesty_partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:12 honesty_partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     239 Nov 20 09:12 honesty_partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:12 honesty_partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     239 Nov 20 09:12 honesty_partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5107 Nov 20 09:12 honesty_partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     241 Nov 20 09:12 honesty_partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5318 Nov 20 09:12 honesty_partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 08:06 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 08:06 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5107 Nov 20 08:06 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:06 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5318 Nov 20 08:06 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     413 Nov 20 08:11 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6514 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1226 Nov 20 08:01 make_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    1918 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  137265 Nov 20 08:17 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 4511593 Nov 20 08:17 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     434 Nov 20 08:18 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu     664 Nov 20 08:10 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu    8325 Nov 20 08:10 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 09:12 partner_cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:12 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 09:12 partner_cmp_on_rows.txt
-rw-r--r-- 1 ubuntu ubuntu     335 Nov 20 09:12 partner_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   20721 Nov 20 09:11 partner_HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   70099 Nov 20 09:15 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu 1990899 Nov 20 09:15 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 09:12 partner_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu  555724 Nov 20 09:12 partner_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22913 Nov 20 09:12 partner_off_G.tsv
-rw-r--r-- 1 ubuntu ubuntu     915 Nov 20 09:12 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309156 Nov 20 09:12 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15780 Nov 20 09:12 partner_off_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 09:12 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309432 Nov 20 09:12 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:11 partner_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   15780 Nov 20 09:12 partner_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 09:11 partner_source.txt
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 08:06 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  555717 Nov 20 08:06 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22913 Nov 20 08:06 P_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 08:06 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309465 Nov 20 08:06 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15780 Nov 20 08:06 P_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:09 poison.fen
-rw-r--r-- 1 ubuntu ubuntu     729 Nov 20 08:11 poison_inserted.diff.txt
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 08:07 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309394 Nov 20 08:07 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 08:07 P_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     721 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    4414 Nov 20 09:17 print_report_tables.py
-rw-r--r-- 1 ubuntu ubuntu   10500 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    5261 Nov 20 09:17 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19276 Nov 20 08:10 R.fens
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:10 R.notes.txt
-rwxr-xr-x 1 ubuntu ubuntu    1207 Nov 20 08:10 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 08:02 smoke_o3.meta
-rw-r--r-- 1 ubuntu ubuntu    9417 Nov 20 08:02 smoke_o3.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     251 Nov 20 08:02 smoke_o3.tsv
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     974 Nov 20 08:03 sum_known.py
-rw-r--r-- 1 ubuntu ubuntu     111 Nov 20 08:06 uci_options_ideak6.txt
```
