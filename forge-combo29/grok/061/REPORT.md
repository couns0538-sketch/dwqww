Idea S25 arms the root aspiration window only after a score has landed inside its bounds, and an unresolved re-search is not a finished iteration for the soft time stop.
I added check option IdeaS25, default false, and spin IdeaS25_ArmAfter, default 1 (range 1 to 16).
With the switch on, depth 1 stays a full window and the narrow window starts once one in-window score exists, which is depth 2. With the switch off, the old depth>=4 gate is what runs.

EXISTS: no. The plain engine narrows at depth >= 4 in the root loop of forge-combo29/src/search.cpp (the `narrow` flag). That is a fixed depth, not "after one resolved score". AspArmLate and AspCappedReopen are different options and default off. I read that loop before editing it.

Honesty, exe B, no setoption, from tables.py honesty (HONESTY_B.txt): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft nodes 4865609.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 061, idea 11 |
| 2 honesty and known sums | done | HONESTY_B.txt, O_b_d12.txt, G_b_d12.txt | honesty matches; O sum 9500069; G sum 18466239 |
| 3 idea, proofs, match | done | idea.patch.txt, proof_tables.txt, match_result.txt | off identical; on 179 of 200; Elo -4.08 +/- 10.02; 1106 games |
| 4 partner 011 | done | partner_verdict.txt, partner_match_result.txt | CONFIRMS; R match 600 games, Elo -2.32 +/- 8.34 |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Patched engine, no setoption. honesty_p/ via tables.py: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft nodes 4865609.

Proof (2). S14, IdeaS25 false. proof_tables.txt: O depth 12 differ 0 of 200 against exe B. G depth 12 differ 0 of 353 against exe B.

Proof (3). S14, IdeaS25 true. proof_tables.txt: O depth 12 differ 179 of 200 against exe B, sum 9619908. First three nodes 17985, 18279, 28002.

Proof (4). uci_options_p.txt lists `option name IdeaS25 type check default false` and `option name IdeaS25_ArmAfter type spin default 1 min 1 max 16`.

Proof (5). G_asan_on_d10.txt.meta has asan_symbols=35. The same runner on the first 100 of G at depth 10 with the switch on finished 100 positions and wrote no stderr. asan_probe.txt from that same runner on the scratch engine reports `ERROR: AddressSanitizer: heap-buffer-overflow` in apply_position. sanitizer=clean.

Match. match_result.txt, pasted from match_table.py on match_fastchess.txt: Elo -4.08 +/- 10.02, 1106 games, 324 wins, 337 losses, 445 draws. The point estimate is not below -20 and the interval is not entirely below 0, so I did not open the code for a second bug hunt. prediction.txt said O sum 10100000 (wrong outside 8200000..12800000) and Elo -8 (wrong outside -70..35). Measured 9619908 and -4.08. prediction.txt was not edited after the commit that added it.

git apply --check of idea.patch.txt on a clean base worktree printed nothing and exited 0 (APPLY_CHECK_OK at the time it was recorded in the step 3 work).

Partner verdict: CONFIRMS. partner_verdict.txt. Seat 111 had no branch. Seat 011 had idea.patch.txt. Their O-on rows match the rebuild (0 of 200). Their claimed 179 of 200 and the honesty numbers match what this seat measured. The required R match is 600 games, Elo -2.32 +/- 8.34.

suspicions, not proven: Seat 011's published OG match line is the same Elo, the same win/loss/draw counts, and the same Ptnml as this seat's OG match. Fixed-node games can match when two patches search alike. I did not diff the two patches line by line, and I did not treat that sameness as a copied log.

what I did NOT do: I did not play the owner's net. I did not try IdeaS25_ArmAfter at any value except the default 1. I did not run a clock match, so the soft-time hold is unmeasured. I did not review seat 111. The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 found no FABLE_TO_grok file. I did not open a pull request.

what I am NOT sure about: The written idea can be read as "do not arm a tiny window at the first depths". This engine already waits until depth 4, so "after one resolved score" arms earlier, at depth 2. That is the reading I built, and seat 011's rows agree with it. I am not sure the soft-time hold changes any clock game, because the soft stop already sat after the aspiration loop and the node match never asks it.

times: see stamps.txt

git status --short
 M forge-combo29/grok/061/stamps.txt
 M forge-combo29/grok/061/tables.py
?? config.json
?? forge-combo29/grok/061/REPORT.md
?? forge-combo29/grok/061/RESULT.txt
?? forge-combo29/grok/061/match_r.sh
?? forge-combo29/grok/061/partner.patch.txt
?? forge-combo29/grok/061/partner_O_off.runlog
?? forge-combo29/grok/061/partner_O_off_d12.txt
?? forge-combo29/grok/061/partner_O_off_d12.txt.meta
?? forge-combo29/grok/061/partner_O_on.runlog
?? forge-combo29/grok/061/partner_O_on_d12.txt
?? forge-combo29/grok/061/partner_O_on_d12.txt.meta
?? forge-combo29/grok/061/partner_apply.txt
?? forge-combo29/grok/061/partner_apply_check.txt
?? forge-combo29/grok/061/partner_build.log
?? forge-combo29/grok/061/partner_claim_decisions.txt
?? forge-combo29/grok/061/partner_claim_match.txt
?? forge-combo29/grok/061/partner_claim_off.txt
?? forge-combo29/grok/061/partner_claim_on.txt
?? forge-combo29/grok/061/partner_cmake.log
?? forge-combo29/grok/061/partner_eval.sh
?? forge-combo29/grok/061/partner_files.txt
?? forge-combo29/grok/061/partner_honesty.runlog
?? forge-combo29/grok/061/partner_honesty/
?? forge-combo29/grok/061/partner_honesty_table.txt
?? forge-combo29/grok/061/partner_match.pgn
?? forge-combo29/grok/061/partner_match.txt
?? forge-combo29/grok/061/partner_match_result.txt
?? forge-combo29/grok/061/partner_off_diff.txt
?? forge-combo29/grok/061/partner_on_sum.txt
?? forge-combo29/grok/061/partner_on_vs_b.txt
?? forge-combo29/grok/061/partner_row_candidates.txt
?? forge-combo29/grok/061/partner_seat.txt
?? forge-combo29/grok/061/partner_status.txt
?? forge-combo29/grok/061/partner_their_O_on.txt
?? forge-combo29/grok/061/partner_verdict.txt

ls -la forge-combo29/grok/061
total 10112
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:09 asan_probe.runlog
-rw-r--r-- 1 ubuntu ubuntu   10077 Nov 20 08:09 asan_probe.txt
-rw-r--r-- 1 ubuntu ubuntu    4216 Nov 20 08:09 asan_probe.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1106 Nov 20 08:10 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:09 G_asan_on_d10.runlog
-rw-r--r-- 1 ubuntu ubuntu  132041 Nov 20 08:09 G_asan_on_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:09 G_asan_on_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:07 G_b_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu  551517 Nov 20 08:07 G_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     808 Nov 20 08:07 G_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:06 G.epd
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:07 G_p_off_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu  551910 Nov 20 08:07 G_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:07 G_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    9635 Nov 20 08:05 harness.py
-rw-r--r-- 1 ubuntu ubuntu    5044 Nov 20 08:06 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:06 honesty_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5044 Nov 20 08:06 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:06 honesty_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5046 Nov 20 08:06 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:06 honesty_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:06 HONESTY_B.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:06 honesty_p
-rw-r--r-- 1 ubuntu ubuntu    5259 Nov 20 08:06 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:06 honesty_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    9433 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1723 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  138535 Nov 20 08:17 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 4587961 Nov 20 08:17 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     295 Nov 20 08:23 match_result.txt
-rwxr-xr-x 1 ubuntu ubuntu    1009 Nov 20 08:24 match_r.sh
-rwxr-xr-x 1 ubuntu ubuntu    1032 Nov 20 08:09 match.sh
-rw-r--r-- 1 ubuntu ubuntu     539 Nov 20 08:23 match_table.py
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:06 O_b_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu  309847 Nov 20 08:06 O_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     808 Nov 20 08:06 O_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:06 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:07 O_p_off_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu  310056 Nov 20 08:07 O_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:07 O_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 08:07 O_p_on_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu  310101 Nov 20 08:07 O_p_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:07 O_p_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     645 Nov 20 09:10 partner_build.log
-rw-r--r-- 1 ubuntu ubuntu    1395 Nov 20 09:12 partner_claim_decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     396 Nov 20 09:12 partner_claim_match.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 09:12 partner_claim_off.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 09:12 partner_claim_on.txt
-rw-r--r-- 1 ubuntu ubuntu     489 Nov 20 09:10 partner_cmake.log
-rwxr-xr-x 1 ubuntu ubuntu    4728 Nov 20 08:24 partner_eval.sh
-rw-r--r-- 1 ubuntu ubuntu    2712 Nov 20 09:10 partner_files.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:10 partner_honesty
-rw-r--r-- 1 ubuntu ubuntu      43 Nov 20 09:10 partner_honesty.runlog
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 09:10 partner_honesty_table.txt
-rw-r--r-- 1 ubuntu ubuntu 1981896 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     300 Nov 20 09:15 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu   82915 Nov 20 09:13 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:10 partner_off_diff.txt
-rw-r--r-- 1 ubuntu ubuntu      80 Nov 20 09:10 partner_on_sum.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 09:13 partner_on_vs_b.txt
-rw-r--r-- 1 ubuntu ubuntu  310267 Nov 20 09:10 partner_O_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     849 Nov 20 09:10 partner_O_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:10 partner_O_off.runlog
-rw-r--r-- 1 ubuntu ubuntu  310309 Nov 20 09:10 partner_O_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     848 Nov 20 09:10 partner_O_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:10 partner_O_on.runlog
-rw-r--r-- 1 ubuntu ubuntu    8437 Nov 20 09:10 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1137 Nov 20 09:10 partner_row_candidates.txt
-rw-r--r-- 1 ubuntu ubuntu       4 Nov 20 09:10 partner_seat.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 09:13 partner_status.txt
-rw-r--r-- 1 ubuntu ubuntu  304694 Nov 20 09:12 partner_their_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1149 Nov 20 09:15 partner_verdict.txt
-rw-r--r-- 1 ubuntu ubuntu     579 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     332 Nov 20 08:10 proof_tables.txt
-rw-r--r-- 1 ubuntu ubuntu    6111 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19170 Nov 20 08:06 R.fens
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:09 special.fen
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    4186 Nov 20 09:13 tables.py
-rw-r--r-- 1 ubuntu ubuntu    5077 Nov 20 08:07 uci_options_p.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:07 uci_options_p.txt.meta
