Idea 42 is hindsight depth: one ply more or less at a node from the reduction the parent move got and the sum of the two plies' static evaluations.
The plain engine already takes that step under HindsightDepth, which is off by default. I did not add a second formula.
IdeaK3 is a check, default false, that turns the same step on. IdeaK3_Withheld defaults to 3 and IdeaK3_Margin defaults to 100, today's literals. With IdeaK3 false the step still uses those literals, so HindsightDepth alone is unchanged.

EXISTS: forge-combo29/src/search.cpp:1604

Honesty, no setoption. Exe B and exe P and the partner build each printed bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

The numbers below are the output of report_table.py, which reads the raw files.

```
HONESTY_B
bench11 info string bench depth 11 nodes 312866 time 188 nps 1664180
bench13 info string bench depth 13 nodes 862329 time 463 nps 1862481
bench16 info string bench depth 16 nodes 3024920 time 1449 nps 2087591
perft5 nodes 4865609
HONESTY_P
bench11 info string bench depth 11 nodes 312866 time 206 nps 1518766
bench13 info string bench depth 13 nodes 862329 time 471 nps 1830847
bench16 info string bench depth 16 nodes 3024920 time 1538 nps 1966788
perft5 nodes 4865609
PARTNER_HONESTY
bench11 info string bench depth 11 nodes 312866 time 218 nps 1435165
bench13 info string bench depth 13 nodes 862329 time 527 nps 1636297
bench16 info string bench depth 16 nodes 3024920 time 1875 nps 1613290
perft5 nodes 4865609
B_O 200 9500069 [41311, 24872, 28574]
B_G 353 18466239 [37203, 70845, 144383]
P_OFF_O n 200/200 differ 0 sum 9500069 vs 9500069
P_OFF_G n 353/353 differ 0 sum 18466239 vs 18466239
P_ON_O n 200/200 differ 200 sum 9845650 vs 9500069
P_ON_VS_HINDSIGHT n 200/200 differ 0 sum 9845650 vs 9845650
PARTNER_OFF n 200/200 differ 0 sum 9500069 vs 9500069
PARTNER_ON_VS_THEIRS n 200/200 differ 0 sum 9845650 vs 9845650
PARTNER_ON_VS_B n 200/200 differ 200 sum 9845650 vs 9500069
ASAN_META
exe /tmp/forge-asan/forge
sha256 8fe33d8d88788a031294565abf3e36596f0829fad1f16b37900fadf2d4965028
count 100
asan_symbols 35
asan_clean_err absent
ASAN_SCRATCH /tmp/forge-scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
ASAN_SCRATCH_META nm_asan 35
MATCH_OG
Results of IdeaK3on vs IdeaK3off (20000 nodes, 1t, 16MB, OG.epd):
Elo: 4.08 +/- 10.50, nElo: 7.97 +/- 20.48
LOS: 77.71 %, DrawRatio: 61.48 %, PairsRatio: 1.11
Games: 1106, Wins: 332, Losses: 319, Draws: 455, Points: 559.5 (50.59 %)
Ptnml(0-2): [12, 89, 340, 98, 14], WL/DD Ratio: 1.54
--------------------------------------------------
PARTNER_MATCH_R
Results of HDon vs HDoff (20000 nodes, 1t, 16MB, R.epd):
Elo: 1.16 +/- 6.42, nElo: 5.02 +/- 27.80
LOS: 63.82 %, DrawRatio: 91.33 %, PairsRatio: 1.00
Games: 600, Wins: 233, Losses: 231, Draws: 136, Points: 301.0 (50.17 %)
Ptnml(0-2): [0, 13, 274, 11, 2], WL/DD Ratio: 3.89
--------------------------------------------------
UCI_OPTIONS
option name IdeaK3 type check default false
option name IdeaK3_Withheld type spin default 3 min 0 max 16
option name IdeaK3_Margin type spin default 100 min 0 max 900
```

step | done / partly / not done | evidence file | result
--- | --- | --- | ---
1 seat | done | SEAT.txt | seat 042, idea 42
2 builds and baseline | done | HONESTY_B.txt, b_sums.txt | pins match; O 9500069; G 18466239
3 idea | done | idea.patch.txt, report_table.txt, match_og.log | off identical; on 200 of 200; Elo 4.08 +/- 10.50
4 partner 092 | done | partner092.patch.txt, cmp_partner_on.txt, partner_match_R.log | CONFIRMS
5 report | done | REPORT.md, RESULT.txt | this file

Proof (1). Exe P with no setoption matches the four honesty numbers. Files honesty_p_bench11.txt, honesty_p_bench13.txt, honesty_p_bench16.txt, honesty_p_perft5.txt.

Proof (2). S14 and IdeaK3 false. O depth 12 differs in 0 of 200 from exe B. G depth 12 differs in 0 of 353. Sums 9500069 and 18466239.

Proof (3). S14 and IdeaK3 true, spins left at 3 and 100. O depth 12 differs in 200 of 200 from exe B. Sum 9845650. The same rows differ in 0 of 200 from exe B with HindsightDepth true, so the defaults are today's numbers.

Proof (4). The uci answer lists IdeaK3 check default false, IdeaK3_Withheld spin default 3 min 0 max 16, IdeaK3_Margin spin default 100 min 0 max 900.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK3 true, first 100 of G at depth 10. nm -C counted 35 __asan_ symbols. The run wrote no stderr. A scratch copy with one heap read past a 4-int array, on the FEN 4k3/8/8/8/8/8/8/4K3 w - - 0 1, built the same way and run through measure.py, reported the sanitizer line in asan_scratch.err.

git apply --check of idea.patch.txt on the clean base tree exited 0 (apply_check.txt). The same check of the partner patch exited 0.

Match. IdeaK3 on versus IdeaK3 off, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours, 1106 games. Elo 4.08 +/- 10.50. The whole interval is not below 0. Prediction was 6 Elo and an O sum of 9100000, wrong outside -35..40 and 6500000..14000000. Both landed inside.

Partner 092. The next seat with idea 42. Their patch keeps HindsightDepth as the switch and replaces the literals 100 and 3 with HindsightDepth_Loss and HindsightDepth_Withheld at those defaults. On a fresh base tree the patch applies, the honesty numbers match, HindsightDepth false matches exe B on O in 0 of 200, and HindsightDepth true matches their own O rows in 0 of 200 (and differs from exe B in 200 of 200, sum 9845650, which is the sum they wrote). A 600-game match of their switch on 300 R openings, both colours, scored Elo 1.16 +/- 6.42. Verdict: CONFIRMS.

suspicions, not proven

Their published 1106-game line is Elo 4.08 +/- 10.50 with the same win, loss, draw and pentanomial counts as my IdeaK3 match. I did not copy that log. At a fixed node count the same openings produce the same games when the search matches, and the node rows do match. I did not re-play their 1106 games on their binary.

what I did NOT do

I did not replay partner 092's 1106-game match. I did not measure G for their off switch; the partner check asked for O. I did not run a full set with a non-default spin. I did not run the sanitizer past the first 100 positions of G at depth 10. No FABLE_TO_grok file was on the handoff branch at 2026-11-20T08:54:33Z. I started the partner check when their patch was already pushed, before minute 75.

what I am NOT sure about

The R match draw ratio is 91.33 percent. Those positions are late random games, and many ends are the fifty-move rule, threefold repetition, or insufficient material. I am not sure a 600-game sample of that set says much about playing strength. The fastchess interval is the number I have.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/042/stamps.txt
?? config.json
?? forge-combo29/grok/042/PARTNER_HONESTY.txt
?? forge-combo29/grok/042/REPORT.md
?? forge-combo29/grok/042/RESULT.txt
?? forge-combo29/grok/042/apply_check.txt
?? forge-combo29/grok/042/cmp_partner_off.txt
?? forge-combo29/grok/042/cmp_partner_on.txt
?? forge-combo29/grok/042/cmp_partner_on_vs_b.txt
?? forge-combo29/grok/042/compare_partner.py
?? forge-combo29/grok/042/partner092.patch.txt
?? forge-combo29/grok/042/partner092_on_O.tsv
?? forge-combo29/grok/042/partner_honesty.py
?? forge-combo29/grok/042/partner_honesty_bench11.meta
?? forge-combo29/grok/042/partner_honesty_bench11.txt
?? forge-combo29/grok/042/partner_honesty_bench13.meta
?? forge-combo29/grok/042/partner_honesty_bench13.txt
?? forge-combo29/grok/042/partner_honesty_bench16.meta
?? forge-combo29/grok/042/partner_honesty_bench16.txt
?? forge-combo29/grok/042/partner_honesty_perft5.meta
?? forge-combo29/grok/042/partner_honesty_perft5.txt
?? forge-combo29/grok/042/partner_match_R.log
?? forge-combo29/grok/042/partner_match_R.pgn
?? forge-combo29/grok/042/partner_off_O_d12.meta
?? forge-combo29/grok/042/partner_off_O_d12.rows.tsv
?? forge-combo29/grok/042/partner_off_O_d12.txt
?? forge-combo29/grok/042/partner_on_O_d12.meta
?? forge-combo29/grok/042/partner_on_O_d12.rows.tsv
?? forge-combo29/grok/042/partner_on_O_d12.txt
?? forge-combo29/grok/042/report_table.py
?? forge-combo29/grok/042/report_table.txt
?? forge-combo29/grok/042/run_partner_match.sh

$ ls -la forge-combo29/grok/042
total 8484
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 08:55 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 08:55 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     945 Nov 20 08:04 asan_G_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    7284 Nov 20 08:04 asan_G_d10.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  132156 Nov 20 08:04 asan_G_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     310 Nov 20 08:06 asan_scratch.err
-rw-r--r-- 1 ubuntu ubuntu     368 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    6288 Nov 20 08:06 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 07:59 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   26067 Nov 20 07:59 b_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  551450 Nov 20 07:59 b_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     905 Nov 20 08:02 b_hindsight_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:02 b_hindsight_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  310417 Nov 20 08:02 b_hindsight_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 07:59 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 07:59 b_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  309927 Nov 20 07:59 b_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     126 Nov 20 08:00 b_sums.txt
-rw-r--r-- 1 ubuntu ubuntu      86 Nov 20 08:03 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      84 Nov 20 08:03 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:03 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu      93 Nov 20 08:03 cmp_on_vs_hindsight.txt
-rw-r--r-- 1 ubuntu ubuntu      90 Nov 20 08:49 cmp_partner_off.txt
-rw-r--r-- 1 ubuntu ubuntu      97 Nov 20 08:49 cmp_partner_on.txt
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:54 cmp_partner_on_vs_b.txt
-rw-r--r-- 1 ubuntu ubuntu    1814 Nov 20 08:48 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    1654 Nov 20 08:03 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu    1168 Nov 20 08:07 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:02 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:02 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:02 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:02 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:02 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1878 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     254 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1878 Nov 20 08:02 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     254 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6865 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1112 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  152103 Nov 20 08:13 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 3627399 Nov 20 08:13 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     229 Nov 20 08:16 match_og_result.txt
-rw-r--r-- 1 ubuntu ubuntu     699 Nov 20 08:07 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu    8405 Nov 20 07:59 measure.py
-rw-r--r-- 1 ubuntu ubuntu    1026 Nov 20 08:08 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 08:48 partner092_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu    3294 Nov 20 08:48 partner092.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:48 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5132 Nov 20 08:48 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:48 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5132 Nov 20 08:48 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:48 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5134 Nov 20 08:48 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     235 Nov 20 08:48 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5345 Nov 20 08:48 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1917 Nov 20 08:48 partner_honesty.py
-rw-r--r-- 1 ubuntu ubuntu     254 Nov 20 08:48 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   69590 Nov 20 08:50 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu 1132336 Nov 20 08:50 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     909 Nov 20 08:48 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:48 partner_off_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  310688 Nov 20 08:48 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:48 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:48 partner_on_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  310734 Nov 20 08:48 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 08:02 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   26067 Nov 20 08:02 p_off_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  551923 Nov 20 08:02 p_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     898 Nov 20 08:02 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:02 p_off_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  310363 Nov 20 08:02 p_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     897 Nov 20 08:02 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 08:02 p_on_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu  310163 Nov 20 08:02 p_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     635 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    8376 Nov 20 08:55 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4099 Nov 20 08:54 report_table.py
-rw-r--r-- 1 ubuntu ubuntu    2405 Nov 20 08:54 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 08:55 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1059 Nov 20 08:07 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1091 Nov 20 08:49 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:05 sets
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:55 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1258 Nov 20 08:00 sum_raw.py
```
