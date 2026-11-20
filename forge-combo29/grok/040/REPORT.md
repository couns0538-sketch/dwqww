IdeaK1 is hash probcut. Off the principal line, a hash lower bound or an exact bound from a search at least four plies shallower, and at least 120 centipawns above beta, returns beta plus that margin.
The check option IdeaK1 defaults to false. The spin IdeaK1_Margin defaults to 120, range 0 to 1000.
While IdeaK1 is false the new block is not entered, so the search is the one the engine already had.

EXISTS: no. In search.cpp the ordinary hash cutoff returns a stored score only when the stored depth is at least the current depth. The block commented "ProbCut: a good capture" searches a capture; it does not cut on a shallow hash bound.

Honesty, no setoption, exe B and exe P. Both files are the same four lines:

bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK

Table, the pasted output of report_table.py:

step | done / partly / not done | evidence file | result
1 seat | done | SEAT.txt, stamps.txt | seat 040
2 two builds, honesty, O and G sums | done | HONESTY_B.txt, O_d12_B.nodes, G_d12_B.nodes | O sum 9500069; G sum 18466239
3 idea, five proofs, 1106-game match | done | proof_off_O.txt, proof_off_G.txt, proof_on_O.txt, match_summary.txt | positions 200 equal 200 differ 0; positions 353 equal 353 differ 0; positions 200 equal 0 differ 200; Elo: -10.37 +/- 10.77, nElo: -19.74 +/- 20.48
4 partner 090 | done | partner_off_vs_B.txt, partner_on_vs_claim.txt, partner_match_summary.txt | off positions 200 equal 200 differ 0; on positions 200 equal 200 differ 0
5 report | done | REPORT.md, RESULT.txt | this report

Proofs on exe P.

(1) Honesty with no setoption, unchanged. HONESTY_P.txt:

bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK

(2) S14 and IdeaK1 false. Position by position against exe B. proof_off_O.txt and proof_off_G.txt:

positions 200 equal 200 differ 0
sum_left 9500069 sum_right 9500069

positions 353 equal 353 differ 0
sum_left 18466239 sum_right 18466239

(3) S14 and IdeaK1 true, margin 120. O depth 12 against exe B. First two lines of proof_on_O.txt:

positions 200 equal 0 differ 200
sum_left 9500069 sum_right 9339181

200 of 200 positions differ, so the new block runs. The sum is 9339181.

(4) uci lists the new options. uci_options.py printed:

OK option name IdeaK1 type check default false
OK option name IdeaK1_Margin type spin default 120 min 0 max 1000

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK1 true, first 100 of G at depth 10. The meta line is `nm -C /tmp/forge-asan/forge | grep -c __asan_ = 35`. A search of that raw log for AddressSanitizer, runtime error, SUMMARY, and heap-buffer-overflow found 0 lines, and parse_nodes.py reported 100 positions at depth 10. The same runner on a scratch copy, which reads index 8 of a 4-int heap vector only for the FEN in scratch_fen.txt, reported `ERROR: AddressSanitizer: heap-buffer-overflow` in apply_position. asan_scratch.meta has the same nm count of 35.

git apply --check of idea.patch.txt on a fresh base worktree: git apply --check exit 0.

Match, exe P with IdeaK1 true against exe P with IdeaK1 false, both S14, Threads 1, Hash 16, 20000 nodes, openings OG.epd (553 positions, both colours). match_summary.txt:

--------------------------------------------------
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -10.37 +/- 10.77, nElo: -19.74 +/- 20.48
LOS: 2.94 %, DrawRatio: 59.13 %, PairsRatio: 0.78
Games: 1106, Wins: 313, Losses: 346, Draws: 447, Points: 536.5 (48.51 %)
Ptnml(0-2): [16, 111, 327, 88, 11], WL/DD Ratio: 1.64
--------------------------------------------------
Finished match

The point is -10.37 and the interval reaches above 0, so the "below -20 with the whole interval below 0" check did not fire. I did not change the patch after the match.

Partner is seat 090, the next idea-40 seat that has a branch. Seat 140 does not exist. git apply --check of partner090.patch.txt: git apply --check exit 0. HONESTY_PARTNER.txt:

bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK

Switch false against exe B, partner_off_vs_B.txt:

positions 200 equal 200 differ 0
sum_left 9500069 sum_right 9500069

Switch true against the partner's own O depth-12 nodes (sum 9457615), partner_on_vs_claim.txt:

positions 200 equal 200 differ 0
sum_left 9457615 sum_right 9457615

Their patch reproduces their O rows exactly, and the off rows reproduce exe B. Verdict: CONFIRMS.

Their switch on my 300 R openings, both colours, partner_match_summary.txt:

--------------------------------------------------
Results of on vs off (20000 nodes, 1t, 16MB, R.fens):
Elo: 7.53 +/- 10.19, nElo: 20.56 +/- 27.80
LOS: 92.64 %, DrawRatio: 86.00 %, PairsRatio: 1.47
Games: 600, Wins: 279, Losses: 266, Draws: 55, Points: 306.5 (51.08 %)
Ptnml(0-2): [4, 13, 258, 16, 9], WL/DD Ratio: 18.85
--------------------------------------------------
Finished match

Suspicions, not proven. Returning beta+margin throws away a larger stored score, and a margin of 120 may cut positions the partner's margin of 180 still searches. Either one could explain a small Elo loss. The measured interval still crosses 0.

What I did NOT do. I did not re-run the partner's sanitizer build or their 1106-game OG match. I did not play a second R match of my own patch, because the partner branch existed. I did not try another margin. LeakSanitizer was off (ASAN_OPTIONS detect_leaks=0). No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

What I am NOT sure about. The sign of the Elo. Whether an exact hash bound should count as a lower bound; I counted it, and the partner did not, which is why the two on-sums differ. Whether fastchess DrawRatio is draws divided by games; the Wins, Losses, Draws, and Games lines are the ones I use.

Prediction, not edited. O depth-12 sum on was predicted as 8200000, wrong outside 6000000 to 9400000. Measured 9339181. Elo was predicted as +6, wrong outside -40 to +50. Measured -10.37. Neither range was missed.

times: see stamps.txt

2026-11-20T07:53:35Z STEP 1
2026-11-20T08:01:25Z STEP 2
2026-11-20T08:18:12Z STEP 3
2026-11-20T09:15:36Z STEP 4
2026-11-20T09:15:36Z STEP 5

git status --short
 M forge-combo29/grok/040/stamps.txt
?? forge-combo29/grok/040/HONESTY_PARTNER.txt
?? forge-combo29/grok/040/REPORT.md
?? forge-combo29/grok/040/RESULT.txt
?? forge-combo29/grok/040/honesty_partner_bench11.meta
?? forge-combo29/grok/040/honesty_partner_bench11.txt
?? forge-combo29/grok/040/honesty_partner_bench13.meta
?? forge-combo29/grok/040/honesty_partner_bench13.txt
?? forge-combo29/grok/040/honesty_partner_bench16.meta
?? forge-combo29/grok/040/honesty_partner_bench16.txt
?? forge-combo29/grok/040/honesty_partner_perft5.meta
?? forge-combo29/grok/040/honesty_partner_perft5.txt
?? forge-combo29/grok/040/partner090.patch.txt
?? forge-combo29/grok/040/partner090_on.nodes
?? forge-combo29/grok/040/partner090_on.rows
?? forge-combo29/grok/040/partner_apply_check.txt
?? forge-combo29/grok/040/partner_match_r.log
?? forge-combo29/grok/040/partner_match_r.pgn
?? forge-combo29/grok/040/partner_match_summary.txt
?? forge-combo29/grok/040/partner_off_O.meta
?? forge-combo29/grok/040/partner_off_O.nodes
?? forge-combo29/grok/040/partner_off_O.raw
?? forge-combo29/grok/040/partner_off_vs_B.txt
?? forge-combo29/grok/040/partner_on_O.meta
?? forge-combo29/grok/040/partner_on_O.nodes
?? forge-combo29/grok/040/partner_on_O.raw
?? forge-combo29/grok/040/partner_on_vs_claim.txt
?? forge-combo29/grok/040/report_table.py
?? forge-combo29/grok/040/report_table.txt
?? forge-combo29/grok/040/run_partner_match.sh

ls -la
total 8356
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:09 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     805 Nov 20 08:06 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     578 Nov 20 08:06 asan_G100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu  132321 Nov 20 08:06 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu     719 Nov 20 08:06 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    9992 Nov 20 08:06 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu     661 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1293 Nov 20 08:03 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu     622 Nov 20 08:00 G_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:00 G_d12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  550237 Nov 20 08:00 G_d12_B.raw
-rw-r--r-- 1 ubuntu ubuntu     667 Nov 20 08:04 G_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:04 G_d12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  550502 Nov 20 08:04 G_d12_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:57 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2693 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 09:10 honesty_partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 honesty_partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 09:10 honesty_partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 honesty_partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 09:10 honesty_partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 honesty_partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:10 honesty_partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 honesty_partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 09:10 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:03 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:03 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:04 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:04 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    4386 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1388 Nov 20 08:01 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  106277 Nov 20 08:16 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 3549483 Nov 20 08:16 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     619 Nov 20 08:08 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu    8761 Nov 20 08:08 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     394 Nov 20 08:18 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     623 Nov 20 08:00 O_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:00 O_d12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  309177 Nov 20 08:00 O_d12_B.raw
-rw-r--r-- 1 ubuntu ubuntu     668 Nov 20 08:04 O_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 O_d12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  309491 Nov 20 08:04 O_d12_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu     667 Nov 20 08:04 O_d12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:04 O_d12_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  310001 Nov 20 08:04 O_d12_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     611 Nov 20 08:18 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    1606 Nov 20 07:58 parse_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:09 partner090_on.nodes
-rw-r--r-- 1 ubuntu ubuntu   20045 Nov 20 09:09 partner090_on.rows
-rw-r--r-- 1 ubuntu ubuntu    5477 Nov 20 09:09 partner090.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 09:09 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   53078 Nov 20 09:13 partner_match_r.log
-rw-r--r-- 1 ubuntu ubuntu 1594726 Nov 20 09:13 partner_match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu     388 Nov 20 09:13 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     719 Nov 20 09:10 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:10 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309525 Nov 20 09:10 partner_off_O.raw
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:10 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     718 Nov 20 09:10 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:10 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309892 Nov 20 09:10 partner_on_O.raw
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:10 partner_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:09 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 08:09 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:09 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    7840 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1337 Nov 20 09:16 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     716 Nov 20 09:16 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19193 Nov 20 08:01 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1159 Nov 20 08:08 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1177 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:06 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu    6327 Nov 20 08:05 search_depth.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1103 Nov 20 08:03 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 08:04 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5040 Nov 20 08:04 uci_p.txt
