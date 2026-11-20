# Seat 062, idea 12, P20

P20 scores a known dead ending before the network: bare kings and king plus one minor as 0, two knights versus a lone king as 0, and king, bishop and knight versus a lone king as a corner drive.
The plain engine already does this. The switch is the check option DeadMaterial, default false.
I turned the two hardcoded drive weights into spins IdeaP20_Corner (default 28) and IdeaP20_King (default 12). With those defaults the corner-drive formula is the one already in the source, so a default engine takes today's path.

EXISTS: forge-combo29/src/eval.cpp:516
The on/off option is already advertised in forge-combo29/src/uci.cpp. The weights were constexpr 28 and 12 and were not options. They are options now. git apply --check of idea.patch.txt on a fresh copy of the base printed MY_APPLY_CHECK_OK (my_apply_check.txt).

## Honesty numbers

Same four lines on exe B and on exe P, each a fresh process, no setoption. From HONESTY_B.txt and HONESTY_P.txt:

bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Both files end ALL_PASS.

Exe B with S14, Threads 1, Hash 16: O depth 12 sum 9500069, first three 41311 / 24872 / 28574. G depth 12 sum 18466239.

## Table

Pasted from make_tables.py, which reads the raw files:

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 062 idea 12
2 honesty B | done | HONESTY_B.txt | bench 11/13/16 and perft 5 match
2 O depth 12 B | done | b_O_d12.meta | 9500069
2 G depth 12 B | done | b_G_d12.meta | 18466239
3 prediction | done | prediction.txt | committed before measuring
3 patch applies | done | my_apply_check.txt | MY_APPLY_CHECK_OK
3 proof 1 honesty P | done | HONESTY_P.txt | ALL_PASS
3 proof 2 off | done | cmp_off_O.txt cmp_off_G.txt | 0 of 200 and 0 of 353
3 proof 3 on O | done | cmp_on_O.txt | 0 of 200
3 proof 4 uci | done | P_idname.txt | DeadMaterial false, Corner 28, King 12
3 proof 5 sanitizer | done | asan_G_d10.meta asan_bug.stderr | nm 35, clean run, bug run reports overflow
3 match | done | match_full.txt | 1106 games
4 partner 012 | done | partner012_cmp.txt partner012_match.txt | CONFIRMS
```

## Proofs

(1) Exe P, no setoption: 312866, 862329, 3024920, 4865609. HONESTY_P.txt ALL_PASS.

(2) Exe P, S14, DeadMaterial false: O depth 12 sum 9500069, 0 of 200 differ from exe B (cmp_off_O.txt). G depth 12 sum 18466239, 0 of 353 differ (cmp_off_G.txt).

(3) Exe P, S14, DeadMaterial true, spins left at 28 and 12: O depth 12 sum 9500069, 0 of 200 differ (cmp_on_O.txt). G at the same setting is also 0 of 353 (cmp_on_G.txt). The true branch is not reached in those trees. KK and king plus one minor are already insufficient material, so search returns a draw before evaluation. The scores that can change a search are two knights versus a lone king, and bishop plus knight versus a lone king. probe_off.txt versus probe_on.txt shows that: the two-knight position goes from 16889 nodes and a network total of 261 to 2868 nodes and total 0. A bishop-and-knight position goes from total 272 to total 796, and the node count changes. probe_corner.txt sets IdeaP20_Corner 1 and IdeaP20_King 1 and the bishop-and-knight total moves again (596 on the same position). The code runs. The opening set and the game set at depth 12 do not.

(4) The uci listing in P_idname.txt contains:
option name DeadMaterial type check default false
option name IdeaP20_Corner type spin default 28 min 0 max 256
option name IdeaP20_King type spin default 12 min 0 max 256

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. nm -C of that exe, grep -c __asan_, is 35 (asan_G_d10.meta). First 100 of G at depth 10 with DeadMaterial true: no sanitizer line (no stderr file, asan_G_d10.txt has no ERROR line). A scratch copy with one heap read past the end of a 4-int array, only when the FEN is 4k3/8/8/8/8/8/8/4K2R w - - 0 1, built the same way and run through run_depth.py, prints AddressSanitizer heap-buffer-overflow in asan_bug.stderr.

## Match

Exe P with DeadMaterial true against exe P with DeadMaterial false. Both S14, Threads 1, Hash 16, 20000 nodes. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3. Final lines of match_full.txt:

```
Elo: 0.31 +/- 0.62, nElo: 10.46 +/- 20.48
Games: 1106, Wins: 337, Losses: 336, Draws: 433, Points: 553.5 (50.05 %)
Ptnml(0-2): [0, 0, 552, 1, 0], WL/DD Ratio: 1.56
```

prediction.txt said the O sum would be 9500069 and the Elo point would be 0, wrong if the point were outside -30 to +30. The sum is 9500069 and the point is 0.31. The interval is not entirely below 0, and the point is not below -20. No second look for a code mistake.

## Partner

Seat 112 has no branch. The next seat with this idea is 012. Their idea.patch.txt applies on a fresh base (partner012_apply.txt). A rebuild here has sha256 ae070d3f1ec8b470d9281e1969142b1dfc49125c39558e56133b638a31a261c9, the same hash as in their meta. Honesty numbers match. Switch false versus exe B's O rows: 0 of 200 differ. Switch true versus their published O rows: 0 of 200 differ (partner012_cmp.txt). Their own OG match reports Elo 0.31 +/- 0.62 over 1106 games, the same final line shape as mine. I did not replay that match. I played their binary on my 300 R openings, both colours, 600 games (partner012_match.txt):

```
Elo: -0.58 +/- 1.96, nElo: -8.19 +/- 27.80
Games: 600, Wins: 243, Losses: 244, Draws: 113, Points: 299.5 (49.92 %)
```

Verdict: CONFIRMS.

## Suspicions, not proven

The pentanomial on the 1106-game match is [0, 0, 552, 1, 0]. One pair is not a level split. I did not open that game. It is not shown to be a rules mistake.
Their spins use max 1000 and mine use max 256. At the defaults 28 and 12 the searches match. Nothing here tests a weight above 256.

## What I did not do

I did not add a second check option named IdeaP20. DeadMaterial is already that switch.
I did not replay seat 012's 1106-game opening match.
I did not review seat 112. It had no branch at 2026-11-20T09:09:26Z.
I did not play the match with the corner weights moved off 28 and 12. The match is the existing switch, weights at today's numbers.
The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 had no FABLE_TO_grok file.

## What I am not sure about

I am not sure a search deeper than 12 from set G would stay node-identical. At depth 12 it is identical, position by position.
fastchess prints DrawRatio 99.82% on a match that has 433 draws out of 1106 games. I read 99.82% as 552/553 level pairs, and I am not sure that is the field they mean.
I am not sure the +/- 0.62 error is a good description of a match where 552 of 553 pairs are level. The point estimate 0.31 is what the tool printed.

times: see stamps.txt

## git status --short and ls -la

These two blocks were pasted from the commands run immediately before the final commit.

```
$ git status --short
 M forge-combo29/grok/062/stamps.txt
?? config.json
?? forge-combo29/grok/062/HONESTY_partner012.txt
?? forge-combo29/grok/062/REPORT.md
?? forge-combo29/grok/062/RESULT.txt
?? forge-combo29/grok/062/make_tables.py
?? forge-combo29/grok/062/my_apply_check.txt
?? forge-combo29/grok/062/partner012_O_off.rows
?? forge-combo29/grok/062/partner012_O_on.rows
?? forge-combo29/grok/062/partner012_apply.txt
?? forge-combo29/grok/062/partner012_bench11.meta
?? forge-combo29/grok/062/partner012_bench11.txt
?? forge-combo29/grok/062/partner012_bench13.meta
?? forge-combo29/grok/062/partner012_bench13.txt
?? forge-combo29/grok/062/partner012_bench16.meta
?? forge-combo29/grok/062/partner012_bench16.txt
?? forge-combo29/grok/062/partner012_cmp.txt
?? forge-combo29/grok/062/partner012_idname.txt
?? forge-combo29/grok/062/partner012_match.err
?? forge-combo29/grok/062/partner012_match.pgn
?? forge-combo29/grok/062/partner012_match.txt
?? forge-combo29/grok/062/partner012_off_O.meta
?? forge-combo29/grok/062/partner012_off_O.rows
?? forge-combo29/grok/062/partner012_off_O.txt
?? forge-combo29/grok/062/partner012_on_O.meta
?? forge-combo29/grok/062/partner012_on_O.rows
?? forge-combo29/grok/062/partner012_on_O.txt
?? forge-combo29/grok/062/partner012_perft5.meta
?? forge-combo29/grok/062/partner012_perft5.txt
?? forge-combo29/grok/062/report_tables.txt
?? forge-combo29/grok/062/run_partner_match.sh

$ ls -la forge-combo29/grok/062
total 9564
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 08:08 asan_bug.fen
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:08 asan_bug_nm.txt
-rw-r--r-- 1 ubuntu ubuntu      54 Nov 20 08:08 asan_bug_runner.txt
-rw-r--r-- 1 ubuntu ubuntu    6211 Nov 20 08:08 asan_bug.stderr
-rw-r--r-- 1 ubuntu ubuntu   11451 Nov 20 08:08 asan_G_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    1373 Nov 20 08:07 asan_G_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  131714 Nov 20 08:07 asan_G_d10.txt
-rw-r--r-- 1 ubuntu ubuntu   37186 Nov 20 08:03 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:03 b_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550212 Nov 20 08:03 b_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   24399 Nov 20 08:03 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:03 b_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309176 Nov 20 08:03 b_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 cmp_on_G.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     835 Nov 20 08:05 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1460 Nov 20 08:11 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    1287 Nov 20 08:10 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu     244 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     244 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     246 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:01 honesty_b_idname.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     398 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     388 Nov 20 09:10 HONESTY_partner012.txt
-rw-r--r-- 1 ubuntu ubuntu     366 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    4671 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    3415 Nov 20 09:15 make_tables.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 match_full.err
-rw-r--r-- 1 ubuntu ubuntu 3575691 Nov 20 08:16 match_full.pgn
-rw-r--r-- 1 ubuntu ubuntu  108124 Nov 20 08:17 match_full.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 match_openings.epd
-rw-r--r-- 1 ubuntu ubuntu      18 Nov 20 09:15 my_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 09:10 partner012_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 09:10 partner012_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner012_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 09:10 partner012_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner012_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:10 partner012_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 partner012_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     243 Nov 20 09:11 partner012_cmp.txt
-rw-r--r-- 1 ubuntu ubuntu    5057 Nov 20 09:10 partner012_idname.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner012_match.err
-rw-r--r-- 1 ubuntu ubuntu 1876834 Nov 20 09:14 partner012_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   54226 Nov 20 09:14 partner012_match.txt
-rw-r--r-- 1 ubuntu ubuntu   24423 Nov 20 09:10 partner012_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:10 partner012_off_O.rows
-rw-r--r-- 1 ubuntu ubuntu  308957 Nov 20 09:10 partner012_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu   24421 Nov 20 09:10 partner012_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:10 partner012_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu  309016 Nov 20 09:10 partner012_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 09:10 partner012_O_off.rows
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 09:10 partner012_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 09:10 partner012_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 partner012_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     244 Nov 20 08:04 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     244 Nov 20 08:04 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     246 Nov 20 08:04 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5055 Nov 20 08:04 P_idname.txt
-rw-r--r-- 1 ubuntu ubuntu   37233 Nov 20 08:04 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:04 p_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550333 Nov 20 08:04 p_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   24446 Nov 20 08:04 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:04 p_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309436 Nov 20 08:04 p_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   37231 Nov 20 08:05 p_on_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5199 Nov 20 08:05 p_on_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550272 Nov 20 08:05 p_on_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   24444 Nov 20 08:04 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 08:04 p_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309340 Nov 20 08:04 p_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:04 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1277 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     792 Nov 20 08:06 probe_corner.txt
-rw-r--r-- 1 ubuntu ubuntu   14496 Nov 20 08:06 probe_corner.txt.raw
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:06 probe_dead.fens
-rw-r--r-- 1 ubuntu ubuntu     834 Nov 20 08:06 probe_off.txt
-rw-r--r-- 1 ubuntu ubuntu   14827 Nov 20 08:06 probe_off.txt.raw
-rw-r--r-- 1 ubuntu ubuntu     796 Nov 20 08:06 probe_on.txt
-rw-r--r-- 1 ubuntu ubuntu   14496 Nov 20 08:06 probe_on.txt.raw
-rw-r--r-- 1 ubuntu ubuntu   19904 Nov 20 08:10 R.epd
-rw-r--r-- 1 ubuntu ubuntu    8322 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3225 Nov 20 09:15 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    7647 Nov 20 08:03 run_depth.py
-rw-r--r-- 1 ubuntu ubuntu    3157 Nov 20 08:01 run_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    3175 Nov 20 08:04 run_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    1351 Nov 20 08:10 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1253 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    5291 Nov 20 08:05 run_probe.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    1477 Nov 20 08:03 smoke_b_O.meta
-rw-r--r-- 1 ubuntu ubuntu      39 Nov 20 08:03 smoke_b_O.rows
-rw-r--r-- 1 ubuntu ubuntu   10363 Nov 20 08:03 smoke_b_O.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 smoke_match.err
-rw-r--r-- 1 ubuntu ubuntu   34307 Nov 20 08:10 smoke_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     816 Nov 20 08:10 smoke_match.txt
-rw-r--r-- 1 ubuntu ubuntu     161 Nov 20 09:16 stamps.txt
```
