Idea S16. A quiet pawn lever that clears the last stopper is ordered higher and reduced less. Nothing is added to the evaluation.
Check `IdeaS16` defaults false. Spins `IdeaS16_Order` 4000 and `IdeaS16_Relief` 1.
The boosted move is a quiet pawn push onto a square that attacks the single lever-stopper, or a capture of that stopper whose static exchange is not losing. Helpers and attackers on the push square are pawns. Why that shape is in `DECISIONS.txt`.

EXISTS: no. The plain engine does not detect this lever or change its order or reduction for it.

Honesty numbers, from `summarize.py` reading the raw bench and perft files. Exe B and exe P with no setoption:

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

Exe B, S14, depth 12: O sum 9500069, first three 41311 / 24872 / 28574. G sum 18466239.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 068, idea 18, IdeaS16 |
| 2 honesty and known sums | done | HONESTY_B.txt, B_O_d12.txt, B_G_d12.txt | benches match; O 9500069; G 18466239 |
| 3 patch applies | done | idea.patch.txt, apply_check.txt | git apply --check exit 0 |
| 3 proof off | done | P_off_O_d12.txt, P_off_G_d12.txt | 0 of 200 and 0 of 353 differ from exe B |
| 3 proof on | done | P_on_O_d12.txt | 190 of 200 differ; sum 9515926 |
| 3 uci options | done | P_uci_id.txt | IdeaS16 false, Order 4000, Relief 1 |
| 3 sanitizer | done | asan_G100_d10.san, asan_scratch_special.san | clean; scratch reports the heap read |
| 3 match | done | match_stdout.txt, match.pgn | 1106 games, Elo -3.46 +/- 10.02 |
| 4 partner 018 | done | partner_compare.txt, partner_match_stdout.txt | CONFIRMS |
| 5 this report | done | REPORT.md, RESULT.txt | one result line |

Proofs, pasted from `proof_summary.txt` (output of `summarize.py`):

```
honesty B
  bench11 312866
  bench13 862329
  bench16 3024920
  perft5 4865609
honesty P
  P_bench11 312866
  P_bench13 862329
  P_bench16 3024920
  P_perft5 4865609
B O sum 9500069
B G sum 18466239
P off O sum 9500069
P off G sum 18466239
P on O sum 9515926
off O vs B differ 0 of 200
off G vs B differ 0 of 353
on O vs B differ 190 of 200
asan clean exe /tmp/forge-asan/forge | asan_symbols 35 | suite_exit 0 | sanitizer_lines 0
asan scratch exe /tmp/scratch-asan/forge | asan_symbols 35 | suite_exit 1 | sanitizer_lines 3 | first /tmp/scratch-forge/src/uci.cpp:47:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
uci id name Chess Engine Forge 6.4.24 candidate
uci option name IdeaS16 type check default false
uci option name IdeaS16_Order type spin default 4000 min 0 max 20000
uci option name IdeaS16_Relief type spin default 1 min 0 max 4
```

(1) Honesty with no setoption is unchanged on exe P.
(2) Switch false, S14: O and G depth 12 match exe B on every position.
(3) Switch true: 190 of 200 O positions differ. Sum 9515926. The code runs.
(4) `uci` lists the three new options with those defaults.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build: `nm -C` count of `__asan_` is 35. First 100 of G at depth 10, switch true: 0 sanitizer lines. The same runner on a scratch copy that reads one past a 4-int heap array on the FEN in `special.fen` prints the AddressSanitizer heap-buffer-overflow line. `apply_check.txt` is `EXIT:0`.

Match, pasted from `match_elo.py`:

```
Results of s16on vs s16off (20000 nodes, 1t, 16MB, match_openings.epd):
Elo: -3.46 +/- 10.02, nElo: -7.06 +/- 20.48
LOS: 24.95 %, DrawRatio: 65.64 %, PairsRatio: 0.92
Games: 1106, Wins: 344, Losses: 355, Draws: 407, Points: 547.5 (49.50 %)
Ptnml(0-2): [14, 85, 363, 80, 11], WL/DD Ratio: 2.00
Total Time: 00:05:17 (hours:minutes:seconds)
```

Both sides S14, Threads 1, Hash 16, OwnBook false, 20000 nodes. Openings are O then G, 553 positions, both colours, 1106 games. Draw adjudication after move 40 for 8 scores inside 15 centipawns, and resign after 4 scores past 800. The interval includes 0 and the point is not below -20, so I did not open the code looking for a match-losing mistake.

Partner. Seat 118 had no branch at 2026-11-20T09:09:40Z. The next seat with this idea is 018. Their patch applies (`partner_apply_check.txt` is `EXIT:0`). Their build's honesty numbers match. Switch false matches exe B on all 200 O positions. Switch true matches their own `p_on_O_d12.tsv` on all 200 positions (0 fen mismatches) and differs from exe B on 165, which is the count in their `compare_on_O.txt`. Their O-on sum is 9482592, same as my run. Pasted from `partner_compare.txt` and `partner_match_elo.py`:

```
off versus exe B
positions 200 differ 0 equal 200
on versus partner tsv
compared 200 fen_mismatch 0 differ 0 equal 200
on versus exe B
positions 200 differ 165 equal 35
Results of on vs off (20000 nodes, 1t, 16MB, R.fens):
Elo: 0.58 +/- 10.83
Games: 600, Wins: 267, Losses: 266, Draws: 67, Points: 300.5 (50.08 %)
Total Time: 00:01:48 (hours:minutes:seconds)
```

Verdict: CONFIRMS. Every proof they stated that this step checks holds on a fresh base. The 600-game R match is my measurement of their switch, not a replay of their 1106-game book.

suspicions, not proven

I predicted an O depth-12 sum of 10800000 and wrote that a sum below 9700000 would prove that prediction wrong. The measured sum is 9515926. The prediction is wrong. `prediction.txt` was not edited. The tree changes shape (190 positions differ) but the node total barely moves, because some positions get smaller. I do not know whether pawn-only helpers are the reading the idea's sources used. Seat 018 counted every piece and only boosted a quiet push that empties the span. Both readings change the search. The Elo -3.46 +/- 10.02 is compatible with a small loss and with no change.

what I did NOT do

No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not replay seat 018's 1106-game match. I did not build the sanitizer match. I did not tune Order or Relief. Games that ended before ply 80 would have been dropped from R; none of the 28 games ended, so R has 300 positions from games that reached ply 80. I did not open a pull request.

what I am NOT sure about

Whether the lever should count non-pawn attackers on the push square. Whether 4000 is a large enough order bonus once history is no longer zero. The match is one node budget on the built-in net.

times: see stamps.txt

```
 M forge-combo29/grok/068/stamps.txt
?? forge-combo29/grok/068/REPORT.md
?? forge-combo29/grok/068/RESULT.txt
?? forge-combo29/grok/068/apply_check.txt
?? forge-combo29/grok/068/compare_partner_tsv.py
?? forge-combo29/grok/068/match_elo.txt
?? forge-combo29/grok/068/partner018.patch.txt
?? forge-combo29/grok/068/partner018_on_O.tsv
?? forge-combo29/grok/068/partner_HONESTY.txt
?? forge-combo29/grok/068/partner_apply_check.txt
?? forge-combo29/grok/068/partner_bench11.meta
?? forge-combo29/grok/068/partner_bench11.txt
?? forge-combo29/grok/068/partner_bench13.meta
?? forge-combo29/grok/068/partner_bench13.txt
?? forge-combo29/grok/068/partner_bench16.meta
?? forge-combo29/grok/068/partner_bench16.txt
?? forge-combo29/grok/068/partner_compare.txt
?? forge-combo29/grok/068/partner_match.pgn
?? forge-combo29/grok/068/partner_match.sh
?? forge-combo29/grok/068/partner_match_config.json
?? forge-combo29/grok/068/partner_match_elo.py
?? forge-combo29/grok/068/partner_match_stderr.txt
?? forge-combo29/grok/068/partner_match_stdout.txt
?? forge-combo29/grok/068/partner_off.setoption
?? forge-combo29/grok/068/partner_off_O_d12.log
?? forge-combo29/grok/068/partner_off_O_d12.meta
?? forge-combo29/grok/068/partner_off_O_d12.stderr
?? forge-combo29/grok/068/partner_off_O_d12.txt
?? forge-combo29/grok/068/partner_on.setoption
?? forge-combo29/grok/068/partner_on_O_d12.log
?? forge-combo29/grok/068/partner_on_O_d12.meta
?? forge-combo29/grok/068/partner_on_O_d12.stderr
?? forge-combo29/grok/068/partner_on_O_d12.txt
?? forge-combo29/grok/068/partner_perft5.meta
?? forge-combo29/grok/068/partner_perft5.txt
?? forge-combo29/grok/068/proof_summary.txt
```

```
total 8636
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  131910 Nov 20 08:07 asan_G100_d10.log
-rw-r--r-- 1 ubuntu ubuntu     978 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:07 asan_G100_d10.san
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100_d10.stderr
-rw-r--r-- 1 ubuntu ubuntu    6194 Nov 20 08:07 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    6349 Nov 20 08:08 asan_scratch_special.log
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 08:08 asan_scratch_special.san
-rw-r--r-- 1 ubuntu ubuntu    3893 Nov 20 08:08 asan_scratch_special.stderr
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:03 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:03 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:03 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu  549808 Nov 20 08:03 B_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 B_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   22195 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  308942 Nov 20 08:03 B_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:03 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 B_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15369 Nov 20 08:03 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1498 Nov 20 09:10 compare_partner_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    1111 Nov 20 08:05 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7324 Nov 20 09:16 config.json
-rw-r--r-- 1 ubuntu ubuntu    1373 Nov 20 08:05 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:02 G.epd
-rw-r--r-- 1 ubuntu ubuntu    3166 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   11688 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1310 Nov 20 08:09 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     474 Nov 20 08:16 match_elo.py
-rw-r--r-- 1 ubuntu ubuntu     455 Nov 20 09:16 match_elo.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 match_openings.epd
-rw-r--r-- 1 ubuntu ubuntu 3889382 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1487 Nov 20 08:09 match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 match_stderr.txt
-rw-r--r-- 1 ubuntu ubuntu  128551 Nov 20 08:15 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:02 O.fens
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 08:05 off.setoption
-rw-r--r-- 1 ubuntu ubuntu      49 Nov 20 08:05 on.setoption
-rw-r--r-- 1 ubuntu ubuntu   15795 Nov 20 09:10 partner018_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu   10244 Nov 20 09:10 partner018.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:16 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 09:10 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 09:10 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 09:10 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1172 Nov 20 09:16 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:10 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    7104 Nov 20 09:16 partner_match_config.json
-rw-r--r-- 1 ubuntu ubuntu     490 Nov 20 09:16 partner_match_elo.py
-rw-r--r-- 1 ubuntu ubuntu 1355446 Nov 20 09:12 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1333 Nov 20 08:17 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_match_stderr.txt
-rw-r--r-- 1 ubuntu ubuntu   60815 Nov 20 09:12 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu  309080 Nov 20 09:10 partner_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 09:10 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15369 Nov 20 09:10 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 09:10 partner_off.setoption
-rw-r--r-- 1 ubuntu ubuntu  309292 Nov 20 09:10 partner_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1009 Nov 20 09:10 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15368 Nov 20 09:10 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 09:10 partner_on.setoption
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 09:10 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:05 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:05 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:05 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:03 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 P_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu  550171 Nov 20 08:05 P_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   22195 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  309517 Nov 20 08:05 P_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15369 Nov 20 08:05 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  309471 Nov 20 08:06 P_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 08:06 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15368 Nov 20 08:06 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:05 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     511 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     898 Nov 20 09:16 proof_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:05 P_uci_id.txt
-rw-r--r-- 1 ubuntu ubuntu    6448 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19231 Nov 20 08:09 R.fens
-rw-r--r-- 1 ubuntu ubuntu    1955 Nov 20 08:06 sanitizer_run.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 special.fen
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    6343 Nov 20 08:03 suite_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    2989 Nov 20 08:10 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:03 uci_id.txt
```
