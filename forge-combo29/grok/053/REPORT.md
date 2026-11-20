# Seat 053, idea 3, S38

S38 adds a signed fraction of a ply, from the eval correction, to the reduction of a quiet move: reduce more when results came back worse than the uncorrected eval, and less when they came back better.
The plain engine already does that when LmrSignedCorrection is true, dividing by 64 and clamping to one ply.
I added the check IdeaS38 (default false) as another gate on that formula, and the spins IdeaS38_Divisor (default 64) and IdeaS38_Clamp (default 1). With IdeaS38 false the new term is not applied. With IdeaS38 true and the spins left at the defaults, the formula is the one already in the engine.

EXISTS: yes, forge-combo29/src/search.cpp:2003. The formula is include/forge/search.hpp:362. The on/off option already existed as LmrSignedCorrection, default false. The numbers 64 and 1 were not options.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Table from report_numbers.py:

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 053, idea 3, model Grok 4.7, 2026-11-20T07:53:34Z, token 45201400732411
honesty B | done | HONESTY_B.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK | PASS
baseline O d12 | done | B_O_d12.sum.txt | sum=9500069
baseline G d12 | done | B_G_d12.sum.txt | sum=18466239
prediction | done | prediction.txt | committed before measuring
patch applies | done | apply_check.txt | git apply --check: ok
honesty P | done | HONESTY_P.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK | PASS
uci options | done | uci_options_p.txt | option name IdeaS38 type check default false YES | option name IdeaS38_Divisor type spin default 64 min 1 max 4096 YES | option name IdeaS38_Clamp type spin default 1 min 0 max 8 YES
proof off O | done | cmp_off_O.txt | off_O positions 200 differ 0
proof off G | done | cmp_off_G.txt | off_G positions 353 differ 0
proof on O | done | cmp_on_O.txt | on_O positions 200 differ 3 | first_differ 114 127 191 sum=9501220
sanitizer clean | done | asan_G100_d10.meta | nm_asan_symbol_lines=35 crashed= asan_lines=0 tag=asan_G100_d10 positions=100 depth=10 switch=true sum=2091663 first3=10526 11083 31798
sanitizer trap | done | scratch_special.raw.txt | SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/scratch/forge-combo29/src/uci.cpp:47 in apply_position
match O+G | done | match_OG.summary.txt | elo=3.14 | err=8.26 | games_line=1106 | wins=349 | losses=339 | draws=418 | pgn_result_headers=1106 | fastchess_finished_games=1106 | bad_lines=0
partner apply | done | partner_apply_check.txt | APPLY_CHECK_OK
partner honesty | done | partner_honesty.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK | PASS
partner nodes | done | partner_compare.txt | partner_off_vs_my_B positions 200 differ 0 sum_off 9500069 sum_B 9500069 | partner_on_vs_claim positions 200 differ 0 sum_on 9501220 sum_claim 9501220 | partner_on_vs_my_B differ 3 first [114, 127, 191]
partner match | done | partner_match.summary.txt | elo=-0.58 | err=8.87 | games_line=600 | wins=253 | losses=254 | draws=93 | pgn_result_headers=600 | finished_lines=600
```

Proofs on exe P:

(1) HONESTY_P.txt PASS. bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.
(2) S14, IdeaS38 false: O depth 12 matches exe B on all 200 positions, sum 9500069, first three 41311 / 24872 / 28574. G depth 12 matches exe B on all 353 positions, sum 18466239.
(3) S14, IdeaS38 true: O depth 12 differs on 3 of 200 positions (114, 127, 191), sum 9501220.
(4) The uci listing contains `option name IdeaS38 type check default false`, `option name IdeaS38_Divisor type spin default 64 min 1 max 4096`, and `option name IdeaS38_Clamp type spin default 1 min 0 max 8`.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, `nm -C` count of `__asan_` symbols = 35. First 100 of G at depth 10 with IdeaS38 true: 0 AddressSanitizer lines and 0 runtime-error lines, node sum 2091663. The same measure_set.py on a scratch copy that reads one int past a four-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 99` reports `SUMMARY: AddressSanitizer: heap-buffer-overflow` in apply_position. idea.patch.txt does not contain that read. `git apply --check` of idea.patch.txt on a fresh base printed `git apply --check: ok`.

Match: exe P with IdeaS38 true against exe P with IdeaS38 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O and G (553), both colours, 1106 games, fastchess concurrency 3. Elo 3.14 +/- 8.26, wins 349, losses 339, draws 418. The point is above -20 and the interval is not entirely below 0, so I did not open the code looking for a match bug. The prediction file said O-on sum 9280000, wrong outside 8200000..10800000, and Elo +4, wrong below -30 or above +40. The measured sum 9501220 and Elo 3.14 sit inside those ranges.

Partner: seat 103, the next seat with idea 3 that had a branch. Their patch applies (`partner_apply_check.txt`). Their release build passes the four honesty numbers. With LmrSignedCorrection false, O depth 12 matches my exe B, 0 of 200, sum 9500069. With LmrSignedCorrection true, O depth 12 matches their own P_on_O_d12.nodes on all 200 positions, sum 9501220, and differs from exe B on the same three positions they named (114, 127, 191). A match of their switch on my 300 R openings, both colours, 600 games: Elo -0.58 +/- 8.87, wins 253, losses 254, draws 93. Verdict: CONFIRMS.

suspicions, not proven:

Their published 1106-game summary has the same Elo, error, wins, losses and draws as my O+G match. I played that match before fetching their branch. Fixed nodes and one thread make the same opening and the same formula play the same game, and their default spins are the same formula as IdeaS38 on. I did not compare the two PGNs move by move.
I did not record the correction value on positions 114, 127 and 191, so the node changes are the evidence that the term ran, not a trace of which quiet moves it changed.

what I did NOT do:

No pull request. The only branch pushed is for-fable-and-opus/grok-053.
I did not try a divisor or a clamp other than 64 and 1.
I did not replay seat 103's 1106-game match. I did not run their search_set.py.
The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 had no FABLE_TO_grok file.
A __pycache__ bytecode file was committed with the step 3 proofs and removed in the following commit. It is not in the tree.

what I am NOT sure about:

The list names the check IdeaS38. The engine already had LmrSignedCorrection. I added IdeaS38 as a second gate. Seat 103 left the check as LmrSignedCorrection and only added the two spins. Both off paths match exe B.
The 1106-game interval includes 0, so 3.14 Elo is not a measured gain.

times: see stamps.txt


```
$ git status --short
AM forge-combo29/grok/053/REPORT.md
A  forge-combo29/grok/053/RESULT.txt
A  forge-combo29/grok/053/config.json
M  forge-combo29/grok/053/measure_set.py
A  forge-combo29/grok/053/partner_103_P_on_O_d12.nodes
A  forge-combo29/grok/053/partner_103_compare_on_O.txt
A  forge-combo29/grok/053/partner_103_idea.patch.txt
A  forge-combo29/grok/053/partner_apply_check.txt
A  forge-combo29/grok/053/partner_compare.txt
A  forge-combo29/grok/053/partner_honesty.txt
A  forge-combo29/grok/053/partner_honesty_bench11.meta
A  forge-combo29/grok/053/partner_honesty_bench11.txt
A  forge-combo29/grok/053/partner_honesty_bench13.meta
A  forge-combo29/grok/053/partner_honesty_bench13.txt
A  forge-combo29/grok/053/partner_honesty_bench16.meta
A  forge-combo29/grok/053/partner_honesty_bench16.txt
A  forge-combo29/grok/053/partner_honesty_perft5.meta
A  forge-combo29/grok/053/partner_honesty_perft5.txt
A  forge-combo29/grok/053/partner_match.exe.sha
A  forge-combo29/grok/053/partner_match.fastchess.txt
A  forge-combo29/grok/053/partner_match.meta
A  forge-combo29/grok/053/partner_match.pgn
A  forge-combo29/grok/053/partner_match.summary.txt
A  forge-combo29/grok/053/partner_off_O_d12.meta
A  forge-combo29/grok/053/partner_off_O_d12.nodes.tsv
A  forge-combo29/grok/053/partner_off_O_d12.raw.txt
A  forge-combo29/grok/053/partner_off_O_d12.sum.txt
A  forge-combo29/grok/053/partner_on_O_d12.meta
A  forge-combo29/grok/053/partner_on_O_d12.nodes.tsv
A  forge-combo29/grok/053/partner_on_O_d12.raw.txt
A  forge-combo29/grok/053/partner_on_O_d12.sum.txt
A  forge-combo29/grok/053/report_numbers.py
A  forge-combo29/grok/053/report_table.txt
A  forge-combo29/grok/053/run_partner_match.sh
M  forge-combo29/grok/053/stamps.txt

$ ls -la forge-combo29/grok/053
total 5004
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     927 Nov 20 08:06 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    2600 Nov 20 08:06 asan_G100_d10.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  132645 Nov 20 08:06 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      90 Nov 20 08:06 asan_G100_d10.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    9462 Nov 20 08:02 B_G_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  552661 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      86 Nov 20 08:02 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     868 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:01 B_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  307314 Nov 20 08:01 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      84 Nov 20 08:01 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:02 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:02 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:02 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    7332 Nov 20 09:14 config.json
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    2193 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2354 Nov 20 08:02 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6405 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1155 Nov 20 08:09 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    7367 Nov 20 08:14 match_OG.config.json
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:08 match_OG.exe.sha
-rw-r--r-- 1 ubuntu ubuntu  108029 Nov 20 08:14 match_OG.fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 08:14 match_OG.meta
-rw-r--r-- 1 ubuntu ubuntu 1036482 Nov 20 08:14 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:16 match_OG.summary.txt
-rwxr-xr-x 1 ubuntu ubuntu    6348 Nov 20 09:10 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 09:09 partner_103_compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    3413 Nov 20 09:09 partner_103_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:09 partner_103_P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:10 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:10 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:10 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5114 Nov 20 09:10 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:10 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5114 Nov 20 09:10 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:10 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5116 Nov 20 09:10 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:10 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5327 Nov 20 09:10 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 09:10 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 09:11 partner_match.exe.sha
-rw-r--r-- 1 ubuntu ubuntu   54153 Nov 20 09:14 partner_match.fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu     255 Nov 20 09:14 partner_match.meta
-rw-r--r-- 1 ubuntu ubuntu  568454 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     105 Nov 20 09:15 partner_match.summary.txt
-rw-r--r-- 1 ubuntu ubuntu     946 Nov 20 09:10 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 09:10 partner_off_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  308945 Nov 20 09:10 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      95 Nov 20 09:10 partner_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     944 Nov 20 09:10 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 09:10 partner_on_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  308908 Nov 20 09:10 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      93 Nov 20 09:10 partner_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     900 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    9462 Nov 20 08:02 P_off_G_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  555462 Nov 20 08:02 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      91 Nov 20 08:02 P_off_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:02 P_off_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  308948 Nov 20 08:02 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      89 Nov 20 08:02 P_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     902 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5323 Nov 20 08:02 P_on_O_d12.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu  308925 Nov 20 08:02 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      87 Nov 20 08:02 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     458 Nov 20 07:58 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   20115 Nov 20 08:09 R300.epd
-rw-r--r-- 1 ubuntu ubuntu    8896 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3121 Nov 20 09:16 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    2503 Nov 20 09:16 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:17 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1634 Nov 20 08:08 run_match_og.sh
-rwxr-xr-x 1 ubuntu ubuntu    1510 Nov 20 08:55 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     960 Nov 20 08:05 scratch_special.meta
-rw-r--r-- 1 ubuntu ubuntu      27 Nov 20 08:05 scratch_special.nodes.tsv
-rw-r--r-- 1 ubuntu ubuntu    8686 Nov 20 08:05 scratch_special.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      69 Nov 20 08:05 scratch_special.sum.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:02 uci_options_p.txt
```
