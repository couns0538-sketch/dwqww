Idea 39 (A8). UCI check IdeaA8, default false, and spin IdeaA8_Captures, default 1 (min 0, max 32).
In quiescence, when not in check, a searched capture that does not raise alpha counts as a miss. After IdeaA8_Captures misses, later captures are skipped unless they land on the square the parent move just moved to.
Quiet promotions stay. Evasions in check stay. Futility and static-exchange skips are not counted. With the check false those branches are not taken.

EXISTS: no. I read `forge-combo29/src/search.cpp` `Worker::qsearch`. It already drops some captures by futility and by `see_ge`. It does not count alpha misses and it does not keep only recaptures.

Honesty, no setoption, fresh process each line. Exe B and exe P both:

```
bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK
PASS
```

Base sums under S14, Threads 1, Hash 16: O depth 12 sum 9500069, first three 41311 / 24872 / 28574. G depth 12 sum 18466239.

Table printed by `report_table.py` from the raw files. The Elo cells are the last `Elo:` line, which is the finished match. Earlier `Elo:` lines are fastchess rating intervals.

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt | seat 039, idea 39, model Grok 4.7, 2026-11-20T07:53:26Z, token 242472437622515
STEP 2 honesty B | done | HONESTY_B.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK | PASS |
STEP 2 O depth 12 | done | B_O_d12.meta | sum=9500069 positions=200
STEP 2 G depth 12 | done | B_G_d12.meta | sum=18466239 positions=353
3b prediction | done | prediction.txt | committed before measuring P
3c patch applies | done | apply_check_own.txt | own apply --check ok
3d honesty P | done | HONESTY_P.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK | PASS |
3d off O | done | cmp_off_O.txt | differ=0 equal=200
3d off G | done | cmp_off_G.txt | differ=0 equal=353
3d on O | done | cmp_on_O.txt | differ=200 sum_right=9328352
3d uci options | done | P_uci.txt | option name IdeaA8 type check default false ; option name IdeaA8_Captures type spin default 1 min 0 max 32
3d sanitizer | done | asan_G_d10.meta | nm_asan_count=35 sanitizer_lines=0 positions=100
3d sanitizer canary | done | canary_d10.meta | nm_asan_count=35 sanitizer_lines=1
3e match | done | match.txt | Elo: -5.03 +/- 10.77, nElo: -9.56 +/- 20.48
STEP 4 partner patch | done | apply_check_partner.txt | partner apply --check ok
STEP 4 partner off | done | cmp_partner_off_O.txt | differ=0
STEP 4 partner on vs own rows | done | cmp_partner_on_O.txt | differ=0 sum_mine=9779075
STEP 4 partner on vs B | done | cmp_partner_on_vs_B.txt | differ=200 sum_right=9779075
STEP 4 partner match | done | partner_match.txt | Elo: 1.16 +/- 9.36, nElo: 3.44 +/- 27.80
```

Proofs on exe P.

(1) Honesty with no setoption: the four numbers above, PASS. Files `P_bench11.txt`, `P_bench13.txt`, `P_bench16.txt`, `P_perft5.txt`.

(2) S14 and IdeaA8 false. O depth 12: differ 0 of 200, both sums 9500069. G depth 12: differ 0 of 353, both sums 18466239.

(3) S14 and IdeaA8 true (spin left at default 1). O depth 12 sum 9328352. differ 200 of 200 against exe B.

(4) `uci` lists `option name IdeaA8 type check default false` and `option name IdeaA8_Captures type spin default 1 min 0 max 32`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `nm -C` count of `__asan_` is 35. First 100 of G at depth 10, switch true: 0 sanitizer lines, sum 1784098. The same runner on a scratch copy with one deliberate read past a 4-int heap array, on FEN `4k3/8/8/8/4P3/8/8/4K3 w - - 77 13`, printed: `/agent/repos/scratch/forge-combo29/src/search.cpp:1577:22: runtime error: load of address 0x502000001080 with insufficient space for an object of type 'int'`. Environment for both runs: `ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:symbolize=0` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=0`.

`git apply --check` of `idea.patch.txt` on a clean base tree succeeded (`apply_check_own.txt`).

Match, exe P switch true versus exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games, concurrency 3. From `show_match.py` on `match.txt`:

```
Elo: -5.03 +/- 10.77, nElo: -9.56 +/- 20.48
LOS: 18.00 %, DrawRatio: 59.86 %, PairsRatio: 0.87
Games: 1106, Wins: 329, Losses: 345, Draws: 432, Points: 545.0 (49.28 %)
Ptnml(0-2): [14, 105, 331, 89, 14], WL/DD Ratio: 1.78
```

Prediction in `prediction.txt` was O sum 8800000, wrong outside 6500000 to 11000000, and Elo -6, wrong outside -35 to +25. Measured 9328352 and -5.03. Neither falls in the "wrong" range. The final Elo is not below -20, and the interval is not entirely below 0, so I did not open the code for a second look.

Partner is seat 089 (idea 39). Seat 139 is outside 001..120. I fetched `for-fable-and-opus/grok-089`. The patch I built is commit `bb6a92367c5e39e8ce56ee1e58ed5284a2104b50`. A later commit `f1b308c17190b74801140ef83939027120451489` adds their match files; `cmp` said the patch bytes were unchanged. `git apply --check` on a clean base succeeded. Honesty matched the four known node counts. Switch false: O depth 12 differ 0 of 200 against exe B. Switch true: O depth 12 differ 0 of 200 against their `P_on_O_d12.txt` rows, sum 9779075, and differ 200 of 200 against exe B. That is what their `proof_off_O.txt`, `proof_on_O.txt`, and `HONESTY_P.txt` say. Verdict: CONFIRMS. My 300 R openings, both colours, 600 games, their switch on versus off:

```
Elo: 1.16 +/- 9.36, nElo: 3.44 +/- 27.80
LOS: 59.58 %, DrawRatio: 81.33 %, PairsRatio: 1.15
Games: 600, Wins: 263, Losses: 261, Draws: 76, Points: 301.0 (50.17 %)
Ptnml(0-2): [3, 23, 244, 29, 1], WL/DD Ratio: 19.33
```

suspicions, not proven

Their published 1106-game summary at `f1b308c` says Elo -12.26 +/- 10.17. I did not replay that match. My own 1106-game run of a different patch (N=1, misses counted only after a search) was -5.03 +/- 10.77. I do not treat those two Elos as a disagreement about the same binary. Draws by threefold repetition, the fifty-move rule, and insufficient mating material in `match.txt` are legal results. The low draw rate on R (76 of 600) fits random middlegame positions.

what I did NOT do

I did not wait until minute 75. Their patch was already on the branch when my match finished. I did not replay their 1106-game match. I did not try IdeaA8_Captures at any value except the default 1. I did not run a second match of my own patch. The handoff branch had no `FABLE_TO_grok_*.md` at step 1 or at the fetch before this report. Minute 60 after the first stamp had not arrived yet. I did not open a pull request.

what I am NOT sure about

The match interval -5.03 +/- 10.77 includes both sides of zero, so I am not sure the point estimate is a real loss. The canary line is UndefinedBehaviorSanitizer's "runtime error" report. `nm` shows AddressSanitizer is in the binary (`__asan_` count 35). I am not sure AddressSanitizer would have printed its own banner, because `halt_on_error=1` stopped the process on the UBSan line. Leak detection was off, so this run does not speak about leaks.

times: see stamps.txt

`git status --short`

```
 M forge-combo29/grok/039/stamps.txt
?? forge-combo29/grok/039/HONESTY_PARTNER.txt
?? forge-combo29/grok/039/Partner_bench11.meta
?? forge-combo29/grok/039/Partner_bench11.txt
?? forge-combo29/grok/039/Partner_bench13.meta
?? forge-combo29/grok/039/Partner_bench13.txt
?? forge-combo29/grok/039/Partner_bench16.meta
?? forge-combo29/grok/039/Partner_bench16.txt
?? forge-combo29/grok/039/Partner_off_O_d12.meta
?? forge-combo29/grok/039/Partner_off_O_d12.nodes
?? forge-combo29/grok/039/Partner_off_O_d12.stderr
?? forge-combo29/grok/039/Partner_off_O_d12.txt
?? forge-combo29/grok/039/Partner_on_O_d12.meta
?? forge-combo29/grok/039/Partner_on_O_d12.nodes
?? forge-combo29/grok/039/Partner_on_O_d12.stderr
?? forge-combo29/grok/039/Partner_on_O_d12.txt
?? forge-combo29/grok/039/Partner_perft5.meta
?? forge-combo29/grok/039/Partner_perft5.txt
?? forge-combo29/grok/039/R.fen
?? forge-combo29/grok/039/REPORT.md
?? forge-combo29/grok/039/RESULT.txt
?? forge-combo29/grok/039/apply_check_own.txt
?? forge-combo29/grok/039/apply_check_partner.txt
?? forge-combo29/grok/039/cmp_partner_off_O.txt
?? forge-combo29/grok/039/cmp_partner_on_O.txt
?? forge-combo29/grok/039/cmp_partner_on_vs_B.txt
?? forge-combo29/grok/039/compare_partner.py
?? forge-combo29/grok/039/config.json
?? forge-combo29/grok/039/make_r.py
?? forge-combo29/grok/039/match.pgn
?? forge-combo29/grok/039/match.txt
?? forge-combo29/grok/039/partner_089.patch.txt
?? forge-combo29/grok/039/partner_089_on_O.tsv
?? forge-combo29/grok/039/partner_match.pgn
?? forge-combo29/grok/039/partner_match.sh
?? forge-combo29/grok/039/partner_match.txt
?? forge-combo29/grok/039/report_table.out
?? forge-combo29/grok/039/report_table.py
?? forge-combo29/grok/039/show_match.py
```

`ls -la`

```
total 10296
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:24 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 08:17 apply_check_own.txt
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:17 apply_check_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     909 Nov 20 08:09 asan_G_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     580 Nov 20 08:09 asan_G_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 asan_G_d10.stderr
-rw-r--r-- 1 ubuntu ubuntu  239222 Nov 20 08:09 asan_G_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:59 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:59 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 07:59 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:03 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 B_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  913215 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     883 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 B_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  514513 Nov 20 08:02 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1091 Nov 20 08:08 canary_d10.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 canary_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 08:08 canary_d10.stderr
-rw-r--r-- 1 ubuntu ubuntu    6571 Nov 20 08:08 canary_d10.txt
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:07 canary.fen
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:04 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 08:04 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     287 Nov 20 08:04 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 08:17 cmp_partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:17 cmp_partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     287 Nov 20 08:22 cmp_partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     729 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     936 Nov 20 08:12 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    6962 Nov 20 08:20 config.json
-rw-r--r-- 1 ubuntu ubuntu    8359 Nov 20 08:08 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:09 design.txt
-rw-r--r-- 1 ubuntu ubuntu    2324 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:16 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6548 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1118 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3623198 Nov 20 08:16 match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1219 Nov 20 08:09 match.sh
-rw-r--r-- 1 ubuntu ubuntu    7645 Nov 20 08:09 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu  132583 Nov 20 08:16 match.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu   17558 Nov 20 08:11 partner_089_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu    8051 Nov 20 08:11 partner_089.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:16 Partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:16 Partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:16 Partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:16 Partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:16 Partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:16 Partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu 1540208 Nov 20 08:20 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1009 Nov 20 08:12 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   70240 Nov 20 08:20 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     936 Nov 20 08:17 Partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:17 Partner_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:17 Partner_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  525844 Nov 20 08:17 Partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     935 Nov 20 08:17 Partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1205 Nov 20 08:17 Partner_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:17 Partner_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  526067 Nov 20 08:17 Partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 08:16 Partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:16 Partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:03 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:03 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 08:03 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 07:59 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:04 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:04 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  934094 Nov 20 08:04 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  526350 Nov 20 08:04 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     916 Nov 20 08:04 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:04 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  526216 Nov 20 08:04 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:03 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     300 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:04 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:04 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7415 Nov 20 08:24 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1819 Nov 20 08:23 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    3323 Nov 20 08:23 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:24 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19365 Nov 20 08:11 R.fen
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     371 Nov 20 08:18 show_match.py
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:24 stamps.txt
```
