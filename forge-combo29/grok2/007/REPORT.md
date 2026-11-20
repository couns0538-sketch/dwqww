# Seat 007 arm 7

Arm 7, K4a. Source seat 093. Switch IdeaK4. Source commit ddc850cbf04b8c7a8592624037844077b33c8ab0 on branch for-fable-and-opus/grok-093.

## Patch sha256 and git apply

sha256 of ~/arm.patch: e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9

That matches the arm table. `git apply --check` then `git apply` on the work tree (../work). After the build, `git apply --reverse --check` also succeeded, so the work tree still matched the patch. Pasted from patch_apply.txt:

```
source_branch for-fable-and-opus/grok-093
commit ddc850cbf04b8c7a8592624037844077b33c8ab0
sha256 e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9
file /home/ubuntu/arm.patch
git_apply_reverse_check ok
diff_stat:
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

IdeaK4_Shrink was not sent. It stayed at the patch default, 24.

The host has AVX-512 and BMI2 and g++ 13.3.0, so both builds were Release CMake without FORGE_PORTABLE. Exe B is the base worktree. Exe P is the patched worktree.

## Honesty numbers

Fresh process per line, no setoption. Both engines:

- bench 11 nodes 312866
- bench 13 nodes 862329
- bench 16 nodes 3024920
- go perft 5 nodes 4865609

Pasted from the raw files:

```
honesty_B_bench11.txt: info string bench depth 11 nodes 312866 time 169 nps 1851278
honesty_B_bench13.txt: info string bench depth 13 nodes 862329 time 444 nps 1942182
honesty_B_bench16.txt: info string bench depth 16 nodes 3024920 time 1496 nps 2022005
honesty_B_perft5.txt: nodes 4865609
honesty_P_bench11.txt: info string bench depth 11 nodes 312866 time 165 nps 1896157
honesty_P_bench13.txt: info string bench depth 13 nodes 862329 time 441 nps 1955394
honesty_P_bench16.txt: info string bench depth 16 nodes 3024920 time 1431 nps 2113850
honesty_P_perft5.txt: nodes 4865609
```

## Three O runs

S14, Threads 1, Hash 16, depth 12, 200 positions. Pasted output of o_table.py on o_B.raw, o_Poff.raw, o_Pon.raw:

```
B n=200 sum=9500069 first=41311 24872 28574
Poff n=200 sum=9500069 first=41311 24872 28574
Pon n=200 sum=8921190 first=24693 26341 35070
Poff_differ_from_B 0
Pon_differ_from_B 200
B_expected_sum 9500069 match True
B_expected_first 41311 24872 28574 match True
Pon_expected_sum 8921190 match True
Pon_expected_first 24693 26341 35070 match True
Pon_expected_differ 200 match True
```

Against the arm table: run (1) sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Run (2) IdeaK4 false equals run (1) on all 200 positions. Run (3) IdeaK4 true sum 8,921,190, first three 24,693 / 26,341 / 35,070, 200 positions differ.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 007 took every 90th line starting at line 7: 29245 lines in mine.epd. The last 300 are the controls and were not used by the chunks.

## C-ARRIVE and C-HALF

C-ARRIVE, from arrive_check.txt: switch_true_count 20, bad_count 0. The 20 log lines around the first `setoption name IdeaK4 value true` are in that file. The trace shows fastchess sending that line to engine ON.

C-HALF, pasted output of games_tsv.py pool FULL on half.tsv:

```
side FULL: games 400 W-L-D 230-32-138 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 5, 42, 95, 56] Elo +188.54 95% [+163.15, +215.92]
```

PASS. FULL's Elo is above +20.

## Pool

18 chunks, 9000 games. Pasted POOL.txt (games_tsv.py pool ON on chunk_*.tsv):

```
side ON: games 9000 W-L-D 2376-2352-4272 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [216, 1079, 1872, 1131, 202] Elo +0.93 95% [-3.79, +5.64]
```

## suspicions, not proven

The arrive trace sends IdeaK4 before Hash. match.sh puts the switch on the -engine line and Hash on -each. I did not prove that this order changes any game. The O-run harness sent Hash and S14 before the switch and reproduced the known node counts. C-HALF, with the node limit on the -engine line and the same -each options, gave the 20000-node side +188.54 Elo.

fastchess wrote config.json in the repository root when the last chunk ended. Every "enabled" field in that file is false. The match command has no -draw, -resign, or -maxmoves. Chunk logs name mate, 3-fold repetition, the fifty-move rule, and insufficient mating material. I did not prove that any game was adjudicated.

## what I did NOT do

No pull request. No engine source, exe, net, PGN, or book committed. IdeaK4_Shrink was not sent. Arm 10 was not played. Openings were not repeated. config.json was not committed. This morning's seat 030 PGN was not run through games_tsv.py.

## what I am NOT sure about

I am not sure fastchess applies -engine options and -each options in the order written in match.sh. The arrive trace shows IdeaK4 before Hash.

I am not sure which fastchess default created config.json. I did not pass a config file to fastchess.

## times: see stamps.txt

## git status --short and ls -la

The pasted command output follows.

```
$ git status --short
 M forge-combo29/grok2/007/stamps.txt
?? config.json
?? forge-combo29/grok2/007/POOL.txt
?? forge-combo29/grok2/007/REPORT.md
?? forge-combo29/grok2/007/RESULT.txt
?? forge-combo29/grok2/007/chunk_18.out
?? forge-combo29/grok2/007/chunk_18.tsv

$ ls -la forge-combo29/grok2/007
total 3016
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2144 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56581 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51460 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56259 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56314 Nov 20 14:35 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51506 Nov 20 14:35 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56168 Nov 20 14:40 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51505 Nov 20 14:40 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56419 Nov 20 14:44 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51627 Nov 20 14:44 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56258 Nov 20 14:49 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 14:49 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56167 Nov 20 14:54 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51395 Nov 20 14:54 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  57064 Nov 20 14:59 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51631 Nov 20 14:59 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56337 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51156 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56048 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51261 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56526 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51525 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56343 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56679 Nov 20 13:56 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 13:56 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56529 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51459 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56167 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  57132 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51579 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56699 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46731 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:31 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42205 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:24 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:24 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:24 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    305 Nov 20 13:24 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:26 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:26 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    303 Nov 20 13:26 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    305 Nov 20 13:26 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:26 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    828 Nov 20 13:24 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281789 Nov 20 13:26 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    864 Nov 20 13:26 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 281833 Nov 20 13:26 o_Poff.raw
-rw-r--r-- 1 ubuntu ubuntu    863 Nov 20 13:27 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 280991 Nov 20 13:27 o_Pon.raw
-rw-r--r-- 1 ubuntu ubuntu   5262 Nov 20 13:26 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1727 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    379 Nov 20 13:27 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    440 Nov 20 13:27 patch_apply.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5511 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1062 Nov 20 15:01 stamps.txt
```
