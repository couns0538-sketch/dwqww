# Seat 056, idea 6, S34

IdeaS34 eases the late-move reduction while this ply's child cutoffs are still few: two plies before a couple (default 2), one ply until four, then no ease.
A beta cutoff whose move is not the transposition move adds IdeaS34_NoTt (default 2); a transposition cutoff still adds one. The check option defaults to false, and the five spins default to those numbers.
With the switch false the historical step remains: one more ply of reduction after LmrCutoffThreshold.

EXISTS: no. The plain engine's cutoff term is one late extra ply, at forge-combo29/src/search.cpp:2001 (`cutoff_count > LmrCutoffThreshold` then `r += 1`). That is not the front-loaded ease. The re-search that restores a full depth when the shallow score is above alpha was already there and was left in place.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both HONESTY_B.txt and HONESTY_P.txt say PASS. Exe B with S14 reproduced O depth 12 sum 9500069 (first three 41311, 24872, 28574) and G depth 12 sum 18466239.

The table below is the output of report_numbers.py, which reads the raw files.

| step | status | evidence file | result |
| --- | --- | --- | --- |
| seat | done | SEAT.txt | seat 056, idea 6 |
| honesty B | done | HONESTY_B.txt | PASS |
| baseline O | done | B_O_d12.meta | node_sum=9500069 |
| baseline G | done | B_G_d12.meta | node_sum=18466239 |
| prediction | done | prediction.txt | file present, not edited after the measuring runs |
| patch applies | done | apply_check.txt | my_patch APPLY_CHECK_OK partner_patch PARTNER_APPLY_CHECK_OK |
| proof 1 honesty P | done | HONESTY_P.txt | PASS |
| proof 2 off O | done | P_off_O_d12.nodes | compared=200 equal=200 differ=0 |
| proof 2 off G | done | P_off_G_d12.nodes | compared=353 equal=353 differ=0 |
| proof 3 on O | done | P_on_O_d12.nodes | compared=200 equal=0 differ=200 sum=14553823 |
| proof 4 uci | done | P_uci.txt | IdeaS34 option lines=6 |
| proof 5 sanitizer | done | asan_G100_d10.meta | sanitizer_lines=0 symbols=35 probe sanitizer_lines=2 |
| match | done | match_stdout.txt | Elo: -4.40 +/- 10.41, nElo: -8.65 +/- 20.48; Games: 1106, Wins: 341, Losses: 355, Draws: 410, Points: 546.0 (49.37 %) |
| partner | done | partner_on_O_d12.nodes | compared=200 equal=200 differ=0 | Elo: -1.16 +/- 10.03, nElo: -3.21 +/- 27.80; Games: 600, Wins: 269, Losses: 271, Draws: 60, Points: 299.0 (49.83 %) |

Proofs on exe P:

1. Honesty with no setoption: the four numbers above, HONESTY_P.txt.
2. S14 and IdeaS34 false: O depth 12 equal to exe B on 200 of 200 (sum 9500069). G depth 12 equal on 353 of 353 (sum 18466239).
3. S14 and IdeaS34 true, spins at the defaults: O depth 12 differs on 200 of 200. Sum 14553823. Prediction was 14500000, wrong outside 11000000 to 24000000. The sum is inside that range.
4. `uci` lists IdeaS34 as check default false, and IdeaS34_EaseZero 2, IdeaS34_EaseMid 1, IdeaS34_Couple 2, IdeaS34_Full 4, IdeaS34_NoTt 2. P_uci.txt.
5. AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: 0 sanitizer lines, node sum 2956522. `nm -C` count of `__asan_` is 35, stored in asan_G100_d10.meta. A scratch copy with one read past a 4-int heap array on the FEN in asan_probe.fen, built the same way and run through depth_sum.py, reported `runtime error: load of address ... with insufficient space for an object of type 'int'` (asan_probe.log, sanitizer_lines=2).

Match: exe P switch true versus exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. fastchess, concurrency 3. 1106 games. Elo -4.40 +/- 10.41. The whole interval is not below 0, and the point is not below -20, so the code was not re-opened for a mistake hunt. Prediction was +6, wrong if the point were below -30 or above +45. -4.40 is inside that.

Partner: seats for idea 6 are 006, 056, 106. At 2026-11-20T09:08:33Z, 106 had no branch. The next seat after 056 that had a branch is 006. Their patch applies (`PARTNER_APPLY_CHECK_OK`). Honesty matches. Switch false matches exe B on O (200 equal) and on G (353 equal). Switch true matches their own O depth-12 rows on 200 of 200 (sum 11275663, the sum they recorded). A match of their switch on my 300 R openings, both colours, 600 games: Elo -1.16 +/- 10.03. Verdict: CONFIRMS.

suspicions, not proven: the two-ply ease is on for a cutoff count of 1 as well as 0, because 1 is not yet "a couple". That may ease more than the sentence "no beta cutoff" asks. The fixed-node elo is slightly negative and the error bar includes zero and the predicted +6, so this match does not show a gain.

what I did NOT do: no pull request. No engine source committed, only idea.patch.txt. Spins were not tried at values other than the defaults. Seat 106 never appeared, so it was not reviewed. The sanitizer search was the first 100 of G at depth 10, not all of G and not depth 12. The partner's own O+G match was not replayed; the partner match here is the 600 R games. Did not edit prediction.txt after it was pushed.

what I am NOT sure about: whether a cutoff count of 1 should already use the one-ply ease. Whether the probe's UndefinedBehaviorSanitizer line, rather than an AddressSanitizer "heap-buffer-overflow" banner, is the report a reader expects. Both sanitizers were in the build, `nm` shows 35 `__asan_` symbols, and the planted read was reported. The fastchess partner line "Draws: 60" with "DrawRatio: 83.00 %" looks inconsistent; the game total 269+271+60 is 600, and the pentanomial row sums to 300 pairs. I did not resolve which draw figure fastchess means.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/056/stamps.txt
?? forge-combo29/grok/056/HONESTY_PARTNER.txt
?? forge-combo29/grok/056/REPORT.md
?? forge-combo29/grok/056/RESULT.txt
?? forge-combo29/grok/056/apply_check.txt
?? forge-combo29/grok/056/compare_partner_on.py
?? forge-combo29/grok/056/honesty_PARTNER_bench11.meta
?? forge-combo29/grok/056/honesty_PARTNER_bench11.txt
?? forge-combo29/grok/056/honesty_PARTNER_bench13.meta
?? forge-combo29/grok/056/honesty_PARTNER_bench13.txt
?? forge-combo29/grok/056/honesty_PARTNER_bench16.meta
?? forge-combo29/grok/056/honesty_PARTNER_bench16.txt
?? forge-combo29/grok/056/honesty_PARTNER_perft5.meta
?? forge-combo29/grok/056/honesty_PARTNER_perft5.txt
?? forge-combo29/grok/056/partner006.patch.txt
?? forge-combo29/grok/056/partner006_P_on_O_d12.rows
?? forge-combo29/grok/056/partner_match.pgn
?? forge-combo29/grok/056/partner_match_stdout.txt
?? forge-combo29/grok/056/partner_measure_stdout.txt
?? forge-combo29/grok/056/partner_off_G_d12.log
?? forge-combo29/grok/056/partner_off_G_d12.meta
?? forge-combo29/grok/056/partner_off_G_d12.nodes
?? forge-combo29/grok/056/partner_off_G_d12.rows
?? forge-combo29/grok/056/partner_off_G_stdout.txt
?? forge-combo29/grok/056/partner_off_O_d12.log
?? forge-combo29/grok/056/partner_off_O_d12.meta
?? forge-combo29/grok/056/partner_off_O_d12.nodes
?? forge-combo29/grok/056/partner_off_O_d12.rows
?? forge-combo29/grok/056/partner_on_O_d12.log
?? forge-combo29/grok/056/partner_on_O_d12.meta
?? forge-combo29/grok/056/partner_on_O_d12.nodes
?? forge-combo29/grok/056/partner_on_O_d12.rows
?? forge-combo29/grok/056/report_numbers.py
?? forge-combo29/grok/056/report_numbers.txt
?? forge-combo29/grok/056/run_partner_match.sh
?? forge-combo29/grok/056/run_partner_measure.sh

$ ls -la forge-combo29/grok/056
total 8848
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:14 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  119526 Nov 20 08:07 asan_G100_d10.log
-rw-r--r-- 1 ubuntu ubuntu    1255 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     592 Nov 20 08:07 asan_G100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu    6391 Nov 20 08:07 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:07 asan_probe.fen
-rw-r--r-- 1 ubuntu ubuntu    7186 Nov 20 08:07 asan_probe.log
-rw-r--r-- 1 ubuntu ubuntu    1257 Nov 20 08:07 asan_probe.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_probe.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_probe.rows
-rw-r--r-- 1 ubuntu ubuntu  507289 Nov 20 08:03 B_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:03 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 08:03 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  281706 Nov 20 08:02 B_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:02 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     862 Nov 20 09:09 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    6071 Nov 20 08:04 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu    1538 Nov 20 08:09 design.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    1512 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1515 Nov 20 08:06 honesty_exe.sh
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:09 honesty_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 honesty_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:09 honesty_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 honesty_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:09 honesty_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 honesty_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 honesty_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 honesty_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 09:09 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:06 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:06 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:06 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:06 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6887 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1495 Nov 20 08:02 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3561639 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     356 Nov 20 08:16 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu  107750 Nov 20 08:15 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     968 Nov 20 08:16 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    7361 Nov 20 09:09 partner006.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   15385 Nov 20 09:09 partner006_P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu 1653321 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   53177 Nov 20 09:13 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu    6340 Nov 20 09:09 partner_measure_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu  507825 Nov 20 09:10 partner_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     976 Nov 20 09:10 partner_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 09:10 partner_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 09:10 partner_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu    5216 Nov 20 09:10 partner_off_G_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu  282040 Nov 20 09:09 partner_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     976 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:09 partner_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 09:09 partner_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  283060 Nov 20 09:09 partner_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1149 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1210 Nov 20 09:09 partner_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   15761 Nov 20 09:09 partner_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  507700 Nov 20 08:05 P_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     970 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:05 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   22888 Nov 20 08:05 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  282068 Nov 20 08:05 P_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     970 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:05 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:05 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  283668 Nov 20 08:05 P_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1194 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1231 Nov 20 08:05 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 08:05 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     407 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    5274 Nov 20 08:05 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7472 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    5288 Nov 20 09:15 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    5724 Nov 20 09:15 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19469 Nov 20 08:02 R.fens
-rw-r--r-- 1 ubuntu ubuntu    1996 Nov 20 08:07 run_asan.sh
-rw-r--r-- 1 ubuntu ubuntu    1311 Nov 20 08:08 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1190 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     821 Nov 20 09:09 run_partner_measure.sh
-rw-r--r-- 1 ubuntu ubuntu    2024 Nov 20 08:05 run_p_measure.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:16 stamps.txt
```
