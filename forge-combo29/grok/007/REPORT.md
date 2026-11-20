# Seat 007, idea 7, S31

S31 accepts a null-move cutoff at once when no cheaper enemy piece attacks a dearer piece of the side to move, and re-searches the cutoff, with null moves disabled, when such an attack exists.
The plain engine already does that below depth 14 when NullThreatVerify is on, and it always verifies a null cutoff at depth 14 or more.
I left that switch as it is and turned the fixed split at 14 into the spin NullThreatVerify_Depth, default 14, minimum 1, maximum 64, so a default search takes today's path.

## EXISTS

yes: forge-combo29/src/search.cpp:1724
The option is already advertised. forge-combo29/src/search.cpp:101 sets NullThreatVerify false, and forge-combo29/src/uci.cpp lists `option name NullThreatVerify type check default false`. The depth 14 in the threat gate was a literal, so it is now NullThreatVerify_Depth.

## Honesty

No setoption. Exe B, then exe P.

```
bench11 nodes 312866 expected 312866 ok true
bench13 nodes 862329 expected 862329 ok true
bench16 nodes 3024920 expected 3024920 ok true
perft5 nodes 4865609 expected 4865609 ok true
```

```
bench11 nodes 312866 expected 312866 ok true
bench13 nodes 862329 expected 862329 ok true
bench16 nodes 3024920 expected 3024920 ok true
perft5 nodes 4865609 expected 4865609 ok true
```

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 007, idea 7 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 2 O and G sums | done | B_SUMS.txt | forge-combo29/grok/007/B_O.rows.tsv count 200 sum 9500069 first 41311 24872 28574 / forge-combo29/grok/007/B_G.rows.tsv count 353 sum 18466239 first 37203 70845 144383 |
| 3 prediction, before measuring P | done | prediction.txt | committed before any exe P measurement |
| 3 patch applies | done | apply_check.txt | idea.patch.txt idea_exit=0 partner.patch.txt partner_exit=0 |
| 3 proof off | done | compare_off_O.txt, compare_off_G.txt | positions 200 differ 0 equal 200 / positions 353 differ 0 equal 353 |
| 3 proof on | done | compare_on_O.txt, on_O_delta.txt | positions 200 differ 147 equal 53 / positions 200 node_differ 147 move_differ 0 nodes_up 147 nodes_down 0 net_nodes 1808 |
| 3 uci options | done | uci_options.txt | option name NullThreatVerify type check default false / option name NullThreatVerify_Depth type spin default 14 min 1 max 64 |
| 3 sanitizer | done | asan_summary.txt | asan_symbols 35; raw hits asan_raw_hits 0 |
| 3 match | done | match_og_result.txt | Elo: -0.31 +/- 8.77, nElo: -0.73 +/- 20.48 / Games: 1106, Wins: 343, Losses: 344, Draws: 419, Points: 552.5 (49.95 %) |
| 4 partner 057 | done | partner_compare_on_O.txt, partner_match_result.txt | CONFIRMS, R match 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty, no setoption, exe P: the four lines in HONESTY_P.txt match exe B and the known counts. bench 11 is 312866, bench 13 is 862329, bench 16 is 3024920, perft 5 is 4865609.

(2) S14, NullThreatVerify false, NullThreatVerify_Depth 14.

```
positions 200 differ 0 equal 200
positions 353 differ 0 equal 353
```

```
forge-combo29/grok/007/B_O.rows.tsv count 200 sum 9500069 first 41311 24872 28574
forge-combo29/grok/007/B_G.rows.tsv count 353 sum 18466239 first 37203 70845 144383
forge-combo29/grok/007/P_off_O.rows.tsv count 200 sum 9500069 first 41311 24872 28574
forge-combo29/grok/007/P_off_G.rows.tsv count 353 sum 18466239 first 37203 70845 144383
forge-combo29/grok/007/P_on_O.rows.tsv count 200 sum 9501877 first 41311 24876 28574
forge-combo29/grok/007/P_asan_G100.rows.tsv count 100 sum 2099866 first 10526 11164 31800
```

(3) S14, NullThreatVerify true, NullThreatVerify_Depth 14. O depth 12.

```
positions 200 differ 147 equal 53
positions 200 node_differ 147 move_differ 0 nodes_up 147 nodes_down 0 net_nodes 1808
```

The O sum is 9501877. The prediction file said 10260000 and said a sum below 9700000 would show that guess wrong. 9501877 is below 9700000. prediction.txt was not edited.

(4) `uci` from exe P.

```
option name NullThreatVerify type check default false
option name NullThreatVerify_Depth type spin default 14 min 1 max 64
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. First 100 positions of G, depth 10, switch true. The scratch engine is that same build plus one heap read past the end of a four-int array, on one FEN, run through harness_search.py.

```
asan_symbols 35
asan_raw_hits 0
SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/scratch-forge/src/board.cpp:370 in forge::Board::set_fen(std::basic_string_view<char, std::char_traits<char> >, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >*)
scratch_nm 35
idea_nm 35
```

```
idea.patch.txt
idea_exit=0
partner.patch.txt
partner_exit=0
```

## Match

Exe P with NullThreatVerify true against exe P with it false. Both S14, Threads 1, Hash 16, NullThreatVerify_Depth 14, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess concurrency 3. Rounds equal the number of openings.

```
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -0.31 +/- 8.77, nElo: -0.73 +/- 20.48
LOS: 47.20 %, DrawRatio: 71.97 %, PairsRatio: 1.01
Games: 1106, Wins: 343, Losses: 344, Draws: 419, Points: 552.5 (49.95 %)
Ptnml(0-2): [9, 68, 398, 71, 7], WL/DD Ratio: 1.84
--------------------------------------------------
Finished match
Total Time: 00:05:55 (hours:minutes:seconds)

fastchess_exit=0
pgn_events 1106
pgn_results 1106
```

The Elo interval includes 0 and the point is above -20, so the brief's one look for a bug was not triggered. The predicted Elo was +6, wrong if below -20 or above +30. -0.31 is inside that range.

## Partner

Partner is seat 057 (idea 7; 107 had no branch). git apply --check of partner.patch.txt on the base commit exited 0. A fresh worktree was built with g++. My harness, not seat 057's scripts.

```
bench11 nodes 312866 expected 312866 ok true
bench13 nodes 862329 expected 862329 ok true
bench16 nodes 3024920 expected 3024920 ok true
perft5 nodes 4865609 expected 4865609 ok true
positions 200 differ 0 equal 200
positions 200 differ 0 equal 200 my_sum 9536516 partner_sum 9536516
positions 200 differ 200 equal 0
```

Off matches exe B's O rows (0 differ, sum 9500069). On matches seat 057's own O rows (0 differ, both sums 9536516) and differs from exe B on all 200, which is what seat 057 reported. Verdict: CONFIRMS.

Their switch, on my 300 R openings, both colours, 600 games:

```
Results of on vs off (20000 nodes, 1t, 16MB, R.epd):
Elo: -1.74 +/- 10.47, nElo: -4.62 +/- 27.80
LOS: 37.24 %, DrawRatio: 82.67 %, PairsRatio: 0.93
Games: 600, Wins: 263, Losses: 266, Draws: 71, Points: 298.5 (49.75 %)
Ptnml(0-2): [6, 21, 248, 20, 5], WL/DD Ratio: 15.53
--------------------------------------------------
Finished match
Total Time: 00:02:37 (hours:minutes:seconds)

fastchess_exit=0
pgn_events 600
pgn_results 600
```

## suspicions, not proven

At depth 12, on_O_delta.txt shows the node count changed on 147 openings, the root move changed on none, every change was an increase, and the net added 1808 nodes. The 1106-game match does not separate the option from zero. That is not a proof that the option is neutral in a longer game or with the owner's net.

## what I did NOT do

I did not re-run seat 057's G depth-12 set, and I did not replay their 1106-game match. I did not search with NullThreatVerify_Depth set to anything but 14. I did not add the comfortable-margin test in the S31 text. Seat 057 built that as IdeaS31 with IdeaS31_Margin 80. I did not open a pull request.

## what I am NOT sure about

S31's text says to do the threat gate at every depth and to accept a quiet cutoff only when the static margin is comfortable. The engine's NullThreatVerify gate applies only below 14, and the always-verify at 14 and above was already there. I called that EXISTS and parameterized 14. Seat 057 called it a different idea and replaced the gate. I am not sure which reading Opus wants. The node-sum prediction was outside the range written in prediction.txt. The partner review was stamped at 2026-11-20T08:57:47Z. Minute 75 after the first stamp is 2026-11-20T09:06:46Z. The patch was already on their branch, and step 3 of this seat was already pushed.

## times: see stamps.txt

```
2026-11-20T07:51:46Z STEP 1 seat
2026-11-20T08:00:14Z STEP 2 honesty and baseline sums
2026-11-20T08:14:13Z STEP 3 proofs and match
2026-11-20T08:57:47Z STEP 4 partner 057
2026-11-20T08:59:14Z STEP 5 report
```

## git status --short

```
 M forge-combo29/grok/007/stamps.txt
?? forge-combo29/grok/007/REPORT.md
?? forge-combo29/grok/007/RESULT.txt
?? forge-combo29/grok/007/apply_check.txt
?? forge-combo29/grok/007/asan_summary.txt
?? forge-combo29/grok/007/partner.patch.txt
?? forge-combo29/grok/007/partner_HONESTY.txt
?? forge-combo29/grok/007/partner_HONESTY_bench11.meta
?? forge-combo29/grok/007/partner_HONESTY_bench11.txt
?? forge-combo29/grok/007/partner_HONESTY_bench13.meta
?? forge-combo29/grok/007/partner_HONESTY_bench13.txt
?? forge-combo29/grok/007/partner_HONESTY_bench16.meta
?? forge-combo29/grok/007/partner_HONESTY_bench16.txt
?? forge-combo29/grok/007/partner_HONESTY_perft5.meta
?? forge-combo29/grok/007/partner_HONESTY_perft5.txt
?? forge-combo29/grok/007/partner_P_on_O.rows.txt
?? forge-combo29/grok/007/partner_compare.py
?? forge-combo29/grok/007/partner_compare_off_O.txt
?? forge-combo29/grok/007/partner_compare_on_O.txt
?? forge-combo29/grok/007/partner_match.log
?? forge-combo29/grok/007/partner_match.pgn
?? forge-combo29/grok/007/partner_match_result.txt
?? forge-combo29/grok/007/partner_off_O.meta
?? forge-combo29/grok/007/partner_off_O.raw.txt
?? forge-combo29/grok/007/partner_off_O.rows.tsv
?? forge-combo29/grok/007/partner_on_O.meta
?? forge-combo29/grok/007/partner_on_O.raw.txt
?? forge-combo29/grok/007/partner_on_O.rows.tsv
?? forge-combo29/grok/007/partner_on_vs_B.txt
?? forge-combo29/grok/007/report_build.py
?? forge-combo29/grok/007/run_partner_match.sh
?? forge-combo29/grok/007/uci_options.txt
```

## ls -la

```
total 4944
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:59 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:57 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     304 Nov 20 08:58 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 07:59 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu  549636 Nov 20 07:59 B_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 07:59 B_G.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 07:59 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309045 Nov 20 07:59 B_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 07:59 B_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:00 B_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:06 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:06 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:06 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:04 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 G.epd
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:00 harness_compare.py
-rw-r--r-- 1 ubuntu ubuntu    2270 Nov 20 07:56 harness_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    5918 Nov 20 07:58 harness_search.py
-rw-r--r-- 1 ubuntu ubuntu     702 Nov 20 08:00 harness_summarize.py
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:07 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:07 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:07 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:07 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:07 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:07 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:07 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:07 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:07 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:01 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5063 Nov 20 08:01 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:01 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5063 Nov 20 08:01 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:01 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5065 Nov 20 08:01 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:01 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5276 Nov 20 08:01 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:01 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    3787 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 07:59 kimi5_commit.txt
-rw-r--r-- 1 ubuntu ubuntu    1395 Nov 20 08:03 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  104471 Nov 20 08:12 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 1056639 Nov 20 08:12 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     434 Nov 20 08:14 match_og_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1154 Nov 20 08:14 move_delta.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      85 Nov 20 08:14 on_O_delta.txt
-rw-r--r-- 1 ubuntu ubuntu     863 Nov 20 08:14 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:53 partner_compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 08:53 partner_compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1102 Nov 20 08:52 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 08:53 partner_HONESTY_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:53 partner_HONESTY_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 08:53 partner_HONESTY_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:53 partner_HONESTY_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 08:53 partner_HONESTY_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 08:53 partner_HONESTY_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:53 partner_HONESTY_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5315 Nov 20 08:53 partner_HONESTY_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:53 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   53039 Nov 20 08:56 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu  473855 Nov 20 08:56 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     431 Nov 20 08:56 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:53 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309036 Nov 20 08:53 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:53 partner_off_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:53 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309055 Nov 20 08:53 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:53 partner_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:53 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    9888 Nov 20 08:52 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   17645 Nov 20 08:52 partner_P_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:04 P_asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu  131735 Nov 20 08:04 P_asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1374 Nov 20 08:04 P_asan_G100.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 08:01 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu  550120 Nov 20 08:01 P_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:01 P_off_G.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 08:01 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309328 Nov 20 08:01 P_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:01 P_off_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     927 Nov 20 08:01 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309210 Nov 20 08:01 P_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:01 P_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu    1506 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     515 Nov 20 08:06 proof_sums.txt
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:02 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   19261 Nov 20 08:05 R.epd
-rw-r--r-- 1 ubuntu ubuntu    7500 Nov 20 08:59 report_build.py
-rw-r--r-- 1 ubuntu ubuntu    8550 Nov 20 08:59 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:59 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1382 Nov 20 08:06 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1197 Nov 20 08:53 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     930 Nov 20 08:04 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu   10150 Nov 20 08:04 scratch_asan.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 scratch_asan.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:04 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu     475 Nov 20 08:04 scratch_heap_read.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 smoke.epd
-rw-r--r-- 1 ubuntu ubuntu     595 Nov 20 08:05 smoke.log
-rw-r--r-- 1 ubuntu ubuntu    3582 Nov 20 08:05 smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:59 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     123 Nov 20 08:58 uci_options.txt
```
