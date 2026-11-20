# Seat 032, idea 32, IdeaA1

IdeaA1 turns the quiet late-move-reduction history term from an integer division into a fraction of a ply, in units of 1/1024 ply.
The plain term is `history / LmrHistoryDivisor`, clamped to ±2, and under S14 that quotient is 0 for every history from -5642 to 5642.
With the switch on, that quotient is kept in 1/1024 ply and rounded half toward zero, so a history past 2821 changes the reduction by one ply, still capped at ±2. `IdeaA1_Scale` defaults to 1024 and `IdeaA1_Clamp` defaults to 2. The check defaults off, and the off path is the original division.

EXISTS: no. The plain engine still does the integer division in `forge-combo29/src/search.cpp` (`r -= clamp(history / LmrHistoryDivisor, -2, 2)`). It does not keep a fractional ply.

## Honesty

exe B and exe P, no setoption, one fresh process per line:

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

Both matched. Files: `HONESTY_B.txt`, `HONESTY_P.txt`.

## Step table

Pasted output of `report_table.py`, which reads the files named in the evidence column:

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 032, idea 32, model Grok 4.7, 2026-11-20T07:52:48Z, token 294932824030963
2 honesty B | done | HONESTY_B.txt | bench 11/13/16 and perft 5 match
2 O and G sums | done | B_O_d12.sum B_G_d12.sum | O 9500069 G 18466239
3 patch applies | done | apply_check.txt idea.patch.txt | APPLY_CHECK_OK
3 proof off | done | compare_off_O.txt compare_off_G.txt | O differ 0, G differ 0
3 proof on | done | compare_on_O.txt | differ 200 sum_b 10279733
3 uci options | done | uci_options.meta | IdeaA1 false, Scale 1024, Clamp 2
3 sanitizer | done | ASAN_G100.meta ASAN_BUG.txt | nm 35, clean run 0 lines, bug run reports heap-buffer-overflow
3 match | done | match_og.log | Elo 1.26 +/- 10.31, 1106 games
4 partner | done | partner_on_vs_theirs.txt partner_match.log | rows differ 0, R match 600 games, Elo 0.58 +/- 12.18
5 report | done | RESULT.txt REPORT.md | this file
```

## Proofs

(1) exe P, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

(2) S14 and IdeaA1 false. O depth 12: 200 of 200 equal to exe B, sum 9500069, first three 41311 24872 28574. G depth 12: 353 of 353 equal to exe B, sum 18466239.

(3) S14 and IdeaA1 true. O depth 12: 200 of 200 differ from exe B. Sum 10279733. First three 42893 29118 29414.

(4) `uci` lists `IdeaA1` check default false, `IdeaA1_Scale` spin default 1024 min 2 max 8192, `IdeaA1_Clamp` spin default 2 min 0 max 8.

(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaA1 true, first 100 of G at depth 10: `nm -C` count of `__asan_` is 35, and the raw log has 0 sanitizer lines. A scratch copy with one read past the end of a 4-int heap array, on the FEN `8/8/8/8/8/8/8/K6k w - - 0 1`, built the same way and run through `depth_set.py`, reports `AddressSanitizer: heap-buffer-overflow`.

`git apply --check` of `idea.patch.txt` on a fresh copy of `6b98f2170a3210e71beed04bbd2553972c253ed7` printed `APPLY_CHECK_OK`.

## Match

exe P with IdeaA1 true against exe P with IdeaA1 false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. Concurrency 3. Pasted last block of `match_og.log` via `match_final.py`:

```
Results of A1on vs A1off (20000 nodes, 1t, 16MB, OG.epd):
Elo: 1.26 +/- 10.31, nElo: 2.50 +/- 20.48
LOS: 59.45 %, DrawRatio: 63.47 %, PairsRatio: 1.04
Games: 1106, Wins: 338, Losses: 334, Draws: 434, Points: 555.0 (50.18 %)
Ptnml(0-2): [13, 86, 351, 90, 13], WL/DD Ratio: 1.72
--------------------------------------------------
```

The interval includes 0 and the point is above -20, so I did not go back to change the code.

## Partner

Partner is seat 082 (same idea, the next seat after 032). Verdict: CONFIRMS.

Their patch applies on a fresh base (`partner_apply.txt`). Honesty numbers match. IdeaA1 false: 200 of 200 O depth-12 rows equal exe B. IdeaA1 true: 200 of 200 rows equal their `P_on_O_d12.rows`, sum 9632936, and 200 of 200 differ from exe B, which is what they report. Their built binary sha256 `4bf38c65bbf26253b58dd7814f8365d6d50db30370599c2406eaa6dccb9f4c66` is the sha256 I got from the same patch. My 300 R openings, both colours, 600 games, their switch:

```
Results of P082on vs P082off (20000 nodes, 1t, 16MB, R.fens):
Elo: 0.58 +/- 12.18, nElo: 1.32 +/- 27.80
LOS: 53.71 %, DrawRatio: 75.67 %, PairsRatio: 0.97
Games: 600, Wins: 248, Losses: 247, Draws: 105, Points: 300.5 (50.08 %)
Ptnml(0-2): [6, 31, 227, 28, 8], WL/DD Ratio: 8.87
--------------------------------------------------
```

## Suspicions, not proven

At 100 games the running Elo in `match_og.log` was -38.37. The finished 1106-game Elo is +1.26. That swing is the sample, not a shown bug in the search.

Seat 082 carries the unused fraction into the child instead of rounding it at the node. Their O sum is 9632936 and mine is 10279733. Both change all 200 positions. I do not know which form the owner's net would prefer.

## What I did NOT do

I did not replay seat 082's 1106-game match. I played their switch on my 300 R openings, 600 games.

I opened their branch at 08:54 UTC. Minute 75 was 09:08 UTC. The patch was already on the remote, and the proofs above are from that patch.

I did not build `../work` once as a plain engine and again after the patch. `../base` is exe B. `../work` was built with the patch, and IdeaA1 false reproduced exe B's rows.

The partner honesty helper did not send `uci`, so those four meta files say `id_name=see uci`. The node lines are in the raw logs.

## What I am NOT sure about

I copied fastchess's printed `+/- 10.31` into `err`. I did not recompute that interval.

I am not sure half-toward-zero is the fraction the idea should use. Seat 082's carry is also a fractional history term, and it also leaves the off path unchanged.

The prediction was an O sum of 9850000, wrong outside 8500000..11500000, and Elo +6, wrong outside -40..+50. Measured sum 10279733 and Elo +1.26 sit inside those ranges. I did not edit `prediction.txt`.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/032/partner_prove.sh
 M forge-combo29/grok/032/stamps.txt
?? forge-combo29/grok/032/PARTNER_HONESTY.txt
?? forge-combo29/grok/032/PARTNER_off_O.meta
?? forge-combo29/grok/032/PARTNER_off_O.nodes
?? forge-combo29/grok/032/PARTNER_off_O.sum
?? forge-combo29/grok/032/PARTNER_off_O.txt
?? forge-combo29/grok/032/PARTNER_on_O.meta
?? forge-combo29/grok/032/PARTNER_on_O.nodes
?? forge-combo29/grok/032/PARTNER_on_O.sum
?? forge-combo29/grok/032/PARTNER_on_O.txt
?? forge-combo29/grok/032/REPORT.md
?? forge-combo29/grok/032/RESULT.txt
?? forge-combo29/grok/032/config.json
?? forge-combo29/grok/032/partner_P_on_O.rows
?? forge-combo29/grok/032/partner_apply.txt
?? forge-combo29/grok/032/partner_honesty_bench_11.meta
?? forge-combo29/grok/032/partner_honesty_bench_11.txt
?? forge-combo29/grok/032/partner_honesty_bench_13.meta
?? forge-combo29/grok/032/partner_honesty_bench_13.txt
?? forge-combo29/grok/032/partner_honesty_bench_16.meta
?? forge-combo29/grok/032/partner_honesty_bench_16.txt
?? forge-combo29/grok/032/partner_honesty_go_perft_5.meta
?? forge-combo29/grok/032/partner_honesty_go_perft_5.txt
?? forge-combo29/grok/032/partner_idea.patch.txt
?? forge-combo29/grok/032/partner_match.log
?? forge-combo29/grok/032/partner_match.pgn
?? forge-combo29/grok/032/partner_match.sh
?? forge-combo29/grok/032/partner_off_vs_B.txt
?? forge-combo29/grok/032/partner_on_vs_B.txt
?? forge-combo29/grok/032/partner_on_vs_theirs.txt
?? forge-combo29/grok/032/partner_vs_rows.py
?? forge-combo29/grok/032/report_numbers.py
?? forge-combo29/grok/032/report_table.py
?? forge-combo29/grok/032/report_table.txt
```

## ls -la

```
total 10164
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:00 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:06 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     934 Nov 20 08:05 ASAN_BUG.meta
-rw-r--r-- 1 ubuntu ubuntu    5135 Nov 20 08:04 ASAN_BUG.txt
-rw-r--r-- 1 ubuntu ubuntu     959 Nov 20 08:04 ASAN_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    1776 Nov 20 08:04 ASAN_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:04 ASAN_G100.sum
-rw-r--r-- 1 ubuntu ubuntu  126676 Nov 20 08:04 ASAN_G100.txt
-rw-r--r-- 1 ubuntu ubuntu     933 Nov 20 08:04 asan_meta.py
-rw-r--r-- 1 ubuntu ubuntu     825 Nov 20 07:59 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    6609 Nov 20 07:59 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 07:59 B_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  544689 Nov 20 07:59 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     829 Nov 20 07:59 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3696 Nov 20 07:59 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 07:59 B_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  304059 Nov 20 07:59 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:04 bug.fen
-rw-r--r-- 1 ubuntu ubuntu    1240 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:06 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 08:06 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 08:06 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    7090 Nov 20 08:59 config.json
-rw-r--r-- 1 ubuntu ubuntu    1246 Nov 20 08:06 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    6509 Nov 20 07:59 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:04 G100.epd
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:58 honesty_b_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:58 honesty_b_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 07:58 honesty_b_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 honesty_b_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    3256 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     335 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:01 honesty_p_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_p_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:01 honesty_p_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_p_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 08:01 honesty_p_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_p_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:01 honesty_p_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_p_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    3251 Nov 20 08:01 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     335 Nov 20 08:01 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6688 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1406 Nov 20 08:01 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     451 Nov 20 08:14 match_final.py
-rw-r--r-- 1 ubuntu ubuntu  117021 Nov 20 08:12 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 4687816 Nov 20 08:12 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    1255 Nov 20 08:05 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:56 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:55 partner_honesty_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:55 partner_honesty_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:55 partner_honesty_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:55 partner_honesty_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:55 partner_honesty_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:55 partner_honesty_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:55 partner_honesty_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:55 partner_honesty_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu     290 Nov 20 08:55 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   10838 Nov 20 08:55 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   64037 Nov 20 08:59 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 2275697 Nov 20 08:59 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1115 Nov 20 08:56 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     862 Nov 20 08:55 PARTNER_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    3696 Nov 20 08:55 PARTNER_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:55 PARTNER_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu  304123 Nov 20 08:55 PARTNER_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:55 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 08:55 PARTNER_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    3694 Nov 20 08:55 PARTNER_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:55 PARTNER_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu  304393 Nov 20 08:55 PARTNER_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:55 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     255 Nov 20 08:55 partner_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu    1929 Nov 20 08:55 partner_P_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu    3220 Nov 20 08:55 partner_prove.sh
-rw-r--r-- 1 ubuntu ubuntu    1387 Nov 20 08:55 partner_vs_rows.py
-rw-r--r-- 1 ubuntu ubuntu     859 Nov 20 08:02 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu    6609 Nov 20 08:02 P_off_G.nodes
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:02 P_off_G.sum
-rw-r--r-- 1 ubuntu ubuntu  544812 Nov 20 08:02 P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     863 Nov 20 08:02 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    3696 Nov 20 08:02 P_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:02 P_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu  304102 Nov 20 08:02 P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     862 Nov 20 08:02 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    3697 Nov 20 08:02 P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:02 P_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu  304317 Nov 20 08:02 P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     814 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    7795 Nov 20 09:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1318 Nov 20 08:54 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    2887 Nov 20 09:00 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 09:00 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19711 Nov 20 08:01 R.fens
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     648 Nov 20 08:05 smoke.log
-rw-r--r-- 1 ubuntu ubuntu   10441 Nov 20 08:05 smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     229 Nov 20 09:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     400 Nov 20 08:03 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    1889 Nov 20 08:03 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5097 Nov 20 08:03 uci_options.txt
```
