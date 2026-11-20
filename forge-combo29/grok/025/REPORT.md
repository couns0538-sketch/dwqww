Idea S33 scales the null-move probe by the static margin over beta: extra plies when that margin is thin, and none once it is large.
The check option IdeaS33 defaults to false. The spins are IdeaS33_Max 3, IdeaS33_Divisor 80, and IdeaS33_Near 40.
With the switch on, a probe that still reaches beta is a cutoff with no verification search, and a miss of at most 40 centipawns adds one ply to the real-move search.

EXISTS: no. The plain engine adds min((eval - beta) / NullMoveEvalDivisor, 3) to the null reduction, which is more reduction when the margin is large, and it still verifies cutoffs from depth 14. That is the opposite scale. See forge-combo29/src/search.cpp in the base commit, the null-move reduction.

Honesty, no setoption, exe B and exe P and the partner build, from print_report_bits.py:
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

step | done / partly / not done | evidence file | result
1 seat | done | SEAT.txt, stamps.txt | seat 025, idea 25, IdeaS33
2 builds and honesty | done | HONESTY_B.txt, O_B_d12.rows, G_B_d12.rows | known bench and perft; O sum 9500069; G sum 18466239
3 idea | done | idea.patch.txt, print_report_bits.py | off identical; on 200 of 200 differ; match 1106 games
4 partner | done | partner_075_idea.patch.txt, partner_O_on.rows, partner_match.txt | CONFIRMS seat 075
5 report | done | REPORT.md, RESULT.txt | this file

Proofs, numbers pasted from print_report_bits.py:
(1) exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Same as exe B.
(2) S14 and IdeaS33 false: O depth 12 node_differ 0 of 200 and move_differ 0 of 200, both sums 9500069. G depth 12 node_differ 0 of 353 and move_differ 0 of 353, both sums 18466239.
(3) S14 and IdeaS33 true: O depth 12 sum 11375225, node_differ 200 of 200, move_differ 47 of 200. Prediction was 12400000, wrong outside 8000000..20000000. The measured sum is inside that range.
(4) uci lists: option name IdeaS33 type check default false; IdeaS33_Max spin default 3 min 0 max 6; IdeaS33_Divisor spin default 80 min 1 max 1000; IdeaS33_Near spin default 40 min 0 max 500.
(5) AddressSanitizer + UndefinedBehaviorSanitizer, IdeaS33 true, first 100 of G at depth 10: positions_finished 100, returncode 0, sanitizer_lines 0, asan_symbols 35 (nm -C | grep -c __asan_). The same runner on a scratch copy that reads one past a heap array of 4 ints on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1 reported ERROR: AddressSanitizer: heap-buffer-overflow, sanitizer_lines 2, asan_symbols 35. git apply --check of idea.patch.txt on a fresh base worktree: APPLY_CHECK_OK in idea_apply_check.txt.

Match, s33on vs s33off, S14, Threads 1, Hash 16, nodes 20000, openings O then G, both colours, 1106 games (match_on_vs_off.txt):
Elo: -1.26 +/- 10.31, nElo: -2.50 +/- 20.48
LOS: 40.55 %, DrawRatio: 64.01 %, PairsRatio: 0.97
Games: 1106, Wins: 342, Losses: 346, Draws: 418, Points: 551.0 (49.82 %)
Ptnml(0-2): [14, 87, 354, 85, 13]
Prediction was +6 Elo, wrong below -30 or above +35. -1.26 is inside that range. The whole interval is not below 0, and the point is not below -20, so the loss rule did not ask for a second look.

Partner verdict: CONFIRMS seat 075. Their idea.patch.txt applied with git apply --check (partner_apply_check.txt says APPLY_CHECK_OK). Honesty numbers matched. Switch false matched exe B on all 200 O depth-12 rows. Switch true matched their own O rows: claimed sum 10838685, mine 10838685, differ 0 of 200. A match of their switch on my 300 R openings, both colours, 600 games (partner_match.txt): Elo 5.79 +/- 10.51, Wins 265, Losses 255, Draws 80. I started this check at 08:22Z, when their patch was already on the branch, rather than waiting until minute 75 (09:08Z).

suspicions, not proven
The O depth-12 sum moved, but depth 12 never enters the depth-14 verification, so that half of the idea did not run on the measured set. The node change is the inverted margin term and the near-miss ply. Seat 075 read "inside the null tree" as extra late-move reduction on the side that passed, not as a change to the null reduction itself. Both versions change all 200 openings. I did not show which reading is the one the idea text wants.

what I did NOT do
I did not try other spin values. I did not run the sanitizer past the first 100 positions of G, or at depth 12. I did not replay seat 075's 1106-game O+G match. I did not wait until minute 75. A second handoff fetch at 08:22Z found no FABLE_TO_grok file. The minute-60 fetch is a later stamp if this run is still going then.

what I am NOT sure about
I am not sure the null-reduction reading is the one intended, against seat 075's in-tree reduction. I am not sure -1.26 Elo is different from zero. The error bar is +/- 10.31.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/025/stamps.txt
?? forge-combo29/grok/025/REPORT.md
?? forge-combo29/grok/025/RESULT.txt
?? forge-combo29/grok/025/idea_apply_check.txt
?? forge-combo29/grok/025/partner_075_idea.patch.txt
?? forge-combo29/grok/025/partner_O_off.meta
?? forge-combo29/grok/025/partner_O_off.rows
?? forge-combo29/grok/025/partner_O_off.txt
?? forge-combo29/grok/025/partner_O_on.meta
?? forge-combo29/grok/025/partner_O_on.rows
?? forge-combo29/grok/025/partner_O_on.txt
?? forge-combo29/grok/025/partner_apply_check.txt
?? forge-combo29/grok/025/partner_claimed_O_on.txt
?? forge-combo29/grok/025/partner_honesty/
?? forge-combo29/grok/025/partner_match.pgn
?? forge-combo29/grok/025/partner_match.sh
?? forge-combo29/grok/025/partner_match.txt
?? forge-combo29/grok/025/print_report_bits.py
$ ls -la forge-combo29/grok/025
total 11876
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 08:29 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu    1466 Nov 20 08:01 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1513 Nov 20 08:07 design.txt
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 07:58 G_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 07:58 G_B_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  901148 Nov 20 07:58 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     881 Nov 20 08:01 G_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:01 G_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu  921367 Nov 20 08:01 G_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     246 Nov 20 07:56 honesty_b_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:56 honesty_b_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     246 Nov 20 07:56 honesty_b_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:56 honesty_b_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 07:56 honesty_b_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 07:56 honesty_b_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 07:56 honesty_b_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 07:56 honesty_b_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 07:56 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu    3474 Nov 20 07:56 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu   20309 Nov 20 07:56 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:29 idea_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    7841 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1831 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    1507 Nov 20 08:04 make_scratch.py
-rw-r--r-- 1 ubuntu ubuntu 4552329 Nov 20 08:12 match_on_vs_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  138370 Nov 20 08:12 match_on_vs_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1303 Nov 20 08:06 match.sh
-rw-r--r-- 1 ubuntu ubuntu    6151 Nov 20 07:57 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 07:57 O_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 07:57 O_B_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  507624 Nov 20 07:57 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:01 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:01 O_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu  519397 Nov 20 08:01 O_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:01 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu   15764 Nov 20 08:01 O_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu  519769 Nov 20 08:01 O_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   13246 Nov 20 08:23 partner_075_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:24 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    4499 Nov 20 08:23 partner_claimed_O_on.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:23 partner_honesty
-rw-r--r-- 1 ubuntu ubuntu 2164923 Nov 20 08:27 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1432 Nov 20 08:23 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   73355 Nov 20 08:27 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu    1032 Nov 20 08:23 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:23 partner_O_off.rows
-rw-r--r-- 1 ubuntu ubuntu  566824 Nov 20 08:23 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1032 Nov 20 08:23 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu   15762 Nov 20 08:23 partner_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu  566819 Nov 20 08:23 partner_O_on.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:01 p_honesty
-rw-r--r-- 1 ubuntu ubuntu    1054 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3563 Nov 20 08:27 print_report_bits.py
-rw-r--r-- 1 ubuntu ubuntu    5670 Nov 20 08:29 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:28 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19313 Nov 20 08:04 R.fens
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:04 R.meta
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:05 san_G100.meta
-rw-r--r-- 1 ubuntu ubuntu  236049 Nov 20 08:05 san_G100.txt
-rw-r--r-- 1 ubuntu ubuntu    5346 Nov 20 08:04 san_run.py
-rw-r--r-- 1 ubuntu ubuntu    1221 Nov 20 08:05 san_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10590 Nov 20 08:05 san_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:05 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 08:29 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1393 Nov 20 08:07 summarize_rows.py
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:04 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    1197 Nov 20 08:03 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5158 Nov 20 08:04 uci_options.txt
```
