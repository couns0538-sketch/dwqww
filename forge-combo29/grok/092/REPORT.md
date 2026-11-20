# Seat 092, idea 42, IdeaK3

Hindsight depth changes a reduced move's child by one ply, from the plies the parent withheld and from the sum of the two static evaluations.
The engine already does that step when HindsightDepth is true. The thresholds in the source are a pawn (100) and three withheld plies.
I left that check as the switch and added the spins HindsightDepth_Loss (default 100) and HindsightDepth_Withheld (default 3). They are read only inside the switch, so the default path is today's path and the on path at those defaults is today's on path.

EXISTS: forge-combo29/src/search.cpp:1611 (the comment that states the rule starts at line 1604; the UCI check is uci.cpp:224, default false). The two numbers were literals, so they are now options. The on/off itself was already an option.

## Honesty numbers

exe B, no setoption, from HONESTY_B.txt (script summarize.py):

check | nodes | expected | result
bench11 | 312866 | 312866 | ok
bench13 | 862329 | 862329 | ok
bench16 | 3024920 | 3024920 | ok
perft5 | 4865609 | 4865609 | ok

exe P, no setoption, honesty_P_bench11.txt, honesty_P_bench13.txt, honesty_P_bench16.txt, honesty_P_perft5.txt: the same four node counts.

exe B, S14, depth 12: O sum 9500069, first three 41311 / 24872 / 28574 (b_O_d12.txt). G sum 18466239 (b_G_d12.txt).

## Steps

step | status | evidence file | result
1 seat | done | SEAT.txt | seat 092, idea 42, Grok 4.7
2 two builds and honesty | done | HONESTY_B.txt, b_O_d12.txt, b_G_d12.txt | known nodes and both depth-12 sums match
3a read | done | search.cpp:1611 | EXISTS
3b predict | done | prediction.txt | O-on point 8800000, range 7200000 to 10800000; Elo point +6, range -35 to +40. File committed before any measuring command.
3c patch | done | idea.patch.txt, apply_check.txt | git apply --check on a clean base tree exited 0
3d proofs | done | proofs.txt, p_uci.txt, asan_nm.txt, asan_bug.txt.raw | see below
3e match | done | match_on_off.log, match_on_off.pgn | Elo 4.08 +/- 10.50, 1106 games
4 partner 042 | done | partner_proofs.txt, partner_match_R.log | CONFIRMS
5 report | done | REPORT.md, RESULT.txt | this file

## Proofs

(1) Honesty on exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Files honesty_P_*.txt.

(2) S14 and HindsightDepth false. O depth 12 equals exe B on every position, sum 9500069. G depth 12 equals exe B on every position, sum 18466239. proofs.txt.

(3) S14 and HindsightDepth true, spins left at 100 and 3. O depth 12 sum 9845650. 200 of 200 positions differ from exe B. proofs.txt, p_on_O_d12.txt.

(4) The uci listing in p_uci.txt includes:
option name HindsightDepth type check default false
option name HindsightDepth_Loss type spin default 100 min 0 max 2000
option name HindsightDepth_Withheld type spin default 3 min 0 max 32

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. nm -C counted 35 __asan_ symbols (asan_nm.txt). First 100 of G at depth 10 with the switch true: 0 lines matching AddressSanitizer or runtime error (asan_G_d10.txt.raw), sum 1973656. A scratch copy with one heap read past the end of a 4-int array, only on the FEN in asan_bug.fen, built the same way and run through harness.py, reported heap-buffer-overflow (asan_bug.txt.raw). That scratch copy also had 35 __asan_ symbols.

## Match

exe P with HindsightDepth true against exe P with HindsightDepth false. Both S14, Threads 1, Hash 16, 20000 nodes. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3. From match_on_off.log:

Elo: 4.08 +/- 10.50, nElo: 7.97 +/- 20.48
Games: 1106, Wins: 332, Losses: 319, Draws: 455, Points: 559.5 (50.59 %)

The point sits inside the prediction range. The whole interval is not below 0, so I did not open the code a second time for a mistake.

Measured O-on sum 9845650 is inside the committed range 7200000 to 10800000. The point I wrote, 8800000, is lower than the measurement. I had expected the one-ply-less arm to dominate.

## Partner

Partner is seat 042 (idea 42; the next seat after 092 is 142, which is outside 001..120, so the partner wraps to 042). Their branch had idea.patch.txt. Their option is IdeaK3, with spins IdeaK3_Margin default 100 and IdeaK3_Withheld default 3. While IdeaK3 is false their step still uses the literals.

git apply --check of partner042.patch.txt on a clean base tree exited 0 (partner_apply_check.txt). Built that tree. My harness, not theirs:

Honesty, no setoption: the four known node counts (honesty_Q_*.txt).
IdeaK3 false, S14, O depth 12: equal to exe B, 0 of 200 differ, sum 9500069.
IdeaK3 true, S14, O depth 12: sum 9845650, 200 of 200 differ from exe B, and 0 of 200 differ from their p_on_O_d12.rows.tsv (partner_proofs.txt, from partner_compare.py).

That is what they claim for applies, off_identical, and on_differs. Verdict: CONFIRMS.

Their switch, 300 of my R openings, both colours, 600 games, same S14 and 20000 nodes (partner_match_R.log):

Elo: -1.16 +/- 7.53
Games: 600, Wins: 261, Losses: 263, Draws: 76, Points: 299.0 (49.83 %)

## Suspicions, not proven

Seat 042's own O+G match log ends at Elo 4.08 +/- 10.50, the same figures as mine. Their on rows are the same as mine, and both switches at the default numbers run the same step, so a fixed-node match on the same openings can repeat. I did not prove their opening file bytes were the same as mine.

Many games in both matches ended by threefold repetition or the 50-move rule. Those finishes follow the rules of chess.

## What I did NOT do

I did not replay seat 042's 1106-game match and I did not rebuild their sanitizer.
I did not search G at depth 12 with the switch on, and I did not try the spins at values other than the defaults.
The handoff branch had no forge-combo29/soak_all/FABLE_TO_grok_<N>.md at step 1 or at minute 60.
I did not open a pull request.

## What I am NOT sure about

fastchess printed DrawRatio 88.33% on the 600-game match in the same block that says Draws: 76. I did not determine which count that percentage uses.
The R file uses a ply cap of 120 that I chose: a game that ends before ply 120 is dropped, and a game still going at ply 120 keeps a position every 7 plies after ply 8. make_r.py reported seed 9201, 19 games, 0 dropped, 300 positions.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok/092/harness.py
 M forge-combo29/grok/092/stamps.txt
?? forge-combo29/grok/092/REPORT.md
?? forge-combo29/grok/092/RESULT.txt
?? forge-combo29/grok/092/apply_check.txt
?? forge-combo29/grok/092/honesty_Q_bench11.meta
?? forge-combo29/grok/092/honesty_Q_bench11.txt
?? forge-combo29/grok/092/honesty_Q_bench13.meta
?? forge-combo29/grok/092/honesty_Q_bench13.txt
?? forge-combo29/grok/092/honesty_Q_bench16.meta
?? forge-combo29/grok/092/honesty_Q_bench16.txt
?? forge-combo29/grok/092/honesty_Q_perft5.meta
?? forge-combo29/grok/092/honesty_Q_perft5.txt
?? forge-combo29/grok/092/partner042.patch.txt
?? forge-combo29/grok/092/partner042_on_O.tsv
?? forge-combo29/grok/092/partner_apply_check.txt
?? forge-combo29/grok/092/partner_compare.py
?? forge-combo29/grok/092/partner_match_R.log
?? forge-combo29/grok/092/partner_match_R.pgn
?? forge-combo29/grok/092/partner_proofs.txt
?? forge-combo29/grok/092/q_off_O_d12.txt
?? forge-combo29/grok/092/q_off_O_d12.txt.meta
?? forge-combo29/grok/092/q_off_O_d12.txt.raw
?? forge-combo29/grok/092/q_on_O_d12.txt
?? forge-combo29/grok/092/q_on_O_d12.txt.meta
?? forge-combo29/grok/092/q_on_O_d12.txt.raw
?? forge-combo29/grok/092/run_partner_match.sh

$ ls -la forge-combo29/grok/092
total 4824
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu      16 Nov 20 09:18 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:10 asan_bug.fen
-rw-r--r-- 1 ubuntu ubuntu     820 Nov 20 08:10 asan_bug.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   10234 Nov 20 08:10 asan_bug.txt.raw
-rw-r--r-- 1 ubuntu ubuntu    5592 Nov 20 08:10 asan_G_d10.txt
-rw-r--r-- 1 ubuntu ubuntu     816 Nov 20 08:10 asan_G_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  131772 Nov 20 08:10 asan_G_d10.txt.raw
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 08:10 asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu   19819 Nov 20 08:05 b_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     797 Nov 20 08:05 b_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  550060 Nov 20 08:05 b_G_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 08:05 b_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     797 Nov 20 08:05 b_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  309038 Nov 20 08:05 b_O_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu    6955 Nov 20 09:18 config.json
-rw-r--r-- 1 ubuntu ubuntu    9882 Nov 20 09:11 harness.py
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:04 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 08:04 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:04 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 08:04 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:04 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      83 Nov 20 08:04 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:08 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 08:06 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 08:06 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      83 Nov 20 08:06 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:04 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     296 Nov 20 08:04 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:06 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     296 Nov 20 08:06 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:12 honesty_Q_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 09:12 honesty_Q_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:12 honesty_Q_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      81 Nov 20 09:12 honesty_Q_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:12 honesty_Q_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      83 Nov 20 09:12 honesty_Q_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     180 Nov 20 09:12 honesty_Q_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     296 Nov 20 09:12 honesty_Q_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3294 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1577 Nov 20 08:08 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  106308 Nov 20 08:18 match_on_off.log
-rw-r--r-- 1 ubuntu ubuntu 1068088 Nov 20 08:18 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:11 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu   17557 Nov 20 09:11 partner042_on_O.tsv
-rw-r--r-- 1 ubuntu ubuntu    6865 Nov 20 09:11 partner042.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 09:18 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1230 Nov 20 09:12 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu   53776 Nov 20 09:15 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu  415654 Nov 20 09:15 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     192 Nov 20 09:12 partner_proofs.txt
-rw-r--r-- 1 ubuntu ubuntu   19819 Nov 20 08:07 p_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:07 p_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  550247 Nov 20 08:07 p_off_G_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 08:06 p_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:06 p_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  309377 Nov 20 08:06 p_off_O_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 08:07 p_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 08:07 p_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  309406 Nov 20 08:07 p_on_O_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu    1389 Nov 20 08:01 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 08:22 proofs.txt
-rwxr-xr-x 1 ubuntu ubuntu     885 Nov 20 08:10 prove_asan.sh
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 08:07 p_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     177 Nov 20 08:07 p_uci.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 09:12 q_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     834 Nov 20 09:12 q_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  309337 Nov 20 09:12 q_off_O_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu   14065 Nov 20 09:12 q_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 09:12 q_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  309408 Nov 20 09:12 q_on_O_d12.txt.raw
-rw-r--r-- 1 ubuntu ubuntu    7604 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   18136 Nov 20 08:08 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1452 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1095 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     189 Nov 20 09:19 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    2268 Nov 20 08:08 summarize.py
```
