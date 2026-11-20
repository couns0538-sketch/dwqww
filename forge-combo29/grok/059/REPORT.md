# Seat 059, idea 9, S23

S23 is a capped re-open of the root aspiration window after a fail.
The engine already does that behind the check AspCappedReopen, default false, and the patch only turns the fixed widths 13 and 640 into spins left at those defaults.
AspCappedReopen_Margin defaults to 13 (min 1, max 1000) and AspCappedReopen_Decisive defaults to 640 (min 1, max 10000).

EXISTS: yes:forge-combo29/src/search.cpp:2128. The constexpr AspReopenMargin 13 and AspDecisiveScore 640 sat next to capped_fail_low and capped_fail_high. The check is already a UCI option, AspCappedReopen, default false (search.cpp:103, uci.cpp:227). The fixed numbers were not options. I did not add a second check named IdeaS23.

Honesty, no setoption, exe B and exe P and the partner build: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Each line is PASS in HONESTY_B.txt, HONESTY_P.txt, and HONESTY_PARTNER.txt.

The table and the numbers under it are the pasted output of report_tables.py, which reads the raw files.

```
HONESTY_B
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=Chess Engine Forge 6.4.24 candidate
bench 11 nodes 312866 expected 312866 ok
bench 13 nodes 862329 expected 862329 ok
bench 16 nodes 3024920 expected 3024920 ok
go perft 5 nodes 4865609 expected 4865609 ok
PASS
HONESTY_P
exe=/agent/repos/work/forge-combo29/build/forge
sha256=ae8e1d1b45dfc603943304eed224a768516f610c648a62c984659565b19d77a5
id_name=Chess Engine Forge 6.4.24 candidate
bench 11 nodes 312866 expected 312866 ok
bench 13 nodes 862329 expected 862329 ok
bench 16 nodes 3024920 expected 3024920 ok
go perft 5 nodes 4865609 expected 4865609 ok
PASS
HONESTY_PARTNER
exe=/agent/repos/partner/forge-combo29/build/forge
sha256=aeeb1198f5b147f0674d9c76387e5b7d2e7b8376da8b5374078dd5fde46358e8
id_name=Chess Engine Forge 6.4.24 candidate
bench 11 nodes 312866 expected 312866 ok
bench 13 nodes 862329 expected 862329 ok
bench 16 nodes 3024920 expected 3024920 ok
go perft 5 nodes 4865609 expected 4865609 ok
PASS
NODES
B_O.nodes first 1 41311 2 24872 3 28574 sum 9500069 count 200
B_G.nodes first 1 37203 2 70845 3 144383 sum 18466239 count 353
P_off_O.nodes first 1 41311 2 24872 3 28574 sum 9500069 count 200
P_off_G.nodes first 1 37203 2 70845 3 144383 sum 18466239 count 353
P_on_O.nodes first 1 21210 2 24516 3 34920 sum 9449926 count 200
partner_off_O.nodes first 1 41311 2 24872 3 28574 sum 9500069 count 200
partner_on_O.nodes first 1 21210 2 24516 3 34920 sum 9449926 count 200
COMPARE
-- proof_off_O.txt
positions 200
differ 0
same 200
-- proof_off_G.txt
positions 353
differ 0
same 353
-- proof_on_O.txt
positions 200
differ 150
same 50
example 1 41311 21210
example 2 24872 24516
example 3 28574 34920
example 4 27838 32684
example 6 43043 39170
-- partner_off_vs_B.txt
positions 200
differ 0
same 200
-- partner_on_vs_B.txt
positions 200
differ 150
same 50
example 1 41311 21210
example 2 24872 24516
example 3 28574 34920
example 4 27838 32684
example 6 43043 39170
-- partner_on_vs_theirs.txt
mine 200 partner 200
differ 0
same 200
UCI
option name AspCappedReopen type check default false
option name AspCappedReopen_Margin type spin default 13 min 1 max 1000
option name AspCappedReopen_Decisive type spin default 640 min 1 max 10000
ASAN_G100
exe=/agent/repos/work/forge-combo29/build-asan/forge
failed=None
nm_asan_symbols=35
sanitizer_lines=0
ASAN_CANARY
exe=/tmp/canary-engine/build-asan/forge
failed=engine exited 1; last=[]
nm_asan_symbols=35
sanitizer_lines=1
sanitizer_line=/tmp/canary-engine/src/uci.cpp:47:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
MATCH
Results of on vs off (20000 nodes, 1t, 16MB, match_openings.epd):
Elo: -7.23 +/- 10.57, nElo: -14.01 +/- 20.48
LOS: 8.99 %, DrawRatio: 62.93 %, PairsRatio: 0.83
Games: 1106, Wins: 329, Losses: 352, Draws: 425, Points: 541.5 (48.96 %)
Ptnml(0-2): [17, 95, 348, 80, 13], WL/DD Ratio: 1.78
--------------------------------------------------
Finished match
finished_games 1106
pgn_events 1106
rounds 553 games 2 concurrency 3
engine on nodes 20000 [['AspCappedReopen', 'true'], ['Threads', '1'], ['Hash', '16'], ['NonPawnCorrection', 'true']]
engine off nodes 20000 [['AspCappedReopen', 'false'], ['Threads', '1'], ['Hash', '16'], ['NonPawnCorrection', 'true']]
PARTNER_MATCH
Results of on vs off (20000 nodes, 1t, 16MB, R300.epd):
Elo: -11.01 +/- 9.63, nElo: -31.81 +/- 27.80
LOS: 1.25 %, DrawRatio: 83.67 %, PairsRatio: 0.58
Games: 600, Wins: 261, Losses: 280, Draws: 59, Points: 290.5 (48.42 %)
Ptnml(0-2): [7, 24, 251, 17, 1], WL/DD Ratio: 26.89
--------------------------------------------------
Finished match
finished_games 600
pgn_events 600
rounds 300 games 2 concurrency 3
engine on nodes 20000 [['AspCappedReopen', 'true'], ['Threads', '1'], ['Hash', '16'], ['NonPawnCorrection', 'true']]
engine off nodes 20000 [['AspCappedReopen', 'false'], ['Threads', '1'], ['Hash', '16'], ['NonPawnCorrection', 'true']]
APPLY
git apply --check: ok
git apply --check: ok
TABLE
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 059, idea 9, model Grok 4.7, 2026-11-20T07:54:21Z, token 82131824422593
STEP 2 honesty B | done | HONESTY_B.txt | PASS
STEP 2 O and G | done | B_O.nodes B_G.nodes | O 9500069 G 18466239
STEP 3 prediction | done | prediction.txt | committed before any P measurement
STEP 3 patch | done | idea.patch.txt apply_check.txt | git apply --check: ok
proof 1 honesty P | done | HONESTY_P.txt | PASS
proof 2 switch off | done | proof_off_O.txt proof_off_G.txt | O differ 0 G differ 0
proof 3 switch on | done | proof_on_O.txt P_on_O.nodes | differ 150 of 200 sum 9449926
proof 4 uci | done | P_uci.txt | option name AspCappedReopen type check default false option name AspCappedReopen_Margin type spin default 13 min 1 max 1000 option name AspCappedReopen_Decisive type spin default 640 min 1 max 10000
proof 5 sanitizer | done | P_asan_G100.meta P_asan_canary.meta | nm 35 lines 0 canary 1
STEP 3 match | done | match_summary.txt | Games: 1106 Elo: -7.23 +/- 10.57, nElo: -14.01 +/- 20.48
STEP 4 partner | done | partner_on_vs_theirs.txt partner_R_summary.txt | their rows differ 0 Games: 600 Elo: -11.01 +/- 9.63, nElo: -31.81 +/- 27.80
```

Proof (1). HONESTY_P.txt is PASS. The four node counts match the known numbers. No setoption was sent.

Proof (2). S14, Threads 1, Hash 16, AspCappedReopen false. O depth 12 differ 0 of 200 against exe B (sum 9500069, first three 41311 / 24872 / 28574). G depth 12 differ 0 of 353 (sum 18466239).

Proof (3). The same settings with AspCappedReopen true. O depth 12 sum 9449926. 150 of 200 positions differ from exe B. The code runs. The prediction was 8700000, wrong outside 6000000 to 13000000, so this sum does not prove the prediction wrong.

Proof (4). P_uci.txt lists AspCappedReopen type check default false, AspCappedReopen_Margin type spin default 13 min 1 max 1000, and AspCappedReopen_Decisive type spin default 640 min 1 max 10000.

Proof (5). The AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree searched the first 100 positions of G at depth 10 with the switch true. P_asan_G100.meta has nm_asan_symbols=35 and sanitizer_lines=0. A scratch build with one heap read past a four-int array, only on the FEN in canary.fen, was run through search_set.py and P_asan_canary.meta records one sanitizer line: a runtime error for a load with insufficient space for an int. ASAN_OPTIONS included detect_leaks=0. That scratch change is not in idea.patch.txt.

Match. exe P with the switch true against exe P with the switch false. S14, Threads 1, Hash 16, 20000 nodes a move, openings O then G (553), both colours, 1106 games, concurrency 3. match_summary.txt: Elo -7.23 +/- 10.57, 329 wins, 352 losses, 425 draws. The interval crosses 0, and the point is not below -20, so I did not open the code a second time. The prediction was +6 Elo, wrong if the point were below -25 or above +30.

Partner. Seats for idea 9 are 009, 059, and 109. At 09:10 UTC, 109 had no branch and 009 was 2e28ca5447542248d436aa2de7d4c2ca7e382f9f, the same tip I had already built. Verdict: CONFIRMS. git apply --check succeeded. Honesty PASS. Switch false matched exe B on all 200 O positions. Switch true matched seat 009's own O rows on all 200 positions, and 150 of those differ from exe B, which is what seat 009 reported. I then played that build, switch true against switch false, on my 300 R openings, both colours, 600 games: Elo -11.01 +/- 9.63. I did not replay seat 009's 1106-game match. Their published score on O+G is the same line as mine, which is what a fixed node count does when both on-paths use 13 and 640.

suspicions, not proven. The R-match interval lies under 0 and the point is about -11. That is not the "below -20 and the whole interval below 0" case, and the O+G interval still crosses 0. I am not claiming the idea loses. Seat 009's 1106-game score matching mine to the win, loss, and draw counts is the deterministic game, not a copied file: their STEP 3 stamp is earlier than my match.

what I did NOT do. I did not rename AspCappedReopen to IdeaS23. I did not try margins other than the default. I did not run the sanitizer with the switch false. I did not replay the partner's 1106 games. I did not open a pull request. Seat 109 never appeared.

what I am NOT sure about. The canary's sanitizer line is UndefinedBehaviorSanitizer's "insufficient space" report, not a line that contains the word AddressSanitizer. The binary does contain __asan_ symbols (35). Fastchess printed DrawRatio 83.67% for the R match while the same block says 59 draws out of 600. I do not know that ratio's definition. The game count is 600 from the Finished lines and from the PGN.

times: see stamps.txt

===== git status --short =====
 M forge-combo29/grok/059/stamps.txt
?? forge-combo29/grok/059/REPORT.md
?? forge-combo29/grok/059/RESULT.txt
?? forge-combo29/grok/059/report_tables.py
?? forge-combo29/grok/059/report_tables.txt
===== ls -la =====
total 4860
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:12 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:08 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:07 asan_env.txt
-rw-r--r-- 1 ubuntu ubuntu    1184 Nov 20 08:06 asan_meta.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 B_G.err
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 08:00 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu    3455 Nov 20 08:00 B_G.nodes
-rw-r--r-- 1 ubuntu ubuntu   36799 Nov 20 08:00 B_G.sent
-rw-r--r-- 1 ubuntu ubuntu  507652 Nov 20 08:00 B_G.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:00 B_O.err
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:00 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1918 Nov 20 08:00 B_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   24013 Nov 20 08:00 B_O.sent
-rw-r--r-- 1 ubuntu ubuntu  281879 Nov 20 08:00 B_O.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 canary.fen
-rw-r--r-- 1 ubuntu ubuntu    1131 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1344 Nov 20 08:20 compare_partner_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1726 Nov 20 08:10 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:59 honesty_b_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:59 honesty_b_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:59 honesty_b_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:59 honesty_b_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     272 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3456 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     339 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 07:59 honesty_b_uci.err
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    3461 Nov 20 08:03 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu     342 Nov 20 08:20 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     339 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    3087 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1517 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    6980 Nov 20 08:16 match_on_off_config.json
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu  105841 Nov 20 08:16 match_on_off.out
-rw-r--r-- 1 ubuntu ubuntu 1058311 Nov 20 08:16 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu       5 Nov 20 08:10 match_on_off.pid
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 match_openings.epd
-rw-r--r-- 1 ubuntu ubuntu    1191 Nov 20 08:19 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     658 Nov 20 08:19 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 08:19 partner_009_head.txt
-rw-r--r-- 1 ubuntu ubuntu    2899 Nov 20 08:19 partner_009_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   14756 Nov 20 08:19 partner_009_P_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:20 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 PARTNER_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 08:20 PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 PARTNER_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 08:20 PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 PARTNER_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 08:20 PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:20 PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1208 Nov 20 08:20 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 partner_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:20 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1918 Nov 20 08:20 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   24064 Nov 20 08:20 partner_off_O.sent
-rw-r--r-- 1 ubuntu ubuntu  281765 Nov 20 08:20 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:20 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 partner_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     920 Nov 20 08:20 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1917 Nov 20 08:20 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   24063 Nov 20 08:20 partner_on_O.sent
-rw-r--r-- 1 ubuntu ubuntu  281845 Nov 20 08:20 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:20 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      39 Nov 20 08:20 partner_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 PARTNER_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     273 Nov 20 08:20 PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:20 PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    6962 Nov 20 08:23 partner_R_config.json
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 partner_R.log
-rw-r--r-- 1 ubuntu ubuntu   52737 Nov 20 08:23 partner_R.out
-rw-r--r-- 1 ubuntu ubuntu  471016 Nov 20 08:23 partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     643 Nov 20 08:23 partner_R_summary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 PARTNER_uci.err
-rw-r--r-- 1 ubuntu ubuntu    5062 Nov 20 08:20 PARTNER_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    1103 Nov 20 08:07 P_asan_canary.err
-rw-r--r-- 1 ubuntu ubuntu    1166 Nov 20 08:07 P_asan_canary.meta
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 08:07 P_asan_canary.nodes
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:07 P_asan_canary.sent
-rw-r--r-- 1 ubuntu ubuntu    5223 Nov 20 08:07 P_asan_canary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_asan_G100.err
-rw-r--r-- 1 ubuntu ubuntu     996 Nov 20 08:07 P_asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 08:07 P_asan_G100.nodes
-rw-r--r-- 1 ubuntu ubuntu   11011 Nov 20 08:07 P_asan_G100.sent
-rw-r--r-- 1 ubuntu ubuntu  119099 Nov 20 08:07 P_asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 P_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:03 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 P_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:03 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 P_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:03 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_G.err
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:04 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu    3455 Nov 20 08:04 P_off_G.nodes
-rw-r--r-- 1 ubuntu ubuntu   36850 Nov 20 08:04 P_off_G.sent
-rw-r--r-- 1 ubuntu ubuntu  507449 Nov 20 08:04 P_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     918 Nov 20 08:04 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1918 Nov 20 08:04 P_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   24064 Nov 20 08:04 P_off_O.sent
-rw-r--r-- 1 ubuntu ubuntu  281788 Nov 20 08:04 P_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:04 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1917 Nov 20 08:04 P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu   24063 Nov 20 08:04 P_on_O.sent
-rw-r--r-- 1 ubuntu ubuntu  281912 Nov 20 08:04 P_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 P_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     264 Nov 20 08:03 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     712 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:08 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:08 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:08 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 P_uci.err
-rw-r--r-- 1 ubuntu ubuntu    5079 Nov 20 08:03 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   19281 Nov 20 08:19 R300.epd
-rw-r--r-- 1 ubuntu ubuntu   19391 Nov 20 08:10 R.epd
-rw-r--r-- 1 ubuntu ubuntu   10097 Nov 20 09:12 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4748 Nov 20 09:11 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu    5265 Nov 20 09:11 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 09:12 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1331 Nov 20 08:09 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    7942 Nov 20 08:03 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    6944 Nov 20 08:09 smoke_config.json
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 smoke.log
-rw-r--r-- 1 ubuntu ubuntu    2438 Nov 20 08:09 smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 09:12 stamps.txt
