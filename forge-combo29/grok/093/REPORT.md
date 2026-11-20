IdeaK4 shrinks the reverse-futility margin when the opponent's static eval fell over two plies.
Built as check option IdeaK4, default false, and spin IdeaK4_Shrink, default 24, range 0 to 200.
On, a lower static eval one ply ago than three plies ago (both the opponent to move, neither the in-check sentinel) subtracts IdeaK4_Shrink from today's margin.

EXISTS: no. Reverse futility in the plain engine uses only `RfpMargin * depth - RfpImproving * improving`.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Table from `report_table.py` reading the raw files:

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 093 idea 43
STEP 2 honesty B and O/G | done | HONESTY_B.txt O_B_d12.raw.txt G_B_d12.raw.txt | pins match; O n 200 sum 9500069; G n 353 sum 18466239
STEP 3 prediction | done | prediction.txt | pushed before the patched measurements
STEP 3 patch | done | idea.patch.txt apply_check.txt | git apply --check exit 0
proof 1 honesty P | done | HONESTY_P.txt | bench 11 nodes 312866 expected 312866 OK bench 13 nodes 862329 expected 862329 OK bench 16 nodes 3024920 expected 3024920 OK go perft 5 nodes 4865609 expected 4865609 OK
proof 2 switch off | done | proof_off_O.txt proof_off_G.txt | O differ 0; G differ 0
proof 3 switch on | done | proof_on_O.txt O_P_on.raw.txt | differ 200; positions 200 sum 8921190
proof 4 uci | done | uci_P.txt | option name IdeaK4 type check default false | option name IdeaK4_Shrink type spin default 24 min 0 max 200
proof 5 sanitizer | done | G100_asan.meta asan_probe.raw.txt | asan_symbols 35; G100 ERROR lines 0; probe AddressSanitizer lines 1
STEP 3 match | done | match_summary.txt | Elo: 5.03 +/- 9.77, nElo: 10.54 +/- 20.48
STEP 4 partner 043 | done | proof_partner_off.txt proof_partner_on.txt match_partner_summary.txt | off differ 0; on vs their rows differ 0; Elo: 1.16 +/- 8.94, nElo: 3.60 +/- 27.80
STEP 5 report | done | REPORT.md RESULT.txt | this commit
```

Proofs on exe P, S14, Threads 1, Hash 16:

(1) Honesty with no setoption: 312866, 862329, 3024920, 4865609.
(2) Switch false: O depth 12 equal to exe B on all 200 positions (sum 9500069). G depth 12 equal on all 353 (sum 18466239).
(3) Switch true, IdeaK4_Shrink 24: O depth 12 sum 8921190. 200 of 200 positions differ from exe B.
(4) `uci` lists `option name IdeaK4 type check default false` and `option name IdeaK4_Shrink type spin default 24 min 0 max 200`.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build. `nm -C` count of `__asan_` is 35 in `G100_asan.meta`. First 100 of G at depth 10 with the switch on: 0 sanitizer lines, sum 1827036. The same runner on a scratch copy that reads one past a four-int heap array on FEN `8/8/8/8/8/8/8/K6k w - - 0 1` reports `ERROR: AddressSanitizer: heap-buffer-overflow`.

`git apply --check` of `idea.patch.txt` on a fresh base worktree exited 0 (`apply_check.txt`). The patch matches `git diff` in the work tree.

Prediction, committed before these measurements: O sum 9150000, wrong outside 8200000..9550000. Measured 8921190. Elo -8, wrong outside -45..+20. Measured +5.03.

Match, K4on versus K4off, both exe P, S14, 20000 nodes, openings O then G, both colours, 1106 games, concurrency 3. From `match_summary.txt`: Elo 5.03 +/- 9.77, 341 wins, 325 losses, 440 draws, 561.0 points. The interval includes 0 and is not entirely below 0, so I did not treat it as a broken idea.

Partner is seat 043 (same idea; the next seat after 093 wraps to 043). Verdict: CONFIRMS. On a fresh base, `git apply --check` and apply succeeded. Honesty pins matched. Switch false matched exe B's O depth-12 rows, 200 equal, 0 differ. Switch true, their default IdeaK4_Shrink 32, matched their own O depth-12 log on all 200 positions (sum 8983632) and differed from exe B on all 200. My match of their switch on 300 R openings, both colours, 600 games: Elo 1.16 +/- 8.94.

suspicions, not proven: both matches are compatible with a small effect and with no effect. Their O+G match, which I did not replay, was Elo -6.60 +/- 10.53. A shrink of 24 and a shrink of 32 need not have the same sign.

what I did NOT do: I did not replay the partner's 1106-game O+G match. I did not try other shrink values. I did not run the sanitizer build through the match. No `FABLE_TO_grok` file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about: a null move leaves a stack entry whose static eval may not be the opponent's last real eval, so the comparison can see a sentinel and stay quiet, or see a null-move eval. I did not measure how often that happens. I am not sure the +5 Elo survives the owner's net. On the R match, fastchess prints DrawRatio 85.33% next to 52 draws in 600 games; I quote the block and do not explain that percentage.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/093/config.json
 M forge-combo29/grok/093/review_partner.sh
 M forge-combo29/grok/093/stamps.txt
?? forge-combo29/grok/093/HONESTY_PARTNER.txt
?? forge-combo29/grok/093/HONESTY_PARTNER_bench11.meta
?? forge-combo29/grok/093/HONESTY_PARTNER_bench11.txt
?? forge-combo29/grok/093/HONESTY_PARTNER_bench13.meta
?? forge-combo29/grok/093/HONESTY_PARTNER_bench13.txt
?? forge-combo29/grok/093/HONESTY_PARTNER_bench16.meta
?? forge-combo29/grok/093/HONESTY_PARTNER_bench16.txt
?? forge-combo29/grok/093/HONESTY_PARTNER_perft5.meta
?? forge-combo29/grok/093/HONESTY_PARTNER_perft5.txt
?? forge-combo29/grok/093/O_partner_off.meta
?? forge-combo29/grok/093/O_partner_off.raw.txt
?? forge-combo29/grok/093/O_partner_off.rows.txt
?? forge-combo29/grok/093/O_partner_on.meta
?? forge-combo29/grok/093/O_partner_on.raw.txt
?? forge-combo29/grok/093/O_partner_on.rows.txt
?? forge-combo29/grok/093/REPORT.md
?? forge-combo29/grok/093/RESULT.txt
?? forge-combo29/grok/093/apply_check.txt
?? forge-combo29/grok/093/match_partner_R.pgn
?? forge-combo29/grok/093/match_partner_fastchess.txt
?? forge-combo29/grok/093/match_partner_summary.txt
?? forge-combo29/grok/093/partner043_O_on.raw.txt
?? forge-combo29/grok/093/partner043_idea.patch.txt
?? forge-combo29/grok/093/proof_partner_off.txt
?? forge-combo29/grok/093/proof_partner_on.txt
?? forge-combo29/grok/093/proof_partner_on_vs_B.txt
?? forge-combo29/grok/093/report_table.py
?? forge-combo29/grok/093/report_table.txt
?? forge-combo29/grok/093/run_partner_match.sh

$ ls -la forge-combo29/grok/093
total 8420
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 09:18 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     364 Nov 20 08:05 asan_probe_insert.txt
-rw-r--r-- 1 ubuntu ubuntu     948 Nov 20 08:06 asan_probe.meta
-rw-r--r-- 1 ubuntu ubuntu    9086 Nov 20 08:06 asan_probe.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 asan_probe.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    1049 Nov 20 08:03 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu    6947 Nov 20 09:16 config.json
-rw-r--r-- 1 ubuntu ubuntu     946 Nov 20 08:05 G100_asan.meta
-rw-r--r-- 1 ubuntu ubuntu  118650 Nov 20 08:05 G100_asan.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5884 Nov 20 08:05 G100_asan.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     850 Nov 20 08:02 G_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  507667 Nov 20 08:02 G_B_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:02 G_B_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     850 Nov 20 08:04 G_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  507685 Nov 20 08:04 G_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:04 G_P_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 07:59 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 07:59 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:59 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:59 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:59 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 07:59 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:59 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2008 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:13 HONESTY_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 09:13 HONESTY_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:13 HONESTY_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 09:13 HONESTY_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:13 HONESTY_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 09:13 HONESTY_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 09:13 HONESTY_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5312 Nov 20 09:13 HONESTY_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 09:13 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:03 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 08:03 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:03 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 08:03 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:03 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:03 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 08:03 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5312 Nov 20 08:03 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     170 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1866 Nov 20 08:03 honesty_run.py
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 08:03 idea_design.txt
-rw-r--r-- 1 ubuntu ubuntu    5305 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1346 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  134256 Nov 20 08:15 match_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 3475718 Nov 20 08:15 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu   80293 Nov 20 09:16 match_partner_fastchess.txt
-rw-r--r-- 1 ubuntu ubuntu 1486109 Nov 20 09:16 match_partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     337 Nov 20 09:18 match_partner_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     578 Nov 20 08:17 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu     336 Nov 20 08:17 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     854 Nov 20 08:01 O_B_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  281787 Nov 20 08:01 O_B_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:01 O_B_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     857 Nov 20 09:13 O_partner_off.meta
-rw-r--r-- 1 ubuntu ubuntu  282064 Nov 20 09:13 O_partner_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:13 O_partner_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     890 Nov 20 09:13 O_partner_on.meta
-rw-r--r-- 1 ubuntu ubuntu  281051 Nov 20 09:13 O_partner_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14755 Nov 20 09:13 O_partner_on.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     854 Nov 20 08:04 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  281932 Nov 20 08:04 O_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:04 O_P_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     925 Nov 20 08:04 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu  280950 Nov 20 08:04 O_P_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14755 Nov 20 08:04 O_P_on.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    5453 Nov 20 09:12 partner043_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  313545 Nov 20 09:12 partner043_O_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     606 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     129 Nov 20 08:05 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     129 Nov 20 08:05 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:05 proof_on_O_sum.txt
-rw-r--r-- 1 ubuntu ubuntu     360 Nov 20 08:05 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 09:13 proof_partner_off.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:13 proof_partner_on.txt
-rw-r--r-- 1 ubuntu ubuntu     404 Nov 20 09:13 proof_partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4857 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3315 Nov 20 09:19 report_table.py
-rw-r--r-- 1 ubuntu ubuntu    1382 Nov 20 09:19 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:19 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1744 Nov 20 09:13 review_partner.sh
-rwxr-xr-x 1 ubuntu ubuntu    1420 Nov 20 08:08 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1352 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    5750 Nov 20 08:04 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   19318 Nov 20 08:08 set_R.epd
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     636 Nov 20 08:00 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:05 uci_P.txt
```
