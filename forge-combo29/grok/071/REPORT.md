Idea S26 keeps the ordinary continuation history and adds a second, confirmed table.
The confirmed table is written on a quiet cutoff deeper than IdeaS26_Floor (default 6), and when a quiet fails high in a reduced search and again on the re-search.
At depth at least IdeaS26_HighDepth (default 8), quiet ordering reads the confirmed table. The check option IdeaS26 defaults to false.

EXISTS: no. I opened `forge-combo29/src/search.cpp`. `Worker::update_continuation` writes one continuation table on every quiet cutoff. There is no confirmed table and no depth gate on that write.

Honesty, no setoption. Exe B (`HONESTY_B.txt`) and exe P (`HONESTY_P.txt`): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Each line matched.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 071, idea 21 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 2 O and G depth 12 on B | done | b_o_d12.run, b_g_d12.run | sums 9500069 and 18466239, first three of O 41311 / 24872 / 28574 |
| 3 prediction | done | prediction.txt | sum 10400000, Elo -8, committed before measuring P, not edited after |
| 3 patch | done | idea.patch.txt | git apply --check on a fresh worktree of 6b98f2170 exited 0 |
| 3 proof off | done | PROOF_ROWS.txt | O 0 of 200 differ, G 0 of 353 differ |
| 3 proof on | done | PROOF_ROWS.txt, p_on_o_d12.run | 200 of 200 differ, sum 9568497 |
| 3 uci options | done | uci_p.txt | IdeaS26 false, Floor 6, HighDepth 8 |
| 3 sanitizer | done | asan_g100.meta, asan_scratch.run | nm __asan_ count 35, 0 sanitizer lines, scratch heap-buffer-overflow |
| 3 match | done | MATCH_RESULT.txt, match_on_vs_off.pgn | Elo -1.26 +/- 10.70, 1106 games |
| 4 partner 021 | done | PARTNER_COMPARE.txt, partner_match.log | CONFIRMS, 600 R games |

Proof (1). Exe P, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (`HONESTY_P.txt`).

Proof (2). S14 and IdeaS26 false. `compare_rows.py` printed (`PROOF_ROWS.txt`): off_O_vs_B diff=0 sum 9500069, off_G_vs_B diff=0 sum 18466239.

Proof (3). S14, IdeaS26 true, Floor 6, HighDepth 8. Same script: on_O_vs_B diff=200 of 200, sum 9568497 against exe B's 9500069. `p_on_o_d12.run` first three nodes 31638 / 23166 / 31150.

Proof (4). `uci_p.txt` lists `option name IdeaS26 type check default false`, `option name IdeaS26_Floor type spin default 6 min 1 max 32`, `option name IdeaS26_HighDepth type spin default 8 min 1 max 64`.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, switch true, first 100 of G at depth 10. `asan_g100.meta` has asan_symbol_count=35 and sanitizer_lines=0. The same runner `asan_run.py` on a scratch copy that reads one past a 4-int heap array when the FEN is `8/8/8/3k4/8/8/8/3K4 w - - 0 1` printed `SUMMARY: AddressSanitizer: heap-buffer-overflow` (`asan_scratch.run`). `asan_scratch.nm` has asan_symbol_count=35.

Match. Exe P with the switch true against exe P with the switch false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. `match_summary.py` printed (`MATCH_RESULT.txt`): Elo -1.26 +/- 10.70, Games 1106, Wins 342, Losses 346, Draws 418. `match_on_vs_off.pgn` has 1106 Result tags. The score is not below -20, and the interval is not entirely below 0, so I did not open the code for a second look. The first fastchess start failed on a missing config file (`match_config_fail.log`); the match above is the rerun.

Prediction (`prediction.txt`, not edited): O sum 10400000, wrong outside 8000000..13000000; Elo -8, wrong if the whole interval is above +20 or below -45. Measured sum 9568497 and interval -1.26 +/- 10.70 sit inside those bounds.

Partner 021, the next idea-21 seat with a branch. `partner_eval.sh` ran `git apply --check` (APPLY_CHECK_OK) and apply on a fresh worktree of 6b98f2170, then built. Honesty matched the four known counts (`PARTNER_HONESTY.txt`). `partner_compare.py` printed (`PARTNER_COMPARE.txt`): switch false, Floor 7, OrderDepth 6, O diff 0 of 200 against exe B, sum 9500069; switch true, O diff 200 of 200 against exe B, sum 9485661, and diff 0 of 200 against their `o_on.tsv` (the sum they wrote in `compare_o_on.txt`). Their 300 of my R openings, both colours, their switch: see `partner_match.log` final block, 600 games. Verdict: CONFIRMS. Every proof they stated that this harness re-ran held.

suspicions, not proven. The confirmed write uses the same history bonus as the shallow write, so the two tables can stay close and a short match can sit inside the error bar. I did not try a smaller confirmed bonus.

what I did NOT do. I did not search set G at depth 12 with IdeaS26 true. I did not build the engine with FORGE_SEARCH_SPEED2 off; the release build defines it, and that is the QuietScorer path the proofs ran. I did not replay the 1106-game match. The handoff branch had no `FABLE_TO_grok_<N>.md` at STEP 1 or at 08:55 UTC.

what I am NOT sure about. Floor 6 and high depth 8 are choices. The 1106-game interval includes a small gain and a small loss, so I am not sure another floor would move the Elo. The partner R match drew much less often than the O+G match; I am not sure how much of that is the random positions.

times: see stamps.txt

`git apply --check` for `idea.patch.txt` was run on `/tmp/apply-check` at base 6b98f2170a3210e71beed04bbd2553972c253ed7 and exited 0.

```
$ git status --short
 M forge-combo29/grok/071/config.json
 M forge-combo29/grok/071/stamps.txt
?? forge-combo29/grok/071/PARTNER_COMPARE.txt
?? forge-combo29/grok/071/PARTNER_HONESTY.txt
?? forge-combo29/grok/071/PARTNER_MATCH_RESULT.txt
?? forge-combo29/grok/071/R300.fens
?? forge-combo29/grok/071/REPORT.md
?? forge-combo29/grok/071/RESULT.txt
?? forge-combo29/grok/071/partner021.patch.txt
?? forge-combo29/grok/071/partner021_o_on.tsv
?? forge-combo29/grok/071/partner_compare.py
?? forge-combo29/grok/071/partner_eval.sh
?? forge-combo29/grok/071/partner_honesty_11.meta
?? forge-combo29/grok/071/partner_honesty_11.txt
?? forge-combo29/grok/071/partner_honesty_13.meta
?? forge-combo29/grok/071/partner_honesty_13.txt
?? forge-combo29/grok/071/partner_honesty_16.meta
?? forge-combo29/grok/071/partner_honesty_16.txt
?? forge-combo29/grok/071/partner_honesty_5.meta
?? forge-combo29/grok/071/partner_honesty_5.txt
?? forge-combo29/grok/071/partner_match.log
?? forge-combo29/grok/071/partner_match.pgn
?? forge-combo29/grok/071/partner_match.sh
?? forge-combo29/grok/071/partner_note.txt
?? forge-combo29/grok/071/partner_off_o.meta
?? forge-combo29/grok/071/partner_off_o.rows
?? forge-combo29/grok/071/partner_off_o.txt
?? forge-combo29/grok/071/partner_on_o.meta
?? forge-combo29/grok/071/partner_on_o.rows
?? forge-combo29/grok/071/partner_on_o.txt
```

```
$ ls -la forge-combo29/grok/071
total 8288
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu    1010 Nov 20 08:10 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu      48 Nov 20 08:10 asan_g100.run
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 asan_g100.stderr
-rw-r--r-- 1 ubuntu ubuntu    5885 Nov 20 08:10 asan_g100.stdout
-rwxr-xr-x 1 ubuntu ubuntu    4369 Nov 20 08:09 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:09 asan_scratch.fen
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:11 asan_scratch.nm
-rw-r--r-- 1 ubuntu ubuntu    2022 Nov 20 08:11 asan_scratch.run
-rw-r--r-- 1 ubuntu ubuntu    5011 Nov 20 08:11 asan_scratch.stderr
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:05 b_g_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21139 Nov 20 08:05 b_g_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:05 b_g_d12.run
-rw-r--r-- 1 ubuntu ubuntu  551665 Nov 20 08:05 b_g_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:05 b_o_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14773 Nov 20 08:05 b_o_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:05 b_o_d12.run
-rw-r--r-- 1 ubuntu ubuntu  310045 Nov 20 08:05 b_o_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1151 Nov 20 08:10 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7295 Nov 20 09:14 config.json
-rw-r--r-- 1 ubuntu ubuntu    1909 Nov 20 08:10 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:09 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:04 G.epd
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:01 honesty_b_run.log
-rwxr-xr-x 1 ubuntu ubuntu     773 Nov 20 08:01 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:05 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:05 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:05 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 honesty_p_run.log
-rwxr-xr-x 1 ubuntu ubuntu    1476 Nov 20 08:05 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   21001 Nov 20 08:08 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:10 match_config_fail.log
-rw-r--r-- 1 ubuntu ubuntu  136760 Nov 20 08:17 match_on_vs_off.log
-rw-r--r-- 1 ubuntu ubuntu 3686680 Nov 20 08:17 match_on_vs_off.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1204 Nov 20 08:10 match_on_vs_off.sh
-rw-r--r-- 1 ubuntu ubuntu     289 Nov 20 08:19 MATCH_RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     608 Nov 20 08:19 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu    4425 Nov 20 08:05 measure.py
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:05 O3.fens
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:04 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:10 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    2892 Nov 20 09:10 partner021_o_on.tsv
-rw-r--r-- 1 ubuntu ubuntu   18112 Nov 20 09:10 partner021.patch.txt
-rwxr-xr-x 1 ubuntu ubuntu    1323 Nov 20 09:11 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     255 Nov 20 09:12 PARTNER_COMPARE.txt
-rwxr-xr-x 1 ubuntu ubuntu    2534 Nov 20 09:11 partner_eval.sh
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:11 partner_honesty_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_honesty_11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:11 partner_honesty_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_honesty_13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:11 partner_honesty_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 partner_honesty_16.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:11 partner_honesty_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 partner_honesty_5.txt
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 09:11 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   62732 Nov 20 09:14 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 1261540 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     280 Nov 20 09:17 PARTNER_MATCH_RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1178 Nov 20 09:11 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 08:48 partner_note.txt
-rw-r--r-- 1 ubuntu ubuntu     986 Nov 20 09:11 partner_off_o.meta
-rw-r--r-- 1 ubuntu ubuntu   14773 Nov 20 09:11 partner_off_o.rows
-rw-r--r-- 1 ubuntu ubuntu  310848 Nov 20 09:11 partner_off_o.txt
-rw-r--r-- 1 ubuntu ubuntu     985 Nov 20 09:11 partner_on_o.meta
-rw-r--r-- 1 ubuntu ubuntu   14771 Nov 20 09:11 partner_on_o.rows
-rw-r--r-- 1 ubuntu ubuntu  310927 Nov 20 09:11 partner_on_o.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:06 p_off_g_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21139 Nov 20 08:06 p_off_g_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:06 p_off_g_d12.run
-rw-r--r-- 1 ubuntu ubuntu  551666 Nov 20 08:06 p_off_g_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:06 p_off_o_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14773 Nov 20 08:06 p_off_o_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:06 p_off_o_d12.run
-rw-r--r-- 1 ubuntu ubuntu  310147 Nov 20 08:06 p_off_o_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     981 Nov 20 08:06 p_on_o_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14771 Nov 20 08:06 p_on_o_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:06 p_on_o_d12.run
-rw-r--r-- 1 ubuntu ubuntu  310269 Nov 20 08:06 p_on_o_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     670 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:10 PROOF_ROWS.txt
-rw-r--r-- 1 ubuntu ubuntu   17265 Nov 20 09:11 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    6838 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   23023 Nov 20 08:04 R.fens
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     866 Nov 20 08:05 smoke_b_o3.meta
-rw-r--r-- 1 ubuntu ubuntu     227 Nov 20 08:05 smoke_b_o3.rows
-rw-r--r-- 1 ubuntu ubuntu   10401 Nov 20 08:05 smoke_b_o3.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     128 Nov 20 08:06 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 08:06 uci_p.txt
-rwxr-xr-x 1 ubuntu ubuntu     877 Nov 20 08:01 write_honesty_b.py
```
