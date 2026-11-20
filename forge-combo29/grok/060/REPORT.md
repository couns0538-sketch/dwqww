Idea S24 sizes the overlap back into the previous root aspiration window by how much recent root scores have been moving: none when they are steady, up to half the old width when they swing, and the same rule on a fail-high and a fail-low.
I built that as the check option IdeaS24, default false, plus IdeaS24_Samples (default 4 finished scores) and IdeaS24_Swing (default 32, the centipawn standard deviation at which the overlap reaches half the old width).
With the switch off, a mate score, or a window that is already open, the fail update is the code that was already there. The change is only in idea.patch.txt. `git apply --check` on a fresh checkout of 6b98f2170 printed MY_APPLY_CHECK_OK.

EXISTS: no. search.cpp already has AspCappedReopen and AspArmLate, which are S23 and S25. It does not scale the overlap by the spread of recent root scores. Today's fail-low sets the other bound to the midpoint, and today's fail-high leaves the other bound where it is.

Honesty, no setoption, both the plain exe and the patched exe: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Files HONESTY_B.txt and HONESTY_P.txt.

The machine has AVX-512F/BW/CD/DQ/VL and BMI2, so the release build is g++ 13.3 with the default march x86-64-v4 and FORGE_PORTABLE left off. S14, Threads 1, Hash 16 on every measured search.

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 060 idea 10
STEP 2 honesty and baseline | done | HONESTY_B.txt proof_B_O_sum.txt proof_B_G_sum.txt | count 200 sum 9500069 first 41311 24872 28574 | count 353 sum 18466239 first 37203 70845 144383
STEP 3 prediction | done | prediction.txt | 9720000 and +3, file not edited
STEP 3 patch | done | idea.patch.txt apply_check.txt | MY_APPLY_CHECK_OK
proof 1 honesty of P | done | HONESTY_P.txt p_honesty/ | bench 11/13/16 and perft 5 match the known nodes
proof 2 switch off | done | proof_off_O.txt proof_off_G.txt | left 200 right 200 differ 0 of 200 first_diff  | left 353 right 353 differ 0 of 353 first_diff 
proof 3 switch on | done | proof_on_O.txt proof_on_O_sum.txt | left 200 right 200 differ 128 of 200 first_diff 1 2 3 6 7 | count 200 sum 9785481 first 40607 24995 49667
proof 4 uci options | done | uci_options.raw | IdeaS24 check false; Samples 4; Swing 32
proof 5 sanitizer | done | asan_G100_d10.meta asan_G100_finding.txt asan_scratch_finding.txt | 35 asan symbols, 0 lines on G100, scratch reports heap-buffer-overflow
STEP 3 match | done | match_stdout.txt match_summary.txt match.pgn | Elo: -9.43 +/- 10.02, nElo: -19.28 +/- 20.48
STEP 4 partner 010 | done | partner_proof_off.txt partner_proof_on.txt partner_match_summary.txt | CONFIRMS; left 200 right 200 differ 0 of 200 first_diff  | Elo: 1.16 +/- 9.50, nElo: 3.39 +/- 27.80
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

That table is the output of report_table.py, which reads the proof files. facts.txt is the output of report_facts.py.

Proof (1). HONESTY_P.txt has nodes 312866, 862329, 3024920, and 4865609.

Proof (2). Switch false against exe B: O differs 0 of 200, G differs 0 of 353. The O sum is 9500069 and the first three are 41311, 24872, 28574. The G sum is 18466239.

Proof (3). Switch true, O depth 12: 128 of 200 positions differ from exe B. Sum 9785481, first three 40607, 24995, 49667. The prediction was 9720000, wrong below 8550000 or above 10900000. 9785481 is inside that range.

Proof (4). uci lists `option name IdeaS24 type check default false`, `option name IdeaS24_Samples type spin default 4 min 2 max 16`, and `option name IdeaS24_Swing type spin default 32 min 1 max 400`.

Proof (5). The sanitizer build's meta line is `nm -C /tmp/forge-asan/forge | grep -c __asan_ 35`. The first 100 of G at depth 10 with the switch true produced 0 sanitizer lines. The same runner on a scratch copy, which reads one past a 4-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 1`, reported `ERROR: AddressSanitizer: heap-buffer-overflow` in apply_position. sanitizer=clean.

Match. IdeaS24 true versus false, both the patched exe, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, rounds 553 and games 2, concurrency 3. fastchess from its GitHub repository. 1106 finished games. Elo of s24on versus s24off: -9.43 +/- 10.02. Wins 329, losses 359, draws 418. The prediction was +3, wrong if the point estimate is below -30 or above +30. -9.43 is inside that range. The interval is about -19.45 to +0.59, so it is not a result below -20 whose whole interval is below 0, and I did not go back into the search code. A first command used rounds 1 and played 2 games; that log is match_probe_2games.txt and is not the match.

Partner. Seat 110 has no branch. The next seat with this idea is 010, commit f6a17dc5cea473249fe8f90fa7a2c057988d76c6. Their option is also IdeaS24. apply --check printed PARTNER_APPLY_CHECK_OK. Honesty matched the four known node counts. Switch false differs 0 of 200 from exe B (sum 9500069). Switch true differs 0 of 200 from their p_on_O_d12.rows (sum 9569208, first three 40604, 42076, 33776), which is the sum they wrote. Verdict: CONFIRMS. The required extra match, their switch on versus off, 300 R openings, both colours, 600 games: Elo 1.16 +/- 9.50. I did not replay their 1106-game O+G match. They report that one as elo -1.88 err 10.38.

suspicions, not proven. The -9 Elo can be noise: the interval still reaches above 0. A lot of games ended by threefold repetition, the fifty-move rule, or insufficient mating material, which are legal finishes. I did not count how many of the losses were those rather than mates. An overlap of 0 puts the other bound on the edge of the old window, so the next try can fail the other way and only then widen; I did not count how often that happens.

what I did NOT do. I did not turn IdeaS24 on together with AspCappedReopen. In this patch AspCappedReopen keeps today's branch if both are set. I did not play a second match of my own patch on R, because 010 had a patch. I did not rebuild the partner match on O and G. I did not change prediction.txt after the first push.

what I am NOT sure about. The idea says "variance" and "bounce". I used the integer standard deviation in centipawns, with half-width overlap at 32. Seat 010 used the mean square in centipawns squared, with a steady floor of 16 and a full overlap at 400. Both read the same sentence and they do not search the same tree (their on-sum is 9569208, mine is 9785481). I am not sure which reading is the one the sources meant. I am sure the off path of this patch matches today's nodes.

times: see stamps.txt

```
git status --short
```

 M forge-combo29/grok/060/stamps.txt
?? forge-combo29/grok/060/PARTNER_HONESTY.txt
?? forge-combo29/grok/060/REPORT.md
?? forge-combo29/grok/060/RESULT.txt
?? forge-combo29/grok/060/apply_check.txt
?? forge-combo29/grok/060/facts.txt
?? forge-combo29/grok/060/partner.patch.txt
?? forge-combo29/grok/060/partner_claimed_on.tsv
?? forge-combo29/grok/060/partner_commit.txt
?? forge-combo29/grok/060/partner_config.json
?? forge-combo29/grok/060/partner_design.txt
?? forge-combo29/grok/060/partner_honesty/
?? forge-combo29/grok/060/partner_match.parse
?? forge-combo29/grok/060/partner_match.pgn
?? forge-combo29/grok/060/partner_match_stdout.txt
?? forge-combo29/grok/060/partner_match_summary.txt
?? forge-combo29/grok/060/partner_off_O.meta
?? forge-combo29/grok/060/partner_off_O.raw
?? forge-combo29/grok/060/partner_off_O.sum
?? forge-combo29/grok/060/partner_off_O.tsv
?? forge-combo29/grok/060/partner_off_sum.txt
?? forge-combo29/grok/060/partner_on_O.meta
?? forge-combo29/grok/060/partner_on_O.raw
?? forge-combo29/grok/060/partner_on_O.rows
?? forge-combo29/grok/060/partner_on_O.sum
?? forge-combo29/grok/060/partner_on_O.tsv
?? forge-combo29/grok/060/partner_on_sum.txt
?? forge-combo29/grok/060/partner_proof_off.txt
?? forge-combo29/grok/060/partner_proof_on.txt
?? forge-combo29/grok/060/partner_rows_to_tsv.py
?? forge-combo29/grok/060/report_facts.py
?? forge-combo29/grok/060/report_table.py
?? forge-combo29/grok/060/run_partner.sh
?? forge-combo29/grok/060/table.txt

```
ls -la
```

total 4948
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:14 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     488 Nov 20 08:08 asan_finding.py
-rw-r--r-- 1 ubuntu ubuntu     939 Nov 20 08:08 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131704 Nov 20 08:08 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu    1700 Nov 20 08:08 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 08:08 asan_G100_finding.txt
-rw-r--r-- 1 ubuntu ubuntu     574 Nov 20 08:08 asan_nm.py
-rw-r--r-- 1 ubuntu ubuntu     551 Nov 20 08:09 asan_scratch_finding.txt
-rw-r--r-- 1 ubuntu ubuntu     962 Nov 20 08:09 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    9979 Nov 20 08:09 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu      27 Nov 20 08:09 asan_scratch.tsv
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:02 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:02 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:02 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     859 Nov 20 08:04 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  549945 Nov 20 08:04 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu    6285 Nov 20 08:04 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     860 Nov 20 08:04 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309071 Nov 20 08:04 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu    3523 Nov 20 08:04 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     957 Nov 20 08:04 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    6886 Nov 20 09:13 config.json
-rw-r--r-- 1 ubuntu ubuntu    1210 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu    3223 Nov 20 09:15 facts.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 G.epd
-rw-r--r-- 1 ubuntu ubuntu     538 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     538 Nov 20 08:07 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    3361 Nov 20 08:02 honesty_run.py
-rw-r--r-- 1 ubuntu ubuntu    9596 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1335 Nov 20 08:03 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 1076846 Nov 20 08:16 match.pgn
-rw-r--r-- 1 ubuntu ubuntu    3465 Nov 20 08:09 match_probe_2games.pgn
-rw-r--r-- 1 ubuntu ubuntu     623 Nov 20 08:09 match_probe_2games.txt
-rw-r--r-- 1 ubuntu ubuntu  138076 Nov 20 08:16 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     814 Nov 20 08:17 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     367 Nov 20 08:18 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1386 Nov 20 08:05 options_dump.py
-rw-r--r-- 1 ubuntu ubuntu    3524 Nov 20 09:10 partner_claimed_on.tsv
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:10 partner_commit.txt
-rw-r--r-- 1 ubuntu ubuntu    6873 Nov 20 09:13 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu    1641 Nov 20 09:10 partner_design.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:10 partner_honesty
-rw-r--r-- 1 ubuntu ubuntu     538 Nov 20 09:10 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 09:10 partner_match.parse
-rw-r--r-- 1 ubuntu ubuntu  459371 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   63139 Nov 20 09:13 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     354 Nov 20 09:13 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 09:10 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309315 Nov 20 09:10 partner_off_O.raw
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:10 partner_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu    3523 Nov 20 09:10 partner_off_O.tsv
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 09:10 partner_off_sum.txt
-rw-r--r-- 1 ubuntu ubuntu     891 Nov 20 09:10 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309730 Nov 20 09:10 partner_on_O.raw
-rw-r--r-- 1 ubuntu ubuntu    4781 Nov 20 09:10 partner_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:10 partner_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu    3524 Nov 20 09:10 partner_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 09:10 partner_on_sum.txt
-rw-r--r-- 1 ubuntu ubuntu   10458 Nov 20 09:10 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      47 Nov 20 09:10 partner_proof_off.txt
-rw-r--r-- 1 ubuntu ubuntu      47 Nov 20 09:10 partner_proof_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1046 Nov 20 09:02 partner_rows_to_tsv.py
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:02 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 perft5.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:05 p_honesty
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  549914 Nov 20 08:05 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu    6285 Nov 20 08:05 P_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309073 Nov 20 08:05 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu    3523 Nov 20 08:05 P_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309382 Nov 20 08:05 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu    3523 Nov 20 08:05 P_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     653 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      48 Nov 20 08:07 proof_B_G_sum.txt
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 08:07 proof_B_O_sum.txt
-rw-r--r-- 1 ubuntu ubuntu      47 Nov 20 08:07 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      47 Nov 20 08:07 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 08:07 proof_on_O_sum.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 08:07 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1034 Nov 20 09:15 report_facts.py
-rw-r--r-- 1 ubuntu ubuntu    6708 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2163 Nov 20 09:15 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19135 Nov 20 08:03 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1211 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    2686 Nov 20 09:02 run_partner.sh
-rwxr-xr-x 1 ubuntu ubuntu    1124 Nov 20 08:18 run_r_match.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:07 sanitizer_fen.epd
-rw-r--r-- 1 ubuntu ubuntu    5981 Nov 20 08:18 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     797 Nov 20 08:04 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1484 Nov 20 09:15 table.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:05 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 08:05 uci_options.raw
