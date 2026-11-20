# Seat 085, idea 35, IdeaA4

Idea 35 puts the capture history into the two capture SEE pruning thresholds, behind check option IdeaA4, default false.
When the option is on, a capture's threshold moves by clamp(history / IdeaA4_Divisor, -IdeaA4_Cap, IdeaA4_Cap); the defaults are divisor 8 and cap 256.
The quiet-move SEE gate is unchanged. While IdeaA4 is false the new branches are not taken, so both thresholds stay today's expressions.

EXISTS: no. In the plain engine the quiescence gate is see_ge(move, -QsSeeMargin) and the noisy gate is see_ge(move, -SeeNoisyMultiplier * depth). Neither threshold reads capture history.

## Honesty

Exe B and exe P, no setoption, fresh process per line. Both matched bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609. Exe B at S14, Threads 1, Hash 16: O depth 12 sum 9500069, first three 41311 / 24872 / 28574; G depth 12 sum 18466239.

## Table

The block below is the output of report_numbers.py, which reads the raw files.

```
HONESTY_B
honesty exe B
exe: /agent/repos/base/forge-combo29/build/forge
sha256: e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id name: Chess Engine Forge 6.4.24 candidate

bench 11 -> nodes 312866 expected 312866 OK raw HONESTY_B_bench11.txt
bench 13 -> nodes 862329 expected 862329 OK raw HONESTY_B_bench13.txt
bench 16 -> nodes 3024920 expected 3024920 OK raw HONESTY_B_bench16.txt
go perft 5 -> nodes 4865609 expected 4865609 OK raw HONESTY_B_perft5.txt
ALL OK
HONESTY_P
honesty exe P
exe: /agent/repos/work/forge-combo29/build/forge
sha256: de22eb4496d657a107bc0aec4db8fdbb57fa86ccb3f820a7b71634198d9ae055
id name: Chess Engine Forge 6.4.24 candidate

bench 11 -> nodes 312866 expected 312866 OK raw HONESTY_P_bench11.txt
bench 13 -> nodes 862329 expected 862329 OK raw HONESTY_P_bench13.txt
bench 16 -> nodes 3024920 expected 3024920 OK raw HONESTY_P_bench16.txt
go perft 5 -> nodes 4865609 expected 4865609 OK raw HONESTY_P_perft5.txt
ALL OK
O_B
positions 200
sum 9500069
first3 41311 24872 28574
G_B
positions 353
sum 18466239
first3 37203 70845 144383
O_OFF
positions 200
equal 200
differ 0
G_OFF
positions 353
equal 353
differ 0
O_ON
positions 200
equal 0
differ 200
pos 1 41311 30185
pos 2 24872 24796
pos 3 28574 39955
pos 4 27838 41553
pos 5 18020 18124
pos 6 43043 39188
pos 7 56414 67281
pos 8 32317 48273
pos 9 37995 34680
pos 10 53959 63546
pos 11 26257 31640
pos 12 58746 41578
pos 13 30949 65699
pos 14 34274 52188
pos 15 21125 25824
pos 16 51393 55361
pos 17 71168 59766
pos 18 50554 70572
pos 19 52621 55317
pos 20 38831 43931
... 180 more
O_ON_SUM
positions 200
sum 9967809
first3 30185 24796 39955
UCI
option name IdeaA4 type check default false
option name IdeaA4_Divisor type spin default 8 min 1 max 1024
option name IdeaA4_Cap type spin default 256 min 0 max 2000
ASAN_NM
35
ASAN_G100
positions 100
sum 2065646
first3 10921 11100 37927
ASAN_SCRATCH_NM
35
ASAN_SCRATCH_HIT
141:==26861==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000d0 at pc 0x55e4bb6749a3 bp 0x7ffc37853010 sp 0x7ffc37853000
MATCH
Results of IdeaA4on vs IdeaA4off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -10.37 +/- 10.48, nElo: -20.28 +/- 20.48
LOS: 2.61 %, DrawRatio: 60.94 %, PairsRatio: 0.77
Games: 1106, Wins: 327, Losses: 360, Draws: 419, Points: 536.5 (48.51 %)
Ptnml(0-2): [15, 107, 337, 84, 10], WL/DD Ratio: 1.96
--------------------------------------------------
Finished match
OWN_APPLY
own_apply_check_exit:0
PARTNER_APPLY
partner_apply_check_exit:0
PARTNER_HONESTY
honesty partner exe
exe: /agent/repos/partner/build/forge
sha256: 25cb29353019821c7c46912ad496fe05fc651508573bd194ab9d7f41695a6138
id name: Chess Engine Forge 6.4.24 candidate

bench 11 -> nodes 312866 expected 312866 OK raw partner_HONESTY_bench11.txt
bench 13 -> nodes 862329 expected 862329 OK raw partner_HONESTY_bench13.txt
bench 16 -> nodes 3024920 expected 3024920 OK raw partner_HONESTY_bench16.txt
go perft 5 -> nodes 4865609 expected 4865609 OK raw partner_HONESTY_perft5.txt
ALL OK
PARTNER_OFF
left forge-combo29/grok/085/O_d12_B.nodes.txt n 200 sum 9500069
right forge-combo29/grok/085/partner_O_d12_off.nodes.txt n 200 sum 9500069
positions 200
fen_or_index_mismatch 0
node_differ 0
node_equal 200
PARTNER_ON
left forge-combo29/grok/085/partner_035_p_on_O_d12.nodes n 200 sum 9759675
right forge-combo29/grok/085/partner_O_d12_on.nodes.txt n 200 sum 9759675
positions 200
fen_or_index_mismatch 0
node_differ 0
node_equal 200
PARTNER_MATCH
Results of PartnerOn vs PartnerOff (20000 nodes, 1t, 16MB, R_positions.fens):
Elo: 1.74 +/- 11.06, nElo: 4.37 +/- 27.80
LOS: 62.09 %, DrawRatio: 78.33 %, PairsRatio: 0.97
Games: 600, Wins: 262, Losses: 259, Draws: 79, Points: 301.5 (50.25 %)
Ptnml(0-2): [3, 30, 235, 25, 7], WL/DD Ratio: 18.58
--------------------------------------------------
Finished match
TABLE
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 085, idea 35, model Grok 4.7, 2026-11-20T07:55:07Z, token 75611273685
2 honesty B | done | HONESTY_B.txt | ALL OK
2 O depth 12 B | done | O_d12_B.sum.txt | positions 200 sum 9500069 first3 41311 24872 28574
2 G depth 12 B | done | G_d12_B.sum.txt | positions 353 sum 18466239 first3 37203 70845 144383
3 patch applies | done | idea.patch.txt own_apply_check.txt | own_apply_check_exit:0
3 honesty P | done | HONESTY_P.txt | ALL OK
3 off O and G | done | compare_O_off.txt compare_G_off.txt | O differ 0; G differ 0
3 on O | done | compare_O_on.txt O_d12_P_on.sum.txt | differ 200; sum 9967809
3 uci options | done | uci_options_IdeaA4.txt | option name IdeaA4 type check default false option name IdeaA4_Divisor type spin default 8 min 1 max 1024 option name IdeaA4_Cap type spin default 256 min 0 max 2000
3 sanitizer | done | asan_nm_count.txt asan_scratch_hit.txt | nm 35 asan_errors 0
3 match | done | match_result.txt match_on_off.pgn | Elo: -10.37 +/- 10.48, nElo: -20.28 +/- 20.48; Games: 1106, Wins: 327, Losses: 360, Draws: 419, Points: 536.5 (48.51 %)
4 partner 035 | done | partner_compare_off.txt partner_compare_on.txt partner_match_r.log | off node_differ 0; on node_differ 0; Games: 600, Wins: 262, Losses: 259, Draws: 79, Points: 301.5 (50.25 %)
5 report | done | REPORT.md RESULT.txt | written this step

```

## Proofs

(1) Honesty on exe P with no setoption: the four node counts match. HONESTY_P.txt.
(2) S14 and IdeaA4 false: O depth 12 differ 0 of 200 against exe B, G depth 12 differ 0 of 353. compare_O_off.txt, compare_G_off.txt.
(3) S14 and IdeaA4 true: O depth 12 differ 200 of 200, sum 9967809. compare_O_on.txt, O_d12_P_on.sum.txt.
(4) uci lists IdeaA4 check default false, IdeaA4_Divisor spin default 8, IdeaA4_Cap spin default 256. uci_options_IdeaA4.txt.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build: nm -C count of __asan_ is 35. First 100 of G at depth 10 with IdeaA4 true: 0 sanitizer ERROR lines, sum 2065646. A scratch copy with one heap read past the end of a 4-int array, on the FEN in scratch_fen.fen, run through search_depth.py, reports ERROR: AddressSanitizer: heap-buffer-overflow. asan_nm_count.txt, asan_G100_on.raw.txt, asan_scratch_hit.txt.

git apply --check of idea.patch.txt on a clean base: exit 0. own_apply_check.txt.

## Match

Exe P with IdeaA4 true against exe P with IdeaA4 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games, concurrency 3. fastchess from github.com/Disservin/fastchess.

```
Results of IdeaA4on vs IdeaA4off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -10.37 +/- 10.48, nElo: -20.28 +/- 20.48
LOS: 2.61 %, DrawRatio: 60.94 %, PairsRatio: 0.77
Games: 1106, Wins: 327, Losses: 360, Draws: 419, Points: 536.5 (48.51 %)
Ptnml(0-2): [15, 107, 337, 84, 10], WL/DD Ratio: 1.96
--------------------------------------------------
Finished match

```

Prediction (prediction.txt, not edited): O sum 10200000, wrong outside 7000000..14000000; Elo +8, wrong outside -60..+60. Actual sum 9967809 and Elo -10.37 sit inside those ranges. The Elo is not below -20 with the whole printed interval below 0 (-10.37 +/- 10.48 reaches about +0.11), so I did not open the code again after the match.

## Partner

Partner is seat 035 (idea 35; 135 has no branch, so the next seat after 085 wraps to 035). git apply --check on a clean base exited 0. Honesty matched. Switch false reproduced exe B's O depth-12 rows, 0 of 200 differ. Switch true reproduced seat 035's own O depth-12 rows, 0 of 200 differ, sum 9759675. A 600-game match of their switch on my 300 R openings, both colours, finished Elo 1.74 +/- 11.06. Verdict: CONFIRMS.

## suspicions, not proven

The built-in-net match is slightly negative and the interval still touches zero. That is not a shown mistake in the patch. Seat 035 used a milder divisor (16) and a depth-scaled clamp and their own 1106-game match was -0.94 +/- 10.32. I do not know which scale is better on the owner's net.

## what I did NOT do

I did not play a second match of my own patch on R, because seat 035 had a patch. I did not re-play their 1106-game OG match. I did not edit prediction.txt after it was pushed. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60. I did not open a pull request.

## what I am NOT sure about

I am not sure the divisor 8 and cap 256 are the right size; they were chosen so a few hundred history points can cross see_ge, and they do change every O position. I am not sure fastchess DrawRatio on the R match is draws/games: the Results block says Draws 79 and DrawRatio 78.33 percent, and I left that block as printed. I am not sure the printed +/- is a 95 percent half-width; I used it as the err field.

times: see stamps.txt

## git status --short

```
A  forge-combo29/grok/085/REPORT.md
A  forge-combo29/grok/085/RESULT.txt
A  forge-combo29/grok/085/compare_partner_nodes.py
M  forge-combo29/grok/085/config.json
A  forge-combo29/grok/085/own_apply_check.txt
A  forge-combo29/grok/085/partner_035_idea.patch.txt
A  forge-combo29/grok/085/partner_035_p_on_O_d12.nodes
A  forge-combo29/grok/085/partner_HONESTY.txt
A  forge-combo29/grok/085/partner_HONESTY_bench11.txt
A  forge-combo29/grok/085/partner_HONESTY_bench11.txt.meta
A  forge-combo29/grok/085/partner_HONESTY_bench13.txt
A  forge-combo29/grok/085/partner_HONESTY_bench13.txt.meta
A  forge-combo29/grok/085/partner_HONESTY_bench16.txt
A  forge-combo29/grok/085/partner_HONESTY_bench16.txt.meta
A  forge-combo29/grok/085/partner_HONESTY_perft5.txt
A  forge-combo29/grok/085/partner_HONESTY_perft5.txt.meta
A  forge-combo29/grok/085/partner_O_d12_off.nodes.txt
A  forge-combo29/grok/085/partner_O_d12_off.raw.txt
A  forge-combo29/grok/085/partner_O_d12_off.raw.txt.meta
A  forge-combo29/grok/085/partner_O_d12_off.sum.txt
A  forge-combo29/grok/085/partner_O_d12_on.nodes.txt
A  forge-combo29/grok/085/partner_O_d12_on.raw.txt
A  forge-combo29/grok/085/partner_O_d12_on.raw.txt.meta
A  forge-combo29/grok/085/partner_O_d12_on.sum.txt
A  forge-combo29/grok/085/partner_apply_check.txt
A  forge-combo29/grok/085/partner_compare_off.txt
A  forge-combo29/grok/085/partner_compare_on.txt
A  forge-combo29/grok/085/partner_match_r.log
A  forge-combo29/grok/085/partner_match_r.pgn
A  forge-combo29/grok/085/report_numbers.py
A  forge-combo29/grok/085/report_numbers.txt
M  forge-combo29/grok/085/stamps.txt
```

## ls -la

```
total 8840
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu    5885 Nov 20 08:09 asan_G100_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  131846 Nov 20 08:09 asan_G100_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     981 Nov 20 08:09 asan_G100_on.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:09 asan_G100_on.sum.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:08 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     142 Nov 20 08:10 asan_scratch_hit.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:10 asan_scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    9763 Nov 20 08:10 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:07 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu    1123 Nov 20 08:06 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:07 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     417 Nov 20 08:07 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1261 Nov 20 09:11 compare_partner_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    7325 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    1238 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu     357 Nov 20 08:16 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:03 G_d12_B.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  549643 Nov 20 08:03 G_d12_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:03 G_d12_B.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:03 G_d12_B.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:07 G_d12_P_off.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  550056 Nov 20 08:07 G_d12_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     977 Nov 20 08:07 G_d12_P_off.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:07 G_d12_P_off.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1596 Nov 20 08:05 generate_r.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:08 G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 HONESTY_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 HONESTY_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:01 HONESTY_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:01 HONESTY_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    2838 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     474 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:06 HONESTY_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:06 HONESTY_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:06 HONESTY_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 08:06 HONESTY_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     474 Nov 20 08:07 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    5733 Nov 20 08:06 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  132366 Nov 20 08:15 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 3598886 Nov 20 08:15 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     355 Nov 20 08:16 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:03 O_d12_B.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  308898 Nov 20 08:03 O_d12_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 08:03 O_d12_B.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:03 O_d12_B.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:06 O_d12_P_off.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309275 Nov 20 08:06 O_d12_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     983 Nov 20 08:06 O_d12_P_off.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:06 O_d12_P_off.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   14761 Nov 20 08:07 O_d12_P_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309211 Nov 20 08:07 O_d12_P_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     982 Nov 20 08:07 O_d12_P_on.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:07 O_d12_P_on.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:16 own_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    6037 Nov 20 09:11 partner_035_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   14758 Nov 20 09:11 partner_035_p_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu      27 Nov 20 09:16 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:12 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:12 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_HONESTY_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 partner_HONESTY_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_HONESTY_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 partner_HONESTY_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_HONESTY_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:12 partner_HONESTY_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner_HONESTY_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:12 partner_HONESTY_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     493 Nov 20 09:12 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   70346 Nov 20 09:15 partner_match_r.log
-rw-r--r-- 1 ubuntu ubuntu 1810566 Nov 20 09:15 partner_match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:12 partner_O_d12_off.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309271 Nov 20 09:12 partner_O_d12_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     974 Nov 20 09:12 partner_O_d12_off.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 09:12 partner_O_d12_off.sum.txt
-rw-r--r-- 1 ubuntu ubuntu   14758 Nov 20 09:12 partner_O_d12_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309462 Nov 20 09:12 partner_O_d12_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     973 Nov 20 09:12 partner_O_d12_on.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 09:12 partner_O_d12_on.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     265 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    9671 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4239 Nov 20 09:17 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    5227 Nov 20 09:17 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19877 Nov 20 08:06 R_positions.fens
-rwxr-xr-x 1 ubuntu ubuntu    1090 Nov 20 08:08 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:10 scratch_fen.fen
-rw-r--r-- 1 ubuntu ubuntu    6414 Nov 20 08:02 search_depth.py
-rw-r--r-- 1 ubuntu ubuntu      75 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:06 uci_options_IdeaA4.txt
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 08:06 uci_options_P.txt
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:06 uci_options_P.txt.meta
```
