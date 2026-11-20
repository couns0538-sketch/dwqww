# REPORT seat 043

Arm 3, id B8a, source seat 078, commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0, SWITCH IdeaB8. Model Grok 4.7.

## Patch sha256 and git apply

The patch file sha256 matches the arm table. `git apply --check` and `git apply` were run in the work tree. The work-tree diff is still that patch. Pasted from `patch_check.txt`:

```
sha256sum ~/arm.patch
b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
git diff --stat in /agent/repos/work
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

IdeaB8_Weight and IdeaB8_Swing were left at their defaults and were never sent.

## Honesty numbers

Both exes, a fresh process per line, no setoption before the measured command. Targets were bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. The machine has BMI2 and AVX-512, so the release build kept the default `-march=x86-64-v4` and did not set FORGE_PORTABLE. Compiler was g++ 13.3.0.

Pasted from `tables.py` (`tables_step2.txt`):

```
honesty
honesty_B_bench11 312866
honesty_B_bench13 862329
honesty_B_bench16 3024920
honesty_B_perft5 4865609
honesty_P_bench11 312866
honesty_P_bench13 862329
honesty_P_bench16 3024920
honesty_P_perft5 4865609
```

## Three O runs

S14, Threads 1, Hash 16, depth 12, 200 positions. Table for arm 3: exe B sum 9500069, first three 41311 / 24872 / 28574; SWITCH false equal on all 200; SWITCH true sum 9295189, first three 24947 / 29945 / 39302, 200 differ.

Pasted from the same `tables.py` run:

```
o_runs
o_B positions 200 sum 9500069
o_B first 41311 / 24872 / 28574
o_off positions 200 sum 9500069
o_off first 41311 / 24872 / 28574
o_off differ 0 length_gap 0
o_on positions 200 sum 9295189
o_on first 24947 / 29945 / 39302
o_on differ 200 length_gap 0
```

`cmp` of `o_B.rows` and `o_off.rows` reported the files identical. on_ok = yes.

## Book

Pasted from `book_sha.txt`. Both hashes match the brief, 2632036 lines. book = ok.

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Seat 043 took every 90th line of that book starting at line 43 (`mine.epd`, 29245 lines). The last 300 lines were held out. Chunks used the top of the book only.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c "setoption name IdeaB8 value true"` on the trace log was 20. `grep -c -E "unknown option|invalid value|No such option"` was 0. The two counts and the 20 log lines around the first switch setoption are in `arrive_check.txt`. arrive = ok.

C-HALF pasted from `half_pool.txt`. FULL's Elo is above +20, so the control passed.

```
side FULL: games 400 W-L-D 231-38-131 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 51, 74, 65] Elo +182.83 95% [+155.70, +212.18]
```

## POOL and chunks

21 chunks, each 500 games, 10500 games. No chunk was marked FAILED. Play stopped with `minute 95: no new chunk` after chunk 21. Pasted from `POOL.txt`:

```
side ON: games 10500 W-L-D 2961-2626-4913 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [207, 1198, 2167, 1409, 269] Elo +11.09 95% [+6.74, +15.44]
```

## suspicions, not proven

None. Every opening in the pool is in exactly two games, and the ON side is the side scored.

## what I did NOT do

I did not open a pull request. I did not commit engine source, the binary, the net, or any PGN. I did not send the patch's other options. I did not turn on adjudication. I did not play the held-out 300 openings, and I did not fall back to arm 10. I did not replay the morning seat 030 PGN named as a known answer of `games_tsv.py`. fastchess wrote `config.json` in the repository root because the match inherited that working directory; I deleted that file and did not commit it.

## what I am NOT sure about

I did not find any `FABLE_TO_grok2_<N>.md` on the handoff branch at the fetches during this run. The `ls -la` pasted below records `REPORT.md` as it was before this status block was appended, so that one file's size is short of the final bytes.

## times

times: see stamps.txt

## git status --short and ls -la
```
$ git status --short
 M forge-combo29/grok2/043/stamps.txt
?? forge-combo29/grok2/043/POOL.txt
?? forge-combo29/grok2/043/REPORT.md
?? forge-combo29/grok2/043/RESULT.txt
?? forge-combo29/grok2/043/patch_check.txt

$ ls -la forge-combo29/grok2/043
total 3408
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2312 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    259 Nov 20 13:30 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:26 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56748 Nov 20 14:13 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51487 Nov 20 14:13 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55689 Nov 20 14:17 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51320 Nov 20 14:17 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56394 Nov 20 14:21 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51490 Nov 20 14:21 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56613 Nov 20 14:25 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51617 Nov 20 14:25 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56759 Nov 20 14:29 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51553 Nov 20 14:29 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56243 Nov 20 14:33 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51535 Nov 20 14:33 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56261 Nov 20 14:38 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51466 Nov 20 14:38 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56183 Nov 20 14:42 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 14:42 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56305 Nov 20 14:46 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 14:46 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56039 Nov 20 14:50 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51492 Nov 20 14:50 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56518 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51262 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56027 Nov 20 14:54 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51523 Nov 20 14:54 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56251 Nov 20 14:58 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:58 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56557 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56299 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51367 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56373 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51238 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55943 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51305 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55972 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56441 Nov 20 14:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56404 Nov 20 14:05 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51572 Nov 20 14:05 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56356 Nov 20 14:09 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:09 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:24 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46761 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:33 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1031 Nov 20 13:33 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42301 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   2410 Nov 20 13:25 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1015 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:26 o_B.err
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu 281812 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:26 o_off.err
-rw-r--r-- 1 ubuntu ubuntu    827 Nov 20 13:26 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:26 o_off.rows
-rw-r--r-- 1 ubuntu ubuntu 281999 Nov 20 13:26 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu      0 Nov 20 13:26 o_on.err
-rw-r--r-- 1 ubuntu ubuntu    826 Nov 20 13:26 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1893 Nov 20 13:26 o_on.rows
-rw-r--r-- 1 ubuntu ubuntu 282064 Nov 20 13:26 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   6626 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    379 Nov 20 15:01 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:26 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:26 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:26 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:26 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:26 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:26 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4641 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    758 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2161 Nov 20 13:28 tables.py
-rw-r--r-- 1 ubuntu ubuntu    466 Nov 20 13:28 tables_step2.txt
```
