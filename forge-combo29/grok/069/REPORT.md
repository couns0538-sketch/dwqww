# Seat 069, idea 19, S20

IdeaS20 is a UCI check, default false, plus spin IdeaS20_MinPly default 2. With the switch on, a surplus node (static eval already at the raised probcut bound) accepts only a non-losing tactical witness, and a gap node still requires the exchange to cover the whole gap. Quiescence may reject a try. Only a real search of at least 2 plies may cut. Principal-variation nodes and checks stay out, which the existing guard already did.

EXISTS: no. The plain engine has one probcut regime (see_ge of probcut_beta minus static eval, then a search at depth minus 4, which is 1 ply when depth is 5). That is not the two-regime witness. Recorded in design.txt.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. HONESTY_B.txt and HONESTY_P.txt both say all_ok true.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 069, idea 19, Grok 4.7 |
| 2 honesty B | done | HONESTY_B.txt | four numbers match |
| 2 known sums | done | B_O_known.txt, B_G_known.txt | O 9500069, first three 41311 / 24872 / 28574; G 18466239 |
| 3 patch | done | idea.patch.txt, apply_check.txt | apply_check_exit=0 on the base tree |
| 3 prediction | done | prediction.txt | committed alone before any exe P measurement |
| proof 1 | done | HONESTY_P.txt | same four numbers, no setoption |
| proof 2 | done | compare_off_O.txt, compare_off_G.txt | switch false, O and G identical to exe B |
| proof 3 | done | on_O_diff_counts.txt, P_on_O_known.txt | switch true, 194 of 200 differ, sum 9581616 |
| proof 4 | done | UCI_P.txt | IdeaS20 check default false; IdeaS20_MinPly spin default 2 min 2 max 8 |
| proof 5 | done | ASAN_G100.meta, ASAN_SCRATCH.stderr.txt | nm __asan_ count 35; clean stderr on 100 of G at depth 10; scratch heap-buffer-overflow |
| match | done | match_og.log, match_og.pgn | Elo 1.88 +/- 10.30, 1106 games |
| 4 partner | done | partner_off_vs_B.txt, partner_on_vs_theirs.txt, partner_match_R.log | seat 019, CONFIRMS; R match 600 games |

Proof (1). HONESTY_P.txt: bench 11 312866, bench 13 862329, bench 16 3024920, perft 5 4865609, all_ok true.

Proof (2). compare_off_O.txt: 200 positions, node_or_move_differ 0, identical yes, both sums 9500069. compare_off_G.txt: 353 positions, node_or_move_differ 0, identical yes, both sums 18466239. S14, IdeaS20 false, Threads 1, Hash 16.

Proof (3). on_O_diff_counts.txt: positions 200, node_differ 194, move_differ 18, same_nodes 6. P_on_O_known.txt: nodes_sum 9581616. The prediction said 10400000, wrong below 7000000 or above 14000000. 9581616 is inside that range.

Proof (4). UCI_P.txt contains `option name IdeaS20 type check default false` and `option name IdeaS20_MinPly type spin default 2 min 2 max 8`.

Proof (5). ASAN_G100.meta: nm_asan_count=35, failed empty, IdeaS20 true, first 100 of set_G.epd at depth 10, nodes_sum 2060490. ASAN_G100.stderr.txt is empty. The same depth_harness.py on the scratch exe and special_oob.fen wrote ASAN_SCRATCH.stderr.txt, which contains `ERROR: AddressSanitizer: heap-buffer-overflow` and `SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/bad-src/src/search.cpp:2168`. That scratch read is not in idea.patch.txt. nm_asan_count on the scratch exe is also 35.

Match. match_og.log, exe P versus exe P, S14, nodes 20000, openings_OG.epd (553 lines), rounds 553, games 2, concurrency 3: `Elo: 1.88 +/- 10.30`, Games 1106, Wins 345, Losses 339, Draws 422, Points 556.0. The prediction was +3, wrong below -40 or above +40. 1.88 is inside that range. The whole interval is not below 0, so the patch was not rewritten after the match. match_og.pgn has 1106 Event tags.

Partner. Next seat after 069 with this idea is 119, which had no branch at 2026-11-20T09:10:23Z. Wrap to 019, which had a branch and idea.patch.txt. partner_apply_check.txt: partner_apply_check_exit=0. HONESTY_PARTNER.txt: the four honesty numbers, all_ok true. partner_off_vs_B.txt: identical yes, sum 9500069. partner_on_vs_theirs.txt: identical yes to their Pon_O_d12.rows.tsv, sum 9452727, first three 36080, 24883, 28415. partner_on_vs_B.txt: node_differ 195. Their PROOF_NODES.txt claims off differ 0, on differ 195, sum 9452727, first three 36080 / 24883 / 28415. Those claims match. Their patch's switch is IdeaS20. partner_match_R.log, their exe, 300 lines of set_R.epd, both colours: `Elo: -1.16 +/- 7.36`, Games 600, Wins 279, Losses 281, Draws 40. Verdict: CONFIRMS.

suspicions, not proven. I did not split the node change into the 2-ply floor versus the non-losing SEE gate, so I cannot say which part moves the 194 positions. Their design leaves a band, when improving, where neither regime runs; mine treats static eval at or above the raised bound as surplus. Both are inside the idea's words at different cuts. I am not claiming one of those cuts is the mistake.

what I did NOT do. I did not open a pull request. I did not run G at depth 12 with my switch on. I did not replay their 1106-game OG match. I did not build their patch with the sanitizers. Seat 119 never appeared, so it was not reviewed. No FABLE_TO_grok file was on the handoff branch at STEP 1 or at minute 60 (handoff 8c5536863464d4af8c07b4788883463eb950ab1d).

what I am NOT sure about. fastchess prints DrawRatio 90.00% on the R match while the same line says 40 draws in 600 games. The pentanomial center is 270 of 300 pairs, which is 90%, so I read DrawRatio as that center and not as draws over games. A first OG match log was overwritten because the shell script changed while bash was still reading it; the committed match_og.log and match_og.pgn are the second run. I compared that pgn with the first by FEN and colour while the first file was still on disk, and every result matched. The first pgn is not in this folder. set_R.log says 0 games dropped: all 30 random games were still going at ply 80, so the drop rule did not fire.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/069/match.sh
 M forge-combo29/grok/069/stamps.txt
?? forge-combo29/grok/069/HONESTY_PARTNER.txt
?? forge-combo29/grok/069/HONESTY_PARTNER_bench11.txt
?? forge-combo29/grok/069/HONESTY_PARTNER_bench11.txt.meta
?? forge-combo29/grok/069/HONESTY_PARTNER_bench13.txt
?? forge-combo29/grok/069/HONESTY_PARTNER_bench13.txt.meta
?? forge-combo29/grok/069/HONESTY_PARTNER_bench16.txt
?? forge-combo29/grok/069/HONESTY_PARTNER_bench16.txt.meta
?? forge-combo29/grok/069/HONESTY_PARTNER_perft5.txt
?? forge-combo29/grok/069/HONESTY_PARTNER_perft5.txt.meta
?? forge-combo29/grok/069/PARTNER_off_O.meta
?? forge-combo29/grok/069/PARTNER_off_O.raw.txt
?? forge-combo29/grok/069/PARTNER_off_O.rows.tsv
?? forge-combo29/grok/069/PARTNER_off_O.stderr.txt
?? forge-combo29/grok/069/PARTNER_on_O.meta
?? forge-combo29/grok/069/PARTNER_on_O.raw.txt
?? forge-combo29/grok/069/PARTNER_on_O.rows.tsv
?? forge-combo29/grok/069/PARTNER_on_O.stderr.txt
?? forge-combo29/grok/069/REPORT.md
?? forge-combo29/grok/069/RESULT.txt
?? forge-combo29/grok/069/apply_check.txt
?? forge-combo29/grok/069/partner.patch.txt
?? forge-combo29/grok/069/partner_MATCH.txt
?? forge-combo29/grok/069/partner_PROOF_NODES.txt
?? forge-combo29/grok/069/partner_Pon_O_d12.rows.tsv
?? forge-combo29/grok/069/partner_apply_check.txt
?? forge-combo29/grok/069/partner_compare.py
?? forge-combo29/grok/069/partner_eval.sh
?? forge-combo29/grok/069/partner_match_R.cmd.txt
?? forge-combo29/grok/069/partner_match_R.log
?? forge-combo29/grok/069/partner_match_R.pgn
?? forge-combo29/grok/069/partner_off_vs_B.txt
?? forge-combo29/grok/069/partner_on_vs_B.txt
?? forge-combo29/grok/069/partner_on_vs_theirs.txt
?? forge-combo29/grok/069/partner_seat.txt

$ ls -la forge-combo29/grok/069
total 5252
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 08:24 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     608 Nov 20 08:06 asan_depth.sh
-rw-r--r-- 1 ubuntu ubuntu     884 Nov 20 08:06 ASAN_G100.meta
-rw-r--r-- 1 ubuntu ubuntu  131703 Nov 20 08:06 ASAN_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   20712 Nov 20 08:06 ASAN_G100.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 ASAN_G100.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     916 Nov 20 08:06 ASAN_SCRATCH.meta
-rw-r--r-- 1 ubuntu ubuntu    6221 Nov 20 08:06 ASAN_SCRATCH.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 08:06 ASAN_SCRATCH.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:06 ASAN_SCRATCH.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     770 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  550066 Nov 20 08:01 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   79058 Nov 20 08:01 B_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:01 B_G_d12.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:01 B_G_known.txt
-rw-r--r-- 1 ubuntu ubuntu     773 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309028 Nov 20 08:01 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   45839 Nov 20 08:01 B_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:01 B_O_d12.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 08:01 B_O_known.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 08:04 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:04 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1088 Nov 20 08:04 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1213 Nov 20 08:01 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu     740 Nov 20 08:08 count_diffs.py
-rw-r--r-- 1 ubuntu ubuntu    7064 Nov 20 08:04 depth_harness.py
-rw-r--r-- 1 ubuntu ubuntu    1798 Nov 20 08:08 design.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 first200.fens
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 07:59 HONESTY_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 07:59 HONESTY_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 07:59 HONESTY_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     261 Nov 20 07:59 HONESTY_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1778 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1879 Nov 20 08:02 honesty_check.sh
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 HONESTY_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     272 Nov 20 09:11 HONESTY_PARTNER_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 HONESTY_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     272 Nov 20 09:11 HONESTY_PARTNER_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 HONESTY_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     272 Nov 20 09:11 HONESTY_PARTNER_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 HONESTY_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     273 Nov 20 09:11 HONESTY_PARTNER_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:11 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:02 HONESTY_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:02 HONESTY_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:02 HONESTY_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     261 Nov 20 08:02 HONESTY_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7154 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     783 Nov 20 08:01 known_sums.py
-rw-r--r-- 1 ubuntu ubuntu    1656 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu      74 Nov 20 08:15 match_og.cmd.txt
-rw-r--r-- 1 ubuntu ubuntu  105891 Nov 20 08:21 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 1066313 Nov 20 08:23 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    1414 Nov 20 09:12 match.sh
-rw-r--r-- 1 ubuntu ubuntu      58 Nov 20 08:09 on_O_diff_counts.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu      27 Nov 20 09:11 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1356 Nov 20 09:11 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu    1936 Nov 20 08:24 partner_eval.sh
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:12 partner_match_R.cmd.txt
-rw-r--r-- 1 ubuntu ubuntu   52756 Nov 20 09:14 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu  428847 Nov 20 09:14 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     357 Nov 20 09:11 partner_MATCH.txt
-rw-r--r-- 1 ubuntu ubuntu     821 Nov 20 09:11 PARTNER_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309086 Nov 20 09:11 PARTNER_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   45837 Nov 20 09:11 PARTNER_off_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 PARTNER_off_O.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 09:11 partner_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     817 Nov 20 09:11 PARTNER_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  309147 Nov 20 09:11 PARTNER_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   45793 Nov 20 09:11 PARTNER_on_O.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 PARTNER_on_O.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     578 Nov 20 09:11 partner_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 09:11 partner_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu    7663 Nov 20 09:10 partner.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   15781 Nov 20 09:10 partner_Pon_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu     366 Nov 20 09:11 partner_PROOF_NODES.txt
-rw-r--r-- 1 ubuntu ubuntu       4 Nov 20 09:11 partner_seat.txt
-rw-r--r-- 1 ubuntu ubuntu     798 Nov 20 08:02 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  549688 Nov 20 08:02 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   79055 Nov 20 08:02 P_off_G_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 P_off_G_d12.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     801 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309204 Nov 20 08:02 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   45840 Nov 20 08:02 P_off_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 P_off_O_d12.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     797 Nov 20 08:02 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309273 Nov 20 08:02 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   45917 Nov 20 08:02 P_on_O_d12.rows.tsv
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 P_on_O_d12.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     103 Nov 20 08:04 P_on_O_known.txt
-rw-r--r-- 1 ubuntu ubuntu    1012 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    7763 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:04 set_G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu   19108 Nov 20 08:05 set_R.epd
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:05 set_R.log
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 special_oob.fen
-rw-r--r-- 1 ubuntu ubuntu     271 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1037 Nov 20 08:02 uci_options.sh
-rw-r--r-- 1 ubuntu ubuntu    5037 Nov 20 08:02 UCI_P.txt
-rw-r--r-- 1 ubuntu ubuntu     243 Nov 20 08:02 UCI_P.txt.meta
```
