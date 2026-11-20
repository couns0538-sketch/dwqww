# Seat 052 arm 2

Arm 2, B1b. Source seat 080. Commit e778c1358711c0571e8f5cc4df87083cce98e03a on for-fable-and-opus/grok-080. Switch IdeaB1.

## Patch

sha256 of ~/arm.patch:

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-080` printed e778c1358711c0571e8f5cc4df87083cce98e03a. In the work tree, `git apply --check ~/arm.patch` and then `git apply ~/arm.patch` both succeeded (the shell printed APPLY OK).

## Honesty

Both exes, fresh process per line, no setoption. Pasted from honesty_table.py into honesty_summary.txt:

```
file honesty_b_bench11.txt
line info string bench depth 11 nodes 312866 time 165 nps 1896157
depth 11 nodes 312866
expected 312866
match True
file honesty_b_bench13.txt
line info string bench depth 13 nodes 862329 time 436 nps 1977818
depth 13 nodes 862329
expected 862329
match True
file honesty_b_bench16.txt
line info string bench depth 16 nodes 3024920 time 1432 nps 2112374
depth 16 nodes 3024920
expected 3024920
match True
file honesty_b_perft5.txt
line nodes 4865609
nodes 4865609
expected 4865609
match True
file honesty_p_bench11.txt
line info string bench depth 11 nodes 312866 time 161 nps 1943267
depth 11 nodes 312866
expected 312866
match True
file honesty_p_bench13.txt
line info string bench depth 13 nodes 862329 time 433 nps 1991521
depth 13 nodes 862329
expected 862329
match True
file honesty_p_bench16.txt
line info string bench depth 16 nodes 3024920 time 1435 nps 2107958
depth 16 nodes 3024920
expected 3024920
match True
file honesty_p_perft5.txt
line nodes 4865609
nodes 4865609
expected 4865609
match True
```

Known targets: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. All eight matched.

## Three O runs

Positions file first200.fens, sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines. S14, Threads 1, Hash 16, depth 12. Pasted from otable.py:

exe B (otable_B.txt):

```
file O_B_d12.txt
count 200
sum 9500069
first 41311 24872 28574
```

Table: sum 9,500,069; first three 41,311 / 24,872 / 28,574. Match.

exe P, IdeaB1 false (otable_off.txt):

```
file O_P_off_d12.txt
count 200
sum 9500069
first 41311 24872 28574
compared O_B_d12.txt
differ 0 of 200
equal True
```

Equal to exe B on all 200 positions.

exe P, IdeaB1 true (head of otable_on.txt; the same command's per-position rows are the rest of that file):

```
file O_P_on_d12.txt
count 200
sum 9748678
first 17841 25977 43905
compared O_B_d12.txt
differ 200 of 200
equal False
```

Table: sum 9,748,678; first three 17,841 / 25,977 / 43,905; 200 differ. Match.

## Book

```
uho.zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
uho.epd lines 2632036
uho.epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 052 took every 90th line of uho.epd starting at line 52 (29245 lines). The last 300 of those were held back as controls.

## C-ARRIVE

arrive_check.txt:

```
grep -c setoption name IdeaB1 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

The true-count is 1 or more and the refusal count is 0. The 20 log lines around the first switch setoption are in arrive_check.txt.

## C-HALF

half_pool.txt, from games_tsv.py pool FULL on half.tsv:

```
side FULL: games 400 W-L-D 239-36-125 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 10, 43, 77, 69] Elo +194.34 95% [+166.37, +224.80]
```

FULL's Elo is +194.34, above +20. Pass.

## POOL

16 chunks, 500 games each, 8000 games. Pasted POOL.txt (games_tsv.py pool ON on chunk_*.tsv):

```
side ON: games 8000 W-L-D 2129-2071-3800 pairs 4000 (openings not in exactly 2 games: 0)
ptnml [185, 964, 1643, 1024, 184] Elo +2.52 95% [-2.49, +7.53]
```

## suspicions, not proven

The interval covers zero, so this sample does not separate a small gain from noise. That is the measurement, not a claim that the switch is zero.

Every chunk_*.out has zero lines matching adjudicat, resign, maxmoves, or tablebase. chunk_1.out's result phrases are mates, 3-fold, fifty-move, insufficient material, and stalemate. I did not pass -draw, -resign, -maxmoves, or -tb.

## what I did NOT do

No pull request. No engine source committed. No IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale, or IdeaB1_Cap sent. No arm-10 fallback (the on-sum matched). No opening repeated to add games. No PGN, exe, or book zip committed. The handoff branch had no FABLE_TO_grok2 file at any fetch.

## what I am NOT sure about

The PGN Termination header is the word normal on all 8000 tsv rows. Fastchess still printed mate and rule-draw phrases in the chunk stdout. I am not sure why the header does not name the ending.

/usr/bin/c++ is Clang and failed to link libstdc++. Both builds used g++ 13.3.0. The machine has avx512f and bmi2, so FORGE_PORTABLE was left off. Local git user.name was unset at the seat commit, so that first commit used the existing global identity. Later commits used the local name grok agent.

fastchess wrote an untracked config.json at the repository root while the controls ran. I did not add it. Its resign, draw, maxmoves, and tablebase blocks were enabled false when I opened it.

## times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/052/stamps.txt
?? config.json
?? forge-combo29/grok2/052/POOL.txt
?? forge-combo29/grok2/052/REPORT.md
?? forge-combo29/grok2/052/RESULT.txt

$ ls -la forge-combo29/grok2/052
total 2880
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2089 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    407 Nov 20 13:34 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu    810 Nov 20 13:25 build_notes.txt
-rw-r--r-- 1 ubuntu ubuntu  56283 Nov 20 14:26 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51459 Nov 20 14:26 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55975 Nov 20 14:32 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 14:32 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56522 Nov 20 14:37 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:37 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56719 Nov 20 14:43 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51640 Nov 20 14:43 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56617 Nov 20 14:48 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51604 Nov 20 14:48 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56526 Nov 20 14:53 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51581 Nov 20 14:53 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56344 Nov 20 14:58 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51513 Nov 20 14:58 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55856 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51037 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56358 Nov 20 13:44 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51380 Nov 20 13:44 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56675 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51524 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56607 Nov 20 13:55 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 13:55 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55984 Nov 20 14:00 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51220 Nov 20 14:00 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56227 Nov 20 14:05 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51277 Nov 20 14:05 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56519 Nov 20 14:10 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:10 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56421 Nov 20 14:16 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 14:16 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56646 Nov 20 14:21 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51576 Nov 20 14:21 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46509 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:34 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1023 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42195 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:34 half_tsv_print.txt
-rw-r--r-- 1 ubuntu ubuntu   6701 Nov 20 13:26 harness.py
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:26 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5215 Nov 20 13:26 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 13:26 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5292 Nov 20 13:26 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5292 Nov 20 13:26 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5294 Nov 20 13:26 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:26 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5505 Nov 20 13:26 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    177 Nov 20 13:26 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1034 Nov 20 13:27 honesty_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   1546 Nov 20 13:26 honesty_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281651 Nov 20 13:26 O_B_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    951 Nov 20 13:26 O_B_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 281989 Nov 20 13:26 O_P_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 13:26 O_P_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282937 Nov 20 13:26 O_P_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    984 Nov 20 13:26 O_P_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 otable_B.txt
-rw-r--r-- 1 ubuntu ubuntu    115 Nov 20 13:27 otable_off.txt
-rw-r--r-- 1 ubuntu ubuntu   5818 Nov 20 13:27 otable_on.txt
-rw-r--r-- 1 ubuntu ubuntu   1815 Nov 20 13:26 otable.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    152 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5618 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    224 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    923 Nov 20 15:03 stamps.txt
```
