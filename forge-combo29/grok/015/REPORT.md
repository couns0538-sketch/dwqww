# Seat 015, idea 15, S6

IdeaS6 is an idle-piece reduction: UCI check IdeaS6 default false, and spin IdeaS6_Margin default 80 (0..1000 centipawns).
At a root that is not in check, and where no legal capture, promotion, or check gains more than that margin over the static evaluation, the friendly non-king piece whose removal changes the network evaluation the least is idle.
Quiet non-captures of that piece get reduction 0 for the rest of that search. The option-off path does not probe and does not change a reduction.

EXISTS: no. The plain engine has no idle-piece test and no reduction exemption for one chosen piece.

Honesty, fresh process, no setoption, exe B and exe P both:
bench 11 nodes 312866; bench 13 nodes 862329; bench 16 nodes 3024920; go perft 5 nodes 4865609.
Raw files: honesty_b_bench11.txt, honesty_b_bench13.txt, honesty_b_bench16.txt, honesty_b_perft5.txt, and the honesty_p_ names of the same four.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 015, idea 15, branch for-fable-and-opus/grok-015 |
| 2 honesty B | done | HONESTY_B.txt | four pins match |
| 3a read | done | decisions.txt | full S6 text, not the one-line summary |
| 3b prediction | done | prediction.txt | O sum 10500000, Elo +8; not edited after |
| 3c patch | done | idea.patch.txt, apply_check.txt | git apply --check OK |
| 3d proofs | done | nodes_compare.txt, uci_p.txt, asan_g100_d10.meta, asan_bug_special.txt | off identical; on 156 of 200; sanitizer clean and the witness fired |
| 3e match | done | match_stdout.txt, match.pgn | 1106 games, Elo -7.85 +/- 10.49 |
| 4 partner | done | partner_compare.txt, partner_match_stdout.txt | seat 065, CONFIRMS |
| handoff | done | (no file: the listing was empty) | no FABLE_TO_grok_N.md at step 1 or at minute 60 |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1), no setoption, exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

Proof (2), S14, IdeaS6 false. From nodes_compare.py:
O depth 12 off vs B | 200 | 0 | 9500069 | 9500069
G depth 12 off vs B | 353 | 0 | 18466239 | 18466239
Exe B alone, before the patch was trusted: O depth 12 sum 9500069, first three 41311 24872 28574; G depth 12 sum 18466239.

Proof (3), S14, IdeaS6 true, O depth 12: 156 of 200 positions differ from exe B. Sum 10340773 against 9500069. Prediction 10500000 is inside the stated band 9600000..14000000.

Proof (4), uci_p.txt: `option name IdeaS6 type check default false` and `option name IdeaS6_Margin type spin default 80 min 0 max 1000`.

Proof (5). AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS6 true, first 100 of G at depth 10: the transcript asan_g100_d10.txt has 0 sanitizer lines. asan_g100_d10.meta has nm_asan_count=35. The scratch copy, one heap read past the end of a 4-int array and only on the start FEN, run with the same depth_search.py, reports in asan_bug_special.txt: `runtime error: load of address ... with insufficient space for an object of type 'int'`.

Match, exe P IdeaS6 true vs exe P IdeaS6 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. fastchess stdout match_stdout.txt, 1106 games in match.pgn:
Elo: -7.85 +/- 10.49, nElo: -15.34 +/- 20.48
Games: 1106, Wins: 319, Losses: 344, Draws: 443, Points: 540.5 (48.87 %)
The point estimate is not below -20, and -7.85 +/- 10.49 reaches above 0, so the "look once for a mistake" rule did not apply. Predicted Elo +8 is inside the stated band -35..+50.

Partner is seat 065 (next idea-15 seat with a branch; 115 had none). The patch applies (partner_apply_check.txt). It is option IdeaS15, not IdeaS6: seat 065 built the rook-meets-passer reduction, and that is what was tested. Honesty pins match. Partner O depth 12, from partner_compare.py:
off vs B | 200 | 0 | 9500069 | 9500069
on vs B | 200 | 0 | 9500069 | 9500069
on vs partner published p_on_O_d12.tsv | 200 | 0 | 9500069 | 9500069
Their decisions.txt says O depth 12 with the switch on differs in 0 positions. That claim matches these rows. Verdict: CONFIRMS.
Their switch, 300 R openings, both colours, 600 games, partner_match_stdout.txt:
Elo: 1.74 +/- 4.68
Games: 600, Wins: 272, Losses: 269, Draws: 59, Points: 301.5 (50.25 %)
That match is a new measurement on R, not a repeat of their O+G match.

suspicions, not proven
Seat 065's idea index is 15, which is S6, and the patch on that branch is S15. The measurements of the patch they published are confirmed; the seat-to-idea mismatch is not a failed node comparison.
The true-side Elo -7.85 on 1106 games has an interval that crosses 0. Nothing in the games was checked by hand against the rules of chess.

what I did NOT do
No second match of my own patch on R, because 065 had a patch.
No re-search of the partner's G set. The required partner search was O.
No pull request. No engine source committed; the change is idea.patch.txt.
The quiet test is one ply of captures, promotions, and checks at the root, not a hash-writing search at every node, and the idle piece is chosen once per root rather than once per node.

what I am NOT sure about
"For one iteration" in S6 might have meant a single iterative-deepening depth. This build exempts the piece at every depth after one probe.
"Changes the evaluation least" is the smallest absolute change. A signed fall (the piece whose removal hurts the least, including a negative fall) could pick a different piece.
The partner Elo on R is not comparable to their published O+G Elo of +1.26, so that number was not checked.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/015/depth_search.py
 M forge-combo29/grok/015/stamps.txt
?? forge-combo29/grok/015/REPORT.md
?? forge-combo29/grok/015/RESULT.txt
?? forge-combo29/grok/015/apply_check.txt
?? forge-combo29/grok/015/partner_apply_check.txt
?? forge-combo29/grok/015/partner_compare.py
?? forge-combo29/grok/015/partner_compare.txt
?? forge-combo29/grok/015/partner_honesty_bench11.meta
?? forge-combo29/grok/015/partner_honesty_bench11.txt
?? forge-combo29/grok/015/partner_honesty_bench13.meta
?? forge-combo29/grok/015/partner_honesty_bench13.txt
?? forge-combo29/grok/015/partner_honesty_bench16.meta
?? forge-combo29/grok/015/partner_honesty_bench16.txt
?? forge-combo29/grok/015/partner_honesty_perft5.meta
?? forge-combo29/grok/015/partner_honesty_perft5.txt
?? forge-combo29/grok/015/partner_match.pgn
?? forge-combo29/grok/015/partner_match_stdout.txt
?? forge-combo29/grok/015/partner_o_off_d12.meta
?? forge-combo29/grok/015/partner_o_off_d12.nodes
?? forge-combo29/grok/015/partner_o_off_d12.txt
?? forge-combo29/grok/015/partner_o_on_d12.meta
?? forge-combo29/grok/015/partner_o_on_d12.nodes
?? forge-combo29/grok/015/partner_o_on_d12.txt
?? forge-combo29/grok/015/partner_published_o_on.nodes
?? forge-combo29/grok/015/run_partner_match.sh

$ ls -la forge-combo29/grok/015
total 9964
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      37 Nov 20 09:14 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:12 asan_bug_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     293 Nov 20 08:13 asan_bug_special.meta
-rw-r--r-- 1 ubuntu ubuntu    7781 Nov 20 08:13 asan_bug_special.txt
-rw-r--r-- 1 ubuntu ubuntu     947 Nov 20 08:11 asan_g100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     584 Nov 20 08:11 asan_g100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu  131395 Nov 20 08:11 asan_g100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:11 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:13 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu    1964 Nov 20 08:10 decisions.txt
-rwxr-xr-x 1 ubuntu ubuntu    5172 Nov 20 09:09 depth_search.py
-rw-r--r-- 1 ubuntu ubuntu     881 Nov 20 08:07 g_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:07 g_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  548098 Nov 20 08:07 g_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:11 g_first100.epd
-rw-r--r-- 1 ubuntu ubuntu     915 Nov 20 08:07 g_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:07 g_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  548152 Nov 20 08:07 g_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:06 g_set.epd
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     203 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    1271 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     396 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:09 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:09 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:09 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:09 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:09 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:09 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:09 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   11272 Nov 20 08:06 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1438 Nov 20 08:13 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 4748086 Nov 20 08:17 match.pgn
-rw-r--r-- 1 ubuntu ubuntu  152509 Nov 20 08:17 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     707 Nov 20 08:09 nodes_compare.py
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 08:09 nodes_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     887 Nov 20 08:07 o_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:07 o_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308066 Nov 20 08:07 o_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:06 o_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 openings_og.epd
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:07 o_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:07 o_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308174 Nov 20 08:07 o_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     920 Nov 20 08:07 o_p_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1207 Nov 20 08:07 o_p_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  310374 Nov 20 08:07 o_p_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:14 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     728 Nov 20 09:14 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 09:14 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:09 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:09 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 09:09 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 09:09 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu 2008416 Nov 20 09:12 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   80347 Nov 20 09:12 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 09:10 partner_o_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:10 partner_o_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308183 Nov 20 09:10 partner_o_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     920 Nov 20 09:10 partner_o_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:10 partner_o_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  308082 Nov 20 09:10 partner_o_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:10 partner_published_o_on.nodes
-rw-r--r-- 1 ubuntu ubuntu     466 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19284 Nov 20 08:13 r_300.epd
-rw-r--r-- 1 ubuntu ubuntu    6928 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:15 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1285 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1143 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     250 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5039 Nov 20 08:13 uci_p.txt
```
