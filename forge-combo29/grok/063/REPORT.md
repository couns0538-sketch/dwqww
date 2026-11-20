# Seat 063, idea 13, S15

In a rook ending of at least eight pieces, a rook move that reaches a passed pawn's file in no more moves than that pawn needs for its next step is searched at full depth. It is not extended, and nothing is added to the evaluation.
The switch is the check option IdeaS15, default false. IdeaS15_MinPieces defaults to 8 and IdeaS15_MaxRookMoves defaults to 1. The rule is in idea.patch.txt and DESIGN.txt.
With the switch false the extra test is not called, so the reduction stays the one the plain engine computed.

EXISTS: no. The reduction block in forge-combo29/src/search.cpp has no rook-versus-passer test.

Honesty, plain engine and patched engine, no setoption. bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. HONESTY_B.txt and HONESTY_P.txt both say the match is true. The plain engine's O depth 12 sum is 9500069 (first three 41311, 24872, 28574) and G depth 12 sum is 18466239.

The table is the output of print_report_table.py.

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 063, idea 13, model Grok 4.7, 2026-11-20T07:54:19Z, token 102692944427088
STEP 2 honesty B | done | HONESTY_B.txt | honesty_b true
STEP 2 O and G baseline | done | O_B_d12.nodes G_B_d12.nodes | positions 200 first3 41311 24872 28574 sum 9500069; positions 353 first3 37203 70845 144383 sum 18466239
STEP 3 prediction | done | prediction.txt | committed before the patched measurements
apply check | done | apply_check.txt | git apply --check exit 0
proof 1 honesty P | done | HONESTY_P.txt | honesty_p true
proof 2 switch off | done | compare_O_off.txt compare_G_off.txt | differ 0 of 200; differ 0 of 353
proof 3 switch on O | done | compare_O_on.txt sum_O_on.txt | differ 0 of 200; sum 9500069
proof 3 why O is 0 | done | compare_rook.txt compare_G_on.txt | differ 1 of 1; differ 77 of 353
proof 4 uci options | done | uci_p.txt | option name IdeaS15 type check default false | option name IdeaS15_MinPieces type spin default 8 min 2 max 32 | option name IdeaS15_MaxRookMoves type spin default 1 min 0 max 4
proof 5 sanitizer | done | san_g100.meta san_g100.hits san_scratch.hits | nm_asan_symbols=35; sanitizer_lines 0; sanitizer_lines 3
test match | done | match_og_summary.txt match_og.txt | elo -3.77; err 6.91; games 1106; interval -10.68 3.14; whole_interval_below_0 false; below_minus_20 false
partner 013 proofs | done | partner_honesty.txt partner_compare_off.txt partner_compare_on.txt | partner_honesty true; off differ 0 of 200; on differ 0 of 200
partner match | done | partner_match_summary.txt | elo -11.01; err 11.69; games 600; interval -22.7 0.6799999999999997; whole_interval_below_0 false; below_minus_20 false
```

Proof (1). Patched engine, no setoption: the four honesty numbers above, all matching. HONESTY_P.txt.

Proof (2). S14 and IdeaS15 false. O depth 12 differs in 0 of 200 positions from the plain engine. G depth 12 differs in 0 of 353. compare_O_off.txt, compare_G_off.txt.

Proof (3). S14 and IdeaS15 true. O depth 12 differs in 0 of 200 and the sum stays 9500069. That is not a dead option. The same binary on the rook ending in rook_ending.fen changes depth-10 nodes from 24914 to 29456 (compare_rook.txt). On G, 77 of 353 positions differ (compare_G_on.txt). Opening trees at depth 12 do not reach a rook ending of this shape, which is why O does not move.

Proof (4). uci_p.txt lists IdeaS15 as a check default false, IdeaS15_MinPieces spin default 8, and IdeaS15_MaxRookMoves spin default 1.

Proof (5). The sanitizer build's meta has nm_asan_symbols=35. The first 100 positions of G at depth 10 with the switch on produced 0 sanitizer lines (san_g100.hits). The same runner on a scratch copy with one deliberate read past the end of a four-int heap array, triggered by the FEN in scratch_fen.fen, reported AddressSanitizer heap-buffer-overflow (san_scratch.hits, 3 sanitizer lines).

git apply --check on a fresh checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0. apply_check.txt.

Match. IdeaS15 on (s15on) against IdeaS15 off (s15off), both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes a move, openings O then G (553), both colours, 1106 games, concurrency 3. extract_match.py on match_og.txt: elo -3.77, err 6.91, games 1106, interval -10.68 to 3.14. The point estimate is not below -20 and the interval is not entirely below 0, so the code was not searched again for a mistake. Prediction was sum 9700000 (wrong outside 8500000 to 14000000) and Elo 3 (wrong outside -25 to 40). The measured sum 9500069 and Elo -3.77 are inside those bands. prediction.txt was not edited.

Partner. Seats for idea 13 are 013, 063, and 113. 113 had no branch. The next seat after 063 that has a branch is 013. That branch has idea.patch.txt. The patch implements IdeaS13 (a history for the quiet piece move before a pawn break), which is list entry 16, not S15. Their design.txt says IdeaS13. On a fresh base: git apply --check exited 0, the release build's honesty numbers match, IdeaS13 false matches the plain O depth-12 rows (0 of 200), and IdeaS13 true matches their own O depth-12 rows (0 of 200; sum 9796924; first three 18065 31357 37580). A match of their switch on the 300 R openings, both colours, was 600 games: elo -11.01, err 11.69. Verdict CONFIRMS the proofs they published for that patch.

Suspicions, not proven. The match Elo of -3.77 may be noise: the interval includes 0 and small positive values. I do not claim the idea loses. The 600-game partner match interval reaches above 0, so I do not claim their patch loses either.

What I did NOT do. I did not measure IdeaS15_MinPieces or IdeaS15_MaxRookMoves at any value other than the defaults. I did not re-play the partner's 1106-game match. I did not run the sanitizer past the first 100 positions of G at depth 10. I did not add a hit counter to the O search. No forge-combo29/soak_all/FABLE_TO_grok file was on the handoff branch at STEP 1 or at minute 60.

What I am NOT sure about. R positions are plies 15, 22, 29, 36, 43 and 50 of random games that were still going at ply 50; "every 7 plies after ply 8" might have meant starting at ply 8. Passed pawns of both colours count, and a rook already on the file counts as 0 moves. A blocked pawn's next step costs 2, so a rook that lands on the file is always in time under the default MaxRookMoves of 1. A rook ending here means no knight, bishop, or queen, and a rook on each side.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/063/stamps.txt
?? config.json
?? forge-combo29/grok/063/REPORT.md
?? forge-combo29/grok/063/RESULT.txt
?? forge-combo29/grok/063/config.json
?? forge-combo29/grok/063/partner_O_off.meta
?? forge-combo29/grok/063/partner_O_off.nodes
?? forge-combo29/grok/063/partner_O_off.txt
?? forge-combo29/grok/063/partner_O_on.meta
?? forge-combo29/grok/063/partner_O_on.nodes
?? forge-combo29/grok/063/partner_O_on.txt
?? forge-combo29/grok/063/partner_apply_check.txt
?? forge-combo29/grok/063/partner_bench11.meta
?? forge-combo29/grok/063/partner_bench11.txt
?? forge-combo29/grok/063/partner_bench13.meta
?? forge-combo29/grok/063/partner_bench13.txt
?? forge-combo29/grok/063/partner_bench16.meta
?? forge-combo29/grok/063/partner_bench16.txt
?? forge-combo29/grok/063/partner_claimed_on_O.nodes
?? forge-combo29/grok/063/partner_claimed_on_O.tsv
?? forge-combo29/grok/063/partner_compare_off.txt
?? forge-combo29/grok/063/partner_compare_on.txt
?? forge-combo29/grok/063/partner_honesty.sh
?? forge-combo29/grok/063/partner_honesty.txt
?? forge-combo29/grok/063/partner_match.pgn
?? forge-combo29/grok/063/partner_match.sh
?? forge-combo29/grok/063/partner_match.txt
?? forge-combo29/grok/063/partner_match_summary.txt
?? forge-combo29/grok/063/partner_perft5.meta
?? forge-combo29/grok/063/partner_perft5.txt
?? forge-combo29/grok/063/partner_sum_on.txt
?? forge-combo29/grok/063/print_report_table.py

$ ls -la forge-combo29/grok/063
total 2760
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:05 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:01 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:01 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:01 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     167 Nov 20 08:05 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     780 Nov 20 08:07 compare_G_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1011 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     167 Nov 20 08:05 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:05 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:07 compare_rook.txt
-rw-r--r-- 1 ubuntu ubuntu    7119 Nov 20 08:20 config.json
-rwxr-xr-x 1 ubuntu ubuntu    5747 Nov 20 08:01 depth_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1189 Nov 20 08:13 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu     715 Nov 20 08:24 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:01 G_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3430 Nov 20 08:01 G_B_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   80782 Nov 20 08:01 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1009 Nov 20 08:05 G_P_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3430 Nov 20 08:05 G_P_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   80782 Nov 20 08:05 G_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1008 Nov 20 08:07 G_P_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3427 Nov 20 08:07 G_P_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   80564 Nov 20 08:07 G_P_on_d12.txt
-rwxr-xr-x 1 ubuntu ubuntu     698 Nov 20 08:00 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1340 Nov 20 08:05 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6953 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1419 Nov 20 08:12 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 1078862 Nov 20 08:20 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     101 Nov 20 08:24 match_og_summary.txt
-rw-r--r-- 1 ubuntu ubuntu  138732 Nov 20 08:20 match_og.txt
-rwxr-xr-x 1 ubuntu ubuntu    1369 Nov 20 08:12 match.sh
-rw-r--r-- 1 ubuntu ubuntu     971 Nov 20 08:01 O_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 08:01 O_B_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   46804 Nov 20 08:01 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:12 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1013 Nov 20 08:05 O_P_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 08:05 O_P_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   46804 Nov 20 08:05 O_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1012 Nov 20 08:05 O_P_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 08:05 O_P_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu   46803 Nov 20 08:05 O_P_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 09:12 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:12 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1897 Nov 20 09:17 partner_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu    2899 Nov 20 09:12 partner_claimed_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 09:12 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:17 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1393 Nov 20 09:11 partner_honesty.sh
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 09:12 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu  538457 Nov 20 09:16 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1245 Nov 20 09:12 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 09:17 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   63871 Nov 20 09:16 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu    1008 Nov 20 09:12 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 09:12 partner_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu   46803 Nov 20 09:12 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1007 Nov 20 09:12 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1897 Nov 20 09:12 partner_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu   46962 Nov 20 09:12 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:12 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 09:12 partner_sum_on.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:05 p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:05 p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:05 p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:01 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:05 p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     991 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    2868 Nov 20 09:17 print_report_table.py
-rw-r--r-- 1 ubuntu ubuntu    7958 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19939 Nov 20 08:12 R.fens
-rw-r--r-- 1 ubuntu ubuntu     103 Nov 20 08:12 R.meta
-rw-r--r-- 1 ubuntu ubuntu      42 Nov 20 08:07 rook_ending.fen
-rw-r--r-- 1 ubuntu ubuntu    1041 Nov 20 08:07 rook_off_d10.meta
-rw-r--r-- 1 ubuntu ubuntu       8 Nov 20 08:07 rook_off_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 08:07 rook_off_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    1040 Nov 20 08:07 rook_on_d10.meta
-rw-r--r-- 1 ubuntu ubuntu       8 Nov 20 08:07 rook_on_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:07 rook_on_d10.txt
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:11 san_g100.hits
-rw-r--r-- 1 ubuntu ubuntu    1058 Nov 20 08:11 san_g100.meta
-rw-r--r-- 1 ubuntu ubuntu   13243 Nov 20 08:11 san_g100.txt
-rw-r--r-- 1 ubuntu ubuntu    6475 Nov 20 08:09 san_run.py
-rw-r--r-- 1 ubuntu ubuntu     418 Nov 20 08:11 san_scratch.hits
-rw-r--r-- 1 ubuntu ubuntu    1085 Nov 20 08:11 san_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    8708 Nov 20 08:11 san_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:11 scratch_fen.fen
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:17 stamps.txt
-rwxr-xr-x 1 ubuntu ubuntu     555 Nov 20 08:01 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:05 sum_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:05 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5106 Nov 20 08:05 uci_p.txt
-rwxr-xr-x 1 ubuntu ubuntu     755 Nov 20 08:01 write_honesty_b.py
```
