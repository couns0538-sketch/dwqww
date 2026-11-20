# Seat 010, idea 10, S24

IdeaS24 is off by default. On a root fail the failing bound stays the returned score shifted by the current delta, and the other bound keeps an overlap back into the old window: none when recent root scores are steady, up to half the old width when their variance is high. The same rule is used on fail-high and fail-low.
Spins, used only while the check is on: IdeaS24_Samples 4, IdeaS24_Steady 16, IdeaS24_Swing 400. Variance is the integer mean of squared deviations from the integer mean. A bound that would sit on the score is pushed one centipawn past it, so the re-search can resolve.
While the check is false the fail-low still sets beta to the midpoint and the fail-high still leaves alpha where it was. `git apply --check` of idea.patch.txt on a clean copy of 6b98f2170 passed.

EXISTS: no. AspCappedReopen and AspArmLate are other aspiration options and stay off.

## Honesty

Exe B, no setoption, HONESTY_B.txt:

```
bench11 nodes 312866 expected 312866 PASS
bench13 nodes 862329 expected 862329 PASS
bench16 nodes 3024920 expected 3024920 PASS
perft5 nodes 4865609 expected 4865609 PASS
```

Exe P, no setoption, HONESTY_P.txt: the same four node counts, all PASS.

Known sums on exe B, S14, Threads 1, Hash 16: b_O_d12.sum is `positions 200 sum 9500069 first 41311 24872 28574` and b_G_d12.sum is `positions 353 sum 18466239 first 37203 70845 144383`.

## Steps

Pasted from `python3 report_table.py`:

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt | seat 010, idea 10, model Grok 4.7, 2026-11-20T07:52:07Z, token 7061179558594
STEP 2 honesty B | done | HONESTY_B.txt | bench11 nodes 312866 expected 312866 PASS ... perft5 nodes 4865609 expected 4865609 PASS
STEP 2 O depth 12 | done | b_O_d12.sum | positions 200 sum 9500069 first 41311 24872 28574
STEP 2 G depth 12 | done | b_G_d12.sum | positions 353 sum 18466239 first 37203 70845 144383
STEP 3 prediction | done | prediction.txt | O depth 12 sum, S14, Threads 1, Hash 16, IdeaS24 true: 11200000
proof 1 honesty P | done | HONESTY_P.txt | bench11 nodes 312866 expected 312866 PASS ... perft5 nodes 4865609 expected 4865609 PASS
proof 2 off O | done | proof_off_O.txt | left 200 right 200 compared 200 differ 0
proof 2 off G | done | proof_off_G.txt | left 353 right 353 compared 353 differ 0
proof 3 on O | done | proof_on_O.txt | left 200 right 200 compared 200 differ 129 | positions 200 sum 9569208 first 40604 42076 33776
proof 5 sanitizer | done | san_g100.meta | nm count 35 sanitizer_lines 0
match | done | match_on_vs_off.parse | elo -1.88 err 10.38 games 1106
STEP 4 off O | done | n060_proof_off_O.txt | left 200 right 200 compared 200 differ 0
STEP 4 off G | done | n060_proof_off_G.txt | left 353 right 353 compared 353 differ 0
STEP 4 on vs partner rows | done | n060_proof_on_O.txt | mine 200 theirs 200 compared 200 differ 0 | mine_sum 9785481 theirs_sum 9785481 | mine_first 40607 24995 49667 | theirs_first 40607 24995 49667
STEP 4 on vs B | done | n060_on_vs_B.txt | left 200 right 200 compared 200 differ 128
STEP 4 match R | done | n060_match_R.parse | elo 1.16 err 9.08 games 600
```

Proof 4, lines in p_bench11.txt saved as uci_mine.txt:

```
option name IdeaS24 type check default false
option name IdeaS24_Samples type spin default 4 min 2 max 16
option name IdeaS24_Steady type spin default 16 min 0 max 1000000
option name IdeaS24_Swing type spin default 400 min 1 max 1000000
```

## Proofs

(1) Honesty on exe P with no setoption: 312866, 862329, 3024920, 4865609.

(2) S14 and IdeaS24 false. O depth 12: differ 0 of 200, sum 9500069. G depth 12: differ 0 of 353, sum 18466239. Both match exe B.

(3) S14 and IdeaS24 true. O depth 12 sum 9569208. 129 of 200 positions differ from exe B.

(4) `uci` lists IdeaS24 default false and the three spins at 4, 16 and 400.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build. san_g100.meta: `nm -C` count of `__asan_` is 35. First 100 of G at depth 10 with the switch true: finished 100, sanitizer_lines 0. A scratch copy, not part of idea.patch.txt, reads one past a 4-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 1`. The same san_run.py reports `ERROR: AddressSanitizer: heap-buffer-overflow` in san_scratch.err. The first sanitizer build, before the one-centipawn push, reported a signed overflow in the delta update. That binary was not used for the proofs or the match.

Prediction, not edited: O sum 11200000, wrong below 8500000 or above 14500000. Measured 9569208, inside that range. Elo +3, wrong below -35 or above +45. Measured -1.88, inside that range.

## Match

Exe P with IdeaS24 true against exe P with IdeaS24 false. S14, Threads 1, Hash 16, nodes 20000. Openings O and G, both colours, 1106 games. fastchess from github.com/Disservin/fastchess, concurrency 3. parse_match.py on match_on_vs_off.txt: `elo -1.88 err 10.38 games 1106`. The printed result line is `Elo: -1.88 +/- 10.38`. The interval is not entirely below 0, and the point is not below -20, so there was no post-match bug hunt. Wins 328, losses 334, draws 444.

## Partner

Partner is seat 060 (idea 10). Seat 110 had no branch. Commit 2d13c26fe23e176eb1ded648d7ab4ddb905d660b. Their idea.patch.txt applied with `git apply --check` on a clean copy of 6b98f2170, then built with the same g++ Release recipe.

Their claims that this rebuild reproduced: honesty nodes 312866, 862329, 3024920, 4865609. Switch false, O depth 12, differ 0 of 200 against exe B, and G depth 12 differ 0 of 353. Switch true, O depth 12, differ 0 of 200 against their P_on_O_d12.tsv, sum 9785481, first 40607 24995 49667, and 128 of 200 differ from exe B. That is what they wrote.

A new match of their switch, my set_R.fen, 300 openings, both colours, 600 games: `elo 1.16 err 9.08 games 600`.

Verdict: CONFIRMS.

## Suspicions, not proven

The overflow on the first sanitizer build was a real loop: with overlap 0 the other bound sat on the score and the re-search failed the other way until delta overflowed. The one-centipawn push is the fix that is in idea.patch.txt. I did not keep the broken binary's O sum.

Seat 060 scales overlap by the integer standard deviation (swing default 32). This seat scales it by the integer variance (swing default 400). Both change the search. I do not know which reading of "swinging" is the stronger one. The two O sums are 9569208 and 9785481.

## What I did not do

I did not replay seat 060's 1106-game match. I did not build their patch under a sanitizer. I did not turn IdeaS24 on together with AspCappedReopen. I did not search the spin values. There was no FABLE_TO_grok file at step 1 or at minute 60. No pull request.

## What I am not sure about

Whether +/- 10.38 is two standard errors or another fastchess convention. I report the number the program printed. Whether a longer match would move the -1.88. The 1106-game interval includes both small gains and small losses.

times: see stamps.txt

## git status and ls
```
$ git status --short
 M forge-combo29/grok/010/stamps.txt
?? forge-combo29/grok/010/HONESTY_N060.txt
?? forge-combo29/grok/010/REPORT.md
?? forge-combo29/grok/010/RESULT.txt
?? forge-combo29/grok/010/compare_partner_rows.py
?? forge-combo29/grok/010/n060_bench11.err
?? forge-combo29/grok/010/n060_bench11.meta
?? forge-combo29/grok/010/n060_bench11.txt
?? forge-combo29/grok/010/n060_bench13.err
?? forge-combo29/grok/010/n060_bench13.meta
?? forge-combo29/grok/010/n060_bench13.txt
?? forge-combo29/grok/010/n060_bench16.err
?? forge-combo29/grok/010/n060_bench16.meta
?? forge-combo29/grok/010/n060_bench16.txt
?? forge-combo29/grok/010/n060_match_R.err
?? forge-combo29/grok/010/n060_match_R.parse
?? forge-combo29/grok/010/n060_match_R.pgn
?? forge-combo29/grok/010/n060_match_R.txt
?? forge-combo29/grok/010/n060_off_G_d12.err
?? forge-combo29/grok/010/n060_off_G_d12.meta
?? forge-combo29/grok/010/n060_off_G_d12.rows
?? forge-combo29/grok/010/n060_off_G_d12.sum
?? forge-combo29/grok/010/n060_off_G_d12.txt
?? forge-combo29/grok/010/n060_off_O_d12.err
?? forge-combo29/grok/010/n060_off_O_d12.meta
?? forge-combo29/grok/010/n060_off_O_d12.rows
?? forge-combo29/grok/010/n060_off_O_d12.sum
?? forge-combo29/grok/010/n060_off_O_d12.txt
?? forge-combo29/grok/010/n060_on_O_d12.err
?? forge-combo29/grok/010/n060_on_O_d12.meta
?? forge-combo29/grok/010/n060_on_O_d12.rows
?? forge-combo29/grok/010/n060_on_O_d12.sum
?? forge-combo29/grok/010/n060_on_O_d12.txt
?? forge-combo29/grok/010/n060_on_vs_B.txt
?? forge-combo29/grok/010/n060_perft5.err
?? forge-combo29/grok/010/n060_perft5.meta
?? forge-combo29/grok/010/n060_perft5.txt
?? forge-combo29/grok/010/n060_proof_off_G.txt
?? forge-combo29/grok/010/n060_proof_off_O.txt
?? forge-combo29/grok/010/n060_proof_on_O.txt
?? forge-combo29/grok/010/partner060.patch.txt
?? forge-combo29/grok/010/partner060_on_O.tsv
?? forge-combo29/grok/010/partner_match.sh
?? forge-combo29/grok/010/report_table.py
?? forge-combo29/grok/010/uci_mine.txt

$ ls -la forge-combo29/grok/010
total 10532
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 b_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:06 b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:06 b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 b_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:06 b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:06 b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 b_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:06 b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:06 b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 b_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     830 Nov 20 08:04 b_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    8822 Nov 20 08:04 b_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      57 Nov 20 08:04 b_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  508243 Nov 20 08:04 b_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 b_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     834 Nov 20 08:03 b_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4785 Nov 20 08:03 b_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      55 Nov 20 08:03 b_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  282178 Nov 20 08:03 b_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 b_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 08:06 b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:06 b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1024 Nov 20 09:08 compare_partner_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1045 Nov 20 08:05 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1641 Nov 20 08:10 design.txt
-rw-r--r-- 1 ubuntu ubuntu    2202 Nov 20 08:05 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu    4949 Nov 20 08:11 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     370 Nov 20 08:06 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     370 Nov 20 09:08 HONESTY_N060.txt
-rw-r--r-- 1 ubuntu ubuntu     370 Nov 20 08:11 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   10458 Nov 20 08:11 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:13 match_on_vs_off.err
-rw-r--r-- 1 ubuntu ubuntu      31 Nov 20 08:23 match_on_vs_off.parse
-rw-r--r-- 1 ubuntu ubuntu 4709486 Nov 20 08:20 match_on_vs_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  138926 Nov 20 08:21 match_on_vs_off.txt
-rw-r--r-- 1 ubuntu ubuntu    8004 Nov 20 08:03 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 n060_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:08 n060_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:08 n060_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 n060_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:08 n060_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 09:08 n060_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 n060_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 09:08 n060_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5163 Nov 20 09:08 n060_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 n060_match_R.err
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 09:14 n060_match_R.parse
-rw-r--r-- 1 ubuntu ubuntu 2224427 Nov 20 09:13 n060_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   70869 Nov 20 09:13 n060_match_R.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 n060_off_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 09:09 n060_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    8822 Nov 20 09:09 n060_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 09:09 n060_off_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  507636 Nov 20 09:09 n060_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 n060_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     875 Nov 20 09:09 n060_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4785 Nov 20 09:09 n060_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:09 n060_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  282075 Nov 20 09:09 n060_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:09 n060_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     874 Nov 20 09:09 n060_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4780 Nov 20 09:09 n060_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:09 n060_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  282485 Nov 20 09:09 n060_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     153 Nov 20 09:09 n060_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 n060_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:08 n060_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5374 Nov 20 09:08 n060_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:09 n060_proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:09 n060_proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     138 Nov 20 09:09 n060_proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:08 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     563 Nov 20 08:23 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    3523 Nov 20 09:08 partner060_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu    9596 Nov 20 09:08 partner060.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1262 Nov 20 09:09 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:11 p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5232 Nov 20 08:11 p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:11 p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5232 Nov 20 08:11 p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 08:11 p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5234 Nov 20 08:11 p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_off_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     865 Nov 20 08:11 p_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    8822 Nov 20 08:11 p_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      52 Nov 20 08:11 p_off_G_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  508770 Nov 20 08:11 p_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:11 p_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4785 Nov 20 08:11 p_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:11 p_off_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  282426 Nov 20 08:11 p_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     868 Nov 20 08:12 p_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    4781 Nov 20 08:12 p_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 08:12 p_on_O_d12.sum
-rw-r--r-- 1 ubuntu ubuntu  282888 Nov 20 08:12 p_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:11 p_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 08:11 p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5445 Nov 20 08:11 p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 08:13 proof_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 08:13 proof_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     154 Nov 20 08:13 proof_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    8962 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    2263 Nov 20 09:15 report_table.py
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:15 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1280 Nov 20 08:08 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:12 san_g100.err
-rw-r--r-- 1 ubuntu ubuntu     919 Nov 20 08:12 san_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  119130 Nov 20 08:12 san_g100.txt
-rw-r--r-- 1 ubuntu ubuntu    6339 Nov 20 08:09 san_run.py
-rw-r--r-- 1 ubuntu ubuntu    4063 Nov 20 08:12 san_scratch.err
-rw-r--r-- 1 ubuntu ubuntu    1553 Nov 20 08:12 san_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    5364 Nov 20 08:12 san_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:12 scratch_fen.fen
-rw-r--r-- 1 ubuntu ubuntu     494 Nov 20 08:13 scratch_note.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   19790 Nov 20 08:05 set_R.fen
-rw-r--r-- 1 ubuntu ubuntu     152 Nov 20 08:05 set_R.meta
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 09:15 uci_mine.txt
```
