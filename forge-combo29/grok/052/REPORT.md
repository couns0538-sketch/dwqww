# grok 052

Idea S28 keeps a quiet from-to history for the cheapest cheaper enemy attacker of the origin: none, pawn, minor, or rook.
The UCI option is IdeaS28, type check, default false. There is no spin. The table uses the existing history bonus, and with the option off the read and the write return before they touch it.
No constant threat bonus is added. The destination is not part of the index. Details are in DECISIONS.txt. The change is idea.patch.txt.

EXISTS: no. ThreatHistory in forge-combo29/src/search.cpp:97 and quiet_threat_index at forge-combo29/src/search.cpp:290 is a different table: one bit for "attacked by a cheaper enemy" on the origin and one bit on the destination. It is not the four attacker classes on the origin only.

Honesty numbers, the step table, proofs, the match, and the partner numbers are the output of report_tables.py below. That script reads the raw files.

## Proofs

(1) HONESTY_P.txt matches bench 11 / 13 / 16 and perft 5 with no setoption.
(2) IdeaS28 false, S14: O depth 12 differs in 0 of 200 positions from exe B, and G depth 12 differs in 0 of 353.
(3) IdeaS28 true, S14: O depth 12 differs in 200 of 200 positions. The sum is 10163822.
(4) The uci listing contains `option name IdeaS28 type check default false`.
(5) The sanitizer build has nm_asan 35. The first 100 positions of G at depth 10 with the switch true finished with 0 sanitizer lines. The same runner on the scratch engine, which reads past a 4-int heap array on one special FEN, reported the runtime-error line in san_canary.err. Leak detection was off, so this does not speak about leaks.

git apply --check of idea.patch.txt on the clean base printed APPLY_CHECK_OK.

## Match

IdeaS28 true against IdeaS28 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours: 1106 games. Elo -0.63 +/- 10.23. The interval is not entirely below 0, so the "look once for a mistake" rule did not apply. Prediction was sum 9350000 (wrong outside 8500000..10500000 or if equal to 9500069) and Elo +3 (wrong below -20 or above +25). The measured sum 10163822 and Elo -0.63 are inside those ranges.

## Partner

Seat 102 had no branch at the minute-75 check, so the partner is 002. idea.patch.txt applied on a fresh base (`APPLY_CHECK_OK` in the partner build log). Their engine's honesty numbers match. Switch false matches exe B on O depth 12 (0 differ). Switch true matches their own published O depth-12 rows (0 differ, sum 10100354). Verdict: CONFIRMS. I also played their switch on 300 R openings, both colours, 600 games: Elo -9.85 +/- 9.91. That is my measurement, not a replay of their 1106-game O+G match.

## suspicions, not proven

All 200 O positions changed at depth 12. Position 2 changed by 4 nodes, so the option does run, and a change can be small. I have not shown that the class split is better than one extra from-to history with no classes. The R match of the partner patch was negative but the interval reaches above 0.

## what I did NOT do

I did not replay the partner's 1106-game match. I did not add a scale spin. I did not run leak detection. I did not test the owner's training net. At minute 60 and at STEP 1 there was no FABLE_TO_grok file. Seat 102 never appeared, so it was not reviewed.

## what I am NOT sure about

A queen attacking the king is not one of the four named classes, so that attack stays class 0. I am not sure the idea wanted the quarter-bonus update on a quiet that becomes best without a cutoff; I copied the main quiet history's three update sites. I am not sure a 1106-game node match can tell a small Elo gain from noise. The interval is +/- 10.23.

times: see stamps.txt

## tables

The block below is the stdout of `python3 forge-combo29/grok/052/report_tables.py`.

```
step	status	evidence	result
STEP 1	done	SEAT.txt	seat 052, idea 2, model Grok 4.7, 2026-11-20T07:53:45Z, token 71694209531
STEP 2	done	HONESTY_B.txt B_O_d12.sum B_G_d12.sum	see those files
STEP 3	done	cmp_off_O.txt cmp_off_G.txt cmp_on_O.txt match_summary.txt san_g100.meta	off O differ 0; off G differ 0; on O differ 200
STEP 4	done	partner_cmp_off_O.txt partner_cmp_on_claimed.txt partner_match_summary.txt partner_seat.txt	off differ 0; on vs claimed differ 0
STEP 5	done	REPORT.md RESULT.txt	this report

--- HONESTY_B.txt ---
command	nodes	expected	match
bench 11	312866	312866	yes
bench 13	862329	862329	yes
bench 16	3024920	3024920	yes
go perft 5	4865609	4865609	yes

--- HONESTY_P.txt ---
command	nodes	expected	match
bench 11	312866	312866	yes
bench 13	862329	862329	yes
bench 16	3024920	3024920	yes
go perft 5	4865609	4865609	yes

--- B_O_d12.sum ---
file B_O_d12.rows
positions 200
sum 9500069
first 1 41311
first 2 24872
first 3 28574

--- B_G_d12.sum ---
file B_G_d12.rows
positions 353
sum 18466239
first 1 37203
first 2 70845
first 3 144383

--- cmp_off_O.txt ---
left B_O_d12.rows 200
right P_off_O.rows 200
compared 200
differ 0
same 200

--- cmp_off_G.txt ---
left B_G_d12.rows 353
right P_off_G.rows 353
compared 353
differ 0
same 353

--- cmp_on_O.txt ---
left B_O_d12.rows 200
right P_on_O.rows 200
compared 200
differ 200
same 0
1 left 41311 right 18591
2 left 24872 right 24876
3 left 28574 right 49848
4 left 27838 right 25690
5 left 18020 right 23076

--- P_on_O.sum ---
file P_on_O.rows
positions 200
sum 10163822
first 1 18591
first 2 24876
first 3 49848

--- apply_check.txt ---
APPLY_CHECK_OK

--- match_summary.txt ---
Results of IdeaS28on vs IdeaS28off (60, 1t, 16MB, openings_OG.epd):
Elo: -0.63 +/- 10.23, nElo: -1.26 +/- 20.48
LOS: 45.21 %, DrawRatio: 65.28 %, PairsRatio: 1.00
Games: 1106, Wins: 341, Losses: 343, Draws: 422, Points: 552.0 (49.91 %)
Ptnml(0-2): [15, 81, 361, 83, 13], WL/DD Ratio: 1.80
--------------------------------------------------
Finished match
Total Time: 00:06:48 (hours:minutes:seconds)

MATCH_EXIT:0

--- PARTNER_HONESTY.txt ---
command	nodes	expected	match
bench 11	312866	312866	yes
bench 13	862329	862329	yes
bench 16	3024920	3024920	yes
go perft 5	4865609	4865609	yes

--- partner_cmp_off_O.txt ---
left B_O_d12.rows 200
right partner_off_O.rows 200
compared 200
differ 0
same 200

--- partner_cmp_on_claimed.txt ---
rows 200 claimed 200
compared 200
differ 0
same 200

--- partner_on_O.sum ---
file partner_on_O.rows
positions 200
sum 10100354
first 1 19410
first 2 23996
first 3 57416

--- partner_match_summary.txt ---
Results of IdeaS28on vs IdeaS28off (60, 1t, 16MB, set_R.epd):
Elo: -9.85 +/- 9.91, nElo: -27.65 +/- 27.80
LOS: 2.56 %, DrawRatio: 83.33 %, PairsRatio: 0.56
Games: 600, Wins: 261, Losses: 278, Draws: 61, Points: 291.5 (48.58 %)
Ptnml(0-2): [6, 26, 250, 15, 3], WL/DD Ratio: 24.00
--------------------------------------------------
Finished match
Total Time: 00:03:09 (hours:minutes:seconds)

MATCH_EXIT:0

--- san_g100.meta ---
exe=/tmp/forge-asan/forge
sha256=5ab0e4ada87fc0987f91bb34fabc16fa7dad008f8c8bd0eccbec13ee27e89dae
id_name=Chess Engine Forge 6.4.24 candidate
nm_asan=35
options_sent:
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name Threads value 1
setoption name Hash value 16
setoption name IdeaS28 value true
depth=10
positions_requested=100
positions_finished=100
crashed=no
sanitizer_lines=0
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1

--- san_canary.meta ---
exe=/tmp/scratch-asan/forge
sha256=39ff73429cd9c98f5906ea2938e13d427a54c86e98ce2558d1359a5f0d07a744
id_name=Chess Engine Forge 6.4.24 candidate
nm_asan=35
options_sent:
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name Threads value 1
setoption name Hash value 16
setoption name IdeaS28 value true
depth=1
positions_requested=1
positions_finished=0
crashed=yes
sanitizer_lines=1
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1

--- prediction.txt ---
seat 052 idea 2 id S28 option IdeaS28
O depth-12 sum with IdeaS28 true, S14, Threads 1, Hash 16: 9350000
proved wrong if that sum is below 8500000 or above 10500000, or if it equals the plain sum 9500069
test-match Elo of IdeaS28 true versus false, 1106 games, 20000 nodes: +3
proved wrong if that Elo point estimate is below -20 or above +25

--- stamps.txt ---
2026-11-20T07:54:23Z STEP 1
2026-11-20T08:03:03Z STEP 2
2026-11-20T08:16:35Z STEP 3
2026-11-20T09:16:29Z STEP 4
2026-11-20T09:16:29Z STEP 5

--- IdeaS28 uci line ---
option name IdeaS28 type check default false

--- canary sanitizer line ---
/tmp/scratch-engine/src/uci.cpp:46:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
```

## git status --short

```
 M forge-combo29/grok/052/stamps.txt
?? forge-combo29/grok/052/PARTNER_HONESTY.txt
?? forge-combo29/grok/052/PARTNER_HONESTY_bench11.meta
?? forge-combo29/grok/052/PARTNER_HONESTY_bench11.txt
?? forge-combo29/grok/052/PARTNER_HONESTY_bench13.meta
?? forge-combo29/grok/052/PARTNER_HONESTY_bench13.txt
?? forge-combo29/grok/052/PARTNER_HONESTY_bench16.meta
?? forge-combo29/grok/052/PARTNER_HONESTY_bench16.txt
?? forge-combo29/grok/052/PARTNER_HONESTY_perft5.meta
?? forge-combo29/grok/052/PARTNER_HONESTY_perft5.txt
?? forge-combo29/grok/052/REPORT.md
?? forge-combo29/grok/052/RESULT.txt
?? forge-combo29/grok/052/apply_check.txt
?? forge-combo29/grok/052/cmp_claimed.py
?? forge-combo29/grok/052/partner.patch.txt
?? forge-combo29/grok/052/partner_claimed_on.nodes.txt
?? forge-combo29/grok/052/partner_cmp_off_O.txt
?? forge-combo29/grok/052/partner_cmp_on_claimed.txt
?? forge-combo29/grok/052/partner_match.pgn
?? forge-combo29/grok/052/partner_match.txt
?? forge-combo29/grok/052/partner_match_summary.txt
?? forge-combo29/grok/052/partner_off_O.meta
?? forge-combo29/grok/052/partner_off_O.rows
?? forge-combo29/grok/052/partner_off_O.txt
?? forge-combo29/grok/052/partner_on_O.meta
?? forge-combo29/grok/052/partner_on_O.rows
?? forge-combo29/grok/052/partner_on_O.sum
?? forge-combo29/grok/052/partner_on_O.txt
?? forge-combo29/grok/052/partner_seat.txt
?? forge-combo29/grok/052/report_tables.out
?? forge-combo29/grok/052/report_tables.py
?? forge-combo29/grok/052/run_partner_rest.sh
```

## ls -la

```
total 5104
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:02 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      88 Nov 20 08:02 B_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  549709 Nov 20 08:02 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:02 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      86 Nov 20 08:02 B_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  308927 Nov 20 08:02 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     797 Nov 20 09:10 cmp_claimed.py
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 08:04 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 08:04 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:04 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:03 cmp_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1425 Nov 20 08:05 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     267 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     267 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     269 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3321 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    3207 Nov 20 08:03 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu     267 Nov 20 08:03 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5047 Nov 20 08:03 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     267 Nov 20 08:03 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5047 Nov 20 08:03 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     269 Nov 20 08:03 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5049 Nov 20 08:03 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 08:03 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5260 Nov 20 08:03 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   11477 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1275 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  139624 Nov 20 08:15 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 1059086 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     276 Nov 20 08:16 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     414 Nov 20 08:16 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:06 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    2494 Nov 20 09:10 partner_claimed_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu      82 Nov 20 09:11 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 09:11 partner_cmp_on_claimed.txt
-rw-r--r-- 1 ubuntu ubuntu     240 Nov 20 09:11 PARTNER_HONESTY_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5047 Nov 20 09:11 PARTNER_HONESTY_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     240 Nov 20 09:11 PARTNER_HONESTY_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5047 Nov 20 09:11 PARTNER_HONESTY_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     242 Nov 20 09:11 PARTNER_HONESTY_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5049 Nov 20 09:11 PARTNER_HONESTY_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     244 Nov 20 09:11 PARTNER_HONESTY_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5260 Nov 20 09:11 PARTNER_HONESTY_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 09:11 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu  500796 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     404 Nov 20 09:16 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   71518 Nov 20 09:14 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 09:11 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:11 partner_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu  309004 Nov 20 09:11 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 09:11 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 09:11 partner_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 09:11 partner_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu  309159 Nov 20 09:11 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   11755 Nov 20 09:09 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1462 Nov 20 08:09 partner_review.sh
-rw-r--r-- 1 ubuntu ubuntu       4 Nov 20 09:09 partner_seat.txt
-rw-r--r-- 1 ubuntu ubuntu     920 Nov 20 08:04 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:04 P_off_G.rows
-rw-r--r-- 1 ubuntu ubuntu  549757 Nov 20 08:04 P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:03 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:03 P_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu  308892 Nov 20 08:03 P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:04 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15760 Nov 20 08:04 P_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu      86 Nov 20 08:04 P_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu  308802 Nov 20 08:04 P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     343 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   17777 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    5837 Nov 20 09:16 report_tables.out
-rw-r--r-- 1 ubuntu ubuntu    2246 Nov 20 09:16 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1179 Nov 20 08:06 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1731 Nov 20 09:10 run_partner_rest.sh
-rw-r--r-- 1 ubuntu ubuntu     909 Nov 20 08:03 run_proofs.sh
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 08:08 san_canary.err
-rw-r--r-- 1 ubuntu ubuntu    1014 Nov 20 08:08 san_canary.meta
-rw-r--r-- 1 ubuntu ubuntu     358 Nov 20 08:08 san_canary_note.txt
-rw-r--r-- 1 ubuntu ubuntu    6127 Nov 20 08:08 san_canary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 san_g100.err
-rw-r--r-- 1 ubuntu ubuntu    1016 Nov 20 08:08 san_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  131823 Nov 20 08:08 san_g100.txt
-rw-r--r-- 1 ubuntu ubuntu    6983 Nov 20 08:06 san_run.py
-rw-r--r-- 1 ubuntu ubuntu    6401 Nov 20 08:01 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      74 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu   19610 Nov 20 08:08 set_R.epd
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     414 Nov 20 08:02 sum_rows.py
```
