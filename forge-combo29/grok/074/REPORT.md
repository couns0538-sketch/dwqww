# Seat 074, idea 24, S32

IdeaS32 grades a null-move fail-high whose probe returned on a hash bound shallower than the parent depth.
The switch is `IdeaS32` (check, default false) and the slack is `IdeaS32_OwedSlack` (spin, default 0, range 0 to 64).
When the switch is on, that cutoff is kept only if the same reduced re-search already used at depth 14 also reaches beta. A pass does not add depth to a stored fail-high.

EXISTS: no. `search.cpp` returns a null cutoff below depth 14 without a hash-depth test, and it stores the depth that was searched.

Honesty, no setoption, fresh process each line. Exe B and exe P both: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

The tables below are the pasted output of `python3 report_numbers.py`, which reads the raw files.

```
HONESTY_B
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
HONESTY_P
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
PARTNER_HONESTY
bench 11 nodes 312866 expected 312866 OK
bench 13 nodes 862329 expected 862329 OK
bench 16 nodes 3024920 expected 3024920 OK
go perft 5 nodes 4865609 expected 4865609 OK
B_O n 200 sum 9500069 first3 41311 24872 28574 file b_O.nodes.txt
B_G n 353 sum 18466239 first3 37203 70845 144383 file b_G.nodes.txt
P_OFF_O n 200 sum 9500069 first3 41311 24872 28574 file p_off_O.nodes.txt
P_OFF_G n 353 sum 18466239 first3 37203 70845 144383 file p_off_G.nodes.txt
P_ON_O n 200 sum 9547450 first3 41442 24989 28711 file p_on_O.nodes.txt
COMPARE_OFF_O
n 200 differ 0 sum_left 9500069 sum_right 9500069
COMPARE_OFF_G
n 353 differ 0 sum_left 18466239 sum_right 18466239
COMPARE_ON_O
n 200 differ 200 sum_left 9500069 sum_right 9547450
pos 1 41311 41442
pos 2 24872 24989
pos 3 28574 28711
pos 4 27838 27927
pos 5 18020 18139
pos 6 43043 43187
pos 7 56414 56670
pos 8 32317 32398
ASAN_NM
35
ASAN_SCAN
AddressSanitizer 0
runtime_error 0
ASAN_SCRATCH_ERROR
==10232==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000001090 at pc 0x556e9fe10dc5 bp 0x7f23461f1650 sp 0x7f23461f1640
SUMMARY: AddressSanitizer: heap-buffer-overflow (/tmp/asan-scratch/forge+0x5b5dc4) (BuildId: c7d69c4b7dca2feb960e085ab0d5880cf43af037) in forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)
APPLY_CHECK
base_apply_exit 0
PARTNER_APPLY_CHECK
partner_apply_on_base_exit 0
PARTNER_OFF
n 200 differ 0 sum_left 9500069 sum_right 9500069
PARTNER_ON
n 200 differ 0 sum_left 9547450 sum_right 9547450
MATCH_FINAL
Elo: 5.97 +/- 9.47, nElo: 12.91 +/- 20.48
Games: 1106, Wins: 338, Losses: 319, Draws: 449, Points: 562.5 (50.86 %)
PARTNER_MATCH_FINAL
Elo: -4.05 +/- 7.25, nElo: -15.54 +/- 27.80
Games: 600, Wins: 269, Losses: 276, Draws: 55, Points: 296.5 (49.42 %)
PREDICTION
O depth-12 sum with IdeaS32 on: 10400000
wrong if that sum is below 9600000 or above 14000000
test-match Elo of IdeaS32 on minus off: 8
wrong if that Elo is below -30 or above 45
written 2026-11-20T08:04:53Z
STEP_TABLE
step | status | evidence | result
1 seat | done | SEAT.txt | 074 idea 24
2 honesty B and sums | done | HONESTY_B.txt b_O.nodes.txt b_G.nodes.txt | benches match; O 9500069; G 18466239
3a read | done | decisions.txt | EXISTS no
3b prediction | done | prediction.txt | 10400000 and Elo 8, not edited
3c patch | done | idea.patch.txt apply_check.txt | base_apply_exit 0
3d proofs | done | compare_on_O.txt asan_g100_scan.txt asan_scratch.raw.txt | off differ 0; on differ 200 of 200; sanitizer clean and poison reported
3e match | done | match_og.txt match_og.pgn | 1106 games
4 partner | done | partner_on_compare.txt partner_match.txt | CONFIRMS; 600 R games
5 report | done | REPORT.md RESULT.txt | this file
```

## Proofs

(1) Honesty on exe P with no setoption matches the four known node counts. See HONESTY_P above.

(2) S14 and IdeaS32 false: O depth 12 differs in 0 of 200 positions from exe B (sum 9500069). G depth 12 differs in 0 of 353 (sum 18466239).

(3) S14 and IdeaS32 true: O depth 12 sum 9547450. 200 of 200 positions differ from exe B. The code runs.

(4) `uci` lists `option name IdeaS32 type check default false` and `option name IdeaS32_OwedSlack type spin default 0 min 0 max 64`. File uci_p.txt.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10: 0 AddressSanitizer lines and 0 runtime-error lines in asan_g100.raw.txt. asan_g100.meta has nm_asan 35. The scratch copy, same flags and the same depth_sum.py runner, on the start FEN, reports `ERROR: AddressSanitizer: heap-buffer-overflow`. ASAN_OPTIONS was detect_leaks=0:halt_on_error=1.

`git apply --check` of idea.patch.txt on a fresh base worktree exited 0 (apply_check.txt).

## Match

Exe P with IdeaS32 true against exe P with IdeaS32 false. S14, Threads 1, Hash 16, 20000 nodes. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3.

Elo: 5.97 +/- 9.47. Games: 1106, Wins: 338, Losses: 319, Draws: 449. The whole interval is not below 0, so the code was not reopened for a second bug hunt.

The prediction file was not edited. The measured O sum 9547450 is below the predicted wrong-if-below line of 9600000, so that prediction is wrong. The Elo 5.97 is inside the predicted band of -30 to 45.

## Partner

Partner is seat 024. Idea 24 also belongs to seat 124, which is outside 001..120, so the next seat after 074 is 024. The branch existed at minute 75 and already had idea.patch.txt.

Their patch applies on a fresh base (`partner_apply_on_base_exit 0`). Their build's honesty numbers match. Switch false: O depth 12 differs in 0 of 200 from exe B. Switch true: O depth 12 differs in 0 of 200 from their own P_on_O_d12.tsv (sum 9547450). A match of their switch on 300 R openings, both colours, 600 games: Elo -4.05 +/- 7.25.

Verdict: CONFIRMS. The proofs they state for honesty, switch off, and switch on are the numbers this harness measured. Their spin is named IdeaS32_Slack. It was left at their default 0. This harness did not send that spin.

## suspicions, not proven

The identical O rows and the identical 1106-game Elo line are what the same rule produces. I did not compare the two patches line by line for a shared bug.

Turning leak detection off may hide a shutdown leak that was already in the engine. The planted overflow still printed a sanitizer line, so the clean run is not "not shown".

## what I did NOT do

I did not remeasure the partner's G depth-12 file. I did not play their 1106-game book again. I did not change the engine after the prediction. I did not open a pull request. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

## what I am NOT sure about

I am not sure a leak-checking sanitizer run would stay silent. I am not sure IdeaS32_OwedSlack values other than 0 are useful; only the default was measured. I am not sure the small node increase is strength rather than extra verification at a fixed node count. The Elo interval includes both signs.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok/074/stamps.txt
?? forge-combo29/grok/074/R300.fens
?? forge-combo29/grok/074/REPORT.md
?? forge-combo29/grok/074/RESULT.txt
?? forge-combo29/grok/074/apply_check.txt
?? forge-combo29/grok/074/partner.patch.txt
?? forge-combo29/grok/074/partner_apply_check.txt
?? forge-combo29/grok/074/partner_claimed_on_O.nodes.txt
?? forge-combo29/grok/074/partner_config.json
?? forge-combo29/grok/074/partner_files.txt
?? forge-combo29/grok/074/partner_honesty.py
?? forge-combo29/grok/074/partner_honesty.txt
?? forge-combo29/grok/074/partner_honesty_bench11.meta
?? forge-combo29/grok/074/partner_honesty_bench11.txt
?? forge-combo29/grok/074/partner_honesty_bench13.meta
?? forge-combo29/grok/074/partner_honesty_bench13.txt
?? forge-combo29/grok/074/partner_honesty_bench16.meta
?? forge-combo29/grok/074/partner_honesty_bench16.txt
?? forge-combo29/grok/074/partner_honesty_perft5.meta
?? forge-combo29/grok/074/partner_honesty_perft5.txt
?? forge-combo29/grok/074/partner_match.pgn
?? forge-combo29/grok/074/partner_match.txt
?? forge-combo29/grok/074/partner_off_O.meta
?? forge-combo29/grok/074/partner_off_O.nodes.txt
?? forge-combo29/grok/074/partner_off_O.raw.txt
?? forge-combo29/grok/074/partner_off_compare.txt
?? forge-combo29/grok/074/partner_on_O.meta
?? forge-combo29/grok/074/partner_on_O.nodes.txt
?? forge-combo29/grok/074/partner_on_O.raw.txt
?? forge-combo29/grok/074/partner_on_compare.txt
?? forge-combo29/grok/074/report_numbers.out
?? forge-combo29/grok/074/report_numbers.py
?? forge-combo29/grok/074/run_partner.sh
?? forge-combo29/grok/074/run_partner_match.sh

$ ls -la forge-combo29/grok/074
total 8296
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 09:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     966 Nov 20 08:10 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu    6783 Nov 20 08:09 asan_g100.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  114070 Nov 20 08:09 asan_g100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      35 Nov 20 08:10 asan_g100_scan.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:09 asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 08:10 asan_scratch.error.txt
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:13 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10939 Nov 20 08:10 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 08:04 b_G.meta
-rw-r--r-- 1 ubuntu ubuntu   24300 Nov 20 08:04 b_G.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  503126 Nov 20 08:04 b_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     896 Nov 20 08:04 b_O.meta
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 08:04 b_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  277276 Nov 20 08:04 b_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:07 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:10 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:10 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:10 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    6910 Nov 20 09:16 config.json
-rw-r--r-- 1 ubuntu ubuntu     994 Nov 20 08:12 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    5316 Nov 20 08:08 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:03 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:03 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:03 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:03 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:03 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:03 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:03 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:03 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2519 Nov 20 08:03 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:06 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:06 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 08:06 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5315 Nov 20 08:06 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2485 Nov 20 08:06 honesty_p.py
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7550 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1339 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3575210 Nov 20 08:19 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  124842 Nov 20 08:19 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 09:16 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1896 Nov 20 09:11 partner_claimed_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu    6928 Nov 20 09:16 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu    2765 Nov 20 09:10 partner_files.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:11 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 09:11 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:11 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 09:11 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:11 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 09:11 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:11 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5311 Nov 20 09:11 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2375 Nov 20 09:11 partner_honesty.py
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 09:11 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu 1558658 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   63118 Nov 20 09:15 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:11 partner_off_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     945 Nov 20 09:11 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 09:11 partner_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  277514 Nov 20 09:11 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:11 partner_on_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     944 Nov 20 09:11 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 09:11 partner_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  277550 Nov 20 09:11 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    8946 Nov 20 09:10 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 08:06 p_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   24300 Nov 20 08:06 p_off_G.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  502463 Nov 20 08:06 p_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 08:06 p_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 08:06 p_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  276816 Nov 20 08:06 p_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     937 Nov 20 08:07 p_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   16557 Nov 20 08:07 p_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  276838 Nov 20 08:07 p_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19515 Nov 20 09:12 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    7227 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3074 Nov 20 09:17 report_numbers.out
-rw-r--r-- 1 ubuntu ubuntu    3788 Nov 20 09:16 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   25977 Nov 20 08:06 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1028 Nov 20 08:12 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1041 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1208 Nov 20 08:23 run_partner.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1154 Nov 20 08:07 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:07 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 08:07 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu    3383 Nov 20 08:03 uci_session.py
```
