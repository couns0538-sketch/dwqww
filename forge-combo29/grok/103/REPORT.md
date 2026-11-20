# Seat 103, idea 3, S38

Idea S38 adds a signed fraction of a ply, from correction history, to the reduction of a quiet move: worse results reduce more, better results reduce less, and the reduction stays at least 0.
The plain engine already does that. I left the existing check option LmrSignedCorrection (default false) as the switch and turned the two fixed numbers into spin options IdeaS38_Divisor (default 64) and IdeaS38_Cap (default 1).
With the switch false the new function body is not called. With the switch true and the spins at their defaults, the formula is the one the engine already had.

EXISTS: include/forge/search.hpp:362 (apply_lmr_signed_correction) and the call at src/search.cpp:2003. The on/off is already "option name LmrSignedCorrection type check default false" in src/uci.cpp. The divisor 64 and the cap 1 were not options.

Honesty numbers, no setoption, bench 11 / bench 13 / bench 16 / go perft 5: 312866, 862329, 3024920, 4865609 on exe B and on exe P. Same four numbers on the partner build.

The block below is the output of report_table.py, which reads the raw files in this folder.

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 103, idea 3, model Grok 4.7, 2026-11-20T07:55:34Z, token 1426815293849
2 honesty B | done | HONESTY_B.txt | HONESTY_B PASS
2 O depth 12 | done | compare_off_O.txt | see proof 2
2 G depth 12 | done | compare_off_G.txt | see proof 2
3 prediction | done | prediction.txt | committed before measuring P
3 patch | done | apply_check_own.txt | own_apply_check_exit=0
3 proof 1 | done | HONESTY_p.txt | HONESTY_p PASS
3 proof 2 O | done | compare_off_O.txt | differ=0 of 200
3 proof 2 G | done | compare_off_G.txt | differ=0 of 353
3 proof 3 | done | compare_on_O.txt | differ=3 of 200
3 proof 4 | done | uci_p.txt | options listed below
3 proof 5 | done | asan_G100_d10.meta | sanitizer_lines from meta
3 match | done | match_og_summary.txt | Elo: 3.14 +/- 8.26, nElo: 7.79 +/- 20.48
4 partner | done | partner003_on_vs_claim.txt | base_mismatch_positions=114,127,191
4 partner match | done | partner003_match_summary.txt | Elo: 4.05 +/- 6.51, nElo: 17.33 +/- 27.80

HONESTY_B
exe=/tmp/forge-base-build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
HONESTY_B PASS

HONESTY_P
exe=/tmp/forge-work-build/forge
sha256=f7a0026777ad38e2ec4f91275291687ea14fc68235092f5fa8f7015810cf84b7
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
HONESTY_p PASS

COMPARE_OFF_O
left=forge-combo29/grok/103/B_O_d12.txt
right=forge-combo29/grok/103/P_off_O_d12.txt
left_count=200 right_count=200
left_sum=9500069 right_sum=9500069
differ=0 of 200

COMPARE_OFF_G
left=forge-combo29/grok/103/B_G_d12.txt
right=forge-combo29/grok/103/P_off_G_d12.txt
left_count=353 right_count=353
left_sum=18466239 right_sum=18466239
differ=0 of 353

COMPARE_ON_O
left=forge-combo29/grok/103/B_O_d12.txt
right=forge-combo29/grok/103/P_on_O_d12.txt
left_count=200 right_count=200
left_sum=9500069 right_sum=9501220
differ=3 of 200
first_differ_positions=114,127,191

UCI_OPTIONS
option name LmrSignedCorrection type check default false
option name IdeaS38_Divisor type spin default 64 min 1 max 4096
option name IdeaS38_Cap type spin default 1 min 0 max 8

ASAN_META_LINES
nm -C /tmp/forge-asan-build/forge | grep -c __asan_ = 35
sanitizer_lines=0
ASAN_SCRATCH
/tmp/forge-scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'

MATCH
Results of signed vs plain (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: 3.14 +/- 8.26, nElo: 7.79 +/- 20.48
LOS: 77.21 %, DrawRatio: 76.13 %, PairsRatio: 1.06
Games: 1106, Wins: 349, Losses: 339, Draws: 418, Points: 558.0 (50.45 %)
Ptnml(0-2): [5, 59, 421, 57, 11], WL/DD Ratio: 1.79
--------------------------------------------------
Finished match

PARTNER_OFF
left=forge-combo29/grok/103/B_O_d12.txt
right=forge-combo29/grok/103/partner003_off_O.txt
left_count=200 right_count=200
left_sum=9500069 right_sum=9500069
differ=0 of 200

PARTNER_ON
base_count=200 claim_count=201 mine_count=200
base_sum=9500069 claim_sum=19002440 mine_sum=9501220
mine_vs_base differ=3 of 200
mine_vs_partner_claim differ=0 of 200
base_mismatch_positions=114,127,191

PARTNER_HONESTY
exe=/tmp/forge-partner-build/forge
sha256=1221bd95215e764d3a07a3d442a20cd6cb6d92c93363396f25cd5279a9e34213
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
HONESTY_partner003 PASS

PARTNER_MATCH
Results of signed vs plain (20000 nodes, 1t, 16MB, R.epd):
Elo: 4.05 +/- 6.51, nElo: 17.33 +/- 27.80
LOS: 88.91 %, DrawRatio: 91.00 %, PairsRatio: 1.45
Games: 600, Wins: 273, Losses: 266, Draws: 61, Points: 303.5 (50.58 %)
Ptnml(0-2): [0, 11, 273, 14, 2], WL/DD Ratio: 14.17
--------------------------------------------------
Finished match

B_O_SUM_LINE
count=200 sum=9500069 first3=41311,24872,28574
G count=353 sum=18466239
```

## Proofs

(1) No setoption. HONESTY_p.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

(2) S14, Threads 1, Hash 16, LmrSignedCorrection false. O depth 12: differ 0 of 200, both sums 9500069, first three 41311 / 24872 / 28574. G depth 12: differ 0 of 353, both sums 18466239. compare_off_O.txt and compare_off_G.txt.

(3) Same settings with LmrSignedCorrection true. O depth 12 sum 9501220, differ 3 of 200, positions 114, 127, 191. compare_on_O.txt. Not zero, so the existing adjustment runs.

(4) uci lists "option name LmrSignedCorrection type check default false", "option name IdeaS38_Divisor type spin default 64 min 1 max 4096", and "option name IdeaS38_Cap type spin default 1 min 0 max 8". uci_p.txt.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build. First 100 of G at depth 10 with the switch true: sanitizer_lines=0. The meta line is `nm -C /tmp/forge-asan-build/forge | grep -c __asan_ = 35`. A scratch copy, not in idea.patch.txt, reads heap[8] of a four-int allocation only on the FEN k7/8/8/8/8/8/8/7K w - - 0 1. The same runner reports `runtime error: load of address ... with insufficient space for an object of type 'int'`. asan_scratch.asan.

idea.patch.txt applies to the base: apply_check_own.txt says own_apply_check_exit=0.

## Match

exe P with LmrSignedCorrection true against the same exe with it false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games, concurrency 3. fastchess from https://github.com/Disservin/fastchess at the clone's HEAD. match_og_summary.txt: Elo 3.14 +/- 8.26, 349 wins, 339 losses, 418 draws, 558.0 points. The interval is not entirely below 0, and the point is not below -20, so I did not open the code a second time.

Prediction, written before any search of exe P: O depth-12 sum 10450000, wrong below 8000000 or above 12500000; Elo +3, wrong below -25 or above +30. The measured sum 9501220 and the measured Elo 3.14 are inside those ranges. The sum's point guess was high: the tree moved by 1151 nodes.

## Partner

Partner is seat 003 (idea 3; after 103 the list wraps). Seat 053 also has a branch; it is not the next seat. git apply --check of partner003_idea.patch.txt on the base exits 0 (partner003_apply_check.txt). Their patch adds check option IdeaS38, default false, OR-ed with LmrSignedCorrection, plus IdeaS38_Divisor 64 and IdeaS38_Clamp 1.

Their build, my harness: honesty numbers match. IdeaS38 false: O depth 12 differ 0 of 200 against exe B. IdeaS38 true: differ 3 of 200 against exe B (114, 127, 191) and differ 0 of the 200 position rows against their O_P_on.nodes. That file has a 201st line, "SUM 9501220", which the parser also added, so claim_count is 201 and claim_sum is twice 9501220. The 200 positions themselves match. Their claim on_differs=3 of 200 and off_identical=yes holds.

Match of their IdeaS38 true against false, 300 of my R openings, both colours, 600 games: Elo 4.05 +/- 6.51. partner003_match_summary.txt.

Verdict: CONFIRMS. I did not re-run their sanitizer build.

## Suspicions, not proven

The depth-12 change is three positions and 1151 nodes. The 1106-game score is 50.45 percent. That is compatible with a real gain and with noise. I am not claiming the idea wins on the owner's net.

Seat 003's match Elo is the same 3.14 +/- 8.26 as mine. Their on-formula with defaults is the same adjustment the engine already had, and the games are deterministic at a fixed node count, so the same openings can produce the same Elo without anyone copying a result. I did not check their PGN move by move.

## What I did NOT do

I did not add a second on/off named IdeaS38. The on/off already existed. I did not play seat 053. I did not re-run seat 003's sanitizer. I did not try IdeaS38_Divisor or IdeaS38_Cap away from 64 and 1 in a match. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not open a pull request.

## What I am NOT sure about

Whether a cap other than 1 would change more than three of the 200 positions. The prediction's "wrong if" window was wide, so a small node change could not falsify the sum. make_r.py drops a game that ends before ply 80; all 30 games were still going, so the drop rule never fired. R is 300 positions from those 30 games.

times: see stamps.txt

RESULT.txt:
seat=103 idea=3 id=S38 option=LmrSignedCorrection exists=yes:include/forge/search.hpp:362 applies=yes off_identical=yes on_differs=3 of 200 sanitizer=clean elo=3.14 err=8.26 games=1106 partner=003 partner_verdict=CONFIRMS

## git status --short

```
 M forge-combo29/grok/103/match.sh
 M forge-combo29/grok/103/stamps.txt
?? forge-combo29/grok/103/HONESTY_partner003.txt
?? forge-combo29/grok/103/REPORT.md
?? forge-combo29/grok/103/RESULT.txt
?? forge-combo29/grok/103/apply_check_own.txt
?? forge-combo29/grok/103/honesty_partner003_bench11.meta
?? forge-combo29/grok/103/honesty_partner003_bench11.txt
?? forge-combo29/grok/103/honesty_partner003_bench13.meta
?? forge-combo29/grok/103/honesty_partner003_bench13.txt
?? forge-combo29/grok/103/honesty_partner003_bench16.meta
?? forge-combo29/grok/103/honesty_partner003_bench16.txt
?? forge-combo29/grok/103/honesty_partner003_perft5.meta
?? forge-combo29/grok/103/honesty_partner003_perft5.txt
?? forge-combo29/grok/103/partner003_apply_check.txt
?? forge-combo29/grok/103/partner003_claim_O_on.nodes
?? forge-combo29/grok/103/partner003_idea.patch.txt
?? forge-combo29/grok/103/partner003_match.log
?? forge-combo29/grok/103/partner003_match.pgn
?? forge-combo29/grok/103/partner003_match_summary.txt
?? forge-combo29/grok/103/partner003_off_O.meta
?? forge-combo29/grok/103/partner003_off_O.nodes
?? forge-combo29/grok/103/partner003_off_O.txt
?? forge-combo29/grok/103/partner003_off_vs_B.txt
?? forge-combo29/grok/103/partner003_on_O.meta
?? forge-combo29/grok/103/partner003_on_O.nodes
?? forge-combo29/grok/103/partner003_on_O.txt
?? forge-combo29/grok/103/partner003_on_vs_claim.txt
?? forge-combo29/grok/103/partner_compare.py
?? forge-combo29/grok/103/report_table.out
?? forge-combo29/grok/103/report_table.py
```

## ls -la

```
total 9792
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:20 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:19 apply_check_own.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100_d10.asan
-rw-r--r-- 1 ubuntu ubuntu     956 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131742 Nov 20 08:07 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     150 Nov 20 08:08 asan_scratch.asan
-rw-r--r-- 1 ubuntu ubuntu     971 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    7305 Nov 20 08:08 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     835 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:03 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  549890 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308908 Nov 20 08:02 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:09 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     167 Nov 20 08:09 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:09 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1583 Nov 20 08:06 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu    1472 Nov 20 08:10 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:00 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:00 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:00 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:00 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 08:00 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:00 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3973 Nov 20 08:04 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     289 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 honesty_partner003_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:12 honesty_partner003_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 honesty_partner003_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:12 honesty_partner003_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 honesty_partner003_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 09:12 honesty_partner003_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:12 honesty_partner003_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 09:12 honesty_partner003_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     301 Nov 20 09:12 HONESTY_partner003.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:04 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5114 Nov 20 08:04 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:04 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5114 Nov 20 08:04 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:04 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5116 Nov 20 08:04 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 08:04 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5327 Nov 20 08:04 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     289 Nov 20 08:04 HONESTY_p.txt
-rw-r--r-- 1 ubuntu ubuntu    3413 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1595 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  138381 Nov 20 08:16 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 4532899 Nov 20 08:16 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     352 Nov 20 08:19 match_og_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    1305 Nov 20 09:13 match.sh
-rw-r--r-- 1 ubuntu ubuntu     613 Nov 20 08:09 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu   14297 Nov 20 08:09 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     439 Nov 20 08:19 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 09:19 partner003_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 09:13 partner003_claim_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    6690 Nov 20 09:13 partner003_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   70512 Nov 20 09:16 partner003_match.log
-rw-r--r-- 1 ubuntu ubuntu 1990135 Nov 20 09:16 partner003_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     341 Nov 20 09:18 partner003_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 09:12 partner003_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:12 partner003_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309502 Nov 20 09:12 partner003_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:13 partner003_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 09:12 partner003_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:12 partner003_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309241 Nov 20 09:12 partner003_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:13 partner003_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu    1605 Nov 20 09:13 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     882 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:05 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  549806 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308994 Nov 20 08:04 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:05 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309000 Nov 20 08:05 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     790 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19023 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu   17772 Nov 20 09:20 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4170 Nov 20 09:19 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    3467 Nov 20 09:19 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:20 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    4374 Nov 20 08:07 sanitizer_run.py
-rw-r--r-- 1 ubuntu ubuntu    7075 Nov 20 08:08 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     242 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1613 Nov 20 08:06 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 08:07 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5053 Nov 20 08:07 uci_p.txt
```
