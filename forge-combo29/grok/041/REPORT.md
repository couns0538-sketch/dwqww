# Seat 041, idea 41, IdeaK2

IdeaK2 keeps a separate quiet from-to history for each of the first plies from the root and adds it only when those quiet moves are ordered.
The switch is the check option IdeaK2, default false. The ply count is the spin IdeaK2_Plies, default 4, range 1 to 8.
A quiet cutoff, and the smaller bonus for a new quiet principal-variation move, updates that ply's row. Late-move reduction still uses the old quiet history.

EXISTS: no. ThreatHistory is a cheaper-attacker table and stays off. Nothing in search.cpp already stores a quiet history by ply from the root.

Honesty, no setoption, exe B and exe P. Both printed bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, and go perft 5 nodes 4865609. The lines are in the table paste below.

## Step table

The block "step table" in the paste below is the output of report_tables.py. It reads the compare files, the honesty file, the match log extract, and the sanitizer stderr.

## Proofs

(1) Honesty on exe P with no setoption matches the four known node counts. See HONESTY_P.txt.

(2) S14, Threads 1, Hash 16, IdeaK2 false, IdeaK2_Plies 4. O depth 12: 200 positions, differ 0 against exe B. G depth 12: 353 positions, differ 0 against exe B. Exe B's own sums were O 9500069 (first three 41311, 24872, 28574) and G 18466239.

(3) Same settings with IdeaK2 true. O depth 12: differ 200 of 200 against exe B. Sum 9752024. First three 30328, 23836, 34993. The code runs.

(4) uci lists `option name IdeaK2 type check default false` and `option name IdeaK2_Plies type spin default 4 min 1 max 8`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `nm -C` count of `__asan_` symbols is 35. First 100 of G at depth 10 with IdeaK2 true: 0 sanitizer lines, 100 bestmoves. A scratch copy with one heap read past the end of a 4-int array, on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, built the same way and run through depth_set.py, printed `ERROR: AddressSanitizer: heap-buffer-overflow`. That fault is not in idea.patch.txt. `git apply --check` of idea.patch.txt on a fresh worktree of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0.

## Match

Exe P with IdeaK2 true against exe P with IdeaK2 false. Both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes. Openings O and G, 553 positions, both colours, 1106 games. fastchess from https://github.com/Disservin/fastchess, concurrency 3.

Elo: -5.65 +/- 10.15. Games 1106, wins 318, losses 336, draws 452. The interval is not entirely below 0, and the point is not below -20, so I did not open the code a second time for a bug hunt.

Prediction, committed before these measurements: O sum 9050000, wrong outside 7500000 to 11500000. Actual 9752024, inside that range. Elo +6, wrong outside -30 to +40. Actual -5.65, inside that range.

## Partner

Partner is seat 091 (same idea, the next seat after 041). Their patch applies. `git apply --check` on a fresh base exited 0 before the apply, and `git apply --reverse --check` after the apply exited 0.

Their claims that I re-ran with depth_set.py, honesty.py, and compare_raw.py: honesty nodes match; IdeaK2 false matches exe B on all 200 O depth-12 rows; IdeaK2 true with IdeaK2_PlyLimit 4 and IdeaK2_Scale 1024 matches their P_on_O_d12.txt on all 200 rows. Those rows differ from exe B in all 200 positions, which is what their P_on_O_vs_B.txt says.

My 300 R openings, both colours, 600 games, their switch: Elo 3.47 +/- 8.64. They did not publish an R-match number. The search proofs they did publish are the ones this re-run matched.

Verdict: CONFIRMS.

## Suspicions, not proven

Seat 091's on-rows are the same 200 numbers as mine, and their OG match log ends on the same Elo line as mine. Two deterministic patches that update the same history on the same cutoff can do that. I rebuilt their patch and measured it. I did not diff the two patches line by line.

## What I did NOT do

I did not turn IdeaK2 on for the G depth-12 set. The brief asked for O with the switch on, and for O and G with the switch off.
I did not try IdeaK2_Plies other than 4.
I did not re-play seat 091's 1106-game match. I played 600 games on my R file.
I did not open a pull request. The scratch heap fault is only in /tmp/apply-check, not in idea.patch.txt.
No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

## What I am NOT sure about

I am not sure the Elo -5.65 is a real loss. +/- 10.15 crosses 0, and the built-in net at 20000 nodes is only a first look.
I am not sure a single shared low-ply table would have moved the nodes less than one row per ply. I measured the per-ply table only.

times: see stamps.txt

## Tables

Pasted output of `python3 report_tables.py forge-combo29/grok/041`:

```
== honesty B ==
file forge-combo29/grok/041/HONESTY_B.txt
# bench11
info string bench depth 11 nodes 312866 time 195 nps 1604441
# bench13
info string bench depth 13 nodes 862329 time 449 nps 1920554
# bench16
info string bench depth 16 nodes 3024920 time 1468 nps 2060572
# perft5
nodes 4865609

== honesty P ==
file forge-combo29/grok/041/HONESTY_P.txt
# bench11
info string bench depth 11 nodes 312866 time 166 nps 1884734
# bench13
info string bench depth 13 nodes 862329 time 429 nps 2010090
# bench16
info string bench depth 16 nodes 3024920 time 1411 nps 2143812
# perft5
nodes 4865609

== baseline B ==
file forge-combo29/grok/041/baseline_B.txt
O
COUNT 200
SUM 9500069
FIRST3 41311 24872 28574
G
COUNT 353
SUM 18466239
FIRST3 37203 70845 144383

== compare O off ==
file forge-combo29/grok/041/raw_p/compare_O_off.txt
left 200 right 200
equal 200
differ 0
left_only 0
right_only 0

== compare G off ==
file forge-combo29/grok/041/raw_p/compare_G_off.txt
left 353 right 353
equal 353
differ 0
left_only 0
right_only 0

== compare O on ==
file forge-combo29/grok/041/raw_p/compare_O_on.txt
left 200 right 200
equal 0
differ 200
left_only 0
right_only 0
0 left 12 41311 right 12 30328
1 left 12 24872 right 12 23836
2 left 12 28574 right 12 34993
3 left 12 27838 right 12 39584
4 left 12 18020 right 12 60870
5 left 12 43043 right 12 67712
6 left 12 56414 right 12 100458
7 left 12 32317 right 12 26631

== sum O on ==
file forge-combo29/grok/041/raw_p/sum_O_on.txt
COUNT 200
SUM 9752024
FIRST3 30328 23836 34993

== apply check ==
file forge-combo29/grok/041/apply_check.txt
exit:0
tree:6b98f2170a3210e71beed04bbd2553972c253ed7

== match ==
file forge-combo29/grok/041/match/result_block.txt
Results of k2on vs k2off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -5.65 +/- 10.15, nElo: -11.41 +/- 20.48
LOS: 13.73 %, DrawRatio: 60.58 %, PairsRatio: 0.83
Games: 1106, Wins: 318, Losses: 336, Draws: 452, Points: 544.0 (49.19 %)
Ptnml(0-2): [8, 111, 335, 89, 10], WL/DD Ratio: 1.66
--------------------------------------------------

== asan meta counts ==
file forge-combo29/grok/041/raw_asan/G100_d10.meta
exe=/agent/repos/work/forge-combo29/build-asan/forge
option=setoption name IdeaK2 value true
option=setoption name IdeaK2_Plies value 4
nm_command=nm -C /agent/repos/work/forge-combo29/build-asan/forge | grep -c __asan_
nm_asan_count=35
file forge-combo29/grok/041/raw_asan/scratch_overrun.meta
exe=/tmp/apply-check/forge-combo29/build-asan/forge
option=setoption name IdeaK2 value true
option=setoption name IdeaK2_Plies value 4
nm_command=nm -C /tmp/apply-check/forge-combo29/build-asan/forge | grep -c __asan_
nm_asan_count=35

== sanitizer lines ==
G100_d10.err hits 0 bytes 0
scratch_overrun.err hits 3 bytes 4179

== uci IdeaK2 lines ==
option name IdeaK2 type check default false
option name IdeaK2_Plies type spin default 4 min 1 max 8

== prediction ==
O depth 12 sum, exe P, IdeaK2 true, IdeaK2_Plies 4, S14, Threads 1, Hash 16.
prediction 9050000
wrong if the sum is below 7500000 or above 11500000
test-match Elo, IdeaK2 true against IdeaK2 false, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours, 1106 games.
prediction +6
wrong if Elo is below -30 or above +40
== step table ==
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | 2026-11-20T07:53:23Z STEP 1 seat
2 honesty B | done | HONESTY_B.txt | info string bench depth 11 nodes 312866 time 195 nps 1604441
2 baseline O | done | baseline_B.txt | SUM 9500069
3 off O | done | raw_p/compare_O_off.txt | differ 0
3 off G | done | raw_p/compare_G_off.txt | differ 0
3 on O | done | raw_p/compare_O_on.txt raw_p/sum_O_on.txt | differ 200 SUM 9752024
3 uci | done | raw_p/uci.txt | option name IdeaK2 type check default false
3 sanitizer | done | raw_asan/G100_d10.err raw_asan/scratch_overrun.err | clean_hits 0 scratch_hits 3
3 match | done | match/result_block.txt | Elo: -5.65 +/- 10.15, nElo: -11.41 +/- 20.48
3 apply | done | apply_check.txt | exit:0
4 partner off | done | partner/compare_off_vs_B.txt | differ 0
4 partner on | done | partner/compare_on_vs_091.txt | differ 0
4 partner match | done | partner/match/result_block.txt | Elo: 3.47 +/- 8.64, nElo: 11.19 +/- 27.80
4 verdict | done | partner compare files | CONFIRMS

== partner ==
== partner apply_check.txt ==
file forge-combo29/grok/041/partner/apply_check.txt
reverse_check_exit:0

== partner HONESTY.txt ==
file forge-combo29/grok/041/partner/HONESTY.txt
# bench11
info string bench depth 11 nodes 312866 time 168 nps 1862297
# bench13
info string bench depth 13 nodes 862329 time 441 nps 1955394
# bench16
info string bench depth 16 nodes 3024920 time 1497 nps 2020654
# perft5
nodes 4865609

== partner compare_off_vs_B.txt ==
file forge-combo29/grok/041/partner/compare_off_vs_B.txt
left 200 right 200
equal 200
differ 0
left_only 0
right_only 0

== partner compare_on_vs_091.txt ==
file forge-combo29/grok/041/partner/compare_on_vs_091.txt
left 200 right 200
equal 200
differ 0
left_only 0
right_only 0

== partner compare_on_vs_B.txt ==
file forge-combo29/grok/041/partner/compare_on_vs_B.txt
left 200 right 200
equal 0
differ 200
left_only 0
right_only 0
0 left 12 41311 right 12 30328
1 left 12 24872 right 12 23836
2 left 12 28574 right 12 34993
3 left 12 27838 right 12 39584
4 left 12 18020 right 12 60870
5 left 12 43043 right 12 67712
6 left 12 56414 right 12 100458
7 left 12 32317 right 12 26631

== partner match/result_block.txt ==
file forge-combo29/grok/041/partner/match/result_block.txt
Results of k2on vs k2off (20000 nodes, 1t, 16MB, R.fens):
Elo: 3.47 +/- 8.64, nElo: 11.19 +/- 27.80
LOS: 78.48 %, DrawRatio: 87.67 %, PairsRatio: 1.18
Games: 600, Wins: 277, Losses: 271, Draws: 52, Points: 303.0 (50.50 %)
Ptnml(0-2): [2, 15, 263, 15, 5], WL/DD Ratio: 22.91
--------------------------------------------------
```

## git status --short

```
 M forge-combo29/grok/041/stamps.txt
?? forge-combo29/grok/041/REPORT.md
?? forge-combo29/grok/041/RESULT.txt
?? forge-combo29/grok/041/partner/
?? forge-combo29/grok/041/report_tables.out
?? forge-combo29/grok/041/report_tables.py
?? forge-combo29/grok/041/run_partner_match.sh
```

## ls -la

```
total 148
drwxr-xr-x 8 ubuntu ubuntu  4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu    53 Nov 20 08:10 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   100 Nov 20 08:04 baseline_B.txt
-rw-r--r-- 1 ubuntu ubuntu  1547 Nov 20 08:04 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu  6161 Nov 20 08:02 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu  1738 Nov 20 08:09 design.txt
-rw-r--r-- 1 ubuntu ubuntu   530 Nov 20 08:18 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   238 Nov 20 08:04 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   238 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu  2017 Nov 20 07:59 honesty.py
-rw-r--r-- 1 ubuntu ubuntu 11454 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   730 Nov 20 08:03 make_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu  2145 Nov 20 08:04 make_r.py
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:18 match
-rw-r--r-- 1 ubuntu ubuntu   475 Nov 20 08:08 note_asan.py
drwxr-xr-x 4 ubuntu ubuntu  4096 Nov 20 09:15 partner
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:07 positions
-rw-r--r-- 1 ubuntu ubuntu   333 Nov 20 08:04 prediction.txt
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:07 raw_asan
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:02 raw_b
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:09 raw_p
-rw-r--r-- 1 ubuntu ubuntu  4828 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu  5813 Nov 20 09:17 report_tables.out
-rw-r--r-- 1 ubuntu ubuntu  4650 Nov 20 09:16 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu   187 Nov 20 09:17 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu  1446 Nov 20 08:09 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu  1514 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   244 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu  1491 Nov 20 08:00 sum_raw.py

ls -laR

forge-combo29/grok/041:
total 148
drwxr-xr-x 8 ubuntu ubuntu  4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu    53 Nov 20 08:10 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   100 Nov 20 08:04 baseline_B.txt
-rw-r--r-- 1 ubuntu ubuntu  1547 Nov 20 08:04 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu  6161 Nov 20 08:02 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu  1738 Nov 20 08:09 design.txt
-rw-r--r-- 1 ubuntu ubuntu   530 Nov 20 08:18 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   238 Nov 20 08:04 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   238 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu  2017 Nov 20 07:59 honesty.py
-rw-r--r-- 1 ubuntu ubuntu 11454 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   730 Nov 20 08:03 make_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu  2145 Nov 20 08:04 make_r.py
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:18 match
-rw-r--r-- 1 ubuntu ubuntu   475 Nov 20 08:08 note_asan.py
drwxr-xr-x 4 ubuntu ubuntu  4096 Nov 20 09:15 partner
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:07 positions
-rw-r--r-- 1 ubuntu ubuntu   333 Nov 20 08:04 prediction.txt
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:07 raw_asan
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:02 raw_b
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:09 raw_p
-rw-r--r-- 1 ubuntu ubuntu  4828 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu  5813 Nov 20 09:17 report_tables.out
-rw-r--r-- 1 ubuntu ubuntu  4650 Nov 20 09:16 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu   187 Nov 20 09:17 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu  1446 Nov 20 08:09 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu  1514 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   244 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu  1491 Nov 20 08:00 sum_raw.py

forge-combo29/grok/041/match:
total 1196
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:18 .
drwxr-xr-x 8 ubuntu ubuntu    4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu    7278 Nov 20 08:16 fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu 1070214 Nov 20 08:16 games.pgn
-rw-r--r-- 1 ubuntu ubuntu  115182 Nov 20 08:16 match.log
-rw-r--r-- 1 ubuntu ubuntu     331 Nov 20 08:18 result_block.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:16 run_note.txt

forge-combo29/grok/041/partner:
total 896
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu  12104 Nov 20 09:09 091-idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 282856 Nov 20 09:09 091_O_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   1943 Nov 20 09:09 091_O_on.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     21 Nov 20 09:10 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:10 compare_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:10 compare_on_vs_091.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 09:15 compare_on_vs_B.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:10 honesty
-rw-r--r-- 1 ubuntu ubuntu    238 Nov 20 09:10 HONESTY.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:15 match
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 09:10 O_off_d12.err
-rw-r--r-- 1 ubuntu ubuntu   1127 Nov 20 09:10 O_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 281938 Nov 20 09:10 O_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 09:10 O_on_d12.err
-rw-r--r-- 1 ubuntu ubuntu   1126 Nov 20 09:10 O_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 282690 Nov 20 09:10 O_on_d12.txt

forge-combo29/grok/041/partner/honesty:
total 48
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 09:10 .
drwxr-xr-x 4 ubuntu ubuntu 4096 Nov 20 09:15 ..
-rw-r--r-- 1 ubuntu ubuntu  212 Nov 20 09:10 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   61 Nov 20 09:10 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu  212 Nov 20 09:10 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   61 Nov 20 09:10 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu  212 Nov 20 09:10 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   63 Nov 20 09:10 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu  214 Nov 20 09:10 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu  274 Nov 20 09:10 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu 5100 Nov 20 09:09 id_name.txt

forge-combo29/grok/041/partner/match:
total 544
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 09:15 ..
-rw-r--r-- 1 ubuntu ubuntu   7479 Nov 20 09:13 fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu 463918 Nov 20 09:13 games.pgn
-rw-r--r-- 1 ubuntu ubuntu  57792 Nov 20 09:13 match.log
-rw-r--r-- 1 ubuntu ubuntu    325 Nov 20 09:15 result_block.txt
-rw-r--r-- 1 ubuntu ubuntu     50 Nov 20 09:13 run_note.txt

forge-combo29/grok/041/positions:
total 108
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:07 .
drwxr-xr-x 8 ubuntu ubuntu  4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu 12861 Nov 20 07:57 first200.fens
-rw-r--r-- 1 ubuntu ubuntu  5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu 30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu 19316 Nov 20 08:04 R.fens
-rw-r--r-- 1 ubuntu ubuntu    30 Nov 20 08:07 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu 17691 Nov 20 07:57 set_G.epd

forge-combo29/grok/041/raw_asan:
total 152
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:07 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:07 G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu   1178 Nov 20 08:08 G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu 118986 Nov 20 08:07 G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu   4179 Nov 20 08:07 scratch_overrun.err
-rw-r--r-- 1 ubuntu ubuntu   1181 Nov 20 08:08 scratch_overrun.meta
-rw-r--r-- 1 ubuntu ubuntu   5186 Nov 20 08:07 scratch_overrun.txt

forge-combo29/grok/041/raw_b:
total 828
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:02 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:02 G_d12.err
-rw-r--r-- 1 ubuntu ubuntu    990 Nov 20 08:02 G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 507306 Nov 20 08:02 G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 07:59 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 07:59 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 07:59 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:59 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 07:59 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:59 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 07:59 id_name.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:02 O_d12.err
-rw-r--r-- 1 ubuntu ubuntu    994 Nov 20 08:02 O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 281693 Nov 20 08:02 O_d12.txt

forge-combo29/grok/041/raw_p:
total 1136
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:09 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:17 ..
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:09 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:09 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu    312 Nov 20 08:09 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:05 G_off_d12.err
-rw-r--r-- 1 ubuntu ubuntu   1074 Nov 20 08:05 G_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 507735 Nov 20 08:05 G_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 08:05 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:05 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 08:05 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:05 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 08:05 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:05 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 08:05 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:05 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5034 Nov 20 08:05 id_name.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:05 O_off_d12.err
-rw-r--r-- 1 ubuntu ubuntu   1078 Nov 20 08:05 O_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 282008 Nov 20 08:05 O_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:05 O_on_d12.err
-rw-r--r-- 1 ubuntu ubuntu   1077 Nov 20 08:05 O_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 282781 Nov 20 08:05 O_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     47 Nov 20 08:09 sum_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu   5034 Nov 20 08:05 uci.txt
```
