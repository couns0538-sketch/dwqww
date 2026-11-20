# Seat 078, idea 28, B8

IdeaB8 is a check, default false. In a position where a cheaper enemy piece attacks a dearer piece of ours, each quiet gets one role: the attacked piece steps away, another piece blocks a slider, the quiet attacks the attacker, the quiet attacks a dearer enemy piece, or none. A table of those roles is added to the quiet history that already feeds ordering, history pruning, and late-move reduction. Spin options are IdeaB8_Weight 1024 and IdeaB8_Swing 48.

EXISTS: no. `ThreatHistory` in `forge-combo29/src/search.cpp` (`quiet_threat_index`) is the cheaper-attacker from-to table, idea S28, and it defaults off. This engine has no piece-value bonus for stepping off an attacked square, so there was nothing to remove. See `decisions.txt`.

## Honesty

Plain engine, no setoption, from `HONESTY_B.txt`:

```
bench 11 -> nodes 312866 expected 312866 OK
bench 13 -> nodes 862329 expected 862329 OK
bench 16 -> nodes 3024920 expected 3024920 OK
go perft 5 -> nodes 4865609 expected 4865609 OK
```

Idea build, no setoption, from `HONESTY_P.txt`: the same four numbers, all OK.

Exe B, S14, from `B_O_d12.sum.txt` and `B_G_d12.sum.txt`: O depth 12 sum 9500069 (first three 41311, 24872, 28574). G depth 12 sum 18466239.

## Steps

| step | state | evidence | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 078, idea 28 |
| 2 builds and baseline | done | HONESTY_B.txt, B_O_d12.sum.txt, B_G_d12.sum.txt | honesty matches; O 9500069; G 18466239 |
| 3 idea | done | idea.patch.txt, P_off_*.compare.txt, P_on_O_d12.compare.txt, asan_G100_d10.meta, match.sum.txt | off identical; on differs 200 of 200; sanitizer clean; Elo 7.23 +/- 10.49 |
| 4 partner 028 | done | partner028.patch.txt, partner_off_O.compare.txt, partner_on_O.compare.txt, partner_R.sum.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

`git apply --check` of `idea.patch.txt` on the plain base tree printed APPLY_CHECK_OK.

(1) Honesty, no setoption, idea build: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

(2) S14, IdeaB8 false. `compare_nodes.py` on O: differ 0, same 200. On G: differ 0, same 353.

(3) S14, IdeaB8 true, O depth 12. differ 200, same 0. Sum 9295189. Prediction was 9350000, wrong outside 6500000..13000000. The sum is inside that range.

(4) `uci` lists `IdeaB8` check default false, `IdeaB8_Weight` spin default 1024 min 0 max 4096, `IdeaB8_Swing` spin default 48 min 0 max 500. File `P_uci.txt`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build. `nm -C` count of `__asan_` is 35. First 100 of G at depth 10 with IdeaB8 true: exit 0, sanitizer lines 0 (`asan_G100_d10.err` is empty). The same runner on a scratch copy that reads one past a 4-int heap array for the FEN in `scratch.fen` reported `runtime error: load of address ... with insufficient space for an object of type 'int'`. Leak detection was off (`ASAN_OPTIONS=detect_leaks=0`).

## Match

`extract_match.py` on `match.log` and `match.pgn`:

```
Elo: 7.23 +/- 10.49, nElo: 14.11 +/- 20.48
Games: 1106, Wins: 361, Losses: 338, Draws: 407, Points: 564.5 (51.04 %)
pgn_games 1106
pgn_results 1106
```

Prediction was Elo 4, wrong if the whole interval was below -25 or above 35. The printed interval is not entirely on either side of that band. It is also not entirely below 0, so the code was not re-opened for a loss.

## Partner

Partner is seat 028 (the other seat of idea 28; seat 128 does not exist). `git apply --check` of `partner028.patch.txt` printed APPLY_CHECK_OK. Honesty of that build matched the four known numbers and the sha256 they published. IdeaB8 false: 0 of 200 O positions differ from exe B. IdeaB8 true: 0 of 200 differ from their `O12_P_on.nodes`. Verdict: CONFIRMS.

Their switch, my harness, 300 R openings, both colours, from `partner_R.sum.txt`:

```
Elo: -8.11 +/- 10.49
Games: 600, Wins: 259, Losses: 273, Draws: 68, Points: 293.0 (48.83 %)
```

## Suspicions, not proven

The two independent patches do not implement the same threat. Theirs can treat the king as the victim and uses swing 40; this one does not treat the king as a victim and uses swing 48. Their O sum with the switch on is 9718009 and this one's is 9295189. Both change the search. That does not say which one is stronger on the owner's net.

fastchess `DrawRatio` is not draws divided by games. The R match prints DrawRatio 80.33% with 68 draws in 600 games.

## What I did not do

I did not replay seat 028's 1106-game match. I did not run the sanitizer build at depth 12, and I did not turn leak detection on. I did not play the owner's net. I did not run a second R match of my own patch, because 028 had a patch.

## What I am not sure about

Whether the fastchess `+/-` number is a 95% interval. Whether a block or a discovered attack is labelled with the role a person would pick. Role labels for pins were not checked against a list of positions.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/078/stamps.txt
?? forge-combo29/grok/078/REPORT.md
?? forge-combo29/grok/078/RESULT.txt
?? forge-combo29/grok/078/compare_partner_on.py
?? forge-combo29/grok/078/honesty_any.py
?? forge-combo29/grok/078/partner028.patch.txt
?? forge-combo29/grok/078/partner028_O_on.nodes
?? forge-combo29/grok/078/partner_R.log
?? forge-combo29/grok/078/partner_R.pgn
?? forge-combo29/grok/078/partner_R.sum.txt
?? forge-combo29/grok/078/partner_honesty.txt
?? forge-combo29/grok/078/partner_honesty_bench11.meta
?? forge-combo29/grok/078/partner_honesty_bench11.txt
?? forge-combo29/grok/078/partner_honesty_bench13.meta
?? forge-combo29/grok/078/partner_honesty_bench13.txt
?? forge-combo29/grok/078/partner_honesty_bench16.meta
?? forge-combo29/grok/078/partner_honesty_bench16.txt
?? forge-combo29/grok/078/partner_honesty_perft5.meta
?? forge-combo29/grok/078/partner_honesty_perft5.txt
?? forge-combo29/grok/078/partner_off_O.compare.txt
?? forge-combo29/grok/078/partner_off_O_d12.meta
?? forge-combo29/grok/078/partner_off_O_d12.raw
?? forge-combo29/grok/078/partner_on_O.compare.txt
?? forge-combo29/grok/078/partner_on_O.sum.txt
?? forge-combo29/grok/078/partner_on_O_d12.meta
?? forge-combo29/grok/078/partner_on_O_d12.raw
?? forge-combo29/grok/078/run_opening_match.sh
```

## ls -la

```
total 8316
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 asan_G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu    1008 Nov 20 08:11 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  119999 Nov 20 08:11 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu    5198 Nov 20 08:10 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu    1068 Nov 20 08:11 asan_scratch.err
-rw-r--r-- 1 ubuntu ubuntu    1002 Nov 20 08:11 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    5261 Nov 20 08:11 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:06 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  510927 Nov 20 08:06 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      91 Nov 20 08:07 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     847 Nov 20 08:06 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  283684 Nov 20 08:06 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      89 Nov 20 08:07 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1407 Nov 20 08:08 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 09:11 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    1955 Nov 20 08:08 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    5227 Nov 20 08:06 depth_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     506 Nov 20 08:21 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:06 G.epd
-rw-r--r-- 1 ubuntu ubuntu    3701 Nov 20 08:56 honesty_any.py
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:05 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:05 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:05 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 08:05 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:05 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:05 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3850 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     290 Nov 20 08:05 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:08 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 08:08 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:08 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 08:08 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:08 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5172 Nov 20 08:08 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 08:08 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5383 Nov 20 08:08 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3850 Nov 20 08:08 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     290 Nov 20 08:08 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   22945 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1168 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  124245 Nov 20 08:19 match.log
-rw-r--r-- 1 ubuntu ubuntu 3583597 Nov 20 08:19 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     378 Nov 20 08:21 match.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:06 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:12 OG.fens
-rw-r--r-- 1 ubuntu ubuntu   14760 Nov 20 09:11 partner028_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu   20136 Nov 20 09:11 partner028.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:11 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 09:11 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:11 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5170 Nov 20 09:11 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:11 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5172 Nov 20 09:11 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 09:11 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5383 Nov 20 09:11 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     293 Nov 20 09:11 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu     229 Nov 20 09:11 partner_off_O.compare.txt
-rw-r--r-- 1 ubuntu ubuntu     903 Nov 20 09:11 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  283804 Nov 20 09:11 partner_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      54 Nov 20 09:11 partner_on_O.compare.txt
-rw-r--r-- 1 ubuntu ubuntu     902 Nov 20 09:11 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  284428 Nov 20 09:11 partner_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      94 Nov 20 09:11 partner_on_O.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   63340 Nov 20 09:14 partner_R.log
-rw-r--r-- 1 ubuntu ubuntu 1624837 Nov 20 09:14 partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     397 Nov 20 09:16 partner_R.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:09 P_off_G_d12.compare.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:09 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  511212 Nov 20 08:09 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:09 P_off_O_d12.compare.txt
-rw-r--r-- 1 ubuntu ubuntu     881 Nov 20 08:08 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  283876 Nov 20 08:08 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:09 P_on_O_d12.compare.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:09 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  284018 Nov 20 08:09 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 08:09 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     161 Nov 20 08:06 positions.source.txt
-rw-r--r-- 1 ubuntu ubuntu     257 Nov 20 08:07 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:09 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:09 P_uci.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5052 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19207 Nov 20 08:11 R.fens
-rwxr-xr-x 1 ubuntu ubuntu     925 Nov 20 08:12 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu     995 Nov 20 08:56 run_opening_match.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:11 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1771 Nov 20 08:06 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1642 Nov 20 08:08 uci_options.py
```
