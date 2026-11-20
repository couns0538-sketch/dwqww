Idea S29 orders captures that already pass a fixed static-exchange gate by a history of the cheaper enemy piece attacking the landing square.
The check option is IdeaS29, default false. The spins are IdeaS29_Threshold default 0 and IdeaS29_Scale default 1.
With the check false the new term is not read, and the good/bad capture split stays see_ge(move, 0).

EXISTS: no. ThreatHistory in include/forge/search.hpp is a quiet-move table. Capture history is added to every capture and is not gated by a fixed exchange. See DECISIONS.txt.

Honesty, no setoption, from HONESTY_B.txt and HONESTY_P.txt:
exe B: bench 11 -> nodes 312866; bench 13 -> nodes 862329; bench 16 -> nodes 3024920; go perft 5 -> nodes 4865609
exe P: bench 11 -> nodes 312866; bench 13 -> nodes 862329; bench 16 -> nodes 3024920; go perft 5 -> nodes 4865609

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 023 idea 23
STEP 2 honesty | done | HONESTY_B.txt | bench 11 -> nodes 312866; bench 13 -> nodes 862329; bench 16 -> nodes 3024920; go perft 5 -> nodes 4865609
STEP 2 baseline | done | B_O_d12.rows B_G_d12.rows proof_compare.txt | O 9500069 and G 18466239
STEP 3 patch | done | idea.patch.txt apply_check_self.txt | git apply --check exit 0
STEP 3 proofs | done | proof_compare.txt asan_G100_d10.meta asan_scratch.txt | off 0 differ; on 200 of 200; sanitizer clean
STEP 3 match | done | match_OG.txt | Elo 3.14 +/- 10.38; games=1106 wins=343 losses=333 draws=430
STEP 4 partner | done | partner_073/ | CONFIRMS seat 073
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P:
(1) Honesty with no setoption: bench 11 -> nodes 312866; bench 13 -> nodes 862329; bench 16 -> nodes 3024920; go perft 5 -> nodes 4865609
(2) S14 and IdeaS29 false, position by position equal to exe B. From proof_compare.txt:
file=forge-combo29/grok/023/B_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
file=forge-combo29/grok/023/P_off_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
compared=200 differ=0 length_mismatch=False
file=forge-combo29/grok/023/B_G_d12.rows n=353 sum=18466239 first3=37203 70845 144383
file=forge-combo29/grok/023/P_off_G_d12.rows n=353 sum=18466239 first3=37203 70845 144383
compared=353 differ=0 length_mismatch=False
file=forge-combo29/grok/023/B_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
file=forge-combo29/grok/023/P_on_O_d12.rows n=200 sum=9540759 first3=27969 24392 28917
compared=200 differ=200 length_mismatch=False
file=forge-combo29/grok/023/P_on_O_d12.rows n=200 sum=9540759 first3=27969 24392 28917
(3) S14 and IdeaS29 true, O depth 12: 200 of 200 positions differ from exe B. Sum 9540759. First three 27969 24392 28917.
(4) uci lists `option name IdeaS29 type check default false`, `IdeaS29_Threshold type spin default 0 min -2000 max 2000`, `IdeaS29_Scale type spin default 1 min 0 max 32`. See HONESTY_P.txt.
(5) AddressSanitizer and UndefinedBehaviorSanitizer, IdeaS29 true, first 100 of G at depth 10. asan_symbol_count=35 sanitizer_lines=0. The scratch copy, one heap read past the end on scratch_fen.epd, run with the same harness_search.py, reported:
==5732==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000d0 at pc 0x55bf7a059f25 bp 0x7ffdd4900c70 sp 0x7ffdd4900c60

Match, exe P with IdeaS29 true against exe P with IdeaS29 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. From the last summary in match_OG.txt: Elo 3.14 +/- 10.38, games=1106 wins=343 losses=333 draws=430.

Partner is seat 073 (idea 23; seat 123 has no branch). Verdict: CONFIRMS.
git apply --check on a fresh base: patch=/agent/repos/dwqww/forge-combo29/grok/023/partner_073_idea.patch.txt
apply_check=yes
apply=yes
Honesty of that build: bench 11 -> nodes 312866; bench 13 -> nodes 862329; bench 16 -> nodes 3024920; go perft 5 -> nodes 4865609
Switch false versus exe B O depth 12:
file=/agent/repos/dwqww/forge-combo29/grok/023/B_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
file=/agent/repos/dwqww/forge-combo29/grok/023/partner_073/off_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
compared=200 differ=0 length_mismatch=False
Switch true versus seat 073's own O depth-12 rows (0 means the rows match):
file=forge-combo29/grok/023/partner_073_on_O.rows n=200 sum=9692566 first3=34858 26527 36306
file=forge-combo29/grok/023/partner_073/on_O_d12.rows n=200 sum=9692566 first3=34858 26527 36306
compared=200 differ=0 length_mismatch=False
Switch true versus exe B, which seat 073 reported as 199 of 200:
file=/agent/repos/dwqww/forge-combo29/grok/023/B_O_d12.rows n=200 sum=9500069 first3=41311 24872 28574
file=/agent/repos/dwqww/forge-combo29/grok/023/partner_073/on_O_d12.rows n=200 sum=9692566 first3=34858 26527 36306
compared=200 differ=199 length_mismatch=False
Their 1106-game O+G match was not replayed. The required 300 R openings, both colours, on their build: Elo 4.63 +/- 11.34, games=600 wins=267 losses=259 draws=74. See partner_073/match_R.txt.

suspicions, not proven
The safety term is added before the good/bad split, so a large history can change the order in which losing captures are deferred, not only the order of two captures that both passed the gate. Bishop and knight have the same SEE value; the lower piece type wins that tie, and I did not count how often the tie happens. Seat 073 divides the same history by 8 instead of adding it raw, and their O sum is 9692566 against my 9540759, so the weight changes the tree.

what I did NOT do
I did not replay seat 073's 1106-game match. I did not play a second R match of my own patch. I did not try any IdeaS29_Threshold except 0 or any IdeaS29_Scale except 1. The term is not added to in-check evasion ordering. No FABLE_TO_grok file was on the handoff branch at step 1 or at minute 60.

what I am NOT sure about
Whether +3.14 Elo at 20000 nodes on the built-in net would hold on the owner's net at a time control. The prediction file said 9350000 and +4 Elo, wrong outside 8000000..11000000 and wrong if the interval lay entirely below -25 or entirely above +35. The measured sum 9540759 and the interval 3.14 +/- 10.38 are inside those ranges. I am not sure a raw scale of 1 is better than seat 073's divisor of 8.

times: see stamps.txt

Own patch apply check (apply_check_self.txt): exit=0

git status --short

 M forge-combo29/grok/023/harness_search.py
 M forge-combo29/grok/023/run_match.sh
 M forge-combo29/grok/023/stamps.txt
?? forge-combo29/grok/023/REPORT.md
?? forge-combo29/grok/023/RESULT.txt
?? forge-combo29/grok/023/apply_check_self.txt
?? forge-combo29/grok/023/honesty_partner_073_bench11.meta
?? forge-combo29/grok/023/honesty_partner_073_bench11.txt
?? forge-combo29/grok/023/honesty_partner_073_bench13.meta
?? forge-combo29/grok/023/honesty_partner_073_bench13.txt
?? forge-combo29/grok/023/honesty_partner_073_bench16.meta
?? forge-combo29/grok/023/honesty_partner_073_bench16.txt
?? forge-combo29/grok/023/honesty_partner_073_perft5.meta
?? forge-combo29/grok/023/honesty_partner_073_perft5.txt
?? forge-combo29/grok/023/make_report.py
?? forge-combo29/grok/023/partner_073/
?? forge-combo29/grok/023/partner_073_idea.patch.txt
?? forge-combo29/grok/023/partner_073_on_O.rows
?? forge-combo29/grok/023/run_partner.sh

ls -la

total 3768
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 09:15 apply_check_self.txt
-rw-r--r-- 1 ubuntu ubuntu    1134 Nov 20 08:08 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     583 Nov 20 08:08 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  131991 Nov 20 08:08 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:11 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu   10371 Nov 20 08:08 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     964 Nov 20 08:04 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:04 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550468 Nov 20 08:04 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     968 Nov 20 08:04 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:04 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309312 Nov 20 08:04 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     974 Nov 20 08:02 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1393 Nov 20 08:10 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    1744 Nov 20 08:01 harness_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    7080 Nov 20 09:09 harness_search.py
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   20348 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:11 honesty_partner_073_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 09:11 honesty_partner_073_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:11 honesty_partner_073_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 09:11 honesty_partner_073_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:11 honesty_partner_073_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 09:11 honesty_partner_073_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:11 honesty_partner_073_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5380 Nov 20 09:11 honesty_partner_073_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 08:05 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5167 Nov 20 08:05 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 08:05 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:05 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5380 Nov 20 08:05 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   21040 Nov 20 08:05 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   11281 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     789 Nov 20 08:07 make_match_book.py
-rw-r--r-- 1 ubuntu ubuntu    6695 Nov 20 09:16 make_report.py
-rw-r--r-- 1 ubuntu ubuntu    1578 Nov 20 08:01 make_r.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 match_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    7359 Nov 20 08:17 match_OG.fastchess.json
-rw-r--r-- 1 ubuntu ubuntu 1073831 Nov 20 08:17 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu  141520 Nov 20 08:17 match_OG.txt
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:11 partner_073
-rw-r--r-- 1 ubuntu ubuntu   12253 Nov 20 09:10 partner_073_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1203 Nov 20 09:10 partner_073_on_O.rows
-rw-r--r-- 1 ubuntu ubuntu    1097 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:05 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550405 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1101 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:05 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309370 Nov 20 08:05 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1099 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1201 Nov 20 08:05 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  309344 Nov 20 08:05 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     521 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     740 Nov 20 08:10 proof_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    6300 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19635 Nov 20 08:01 R.fens
-rw-r--r-- 1 ubuntu ubuntu     105 Nov 20 08:01 R.log
-rw-r--r-- 1 ubuntu ubuntu    1048 Nov 20 08:01 run_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    1062 Nov 20 08:05 run_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    1656 Nov 20 09:09 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1814 Nov 20 09:10 run_partner.sh
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     209 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1681 Nov 20 08:11 summarize.py

ls -la partner_073

total 1292
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 09:11 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 09:16 ..
-rw-r--r-- 1 ubuntu ubuntu    101 Nov 20 09:10 apply.txt
-rw-r--r-- 1 ubuntu ubuntu     47 Nov 20 09:11 build.txt
-rw-r--r-- 1 ubuntu ubuntu    264 Nov 20 09:11 compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu    265 Nov 20 09:11 compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    234 Nov 20 09:11 compare_on_vs_partner.txt
-rw-r--r-- 1 ubuntu ubuntu  21080 Nov 20 09:11 HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   7330 Nov 20 09:14 match_R.fastchess.json
-rw-r--r-- 1 ubuntu ubuntu 542051 Nov 20 09:14 match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu  73045 Nov 20 09:14 match_R.txt
-rw-r--r-- 1 ubuntu ubuntu   1110 Nov 20 09:11 off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   1204 Nov 20 09:11 off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu 309208 Nov 20 09:11 off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   1108 Nov 20 09:11 on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   1203 Nov 20 09:11 on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu 309285 Nov 20 09:11 on_O_d12.txt
