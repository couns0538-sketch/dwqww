# Seat 008, idea 8, S45

Idea S45 refuses a null-move drop when a cheaper piece has a legal capture of a dearer piece and static exchange does not call that capture a loss.
The plain engine already does this behind the check `NullSeeVeto` (default false). The two fixed numbers in `null_see_veto_threat` were king price 100000 and SEE margin 0.
I added check `IdeaS45` (default false) and spins `IdeaS45_KingWorth` (default 100000) and `IdeaS45_SeeMargin` (default 0). With the check false the new call is not made. With the check true the existing veto runs at those defaults.

EXISTS: yes:forge-combo29/src/search.cpp:1699
The scan is `null_see_veto_threat` at forge-combo29/src/search.cpp:1174. The check is already advertised at forge-combo29/src/uci.cpp:226 (`option name NullSeeVeto type check default false`). The two numbers were not options. Turning `NullSeeVeto` on was already the idea, so the new check is a second switch onto that same veto, and the spins are those two numbers.

## Honesty numbers

exe B, no setoption, from `HONESTY_B.txt`:

```
bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK
```

exe P, no setoption, from `HONESTY_P.txt`: the same four lines, all OK.

Baseline sums of exe B, S14, Threads 1, Hash 16, from `read_sums.py`:

```
file B_O_d12.nodes
n 200
sum 9500069
first3 41311 24872 28574
file B_G_d12.nodes
n 353
sum 18466239
first3 37203 70845 144383
```

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 008, idea 8 |
| 2 honesty B | done | HONESTY_B.txt | four pins OK |
| 2 set O | done | B_O_d12.sum.txt | sum 9500069, first3 41311 24872 28574 |
| 2 set G | done | B_G_d12.sum.txt | sum 18466239 |
| 3 prediction | done | prediction.txt | committed alone before any exe P measurement |
| 3 patch | done | idea.patch.txt, apply_check.txt | apply_check_exit=0 |
| 3 proof 1 | done | HONESTY_P.txt | four pins OK |
| 3 proof 2 | done | P_off_O_d12.cmp.txt, P_off_G_d12.cmp.txt | differ 0 of 200 and 0 of 353 |
| 3 proof 3 | done | P_on_O_d12.cmp.txt, P_on_O_d12.sum.txt | differ 194 of 200, sum 9384814 |
| 3 proof 4 | done | uci_p.options.txt | IdeaS45 false, KingWorth 100000, SeeMargin 0 |
| 3 proof 5 | done | san_G100_d10.meta, san_scratch.raw.txt | asan_symbols 35, 0 lines on G, scratch reported |
| 3 match | done | match_og.result.txt | Elo -3.14 +/- 10.74, 1106 games |
| 4 partner 058 | done | partner_off_O.cmp.txt, partner_on_O.cmp.txt, partner_match.result.txt | CONFIRMS |

## Proofs

(1) exe P, no setoption. `HONESTY_P.txt`: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

(2) S14 and `IdeaS45 false`. `compare_nodes.py`:

```
left B_O_d12.nodes n 200 sum 9500069
right P_off_O_d12.nodes n 200 sum 9500069
differ 0 of 200
left B_G_d12.nodes n 353 sum 18466239
right P_off_G_d12.nodes n 353 sum 18466239
differ 0 of 353
```

(3) S14 and `IdeaS45 true`, spins at 100000 and 0. `compare_nodes.py` and `read_sums.py`:

```
differ 194 of 200
sum 9384814
first3 41280 24866 28556
```

(4) `uci` on exe P, from `uci_p.options.txt`:

```
id name Chess Engine Forge 6.4.24 candidate
option name IdeaS45 type check default false
option name IdeaS45_KingWorth type spin default 100000 min 0 max 1000000
option name IdeaS45_SeeMargin type spin default 0 min -2000 max 2000
```

(5) AddressSanitizer + UndefinedBehaviorSanitizer build of the patched tree. `san_G100_d10.meta` has `asan_symbols=35`. First 100 of G at depth 10 with `IdeaS45 true`: `san_G100_d10.log` says `SUM 2091206 N 100`, and a search of `san_G100_d10.raw.txt` found 0 lines matching AddressSanitizer or `runtime error`. The same runner `san_run.sh` on a scratch copy, whose only extra change is `heap[4]` on `new int[4]` when the FEN is `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, wrote this line into `san_scratch.raw.txt`:

```
/tmp/scratch-s45/forge-combo29/src/uci.cpp:488:30: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
```

`san_scratch.meta` also has `asan_symbols=35`.

`git apply --check` of `idea.patch.txt` on a clean base worktree exited 0 (`apply_check.txt`).

## Match

exe P with `IdeaS45 true` (spins at default) against exe P with `IdeaS45 false`. Both S14, Threads 1, Hash 16, OwnBook false, 20000 nodes, openings O then G (553), both colours, 1106 games, concurrency 3. `parse_match.py` on `match_og.stdout.txt`:

```
finished_games 1106
Elo: -3.14 +/- 10.74, nElo: -5.99 +/- 20.48
Games: 1106, Wins: 331, Losses: 341, Draws: 434, Points: 548.0 (49.55 %)
```

The point -3.14 is not below -20, and the interval [-13.88, +7.60] is not entirely below 0, so I did not open the search for a code mistake. Prediction was sum 9850000, wrong outside [9200000, 12000000] or if equal to 9500069, and Elo +3, wrong outside [-25, +40]. Measured sum 9384814 and Elo -3.14 sit inside those ranges. `prediction.txt` was not edited after the measuring runs.

## Partner

Partner is seat 058 (next seat with this idea that has a branch). Seat 108 had no branch. Verdict: CONFIRMS.

My harness, not theirs. Their patch `partner_058.patch.txt` applies to the base (`partner_apply_check.txt` is `APPLY_CHECK_OK`). Their switch is the existing `NullSeeVeto`, and they turned the two fixed numbers into `NullSeeVeto_KingWorth` (default 100000) and `NullSeeVeto_SeeMargin` (default 0). Honesty of that build is `PARTNER_HONESTY.txt`, four pins OK. Switch false versus exe B on O: `differ 0 of 200`. Switch true versus their published `P_O_d12_on.rows` node column: `differ 0 of 200` (both sums 9384814). Those same rows versus exe B: `differ 194 of 200`, which is the `on_differs` they wrote. A 600-game match of their switch on 300 of my R openings, both colours, gave Elo -3.47 +/- 10.64 (`partner_match.result.txt`). They did not publish that R number. Their O+G Elo in RESULT.txt is -3.14 +/- 10.74, the same as my IdeaS45 match on the same openings, which is what the same veto at the same defaults should do.

## Suspicions, not proven

The node sum fell (9500069 to 9384814) even though the veto skips a pruning cutoff. I did not separate "more nodes where the veto fires" from "fewer nodes because a different tree stores different hash hits". The near-zero Elo on both the 1106-game set and the 600-game R set is the same direction, and I do not have a second net or a longer match.

## What I did NOT do

I did not re-run seat 058's sanitizer build. I did not replay their 1106-game O+G match. I did not try KingWorth or SeeMargin at any value other than the defaults. I did not measure `IdeaS45` and `NullSeeVeto` both true. I did not build a second copy of exe P at STEP 2 before the patch. There was no `FABLE_TO_grok_*.md` on the handoff branch at STEP 1 or at minute 60.

## What I am NOT sure about

I am not sure the random games in `make_r.py` match the engine's draw claims in every case. The script uses python-chess `is_game_over(claim_draw=True)` and drops a game that ends before ply 80. In this run, `R.meta.txt` says `games_seen 28`, `games_dropped 0`, `seed 801`. I am not sure a defended piece that only looks attacked to a pin-blind SEE is the right thing to veto. I am not sure the 20000-node games are long enough for this veto to show a real Elo.

times: see stamps.txt

## git status --short

```
A  forge-combo29/grok/008/PARTNER_HONESTY.txt
A  forge-combo29/grok/008/REPORT.md
A  forge-combo29/grok/008/RESULT.txt
A  forge-combo29/grok/008/partner_058.patch.txt
A  forge-combo29/grok/008/partner_058_O_on.nodes
A  forge-combo29/grok/008/partner_058_O_on.rows
A  forge-combo29/grok/008/partner_apply_check.txt
A  forge-combo29/grok/008/partner_config.json
A  forge-combo29/grok/008/partner_h_bench11.meta
A  forge-combo29/grok/008/partner_h_bench11.txt
A  forge-combo29/grok/008/partner_h_bench13.meta
A  forge-combo29/grok/008/partner_h_bench13.txt
A  forge-combo29/grok/008/partner_h_bench16.meta
A  forge-combo29/grok/008/partner_h_bench16.txt
A  forge-combo29/grok/008/partner_h_perft5.meta
A  forge-combo29/grok/008/partner_h_perft5.txt
A  forge-combo29/grok/008/partner_match.exit.txt
A  forge-combo29/grok/008/partner_match.pgn
A  forge-combo29/grok/008/partner_match.result.txt
A  forge-combo29/grok/008/partner_match.sh
A  forge-combo29/grok/008/partner_match.stderr.txt
A  forge-combo29/grok/008/partner_match.stdout.txt
A  forge-combo29/grok/008/partner_off_O.cmp.txt
A  forge-combo29/grok/008/partner_off_O.log
A  forge-combo29/grok/008/partner_off_O.meta
A  forge-combo29/grok/008/partner_off_O.nodes
A  forge-combo29/grok/008/partner_off_O.raw.txt
A  forge-combo29/grok/008/partner_on_O.cmp.txt
A  forge-combo29/grok/008/partner_on_O.log
A  forge-combo29/grok/008/partner_on_O.meta
A  forge-combo29/grok/008/partner_on_O.nodes
A  forge-combo29/grok/008/partner_on_O.raw.txt
A  forge-combo29/grok/008/partner_on_vs_B.cmp.txt
M  forge-combo29/grok/008/stamps.txt
```

## ls -la

```
total 9852
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:13 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      19 Nov 20 08:12 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 07:58 B_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu     961 Nov 20 07:58 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 07:58 B_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  545008 Nov 20 07:58 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      64 Nov 20 07:59 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     110 Nov 20 07:57 B_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu     965 Nov 20 07:57 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 07:57 B_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  304249 Nov 20 07:57 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      62 Nov 20 07:59 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     687 Nov 20 08:00 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    7329 Nov 20 09:12 config.json
-rw-r--r-- 1 ubuntu ubuntu    5574 Nov 20 08:00 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:57 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:03 G_first100.epd
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     234 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:57 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2951 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:00 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:00 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 08:00 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     234 Nov 20 08:00 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 08:00 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7331 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1333 Nov 20 08:12 make_r.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:03 match_og.epd
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:10 match_og.exit.txt
-rw-r--r-- 1 ubuntu ubuntu 4583653 Nov 20 08:10 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     418 Nov 20 08:11 match_og.result.txt
-rw-r--r-- 1 ubuntu ubuntu    1322 Nov 20 08:04 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 match_og.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu  119350 Nov 20 08:10 match_og.stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     626 Nov 20 08:11 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 09:07 partner_058_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    2915 Nov 20 09:07 partner_058_O_on.rows
-rw-r--r-- 1 ubuntu ubuntu    3512 Nov 20 09:07 partner_058.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 09:07 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    7354 Nov 20 09:12 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:07 partner_h_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:07 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:07 partner_h_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:07 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 09:08 partner_h_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:08 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     163 Nov 20 09:08 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu     237 Nov 20 09:08 partner_h_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:08 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu      21 Nov 20 09:11 partner_match.exit.txt
-rw-r--r-- 1 ubuntu ubuntu 2026027 Nov 20 09:11 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu     411 Nov 20 09:12 partner_match.result.txt
-rw-r--r-- 1 ubuntu ubuntu    1288 Nov 20 09:08 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:08 partner_match.stderr.txt
-rw-r--r-- 1 ubuntu ubuntu   65919 Nov 20 09:11 partner_match.stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 09:08 partner_off_O.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     110 Nov 20 09:08 partner_off_O.log
-rw-r--r-- 1 ubuntu ubuntu    1029 Nov 20 09:08 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:08 partner_off_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  303989 Nov 20 09:08 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 09:08 partner_on_O.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     110 Nov 20 09:08 partner_on_O.log
-rw-r--r-- 1 ubuntu ubuntu    1137 Nov 20 09:08 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 09:08 partner_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu  304175 Nov 20 09:08 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     376 Nov 20 09:08 partner_on_vs_B.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:01 P_off_G_d12.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     115 Nov 20 08:01 P_off_G_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1018 Nov 20 08:00 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:01 P_off_G_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  544579 Nov 20 08:01 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     141 Nov 20 08:00 P_off_O_d12.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     110 Nov 20 08:00 P_off_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1022 Nov 20 08:00 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:00 P_off_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  303750 Nov 20 08:00 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     374 Nov 20 08:01 P_on_O_d12.cmp.txt
-rw-r--r-- 1 ubuntu ubuntu     110 Nov 20 08:01 P_on_O_d12.log
-rw-r--r-- 1 ubuntu ubuntu    1122 Nov 20 08:01 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:01 P_on_O_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  304196 Nov 20 08:01 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      65 Nov 20 08:01 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    1146 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     360 Nov 20 07:59 read_sums.py
-rw-r--r-- 1 ubuntu ubuntu   19265 Nov 20 08:12 R.epd
-rw-r--r-- 1 ubuntu ubuntu    7467 Nov 20 09:13 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 09:13 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      87 Nov 20 08:12 R.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:03 san_G100_d10.log
-rw-r--r-- 1 ubuntu ubuntu    1129 Nov 20 08:03 san_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu     581 Nov 20 08:03 san_G100_d10.nodes
-rw-r--r-- 1 ubuntu ubuntu  126588 Nov 20 08:03 san_G100_d10.raw.txt
-rwxr-xr-x 1 ubuntu ubuntu     445 Nov 20 08:02 san_run.sh
-rw-r--r-- 1 ubuntu ubuntu      36 Nov 20 08:04 san_scratch.log
-rw-r--r-- 1 ubuntu ubuntu    1025 Nov 20 08:04 san_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu    2028 Nov 20 08:04 san_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:04 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:57 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     224 Nov 20 09:13 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     534 Nov 20 08:01 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     231 Nov 20 08:01 uci_p.options.txt
-rw-r--r-- 1 ubuntu ubuntu    5120 Nov 20 08:01 uci_p.txt
```

