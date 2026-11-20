# Seat 027, idea 27, S44

IdeaS44 is an extra static drop for a quiet hash move with elite history. The check option defaults to false. With it on, and only off the PV and out of check, the node returns its static eval when depth is at most IdeaS44_Depth (8), the eval is at least IdeaS44_Margin (48) centipawns per ply above beta and is not a mate score, the hash move is a non-capture non-promotion pseudo-legal move whose quiet history is at least IdeaS44_History (6000), and no cheaper enemy piece attacks a dearer piece of ours.
A capture hash move does not open this drop. The three numbers are spin options.
The patch is idea.patch.txt. `git apply --check` on a fresh checkout of 6b98f2170 printed exit 0 (apply_check.txt).

EXISTS: no. The plain engine's reverse futility in forge-combo29/src/search.cpp (base, the block at lines 1688-1692) returns eval from depth and margin alone. It does not ask for a quiet hash move, a history band, or the cheaper-attacker test.

## Honesty numbers

Exe B, no setoption, from HONESTY_B.txt:

```
bench 11 -> nodes 312866 expected 312866 match true
bench 13 -> nodes 862329 expected 862329 match true
bench 16 -> nodes 3024920 expected 3024920 match true
go perft 5 -> nodes 4865609 expected 4865609 match true
PASS
```

Exe B, S14, Threads 1, Hash 16, from b_O.meta and b_G.meta: O depth 12 sum 9500069 (first three 41311 / 24872 / 28574). G depth 12 sum 18466239. Both match the known sums.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 027 idea 27 |
| 2 honesty B | done | HONESTY_B.txt | PASS, four known node counts |
| 2 known sums | done | b_O.meta, b_G.meta | O 9500069, G 18466239 |
| 3 prediction | done | prediction.txt | pushed before any switch-on search |
| 3 patch | done | idea.patch.txt, apply_check.txt | apply --check exit 0 |
| 3 proof 1 | done | HONESTY_p.txt | PASS |
| 3 proof 2 | done | compare_off_O.txt, compare_off_G.txt | differ 0 and 0 |
| 3 proof 3 | done | compare_on_O.txt | 159 of 200, sum 9567212 |
| 3 proof 4 | done | options_p.txt | four options, defaults false / 8 / 48 / 6000 |
| 3 proof 5 | done | asan_g100.meta, scratch_overflow.sanlines | 0 lines, scratch reports the overflow |
| 3 match | done | match_s44.txt | Elo -2.20 +/- 10.65, 1106 games |
| 4 partner 077 | done | partner_compare_on.txt, partner_match.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Exe P, no setoption, HONESTY_p.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. PASS.

(2) S14 and IdeaS44 false. compare_off_O.txt: differ 0 of 200, both sums 9500069. compare_off_G.txt: differ 0 of 353, both sums 18466239.

(3) S14 and IdeaS44 true, O depth 12. compare_on_O.txt:

```
name=on_O
left=/agent/repos/dwqww/forge-combo29/grok/027/b_O.nodes n=200 sum=9500069
right=/agent/repos/dwqww/forge-combo29/grok/027/p_on_O.nodes n=200 sum=9567212
compared=200
differ=159
same_length=true
```

159 of 200 positions differ, so the new code runs. The sum is higher than exe B, not lower.

(4) uci listing, options_p.txt, from p_id.txt via show_options.py:

```
option name IdeaS44 type check default false
option name IdeaS44_Depth type spin default 8 min 0 max 15
option name IdeaS44_Margin type spin default 48 min 0 max 300
option name IdeaS44_History type spin default 6000 min 0 max 60000
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the idea. asan_g100.meta: nm_asan_symbols=35, sanitizer_lines=0, first 100 of G at depth 10, IdeaS44 true, status ok. The same runner on a scratch copy that reads past a 4-int heap array on the FEN 8/8/8/8/8/8/8/K6k w - - 0 1 wrote scratch_overflow.sanlines: runtime error plus `AddressSanitizer: heap-buffer-overflow` in apply_position. nm_asan_symbols=35 on that exe too.

## Match

Exe P with IdeaS44 true against exe P with IdeaS44 false. Both S14, Threads 1, Hash 16, 20000 nodes a move. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3. From match_s44.txt:

```
Results of s44on vs s44off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -2.20 +/- 10.65, nElo: -4.23 +/- 20.48
LOS: 34.28 %, DrawRatio: 63.83 %, PairsRatio: 0.90
Games: 1106, Wins: 332, Losses: 339, Draws: 435, Points: 549.5 (49.68 %)
Ptnml(0-2): [15, 90, 353, 77, 18], WL/DD Ratio: 1.63
```

The point is not below -20, and the interval is not entirely below 0. I did not open the search for a second bug hunt.

prediction.txt said O depth-12 sum 9200000, proved wrong outside 8200000 to 9500069. The measured sum is 9567212, so that prediction is wrong. It said Elo +4, proved wrong outside -30 to +35. The measured point -2.20 is inside that range. prediction.txt was not edited.

## Partner

Partner is seat 077 (same idea, the next seat after 027 that has a branch). Their patch applies (`partner_apply_check.txt`, exit 0). Their build's honesty is HONESTY_partner077.txt, PASS, the four known counts.

Switch false versus exe B, partner_compare_off.txt: differ 0 of 200, sum 9500069. They claim off_identical=yes.

Switch true versus their file P_O_d12_on.nodes, partner_compare_on.txt: both sums 8965644, differ 0 of 200. Versus exe B, partner_compare_on_vs_B.txt: differ 200 of 200. They claim on_differs=200 of 200.

A match of their switch, my 300 R openings, both colours, 600 games, from partner_match.txt:

```
Results of p077on vs p077off (20000 nodes, 1t, 16MB, R.fens):
Elo: -4.05 +/- 9.69, nElo: -11.63 +/- 27.80
LOS: 20.60 %, DrawRatio: 84.67 %, PairsRatio: 0.84
Games: 600, Wins: 266, Losses: 273, Draws: 61, Points: 296.5 (49.42 %)
Ptnml(0-2): [6, 19, 254, 18, 3], WL/DD Ratio: 20.17
```

Verdict: CONFIRMS. The proofs they state for apply, honesty, switch-off identity, and the switch-on O rows hold on this machine.

## Suspicions, not proven

The switch-on O sum rose by 67143 nodes. I suspect some returned evals changed a parent cutoff and the parent then searched more. I did not trace a position to show that.

## What I did NOT do

I did not run G at depth 12 with IdeaS44 true. I did not sweep the three spins. I did not rebuild the partner under a sanitizer. I did not replay their 1106-game match. The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 had no FABLE_TO_grok file, and neither did the fetch at step 1. I did not open a pull request.

## What I am NOT sure about

I am not sure 48 centipawns per ply and a history of 6000 are a useful scale. The match interval includes both a small loss and a small gain. I am not sure why the node total grew; the off path matching exe B only shows that the growth is tied to the option being on.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/027/stamps.txt
?? forge-combo29/grok/027/HONESTY_partner077.txt
?? forge-combo29/grok/027/REPORT.md
?? forge-combo29/grok/027/RESULT.txt
?? forge-combo29/grok/027/compare_partner_on.py
?? forge-combo29/grok/027/partner077_bench_11.meta
?? forge-combo29/grok/027/partner077_bench_11.txt
?? forge-combo29/grok/027/partner077_bench_13.meta
?? forge-combo29/grok/027/partner077_bench_13.txt
?? forge-combo29/grok/027/partner077_bench_16.meta
?? forge-combo29/grok/027/partner077_bench_16.txt
?? forge-combo29/grok/027/partner077_go_perft_5.meta
?? forge-combo29/grok/027/partner077_go_perft_5.txt
?? forge-combo29/grok/027/partner077_id.txt
?? forge-combo29/grok/027/partner_077.patch.txt
?? forge-combo29/grok/027/partner_apply_check.txt
?? forge-combo29/grok/027/partner_claimed_on_O.nodes
?? forge-combo29/grok/027/partner_compare_off.txt
?? forge-combo29/grok/027/partner_compare_on.txt
?? forge-combo29/grok/027/partner_compare_on_vs_B.txt
?? forge-combo29/grok/027/partner_match.pgn
?? forge-combo29/grok/027/partner_match.txt
?? forge-combo29/grok/027/partner_off_O.meta
?? forge-combo29/grok/027/partner_off_O.nodes
?? forge-combo29/grok/027/partner_off_O.txt
?? forge-combo29/grok/027/partner_on_O.meta
?? forge-combo29/grok/027/partner_on_O.nodes
?? forge-combo29/grok/027/partner_on_O.txt
?? forge-combo29/grok/027/run_partner_match.sh
```

## ls -la

```
total 8480
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 08:07 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     949 Nov 20 08:05 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 asan_g100.sanlines
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 asan_g100.stderr
-rw-r--r-- 1 ubuntu ubuntu  135881 Nov 20 08:05 asan_g100.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:02 b_G.meta
-rw-r--r-- 1 ubuntu ubuntu   27574 Nov 20 08:02 b_G.nodes
-rw-r--r-- 1 ubuntu ubuntu  566005 Nov 20 08:02 b_G.txt
-rw-r--r-- 1 ubuntu ubuntu     902 Nov 20 08:02 b_O.meta
-rw-r--r-- 1 ubuntu ubuntu   18248 Nov 20 08:02 b_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318507 Nov 20 08:02 b_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1159 Nov 20 08:03 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:07 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:07 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:07 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1174 Nov 20 09:10 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    1444 Nov 20 08:07 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 G.epd
-rw-r--r-- 1 ubuntu ubuntu     266 Nov 20 07:59 honesty_b_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     266 Nov 20 07:59 honesty_b_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     268 Nov 20 07:59 honesty_b_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 07:59 honesty_b_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_id.txt
-rw-r--r-- 1 ubuntu ubuntu     405 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     403 Nov 20 09:10 HONESTY_partner077.txt
-rw-r--r-- 1 ubuntu ubuntu     401 Nov 20 08:04 HONESTY_p.txt
-rw-r--r-- 1 ubuntu ubuntu    5587 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1721 Nov 20 08:00 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3468842 Nov 20 08:13 match_s44.pgn
-rw-r--r-- 1 ubuntu ubuntu  119081 Nov 20 08:13 match_s44.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     233 Nov 20 08:07 options_p.txt
-rw-r--r-- 1 ubuntu ubuntu     259 Nov 20 09:10 partner077_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner077_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     259 Nov 20 09:10 partner077_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:10 partner077_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     261 Nov 20 09:10 partner077_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:10 partner077_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:10 partner077_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:10 partner077_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    5165 Nov 20 09:10 partner077_id.txt
-rw-r--r-- 1 ubuntu ubuntu    5219 Nov 20 09:09 partner_077.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 09:10 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1893 Nov 20 09:09 partner_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:10 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:10 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     222 Nov 20 09:10 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu 1548389 Nov 20 09:13 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   62754 Nov 20 09:13 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     932 Nov 20 09:10 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   18248 Nov 20 09:10 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318636 Nov 20 09:10 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     931 Nov 20 09:10 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   18241 Nov 20 09:10 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318718 Nov 20 09:10 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     266 Nov 20 08:04 p_bench_11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 p_bench_11.txt
-rw-r--r-- 1 ubuntu ubuntu     266 Nov 20 08:04 p_bench_13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 p_bench_13.txt
-rw-r--r-- 1 ubuntu ubuntu     268 Nov 20 08:04 p_bench_16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 p_bench_16.txt
-rw-r--r-- 1 ubuntu ubuntu     270 Nov 20 08:04 p_go_perft_5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 p_go_perft_5.txt
-rw-r--r-- 1 ubuntu ubuntu    5166 Nov 20 08:04 p_id.txt
-rw-r--r-- 1 ubuntu ubuntu     941 Nov 20 08:04 p_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   27574 Nov 20 08:04 p_off_G.nodes
-rw-r--r-- 1 ubuntu ubuntu  566193 Nov 20 08:04 p_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     939 Nov 20 08:04 p_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   18248 Nov 20 08:04 p_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318808 Nov 20 08:04 p_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     938 Nov 20 08:04 p_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   18249 Nov 20 08:04 p_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  318463 Nov 20 08:04 p_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     613 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    6778 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19329 Nov 20 08:00 R.fens
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:00 R.meta
-rw-r--r-- 1 ubuntu ubuntu    3104 Nov 20 07:58 run_honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu    2994 Nov 20 08:03 run_honesty.py
-rwxr-xr-x 1 ubuntu ubuntu    1068 Nov 20 08:07 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu     943 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    4767 Nov 20 08:05 run_sanitizer.py
-rw-r--r-- 1 ubuntu ubuntu    7562 Nov 20 08:02 run_search.py
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu     972 Nov 20 08:06 scratch_overflow.meta
-rw-r--r-- 1 ubuntu ubuntu     397 Nov 20 08:06 scratch_overflow.sanlines
-rw-r--r-- 1 ubuntu ubuntu    3475 Nov 20 08:06 scratch_overflow.stderr
-rw-r--r-- 1 ubuntu ubuntu    6618 Nov 20 08:06 scratch_overflow.txt
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     642 Nov 20 08:04 show_options.py
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:14 stamps.txt
```
