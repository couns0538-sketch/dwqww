IdeaA6 is the negative extension the search already takes when a singular search fails high.
I added check option IdeaA6, default false, and spins IdeaA6_TtBeta default -2 and IdeaA6_Cut default -1.
With the check false the search uses the literals -2 and -1. With the check true it uses the spins. idea.patch.txt applies on the base with git apply --check.

EXISTS: forge-combo29/src/search.cpp:1951 (extension = -2 when tt_score >= beta) and forge-combo29/src/search.cpp:1953 (extension = -1 on a cut node). Those integers were not options. SingularDepth and SingularMargin already were.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Exe B, S14, depth 12: O sum 9500069, first three 41311 / 24872 / 28574. G sum 18466239.

The table is the output of step_table.py.

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 037, idea 37, model Grok 4.7, 2026-11-20T07:52:54Z, token 32115101828595
2 honesty B | done | HONESTY_B.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK
2 O and G sums | done | B_O_d12.meta | sum=9500069 first3=41311 / 24872 / 28574
2 G sum | done | B_G_d12.meta | sum=18466239
3 prediction | done | prediction.txt | O depth 12, S14, IdeaA6 true, IdeaA6_TtBeta -2, IdeaA6_Cut -1: sum 9500069. Proved wrong if that sum is not 9500069. Test match, switch true vs switch false, 1106 games, 20000 nodes: Elo 0.
3 patch applies | done | apply_check.txt | command: git -C /agent/repos/base apply --check /agent/repos/dwqww/forge-combo29/grok/037/idea.patch.txt | result: ok
3 proof 1 honesty P | done | HONESTY_P.txt | bench11 nodes 312866 expected 312866 OK | bench13 nodes 862329 expected 862329 OK | bench16 nodes 3024920 expected 3024920 OK | perft5 nodes 4865609 expected 4865609 OK
3 proof 2 off | done | compare_off_O.txt compare_off_G.txt | step	differ	n	same | off_O	0	200	200 || step	differ	n	same | off_G	0	353	353
3 proof 3 on | done | compare_on_O.txt | step	differ	n	same | on_O	0	200	200
3 proof 3 wiring | done | compare_on_zero_O.txt | step	differ	n	same | on_zero_O	200	200	0 | pos	1	41311	23979 | pos	2	24872	35701 | pos	3	28574	52558 | pos	4	27838	61802 | pos	5	18020	25370 | pos	6	43043	44342 | pos	7	56414	82796 | pos	8	32317	74924 | pos	9	37995	47270 | pos	10	53959	58337 | pos	11	26257	53198 | pos	12	58746	51711 | pos	13	30949	51730 | pos	14	34274	41288 | pos	15	21125	41120 | pos	16	51393	61143 | pos	17	71168	85277 | pos	18	50554	58225 | pos	19	52621	39547 | pos	20	38831	67520
3 proof 4 uci | done | uci_options_table.txt | option	present | option name IdeaA6 type check default false	yes | option name IdeaA6_TtBeta type spin default -2 min -8 max 2	yes | option name IdeaA6_Cut type spin default -1 min -8 max 2	yes
3 proof 5 sanitizer | done | asan_G100_d10.meta asan_scratch.meta | nm_asan_count=35 sanitizer_lines=0 || nm_asan_count=35 sanitizer_lines=3 ==6517==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000a0 at pc 0x5588816d72d3 bp 0x7ffcbaa331f0 sp 0x7ffcbaa331e0 SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/scratch-engine/src/board.cpp:232 in forge::Board::set_fen(std::basic_string_view<char, std::char_traits<char> >, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >*)
3 match | done | match_elo.txt | Results of on vs off (20000 nodes, 1t, 16MB, openings_OG.epd): | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan | LOS: -nan %, DrawRatio: 100.00 %, PairsRatio: -nan | Games: 1106, Wins: 336, Losses: 336, Draws: 434, Points: 553.0 (50.00 %) | Ptnml(0-2): [0, 0, 553, 0, 0], WL/DD Ratio: 1.55 | -------------------------------------------------- | Finished match
4 partner | done | partner_compare_off.txt partner_compare_on.txt match_partner_elo.txt | label	off_vs_B | left_n	200 | right_n	200 | compared	200 | differ	0 || label	on_vs_their_rows | left_n	200 | right_n	200 | compared	200 | differ	0
```

Proof (1). HONESTY_P.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

Proof (2). compare_off_O.txt: off_O differ 0 of 200. compare_off_G.txt: off_G differ 0 of 353. Both against exe B's rows.

Proof (3). compare_on_O.txt: on_O differ 0 of 200 at IdeaA6 true and the default spins. That is the same tree, because the defaults are the literals. compare_on_zero_O.txt: IdeaA6 true with both spins set to 0 differs in 200 of 200 (sum 11912888). The option runs.

Proof (4). uci_options_table.txt: IdeaA6 check default false, IdeaA6_TtBeta spin default -2 min -8 max 2, IdeaA6_Cut spin default -1 min -8 max 2.

Proof (5). asan_G100_d10.meta: nm_asan_count=35, sanitizer_lines=0, first 100 of G at depth 10, IdeaA6 true. asan_scratch.meta: the same runner on a scratch build reports AddressSanitizer heap-buffer-overflow in Board::set_fen, nm_asan_count=35.

Match. match_elo.txt: Elo -0.00 +/- 0.00, 1106 games, 336 wins, 336 losses, 434 draws, points 553.0. Ptnml(0-2) is [0, 0, 553, 0, 0]. The prediction was sum 9500069 and Elo 0. The sum was 9500069. The interval is 0 +/- 0, which is not entirely above +10 or entirely below -10.

Partner verdict: CONFIRMS. Seat 087, idea 37. partner_apply_check.txt exit 0. HONESTY_PARTNER.txt matches the four honesty numbers. partner_compare_off.txt: their switch false differs from exe B in 0 of 200 O depth-12 rows. partner_compare_on.txt: my run of their switch true differs from their published P_on_O rows in 0 of 200. match_partner_elo.txt: 600 games on my R book, Elo -0.00 +/- 0.00, 269 wins, 269 losses, 62 draws, Ptnml [0, 0, 300, 0, 0].

suspicions, not proven. fastchess prints nElo and LOS as nan on both matches. Every pair was an equal result, so the pentanomial variance is zero. I did not prove a second cause.

what I did NOT do. I did not rebuild seat 087's sanitizer binary or replay their 1106-game book. I did not run a second match of my own patch on R, because 087 already had idea.patch.txt. I did not change the official on test away from the default spins. The fastchess config.json in this folder is the one written by the partner match. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about. The spin limits are a choice. I am not sure a later training run wants these knobs, because the defaults reproduce today's search.

times: see stamps.txt

git status --short
 M forge-combo29/grok/037/stamps.txt
?? forge-combo29/grok/037/REPORT.md
?? forge-combo29/grok/037/RESULT.txt
?? forge-combo29/grok/037/step_table.py
?? forge-combo29/grok/037/step_table.txt

ls -la forge-combo29/grok/037
total 8712
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:14 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu     116 Nov 20 08:13 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     867 Nov 20 08:04 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131858 Nov 20 08:04 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:03 asan_runner.py
-rw-r--r-- 1 ubuntu ubuntu    1391 Nov 20 08:04 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10220 Nov 20 08:04 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     890 Nov 20 07:58 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 07:58 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  550253 Nov 20 07:58 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 07:58 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 07:58 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309187 Nov 20 07:58 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      35 Nov 20 08:01 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      35 Nov 20 08:01 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:01 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     410 Nov 20 08:01 compare_on_zero_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1038 Nov 20 08:01 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    6913 Nov 20 09:12 config.json
-rw-r--r-- 1 ubuntu ubuntu    1336 Nov 20 08:06 design.txt
-rw-r--r-- 1 ubuntu ubuntu     332 Nov 20 08:54 find_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 07:57 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:57 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 07:57 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 07:57 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 07:57 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 07:57 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     282 Nov 20 07:57 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5223 Nov 20 07:57 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    4259 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     251 Nov 20 09:08 HONESTY_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 09:08 HONESTY_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     251 Nov 20 09:09 HONESTY_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 09:09 HONESTY_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     253 Nov 20 09:09 HONESTY_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 09:09 HONESTY_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     285 Nov 20 09:09 HONESTY_PARTNER_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5386 Nov 20 09:09 HONESTY_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 09:09 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:00 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 08:00 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 08:00 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 08:00 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 08:00 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 08:00 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     282 Nov 20 08:00 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5384 Nov 20 08:00 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 08:00 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    4694 Nov 20 07:59 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     463 Nov 20 08:06 match_elo.py
-rw-r--r-- 1 ubuntu ubuntu     343 Nov 20 08:13 match_elo.txt
-rw-r--r-- 1 ubuntu ubuntu    5269 Nov 20 08:12 match_on_off.meta
-rw-r--r-- 1 ubuntu ubuntu 3481284 Nov 20 08:11 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  124724 Nov 20 08:12 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu     331 Nov 20 09:13 match_partner_elo.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 09:12 match_partner.meta
-rw-r--r-- 1 ubuntu ubuntu 1498048 Nov 20 09:12 match_partner.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1157 Nov 20 09:09 match_partner.sh
-rw-r--r-- 1 ubuntu ubuntu   63065 Nov 20 09:12 match_partner.txt
-rwxr-xr-x 1 ubuntu ubuntu    1236 Nov 20 08:03 match.sh
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:03 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:08 partner_087_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu    5068 Nov 20 09:08 partner_087.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:09 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 09:09 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:09 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu      59 Nov 20 09:09 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     814 Nov 20 09:09 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     929 Nov 20 09:09 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:09 partner_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  308998 Nov 20 09:09 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 09:09 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:09 partner_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  308990 Nov 20 09:09 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     924 Nov 20 08:00 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:00 P_off_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  550275 Nov 20 08:00 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     926 Nov 20 08:00 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:00 P_off_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309374 Nov 20 08:00 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     925 Nov 20 08:00 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:00 P_on_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  309402 Nov 20 08:00 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     997 Nov 20 08:00 P_on_zero_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14761 Nov 20 08:00 P_on_zero_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu  310121 Nov 20 08:00 P_on_zero_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     506 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    1748 Nov 20 08:43 proof_table.py
-rw-r--r-- 1 ubuntu ubuntu    1930 Nov 20 08:43 proof_table.txt
-rw-r--r-- 1 ubuntu ubuntu   19263 Nov 20 08:05 R.epd
-rw-r--r-- 1 ubuntu ubuntu    6703 Nov 20 09:14 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 09:14 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    5711 Nov 20 07:58 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:14 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    2618 Nov 20 09:14 step_table.py
-rw-r--r-- 1 ubuntu ubuntu    3183 Nov 20 09:14 step_table.txt
-rw-r--r-- 1 ubuntu ubuntu     889 Nov 20 08:01 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:01 uci_options_table.txt
-rw-r--r-- 1 ubuntu ubuntu    5102 Nov 20 08:01 uci_P.txt
