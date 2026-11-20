Idea S29, option IdeaS29: a capture-history axis indexed by the moved piece, the cheapest enemy attacker of the landing square, and the destination.
That term orders only captures that already pass see_ge at IdeaS29_Threshold (default 0). The history value is not added to the threshold, and the stored bonus is divided by IdeaS29_Divisor (default 8).
The check option defaults to false. While it is false the search does not read the table and does not call see_ge for this term.

EXISTS: no. ThreatHistory is a quiet-move table. The existing capture history is added to every capture and is not gated by a fixed exchange threshold.

Honesty, no setoption, plain exe B and patched exe P (HONESTY_B.txt and HONESTY_P.txt): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

The table below is the output of summarize.py, which reads the raw files:

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 073, idea 23, model Grok 4.7, 2026-11-20T07:54:49Z, token 2441718313384
2 honesty B | done | HONESTY_B.txt | bench11 bench 11 312866 312866 ok; bench13 bench 13 862329 862329 ok; bench16 bench 16 3024920 3024920 ok; perft5 go perft 5 4865609 4865609 ok
2 O and G baseline | done | compare not needed; B_O_d12.rows.txt B_G_d12.rows.txt | O sum is the left sum in compare_off_O.txt 9500069; G sum is the left sum in compare_off_G.txt 18466239
3 prediction | done | prediction.txt | committed before the patched measurements
3 apply | done | apply_check.txt idea.patch.txt | git apply --check exit 0
3 honesty P | done | HONESTY_P.txt | bench11 bench 11 312866 312866 ok; bench13 bench 13 862329 862329 ok; bench16 bench 16 3024920 3024920 ok; perft5 go perft 5 4865609 4865609 ok
3 off O | done | compare_off_O.txt | nodes_differ 0 of 200 sum 9500069
3 off G | done | compare_off_G.txt | nodes_differ 0 of 353 sum 18466239
3 on O | done | compare_on_O.txt | nodes_differ 199 of 200 sum 9692566
3 uci options | done | P_uci.txt | option name IdeaS29 type check default false ; option name IdeaS29_Threshold type spin default 0 min -400 max 400 ; option name IdeaS29_Divisor type spin default 8 min 1 max 64
3 sanitizer | done | P_asan_G100.meta P_asan_G100.txt P_asan_probe.txt | nm -C /tmp/forge_asan/forge | grep -c __asan_ 35; AddressSanitizer lines in G100 0; heap-buffer-overflow lines in probe 2
3 match | done | match_on_off.txt match_on_off.pgn | Results of IdeaS29_on vs IdeaS29_off (20000 nodes, 1t, 16MB, OG.epd): | Elo: -1.88 +/- 10.52, nElo: -3.67 +/- 20.48 | LOS: 36.27 %, DrawRatio: 62.39 %, PairsRatio: 0.91 | Games: 1106, Wins: 334, Losses: 340, Draws: 432, Points: 550.0 (49.73 %)
4 partner 023 | done | partner023_apply_check.txt partner023_HONESTY.txt partner023_compare_off.txt partner023_compare_on.txt partner023_match_R.txt | apply git apply --check exit 0; honesty bench11 bench 11 312866 312866 ok; bench13 bench 13 862329 862329 ok; bench16 bench 16 3024920 3024920 ok; perft5 go perft 5 4865609 4865609 ok; off nodes_differ 0 of 200; on count_theirs 200; count_mine 200; sum_theirs 9540759; sum_mine 9540759; nodes_differ 0 of 200; ; match Results of IdeaS29_on vs IdeaS29_off (20000 nodes, 1t, 16MB, R.fens): | Elo: -6.95 +/- 11.22, nElo: -17.24 +/- 27.80 | LOS: 11.22 %, DrawRatio: 83.33 %, PairsRatio: 0.79 | Games: 600, Wins: 256, Losses: 268, Draws: 76, Points: 294.0 (49.00 %)
5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P:

(1) No setoption. bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Same as exe B.

(2) S14 and IdeaS29 false. O depth 12: nodes_differ 0 of 200, sum 9500069, and the moves match exe B. G depth 12: nodes_differ 0 of 353, sum 18466239, and the moves match exe B. The plain O sum and the first three O rows are 9500069 and 41311 / 24872 / 28574.

(3) S14 and IdeaS29 true. O depth 12 sum 9692566. nodes_differ 199 of 200 against exe B. move_differ 31 of 200. The switch runs.

(4) The uci answer lists `option name IdeaS29 type check default false`, `option name IdeaS29_Threshold type spin default 0 min -400 max 400`, and `option name IdeaS29_Divisor type spin default 8 min 1 max 64`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS29 true, first 100 of G at depth 10: 0 lines containing `ERROR: AddressSanitizer`. P_asan_G100.meta records `nm -C /tmp/forge_asan/forge | grep -c __asan_` as 35. The same harness on a scratch copy that reads past a 4-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 1` reports `ERROR: AddressSanitizer: heap-buffer-overflow` (2 lines contain heap-buffer-overflow). Its meta also records 35 asan symbols.

Match: exe P with IdeaS29 true against exe P with IdeaS29 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess result: Elo -1.88 +/- 10.52, 334 wins, 340 losses, 432 draws, 550.0 points. The point is not below -20 and the interval is not entirely below 0, so I did not open the code again for a match bug. OwnBook was false on both sides. prediction.txt said +4, wrong if below -20 or above +30. -1.88 is inside that range. The on O sum 9692566 is inside 8000000 to 11000000.

Partner verdict: CONFIRMS, seat 023. Next seat after 073 with this idea; seat 123 has no branch. git apply --check on a fresh tree of 6b98f2170 exited 0, then the patch was applied and built. Honesty numbers match. IdeaS29 false, S14, O depth 12: nodes_differ 0 of 200 against exe B. IdeaS29 true with their default threshold 0 and scale 1: my O depth-12 nodes match their P_on_O_d12.rows on all 200 positions, both sums 9540759. A match of their switch on my 300 R openings, both colours, 600 games: Elo -6.95 +/- 11.22. I did not copy their harness.

suspicions, not proven: attackers_to of the landing square misses a slider that the capture would discover. I did not test that. Divisor 8 and seat 023's scale 1 are different weights; both match intervals include both signs, so this does not pick a weight.

what I did NOT do: I did not re-run seat 023's 1106-game match or their sanitizer. I did not play the owner's net. I did not search for a match bug, because the Elo test in the brief was not met. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about: why 1 of the 200 O positions kept the same node count with the switch on. Whether another divisor would move the Elo across zero. The prediction was not proved wrong.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/073/config.json
 M forge-combo29/grok/073/harness.py
 M forge-combo29/grok/073/run_match.sh
 M forge-combo29/grok/073/stamps.txt
?? forge-combo29/grok/073/REPORT.md
?? forge-combo29/grok/073/RESULT.txt
?? forge-combo29/grok/073/match_on_off.config.json
?? forge-combo29/grok/073/partner023_HONESTY.txt
?? forge-combo29/grok/073/partner023_P_on_O_d12.rows
?? forge-combo29/grok/073/partner023_apply_check.txt
?? forge-combo29/grok/073/partner023_compare_off.txt
?? forge-combo29/grok/073/partner023_compare_on.txt
?? forge-combo29/grok/073/partner023_honesty_bench11.meta
?? forge-combo29/grok/073/partner023_honesty_bench11.txt
?? forge-combo29/grok/073/partner023_honesty_bench13.meta
?? forge-combo29/grok/073/partner023_honesty_bench13.txt
?? forge-combo29/grok/073/partner023_honesty_bench16.meta
?? forge-combo29/grok/073/partner023_honesty_bench16.txt
?? forge-combo29/grok/073/partner023_honesty_perft5.meta
?? forge-combo29/grok/073/partner023_honesty_perft5.txt
?? forge-combo29/grok/073/partner023_idea.patch.txt
?? forge-combo29/grok/073/partner023_match_R.config.json
?? forge-combo29/grok/073/partner023_match_R.pgn
?? forge-combo29/grok/073/partner023_match_R.txt
?? forge-combo29/grok/073/partner023_off_O_d12.meta
?? forge-combo29/grok/073/partner023_off_O_d12.rows.txt
?? forge-combo29/grok/073/partner023_off_O_d12.txt
?? forge-combo29/grok/073/partner023_on_O_d12.meta
?? forge-combo29/grok/073/partner023_on_O_d12.rows.txt
?? forge-combo29/grok/073/partner023_on_O_d12.txt
?? forge-combo29/grok/073/summarize.py
?? forge-combo29/grok/073/summary_table.txt

$ ls -la forge-combo29/grok/073
total 8544
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:26 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:11 asan_probe.fen
-rw-r--r-- 1 ubuntu ubuntu     810 Nov 20 08:05 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22913 Nov 20 08:05 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  548332 Nov 20 08:05 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     810 Nov 20 08:04 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15779 Nov 20 08:04 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308180 Nov 20 08:04 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      90 Nov 20 08:12 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      88 Nov 20 08:12 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      91 Nov 20 08:12 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:07 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7111 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    1413 Nov 20 08:06 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:07 G.epd
-rw-r--r-- 1 ubuntu ubuntu   11840 Nov 20 09:11 harness.py
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:04 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5029 Nov 20 08:04 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:04 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5029 Nov 20 08:04 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:04 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5031 Nov 20 08:04 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:04 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:04 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5244 Nov 20 08:04 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   12253 Nov 20 08:11 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1360 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    7141 Nov 20 09:12 match_on_off.config.json
-rw-r--r-- 1 ubuntu ubuntu 3543637 Nov 20 08:23 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  141316 Nov 20 08:23 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:07 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:12 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 09:12 partner023_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      88 Nov 20 09:12 partner023_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      90 Nov 20 09:12 partner023_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 partner023_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5202 Nov 20 09:12 partner023_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 partner023_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5202 Nov 20 09:12 partner023_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 partner023_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5204 Nov 20 09:12 partner023_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 partner023_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5417 Nov 20 09:12 partner023_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 09:12 partner023_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   11281 Nov 20 09:11 partner023_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    7111 Nov 20 09:17 partner023_match_R.config.json
-rw-r--r-- 1 ubuntu ubuntu 1573167 Nov 20 09:15 partner023_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   73064 Nov 20 09:15 partner023_match_R.txt
-rw-r--r-- 1 ubuntu ubuntu     829 Nov 20 09:12 partner023_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15779 Nov 20 09:12 partner023_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308148 Nov 20 09:12 partner023_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     906 Nov 20 09:12 partner023_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15776 Nov 20 09:12 partner023_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308278 Nov 20 09:12 partner023_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1201 Nov 20 09:11 partner023_P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 08:09 P_asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    6404 Nov 20 08:09 P_asan_G100.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  131249 Nov 20 08:09 P_asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:11 P_asan_probe.meta
-rw-r--r-- 1 ubuntu ubuntu    9148 Nov 20 08:11 P_asan_probe.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 P_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5202 Nov 20 08:09 P_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 P_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5202 Nov 20 08:09 P_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 P_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5204 Nov 20 08:09 P_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 P_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5417 Nov 20 08:09 P_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     845 Nov 20 08:09 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   22913 Nov 20 08:09 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  548978 Nov 20 08:09 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     845 Nov 20 08:09 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15779 Nov 20 08:09 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308508 Nov 20 08:09 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 08:09 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   15778 Nov 20 08:09 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu  308592 Nov 20 08:09 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 08:07 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:09 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5130 Nov 20 08:09 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    8162 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:19 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19076 Nov 20 08:06 R.fens
-rw-r--r-- 1 ubuntu ubuntu    1301 Nov 20 09:11 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    3089 Nov 20 09:18 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    2536 Nov 20 09:18 summary_table.txt
```
