# Seat 088, idea 38, IdeaA7

Once a non-mate score has raised alpha at a node of depth 2 to 12, each later move is searched one ply shallower, and not below 1 ply. The UCI switch is IdeaA7, default false. The spins are IdeaA7_MinDepth 2, IdeaA7_MaxDepth 12 and IdeaA7_Plies 1. With the switch false the flag stays false and new_depth is not written.

EXISTS: no. I read forge-combo29/src/search.cpp. Nothing there shortens the remaining moves after alpha rises. LmrDeeperShallower and HindsightDepth are other switches and they default off.

Honesty, no setoption, exe B, exe P, and the AddressSanitizer build: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Files HONESTY_B.txt, HONESTY_P.txt, HONESTY_ASAN.txt.

step | done / partly / not done | evidence file | result
--- | --- | --- | ---
1 seat | done | SEAT.txt, stamps.txt | seat 088, idea 38, IdeaA7
2 builds and known sums | done | HONESTY_B.txt, B_O_d12.sum, B_G_d12.sum | honesty exact; O sum 9500069 first3 41311 / 24872 / 28574; G sum 18466239
3 idea | done | idea.patch.txt, apply_check.txt, proof_off_O.txt, proof_off_G.txt, proof_on_O.txt, P_uci.txt, asan_G100.meta, asan_scratch.txt, match_og.elo.txt | apply check ok; off identical; on positions=200 differ=200 missing=0; O-on sum 5896450; sanitizer clean, trap reports; Elo 0.94 +/- 10.36 over 1106 games
4 partner 038 | done | partner_038_idea.patch.txt, partner_038_apply_check.txt, HONESTY_PARTNER.txt, partner_cmp_off_O.txt, partner_cmp_on_vs_claim.txt, partner_cmp_on_vs_B.txt, partner_R.elo.txt | CONFIRMS; off positions=200 differ=0 missing=0; on vs their rows positions=200 differ=0 claim_sum=5767895 mine_sum=5767895; on vs B positions=200 differ=200 missing=0; R match Elo 5.79 +/- 9.88 games 600
5 report | done | REPORT.md, RESULT.txt | this file

The table is the output of report_table.py.

Proof (1). HONESTY_P.txt: bench 11 got 312866, bench 13 got 862329, bench 16 got 3024920, perft 5 got 4865609.

Proof (2). proof_off_O.txt: positions 200, differ 0. proof_off_G.txt: positions 353, differ 0. Sums 9500069 and 18466239. S14 and IdeaA7 false.

Proof (3). proof_on_O.txt: positions 200, differ 200. P_on_O_d12.sum sum 5896450, first three 10632 / 13788 / 20264. prediction.txt said 7100000, wrong below 4000000 or above 9400000. 5896450 is inside that band. The code runs.

Proof (4). P_uci.txt lists `option name IdeaA7 type check default false`, `IdeaA7_MinDepth type spin default 2 min 1 max 64`, `IdeaA7_MaxDepth type spin default 12 min 1 max 64`, `IdeaA7_Plies type spin default 1 min 0 max 8`.

Proof (5). asan_G100.meta nm_asan_count=35. asan_G100.txt has 0 lines with AddressSanitizer or runtime error. First 100 of G, depth 10, IdeaA7 true. The same runner, measure_depth.py, on the scratch engine and asan_special.fen reports `runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'` at the inserted heap read in asan_scratch.txt. sanitizer=clean.

Match. match_og.elo.txt: Elo 0.94, err 10.36, games 1106. match_og.pgn has 1106 Event tags. The point is not below -20 and the interval is not entirely below 0, so the brief's one look for a mistake was not triggered. prediction.txt said Elo +6, wrong below -30 or above +40. 0.94 is inside that band.

Partner verdict: CONFIRMS. Partner is seat 038 (idea 38; seat 138 does not exist). Fetched for-fable-and-opus/grok-038 at 2026-11-20T09:11:43Z, commit e3a04dcaf7e46826b6fbf6c708cb589f50f344ff. Their idea.patch.txt applies on a fresh worktree of 6b98f2170 (`git apply --check` ok, partner_038_apply_check.txt). HONESTY_PARTNER.txt: 312866, 862329, 3024920, 4865609. partner_cmp_off_O.txt: differ 0 of 200 against exe B, sum 9500069. partner_cmp_on_vs_claim.txt: differ 0 of 200 against their sum_P_on_O_d12.txt, both sums 5767895. partner_cmp_on_vs_B.txt: differ 200 of 200. They claim off identical, on 200 of 200, and that sum. partner_R.elo.txt is my match of their switch, 300 R openings, both colours: Elo 5.79 +/- 9.88, 600 games, 600 Event tags in the PGN. Their RESULT.txt says elo=-6.91 err=9.96 games=1106 on their own OG match. My R match is a different opening set, so it does not contradict that claim.

suspicions, not proven. In partner_R.txt fastchess prints DrawRatio 84.67 % next to Draws: 72. 72/600 is 12 percent, not 84.67 percent. I do not know which ratio DrawRatio is. The same label appeared in their report. Game counts match the PGN.

what I did NOT do. I did not commit the fastchess engine logs (match_og.log was 406MB, partner_R.log was 175MB). A scan of each found 0 lines with unknown option, invalid value, illegal move, or invalid FEN. The host rejects a file over 100MB, so those logs are not in the commit. The stdout and the PGN are. I did not re-run seat 038's sanitizer. I did not open a pull request. I did not push any branch except for-fable-and-opus/grok-088. The handoff branch was fetched at STEP 1 and again at 2026-11-20T08:56:47Z. It has no forge-combo29/soak_all/FABLE_TO_grok_<N>.md. review_partner.sh failed once because it applied a relative patch after changing directory; the check that passed used the absolute path.

what I am NOT sure about. "One ply shallower" is applied on top of the existing late-move reduction, and I refuse to take the child below 1 ply so the late-move clamp stays defined. Seat 038 allows the child to enter quiescence. Their O-on sum is 5767895 and mine is 5896450. Both differ from the plain engine on all 200 positions. I am not sure which reading the owner wants. The off path does not depend on that choice. I also treated the root as a node, because the idea says "at a node".

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/088/run_match.sh
 M forge-combo29/grok/088/stamps.txt
?? forge-combo29/grok/088/HONESTY_PARTNER.txt
?? forge-combo29/grok/088/PARTNER_bench11.meta
?? forge-combo29/grok/088/PARTNER_bench11.txt
?? forge-combo29/grok/088/PARTNER_bench13.meta
?? forge-combo29/grok/088/PARTNER_bench13.txt
?? forge-combo29/grok/088/PARTNER_bench16.meta
?? forge-combo29/grok/088/PARTNER_bench16.txt
?? forge-combo29/grok/088/PARTNER_perft5.meta
?? forge-combo29/grok/088/PARTNER_perft5.txt
?? forge-combo29/grok/088/REPORT.md
?? forge-combo29/grok/088/RESULT.txt
?? forge-combo29/grok/088/partner_038_RESULT.txt
?? forge-combo29/grok/088/partner_038_apply_check.txt
?? forge-combo29/grok/088/partner_038_idea.patch.txt
?? forge-combo29/grok/088/partner_038_on_O.sum
?? forge-combo29/grok/088/partner_R.elo.txt
?? forge-combo29/grok/088/partner_R.pgn
?? forge-combo29/grok/088/partner_R.txt
?? forge-combo29/grok/088/partner_cmp_off_O.txt
?? forge-combo29/grok/088/partner_cmp_on_vs_B.txt
?? forge-combo29/grok/088/partner_cmp_on_vs_claim.txt
?? forge-combo29/grok/088/partner_off_O_d12.log
?? forge-combo29/grok/088/partner_off_O_d12.meta
?? forge-combo29/grok/088/partner_off_O_d12.rows
?? forge-combo29/grok/088/partner_off_O_d12.sum
?? forge-combo29/grok/088/partner_off_O_d12.txt
?? forge-combo29/grok/088/partner_on_O_d12.log
?? forge-combo29/grok/088/partner_on_O_d12.meta
?? forge-combo29/grok/088/partner_on_O_d12.rows
?? forge-combo29/grok/088/partner_on_O_d12.sum
?? forge-combo29/grok/088/partner_on_O_d12.txt
?? forge-combo29/grok/088/report_table.py
?? forge-combo29/grok/088/report_table.txt
?? forge-combo29/grok/088/review_partner.sh
```

ls -la

```
total 12768
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      87 Nov 20 08:16 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:17 ASAN_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:17 ASAN_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:17 ASAN_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:17 ASAN_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:17 ASAN_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:17 ASAN_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     889 Nov 20 08:06 asan_G100.log
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:06 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    5854 Nov 20 08:06 asan_G100.rows
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:06 asan_G100.sum
-rw-r--r-- 1 ubuntu ubuntu  239553 Nov 20 08:06 asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:17 ASAN_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:17 ASAN_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_scratch.log
-rw-r--r-- 1 ubuntu ubuntu      17 Nov 20 08:07 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    6915 Nov 20 08:07 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21121 Nov 20 08:01 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:01 B_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  925978 Nov 20 08:01 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     850 Nov 20 08:00 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14755 Nov 20 08:00 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:00 B_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  521993 Nov 20 08:00 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     861 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1542 Nov 20 08:08 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 G100.epd
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:17 HONESTY_ASAN.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:58 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:58 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2238 Nov 20 07:58 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     587 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     162 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1799 Nov 20 08:02 honesty_run.sh
-rw-r--r-- 1 ubuntu ubuntu    5884 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1306 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu      96 Nov 20 08:16 match_og.elo.txt
-rw-r--r-- 1 ubuntu ubuntu 4585219 Nov 20 08:15 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  151829 Nov 20 08:15 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu    5445 Nov 20 08:00 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     578 Nov 20 08:09 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 09:12 partner_038_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    5772 Nov 20 09:12 partner_038_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1934 Nov 20 09:12 partner_038_on_O.sum
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:12 partner_038_RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:12 PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:12 PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:12 PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 09:13 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 09:13 partner_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 09:13 partner_cmp_on_vs_claim.txt
-rw-r--r-- 1 ubuntu ubuntu    1940 Nov 20 09:13 partner_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     890 Nov 20 09:13 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14755 Nov 20 09:13 partner_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 09:13 partner_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  533527 Nov 20 09:13 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1933 Nov 20 09:12 partner_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     889 Nov 20 09:12 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14749 Nov 20 09:12 partner_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      54 Nov 20 09:12 partner_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  520794 Nov 20 09:12 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 09:12 PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      93 Nov 20 09:17 partner_R.elo.txt
-rw-r--r-- 1 ubuntu ubuntu 2109218 Nov 20 09:16 partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   78076 Nov 20 09:16 partner_R.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 08:02 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 08:02 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 08:02 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    3478 Nov 20 08:03 P_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:03 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21121 Nov 20 08:03 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:03 P_off_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  946891 Nov 20 08:03 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1940 Nov 20 08:03 P_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     884 Nov 20 08:03 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14755 Nov 20 08:03 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:03 P_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  533876 Nov 20 08:03 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1936 Nov 20 08:03 P_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     883 Nov 20 08:03 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14751 Nov 20 08:03 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:03 P_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  521905 Nov 20 08:03 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:02 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     899 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:03 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:03 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:03 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1134 Nov 20 08:09 proof_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     198 Nov 20 08:03 P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5157 Nov 20 08:03 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu       9 Nov 20 08:03 P_uci.txt.cmd
-rw-r--r-- 1 ubuntu ubuntu   19248 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu    5756 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2141 Nov 20 09:17 report_table.py
-rw-r--r-- 1 ubuntu ubuntu    1064 Nov 20 09:18 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     735 Nov 20 08:17 review_partner.sh
-rw-r--r-- 1 ubuntu ubuntu    1268 Nov 20 09:13 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu  717010 Nov 20 08:07 smoke.log
-rw-r--r-- 1 ubuntu ubuntu    8227 Nov 20 08:07 smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     672 Nov 20 08:07 smoke.txt
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    2772 Nov 20 08:09 summarize_proofs.py
```
