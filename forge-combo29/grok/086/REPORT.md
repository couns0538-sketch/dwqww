IdeaA5 returns (eval + beta) / IdeaA5_Divisor from reverse futility instead of eval.
The check IdeaA5 defaults false, and the spin IdeaA5_Divisor defaults to 2 (range 2 to 8).
Off returns eval on the lock's condition. On returns that quotient, or beta if the quotient is below beta.

EXISTS: no. In the base, the reverse-futility block in forge-combo29/src/search.cpp returns eval. It does not blend toward beta.

Honesty, no setoption, fresh process each line, exe B and exe P. Both matched. Pasted from proof_summary.py for exe P, and HONESTY_B.txt ends ALL_OK with the same four expected counts:

```
honesty_P
  HONESTY_P_bench11.txt 312866 expected 312866 OK
  HONESTY_P_bench13.txt 862329 expected 862329 OK
  HONESTY_P_bench16.txt 3024920 expected 3024920 OK
  HONESTY_P_perft5.txt 4865609 expected 4865609 OK
```

Exe B's S14 depth-12 sums, from sum_nodes.py: O 9500069 (first three 41311 24872 28574), G 18466239.

Table from report_table.py:

```
step | status | evidence | result
1 seat | done | SEAT.txt | seat 086, idea 36, model Grok 4.7, 2026-11-20T07:55:16Z, token 22103662012805
2 honesty B | done | HONESTY_B.txt | ALL_OK
2 O depth 12 B | done | B_O_d12.nodes | off_O differ 0 of 200 sum 9500069
2 G depth 12 B | done | B_G_d12.nodes | off_G differ 0 of 353 sum 18466239
3 prediction | done | prediction.txt | pushed before any exe P search
3 patch applies | done | apply_check.txt | exit=0
3 proof off | done | P_off_O_d12.nodes P_off_G_d12.nodes | off_O differ 0 of 200 sum 9500069 ; off_G differ 0 of 353 sum 18466239
3 proof on | done | P_on_O_d12.nodes | on_O differ 200 of 200 sum 9272040
3 uci options | done | P_uci.txt | uci option name IdeaA5 type check default false
3 sanitizer | done | asan_G100_d10.raw asan_scratch.raw | asan_error_lines 0 ; scratch_heap 1
3 match | done | match_OG.out match_final.txt | Elo: 1.57 +/- 10.51, nElo: 3.06 +/- 20.48
4 partner | done | partner_compare.out partner_match_final.txt | partner_on_vs_claim positions 200 differ 0 equal 200 ; Games: 600, Wins: 249, Losses: 237, Draws: 114, Points: 306.0 (51.00 %)
5 report | done | REPORT.md RESULT.txt | this commit
```

Proofs, pasted from proof_summary.py:

```
off_O differ 0 of 200 sum 9500069
off_G differ 0 of 353 sum 18466239
on_O differ 200 of 200 sum 9272040
on_O first3 22956 27965 29723
uci option name IdeaA5 type check default false
uci option name IdeaA5_Divisor type spin default 2 min 2 max 8
apply_check
exit=0
base=6b98f2170a3210e71beed04bbd2553972c253ed7
asan_nm 35
asan_bestmoves 100
asan_error_lines 0
scratch_heap 1
scratch_nm 35
```

(1) Honesty on exe P, no setoption: the four counts above.
(2) S14, IdeaA5 false: O and G depth 12, position by position equal to exe B.
(3) S14, IdeaA5 true: 200 of 200 O positions differ. Sum 9272040. The predicted sum was 9650000, wrong outside 8700000 to 10500000, so the sum is inside the predicted range.
(4) uci lists both new options at those defaults.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaA5 true, first 100 of G at depth 10: 100 bestmove lines, 0 AddressSanitizer error lines, nm count of __asan_ symbols 35. The scratch copy (not in the patch) reads index 8 of a 4-int heap array on asan_probe.fen. The same uci_search.py runner recorded one heap-buffer-overflow line.

Match, pasted from extract_result.py on match_OG.out:

```
Results of IdeaA5on vs IdeaA5off (20000 nodes, 1t, 16MB, openings_OG.fens):
Elo: 1.57 +/- 10.51, nElo: 3.06 +/- 20.48
LOS: 61.53 %, DrawRatio: 60.94 %, PairsRatio: 1.04
Games: 1106, Wins: 348, Losses: 343, Draws: 415, Points: 555.5 (50.23 %)
Ptnml(0-2): [12, 94, 337, 97, 13], WL/DD Ratio: 2.01
--------------------------------------------------
Finished match
Total Time: 00:06:14 (hours:minutes:seconds)
```

Predicted Elo was +6, wrong outside -35 to +50. 1.57 is inside that range. The interval is not entirely below 0, and the point is not below -20, so I did not open the code for a second bug hunt.

Partner verdict: CONFIRMS. Partner seat 036. git apply --check on a fresh base exited 0, the build ran, honesty matched the four counts, IdeaS36 false matched exe B on all 200 O rows (sum 9500069), IdeaS36 true matched the partner's own O rows on all 200 (sum 9646880) and differed from exe B on 166, which is the count in their PROOFS.txt. Pasted from compare_nodes.py:

```
partner_off_vs_B positions 200 differ 0 equal 200
partner_on_vs_claim positions 200 differ 0 equal 200
partner_on_vs_B positions 200 differ 166 equal 34
```

Their switch, 300 R openings, both colours, pasted from extract_result.py on partner_match_R.out:

```
Results of on vs off (20000 nodes, 1t, 16MB, set_R.fens):
Elo: 6.95 +/- 6.77, nElo: 28.56 +/- 27.80
LOS: 97.80 %, DrawRatio: 89.00 %, PairsRatio: 2.00
Games: 600, Wins: 249, Losses: 237, Draws: 114, Points: 306.0 (51.00 %)
Ptnml(0-2): [0, 11, 267, 21, 1], WL/DD Ratio: 5.51
--------------------------------------------------
Finished match
Total Time: 00:01:30 (hours:minutes:seconds)
```

Seat 036's patch is IdeaS36 (list entry 26, a root quiet reduction shift), which is what their DESIGN.txt and idea.patch.txt contain. Idea 36 on the list is IdeaA5. Their node proofs are about the patch they wrote, and those proofs reproduced.

suspicions, not proven

The R match drew 89 percent of the games. The positions come from long random games. I did not show that the draw rate is because those positions are quiet.

what I did NOT do

I did not run G at depth 12 with IdeaA5 true. I did not try IdeaA5_Divisor at any value except the default 2. I did not run the sanitizer past the first 100 positions of G, and not at depth 12. I did not play my own patch on the R set, because seat 036 had a patch. I did not search the code for a bug after the match, because the Elo interval was not entirely below 0.

what I am NOT sure about

I am not sure the beta clamp ever changes a returned score at divisor 2. The lock's reverse-futility margin stays positive at the default spins, so the midpoint should already be above beta, but I did not count how often the clamp runs. I am not sure the +1.57 Elo is different from 0. The reported error is 10.51.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/086/stamps.txt
 M forge-combo29/grok/086/uci_search.py
?? forge-combo29/grok/086/REPORT.md
?? forge-combo29/grok/086/RESULT.txt
?? forge-combo29/grok/086/extract_result.py
?? forge-combo29/grok/086/handoff_60.txt
?? forge-combo29/grok/086/partner_HONESTY_B.txt
?? forge-combo29/grok/086/partner_HONESTY_B_bench11.meta
?? forge-combo29/grok/086/partner_HONESTY_B_bench11.txt
?? forge-combo29/grok/086/partner_HONESTY_B_bench13.meta
?? forge-combo29/grok/086/partner_HONESTY_B_bench13.txt
?? forge-combo29/grok/086/partner_HONESTY_B_bench16.meta
?? forge-combo29/grok/086/partner_HONESTY_B_bench16.txt
?? forge-combo29/grok/086/partner_HONESTY_B_perft5.meta
?? forge-combo29/grok/086/partner_HONESTY_B_perft5.txt
?? forge-combo29/grok/086/partner_HONESTY_B_uci.meta
?? forge-combo29/grok/086/partner_HONESTY_B_uci.txt
?? forge-combo29/grok/086/partner_compare.out
?? forge-combo29/grok/086/partner_exe.txt
?? forge-combo29/grok/086/partner_idea.patch.txt
?? forge-combo29/grok/086/partner_match.sh
?? forge-combo29/grok/086/partner_match_R.out
?? forge-combo29/grok/086/partner_match_R.pgn
?? forge-combo29/grok/086/partner_match_final.txt
?? forge-combo29/grok/086/partner_off_O.meta
?? forge-combo29/grok/086/partner_off_O.nodes
?? forge-combo29/grok/086/partner_off_O.raw
?? forge-combo29/grok/086/partner_on_O.meta
?? forge-combo29/grok/086/partner_on_O.nodes
?? forge-combo29/grok/086/partner_on_O.raw
?? forge-combo29/grok/086/partner_on_repro.nodes
?? forge-combo29/grok/086/partner_review.sh
?? forge-combo29/grok/086/proof_summary.out
?? forge-combo29/grok/086/report_table.out
?? forge-combo29/grok/086/report_table.py

$ ls -la forge-combo29/grok/086
total 9180
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:08 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     983 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  131576 Nov 20 08:07 asan_G100_d10.raw
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:07 asan_probe.fen
-rw-r--r-- 1 ubuntu ubuntu     402 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu   10260 Nov 20 08:07 asan_scratch.raw
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:02 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  549929 Nov 20 08:02 B_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:01 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309006 Nov 20 08:01 B_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1029 Nov 20 08:08 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu     490 Nov 20 09:16 extract_result.py
-rw-r--r-- 1 ubuntu ubuntu     108 Nov 20 08:56 handoff_60.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:01 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:01 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:01 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:01 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3027 Nov 20 08:01 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     742 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 08:01 HONESTY_B_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:01 HONESTY_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:03 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:03 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     230 Nov 20 08:03 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     232 Nov 20 08:03 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     742 Nov 20 08:03 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 08:03 HONESTY_P_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5036 Nov 20 08:03 HONESTY_P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    4569 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     992 Nov 20 08:02 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     594 Nov 20 08:13 match_final.py
-rw-r--r-- 1 ubuntu ubuntu     406 Nov 20 09:16 match_final.txt
-rw-r--r-- 1 ubuntu ubuntu  134631 Nov 20 08:12 match_OG.out
-rw-r--r-- 1 ubuntu ubuntu 4504082 Nov 20 08:12 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 openings_O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 openings_OG.fens
-rw-r--r-- 1 ubuntu ubuntu     301 Nov 20 09:15 partner_compare.out
-rw-r--r-- 1 ubuntu ubuntu      43 Nov 20 09:12 partner_exe.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:13 partner_HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:13 partner_HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:13 partner_HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:13 partner_HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:13 partner_HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:13 partner_HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:13 partner_HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:13 partner_HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     742 Nov 20 09:13 partner_HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 09:13 partner_HONESTY_B_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5099 Nov 20 09:13 partner_HONESTY_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7162 Nov 20 09:12 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     385 Nov 20 09:16 partner_match_final.txt
-rw-r--r-- 1 ubuntu ubuntu   54209 Nov 20 09:14 partner_match_R.out
-rw-r--r-- 1 ubuntu ubuntu 1416259 Nov 20 09:14 partner_match_R.pgn
-rwxr-xr-x 1 ubuntu ubuntu     920 Nov 20 09:13 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     900 Nov 20 09:12 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:12 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309069 Nov 20 09:12 partner_off_O.raw
-rw-r--r-- 1 ubuntu ubuntu     899 Nov 20 09:12 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:12 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  309438 Nov 20 09:12 partner_on_O.raw
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:12 partner_on_repro.nodes
-rwxr-xr-x 1 ubuntu ubuntu     997 Nov 20 08:42 partner_review.sh
-rw-r--r-- 1 ubuntu ubuntu     908 Nov 20 08:04 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:04 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  550073 Nov 20 08:04 P_off_G_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     914 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309131 Nov 20 08:04 P_off_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     913 Nov 20 08:04 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  309607 Nov 20 08:04 P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     785 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     601 Nov 20 09:15 proof_summary.out
-rw-r--r-- 1 ubuntu ubuntu    2468 Nov 20 08:08 proof_summary.py
-rw-r--r-- 1 ubuntu ubuntu    5036 Nov 20 08:05 P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7853 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    1168 Nov 20 09:16 report_table.out
-rw-r--r-- 1 ubuntu ubuntu    1805 Nov 20 09:16 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:16 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1013 Nov 20 08:05 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:06 set_G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu   14395 Nov 20 08:02 set_R.fens
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1645 Nov 20 08:01 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    4800 Nov 20 09:12 uci_search.py
```
