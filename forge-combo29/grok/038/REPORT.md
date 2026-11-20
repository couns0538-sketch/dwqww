# Seat 038, idea 38, IdeaA7

Once a non-mate score has raised alpha at a node whose depth is 2 to 12, each later move is searched one ply shallower. The UCI switch is IdeaA7, default false. Spins IdeaA7_MinDepth 2, IdeaA7_MaxDepth 12 and IdeaA7_Ply 1 hold those three numbers. The cut is applied to new_depth after extensions, so the reduced search and the re-search both use it. A cut that lands at depth below 1 skips the late-move clamp and goes to search(), which already treats that as quiescence.

EXISTS: no. search.cpp does not shorten the remaining moves after alpha rises. LmrDeeperShallower and HindsightDepth are other switches and default off.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Files HONESTY_B.txt and HONESTY_P.txt.

| step | status | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 038, idea 38, Grok 4.7 |
| 2 builds and known sums | done | HONESTY_B.txt, sum_B_O_d12.txt, sum_B_G_d12.txt | honesty exact; O sum 9500069 first3 41311 24872 28574; G sum 18466239 |
| 3 idea | done | idea.patch.txt, apply_check.txt, cmp_off_O.txt, cmp_off_G.txt, cmp_on_O.txt, uci_P.txt, asan_G100_d10.meta, asan_trap.txt, match_on_off_result.txt | apply check ok; off identical; on 200 differ; sanitizer clean and the trap reports; Elo -6.91 +/- 9.96 over 1106 games |
| 4 partner 088 | done | partner_088_idea.patch.txt, cmp_partner_off_O.txt, cmp_partner_on_O.txt, HONESTY_Q.txt, match_partner_R_result.txt | CONFIRMS; see below |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1). HONESTY_P.txt: 312866, 862329, 3024920, 4865609.

Proof (2). cmp_off_O.txt: compared 200, equal 200, differ 0. cmp_off_G.txt: compared 353, equal 353, differ 0. S14 and IdeaA7 false.

Proof (3). cmp_on_O.txt: compared 200, equal 0, differ 200. sum_P_on_O_d12.txt sum 5767895. The code runs. prediction.txt said 6200000, wrong outside 3500000..9200000. 5767895 is inside that band.

Proof (4). uci_P.txt lists `option name IdeaA7 type check default false`, `IdeaA7_MinDepth type spin default 2 min 0 max 64`, `IdeaA7_MaxDepth type spin default 12 min 0 max 64`, `IdeaA7_Ply type spin default 1 min 0 max 8`.

Proof (5). asan_nm_count.txt is 35. asan_G100_d10.txt has 0 lines matching AddressSanitizer or runtime error, first 100 of G, depth 10, IdeaA7 true. The same runner on the scratch engine and positions_asan_trap.fen reports `ERROR: AddressSanitizer: heap-buffer-overflow` at search.cpp:1568 in asan_trap.txt. sanitizer=clean.

Match. match_on_off_result.txt: Elo -6.91 +/- 9.96, games 1106, wins 317, losses 339, draws 450. The point is not below -20, and the interval is not entirely below 0, so the brief's one look for a mistake was not triggered. prediction.txt said Elo -15, wrong outside -60..30. -6.91 is inside that band.

Partner verdict: CONFIRMS. Partner seat 088, fetched commit eef631a8c089500fd9e631db1cf60442813527b9. git apply --check printed ok (review_partner.sh). HONESTY_Q.txt on that build: 312866, 862329, 3024920, 4865609. cmp_partner_off_O.txt: differ 0 of 200 against exe B. cmp_partner_on_O.txt: differ 0 of 200 against their P_on_O_d12.rows, both sums 5896450. They claim that sum and 200 differences from the plain engine. My run of their switch on matches their rows. match_partner_R_result.txt is my match, not theirs: 600 games, Elo -11.59 +/- 9.95.

suspicions, not proven. In that 600-game log fastchess prints DrawRatio 85.00 % next to Draws: 54. 54/600 is not 85 percent. Finished-game lines are 600 and the PGN has 600 Event tags, so the game count stands. I do not know which ratio DrawRatio is.

what I did NOT do. I did not re-run seat 088's sanitizer build, their G-off search, or their 1106-game OG match. Step 4 asked for honesty, O off against exe B, O on against their rows, and a 600-game R match. I did not open a pull request. I did not change any branch except for-fable-and-opus/grok-038.

what I am NOT sure about. "One ply shallower" is implemented on top of the existing late-move reduction, not instead of it. A reading that replaced the child depth and left the reduction table out would search more nodes. The off path does not depend on that choice: IdeaA7 false never writes new_depth. Handoff branch handoff/fable-opus-combo29-all-20261114 was fetched at 2026-11-20T08:55:59Z (handoff_check_time.txt, commit 8c5536863464d4af8c07b4788883463eb950ab1d) and has no forge-combo29/soak_all/FABLE_TO_grok_<N>.md. Partner 088 was fetched again at that same time and was still eef631a8c089500fd9e631db1cf60442813527b9, the commit that was built.

times: see stamps.txt

git status --short

```
A  forge-combo29/grok/038/HONESTY_Q.meta
A  forge-combo29/grok/038/HONESTY_Q.txt
A  forge-combo29/grok/038/REPORT.md
A  forge-combo29/grok/038/RESULT.txt
A  forge-combo29/grok/038/cmp_partner_off_O.txt
A  forge-combo29/grok/038/cmp_partner_on_O.txt
A  forge-combo29/grok/038/handoff_check_time.txt
A  forge-combo29/grok/038/honesty_Q_bench11.meta
A  forge-combo29/grok/038/honesty_Q_bench11.txt
A  forge-combo29/grok/038/honesty_Q_bench13.meta
A  forge-combo29/grok/038/honesty_Q_bench13.txt
A  forge-combo29/grok/038/honesty_Q_bench16.meta
A  forge-combo29/grok/038/honesty_Q_bench16.txt
A  forge-combo29/grok/038/honesty_Q_perft5.meta
A  forge-combo29/grok/038/honesty_Q_perft5.txt
A  forge-combo29/grok/038/match_partner_R.meta
A  forge-combo29/grok/038/match_partner_R.pgn
A  forge-combo29/grok/038/match_partner_R.txt
A  forge-combo29/grok/038/match_partner_R_result.txt
A  forge-combo29/grok/038/partner_088_P_on_O_d12.rows
A  forge-combo29/grok/038/partner_088_fetch.txt
A  forge-combo29/grok/038/partner_088_idea.patch.txt
A  forge-combo29/grok/038/partner_088_ls.txt
A  forge-combo29/grok/038/partner_off_O_d12.meta
A  forge-combo29/grok/038/partner_off_O_d12.txt
A  forge-combo29/grok/038/partner_on_O_d12.meta
A  forge-combo29/grok/038/partner_on_O_d12.txt
A  forge-combo29/grok/038/review_partner.sh
A  forge-combo29/grok/038/run_partner_match.sh
M  forge-combo29/grok/038/stamps.txt
A  forge-combo29/grok/038/sum_partner_off_O.txt
A  forge-combo29/grok/038/sum_partner_on_O.txt
```

ls -la

```
total 10052
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:55 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      22 Nov 20 08:08 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1042 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  132793 Nov 20 08:06 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    1077 Nov 20 08:07 asan_trap.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:06 asan_trap_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu   11818 Nov 20 08:07 asan_trap.txt
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:04 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:04 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 08:04 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:46 cmp_partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:46 cmp_partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     686 Nov 20 08:04 compare_sums.py
-rw-r--r-- 1 ubuntu ubuntu    1182 Nov 20 08:04 design.txt
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 08:55 handoff_check_time.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 07:59 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 07:59 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 07:59 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 07:59 HONESTY_B.meta
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 07:59 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     573 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:02 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:02 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     200 Nov 20 08:02 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 08:02 HONESTY_P.meta
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:02 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     573 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:45 honesty_Q_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:45 honesty_Q_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:45 honesty_Q_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:45 honesty_Q_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:45 honesty_Q_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:45 honesty_Q_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 08:45 HONESTY_Q.meta
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 08:45 honesty_Q_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:45 honesty_Q_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     573 Nov 20 08:45 HONESTY_Q.txt
-rw-r--r-- 1 ubuntu ubuntu    2710 Nov 20 07:59 honesty_run.py
-rw-r--r-- 1 ubuntu ubuntu    5772 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1418 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     337 Nov 20 08:07 match_on_off.meta
-rw-r--r-- 1 ubuntu ubuntu 4717511 Nov 20 08:13 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu     353 Nov 20 08:16 match_on_off_result.txt
-rw-r--r-- 1 ubuntu ubuntu  134394 Nov 20 08:13 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu     360 Nov 20 08:46 match_partner_R.meta
-rw-r--r-- 1 ubuntu ubuntu 2017269 Nov 20 08:49 match_partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     356 Nov 20 08:49 match_partner_R_result.txt
-rw-r--r-- 1 ubuntu ubuntu   73178 Nov 20 08:49 match_partner_R.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     483 Nov 20 08:16 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:45 partner_088_fetch.txt
-rw-r--r-- 1 ubuntu ubuntu    5884 Nov 20 08:45 partner_088_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    3395 Nov 20 08:45 partner_088_ls.txt
-rw-r--r-- 1 ubuntu ubuntu   14751 Nov 20 08:45 partner_088_P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu     915 Nov 20 08:45 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  317818 Nov 20 08:46 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:46 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  306250 Nov 20 08:46 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:07 positions_asan_trap.fen
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 positions_G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 positions_G.epd
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 positions_O.fens
-rw-r--r-- 1 ubuntu ubuntu   19310 Nov 20 08:05 positions_R.fens
-rw-r--r-- 1 ubuntu ubuntu     597 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   13145 Nov 20 08:56 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 08:51 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1487 Nov 20 08:44 review_partner.sh
-rwxr-xr-x 1 ubuntu ubuntu    1251 Nov 20 08:05 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    2426 Nov 20 08:00 run_measured.py
-rwxr-xr-x 1 ubuntu ubuntu    1164 Nov 20 08:46 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:00 search_B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  565181 Nov 20 08:00 search_B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 08:00 search_B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  317762 Nov 20 08:00 search_B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     907 Nov 20 08:02 search_P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  565082 Nov 20 08:03 search_P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:02 search_P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  317642 Nov 20 08:02 search_P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     907 Nov 20 08:03 search_P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  304998 Nov 20 08:03 search_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    3622 Nov 20 07:59 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 08:56 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    3479 Nov 20 08:00 sum_B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1941 Nov 20 08:00 sum_B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1108 Nov 20 07:59 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1941 Nov 20 08:46 sum_partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1937 Nov 20 08:46 sum_partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    3479 Nov 20 08:03 sum_P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1941 Nov 20 08:03 sum_P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1934 Nov 20 08:03 sum_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:08 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:04 uci_P.sha
-rw-r--r-- 1 ubuntu ubuntu    5155 Nov 20 08:04 uci_P.txt
```
