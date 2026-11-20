# Seat 026, idea 26, S36

Idea S36 reduces later quiet moves at the root by one ply less after an aspiration fail-low and one ply more after a fail-high, only on the re-search, then clears the shift.
I built check option IdeaS36, default false, and spins IdeaS36_FailLow and IdeaS36_FailHigh, default 1, range 0 to 8.
Captures are not shifted. The engine already skips reduction for the first two root moves, so the shift sits inside that existing reduction, and a negative reduction is clamped to 0 so the shift cannot extend.

EXISTS: no. search.cpp already has AspCappedReopen and AspArmLate, and those change the window. Nothing there shifts root quiet reductions on the re-search. See DESIGN.txt.

Honesty, no setoption, exe B and exe P, from make_table.py reading the raw files: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

## Steps

| step | status | evidence | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 026, idea 26, branch for-fable-and-opus/grok-026 |
| 2 two builds and known sums | done | HONESTY_B.txt, sum_B_O.txt, sum_B_G.txt | pins match; O depth 12 sum 9500069, first three 41311 / 24872 / 28574; G depth 12 sum 18466239 |
| 3 idea | done | idea.patch.txt, apply_check.txt, compare_off_O.txt, compare_off_G.txt, compare_on_O.txt, sum_P_on_O.txt, uci_options_p.txt, asan_summary.txt, match_og.txt | off identical; on differs 166 of 200; sum 9607737; sanitizer clean with a live fault on the scratch build; match 1106 games, Elo 0.94 +/- 10.03 |
| 4 partner 076 | done | partner076_apply.txt, partner076_bench11.txt, partner076_off_vs_B.txt, partner076_on_vs_claim.txt, partner076_on_vs_B.txt, partner076_match.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

The numbers in the proof sections are the output of make_table.py, sum_rows.py, and compare_rows.py on the raw files.

## Proofs

(1) Honesty on exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Same on exe B. Raw files honesty_p_bench11.txt, honesty_p_bench13.txt, honesty_p_bench16.txt, honesty_p_perft5.txt and the B twins.

(2) S14 and IdeaS36 false. O depth 12: differ 0 of 200 against exe B (compare_off_O.txt). G depth 12: differ 0 of 353 (compare_off_G.txt).

(3) S14 and IdeaS36 true, FailLow 1, FailHigh 1. O depth 12 sum 9607737, first three 46657 / 25057 / 36953 (sum_P_on_O.txt). differ 166 of 200 against exe B (compare_on_O.txt). The code runs.

(4) uci lists the new options at their defaults (uci_options_p.txt, taken from HONESTY_P.txt): IdeaS36 check default false, IdeaS36_FailLow spin default 1 min 0 max 8, IdeaS36_FailHigh spin default 1 min 0 max 8.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS36 true, first 100 of G at depth 10: 0 sanitizer lines, and the .meta records asan_symbols 35 (asan_summary.txt, asan_G100_d10.txt.meta). A scratch copy with one heap read past the end of a four-int array, only on the FEN 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1, built the same way and run through uci_harness.py, reported AddressSanitizer heap-buffer-overflow and a runtime error (asan_bug_special.txt, 3 matching lines). The first special FEN I tried, bare kings, never enters search because the engine calls it insufficient material, so the probe uses a king-and-pawn FEN that does search.

git apply --check of idea.patch.txt on a fresh worktree of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0 (apply_check.txt).

## Match

exe P with IdeaS36 true against exe P with IdeaS36 false. S14, Threads 1, Hash 16, 20000 nodes, openings OG.epd (O then G, 553 positions), both colours, 1106 games, concurrency 3. Final block of match_og.txt:

```
Results of s36on vs s36off (20000 nodes, 1t, 16MB, OG.epd):
Elo: 0.94 +/- 10.03, nElo: 1.93 +/- 20.48
LOS: 57.31 %, DrawRatio: 65.64 %, PairsRatio: 1.00
Games: 1106, Wins: 333, Losses: 330, Draws: 443, Points: 554.5 (50.14 %)
Ptnml(0-2): [11, 84, 363, 81, 14], WL/DD Ratio: 1.61
```

The point Elo is inside the range written in prediction.txt before any measurement of exe P (predicted +3, wrong below -35 or above +45). The O sum 9607737 is inside the predicted band 8200000 to 10200000. The guess that the sum would fall below the baseline 9500069 was wrong; the measured sum is higher. prediction.txt was not edited.

## Partner

Partner is seat 076, the next seat with this idea. Their branch had idea.patch.txt. I applied it myself on a fresh base worktree. git apply --check exited 0. Their build's honesty numbers are the four pins above (partner076_bench11.txt through partner076_perft5.txt). IdeaS36 false matches exe B on O depth 12, differ 0 of 200 (partner076_off_vs_B.txt). IdeaS36 true matches their own O depth-12 rows, differ 0 of 200 (partner076_on_vs_claim.txt), and differs from exe B in 166 of 200 (partner076_on_vs_B.txt), which is what they claim. Sum 9607737.

A 300-opening match of their switch on R.fens, both colours, 600 games, final block of partner076_match.txt:

```
Results of p076on vs p076off (20000 nodes, 1t, 16MB, R.fens):
Elo: -2.90 +/- 10.21, nElo: -7.88 +/- 27.80
LOS: 28.92 %, DrawRatio: 82.00 %, PairsRatio: 0.86
Games: 600, Wins: 263, Losses: 268, Draws: 69, Points: 297.5 (49.58 %)
```

Verdict: CONFIRMS. Their patch and mine implement the same one-ply root quiet shift, and the searches I ran agree with the rows they published.

## Suspicions, not proven

Their published 1106-game Elo, 0.94 +/- 10.03, and the Ptnml line match my match_og.txt exactly. Their patch produces the same O depth-12 nodes as mine, and both matches used OG.epd at 20000 nodes with one thread, so the same games are what a deterministic engine would play. I did not diff the PGN files move by move.

## What I did not do

I did not re-run their sanitizer build. I did not replay their 1106-game match; step 4 asks for 600 games on R, and that is the match I played. I did not try FailLow or FailHigh at any value other than 1. I did not run more than one thread. No FABLE_TO_grok file was on the handoff branch when I fetched it (at step 1, and again at 2026-11-20T08:44:39Z, 2026-11-20T08:51:05Z, and 2026-11-20T08:52:17Z).

## What I am not sure about

The engine withholds reduction from the first two root moves. The idea text says to leave the first root move alone. I did not add a reduction for the second root move, and neither did seat 076. A reading that shifts that second move on a fail-high was not tested. The match interval is about +/- 10 Elo, so 0.94 is not a measured gain.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/026/stamps.txt
?? forge-combo29/grok/026/REPORT.md
?? forge-combo29/grok/026/RESULT.txt
?? forge-combo29/grok/026/make_table.py
?? forge-combo29/grok/026/partner076.patch.txt
?? forge-combo29/grok/026/partner076_O_on.rows
?? forge-combo29/grok/026/partner076_apply.txt
?? forge-combo29/grok/026/partner076_bench11.txt
?? forge-combo29/grok/026/partner076_bench11.txt.meta
?? forge-combo29/grok/026/partner076_bench13.txt
?? forge-combo29/grok/026/partner076_bench13.txt.meta
?? forge-combo29/grok/026/partner076_bench16.txt
?? forge-combo29/grok/026/partner076_bench16.txt.meta
?? forge-combo29/grok/026/partner076_match.config.json
?? forge-combo29/grok/026/partner076_match.pgn
?? forge-combo29/grok/026/partner076_match.txt
?? forge-combo29/grok/026/partner076_off_O_d12.txt
?? forge-combo29/grok/026/partner076_off_O_d12.txt.meta
?? forge-combo29/grok/026/partner076_off_O_d12.txt.rows
?? forge-combo29/grok/026/partner076_off_vs_B.txt
?? forge-combo29/grok/026/partner076_on_O_d12.txt
?? forge-combo29/grok/026/partner076_on_O_d12.txt.meta
?? forge-combo29/grok/026/partner076_on_O_d12.txt.rows
?? forge-combo29/grok/026/partner076_on_sum.txt
?? forge-combo29/grok/026/partner076_on_vs_B.txt
?? forge-combo29/grok/026/partner076_on_vs_claim.txt
?? forge-combo29/grok/026/partner076_perft5.txt
?? forge-combo29/grok/026/partner076_perft5.txt.meta
?? forge-combo29/grok/026/partner_plan.txt
?? forge-combo29/grok/026/run_partner076_match.sh
```

## ls -la

```
total 9936
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:52 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:11 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   11027 Nov 20 08:10 asan_bug_special.txt
-rw-r--r-- 1 ubuntu ubuntu    1017 Nov 20 08:10 asan_bug_special.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 asan_bug_special.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  119011 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    1090 Nov 20 08:06 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    2101 Nov 20 08:06 asan_G100_d10.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     161 Nov 20 08:11 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu  508242 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:03 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 08:03 B_G_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  282084 Nov 20 08:02 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     971 Nov 20 08:02 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 08:02 B_O_d12.txt.rows
-rwxr-xr-x 1 ubuntu ubuntu     839 Nov 20 08:00 collect_honesty_b.py
-rwxr-xr-x 1 ubuntu ubuntu     814 Nov 20 08:02 collect_honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:06 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:06 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:06 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     951 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1108 Nov 20 08:11 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:00 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:00 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:00 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:00 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:00 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:00 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   20384 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    5160 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:02 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5160 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:02 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5162 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:02 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5373 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:02 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   21048 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7473 Nov 20 08:01 idea.patch.txt
-rwxr-xr-x 1 ubuntu ubuntu    1701 Nov 20 08:02 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    2118 Nov 20 08:51 make_table.py
-rw-r--r-- 1 ubuntu ubuntu    7054 Nov 20 08:14 match_og.config.json
-rw-r--r-- 1 ubuntu ubuntu 4736181 Nov 20 08:14 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  138387 Nov 20 08:14 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu   11386 Nov 20 08:06 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     637 Nov 20 08:06 match_smoke.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:46 partner076_apply.txt
-rw-r--r-- 1 ubuntu ubuntu    5160 Nov 20 08:46 partner076_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:46 partner076_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5160 Nov 20 08:46 partner076_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:46 partner076_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5162 Nov 20 08:46 partner076_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:46 partner076_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    7046 Nov 20 08:50 partner076_match.config.json
-rw-r--r-- 1 ubuntu ubuntu 2069903 Nov 20 08:50 partner076_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   73124 Nov 20 08:50 partner076_match.txt
-rw-r--r-- 1 ubuntu ubuntu  281874 Nov 20 08:46 partner076_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1021 Nov 20 08:46 partner076_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 08:46 partner076_off_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:47 partner076_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu  282248 Nov 20 08:46 partner076_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1098 Nov 20 08:46 partner076_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4189 Nov 20 08:46 partner076_on_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     155 Nov 20 08:47 partner076_on_sum.txt
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:47 partner076_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     150 Nov 20 08:47 partner076_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu    4189 Nov 20 08:45 partner076_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu    7364 Nov 20 08:45 partner076.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    5373 Nov 20 08:46 partner076_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 08:46 partner076_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     364 Nov 20 08:15 partner_plan.txt
-rw-r--r-- 1 ubuntu ubuntu  508238 Nov 20 08:04 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1006 Nov 20 08:04 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 08:04 P_off_G_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  282116 Nov 20 08:04 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1010 Nov 20 08:04 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 08:04 P_off_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  282685 Nov 20 08:04 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1087 Nov 20 08:04 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4189 Nov 20 08:04 P_on_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     918 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    6662 Nov 20 08:52 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:52 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19374 Nov 20 08:02 R.fens
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:02 R.txt
-rwxr-xr-x 1 ubuntu ubuntu     607 Nov 20 08:00 run_honesty_b.sh
-rwxr-xr-x 1 ubuntu ubuntu     611 Nov 20 08:02 run_honesty_p.sh
-rwxr-xr-x 1 ubuntu ubuntu    1206 Nov 20 08:06 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1169 Nov 20 08:46 run_partner076_match.sh
-rwxr-xr-x 1 ubuntu ubuntu     387 Nov 20 08:01 run_search.sh
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     289 Nov 20 08:11 show_options.py
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 08:52 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:06 sum_B_G.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 08:06 sum_B_O.txt
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:06 sum_P_on_O.txt
-rwxr-xr-x 1 ubuntu ubuntu     583 Nov 20 08:02 sum_rows.py
-rwxr-xr-x 1 ubuntu ubuntu    9948 Nov 20 08:03 uci_harness.py
-rw-r--r-- 1 ubuntu ubuntu     664 Nov 20 08:11 uci_options_p.txt
```
