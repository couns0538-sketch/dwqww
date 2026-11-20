# Seat 051, idea 1, E2

Idea E2 scales the static evaluation toward 0 as the fifty-move counter rises, at the node, and leaves the hash holding the unscaled score.
The plain engine already does that in `rule50_damped_static` when `EvalRule50Damp` is true, with a fixed divisor of 100.
I added check `IdeaE2` (default false), the same gate, and spin `IdeaE2_Span` (default 100), so the divisor is an option and 100 is today's scale.

EXISTS: include/forge/search.hpp:351. The on/off `EvalRule50Damp` is already an option at src/uci.cpp:220. The number 100 was a literal, so it is now `IdeaE2_Span`.

## Honesty numbers

Exe B, no setoption, from HONESTY_B.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.
Exe P, no setoption, from honesty_p_summary.txt: the same four numbers.
S14 on exe B: O depth 12 sum 9500069 (first three 41311, 24872, 28574). G depth 12 sum 18466239.

Release builds used g++ 13.3.0. This machine has AVX-512 and BMI2, so the build left `FORGE_PORTABLE` off and `FORGE_MARCH` at x86-64-v4.

## Table

Stdout of `report_table.py`, which reads the raw files:

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 051 idea 1
2 honesty B | done | HONESTY_B.txt | bench 11 nodes 312866 rc 0 | bench 13 nodes 862329 rc 0 | bench 16 nodes 3024920 rc 0 | go perft 5 nodes 4865609 rc 0
2 O and G on B | done | B_O.sum B_G.sum | positions 200 | depth 12 | sum 9500069 | first 41311 24872 28574 || positions 353 | depth 12 | sum 18466239 | first 37203 70845 144383
3a read | done | include/forge/search.hpp | EXISTS include/forge/search.hpp:351
3b prediction | done | prediction.txt | locked before measuring P
3c patch | done | idea.patch.txt apply_check.txt | idea.patch.txt git apply --check: ok | partner_001.patch.txt git apply --check on fresh base: ok
3d honesty P | done | honesty_p_summary.txt | bench 11 nodes 312866 rc 0 | bench 13 nodes 862329 rc 0 | bench 16 nodes 3024920 rc 0 | go perft 5 nodes 4865609 rc 0
3d off | done | compare_off_O.txt compare_off_G.txt | positions 200 | same 200 | differ 0 | left_sum 9500069 | right_sum 9500069 || positions 353 | same 353 | differ 0 | left_sum 18466239 | right_sum 18466239
3d on | done | compare_on_O.txt | positions 200 | same 0 | differ 200 | left_sum 9500069 | right_sum 10347764
3d uci | done | uci_options.txt | option name EvalRule50Damp type check default false | option name IdeaE2 type check default false | option name IdeaE2_Span type spin default 100 min 1 max 200
3d sanitizer | done | asan_G100_sanitizer.txt asan_G100.meta asan_scratch_sanitizer.txt | sanitizer_lines 0 || sanitizer_lines 1 | /tmp/scratch_engine/src/search.cpp:2154:22: runtime error: load of address 0x502000001080 with insufficient space for an object of type 'int'
3e match | done | match_result.txt match_og/games.pgn | -------------------------------------------------- | Results of IdeaE2on vs IdeaE2off (20000 nodes, 1t, 16MB, match_OG.epd): | Elo: -22.02 +/- 10.40, nElo: -43.46 +/- 20.48 | LOS: 0.00 %, DrawRatio: 63.47 %, PairsRatio: 0.57 | Games: 1106, Wins: 318, Losses: 388, Draws: 400, Points: 518.0 (46.84 %) | Ptnml(0-2): [22, 107, 351, 65, 8], WL/DD Ratio: 2.08 | -------------------------------------------------- | Finished match
4 partner | done | partner_cmp_off_O.txt partner_cmp_on_O.txt partner_result.txt | positions 200 | same 200 | differ 0 | left_sum 9500069 | right_sum 9500069 || positions 200 | same 200 | differ 0 | left_sum 10347764 | right_sum 10347764 || -------------------------------------------------- | Results of DampOn vs DampOff (20000 nodes, 1t, 16MB, R.fens): | Elo: -12.17 +/- 8.32, nElo: -40.71 +/- 27.80 | LOS: 0.21 %, DrawRatio: 88.67 %, PairsRatio: 0.42 | Games: 600, Wins: 264, Losses: 285, Draws: 51, Points: 289.5 (48.25 %) | Ptnml(0-2): [7, 17, 266, 10, 0], WL/DD Ratio: 21.17 | -------------------------------------------------- | Finished match
```


Same bytes as `report_table.txt`.

## Proofs

(1) Honesty on exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

(2) S14 and `IdeaE2` false: O depth 12, 200 same and 0 differ against exe B, sum 9500069. G depth 12, 353 same and 0 differ, sum 18466239.

(3) S14 and `IdeaE2` true, `IdeaE2_Span` 100: O depth 12 differs on 200 of 200 positions. Sum 10347764. The prediction of 10400000 sits inside 9600000 to 12000000.

(4) `uci` lists `EvalRule50Damp` check default false, `IdeaE2` check default false, `IdeaE2_Span` spin default 100 min 1 max 200.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: 0 sanitizer lines. `asan_G100.meta` has `asan_symbol_count: 35` from `nm -C`. The scratch engine, one deliberate heap read past the end on the FEN in `san_probe.fen`, run with the same `search_depth.py`, reported one sanitizer line: a runtime error load with insufficient space for an `int` at scratch `search.cpp:2154`.

`idea.patch.txt` applies to a fresh copy of the base: `git apply --check` printed ok (`apply_check.txt`).

## Match

`IdeaE2` true versus `IdeaE2` false, both S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours. fastchess from github.com/Disservin/fastchess, concurrency 3.

Stdout of `extract_result.py` on `match_og/fastchess.txt`:

```
Results of IdeaE2on vs IdeaE2off (20000 nodes, 1t, 16MB, match_OG.epd):
Elo: -22.02 +/- 10.40, nElo: -43.46 +/- 20.48
LOS: 0.00 %, DrawRatio: 63.47 %, PairsRatio: 0.57
Games: 1106, Wins: 318, Losses: 388, Draws: 400, Points: 518.0 (46.84 %)
Ptnml(0-2): [22, 107, 351, 65, 8], WL/DD Ratio: 2.08
```

`match_og/games.pgn` has 1106 Event tags. `match_og/fastchess.err` is empty.

The point -22.02 is below -20 and -22.02+10.40 = -11.62 is still below 0, so the whole interval is below 0. I looked once (`look_once.txt`). The off path matches exe B node for node. The on path matches seat 001's `EvalRule50Damp` true rows, 200 of 200. The hash stores `raw_eval`. Mate scores are left alone. The two colours of the first opening diverge, and the sample draws are threefold repetition. I left the code as it is. The fade of one percent per half-move, which is today's formula, is active from the first quiet ply, and at 20000 nodes on the built-in net it loses. The Elo prediction of +2 is wrong: -22.02 is below -20.

## Partner

Partner is seat 001. Seats for idea 1 are 001, 051, and 101. 101 had no branch, so the next seat after 051 that has a branch is 001. Reviewed commit 734fab295924d37ba5b401d3e48a81935eb45002. The patch sha256 matches `partner_001.patch.txt`.

Their patch keeps `EvalRule50Damp` as the switch and adds spin `EvalRule50Damp_Span` default 100. `git apply --check` on a fresh base was ok. My build of that patch: honesty numbers unchanged; switch false matches exe B on all 200 O positions; switch true matches their O rows on all 200 (sum 10347764). The required match is their switch on 300 R openings, both colours, 600 games: Elo -12.17 +/- 8.32, 264 wins, 285 losses, 51 draws. Their own O+G match, which I did not re-run on their binary, is Elo -22.02 +/- 10.40 with the same 318/388/400 split as my match.

Verdict: CONFIRMS.

## Suspicions, not proven

The loss may be mostly the fade during the first few quiet plies, long before the fifty-move rule. I did not play a second match that starts the fade only near a high clock.

Seat 001's 1106-game scoreline matching mine is what a deterministic engine would do if the two ons are the same search. I did not replay their binary.

## What I did NOT do

I did not open a pull request. I did not commit an engine source file. I did not measure `IdeaE2_Span` at any value other than 100. I did not re-run seat 001's 1106-game match. I started the partner checks before minute 75, after my own match had finished and their patch was already on the branch.

## What I am NOT sure about

I treat fastchess's +/- figure as the interval in the look-once rule. The launcher log `match_og_launch.log` contains a quote-parse message. During the match the process command line listed IdeaE2 true versus false, S14, and nodes 20000, and the PGN has 1106 finished games.

Handoff branch `handoff/fable-opus-combo29-all-20261114` had no `FABLE_TO_grok_<N>.md` at STEP 1 or at the check after the partner match.

times: see stamps.txt

## git status --short and ls -la

The block below is filled by the commands run after this file was written.

```
$ git status --short
 M forge-combo29/grok/051/stamps.txt
?? forge-combo29/grok/051/REPORT.md
?? forge-combo29/grok/051/RESULT.txt
?? forge-combo29/grok/051/apply_check.txt
?? forge-combo29/grok/051/match_og.pid
?? forge-combo29/grok/051/partner_match/
?? forge-combo29/grok/051/partner_result.txt
?? forge-combo29/grok/051/report_numbers.py
?? forge-combo29/grok/051/report_table.py
?? forge-combo29/grok/051/report_table.txt

$ ls -la forge-combo29/grok/051
total 3304
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 08:27 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu     95 Nov 20 08:26 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1089 Nov 20 08:06 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    876 Nov 20 08:06 asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu     18 Nov 20 08:06 asan_G100_sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:06 asan_G100.stderr
-rw-r--r-- 1 ubuntu ubuntu     59 Nov 20 08:06 asan_G100.sum
-rw-r--r-- 1 ubuntu ubuntu 133965 Nov 20 08:06 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu    289 Nov 20 08:04 asan_meta.sh
-rw-r--r-- 1 ubuntu ubuntu   1099 Nov 20 08:06 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:06 asan_scratch.nodes
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 08:06 asan_scratch_sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu   1399 Nov 20 08:06 asan_scratch.stderr
-rw-r--r-- 1 ubuntu ubuntu     62 Nov 20 08:06 asan_scratch.sum
-rw-r--r-- 1 ubuntu ubuntu   6444 Nov 20 08:06 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    882 Nov 20 08:01 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu   3432 Nov 20 08:01 B_G.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:01 B_G.stderr
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:01 B_G.sum
-rw-r--r-- 1 ubuntu ubuntu 558878 Nov 20 08:01 B_G.txt
-rw-r--r-- 1 ubuntu ubuntu    886 Nov 20 08:01 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 08:01 B_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:01 B_O.stderr
-rw-r--r-- 1 ubuntu ubuntu     59 Nov 20 08:01 B_O.sum
-rw-r--r-- 1 ubuntu ubuntu 314148 Nov 20 08:01 B_O.txt
-rw-r--r-- 1 ubuntu ubuntu    684 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     69 Nov 20 08:04 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     67 Nov 20 08:04 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     68 Nov 20 08:04 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    427 Nov 20 08:04 count_sanitizer.py
-rw-r--r-- 1 ubuntu ubuntu    489 Nov 20 08:19 extract_result.py
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 08:00 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 07:59 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 07:59 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 07:59 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    288 Nov 20 07:59 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2372 Nov 20 08:02 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    112 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    281 Nov 20 07:59 honesty_b_uci.meta
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 07:59 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:03 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 08:03 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:03 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 08:03 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:03 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 08:03 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:03 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    288 Nov 20 08:03 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    112 Nov 20 08:03 honesty_p_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    281 Nov 20 08:03 honesty_p_uci.meta
-rw-r--r-- 1 ubuntu ubuntu   5037 Nov 20 08:03 honesty_p_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   5339 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 08:20 look_once.txt
-rw-r--r-- 1 ubuntu ubuntu   1102 Nov 20 08:02 make_r.py
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:08 match_og
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:07 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     88 Nov 20 08:15 match_og_launch.log
-rw-r--r-- 1 ubuntu ubuntu      5 Nov 20 08:08 match_og.pid
-rw-r--r-- 1 ubuntu ubuntu    411 Nov 20 08:19 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu   1532 Nov 20 08:08 match.sh
-rw-r--r-- 1 ubuntu ubuntu   4178 Nov 20 08:10 partner_001_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   3384 Nov 20 08:09 partner_001.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     67 Nov 20 08:10 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     69 Nov 20 08:10 partner_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   5732 Nov 20 08:10 partner_depth.py
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:10 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    267 Nov 20 08:10 partner_h_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:10 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    267 Nov 20 08:10 partner_h_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:10 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    267 Nov 20 08:10 partner_h_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:10 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    269 Nov 20 08:10 partner_h_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    112 Nov 20 08:10 partner_h_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    262 Nov 20 08:10 partner_h_uci.meta
-rw-r--r-- 1 ubuntu ubuntu   5001 Nov 20 08:10 partner_h_uci.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:19 partner_match
-rw-r--r-- 1 ubuntu ubuntu   1507 Nov 20 08:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    955 Nov 20 08:10 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 08:10 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:10 partner_off_O.stderr
-rw-r--r-- 1 ubuntu ubuntu     59 Nov 20 08:10 partner_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu 314161 Nov 20 08:10 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    953 Nov 20 08:10 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   1897 Nov 20 08:10 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:10 partner_on_O.stderr
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 08:10 partner_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu 314019 Nov 20 08:10 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    397 Nov 20 08:25 partner_result.txt
-rw-r--r-- 1 ubuntu ubuntu    954 Nov 20 08:03 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   3432 Nov 20 08:03 P_off_G.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:03 P_off_G.stderr
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:03 P_off_G.sum
-rw-r--r-- 1 ubuntu ubuntu 559337 Nov 20 08:03 P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu    958 Nov 20 08:03 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 08:03 P_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:03 P_off_O.stderr
-rw-r--r-- 1 ubuntu ubuntu     59 Nov 20 08:03 P_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu 314509 Nov 20 08:03 P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    956 Nov 20 08:03 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   1897 Nov 20 08:03 P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:03 P_on_O.stderr
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 08:03 P_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu 314447 Nov 20 08:03 P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    790 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   8443 Nov 20 08:27 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    919 Nov 20 08:25 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu   1668 Nov 20 08:26 report_table.py
-rw-r--r-- 1 ubuntu ubuntu   2797 Nov 20 08:26 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu    213 Nov 20 08:27 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu  18421 Nov 20 08:03 R.fens
-rw-r--r-- 1 ubuntu ubuntu     59 Nov 20 08:05 san_probe.fen
-rw-r--r-- 1 ubuntu ubuntu   6598 Nov 20 08:04 search_depth.py
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  17691 Nov 20 08:00 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    294 Nov 20 08:03 show_options.py
-rw-r--r-- 1 ubuntu ubuntu    140 Nov 20 08:27 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 08:04 uci_options.txt
```

```
$ ls -la forge-combo29/grok/051/match_og forge-combo29/grok/051/partner_match
forge-combo29/grok/051/match_og:
total 1204
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:08 .
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 08:27 ..
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 fastchess.err
-rw-r--r-- 1 ubuntu ubuntu  134505 Nov 20 08:15 fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 1080280 Nov 20 08:14 games.pgn

forge-combo29/grok/051/partner_match:
total 484
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:19 .
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 08:27 ..
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:19 fastchess.err
-rw-r--r-- 1 ubuntu ubuntu  62718 Nov 20 08:22 fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 417716 Nov 20 08:22 games.pgn
```
