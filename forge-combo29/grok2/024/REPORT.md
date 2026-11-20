# grok2 seat 024 arm 4 B8b

Arm 4, source seat 028, switch IdeaB8, commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75.

## Patch

sha256 of ~/arm.patch (git show of forge-combo29/grok/028/idea.patch.txt):

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
```

Expected f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474. git apply --check and git apply both exited 0. The applied diff stat was search.hpp, search.cpp, uci.cpp.

## Honesty

Fresh process per line, no setoption. Numbers read back from the raw honesty_*.txt files:

```
B bench11 nodes 312866 expect 312866 OK
B bench13 nodes 862329 expect 862329 OK
B bench16 nodes 3024920 expect 3024920 OK
B perft5 nodes 4865609 expect 4865609 OK
P bench11 nodes 312866 expect 312866 OK
P bench13 nodes 862329 expect 862329 OK
P bench16 nodes 3024920 expect 3024920 OK
P perft5 nodes 4865609 expect 4865609 OK
```

## O runs

Expected exe B: sum 9500069, first 41311 / 24872 / 28574.
Expected exe P switch false: equal on all 200.
Expected exe P switch true: sum 9718009, first 17283 / 17878 / 31115, 200 differ.

```
B sum 9500069 first 41311 24872 28574
Poff sum 9500069 first 41311 24872 28574
Pon sum 9718009 first 17283 17878 31115
Poff identical to B: 200 of 200
Pon positions differing from B: 200 of 200
```

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Expected zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 and epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a, 2632036 lines.

## C-ARRIVE and C-HALF

Arrive check counts (full extract is arrive_check.txt):

```
command: grep -c "setoption name IdeaB8 value true" ~/arrive.log
20
command: grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

C-HALF pool of side FULL (half_pool.txt):

```
side FULL: games 400 W-L-D 237-26-137 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 38, 91, 64] Elo +203.83 95% [+177.53, +232.43]
```

FULL Elo +203.83 is above +20.

## Pool

Chunks: 21. Games: 10500.

```
side ON: games 10500 W-L-D 3000-2662-4838 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [234, 1163, 2175, 1387, 291] Elo +11.19 95% [+6.77, +15.61]
```

## suspicions, not proven

None. The on-sum, the off identity, and the honesty counts matched the table on the first run.

## what I did NOT do

I did not open a pull request. I did not adjudicate games. I did not send IdeaB8_Weight or IdeaB8_Swing. I did not commit an engine binary, a net, a PGN, or an engine source file. I did not play the last 300 openings of mine.epd (those are ctl.epd). I did not change any branch except for-fable-and-opus/grok2-024.

## what I am NOT sure about

The RESULT.txt id field is B8b, the label of arm 4 in the brief's table. No other id was given. fastchess printed the same C-HALF Elo as games_tsv.py; I used the games_tsv.py figure.

## times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/024/stamps.txt
?? config.json
?? forge-combo29/grok2/024/POOL.txt
?? forge-combo29/grok2/024/REPORT.md
?? forge-combo29/grok2/024/RESULT.txt
?? forge-combo29/grok2/024/step5_report.py
```

## ls -la

The size of REPORT.md in this listing is from before these two sections were appended.

```
total 3544
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2268 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56937 Nov 20 14:12 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:12 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56559 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51312 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56522 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51269 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56091 Nov 20 14:25 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51502 Nov 20 14:25 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56115 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51500 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56711 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51432 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56120 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51367 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56114 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56200 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56337 Nov 20 14:51 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51528 Nov 20 14:51 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51152 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56078 Nov 20 14:55 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51400 Nov 20 14:55 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56501 Nov 20 15:00 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51673 Nov 20 15:00 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56106 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51318 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56187 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56093 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51383 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56745 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51541 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56020 Nov 20 13:56 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51305 Nov 20 13:56 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56049 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56069 Nov 20 14:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 14:08 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51348 Nov 20 14:08 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   1095 Nov 20 13:25 compare_o.py
-rw-r--r-- 1 ubuntu ubuntu   2802 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46745 Nov 20 13:29 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:29 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1027 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42292 Nov 20 13:29 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    290 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    243 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 13:24 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    286 Nov 20 13:24 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    290 Nov 20 13:24 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    243 Nov 20 13:24 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3169 Nov 20 13:24 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1019 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu 318078 Nov 20 13:25 o_B.log
-rw-r--r-- 1 ubuntu ubuntu    779 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu  31946 Nov 20 13:25 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu 318284 Nov 20 13:25 o_Poff.log
-rw-r--r-- 1 ubuntu ubuntu    813 Nov 20 13:25 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu  31947 Nov 20 13:25 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu 318900 Nov 20 13:25 o_Pon.log
-rw-r--r-- 1 ubuntu ubuntu    812 Nov 20 13:25 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu  32159 Nov 20 13:25 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   5509 Nov 20 13:24 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 15:05 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   3051 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    798 Nov 20 15:05 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   6798 Nov 20 15:05 step5_report.py
```
