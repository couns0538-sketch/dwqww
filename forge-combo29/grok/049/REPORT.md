# Seat 049, idea 49, IdeaK10

IdeaK10 searches a quiet hash move one ply deeper at depth 8 or more when the sum of the two continuation-history tables behind the node is at least 3072.
The check option defaults to false. IdeaK10_MinDepth (8) and IdeaK10_Threshold (3072) are read only while the check is on.
A move that already has a positive extension is left alone, so a singular or check extension is not stacked.

EXISTS: no. In search.cpp the only extensions are the singular block (extension 1 or 2, or a negative extension) and the SEE-non-losing check extension. Continuation history is added into quiet move ordering and late-move reduction. It does not add a ply.

## Honesty

Plain exe B, no setoption, from collect_honesty.py / HONESTY_B.txt:

```
bench 11	expect 312866	got 312866	ok
bench 13	expect 862329	got 862329	ok
bench 16	expect 3024920	got 3024920	ok
perft 5	expect 4865609	got 4865609	ok
```

The same four numbers came back from exe P with no setoption (honesty_p_bench11.txt, honesty_p_bench13.txt, honesty_p_bench16.txt, honesty_p_perft5.txt) and from the partner build (partner_bench11.txt, partner_bench13.txt, partner_bench16.txt, partner_perft5.txt).

Exe B, S14, Threads 1, Hash 16: O depth 12 sum 9500069, first three 41311 / 24872 / 28574. G depth 12 sum 18466239. Both match the known sums.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt stamps.txt | seat 049 idea 49 |
| 2 honesty and baseline | done | HONESTY_B.txt o_b_d12.nodes g_b_d12.nodes | benches match; O 9500069; G 18466239 |
| 3a read | done | design.txt | not already in the engine |
| 3b prediction | done | prediction.txt | committed before measuring exe P |
| 3c patch | done | idea.patch.txt | git apply --check passed on the base |
| 3d proofs | done | compare_nodes.txt uci_p.txt asan_g100_d10.meta asan_scratch.txt | off identical; on 200/200 differ; sanitizer clean and the scratch run reports |
| 3e match | done | match_og.txt match_og.pgn match_og_result.txt | 1106 games, Elo -13.20 +/- 10.98 |
| 4 partner | done | partner_compare.txt partner_match_result.txt partner_apply.txt | CONFIRMS |
| 5 report | done | REPORT.md RESULT.txt | this file |

## Proofs

(1) Exe P, no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

(2) Exe P, S14, IdeaK10 false. compare_nodes.py: O_off_vs_B positions 200 differ 0. G_off_vs_B positions 353 differ 0. Sums 9500069 and 18466239.

(3) Exe P, S14, IdeaK10 true, MinDepth 8, Threshold 3072. O depth 12: 200 of 200 positions differ from exe B. Sum 31066517. First five nodes 181328, 126578, 42602, 330995, 64015 against 41311, 24872, 28574, 27838, 18020.

(4) uci_p.txt lists `option name IdeaK10 type check default false`, `option name IdeaK10_MinDepth type spin default 8 min 1 max 64`, and `option name IdeaK10_Threshold type spin default 3072 min 0 max 32767`.

(5) AddressSanitizer + UndefinedBehaviorSanitizer build. asan_g100_d10.meta has asan_symbol_count=35. First 100 of G at depth 10 with the switch on: 100 positions, sum 3485759, no sanitizer line in asan_g100_d10.txt. The same harness on a scratch copy that reads one past a 4-int heap array on the FEN `8/8/8/8/8/8/8/4K2k w - - 0 1` printed `ERROR: AddressSanitizer: heap-buffer-overflow` (asan_scratch.txt). That exe also has asan_symbol_count=35.

## Match

extract_match.py on match_og.txt:

```
Results of IdeaK10on vs IdeaK10off (20000 nodes, 1t, 16MB, openings_OG.epd):
Elo: -13.20 +/- 10.98, nElo: -24.65 +/- 20.48
LOS: 0.91 %, DrawRatio: 58.95 %, PairsRatio: 0.76
Games: 1106, Wins: 329, Losses: 371, Draws: 406, Points: 532.0 (48.10 %)
Ptnml(0-2): [21, 108, 326, 88, 10], WL/DD Ratio: 2.10
```

PGN event count 1106 (match_og.pgn). The point estimate is -13.20, not below -20, so I did not open the code for a second bug hunt. The interval -24.18 to -2.22 lies below 0.

prediction.txt said O depth-12 sum 10400000, wrong outside 8000000..14000000. The measured sum 31066517 is outside that band. It said Elo +5, wrong if the whole interval lies below -25 or above +40. The measured interval does not meet that bar. The file was not edited.

## Partner

Partner is seat 099 (same idea, the next seat after 049). Commit 76b5c99ee80bbff19e2ea65c18afbbe49ded6981. Their patch applies with git apply --check (partner_apply.txt).

Their shipped default is IdeaK10_Threshold 12000. I built that patch and measured it with my harness.

compare_partner.py:

```
off_vs_B left 200 right 200 compared 200 differ 0 same 200
on_vs_partner_rows left 200 right 200 compared 200 differ 0 same 200
on_vs_B left 200 right 200 compared 200 differ 198 same 2
on_sum 16294055 partner_sum 16294055 B_sum 9500069
```

Their compare_off_O.txt says equal 200. Their compare_on_O.txt says differ 198. Both match. Honesty numbers match. Verdict: CONFIRMS.

Their own OG match (not replayed) is Elo -6.60 +/- 9.55 over 1106 games. My required partner match is 300 R openings, both colours, 600 games, their switch, threshold 12000:

```
Results of p099on vs p099off (20000 nodes, 1t, 16MB, R300.epd):
Elo: -7.53 +/- 10.56, nElo: -19.83 +/- 27.80
LOS: 8.10 %, DrawRatio: 79.00 %, PairsRatio: 0.66
Games: 600, Wins: 251, Losses: 264, Draws: 85, Points: 293.5 (48.92 %)
```

partner_match.pgn has 600 events.

## Suspicions, not proven

The on-switch depth-12 sum is about 3.27 times the baseline and every opening changed. A hit sets extension to one more than it was, including when it was 0, -1, or -2, so a run of quiet hash moves can keep a full extra ply. That is enough to explain the node growth without a second bug. The off switch matching exe B on all 553 positions is the evidence that the extra code is not on the default path.

Draws by threefold repetition and the fifty-move rule in both matches are legal endings. python-chess agrees those are game-overs. I am not calling them engine faults.

## What I did NOT do

I did not replay seat 099's 1106-game OG match. I did not run a sanitizer on their patch. I did not change Threshold after the 3.27x measurement. No forge-combo29/soak_all/FABLE_TO_grok file existed at step 1 or at minute 60. I did not open a pull request. I did not measure G at depth 12 with the switch on. I did not hunt for a code mistake after the match, because the Elo point was not below -20.

## What I am NOT sure about

I am not sure 3072 is a good bar for "very high". It is above one S14 history bonus (the cap is 2212) and it still fired on all 200 openings. I am not sure a fixed 20000-node match on the built-in net is the same sign the owner's net will give. I am not sure seat 099's file P_on_O_sum_t3000.txt still describes the rows file it names: that note quotes a 64848074 sum, while the rows file whose meta says threshold 12000 sums to 16294055, which is the file I reproduced.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok/049/harness_depth.py
 M forge-combo29/grok/049/stamps.txt
?? forge-combo29/grok/049/R300.epd
?? forge-combo29/grok/049/REPORT.md
?? forge-combo29/grok/049/RESULT.txt
?? forge-combo29/grok/049/compare_partner.py
?? forge-combo29/grok/049/partner099_on_O.rows.txt
?? forge-combo29/grok/049/partner_apply.txt
?? forge-combo29/grok/049/partner_bench11.meta
?? forge-combo29/grok/049/partner_bench11.txt
?? forge-combo29/grok/049/partner_bench13.meta
?? forge-combo29/grok/049/partner_bench13.txt
?? forge-combo29/grok/049/partner_bench16.meta
?? forge-combo29/grok/049/partner_bench16.txt
?? forge-combo29/grok/049/partner_compare.txt
?? forge-combo29/grok/049/partner_config.json
?? forge-combo29/grok/049/partner_match.nohup
?? forge-combo29/grok/049/partner_match.pgn
?? forge-combo29/grok/049/partner_match.txt
?? forge-combo29/grok/049/partner_match_result.txt
?? forge-combo29/grok/049/partner_off_O.log
?? forge-combo29/grok/049/partner_off_O.meta
?? forge-combo29/grok/049/partner_off_O.nodes
?? forge-combo29/grok/049/partner_off_O.txt
?? forge-combo29/grok/049/partner_on_O.log
?? forge-combo29/grok/049/partner_on_O.meta
?? forge-combo29/grok/049/partner_on_O.nodes
?? forge-combo29/grok/049/partner_on_O.txt
?? forge-combo29/grok/049/partner_perft5.meta
?? forge-combo29/grok/049/partner_perft5.txt
?? forge-combo29/grok/049/run_partner_match.sh

$ ls -la forge-combo29/grok/049
total 10632
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:17 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:06 asan_g100_d10.log
-rw-r--r-- 1 ubuntu ubuntu     928 Nov 20 08:06 asan_g100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:06 asan_g100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu  137157 Nov 20 08:06 asan_g100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:07 asan_scratch.log
-rw-r--r-- 1 ubuntu ubuntu     932 Nov 20 08:07 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_scratch.nodes
-rw-r--r-- 1 ubuntu ubuntu   10860 Nov 20 08:07 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu    1267 Nov 20 08:01 collect_honesty.py
-rw-r--r-- 1 ubuntu ubuntu    1354 Nov 20 08:04 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     283 Nov 20 08:05 compare_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu    1671 Nov 20 09:11 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    7226 Nov 20 09:17 config.json
-rw-r--r-- 1 ubuntu ubuntu    1105 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu     668 Nov 20 08:15 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu     786 Nov 20 08:01 g_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3453 Nov 20 08:01 g_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  565942 Nov 20 08:01 g_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    3453 Nov 20 08:03 g_p_off_d12.log
-rw-r--r-- 1 ubuntu ubuntu     905 Nov 20 08:03 g_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    3453 Nov 20 08:03 g_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  566579 Nov 20 08:03 g_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu    7110 Nov 20 09:10 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:00 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:00 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     350 Nov 20 08:01 HONESTY_B.txt
-rwxr-xr-x 1 ubuntu ubuntu     542 Nov 20 07:59 honesty_one.sh
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:02 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:02 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:02 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:02 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    5127 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1572 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    1651 Nov 20 08:13 match_og.nohup
-rw-r--r-- 1 ubuntu ubuntu 4721305 Nov 20 08:13 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     366 Nov 20 08:15 match_og_result.txt
-rw-r--r-- 1 ubuntu ubuntu  156545 Nov 20 08:13 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu    9691 Nov 20 08:05 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu     685 Nov 20 08:05 match_smoke.txt
-rw-r--r-- 1 ubuntu ubuntu     786 Nov 20 08:01 o_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1916 Nov 20 08:01 o_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  318093 Nov 20 08:01 o_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:05 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1916 Nov 20 08:02 o_p_off_d12.log
-rw-r--r-- 1 ubuntu ubuntu     905 Nov 20 08:02 o_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1916 Nov 20 08:02 o_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  318747 Nov 20 08:02 o_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    2050 Nov 20 08:03 o_p_on_d12.log
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:03 o_p_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2050 Nov 20 08:03 o_p_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  327490 Nov 20 08:03 o_p_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  211419 Nov 20 08:06 option_check.log
-rw-r--r-- 1 ubuntu ubuntu    3028 Nov 20 08:06 option_check.pgn
-rw-r--r-- 1 ubuntu ubuntu     653 Nov 20 08:06 option_check.txt
-rw-r--r-- 1 ubuntu ubuntu   15797 Nov 20 09:11 partner099_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:16 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 09:11 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 09:11 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 09:11 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     392 Nov 20 09:11 partner_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    7221 Nov 20 09:17 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu     973 Nov 20 09:14 partner_match.nohup
-rw-r--r-- 1 ubuntu ubuntu 2300247 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     348 Nov 20 09:16 partner_match_result.txt
-rw-r--r-- 1 ubuntu ubuntu   73989 Nov 20 09:14 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu    1916 Nov 20 09:11 partner_off_O.log
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 09:11 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1916 Nov 20 09:11 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318761 Nov 20 09:11 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1959 Nov 20 09:11 partner_on_O.log
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 09:11 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1959 Nov 20 09:11 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  322058 Nov 20 09:11 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:11 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     648 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19651 Nov 20 09:11 R300.epd
-rw-r--r-- 1 ubuntu ubuntu   15069 Nov 20 09:17 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     190 Nov 20 09:17 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   26231 Nov 20 08:05 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1394 Nov 20 08:05 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1171 Nov 20 09:11 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:07 scratch_fen.fen
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5109 Nov 20 08:02 uci_p.txt
```
