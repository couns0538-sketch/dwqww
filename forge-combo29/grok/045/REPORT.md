# Seat 045, idea 45, IdeaK6

IdeaK6 orders a quiet move that gives check before the other quiet moves. I added UCI check option `IdeaK6`, default false, and spin `IdeaK6_Band`, default 200000 (min 0, max 1000000). When the check is true, `Board::gives_check` (direct or discovered) adds the band on top of today's quiet score. When the check is false the band is not added and `gives_check` is not called.

EXISTS: no. `forge-combo29/src/search.cpp` QuietScorer adds 12000 only for a direct check. History can still put a non-checking quiet first, and a discovered check gets no bonus. See `design.txt`.

## Honesty numbers

Exe B and exe P, no setoption, fresh process per line. Both:

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

Files: `HONESTY_B.txt`, `HONESTY_P.txt`.

Exe B, S14, Threads 1, Hash 16, from `print_rows.py`: O depth 12 sum 9500069, first three 41311 24872 28574. G depth 12 sum 18466239. Those are the known sums.

`git apply --check` of `idea.patch.txt` on a clean base printed `MY_APPLY_CHECK_OK` (`apply_check.txt`).

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| seat | done | SEAT.txt, stamps.txt | seat 045 idea 45 |
| honesty B | done | HONESTY_B.txt | 312866, 862329, 3024920, 4865609 |
| baseline O and G | done | B_O_d12.rows.txt, B_G_d12.rows.txt, print_rows.py | 9500069 and 18466239 |
| prediction | done | prediction.txt | O sum 9100000, Elo +6, committed before any P measurement |
| patch | done | idea.patch.txt, apply_check.txt | applies, default off |
| proof off | done | proofs_compare.txt | O and G differ 0 |
| proof on | done | proofs_compare.txt, P_on_O_d12.rows.txt | 200 of 200 differ, sum 9705311 |
| uci options | done | uci_P.txt | IdeaK6 false, IdeaK6_Band 200000 |
| sanitizer | done | asan_G100_d10.meta, asan_bug.raw.txt, asan_nm.txt | clean, nm 35, poison line reported |
| match | done | match_on_off.txt, match_on_off.pgn | Elo -0.31 +/- 9.99, 1106 games |
| partner | done | partner_proofs.txt, partner_match.txt | CONFIRMS, 600 games on my R |

## Proofs

(1) Honesty on exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. `HONESTY_P.txt`.

(2) S14 and IdeaK6 false. `proofs_compare.txt`:

```
=== off O vs B ===
left_n 200 right_n 200
left_sum 9500069 right_sum 9500069
differ 0 of 200
=== off G vs B ===
left_n 353 right_n 353
left_sum 18466239 right_sum 18466239
differ 0 of 353
```

(3) S14 and IdeaK6 true, O depth 12. `proofs_compare.txt`:

```
=== on O vs B ===
left_n 200 right_n 200
left_sum 9500069 right_sum 9705311
differ 200 of 200
=== on O sum ===
n 200
sum 9705311
first3 27670 27733 32279
```

The prediction said 9100000, wrong below 7000000 or above 12000000. 9705311 is inside that range. The direction was the other way: the sum rose.

(4) `uci` lists `option name IdeaK6 type check default false` and `option name IdeaK6_Band type spin default 200000 min 0 max 1000000`. `uci_P.txt`.

(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaK6 true, first 100 of G at depth 10. `asan_G100_d10.meta` has `nm_asan_count=35`. The raw log has 0 lines of `ERROR: AddressSanitizer`, `ERROR: UndefinedBehaviorSanitizer`, or `runtime error:`. A scratch copy with one heap read past the end on fen `8/8/8/8/8/8/8/K6k w - - 0 1`, built the same way, run through `measure.py`, reports this line in `asan_bug.raw.txt`:

`/tmp/scratch-forge/src/uci.cpp:47:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'`

`asan_bug_runner.txt` also has `bug_nm 35`.

## Match

`print_match.py` on `match_on_off.txt`:

```
Results of IdeaK6on vs IdeaK6off (20000 nodes, 1t, 16MB, OG553.epd):
Elo: -0.31 +/- 9.99, nElo: -0.64 +/- 20.48
LOS: 47.54 %, DrawRatio: 66.55 %, PairsRatio: 0.99
Games: 1106, Wins: 333, Losses: 334, Draws: 439, Points: 552.5 (49.95 %)
Ptnml(0-2): [13, 80, 368, 79, 13], WL/DD Ratio: 1.63
```

PGN events: 1106. The prediction said +6, wrong below -25 or above +40. -0.31 is inside that range. The point is not below -20 and the interval is not entirely below 0, so I did not open the code for a second bug hunt. 0 `unknown option`, 0 `invalid value`, 0 `illegal move` in the log.

## Partner

Partner is seat 095 (same idea, the next seat after 045). `partner_095.patch.txt` applies on a clean base (`PARTNER_APPLY_CHECK_OK` in `apply_check.txt`). I built that tree and used my own `honesty.py` and `measure.py`.

`partner_proofs.txt`: honesty nodes 312866, 862329, 3024920, 4865609. Switch false versus exe B: differ 0 of 200, sum 9500069. Switch true versus their `P_on_O_d12.tsv`: differ 0 of 200, sum 9781037. Their claim was exactly that (off identical, on sum 9781037, 200 of 200 differ from B). `partner_uci.txt` shows the same two options and defaults they printed.

Their patch adds the band only in `generate_quiets`. Mine also adds it on quiet evasions. That is why my on-sum is 9705311 and theirs is 9781037. Both are real.

`print_match.py` on `partner_match.txt` (my R300, both colours, their switch):

```
Results of IdeaK6on vs IdeaK6off (20000 nodes, 1t, 16MB, R300.fens):
Elo: -8.11 +/- 9.86, nElo: -22.88 +/- 27.80
LOS: 5.34 %, DrawRatio: 83.67 %, PairsRatio: 0.69
Games: 600, Wins: 263, Losses: 277, Draws: 60, Points: 293.0 (48.83 %)
```

Verdict: CONFIRMS. I did not re-run their sanitizer or their 1106-game match. The proofs this step asks for match what they claim.

## Suspicions, not proven

The node sum went up, not down. Earlier checks did not buy fewer nodes on this set. The match interval includes both a small loss and a small gain, so the built-in net does not show a clear result.

## What I did NOT do

I did not re-run seat 095's sanitizer build or their 1106-game match. I did not search other values of `IdeaK6_Band`. I did not measure G at depth 12 with the switch on. I did not move quiet checks in front of killers or the countermove. No `FABLE_TO_grok_<N>.md` exists on the handoff branch (checked at step 1 and at minute 60).

## What I am NOT sure about

I am not sure how much of my 200/200 node change is discovered checks and how much is the larger band on direct checks that already had +12000. I am not sure the same patch helps or hurts with the owner's net. This match used the built-in net.

times: see stamps.txt

## git status and ls

The lines below are the command output pasted after the files in this folder were written.

```
$ git status --short
 M forge-combo29/grok/045/stamps.txt
?? forge-combo29/grok/045/HONESTY_PARTNER.txt
?? forge-combo29/grok/045/HONESTY_PARTNER.txt.meta
?? forge-combo29/grok/045/HONESTY_PARTNER_bench11.txt
?? forge-combo29/grok/045/HONESTY_PARTNER_bench11.txt.meta
?? forge-combo29/grok/045/HONESTY_PARTNER_bench13.txt
?? forge-combo29/grok/045/HONESTY_PARTNER_bench13.txt.meta
?? forge-combo29/grok/045/HONESTY_PARTNER_bench16.txt
?? forge-combo29/grok/045/HONESTY_PARTNER_bench16.txt.meta
?? forge-combo29/grok/045/HONESTY_PARTNER_perft5.txt
?? forge-combo29/grok/045/HONESTY_PARTNER_perft5.txt.meta
?? forge-combo29/grok/045/REPORT.md
?? forge-combo29/grok/045/RESULT.txt
?? forge-combo29/grok/045/apply_check.txt
?? forge-combo29/grok/045/partner_095.patch.txt
?? forge-combo29/grok/045/partner_095_on_O.rows.txt
?? forge-combo29/grok/045/partner_match.pgn
?? forge-combo29/grok/045/partner_match.txt
?? forge-combo29/grok/045/partner_off_O_d12.meta
?? forge-combo29/grok/045/partner_off_O_d12.raw.txt
?? forge-combo29/grok/045/partner_off_O_d12.rows.txt
?? forge-combo29/grok/045/partner_on_O_d12.meta
?? forge-combo29/grok/045/partner_on_O_d12.raw.txt
?? forge-combo29/grok/045/partner_on_O_d12.rows.txt
?? forge-combo29/grok/045/partner_proofs.txt
?? forge-combo29/grok/045/partner_uci.txt
?? forge-combo29/grok/045/run_partner_match.sh

$ ls -la
total 11516
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu     120 Nov 20 09:15 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     909 Nov 20 08:06 asan_bug.meta
-rw-r--r-- 1 ubuntu ubuntu    7003 Nov 20 08:06 asan_bug.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 asan_bug.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    1260 Nov 20 08:06 asan_bug_runner.txt
-rw-r--r-- 1 ubuntu ubuntu     918 Nov 20 08:05 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  233422 Nov 20 08:05 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1373 Nov 20 08:05 asan_G100_d10.rows.txt
-rw-r--r-- 1 ubuntu ubuntu      16 Nov 20 08:05 asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 07:59 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  892598 Nov 20 07:59 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 07:59 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 07:59 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  502821 Nov 20 07:59 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 07:59 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     663 Nov 20 08:00 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1499 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu     437 Nov 20 08:05 dump_uci.py
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:02 extras_off.txt
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:02 extras_on.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 G100.epd
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 HONESTY_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 07:58 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 HONESTY_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 07:58 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 HONESTY_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 07:58 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 HONESTY_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   20277 Nov 20 07:58 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 07:58 HONESTY_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:10 HONESTY_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 09:10 HONESTY_PARTNER_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:10 HONESTY_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 09:10 HONESTY_PARTNER_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5107 Nov 20 09:10 HONESTY_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 09:10 HONESTY_PARTNER_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5318 Nov 20 09:10 HONESTY_PARTNER_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 09:10 HONESTY_PARTNER_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   20721 Nov 20 09:10 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     226 Nov 20 09:10 HONESTY_PARTNER.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 08:02 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 HONESTY_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 08:02 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 HONESTY_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5107 Nov 20 08:02 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 HONESTY_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5318 Nov 20 08:02 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 HONESTY_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   20721 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:02 HONESTY_P.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    2964 Nov 20 07:57 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    5097 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1334 Nov 20 08:01 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 4513966 Nov 20 08:14 match_on_off.pgn
-rw-r--r-- 1 ubuntu ubuntu  132855 Nov 20 08:14 match_on_off.txt
-rw-r--r-- 1 ubuntu ubuntu    5939 Nov 20 08:04 measure.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG553.epd
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:10 partner_095_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    6514 Nov 20 09:10 partner_095.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 1926024 Nov 20 09:14 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   67584 Nov 20 09:14 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 09:10 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  513982 Nov 20 09:10 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:10 partner_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 09:10 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  513624 Nov 20 09:10 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2896 Nov 20 09:10 partner_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     765 Nov 20 09:10 partner_proofs.txt
-rw-r--r-- 1 ubuntu ubuntu    5044 Nov 20 09:11 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     867 Nov 20 08:03 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  912345 Nov 20 08:03 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5197 Nov 20 08:03 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     871 Nov 20 08:02 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  514039 Nov 20 08:02 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:02 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     870 Nov 20 08:03 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  513971 Nov 20 08:03 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 08:03 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     642 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     399 Nov 20 08:17 print_match.py
-rw-r--r-- 1 ubuntu ubuntu     405 Nov 20 08:00 print_rows.py
-rw-r--r-- 1 ubuntu ubuntu     574 Nov 20 08:07 proofs_compare.txt
-rw-r--r-- 1 ubuntu ubuntu   19176 Nov 20 08:01 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    7836 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:15 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1169 Nov 20 08:07 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1170 Nov 20 09:11 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 special_oob.fen
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5044 Nov 20 08:05 uci_P.txt
```
