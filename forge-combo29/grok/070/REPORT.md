# Seat 070, idea 20, S22

Idea S22 refuses the shallow ProbCut proof for one ply after a capture, and for one ply after a check has been answered, including when the side to move is no longer in check. The ProbCut margin is unchanged.
I built check option IdeaS22, default false, and spin IdeaS22_Ply, default 1 (range 0 to 16). The switch is read before any stack walk.
With the switch false, ProbCut keeps today's condition. With it true and the ply at 1, a node skips ProbCut when the move that entered it was a capture, or when the parent node was in check.

EXISTS: no. ProbCut in src/search.cpp already does not run while the side to move is in check. Nothing there skips the following quiet ply because the previous move was a capture or the previous node was in check.

## Honesty numbers

exe B and exe P, no setoption. bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. exe B also reproduced O depth 12 sum 9500069 (first three 41311, 24872, 28574) and G depth 12 sum 18466239.

## Steps

The number block below is the output of report_numbers.py, which reads the evidence files.

```
honesty_B
info string bench depth 11 nodes 312866 time 178 nps 1757674
info string bench depth 13 nodes 862329 time 441 nps 1955394
info string bench depth 16 nodes 3024920 time 1439 nps 2102098
nodes 4865609
honesty_P
info string bench depth 11 nodes 312866 time 169 nps 1851278
info string bench depth 13 nodes 862329 time 441 nps 1955394
info string bench depth 16 nodes 3024920 time 1458 nps 2074705
nodes 4865609
cmp_off_O
positions 200
differ 0
sum_left 9500069
sum_right 9500069
cmp_off_G
positions 353
differ 0
sum_left 18466239
sum_right 18466239
cmp_on_O_head
positions 200
differ 194
sum_left 9500069
sum_right 9571899
uci
option name IdeaS22 type check default false
option name IdeaS22_Ply type spin default 1 min 0 max 16
asan_meta_nm
nm_command=nm -C /tmp/forge-asan/forge | grep -c __asan_
nm_asan_count=35
asan_clean_hit_lines 0
asan_scratch_hit_lines 3
/tmp/scratch-forge/src/uci.cpp:46:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
match
finished_games 1106
Results of s22on vs s22off (20000 nodes, 1t, 16MB, match_OG.epd):
Elo: -5.65 +/- 9.85, nElo: -11.77 +/- 20.48
LOS: 13.00 %, DrawRatio: 62.93 %, PairsRatio: 0.85
Games: 1106, Wins: 334, Losses: 352, Draws: 420, Points: 544.0 (49.19 %)
Ptnml(0-2): [9, 102, 348, 86, 8], WL/DD Ratio: 2.00
--------------------------------------------------
start 2026-11-20T08:09:05Z
Total Time: 00:06:19 (hours:minutes:seconds)
fastchess_exit=0
end 2026-11-20T08:15:25Z
partner_apply
PARTNER_APPLY_CHECK_OK
partner_off
positions 200
differ 0
sum_left 9500069
sum_right 9500069
partner_on_vs_theirs
positions 200 200
differ 0
sum_mine 9571899
sum_theirs 9571899
partner_on_vs_B_head
positions 200
differ 194
sum_left 9500069
sum_right 9571899
partner_match
finished_games 600
Results of p020on vs p020off (20000 nodes, 1t, 16MB, R.fens):
Elo: 0.58 +/- 8.87, nElo: 1.82 +/- 27.80
LOS: 55.09 %, DrawRatio: 84.67 %, PairsRatio: 1.09
Games: 600, Wins: 260, Losses: 259, Draws: 81, Points: 300.5 (50.08 %)
Ptnml(0-2): [3, 19, 254, 22, 2], WL/DD Ratio: 11.70
--------------------------------------------------
start 2026-11-20T09:12:53Z
Total Time: 00:03:08 (hours:minutes:seconds)
fastchess_exit=0
end 2026-11-20T09:16:02Z
stamps
2026-11-20T07:55:03Z STEP 1 seat
2026-11-20T08:02:33Z STEP 2 honesty and B sums
2026-11-20T08:17:34Z STEP 3 idea proofs and match
2026-11-20T09:18:15Z STEP 4 partner 020
2026-11-20T09:18:41Z STEP 5 report
```

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 070, idea 20, Grok 4.7 |
| 2 two builds, honesty, B sums | done | HONESTY_B.txt, B_O_d12.nodes.txt, B_G_d12.nodes.txt | honesty exact; O 9500069; G 18466239 |
| 3 idea, proofs, match | done | idea.patch.txt, cmp_on_O.txt, match_result.txt | applies; off identical; on 194 of 200; Elo -5.65 +/- 9.85 over 1106 games |
| 4 partner 020 | done | partner020_apply_check.txt, partner_cmp_on_O.txt, partner_match_result.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) exe P, no setoption: the four honesty numbers above. File P_HONESTY.txt.
(2) S14 and IdeaS22 false. O depth 12: differ 0, both sums 9500069. G depth 12: differ 0, both sums 18466239. Position by position equal to exe B.
(3) S14 and IdeaS22 true, IdeaS22_Ply 1. O depth 12: differ 194 of 200, sum 9571899 against exe B's 9500069. The code runs. Six positions stay equal: 71 111 135 151 166 186 (same_on_O.txt).
(4) uci lists `option name IdeaS22 type check default false` and `option name IdeaS22_Ply type spin default 1 min 0 max 16`.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10. nm -C of that exe counted 35 __asan_ symbols. The run's raw log has 0 sanitizer lines. A scratch copy with one deliberate heap read past a 4-int array, on the FEN in scratch_fen.txt, built the same way and run through depth_sum.py, reported AddressSanitizer heap-buffer-overflow. sanitizer=clean.

git apply --check of idea.patch.txt on a fresh base printed APPLY_CHECK_OK.

Prediction, committed before any exe P measurement: O sum 10900000, wrong below 9550000 or above 14250000. Measured sum 9571899, inside that range. The point estimate was high. Elo prediction -8, wrong above 15 or below -45. Measured -5.65, inside that range.

## Match

exe P with the switch true against exe P with the switch false. Both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes. Openings match_OG.epd (200 O + 353 G). Both colours: 1106 games. fastchess concurrency 3. parse_match.py on match_fastchess.txt:

Elo -5.65 +/- 9.85, 1106 games, 334 wins, 352 losses, 420 draws. The interval is not entirely below 0, and the point estimate is not below -20, so I did not open the code for a second bug hunt. PGN `[Result` count is 1106.

## Partner

Partner is seat 020 (same idea; 120 had no branch at 2026-11-20T09:10:56Z). Their patch applies with git apply --check. My build of it, with my harness: honesty numbers match; IdeaS22 false matches exe B on O depth 12 (differ 0); IdeaS22 true and IdeaS22_Plies 1 matches their published O rows (differ 0, sum 9571899) and differs from exe B in 194 of 200, which is what they reported. Verdict: CONFIRMS.

Their switch on 300 of my R openings, both colours, 600 games: Elo 0.58 +/- 8.87. They had not published an R match. This game is mine, not one of their claims.

## Suspicions, not proven

The on sum rose only from 9500069 to 9571899, about three quarters of a percent, while 194 positions changed. The cooldown fires often and usually moves the node count a little. I do not know whether that small change is the whole Elo of -5.65 or noise around zero. The error bar crosses zero.

Seat 020's depth-12 rows matched mine exactly, including the sum 9571899. Their counter and my one-ply lookback are the same rule when the ply option is 1. That agreement is evidence about this rule, not about other ply values.

## What I did NOT do

I did not run G depth 12 with the switch on. I did not try IdeaS22_Ply other than 1. I did not run the sanitizer past the first 100 positions of G, or at depth 12. I did not replay the 1106-game match. I did not review seat 120, because that branch was absent. I did not open a pull request.

## What I am NOT sure about

I am not sure a longer cooldown would be better or worse. The idea asked for one ply, and that is the default.
I am not sure "after a check" might have meant only the in-check node. That node already skips ProbCut, so that reading would change nothing. I counted the quiet reply, where the side to move is no longer in check. Seat 020 did the same, and the rows matched.
OwnBook defaults to true because an embedded book is present. A nodes-only go does not consult it, because the book path requires a clock or a movetime. I still sent OwnBook false in both matches.
The ls listing at the end is the command output from just before it was pasted, so the byte size it shows for REPORT.md is the size before this listing was inserted.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/070/stamps.txt
?? config.json
?? forge-combo29/grok/070/REPORT.md
?? forge-combo29/grok/070/RESULT.txt
?? forge-combo29/grok/070/find_partner.sh
?? forge-combo29/grok/070/partner020_apply_check.txt
?? forge-combo29/grok/070/partner020_idea.patch.txt
?? forge-combo29/grok/070/partner020_on_O.tsv
?? forge-combo29/grok/070/partner_HONESTY.txt
?? forge-combo29/grok/070/partner_bench11.meta
?? forge-combo29/grok/070/partner_bench11.txt
?? forge-combo29/grok/070/partner_bench13.meta
?? forge-combo29/grok/070/partner_bench13.txt
?? forge-combo29/grok/070/partner_bench16.meta
?? forge-combo29/grok/070/partner_bench16.txt
?? forge-combo29/grok/070/partner_cmp_off_O.txt
?? forge-combo29/grok/070/partner_cmp_on_O.txt
?? forge-combo29/grok/070/partner_cmp_on_vs_B.txt
?? forge-combo29/grok/070/partner_match.pgn
?? forge-combo29/grok/070/partner_match.sh
?? forge-combo29/grok/070/partner_match_fastchess.txt
?? forge-combo29/grok/070/partner_match_result.txt
?? forge-combo29/grok/070/partner_off_O_d12.meta
?? forge-combo29/grok/070/partner_off_O_d12.nodes.txt
?? forge-combo29/grok/070/partner_off_O_d12.raw.txt
?? forge-combo29/grok/070/partner_on_O_d12.meta
?? forge-combo29/grok/070/partner_on_O_d12.nodes.txt
?? forge-combo29/grok/070/partner_on_O_d12.raw.txt
?? forge-combo29/grok/070/partner_perft5.meta
?? forge-combo29/grok/070/partner_perft5.txt
?? forge-combo29/grok/070/report_numbers.py
?? forge-combo29/grok/070/report_numbers.txt
?? forge-combo29/grok/070/tsv_nodes.py
```

## ls -la

```
total 8352
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:05 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     849 Nov 20 08:07 asan_G_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131708 Nov 20 08:07 asan_G_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     805 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10283 Nov 20 08:08 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     722 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3459 Nov 20 08:02 B_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  550006 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     726 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1922 Nov 20 08:02 B_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309077 Nov 20 08:01 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 08:06 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 08:06 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     351 Nov 20 08:06 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     886 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1272 Nov 20 08:03 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu    5360 Nov 20 08:01 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu    1008 Nov 20 08:17 find_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 07:58 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 07:58 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 07:58 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 07:58 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1210 Nov 20 07:58 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     684 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1176 Nov 20 08:05 honesty_run.sh
-rw-r--r-- 1 ubuntu ubuntu    4940 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     527 Nov 20 08:17 list_same.py
-rw-r--r-- 1 ubuntu ubuntu    1324 Nov 20 08:03 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  138350 Nov 20 08:15 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu 3489980 Nov 20 08:15 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     471 Nov 20 08:17 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1215 Nov 20 08:09 match.sh
-rw-r--r-- 1 ubuntu ubuntu     771 Nov 20 08:09 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:12 partner020_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    6354 Nov 20 09:11 partner020_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   16388 Nov 20 09:11 partner020_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:12 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:12 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:12 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 09:12 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     351 Nov 20 09:13 partner_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     687 Nov 20 09:12 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   73544 Nov 20 09:16 partner_match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 1602403 Nov 20 09:16 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     461 Nov 20 09:18 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1221 Nov 20 09:12 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     756 Nov 20 09:12 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1922 Nov 20 09:12 partner_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309565 Nov 20 09:12 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     784 Nov 20 09:12 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1922 Nov 20 09:12 partner_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309741 Nov 20 09:12 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:12 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:05 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:05 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:05 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     684 Nov 20 08:05 P_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     749 Nov 20 08:06 Poff_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3459 Nov 20 08:06 Poff_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  549968 Nov 20 08:06 Poff_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     753 Nov 20 08:05 Poff_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1922 Nov 20 08:06 Poff_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309109 Nov 20 08:05 Poff_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     779 Nov 20 08:06 Pon_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1922 Nov 20 08:06 Pon_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309288 Nov 20 08:06 Pon_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:05 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     249 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    8263 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2465 Nov 20 09:18 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    2443 Nov 20 09:18 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19249 Nov 20 08:03 R.fens
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:17 same_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:08 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1012 Nov 20 08:01 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     999 Nov 20 09:12 tsv_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     102 Nov 20 08:06 uci_options_IdeaS22.txt
```
