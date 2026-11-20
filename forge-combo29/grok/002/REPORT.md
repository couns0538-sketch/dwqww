S28 keeps a quiet from-to history for the cheapest cheaper enemy attacker of the origin: none, pawn, minor, or rook.
IdeaS28 is a check option, default false. There is no spin. The stored value is added in full, and no constant is added for being attacked.
The read and the write use the same sites as ThreatHistory. With the option false both return before they touch the table.

EXISTS: no. ThreatHistory at forge-combo29/src/search.cpp:97, indexed by quiet_threat_index at forge-combo29/src/search.cpp:290, is the any-cheaper-attack bit on the origin and the destination. S28 is the attacker class on the origin only.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both HONESTY_B.txt and HONESTY_P.txt say PASS.

The table is the output of proof_table.py.

```
step | status | evidence file | result
--- | --- | --- | ---
1 seat | done | SEAT.txt | seat 002 idea 2
2 honesty B | done | HONESTY_B.txt | PASS
2 baseline O | done | sum_B_O.txt | sum 9500069
2 baseline G | done | sum_B_G.txt | sum 18466239
3 patch applies | done | apply_check_mine.txt | MY_APPLY_CHECK_OK
3 honesty P | done | HONESTY_P.txt | PASS
3 off O | done | compare_off_O.txt | differ 0
3 off G | done | compare_off_G.txt | differ 0
3 on O | done | compare_on_O.txt | differ 200
3 sanitizer | done | asan_g100.meta | clean, scratch reported
3 match | done | match_s28.parsed.txt | games 1106
4 partner apply | done | apply_check_partner.txt | PARTNER_APPLY_CHECK_OK
4 partner off | done | partner_off_vs_B.txt | differ 0
4 partner on rows | done | partner_on_vs_rows.txt | equal to partner rows
4 partner on vs B | done | partner_on_vs_B.txt | differ 200
4 partner match | done | partner_match.parsed.txt | games 600
5 report | done | REPORT.md | this file
```

Proof (1). HONESTY_P.txt: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

Proof (2). compare_off_O.txt: 200 compared, differ 0. compare_off_G.txt: 353 compared, differ 0. Sums 9500069 and 18466239.

Proof (3). compare_on_O.txt: 200 compared, differ 200, equal 0. sum_P_on_O.txt: sum 10100354, first three 19410 / 23996 / 57416. prediction.txt said 9100000, wrong below 6500000 or above 13000000. 10100354 is inside that range.

Proof (4). uci_options.py printed FOUND option name IdeaS28 type check default false. The line is in P_uci.txt.

Proof (5). asan_g100.meta: asan_symbol_count 35, sanitizer_lines 0, 100 positions finished at depth 10 with IdeaS28 true. asan_nm_count.txt is 35. The same asan_run.py on the scratch build, which reads one past the end of a four-int heap array when the FEN is 8/8/8/8/8/8/8/K6k w - - 0 1, wrote asan_scratch.sanitizer.txt: ERROR: AddressSanitizer: heap-buffer-overflow.

Match. parse_match.py on match_s28.out: elo 2.83, err 10.89, games 1106, wins 335, losses 326, draws 445. The whole interval is not below 0. prediction.txt said +4, wrong below -20 or above +25. 1106 PGN results. fastchess exit 0. No unknown-option line in the output.

Partner 052. git apply --check of partner_052_idea.patch.txt on the base commit printed PARTNER_APPLY_CHECK_OK. Rebuilt binary sha256 b97bffae5387c6fdc209caef3724679d803864680a9f883ef87801adf7892312, the same sha256 as in the partner's P_on_O.meta. Honesty PASS. Switch false: differ 0 of 200 against exe B. Switch true: differ 0 of 200 against the partner's P_on_O.rows, sum 10163822, and differ 200 of 200 against exe B, which is what the partner claimed. Verdict: CONFIRMS. The extra match is mine, on 300 R openings, both colours, 600 games: elo -1.16, err 9.5, games 600. The partner did not publish that match.

Suspicions, not proven. My on-sum is 10100354 and the partner's is 10163822. The class functions differ on a king: I return class 0 because a king has SEE value 0, and the partner can return class 1 when a pawn attacks the king. I did not isolate that as the only cause. The R match reports Draws 58 and DrawRatio 83.67% in the same fastchess block. I did not work out what DrawRatio counts.

What I did NOT do. No spin option. I did not re-run the partner's G depth-12 set. I did not replay the partner's 1106-game match. Seat 102 had no branch. No pull request. The scratch read is not in idea.patch.txt.

What I am NOT sure about. The off path adds a function that returns 0. The node counts matched exactly. I did not compare the generated instructions. A queen-only attack stays class 0, as the four classes name none, pawn, minor, and rook.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/002/stamps.txt
?? forge-combo29/grok/002/HONESTY_PARTNER.txt
?? forge-combo29/grok/002/PARTNER_bench11.meta
?? forge-combo29/grok/002/PARTNER_bench11.txt
?? forge-combo29/grok/002/PARTNER_bench13.meta
?? forge-combo29/grok/002/PARTNER_bench13.txt
?? forge-combo29/grok/002/PARTNER_bench16.meta
?? forge-combo29/grok/002/PARTNER_bench16.txt
?? forge-combo29/grok/002/PARTNER_off_O_d12.meta
?? forge-combo29/grok/002/PARTNER_off_O_d12.nodes.txt
?? forge-combo29/grok/002/PARTNER_off_O_d12.raw.txt
?? forge-combo29/grok/002/PARTNER_on_O_d12.meta
?? forge-combo29/grok/002/PARTNER_on_O_d12.nodes.txt
?? forge-combo29/grok/002/PARTNER_on_O_d12.raw.txt
?? forge-combo29/grok/002/PARTNER_perft5.meta
?? forge-combo29/grok/002/PARTNER_perft5.txt
?? forge-combo29/grok/002/REPORT.md
?? forge-combo29/grok/002/RESULT.txt
?? forge-combo29/grok/002/apply_check_mine.txt
?? forge-combo29/grok/002/apply_check_partner.txt
?? forge-combo29/grok/002/compare_partner_rows.py
?? forge-combo29/grok/002/partner_052_P_on_O.rows
?? forge-combo29/grok/002/partner_052_idea.patch.txt
?? forge-combo29/grok/002/partner_match.err
?? forge-combo29/grok/002/partner_match.meta
?? forge-combo29/grok/002/partner_match.out
?? forge-combo29/grok/002/partner_match.parsed.txt
?? forge-combo29/grok/002/partner_match.pgn
?? forge-combo29/grok/002/partner_off_vs_B.txt
?? forge-combo29/grok/002/partner_on_vs_B.txt
?? forge-combo29/grok/002/partner_on_vs_rows.txt
?? forge-combo29/grok/002/proof_table.py
?? forge-combo29/grok/002/proof_table.txt
?? forge-combo29/grok/002/report_numbers.py
?? forge-combo29/grok/002/sum_PARTNER_on_O.txt
```

ls -la

```
total 10072
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 09:14 apply_check_mine.txt
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:14 apply_check_partner.txt
-rw-r--r-- 1 ubuntu ubuntu    1017 Nov 20 08:07 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  131520 Nov 20 08:07 asan_g100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_g100.sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    4661 Nov 20 08:06 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu    1051 Nov 20 08:06 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu   10198 Nov 20 08:06 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     566 Nov 20 08:06 asan_scratch.sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 07:58 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 07:58 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     319 Nov 20 07:59 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4491 Nov 20 08:02 B_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  549589 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2496 Nov 20 08:01 B_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  308970 Nov 20 08:01 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     323 Nov 20 07:59 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1568 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:06 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1859 Nov 20 09:09 compare_partner_rows.py
-rw-r--r-- 1 ubuntu ubuntu    4578 Nov 20 08:01 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu    1284 Nov 20 08:07 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu     358 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4673 Nov 20 07:58 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu     361 Nov 20 09:10 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     358 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   11755 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1883 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 match_s28.err
-rw-r--r-- 1 ubuntu ubuntu     309 Nov 20 08:15 match_s28.meta
-rw-r--r-- 1 ubuntu ubuntu  138264 Nov 20 08:15 match_s28.out
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 08:17 match_s28.parsed.txt
-rw-r--r-- 1 ubuntu ubuntu 4620458 Nov 20 08:14 match_s28.pgn
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:06 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1186 Nov 20 08:17 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu   11477 Nov 20 09:09 partner_052_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   15760 Nov 20 09:09 partner_052_P_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu     320 Nov 20 09:10 PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     320 Nov 20 09:10 PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     322 Nov 20 09:10 PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_match.err
-rw-r--r-- 1 ubuntu ubuntu     311 Nov 20 09:13 partner_match.meta
-rw-r--r-- 1 ubuntu ubuntu   70402 Nov 20 09:13 partner_match.out
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 09:14 partner_match.parsed.txt
-rw-r--r-- 1 ubuntu ubuntu 2123492 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 09:10 PARTNER_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2496 Nov 20 09:10 PARTNER_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  308876 Nov 20 09:10 PARTNER_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:10 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 09:10 PARTNER_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2499 Nov 20 09:10 PARTNER_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  308823 Nov 20 09:10 PARTNER_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 09:10 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     231 Nov 20 09:10 partner_on_vs_rows.txt
-rw-r--r-- 1 ubuntu ubuntu     326 Nov 20 09:10 PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 08:04 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 08:04 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     319 Nov 20 08:04 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:04 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4491 Nov 20 08:04 P_off_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  550161 Nov 20 08:04 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     910 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2496 Nov 20 08:04 P_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309158 Nov 20 08:04 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     909 Nov 20 08:04 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2494 Nov 20 08:04 P_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309362 Nov 20 08:04 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     323 Nov 20 08:04 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     603 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3944 Nov 20 09:15 proof_table.py
-rw-r--r-- 1 ubuntu ubuntu    1348 Nov 20 09:15 proof_table.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:04 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    4978 Nov 20 08:04 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   19846 Nov 20 08:08 R.epd
-rw-r--r-- 1 ubuntu ubuntu   13514 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1019 Nov 20 08:17 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     148 Nov 20 08:08 R.meta
-rw-r--r-- 1 ubuntu ubuntu    1979 Nov 20 08:07 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     113 Nov 20 08:06 sum_B_G.txt
-rw-r--r-- 1 ubuntu ubuntu     111 Nov 20 08:06 sum_B_O.txt
-rw-r--r-- 1 ubuntu ubuntu     959 Nov 20 07:59 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     121 Nov 20 09:10 sum_PARTNER_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:06 sum_P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 08:06 sum_P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 08:06 sum_P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    2304 Nov 20 08:01 uci_io.py
-rw-r--r-- 1 ubuntu ubuntu    1473 Nov 20 08:03 uci_options.py
```
