# Seat 012, idea 12, P20

P20 scores a known dead ending, and king plus bishop plus knight versus a lone king, before the network is called.
The plain engine already does that in `dead_material_score`, behind the check option DeadMaterial, default false.
The two corner-drive weights were fixed numbers. They are now the spins IdeaP20_Corner (default 28) and IdeaP20_King (default 12).

EXISTS: yes, `src/eval.cpp:516`. The on/off switch is already the UCI option DeadMaterial in `src/uci.cpp`. The weights were not options. With the switch false the search does not read them, so the defaults leave today's path unchanged.

Honesty numbers, no setoption, from `report_facts.py`:

```
info string bench depth 11 nodes 312866 time 179 nps 1747854
info string bench depth 13 nodes 862329 time 467 nps 1846528
info string bench depth 16 nodes 3024920 time 1587 nps 1906061
nodes 4865609
```

Exe P printed the same four node counts (312866, 862329, 3024920, 4865609).

Table, pasted from `report_facts.py`:

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat file present
2 honesty B | done | HONESTY_B.txt | 312866
2 O sum | done | B_O_d12.rows.txt | positions 200 sum 9500069 first3 41311 24872 28574
2 G sum | done | B_G_d12.rows.txt | positions 353 sum 18466239 first3 37203 70845 144383
3 patch applies | done | apply_check.txt | APPLY_CHECK_OK
3 proof off O | done | cmp_off_O.txt | positions 200; differ 0; equal 200
3 proof off G | done | cmp_off_G.txt | positions 353; differ 0; equal 353
3 proof on O | done | cmp_on_O.txt | positions 200; differ 0; equal 200
3 uci options | done | uci_p.txt | option name DeadMaterial type check default false | option name IdeaP20_Corner type spin default 28 min 0 max 1000 | option name IdeaP20_King type spin default 12 min 0 max 1000
3 sanitizer | done | asan_G100_d10.meta | nm_asan_count=35 error_lines 0
3 scratch | done | scratch_asan.raw.txt | SUMMARY: AddressSanitizer: heap-buffer-overflow /home/ubuntu/scratch-forge/src/uci.cpp:47 in apply_position
3 match | done | match_og_summary.txt | 1106 games
4 partner | done | partner_cmp_on_O.txt | positions 200; differ 0; equal 200
4 partner match | done | partner_match_summary.txt | 600 games
```

Proofs on exe P:

(1) Honesty with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

(2) S14 and DeadMaterial false. O depth 12: 200 positions, differ 0. G depth 12: 353 positions, differ 0. Both match exe B position by position, including the best move and the score.

(3) S14 and DeadMaterial true, spins left at 28 and 12. O depth 12: 200 positions, differ 0, sum 9500069, first three 41311 24872 28574. That is 0 of 200. The code does run. O's smallest position has 26 pieces, so a 12-ply search cannot reach a pawnless minor ending (`why_o_zero.txt`). A king-bishop-knight versus king probe changed from 25478 nodes and cp 303 to 16171 nodes and cp 676. A king and two knights versus king probe changed from 44393 nodes and cp 243 to 5814 nodes and cp 0. King and one knight versus king stayed equal, because the search already treats that as insufficient material before evaluation. G with the switch on also differed in 0 of 353 positions.

(4) The `uci` answer lists `option name DeadMaterial type check default false`, `option name IdeaP20_Corner type spin default 28 min 0 max 1000`, and `option name IdeaP20_King type spin default 12 min 0 max 1000`.

(5) The AddressSanitizer and UndefinedBehaviorSanitizer build has `nm_asan_count=35`. The first 100 positions of G at depth 10 with the switch on produced 0 sanitizer lines. The same runner, on a scratch copy with one heap read past the end of a 4-int array for the FEN `8/8/8/8/8/k7/8/K1N5 w - - 0 1`, reported `ERROR: AddressSanitizer: heap-buffer-overflow` and `SUMMARY: AddressSanitizer: heap-buffer-overflow /home/ubuntu/scratch-forge/src/uci.cpp:47 in apply_position`.

`git apply --check` of `idea.patch.txt` on a fresh copy of the base printed `APPLY_CHECK_OK`.

Match, exe P with DeadMaterial true against exe P with DeadMaterial false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. Pasted from `match_og_summary.txt`:

```
Results of P-on vs P-off (20000 nodes, 1t, 16MB, OG.fens):
Elo: 0.31 +/- 0.62, nElo: 10.46 +/- 20.48
LOS: 84.16 %, DrawRatio: 99.82 %, PairsRatio: inf
Games: 1106, Wins: 337, Losses: 336, Draws: 433, Points: 553.5 (50.05 %)
Ptnml(0-2): [0, 0, 552, 1, 0], WL/DD Ratio: 1.56
finished_games 1106
```

The point estimate 0.31 is inside the prediction (0, wrong outside -20 to +20). The interval is not entirely below 0. The O depth-12 sum 9500069 matches the prediction.

Partner: seat 062, the next seat with this idea. Seat 112 had no branch. Verdict: CONFIRMS. Their patch applies (`APPLY_CHECK_OK`). Their build's honesty numbers are 312866, 862329, 3024920, and 4865609. DeadMaterial false matched exe B on all 200 O depth-12 rows. DeadMaterial true matched their own O depth-12 rows on all 200 (they claimed differ 0). A match of their switch on my 300 R openings, both colours, finished 600 games:

```
Results of P062-on vs P062-off (20000 nodes, 1t, 16MB, R.fens):
Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
LOS: -nan %, DrawRatio: 100.00 %, PairsRatio: -nan
Games: 600, Wins: 255, Losses: 255, Draws: 90, Points: 300.0 (50.00 %)
Ptnml(0-2): [0, 0, 300, 0, 0], WL/DD Ratio: 5.67
finished_games 600
```

suspicions, not proven: the R match's `nElo: -nan` and `+/- 0.00` come from a perfectly balanced pentanomial, `[0, 0, 300, 0, 0]`, not from a missing game. All 600 games finished. I did not prove that fastchess's formula is undefined only in that case; that is what the printed block shows.

What I did NOT do: I did not replay seat 062's sanitizer scratch. I did not play their 1106-game book a second time. I did not run a match with IdeaP20_Corner or IdeaP20_King set away from 28 and 12. I did not add a second check option named IdeaP20. I did not open a pull request.

What I am NOT sure about: a corner weight other than 28 might change results, and I did not measure one. My spin maximum is 1000 and seat 062's is 256; at the defaults the searches match. A depth-12 node count that does not change does not by itself prove the function was never called inside the tree. The probe positions are the evidence that it changes the search when the position is one it recognizes.

times: see stamps.txt


```
$ git status --short
 M forge-combo29/grok/012/stamps.txt
?? config.json
?? forge-combo29/grok/012/REPORT.md
?? forge-combo29/grok/012/RESULT.txt
?? forge-combo29/grok/012/report_facts.py
?? forge-combo29/grok/012/report_facts.txt
$ ls -la forge-combo29/grok/012
total 10692
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:05 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     985 Nov 20 08:05 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  114076 Nov 20 08:05 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7119 Nov 20 08:05 asan_G100_d10.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 07:57 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  502708 Nov 20 07:57 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   25456 Nov 20 07:57 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:57 B_G_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu     862 Nov 20 07:57 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277036 Nov 20 07:57 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 07:57 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     142 Nov 20 07:57 B_O_d12.runlog
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:04 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:04 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:04 cmp_on_G.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:04 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 08:04 cmp_probe.txt
-rw-r--r-- 1 ubuntu ubuntu    1025 Nov 20 07:59 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:01 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:55 G.epd
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:55 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:55 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:55 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:55 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:55 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:55 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:55 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:55 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     830 Nov 20 07:55 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     542 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:59 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:59 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 07:59 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 07:59 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     830 Nov 20 07:59 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu    4615 Nov 20 07:57 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1288 Nov 20 07:59 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     483 Nov 20 08:09 match_og.log
-rw-r--r-- 1 ubuntu ubuntu     315 Nov 20 08:02 match_og.meta
-rw-r--r-- 1 ubuntu ubuntu      11 Nov 20 08:09 match_og.nohup
-rw-r--r-- 1 ubuntu ubuntu  114663 Nov 20 08:09 match_og.out.txt
-rw-r--r-- 1 ubuntu ubuntu 4625308 Nov 20 08:09 match_og.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1800 Nov 20 08:02 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu     293 Nov 20 08:10 match_og_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:55 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:02 OG.fens
-rw-r--r-- 1 ubuntu ubuntu     621 Nov 20 08:06 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:08 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:08 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:08 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:08 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:08 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:08 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:08 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 09:09 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 09:09 partner_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1092 Nov 20 09:08 partner_cmp.py
-rw-r--r-- 1 ubuntu ubuntu    4671 Nov 20 09:07 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     482 Nov 20 09:12 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 09:09 partner_match.meta
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 09:12 partner_match.nohup
-rw-r--r-- 1 ubuntu ubuntu   65788 Nov 20 09:12 partner_match.out.txt
-rw-r--r-- 1 ubuntu ubuntu 2414019 Nov 20 09:12 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1683 Nov 20 09:09 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     295 Nov 20 09:14 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     989 Nov 20 09:08 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  276873 Nov 20 09:08 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 09:08 partner_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     988 Nov 20 09:08 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  276802 Nov 20 09:08 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 09:08 partner_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:07 partner_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 09:08 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:08 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     982 Nov 20 07:59 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  502758 Nov 20 08:00 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   25456 Nov 20 08:00 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     983 Nov 20 07:59 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  276919 Nov 20 07:59 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 07:59 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     985 Nov 20 08:01 P_off_probe_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3772 Nov 20 08:01 P_off_probe_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 08:01 P_off_probe_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     981 Nov 20 08:01 P_on_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  502772 Nov 20 08:01 P_on_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   25456 Nov 20 08:01 P_on_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     982 Nov 20 08:00 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277104 Nov 20 08:00 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   17048 Nov 20 08:00 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     984 Nov 20 08:01 P_on_probe_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3757 Nov 20 08:01 P_on_probe_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     149 Nov 20 08:01 P_on_probe_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     598 Nov 20 07:58 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:02 probe_eval.txt
-rw-r--r-- 1 ubuntu ubuntu      98 Nov 20 08:01 probe.fens
-rw-r--r-- 1 ubuntu ubuntu    3935 Nov 20 09:15 report_facts.py
-rw-r--r-- 1 ubuntu ubuntu    3799 Nov 20 09:15 report_facts.txt
-rw-r--r-- 1 ubuntu ubuntu    6677 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19961 Nov 20 07:59 R.fens
-rw-r--r-- 1 ubuntu ubuntu     996 Nov 20 08:05 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu    3567 Nov 20 08:05 scratch_asan.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:05 scratch_fen.fens
-rw-r--r-- 1 ubuntu ubuntu    1338 Nov 20 08:05 scratch_run.txt
-rw-r--r-- 1 ubuntu ubuntu    6822 Nov 20 08:03 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:04 sum_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     429 Nov 20 07:56 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu    5057 Nov 20 07:59 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu     835 Nov 20 08:04 why_o_zero.py
-rw-r--r-- 1 ubuntu ubuntu     124 Nov 20 08:04 why_o_zero.txt
-rw-r--r-- 1 ubuntu ubuntu     475 Nov 20 07:57 write_honesty_b.py
```
