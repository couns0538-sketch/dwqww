Idea S20, option IdeaS20: two-regime probcut, off by default, so the old witness block is unchanged.
Surplus (static eval at least beta plus ProbcutMargin) confirms one non-losing tactical move; a gap requires the exchange to cover the whole shortfall to the raised bound.
Quiescence may reject a try and cannot cut. The real search is at least IdeaS20_MinDepth plies (default 2). Spins IdeaS20_Reduction default 4 and IdeaS20_SeeFloor default 0.

EXISTS: no. Today's probcut is one regime at forge-combo29/src/search.cpp:1745. It does not split surplus from gap, and at depth 5 the witness is depth minus 4, which is one ply.

Honesty, exe B and exe P, no setoption:
bench 11 nodes 312866 expected 312866 PASS
bench 13 nodes 862329 expected 862329 PASS
bench 16 nodes 3024920 expected 3024920 PASS
go perft 5 nodes 4865609 expected 4865609 PASS
ALL PASS

Table from emit (this file is the pasted script output of the numbers above and below):

step | status | evidence | result
--- | --- | --- | ---
STEP 1 seat | done | SEAT.txt | seat 019 idea 19 model Grok 4.7
STEP 2 honesty B | done | HONESTY_B.txt | bench 11 nodes 312866 expected 312866 PASS | bench 13 nodes 862329 expected 862329 PASS | bench 16 nodes 3024920 expected 3024920 PASS | go perft 5 nodes 4865609 expected 4865609 PASS | ALL PASS
STEP 2 O and G | done | BASELINE_OG.txt | O positions 200 sum 9500069 expected 9500069 PASS | O first3 41311 / 24872 / 28574 expected 41311 / 24872 / 28574 PASS | G positions 353 sum 18466239 expected 18466239 PASS
STEP 3 prediction | done | prediction.txt | O sum 9850000 wrong outside 9200000..11000000; elo 6 wrong outside -30..45
STEP 3 patch applies | done | apply_check.txt | APPLY_CHECK_OK
proof 1 honesty P | done | HONESTY_P.txt | bench 11/13/16 and perft 5 PASS
proof 2 switch off | done | PROOF_NODES.txt | O differ 0 of 200; G differ 0 of 353
proof 3 switch on | done | PROOF_NODES.txt | on O differ 195 of 200 sum 9452727
proof 4 uci options | done | UCI_OPTIONS.txt | PASS option name IdeaS20 type check default false | PASS option name IdeaS20_MinDepth type spin default 2 min 2 max 8 | PASS option name IdeaS20_Reduction type spin default 4 min 1 max 8 | PASS option name IdeaS20_SeeFloor type spin default 0 min -200 max 200
proof 5 sanitizer | done | SANITIZER.txt | real nm nm_asan_count=37 asan_or_ubsan_lines 0 | scratch nm nm_asan_count=37 asan_or_ubsan_lines 3 | scratch_has_heap_overflow YES
test match | done | MATCH.txt | Elo: 2.20 +/- 9.83, nElo: 4.58 +/- 20.48 games 1106
partner 069 | done | partner_compare.txt | CONFIRMS; honesty partner_h_bench11.txt nodes 312866 expected 312866 PASS | honesty partner_h_bench13.txt nodes 862329 expected 862329 PASS | honesty partner_h_bench16.txt nodes 3024920 expected 3024920 PASS | honesty partner_h_perft5.txt nodes 4865609 expected 4865609 PASS | off_vs_B differ 0 of 200 sum 9500069 PASS | on_vs_partner_rows differ 0 of 200 sum 9581616 partner_sum 9581616 PASS | on_vs_B differ 194 of 200 | honesty_all PASS
partner R match | done | partner_match.log | Elo: -3.47 +/- 11.12, nElo: -8.69 +/- 27.80

Proofs:
(1) exe P honesty, no setoption: bench 11 nodes 312866 expected 312866 PASS | bench 13 nodes 862329 expected 862329 PASS | bench 16 nodes 3024920 expected 3024920 PASS | go perft 5 nodes 4865609 expected 4865609 PASS | ALL PASS
(2) S14 and IdeaS20 false: O differ 0 of 200 sum 9500069; G differ 0 of 353 sum 18466239. Position rows equal exe B.
(3) S14 and IdeaS20 true: on O differ 195 of 200 sum 9452727. First three 36080 / 24883 / 28415. The code runs.
(4) uci lists the new options at their defaults:
PASS option name IdeaS20 type check default false
PASS option name IdeaS20_MinDepth type spin default 2 min 2 max 8
PASS option name IdeaS20_Reduction type spin default 4 min 1 max 8
PASS option name IdeaS20_SeeFloor type spin default 0 min -200 max 200
(5) Sanitizer build, IdeaS20 true, first 100 of G at depth 10: real nm nm_asan_count=37 asan_or_ubsan_lines 0 | scratch nm nm_asan_count=37 asan_or_ubsan_lines 3 | scratch_has_heap_overflow YES. nm count 37 is above 0. The scratch copy, one heap read past a 2-int array on FEN 7k/8/8/8/8/8/8/K7 w - - 0 1, run through measure_depth.py, reports heap-buffer-overflow.

Match, exe P on versus exe P off, S14, Threads 1, Hash 16, 20000 nodes, openings O+G, both colours:
finished_games 1106
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: 2.20 +/- 9.83, nElo: 4.58 +/- 20.48
LOS: 66.95 %, DrawRatio: 65.28 %, PairsRatio: 1.11
Games: 1106, Wins: 342, Losses: 335, Draws: 429, Points: 556.5 (50.32 %)
Ptnml(0-2): [12, 79, 361, 92, 9], WL/DD Ratio: 1.80
--------------------------------------------------
Finished match

Prediction in prediction.txt was O sum 9850000 (wrong below 9200000 or above 11000000) and Elo 6 (wrong below -30 or above 45). Actual O sum 9452727 and Elo 2.20 are inside those ranges. The sum moved down, not up.

Partner: seat 069, the next seat with idea 19 that had a branch at minute 75 (119 had none). Fetched 9f45537abf508874880059d0042df82352146a25. git apply --check passed. Their IdeaS20 off matched exe B on all 200 O rows. Their IdeaS20 on matched their own P_on_O_d12.rows.tsv on all 200 rows (sum 9581616, 194 differ from exe B, the count in their compare_on_O.txt). Honesty numbers matched. Verdict: CONFIRMS.
Partner switch on versus off, 300 R openings, both colours, same harness settings:
Results of on vs off (20000 nodes, 1t, 16MB, R.epd):
Elo: -3.47 +/- 11.12, nElo: -8.69 +/- 27.80
LOS: 27.00 %, DrawRatio: 80.00 %, PairsRatio: 0.88
Games: 600, Wins: 257, Losses: 263, Draws: 80, Points: 297.0 (49.50 %)
Ptnml(0-2): [7, 25, 240, 23, 5], WL/DD Ratio: 14.00
--------------------------------------------------
Finished match
Total Time: 00:03:17 (hours:minutes:seconds)

suspicions, not proven:
The depth-12 sum fell by 47342 nodes instead of rising. Inside the predicted range, and 195 positions did change, so this is not a dead option. Seat 069's surplus test uses the improving-adjusted bound and their tree grew to 9581616. The two readings are not the same patch.
The fixed-node interval 2.20 +/- 9.83 includes negative values. Nothing in the games shows a rules bug; mates and the fifty-move and repetition draws are legal ends.

what I did NOT do:
Did not re-run seat 069's sanitizer and did not replay their 1106-game O+G match. Did not build seat 119. Did not retune MinDepth, Reduction, or SeeFloor after the match. Did not open a pull request.

what I am NOT sure about:
Whether "clears beta by the full margin" includes the existing minus 50 times improving term. I treated the full margin as ProbcutMargin and skipped the band between that and the raised bound. Seat 069 folded improving into the surplus test.
Whether "confirm with one" means the first tactical candidate only. I try candidates in the existing quiescence order until one real search meets the bound.
The +2.20 Elo is not separated from noise.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/019/partner_step4.sh
 M forge-combo29/grok/019/stamps.txt
?? config.json
?? forge-combo29/grok/019/REPORT.md
?? forge-combo29/grok/019/RESULT.txt
?? forge-combo29/grok/019/partner_apply.txt
?? forge-combo29/grok/019/partner_checks.txt
?? forge-combo29/grok/019/partner_compare.py
?? forge-combo29/grok/019/partner_compare.txt
?? forge-combo29/grok/019/partner_files.txt
?? forge-combo29/grok/019/partner_h_bench11.txt
?? forge-combo29/grok/019/partner_h_bench11.txt.meta
?? forge-combo29/grok/019/partner_h_bench13.txt
?? forge-combo29/grok/019/partner_h_bench13.txt.meta
?? forge-combo29/grok/019/partner_h_bench16.txt
?? forge-combo29/grok/019/partner_h_bench16.txt.meta
?? forge-combo29/grok/019/partner_h_perft5.txt
?? forge-combo29/grok/019/partner_h_perft5.txt.meta
?? forge-combo29/grok/019/partner_id.txt
?? forge-combo29/grok/019/partner_match.log
?? forge-combo29/grok/019/partner_match.pgn
?? forge-combo29/grok/019/partner_match.pid
?? forge-combo29/grok/019/partner_match.runner
?? forge-combo29/grok/019/partner_match.sh
?? forge-combo29/grok/019/partner_new_options.txt
?? forge-combo29/grok/019/partner_off_O.raw.txt
?? forge-combo29/grok/019/partner_off_O.raw.txt.meta
?? forge-combo29/grok/019/partner_off_O.rows.tsv
?? forge-combo29/grok/019/partner_on_O.raw.txt
?? forge-combo29/grok/019/partner_on_O.raw.txt.meta
?? forge-combo29/grok/019/partner_on_O.rows.tsv
?? forge-combo29/grok/019/partner_opt_off.txt
?? forge-combo29/grok/019/partner_opt_on.txt
?? forge-combo29/grok/019/partner_pick.txt
?? forge-combo29/grok/019/partner_prove.sh
?? forge-combo29/grok/019/partner_src/
?? forge-combo29/grok/019/partner_status.txt
?? forge-combo29/grok/019/partner_uci.txt
?? forge-combo29/grok/019/partner_using_check.txt

$ ls -la forge-combo29/grok/019
total 10340
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:06 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  136103 Nov 20 08:04 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     925 Nov 20 08:04 asan_G100.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    6407 Nov 20 08:04 asan_G100.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu   10204 Nov 20 08:05 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     387 Nov 20 08:06 asan_scratch.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:57 BASELINE_OG.txt
-rw-r--r-- 1 ubuntu ubuntu  566352 Nov 20 07:57 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     887 Nov 20 07:57 B_G_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22915 Nov 20 07:57 B_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  318452 Nov 20 07:57 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 07:57 B_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 07:57 B_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu    2434 Nov 20 08:02 compare_proof.py
-rw-r--r-- 1 ubuntu ubuntu     984 Nov 20 08:01 design.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:57 G.epd
-rw-r--r-- 1 ubuntu ubuntu     105 Nov 20 08:53 handoff60.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:56 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 07:56 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:56 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 07:56 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:56 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 07:56 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:56 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 07:56 honesty_b_perft5.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu    2211 Nov 20 07:55 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 07:56 HONESTY_B.txt
-rwxr-xr-x 1 ubuntu ubuntu     819 Nov 20 08:01 honesty_one.sh
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:01 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:01 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:01 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:01 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7663 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1955 Nov 20 08:07 make_R.py
-rw-r--r-- 1 ubuntu ubuntu  104686 Nov 20 08:12 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 4572644 Nov 20 08:12 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu       5 Nov 20 08:06 match.pid
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 match_runner.out
-rw-r--r-- 1 ubuntu ubuntu     357 Nov 20 08:15 MATCH.txt
-rwxr-xr-x 1 ubuntu ubuntu    5613 Nov 20 08:00 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:57 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:06 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 08:01 opt_off.txt
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:01 opt_on.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu       8 Nov 20 09:09 partner_checks.txt
-rw-r--r-- 1 ubuntu ubuntu    2077 Nov 20 09:10 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     416 Nov 20 09:10 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    1426 Nov 20 09:07 partner_files.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:09 partner_h_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:09 partner_h_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:09 partner_h_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:09 partner_h_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       4 Nov 20 09:07 partner_id.txt
-rw-r--r-- 1 ubuntu ubuntu   52845 Nov 20 09:13 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 2327516 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:10 partner_match.pid
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_match.runner
-rwxr-xr-x 1 ubuntu ubuntu    1062 Nov 20 09:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 09:09 partner_new_options.txt
-rw-r--r-- 1 ubuntu ubuntu  318411 Nov 20 09:09 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 09:09 partner_off_O.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 09:09 partner_off_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  318596 Nov 20 09:10 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 09:10 partner_on_O.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15783 Nov 20 09:10 partner_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 09:09 partner_opt_off.txt
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 09:09 partner_opt_on.txt
-rwxr-xr-x 1 ubuntu ubuntu     852 Nov 20 08:44 partner_pick.py
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:07 partner_pick.txt
-rwxr-xr-x 1 ubuntu ubuntu    3091 Nov 20 09:09 partner_prove.sh
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:07 partner_src
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 09:09 partner_status.txt
-rwxr-xr-x 1 ubuntu ubuntu    1077 Nov 20 08:54 partner_step4.sh
-rw-r--r-- 1 ubuntu ubuntu    5037 Nov 20 09:09 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu      20 Nov 20 09:09 partner_using_check.txt
-rw-r--r-- 1 ubuntu ubuntu  566384 Nov 20 08:01 Poff_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 08:01 Poff_G_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22915 Nov 20 08:01 Poff_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  318592 Nov 20 08:01 Poff_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:01 Poff_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 08:01 Poff_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  318671 Nov 20 08:02 Pon_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 08:02 Pon_O_d12.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15781 Nov 20 08:02 Pon_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     722 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     366 Nov 20 08:02 PROOF_NODES.txt
-rw-r--r-- 1 ubuntu ubuntu   20086 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu    8752 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 08:07 R.meta
-rwxr-xr-x 1 ubuntu ubuntu    1190 Nov 20 08:06 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 08:06 SANITIZER.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:05 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 07:57 sets.meta
-rw-r--r-- 1 ubuntu ubuntu   10795 Nov 20 07:57 smoke_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 07:57 smoke_O.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     251 Nov 20 07:57 smoke_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     347 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 07:57 summarize_baseline.py
-rw-r--r-- 1 ubuntu ubuntu     682 Nov 20 08:15 summarize_match.py
-rw-r--r-- 1 ubuntu ubuntu    1225 Nov 20 08:06 summarize_sanitizer.py
-rw-r--r-- 1 ubuntu ubuntu     254 Nov 20 08:01 UCI_OPTIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 08:01 uci_p.txt
```
