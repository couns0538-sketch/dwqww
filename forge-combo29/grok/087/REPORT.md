Idea 37, IdeaA6: a negative extension when the singular search fails high.
The plain engine already does that, with the literals -2 and -1, so the check IdeaA6 defaults false and leaves those literals in place.
The spins IdeaA6_FailHigh (default -2) and IdeaA6_Cut (default -1) are read only while the check is true.

EXISTS: forge-combo29/src/search.cpp:1951 (extension -2) and forge-combo29/src/search.cpp:1953 (extension -1).

Honesty, no setoption, exe B and exe P, from HONESTY_B.txt and HONESTY_P.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Table, pasted from make_table.py (table.txt):

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt | seat 087, idea 37, model Grok 4.7, 2026-11-20T07:55:17Z, token 281242682822105
STEP 2 honesty B | done | HONESTY_B.txt | info string bench depth 11 nodes 312866 time 201 nps 1556547
STEP 2 O depth 12 | done | sums.txt | sum 9500069
STEP 2 G depth 12 | done | sums.txt | sum 18466239
proof off O | done | compare_off_O.txt | differ 0
proof off G | done | compare_off_G.txt | differ 0
proof on O defaults | done | compare_on_O.txt | differ 0
proof on spins 0 | done | compare_on_zero_O.txt | differ 200
proof sanitizer clean | done | sanitizer_lines.txt | clean runtime_error 0
proof sanitizer scratch | done | sanitizer_lines.txt | scratch_line /tmp/forge_scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
proof asan symbols | done | asan_nm_count.txt | 35
match 1106 | done | match_result.txt | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
partner apply | done | partner_apply_check.txt | exit 0
partner honesty | done | HONESTY_PARTNER.txt | info string bench depth 11 nodes 312866 time 179 nps 1747854
partner off O | done | partner_compare_off_O.txt | differ 0
partner on vs their rows | done | partner_compare_on_O.txt | differ 0
partner match 600 | done | match_partner.log | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
```

Proofs on exe P:

(1) Honesty with no setoption matches the four known node counts. HONESTY_P.txt.
(2) S14 and IdeaA6 false: O depth 12 differs in 0 of 200 from exe B, G depth 12 differs in 0 of 353. compare_off_O.txt, compare_off_G.txt. O sum 9500069, first three 41311, 24872, 28574. G sum 18466239.
(3) S14 and IdeaA6 true, spins at default -2 and -1: O depth 12 differs in 0 of 200. compare_on_O.txt. Sum 9500069. That is the same extension as today, so the zero is not a dead option. The same switch with IdeaA6_FailHigh 0 and IdeaA6_Cut 0 differs in 200 of 200, sum 11912888. compare_on_zero_O.txt.
(4) uci lists `option name IdeaA6 type check default false`, `option name IdeaA6_FailHigh type spin default -2 min -6 max 2`, `option name IdeaA6_Cut type spin default -1 min -6 max 2`. uci_p_idea.txt.
(5) ASan+UBSan build, nm -C count of __asan_ is 35 (asan_nm_count.txt, also in P_asan_G100_d10.txt.meta). First 100 of G at depth 10 with IdeaA6 true: 0 runtime-error lines and 0 AddressSanitizer lines. The scratch engine, one heap read past the end on the special FEN, run with the same measure_set.py, printed: `/tmp/forge_scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'`. sanitizer_lines.txt.

git apply --check of idea.patch.txt on the base commit exited 0. apply_check.txt.

Match, exe P IdeaA6 true against exe P IdeaA6 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games, concurrency 3. From match_result.txt: Elo -0.00 +/- 0.00, Games 1106, Wins 336, Losses 336, Draws 434, Points 553.0 (50.00 %), Ptnml(0-2) [0, 0, 553, 0, 0]. The prediction was sum 9500069 and Elo 0. Both stand.

Partner is seat 037 (idea 37; 137 is past 120). Commit dc16f1e927e57fee830653a35f9c59fdbede97fd. Verdict CONFIRMS. The patch applies (exit 0). Honesty numbers match. Switch false O depth 12 differs in 0 of 200 from exe B. Switch true O depth 12 differs in 0 of 200 from the partner's own P_on_O_d12.tsv. Their claim for that file is differ 0, and the measured rows are those rows. The 300 R openings, both colours, 600 games, their switch true against false: Elo -0.00 +/- 0.00, Wins 280, Losses 280, Draws 40, Ptnml [0, 0, 300, 0, 0]. match_partner_result.txt. They also reported Elo -0.00 +/- 0.00 on their 1106-game OG match. I did not replay that list.

suspicions, not proven: setting both spins to 0 searches more nodes (11912888 against 9500069). I did not play a match at those spins, so I do not know if removing the negative extension wins or loses.

What I did NOT do: a match with the spins off today's -2 and -1. A replay of the partner's 1106-game OG match. I started the partner check before minute 75 because step 3 was finished and their patch was already on the branch. The minute-60 handoff read is recorded in handoff_60.txt if that file is in the listing below; if it is absent, that read had not been done when this report was first written.

What I am NOT sure about: RESULT on_differs is 0, the switch-true count at the default spins. The spins-at-0 count is 200. Both are measured. The scratch report is a UBSan runtime error on that out-of-bounds load, and the binary has 35 __asan_ symbols. The text "ERROR: AddressSanitizer" does not appear.

times: see stamps.txt


```
$ git status --short
?? config.json
?? forge-combo29/grok/087/HONESTY_PARTNER.txt
?? forge-combo29/grok/087/REPORT.md
?? forge-combo29/grok/087/RESULT.txt
?? forge-combo29/grok/087/compare_partner_on.py
?? forge-combo29/grok/087/honesty_partner.sh
?? forge-combo29/grok/087/make_table.py
?? forge-combo29/grok/087/match_partner.log
?? forge-combo29/grok/087/match_partner.meta
?? forge-combo29/grok/087/match_partner.pgn
?? forge-combo29/grok/087/match_partner.sh
?? forge-combo29/grok/087/match_partner_result.txt
?? forge-combo29/grok/087/partner_037_on_O.tsv
?? forge-combo29/grok/087/partner_apply_check.txt
?? forge-combo29/grok/087/partner_bench11.meta
?? forge-combo29/grok/087/partner_bench11.txt
?? forge-combo29/grok/087/partner_bench13.meta
?? forge-combo29/grok/087/partner_bench13.txt
?? forge-combo29/grok/087/partner_bench16.meta
?? forge-combo29/grok/087/partner_bench16.txt
?? forge-combo29/grok/087/partner_compare_off_O.txt
?? forge-combo29/grok/087/partner_compare_on_O.txt
?? forge-combo29/grok/087/partner_compare_on_vs_B.txt
?? forge-combo29/grok/087/partner_off_O_d12.txt
?? forge-combo29/grok/087/partner_off_O_d12.txt.meta
?? forge-combo29/grok/087/partner_off_O_d12.txt.rows
?? forge-combo29/grok/087/partner_on_O_d12.txt
?? forge-combo29/grok/087/partner_on_O_d12.txt.meta
?? forge-combo29/grok/087/partner_on_O_d12.txt.rows
?? forge-combo29/grok/087/partner_perft5.meta
?? forge-combo29/grok/087/partner_perft5.txt
?? forge-combo29/grok/087/table.txt

$ ls -la forge-combo29/grok/087
total 10060
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:25 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 08:05 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:08 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu  549695 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     841 Nov 20 08:03 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:03 B_G_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  308846 Nov 20 08:03 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:03 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:03 B_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     146 Nov 20 08:12 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     146 Nov 20 08:12 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:12 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:12 compare_on_zero_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1299 Nov 20 08:20 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    1138 Nov 20 08:05 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1110 Nov 20 08:07 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:08 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:02 G.epd
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1188 Nov 20 08:01 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     712 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1129 Nov 20 08:20 honesty_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     701 Nov 20 08:20 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:05 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:05 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:05 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 08:05 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1188 Nov 20 08:05 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     712 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    5068 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1505 Nov 20 08:12 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    2510 Nov 20 08:25 make_table.py
-rw-r--r-- 1 ubuntu ubuntu  133292 Nov 20 08:17 match.log
-rw-r--r-- 1 ubuntu ubuntu     322 Nov 20 08:11 match.meta
-rw-r--r-- 1 ubuntu ubuntu   65135 Nov 20 08:23 match_partner.log
-rw-r--r-- 1 ubuntu ubuntu     294 Nov 20 08:21 match_partner.meta
-rw-r--r-- 1 ubuntu ubuntu 1810506 Nov 20 08:23 match_partner.pgn
-rw-r--r-- 1 ubuntu ubuntu     379 Nov 20 08:25 match_partner_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1462 Nov 20 08:21 match_partner.sh
-rw-r--r-- 1 ubuntu ubuntu 4533302 Nov 20 08:17 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     383 Nov 20 08:19 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1463 Nov 20 08:12 match_r.sh
-rw-r--r-- 1 ubuntu ubuntu    1704 Nov 20 08:10 match.sh
-rw-r--r-- 1 ubuntu ubuntu    5012 Nov 20 08:07 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:02 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:11 OG.epd
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:20 partner_037_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu      85 Nov 20 08:21 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:20 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:20 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:20 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:20 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 08:20 partner_compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     159 Nov 20 08:20 partner_compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:20 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu  309252 Nov 20 08:20 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:20 partner_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:20 partner_off_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  309309 Nov 20 08:20 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     878 Nov 20 08:20 partner_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:20 partner_on_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:20 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:20 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  131836 Nov 20 08:08 P_asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     965 Nov 20 08:08 P_asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    6382 Nov 20 08:08 P_asan_G100_d10.txt.rows
-rw-r--r-- 1 ubuntu ubuntu    7320 Nov 20 08:09 P_asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:09 P_asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  549838 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:05 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:05 P_off_G_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  309065 Nov 20 08:05 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 08:05 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:05 P_off_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  309077 Nov 20 08:06 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:06 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:06 P_on_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu  309653 Nov 20 08:06 P_on_zero_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     948 Nov 20 08:06 P_on_zero_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   15761 Nov 20 08:06 P_on_zero_O_d12.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     588 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19160 Nov 20 08:12 R.epd
-rw-r--r-- 1 ubuntu ubuntu    6872 Nov 20 08:26 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 08:25 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 08:19 sanitizer_lines.txt
-rw-r--r-- 1 ubuntu ubuntu    3409 Nov 20 08:08 sanitizer_run.sh
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     537 Nov 20 08:19 show_match.py
-rw-r--r-- 1 ubuntu ubuntu     862 Nov 20 08:12 show_sanitizer.py
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:09 special.fen
-rw-r--r-- 1 ubuntu ubuntu      84 Nov 20 08:19 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     918 Nov 20 08:02 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu     514 Nov 20 08:12 sums.txt
-rw-r--r-- 1 ubuntu ubuntu    1373 Nov 20 08:25 table.txt
-rw-r--r-- 1 ubuntu ubuntu     623 Nov 20 08:05 uci_options.sh
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:05 uci_p_idea.txt
-rw-r--r-- 1 ubuntu ubuntu    5096 Nov 20 08:05 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:05 uci_p.txt.meta
```
