# Seat 080, idea 30, B1

IdeaB1 adds a board prior only inside the quiet-move group, then fades it as that move's history grows. The prior is the live net's first-order change for the move, from 16 hidden units of the current accumulator, not a trained ordering head and not a piece-square table. With the switch off the bonus is never added.

EXISTS: no. Quiet order in the plain engine is history, killers, and a check bonus (`forge-combo29/src/search.cpp` quiet scorer). Nothing there fades a placement prior.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Exe B, S14, depth 12: O sum 9500069 (first 41311 24872 28574), G sum 18466239.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 080, idea 30 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 3a patch | done | idea.patch.txt, apply_check.txt, DECISION.txt | `git apply --check` exit 0 |
| 3b prediction | done | prediction.txt | O-on 9050000, Elo +5, pushed before measuring |
| 3 proofs | done | nodes_table.txt, HONESTY_P.txt, asan_G100_d10.txt.meta | off identical, on 200 differ, sanitizer clean |
| 3e match | done | match_final.txt | 1106 games, Elo -1.57 +/- 11.24 |
| 4 partner 030 | done | partner_cmp_off_data.txt, partner_cmp_on_data.txt, partner_match_final.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). Exe P, no setoption: HONESTY_P.txt, same four counts as exe B.

Proof (2). S14, IdeaB1 false. O depth 12: 0 of 200 differ from exe B, sum 9500069. G depth 12: 0 of 353 differ, sum 18466239. nodes_table.txt.

Proof (3). S14, IdeaB1 true. O depth 12 sum 9748678, 200 of 200 differ from exe B. First three: 17841 25977 43905. nodes_table.txt.

Proof (4). `uci` lists `option name IdeaB1 type check default false`, `IdeaB1_Lanes` default 16, `IdeaB1_Fade` default 1024, `IdeaB1_Scale` default 32, `IdeaB1_Cap` default 4000. honesty_p_bench11.txt.

Proof (5). ASan+UBSan exe, `nm -C` count of `__asan_` is 35 (asan_G100_d10.txt.meta). First 100 of G, depth 10, IdeaB1 true: 100 bestmoves, 0 sanitizer lines (asan_G100_d10.txt). The same runner on a scratch build that reads `scratch[8]` of a `new int[4]` for FEN `8/8/8/8/8/8/8/K6k w - - 0 1` prints `ERROR: AddressSanitizer: heap-buffer-overflow` (asan_trigger.txt).

Match. Exe P IdeaB1 true vs false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games. match_final.txt: Elo -1.57 +/- 11.24, 346 wins, 351 losses, 409 draws. The interval is not entirely below 0, and the point is not below -20, so the code was not reopened for a bug hunt. Prediction 9050000 (wrong outside 6500000–13000000) and Elo +5 (wrong outside -30–+50): both measured numbers sit inside those ranges.

Partner 030, same idea. partner_build_notes.txt: apply --check ok, apply ok, honesty bench/perft the known counts. Switch false vs this seat's O_B_d12.txt: differ 0 of 200, sum 9500069 (partner_cmp_off_data.txt). Switch true vs their O_P_on_d12.rows, ignoring the final `SUM` line: differ 0 of 200, sum 10081213 (partner_cmp_on_data.txt), the sum they wrote in PATCH_SUMS.txt. Their R match on this seat's 300 R openings, both colours, 600 games: Elo 4.05 +/- 8.86 (partner_match_final.txt). Verdict: CONFIRMS.

Suspicions, not proven. A 16-unit gradient can be near zero when those units are saturated, so some quiets may get no prior even with the switch on. The match being about equal does not show the prior is useless at longer time controls or with the owner's net. Seat 030's prior is a different formula (their scale 96, fade 4) and their OG match was +8.17 +/- 9.80; that is their claim, reproduced here only as node rows, not as that match.

What I did NOT do. No trained ordering head. No spin sweep. No re-run of seat 030's sanitizer or their 1106-game OG match. No game on the owner's net. The second channel fetch at 2026-11-20T08:55:35Z found no FABLE_TO_grok file, same as STEP 1.

What I am NOT sure about. Whether lanes 16, fade 1024, scale 32 and cap 4000 are near a strong setting. The +/- 11 Elo bar on 1106 games does not separate a small gain from a small loss. I am not sure a saturated-unit prior of zero is rare.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/080/run_depth_set.py
 M forge-combo29/grok/080/stamps.txt
?? forge-combo29/grok/080/REPORT.md
?? forge-combo29/grok/080/RESULT.txt
?? forge-combo29/grok/080/apply_check.txt
?? forge-combo29/grok/080/compare_rows.py
?? forge-combo29/grok/080/config.json
?? forge-combo29/grok/080/match_final.txt
?? forge-combo29/grok/080/partner.patch.txt
?? forge-combo29/grok/080/partner_O_off_d12.txt
?? forge-combo29/grok/080/partner_O_off_d12.txt.meta
?? forge-combo29/grok/080/partner_O_on_d12.txt
?? forge-combo29/grok/080/partner_O_on_d12.txt.meta
?? forge-combo29/grok/080/partner_build_notes.txt
?? forge-combo29/grok/080/partner_cmp_off.txt
?? forge-combo29/grok/080/partner_cmp_off_data.txt
?? forge-combo29/grok/080/partner_cmp_on.txt
?? forge-combo29/grok/080/partner_cmp_on_data.txt
?? forge-combo29/grok/080/partner_files.txt
?? forge-combo29/grok/080/partner_honesty_bench11.txt
?? forge-combo29/grok/080/partner_honesty_bench11.txt.meta
?? forge-combo29/grok/080/partner_honesty_bench13.txt
?? forge-combo29/grok/080/partner_honesty_bench13.txt.meta
?? forge-combo29/grok/080/partner_honesty_bench16.txt
?? forge-combo29/grok/080/partner_honesty_bench16.txt.meta
?? forge-combo29/grok/080/partner_honesty_perft5.txt
?? forge-combo29/grok/080/partner_honesty_perft5.txt.meta
?? forge-combo29/grok/080/partner_honesty_summary.txt
?? forge-combo29/grok/080/partner_match.pgn
?? forge-combo29/grok/080/partner_match.txt
?? forge-combo29/grok/080/partner_match_final.txt
?? forge-combo29/grok/080/partner_off_vs_B.txt
?? forge-combo29/grok/080/partner_on_sum.txt
?? forge-combo29/grok/080/partner_raw/
?? forge-combo29/grok/080/run_honesty_exe.py
?? forge-combo29/grok/080/run_partner.sh
?? forge-combo29/grok/080/run_partner_match.sh
```

## ls -la

```
total 8300
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:17 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  119164 Nov 20 08:14 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     972 Nov 20 08:14 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:14 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:14 asan_trigger.fen
-rw-r--r-- 1 ubuntu ubuntu    9380 Nov 20 08:14 asan_trigger.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:14 asan_trigger.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1654 Nov 20 09:17 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7070 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    1679 Nov 20 08:06 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:13 G100.epd
-rw-r--r-- 1 ubuntu ubuntu  507630 Nov 20 08:09 G_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:09 G_B_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  508106 Nov 20 08:09 G_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 08:09 G_P_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:05 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:05 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 08:05 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:05 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:05 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:05 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     330 Nov 20 08:05 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    5292 Nov 20 08:09 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:09 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5292 Nov 20 08:09 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:09 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5294 Nov 20 08:09 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 08:09 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5505 Nov 20 08:09 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 08:09 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     330 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   15766 Nov 20 08:06 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1451 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  133607 Nov 20 08:24 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu     413 Nov 20 09:17 match_final.txt
-rw-r--r-- 1 ubuntu ubuntu 3622087 Nov 20 08:24 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     661 Nov 20 08:11 nodes_table.txt
-rw-r--r-- 1 ubuntu ubuntu  281848 Nov 20 08:09 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:09 O_B_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:15 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu  282138 Nov 20 08:09 O_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     881 Nov 20 08:09 O_P_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  283146 Nov 20 08:09 O_P_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:09 O_P_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     258 Nov 20 09:17 partner_build_notes.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 09:17 partner_cmp_off_data.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 09:12 partner_cmp_off.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 09:17 partner_cmp_on_data.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 09:12 partner_cmp_on.txt
-rw-r--r-- 1 ubuntu ubuntu    4253 Nov 20 09:11 partner_files.txt
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 09:11 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:11 partner_honesty_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 09:11 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:11 partner_honesty_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 09:11 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:11 partner_honesty_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5376 Nov 20 09:11 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 09:11 partner_honesty_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     326 Nov 20 09:11 partner_honesty_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     399 Nov 20 09:17 partner_match_final.txt
-rw-r--r-- 1 ubuntu ubuntu 1633585 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   67913 Nov 20 09:15 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 09:12 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 09:12 partner_on_sum.txt
-rw-r--r-- 1 ubuntu ubuntu  282239 Nov 20 09:11 partner_O_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 09:11 partner_O_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  283125 Nov 20 09:12 partner_O_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 09:12 partner_O_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    9073 Nov 20 09:11 partner.patch.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:11 partner_raw
-rw-r--r-- 1 ubuntu ubuntu     346 Nov 20 08:07 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   12121 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1354 Nov 20 08:08 report_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19507 Nov 20 08:08 R.fens
-rw-r--r-- 1 ubuntu ubuntu    2740 Nov 20 08:13 run_asan.sh
-rw-r--r-- 1 ubuntu ubuntu    5303 Nov 20 08:11 run_depth_set.py
-rw-r--r-- 1 ubuntu ubuntu    3135 Nov 20 08:05 run_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    2929 Nov 20 08:28 run_honesty_exe.py
-rw-r--r-- 1 ubuntu ubuntu    3174 Nov 20 08:09 run_honesty_p.py
-rwxr-xr-x 1 ubuntu ubuntu    1338 Nov 20 08:11 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1156 Nov 20 09:11 run_partner_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    2004 Nov 20 09:11 run_partner.sh
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     251 Nov 20 09:17 stamps.txt
```
