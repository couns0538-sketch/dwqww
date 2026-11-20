# Seat 030, idea 30, B1

IdeaB1 is a fading board prior on quiet-move ordering. The check option IdeaB1 defaults to false, and the spins are IdeaB1_Scale 96 and IdeaB1_Fade 4. The bonus is how many more enemy men and enemy-king-zone squares the moving piece attacks after the step, times Scale, divided by (1024 + Fade * |main history|), and it is added only to quiet scores.

EXISTS: no. Quiet ordering in the plain engine is history, the threat-history bonus, and +12000 for a direct check. There is no placement prior that shrinks as main history is written.

Honesty, no setoption, from HONESTY_B.txt and HONESTY_P.txt: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on exe B and on exe P.

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 030 idea 30 |
| 2 honesty B | done | HONESTY_B.txt | four numbers match |
| 2 baseline O and G | done | BASELINE_SUMS.txt | O 9500069, G 18466239 |
| 3 prediction | done | prediction.txt | 9050000 and +5, committed before any patched search |
| 3 patch applies | done | apply_check.txt | git apply --check exit 0 |
| 3 proof off | done | cmp_O_off.txt, cmp_G_off.txt | 0 of 200 and 0 of 353 differ |
| 3 proof on | done | cmp_O_on.txt, PATCH_SUMS.txt | 200 of 200 differ, sum 10081213 |
| 3 uci options | done | uci_P.txt | IdeaB1 false, Scale 96, Fade 4 |
| 3 sanitizer | done | asan_G100_d10.txt.runner_meta, asan_poison.txt.runner_meta | clean, and the poison copy reports one sanitizer line |
| 3 match | done | MATCH_RESULT.txt | Elo 8.17 +/- 9.80, 1106 games |
| 4 partner | done | partner_cmp_off.txt, partner_cmp_on.txt, partner_match_R.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Exe P, no setoption. HONESTY_P.txt: bench 11 nodes=312866, bench 13 nodes=862329, bench 16 nodes=3024920, perft 5 nodes=4865609.

Proof (2). S14 and IdeaB1 false. cmp_O_off.txt: compared=200 differ=0 IDENTICAL to exe B. cmp_G_off.txt: compared=353 differ=0 IDENTICAL to exe B. Sums 9500069 and 18466239.

Proof (3). S14 and IdeaB1 true. cmp_O_on.txt: compared=200 differ=200. PATCH_SUMS.txt: O_P_on_d12.txt sum=10081213, first3=[12481, 31753, 31668]. The prediction 9050000 is inside the stated band 7500000 to 12000000.

Proof (4). uci_P.txt lists `option name IdeaB1 type check default false`, `option name IdeaB1_Scale type spin default 96 min 0 max 500`, `option name IdeaB1_Fade type spin default 4 min 0 max 64`.

Proof (5). asan_G100_d10.txt.runner_meta: asan_symbols=35, sanitizer_lines=0, first 100 of G at depth 10, IdeaB1 true, sum 1989201. asan_poison.txt.runner_meta: asan_symbols=35, sanitizer_lines=1. The line is a runtime error on a load past a 4-int heap array in the scratch copy, at the special FEN, through asan_runner.sh.

Match, from match_last.py on match_OG.txt (MATCH_RESULT.txt):

```
Results of IdeaB1on vs IdeaB1off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: 8.17 +/- 9.80, nElo: 17.08 +/- 20.48
LOS: 94.90 %, DrawRatio: 66.00 %, PairsRatio: 1.32
Games: 1106, Wins: 351, Losses: 325, Draws: 430, Points: 566.0 (51.18 %)
Ptnml(0-2): [11, 70, 365, 96, 11], WL/DD Ratio: 1.77
Finished match
Total Time: 00:06:42 (hours:minutes:seconds)
finished_games=1106
```

The point +8.17 is inside the prediction band -30 to +45. The interval crosses 0. It is not below -20.

Partner 080. Verdict: CONFIRMS. partner_apply_check.txt: apply_check_exit=0. partner_HONESTY.txt: the four honesty numbers match, sha256 4b77e3d5d647b7080b40d907719594e849bfb5e119e9d172d73ffc4a16178c27, the same sha256 their HONESTY_P.txt names. partner_cmp_off.txt: differ=0 IDENTICAL to exe B O depth 12. partner_cmp_on.txt: differ=0 IDENTICAL to their committed O_P_on_d12.txt (sum 9748678, 200 of 200 differ from exe B, which is what their nodes_table.txt says). Partner match on my R.epd, 600 games, from match_last.py: Elo -1.74 +/- 8.72, Games 600, Wins 272, Losses 275, Draws 53. Their own OG match claim, which I did not replay, was Elo -1.57 +/- 11.24 over 1106 games.

Suspicions, not proven. The pressure delta is a cheap stand-in. A match gain would not show that a trained ordering head works. All 200 positions changing means the cold prior is large, because history starts at 0. Draws by the fifty-move rule, threefold repetition, and insufficient material in the match are legal results.

What I did NOT do. I did not train an ordering head. I did not replay the partner's 1106-game match or the partner's sanitizer. I did not wait until minute 75 to open their patch: the review started at 08:47Z, after step 3 was pushed, because their branch already had idea.patch.txt. The minute-60 handoff fetch (08:47Z, commit 8c5536863) contains no FABLE_TO_grok file.

What I am NOT sure about. Whether the owner's book, left at its default, would hide the ordering change for the first moves. Whether IdeaB1_Scale 96 is too large for a prior that is supposed to fade behind history. The Elo interval includes negative values, so the sign of the 8.17 is not settled.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/030/stamps.txt
?? config.json
?? forge-combo29/grok/030/REPORT.md
?? forge-combo29/grok/030/RESULT.txt
?? forge-combo29/grok/030/match_nohup.log
?? forge-combo29/grok/030/partner_HONESTY.txt
?? forge-combo29/grok/030/partner_O_off.rows
?? forge-combo29/grok/030/partner_O_off.txt
?? forge-combo29/grok/030/partner_O_off.txt.meta
?? forge-combo29/grok/030/partner_O_on.rows
?? forge-combo29/grok/030/partner_O_on.txt
?? forge-combo29/grok/030/partner_O_on.txt.meta
?? forge-combo29/grok/030/partner_apply.txt
?? forge-combo29/grok/030/partner_apply_check.txt
?? forge-combo29/grok/030/partner_claimed_O_on.txt
?? forge-combo29/grok/030/partner_claimed_nodes.txt
?? forge-combo29/grok/030/partner_cmp_off.txt
?? forge-combo29/grok/030/partner_cmp_on.txt
?? forge-combo29/grok/030/partner_cmp_on_vs_b.txt
?? forge-combo29/grok/030/partner_fetch.log
?? forge-combo29/grok/030/partner_files.txt
?? forge-combo29/grok/030/partner_honesty_bench11.meta
?? forge-combo29/grok/030/partner_honesty_bench11.txt
?? forge-combo29/grok/030/partner_honesty_bench13.meta
?? forge-combo29/grok/030/partner_honesty_bench13.txt
?? forge-combo29/grok/030/partner_honesty_bench16.meta
?? forge-combo29/grok/030/partner_honesty_bench16.txt
?? forge-combo29/grok/030/partner_honesty_perft5.meta
?? forge-combo29/grok/030/partner_honesty_perft5.txt
?? forge-combo29/grok/030/partner_idea.patch.txt
?? forge-combo29/grok/030/partner_match_R.pgn
?? forge-combo29/grok/030/partner_match_R.txt
?? forge-combo29/grok/030/partner_status.txt
?? forge-combo29/grok/030/partner_step.sh
?? forge-combo29/grok/030/partner_sums.txt
?? forge-combo29/grok/030/run_partner_match.sh
```

## ls -la

```
total 11344
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:52 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  233756 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_G100_d10.txt.asan_count
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:06 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     890 Nov 20 08:06 asan_G100_d10.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:06 asan_G100_d10.txt.runner_meta
-rw-r--r-- 1 ubuntu ubuntu    7297 Nov 20 08:06 asan_poison.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_poison.txt.asan_count
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 asan_poison.txt.rows
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:06 asan_poison.txt.runner_meta
-rwxr-xr-x 1 ubuntu ubuntu    1119 Nov 20 08:05 asan_runner.sh
-rw-r--r-- 1 ubuntu ubuntu     120 Nov 20 08:01 BASELINE_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:03 cmp_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:03 cmp_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     241 Nov 20 08:03 cmp_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1076 Nov 20 08:03 cmp_raw.py
-rw-r--r-- 1 ubuntu ubuntu    4985 Nov 20 08:00 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    1427 Nov 20 08:07 design.txt
-rw-r--r-- 1 ubuntu ubuntu    3449 Nov 20 08:01 G_B_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  892530 Nov 20 08:01 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     804 Nov 20 08:01 G_B_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    3449 Nov 20 08:02 G_P_off_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  912159 Nov 20 08:02 G_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 08:02 G_P_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 07:58 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 07:58 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 07:58 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:58 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:58 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:58 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3284 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     256 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5155 Nov 20 08:02 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:02 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5155 Nov 20 08:02 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:02 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5157 Nov 20 08:02 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:02 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5368 Nov 20 08:02 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     256 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    9073 Nov 20 07:59 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1184 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     515 Nov 20 08:16 match_last.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 match_nohup.log
-rw-r--r-- 1 ubuntu ubuntu 4620442 Nov 20 08:14 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu  134801 Nov 20 08:14 match_OG.txt
-rw-r--r-- 1 ubuntu ubuntu     425 Nov 20 08:16 MATCH_RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1912 Nov 20 08:00 O_B_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  502660 Nov 20 08:00 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     803 Nov 20 08:00 O_B_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1912 Nov 20 08:02 O_P_off_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  513883 Nov 20 08:02 O_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:02 O_P_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1915 Nov 20 08:02 O_P_on_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  514575 Nov 20 08:02 O_P_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:02 O_P_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 08:47 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:47 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     661 Nov 20 08:47 partner_claimed_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  283146 Nov 20 08:47 partner_claimed_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:48 partner_cmp_off.txt
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:48 partner_cmp_on.txt
-rw-r--r-- 1 ubuntu ubuntu     241 Nov 20 08:48 partner_cmp_on_vs_b.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 08:47 partner_fetch.log
-rw-r--r-- 1 ubuntu ubuntu    2137 Nov 20 08:47 partner_files.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:47 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5284 Nov 20 08:47 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:47 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5284 Nov 20 08:47 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 08:47 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5286 Nov 20 08:47 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:47 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5497 Nov 20 08:47 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:47 partner_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   15766 Nov 20 08:47 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 1383863 Nov 20 08:51 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   69842 Nov 20 08:51 partner_match_R.txt
-rw-r--r-- 1 ubuntu ubuntu    1912 Nov 20 08:48 partner_O_off.rows
-rw-r--r-- 1 ubuntu ubuntu  514068 Nov 20 08:48 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:48 partner_O_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1913 Nov 20 08:48 partner_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu  514893 Nov 20 08:48 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:48 partner_O_on.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:47 partner_status.txt
-rwxr-xr-x 1 ubuntu ubuntu    1788 Nov 20 08:17 partner_step.sh
-rw-r--r-- 1 ubuntu ubuntu     129 Nov 20 08:48 partner_sums.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:03 PATCH_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu     352 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   18146 Nov 20 08:06 R.epd
-rw-r--r-- 1 ubuntu ubuntu    5116 Nov 20 08:52 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:52 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1097 Nov 20 08:07 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1087 Nov 20 08:48 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:52 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     803 Nov 20 08:01 sum_raw.py
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:07 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5094 Nov 20 08:03 uci_P.txt
```
