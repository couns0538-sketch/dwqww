Idea 35 (A4) puts capture history into the two capture SEE pruning thresholds: quiescence (`-QsSeeMargin`) and the main-search capture gate (`-SeeNoisyMultiplier * depth`).
The check option is IdeaA4, default false. The spins are IdeaA4_Divisor default 16 and IdeaA4_Clamp default 64. Positive history lowers the threshold; negative history raises it. Quiet checks are not adjusted.
The patch is forge-combo29/grok/035/idea.patch.txt. `git apply --check` on a fresh worktree of 6b98f2170a3210e71beed04bbd2553972c253ed7 printed EXIT:0 (apply_check.txt).

EXISTS: no. search.cpp still prunes those captures with the fixed margins when IdeaA4 is false.

Honesty, no setoption, fresh process each line. Script output:

```
line	expected	got	match
bench 11	312866	312866	yes
bench 13	862329	862329	yes
bench 16	3024920	3024920	yes
go perft 5	4865609	4865609	yes
ALL_MATCH	yes
```

That block is HONESTY_B.txt and, again, HONESTY_P.txt. Exe B S14 depth 12, from B_DEPTH12.txt: O sum 9500069 first3 41311 24872 28574; G sum 18466239.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt stamps.txt | seat 035 idea 35 |
| 2 honesty and known sums | done | HONESTY_B.txt B_DEPTH12.txt | bench/perft match; O 9500069; G 18466239 |
| 3a read | done | design.txt | two capture SEE gates, not already history-adjusted |
| 3b predict | done | prediction.txt | 9650000 and Elo +4, committed before measuring on |
| 3c patch | done | idea.patch.txt apply_check.txt | applies, EXIT:0 |
| 3d proofs | done | compare_off_O.txt compare_off_G.txt compare_on_O.txt uci_options_idea.txt san_g100.meta san_scratch.meta | off 0 differ; on 200 differ; options listed; sanitizer clean and scratch reports |
| 3e match | done | match_og_summary.txt | 1106 games, Elo -0.94 +/- 10.32 |
| 4 partner 085 | done | PARTNER_HONESTY.txt partner_compare_off.txt partner_compare_on.txt match_partner_summary.txt | proofs match their files; R match 600 games Elo 2.32 +/- 9.22 |
| 5 report | done | REPORT.md RESULT.txt | this file |

Proofs:

(1) Exe P with no setoption matches the four honesty numbers. HONESTY_P.txt ALL_MATCH yes.

(2) S14 and IdeaA4 false. compare_off_O.txt: O 200 positions, differ 0, both sums 9500069. compare_off_G.txt: G 353 positions, differ 0, both sums 18466239.

(3) S14 and IdeaA4 true. compare_on_O.txt: differ 200, same 0, on sum 9759675 against exe B 9500069. The code runs on every opening.

(4) uci_options_idea.txt:

```
option name IdeaA4 type check default false
option name IdeaA4_Divisor type spin default 16 min 1 max 256
option name IdeaA4_Clamp type spin default 64 min 0 max 512
```

(5) san_g100.meta: nm_asan_count 35, sanitizer_lines 0, 100 positions of G at depth 10, IdeaA4 true. san_scratch.meta: nm_asan_count 35, sanitizer_lines 1. The scratch line is a read of index 8 on a 4-int heap array, only in that copy, on FEN 8/8/8/8/8/8/8/K6k w - - 0 1. Same runner, san_run.py. scratch_note.txt.

Match, from match_og_summary.txt (parse_match.py on match_og.raw):

```
finished_games 1106
Elo: -0.94 +/- 10.32
Games: 1106, Wins: 334, Losses: 337, Draws: 435, Points: 551.5 (49.86 %)
```

Prediction was O sum 9650000 (wrong outside 8800000..10600000) and Elo +4 (wrong outside -20..+25). Measured sum 9759675 and Elo -0.94 are inside both ranges. The point is not below -20 and the interval is not entirely below 0, so I did not open the code for a second bug hunt.

Partner is seat 085, the next idea-35 seat with a branch. Verdict: CONFIRMS.

- partner_085_idea.patch.txt applies on a fresh base (CHECK_OK, APPLY_OK) and builds.
- PARTNER_HONESTY.txt ALL_MATCH yes, the numbers they claim in partner_085_HONESTY_P.txt.
- partner_compare_off.txt: their switch false versus exe B O rows, differ 0.
- partner_compare_on.txt: their switch true versus their own O_d12_P_on.nodes.txt, differ 0, both sums 9967809. They claimed differ 200 against the plain engine; reproducing their on file exactly agrees with that claim.
- Their switch, my 300 R openings, both colours, from match_partner_summary.txt: 600 games, Elo 2.32 +/- 9.22. That match is mine; they had not published an R match to compare.

Suspicions, not proven:

- All 200 openings changed node count with the switch on. That is a wide footprint for a shallow SEE tweak. Off is node-identical, so the extra nodes come from history moving the threshold during the search, not from a broken off path.
- The R match draw rate is 85%. Many sampled positions are late in random games. I did not show that this hides a loss.
- The scratch report is a UBSan "insufficient space" line, not an AddressSanitizer summary. The binary does contain __asan_ (count 35).

What I did NOT do:

- I did not build the patched engine during step 2. Exe P was built after the patch, then honesty-checked.
- I did not play a second R match of my own switch. Seat 085 had a patch, so the R match is theirs.
- I did not re-play their 1106-game OG match.
- I did not copy their scripts. measure_depth.py, partner_honesty.sh, and compare_partner.py are mine.
- No pull request. No engine source committed. No FABLE_TO_grok file existed at step 1 or at minute 60.

What I am NOT sure about:

- I treated the two capture thresholds as quiescence SEE and the main-search noisy SEE, and I left probcut's SEE test alone. Quiet checks in the noisy branch stay on the old threshold.
- Fastchess sends the S14 values, but I am not sure it sends them in the required order. The depth-12 proofs used measure_depth.py, which does send them in that order, with isready after each.
- R positions are ply 15, 22, 29, ... from random legal games with seed 3501. A game that ends before ply 15 is dropped. None were. "games that end are dropped" can be read more strictly; that reading would keep nothing, because every game ends.

times: see stamps.txt


```
 M forge-combo29/grok/035/config.json
 M forge-combo29/grok/035/stamps.txt
?? forge-combo29/grok/035/PARTNER_HONESTY.txt
?? forge-combo29/grok/035/REPORT.md
?? forge-combo29/grok/035/RESULT.txt
?? forge-combo29/grok/035/compare_partner.py
?? forge-combo29/grok/035/inputs/partner_off.txt
?? forge-combo29/grok/035/inputs/partner_on.txt
?? forge-combo29/grok/035/match_og_config.json
?? forge-combo29/grok/035/match_partner.meta
?? forge-combo29/grok/035/match_partner.pgn
?? forge-combo29/grok/035/match_partner.raw
?? forge-combo29/grok/035/match_partner.sh
?? forge-combo29/grok/035/match_partner_summary.txt
?? forge-combo29/grok/035/partner_085_HONESTY_P.txt
?? forge-combo29/grok/035/partner_085_O_on.nodes
?? forge-combo29/grok/035/partner_085_compare_O_off.txt
?? forge-combo29/grok/035/partner_085_compare_O_on.txt
?? forge-combo29/grok/035/partner_085_idea.patch.txt
?? forge-combo29/grok/035/partner_compare_off.txt
?? forge-combo29/grok/035/partner_compare_on.txt
?? forge-combo29/grok/035/partner_honesty.sh
?? forge-combo29/grok/035/partner_honesty_bench11.meta
?? forge-combo29/grok/035/partner_honesty_bench11.txt
?? forge-combo29/grok/035/partner_honesty_bench13.meta
?? forge-combo29/grok/035/partner_honesty_bench13.txt
?? forge-combo29/grok/035/partner_honesty_bench16.meta
?? forge-combo29/grok/035/partner_honesty_bench16.txt
?? forge-combo29/grok/035/partner_honesty_perft5.meta
?? forge-combo29/grok/035/partner_honesty_perft5.txt
?? forge-combo29/grok/035/partner_off_O_d12.meta
?? forge-combo29/grok/035/partner_off_O_d12.nodes
?? forge-combo29/grok/035/partner_off_O_d12.raw
?? forge-combo29/grok/035/partner_on_O_d12.meta
?? forge-combo29/grok/035/partner_on_O_d12.nodes
?? forge-combo29/grok/035/partner_on_O_d12.raw
```

```
total 8520
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 08:02 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     132 Nov 20 08:00 B_DEPTH12.txt
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 07:59 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 07:59 b_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  549719 Nov 20 07:59 b_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 07:59 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 07:59 b_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309116 Nov 20 07:59 b_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 08:02 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:03 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:03 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 08:03 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1002 Nov 20 09:09 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    7193 Nov 20 09:13 config.json
-rw-r--r-- 1 ubuntu ubuntu     959 Nov 20 08:02 design.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:58 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:58 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 07:58 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 07:58 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1940 Nov 20 07:58 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     169 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     171 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1940 Nov 20 08:02 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6037 Nov 20 08:01 idea.patch.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:09 inputs
-rw-r--r-- 1 ubuntu ubuntu    1199 Nov 20 08:02 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    7187 Nov 20 09:10 match_og_config.json
-rw-r--r-- 1 ubuntu ubuntu     302 Nov 20 08:04 match_og.meta
-rw-r--r-- 1 ubuntu ubuntu 3651441 Nov 20 08:11 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  124476 Nov 20 08:11 match_og.raw
-rw-r--r-- 1 ubuntu ubuntu    1607 Nov 20 08:04 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu     346 Nov 20 08:13 match_og_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     325 Nov 20 09:10 match_partner.meta
-rw-r--r-- 1 ubuntu ubuntu 1553079 Nov 20 09:13 match_partner.pgn
-rw-r--r-- 1 ubuntu ubuntu   65883 Nov 20 09:13 match_partner.raw
-rw-r--r-- 1 ubuntu ubuntu    1626 Nov 20 09:09 match_partner.sh
-rw-r--r-- 1 ubuntu ubuntu     344 Nov 20 09:14 match_partner_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    4937 Nov 20 07:59 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu     635 Nov 20 08:13 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 09:09 partner_085_compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     417 Nov 20 09:09 partner_085_compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     474 Nov 20 09:09 partner_085_HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    5733 Nov 20 09:09 partner_085_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   14761 Nov 20 09:09 partner_085_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 09:10 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 09:10 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 09:10 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 09:10 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 09:10 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:10 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1915 Nov 20 09:09 partner_honesty.sh
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 09:10 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     991 Nov 20 09:10 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:10 partner_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309324 Nov 20 09:10 partner_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     990 Nov 20 09:10 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14761 Nov 20 09:10 partner_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309307 Nov 20 09:10 partner_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     984 Nov 20 08:03 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:03 p_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  550354 Nov 20 08:03 p_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     987 Nov 20 08:03 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:03 p_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309430 Nov 20 08:03 p_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     986 Nov 20 08:03 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   14758 Nov 20 08:03 p_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309799 Nov 20 08:03 p_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     544 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    5843 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:14 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1002 Nov 20 08:06 san_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  131743 Nov 20 08:06 san_g100.raw
-rw-r--r-- 1 ubuntu ubuntu    4616 Nov 20 08:03 san_run.py
-rw-r--r-- 1 ubuntu ubuntu    1170 Nov 20 08:06 san_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    7435 Nov 20 08:06 san_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu     522 Nov 20 08:06 scratch_note.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     612 Nov 20 08:00 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:03 uci_options_idea.txt
-rw-r--r-- 1 ubuntu ubuntu     164 Nov 20 08:03 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 08:03 uci_options.raw
```
