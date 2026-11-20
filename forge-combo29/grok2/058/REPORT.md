# Seat 058, arm 8 (K4b)

Source seat 043. Switch IdeaK4. Morning commit 2f38a63656ec17062b581c933fcc77d961b946f1 on for-fable-and-opus/grok-043. Model Grok 4.7.

## Patch

sha256 of ~/arm.patch (the file taken from that commit's forge-combo29/grok/043/idea.patch.txt):

```
b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
```

That is the table's sha256. `git apply --check` then `git apply` on the work tree at 6b98f2170a3210e71beed04bbd2553972c253ed7 both succeeded. `git diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)
```

IdeaK4_Shrink was left at the patch default (32). It was never sent.

## Honesty

Fresh process, no setoption. Expected: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 191 nps 1638041
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 569 nps 1515516
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 2417 nps 1251518
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 171 nps 1829625
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 571 nps 1510208
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 2006 nps 1507936
honesty_P_perft5.txt:nodes 4865609
```

Both exes match. honesty=ok.

## Three O runs

first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8 (200 lines). S14, Threads 1, Hash 16, depth 12. Table for arm 8: exe B sum 9,500,069 first 41,311 / 24,872 / 28,574; switch false equal on all 200; switch true sum 8,983,632 first 23,741 / 21,846 / 35,911; 200 differ.

`python3 o_table.py O_B.txt O_P_off.txt O_P_on.txt`:

```
B n=200 sum=9500069 first=41311 24872 28574
Poff n=200 sum=9500069 first=41311 24872 28574
Pon n=200 sum=8983632 first=23741 21846 35911
Poff equal to B: 200 of 200
Pon differ from B: 200 of 200
```

off_identical=yes. on_sum=8983632. on_ok=yes.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. book=ok. Seat 058 takes line 58 and every 90th line after it: 29245 openings. Chunks used the first 4500. The reserved tail starts at line 28946 of mine.epd.

## C-ARRIVE and C-HALF

C-ARRIVE, from arrive_check.txt:

```
grep -c setoption name IdeaK4 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

arrive=ok.

C-HALF, `python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 233-27-140 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 9, 40, 87, 64] Elo +197.87 95% [+171.49, +226.49]
```

half_elo=+197.87, above +20.

## POOL

18 chunks, 9000 games. `python3 games_tsv.py pool ON chunk_*.tsv` wrote POOL.txt:

```
side ON: games 9000 W-L-D 2228-2539-4233 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [236, 1209, 1864, 1012, 179] Elo -12.01 95% [-16.72, -7.31]
```

grep of every chunk_*.out for adjudicat, resign, or maxmoves: 0 hits in each file.

## suspicions, not proven

None beyond the measurement itself. The interval lies entirely below zero. I did not replay any opening, so I did not test whether a second run would be byte-identical.

## what I did NOT do

No pull request. No adjudication flags. IdeaK4_Shrink was not sent. No portable build: this CPU has AVX-512 and BMI2, so the default Release march x86-64-v4 was used. Arm 10 was not played, because run (3) matched. No FABLE_TO_grok2 file was on handoff/fable-opus-combo29-all-20261114 at any fetch during this run. No engine source, exe, net, or PGN was committed. play.sh stopped itself with "minute 95: no new chunk" after chunk 18. Nothing was killed.

## what I am NOT sure about

The morning commit's engine sources, compared with `git diff 2f38a636 --` the three patched paths, differ by this same 20-line patch: that commit holds the patch file and the unpatched sources. The node counts still matched the table, which is the check the brief asked for. I am not sure a different Elo program would print the same interval to the last digit; the numbers above are the script's.

times: see stamps.txt

## git status --short and ls -la

Pasted below after this file and RESULT.txt were written.

```
$ git status --short
 M forge-combo29/grok2/058/stamps.txt
?? config.json
?? forge-combo29/grok2/058/POOL.txt
?? forge-combo29/grok2/058/REPORT.md
?? forge-combo29/grok2/058/RESULT.txt
?? forge-combo29/grok2/058/chunk_18.out
?? forge-combo29/grok2/058/chunk_18.tsv

$ ls -la forge-combo29/grok2/058
total 3120
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2270 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56540 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51414 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56162 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51478 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56115 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56661 Nov 20 14:36 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 14:36 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56381 Nov 20 14:41 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51422 Nov 20 14:41 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56652 Nov 20 14:46 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 14:46 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56452 Nov 20 14:51 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51613 Nov 20 14:51 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56661 Nov 20 14:55 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:55 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56281 Nov 20 15:00 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51375 Nov 20 15:00 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56417 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51180 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  55965 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51257 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56521 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51507 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56282 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51575 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56407 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51410 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56184 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51371 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56426 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51612 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56316 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51362 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46860 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1095 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42228 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:25 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:25 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:25 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    963 Nov 20 13:25 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    950 Nov 20 13:26 O_B.meta
-rw-r--r-- 1 ubuntu ubuntu 309159 Nov 20 13:26 O_B.txt
-rw-r--r-- 1 ubuntu ubuntu    991 Nov 20 13:26 O_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 309185 Nov 20 13:26 O_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    990 Nov 20 13:26 O_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 307995 Nov 20 13:26 O_P_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   3713 Nov 20 13:26 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1252 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:27 O_TABLE.txt
-rw-r--r-- 1 ubuntu ubuntu    211 Nov 20 13:27 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:25 patch.sha256
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4888 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    740 Nov 20 15:03 stamps.txt
```
