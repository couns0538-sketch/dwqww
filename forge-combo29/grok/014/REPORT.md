# Seat 014, idea 14, IdeaS5

Idea S5 orders quiet piece moves that raise the evaluation ahead of pawn breaks, and reduces those moves less, when a one-ply search of captures and checks stays near the quiet eval.
The switch is IdeaS5, a check option, default false. The spins are IdeaS5_Margin 40, IdeaS5_Less 1, IdeaS5_MinDepth 4, and IdeaS5_Order 80000.
With the switch false the probe is not run. With it true, a nothing-to-play node gives those piece moves an order bonus and one ply less late-move reduction. Pawn moves stay in the list.

EXISTS: no. src/search.cpp has no probe of this kind. The patch is forge-combo29/grok/014/idea.patch.txt. git apply --check on a fresh checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0 (apply_check.txt).

Honesty, no setoption, fresh process each line. Exe B and exe P both printed the known counts: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Raw lines are in HONESTY_B.txt, bench11_B.txt, bench13_B.txt, bench16_B.txt, perft5_B.txt, and the matching _P files. proofs.py prints the same lines into proofs.txt.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt stamps.txt | seat 014 idea 14 |
| 2 honesty B | done | HONESTY_B.txt | 312866, 862329, 3024920, 4865609 |
| 2 O and G on B | done | O_d12_B.txt G_d12_B.txt | 9500069 and 18466239 |
| 3 prediction | done | prediction.txt | committed before any patched measurement |
| 3 patch | done | idea.patch.txt apply_check.txt | applies, exit 0 |
| 3 proof 1 | done | bench11_P.txt bench13_P.txt bench16_P.txt perft5_P.txt | same four counts |
| 3 proof 2 | done | O_d12_P_off.txt G_d12_P_off.txt | 0 of 200 and 0 of 353 differ from B |
| 3 proof 3 | done | O_d12_P_on.txt | 200 of 200 differ, sum 9620456 |
| 3 proof 4 | done | uci_P.txt | IdeaS5 false, four spins at the defaults above |
| 3 proof 5 | done | asan_G100_d10.meta asan_bug_special.txt.log | nm count 35, clean 0 errors, bug run reports the overflow |
| 3 match | done | match_fastchess.txt | Elo -3.14 +/- 10.12, 1106 games |
| 4 partner | done | partner_O_on.txt partner_match.txt | seat 064, rows match, CONFIRMS |
| 5 report | done | REPORT.md RESULT.txt | this file |

Proof (1). No setoption. P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

Proof (2). S14 and IdeaS5 false. O depth 12: differ 0 of 200, sum 9500069, first three 41311 / 24872 / 28574. G depth 12: differ 0 of 353, sum 18466239. Same rows as exe B.

Proof (3). S14 and IdeaS5 true. O depth 12 sum 9620456. Differ 200 of 200 from exe B. The code runs. Prediction was 11200000, wrong outside 7500000..18000000. 9620456 is inside that range.

Proof (4). uci lists `option name IdeaS5 type check default false` and IdeaS5_Margin 40, IdeaS5_Less 1, IdeaS5_MinDepth 4, IdeaS5_Order 80000.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS5 true, first 100 of G at depth 10. asan_G100_d10.meta has nm_asan_count=35. The log has 0 lines containing `ERROR: AddressSanitizer` or `ERROR: UndefinedBehaviorSanitizer`. A scratch copy with one heap read past a 4-int array, only on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, built the same way and run through search_sum.py, wrote `ERROR: AddressSanitizer: heap-buffer-overflow` into asan_bug_special.txt.log. Sanitizer result: clean.

Match. IdeaS5 true versus false, both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G (553), both colours, concurrency 3. match_fastchess.txt ends with: Elo: -3.14 +/- 10.12, Games: 1106, Wins: 320, Losses: 330, Draws: 456. The interval is about -13.3 to +7.0, so it is not entirely below 0. No second look for a code mistake. Prediction was +8 Elo, wrong outside -60..+60. -3.14 is inside that range.

Partner. Next seat with this idea number and a branch is 064. 114 had no branch at 2026-11-20T09:08:35Z. Their patch applies on a fresh base. Their published option is IdeaS6, not IdeaS5. Honesty of that build: 312866, 862329, 3024920, 4865609. IdeaS6 false: O depth 12 differs 0 of 200 from exe B, sum 9500069. IdeaS6 true: O depth 12 differs 0 of 200 from their P_on_O.nodes.txt, sum 9749922, which is the sum they wrote. My R match of their switch, 300 openings, both colours: Elo: -4.63 +/- 10.14, Games: 600 (partner_match.txt). Verdict: CONFIRMS. The node proofs they published are the rows I measured. I did not replay their 1106-game match.

suspicions, not proven. The probe uses the hand-crafted eval, not the network eval the search stores, so a move can "raise the eval" for the probe and not for the net. The SEE pre-screen treats a capture that wins more than the margin as something to play and skips the eval probe. Seat 064's DECISIONS.txt calls idea 14 "S6"; the list in the brief gives idea 14 the id S5. Their measurements still match the IdeaS6 patch they published.

what I did NOT do. No G depth-12 run with IdeaS5 true. No match at other spin values. No replay of seat 064's 1106-game book. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. Seat 114 did not exist.

what I am NOT sure about. Whether a one-ply hand-crafted probe is the shallow search the idea text describes. Whether king moves should count as the piece moves. fastchess printed DrawRatio 85.33% on the partner match next to Draws: 54; I report the raw line and do not know which count a reader should prefer.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/014/stamps.txt
?? forge-combo29/grok/014/REPORT.md
?? forge-combo29/grok/014/RESULT.txt
?? forge-combo29/grok/014/partner_O_off.meta
?? forge-combo29/grok/014/partner_O_off.txt
?? forge-combo29/grok/014/partner_O_off.txt.log
?? forge-combo29/grok/014/partner_O_on.meta
?? forge-combo29/grok/014/partner_O_on.txt
?? forge-combo29/grok/014/partner_O_on.txt.log
?? forge-combo29/grok/014/partner_bench11.meta
?? forge-combo29/grok/014/partner_bench11.txt
?? forge-combo29/grok/014/partner_bench13.meta
?? forge-combo29/grok/014/partner_bench13.txt
?? forge-combo29/grok/014/partner_bench16.meta
?? forge-combo29/grok/014/partner_bench16.txt
?? forge-combo29/grok/014/partner_cmp.py
?? forge-combo29/grok/014/partner_cmp.txt
?? forge-combo29/grok/014/partner_match.pgn
?? forge-combo29/grok/014/partner_match.sh
?? forge-combo29/grok/014/partner_match.txt
?? forge-combo29/grok/014/partner_note.txt
?? forge-combo29/grok/014/partner_perft5.meta
?? forge-combo29/grok/014/partner_perft5.txt
?? forge-combo29/grok/014/partner_s14_off.txt
?? forge-combo29/grok/014/partner_s14_on.txt
?? forge-combo29/grok/014/partner_uci.meta
?? forge-combo29/grok/014/partner_uci.txt
```

```
$ ls -la forge-combo29/grok/014
total 6312
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:18 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     337 Nov 20 08:11 asan_bug_special.meta
-rw-r--r-- 1 ubuntu ubuntu    8763 Nov 20 08:09 asan_bug_special.txt.log
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:08 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    6400 Nov 20 08:08 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu  119306 Nov 20 08:08 asan_G100_d10.txt.log
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:03 bench11_B.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 bench11_B.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:05 bench11_P.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 bench11_P.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:03 bench13_B.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 bench13_B.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:05 bench13_P.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 bench13_P.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:03 bench16_B.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 bench16_B.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:05 bench16_P.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 bench16_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1206 Nov 20 08:10 design.txt
-rw-r--r-- 1 ubuntu ubuntu     824 Nov 20 08:04 G_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu   22903 Nov 20 08:04 G_d12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     858 Nov 20 08:05 G_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   22903 Nov 20 08:05 G_d12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1459 Nov 20 08:04 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   12614 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1325 Nov 20 08:10 make_R.py
-rw-r--r-- 1 ubuntu ubuntu 3485023 Nov 20 08:16 match_fastchess.pgn
-rw-r--r-- 1 ubuntu ubuntu  135452 Nov 20 08:16 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 match_OG.epd
-rwxr-xr-x 1 ubuntu ubuntu    1291 Nov 20 08:10 match.sh
-rw-r--r-- 1 ubuntu ubuntu     824 Nov 20 08:04 O_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu   15769 Nov 20 08:04 O_d12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     858 Nov 20 08:05 O_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   15769 Nov 20 08:05 O_d12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     857 Nov 20 08:06 O_d12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu   15766 Nov 20 08:06 O_d12_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:09 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:09 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:09 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1021 Nov 20 09:15 partner_cmp.py
-rw-r--r-- 1 ubuntu ubuntu     124 Nov 20 09:15 partner_cmp.txt
-rw-r--r-- 1 ubuntu ubuntu 1573449 Nov 20 09:13 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1234 Nov 20 09:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   68993 Nov 20 09:13 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:53 partner_note.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 09:09 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu   15769 Nov 20 09:09 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu  282093 Nov 20 09:09 partner_O_off.txt.log
-rw-r--r-- 1 ubuntu ubuntu     860 Nov 20 09:09 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu   15767 Nov 20 09:09 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu  283458 Nov 20 09:09 partner_O_on.txt.log
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:09 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     654 Nov 20 09:09 partner_s14_off.txt
-rw-r--r-- 1 ubuntu ubuntu     653 Nov 20 09:09 partner_s14_on.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 09:09 partner_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 09:09 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:03 perft5_B.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 perft5_B.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:05 perft5_P.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 perft5_P.txt
-rw-r--r-- 1 ubuntu ubuntu     752 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    2492 Nov 20 08:11 proofs.py
-rw-r--r-- 1 ubuntu ubuntu    1391 Nov 20 08:11 proofs.txt
-rw-r--r-- 1 ubuntu ubuntu    5518 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19235 Nov 20 08:10 R.fen
-rw-r--r-- 1 ubuntu ubuntu     654 Nov 20 08:05 s14_off.txt
-rw-r--r-- 1 ubuntu ubuntu     653 Nov 20 08:05 s14_on.txt
-rw-r--r-- 1 ubuntu ubuntu     620 Nov 20 08:04 s14.txt
-rw-r--r-- 1 ubuntu ubuntu    4448 Nov 20 08:07 search_sum.py
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     167 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:05 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5221 Nov 20 08:05 uci_P.txt
```
