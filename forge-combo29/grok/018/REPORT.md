# Seat 018, idea 18, S16

IdeaS16 is a quiet pawn lever with no evaluation bonus. A friendly pawn whose every stopper is a lever, and whose one-step push square has at least as many friendly attackers as enemy attackers, marks the move that clears the last stopper. That move is a quiet pawn push that leaves the span empty, or a capture of the only stopper whose exchange is not losing. With the check on, the move gains IdeaS16_OrderBonus (default 4000) in the picker and loses IdeaS16_ReductionCut (default 1) ply of late-move reduction. The check defaults false, and false leaves the score and the reduction unchanged.

EXISTS: no. The search has no lever or stopper test. DESIGN.txt records the definition.

Honesty. Exe B and exe P, no setoption. Known pins: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. O depth 12 first three 41311 24872 28574.

The block below is the output of report_numbers.py, which reads the raw files.

```
HONESTY_B
info string bench depth 11 nodes 312866 time 195 nps 1604441
info string bench depth 13 nodes 862329 time 532 nps 1620919
info string bench depth 16 nodes 3024920 time 1496 nps 2022005
nodes 4865609
HONESTY_P
info string bench depth 11 nodes 312866 time 169 nps 1851278
info string bench depth 13 nodes 862329 time 446 nps 1933473
info string bench depth 16 nodes 3024920 time 1447 nps 2090476
nodes 4865609
COMPARE
compare_off_O.txt left 200 right 200 missing 0 differ 0
compare_off_G.txt left 353 right 353 missing 0 differ 0
compare_on_O.txt left 200 right 200 missing 0 differ 165
O_FIRST3
41311 24872 28574
O_SUMS
b_O_d12.tsv SUM	9500069
p_off_O_d12.tsv SUM	9500069
p_on_O_d12.tsv SUM	9482592
b_G_d12.tsv SUM	18466239
p_off_G_d12.tsv SUM	18466239
ASAN
hits 0
depth 10
positions 100
asan_symbols 35
MATCH
Results of s16on vs s16off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: -3.77 +/- 9.66, nElo: -8.00 +/- 20.48
Games: 1106, Wins: 333, Losses: 345, Draws: 428, Points: 547.0 (49.46 %)
PARTNER_HONESTY
info string bench depth 11 nodes 312866 time 176 nps 1777647
info string bench depth 13 nodes 862329 time 441 nps 1955394
info string bench depth 16 nodes 3024920 time 1435 nps 2107958
nodes 4865609
PARTNER_COMPARE
partner_compare_off_O.txt left 200 right 200 missing 0 differ 0
partner_compare_on_O.txt mine 200 sum 9515926 theirs 200 claimed_sum 9515926 missing 0 differ 0
partner_apply_check.txt EXIT:0
PARTNER_MATCH
Results of s16on vs s16off (20000 nodes, 1t, 16MB, R.epd):
Elo: 6.95 +/- 10.25, nElo: 18.85 +/- 27.80
Games: 600, Wins: 271, Losses: 259, Draws: 70, Points: 306.0 (51.00 %)
STEPS
step | status | evidence | result
1 seat | done | SEAT.txt | seat 018, idea 18, model Grok 4.7, 2026-11-20T07:52:11Z, token 2217374222915
2 honesty | done | HONESTY_B.txt honesty_p_*.txt | see HONESTY_B and HONESTY_P above
2 baseline | done | b_O_d12.tsv b_G_d12.tsv | SUM	9500069		 ; SUM	18466239		
3 apply | done | apply_check.txt idea.patch.txt | APPLY_CHECK_EXIT:0
3 off | done | compare_off_O.txt compare_off_G.txt | left 200 right 200 missing 0 differ 0 ; left 353 right 353 missing 0 differ 0
3 on | done | compare_on_O.txt p_on_O_d12.tsv | left 200 right 200 missing 0 differ 165 ; SUM	9482592		
3 uci | done | uci_p.txt | option name IdeaS16 type check default false | option name IdeaS16_OrderBonus type spin default 4000 min 0 max 30000 | option name IdeaS16_ReductionCut type spin default 1 min 0 max 4
3 sanitizer | done | asan_G100_d10.meta asan_G100_hits.txt asan_scratch.raw | asan_symbols 35 hits 0
3 match | done | match_OG.log | elo -3.77 err 9.66
4 partner | done | partner_apply_check.txt partner_compare_off_O.txt partner_compare_on_O.txt partner_match_R.log | EXIT:0 ; left 200 right 200 missing 0 differ 0 ; mine 200 sum 9515926 theirs 200 claimed_sum 9515926 missing 0 differ 0
RESULT_FIELDS
elo=-3.77 err=9.66 on_differs=165 of 200

```

Proofs.
(1) Honesty with no setoption matches the pins on exe B and on exe P. See HONESTY_B and HONESTY_P above.
(2) S14 and IdeaS16 false: O depth 12 differ 0 against exe B, sum 9500069. G depth 12 differ 0, sum 18466239.
(3) S14 and IdeaS16 true: O depth 12 differ 165 of 200, sum 9482592. The code runs.
(4) uci lists IdeaS16 check default false, IdeaS16_OrderBonus spin default 4000, IdeaS16_ReductionCut spin default 1.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build: nm count of __asan_ symbols is 35. First 100 of G at depth 10 with the switch on: 0 sanitizer lines (asan_G100_hits.txt). The same harness on a scratch copy with one deliberate read past a 4-int heap array, on the FEN in scratch_fen.epd, reports heap-buffer-overflow in asan_scratch.raw.

Match. Exe P with IdeaS16 true against the same exe with IdeaS16 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. Final line from match_OG.log: Elo -3.77 +/- 9.66, 333 wins, 345 losses, 428 draws. The interval crosses 0, so the -20 rule did not trigger a code search. Prediction was 9800000 (wrong outside 8500000..12500000) and Elo 4 (wrong outside -40..40). The measured sum 9482592 and Elo -3.77 are inside those ranges. prediction.txt was not edited.

Partner. Seat 068 is the next idea-18 branch. 118 had no branch. git apply --check of partner.patch.txt on the clean base exits 0. A fresh build matches the honesty pins. Switch false matches exe B's O depth-12 rows (differ 0). Switch true matches seat 068's own O depth-12 rows (differ 0, sum 9515926, the sum they published). Their switch, 300 R openings, both colours, 600 games: Elo 6.95 +/- 10.25. Verdict: CONFIRMS.

suspicions, not proven
The match Elo is a little below zero and the error bar includes zero. I do not have a separate sign that the implementation is inverted.

what I did NOT do
I did not open a pull request. I did not commit an engine source file. I did not copy another engine's code. I did not repeat the O+G opening list. I did not play a second match of my own patch, because seat 068 had a patch. The minute-60 handoff fetch had no FABLE_TO_grok file. I did not try other OrderBonus or ReductionCut values.

what I am NOT sure about
Helpers are every attacker of the push square, including pieces other than pawns. A double pawn step counts as a quiet push. Seat 068 counted pawn helpers only and required the quiet push to attack the stopper. Both readings fit the sentence. I am not sure which one the later net match will prefer.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/018/stamps.txt
?? config.json
?? forge-combo29/grok/018/REPORT.md
?? forge-combo29/grok/018/RESULT.txt
?? forge-combo29/grok/018/compare_partner_rows.py
?? forge-combo29/grok/018/partner.patch.txt
?? forge-combo29/grok/018/partner_P_HONESTY.txt
?? forge-combo29/grok/018/partner_P_on_O_d12.txt
?? forge-combo29/grok/018/partner_apply_check.txt
?? forge-combo29/grok/018/partner_compare_off_O.txt
?? forge-combo29/grok/018/partner_compare_on_O.txt
?? forge-combo29/grok/018/partner_honesty_bench11.txt
?? forge-combo29/grok/018/partner_honesty_bench13.txt
?? forge-combo29/grok/018/partner_honesty_bench16.txt
?? forge-combo29/grok/018/partner_honesty_perft5.txt
?? forge-combo29/grok/018/partner_match_R.log
?? forge-combo29/grok/018/partner_match_R.pgn
?? forge-combo29/grok/018/partner_off_O_d12.meta
?? forge-combo29/grok/018/partner_off_O_d12.raw
?? forge-combo29/grok/018/partner_off_O_d12.tsv
?? forge-combo29/grok/018/partner_on_O_d12.meta
?? forge-combo29/grok/018/partner_on_O_d12.raw
?? forge-combo29/grok/018/partner_on_O_d12.tsv
?? forge-combo29/grok/018/report_numbers.py
?? forge-combo29/grok/018/report_numbers.txt
?? forge-combo29/grok/018/run_partner_match.sh

$ ls -la /agent/repos/dwqww/forge-combo29/grok/018
total 9620
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:14 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 08:21 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     985 Nov 20 08:19 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  119221 Nov 20 08:18 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu    6421 Nov 20 08:18 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu       2 Nov 20 08:27 asan_G100_hits.txt
-rw-r--r-- 1 ubuntu ubuntu    8648 Nov 20 08:18 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:17 asan_symbol_count.txt
-rw-r--r-- 1 ubuntu ubuntu     950 Nov 20 08:13 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507472 Nov 20 08:13 b_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   22930 Nov 20 08:13 b_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:13 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  281824 Nov 20 08:13 b_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   15796 Nov 20 08:13 b_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu      38 Nov 20 08:21 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      38 Nov 20 08:21 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      40 Nov 20 08:21 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1292 Nov 20 09:09 compare_partner_rows.py
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:15 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    1552 Nov 20 08:20 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu    5305 Nov 20 08:13 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:14 honesty_b.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 07:59 honesty_b.sha
-rw-r--r-- 1 ubuntu ubuntu     594 Nov 20 08:14 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:15 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:15 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:15 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:27 honesty_p.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:15 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   10244 Nov 20 08:15 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1526 Nov 20 08:20 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    6893 Nov 20 08:27 match_OG_config.json
-rw-r--r-- 1 ubuntu ubuntu  127729 Nov 20 08:27 match_OG.log
-rw-r--r-- 1 ubuntu ubuntu 4580006 Nov 20 08:27 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu    1044 Nov 20 08:20 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:19 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:19 openings_smoke.epd
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:13 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      38 Nov 20 09:09 partner_compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 09:09 partner_compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   61691 Nov 20 09:12 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu 1994315 Nov 20 09:12 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     999 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282107 Nov 20 09:09 partner_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   15796 Nov 20 09:09 partner_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282300 Nov 20 09:09 partner_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   15795 Nov 20 09:09 partner_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu   11688 Nov 20 09:08 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:08 partner_P_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   15368 Nov 20 09:08 partner_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     992 Nov 20 08:15 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507653 Nov 20 08:15 p_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   22930 Nov 20 08:15 p_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     996 Nov 20 08:15 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  282034 Nov 20 08:15 p_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   15796 Nov 20 08:15 p_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     995 Nov 20 08:15 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  281985 Nov 20 08:15 p_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu   15795 Nov 20 08:15 p_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 08:14 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19237 Nov 20 08:21 R.epd
-rw-r--r-- 1 ubuntu ubuntu   13185 Nov 20 09:14 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    5203 Nov 20 09:14 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    2877 Nov 20 09:14 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:14 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:21 R.meta
-rwxr-xr-x 1 ubuntu ubuntu    1019 Nov 20 08:20 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1037 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:18 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5113 Nov 20 08:16 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu     698 Nov 20 08:14 write_honesty_b.py
```
