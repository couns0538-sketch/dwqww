# Seat 034, idea 34, IdeaA3

The check extension is given only to a checking move whose static exchange is not losing.
The plain engine already does that, so the patch adds option IdeaA3 (check, default false) and spin IdeaA3_SeeFloor (default 0, today's floor, range -900 to 900).
Switch off keeps the original expression. Switch on uses the spin. At 0 the search is unchanged. At 100 every measured opening changes.

EXISTS: forge-combo29/src/search.cpp:1955
`picker.last_move_see_nonnegative() || board.see_ge(move, 0)` then `extension = 1`. GoodCaptures returns a move only after `see_ge(move, 0)`. CheckExtensionDepth is already a spin (default 2). The floor 0 was not an option. decision.txt.

## Honesty numbers

exe B and exe P, no setoption, one process per line (HONESTY_B.txt, HONESTY_P.txt):

| command | nodes |
| --- | ---: |
| bench 11 | 312866 |
| bench 13 | 862329 |
| bench 16 | 3024920 |
| go perft 5 | 4865609 |

O depth 12 on exe B, S14, Threads 1, Hash 16: sum 9500069, first three 41311 / 24872 / 28574 (sum_B_O.txt). G depth 12: sum 18466239 (sum_B_G.txt).

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 034, idea 34 |
| 2 honesty and base sums | done | HONESTY_B.txt, sum_B_O.txt, sum_B_G.txt | known numbers matched |
| 3a read | done | decision.txt | EXISTS at search.cpp:1955 |
| 3b prediction | done | prediction.txt | 9500069 and Elo 0, committed before measuring P |
| 3c patch | done | idea.patch.txt, apply_check.txt | git apply --check exit 0 on the base tree |
| 3d proofs | done | compare_off_O.txt, compare_on_O.txt, uci_P.txt, asan_G100_d10.meta, asan_scratch.txt | off identical; on at default 0 differ; floor 100 differs 200; sanitizer clean and shown |
| 3e match | done | match_OG.log, match_OG_result.txt | 1106 games, Elo -0.00 +/- 0.00 |
| 4 partner 084 | done | P084_off_vs_B.txt, P084_on_vs_claim.txt, match_P084_result.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) exe P, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. HONESTY_P.txt.

(2) S14, IdeaA3 false. O depth 12: 200 equal, 0 differ (compare_off_O.txt). G depth 12: 353 equal, 0 differ (compare_off_G.txt).

(3) S14, IdeaA3 true, SeeFloor left at 0. O depth 12 sum 9500069, 0 of 200 differ from exe B (compare_on_O.txt, sum_on_O.txt). That is the prediction. It is 0 because the engine already uses floor 0 (why_on_zero.txt). The option does run: IdeaA3 true and IdeaA3_SeeFloor 100 differs in 200 of 200 (compare_on_floor100.txt). First three nodes become 19960 / 17388 / 46301.

(4) uci lists `option name IdeaA3 type check default false` and `option name IdeaA3_SeeFloor type spin default 0 min -900 max 900` (uci_P.txt).

(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaA3 true, first 100 of G at depth 10: no sanitizer line (asan_G100_d10.txt). The .meta has `nm -C` `__asan_` count 35. A scratch copy with one heap read past the end of a 4-int array, only on the FEN in asan_scratch.fen, built the same way and run through depth_run.py, reports `ERROR: AddressSanitizer: heap-buffer-overflow` (asan_scratch.txt).

## Match

exe P, IdeaA3 true against IdeaA3 false, both at SeeFloor 0, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours. fastchess output: match_OG.log, match_OG.pgn.

```
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
LOS: -nan %, DrawRatio: 100.00 %, PairsRatio: -nan
Games: 1106, Wins: 336, Losses: 336, Draws: 434, Points: 553.0 (50.00 %)
Ptnml(0-2): [0, 0, 553, 0, 0], WL/DD Ratio: 1.55
```

From match_result.py on match_OG.log (match_OG_result.txt). The point estimate is 0, inside the predicted range. Wins and losses are equal and every opening pair is balanced, which is self-play of one search. No unknown option, invalid value, or illegal move in the log.

## Partner

Partner is seat 084 (same idea; 134 is not a seat). Tip fetched: 78d12f1b47329462e9e3e777ea37d551b333f051. Their patch adds IdeaA3, IdeaA3_Threshold default 0, IdeaA3_Extension default 1.

On a fresh worktree of 6b98f2170, `git apply --check` exit 0 (partner_apply_check.txt), then apply and a release build. Honesty of that build: 312866, 862329, 3024920, 4865609 (HONESTY_P084.txt). Switch false: O depth 12 equals exe B on 200 of 200 (P084_off_vs_B.txt). Switch true at their defaults: my rows equal their P_on_O.txt on 200 of 200, both sums 9500069 (P084_on_vs_claim.txt). They claim that. Match of their switch, my 300 R openings, both colours, 600 games (match_P084.log): Elo -0.00 +/- 0.00, wins 253, losses 253, draws 94.

Verdict: CONFIRMS.

## Suspicions, not proven

Their on-path calls `see_ge(move, threshold)` and does not use the GoodCaptures shortcut. At threshold 0 the node totals still matched theirs and exe B on these 200 positions. I did not inspect every internal move.

The two OG matches (mine and theirs) both printed 336 wins, 336 losses, 434 draws. Both switches at default search as exe B, and the opening file hash is the same (`ca2f576b…`), so the games are the same self-play. I did not diff the PGNs move by move.

## What I did NOT do

I did not play the 1106-game match at SeeFloor 100. The required match is switch true against switch false, spins at default.
I did not re-run their IdeaA3_Extension=0 measurement (their cmp_on_ext0_O.txt says 200 of 200 differ, sum 8984130).
I did not measure a negative SeeFloor.
No forge-combo29/soak_all/FABLE_TO_grok_<N>.md was on the handoff branch at either fetch. No STOP line.
I did not open a pull request.

## What I am NOT sure about

A negative IdeaA3_SeeFloor should extend some losing checks. I did not measure one, so I have not seen that path move a node count.
I am sure the default-on search matches exe B on O at depth 12. I am not sure it matches on a set other than O and G.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/034/stamps.txt
?? forge-combo29/grok/034/HONESTY_P084.meta
?? forge-combo29/grok/034/HONESTY_P084.txt
?? forge-combo29/grok/034/HONESTY_P084_bench11.meta
?? forge-combo29/grok/034/HONESTY_P084_bench11.txt
?? forge-combo29/grok/034/HONESTY_P084_bench13.meta
?? forge-combo29/grok/034/HONESTY_P084_bench13.txt
?? forge-combo29/grok/034/HONESTY_P084_bench16.meta
?? forge-combo29/grok/034/HONESTY_P084_bench16.txt
?? forge-combo29/grok/034/HONESTY_P084_perft5.meta
?? forge-combo29/grok/034/HONESTY_P084_perft5.txt
?? forge-combo29/grok/034/P084_off_O.meta
?? forge-combo29/grok/034/P084_off_O.txt
?? forge-combo29/grok/034/P084_off_vs_B.txt
?? forge-combo29/grok/034/P084_on_O.meta
?? forge-combo29/grok/034/P084_on_O.txt
?? forge-combo29/grok/034/P084_on_vs_B.txt
?? forge-combo29/grok/034/P084_on_vs_claim.txt
?? forge-combo29/grok/034/REPORT.md
?? forge-combo29/grok/034/RESULT.txt
?? forge-combo29/grok/034/compare_partner.py
?? forge-combo29/grok/034/match_P084.log
?? forge-combo29/grok/034/match_P084.pgn
?? forge-combo29/grok/034/match_P084_result.txt
?? forge-combo29/grok/034/match_p084.sh
?? forge-combo29/grok/034/partner084_P_on_O.txt
?? forge-combo29/grok/034/partner_apply_check.txt
```

## ls -la

```
total 12564
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:52 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:07 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     950 Nov 20 08:06 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  252331 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 asan_scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      17 Nov 20 08:06 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10908 Nov 20 08:06 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    1753 Nov 20 08:02 compare_depth.py
-rw-r--r-- 1 ubuntu ubuntu     156 Nov 20 08:07 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     156 Nov 20 08:07 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     373 Nov 20 08:03 compare_on_floor100.txt
-rw-r--r-- 1 ubuntu ubuntu     155 Nov 20 08:07 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1917 Nov 20 08:46 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    1501 Nov 20 08:01 decision.txt
-rw-r--r-- 1 ubuntu ubuntu    4695 Nov 20 08:00 depth_run.py
-rw-r--r-- 1 ubuntu ubuntu    1380 Nov 20 08:00 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 08:00 G_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  959094 Nov 20 08:00 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:04 G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu     867 Nov 20 08:03 G_P_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  980916 Nov 20 08:03 G_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:58 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:58 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:58 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     282 Nov 20 07:58 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 07:58 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1410 Nov 20 07:58 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     725 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:46 HONESTY_P084_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:46 HONESTY_P084_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:46 HONESTY_P084_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:46 HONESTY_P084_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:46 HONESTY_P084_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:46 HONESTY_P084_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:46 HONESTY_P084.meta
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:46 HONESTY_P084_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:46 HONESTY_P084_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     737 Nov 20 08:46 HONESTY_P084.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:03 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:03 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:03 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:03 HONESTY_P.meta
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:03 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     725 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1348 Nov 20 08:02 honesty_run.sh
-rw-r--r-- 1 ubuntu ubuntu    5342 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1231 Nov 20 08:07 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  108044 Nov 20 08:13 match_OG.log
-rw-r--r-- 1 ubuntu ubuntu 4630176 Nov 20 08:13 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu     379 Nov 20 08:15 match_OG_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1349 Nov 20 08:06 match_on_off.sh
-rw-r--r-- 1 ubuntu ubuntu   53793 Nov 20 08:50 match_P084.log
-rw-r--r-- 1 ubuntu ubuntu 2024190 Nov 20 08:50 match_P084.pgn
-rw-r--r-- 1 ubuntu ubuntu     381 Nov 20 08:52 match_P084_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1322 Nov 20 08:47 match_p084.sh
-rw-r--r-- 1 ubuntu ubuntu     430 Nov 20 08:15 match_result.py
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:00 O_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  540978 Nov 20 08:00 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:03 O_P_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  552954 Nov 20 08:03 O_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:03 O_P_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  552731 Nov 20 08:03 O_P_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:03 O_P_on_floor100_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  565390 Nov 20 08:03 O_P_on_floor100_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:46 P084_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  553082 Nov 20 08:46 P084_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     155 Nov 20 08:46 P084_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:46 P084_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  552842 Nov 20 08:46 P084_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     154 Nov 20 08:46 P084_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:46 P084_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:46 partner084_P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 08:52 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     560 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   20084 Nov 20 08:04 R_300.fens
-rw-r--r-- 1 ubuntu ubuntu    6033 Nov 20 08:52 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:52 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     624 Nov 20 08:06 smoke_match.log
-rw-r--r-- 1 ubuntu ubuntu   37870 Nov 20 08:06 smoke_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:53 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:07 sum_B_G.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:07 sum_B_O.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:07 sum_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    5042 Nov 20 08:03 uci_P.txt
-rw-r--r-- 1 ubuntu ubuntu     678 Nov 20 08:07 why_on_zero.txt
```
