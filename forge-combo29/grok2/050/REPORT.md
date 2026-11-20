# grok2 seat 050

## Arm and source seat

Arm 10, table label K3. Source seat none. SWITCH HindsightDepth. There is no morning patch: exe P is exe B, both built from commit 6b98f2170a3210e71beed04bbd2553972c253ed7.

## Patch sha256 and git apply

No patch file. git apply was not run. The two release binaries (base worktree and work worktree) have the same sha256:

e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83

The first cmake picked /usr/bin/c++ (Clang 18) and failed to link libstdc++. I configured again with -DCMAKE_CXX_COMPILER=g++ (g++ 13.3.0). The machine has AVX-512 and BMI2, so I did not pass -DFORGE_PORTABLE or -DFORGE_MARCH. id name: Chess Engine Forge 6.4.24 candidate.

## Honesty

Fresh process per line, no setoption. Expected nodes: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609. Both exes matched. Pasted output of summarize_o.py:

```
forge-combo29/grok2/050/honesty_B_bench11.txt info string bench depth 11 nodes 312866 time 178 nps 1757674
forge-combo29/grok2/050/honesty_B_bench13.txt info string bench depth 13 nodes 862329 time 474 nps 1819259
forge-combo29/grok2/050/honesty_B_bench16.txt info string bench depth 16 nodes 3024920 time 1480 nps 2043864
forge-combo29/grok2/050/honesty_B_perft5.txt nodes 4865609
forge-combo29/grok2/050/honesty_P_bench11.txt info string bench depth 11 nodes 312866 time 170 nps 1840388
forge-combo29/grok2/050/honesty_P_bench13.txt info string bench depth 13 nodes 862329 time 453 nps 1903596
forge-combo29/grok2/050/honesty_P_bench16.txt info string bench depth 16 nodes 3024920 time 1468 nps 2060572
forge-combo29/grok2/050/honesty_P_perft5.txt nodes 4865609
B n=200 sum=9500069 first=41311 / 24872 / 28574 differ=0
Poff n=200 sum=9500069 first=41311 / 24872 / 28574 differ=0
Pon n=200 sum=9845650 first=23395 / 31504 / 35958 differ=200
```

## Three O runs

Table for arm 10: run (1) sum 9500069, first three 41311 / 24872 / 28574. Run (3) sum 9845650, first three 23395 / 31504 / 35958, 200 positions differ. S14, Threads 1, Hash 16, go depth 12, 200 FENs (sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8).

(1) exe B, switch not sent: sum 9500069, first 41311 / 24872 / 28574. Matches the table.
(2) exe P, HindsightDepth false: same sum, same first three, 0 of 200 differ from (1).
(3) exe P, HindsightDepth true: sum 9845650, first 23395 / 31504 / 35958, 200 differ. Matches the table.

Raw transcripts: o_B.txt, o_Poff.txt, o_Pon.txt. The block above is the committed script summarize_o.py reading those files.

## Book

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 050 takes every 90th line of the epd starting at line 50 (29245 lines in mine.epd). Chunks used lines 1 through 5000 of mine.epd. The reserved tail is the last 300 lines (ctl.epd), which the chunks did not reach.

## C-ARRIVE and C-HALF

C-ARRIVE: grep -c of `setoption name HindsightDepth value true` in arrive.log was 20. grep -c of `unknown option|invalid value|No such option` was 0. The 20 surrounding log lines are in arrive_check.txt.

C-HALF: pasted output of games_tsv.py pool FULL on half.tsv:

```
side FULL: games 400 W-L-D 241-31-128 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 43, 82, 68] Elo +202.63 95% [+175.57, +232.11]
```

FULL (20000 nodes) against HALF (10000 nodes), both with HindsightDepth false. Elo +202.63 is above +20.

## POOL.txt and chunks

20 chunks, 500 games each, 10000 games. Each chunk_N.tsv has 500 lines. play.log has no FAILED line. Every termination field is `normal`. Pasted POOL.txt (games_tsv.py pool ON on chunk_1.tsv through chunk_20.tsv):

```
side ON: games 10000 W-L-D 2822-2598-4580 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [229, 1158, 2034, 1318, 261] Elo +7.78 95% [+3.25, +12.32]
```

## suspicions, not proven

None. I did not run a second Elo estimator. The +7.78 and the interval are only what games_tsv.py printed.

## what I did NOT do

I did not open a pull request. I did not apply a patch or edit engine source. I did not pass adjudication flags to fastchess (no -draw, -resign, -maxmoves, no tablebases). I did not play the reserved last 300 openings. I did not send any option besides the S14 list, Threads, Hash, OwnBook false, and HindsightDepth. No FABLE_TO_grok2 file was on the handoff branch at any fetch. fastchess wrote config.json in the repository root (the match was started from that directory). Its resign, draw, maxmoves, and tb_adjudication enabled fields are false. I did not commit config.json.

## what I am NOT sure about

The RESULT id field is K3, the label on arm 10's row of the brief. The brief does not define ID separately from that label. Match options were sent by fastchess; the arrive trace shows HindsightDepth value true, and the saved fastchess config lists the same option values as match.sh, but the send order in the trace is not the S14 order used by o_run.py.

## times: see stamps.txt


## git status --short

```
 M forge-combo29/grok2/050/stamps.txt
?? config.json
?? forge-combo29/grok2/050/POOL.txt
?? forge-combo29/grok2/050/REPORT.md
?? forge-combo29/grok2/050/RESULT.txt
```

## ls -la forge-combo29/grok2/050

```
total 3268
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2200 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    259 Nov 20 13:33 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56210 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51565 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56269 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56304 Nov 20 14:23 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51469 Nov 20 14:23 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56299 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56095 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51306 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56283 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51561 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56344 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51595 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56221 Nov 20 14:45 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51582 Nov 20 14:45 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56151 Nov 20 14:49 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51661 Nov 20 14:49 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56015 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51641 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56368 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51284 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55982 Nov 20 14:58 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51387 Nov 20 14:58 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56507 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51252 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56219 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51248 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56476 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51335 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55815 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51312 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56065 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51556 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56115 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51251 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56159 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56238 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51505 Nov 20 14:11 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46667 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1065 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42322 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4036 Nov 20 13:26 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1049 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    924 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281844 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    966 Nov 20 13:27 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 281817 Nov 20 13:27 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    965 Nov 20 13:27 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 281968 Nov 20 13:27 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   6185 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    942 Nov 20 13:28 o_summary.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5422 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    230 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     78 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1180 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1988 Nov 20 13:26 summarize_o.py
```
