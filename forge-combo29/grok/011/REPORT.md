# Seat 011, idea 11, S25

Idea S25 keeps the root search full-width until a score has landed inside the window, then arms the narrow window, and it does not treat a re-search that is still outside the window as finished for the soft time stop.
I built UCI check `IdeaS25` (default false) and spin `IdeaS25_Resolved` (default 1, range 1 to 64).
Off, the narrow window still starts at depth 4. On, depth 1 stays full-width and the window arms after `IdeaS25_Resolved` in-window root scores (default 1, so depth 2).

EXISTS: no. The plain root loop in `forge-combo29/src/search.cpp` sets the narrow window with `depth >= 4`. That is a fixed depth, not a count of scores that landed inside the bounds.

## Honesty numbers

Exe B, no setoption, from `HONESTY_B.txt` (written by `write_honesty_b.py`):

```
bench11 nodes 312866 expected 312866 match true
bench13 nodes 862329 expected 862329 match true
bench16 nodes 3024920 expected 3024920 match true
perft5 nodes 4865609 expected 4865609 match true
all_match true
```

Exe P, no setoption, from `evidence.py`:

```
HONESTY_P
bench11 nodes 312866 expected 312866 match true
bench13 nodes 862329 expected 862329 match true
bench16 nodes 3024920 expected 3024920 match true
perft5 nodes 4865609 expected 4865609 match true
```

Baseline sums, S14, Threads 1, Hash 16, from `BASELINE_B.txt`:

```
B_O_d12.rows count 200 sum 9500069 first 41311 24872 28574 sum_ok true count_ok true first_ok true
B_G_d12.rows count 353 sum 18466239 first 37203 70845 144383 sum_ok true count_ok true first_ok true
```

## Steps

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 011 idea 11
STEP 2 builds and baseline | done | HONESTY_B.txt BASELINE_B.txt | honesty match, O 9500069, G 18466239
STEP 3 idea | done | idea.patch.txt evidence.txt match_summary.txt | off identical, on differs, match played
STEP 4 partner 061 | done | partner_compare_off.txt partner_compare_on.txt partner_match_summary.txt | CONFIRMS
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

## Proofs

(1) Honesty with no setoption. Exe P matches exe B: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. See the honesty block above and `honesty_P_*.txt`.

(2) S14 and `IdeaS25` false. From `compare_off_O.txt` and `compare_off_G.txt`:

```
left forge-combo29/grok/011/B_O_d12.rows count 200 sum 9500069
right forge-combo29/grok/011/P_off_O_d12.rows count 200 sum 9500069
compared 200
differ 0 of 200
left forge-combo29/grok/011/B_G_d12.rows count 353 sum 18466239
right forge-combo29/grok/011/P_off_G_d12.rows count 353 sum 18466239
compared 353
differ 0 of 353
```

(3) S14 and `IdeaS25` true, O depth 12. From `compare_on_O.txt`:

```
left forge-combo29/grok/011/B_O_d12.rows count 200 sum 9500069
right forge-combo29/grok/011/P_on_O_d12.rows count 200 sum 9619908
compared 200
differ 179 of 200
first_differ_index 0 1 2 3 4 5 6 7 8 9
```

179 of 200 positions differ from exe B, so the new path runs. The sum is 9619908. `prediction.txt` said 9700000, wrong outside 8000000 to 12500000. The measured sum is inside that range.

(4) `uci` lists the new options. From `uci_P.txt`:

```
option name IdeaS25 type check default false
option name IdeaS25_Resolved type spin default 1 min 1 max 64
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build `/tmp/forge-A/forge`. `asan_G100_d10.meta` records `nm_asan 35`. `asan_G100_d10.txt` has 0 AddressSanitizer error lines (first 100 of G, depth 10, switch true). The scratch engine, one heap read past the end of a 4-int vector on the FEN in `scratch.fen`, run with the same `search_set.py`, reports one line in `asan_scratch.txt`: `ERROR: AddressSanitizer: heap-buffer-overflow`.

`git apply --check` of `idea.patch.txt` on the base worktree exited 0 when the patch was written.

## Match

Exe P switch true versus exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. `extract_match.py` on `match_on_off.txt`:

```
Results of on vs off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: -4.08 +/- 10.02, nElo: -8.35 +/- 20.48
LOS: 21.21 %, DrawRatio: 62.93 %, PairsRatio: 0.88
Games: 1106, Wins: 324, Losses: 337, Draws: 445, Points: 546.5 (49.41 %)
Ptnml(0-2): [10, 99, 348, 86, 10], WL/DD Ratio: 1.68
--------------------------------------------------
Finished match
Total Time: 00:07:15 (hours:minutes:seconds)
```

1106 games are in `match_on_off.pgn`. Elo -4.08 +/- 10.02. The point estimate is inside the prediction range (-30 to +40). The interval is not entirely below 0, and the point estimate is not below -20, so I did not open a second bug hunt. `prediction.txt` guessed +3.

## Partner

Partner is seat 061 (same idea, next seat with a branch). Seat 111 had no branch. `git apply --check` of their `idea.patch.txt` on a clean base worktree:

```
git_apply_check_exit 0
```

Their build, my `honesty_harness.py` and `search_set.py`. Switch false versus my exe B O rows (`partner_compare_off.txt`):

```
left forge-combo29/grok/011/B_O_d12.rows count 200 sum 9500069
right forge-combo29/grok/011/partner_off_O_d12.rows count 200 sum 9500069
compared 200
differ 0 of 200
```

Switch true versus the nodes I parsed from their `O_p_on_d12.txt` (`partner_compare_on.txt`):

```
left forge-combo29/grok/011/partner_claimed_on_O.rows count 200 sum 9619908
right forge-combo29/grok/011/partner_on_O_d12.rows count 200 sum 9619908
compared 200
differ 0 of 200
```

Switch true versus exe B (`partner_compare_on_vs_B.txt`):

```
left forge-combo29/grok/011/B_O_d12.rows count 200 sum 9500069
right forge-combo29/grok/011/partner_on_O_d12.rows count 200 sum 9619908
compared 200
differ 179 of 200
first_differ_index 0 1 2 3 4 5 6 7 8 9
```

Their proof table says O on sum 9619908 and 179 positions differ from B. My run of their patch matches both, position by position against their log. Honesty on their binary matched 312866, 862329, 3024920, and 4865609.

Their own match claim (1106 games, Elo -4.08 +/- 10.02) was not replayed. The required partner match is 300 of my R openings, both colours, their switch. `extract_match.py` on `partner_match.txt`:

```
Results of on vs off (20000 nodes, 1t, 16MB, R.fens):
Elo: -3.47 +/- 9.76, nElo: -9.90 +/- 27.80
LOS: 24.26 %, DrawRatio: 84.33 %, PairsRatio: 0.81
Games: 600, Wins: 262, Losses: 268, Draws: 70, Points: 297.0 (49.50 %)
Ptnml(0-2): [5, 21, 253, 17, 4], WL/DD Ratio: 14.81
--------------------------------------------------
Finished match
Total Time: 00:02:46 (hours:minutes:seconds)
```

Verdict: CONFIRMS. The patch applies, honesty holds, switch false matches exe B on every O position, and switch true matches their O rows on every position.

## Suspicions, not proven

Their published 1106-game score line, including the pentanomial, is the same text as mine. Their on-search nodes also match my on-search nodes on all 200 positions. Equivalent arming plus the same opening order can produce the same games. I did not prove a copy, and I did not prove the games were played independently.

## What I did NOT do

I did not measure the soft-time hold on a clock. Depth and node searches leave that path idle.
I did not rebuild their sanitizer or their scratch bug. I read their probe log and ran my own.
I did not replay their 1106-game match.
The minute-60 fetch of `handoff/fable-opus-combo29-all-20261114` had no `FABLE_TO_grok_<N>.md`. Seat 111 had no branch.
I did not try `IdeaS25_Resolved` at any value other than the default 1.

## What I am NOT sure about

I am not sure the soft-time clause changes a clock game. It was not played.
I am not sure -4.08 Elo is a real loss. The +/- 10.02 interval includes positive values.
I am not sure a value of `IdeaS25_Resolved` other than 1 is useful. Only the default was measured.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok/011/stamps.txt
?? forge-combo29/grok/011/REPORT.md
?? forge-combo29/grok/011/RESULT.txt
?? forge-combo29/grok/011/make_report.py
?? forge-combo29/grok/011/partner_apply.txt
?? forge-combo29/grok/011/partner_claimed_on_O.rows
?? forge-combo29/grok/011/partner_compare_off.txt
?? forge-combo29/grok/011/partner_compare_on.txt
?? forge-combo29/grok/011/partner_compare_on_vs_B.txt
?? forge-combo29/grok/011/partner_honesty_Partner_bench11.meta
?? forge-combo29/grok/011/partner_honesty_Partner_bench11.txt
?? forge-combo29/grok/011/partner_honesty_Partner_bench13.meta
?? forge-combo29/grok/011/partner_honesty_Partner_bench13.txt
?? forge-combo29/grok/011/partner_honesty_Partner_bench16.meta
?? forge-combo29/grok/011/partner_honesty_Partner_bench16.txt
?? forge-combo29/grok/011/partner_honesty_Partner_perft5.meta
?? forge-combo29/grok/011/partner_honesty_Partner_perft5.txt
?? forge-combo29/grok/011/partner_match.pgn
?? forge-combo29/grok/011/partner_match.txt
?? forge-combo29/grok/011/partner_match_summary.txt
?? forge-combo29/grok/011/partner_off_O_d12.meta
?? forge-combo29/grok/011/partner_off_O_d12.rows
?? forge-combo29/grok/011/partner_off_O_d12.txt
?? forge-combo29/grok/011/partner_on_O_d12.meta
?? forge-combo29/grok/011/partner_on_O_d12.rows
?? forge-combo29/grok/011/partner_on_O_d12.txt
?? forge-combo29/grok/011/run_partner_match.sh

$ ls -la forge-combo29/grok/011
total 8324
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 08:08 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     582 Nov 20 08:06 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  129030 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     924 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu       1 Nov 20 08:07 asan_scratch.rows
-rw-r--r-- 1 ubuntu ubuntu    9628 Nov 20 08:07 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:03 BASELINE_B.txt
-rw-r--r-- 1 ubuntu ubuntu     823 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:01 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  542424 Nov 20 08:01 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     827 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:01 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  304719 Nov 20 08:01 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 08:05 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:05 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:05 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     723 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1395 Nov 20 08:01 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    1815 Nov 20 08:20 evidence.py
-rw-r--r-- 1 ubuntu ubuntu    1502 Nov 20 08:20 evidence.txt
-rw-r--r-- 1 ubuntu ubuntu     363 Nov 20 08:19 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu    1349 Nov 20 08:01 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 07:57 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:57 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 07:57 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:57 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 07:57 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:57 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 07:57 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:57 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1534 Nov 20 07:57 honesty_harness.py
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 08:02 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:02 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 08:02 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:02 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 08:02 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 08:02 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:02 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5314 Nov 20 08:02 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    8437 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    7353 Nov 20 09:17 make_report.py
-rw-r--r-- 1 ubuntu ubuntu 3545720 Nov 20 08:15 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  106331 Nov 20 08:15 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu     396 Nov 20 08:19 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:09 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:09 partner_claimed_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 09:09 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:09 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 09:09 partner_honesty_Partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 09:09 partner_honesty_Partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 09:09 partner_honesty_Partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 09:09 partner_honesty_Partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 09:09 partner_honesty_Partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 09:09 partner_honesty_Partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:09 partner_honesty_Partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5314 Nov 20 09:09 partner_honesty_Partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu 1572402 Nov 20 09:12 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     383 Nov 20 09:17 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   52588 Nov 20 09:12 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     867 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:09 partner_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  304517 Nov 20 09:09 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     865 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:09 partner_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  304512 Nov 20 09:09 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     857 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:02 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  542334 Nov 20 08:02 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  304662 Nov 20 08:02 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     859 Nov 20 08:03 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 08:03 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  304694 Nov 20 08:03 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    9265 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19076 Nov 20 08:01 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1216 Nov 20 08:08 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1152 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:06 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu    6111 Nov 20 08:03 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     731 Nov 20 08:02 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     159 Nov 20 08:02 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5040 Nov 20 08:02 uci_P.txt
-rw-r--r-- 1 ubuntu ubuntu     773 Nov 20 08:00 write_honesty_b.py
```
