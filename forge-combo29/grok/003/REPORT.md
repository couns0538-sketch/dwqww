# Seat 003, idea 3, S38

S38 adds a signed fraction of a ply, taken from the correction history, to the reduction of a quiet move: worse recent results reduce more, better results reduce less, and the reduction stays at least zero.
The plain engine already does that when `LmrSignedCorrection` is on. The divisor 64 and the cap of 1 ply were literals, not options.
I added `IdeaS38` (check, default false) which turns on that same adjustment, and the spins `IdeaS38_Divisor` (default 64) and `IdeaS38_Clamp` (default 1). With the check false, and `LmrSignedCorrection` left false, the branch is not taken.

EXISTS: `include/forge/search.hpp:362` `apply_lmr_signed_correction`, called from `src/search.cpp:2003` when `LmrSignedCorrection` is true.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

The table is the output of `report_numbers.py`.

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 003, idea 3, model Grok 4.7, 2026-11-20T07:52:05Z, token 8168252358750
2 honesty B | done | HONESTY_B.txt | 312866 862329 3024920 4865609
2 baseline O | done | O_B.nodes | SUM 9500069
2 baseline G | done | G_B.nodes | SUM 18466239
3 prediction | done | prediction.txt | committed before measuring exe P
3 proof 1 | done | HONESTY_P.txt | 312866 862329 3024920 4865609
3 proof 2 O off | done | compare_O_off.txt | differ 0 of 200
3 proof 2 G off | done | compare_G_off.txt | differ 0 of 353
3 proof 3 O on | done | compare_O_on.txt | differ 3 of 200 SUM 9501220
3 proof 4 | done | uci_p.txt | IdeaS38 false, IdeaS38_Divisor 64, IdeaS38_Clamp 1
3 proof 5 | done | asan_nm.txt asan_G100.raw asan_bug.raw | nm 35 G100_errors 0 bug_errors 1
3 match | done | match.txt | Elo 3.14 +/- 8.26, 1106 games
4 partner rows | done | partner_compare_off.txt partner_compare_on.txt | differ 0 of 200 / differ 3 of 200
4 partner match | done | partner_match.txt | Elo 5.79 +/- 5.52, 600 games
5 report | done | REPORT.md RESULT.txt | this file
```

Proof (1). `HONESTY_P.txt`: bench11=312866, bench13=862329, bench16=3024920, perft5=4865609. No setoption.

Proof (2). S14, Threads 1, Hash 16, `IdeaS38` false. O depth 12: differ 0 of 200, both sums 9500069. G depth 12: differ 0 of 353, both sums 18466239. First three O positions on exe B were 41311, 24872, 28574.

Proof (3). Same settings, `IdeaS38` true, spins left at 64 and 1. O depth 12: differ 3 of 200, sum 9501220 against exe B's 9500069. The positions are 114, 127, and 191.

Proof (4). `uci` lists `option name IdeaS38 type check default false`, `option name IdeaS38_Divisor type spin default 64 min 1 max 4096`, and `option name IdeaS38_Clamp type spin default 1 min 0 max 8`.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, `nm -C` count of `__asan_` is 35. First 100 of G at depth 10 with the switch true: 0 `ERROR: AddressSanitizer` lines and 0 `runtime error:` lines (`ASAN_OPTIONS=detect_leaks=0`). A scratch copy, not in `idea.patch.txt`, reads index 4 of a heap `int[4]` on one FEN. The same runner reports `ERROR: AddressSanitizer: heap-buffer-overflow` in `scratch_read_past`. `git apply --check` of `idea.patch.txt` on the plain base printed `APPLY_CHECK_OK`.

Prediction, committed before any exe P measurement: O depth-12 sum 10200000, wrong outside 8000000..12000000. Measured 9501220, inside that range. Predicted match Elo +6, wrong outside -15..+25.

Match, `IdeaS38` true against false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. Last block of `match.txt`:

```
Results of IdeaS38on vs IdeaS38off (20000 nodes, 1t, 16MB, OG.epd):
Elo: 3.14 +/- 8.26, nElo: 7.79 +/- 20.48
LOS: 77.21 %, DrawRatio: 76.13 %, PairsRatio: 1.06
Games: 1106, Wins: 349, Losses: 339, Draws: 418, Points: 558.0 (50.45 %)
```

The point estimate is inside the prediction range. The interval is not entirely below 0, so I did not go back to hunt a bug for a loss.

Partner is seat 053 (next seat with idea 3; 053 and 103 both had branches). Verdict: CONFIRMS. `git apply --check` of their patch on the plain base printed `PARTNER_APPLY_CHECK_OK`. Their binary's honesty pins match. Switch false: differ 0 of 200 against exe B, sum 9500069, which is what their `P_off_O_d12.sum.txt` says. Switch true: differ 3 of 200, positions 114, 127, 191, sum 9501220, which is what their `cmp_on_O.txt` and `P_on_O_d12.sum.txt` say. `partner_vs_claim.py` compares my rows with the node files they published: off differ 0, on differ 0. Their switch, 300 R openings, both colours, 600 games, last block of `partner_match.txt`:

```
Results of IdeaS38on vs IdeaS38off (20000 nodes, 1t, 16MB, R.epd):
Elo: 5.79 +/- 5.52, nElo: 29.16 +/- 27.80
LOS: 98.01 %, DrawRatio: 93.00 %, PairsRatio: 2.50
Games: 600, Wins: 284, Losses: 274, Draws: 42, Points: 305.0 (50.83 %)
```

suspicions, not proven

The +3.14 Elo and the partner's +5.79 Elo both have intervals that include values near zero. I am not claiming a strength gain. Seat 053's patch is the same gate on the same existing function, with the same defaults, so matching node rows was likely. I did not search non-default divisor or clamp values. Leak detection was off during the sanitizer run.

what I did NOT do

I did not run G at depth 12 with the switch on. I did not play seat 103. I did not test divisor or clamp away from 64 and 1. I did not open a pull request. No `FABLE_TO_grok` file was on the handoff branch at step 1 or at the second fetch (`2026-11-20T08:19:13Z`).

what I am NOT sure about

R positions are plies 15, 22, 29, and so on, from games that are still ongoing at ply 80. Games that end earlier are dropped. A reading that also keeps ply 8 would be a different file. Fastchess prints the Elo of the first engine, which is the side with `IdeaS38` true.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/003/stamps.txt
?? forge-combo29/grok/003/OG.epd
?? forge-combo29/grok/003/PARTNER_HONESTY.txt
?? forge-combo29/grok/003/R.epd
?? forge-combo29/grok/003/R.meta
?? forge-combo29/grok/003/REPORT.md
?? forge-combo29/grok/003/RESULT.txt
?? forge-combo29/grok/003/apply_check.txt
?? forge-combo29/grok/003/make_r.py
?? forge-combo29/grok/003/match.meta
?? forge-combo29/grok/003/match.pgn
?? forge-combo29/grok/003/match.txt
?? forge-combo29/grok/003/match_run.log
?? forge-combo29/grok/003/partner_053.patch.txt
?? forge-combo29/grok/003/partner_053_off.tsv
?? forge-combo29/grok/003/partner_053_on.tsv
?? forge-combo29/grok/003/partner_O_off.meta
?? forge-combo29/grok/003/partner_O_off.nodes
?? forge-combo29/grok/003/partner_O_off.raw
?? forge-combo29/grok/003/partner_O_on.meta
?? forge-combo29/grok/003/partner_O_on.nodes
?? forge-combo29/grok/003/partner_O_on.raw
?? forge-combo29/grok/003/partner_apply.txt
?? forge-combo29/grok/003/partner_bench11.meta
?? forge-combo29/grok/003/partner_bench11.txt
?? forge-combo29/grok/003/partner_bench13.meta
?? forge-combo29/grok/003/partner_bench13.txt
?? forge-combo29/grok/003/partner_bench16.meta
?? forge-combo29/grok/003/partner_bench16.txt
?? forge-combo29/grok/003/partner_compare_off.txt
?? forge-combo29/grok/003/partner_compare_on.txt
?? forge-combo29/grok/003/partner_honesty.sh
?? forge-combo29/grok/003/partner_match.meta
?? forge-combo29/grok/003/partner_match.pgn
?? forge-combo29/grok/003/partner_match.sh
?? forge-combo29/grok/003/partner_match.txt
?? forge-combo29/grok/003/partner_perft5.meta
?? forge-combo29/grok/003/partner_perft5.txt
?? forge-combo29/grok/003/partner_vs_claim.py
?? forge-combo29/grok/003/partner_vs_claim.txt
?? forge-combo29/grok/003/report_numbers.out
?? forge-combo29/grok/003/report_numbers.py
```

ls -la forge-combo29/grok/003

```
total 8440
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:20 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu     132 Nov 20 08:20 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:06 asan_bug_lines.txt
-rw-r--r-- 1 ubuntu ubuntu     918 Nov 20 08:06 asan_bug.meta
-rw-r--r-- 1 ubuntu ubuntu       6 Nov 20 08:06 asan_bug.nodes
-rw-r--r-- 1 ubuntu ubuntu    9490 Nov 20 08:06 asan_bug.raw
-rw-r--r-- 1 ubuntu ubuntu     526 Nov 20 08:03 asan_build.sh
-rw-r--r-- 1 ubuntu ubuntu     916 Nov 20 08:04 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:04 asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu  132268 Nov 20 08:04 asan_G100.raw
-rw-r--r-- 1 ubuntu ubuntu     142 Nov 20 08:04 asan_nm.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:04 asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu     474 Nov 20 08:03 asan_run.sh
-rw-r--r-- 1 ubuntu ubuntu    1237 Nov 20 08:00 baseline_check.py
-rw-r--r-- 1 ubuntu ubuntu     473 Nov 20 08:00 BASELINE.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 07:58 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 07:58 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 07:58 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:02 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1158 Nov 20 08:01 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:02 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     158 Nov 20 08:02 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1122 Nov 20 08:00 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 07:59 G_B.meta
-rw-r--r-- 1 ubuntu ubuntu    3445 Nov 20 07:59 G_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  551514 Nov 20 07:59 G_B.raw
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 G.epd
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:02 G_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    3445 Nov 20 08:02 G_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  551743 Nov 20 08:02 G_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    5801 Nov 20 07:59 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu    1846 Nov 20 07:57 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     314 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2404 Nov 20 08:01 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     314 Nov 20 08:01 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6690 Nov 20 08:20 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     440 Nov 20 08:01 make_patch.sh
-rw-r--r-- 1 ubuntu ubuntu    1777 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    1828 Nov 20 08:05 make_scratch.py
-rw-r--r-- 1 ubuntu ubuntu     977 Nov 20 08:07 match.meta
-rw-r--r-- 1 ubuntu ubuntu 3520808 Nov 20 08:13 match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1703 Nov 20 08:13 match_run.log
-rw-r--r-- 1 ubuntu ubuntu    2379 Nov 20 08:05 match.sh
-rw-r--r-- 1 ubuntu ubuntu  156014 Nov 20 08:13 match.txt
-rw-r--r-- 1 ubuntu ubuntu     878 Nov 20 07:59 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 07:59 O_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  309982 Nov 20 07:59 O_B.raw
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:02 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:02 O_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  310237 Nov 20 08:02 O_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 08:02 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:02 O_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  310201 Nov 20 08:02 O_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:19 partner_053_off.tsv
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:19 partner_053_on.tsv
-rw-r--r-- 1 ubuntu ubuntu    6405 Nov 20 08:09 partner_053.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:20 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:10 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:10 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:10 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:10 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:10 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:10 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:10 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     158 Nov 20 08:10 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1852 Nov 20 08:10 partner_honesty.sh
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 08:10 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     342 Nov 20 08:15 partner_match.meta
-rw-r--r-- 1 ubuntu ubuntu 1505646 Nov 20 08:18 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1508 Nov 20 08:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   80295 Nov 20 08:18 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:10 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:10 partner_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  309924 Nov 20 08:10 partner_O_off.raw
-rw-r--r-- 1 ubuntu ubuntu     915 Nov 20 08:10 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:10 partner_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  309902 Nov 20 08:10 partner_O_on.raw
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:10 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:10 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1253 Nov 20 08:20 partner_vs_claim.py
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:20 partner_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 07:58 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:58 positions_source.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:01 p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     346 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     733 Nov 20 08:07 PROOFS.txt
-rw-r--r-- 1 ubuntu ubuntu   19223 Nov 20 08:08 R.epd
-rw-r--r-- 1 ubuntu ubuntu    7693 Nov 20 08:21 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3389 Nov 20 08:20 report_numbers.out
-rw-r--r-- 1 ubuntu ubuntu    4623 Nov 20 08:20 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:20 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:08 R.meta
-rw-r--r-- 1 ubuntu ubuntu     242 Nov 20 08:05 scratch_bug.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:06 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   10859 Nov 20 08:06 smoke_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1035 Nov 20 08:06 smoke_match.sh
-rw-r--r-- 1 ubuntu ubuntu     643 Nov 20 08:06 smoke_match.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 07:59 smoke_O_B.meta
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 07:59 smoke_O_B.nodes
-rw-r--r-- 1 ubuntu ubuntu   10401 Nov 20 07:59 smoke_O_B.raw
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:21 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1976 Nov 20 08:07 summarize_proofs.py
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:01 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 08:01 uci_p.txt
```
