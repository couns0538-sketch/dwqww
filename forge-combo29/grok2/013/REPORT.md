# grok2 seat 013

Arm 3, B8a, source seat 078, switch IdeaB8, commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0.
Model Grok 4.7. Branch for-fable-and-opus/grok2-013.

## Patch

sha256 of ~/arm.patch matched the arm table. `git apply --check` then `git apply` on the work tree succeeded before the build. The work tree still shows that diff:

```
sha256 b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
expected b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

The CPU advertises AVX-512 and BMI2, so both exes were Release builds with the CMake default `-march=x86-64-v4` and FORGE_PORTABLE left off. Exe P is `/agent/repos/work/forge-combo29/build/forge`. Exe B is `/agent/repos/base/forge-combo29/build/forge`.

## Honesty

`python3 honesty_table.py` in this folder:

```
honesty_B_bench11.txt: info string bench depth 11 nodes 312866 time 197 nps 1588152
honesty_B_bench13.txt: info string bench depth 13 nodes 862329 time 491 nps 1756270
honesty_B_bench16.txt: info string bench depth 16 nodes 3024920 time 1556 nps 1944035
honesty_B_perft5.txt: nodes 4865609
honesty_P_bench11.txt: info string bench depth 11 nodes 312866 time 291 nps 1075140
honesty_P_bench13.txt: info string bench depth 13 nodes 862329 time 648 nps 1330754
honesty_P_bench16.txt: info string bench depth 16 nodes 3024920 time 1756 nps 1722619
honesty_P_perft5.txt: nodes 4865609
```

Required nodes: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match.

## O runs

`python3 o_table.py o_B_raw.txt o_Poff_raw.txt o_Pon_raw.txt`:

```
B n=200 sum=9500069 first=41311 24872 28574
Poff n=200 sum=9500069 first=41311 24872 28574
Pon n=200 sum=9295189 first=24947 29945 39302
Poff equal to B: 200 of 200
Pon differ from B: 200 of 200
```

Against the arm table: run (1) sum 9500069 and first three 41311 / 24872 / 28574. Run (2) equal on all 200. Run (3) sum 9295189, first three 24947 / 29945 / 39302, 200 differ. All three match. Options sent are in the `.meta` files: Threads 1, Hash 16, then S14, and IdeaB8 false or true on exe P only. The patched engine also advertises IdeaB8_Weight and IdeaB8_Swing. They were not sent.

## Book

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
  2632036 /home/ubuntu/uho.epd
```

Both digests match the brief. Seat 013 took every 90th line of the epd starting at line 13 (29245 lines in mine.epd). The last 300 lines were the controls and were not used by the chunks.

## C-ARRIVE

`grep` counts written to arrive_check.txt: `setoption name IdeaB8 value true` = 20, and `unknown option|invalid value|No such option` = 0. The 20 log lines around the first true setoption are in that file.

## C-HALF

`python3 ~/games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 234-30-136 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 44, 86, 63] Elo +195.51 95% [+169.29, +223.92]
```

FULL at 20000 nodes against HALF at 10000, switch off. Elo +195.51 is above +20.

## Pool

18 chunks, 9000 games, every termination `normal`. `python3 ~/games_tsv.py pool ON chunk_*.tsv` wrote POOL.txt:

```
side ON: games 9000 W-L-D 2537-2260-4203 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [176, 1053, 1827, 1206, 238] Elo +10.70 95% [+5.97, +15.43]
```

ON is IdeaB8 true. OFF is IdeaB8 false. 4500 opening pairs, none shared across a different count than 2.

## suspicions, not proven

Chunk 13 took longer on the wall clock than the chunks around it (done stamp 14:36:52Z after chunk 12 at 14:28:32Z). Its tsv is 500 games and the termination column is normal. I have no evidence those games were played differently.

## what I did NOT do

No pull request. No engine source committed. No adjudication, resign, draw, maxmoves, or tablebase flags. No opening repeated to add games. Arm 10 was not played. fastchess was not killed; play.sh stopped itself with `minute 95: no new chunk` after chunk 18. No FABLE_TO_grok2 note was on the handoff branch at the fetches, so nothing there changed the run.

## what I am NOT sure about

The result field `id` is B8a, the short name on arm row 3. The channel fetch used a depth-1 fetch of handoff/fable-opus-combo29-all-20261114; a note added on that branch after the last fetch (the chunk 18 push) would not be in this report.

## times: see stamps.txt

## status and listing

```
$ git status --short
 M forge-combo29/grok2/013/stamps.txt
?? config.json
?? forge-combo29/grok2/013/POOL.txt
?? forge-combo29/grok2/013/REPORT.md
?? forge-combo29/grok2/013/RESULT.txt
?? forge-combo29/grok2/013/honesty_table.out
?? forge-combo29/grok2/013/patch_check.txt

$ ls -la forge-combo29/grok2/013
total 3008
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2205 Nov 20 13:25 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    366 Nov 20 13:28 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56210 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51604 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 14:23 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51444 Nov 20 14:23 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56185 Nov 20 14:28 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51467 Nov 20 14:28 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56206 Nov 20 14:36 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:36 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56630 Nov 20 14:41 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:41 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56507 Nov 20 14:46 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:46 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56351 Nov 20 14:51 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 14:51 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56433 Nov 20 14:56 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51518 Nov 20 14:56 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56218 Nov 20 15:01 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51517 Nov 20 15:01 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56542 Nov 20 13:33 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51365 Nov 20 13:33 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56231 Nov 20 13:37 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51354 Nov 20 13:37 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56277 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56361 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51347 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56276 Nov 20 13:52 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51383 Nov 20 13:52 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56601 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51454 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56311 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56402 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51488 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56601 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51499 Nov 20 14:13 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:25 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46824 Nov 20 13:28 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:28 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1030 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42312 Nov 20 13:28 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    580 Nov 20 15:04 honesty_table.out
-rw-r--r-- 1 ubuntu ubuntu    374 Nov 20 13:24 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:25 match.sh
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:23 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:23 o_B_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu 281719 Nov 20 13:23 o_B_raw.txt
-rw-r--r-- 1 ubuntu ubuntu   5082 Nov 20 13:23 o_harness.py
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:23 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:23 o_Poff_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu 281908 Nov 20 13:23 o_Poff_raw.txt
-rw-r--r-- 1 ubuntu ubuntu    829 Nov 20 13:23 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu   1893 Nov 20 13:23 o_Pon_nodes.txt
-rw-r--r-- 1 ubuntu ubuntu 282046 Nov 20 13:23 o_Pon_raw.txt
-rw-r--r-- 1 ubuntu ubuntu    195 Nov 20 13:24 o_table.out
-rw-r--r-- 1 ubuntu ubuntu   1469 Nov 20 13:23 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    401 Nov 20 15:04 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:25 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4733 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    661 Nov 20 15:04 stamps.txt
```
