# Seat 050, idea 50, IdeaK11

IdeaK11 scales the history bonus of a move that fails high, by how far the score beat beta.
The switch is the check option IdeaK11, default false. The spins are IdeaK11_Base 64, IdeaK11_Divisor 160, and IdeaK11_Cap 320.
With the switch on, the bonus is today's bonus times (margin + 64) / 160, the margin capped at 320. A mate cutoff uses 320 as the margin. With the switch off, the old update calls run as they do today.

EXISTS: no. In the plain engine, `forge-combo29/src/search.cpp:2077` adds one to the quiet-cutoff depth when the margin is above 100 centipawns. That is a step of one ply. Captures do not get it. The patch leaves that call unchanged while IdeaK11 is false.

Honesty numbers, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

`git apply --check` of `idea.patch.txt` on the clean base worktree exited 0. See `apply_check.txt`.

The table and the proof lines are the output of `summarize.py`, which reads the raw files:

```
honesty_B 312866 862329 3024920 4865609
honesty_P 312866 862329 3024920 4865609
proof1_match True
proof2_off_O_differ 0
proof2_off_G_differ 0
proof3_on_O_differ 200
proof3_on_line sum 9484082
proof4
option name IdeaK11 type check default false
option name IdeaK11_Base type spin default 64 min 0 max 2000
option name IdeaK11_Divisor type spin default 160 min 1 max 4000
option name IdeaK11_Cap type spin default 320 min 0 max 4000
proof5_nm_asan 35
proof5_clean_sanitizer_lines 0
proof5_bad_heap_overflow True
proof5_bad_nm 35
base_O sum 9500069
base_G sum 18466239

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 050 idea 50 |
| 2 honesty B | done | HONESTY_B.txt | 312866 862329 3024920 4865609 |
| 2 O depth 12 B | done | B_O_d12.rows | sum 9500069 |
| 2 G depth 12 B | done | B_G_d12.rows | sum 18466239 |
| 3 prediction | done | prediction.txt | committed before measuring P |
| 3 patch applies | done | apply_check.txt | APPLY_CHECK_OK apply check exit 0 |
| 3 proof 1 honesty P | done | HONESTY_P.txt | 312866 862329 3024920 4865609 |
| 3 proof 2 switch off | done | compare_off_O.txt compare_off_G.txt | O differ 0; G differ 0 |
| 3 proof 3 switch on | done | compare_on_O.txt | differ 200; sum 9484082 |
| 3 proof 4 uci | done | uci_ideak11.txt | IdeaK11 false; Base 64; Divisor 160; Cap 320 |
| 3 proof 5 sanitizer | done | asan_G100.meta asan_bad_runner.txt | nm 35; clean lines 0; bad overflow True |
| 3 match O+G | done | match_og_result.txt | 1106 games, see that file |
| 4 partner | not done | partner_none.txt | no branch for-fable-and-opus/grok-100 |
| 4 second match R | done | match_r_result.txt | 600 games, see that file |
| 5 report | done | REPORT.md RESULT.txt | this step |
```

Proof (1). No setoption. Exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Same four numbers as exe B.

Proof (2). S14 and IdeaK11 false. O depth 12: 0 of 200 positions differ from exe B, sum 9500069. G depth 12: 0 of 353 differ, sum 18466239.

Proof (3). S14 and IdeaK11 true. O depth 12: 200 of 200 positions differ from exe B. Sum 9484082. First three nodes 13656, 24853, 60485.

Proof (4). The uci listing contains IdeaK11 default false, IdeaK11_Base default 64, IdeaK11_Divisor default 160, IdeaK11_Cap default 320.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build. `nm -C` count of `__asan_` is 35 in `asan_G100.meta`. First 100 of G at depth 10 with the switch true: 0 sanitizer lines, sum 1894807. A scratch copy with one read past the end of a four-int heap array, on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, run through the same `depth_set.py`, printed `ERROR: AddressSanitizer: heap-buffer-overflow`. Its `__asan_` count is 35.

Match, switch on against switch off, S14, Threads 1, Hash 16, 20000 nodes, openings O and G, both colours. Output of `extract_match.py` on `match_og.out`:

```
--------------------------------------------------
Results of K11on vs K11off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -5.97 +/- 10.28, nElo: -11.90 +/- 20.48
LOS: 12.74 %, DrawRatio: 62.03 %, PairsRatio: 0.83
Games: 1106, Wins: 320, Losses: 339, Draws: 447, Points: 543.5 (49.14 %)
Ptnml(0-2): [11, 104, 343, 83, 12], WL/DD Ratio: 1.64
--------------------------------------------------
Finished match
Total Time: 00:06:15 (hours:minutes:seconds)
```

`prediction.txt` said the O depth-12 sum would be 10400000, and that a sum below 9600000 or above 13000000 would show that guess wrong. The sum is 9484082, so that guess is wrong. It said the match Elo would be 8, and that an Elo below -25 or above 40 would show that guess wrong. -5.97 is inside that band. The file was not edited after the push that contained only that file.

Partner verdict: not done. Idea 50 belongs to seats 050 and 100. This seat is 050. At 09:09:56 and again at 09:20:08, `git ls-remote` printed no `for-fable-and-opus/grok-100`. There was no patch to review. The second match is this patch, 300 R openings, both colours, 600 games. Output of `extract_match.py` on `match_r.out`:

```
--------------------------------------------------
Results of K11on vs K11off (20000 nodes, 1t, 16MB, R.fens):
Elo: -15.65 +/- 13.10, nElo: -33.26 +/- 27.80
LOS: 0.95 %, DrawRatio: 71.00 %, PairsRatio: 0.67
Games: 600, Wins: 232, Losses: 259, Draws: 109, Points: 286.5 (47.75 %)
Ptnml(0-2): [13, 39, 213, 32, 3], WL/DD Ratio: 10.21
--------------------------------------------------
Finished match
Total Time: 00:03:43 (hours:minutes:seconds)
```

suspicions, not proven

The on-switch sum is only 15987 nodes under the off-switch sum, while all 200 positions differ. I suspect the scale mostly reorders moves. That is not a strength result.
The R match interval stays under 0 (-15.65 +/- 13.10). The rule that asks for one look at the code asks for a point below -20 as well. I did not open the code again for that. A bare cutoff keeps 64/160 of today's bonus, and I suspect that is harsh. Not shown by anything except the match score.

what I did NOT do

I did not review a partner patch. `partner_review.sh` was not run.
I did not measure IdeaK11_Base, IdeaK11_Divisor, or IdeaK11_Cap at any value except 64, 160, and 320.
I did not play the owner's net. Both matches use the built-in net.
I did not re-run the depth-12 searches after editing the crash text in `depth_set.py`. That edit prints more lines when the engine dies. The searches that finished used the earlier reader.
The handoff branch had no `FABLE_TO_grok_<N>.md` at the step 1 fetch or at the minute-60 fetch (08:54:33Z, commit 8c5536863464d4af8c07b4788883463eb950ab1d).

what I am NOT sure about

The scale is applied to the quiet cutoff and to the capture cutoff. The sentence of the idea says "the cutoff move", and a capture can be that move. I am not sure a capture was meant to be included.
On the quiet path the old +1 depth, used when the margin is above 100, is still the depth that is scaled. I am not sure the scale was meant to replace that step.
The matches send OwnBook false. S14 does not name OwnBook. In this engine the book is for clock and movetime games, and these games were node limited. I am not sure the match runner never also sends a clock.
`make_r.py` played 60 games with seed 5001 to ply 40. None had ended, so the rule that drops games that end dropped zero games. The 300 positions are plies 8, 15, 22, 29, and 36 of those games.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/050/stamps.txt
?? forge-combo29/grok/050/REPORT.md
?? forge-combo29/grok/050/RESULT.txt
?? forge-combo29/grok/050/match_r.out
?? forge-combo29/grok/050/match_r.pgn
?? forge-combo29/grok/050/match_r.sh
?? forge-combo29/grok/050/match_r_result.txt
?? forge-combo29/grok/050/partner_none.txt
?? forge-combo29/grok/050/summarize.py
?? forge-combo29/grok/050/summary.txt
```

ls -la

```
total 8120
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:26 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:01 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:05 asan_bad_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    1896 Nov 20 08:05 asan_bad_runner.txt
-rw-r--r-- 1 ubuntu ubuntu     644 Nov 20 08:04 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    1209 Nov 20 08:04 asan_G100.rows
-rw-r--r-- 1 ubuntu ubuntu  131696 Nov 20 08:04 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:04 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:05 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     611 Nov 20 07:58 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4530 Nov 20 07:58 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  549693 Nov 20 07:58 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     615 Nov 20 07:58 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2533 Nov 20 07:58 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  308901 Nov 20 07:58 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     229 Nov 20 08:02 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:02 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 08:02 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1307 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    5336 Nov 20 08:03 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    1217 Nov 20 08:02 design.txt
-rw-r--r-- 1 ubuntu ubuntu     562 Nov 20 08:14 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:04 G100.epd
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:57 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1151 Nov 20 07:56 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     676 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1151 Nov 20 08:02 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     676 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   10166 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1578 Nov 20 08:03 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  119320 Nov 20 08:12 match_og.out
-rw-r--r-- 1 ubuntu ubuntu 3610586 Nov 20 08:12 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     445 Nov 20 08:14 match_og_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1125 Nov 20 08:06 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu   61313 Nov 20 09:24 match_r.out
-rw-r--r-- 1 ubuntu ubuntu 1934541 Nov 20 09:24 match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu     443 Nov 20 09:25 match_r_result.txt
-rw-r--r-- 1 ubuntu ubuntu    1122 Nov 20 09:20 match_r.sh
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     148 Nov 20 09:25 partner_none.txt
-rw-r--r-- 1 ubuntu ubuntu    2507 Nov 20 08:14 partner_review.sh
-rw-r--r-- 1 ubuntu ubuntu     632 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4530 Nov 20 08:02 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  549948 Nov 20 08:02 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     636 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2533 Nov 20 08:02 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309177 Nov 20 08:02 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     635 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2531 Nov 20 08:02 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309523 Nov 20 08:02 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     523 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   12953 Nov 20 09:27 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:26 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   20107 Nov 20 08:03 R.fens
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:25 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    3903 Nov 20 09:25 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    1757 Nov 20 09:25 summary.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:02 uci_ideak11.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 08:02 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 08:02 uci_p.txt
```
