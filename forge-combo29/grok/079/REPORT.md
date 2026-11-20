# Seat 079, idea 29, B10

IdeaB10 is depth-normalised effort repayment, a check option that defaults to false.
When it is on, a finished node remembers a move whose nodes divided by the depth it was actually given clearly beats the next move, including when the node failed low.
On the next visit that move is given back withheld late-move reduction, in proportion to the rate gap, and the repaid plies from the root stop at IdeaB10_Cap (default 3). Spins: IdeaB10_Ratio 150, IdeaB10_MinNodes 32, IdeaB10_Step 100.

EXISTS no. The engine already has HindsightDepth and a root node-share clock term. Neither stores a depth-normalised effort mark or pays withheld reduction back on a later visit.

Honesty, no setoption, both exe B and exe P (`HONESTY_B.txt`, `HONESTY_P.txt`):

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 079, idea 29, Grok 4.7 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 2 O and G depth 12 | done | B_O_d12.nodes, B_G_d12.nodes, tables.txt | O sum 9500069, first three 41311 24872 28574; G sum 18466239 |
| 3 prediction | done | prediction.txt | O sum 10200000, wrong outside 9600000..12500000; Elo +6, wrong outside -30..+50. Written before any exe P measurement |
| 3 patch | done | idea.patch.txt, my_apply_check.txt | `git apply --check` printed APPLY_CHECK_OK |
| 3 proofs | done | tables.txt | off identical; on differs; options listed; sanitizer clean with a positive control |
| 3 match | done | match.log, match.pgn | Elo 1.57 +/- 10.68, 1106 games |
| 4 partner 029 | done | partner_tables.txt, partner_match.log | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Exe P, no setoption, same four counts as exe B. `HONESTY_P.txt`.

Proof (2). S14, Threads 1, Hash 16, IdeaB10 false. O depth 12 differ 0 of 200, sum 9500069. G depth 12 differ 0 of 353, sum 18466239. `tables.txt`.

Proof (3). S14 and IdeaB10 true. O depth 12 sum 9836323, differ 199 of 200 from exe B. Inside the prediction range. `tables.txt`, `P_on_O_d12.nodes`.

Proof (4). `uci` lists, from `tables.txt` / `uci_p.txt`:

```
option name IdeaB10 type check default false
option name IdeaB10_Ratio type spin default 150 min 100 max 1000
option name IdeaB10_MinNodes type spin default 32 min 1 max 100000
option name IdeaB10_Step type spin default 100 min 1 max 1000
option name IdeaB10_Cap type spin default 3 min 0 max 16
```

Proof (5). AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaB10 true, first 100 of G at depth 10. `nm -C` count of `__asan_` is 35 in `asan_G100_d10.meta`. Sanitizer lines in `asan_G100_d10.raw.txt`: 0. The same runner on a scratch copy with one deliberate heap read past the end, special FEN `asan_special.fen`, reported `SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/bad-src/src/uci.cpp:46 in apply_position` in `asan_bad.partial.txt`.

Match. Exe P with IdeaB10 true against exe P with IdeaB10 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games. From `match.log`:

```
Elo: 1.57 +/- 10.68, nElo: 3.01 +/- 20.48
LOS: 61.34 %, DrawRatio: 60.22 %, PairsRatio: 1.06
Games: 1106, Wins: 342, Losses: 337, Draws: 427, Points: 555.5 (50.23 %)
```

The point is inside the prediction. It is not below -20 with the whole interval below 0, so the code was not re-opened for a bug hunt. `match.pgn` has 1106 games.

Partner. Seat 029 is the next seat with this idea that has a branch. `partner029_idea.patch.txt` applied on a fresh base: `partner_apply_check.txt` says APPLY_CHECK_OK and APPLY_OK. Their engine's honesty counts match. Switch false versus exe B's O depth-12 rows: differ 0, sum 9500069. Switch true versus their own `P_on_O_d12.txt` rows: differ 0 of 200, sum 11919607. `partner_tables.txt`. A match of their switch, my 300 R openings, both colours, 600 games, from `partner_match.log`:

```
Elo: 3.47 +/- 6.80, nElo: 14.21 +/- 27.80
LOS: 84.17 %, DrawRatio: 93.00 %, PairsRatio: 1.62
Games: 600, Wins: 273, Losses: 267, Draws: 60, Points: 303.0 (50.50 %)
```

Verdict: CONFIRMS. The proofs they published that this step re-runs (honesty counts, the on rows in their file, and a clean apply) came out the same.

suspicions, not proven. 199 of 200 positions changed at depth 12. That is a wide footprint for a mark that was meant to catch a rare expensive try. The match does not show a gain. I do not know whether Ratio 150 is simply too easy to pass.

what I did NOT do. I did not run G at depth 12 with the switch on. I did not replay seat 029's 1106-game OG match. I did not play a second R match of my own patch, because 029 had a patch. No `FABLE_TO_grok_<N>.md` was on the handoff branch at step 1 or at minute 60. I did not open a pull request.

what I am NOT sure about. Whether the table's preference for shallower marks keeps the moves that matter. What fastchess means by DrawRatio 93.00 % on the partner match when the same block says Draws: 60 of 600. The main match's DrawRatio 60.22 % does match 427/1106.

times: see stamps.txt

```
git status --short
A  forge-combo29/grok/079/HONESTY_PARTNER.txt
A  forge-combo29/grok/079/REPORT.md
A  forge-combo29/grok/079/RESULT.txt
A  forge-combo29/grok/079/honesty_partner_bench11.meta
A  forge-combo29/grok/079/honesty_partner_bench11.txt
A  forge-combo29/grok/079/honesty_partner_bench13.meta
A  forge-combo29/grok/079/honesty_partner_bench13.txt
A  forge-combo29/grok/079/honesty_partner_bench16.meta
A  forge-combo29/grok/079/honesty_partner_bench16.txt
A  forge-combo29/grok/079/honesty_partner_perft5.meta
A  forge-combo29/grok/079/honesty_partner_perft5.txt
A  forge-combo29/grok/079/my_apply_check.txt
A  forge-combo29/grok/079/partner029_P_on_O_d12.txt
A  forge-combo29/grok/079/partner029_claimed_O.nodes
A  forge-combo29/grok/079/partner029_idea.patch.txt
A  forge-combo29/grok/079/partner_apply_check.txt
A  forge-combo29/grok/079/partner_match.log
A  forge-combo29/grok/079/partner_match.pgn
A  forge-combo29/grok/079/partner_match_R300.fens
A  forge-combo29/grok/079/partner_off_O_d12.meta
A  forge-combo29/grok/079/partner_off_O_d12.nodes
A  forge-combo29/grok/079/partner_off_O_d12.raw.txt
A  forge-combo29/grok/079/partner_on_O_d12.meta
A  forge-combo29/grok/079/partner_on_O_d12.nodes
A  forge-combo29/grok/079/partner_on_O_d12.raw.txt
A  forge-combo29/grok/079/partner_tables.txt
M  forge-combo29/grok/079/stamps.txt
?? config.json

ls -la
total 8412
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu    8696 Nov 20 08:13 asan_bad.partial.txt
-rw-r--r-- 1 ubuntu ubuntu    1253 Nov 20 08:15 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     585 Nov 20 08:12 asan_G100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu  117669 Nov 20 08:12 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:13 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     966 Nov 20 08:09 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:09 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  502539 Nov 20 08:09 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     966 Nov 20 08:09 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:09 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  278969 Nov 20 08:09 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7873 Nov 20 08:20 config.json
-rw-r--r-- 1 ubuntu ubuntu    1487 Nov 20 08:15 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:12 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 G.epd
-rw-r--r-- 1 ubuntu ubuntu    9516 Nov 20 08:10 harness.py
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:08 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:08 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:08 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:08 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:08 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:08 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:08 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:08 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 08:08 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:11 honesty_partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:11 honesty_partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:11 honesty_partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:11 honesty_partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:11 honesty_partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 09:11 honesty_partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 09:11 honesty_partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 09:11 honesty_partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 09:11 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:10 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5290 Nov 20 08:10 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:10 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5290 Nov 20 08:10 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:10 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5292 Nov 20 08:10 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:10 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5503 Nov 20 08:10 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 08:10 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   16769 Nov 20 08:10 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1297 Nov 20 08:15 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  145963 Nov 20 08:20 match.log
-rw-r--r-- 1 ubuntu ubuntu 4045225 Nov 20 08:20 match.pgn
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:14 my_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:14 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1220 Nov 20 09:12 partner029_claimed_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:11 partner029_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  301108 Nov 20 09:11 partner029_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:11 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   76314 Nov 20 09:13 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu  989085 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   15724 Nov 20 09:12 partner_match_R300.fens
-rw-r--r-- 1 ubuntu ubuntu    1033 Nov 20 09:11 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:11 partner_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  278783 Nov 20 09:11 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1033 Nov 20 09:11 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1220 Nov 20 09:11 partner_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  280732 Nov 20 09:11 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 09:14 partner_tables.txt
-rw-r--r-- 1 ubuntu ubuntu    1027 Nov 20 08:11 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:11 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  502288 Nov 20 08:11 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1027 Nov 20 08:11 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:11 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  278869 Nov 20 08:11 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1207 Nov 20 08:11 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:11 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  279546 Nov 20 08:11 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     593 Nov 20 08:09 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   12241 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:14 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   21059 Nov 20 08:15 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1215 Nov 20 08:15 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1355 Nov 20 08:22 run_r_match.sh
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    2345 Nov 20 08:16 tables.py
-rw-r--r-- 1 ubuntu ubuntu    1003 Nov 20 08:16 tables.txt
-rw-r--r-- 1 ubuntu ubuntu    5229 Nov 20 08:16 uci_p.txt
```
