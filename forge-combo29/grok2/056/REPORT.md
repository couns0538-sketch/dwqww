# Seat 056 arm 6

Arm 6, id S32, source seat 074, commit 0fd01685b0465c11e29816b5a759e6496d2a69ae, switch IdeaS32.
SEAT.txt: seat 056, arm 6, model Grok 4.7, 2026-11-20T13:22:40Z.

## Patch sha256 and git apply

`git apply --check` then `git apply` of `~/arm.patch` onto the work tree at 6b98f2170a3210e71beed04bbd2553972c253ed7. Output saved in patch_apply.txt:

```
fetch_head 0fd01685b0465c11e29816b5a759e6496d2a69ae
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
reverse-check-ok
 forge-combo29/include/forge/search.hpp |  6 ++++++
 forge-combo29/src/search.cpp           | 30 +++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  5 +++++
 3 files changed, 40 insertions(+), 1 deletion(-)
```

The sha256 is the arm table's sha256. `git apply --reverse --check` printed reverse-check-ok, so the applied tree still matches that patch. IdeaS32_OwedSlack was left at its default and was never sent.

## Honesty numbers

Known: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. honesty_table.py read the raw files:

```
B bench11 info string bench depth 11 nodes 312866 time 176 nps 1777647
B bench13 info string bench depth 13 nodes 862329 time 443 nps 1946566
B bench16 info string bench depth 16 nodes 3024920 time 1447 nps 2090476
B perft5 nodes 4865609
P bench11 info string bench depth 11 nodes 312866 time 162 nps 1931271
P bench13 info string bench depth 13 nodes 862329 time 438 nps 1968787
P bench16 info string bench depth 16 nodes 3024920 time 1466 nps 2063383
P perft5 nodes 4865609
```

Exe B and exe P both match. Each line was a fresh process with no setoption.

## Three O runs

Known off: sum 9500069, first three 41311 / 24872 / 28574. Known on for IdeaS32: sum 9547450, first three 41442 / 24989 / 28711, 200 differ. o_table.py read o_B.out, o_P_off.out, and o_P_on.out. The sum lines and the comparison lines are:

```
sum 9500069 first 41311 24872 28574 count 200
sum 9500069 first 41311 24872 28574 count 200
differ_from /agent/repos/dwqww/forge-combo29/grok2/056/o_B.out 0
sum 9547450 first 41442 24989 28711 count 200
differ_from /agent/repos/dwqww/forge-combo29/grok2/056/o_B.out 200

known_off_match true sum 9500069 first 41311 24872 28574
off_identical true
known_on_match true sum 9547450 first 41442 24989 28711 differ 200
```

The 200 position rows are the rest of o_table.txt. S14, Threads 1, and Hash 16 were sent, then IdeaS32 false or true on exe P. Exe B was not sent IdeaS32.

## Book sha256

book_check.txt:

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd_lines 2632036
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine_lines 29245
ctl_lines 300
arrive_lines 10
half_lines 200
```

Zip sha256, line count, and epd sha256 match the known copy. Seat 056 took every 90th line starting at line 56.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c` of `setoption name IdeaS32 value true` was 20, and `grep -c` of `unknown option|invalid value|No such option` was 0. arrive_check.txt begins:

```
setoption_true_count 20
refusal_count 0
first_setoption_line 394
window 385-404
```

The engine line in that window is `ON <--- setoption name IdeaS32 value true`.

C-HALF: games_tsv.py pool FULL on half.tsv, saved as half_pool.txt:

```
side FULL: games 400 W-L-D 230-26-144 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 42, 94, 58] Elo +195.51 95% [+170.79, +222.18]
```

fastchess printed the same Elo, +195.51. PASS: +195.51 is above +20.

## POOL.txt and chunks

18 chunks, each 500 games, 9000 games. No chunk FAILED. play.sh then printed `minute 95: no new chunk`. POOL.txt:

```
side ON: games 9000 W-L-D 2449-2478-4073 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [212, 1110, 1898, 1055, 225] Elo -1.12 95% [-5.85, +3.61]
```

## suspicions, not proven

The point estimate is -1.12 Elo. The 95% interval [-5.85, +3.61] includes 0 and also includes about +3.6. A gain of a few Elo is not established, and a loss of a few Elo is not established. Across the chunks the running estimate moved between about +4 and about -1, which is what this interval allows.

Every TSV termination field is the word `normal` (9000 of 9000). Result counts are 2807 times 1-0, 2120 times 0-1, and 4073 times 1/2-1/2. fastchess's own log named mates, 3-fold repetition, and the fifty-move rule. No adjudication flag was passed on the command line.

## what I did NOT do

I did not open a pull request. I did not change engine source. I did not send IdeaS32_OwedSlack. I did not pass -draw, -resign, -maxmoves, or tablebases. I did not replay an opening. I did not switch to arm 10. I did not re-run the published seat-030 PGN check of games_tsv.py. No forge-combo29/soak_all/FABLE_TO_grok2_<N>.md file was on the handoff branch at any fetch, so no channel instruction applied. fastchess left an untracked config.json in the repository root; I did not write it and I did not add it. Its adjudication switches are disabled.

## what I am NOT sure about

The id name in the O-run .meta files was read from a separate `uci` process of the same executable. The measured process did not send `uci`. The node counts still matched the known table.

I did not reproduce the seat-030 known answer of games_tsv.py. On C-HALF, that script's Elo matched fastchess's Elo on the same games.

I am not sure the PGN Termination header stores the specific end reason. In these files it is `normal` for every game, while the Result field is a scored result for every game.

## times: see stamps.txt

The first stamp is 2026-11-20T13:22:54Z STEP 1. Chunk 18 was committed at 2026-11-20T15:03:49Z.

## git status --short and ls -la
```
 M forge-combo29/grok2/056/stamps.txt
?? config.json
?? forge-combo29/grok2/056/POOL.txt
?? forge-combo29/grok2/056/REPORT.md
?? forge-combo29/grok2/056/RESULT.txt
```

```
total 3040
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:06 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2125 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    262 Nov 20 13:30 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56294 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51402 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56167 Nov 20 14:27 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51212 Nov 20 14:27 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56169 Nov 20 14:32 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:32 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55873 Nov 20 14:37 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51375 Nov 20 14:37 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56081 Nov 20 14:42 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51445 Nov 20 14:42 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56017 Nov 20 14:47 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51239 Nov 20 14:47 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  55933 Nov 20 14:51 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51399 Nov 20 14:51 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55989 Nov 20 14:56 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51579 Nov 20 14:56 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56491 Nov 20 15:01 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51439 Nov 20 15:01 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56082 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51190 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56107 Nov 20 13:44 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51313 Nov 20 13:44 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55889 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56531 Nov 20 13:53 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51359 Nov 20 13:53 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56331 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56414 Nov 20 14:03 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 14:03 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55854 Nov 20 14:08 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51212 Nov 20 14:08 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56713 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51601 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56681 Nov 20 14:18 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 14:18 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:30 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46886 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:34 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu    995 Nov 20 13:30 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42268 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    813 Nov 20 13:25 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    647 Nov 20 13:28 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu    476 Nov 20 13:28 honesty_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1042 Nov 20 13:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu    951 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 277008 Nov 20 13:27 o_B.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 276846 Nov 20 13:27 o_P_off.out
-rw-r--r-- 1 ubuntu ubuntu    985 Nov 20 13:27 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 276846 Nov 20 13:27 o_P_on.out
-rw-r--r-- 1 ubuntu ubuntu   5520 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   2949 Nov 20 13:27 o_table.py
-rw-r--r-- 1 ubuntu ubuntu   6279 Nov 20 13:27 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    387 Nov 20 13:28 patch_apply.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:30 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5929 Nov 20 15:07 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:06 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    661 Nov 20 15:07 stamps.txt
```
