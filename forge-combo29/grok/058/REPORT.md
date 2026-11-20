# Seat 058, idea 8, S45

S45 refuses a null move when a cheaper piece can capture a dearer piece and static exchange does not call that capture a loss. The plain engine already does this. The on/off option is `NullSeeVeto`, default false, at `forge-combo29/src/search.cpp:1699`, implemented by `null_see_veto_threat` at `forge-combo29/src/search.cpp:1174` and advertised at `forge-combo29/src/uci.cpp:226`. I did not add a second check. I turned the two fixed numbers in that function into spins: `NullSeeVeto_SeeMargin` default 0 (range -400 to 400) and `NullSeeVeto_KingWorth` default 100000 (range 1 to 1000000). With the check false the function is not called. With the check true and the spins left at those defaults, the search matches today's `NullSeeVeto` true path.

EXISTS: forge-combo29/src/search.cpp:1699. The on/off was already an option. The SEE margin 0 and the king price 100000 were not.

Honesty, no setoption, fresh process each line. exe B and exe P both: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Files `HONESTY_B.txt` and `HONESTY_P.txt`.

## Step table

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 058, idea 8 |
| 2 honesty and baseline | done | HONESTY_B.txt, B_O_d12.rows, B_G_d12.rows | honesty ok; O sum 9500069; G sum 18466239 |
| 3a read | done | this report | EXISTS at search.cpp:1699 |
| 3b prediction | done | prediction.txt | not edited after the push |
| 3c patch | done | idea.patch.txt, apply_check.txt | git apply --check exit 0 on a clean base tree |
| 3d proofs | done | proofs_compare.txt, uci_p.txt, asan_G100_d10.txt, scratch_asan.txt | off identical; on differs in 194 of 200; sanitizer clean, and the scratch overrun is reported |
| 3e match | done | match_og.txt, match_og.pgn | 1106 games, Elo -3.14 +/- 10.74 |
| 4 partner | done | partner_proofs.txt, partner_match.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty on exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Same four numbers on exe B.

(2) S14, Threads 1, Hash 16, `NullSeeVeto` false. O depth 12 sum 9500069, first three 41311 / 24872 / 28574, 0 of 200 node rows differ from exe B. G depth 12 sum 18466239, 0 of 353 differ from exe B. `summarize.py` output is `proofs_compare.txt`.

(3) S14 and `NullSeeVeto` true, spins at default. O depth 12 sum 9384814, first three 41280 / 24866 / 28556. 194 of 200 positions differ from exe B with the switch false. 8 of 200 best moves differ. The same 200 rows are identical to exe B with `NullSeeVeto` true (0 of 200), so the new spins at their defaults do not change today's on path.

(4) `uci` on exe P lists `option name NullSeeVeto type check default false`, `option name NullSeeVeto_SeeMargin type spin default 0 min -400 max 400`, and `option name NullSeeVeto_KingWorth type spin default 100000 min 1 max 1000000`. Raw file `uci_p.txt`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `nm -C` count of `__asan_` is 35, recorded in `asan_nm_count.txt` and appended on `asan_G100_d10.meta`. First 100 positions of G at depth 10 with `NullSeeVeto` true: 0 lines containing AddressSanitizer or a runtime error (`asan_G100_d10.txt`). A scratch copy, same flags and the same `harness.py` runner, reads one past the end of a 4-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 1` (`scratch_insert.txt`). That run's log contains `heap-buffer-overflow` and `SUMMARY: AddressSanitizer` (`scratch_asan.txt`). The scratch source is not in the patch.

## Match

exe P with `NullSeeVeto` true against exe P with it false. Both S14, Threads 1, Hash 16, 20000 nodes, time control 60+0.6 as a backstop that does not bind at this node count. Openings O then G, 553 positions, both colours, 1106 games. fastchess from https://github.com/Disservin/fastchess commit d6e3a7a, concurrency 3. Whole stdout is `match_og.txt`, games are `match_og.pgn`.

```
Elo: -3.14 +/- 10.74, nElo: -5.99 +/- 20.48
LOS: 28.31 %, DrawRatio: 65.10 %, PairsRatio: 0.91
Games: 1106, Wins: 332, Losses: 342, Draws: 432, Points: 548.0 (49.55 %)
Ptnml(0-2): [19, 82, 360, 74, 18], WL/DD Ratio: 1.61
Total Time: 00:07:15
```

The point estimate is above -20 and the interval crosses 0, so I did not open a second bug hunt. The on path already matches exe B with the existing option on, position by position.

Prediction in `prediction.txt` (not edited): O sum 10300000, wrong below 9600000 or above 13000000; Elo +5, wrong below -25 or above +40. The measured sum 9384814 is below 9600000, so the node prediction is wrong. The Elo point -3.14 is inside the Elo range I wrote.

## Partner

Partner is seat 008 (next seat with this idea that has a branch; 108 had no branch). Fetched `for-fable-and-opus/grok-008` at `bda7bba242e053dc97e684141233a5b73b7ab141`. Their patch is `partner_008_idea.patch.txt`. `git apply --check` on a clean base tree exited 0 (`partner_apply_check.txt`). My harness, not theirs.

Honesty: the same four numbers. `NullSeeVeto` left false, `IdeaS45` false: O depth 12 equals exe B, 0 of 200. `IdeaS45` true, their spins at default: O depth 12 equals their own `P_on_O_d12.nodes`, 0 of 200, sum 9384814. Versus exe B, 194 of 200 differ, which is the count in their `P_on_O_d12.cmp.txt`. Output: `partner_proofs.txt`.

Their switch, 300 of my R openings, both colours, 600 games (`partner_match.txt`): Elo 0.58 +/- 8.57, games 600, points 300.5. I did not replay their 1106-game O+G match. The proofs this step asks for match what they recorded.

Verdict: CONFIRMS.

## Suspicions, not proven

The on-tree is slightly smaller than the off-tree (9384814 versus 9500069), which is the opposite of "refusing a cutoff always searches more". I did not trace a position to show where the extra pruning comes from. Seat 008's stdout says 331 wins, 341 losses, 434 draws, while mine says 332, 342, 432, but the Elo, the error, the points, and the pentanomial are the same numbers. I did not reconcile those two win counts.

## What I did not do

I did not add an option named `IdeaS45`. I did not sweep `NullSeeVeto_SeeMargin` or `NullSeeVeto_KingWorth` away from the defaults. I did not run G at depth 12 with the switch on. I did not replay seat 008's 1106-game match. I started the partner check before minute 75 because their patch and their O rows were already on the branch.

## What I am not sure about

Whether another SEE margin or another king price would change the Elo. The match interval includes both a small loss and a small gain, so -3.14 is not a measured loss of strength.

## Handoff

Minute-60 read of `handoff/fable-opus-combo29-all-20261114` at 2026-11-20T08:55:37Z, commit 8c5536863464d4af8c07b4788883463eb950ab1d. No file named FABLE_TO_grok_<N>.md. Nothing to stop for.

times: see stamps.txt

## git status --short

 M forge-combo29/grok/058/stamps.txt
?? forge-combo29/grok/058/REPORT.md
?? forge-combo29/grok/058/RESULT.txt
?? forge-combo29/grok/058/apply_check.txt
?? forge-combo29/grok/058/partner_config.json

## ls -la

total 9880
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:28 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:27 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     868 Nov 20 08:10 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    1394 Nov 20 08:10 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  119223 Nov 20 08:10 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:10 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:05 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    5220 Nov 20 08:05 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  507815 Nov 20 08:05 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:05 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:08 B_O_d12_on.meta
-rw-r--r-- 1 ubuntu ubuntu    2915 Nov 20 08:08 B_O_d12_on.rows
-rw-r--r-- 1 ubuntu ubuntu  282051 Nov 20 08:08 B_O_d12_on.txt
-rw-r--r-- 1 ubuntu ubuntu    2917 Nov 20 08:05 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  282208 Nov 20 08:05 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    6949 Nov 20 08:27 config.json
-rw-r--r-- 1 ubuntu ubuntu    9104 Nov 20 08:04 harness.py
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:05 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:05 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:05 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:05 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 08:05 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:05 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:05 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     231 Nov 20 08:05 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:07 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5150 Nov 20 08:07 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:07 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5150 Nov 20 08:07 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:07 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5152 Nov 20 08:07 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:07 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5363 Nov 20 08:07 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     231 Nov 20 08:07 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    3512 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     983 Nov 20 08:07 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 4698532 Nov 20 08:19 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  147313 Nov 20 08:19 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu    8802 Nov 20 08:11 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:11 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    7331 Nov 20 08:20 partner_008_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:20 partner_008_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:22 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1160 Nov 20 08:21 partner_compare.py
-rw-r--r-- 1 ubuntu ubuntu    6939 Nov 20 08:27 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:21 partner_honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5189 Nov 20 08:21 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:21 partner_honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5189 Nov 20 08:21 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:21 partner_honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5191 Nov 20 08:21 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 08:21 partner_honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5402 Nov 20 08:21 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     255 Nov 20 08:21 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu 1878233 Nov 20 08:25 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   70124 Nov 20 08:25 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:21 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2917 Nov 20 08:21 partner_O_off.rows
-rw-r--r-- 1 ubuntu ubuntu  282337 Nov 20 08:21 partner_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 08:21 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu    2915 Nov 20 08:21 partner_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu  282449 Nov 20 08:21 partner_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     686 Nov 20 08:21 partner_proofs.txt
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:08 P_G_d12_off.meta
-rw-r--r-- 1 ubuntu ubuntu    5220 Nov 20 08:08 P_G_d12_off.rows
-rw-r--r-- 1 ubuntu ubuntu  508113 Nov 20 08:08 P_G_d12_off.txt
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:07 P_O_d12_off.meta
-rw-r--r-- 1 ubuntu ubuntu    2917 Nov 20 08:07 P_O_d12_off.rows
-rw-r--r-- 1 ubuntu ubuntu  282092 Nov 20 08:07 P_O_d12_off.txt
-rw-r--r-- 1 ubuntu ubuntu     839 Nov 20 08:08 P_O_d12_on.meta
-rw-r--r-- 1 ubuntu ubuntu    2915 Nov 20 08:08 P_O_d12_on.rows
-rw-r--r-- 1 ubuntu ubuntu  282189 Nov 20 08:08 P_O_d12_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1252 Nov 20 08:06 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    1030 Nov 20 08:11 proofs_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    6880 Nov 20 08:28 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     223 Nov 20 08:28 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   18937 Nov 20 08:07 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1164 Nov 20 08:11 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1066 Nov 20 08:21 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     840 Nov 20 08:10 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 08:10 scratch_asan.rows
-rw-r--r-- 1 ubuntu ubuntu    9280 Nov 20 08:10 scratch_asan.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:10 scratch_fen.txt
-rw-r--r-- 1 ubuntu ubuntu     308 Nov 20 08:11 scratch_insert.txt
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     351 Nov 20 08:55 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1510 Nov 20 08:09 summarize.py
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:08 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5089 Nov 20 08:08 uci_p.txt

