IdeaS37 is the off-PV worsening shave from IDEAS.md S37.
With the check on, a non-PV node that is not in check, whose parent already reduced the move by at least one ply, is searched IdeaS37_Shave plies shallower when the two corrected evals show the mover lost at least IdeaS37_Margin centipawns, unless the hash entry is already as deep as the current depth.
If the eval did not worsen and at least IdeaS37_DeepAt plies were withheld, the node is searched IdeaS37_Bonus plies deeper. Defaults: check false, margin 100, deep-at 3, shave 1, bonus 1.

EXISTS: no. The default search does not do this shave. HindsightDepth in search.cpp is a different option, default false: it also adds a ply, and it blocks the change when the hash depth reaches the proposed depth rather than the current depth. The one-line swarm summary matches the existing `if (!improving) r += 1` in the late-move reduction; that line was left as it is. See design.txt.

Honesty, no setoption, exe B and exe P (HONESTY_B.txt, P_bench11.txt, P_bench13.txt, P_bench16.txt, P_perft5.txt):
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 005, idea 5 |
| 2 honesty B | done | HONESTY_B.txt | all four numbers pass |
| 2 baseline O and G | done | compare is the sums in B_O_d12.txt and B_G_d12.txt via sum_nodes.py | O 9500069 first3 41311 24872 28574; G 18466239 |
| 3 prediction | done | prediction.txt | committed before any exe P measurement |
| 3 patch | done | idea.patch.txt | git apply --check on the base worktree passed |
| 3 proof 1 | done | P_bench11.txt P_bench13.txt P_bench16.txt P_perft5.txt | same four numbers |
| 3 proof 2 | done | compare_off_O.txt compare_off_G.txt | differ 0 and differ 0 |
| 3 proof 3 | done | compare_on_O.txt | differ 200, on sum 9702724 |
| 3 proof 4 | done | id_P.txt | IdeaS37 false; Margin 100; DeepAt 3; Shave 1; Bonus 1 |
| 3 proof 5 | done | asan_summary.txt asan_G100_d10.txt.meta asan_probe.txt | nm count 35; clean run 0 lines; probe heap-buffer-overflow |
| 3 match | done | match_summary.txt match_fastchess.txt match.pgn | Elo -1.88 +/- 10.41, 1106 games |
| 4 partner | done | partner055_cmp_off_O.txt partner055_cmp_on_O.txt partner055_match.txt | CONFIRMS |
| 5 report | done | REPORT.md RESULT.txt | this file |

Proofs on exe P:
(1) No setoption. bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.
(2) S14 and IdeaS37 false. O depth 12: differ 0, both sums 9500069. G depth 12: differ 0, both sums 18466239.
(3) S14 and IdeaS37 true. O depth 12: 200 of 200 positions differ from exe B. Sum 9702724. First three nodes 29011, 19718, 30514.
(4) uci lists `option name IdeaS37 type check default false` and the four spins at 100, 3, 1, 1.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaS37 true, first 100 of G at depth 10: 0 sanitizer lines, 100 bestmoves. `nm -C` count of `__asan_` is 35, stored in asan_G100_d10.txt.meta. The same harness on a scratch copy that reads past a 4-int heap array on the FEN in san_probe.fen printed `AddressSanitizer: heap-buffer-overflow` (asan_summary.txt).

Match: exe P with IdeaS37 true against exe P with IdeaS37 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess from github.com/Disservin/fastchess, concurrency 3. Elo -1.88 +/- 10.41, 349 wins, 355 losses, 402 draws. prediction.txt said +5 and would be wrong outside -35 to +45, so this Elo is inside the predicted range. The O sum 9702724 is inside 6000000 to 11000000. The interval is not entirely below 0, so the code was not re-opened for a second look. smoke_2games.txt is a 2-game command check with rounds set to 1. It is not the match.

Partner: seat 055 (next seat with this idea that had a branch). partner055_idea.patch.txt applies to the base (`check_exit 0` in partner055_apply_check.txt). Rebuilt with g++. Honesty numbers pass (partner055_bench11.txt through partner055_perft5.txt). IdeaS37 false: O depth 12 differ 0 against exe B, sum 9500069. IdeaS37 true: 200 positions, sum 9856085, differ 0 against the partner's own P_on_O rows, and differ 200 against exe B, which is what the partner reported. A match of that build, IdeaS37 true vs false, 300 R openings, both colours, 600 games: Elo 0.58 +/- 10.22 (partner055_match.txt). Verdict: CONFIRMS.

suspicions, not proven: turning the shave on raised the O node sum (9702724 against 9500069) instead of cutting it, so the extra ply, or the searches that follow a shallower node, may cost more than the shave saves. The partner, who left the extra ply out, also saw a higher sum (9856085). Neither result says which term dominates.

what I did NOT do: I did not wait until minute 75 to open the partner branch. Both partner branches already existed and 055 already had a patch and a match, so the review started at 08:47Z. I did not replay the partner's 1106-game match. I did not enable IdeaS37 and HindsightDepth together. I did not change the spin defaults during the measured searches. I did not open a pull request.

what I am NOT sure about: whether "off the PV" should also skip nodes that are only tt-pv. The parent value used is the stored static eval; with EvalRule50Damp left false that is the corrected eval. fastchess sends the S14 options, but not necessarily in the harness order. The depth proofs used harness_depth.py, which sends them in the listed order.

times: see stamps.txt

Minute-60 handoff fetch at 2026-11-20T08:52:44Z found no forge-combo29/soak_all/FABLE_TO_grok_*.md. The earlier fetch during step 1 also found none.

```
$ git status --short
 M forge-combo29/grok/005/config.json
 M forge-combo29/grok/005/stamps.txt
?? forge-combo29/grok/005/REPORT.md
?? forge-combo29/grok/005/RESULT.txt
?? forge-combo29/grok/005/partner055_P_on_O_d12.txt
?? forge-combo29/grok/005/partner055_apply_check.txt
?? forge-combo29/grok/005/partner055_bench11.meta
?? forge-combo29/grok/005/partner055_bench11.txt
?? forge-combo29/grok/005/partner055_bench13.meta
?? forge-combo29/grok/005/partner055_bench13.txt
?? forge-combo29/grok/005/partner055_bench16.meta
?? forge-combo29/grok/005/partner055_bench16.txt
?? forge-combo29/grok/005/partner055_cmp_off_O.txt
?? forge-combo29/grok/005/partner055_cmp_on_O.txt
?? forge-combo29/grok/005/partner055_id.txt
?? forge-combo29/grok/005/partner055_idea.patch.txt
?? forge-combo29/grok/005/partner055_match.pgn
?? forge-combo29/grok/005/partner055_match.pid
?? forge-combo29/grok/005/partner055_match.txt
?? forge-combo29/grok/005/partner055_off_O_d12.txt
?? forge-combo29/grok/005/partner055_off_O_d12.txt.meta
?? forge-combo29/grok/005/partner055_on_O_d12.txt
?? forge-combo29/grok/005/partner055_on_O_d12.txt.meta
?? forge-combo29/grok/005/partner055_perft5.meta
?? forge-combo29/grok/005/partner055_perft5.txt
?? forge-combo29/grok/005/partner055_wrapper.log
?? forge-combo29/grok/005/run_partner_match.sh

$ ls -la forge-combo29/grok/005
total 9628
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:53 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu  119272 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     973 Nov 20 08:06 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    8875 Nov 20 08:07 asan_probe.txt
-rw-r--r-- 1 ubuntu ubuntu      98 Nov 20 08:07 asan_probe.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     518 Nov 20 08:08 asan_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:00 bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:00 bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:00 bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu  507438 Nov 20 08:01 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:01 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  281717 Nov 20 08:01 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:01 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:04 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 08:04 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     664 Nov 20 08:04 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1785 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    6940 Nov 20 08:51 config.json
-rw-r--r-- 1 ubuntu ubuntu     763 Nov 20 08:07 count_san.py
-rw-r--r-- 1 ubuntu ubuntu    2137 Nov 20 08:02 design.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:06 g100.epd
-rw-r--r-- 1 ubuntu ubuntu    4580 Nov 20 08:03 harness_depth.py
-rwxr-xr-x 1 ubuntu ubuntu    1799 Nov 20 08:00 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:00 id_B.txt
-rw-r--r-- 1 ubuntu ubuntu    8444 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    5218 Nov 20 08:04 id_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1589 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  118643 Nov 20 08:15 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 4549693 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu       5 Nov 20 08:09 match.pid
-rw-r--r-- 1 ubuntu ubuntu     312 Nov 20 08:18 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 match_wrapper.log
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 openings_O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu   19125 Nov 20 08:10 openings_R.epd
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:53 partner055_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:48 partner055_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:48 partner055_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:48 partner055_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:48 partner055_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:48 partner055_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:48 partner055_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 08:48 partner055_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:48 partner055_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    7816 Nov 20 08:47 partner055_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    5042 Nov 20 08:48 partner055_id.txt
-rw-r--r-- 1 ubuntu ubuntu 2107823 Nov 20 08:51 partner055_match.pgn
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 08:48 partner055_match.pid
-rw-r--r-- 1 ubuntu ubuntu   60765 Nov 20 08:51 partner055_match.txt
-rw-r--r-- 1 ubuntu ubuntu  281873 Nov 20 08:48 partner055_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:48 partner055_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  281969 Nov 20 08:48 partner055_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     870 Nov 20 08:48 partner055_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:48 partner055_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:48 partner055_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   15775 Nov 20 08:48 partner055_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:48 partner055_wrapper.log
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:04 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:04 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:04 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     234 Nov 20 08:00 perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  507708 Nov 20 08:04 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:04 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  282026 Nov 20 08:04 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:04 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  282238 Nov 20 08:04 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 08:04 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     234 Nov 20 08:04 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    7057 Nov 20 08:53 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:53 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1108 Nov 20 08:09 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1123 Nov 20 08:48 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:07 san_probe.fen
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu   11539 Nov 20 08:08 smoke_2games.pgn
-rw-r--r-- 1 ubuntu ubuntu     640 Nov 20 08:08 smoke_2games.txt
-rw-r--r-- 1 ubuntu ubuntu     299 Nov 20 08:53 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1765 Nov 20 08:01 sum_nodes.py
```
