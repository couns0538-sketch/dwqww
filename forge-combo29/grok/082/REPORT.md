# Seat 082, idea 32, IdeaA1

IdeaA1 is a check, default false, that changes only the quiet late-move reduction's history term.
When it is on, that term is history times IdeaA1_Scale divided by LmrHistoryDivisor, in units of one ply over IdeaA1_Scale (default 1024), capped at plus or minus IdeaA1_Clamp plies (default 2), and the leftover fraction is carried to the child until it makes a whole ply.
When it is off, the reduction keeps the original line r -= clamp(history / LmrHistoryDivisor, -2, 2), and the carry is not read or written.

EXISTS: no. The plain engine's history term is that integer division (forge-combo29/src/search.cpp, the off branch of the patch). It is not a 1/1024-ply term.

## Honesty numbers

Exe B and exe P, no setoption, from report_numbers.py reading HONESTY_B.txt and HONESTY_P.txt:

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

Exe B, S14, depth 12: O sum 9500069 (first three 41311 24872 28574), G sum 18466239. Both match the known sums.

git apply --check of idea.patch.txt on a fresh base worktree exited 0 (apply_check_mine.txt). The same check of the partner patch exited 0 (apply_check_partner.txt).

## Table

Pasted from report_numbers.py, the TABLE section. That script reads the compare files and match_summary.txt. The full print is report_numbers.txt.

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 082 idea 32
2 two builds and honesty | done | HONESTY_B.txt B_O_d12.rows B_G_d12.rows | bench nodes 312866 862329 3024920 perft 4865609; O sum 9500069; G sum 18466239
3 idea | done | idea.patch.txt compare_O_off.txt compare_G_off.txt compare_O_on.txt asan_G100_d10.meta canary_asan.runner.txt match_summary.txt | left 200 right 200 compared 200 differ 0; left 353 right 353 compared 353 differ 0; left 200 right 200 compared 200 differ 200
4 partner 032 | done | partner032_compare.txt partner032_match.log | off differ 0; on vs their rows differ 0; CONFIRMS
5 report | done | REPORT.md RESULT.txt | this file
proof 1 honesty no setoption | done | HONESTY_P.txt | same four node counts as exe B
proof 2 switch false | done | compare_O_off.txt compare_G_off.txt | left 200 right 200 compared 200 differ 0; left 353 right 353 compared 353 differ 0
proof 3 switch true | done | compare_O_on.txt | left 200 right 200 compared 200 differ 200
proof 4 uci options | done | uci_options.txt | IdeaA1 check false; IdeaA1_Scale 1024; IdeaA1_Clamp 2
proof 5 sanitizer | done | asan_G100_d10.err asan_G100_d10.meta canary_asan.runner.txt | err bytes 0; asan symbols 35; canary heap-buffer-overflow
match | done | match_summary.txt | Elo: -3.77 +/- 10.08, nElo: -7.66 +/- 20.48 | Games: 1106, Wins: 336, Losses: 348, Draws: 422, Points: 547.0 (49.46 %)
```

## Proofs

(1) Honesty, no setoption, exe P: bench 11/13/16 and perft 5 are 312866, 862329, 3024920, 4865609. Same as exe B. HONESTY_P.txt.

(2) S14 and IdeaA1 false. O depth 12: 200 positions, 0 differ, both sums 9500069. G depth 12: 353 positions, 0 differ, both sums 18466239. compare_O_off.txt, compare_G_off.txt.

(3) S14 and IdeaA1 true. O depth 12: 200 of 200 positions differ from exe B. Sum 9632936 against exe B's 9500069. compare_O_on.txt. The code runs.

(4) The uci answer lists option name IdeaA1 type check default false, option name IdeaA1_Scale type spin default 1024 min 128 max 8192, and option name IdeaA1_Clamp type spin default 2 min 0 max 4. uci_options.txt.

(5) AddressSanitizer plus UndefinedBehaviorSanitizer build, IdeaA1 true, first 100 of G at depth 10: stderr 0 bytes, sum 2031063. nm -C count of __asan_ is 35. asan_G100_d10.meta, asan_G100_d10.err. The same runner on a scratch engine with one heap read past the end of a 4-int array, only for the FEN 8/8/8/8/8/8/8/K6k w - - 0 1, reports AddressSanitizer: heap-buffer-overflow. canary_asan.runner.txt.

## Match

Exe P with IdeaA1 true against exe P with IdeaA1 false. Both S14, Threads 1, Hash 16, 20000 nodes a move. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3. From match_summary.txt:

Elo: -3.77 +/- 10.08, 1106 games, 336 wins, 348 losses, 422 draws, 547.0 points (49.46%).

The point is not below -20, and the interval is not entirely below 0, so I did not open the code a second time for a mistake.

Prediction, committed before any measurement (prediction.txt): O sum 9300000, wrong outside 7500000..11500000; Elo +6, wrong outside -30..+40. The measured sum 9632936 and Elo -3.77 are inside those ranges.

## Partner

Partner is seat 032. Idea seats are 032, 082 and 132. 132 is not a seat. The next seat after 082 with a branch is 032.

I fetched for-fable-and-opus/grok-032, applied their idea.patch.txt on a fresh worktree of the base (git apply --check exit 0, then apply), and built it. Their option is also IdeaA1, default false. Their on-path rounds the 1/1024 term half toward zero and does not carry a fraction. That is a different patch from mine.

Their proofs, measured with my harness:

- Honesty: 312866, 862329, 3024920, 4865609.
- IdeaA1 false, O depth 12: 0 of 200 differ from exe B.
- IdeaA1 true, O depth 12: 0 of 200 differ from their P_on_O.nodes. Sum 10279733, which is their sum. 200 of 200 differ from exe B, as they claim.
- Match of their switch, my 300 R openings, both colours, 600 games: Elo 4.63 +/- 11.57. This is not their 1106-game match. Their RESULT claims Elo 1.26 +/- 10.31 on O+G. I did not replay that match.

Verdict: CONFIRMS. The honesty numbers, the off rows and their on rows match what they published.

## Suspicions, not proven

Almost every O position changed its node count with the carry on, while the sum moved only from 9500069 to 9632936. I suspect one carried fraction crosses a ply somewhere in nearly every tree and the extra nodes and the saved nodes mostly cancel. I did not trace a single position to show that.

Their round-half patch and my carry patch both move all 200 positions and both score near zero Elo on the built-in net. I do not know which one the owner's net would prefer.

## What I did NOT do

I did not rebuild seat 032 under a sanitizer. I did not replay their 1106-game match. I did not try IdeaA1_Scale or IdeaA1_Clamp at any value except the defaults. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not open a pull request.

## What I am NOT sure about

I am not sure the leftover fraction should survive a null move and a probcut. It might be cleaner to drop it when the move is not a quiet reduction. I left it in place so a fraction is not thrown away before it can become a ply.

The match interval -3.77 +/- 10.08 includes zero and includes small positive values. I am not sure the idea loses.

Random games use python-chess is_game_over(claim_draw=True), which can call a draw on the 50-move rule or a repetition. No game was dropped before ply 36 (R.meta), so that rule did not remove a position from R.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/082/stamps.txt
?? forge-combo29/grok/082/REPORT.md
?? forge-combo29/grok/082/RESULT.txt
?? forge-combo29/grok/082/apply_check_mine.txt
?? forge-combo29/grok/082/apply_check_partner.txt
?? forge-combo29/grok/082/partner032.patch.txt
?? forge-combo29/grok/082/partner032_P_on_O.nodes
?? forge-combo29/grok/082/partner032_bench11.err
?? forge-combo29/grok/082/partner032_bench11.meta
?? forge-combo29/grok/082/partner032_bench11.txt
?? forge-combo29/grok/082/partner032_bench13.err
?? forge-combo29/grok/082/partner032_bench13.meta
?? forge-combo29/grok/082/partner032_bench13.txt
?? forge-combo29/grok/082/partner032_bench16.err
?? forge-combo29/grok/082/partner032_bench16.meta
?? forge-combo29/grok/082/partner032_bench16.txt
?? forge-combo29/grok/082/partner032_compare.txt
?? forge-combo29/grok/082/partner032_match.log
?? forge-combo29/grok/082/partner032_match.pgn
?? forge-combo29/grok/082/partner032_off_O.err
?? forge-combo29/grok/082/partner032_off_O.meta
?? forge-combo29/grok/082/partner032_off_O.rows
?? forge-combo29/grok/082/partner032_off_O.txt
?? forge-combo29/grok/082/partner032_on_O.err
?? forge-combo29/grok/082/partner032_on_O.meta
?? forge-combo29/grok/082/partner032_on_O.rows
?? forge-combo29/grok/082/partner032_on_O.txt
?? forge-combo29/grok/082/partner032_perft5.err
?? forge-combo29/grok/082/partner032_perft5.meta
?? forge-combo29/grok/082/partner032_perft5.txt
?? forge-combo29/grok/082/report_numbers.py
?? forge-combo29/grok/082/report_numbers.txt
```

## ls -la forge-combo29/grok/082

```
total 5128
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:17 apply_check_mine.txt
-rw-r--r-- 1 ubuntu ubuntu      10 Nov 20 09:17 apply_check_partner.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 asan_G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu    1001 Nov 20 08:11 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     910 Nov 20 08:11 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  134091 Nov 20 08:11 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 B_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 08:05 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3469 Nov 20 08:05 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  558382 Nov 20 08:05 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 B_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 08:05 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1931 Nov 20 08:05 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  310281 Nov 20 08:05 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1011 Nov 20 08:11 canary_asan.meta
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 08:10 canary_asan.nm.txt
-rw-r--r-- 1 ubuntu ubuntu    5451 Nov 20 08:10 canary_asan.runner.txt
-rw-r--r-- 1 ubuntu ubuntu    5259 Nov 20 08:10 canary_asan.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:10 canary.fen
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 08:08 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 08:08 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 08:08 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     613 Nov 20 08:08 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1226 Nov 20 08:12 DECISION.txt
-rwxr-xr-x 1 ubuntu ubuntu    5743 Nov 20 08:10 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:08 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:05 G.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:03 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:03 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:03 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:03 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 honesty_b_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:04 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 08:04 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 honesty_b_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 08:04 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:04 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:07 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5168 Nov 20 08:07 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:07 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5168 Nov 20 08:07 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:07 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 08:07 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 08:07 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5381 Nov 20 08:07 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:08 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   10838 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1591 Nov 20 08:12 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  151636 Nov 20 08:17 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 1086453 Nov 20 08:17 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     398 Nov 20 08:19 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:05 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:12 partner032_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5166 Nov 20 09:12 partner032_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:12 partner032_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5166 Nov 20 09:12 partner032_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:12 partner032_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5168 Nov 20 09:12 partner032_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 09:12 partner032_compare.txt
-rw-r--r-- 1 ubuntu ubuntu   78831 Nov 20 09:16 partner032_match.log
-rw-r--r-- 1 ubuntu ubuntu  569571 Nov 20 09:16 partner032_match.pgn
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 09:12 partner032_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1931 Nov 20 09:12 partner032_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu  312369 Nov 20 09:12 partner032_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 09:12 partner032_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1933 Nov 20 09:12 partner032_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu  312796 Nov 20 09:12 partner032_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    6688 Nov 20 09:11 partner032.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner032_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 09:12 partner032_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5379 Nov 20 09:12 partner032_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3697 Nov 20 09:11 partner032_P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_off_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     930 Nov 20 08:07 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3469 Nov 20 08:07 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  561125 Nov 20 08:07 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     930 Nov 20 08:07 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1931 Nov 20 08:07 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  312108 Nov 20 08:07 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 08:07 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1929 Nov 20 08:07 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  312464 Nov 20 08:07 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     605 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    6964 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4358 Nov 20 09:17 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    3170 Nov 20 09:18 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19964 Nov 20 08:12 R.fens
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:12 R.meta
-rwxr-xr-x 1 ubuntu ubuntu     965 Nov 20 08:09 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1135 Nov 20 08:27 run_switch_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 smoke.epd
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:09 smoke_match.log
-rw-r--r-- 1 ubuntu ubuntu    2172 Nov 20 08:09 smoke_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rwxr-xr-x 1 ubuntu ubuntu    3574 Nov 20 08:03 uci_one.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 uci_options.err
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 08:07 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    5107 Nov 20 08:07 uci_options.txt
```
