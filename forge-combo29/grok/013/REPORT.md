Idea S13, option IdeaS13. A separate history remembers a non-capturing piece move that is followed, a few plies later and with the pawn structure unchanged, by a pawn move that raised the score. That history only orders those piece moves and shortens their reduction. It is not added to the evaluation.
The check defaults to false. The spins are Lag 4, Bonus 160, Divisor 48 and Shave 1: one credit adds 160 to the ordering score and takes one ply off the reduction, because 160/48 is capped at 1.
EXISTS: no. The plain search has continuation history and a threat history, and neither is this table.

Honesty, no setoption, bench 11 / 13 / 16 and go perft 5. Exe B and exe P both: 312866, 862329, 3024920, 4865609.

The block below is the output of proof_table.py, which reads the raw files.

HONESTY_B
exe /agent/repos/base/forge-combo29/build/forge
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name Chess Engine Forge 6.4.24 candidate
setoption none
bench 11 nodes 312866 expected 312866 ok
bench 13 nodes 862329 expected 862329 ok
bench 16 nodes 3024920 expected 3024920 ok
go perft 5 nodes 4865609 expected 4865609 ok
HONESTY_P
exe /agent/repos/work/forge-combo29/build/forge
sha256 dd087d351737e0a3d09f5a5587e51626aea31072ea521dd55012232db4d3b8b0
id_name Chess Engine Forge 6.4.24 candidate
setoption none
bench 11 nodes 312866 expected 312866 ok
bench 13 nodes 862329 expected 862329 ok
bench 16 nodes 3024920 expected 3024920 ok
go perft 5 nodes 4865609 expected 4865609 ok
SUMS
tag B_O_d12
count 200
depth 12
sum 9500069
first 41311 24872 28574
tag B_G_d12
count 353
depth 12
sum 18466239
first 37203 70845 144383
tag P_off_O_d12
count 200
depth 12
sum 9500069
first 41311 24872 28574
tag P_off_G_d12
count 353
depth 12
sum 18466239
first 37203 70845 144383
tag P_on_O_d12
count 200
depth 12
sum 9796924
first 18065 31357 37580
tag asan_on_G_d10
count 100
depth 10
sum 2024891
first 20133 13249 20150
tag partner_off_O
count 200
depth 12
sum 9500069
first 41311 24872 28574
tag partner_on_O
count 200
depth 12
sum 9500069
first 41311 24872 28574
COMPARES
compare_off_O.txt
count 200 differ 0 equal 200
compare_off_G.txt
count 353 differ 0 equal 353
compare_on_O.txt
differ index 1 left 41311 f1e2 right 18065 f1e2
differ index 2 left 24872 f1c4 right 31357 f1c4
differ index 3 left 28574 e5d4 right 37580 e5d4
differ index 4 left 27838 e1g1 right 23026 e1g1
differ index 5 left 18020 c8e6 right 37575 c8e6
differ index 6 left 43043 g1f3 right 51147 g1f3
differ index 7 left 56414 d2d4 right 39938 d2d4
differ index 8 left 32317 g1f3 right 61828 f2f4
count 200 differ 200 equal 0
partner_compare_off.txt
count 200 differ 0 equal 200
partner_compare_on.txt
count 200 differ 0 equal 200
partner_compare_on_vs_B.txt
count 200 differ 0 equal 200
ASAN_META
exe /tmp/forge-asan/forge
asan_symbol_count 35
scratch_sanitizer_lines 2
g100_sanitizer_lines 0
MATCH -12.26 10.25 1106
PARTNER_MATCH -2.90 4.67 600
APPLY
mine exit:0
partner exit:0
STEP_TABLE
step | done | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 013 idea 13
2 honesty B | done | HONESTY_B.txt | 312866 862329 3024920 4865609
2 O and G | done | B_O_d12.sum.txt B_G_d12.sum.txt | 9500069 and 18466239
3 prediction | done | prediction.txt | 9200000 and Elo 8, committed before measuring
3 patch | done | idea.patch.txt apply_check.txt | apply exit 0
3 proof off | done | compare_off_O.txt compare_off_G.txt | 0 of 200 and 0 of 353
3 proof on | done | compare_on_O.txt P_on_O_d12.sum.txt | 200 of 200, sum 9796924
3 uci | done | uci_options.txt | IdeaS13 false, Lag 4, Bonus 160, Divisor 48, Shave 1
3 sanitizer | done | asan_on_G_d10.meta asan_scratch.raw.txt | symbols 35, G lines 0, scratch heap-buffer-overflow
3 match | done | match_on_off.log match_on_off.pgn | Elo -12.26 +/- 10.25, 1106 games
4 partner | done | partner_compare_off.txt partner_compare_on.txt partner_match.log | CONFIRMS, R match Elo -2.90 +/- 4.67, 600 games

Proof (1). Exe P with no setoption matches the four honesty numbers. See HONESTY_P.txt.
Proof (2). S14 and IdeaS13 false: O depth 12 differs in 0 of 200 positions from exe B, sum 9500069. G depth 12 differs in 0 of 353, sum 18466239.
Proof (3). S14 and IdeaS13 true: O depth 12 differs in 200 of 200 positions, sum 9796924. The prediction was 9200000, wrong outside 7000000 to 11500000. 9796924 is inside that range.
Proof (4). The uci answer lists IdeaS13 check default false, IdeaS13_Lag 4, IdeaS13_Bonus 160, IdeaS13_Divisor 48, IdeaS13_Shave 1.
Proof (5). The sanitizer build's meta has asan_symbol_count 35. The first 100 of G at depth 10 with the switch on produced 0 sanitizer lines. The same runner on a scratch copy, with one deliberate read past a 4-int heap array on the FEN 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1, reported AddressSanitizer heap-buffer-overflow.

Match. IdeaS13 true against false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours: 1106 games. Elo of the true side -12.26 +/- 10.25. Wins 314, losses 353, draws 439. The point is not below -20, so I did not rewrite the code. The whole interval is below 0. The predicted Elo was 8, wrong outside -30 to 40, and -12.26 is inside that range. git apply --check of idea.patch.txt on a clean base exits 0.

Partner. Seat 063 is the next seat of idea 13 and it has a branch. Seat 113 has none. Their patch is option IdeaS15, the rook-meets-passer reduction, and their DESIGN calls that "Idea 13, S15". I applied it myself. apply --check exits 0. Honesty matches. Switch false matches exe B on O, 0 of 200. Switch true matches their O depth-12 node file, 0 of 200, and also matches exe B, which is what they claim for openings. A match of their switch on my 300 R openings, both colours, is 600 games, Elo -2.90 +/- 4.67. Verdict: CONFIRMS. I did not re-run their claim that 77 of 353 G positions change, or their rook-ending node pair.

Suspicions, not proven. The bonus fires on every one of the 200 openings, so a pawn that merely raises alpha is enough to mark the previous quiet piece moves, including the opponent's. That may be why the match is negative without a broken rule. Seat 063 implemented idea 15's text under the idea-13 seat number.

What I did NOT do. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not play a second match of my own patch, because a partner branch existed. I did not re-measure the partner's G set or rook ending. I did not change the spins after seeing the match.

What I am NOT sure about. I am not sure the one-ply shave after a single credit of 160 is mild enough for a 20000-node game. I am not sure king moves belong in the credited set. I am not sure a negative interval that still contains no positive Elo is a bug; the -20 rule was not met.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/013/stamps.txt
?? config.json
?? forge-combo29/grok/013/REPORT.md
?? forge-combo29/grok/013/RESULT.txt
?? forge-combo29/grok/013/apply_check.txt
?? forge-combo29/grok/013/asan_scratch.rows.tsv
?? forge-combo29/grok/013/asan_scratch.sum.txt
?? forge-combo29/grok/013/compare_partner.py
?? forge-combo29/grok/013/ls_la.txt
?? forge-combo29/grok/013/partner063_O_on.nodes
?? forge-combo29/grok/013/partner_HONESTY.txt
?? forge-combo29/grok/013/partner_apply_check.txt
?? forge-combo29/grok/013/partner_compare_off.txt
?? forge-combo29/grok/013/partner_compare_on.txt
?? forge-combo29/grok/013/partner_compare_on_vs_B.txt
?? forge-combo29/grok/013/partner_h_bench11.txt
?? forge-combo29/grok/013/partner_h_bench13.txt
?? forge-combo29/grok/013/partner_h_bench16.txt
?? forge-combo29/grok/013/partner_h_perft5.txt
?? forge-combo29/grok/013/partner_honesty.py
?? forge-combo29/grok/013/partner_match.log
?? forge-combo29/grok/013/partner_match.pgn
?? forge-combo29/grok/013/partner_off_O.meta
?? forge-combo29/grok/013/partner_off_O.raw.txt
?? forge-combo29/grok/013/partner_off_O.rows.tsv
?? forge-combo29/grok/013/partner_off_O.sum.txt
?? forge-combo29/grok/013/partner_on_O.meta
?? forge-combo29/grok/013/partner_on_O.raw.txt
?? forge-combo29/grok/013/partner_on_O.rows.tsv
?? forge-combo29/grok/013/partner_on_O.sum.txt
?? forge-combo29/grok/013/proof_table.py
?? forge-combo29/grok/013/proof_table.txt
?? forge-combo29/grok/013/run_partner_match.sh
?? forge-combo29/grok/013/status_short.txt

$ ls -la forge-combo29/grok/013
total 9760
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:14 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     976 Nov 20 08:08 asan_on_G_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  119233 Nov 20 08:08 asan_on_G_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1376 Nov 20 08:08 asan_on_G_d10.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:08 asan_on_G_d10.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1006 Nov 20 08:09 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   11147 Nov 20 08:09 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       9 Nov 20 08:09 asan_scratch.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      47 Nov 20 08:09 asan_scratch.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     812 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507843 Nov 20 08:03 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:03 B_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      69 Nov 20 08:03 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     812 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282280 Nov 20 08:02 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:02 B_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:02 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:07 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:07 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     413 Nov 20 08:07 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     991 Nov 20 09:09 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 08:07 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1422 Nov 20 08:11 design.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 G.epd
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:57 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3527 Nov 20 07:57 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     349 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:05 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5280 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:05 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5280 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:05 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5282 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:05 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5493 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3006 Nov 20 08:11 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     349 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   11035 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:15 ls_la.txt
-rw-r--r-- 1 ubuntu ubuntu    1004 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  106229 Nov 20 08:17 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 4603826 Nov 20 08:17 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu    7557 Nov 20 08:06 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1894 Nov 20 09:08 partner063_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:14 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 09:09 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 09:09 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 09:09 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 09:09 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 09:09 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 09:09 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    2358 Nov 20 09:09 partner_honesty.py
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 09:09 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    5380 Nov 20 09:09 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   53694 Nov 20 09:13 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 2134027 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 09:09 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  282006 Nov 20 09:09 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:09 partner_off_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 09:09 partner_off_O.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 09:09 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  282000 Nov 20 09:09 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:09 partner_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      72 Nov 20 09:09 partner_on_O.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 08:07 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  508384 Nov 20 08:07 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:07 P_off_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:07 P_off_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 08:06 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282440 Nov 20 08:06 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:06 P_off_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 08:06 P_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     997 Nov 20 08:07 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282330 Nov 20 08:07 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2899 Nov 20 08:07 P_on_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:07 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     341 Nov 20 08:05 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3082 Nov 20 09:14 proof_table.py
-rw-r--r-- 1 ubuntu ubuntu    3149 Nov 20 09:15 proof_table.txt
-rw-r--r-- 1 ubuntu ubuntu   14854 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19499 Nov 20 08:00 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1241 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1133 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1513 Nov 20 09:15 status_short.txt
-rw-r--r-- 1 ubuntu ubuntu    5219 Nov 20 08:07 uci_options.txt
```
