# Seat 066, idea 16, S13

IdeaS13 keeps a separate from-to history for a quiet non-pawn move that is followed, with the pawn structure unchanged, by a pawn move whose score rose above the alpha the node started with. That history is added only when those piece moves are ordered, and it can take at most IdeaS13_LmrCap plies off their late-move reduction. It is not added to the evaluation. The check option IdeaS13 defaults to false. The spins are IdeaS13_Window 4, IdeaS13_LmrDivisor 4096, and IdeaS13_LmrCap 1. The reasons are in DESIGN.txt.

EXISTS: no. ThreatHistory in forge-combo29/src/search.cpp is a different quiet history, keyed by a cheaper enemy attacker.

## Honesty

Exe B and exe P, no setoption, from honesty_b.py. Both files say the same thing:

```
bench 11 nodes 312866 expect 312866 OK
bench 13 nodes 862329 expect 862329 OK
bench 16 nodes 3024920 expect 3024920 OK
go perft 5 nodes 4865609 expect 4865609 OK
```

Raw lines are HONESTY_B_bench11.txt, HONESTY_B_bench13.txt, HONESTY_B_bench16.txt, HONESTY_B_perft5.txt, and the same names with HONESTY_P_.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 066, idea 16 |
| 2 builds and honesty | done | HONESTY_B.txt, proofs.txt | bench and perft match; O sum 9500069; G sum 18466239 |
| 3 idea | done | idea.patch.txt, proofs.txt, match_summary.txt | off identical; on differs in 200 of 200; Elo -11.00 +/- 10.44 over 1106 games |
| 4 partner 016 | done | partner_off_vs_B.txt, partner_on_vs_rows.txt, partner_match_summary.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty with no setoption. Exe B and exe P both match the four known node counts. See the block above.

(2) S14, IdeaS13 false. print_proofs.py / table_depth.py:

```
O off vs base
count 200
sum 9500069
first 41311 24872 28574
compared 200
differ 0

G off vs base
count 353
sum 18466239
first 37203 70845 144383
compared 353
differ 0
```

(3) S14, IdeaS13 true, O depth 12:

```
O on vs base
count 200
sum 9656004
first 26526 19210 49901
compared 200
differ 200
```

(4) uci, from HONESTY_P_uci.txt via print_proofs.py:

```
option name IdeaS13 type check default false
option name IdeaS13_Window type spin default 4 min 2 max 12
option name IdeaS13_LmrDivisor type spin default 4096 min 256 max 32768
option name IdeaS13_LmrCap type spin default 1 min 0 max 4
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the idea, IdeaS13 true, first 100 of G at depth 10. asan_G100_d10.meta ends with `asan_symbols 35`. asan_G100_d10.err is empty (0 bytes) and the run logged 100 bestmoves. A scratch copy with one heap read past the end of a 4-int array, on the FEN `8/8/8/8/8/8/8/K6k w - - 0 1`, through the same measure_depth.py runner, wrote asan_bug.err. The first sanitizer line is in asan_bug_line.txt:

```
==6093==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000001080 at pc 0x563b2e59b0cc bp 0x7f81e35f4be0 sp 0x7f81e35f4bd0
```

git apply --check of idea.patch.txt on a fresh base printed nothing and exited 0. The same check of the partner patch printed PARTNER_APPLY_CHECK_OK.

## Match

print_match.py on match_on_off.txt:

```
Results of on vs off (20000 nodes, 1t, 16MB, match_OG.epd):
Elo: -11.00 +/- 10.44, nElo: -21.59 +/- 20.48
LOS: 1.94 %, DrawRatio: 61.30 %, PairsRatio: 0.75
Games: 1106, Wins: 317, Losses: 352, Draws: 437, Points: 535.5 (48.42 %)
Ptnml(0-2): [15, 107, 339, 82, 10], WL/DD Ratio: 1.73
--------------------------------------------------
Finished match
```

The point estimate is -11.00, not below -20, so I did not do the extra code pass the brief asks for only in that case. The whole interval (-21.44 to -0.56) is below 0. Fastchess also adjudicated draws and resignations; those rules are in run_match.sh.

## Partner

Seat 116 has no branch. The next seat with this idea is 016. git apply --check succeeded. Their exe matched the four honesty counts (PARTNER.txt). Switch false matched exe B on all 200 O positions (partner_off_vs_B.txt, differ 0, sum 9500069), which is what they report. Switch true matched their P_on_O_d12.rows on all 200 positions (partner_on_vs_rows.txt, differ 0, both sums 9722445), which is the sum in their compare_on_O.txt. Verdict: CONFIRMS.

The required match of their switch on my 300 R openings, print_match.py on partner_match.txt:

```
Results of on vs off (20000 nodes, 1t, 16MB, R_match.epd):
Elo: -0.00 +/- 10.53, nElo: 0.00 +/- 27.80
LOS: 50.00 %, DrawRatio: 84.33 %, PairsRatio: 0.88
Games: 600, Wins: 270, Losses: 270, Draws: 60, Points: 300.0 (50.00 %)
Ptnml(0-2): [5, 20, 253, 14, 8], WL/DD Ratio: 18.46
--------------------------------------------------
Finished match
```

They claimed +4.40 +/- 9.85 on their own 1106-game OG match. I did not replay that match. This R match is a different book, so it does not confirm or refute that Elo.

## Suspicions, not proven

Every one of the 200 openings changed its node count with the switch on. The off path is node-identical, so the search does change only when the option is on. A depth-12 search has many chances to store one of these credits.

The OG match interval lies entirely below 0. The idea text itself says a piece move can be rewarded only because it happened to come before a good pawn move. I did not prove that this is why the Elo is negative.

## What I did NOT do

I did not replay seat 016's 1106-game match. I did not build their patch with a sanitizer. I did not try other values of the three spins. I did not search depths other than the ones named above. There was no FABLE_TO_grok file at step 1 or at minute 60.

## What I am NOT sure about

I counted any pawn move that scored above the alpha at the start of the move loop, including a fail-high. Seat 016 counted only a fail-high. Both are readings of "raised the score". I do not know which one the owner will want.

I am not sure the built-in net is close to the owner's net. This match is only the first look the brief describes.

## Times

times: see stamps.txt

## git status --short

```
A  forge-combo29/grok/066/PARTNER.meta
A  forge-combo29/grok/066/PARTNER.txt
A  forge-combo29/grok/066/PARTNER_bench11.meta
A  forge-combo29/grok/066/PARTNER_bench11.txt
A  forge-combo29/grok/066/PARTNER_bench13.meta
A  forge-combo29/grok/066/PARTNER_bench13.txt
A  forge-combo29/grok/066/PARTNER_bench16.meta
A  forge-combo29/grok/066/PARTNER_bench16.txt
A  forge-combo29/grok/066/PARTNER_perft5.meta
A  forge-combo29/grok/066/PARTNER_perft5.txt
A  forge-combo29/grok/066/PARTNER_uci.meta
A  forge-combo29/grok/066/PARTNER_uci.txt
AM forge-combo29/grok/066/REPORT.md
A  forge-combo29/grok/066/RESULT.txt
A  forge-combo29/grok/066/R_match.epd
A  forge-combo29/grok/066/__pycache__/table_depth.cpython-312.pyc
A  forge-combo29/grok/066/asan_bug_line.txt
A  forge-combo29/grok/066/compare_partner.py
A  forge-combo29/grok/066/partner_O_off.err
A  forge-combo29/grok/066/partner_O_off.meta
A  forge-combo29/grok/066/partner_O_off.sent
A  forge-combo29/grok/066/partner_O_off.txt
A  forge-combo29/grok/066/partner_O_on.err
A  forge-combo29/grok/066/partner_O_on.meta
A  forge-combo29/grok/066/partner_O_on.rows
A  forge-combo29/grok/066/partner_O_on.sent
A  forge-combo29/grok/066/partner_O_on.txt
A  forge-combo29/grok/066/partner_match.pgn
A  forge-combo29/grok/066/partner_match.txt
A  forge-combo29/grok/066/partner_match_summary.txt
A  forge-combo29/grok/066/partner_off_vs_B.txt
A  forge-combo29/grok/066/partner_on_vs_rows.txt
A  forge-combo29/grok/066/run_partner_match.sh
M  forge-combo29/grok/066/stamps.txt
?? config.json
```

## ls -la

```
total 9316
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu    5432 Nov 20 08:13 asan_bug.err
-rw-r--r-- 1 ubuntu ubuntu     137 Nov 20 09:16 asan_bug_line.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 asan_G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu     994 Nov 20 08:12 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  103726 Nov 20 08:11 asan_G100_d10.sent
-rw-r--r-- 1 ubuntu ubuntu  134936 Nov 20 08:11 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    1038 Nov 20 09:11 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    1479 Nov 20 08:13 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 G_B_d12.err
-rw-r--r-- 1 ubuntu ubuntu     845 Nov 20 08:08 G_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  300108 Nov 20 08:08 G_B_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  553095 Nov 20 08:08 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:05 G.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 G_Poff_d12.err
-rw-r--r-- 1 ubuntu ubuntu    1001 Nov 20 08:09 G_Poff_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  366472 Nov 20 08:09 G_Poff_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  565275 Nov 20 08:09 G_Poff_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:03 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:03 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:03 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:03 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:03 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2847 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:03 HONESTY_B_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:03 HONESTY_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:09 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:09 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:09 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      62 Nov 20 08:09 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:09 HONESTY_P.meta
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:09 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:09 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 HONESTY_P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 08:09 HONESTY_P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   13055 Nov 20 08:08 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1375 Nov 20 08:11 make_r.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:13 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu 3137998 Nov 20 08:19 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  134234 Nov 20 08:19 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu     349 Nov 20 08:21 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    5917 Nov 20 08:10 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 O_B_d12.err
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:08 O_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  172878 Nov 20 08:08 O_B_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  307614 Nov 20 08:08 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:05 O.fens
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 O_Poff_d12.err
-rw-r--r-- 1 ubuntu ubuntu    1002 Nov 20 08:09 O_Poff_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  210478 Nov 20 08:09 O_Poff_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  314645 Nov 20 08:09 O_Poff_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 O_Pon_d12.err
-rw-r--r-- 1 ubuntu ubuntu    1001 Nov 20 08:09 O_Pon_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  210278 Nov 20 08:09 O_Pon_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  314778 Nov 20 08:09 O_Pon_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:11 PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:11 PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:11 PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu 1102949 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     342 Nov 20 09:16 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   71109 Nov 20 09:14 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 09:11 PARTNER.meta
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:11 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      72 Nov 20 09:11 partner_on_vs_rows.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_O_off.err
-rw-r--r-- 1 ubuntu ubuntu     964 Nov 20 09:11 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu  202278 Nov 20 09:11 partner_O_off.sent
-rw-r--r-- 1 ubuntu ubuntu  312734 Nov 20 09:11 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_O_on.err
-rw-r--r-- 1 ubuntu ubuntu     963 Nov 20 09:11 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 09:11 partner_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu  202078 Nov 20 09:11 partner_O_on.sent
-rw-r--r-- 1 ubuntu ubuntu  312891 Nov 20 09:11 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:11 PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 09:11 PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 09:11 PARTNER_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5115 Nov 20 09:11 PARTNER_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     427 Nov 20 08:21 print_match.py
-rw-r--r-- 1 ubuntu ubuntu    1043 Nov 20 08:13 print_proofs.py
-rw-r--r-- 1 ubuntu ubuntu     616 Nov 20 08:13 proofs.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:11 __pycache__
-rw-r--r-- 1 ubuntu ubuntu    7655 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19620 Nov 20 08:11 R.fens
-rw-r--r-- 1 ubuntu ubuntu   19561 Nov 20 09:12 R_match.epd
-rwxr-xr-x 1 ubuntu ubuntu    1464 Nov 20 08:12 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1409 Nov 20 09:11 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1800 Nov 20 08:05 table_depth.py
```
