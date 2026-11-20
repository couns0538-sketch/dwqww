# Seat 024, idea 24, S32

Idea S32 grades a hash proof inside the null-move tree. I added the check option IdeaS32, default false, and the spin IdeaS32_Slack, default 0 (range 0 to 64). When the check is on, a null-move fail-high is kept at once only when the probe did not return on a hash bound shallower than the parent depth minus the slack; otherwise the cutoff stands only if the reduced re-search also reaches beta, and a pass does not add plies to a stored fail-high.

EXISTS: no. The plain engine returns a null cutoff below depth 14 with no look at the hash depth, and it stores the depth that was searched.

Honesty, exe B, no setoption, from HONESTY_B.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. The same four numbers on exe P are in HONESTY_P.txt.

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 024, idea 24 |
| 2 honesty and baseline | done | HONESTY_B.txt, B_O_d12.sum, B_G_d12.sum | nodes as above; O sum 9500069; G sum 18466239 |
| 3 patch | done | idea.patch.txt | git apply --check passed on a clean base |
| 3 proof off | done | off_O.txt, off_G.txt | O differ 0, G differ 0 |
| 3 proof on | done | on_O.txt | 200 of 200 differ, sum 9547450 |
| 3 uci | done | uci_options_p.txt | IdeaS32 check false, IdeaS32_Slack spin 0 |
| 3 sanitizer | done | asan_G100_d10.meta, asan_G100_scan.txt, asan_poison.raw | nm count 35; clean run 0 lines; poison run reports AddressSanitizer |
| 3 match | done | match.txt, match.pgn | Elo 5.97 +/- 9.47, 1106 games |
| 4 partner | done | partner_compare.txt, partner_match.txt | CONFIRMS; R match Elo 5.21 +/- 9.95, 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1), exe P, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

Proof (2), S14 and IdeaS32 false: O depth 12 differ 0 of 200, sum 9500069. G depth 12 differ 0 of 353, sum 18466239.

Proof (3), S14 and IdeaS32 true, Slack 0: O depth 12 differ 200 of 200, sum 9547450 against the plain sum 9500069.

Proof (4), uci: `option name IdeaS32 type check default false` and `option name IdeaS32_Slack type spin default 0 min 0 max 64`.

Proof (5): AddressSanitizer and UndefinedBehaviorSanitizer build, `nm -C` count of `__asan_` is 35. First 100 of G at depth 10 with the switch on: sum 2083110, AddressSanitizer 0, runtime error 0. A scratch copy with one read past a heap array of 4 ints, on the FEN in poison.fen, run through search_set.py, reports `ERROR: AddressSanitizer: heap-buffer-overflow` and a runtime error on that load.

Match, switch on versus switch off, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours: Elo 5.97 +/- 9.47, 1106 games, 338 wins, 319 losses, 449 draws. The interval includes values below 0 and above 0. I did not treat this as a loss to debug.

Partner is seat 074. `git apply --check` passed, the build's honesty numbers matched, switch false matched exe B on O (differ 0), switch true matched seat 074's own O rows (differ 0, both sums 9547450). The R match was 600 games, Elo 5.21 +/- 9.95. Verdict: CONFIRMS.

suspicions, not proven: The O sum rose by about half a percent. I do not know whether those extra re-searches are the tactical cases the idea is aimed at. Seat 074's O rows matched mine exactly; that fits two deterministic implementations of the same rule, and it is not a claim that the binaries are identical. The match does not show a strength gain.

what I did NOT do: I did not repeat seat 074's G-off run or their sanitizer run. I did not replay their 1106-game match. I did not try Slack values other than 0. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about: A null cutoff is the negation of a low score in the child, so the hash behind it is often an upper bound. Marking only child fail-highs changed nothing; marking every hash cutoff is what moved the node counts. I am not sure a fail-high bubbled up from a grandchild ever changes a null cutoff. The predicted O sum was 11200000, and I said a sum below 9700000 would prove that prediction wrong. The measured sum is 9547450, so that prediction is wrong. The predicted Elo was -15, with the prediction wrong above 20 or below -70. 5.97 sits inside that band.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/024/stamps.txt
?? forge-combo29/grok/024/REPORT.md
?? forge-combo29/grok/024/RESULT.txt
?? forge-combo29/grok/024/asan_G100_scan.txt
?? forge-combo29/grok/024/partner_claimed_O.nodes.txt
?? forge-combo29/grok/024/partner_compare.txt
?? forge-combo29/grok/024/partner_honesty.txt
?? forge-combo29/grok/024/partner_honesty_bench11.meta
?? forge-combo29/grok/024/partner_honesty_bench11.txt
?? forge-combo29/grok/024/partner_honesty_bench13.meta
?? forge-combo29/grok/024/partner_honesty_bench13.txt
?? forge-combo29/grok/024/partner_honesty_bench16.meta
?? forge-combo29/grok/024/partner_honesty_bench16.txt
?? forge-combo29/grok/024/partner_honesty_perft5.meta
?? forge-combo29/grok/024/partner_honesty_perft5.txt
?? forge-combo29/grok/024/partner_match.pgn
?? forge-combo29/grok/024/partner_match.sh
?? forge-combo29/grok/024/partner_match.txt
?? forge-combo29/grok/024/partner_match_summary.txt
?? forge-combo29/grok/024/partner_measure.sh
?? forge-combo29/grok/024/partner_off_O.meta
?? forge-combo29/grok/024/partner_off_O.raw
?? forge-combo29/grok/024/partner_off_O.sum
?? forge-combo29/grok/024/partner_off_O.tsv
?? forge-combo29/grok/024/partner_on_O.meta
?? forge-combo29/grok/024/partner_on_O.raw
?? forge-combo29/grok/024/partner_on_O.sum
?? forge-combo29/grok/024/partner_on_O.tsv
?? forge-combo29/grok/024/tables.txt

$ ls -la forge-combo29/grok/024
total 8464
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu    1030 Nov 20 08:15 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131806 Nov 20 08:15 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:15 asan_G100_d10.sum
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:15 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu      35 Nov 20 09:14 asan_G100_scan.txt
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 08:17 asan_poison.error
-rw-r--r-- 1 ubuntu ubuntu     456 Nov 20 08:18 asan_poison.meta
-rw-r--r-- 1 ubuntu ubuntu   10167 Nov 20 08:17 asan_poison.raw
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  550423 Nov 20 08:01 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      62 Nov 20 08:01 B_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu    3444 Nov 20 08:01 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309315 Nov 20 08:01 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:01 B_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:01 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     663 Nov 20 08:15 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1593 Nov 20 08:18 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:14 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G.epd
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu     951 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu      89 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:14 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:13 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:14 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:13 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:14 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:13 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 08:14 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:13 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:14 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    8946 Nov 20 08:17 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 3575210 Nov 20 08:24 match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1080 Nov 20 08:18 match.sh
-rw-r--r-- 1 ubuntu ubuntu     384 Nov 20 08:26 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu  124829 Nov 20 08:24 match.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O.fens
-rw-r--r-- 1 ubuntu ubuntu      59 Nov 20 08:13 off_compare.txt
-rw-r--r-- 1 ubuntu ubuntu      66 Nov 20 08:15 off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      64 Nov 20 08:15 off_O.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:17 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 08:13 on_compare.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:15 on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 09:09 partner_claimed_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu     138 Nov 20 09:10 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 09:09 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 09:09 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 09:09 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     243 Nov 20 09:10 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu 1594612 Nov 20 09:12 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1018 Nov 20 09:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     381 Nov 20 09:14 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   63381 Nov 20 09:12 partner_match.txt
-rwxr-xr-x 1 ubuntu ubuntu    1039 Nov 20 09:09 partner_measure.sh
-rw-r--r-- 1 ubuntu ubuntu     965 Nov 20 09:09 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309173 Nov 20 09:09 partner_off_O.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 09:09 partner_off_O.sum
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 09:09 partner_off_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     964 Nov 20 09:09 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309178 Nov 20 09:09 partner_on_O.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 09:09 partner_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 09:09 partner_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:13 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  550630 Nov 20 08:13 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      62 Nov 20 08:13 P_off_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu    3444 Nov 20 08:13 P_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     955 Nov 20 08:13 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309503 Nov 20 08:13 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:13 P_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:13 P_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:17 poison.fen
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:13 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309651 Nov 20 08:13 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:13 P_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu    1908 Nov 20 08:13 P_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     652 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19475 Nov 20 08:15 R.epd
-rw-r--r-- 1 ubuntu ubuntu    5786 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:15 R.meta
-rwxr-xr-x 1 ubuntu ubuntu    5749 Nov 20 08:01 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    2244 Nov 20 09:14 tables.txt
-rw-r--r-- 1 ubuntu ubuntu     148 Nov 20 08:14 uci_options_p.txt
-rw-r--r-- 1 ubuntu ubuntu    5037 Nov 20 08:14 uci_p.txt
```
