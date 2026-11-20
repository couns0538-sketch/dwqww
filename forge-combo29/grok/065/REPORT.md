Idea S15 searches a rook move that reaches a passed pawn's file at full depth, in a rook ending of at least eight pieces.
The switch is IdeaS15, a check, default false. The only number is IdeaS15_MinPieces, a spin, default 8.
When the switch is on and the move qualifies, the late-move reduction is set to 0. That does not extend, and the evaluation is not changed.

EXISTS: no. Passed pawns are scored in forge-combo29/src/eval.cpp. Nothing in the search skips a reduction for a rook that meets one.

Honesty numbers, exe B and exe P, no setoption. The lines are in report_numbers.txt, which is the output of make_report_numbers.py.

```
bench 11 expect 312866 B 312866 P 312866
bench 13 expect 862329 B 862329 P 862329
bench 16 expect 3024920 B 3024920 P 3024920
perft 5 expect 4865609 B 4865609 P 4865609
```

Exe B with S14 also reproduced the known sums: O depth 12 = 9500069, first three 41311 / 24872 / 28574, G depth 12 = 18466239.

Step table, pasted from make_report_numbers.py:

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 065 idea 15
2 honesty B | done | HONESTY_B.txt | four known node counts
3a read | done | decisions.txt | S15 not already in the engine
3b predict | done | prediction.txt | O sum 9500069 elo 0
3c patch | done | idea.patch.txt apply_check_mine.txt | apply check exit 0
3d proofs | done | report_numbers.txt | off 0 differ, on 0 of 200, asan clean
3e match | done | match_s15_fastchess.txt | 1106 games
4 partner | done | partner015_match_fastchess.txt | 015 CONFIRMS
5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P. Numbers from the same script.

(1) Honesty with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.
(2) S14 and IdeaS15 false: O depth 12 differs in 0 of 200 from exe B (both sums 9500069). G depth 12 differs in 0 of 353 (both sums 18466239).
(3) S14 and IdeaS15 true: O depth 12 differs in 0 of 200 (both sums 9500069). A counter build of this patch reported s15true 0 and s15zero 0 on those 200 searches, then s15true 60 and s15zero 19 on G line 22. The code does not run inside the opening searches. It does run: G depth 12 with the switch on differs in 59 of 353 (sum 18365205 against exe B 18466239).
(4) uci lists `option name IdeaS15 type check default false` and `option name IdeaS15_MinPieces type spin default 8 min 2 max 32` in honesty_p_id.txt.
(5) AddressSanitizer build: `nm -C` count of __asan_ is 35. First 100 of G at depth 10 with the switch on: 0 sanitizer lines (asan_G100_d10.txt). The same harness on a scratch copy with one heap read past the end, on fen `8/8/8/8/8/8/8/K6k w - - 0 1`, reports `ERROR: AddressSanitizer: heap-buffer-overflow` (asan_scratch_special.txt).

The patch applies to a clean checkout of 6b98f2170: apply_check_mine.txt says MINE:0.

Match, IdeaS15 true against false, both S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours. Pasted from match_s15_fastchess.txt:

```
Elo: 1.26 +/- 5.78, nElo: 4.46 +/- 20.48
Games: 1106, Wins: 341, Losses: 337, Draws: 428, Points: 555.0 (50.18 %)
```

The whole output is match_s15_fastchess.txt and the games are match_s15.pgn (1106 events). The point estimate is inside the prediction's -20 to +20 band. It is not below -20, so the code was not re-opened for a mistake.

Partner. Seats for idea 15 are 015, 065, 115. At minute 75, 115 had no branch, so the partner is 015. Their patch is IdeaS6 (idle-piece reduction), which their decisions.txt states. Their seat line still says idea 15. I applied their patch with git apply --check on the clean base (apply_check_partner.txt says PARTNER:0), built it, and measured with harness_go.py.

Their honesty numbers match: 312866, 862329, 3024920, 4865609. Switch false matches exe B on O depth 12, 0 of 200. Switch true matches their own o_p_on_d12.nodes on all 200 rows (sum 10340773) and differs from exe B in 156 positions, which is the count they published. A 600-game match of their switch on my 300 R openings, both colours, finished at Elo 2.90 +/- 9.15 (partner015_match_fastchess.txt, 600 events in the pgn). Verdict: CONFIRMS. The proofs they published are what this rebuild measured. The patch itself is idea 6, not idea 15.

suspicions, not proven

Setting the reduction to 0 still enters the late-move block, so that search is a cut node at a zero window. I did not prove this is the same as never reducing the move. G's node changes show that the assignment does change searches.

what I did NOT do

I did not play a second match of my own patch on R. A partner branch existed, so that fallback was not the step. I did not change pruning, extensions, or the evaluation. I did not open a pull request. I did not wait on seat 115 after minute 75, because it had no branch then.

what I am NOT sure about

I am not sure a one-move rook file change should sometimes fail the tempo test. With the rule I wrote, the pawn's next step always costs 1 or 2, so the test never rejects that move. I am not sure why seat 015 built idea 6. Their decisions.txt says they did it on purpose. The numbers they published are the numbers I measured.

times: see stamps.txt

The block below is the full pasted output of make_report_numbers.py (report_numbers.txt).

```
honesty
bench 11 expect 312866 B 312866 P 312866
bench 13 expect 862329 B 862329 P 862329
bench 16 expect 3024920 B 3024920 P 3024920
perft 5 expect 4865609 B 4865609 P 4865609
partner honesty 312866 862329 3024920 4865609
O B sum 9500069 first3 [41311, 24872, 28574] n 200
G B sum 18466239 n 353
O off differ 0 sums 9500069 9500069
G off differ 0 sums 18466239 18466239
O on differ 0 of 200 sums 9500069 9500069
G on differ 59 of 353 sums 18365205 18466239
fire
O_200_depth12_last info string s15true 0 s15zero 0
G_line22_after_O info string s15true 60 s15zero 19
asan_nm 35
asan_clean_errors 0
asan_scratch_has_heap True
apply_mine MINE:0
apply_partner PARTNER:0
partner off differ 0 sums 9500069 9500069
partner on vs claimed differ 0 sums 10340773 10340773
partner on vs B differ 156
MATCH
Results of s15on vs s15off (20000 nodes, 1t, 16MB, match_OG.epd):
Elo: 1.26 +/- 5.78, nElo: 4.46 +/- 20.48
LOS: 66.51 %, DrawRatio: 85.71 %, PairsRatio: 1.08
Games: 1106, Wins: 341, Losses: 337, Draws: 428, Points: 555.0 (50.18 %)
Ptnml(0-2): [1, 37, 474, 39, 2], WL/DD Ratio: 1.69
--------------------------------------------------
Finished match
Total Time: 00:06:38 (hours:minutes:seconds)
PARTNER_MATCH
Results of p015on vs p015off (20000 nodes, 1t, 16MB, set_R.fen):
Elo: 2.90 +/- 9.15, nElo: 8.80 +/- 27.80
LOS: 73.26 %, DrawRatio: 87.33 %, PairsRatio: 1.00
Games: 600, Wins: 282, Losses: 277, Draws: 41, Points: 302.5 (50.42 %)
Ptnml(0-2): [2, 17, 262, 12, 7], WL/DD Ratio: 42.67
--------------------------------------------------
Finished match
Total Time: 00:02:38 (hours:minutes:seconds)
partner pgn events 600
own pgn events 1106
RESULT
seat=065 idea=15 id=S15 option=IdeaS15 exists=no applies=yes off_identical=yes on_differs=0 of 200 sanitizer=clean elo=1.26 err=5.78 games=1106 partner=015 partner_verdict=CONFIRMS
STEP_TABLE
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 065 idea 15
2 honesty B | done | HONESTY_B.txt | four known node counts
3a read | done | decisions.txt | S15 not already in the engine
3b predict | done | prediction.txt | O sum 9500069 elo 0
3c patch | done | idea.patch.txt apply_check_mine.txt | apply check exit 0
3d proofs | done | report_numbers.txt | off 0 differ, on 0 of 200, asan clean
3e match | done | match_s15_fastchess.txt | 1106 games
4 partner | done | partner015_match_fastchess.txt | 015 CONFIRMS
5 report | done | REPORT.md RESULT.txt | this file
```

git status --short
```
 M forge-combo29/grok/065/harness_go.py
 M forge-combo29/grok/065/stamps.txt
?? config.json
?? forge-combo29/grok/065/REPORT.md
?? forge-combo29/grok/065/RESULT.txt
?? forge-combo29/grok/065/apply_check_mine.txt
?? forge-combo29/grok/065/apply_check_partner.txt
?? forge-combo29/grok/065/make_report_numbers.py
?? forge-combo29/grok/065/partner015_bench11.meta
?? forge-combo29/grok/065/partner015_bench11.txt
?? forge-combo29/grok/065/partner015_bench13.meta
?? forge-combo29/grok/065/partner015_bench13.txt
?? forge-combo29/grok/065/partner015_bench16.meta
?? forge-combo29/grok/065/partner015_bench16.txt
?? forge-combo29/grok/065/partner015_idea.patch.txt
?? forge-combo29/grok/065/partner015_match.pgn
?? forge-combo29/grok/065/partner015_match_fastchess.txt
?? forge-combo29/grok/065/partner015_o_on_claimed.nodes
?? forge-combo29/grok/065/partner015_off_O_d12.meta
?? forge-combo29/grok/065/partner015_off_O_d12.tsv
?? forge-combo29/grok/065/partner015_off_O_d12.txt
?? forge-combo29/grok/065/partner015_on_O_d12.meta
?? forge-combo29/grok/065/partner015_on_O_d12.tsv
?? forge-combo29/grok/065/partner015_on_O_d12.txt
?? forge-combo29/grok/065/partner015_perft5.meta
?? forge-combo29/grok/065/partner015_perft5.txt
?? forge-combo29/grok/065/partner015_uci.txt
?? forge-combo29/grok/065/report_numbers.txt
```

ls -la forge-combo29/grok/065
```
total 9200
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:15 apply_check_mine.txt
-rw-r--r-- 1 ubuntu ubuntu      10 Nov 20 09:15 apply_check_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 08:08 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    7307 Nov 20 08:08 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu  131864 Nov 20 08:08 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:08 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:11 asan_scratch_special.meta
-rw-r--r-- 1 ubuntu ubuntu    9512 Nov 20 08:09 asan_scratch_special.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:09 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     866 Nov 20 08:04 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   26092 Nov 20 08:04 b_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  549713 Nov 20 08:04 b_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:04 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17582 Nov 20 08:04 b_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  308953 Nov 20 08:04 b_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1266 Nov 20 08:10 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    6155 Nov 20 09:11 harness_go.py
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:00 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:00 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:00 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:00 honesty_b_id.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:00 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     360 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:03 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:03 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:03 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 08:03 honesty_p_id.txt
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:03 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    7286 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1117 Nov 20 08:00 make_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    1885 Nov 20 08:10 make_proof_table.py
-rw-r--r-- 1 ubuntu ubuntu    5014 Nov 20 09:16 make_report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu  138196 Nov 20 08:16 match_s15_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 3677833 Nov 20 08:16 match_s15.pgn
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 openings_O.fens
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:11 partner015_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner015_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:11 partner015_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner015_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:11 partner015_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 partner015_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   11272 Nov 20 09:11 partner015_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   72661 Nov 20 09:14 partner015_match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 1582011 Nov 20 09:14 partner015_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     890 Nov 20 09:11 partner015_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17582 Nov 20 09:11 partner015_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309045 Nov 20 09:11 partner015_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     889 Nov 20 09:11 partner015_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17585 Nov 20 09:11 partner015_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  311077 Nov 20 09:11 partner015_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1207 Nov 20 09:11 partner015_o_on_claimed.nodes
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 09:11 partner015_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 partner015_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    5039 Nov 20 09:11 partner015_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     901 Nov 20 08:04 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   26092 Nov 20 08:04 p_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  549879 Nov 20 08:04 p_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     907 Nov 20 08:04 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17582 Nov 20 08:04 p_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309077 Nov 20 08:04 p_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     900 Nov 20 08:05 p_on_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   26090 Nov 20 08:05 p_on_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  549816 Nov 20 08:05 p_on_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     906 Nov 20 08:04 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   17582 Nov 20 08:04 p_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309023 Nov 20 08:04 p_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     632 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    9064 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2427 Nov 20 09:16 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:16 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu     872 Nov 20 08:10 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu     102 Nov 20 08:10 s15_fire_counts.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu   19565 Nov 20 08:08 set_R.fen
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
```
