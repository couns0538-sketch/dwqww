# Seat 077, idea 27, S44

Idea S44 is a static drop when the eval sits above beta, off the PV and out of check, only for a quiet transposition move whose history is in a very high band, and only when no cheaper enemy piece attacks a dearer piece of ours. A capture transposition move does not qualify.
I built UCI check IdeaS44, default false, and spins IdeaS44_Margin 40, IdeaS44_Depth 5, IdeaS44_History 5000. The reasons are in decisions.txt.
The drop is after today's reverse futility and returns eval. The flag is tested first, so with it false the history read and the attack scan do not run.

EXISTS: no. Reverse futility in forge-combo29/src/search.cpp returns eval from RfpMargin and does not look at the hash move or its history.

Honesty, no setoption, fresh process each line, both exes (HONESTY_B.txt and HONESTY_P.txt):
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Exe B, S14, Threads 1, Hash 16, depth 12 (read_nodes.py): O sum 9500069, first three 41311 24872 28574. G sum 18466239.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt stamps.txt | seat 077 idea 27 |
| 2 honesty and known sums | done | HONESTY_B.txt B_O_d12.nodes B_G_d12.nodes | honesty OK; O 9500069; G 18466239 |
| 3a read and design | done | decisions.txt idea.patch.txt | not already present |
| 3b prediction | done | prediction.txt | 9100000 and Elo +4, committed before measuring P |
| 3c patch | done | idea.patch.txt apply_check.txt | apply_check_exit=0 |
| 3d proofs | done | proof_off_O.txt proof_off_G.txt proof_on_O.txt proof_uci_options.txt asan_G100.txt.meta asan_scratch.san asan_scratch_asan.san | off 0 differ; on 200 of 200; options listed; sanitizer clean |
| 3e match | done | match_summary.txt match_fastchess.txt match.pgn | 1106 games, Elo -4.71 +/- 10.43 |
| 4 partner | done | partner_compare.txt partner_match_summary.txt HONESTY_partner.txt | CONFIRMS |
| 5 report | done | REPORT.md RESULT.txt | this file |

Proof (1). HONESTY_P.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Same as exe B.

Proof (2). proof_off_O.txt: P with IdeaS44 false, O depth 12, sum 9500069, differ 0 of 200 against B_O_d12.nodes. proof_off_G.txt: G depth 12, sum 18466239, differ 0 of 353.

Proof (3). proof_on_O.txt: IdeaS44 true, O depth 12, sum 8965644, differ 200 of 200 against exe B. Prediction was 9100000, wrong outside 7800000 to 9490000. 8965644 is inside that range.

Proof (4). proof_uci_options.txt:
option name IdeaS44 type check default false
option name IdeaS44_Margin type spin default 40 min 0 max 400
option name IdeaS44_Depth type spin default 5 min 1 max 8
option name IdeaS44_History type spin default 5000 min 0 max 32767
count 4

Proof (5). asan_G100.txt.meta: nm_asan_count=35, asan_or_ubsan_lines=0, first 100 of G, depth 10, IdeaS44 true, S14. The same runner on a scratch copy built with the same AddressSanitizer and UndefinedBehaviorSanitizer flags, one heap read past the end on scratch_fen.epd, wrote asan_scratch.san: `runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'`. A second scratch build with AddressSanitizer only, same runner, wrote asan_scratch_asan.san: `ERROR: AddressSanitizer: heap-buffer-overflow` and `SUMMARY: AddressSanitizer: heap-buffer-overflow ... uci.cpp:47 in apply_position`, nm_asan_count=35.

Match. match_summary.txt, pasted from read_match.py:
finished_games 1106
Elo: -4.71 +/- 10.43, nElo: -9.26 +/- 20.48
Games: 1106, Wins: 328, Losses: 343, Draws: 435, Points: 545.5 (49.32 %)
match_exit=0
Prediction was Elo +4, wrong outside -35 to +45. -4.71 is inside that range. The printed interval is about -15.14 to +5.72, so it is not entirely below 0, and the point is not below -20. I did not go looking for a code mistake.

Partner 027 (same idea; next seat after 077 wraps to 027). partner_apply_check.txt exit 0. HONESTY_partner.txt matches the four honesty numbers. partner_compare.txt: off versus exe B differ 0 of 200, sums 9500069; on versus the partner's claimed rows differ 0 of 200, sums 9567212; on versus exe B differ 159 of 200. That is what the partner's compare_on_O.txt and compare_off_O.txt say. Their uci list on this build is the four IdeaS44 options with defaults false, depth 8, margin 48, history 6000. partner_match_summary.txt: 600 games on my R.fens, both colours, Elo -1.74 +/- 14.04. Verdict: CONFIRMS.

suspicions, not proven
The on-switch changed the node count of all 200 openings. One early drop changes a whole count, so this does not show the drop at every root. The partner's on-sum rose (9567212) while mine fell (8965644). The margins differ (theirs is 48 centipawns times depth, mine is a flat 40), so the two builds are not the same experiment.

what I did NOT do
I did not rebuild the partner's sanitizer. I did not play the partner match on the partner's R file; I used my R.fens, 300 positions, both colours. I did not edit prediction.txt after measuring. I did not open a pull request.

what I am NOT sure about
Whether history 5000 is the best band. It is high enough that the proof (3) count is not zero, and low enough that depth-12 search reaches it. I am not sure the fastchess +/- number is a 95 percent half-width; err in RESULT.txt is the number they printed, 10.43. The combined sanitizer scratch stopped on the UndefinedBehaviorSanitizer line before an AddressSanitizer summary; the AddressSanitizer summary is in the address-only scratch run.

times: see stamps.txt

Handoff check at 2026-11-20T08:22:25Z: no forge-combo29/soak_all/FABLE_TO_grok_<N>.md on handoff/fable-opus-combo29-all-20261114. Minute 60 from the first stamp (07:55:24Z) is 08:55:24Z. A later stamp line records that check if this commit is after it.

git status --short
```
 M forge-combo29/grok/077/stamps.txt
?? config.json
?? forge-combo29/grok/077/REPORT.md
?? forge-combo29/grok/077/RESULT.txt
?? forge-combo29/grok/077/asan_scratch_asan.san
?? forge-combo29/grok/077/asan_scratch_asan.txt
?? forge-combo29/grok/077/asan_scratch_asan.txt.meta
?? forge-combo29/grok/077/partner_apply_check.txt
```

ls -la forge-combo29/grok/077
```
total 4904
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:24 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu     19 Nov 20 08:04 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    870 Nov 20 08:06 asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:06 asan_G100.san
-rw-r--r-- 1 ubuntu ubuntu 131574 Nov 20 08:06 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu    904 Nov 20 08:06 asan_G100.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2582 Nov 20 08:05 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu    240 Nov 20 08:24 asan_scratch_asan.san
-rw-r--r-- 1 ubuntu ubuntu   9364 Nov 20 08:24 asan_scratch_asan.txt
-rw-r--r-- 1 ubuntu ubuntu    950 Nov 20 08:24 asan_scratch_asan.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    137 Nov 20 08:07 asan_scratch.san
-rw-r--r-- 1 ubuntu ubuntu   7126 Nov 20 08:07 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    945 Nov 20 08:07 asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3430 Nov 20 08:03 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu 549959 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 08:03 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 08:03 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu 309077 Nov 20 08:03 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 08:03 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1481 Nov 20 08:08 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu   5009 Nov 20 08:06 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   5013 Nov 20 08:03 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5013 Nov 20 08:03 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5015 Nov 20 08:03 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5228 Nov 20 08:03 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    193 Nov 20 08:03 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    170 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu   5246 Nov 20 08:10 honesty_partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 08:10 honesty_partner_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5246 Nov 20 08:10 honesty_partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 08:10 honesty_partner_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5248 Nov 20 08:10 honesty_partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 08:10 honesty_partner_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5461 Nov 20 08:10 honesty_partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 08:10 honesty_partner_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    170 Nov 20 08:10 HONESTY_partner.txt
-rw-r--r-- 1 ubuntu ubuntu   5245 Nov 20 08:03 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5245 Nov 20 08:03 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5247 Nov 20 08:03 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    191 Nov 20 08:03 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5460 Nov 20 08:03 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    193 Nov 20 08:03 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    170 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   2416 Nov 20 08:01 honesty_run.py
-rw-r--r-- 1 ubuntu ubuntu   5219 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1242 Nov 20 08:01 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 108161 Nov 20 08:15 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 968629 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:09 match_run.log
-rw-r--r-- 1 ubuntu ubuntu    316 Nov 20 08:16 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:06 OG.fens
-rw-r--r-- 1 ubuntu ubuntu    785 Nov 20 08:05 options_run.py
-rw-r--r-- 1 ubuntu ubuntu     27 Nov 20 08:24 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  18249 Nov 20 08:10 partner_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   1239 Nov 20 08:11 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu    304 Nov 20 08:11 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu   5587 Nov 20 08:10 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  54484 Nov 20 08:20 partner_match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 570629 Nov 20 08:20 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 08:16 partner_match_run.log
-rw-r--r-- 1 ubuntu ubuntu    313 Nov 20 08:22 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 08:10 partner_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu 309185 Nov 20 08:10 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu    842 Nov 20 08:10 partner_O_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1895 Nov 20 08:10 partner_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu 309191 Nov 20 08:10 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 08:10 partner_O_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3430 Nov 20 08:04 P_G_d12_off.nodes
-rw-r--r-- 1 ubuntu ubuntu 550290 Nov 20 08:04 P_G_d12_off.txt
-rw-r--r-- 1 ubuntu ubuntu    861 Nov 20 08:04 P_G_d12_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 08:04 P_O_d12_off.nodes
-rw-r--r-- 1 ubuntu ubuntu 309290 Nov 20 08:04 P_O_d12_off.txt
-rw-r--r-- 1 ubuntu ubuntu    861 Nov 20 08:04 P_O_d12_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1893 Nov 20 08:04 P_O_d12_on.nodes
-rw-r--r-- 1 ubuntu ubuntu 309323 Nov 20 08:04 P_O_d12_on.txt
-rw-r--r-- 1 ubuntu ubuntu    859 Nov 20 08:04 P_O_d12_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    531 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    166 Nov 20 08:04 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu    164 Nov 20 08:04 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    165 Nov 20 08:04 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    240 Nov 20 08:05 proof_uci_options.txt
-rw-r--r-- 1 ubuntu ubuntu    798 Nov 20 08:11 read_match.py
-rw-r--r-- 1 ubuntu ubuntu   1078 Nov 20 08:03 read_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    329 Nov 20 08:05 read_options.py
-rw-r--r-- 1 ubuntu ubuntu   6226 Nov 20 08:24 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    185 Nov 20 08:24 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu  19924 Nov 20 08:03 R.fens
-rw-r--r-- 1 ubuntu ubuntu   1073 Nov 20 08:09 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu   1089 Nov 20 08:11 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     28 Nov 20 08:07 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu   3290 Nov 20 08:03 search_set.py
-rw-r--r-- 1 ubuntu ubuntu     78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    161 Nov 20 08:24 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   5172 Nov 20 08:05 uci_options.txt
-rw-r--r-- 1 ubuntu ubuntu    186 Nov 20 08:05 uci_options.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2964 Nov 20 08:02 uci_session.py
```
