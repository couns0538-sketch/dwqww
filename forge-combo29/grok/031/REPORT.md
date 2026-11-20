# Seat 031, idea 31, S10

IdeaS10 shrinks a quiet score that only shuffles. The option is a check, default false. With it on, a short probe forbids captures and pawn moves for the side the static eval calls the winner, and if that probe stays close to the searched score while the defender can shuffle or repeat, the score is multiplied by 768/1024. Six spins hold the numbers: Margin 80, Flat 40, Probe 2, Close 30, Shrink 768, MinDepth 4.

EXISTS: no. EvalRule50Damp scales by the half-move clock. The word shuffle in search.cpp is an SIMD permute. Neither is this probe.

Honesty, no setoption, both builds. From HONESTY_B.txt and HONESTY_P.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 031 idea 31 |
| 2 honesty and baseline | done | HONESTY_B.txt, B_O_d12.nodes.txt, B_G_d12.nodes.txt | O sum 9500069, G sum 18466239 |
| 3 idea | done | idea.patch.txt, off_O_vs_B.txt, on_O_vs_B.txt, match_on_off.txt | off identical, on differs 195 of 200, Elo -100.06 +/- 11.96 |
| 4 partner | done | partner081.patch.txt, partner081_on_vs_claimed.txt, partner081_R.txt | CONFIRMS, R Elo -1.16 +/- 8.18 |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty on exe P with no setoption matches the four known numbers. HONESTY_P.txt.

(2) S14 and IdeaS10 false. O depth 12: differ 0 of 200 against exe B (off_O_vs_B.txt). G depth 12: differ 0 of 353 (off_G_vs_B.txt). Exe B itself reproduced O sum 9500069, first three 41311, 24872, 28574, and G sum 18466239.

(3) S14 and IdeaS10 true. O depth 12 sum 10937472, first three 39695, 24369, 46521 (P_on_O_d12.nodes.txt). differ 195 of 200 against exe B (on_O_vs_B.txt). The code runs.

(4) uci lists the new options at the defaults. capture_uci.py printed missing 0. The lines are in P_uci.txt: IdeaS10 check default false, and the six IdeaS10_ spins at 80, 40, 2, 30, 768, 4.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS10 true, first 100 of G at depth 10. P_asan_G100_d10.err is empty. P_asan_G100_d10.meta has nm_asan_count 35. The scratch engine, same runner, FEN 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1, reports heap-buffer-overflow in asan_fault.err. A first FEN of bare kings never entered search (insufficient material), so that attempt proved nothing and was replaced.

git apply --check of idea.patch.txt on a fresh base worktree printed APPLY_CHECK_OK.

## Match

exe P with IdeaS10 true against exe P with IdeaS10 false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games, concurrency 3. From match_on_off.txt:

Elo: -100.06 +/- 11.96, games 1106, wins 183, losses 493, draws 430.

The whole interval is below 0 and the point is below -20. LOOK.txt records the one look. I did not find a sign error or a shrunk mate. The loss fits the idea's own warning, and the probe spends part of the 20000-node budget. I did not change the code after that look.

prediction.txt, written before any exe P measurement, said 14000000 (wrong below 8000000 or above 30000000) and Elo -25 (wrong if the whole interval is above +10 or below -120). The measured sum 10937472 is inside that sum range. The Elo interval is about -112 to -88, which is not entirely below -120. The point estimate -25 was far from -100.

## Partner

Partner is seat 081 (same idea, next seat with a branch). At minute 75 the branch had idea.patch.txt. git apply --check printed APPLY_CHECK_OK (partner_build_log.txt). My harness, not theirs: honesty matched the four numbers (HONESTY_partner081.txt). IdeaS10 false, O depth 12, differ 0 of 200 against my exe B (partner081_off_vs_B.txt). IdeaS10 true, O depth 12, differ 0 of 200 against their published rows, both sums 9542904 (partner081_on_vs_claimed.txt). They claim 10 of 200 differ from the plain engine and sum 9542904. That is what this rebuild did.

Their switch, 300 of my R openings, both colours, 600 games (partner081_R.txt): Elo -1.16 +/- 8.18. I did not replay their 1106-game match.

Verdict: CONFIRMS.

## Suspicions, not proven

The -100 Elo may be mostly the probe consuming the node budget, not the 768/1024 shrink. I did not separate those two.

## What I did NOT do

I did not turn the switch on for G depth 12. I did not try other spin values. I did not replay seat 081's 1106-game match. I did not run a second 600-game match of my own patch on R, because 081 had a patch. No FABLE_TO_grok file existed at step 1 or at minute 60.

## What I am NOT sure about

Forge has no pawn-score number in search. I treated a large flat static eval over two non-pawn plies as that condition, and I wrote why in DECISIONS.txt. I am not sure that is the reading the idea's author would count.

## times: see stamps.txt

The last part is the command output below.

```
$ git status --short
 M forge-combo29/grok/031/config.json
 M forge-combo29/grok/031/stamps.txt
?? forge-combo29/grok/031/HONESTY_partner081.txt
?? forge-combo29/grok/031/REPORT.md
?? forge-combo29/grok/031/RESULT.txt
?? forge-combo29/grok/031/compare_claimed.py
?? forge-combo29/grok/031/honesty_partner081_bench11.err
?? forge-combo29/grok/031/honesty_partner081_bench11.meta
?? forge-combo29/grok/031/honesty_partner081_bench11.txt
?? forge-combo29/grok/031/honesty_partner081_bench13.err
?? forge-combo29/grok/031/honesty_partner081_bench13.meta
?? forge-combo29/grok/031/honesty_partner081_bench13.txt
?? forge-combo29/grok/031/honesty_partner081_bench16.err
?? forge-combo29/grok/031/honesty_partner081_bench16.meta
?? forge-combo29/grok/031/honesty_partner081_bench16.txt
?? forge-combo29/grok/031/honesty_partner081_id.txt
?? forge-combo29/grok/031/honesty_partner081_perft5.err
?? forge-combo29/grok/031/honesty_partner081_perft5.meta
?? forge-combo29/grok/031/honesty_partner081_perft5.txt
?? forge-combo29/grok/031/partner081.patch.txt
?? forge-combo29/grok/031/partner081_O_on_claimed.nodes.txt
?? forge-combo29/grok/031/partner081_R.err
?? forge-combo29/grok/031/partner081_R.pgn
?? forge-combo29/grok/031/partner081_R.txt
?? forge-combo29/grok/031/partner081_config.json
?? forge-combo29/grok/031/partner081_off_O_d12.err
?? forge-combo29/grok/031/partner081_off_O_d12.meta
?? forge-combo29/grok/031/partner081_off_O_d12.nodes.txt
?? forge-combo29/grok/031/partner081_off_O_d12.sent
?? forge-combo29/grok/031/partner081_off_O_d12.txt
?? forge-combo29/grok/031/partner081_off_vs_B.txt
?? forge-combo29/grok/031/partner081_on_O_d12.err
?? forge-combo29/grok/031/partner081_on_O_d12.meta
?? forge-combo29/grok/031/partner081_on_O_d12.nodes.txt
?? forge-combo29/grok/031/partner081_on_O_d12.sent
?? forge-combo29/grok/031/partner081_on_O_d12.txt
?? forge-combo29/grok/031/partner081_on_vs_claimed.txt
?? forge-combo29/grok/031/partner_build_log.txt
?? forge-combo29/grok/031/run_partner_match.sh

$ ls -la
total 4832
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu    5789 Nov 20 08:09 asan_fault.err
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 asan_fault_id.err
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:09 asan_fault_id.meta
-rw-r--r-- 1 ubuntu ubuntu    5346 Nov 20 08:09 asan_fault_id.txt
-rw-r--r-- 1 ubuntu ubuntu     322 Nov 20 08:09 asan_fault.meta
-rw-r--r-- 1 ubuntu ubuntu    5498 Nov 20 08:09 asan_fault.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 B_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 08:03 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4562 Nov 20 08:04 B_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   36804 Nov 20 08:03 B_G_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  507462 Nov 20 08:03 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 B_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 08:03 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2565 Nov 20 08:04 B_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   24018 Nov 20 08:03 B_O_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  281757 Nov 20 08:03 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1782 Nov 20 08:05 capture_uci.py
-rw-r--r-- 1 ubuntu ubuntu    1187 Nov 20 09:08 compare_claimed.py
-rw-r--r-- 1 ubuntu ubuntu    1075 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    6882 Nov 20 09:13 config.json
-rw-r--r-- 1 ubuntu ubuntu    1850 Nov 20 08:08 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:09 fault.fen
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:08 G100.epd
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 honesty_B_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:02 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 honesty_B_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:02 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 honesty_B_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:02 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:02 honesty_B_id.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 honesty_B_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:02 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:04 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 honesty_partner081_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:09 honesty_partner081_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 honesty_partner081_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 honesty_partner081_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:09 honesty_partner081_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 honesty_partner081_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 honesty_partner081_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:09 honesty_partner081_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 honesty_partner081_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5281 Nov 20 09:09 honesty_partner081_id.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 honesty_partner081_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     265 Nov 20 09:09 honesty_partner081_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 honesty_partner081_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 HONESTY_partner081.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 honesty_P_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 honesty_P_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:05 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 honesty_P_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:05 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:05 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5346 Nov 20 08:05 honesty_P_id.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 honesty_P_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:05 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:05 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:09 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    2382 Nov 20 08:02 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   12670 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     968 Nov 20 08:16 LOOK.txt
-rw-r--r-- 1 ubuntu ubuntu    1735 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 match_on_off.err
-rw-r--r-- 1 ubuntu ubuntu 1016490 Nov 20 08:14 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  108668 Nov 20 08:14 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu    4877 Nov 20 08:07 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu      80 Nov 20 08:09 off_G_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      80 Nov 20 08:09 off_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 OG553.epd
-rw-r--r-- 1 ubuntu ubuntu    3109 Nov 20 08:09 on_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 08:05 opt_off.txt
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:05 opt_on.txt
-rw-r--r-- 1 ubuntu ubuntu    6882 Nov 20 09:14 partner081_config.json
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 partner081_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 09:09 partner081_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2565 Nov 20 09:09 partner081_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   24061 Nov 20 09:09 partner081_off_O_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  282057 Nov 20 09:09 partner081_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      80 Nov 20 09:09 partner081_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 partner081_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     903 Nov 20 09:09 partner081_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2565 Nov 20 09:09 partner081_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   24060 Nov 20 09:09 partner081_on_O_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  282130 Nov 20 09:09 partner081_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 09:10 partner081_on_vs_claimed.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:08 partner081_O_on_claimed.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   16833 Nov 20 09:08 partner081.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:10 partner081_R.err
-rw-r--r-- 1 ubuntu ubuntu  470992 Nov 20 09:13 partner081_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   53635 Nov 20 09:13 partner081_R.txt
-rw-r--r-- 1 ubuntu ubuntu      38 Nov 20 09:14 partner_build_log.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 P_asan_G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:08 P_asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu   11008 Nov 20 08:08 P_asan_G100_d10.sent
-rw-r--r-- 1 ubuntu ubuntu  115051 Nov 20 08:08 P_asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     923 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4562 Nov 20 08:06 P_off_G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   36847 Nov 20 08:05 P_off_G_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  507779 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     927 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2565 Nov 20 08:06 P_off_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   24061 Nov 20 08:05 P_off_O_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  282050 Nov 20 08:05 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     926 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2571 Nov 20 08:06 P_on_O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu   24060 Nov 20 08:05 P_on_O_d12.sent
-rw-r--r-- 1 ubuntu ubuntu  272588 Nov 20 08:05 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     292 Nov 20 08:05 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 P_uci.err
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:06 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5346 Nov 20 08:06 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu   19054 Nov 20 08:04 R300.fen
-rw-r--r-- 1 ubuntu ubuntu    1519 Nov 20 08:03 read_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    6923 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:14 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1563 Nov 20 08:07 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1405 Nov 20 09:08 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1459 Nov 20 08:10 run_partner.sh
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     707 Nov 20 08:04 summarize_honesty.py
```
