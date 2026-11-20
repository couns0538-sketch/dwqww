# Seat 016, idea 16, S13

IdeaS13 credits the quiet non-pawn move that came before a pawn break.
The option is a check, default false. Two spins: IdeaS13_Lookback default 4, IdeaS13_ReduceDivisor default 1024.
On a pawn fail-high, same-side quiet piece moves 2 and 4 plies back are credited when the pawn key is unchanged. That history orders those piece moves and can take one ply off their reduction. It is not added to the evaluation.

EXISTS: no. ThreatHistory in search.cpp is a different table, keyed by a cheaper enemy attacker. It is not this credit.

## Honesty numbers

Pasted from HONESTY_B.txt and HONESTY_P.txt. No setoption. Both builds:

```
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
```

Exe B also reproduced S14 depth 12: O sum 9500069 (first three nodes 41311, 24872, 28574) and G sum 18466239.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 016, idea 16 |
| 2 honesty and baseline | done | HONESTY_B.txt, B_O_d12.rows, B_G_d12.rows | honesty OK, O 9500069, G 18466239 |
| 3 idea | done | idea.patch.txt, compare_on_O.txt, match_s13.txt | off identical, on differs 200 of 200, Elo 4.40 +/- 9.85 |
| 4 partner 066 | done | partner066_on_vs_claim.txt, partner066_match.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty, no setoption, exe P. Same four node counts as exe B. HONESTY_P.txt.

(2) S14, IdeaS13 false. compare_rows.py of P_off against B:

```
positions 200
equal 200
differ 0
nodes_differ 0
bestmove_differ 0
sum_left 9500069
sum_right 9500069
```

G, same comparison:

```
positions 353
equal 353
differ 0
nodes_differ 0
bestmove_differ 0
sum_left 18466239
sum_right 18466239
```

(3) S14, IdeaS13 true, O depth 12. compare_rows.py against B:

```
positions 200
equal 0
differ 200
nodes_differ 200
bestmove_differ 47
sum_left 9500069
sum_right 9722445
```

Prediction was 10200000, wrong outside 8000000 to 14000000. 9722445 is inside that range.

(4) uci lists the new options. Pasted from uci_options.txt:

```
option name IdeaS13 type check default false
option name IdeaS13_Lookback type spin default 4 min 2 max 12
option name IdeaS13_ReduceDivisor type spin default 1024 min 256 max 16384
```

(5) Sanitizer. asan_G100.meta: nm_asan_symbols 35, sanitizer_lines 0, positions_finished 100 of 100, IdeaS13 true, first 100 of G, depth 10. The same runner on the scratch exe, one heap read past the end of a 4-int array on the FEN `8/8/8/8/8/8/8/K6k w - - 0 1`, reported:

```
/agent/repos/scratch/forge-combo29/src/uci.cpp:48:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
```

git apply --check on a fresh base (6b98f2170), from apply_check.txt: exit 0. The patch matches the work tree diff.

## Match

fastchess, s13on versus s13off, both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G, both colours, 1106 games. Last result block of match_s13.txt:

```
Results of s13on vs s13off (20000 nodes, 1t, 16MB, match_OG.epd):
Elo: 4.40 +/- 9.85, nElo: 9.15 +/- 20.48
LOS: 80.94 %, DrawRatio: 66.73 %, PairsRatio: 1.14
Games: 1106, Wins: 341, Losses: 327, Draws: 438, Points: 560.0 (50.63 %)
Ptnml(0-2): [11, 75, 369, 85, 13], WL/DD Ratio: 1.65
```

Predicted Elo +6, wrong if the point estimate is below -30 or above +40. 4.40 is inside that range. The interval includes 0. It is not below -20 with the whole interval below 0, so I did not go back to hunt for a bug.

## Partner verdict

Partner is seat 066 (idea 16). Seat 116 had no branch. Their patch applies. My rebuild matches the honesty numbers. Switch false matches exe B on O (200 equal) and on G (353 equal). Switch true matches their own O depth-12 rows: 200 equal, sum 9656004, and 200 of 200 differ from exe B, which is what their proofs.txt claims. Their uci line is IdeaS13 default false, Window 4, LmrDivisor 4096, LmrCap 1.

My match of their switch, 300 R openings, both colours, 600 games, from partner066_match.txt:

```
Results of on vs off (20000 nodes, 1t, 16MB, R300.epd):
Elo: -5.21 +/- 8.70, nElo: -16.66 +/- 27.80
LOS: 12.01 %, DrawRatio: 87.33 %, PairsRatio: 0.58
Games: 600, Wins: 274, Losses: 283, Draws: 43, Points: 295.5 (49.25 %)
```

CONFIRMS. Their OG Elo of -11.00 +/- 10.44 is a different book. I did not replay those 1106 games.

## Suspicions, not proven

All 200 opening positions change node count with the switch on. That is a large footprint for a history that is cleared every position. The off path is node-identical, so the extra nodes come from the switch, not from the pawn-key store. I did not prove the credit is the move a deeper search would have wanted.

## What I did NOT do

I did not replay the partner's 1106-game match. I did not build their patch with a sanitizer. I did not run a second match of my own patch on the R book. I did not try Lookback or ReduceDivisor away from the defaults. I did not check the idea's falsify test against a much deeper search.

## What I am NOT sure about

"Raised the score" is implemented as a pawn fail-high. A pawn move that only raises alpha is ignored. The partner credits that case too, and their search also changes. I do not know which reading is the one the note meant. The match Elo interval includes zero, so I do not know the sign on the built-in net.

## Times

times: see stamps.txt

Minute 60: fetched handoff/fable-opus-combo29-all-20261114 again (FETCH_HEAD 8c5536863464d4af8c07b4788883463eb950ab1d). No file named FABLE_TO_grok_N.

## git status --short and ls -la

These two blocks are appended by the shell after this text was written.

```
$ git status --short
 M forge-combo29/grok/016/stamps.txt
?? config.json
?? forge-combo29/grok/016/REPORT.md
?? forge-combo29/grok/016/RESULT.txt
?? forge-combo29/grok/016/make_report.py
?? forge-combo29/grok/016/partner066_HONESTY.txt
?? forge-combo29/grok/016/partner066_apply.txt
?? forge-combo29/grok/016/partner066_claimed_O.rows
?? forge-combo29/grok/016/partner066_honesty_bench_11.meta
?? forge-combo29/grok/016/partner066_honesty_bench_11.txt
?? forge-combo29/grok/016/partner066_honesty_bench_13.meta
?? forge-combo29/grok/016/partner066_honesty_bench_13.txt
?? forge-combo29/grok/016/partner066_honesty_bench_16.meta
?? forge-combo29/grok/016/partner066_honesty_bench_16.txt
?? forge-combo29/grok/016/partner066_honesty_go_perft_5.meta
?? forge-combo29/grok/016/partner066_honesty_go_perft_5.txt
?? forge-combo29/grok/016/partner066_idea.patch.txt
?? forge-combo29/grok/016/partner066_match.pgn
?? forge-combo29/grok/016/partner066_match.txt
?? forge-combo29/grok/016/partner066_off_G.meta
?? forge-combo29/grok/016/partner066_off_G.rows
?? forge-combo29/grok/016/partner066_off_G.txt
?? forge-combo29/grok/016/partner066_off_G_vs_B.txt
?? forge-combo29/grok/016/partner066_off_O.meta
?? forge-combo29/grok/016/partner066_off_O.rows
?? forge-combo29/grok/016/partner066_off_O.txt
?? forge-combo29/grok/016/partner066_off_vs_B.txt
?? forge-combo29/grok/016/partner066_on_O.meta
?? forge-combo29/grok/016/partner066_on_O.rows
?? forge-combo29/grok/016/partner066_on_O.txt
?? forge-combo29/grok/016/partner066_on_vs_B.txt
?? forge-combo29/grok/016/partner066_on_vs_claim.txt
?? forge-combo29/grok/016/run_pair.sh

$ ls -la forge-combo29/grok/016
total 5348
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:13 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu     113 Nov 20 08:29 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1034 Nov 20 08:20 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    1177 Nov 20 08:20 asan_G100.runlog
-rw-r--r-- 1 ubuntu ubuntu  118904 Nov 20 08:20 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu    7064 Nov 20 08:20 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu    1031 Nov 20 08:20 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    6180 Nov 20 08:20 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     987 Nov 20 08:00 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:00 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  507965 Nov 20 08:00 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     995 Nov 20 07:59 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 07:59 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  281980 Nov 20 07:59 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     103 Nov 20 08:03 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     101 Nov 20 08:03 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:03 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1329 Nov 20 08:03 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    5372 Nov 20 08:02 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu    1521 Nov 20 08:21 design.txt
-rw-r--r-- 1 ubuntu ubuntu    1344 Nov 20 08:22 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:06 G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:58 honesty_B_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 honesty_B_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:58 honesty_B_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 honesty_B_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:58 honesty_B_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:58 honesty_B_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 07:58 honesty_B_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:58 honesty_B_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    3177 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     280 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:03 honesty_P_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    5176 Nov 20 08:03 honesty_P_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:03 honesty_P_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    5176 Nov 20 08:03 honesty_P_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:03 honesty_P_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    5178 Nov 20 08:03 honesty_P_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:03 honesty_P_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5389 Nov 20 08:03 honesty_P_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu     280 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   14270 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1768 Nov 20 08:30 make_report.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:21 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu 1069619 Nov 20 08:28 match_s13.pgn
-rw-r--r-- 1 ubuntu ubuntu  138573 Nov 20 08:28 match_s13.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 09:10 partner066_apply.txt
-rw-r--r-- 1 ubuntu ubuntu   15758 Nov 20 09:09 partner066_claimed_O.rows
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 partner066_honesty_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    5230 Nov 20 09:09 partner066_honesty_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 partner066_honesty_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    5230 Nov 20 09:09 partner066_honesty_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 partner066_honesty_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    5232 Nov 20 09:09 partner066_honesty_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:09 partner066_honesty_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5443 Nov 20 09:09 partner066_honesty_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu     283 Nov 20 09:09 partner066_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   13055 Nov 20 09:08 partner066_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  467743 Nov 20 09:12 partner066_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   62873 Nov 20 09:12 partner066_match.txt
-rw-r--r-- 1 ubuntu ubuntu     995 Nov 20 09:10 partner066_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 09:10 partner066_off_G.rows
-rw-r--r-- 1 ubuntu ubuntu  507790 Nov 20 09:10 partner066_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     103 Nov 20 09:10 partner066_off_G_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 09:09 partner066_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:09 partner066_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu  281942 Nov 20 09:09 partner066_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     101 Nov 20 09:09 partner066_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1180 Nov 20 09:09 partner066_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15758 Nov 20 09:09 partner066_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu  282030 Nov 20 09:09 partner066_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 09:09 partner066_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     101 Nov 20 09:09 partner066_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu     989 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:02 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  508482 Nov 20 08:02 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     994 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:02 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  282178 Nov 20 08:02 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1034 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:02 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  282399 Nov 20 08:02 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     957 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19425 Nov 20 08:22 R300.epd
-rw-r--r-- 1 ubuntu ubuntu    7436 Nov 20 09:14 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:13 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1414 Nov 20 08:21 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1109 Nov 20 08:29 run_pair.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:04 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    1067 Nov 20 08:04 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5115 Nov 20 08:04 uci_options.txt
```
