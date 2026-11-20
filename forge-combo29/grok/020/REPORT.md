Idea S22 refuses the shallow ProbCut proof for one ply after a capture, and for the ply after a check has been answered, when the side to move is no longer in check. The margin is unchanged.
The switch is IdeaS22, a check, default false. The length is IdeaS22_Plies, a spin, default 1, range 0 to 8.
With the switch off the search is today's path. With it on, ProbCut is skipped while a one-ply counter is positive.

EXISTS: no. ProbCut in src/search.cpp already does not run while the side to move is in check. Nothing there skips it because the move that entered the node was a capture, or because the parent node was in check.

Honesty, no setoption, exe B and exe P: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

The table and the numbers under it are the output of report_numbers.py, which reads the raw files.

```
step | status | evidence | result
1 seat | done | SEAT.txt | 020 idea 20
2 honesty B | done | HONESTY_B.txt | PASS
2 baseline O G | done | B_OG_sums.txt | 9500069 and 18466239
3 prediction | done | prediction.txt | pushed before measuring P
3 patch applies | done | idea.patch.txt | git apply --check passed
3 proof 1 honesty P | done | HONESTY_P.txt | PASS
3 proof 2 off | done | off_O_vs_B.txt off_G_vs_B.txt | differ 0 and differ 0
3 proof 3 on | done | on_O_vs_B.txt | differ 194 sum 9571899
3 proof 4 uci | done | uci_p.txt | IdeaS22 false, IdeaS22_Plies 1
3 proof 5 sanitizer | done | asan_G100.meta asan_scratch.meta | 0 lines, scratch 1 line, asan symbols 35
3 match | done | match_og_final.txt | 1106 games Elo -5.65 +/- 9.85
4 partner | done | partner_on_vs_claim.txt partner_match_final.txt | CONFIRMS
5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P.

(1) No setoption. bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. HONESTY_P.txt says PASS.

(2) S14, IdeaS22 false. O depth 12: 200 positions, differ 0, sum 9500069, same as exe B. G depth 12: 353 positions, differ 0, sum 18466239, same as exe B. Exe B itself matched the known sums, first three of O 41311 / 24872 / 28574.

(3) S14, IdeaS22 true. O depth 12 sum 9571899. 194 of 200 positions differ from exe B. The code runs.

(4) uci lists `option name IdeaS22 type check default false` and `option name IdeaS22_Plies type spin default 1 min 0 max 8`. id name Chess Engine Forge 6.4.24 candidate.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS22 true, first 100 of G at depth 10: 100 finished, sanitizer lines 0, nm -C count of __asan_ is 35. The same runner on a scratch copy with one read past a 4-int heap array, on the FEN in scratch_fen.txt, reported one sanitizer line: a runtime error for a load with insufficient space for an int. asan_G100.meta and asan_scratch.meta.

git apply --check on idea.patch.txt against the base commit exited 0. apply_check.txt.

Match: exe P with IdeaS22 true against exe P with IdeaS22 false, both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O and G, both colours. 1106 games. Elo of the switch-on side -5.65 +/- 9.85. Wins 334, losses 352, draws 420. The point is not below -20 and the interval is not entirely below 0, so the code was not reopened for a mistake. match_og.log is the whole fastchess output. No illegal-move, disconnect, or crash lines.

Partner is seat 070 (idea 20; 120 had no branch). Verdict: CONFIRMS. On a fresh worktree of the base, partner070.patch.txt passed git apply --check, applied, and built. Honesty matched the four known numbers. Switch false: O depth 12 differ 0 against exe B, sum 9500069. Switch true: sum 9571899, differ 194 against exe B, and differ 0 of 200 against the partner's own published O rows (sum 9571899). Their uci lists IdeaS22 default false and IdeaS22_Ply default 1. A match of their switch on my 300 R openings, both colours, 600 games, finished: Elo +2.32 +/- 11.00. partner_match.log has no illegal-move, disconnect, or crash lines.

suspicions, not proven

The small negative Elo may be the recapture witnesses the idea said make the prune pay. The interval includes positive values, so that is not shown. Six of the 200 openings kept the same node count with the switch on. I did not show that those trees never reached a cooldown at a ProbCut depth.

what I did NOT do

No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60, so nothing there changed the rules. I did not play a second match of my own patch on R, because 070 had a patch. I did not search G at depth 12 with the switch on. I did not try IdeaS22_Plies other than 1. I did not rebuild the partner under a sanitizer. I did not open a pull request.

what I am NOT sure about

At ply 1 my counter and seat 070's ancestor walk produced the same 200 node counts. I did not measure any other ply setting, so I do not know if the two readings stay the same when the spin is not 1. The scratch report is a UndefinedBehaviorSanitizer line for the bad load. The executable does contain AddressSanitizer symbols (35). I am not sure a reader who looks only for the words "AddressSanitizer" in that log will count the line; the runner counted it, and the clean run had zero such lines.

times: see stamps.txt

Prediction, left as pushed: O depth-12 sum 10200000, wrong if 9500069 or below or 13000000 or above. Measured sum 9571899, so the prediction was not proved wrong. Match Elo -8, wrong if the point is +15 or higher or -40 or lower. Measured -5.65, so that prediction was not proved wrong either.

```
$ git status --short
 M forge-combo29/grok/020/stamps.txt
?? forge-combo29/grok/020/REPORT.md
?? forge-combo29/grok/020/RESULT.txt
?? forge-combo29/grok/020/apply_check.txt
?? forge-combo29/grok/020/config.json
?? forge-combo29/grok/020/partner070.patch.txt
?? forge-combo29/grok/020/partner070_claimed_on_O.txt
?? forge-combo29/grok/020/partner_HONESTY.txt
?? forge-combo29/grok/020/partner_apply_check.txt
?? forge-combo29/grok/020/partner_h_bench11.txt
?? forge-combo29/grok/020/partner_h_bench13.txt
?? forge-combo29/grok/020/partner_h_bench16.txt
?? forge-combo29/grok/020/partner_h_perft5.txt
?? forge-combo29/grok/020/partner_match.log
?? forge-combo29/grok/020/partner_match.pgn
?? forge-combo29/grok/020/partner_match_final.txt
?? forge-combo29/grok/020/partner_off_O_d12.meta
?? forge-combo29/grok/020/partner_off_O_d12.nodes.tsv
?? forge-combo29/grok/020/partner_off_O_d12.raw.txt
?? forge-combo29/grok/020/partner_off_vs_B.txt
?? forge-combo29/grok/020/partner_on_O_d12.meta
?? forge-combo29/grok/020/partner_on_O_d12.nodes.tsv
?? forge-combo29/grok/020/partner_on_O_d12.raw.txt
?? forge-combo29/grok/020/partner_on_vs_B.txt
?? forge-combo29/grok/020/partner_on_vs_claim.txt
?? forge-combo29/grok/020/partner_uci.txt
?? forge-combo29/grok/020/partner_vs_claim.py
?? forge-combo29/grok/020/report_numbers.py
?? forge-combo29/grok/020/report_numbers.txt
?? forge-combo29/grok/020/run_partner_match.sh

$ ls -la forge-combo29/grok/020
total 4796
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu     25 Nov 20 09:14 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    913 Nov 20 08:07 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu 131639 Nov 20 08:07 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   6915 Nov 20 08:06 asan_runner.py
-rw-r--r-- 1 ubuntu ubuntu   1085 Nov 20 08:07 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   7232 Nov 20 08:07 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 08:00 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  23980 Nov 20 08:00 B_G_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 550138 Nov 20 08:00 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 08:00 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  16388 Nov 20 08:00 B_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 309230 Nov 20 08:00 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    124 Nov 20 08:00 B_OG_sums.txt
-rw-r--r-- 1 ubuntu ubuntu   1193 Nov 20 08:04 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu   7003 Nov 20 09:12 config.json
-rw-r--r-- 1 ubuntu ubuntu    945 Nov 20 08:08 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu    412 Nov 20 08:16 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   2306 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    369 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:03 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:03 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:03 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:03 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    369 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   6354 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1517 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    391 Nov 20 08:16 match_og_final.txt
-rw-r--r-- 1 ubuntu ubuntu 117725 Nov 20 08:14 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 961624 Nov 20 08:14 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    641 Nov 20 08:08 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu   2423 Nov 20 08:08 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu   6365 Nov 20 07:59 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu    111 Nov 20 08:04 off_G_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    109 Nov 20 08:04 off_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:08 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    690 Nov 20 08:04 on_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   1922 Nov 20 09:09 partner070_claimed_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   4940 Nov 20 09:09 partner070.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 09:14 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:09 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    333 Nov 20 09:09 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 09:09 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    386 Nov 20 09:14 partner_match_final.txt
-rw-r--r-- 1 ubuntu ubuntu  59848 Nov 20 09:12 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 452457 Nov 20 09:12 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    797 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  16388 Nov 20 09:09 partner_off_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 308943 Nov 20 09:09 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 09:09 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    831 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  16388 Nov 20 09:09 partner_on_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 309323 Nov 20 09:09 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    696 Nov 20 09:09 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     65 Nov 20 09:09 partner_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu   5035 Nov 20 09:09 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   1075 Nov 20 09:09 partner_vs_claim.py
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 08:03 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  23980 Nov 20 08:03 P_off_G_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 549919 Nov 20 08:03 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    816 Nov 20 08:03 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  16388 Nov 20 08:03 P_off_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 309270 Nov 20 08:03 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    850 Nov 20 08:03 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  16388 Nov 20 08:03 P_on_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu 309518 Nov 20 08:03 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    915 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   5512 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   3981 Nov 20 09:14 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu   3613 Nov 20 09:14 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu    184 Nov 20 09:14 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu  19226 Nov 20 08:08 R.fen
-rwxr-xr-x 1 ubuntu ubuntu   1202 Nov 20 08:08 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    966 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     28 Nov 20 08:07 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    186 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    651 Nov 20 08:00 sum_tsv.py
-rw-r--r-- 1 ubuntu ubuntu   5036 Nov 20 08:03 uci_p.txt
```
