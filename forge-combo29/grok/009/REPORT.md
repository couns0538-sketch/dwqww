# Seat 009, idea 9, S23

S23 caps the root aspiration reopen after a fail. The plain engine already does that when AspCappedReopen is true: a mate, or a score at or past 640, opens that side to the win or loss bound, and any other fail places the bound 13 centipawns past the returned score.
The two widths were constexpr. idea.patch.txt turns them into the spins IdeaS23_Margin (default 13, min 0, max 400) and IdeaS23_Decisive (default 640, min 0, max 10000). The check stays AspCappedReopen, default false.
With the check false those spins are not read. With the check true and the spins left at the defaults, the reopen uses the same 13 and 640. git apply --check of idea.patch.txt on this seat's checkout of the base printed APPLY_CHECK_OK.

EXISTS: forge-combo29/src/search.cpp:2128 (constexpr int AspReopenMargin = 13 on commit 6b98f2170). The check is forge-combo29/src/search.cpp:103, forge-combo29/include/forge/search.hpp:303, and forge-combo29/src/uci.cpp:227. The branch that calls capped_fail_low is forge-combo29/src/search.cpp:2419.

Honesty, no setoption, exe B and exe P and the partner build: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. All four matched on all three builds.

The block below is the output of tables.py, which reads the raw files.

```
honesty_B
  bench11 312866 OK
  bench13 862329 OK
  bench16 3024920 OK
  perft5 4865609 OK
honesty_P
  bench11 312866 OK
  bench13 862329 OK
  bench16 3024920 OK
  perft5 4865609 OK
honesty_PARTNER
  bench11 312866 OK
  bench13 862329 OK
  bench16 3024920 OK
  perft5 4865609 OK
sum B_O count 200 sum 9500069 first 41311 24872 28574
sum B_G count 353 sum 18466239 first 37203 70845 144383
sum P_off_O count 200 sum 9500069 first 41311 24872 28574
sum P_off_G count 353 sum 18466239 first 37203 70845 144383
sum P_on_O count 200 sum 9449926 first 21210 24516 34920
sum partner_off_O count 200 sum 9500069 first 41311 24872 28574
sum partner_on_O count 200 sum 9449926 first 21210 24516 34920
differ off_O compared 200 differ 0
differ off_G compared 353 differ 0
differ on_O_vs_B compared 200 differ 150
differ partner_off_vs_B compared 200 differ 0
differ partner_on_vs_B compared 200 differ 150
differ partner_on_vs_mine compared 200 differ 0
uci_options
  option name AspCappedReopen type check default false
  option name IdeaS23_Margin type spin default 13 min 0 max 400
  option name IdeaS23_Decisive type spin default 640 min 0 max 10000
asan_meta
  exe /tmp/forge-asan/forge
  nm_asan_count 35
  asan_lines 0
asan_canary
  /tmp/forge-bad-src/src/search.cpp:2149:22: runtime error: load of address 0x502000001080 with insufficient space for an object of type 'int'
partner_nodes_file
  compared 200 mine 200 theirs 200 differ 0
step_table
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 009 idea 9
STEP 2 builds and sums | done | HONESTY_B.txt B_SUMS.txt | O 9500069 G 18466239 honesty pass
STEP 3 patch and proofs | done | idea.patch.txt tables.txt | off differ 0 on differ 150 of 200
STEP 3 match | done | match_on_vs_off.txt | Elo -7.23 +/- 10.57 games 1106
STEP 4 partner 059 | done | partner_off_vs_B.txt partner_on_vs_theirs.txt partner_match.summary.txt | CONFIRMS
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

Proof (1). Honesty of exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. HONESTY_P.txt.

Proof (2). S14 and AspCappedReopen false. O depth 12: 200 positions, differ 0 from exe B, sum 9500069, first three 41311, 24872, 28574. G depth 12: 353 positions, differ 0 from exe B, sum 18466239.

Proof (3). S14 and AspCappedReopen true. O depth 12 sum 9449926. 150 of 200 positions differ from exe B. prediction.txt said 9750000, wrong below 8500000 or above 11500000. 9449926 is inside that range.

Proof (4). The uci list from exe P contains AspCappedReopen type check default false, IdeaS23_Margin type spin default 13 min 0 max 400, and IdeaS23_Decisive type spin default 640 min 0 max 10000.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. nm -C counted 35 __asan_ symbols. First 100 of G at depth 10 with AspCappedReopen true: 0 sanitizer lines. A scratch copy with one read past the end of a four-int heap array, on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1, built the same way and run through run_depth.py, reported the runtime error quoted above. sanitizer=clean.

Match. exe P with AspCappedReopen true against exe P with AspCappedReopen false. Both S14, Threads 1, Hash 16, the two spins set to 13 and 640, nodes 20000, openings O and G (553), both colours, 1106 games, concurrency 3. From match_on_vs_off.summary.txt: Elo -7.23 +/- 10.57, wins 329, losses 352, draws 425, points 541.5. The point is not below -20, and -7.23 +/- 10.57 is not an interval that lies entirely below 0, so I did not open the search a second time looking for a mistake. prediction.txt said Elo +4, wrong below -25 or above +40. -7.23 is inside that range.

Partner verdict: CONFIRMS. The next seat after 009 with idea 9 and a branch is 059. 109 has no branch. Their idea.patch.txt passed git apply --check on a fresh worktree of 6b98f2170, then built. Honesty matched the four known node counts. AspCappedReopen false: O depth 12 differ 0 from exe B. AspCappedReopen true: differ 0 from their P_on_O.nodes (200 positions) and differ 150 from exe B, which is the count in their proof_on_O.txt. A match of that build, my R300.fen, both colours, 600 games: Elo 1.16 +/- 10.15, wins 270, losses 268, draws 62.

suspicions, not proven. Their published O+G match line is the same Elo, the same pentanomial, and the same 1106-game split as mine. Both patches leave the on-path at 13 and 640, and a fixed node count repeats a game, so the same book can do that. I did not prove they played that match themselves. The search claim does not rest on it: my run of their patch matched their node file on all 200 positions.

what I did NOT do. I did not add a second check named IdeaS23. I did not measure a spin value other than the defaults 13 and 640. I did not run G at depth 12 with the switch on. I did not play a second match of my own patch on R, because 059 already had a patch. I did not review seat 109. No forge-combo29/soak_all/FABLE_TO_grok_<N>.md existed at step 1 or at minute 60.

what I am NOT sure about. I quote fastchess "+/-" as printed and do not know whether that half-width is one standard error. The canary line is a UndefinedBehaviorSanitizer "runtime error" on the inserted load. The stack contains asan_thread_start. I did not see the words "ERROR: AddressSanitizer".

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/009/stamps.txt
?? forge-combo29/grok/009/HONESTY_PARTNER.txt
?? forge-combo29/grok/009/REPORT.md
?? forge-combo29/grok/009/RESULT.txt
?? forge-combo29/grok/009/honesty_PARTNER_bench11.meta
?? forge-combo29/grok/009/honesty_PARTNER_bench11.txt
?? forge-combo29/grok/009/honesty_PARTNER_bench13.meta
?? forge-combo29/grok/009/honesty_PARTNER_bench13.txt
?? forge-combo29/grok/009/honesty_PARTNER_bench16.meta
?? forge-combo29/grok/009/honesty_PARTNER_bench16.txt
?? forge-combo29/grok/009/honesty_PARTNER_perft5.meta
?? forge-combo29/grok/009/honesty_PARTNER_perft5.txt
?? forge-combo29/grok/009/partner_059_P_on_O.nodes
?? forge-combo29/grok/009/partner_059_apply_check.txt
?? forge-combo29/grok/009/partner_059_idea.patch.txt
?? forge-combo29/grok/009/partner_059_proof_on_O.txt
?? forge-combo29/grok/009/partner_match.meta
?? forge-combo29/grok/009/partner_match.summary.txt
?? forge-combo29/grok/009/partner_match.txt
?? forge-combo29/grok/009/partner_off_O_d12.meta
?? forge-combo29/grok/009/partner_off_O_d12.raw
?? forge-combo29/grok/009/partner_off_O_d12.rows
?? forge-combo29/grok/009/partner_off_vs_B.txt
?? forge-combo29/grok/009/partner_on_O_d12.meta
?? forge-combo29/grok/009/partner_on_O_d12.raw
?? forge-combo29/grok/009/partner_on_O_d12.rows
?? forge-combo29/grok/009/partner_on_vs_B.txt
?? forge-combo29/grok/009/partner_on_vs_theirs.txt
?? forge-combo29/grok/009/run_partner_match.sh
?? forge-combo29/grok/009/tables.py
?? forge-combo29/grok/009/tables.txt

$ ls -la forge-combo29/grok/009
total 3536
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu     27 Nov 20 08:03 asan_bad.fail
-rw-r--r-- 1 ubuntu ubuntu     17 Nov 20 08:03 asan_bad.meta
-rw-r--r-- 1 ubuntu ubuntu   7977 Nov 20 08:03 asan_bad.raw
-rw-r--r-- 1 ubuntu ubuntu   1033 Nov 20 08:02 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu 135982 Nov 20 08:02 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu   5882 Nov 20 08:02 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu      3 Nov 20 08:02 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     28 Nov 20 08:03 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu    955 Nov 20 07:59 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 566190 Nov 20 07:59 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  21123 Nov 20 07:59 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu    959 Nov 20 07:58 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 318395 Nov 20 07:58 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  14757 Nov 20 07:58 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu    120 Nov 20 07:59 B_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu     34 Nov 20 08:02 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     34 Nov 20 08:02 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    325 Nov 20 08:02 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   1162 Nov 20 08:01 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu   1180 Nov 20 07:59 decision.txt
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 07:58 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   5009 Nov 20 08:02 G100.epd
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 07:55 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:55 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 07:55 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 07:55 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 07:55 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 07:55 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 07:55 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 07:55 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    389 Nov 20 07:56 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 09:09 honesty_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 honesty_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 09:09 honesty_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 09:09 honesty_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 09:09 honesty_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 09:09 honesty_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    200 Nov 20 09:09 honesty_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 09:09 honesty_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    395 Nov 20 09:09 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 08:00 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:00 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 08:00 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 08:00 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 08:00 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 08:00 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 08:00 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 08:00 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    389 Nov 20 08:00 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 07:59 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1483 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu   1220 Nov 20 08:10 match_on_vs_off.meta
-rw-r--r-- 1 ubuntu ubuntu    370 Nov 20 09:14 match_on_vs_off.summary.txt
-rw-r--r-- 1 ubuntu ubuntu 104749 Nov 20 08:10 match_on_vs_off.txt
-rw-r--r-- 1 ubuntu ubuntu  30552 Nov 20 08:03 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     67 Nov 20 09:09 partner_059_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   3087 Nov 20 09:08 partner_059_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   1917 Nov 20 09:08 partner_059_P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu    143 Nov 20 09:08 partner_059_proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    388 Nov 20 09:12 partner_match.meta
-rw-r--r-- 1 ubuntu ubuntu    357 Nov 20 09:14 partner_match.summary.txt
-rw-r--r-- 1 ubuntu ubuntu  52458 Nov 20 09:12 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu   1012 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 318654 Nov 20 09:09 partner_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  14757 Nov 20 09:09 partner_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     34 Nov 20 09:09 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   1011 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 318739 Nov 20 09:09 partner_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  14756 Nov 20 09:09 partner_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu    325 Nov 20 09:09 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     42 Nov 20 09:09 partner_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu   1005 Nov 20 08:00 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 566481 Nov 20 08:00 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  21123 Nov 20 08:00 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu   1009 Nov 20 08:00 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 318667 Nov 20 08:00 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  14757 Nov 20 08:00 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu   1008 Nov 20 08:00 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu 318619 Nov 20 08:00 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu  14756 Nov 20 08:00 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu    361 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu  19142 Nov 20 08:05 R300.fen
-rw-r--r-- 1 ubuntu ubuntu   8221 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   5545 Nov 20 08:01 run_depth.py
-rw-r--r-- 1 ubuntu ubuntu   1702 Nov 20 07:55 run_honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   2800 Nov 20 08:04 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu   1734 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   1180 Nov 20 08:02 run_uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  17691 Nov 20 07:58 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1310 Nov 20 07:56 summarize_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    787 Nov 20 08:13 summarize_match.py
-rw-r--r-- 1 ubuntu ubuntu    619 Nov 20 07:59 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu   3779 Nov 20 09:14 tables.py
-rw-r--r-- 1 ubuntu ubuntu   1967 Nov 20 09:14 tables.txt
-rw-r--r-- 1 ubuntu ubuntu    185 Nov 20 08:02 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu   5062 Nov 20 08:02 uci_P.txt
```
