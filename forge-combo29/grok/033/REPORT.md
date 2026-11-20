# Seat 033, idea 33, IdeaA2

IdeaA2, at a non-PV non-root node of depth at least IdeaA2_MinDepth, returns a non-mate fail-high blended toward beta: (score * depth + beta) / (depth + 1).
The check IdeaA2 defaults to false. The only spin is IdeaA2_MinDepth, default 2, range 1 to 64. The blend weights are the formula in the brief.
The transposition table, history, and correction history keep the unblended score. Only the integer returned to the parent changes, and a later hash cutoff blends that stored score once. Quiescence and abort returns are unchanged. `git apply --check` on a fresh base worktree exited 0 (`apply_check.txt`).

EXISTS: no. In the plain engine, `Worker::search` returns `best_score` and the earlier cutoffs (reverse futility, null move, probcut, hash) without blending a fail-high toward beta.

Honesty, no setoption, fresh process each line. Both exe B (`/agent/repos/base/forge-combo29/build/forge`) and exe P (`/agent/repos/work/forge-combo29/build/forge`) matched the known nodes. The block below is the pasted output of `report_tables.py`, which reads the raw files.

```
honesty_B
bench11	312866	312866	true
bench13	862329	862329	true
bench16	3024920	3024920	true
perft5	4865609	4865609	true
honesty_P
bench11	312866	312866	true
bench13	862329	862329	true
bench16	3024920	3024920	true
perft5	4865609	4865609	true
compares
off_O	differ	0	of	200
off_G	differ	0	of	353
on_O	differ	200	of	200
partner_off_O	differ	0	of	200
partner_on_O	differ	200	of	200
B_O_sum	9500069	count	200
B_G_sum	18466239	count	353
on_O_sum	9490331
step_table
step	status	evidence	result
1	done	SEAT.txt stamps.txt	seat 033 idea 33
2	done	HONESTY_B.txt B_O_d12.raw.txt B_G_d12.raw.txt	honesty match and baseline sums above
3	done	idea.patch.txt proof_off_O.txt proof_on_O.txt match.log	option off identical, on differs, match played
4	done	partner_apply_check.txt partner_on_vs_claim.txt partner_match.log	partner 083 CONFIRMS
5	done	REPORT.md RESULT.txt	this report
partner_on_vs_claim	same	200	differ	0	of	200
asan_G100_sanitizer_lines	0
asan_scratch_heap_overflow	2
asan_symbols=35
uci
option name IdeaA2 type check default false
option name IdeaA2_MinDepth type spin default 2 min 1 max 64
```

Plain exe B, S14, Threads 1, Hash 16, depth 12: O sum 9,500,069 (200 positions) and G sum 18,466,239 (353). Those are the known sums.

Proofs on exe P:

(1) Honesty with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Files `honesty_p_bench11.txt`, `honesty_p_bench13.txt`, `honesty_p_bench16.txt`, `honesty_p_perft5.txt`.

(2) S14 and IdeaA2 false: O depth 12 differs in 0 of 200 positions from exe B. G depth 12 differs in 0 of 353. Raw files `P_off_O_d12.raw.txt`, `P_off_G_d12.raw.txt`.

(3) S14 and IdeaA2 true, IdeaA2_MinDepth 2: O depth 12 differs in 200 of 200 positions. Sum of nodes 9,490,331. Raw file `P_on_O_d12.raw.txt`. The code runs.

(4) `uci` lists `option name IdeaA2 type check default false` and `option name IdeaA2_MinDepth type spin default 2 min 1 max 64`. File `uci_options.txt`.

(5) AddressSanitizer + UndefinedBehaviorSanitizer build of the patched tree, switch true, first 100 of G at depth 10: 0 sanitizer lines in `asan_G100.raw.txt`. Its meta has `asan_symbols=35` (`nm -C` count of `__asan_`). A scratch copy with one deliberate heap read past a 4-int array, fired only on the FEN in `scratch.fen`, built the same way and run through `run_depth.py`, reports `AddressSanitizer: heap-buffer-overflow` in `asan_scratch.raw.txt` (the substring is counted twice because the summary repeats it).

Prediction, committed before any patched measurement (`prediction.txt`): O depth-12 sum 10,600,000, wrong outside 7,500,000 to 14,000,000. Measured 9,490,331, inside the band. Test-match Elo +3, wrong outside -35 to +45. Measured -1.88, inside the band.

Match: exe P with IdeaA2 true against exe P with IdeaA2 false. Both S14, Threads 1, Hash 16, 20000 nodes a move. OwnBook was set false because the engine's default is true and a book move is not this search. `-maxmoves 200` stops a game that never ends. Openings `OG553.epd` (O then G, 553 positions), both colours, 1106 games. fastchess from https://github.com/Disservin/fastchess , concurrency 3. Result from `match.log` via `extract_match.py`: Elo -1.88 +/- 10.45, 1106 games, 333 wins, 339 losses, 434 draws, points 550.0 (49.73 %). The point is not below -20 and the interval is not entirely below 0, so I did not open the code looking for a mistake. Whole output: `match.log`, `match.pgn` (1106 events), `config.json`.

Partner: seat 083, the next seat with this idea. Their patch applies (`partner_apply_check.txt`, exit 0). Built from a fresh base. Honesty matches the four known numbers, and the binary sha256 is the one in their `HONESTY_P.txt` (`4f3a4eabd8638f62b24367ace288e958108fccaf05a1e2f36b6e2e47d4ef880a`). Switch false: 0 of 200 O depth-12 rows differ from exe B. Switch true: 200 of 200 differ from exe B, and 0 of 200 differ from their own `O_d12_P_on.tsv`. Their switch, 300 R openings, both colours, 600 games (`partner_match.log`): Elo -10.43 +/- 10.59, 600 games. Verdict: CONFIRMS.

suspicions, not proven

The O sum moved only from 9,500,069 to 9,490,331 while every position changed. Ups and downs cancelled. I do not know whether that near-tie is the idea being small or the blend and the history bonus pulling in opposite directions.
Their patch stores the blended score and does not blend a hash hit a second time. Mine stores the raw score and blends every qualifying return, including a hash hit. Both are off by default and both change the search when on. I do not know which reading Opus will prefer.
fastchess printed DrawRatio 80.67 % on the 600-game match while the same block says Draws: 68. I did not re-derive that percentage.

what I did NOT do

I did not re-play their 1106-game OG match. I did not build their patch under a sanitizer. I did not try IdeaA2_MinDepth at any value other than 2. I did not play either patch with the owner's net. I did not open a pull request.

what I am NOT sure about

Whether a root aspiration window that collapses to one ply of width should be treated as off the principal line. I excluded every root node.
Whether negative fail-highs stay on the correct side of beta after truncating division in every case. The cases I checked by hand do. There is no separate unit test.
The Elo error in RESULT.txt is the fastchess `+/-` figure, not a figure I computed.

times: see stamps.txt

```
step	status	evidence	result
1	done	SEAT.txt stamps.txt	seat 033 idea 33
2	done	HONESTY_B.txt B_O_d12.raw.txt B_G_d12.raw.txt	honesty match and baseline sums above
3	done	idea.patch.txt proof_off_O.txt proof_on_O.txt match.log	option off identical, on differs, match played
4	done	partner_apply_check.txt partner_on_vs_claim.txt partner_match.log	partner 083 CONFIRMS
5	done	REPORT.md RESULT.txt	this report
```

git status --short
```
 M forge-combo29/grok/033/stamps.txt
?? forge-combo29/grok/033/REPORT.md
?? forge-combo29/grok/033/RESULT.txt
?? forge-combo29/grok/033/apply_check.txt
?? forge-combo29/grok/033/report_tables.py
?? forge-combo29/grok/033/report_tables.txt
```

ls -la forge-combo29/grok/033
```
total 8560
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:15 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     943 Nov 20 08:09 asan_G100.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  128352 Nov 20 08:09 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     969 Nov 20 08:09 asan_scratch.raw.meta
-rw-r--r-- 1 ubuntu ubuntu    4166 Nov 20 08:09 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 08:00 B_G_d12.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  548241 Nov 20 08:00 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     878 Nov 20 08:00 B_O_d12.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  302646 Nov 20 08:00 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1016 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1256 Nov 20 09:09 compare_to_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    7212 Nov 20 09:13 config.json
-rw-r--r-- 1 ubuntu ubuntu    1196 Nov 20 08:04 design.txt
-rw-r--r-- 1 ubuntu ubuntu     853 Nov 20 08:20 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:57 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:08 G100.epd
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 07:58 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 07:58 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 07:58 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 07:58 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3385 Nov 20 08:05 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     491 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 07:58 honesty_b_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:58 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:05 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:05 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:05 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:05 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     491 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 08:05 honesty_p_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:05 honesty_p_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    9487 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1413 Nov 20 07:58 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  151964 Nov 20 08:17 match.log
-rw-r--r-- 1 ubuntu ubuntu 3640186 Nov 20 08:17 match.pgn
-rw-r--r-- 1 ubuntu ubuntu     667 Nov 20 08:09 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu    5225 Nov 20 08:09 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     421 Nov 20 08:20 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG553.epd
-rw-r--r-- 1 ubuntu ubuntu   15471 Nov 20 09:09 partner083_O_d12_P_on.tsv
-rw-r--r-- 1 ubuntu ubuntu    9394 Nov 20 09:09 partner083.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 09:09 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:10 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:10 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:10 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:10 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     507 Nov 20 09:10 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:10 partner_honesty_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 09:10 partner_honesty_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   78133 Nov 20 09:13 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 1605012 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     418 Nov 20 09:13 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     919 Nov 20 09:10 partner_off_O.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  304095 Nov 20 09:10 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      49 Nov 20 09:10 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     957 Nov 20 09:10 partner_on_O.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  305909 Nov 20 09:10 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1480 Nov 20 09:10 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 09:10 partner_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:05 P_off_G_d12.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  550579 Nov 20 08:05 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 08:05 P_off_O_d12.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  304045 Nov 20 08:05 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     950 Nov 20 08:05 P_on_O_d12.raw.meta
-rw-r--r-- 1 ubuntu ubuntu  305766 Nov 20 08:05 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     707 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      49 Nov 20 08:07 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      49 Nov 20 08:07 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:07 proof_on_O_sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1481 Nov 20 08:07 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   19298 Nov 20 07:58 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    7199 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    4325 Nov 20 09:15 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu    2072 Nov 20 09:15 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    5421 Nov 20 08:06 run_depth.py
-rwxr-xr-x 1 ubuntu ubuntu    1325 Nov 20 08:08 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:09 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:57 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    1333 Nov 20 08:07 show_options.py
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:09 smoke_one.fen
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1412 Nov 20 07:59 summarize_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     294 Nov 20 08:07 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:07 uci_options.txt
```
