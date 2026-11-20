IdeaS15 searches a rook move that meets a passed pawn at full depth in a rook ending, and it does not add an extension or an eval term.
The UCI check IdeaS15 defaults to false. The spin IdeaS15_MinPieces defaults to 8 (range 2 to 32) and is the piece count, kings included.
With the check false the predicate is not called, so the reduction is the plain engine's reduction.

EXISTS: no. In forge-combo29/src/search.cpp the late-move reduction has other optional terms, and none of them drops the reduction because a rook move meets a passer.

Honesty, no setoption, exe B (HONESTY_B.txt) and exe P (HONESTY_P.txt), both PASS:
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 067, idea 17, IdeaS15 |
| 2 honesty B | done | HONESTY_B.txt | PASS, the four node counts above |
| 2 O and G depth 12 on B | done | SUMS_B.txt | O sum 9500069 first 41311 24872 28574; G sum 18466239 |
| 3 prediction | done | prediction.txt | O on sum 9500069; match Elo 3, wrong outside an interval entirely below -25 or entirely above 35 |
| 3 patch | done | idea.patch.txt, APPLY_CHECK.txt | git apply --check printed APPLY_CHECK_OK |
| 3 proof off | done | cmp_O_off.txt, cmp_G_off.txt | O 0 of 200 differ; G 0 of 353 differ |
| 3 proof on | done | cmp_O_on.txt, cmp_G_on.txt | O 0 of 200 differ; G 82 of 353 differ |
| 3 uci options | done | uci_P.txt | IdeaS15 check default false; IdeaS15_MinPieces spin default 8 min 2 max 32 |
| 3 sanitizer | done | asan_nm.txt, asan_clean_count.txt, asan_bug_runner.txt | nm __asan_ count 35; clean search 0 sanitizer lines; bug run printed the runtime error |
| 3 match | done | match_result.txt | Elo -3.14 +/- 6.39, 1106 games |
| 4 partner 017 | done | partner_apply_check.txt, HONESTY_PARTNER.txt, partner_cmp_off.txt, partner_cmp_on.txt, partner_match_result.txt | CONFIRMS; R match Elo -1.16 +/- 3.93, 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). HONESTY_P.txt: bench 11 got 312866, bench 13 got 862329, bench 16 got 3024920, perft 5 got 4865609. PASS. No setoption.

Proof (2). S14 then IdeaS15 false, Threads 1, Hash 16. compare_nodes.py: cmp_O_off.txt says N 200 DIFFER 0 SAME 200. cmp_G_off.txt says N 353 DIFFER 0 SAME 353. read_sums.py: O_d12_P_off sum 9500069, G_d12_P_off sum 18466239, the same sums as exe B.

Proof (3). IdeaS15 true on the same 200 openings: cmp_O_on.txt says N 200 DIFFER 0 SAME 200, sum 9500069. That is 0 of 200. The 200 openings contain no rook ending (no queen, bishop or knight, at least one rook, 8 or more pieces), so the gate does not change those trees at depth 12. The same switch on set G changes the search: cmp_G_on.txt says N 353 DIFFER 82 SAME 271, and the sum moves from 18466239 to 18629385. The code runs. It does not run inside those 200 depth-12 trees.

Proof (4). uci_P.txt lists `option name IdeaS15 type check default false` and `option name IdeaS15_MinPieces type spin default 8 min 2 max 32`.

Proof (5). The AddressSanitizer and UndefinedBehaviorSanitizer build of the patched engine has nm -C | grep -c __asan_ = 35 (asan_nm.txt). measure_depth.py on the first 100 of G at depth 10 with IdeaS15 true wrote asan_G100.txt, and asan_clean_count.txt says sanitizer_lines=0. A scratch copy with one deliberate read past a 4-int heap array on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1, built the same way and run through measure_depth.py, printed `/tmp/asan-bug-src/src/uci.cpp:46:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'` (asan_bug_runner.txt). Its nm count is also 35.

Match. exe P with IdeaS15 true against exe P with IdeaS15 false. S14, Threads 1, Hash 16, 20000 nodes, OwnBook false, openings O then G (553), both colours, 1106 games, concurrency 3. match_result.txt:
Elo: -3.14 +/- 6.39, games 1106, wins 332, losses 342, draws 432. The point is not below -20 and the interval is not entirely below 0, so the match did not trigger the one look for a code mistake. The O-sum prediction 9500069 was the measured sum. The Elo guess of +3 is inside an interval that is not entirely below -25 and not entirely above 35.

Partner. Seats for idea 17 are 017, 067 and 117. This seat is 067. 117 had no branch at minute 75. The next seat after 067 that had a branch is 017. partner_017.patch.txt applied on a fresh base worktree: partner_apply_check.txt says APPLY_CHECK_OK. Honesty of that build PASS with the same four node counts, and the sha256 364f47e6d00affa06ce4eb0438072528a62b90c407324e590957a286b926fb16 is the sha256 seat 017 published in its HONESTY_P.txt. Switch false against exe B: partner_cmp_off.txt says N 200 DIFFER 0 SAME 200. Switch true against seat 017's own O depth-12 rows: partner_cmp_on.txt says N 200 DIFFER 0 SAME 200, both sums 9500069. They claimed those proofs. They hold. The extra match of their switch on 300 R openings, both colours, 600 games: partner_match_result.txt says Elo -1.16 +/- 3.93, wins 264, losses 266, draws 70. Verdict: CONFIRMS.

suspicions, not proven
A rook that is already on the passer file is also searched at full depth, because reaching the file costs 0 moves and the pawn's next step costs 1 or 2. The match does not separate those moves from a rook that steps onto the file. I do not know which of the two is carrying the -3 Elo.
Seat 017 requires exactly one rook on each side. This seat allows more than one rook when there is still no queen, bishop or knight. The two patches are not the same gate. I did not play them against each other.

what I did NOT do
I did not change the patch after the match. The result was not below -20 with the interval below 0.
I did not repeat the 1106-game book.
I did not search set G at depth 12 with seat 017's binary.
I did not run the 1106-game match under a sanitizer.
I did not review seat 117. It had no branch.
I did not open a pull request.

what I am NOT sure about
I am not sure the idea should treat a rook that is already on the file the same as a rook that moves onto the file.
I am not sure both colours' passed pawns should count.
I am not sure the -3.14 Elo is a real loss. The interval includes positive values.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/067/compare_nodes.py
 M forge-combo29/grok/067/config.json
 M forge-combo29/grok/067/stamps.txt
?? forge-combo29/grok/067/HONESTY_PARTNER.txt
?? forge-combo29/grok/067/PARTNER_bench11.meta
?? forge-combo29/grok/067/PARTNER_bench11.txt
?? forge-combo29/grok/067/PARTNER_bench13.meta
?? forge-combo29/grok/067/PARTNER_bench13.txt
?? forge-combo29/grok/067/PARTNER_bench16.meta
?? forge-combo29/grok/067/PARTNER_bench16.txt
?? forge-combo29/grok/067/PARTNER_perft5.meta
?? forge-combo29/grok/067/PARTNER_perft5.txt
?? forge-combo29/grok/067/REPORT.md
?? forge-combo29/grok/067/RESULT.txt
?? forge-combo29/grok/067/match_partner_R.log
?? forge-combo29/grok/067/match_partner_R.pgn
?? forge-combo29/grok/067/match_partner_r.sh
?? forge-combo29/grok/067/parse_bestmove_nodes.py
?? forge-combo29/grok/067/partner_017.patch.txt
?? forge-combo29/grok/067/partner_O_off.meta
?? forge-combo29/grok/067/partner_O_off.nodes
?? forge-combo29/grok/067/partner_O_off.txt
?? forge-combo29/grok/067/partner_O_on.meta
?? forge-combo29/grok/067/partner_O_on.nodes
?? forge-combo29/grok/067/partner_O_on.txt
?? forge-combo29/grok/067/partner_apply_check.txt
?? forge-combo29/grok/067/partner_claimed_O_on.nodes
?? forge-combo29/grok/067/partner_cmp_off.txt
?? forge-combo29/grok/067/partner_cmp_on.txt
?? forge-combo29/grok/067/partner_match_result.txt
?? forge-combo29/grok/067/partner_sums.txt

$ ls -la forge-combo29/grok/067
total 8672
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:08 APPLY_CHECK.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:08 asan_bug.fen
-rw-r--r-- 1 ubuntu ubuntu     950 Nov 20 08:10 asan_bug.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:09 asan_bug_nm.txt
-rw-r--r-- 1 ubuntu ubuntu     466 Nov 20 08:09 asan_bug_runner.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 asan_bug.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:10 asan_clean_count.txt
-rw-r--r-- 1 ubuntu ubuntu     949 Nov 20 08:10 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    1372 Nov 20 08:09 asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu  113164 Nov 20 08:09 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:09 asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 07:58 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 07:58 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 07:58 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 08:08 cmp_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     434 Nov 20 08:08 cmp_G_on.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 08:08 cmp_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 08:08 cmp_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     952 Nov 20 09:12 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    7081 Nov 20 09:14 config.json
-rw-r--r-- 1 ubuntu ubuntu    1514 Nov 20 08:08 design.txt
-rw-r--r-- 1 ubuntu ubuntu     616 Nov 20 08:17 extract_last_result.py
-rw-r--r-- 1 ubuntu ubuntu     897 Nov 20 08:01 G_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:01 G_d12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  500172 Nov 20 08:01 G_d12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     939 Nov 20 08:05 G_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:05 G_d12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  500086 Nov 20 08:05 G_d12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 08:05 G_d12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    5195 Nov 20 08:05 G_d12_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  500197 Nov 20 08:05 G_d12_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    2899 Nov 20 08:04 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     338 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     347 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     338 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6634 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     500 Nov 20 08:07 make_openings_og.py
-rw-r--r-- 1 ubuntu ubuntu    1240 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  138709 Nov 20 08:15 match_OG.log
-rw-r--r-- 1 ubuntu ubuntu 3664713 Nov 20 08:15 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu    1071 Nov 20 08:08 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu   73111 Nov 20 09:14 match_partner_R.log
-rw-r--r-- 1 ubuntu ubuntu 1522842 Nov 20 09:14 match_partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu    1081 Nov 20 09:11 match_partner_r.sh
-rw-r--r-- 1 ubuntu ubuntu     354 Nov 20 08:17 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu    6625 Nov 20 08:07 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu     897 Nov 20 08:01 O_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:01 O_d12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  275413 Nov 20 08:01 O_d12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     939 Nov 20 08:05 O_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:05 O_d12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  275340 Nov 20 08:05 O_d12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 08:05 O_d12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:05 O_d12_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  275383 Nov 20 08:05 O_d12_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     865 Nov 20 09:11 parse_bestmove_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    7236 Nov 20 09:11 partner_017.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:11 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 09:11 PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 09:11 PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 09:12 PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    2094 Nov 20 09:12 partner_claimed_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:12 partner_cmp_off.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:12 partner_cmp_on.txt
-rw-r--r-- 1 ubuntu ubuntu     341 Nov 20 09:17 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu     942 Nov 20 09:12 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:12 partner_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  275373 Nov 20 09:12 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     941 Nov 20 09:12 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:12 partner_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  275367 Nov 20 09:12 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 09:12 PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 09:12 partner_sums.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:05 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:05 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:05 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 07:58 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:05 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     687 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     633 Nov 20 08:03 read_sums.py
-rw-r--r-- 1 ubuntu ubuntu   19087 Nov 20 08:08 R.epd
-rw-r--r-- 1 ubuntu ubuntu    7740 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     114 Nov 20 08:03 SUMS_B.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:07 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:08 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 08:08 uci_P.txt
```
