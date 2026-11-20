Idea S26 keeps a second continuation history, written when a quiet cutoff is past depth 7 and when the same quiet fails high on a reduced search and again on the re-search.
At remaining depth 6 or more, quiet ordering reads that confirmed table. The check option is IdeaS26, default false. The spins are IdeaS26_Floor default 7 and IdeaS26_OrderDepth default 6.
The ordinary continuation table is still updated on every quiet cutoff, and history pruning still reads it.

EXISTS: no. One continuation table is updated on every quiet cutoff in `Worker::update_continuation` (`forge-combo29/src/search.cpp`). There is no confirmed table in the plain engine.

Honesty, no setoption, exe B (`HONESTY_B.txt`) and exe P (`HONESTY_P.txt`): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Each line matched.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 021, idea 21 |
| 2 honesty B | done | HONESTY_B.txt | four known node counts |
| 2 O and G depth 12 | done | o_b.tsv, g_b.tsv | sums 9500069 and 18466239 |
| 3 prediction | done | prediction.txt | sum 12500000, Elo -12, committed before measuring P |
| 3 patch | done | idea.patch.txt | git apply --check passed on a fresh base |
| 3 proof off | done | compare_o_off.txt, compare_g_off.txt | 0 of 200 and 0 of 353 node differences |
| 3 proof on | done | compare_o_on.txt, o_on.tsv | 200 of 200 differ, sum 9485661 |
| 3 uci options | done | uci_p.out | IdeaS26 false, Floor 7, OrderDepth 6 |
| 3 sanitizer | done | g_asan100.meta, g_asan100.out, scratch_asan.out | nm __asan_ count 35, 0 sanitizer lines, scratch heap-buffer-overflow |
| 3 match | done | match.out, match.pgn | Elo 0.63 +/- 10.16, 1106 games |
| 4 partner | done | compare_p071_on.txt, partner_match.out | CONFIRMS, 600 R games |

Proof (1). Exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (`HONESTY_P.txt`).

Proof (2). S14 and IdeaS26 false, Floor 7, OrderDepth 6. O depth 12: node_diff 0 of 200, sum 9500069 (`compare_o_off.txt`). G depth 12: node_diff 0 of 353, sum 18466239 (`compare_g_off.txt`). Best moves matched exe B as well.

Proof (3). S14 and IdeaS26 true. O depth 12 sum 9485661. node_diff 200 of 200 against exe B, move_diff 47 of 200 (`compare_o_on.txt`).

Proof (4). `uci` lists `option name IdeaS26 type check default false`, `option name IdeaS26_Floor type spin default 7 min 0 max 63`, `option name IdeaS26_OrderDepth type spin default 6 min 0 max 63` (`uci_p.out`).

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS26 true, first 100 of G at depth 10: sum 1958751, exit 0, `nm_asan_count=35` (`g_asan100.meta`). A count of `ERROR: AddressSanitizer` and `runtime error:` lines in `g_asan100.out` is 0. The same runner on a scratch copy that reads `heap[8]` of a 4-int heap array when the FEN is `4k3/8/8/8/8/8/8/4K3 w - - 0 1` reports `ERROR: AddressSanitizer: heap-buffer-overflow` (`scratch_asan.out`). That scratch copy's meta also has `nm_asan_count=35`.

Match. Exe P with the switch true against exe P with the switch false, S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G, both colours. `match.out` final block: Elo 0.63 +/- 10.16, 1106 games, 335 wins, 333 losses, 438 draws. `match.pgn` has 1106 Result tags. The interval includes 0, so I did not open the code for a second look. Prediction said sum 12500000 (wrong below 7000000 or above 20000000) and Elo -12 (wrong above +30 or below -80). Measured sum 9485661 and Elo 0.63 sit inside those ranges. The point guesses were high on nodes and low on Elo.

Partner 071, the next seat with idea 21. `git apply --check` of `idea.patch.txt` on a fresh base printed nothing and exited 0 (rechecked on `/tmp/applycheck`). Their build's honesty matches the four known counts (`HONESTY_P071.txt`). Switch false, their Floor 6 and HighDepth 8: O node_diff 0 of 200 against exe B (`compare_p071_off.txt`), G node_diff 0 of 353 (`compare_p071_g_off.txt`). Switch true: O sum 9568497, node_diff 0 of 200 against their `p_on_o_d12.rows` (`compare_p071_on.txt`), and node_diff 200 of 200 against exe B (`compare_p071_on_vs_b.txt`). That is the row count and the sum they wrote in `PROOF_ROWS.txt`. My 300 R openings, both colours, their switch: Elo -0.58 +/- 8.26, 600 games (`partner_match.out`). Verdict: CONFIRMS.

suspicions, not proven. Cutoffs past the floor copy the same bonus into the confirmed table that the shallow table already received, so the two histories can stay close. That would fit a match inside the error bar. I did not run a colder write rule against this one.

what I did NOT do. I did not replay seat 071's 1106-game O+G match. I did not measure my switch on set G at depth 12. I did not build the quiet-ordering path that is compiled out when FORGE_SEARCH_SPEED2 is on. The handoff branch had no `FABLE_TO_grok_<N>.md` at STEP 1 or at the second fetch (08:45 UTC).

what I am NOT sure about. Floor 7 and order depth 6 are choices, and the 1106-game error bar includes both a small gain and a small loss. I am not sure a different floor would move the Elo. The R games are random positions and drew 87 percent of the time, so that Elo is a weak strength signal.

times: see stamps.txt

`git apply --check` for `idea.patch.txt` was run on a fresh worktree of 6b98f2170a3210e71beed04bbd2553972c253ed7 and exited 0.

```
$ git status --short
 M forge-combo29/grok/021/stamps.txt
?? config.json
?? forge-combo29/grok/021/HONESTY_P071.txt
?? forge-combo29/grok/021/HONESTY_P071_bench_11.meta
?? forge-combo29/grok/021/HONESTY_P071_bench_11.out
?? forge-combo29/grok/021/HONESTY_P071_bench_13.meta
?? forge-combo29/grok/021/HONESTY_P071_bench_13.out
?? forge-combo29/grok/021/HONESTY_P071_bench_16.meta
?? forge-combo29/grok/021/HONESTY_P071_bench_16.out
?? forge-combo29/grok/021/HONESTY_P071_go_perft_5.meta
?? forge-combo29/grok/021/HONESTY_P071_go_perft_5.out
?? forge-combo29/grok/021/REPORT.md
?? forge-combo29/grok/021/RESULT.txt
?? forge-combo29/grok/021/compare_p071_g_off.txt
?? forge-combo29/grok/021/compare_p071_off.txt
?? forge-combo29/grok/021/compare_p071_on.txt
?? forge-combo29/grok/021/compare_p071_on_vs_b.txt
?? forge-combo29/grok/021/compare_partner.py
?? forge-combo29/grok/021/p071_g_off.meta
?? forge-combo29/grok/021/p071_g_off.out
?? forge-combo29/grok/021/p071_g_off.tsv
?? forge-combo29/grok/021/p071_off.meta
?? forge-combo29/grok/021/p071_off.out
?? forge-combo29/grok/021/p071_off.tsv
?? forge-combo29/grok/021/p071_on.meta
?? forge-combo29/grok/021/p071_on.out
?? forge-combo29/grok/021/p071_on.tsv
?? forge-combo29/grok/021/partner071_o_on.rows
?? forge-combo29/grok/021/partner_match.err
?? forge-combo29/grok/021/partner_match.out
?? forge-combo29/grok/021/partner_match.pgn
?? forge-combo29/grok/021/partner_match.sh

$ ls -la forge-combo29/grok/021
total 10124
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:52 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:08 compare_g_off.txt
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 08:08 compare_o_off.txt
-rw-r--r-- 1 ubuntu ubuntu      74 Nov 20 08:08 compare_o_on.txt
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 08:47 compare_p071_g_off.txt
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 08:47 compare_p071_off.txt
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:47 compare_p071_on.txt
-rw-r--r-- 1 ubuntu ubuntu      74 Nov 20 08:47 compare_p071_on_vs_b.txt
-rw-r--r-- 1 ubuntu ubuntu     985 Nov 20 08:47 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:08 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    7201 Nov 20 08:05 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu    1580 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu     901 Nov 20 08:09 g_asan100.meta
-rw-r--r-- 1 ubuntu ubuntu  119840 Nov 20 08:09 g_asan100.out
-rw-r--r-- 1 ubuntu ubuntu    1372 Nov 20 08:09 g_asan100.tsv
-rw-r--r-- 1 ubuntu ubuntu     793 Nov 20 08:03 g_b.meta
-rw-r--r-- 1 ubuntu ubuntu  510892 Nov 20 08:03 g_b.out
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:03 g_b.tsv
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:06 g_off.meta
-rw-r--r-- 1 ubuntu ubuntu  510990 Nov 20 08:06 g_off.out
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:06 g_off.tsv
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:00 honesty_b_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench_11.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:00 honesty_b_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:00 honesty_b_bench_13.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:00 honesty_b_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:00 honesty_b_bench_16.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:00 honesty_b_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:00 honesty_b_go_perft_5.out
-rw-r--r-- 1 ubuntu ubuntu    3723 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    3177 Nov 20 08:06 honesty_exe.py
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:46 HONESTY_P071_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:46 HONESTY_P071_bench_11.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:46 HONESTY_P071_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:46 HONESTY_P071_bench_13.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:47 HONESTY_P071_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 08:47 HONESTY_P071_bench_16.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:47 HONESTY_P071_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 08:47 HONESTY_P071_go_perft_5.out
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:47 HONESTY_P071.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:06 HONESTY_P_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu    5162 Nov 20 08:06 HONESTY_P_bench_11.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:06 HONESTY_P_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu    5162 Nov 20 08:06 HONESTY_P_bench_13.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:06 HONESTY_P_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu    5164 Nov 20 08:06 HONESTY_P_bench_16.out
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:06 HONESTY_P_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu    5375 Nov 20 08:06 HONESTY_P_go_perft_5.out
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   18112 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1433 Nov 20 08:10 make_r.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 match.err
-rw-r--r-- 1 ubuntu ubuntu  124570 Nov 20 08:15 match.out
-rw-r--r-- 1 ubuntu ubuntu 4678525 Nov 20 08:15 match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1338 Nov 20 08:08 match.sh
-rw-r--r-- 1 ubuntu ubuntu     793 Nov 20 08:03 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu  283699 Nov 20 08:03 o_b.out
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:03 o_b.tsv
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 og.epd
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:06 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu  283742 Nov 20 08:06 o_off.out
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:06 o_off.tsv
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 08:06 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu  283952 Nov 20 08:06 o_on.out
-rw-r--r-- 1 ubuntu ubuntu    2892 Nov 20 08:06 o_on.tsv
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 08:47 p071_g_off.meta
-rw-r--r-- 1 ubuntu ubuntu  511625 Nov 20 08:47 p071_g_off.out
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:47 p071_g_off.tsv
-rw-r--r-- 1 ubuntu ubuntu     922 Nov 20 08:47 p071_off.meta
-rw-r--r-- 1 ubuntu ubuntu  284142 Nov 20 08:47 p071_off.out
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:47 p071_off.tsv
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:47 p071_on.meta
-rw-r--r-- 1 ubuntu ubuntu  284175 Nov 20 08:47 p071_on.out
-rw-r--r-- 1 ubuntu ubuntu    2892 Nov 20 08:47 p071_on.tsv
-rw-r--r-- 1 ubuntu ubuntu   14771 Nov 20 08:46 partner071_o_on.rows
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:47 partner_match.err
-rw-r--r-- 1 ubuntu ubuntu   63303 Nov 20 08:50 partner_match.out
-rw-r--r-- 1 ubuntu ubuntu 1892964 Nov 20 08:50 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1243 Nov 20 08:47 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     344 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19179 Nov 20 08:10 r300.fen
-rw-r--r-- 1 ubuntu ubuntu    6920 Nov 20 08:52 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:52 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     905 Nov 20 08:10 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu    9283 Nov 20 08:10 scratch_asan.out
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 smoke.err
-rw-r--r-- 1 ubuntu ubuntu     601 Nov 20 08:08 smoke.out
-rw-r--r-- 1 ubuntu ubuntu   14791 Nov 20 08:08 smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 08:52 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1765 Nov 20 08:06 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:06 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:06 uci_p.out
```
