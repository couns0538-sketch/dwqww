# Seat 047, idea 47, IdeaK8

IdeaK8 adds one ply of late-move reduction to a capture whose static exchange loses material.
The check option IdeaK8 defaults to false, and the spin IdeaK8_Extra defaults to 1 (range 0 to 4).
The loss is read with see_ge before make_move. With the switch false that call is skipped and the reduction is unchanged.

EXISTS: no. In forge-combo29/src/search.cpp the noisy reduction does not look at static exchange. see_ge is used to prune bad captures and to allow a check extension. No IdeaK8 option was advertised.

Honesty, no setoption, fresh process each line. Both exes pass. Plain exe B sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83. Patched exe P sha256 b0430bd7371348e72d10e8283b6206087acf66ab7da78d777a6ee8ca574920cb. id name Chess Engine Forge 6.4.24 candidate.

```
bench 11 nodes 312866
bench 13 nodes 862329
bench 16 nodes 3024920
go perft 5 nodes 4865609
```

Raw files: HONESTY_B.txt, HONESTY_P.txt, honesty_b_*.txt, honesty_p_*.txt.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 047 idea 47 |
| 2 honesty and baseline | done | HONESTY_B.txt, B_O_d12.nodes, B_G_d12.nodes | honesty pass; O 9500069; G 18466239 |
| 3a read | done | decisions.txt, idea.patch.txt | not already present |
| 3b prediction | done | prediction.txt | 9140000 and +5, committed before measuring P |
| 3c patch | done | idea.patch.txt, apply_check.txt | apply_check_exit=0 |
| 3d proofs | done | numbers_out.txt | off differ 0; on differ 200; sanitizer clean |
| 3e match | done | match_og.txt, match_og.pgn | 1106 games, Elo -7.85 +/- 10.27 |
| 4 partner | not done | partner.txt, match_r.txt | no seat 097; second match played instead |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Patched exe, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. HONESTY_P.txt says ALL_PASS.

Proof (2). S14 and IdeaK8 false. O depth 12: 200 lines, sum 9500069, differ 0 against exe B. G depth 12: 353 lines, sum 18466239, differ 0 against exe B. compare_off_O.txt, compare_off_G.txt.

Proof (3). S14 and IdeaK8 true. O depth 12 sum 9332591, first three 22042 23930 33107. differ 200 of 200 against exe B. compare_on_O.txt. Prediction was 9140000, wrong outside 8600000 to 9450000. 9332591 is inside that range.

Proof (4). uci lists `option name IdeaK8 type check default false` and `option name IdeaK8_Extra type spin default 1 min 0 max 4`. uci_p.txt.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK8 true, first 100 of G at depth 10. asan_g100.stderr is 0 bytes. asan_g100.meta has nm_asan_count=35 from `nm -C` counting `__asan_`. A scratch copy with one heap read past the end of a 4-int array, triggered only by the FEN in asan_trigger.fen, built the same way and run through search_set.py, prints `AddressSanitizer: heap-buffer-overflow` in asan_scratch.stderr.

Match. IdeaK8 true versus IdeaK8 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. fastchess output match_og.txt, games match_og.pgn (1106 Result headers). Last block from numbers.py:

```
Results of on vs off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -7.85 +/- 10.27, nElo: -15.67 +/- 20.48
LOS: 6.68 %, DrawRatio: 65.28 %, PairsRatio: 0.78
Games: 1106, Wins: 327, Losses: 352, Draws: 427, Points: 540.5 (48.87 %)
Ptnml(0-2): [15, 93, 361, 70, 14], WL/DD Ratio: 1.73
Finished match
Total Time: 00:06:17 (hours:minutes:seconds)
```

Predicted Elo was +5, wrong below -15 or above +25. -7.85 is inside that range. The interval is not entirely below 0, and the point is not below -20, so the required second look for a code mistake was not triggered. Draws by threefold repetition and the fifty-move rule in the PGN are legal endings.

Partner verdict: not done. Idea 47 belongs to seats 047 and 097. At 2026-11-20T09:09:07Z, ls-remote had no for-fable-and-opus/grok-097. There was no partner branch to fetch, so I did not wait for a patch. Second match of this patch, 300 R openings, both colours, 600 games, match_r.txt:

```
Results of on vs off (20000 nodes, 1t, 16MB, R.epd):
Elo: 5.21 +/- 11.17, nElo: 12.98 +/- 27.80
LOS: 81.99 %, DrawRatio: 79.67 %, PairsRatio: 1.18
Games: 600, Wins: 268, Losses: 259, Draws: 73, Points: 304.5 (50.75 %)
Ptnml(0-2): [4, 24, 239, 25, 8], WL/DD Ratio: 18.92
Finished match
Total Time: 00:02:41 (hours:minutes:seconds)
```

suspicions, not proven

The main match point is negative and the random-opening match point is positive. Both intervals include values on either side of 0. I do not know which sign would remain at more games or with the owner's net.
Calling see_ge after make_move sees no capture, so an extra ply placed there changes nothing. The patch reads the exchange first. I did not keep a node file from that earlier binary.

what I did NOT do

I did not review another seat's patch. I did not try IdeaK8_Extra at any value except 1. I did not run the sanitizer past the first 100 positions of G at depth 10. I did not play with a net other than the one built into the engine. I did not repeat an opening list.

what I am NOT sure about

I am not sure the one-ply default is better than leaving the search alone. The 1106-game interval still covers a small gain and a modest loss.
I am not sure every fastchess "mates" line is a checkmate under python-chess. I did not replay the PGN. The fifty-move and threefold lines match the rules of chess, so I am not treating those as engine faults.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/047/stamps.txt
?? config.json
?? forge-combo29/grok/047/REPORT.md
?? forge-combo29/grok/047/RESULT.txt
?? forge-combo29/grok/047/apply_check.txt
?? forge-combo29/grok/047/match_r.err
?? forge-combo29/grok/047/match_r.meta
?? forge-combo29/grok/047/match_r.pgn
?? forge-combo29/grok/047/match_r.sh
?? forge-combo29/grok/047/match_r.txt
?? forge-combo29/grok/047/numbers.py
?? forge-combo29/grok/047/numbers_out.txt
?? forge-combo29/grok/047/partner.txt
```

ls -la

```
total 9244
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:13 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu     482 Nov 20 08:09 append_asan_meta.py
-rw-r--r-- 1 ubuntu ubuntu      40 Nov 20 09:12 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  130614 Nov 20 08:09 asan_g100.log
-rw-r--r-- 1 ubuntu ubuntu     721 Nov 20 08:10 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu     583 Nov 20 08:09 asan_g100.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 asan_g100.stderr
-rw-r--r-- 1 ubuntu ubuntu    1193 Nov 20 08:10 asan_scratch.log
-rw-r--r-- 1 ubuntu ubuntu     746 Nov 20 08:10 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 asan_scratch.nodes
-rw-r--r-- 1 ubuntu ubuntu    3357 Nov 20 08:10 asan_scratch.stderr
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:10 asan_trigger.fen
-rw-r--r-- 1 ubuntu ubuntu  560932 Nov 20 07:58 B_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     621 Nov 20 07:57 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 07:58 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:57 B_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  312997 Nov 20 07:57 B_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     622 Nov 20 07:57 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 07:57 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:57 B_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu     718 Nov 20 08:01 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 08:07 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     155 Nov 20 08:07 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:07 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     999 Nov 20 08:10 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:56 G.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:56 honesty_b_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 07:56 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:56 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:56 honesty_b_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 07:56 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:56 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:56 honesty_b_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 07:56 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:56 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:56 honesty_b_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 07:56 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:56 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2325 Nov 20 08:01 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     341 Nov 20 07:56 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:07 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:07 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:07 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:07 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:07 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:07 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 honesty_p_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 08:07 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:07 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     341 Nov 20 08:07 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6132 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1492 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 match_og.err
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:17 match_og.meta
-rw-r--r-- 1 ubuntu ubuntu    1476 Nov 20 08:17 match_og.nohup
-rw-r--r-- 1 ubuntu ubuntu 4692999 Nov 20 08:17 match_og.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1513 Nov 20 08:11 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu  124594 Nov 20 08:17 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 match_r.err
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 09:11 match_r.meta
-rw-r--r-- 1 ubuntu ubuntu 2003360 Nov 20 09:11 match_r.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1496 Nov 20 08:54 match_r.sh
-rw-r--r-- 1 ubuntu ubuntu   63400 Nov 20 09:11 match_r.txt
-rw-r--r-- 1 ubuntu ubuntu    2602 Nov 20 09:12 numbers_out.txt
-rw-r--r-- 1 ubuntu ubuntu    1968 Nov 20 09:12 numbers.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:56 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:11 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      91 Nov 20 09:09 partner.txt
-rw-r--r-- 1 ubuntu ubuntu  561136 Nov 20 08:07 P_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     641 Nov 20 08:07 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:07 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_off_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  313287 Nov 20 08:07 P_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     642 Nov 20 08:07 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:07 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  313783 Nov 20 08:07 P_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     641 Nov 20 08:07 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:07 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu     891 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19275 Nov 20 08:09 R.epd
-rw-r--r-- 1 ubuntu ubuntu    6087 Nov 20 09:13 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:13 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    6089 Nov 20 07:57 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 09:12 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     807 Nov 20 08:01 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5034 Nov 20 08:07 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:07 uci_p.txt.meta
```
