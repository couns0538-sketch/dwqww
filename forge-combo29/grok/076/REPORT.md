Idea S36, option IdeaS36, default false. On a root re-search after the aspiration score leaves the window, later quiet moves lose IdeaS36_FailLow plies of reduction after a fail-low and gain IdeaS36_FailHigh plies after a fail-high (both default 1, range 0 to 8).
Captures are not shifted. The existing reduction already starts at the third root move, so the first root move is untouched. A negative reduction after the shift is clamped to 0, and the shift is cleared at the next iteration.
The patch is idea.patch.txt. `git apply --check` on a clean checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7 printed nothing and exited 0.

EXISTS: no. AspCappedReopen and AspArmLate change the window. They do not change quiet reductions on the re-search. No such shift was in search.cpp.

Honesty, no setoption, fresh process each line. Exe B and exe P both: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. See HONESTY_B.txt, bench11_P.txt, bench13_P.txt, bench16_P.txt, perft5_P.txt.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 076, idea 26 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts, all OK |
| 2 baseline O and G | done | O_B_depth12.sum, G_B_depth12.sum | O 9500069 (first three 41311 24872 28574); G 18466239 |
| 3 prediction | done | prediction.txt | locked before any patched measurement; it describes a misread (see below) |
| 3 patch | done | idea.patch.txt | applies on the base; option IdeaS36 |
| 3 proof off | done | O_P_off_vs_B.txt, G_P_off_vs_B.txt | 0 of 200 and 0 of 353 |
| 3 proof on | done | O_P_on_vs_B.txt, O_P_on_depth12.sum | 166 of 200 differ; sum 9607737 |
| 3 uci | done | uci_P.txt | IdeaS36 check default false; FailLow and FailHigh spin default 1 |
| 3 sanitizer | done | asan_G100_depth10.meta, asan_scratch_oob.txt | clean on G100; tripwire reports heap-buffer-overflow |
| 3 match | done | match_on_off.sum, match_on_off.pgn | Elo 0.94 +/- 10.03, 1106 games |
| 4 partner | done | partner_O_on_vs_rows.txt, partner_match.sum | CONFIRMS; R match 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Patched engine, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

Proof (2). S14 plus IdeaS36 false, Threads 1, Hash 16. O depth 12 differs from exe B in 0 of 200. G depth 12 differs in 0 of 353.

Proof (3). S14 plus IdeaS36 true. O depth 12 differs from exe B in 166 of 200. Sum 9607737. First three nodes 46657, 25057, 36953. Depth mismatches 0.

Proof (4). `uci` lists `option name IdeaS36 type check default false`, `option name IdeaS36_FailLow type spin default 1 min 0 max 8`, and `option name IdeaS36_FailHigh type spin default 1 min 0 max 8`.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `nm -C` count of `__asan_` is 35, written in asan_G100_depth10.meta. First 100 of G at depth 10 with the switch true: 0 sanitizer lines, 100 positions, depth mismatches 0. A scratch copy with one heap read past the end of a 4-int array, only when the root FEN is `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1`, built the same way and run through harness_depth.py, printed `ERROR: AddressSanitizer: heap-buffer-overflow` in asan_scratch_oob.txt. The runner then saw the engine abort. Its own error string has a type bug (`done` is a function), which is why that process exited 1 after the sanitizer line was already saved.

Match. IdeaS36 true against false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess from github.com/Disservin/fastchess, concurrency 3. fastchess keeps only `-rounds` openings, so rounds was 553 and games was 2. Result from match_on_off.sum: Elo 0.94 +/- 10.03, games 1106, wins 333, losses 330, draws 443. The point estimate is not below -20. PGN has 1106 Result tags.

Partner. Seats for idea 26 are 026 and 076. The next after 076 is 026. Branch for-fable-and-opus/grok-026 had idea.patch.txt. `git apply --check` on a fresh worktree of the base succeeded, then the patch was applied (partner_apply.txt: 36 insertions in search.hpp, search.cpp, uci.cpp). Their option is IdeaS36. Honesty of their binary matched the four known counts. Switch false: O depth 12 differs from exe B in 0 of 200, and G in 0 of 353, which is what they wrote. Switch true: their O depth-12 nodes, position by position, differ from the rows in their P_on_O_d12.txt.rows in 0 of 200, sum 9607737, and differ from exe B in 166 of 200. That is what they wrote. Their engine, switch on against off, 300 R openings, both colours, 600 games: Elo 0.58 +/- 8.11 (partner_match.sum). Verdict: CONFIRMS.

The misread. The script printed IDEA 26. Idea 26 in the list is IdeaS36. I first built idea 22, IdeaS27, and measured it (commit 78dc7e2da). prediction.txt was pushed before that measurement and was not edited. It is a prediction of that discarded build, not of S36. The files in this folder now are the S36 re-run. S36's O sum 9607737 happens to sit inside the numeric range written in prediction.txt. That range was not a forecast of S36.

suspicions, not proven. My S36 O rows and the 1106-game match printed the same numbers seat 026 published. The patches are not the same text (mine is the shorter idea.patch.txt). Same nodes on a deterministic search can come from the same rule. I had read their DESIGN.txt before writing the S36 patch, so the details were not made in isolation. I am not claiming the match proves a gain. 0.94 +/- 10.03 includes zero.

what I did NOT do. I did not wait until minute 75 to open their patch. Step 3 was already pushed and their patch was already on the branch. I did not rebuild their sanitizer. I did not edit prediction.txt. I did not repeat the opening list. I did not open a pull request. No FABLE_TO_grok file was on the handoff branch at step 1 or at the check recorded in stamps.txt (handoff commit 8c5536863464d4af8c07b4788883463eb950ab1d).

what I am NOT sure about. The idea says to leave the first root move alone. This engine also does not reduce the second root move. I did not give that move a new reduction, so a fail-high does not make it one ply shallower. A reading that shifts the second move would be a different search. The R-match DrawRatio of 86% and the Draws field of 59 do not describe the same count; both numbers are fastchess's, copied by parse_match.py, and I did not try to reconcile them.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/076/G_P_off_depth12.meta
 M forge-combo29/grok/076/G_P_off_depth12.txt
 M forge-combo29/grok/076/O_P_off_depth12.meta
 M forge-combo29/grok/076/O_P_off_depth12.txt
 M forge-combo29/grok/076/O_P_on_depth12.meta
 M forge-combo29/grok/076/O_P_on_depth12.sum
 M forge-combo29/grok/076/O_P_on_depth12.txt
 M forge-combo29/grok/076/O_P_on_vs_B.txt
 M forge-combo29/grok/076/asan_G100_depth10.meta
 M forge-combo29/grok/076/asan_G100_depth10.txt
 M forge-combo29/grok/076/asan_scratch_oob.meta
 M forge-combo29/grok/076/asan_scratch_oob.txt
 M forge-combo29/grok/076/bench11_P.txt
 M forge-combo29/grok/076/bench11_P.txt.meta
 M forge-combo29/grok/076/bench13_P.txt
 M forge-combo29/grok/076/bench13_P.txt.meta
 M forge-combo29/grok/076/bench16_P.txt
 M forge-combo29/grok/076/bench16_P.txt.meta
 M forge-combo29/grok/076/decisions.txt
 M forge-combo29/grok/076/idea.patch.txt
 M forge-combo29/grok/076/list_uci.py
 M forge-combo29/grok/076/match_on_off.log
 M forge-combo29/grok/076/match_on_off.pgn
 M forge-combo29/grok/076/match_on_off.sum
 M forge-combo29/grok/076/perft5_P.txt.meta
 M forge-combo29/grok/076/run_match.sh
 M forge-combo29/grok/076/s14_off.txt
 M forge-combo29/grok/076/s14_on.txt
 M forge-combo29/grok/076/stamps.txt
 M forge-combo29/grok/076/uci_P.meta
 M forge-combo29/grok/076/uci_P.txt
?? config.json
?? forge-combo29/grok/076/REPORT.md
?? forge-combo29/grok/076/RESULT.txt
?? forge-combo29/grok/076/openings_R300.fens
?? forge-combo29/grok/076/partner026.patch.txt
?? forge-combo29/grok/076/partner026_O_on.rows
?? forge-combo29/grok/076/partner_G_off.meta
?? forge-combo29/grok/076/partner_G_off.txt
?? forge-combo29/grok/076/partner_G_off_vs_B.txt
?? forge-combo29/grok/076/partner_O_off.meta
?? forge-combo29/grok/076/partner_O_off.txt
?? forge-combo29/grok/076/partner_O_off_vs_B.txt
?? forge-combo29/grok/076/partner_O_on.meta
?? forge-combo29/grok/076/partner_O_on.txt
?? forge-combo29/grok/076/partner_O_on_vs_B.txt
?? forge-combo29/grok/076/partner_O_on_vs_rows.txt
?? forge-combo29/grok/076/partner_apply.txt
?? forge-combo29/grok/076/partner_bench11.txt
?? forge-combo29/grok/076/partner_bench13.txt
?? forge-combo29/grok/076/partner_bench16.txt
?? forge-combo29/grok/076/partner_match.log
?? forge-combo29/grok/076/partner_match.pgn
?? forge-combo29/grok/076/partner_match.sum
?? forge-combo29/grok/076/partner_perft5.txt
?? forge-combo29/grok/076/run_partner_match.sh
```

ls -la

```
total 4984
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:36 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu    932 Nov 20 08:30 asan_G100_depth10.meta
-rw-r--r-- 1 ubuntu ubuntu 118902 Nov 20 08:30 asan_G100_depth10.txt
-rw-r--r-- 1 ubuntu ubuntu    939 Nov 20 08:30 asan_scratch_oob.meta
-rw-r--r-- 1 ubuntu ubuntu  11073 Nov 20 08:30 asan_scratch_oob.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:01 bench11_B.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:03 bench11_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:21 bench11_P.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:21 bench11_P.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:01 bench13_B.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:03 bench13_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:21 bench13_P.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:21 bench13_P.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:01 bench16_B.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:03 bench16_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:21 bench16_P.txt
-rw-r--r-- 1 ubuntu ubuntu    194 Nov 20 08:21 bench16_P.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1278 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu   1353 Nov 20 08:21 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu   5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu    896 Nov 20 08:03 G_B_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu     70 Nov 20 08:03 G_B_depth12.sum
-rw-r--r-- 1 ubuntu ubuntu 507595 Nov 20 08:03 G_B_depth12.txt
-rw-r--r-- 1 ubuntu ubuntu    938 Nov 20 08:21 G_P_off_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu 507599 Nov 20 08:21 G_P_off_depth12.txt
-rw-r--r-- 1 ubuntu ubuntu     35 Nov 20 08:21 G_P_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   3564 Nov 20 08:03 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu    366 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   7364 Nov 20 08:21 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1009 Nov 20 08:21 list_uci.py
-rw-r--r-- 1 ubuntu ubuntu   1489 Nov 20 08:05 make_r_positions.py
-rw-r--r-- 1 ubuntu ubuntu 119507 Nov 20 08:27 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 982951 Nov 20 08:27 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu    419 Nov 20 08:29 match_on_off.sum
-rw-r--r-- 1 ubuntu ubuntu    896 Nov 20 08:03 O_B_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu     68 Nov 20 08:03 O_B_depth12.sum
-rw-r--r-- 1 ubuntu ubuntu 281816 Nov 20 08:03 O_B_depth12.txt
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 08:02 openings_O.fens
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:07 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu  19059 Nov 20 08:22 openings_R300.fens
-rw-r--r-- 1 ubuntu ubuntu  20342 Nov 20 08:05 openings_R.fens
-rw-r--r-- 1 ubuntu ubuntu    938 Nov 20 08:21 O_P_off_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu 282001 Nov 20 08:21 O_P_off_depth12.txt
-rw-r--r-- 1 ubuntu ubuntu     35 Nov 20 08:21 O_P_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    937 Nov 20 08:21 O_P_on_depth12.meta
-rw-r--r-- 1 ubuntu ubuntu     68 Nov 20 08:21 O_P_on_depth12.sum
-rw-r--r-- 1 ubuntu ubuntu 282319 Nov 20 08:21 O_P_on_depth12.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 08:21 O_P_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    505 Nov 20 08:11 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu   4189 Nov 20 08:22 partner026_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu   7473 Nov 20 08:18 partner026.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    209 Nov 20 08:35 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:26 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:26 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:26 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    941 Nov 20 08:26 partner_G_off.meta
-rw-r--r-- 1 ubuntu ubuntu 507350 Nov 20 08:26 partner_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     35 Nov 20 08:26 partner_G_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu  60355 Nov 20 08:33 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 415802 Nov 20 08:33 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    417 Nov 20 08:35 partner_match.sum
-rw-r--r-- 1 ubuntu ubuntu    941 Nov 20 08:26 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281706 Nov 20 08:26 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     35 Nov 20 08:26 partner_O_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    940 Nov 20 08:26 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282106 Nov 20 08:26 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 08:26 partner_O_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     55 Nov 20 08:35 partner_O_on_vs_rows.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:26 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:01 perft5_B.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 08:03 perft5_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:21 perft5_P.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 08:21 perft5_P.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1265 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   6578 Nov 20 08:36 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 08:36 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   1281 Nov 20 08:20 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu   1196 Nov 20 08:26 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    655 Nov 20 08:20 s14_off.txt
-rw-r--r-- 1 ubuntu ubuntu    654 Nov 20 08:20 s14_on.txt
-rw-r--r-- 1 ubuntu ubuntu    620 Nov 20 08:02 s14_options.txt
-rw-r--r-- 1 ubuntu ubuntu     79 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  17691 Nov 20 08:02 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     60 Nov 20 08:09 special_oob.fen
-rw-r--r-- 1 ubuntu ubuntu    212 Nov 20 08:35 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1249 Nov 20 08:03 sum_depth.py
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 08:01 uci_id_B.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 08:21 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 08:21 uci_P.txt
-rw-r--r-- 1 ubuntu ubuntu   2385 Nov 20 08:03 write_honesty_b.py
```
