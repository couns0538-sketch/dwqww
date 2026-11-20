Idea S10 pulls a quiet non-PV score toward equality when four plies have been piece shuffles, the existing pawn-structure term and the eval are both at least 25 centipawns with the same sign, a one-ply probe that allows the ahead side only non-pawn non-captures stays within 40 centipawns, and the defender has a reverse shuffle or a repetition.
The check option is IdeaS10, default false. The spins are IdeaS10_Margin 25, IdeaS10_Flat 40, IdeaS10_Look 4, IdeaS10_Shrink 896 (kept fraction over 1024), and IdeaS10_Depth 5.
With the check false that block is not entered, so the search path is the one the plain engine already takes.

EXISTS: no. search.cpp uses the word shuffle only for an SIMD register permute. There is no fortress probe.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Files HONESTY_B.txt and HONESTY_P.txt.

The table is the output of proof_table.py:

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 081, idea 31, model Grok 4.7, 2026-11-20T07:55:08Z, token 15773208504359
2 honesty B | done | HONESTY_B.txt | exe B honesty | bench 11: 312866 | bench 13: 862329 | bench 16: 3024920 | perft 5: 4865609 | expected: 312866 862329 3024920 4865609
2 O depth 12 B | done | O_b_d12.sum.txt | file forge-combo29/grok/081/O_b_d12.nodes.txt | positions 200 | sum 9500069 | first3 41311 24872 28574
2 G depth 12 B | done | G_b_d12.sum.txt | file forge-combo29/grok/081/G_b_d12.nodes.txt | positions 353 | sum 18466239 | first3 37203 70845 144383
3 patch applies | done | idea.patch.txt | git apply --check on a fresh base of 6b98f2170 exited 0
3 proof 1 honesty P | done | HONESTY_P.txt | exe P honesty, no setoption | bench 11: 312866 | bench 13: 862329 | bench 16: 3024920 | perft 5: 4865609 | expected: 312866 862329 3024920 4865609
3 proof 2 off O | done | O_off_compare.txt | left forge-combo29/grok/081/O_b_d12.nodes.txt | right forge-combo29/grok/081/O_p_off_d12.nodes.txt | positions 200 200 | differ 0 of 200
3 proof 2 off G | done | G_off_compare.txt | left forge-combo29/grok/081/G_b_d12.nodes.txt | right forge-combo29/grok/081/G_p_off_d12.nodes.txt | positions 353 353 | differ 0 of 353
3 proof 3 on O | done | O_on_compare.txt | differ 10 of 200
3 proof 3 on sum | done | O_p_on_d12.sum.txt | file forge-combo29/grok/081/O_p_on_d12.nodes.txt | positions 200 | sum 9542904 | first3 41311 24872 28574
3 proof 4 uci | done | uci_p.txt | IdeaS10 check default false; five IdeaS10_ spins at their defaults
3 proof 5 sanitizer | done | asan_g100.sanitizer.txt | asan_symbol_lines 35 | sanitizer_lines 0
3 proof 5 scratch | done | asan_scratch.sanitizer.txt | asan_symbol_lines 35 | sanitizer_lines 1 | stopped: no readyok | /tmp/scratch-src/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
3 match | done | match_og.summary.txt | Elo: 6.91 +/- 8.69, nElo: 16.29 +/- 20.48 ; Games: 1106, Wins: 349, Losses: 327, Draws: 430, Points: 564.0 (50.99 %)
4 partner apply | done | partner_apply.txt | apply_check_exit 0
4 partner honesty | done | partner_honesty.txt | partner rebuild honesty, no setoption | bench 11: 312866 | bench 13: 862329 | bench 16: 3024920 | perft 5: 4865609 | expected: 312866 862329 3024920 4865609
4 partner off | done | partner_off_compare.txt | differ 0 of 200
4 partner on vs published | done | partner_on_compare.txt | differ 0 of 200
4 partner on vs B | done | partner_on_vs_b.txt | differ 195 of 200
4 partner R match | done | partner_match.summary.txt | Elo: -52.51 +/- 12.02, nElo: -123.41 +/- 27.80 ; Games: 600, Wins: 204, Losses: 294, Draws: 102, Points: 255.0 (42.50 %)
```

Proofs. (1) Exe P with no setoption matches the four honesty numbers above. (2) S14 and IdeaS10 false: O depth 12 differs in 0 of 200 positions from exe B, and G depth 12 differs in 0 of 353. (3) S14 and IdeaS10 true: O depth 12 sum 9542904, and 10 of 200 positions differ from exe B. (4) The uci listing in uci_p.txt contains `option name IdeaS10 type check default false` and the five spins IdeaS10_Margin 25, IdeaS10_Flat 40, IdeaS10_Look 4, IdeaS10_Shrink 896, IdeaS10_Depth 5. (5) The AddressSanitizer and UndefinedBehaviorSanitizer build has `nm -C | grep -c __asan_` = 35 in asan_g100.meta, and the first 100 of G at depth 10 with the switch true produced 0 sanitizer lines. The same runner on a scratch build with one deliberate read past the end of a four-int heap array, on the first G fen, reported `runtime error: load of address ... with insufficient space for an object of type 'int'` at the inserted line. idea.patch.txt does not contain that fault. `git apply --check` of idea.patch.txt on a fresh checkout of 6b98f2170 succeeded.

Match. Exe P with IdeaS10 true against exe P with IdeaS10 false, both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G, both colours, 1106 games, concurrency 3. From match_og.summary.txt: Elo 6.91 +/- 8.69, games 1106, wins 349, losses 327, draws 430. The interval crosses 0, so this is not a loss that required a second look at the code. fastchess's stdout is match_og.txt and the PGN is match_og.pgn.

Partner verdict: CONFIRMS. Seat 031, the previous seat with idea 31. `git apply --check` of their idea.patch.txt on a fresh base exited 0 (partner_apply.txt). Their rebuild's honesty numbers match. With IdeaS10 false, O depth 12 matches exe B in 0 of 200 positions. With IdeaS10 true, my rebuild's O depth-12 nodes match the rows they published in P_on_O_d12.nodes.txt in 0 of 200 positions, and those rows differ from exe B in 195 of 200, which is the count in their on_O_vs_B.txt. My own match of their switch on 300 R openings, both colours, 600 games, was Elo -52.51 +/- 12.02 (partner_match.summary.txt). Their published O+G match was about -100 Elo; I did not replay that book. The node proofs are what they claim.

suspicions, not proven. The +6.91 Elo may be noise. Their patch losing on my R set is consistent with the loss they already reported on O+G, and it is not a separate fault in the node counts. A score that only shuffles may still be a real advantage; shrinking it can throw away wins. I did not prove that the probe fires on fortresses rather than on ordinary quiet positions.

what I did NOT do. I did not run a second match of my own patch on R, because seat 031 had a patch. I did not replay their 1106-game O+G match. I did not build their patch with a sanitizer. I did not try spin values other than the defaults. I did not scale PV nodes. I did not open a pull request.

what I am NOT sure about. The pawn score I used is the hand-crafted pawn-structure term, tapered, not the network eval. The network is what the search returns. I am not sure that is the pawn score the idea meant, and the plain search does not keep a separate pawn number on the NNUE path. R positions are plies 8, 15, 22, ... from random games that were still going at ply 64; games that ended before then would have been dropped, and none did (R.meta.txt). I am not sure a different reading of "every 7 plies after ply 8" was intended.

times: see stamps.txt

git status --short

```
 M forge-combo29/grok/081/stamps.txt
?? config.json
?? forge-combo29/grok/081/REPORT.md
?? forge-combo29/grok/081/RESULT.txt
?? forge-combo29/grok/081/match_partner.sh
?? forge-combo29/grok/081/partner031_O_on.nodes.txt
?? forge-combo29/grok/081/partner_O_off.meta
?? forge-combo29/grok/081/partner_O_off.nodes.txt
?? forge-combo29/grok/081/partner_O_off.raw.txt
?? forge-combo29/grok/081/partner_O_on.meta
?? forge-combo29/grok/081/partner_O_on.nodes.txt
?? forge-combo29/grok/081/partner_O_on.raw.txt
?? forge-combo29/grok/081/partner_apply.txt
?? forge-combo29/grok/081/partner_bench11.meta
?? forge-combo29/grok/081/partner_bench11.txt
?? forge-combo29/grok/081/partner_bench13.meta
?? forge-combo29/grok/081/partner_bench13.txt
?? forge-combo29/grok/081/partner_bench16.meta
?? forge-combo29/grok/081/partner_bench16.txt
?? forge-combo29/grok/081/partner_compare.py
?? forge-combo29/grok/081/partner_honesty.sh
?? forge-combo29/grok/081/partner_honesty.txt
?? forge-combo29/grok/081/partner_match.pgn
?? forge-combo29/grok/081/partner_match.summary.txt
?? forge-combo29/grok/081/partner_match.txt
?? forge-combo29/grok/081/partner_off_compare.txt
?? forge-combo29/grok/081/partner_on_compare.txt
?? forge-combo29/grok/081/partner_on_vs_b.txt
?? forge-combo29/grok/081/partner_perft5.meta
?? forge-combo29/grok/081/partner_perft5.txt
?? forge-combo29/grok/081/partner_uci.txt
?? forge-combo29/grok/081/proof_table.py
?? forge-combo29/grok/081/proof_table.txt
```

ls -la forge-combo29/grok/081

```
total 8608
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu     885 Nov 20 08:14 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  136326 Nov 20 08:14 asan_g100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      39 Nov 20 08:14 asan_g100.sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:14 asan_g100.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     891 Nov 20 08:15 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    6791 Nov 20 08:15 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:15 asan_scratch.sanitizer.txt
-rw-r--r-- 1 ubuntu ubuntu    1100 Nov 20 08:15 asan_scratch.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:09 bench11_b.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 bench11_b.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:12 bench11_p.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:12 bench11_p.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:09 bench13_b.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 bench13_b.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:12 bench13_p.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:12 bench13_p.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:09 bench16_b.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:09 bench16_b.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:12 bench16_p.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:12 bench16_p.txt
-rw-r--r-- 1 ubuntu ubuntu     771 Nov 20 08:12 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1702 Nov 20 08:12 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     794 Nov 20 08:11 G_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:11 G_b_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  566514 Nov 20 08:11 G_b_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      99 Nov 20 08:11 G_b_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:16 G_off_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     829 Nov 20 08:12 G_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:12 G_p_off_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  567368 Nov 20 08:12 G_p_off_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     103 Nov 20 08:16 G_p_off_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1397 Nov 20 08:09 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     123 Nov 20 08:09 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1407 Nov 20 08:12 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     137 Nov 20 08:12 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   16833 Nov 20 08:11 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1313 Nov 20 08:27 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3652117 Nov 20 08:24 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    1399 Nov 20 08:17 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu     353 Nov 20 08:27 match_og.summary.txt
-rw-r--r-- 1 ubuntu ubuntu  119287 Nov 20 08:24 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu    1334 Nov 20 09:12 match_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     477 Nov 20 08:27 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu    5841 Nov 20 08:10 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu     794 Nov 20 08:11 O_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:11 O_b_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  318528 Nov 20 08:11 O_b_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      97 Nov 20 08:11 O_b_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:16 O_off_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     329 Nov 20 08:16 O_on_compare.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:16 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     829 Nov 20 08:12 O_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:12 O_p_off_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  319210 Nov 20 08:12 O_p_off_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     101 Nov 20 08:16 O_p_off_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     828 Nov 20 08:12 O_p_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:12 O_p_on_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  319417 Nov 20 08:12 O_p_on_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     100 Nov 20 08:16 O_p_on_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    2571 Nov 20 09:11 partner031_O_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 09:12 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:11 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:11 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:11 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1087 Nov 20 09:12 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu    1371 Nov 20 09:11 partner_honesty.sh
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 09:11 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu 1632599 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     346 Nov 20 09:17 partner_match.summary.txt
-rw-r--r-- 1 ubuntu ubuntu   61273 Nov 20 09:15 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     133 Nov 20 09:12 partner_off_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 09:12 partner_on_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     392 Nov 20 09:12 partner_on_vs_b.txt
-rw-r--r-- 1 ubuntu ubuntu     832 Nov 20 09:11 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:11 partner_O_off.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  319072 Nov 20 09:11 partner_O_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     831 Nov 20 09:12 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    1209 Nov 20 09:12 partner_O_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  309511 Nov 20 09:12 partner_O_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:11 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    5346 Nov 20 09:11 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:09 perft5_b.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:09 perft5_b.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:12 perft5_p.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:12 perft5_p.txt
-rw-r--r-- 1 ubuntu ubuntu     762 Nov 20 08:08 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    2706 Nov 20 09:17 proof_table.py
-rw-r--r-- 1 ubuntu ubuntu    2746 Nov 20 09:17 proof_table.txt
-rw-r--r-- 1 ubuntu ubuntu   19533 Nov 20 08:27 R.epd
-rw-r--r-- 1 ubuntu ubuntu    7160 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:27 R.meta.txt
-rw-r--r-- 1 ubuntu ubuntu    6251 Nov 20 08:13 sanitizer_runner.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     489 Nov 20 08:10 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:09 uci_b.txt
-rw-r--r-- 1 ubuntu ubuntu    5281 Nov 20 08:12 uci_p.txt
```
