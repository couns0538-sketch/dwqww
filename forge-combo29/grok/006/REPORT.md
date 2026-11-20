Idea S34 eases late-move reduction while this ply has seen few beta cutoffs: two plies at a weighted count of zero, one ply until the count reaches four, then none.
A cutoff at a node with no transposition move adds two. A shallow score above alpha is searched again at the full unreduced depth.
The switch is IdeaS34, type check, default false. The spins are IdeaS34_None 2, IdeaS34_After 1, IdeaS34_Stop 4, and IdeaS34_Bare 2.

EXISTS: no. The plain engine adds one ply of reduction when the child cutoff count is above LmrCutoffThreshold (default 3). That is a late step. It does not ease the reduction when the count is still low. See DECISION.txt.

Honesty, no setoption, exe B and exe P. From HONESTY_B.txt and HONESTY_P.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Table printed by report_numbers.py:

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 006, idea 6, model Grok 4.7, 2026-11-20T07:51:39Z, token 72352922313944
2 honesty B and baseline sums | done | HONESTY_B.txt B_O_d12.sum B_G_d12.sum | bench11=info string bench depth 11 nodes 312866 time 174 nps 1798080 ; sum=9500069 ; sum=18466239
3 patch applies, off identical, on differs | done | apply_check.txt compare_B_Poff_O.txt compare_B_Poff_G.txt compare_B_Pon_O.txt | apply_check_exit=0 ; node_differ=0 ; node_differ=0 ; node_differ=200
3 uci options | done | uci_options_idea.txt | option name IdeaS34 type check default false ; option name IdeaS34_None type spin default 2 min 0 max 4 ; option name IdeaS34_After type spin default 1 min 0 max 4 ; option name IdeaS34_Stop type spin default 4 min 1 max 32 ; option name IdeaS34_Bare type spin default 2 min 1 max 8
3 sanitizer | done | asan_nm_count.txt asan_g100.san asan_bug.san | nm=35 ; sanitizer_lines=0 ; sanitizer_lines=1
3 match | done | match_s34.log | Elo: -6.28 +/- 10.07, nElo: -12.78 +/- 20.48 ; Games: 1106, Wins: 326, Losses: 346, Draws: 434, Points: 543.0 (49.10 %)
4 partner | done | partner_apply.txt partner_compare.txt partner_honesty.txt partner_match.log | partner_apply_check_exit=0 ; on_vs_partner_file n=200 differ=0 left_sum=14553823 right_sum=14553823 ; Games: 600, Wins: 270, Losses: 256, Draws: 74, Points: 307.0 (51.17 %)
5 report | done | REPORT.md RESULT.txt | this file
```

Proof (1). Both builds, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

Proof (2). S14 and IdeaS34 false. compare_rows.py: O depth 12 node_differ=0 of 200, sum 9500069. G depth 12 node_differ=0 of 353, sum 18466239. Both equal exe B, including the known first three of O (41311 24872 28574).

Proof (3). S14 and IdeaS34 true. O depth 12 node_differ=200 of 200 against exe B. Sum 11275663. First three 19684 42539 37961. The code runs.

Proof (4). uci lists IdeaS34 type check default false, and the four spins at 2, 1, 4, and 2. Raw lines are in uci_options_idea.txt.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build. nm -C | grep -c __asan_ printed 35. The same runner, switch true, first 100 of G at depth 10: sanitizer_lines=0, positions_finished=100, returncode=0. A scratch copy with one read past a heap array of 4 ints, on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1, built the same way and run through that runner: sanitizer_lines=1, returncode=-6, and the line names a load with insufficient space for an int. ASAN_OPTIONS set detect_leaks=0. The overflow check was on.

Match. exe P with the switch true against exe P with the switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours. From the last Elo and Games lines of match_s34.log: Elo -6.28 +/- 10.07, 1106 games, 326 wins, 346 losses, 434 draws. The point is not below -20 and the interval is not entirely below 0, so the code was not opened again for a mistake. prediction.txt said 13200000 (wrong outside 9700000 to 24000000) and Elo -8 (wrong above +30 or below -70). The measured sum 11275663 and Elo -6.28 sit inside those ranges.

Partner seat 056, the next seat with this idea that had a branch. Verdict: CONFIRMS. git apply --check on a fresh base tree exited 0 (partner_apply.txt). Honesty nodes were 312866, 862329, 3024920, and perft 4865609. Switch false matched exe B on all 200 O positions and matched the partner's own off file. Switch true matched the partner's own on file on all 200 positions (sum 14553823) and differed from exe B on all 200. A match of their switch on 300 R openings, both colours, was 600 games, Elo 8.11 +/- 12.09 (partner_match.log). Their design.txt says the off path is today's path and their published on rows are the on search. Both of those held.

suspicions, not proven. The two-ply ease is a large share of an ordinary reduction, and the fixed-node point estimate is negative. The error bar crosses zero, so a loss is not shown. Seat 056 counted a cutoff whose move was not the hash move as two, which is a different reading, and their R match point was positive with an error bar that also crosses zero.

What I did NOT do. I did not play the owner's net. I did not try spin values other than the defaults. Seat 106 had no branch. I did not build the partner patch with a sanitizer. Leak detection was off in the sanitizer proof. I did not search past the unreduced depth when a shallow score beat alpha. The restore is the existing full-depth re-search.

What I am NOT sure about. "After a couple" might mean the two-ply ease lasts until two cutoffs, not until the first. I used the first cutoff because the idea's opening clause is "no beta cutoff". "No transposition move" might mean the cutoff move was not the hash move. That is what seat 056 did. I counted two when the node that cut off had no hash move.

times: see stamps.txt

git status --short and ls -la follow.

```
$ git status --short
 M forge-combo29/grok/006/stamps.txt
?? forge-combo29/grok/006/REPORT.md
?? forge-combo29/grok/006/RESULT.txt
?? forge-combo29/grok/006/compare_partner.py
?? forge-combo29/grok/006/partner056_P_off_O.nodes
?? forge-combo29/grok/006/partner056_P_on_O.nodes
?? forge-combo29/grok/006/partner056_idea.patch.txt
?? forge-combo29/grok/006/partner_apply.txt
?? forge-combo29/grok/006/partner_compare.txt
?? forge-combo29/grok/006/partner_honesty.txt
?? forge-combo29/grok/006/partner_honesty_bench11.meta
?? forge-combo29/grok/006/partner_honesty_bench11.txt
?? forge-combo29/grok/006/partner_honesty_bench13.meta
?? forge-combo29/grok/006/partner_honesty_bench13.txt
?? forge-combo29/grok/006/partner_honesty_bench16.meta
?? forge-combo29/grok/006/partner_honesty_bench16.txt
?? forge-combo29/grok/006/partner_honesty_perft5.meta
?? forge-combo29/grok/006/partner_honesty_perft5.txt
?? forge-combo29/grok/006/partner_match.log
?? forge-combo29/grok/006/partner_match.pgn
?? forge-combo29/grok/006/partner_match.sh
?? forge-combo29/grok/006/partner_match_config.json
?? forge-combo29/grok/006/partner_off_O.meta
?? forge-combo29/grok/006/partner_off_O.rows
?? forge-combo29/grok/006/partner_off_O.sum
?? forge-combo29/grok/006/partner_off_O.transcript
?? forge-combo29/grok/006/partner_on_O.meta
?? forge-combo29/grok/006/partner_on_O.rows
?? forge-combo29/grok/006/partner_on_O.sum
?? forge-combo29/grok/006/partner_on_O.transcript
?? forge-combo29/grok/006/report_numbers.py
?? forge-combo29/grok/006/report_numbers.txt

$ ls -la forge-combo29/grok/006
total 4856
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu     19 Nov 20 08:07 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     28 Nov 20 08:05 asan_bug.fen
-rw-r--r-- 1 ubuntu ubuntu   1001 Nov 20 08:05 asan_bug.meta
-rw-r--r-- 1 ubuntu ubuntu    210 Nov 20 08:05 asan_bug.san
-rw-r--r-- 1 ubuntu ubuntu   7204 Nov 20 08:05 asan_bug.transcript
-rw-r--r-- 1 ubuntu ubuntu    997 Nov 20 08:05 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:05 asan_g100.san
-rw-r--r-- 1 ubuntu ubuntu 132230 Nov 20 08:05 asan_g100.transcript
-rw-r--r-- 1 ubuntu ubuntu      3 Nov 20 08:06 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu   6397 Nov 20 08:04 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu    823 Nov 20 08:00 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  22204 Nov 20 08:00 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     62 Nov 20 08:00 B_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu 550321 Nov 20 08:00 B_G_d12.transcript
-rw-r--r-- 1 ubuntu ubuntu    823 Nov 20 08:00 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  15379 Nov 20 08:00 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 08:00 B_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu 309151 Nov 20 08:00 B_O_d12.transcript
-rw-r--r-- 1 ubuntu ubuntu    111 Nov 20 08:02 compare_B_Poff_G.txt
-rw-r--r-- 1 ubuntu ubuntu    109 Nov 20 08:02 compare_B_Poff_O.txt
-rw-r--r-- 1 ubuntu ubuntu    110 Nov 20 08:02 compare_B_Pon_O.txt
-rw-r--r-- 1 ubuntu ubuntu   1031 Nov 20 09:10 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu   1305 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu   1549 Nov 20 08:07 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu   5009 Nov 20 08:04 G100.epd
-rw-r--r-- 1 ubuntu ubuntu    908 Nov 20 08:07 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    209 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1063 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu    402 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    209 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    402 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   7361 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   7128 Nov 20 08:13 match_s34_config.json
-rw-r--r-- 1 ubuntu ubuntu 119251 Nov 20 08:13 match_s34.log
-rw-r--r-- 1 ubuntu ubuntu 953890 Nov 20 08:12 match_s34.pgn
-rwxr-xr-x 1 ubuntu ubuntu   1044 Nov 20 08:06 match_s34.sh
-rw-r--r-- 1 ubuntu ubuntu   5899 Nov 20 08:00 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:04 OG.epd
-rw-r--r-- 1 ubuntu ubuntu   6887 Nov 20 09:08 partner056_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1204 Nov 20 09:08 partner056_P_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   1231 Nov 20 09:08 partner056_P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu     27 Nov 20 09:10 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu    261 Nov 20 09:10 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 09:09 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 09:09 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    207 Nov 20 09:09 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:09 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    209 Nov 20 09:09 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 09:09 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    358 Nov 20 09:09 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu   7134 Nov 20 09:14 partner_match_config.json
-rw-r--r-- 1 ubuntu ubuntu  63421 Nov 20 09:13 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 466355 Nov 20 09:13 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu   1056 Nov 20 09:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    858 Nov 20 09:09 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  15379 Nov 20 09:09 partner_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 09:09 partner_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu 309604 Nov 20 09:09 partner_off_O.transcript
-rw-r--r-- 1 ubuntu ubuntu    857 Nov 20 09:09 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  15406 Nov 20 09:09 partner_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 partner_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu 311174 Nov 20 09:09 partner_on_O.transcript
-rw-r--r-- 1 ubuntu ubuntu    858 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  22204 Nov 20 08:02 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     62 Nov 20 08:02 P_off_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu 550312 Nov 20 08:02 P_off_G_d12.transcript
-rw-r--r-- 1 ubuntu ubuntu    858 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  15379 Nov 20 08:02 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 08:02 P_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu 309495 Nov 20 08:02 P_off_O_d12.transcript
-rw-r--r-- 1 ubuntu ubuntu    857 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  15385 Nov 20 08:02 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:02 P_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu 310558 Nov 20 08:02 P_on_O_d12.transcript
-rw-r--r-- 1 ubuntu ubuntu    957 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   2182 Nov 20 08:08 proof_table.py
-rw-r--r-- 1 ubuntu ubuntu  19612 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu   7378 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   2509 Nov 20 09:14 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu   1800 Nov 20 09:15 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    140 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    202 Nov 20 08:02 uci_options_idea.meta
-rw-r--r-- 1 ubuntu ubuntu    275 Nov 20 08:02 uci_options_idea.txt
```
