# Seat 043, idea 43, IdeaK4

IdeaK4 makes the reverse-futility margin smaller when the opponent's static evaluation worsened over two plies. The switch is a check option, default false, and IdeaK4_Shrink is a spin option, default 32, range 0 to 200. When the switch is on, and the parent static eval and the static eval two plies before the parent are both real numbers and the parent value is strictly lower, the margin drops by IdeaK4_Shrink.

EXISTS: no. The plain engine's reverse futility, in search.cpp at the block commented "Reverse futility pruning", uses only RfpMargin * depth - RfpImproving * improving. improving compares our own static eval with our eval two or four plies ago. It does not look at the opponent's eval.

## Honesty

Exe B, no setoption before each command, and the same four commands on exe P:

```
HONESTY_B
exe B honesty, parsed from the raw files by this writer
bench11.txt: info string bench depth 11 nodes 312866 time 166 nps 1884734
bench13.txt: info string bench depth 13 nodes 862329 time 444 nps 1942182
bench16.txt: info string bench depth 16 nodes 3024920 time 1439 nps 2102098
perft5.txt: nodes 4865609
O positions 200 | sum 9500069 | first3 41311 24872 28574
G positions 353 | sum 18466239 | first3 37203 70845 144383
HONESTY_P
bench11.txt: info string bench depth 11 nodes 312866 time 161 nps 1943267
bench13.txt: info string bench depth 13 nodes 862329 time 422 nps 2043433
bench16.txt: info string bench depth 16 nodes 3024920 time 1407 nps 2149907
perft5.txt: nodes 4865609
```

O depth 12 on exe B is 9500069, first three 41311 24872 28574. G depth 12 on exe B is 18466239. Those are the known sums.

## Step table

The numbers below are the pasted output of scripts/compare_nodes.py, scripts/summarize_nodes.py (via those compares), and the raw-file reader that wrote proof/report_numbers.txt.

```
HONESTY_B
exe B honesty, parsed from the raw files by this writer
bench11.txt: info string bench depth 11 nodes 312866 time 166 nps 1884734
bench13.txt: info string bench depth 13 nodes 862329 time 444 nps 1942182
bench16.txt: info string bench depth 16 nodes 3024920 time 1439 nps 2102098
perft5.txt: nodes 4865609
O positions 200 | sum 9500069 | first3 41311 24872 28574
G positions 353 | sum 18466239 | first3 37203 70845 144383
HONESTY_P
bench11.txt: info string bench depth 11 nodes 312866 time 161 nps 1943267
bench13.txt: info string bench depth 13 nodes 862329 time 422 nps 2043433
bench16.txt: info string bench depth 16 nodes 3024920 time 1407 nps 2149907
perft5.txt: nodes 4865609
CMP_OFF_O
left forge-combo29/grok/043/proof/P_off_O_d12.txt
right forge-combo29/grok/043/honesty/B_O_d12.txt
left_n 200 left_sum 9500069
right_n 200 right_sum 9500069
compared 200 differ 0
CMP_OFF_G
left forge-combo29/grok/043/proof/P_off_G_d12.txt
right forge-combo29/grok/043/honesty/B_G_d12.txt
left_n 353 left_sum 18466239
right_n 353 right_sum 18466239
compared 353 differ 0
CMP_ON_O
left forge-combo29/grok/043/proof/P_on_O_d12.txt
right forge-combo29/grok/043/honesty/B_O_d12.txt
left_n 200 left_sum 8983632
right_n 200 right_sum 9500069
compared 200 differ 200
APPLY
APPLY_CHECK_OK 2026-11-20T09:15:32Z
ASAN_META_TAIL
setoption name IdeaK4_Shrink value 32
error=
asan_symbols 35
asan_clean_runtime_error_lines 0
asan_scratch_hit
/tmp/forge-scratch/src/uci.cpp:48:47: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
MATCH
Results of IdeaK4on vs IdeaK4off (20000 nodes, 1t, 16MB, OG553.epd):
Elo: -6.60 +/- 10.53, nElo: -12.83 +/- 20.48
LOS: 10.96 %, DrawRatio: 63.29 %, PairsRatio: 0.83
Games: 1106, Wins: 330, Losses: 351, Draws: 425, Points: 542.5 (49.05 %)
Ptnml(0-2): [16, 95, 350, 78, 14], WL/DD Ratio: 1.78
--------------------------------------------------
Finished match
Total Time: 00:06:07 (hours:minutes:seconds)

MATCH_DONE:0
PARTNER_OFF
left /agent/repos/dwqww/forge-combo29/grok/043/partner/off_O.txt
right /agent/repos/dwqww/forge-combo29/grok/043/honesty/B_O_d12.txt
left_n 200 left_sum 9500069
right_n 200 right_sum 9500069
compared 200 differ 0
PARTNER_ON
mine_n 200 mine_sum 8921190
theirs_n 200 theirs_sum 8921190
compared 200 differ 0
first_both 24693
PARTNER_APPLY
APPLY_CHECK_OK
PARTNER_FETCH
partner_head 3d06b548f2c6c1329413cb4f23ff969b6f1db673
PARTNER_MATCH
Results of IdeaK4on vs IdeaK4off (20000 nodes, 1t, 16MB, R300.fens):
Elo: 2.32 +/- 10.77, nElo: 5.98 +/- 27.80
LOS: 66.34 %, DrawRatio: 81.00 %, PairsRatio: 1.04
Games: 600, Wins: 265, Losses: 261, Draws: 74, Points: 302.0 (50.33 %)
Ptnml(0-2): [4, 24, 243, 22, 7], WL/DD Ratio: 16.36
--------------------------------------------------
Finished match
Total Time: 00:02:39 (hours:minutes:seconds)

PARTNER_MATCH_DONE:0
pgn_self_results 1106
pgn_partner_results 600
```

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 043, idea 43, Grok 4.7 |
| 2 two builds and honesty | done | HONESTY_B.txt, honesty/ | bench 312866 / 862329 / 3024920, perft 4865609; O 9500069; G 18466239 |
| 3a read | done | DESIGN.txt | plain engine does not do IdeaK4 |
| 3b predict | done | prediction.txt | O sum 9120000, Elo +4; not edited after |
| 3c patch | done | idea.patch.txt, proof/apply_check.txt | APPLY_CHECK_OK on a fresh base |
| 3d proofs | done | proof/ | off 0 differ; on 200 of 200; sanitizer clean with both proofs |
| 3e match | done | match/result_block.txt, match/games.pgn | Elo -6.60 +/- 10.53, 1106 games |
| 4 partner 093 | done | partner/ | CONFIRMS; R match Elo 2.32 +/- 10.77, 600 games |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty on exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Same four numbers as exe B.

(2) S14 and IdeaK4 false: O depth 12 differ 0 of 200, sum 9500069. G depth 12 differ 0 of 353, sum 18466239. Position by position equal to exe B.

(3) S14 and IdeaK4 true with IdeaK4_Shrink 32: O depth 12 sum 8983632, differ 200 of 200 against exe B. The code runs on every opening in the set.

(4) uci lists `option name IdeaK4 type check default false` and `option name IdeaK4_Shrink type spin default 32 min 0 max 200` in proof/uci.txt.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK4 true, first 100 of G at depth 10: 0 lines containing "runtime error:" or "AddressSanitizer". proof/asan_G100_d10.txt.meta ends with `asan_symbols 35`, which is `nm -C` counting `__asan_` symbols. The scratch copy, one deliberate read one past a four-int heap array on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, built the same way and run through scripts/search_set.py, reports `runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'` at the inserted line. That is proof/asan_scratch.txt.

git apply --check of idea.patch.txt on a fresh checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7 printed APPLY_CHECK_OK.

## Match

Exe P with IdeaK4 true and IdeaK4_Shrink 32 against exe P with IdeaK4 false. Both sides got S14, Threads 1, Hash 16, OwnBook false, and 20000 nodes. Openings were the 553 positions in positions/OG553.epd, both colours, 1106 games. fastchess concurrency 3. PGN result tags: 1106.

```
Results of IdeaK4on vs IdeaK4off (20000 nodes, 1t, 16MB, OG553.epd):
Elo: -6.60 +/- 10.53, nElo: -12.83 +/- 20.48
LOS: 10.96 %, DrawRatio: 63.29 %, PairsRatio: 0.83
Games: 1106, Wins: 330, Losses: 351, Draws: 425, Points: 542.5 (49.05 %)
Ptnml(0-2): [16, 95, 350, 78, 14], WL/DD Ratio: 1.78
```

The point is not below -20 and the interval is not entirely below 0, so I did not open the code a second time for a bug hunt. Prediction was O sum 9120000, wrong below 7800000 or above 9480000: measured 8983632, inside the range. Predicted Elo +4, wrong below -12 or above +30: measured -6.60, inside the range.

## Partner

Partner is seat 093, the next seat with this idea. Fetched head 3d06b548f2c6c1329413cb4f23ff969b6f1db673. Their patch applies with git apply --check. Honesty numbers match. Their switch false matches exe B on O depth 12, differ 0 of 200. Their switch true with IdeaK4_Shrink 24 matches their own O rows, differ 0 of 200, sum 8921190, first position 24693. Verdict: CONFIRMS.

Their R match, 300 openings, both colours, 600 games, same harness pattern, same S14 and node limit, their binary:

```
Elo: 2.32 +/- 10.77
Games: 600, Wins: 265, Losses: 261, Draws: 74, Points: 302.0 (50.33 %)
```

pgn_partner_results 600. They also published an OG match of +5.03 +/- 9.77 on their shrink of 24. I did not replay that match. The required partner match is the 300 R openings.

## Suspicions, not proven

A shrink of 32 lost about 7 Elo here and a shrink of 24 was about even on random positions and positive on their OG match. The extra pruning may be a little too large at 32. The intervals all cross 0, so this is not a demonstrated loss or gain.

The scratch sanitizer line is UndefinedBehaviorSanitizer's "insufficient space" report of the out-of-bounds heap load. AddressSanitizer is in the binary (35 `__asan_` symbols) but its "heap-buffer-overflow" summary did not appear, because UBSan aborted first.

## What I did NOT do

I did not replay partner 093's 1106-game OG match. I did not run the sanitizer on their binary. I did not compare their switch-false G rows; the required false check was O. I did not change the engine after the match. I did not open a pull request. No FABLE_TO_grok file existed at step 1 or at minute 60, so nothing there changed the job.

## What I am NOT sure about

I am not sure the fastchess +/- figure is a 95 percent interval; I report the number it printed. I am not sure a reader who wants the literal text "AddressSanitizer" will accept the UBSan line as the scratch proof, though it names the out-of-bounds load and the instrumented binary has the ASan symbols. I am not sure "worsened" should include an equal eval; I used a strict drop.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok/043/stamps.txt
?? forge-combo29/grok/043/REPORT.md
?? forge-combo29/grok/043/RESULT.txt
?? forge-combo29/grok/043/partner/
?? forge-combo29/grok/043/proof/apply_check.txt
?? forge-combo29/grok/043/proof/report_numbers.txt
?? forge-combo29/grok/043/scripts/compare_partner_rows.py
?? forge-combo29/grok/043/scripts/eval_partner.sh
$ ls -la forge-combo29/grok/043
$ ls -la forge-combo29/grok/043/*
total 76
drwxr-xr-x 8 ubuntu ubuntu 4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu 1281 Nov 20 08:02 DESIGN.txt
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:02 honesty
-rw-r--r-- 1 ubuntu ubuntu  422 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu 5453 Nov 20 08:03 idea.patch.txt
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:17 match
drwxr-xr-x 4 ubuntu ubuntu 4096 Nov 20 09:09 partner
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:08 positions
-rw-r--r-- 1 ubuntu ubuntu  305 Nov 20 08:02 prediction.txt
drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 20 09:15 proof
-rw-r--r-- 1 ubuntu ubuntu 9985 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu  187 Nov 20 09:16 RESULT.txt
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:17 scripts
-rw-r--r-- 1 ubuntu ubuntu   78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  208 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu 1281 Nov 20 08:02 forge-combo29/grok/043/DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu  422 Nov 20 08:02 forge-combo29/grok/043/HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu 5453 Nov 20 08:03 forge-combo29/grok/043/idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  305 Nov 20 08:02 forge-combo29/grok/043/prediction.txt
-rw-r--r-- 1 ubuntu ubuntu 9985 Nov 20 09:16 forge-combo29/grok/043/REPORT.md
-rw-r--r-- 1 ubuntu ubuntu  187 Nov 20 09:16 forge-combo29/grok/043/RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   78 Nov 20 07:53 forge-combo29/grok/043/SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  208 Nov 20 09:15 forge-combo29/grok/043/stamps.txt

forge-combo29/grok/043/honesty:
total 928
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:02 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 07:57 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 07:57 bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 07:57 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 07:57 bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 07:57 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 07:57 bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 559781 Nov 20 08:00 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    884 Nov 20 08:00 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3485 Nov 20 08:02 B_G_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu 314605 Nov 20 08:00 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    888 Nov 20 08:00 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1947 Nov 20 08:02 B_O_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 07:57 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    216 Nov 20 07:57 perft5.txt.meta

forge-combo29/grok/043/match:
total 3640
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:17 .
drwxr-xr-x 8 ubuntu ubuntu    4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu    7192 Nov 20 08:15 config.json
-rw-r--r-- 1 ubuntu ubuntu 3566845 Nov 20 08:15 games.pgn
-rw-r--r-- 1 ubuntu ubuntu     416 Nov 20 08:17 result_block.txt
-rw-r--r-- 1 ubuntu ubuntu  134731 Nov 20 08:15 stdout.txt

forge-combo29/grok/043/partner:
total 688
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 09:09 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu     15 Nov 20 09:09 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    213 Nov 20 09:09 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     99 Nov 20 09:09 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     54 Nov 20 09:08 fetch.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:09 honesty
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:09 match
-rw-r--r-- 1 ubuntu ubuntu 314722 Nov 20 09:09 off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    935 Nov 20 09:09 off_O.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 313835 Nov 20 09:09 on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    972 Nov 20 09:09 on_O.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  14755 Nov 20 09:08 their_O_on.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   5305 Nov 20 09:08 their.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    129 Nov 20 09:08 their_proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    360 Nov 20 09:08 their_proof_on_O.txt

forge-combo29/grok/043/positions:
total 108
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 08:08 .
drwxr-xr-x 8 ubuntu ubuntu  4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu 12861 Nov 20 07:56 first200.fens
-rw-r--r-- 1 ubuntu ubuntu  5009 Nov 20 08:05 G100.epd
-rw-r--r-- 1 ubuntu ubuntu 30552 Nov 20 08:08 OG553.epd
-rw-r--r-- 1 ubuntu ubuntu 19024 Nov 20 08:03 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    30 Nov 20 08:05 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu 17691 Nov 20 07:56 set_G.epd

forge-combo29/grok/043/proof:
total 1376
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 09:15 .
drwxr-xr-x 8 ubuntu ubuntu   4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu     36 Nov 20 09:15 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu 134148 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    958 Nov 20 08:06 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   7114 Nov 20 08:08 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    993 Nov 20 08:08 asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    181 Nov 20 08:09 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu    179 Nov 20 08:09 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 08:09 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    347 Nov 20 08:04 COMPARE.txt
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 08:03 honesty
-rw-r--r-- 1 ubuntu ubuntu    250 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu 559783 Nov 20 08:04 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    918 Nov 20 08:04 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 314562 Nov 20 08:03 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    922 Nov 20 08:03 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 313545 Nov 20 08:04 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    959 Nov 20 08:04 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2897 Nov 20 09:15 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu   5038 Nov 20 08:04 uci.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 08:04 uci.txt.meta

forge-combo29/grok/043/scripts:
total 40
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:17 .
drwxr-xr-x 8 ubuntu ubuntu 4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu  932 Nov 20 08:09 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu 1264 Nov 20 08:17 compare_partner_rows.py
-rwxr-xr-x 1 ubuntu ubuntu 2700 Nov 20 08:17 eval_partner.sh
-rw-r--r-- 1 ubuntu ubuntu 2697 Nov 20 07:57 honesty_run.py
-rwxr-xr-x 1 ubuntu ubuntu 1072 Nov 20 08:08 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu 5831 Nov 20 08:05 search_set.py
-rw-r--r-- 1 ubuntu ubuntu 1442 Nov 20 08:00 summarize_nodes.py

$ ls -la nested evidence directories
forge-combo29/grok/043/partner/honesty:
total 56
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 09:09 .
drwxr-xr-x 4 ubuntu ubuntu 4096 Nov 20 09:09 ..
-rw-r--r-- 1 ubuntu ubuntu 5099 Nov 20 09:09 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu  220 Nov 20 09:09 bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5099 Nov 20 09:09 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu  220 Nov 20 09:09 bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5101 Nov 20 09:09 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu  220 Nov 20 09:09 bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5312 Nov 20 09:09 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  222 Nov 20 09:09 perft5.txt.meta

forge-combo29/grok/043/partner/match:
total 1608
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:09 .
drwxr-xr-x 4 ubuntu ubuntu    4096 Nov 20 09:09 ..
-rw-r--r-- 1 ubuntu ubuntu    7202 Nov 20 09:12 config.json
-rw-r--r-- 1 ubuntu ubuntu 1554085 Nov 20 09:12 games.pgn
-rw-r--r-- 1 ubuntu ubuntu   68283 Nov 20 09:12 stdout.txt

forge-combo29/grok/043/proof/honesty:
total 56
drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 20 08:03 .
drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 20 09:15 ..
-rw-r--r-- 1 ubuntu ubuntu 5099 Nov 20 08:03 bench11.txt
-rw-r--r-- 1 ubuntu ubuntu  214 Nov 20 08:03 bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5099 Nov 20 08:03 bench13.txt
-rw-r--r-- 1 ubuntu ubuntu  214 Nov 20 08:03 bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5101 Nov 20 08:03 bench16.txt
-rw-r--r-- 1 ubuntu ubuntu  214 Nov 20 08:03 bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 5312 Nov 20 08:03 perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  216 Nov 20 08:03 perft5.txt.meta
```
