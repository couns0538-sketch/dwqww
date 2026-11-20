# grok2 seat 020

## Arm and source seat

Arm 10, row K3. Source seat none. SWITCH HindsightDepth. There is no patch: exe P is the base engine.

Both release builds used CMake with `CMAKE_CXX_COMPILER=g++` (g++ 13.3.0). `/usr/bin/c++` is clang 18 and its link test failed with `cannot find -lstdc++`. `/proc/cpuinfo` has `avx512f` and `bmi2`, so the build left `FORGE_PORTABLE` off and kept the CMake default `-march=x86-64-v4`.

exe B: `/agent/repos/base/forge-combo29/build/forge`
exe P: `/agent/repos/work/forge-combo29/build/forge`
sha256 of both, from the `.meta` files: `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
id name: Chess Engine Forge 6.4.24 candidate

Matches in `match.sh` use the exe B path, because arm 10 says exe P is exe B. The two files have the same sha256.

## Patch sha256 and git apply

No patch. `idea.patch.txt` was not fetched. `git apply` was not run. patch=none.

## Honesty numbers

`python3 read_runs.py honesty` on the raw files (also saved as `o_table.txt`):

```
file	nodes	expected	match
honesty_B_bench11.txt	312866	312866	yes
honesty_B_bench13.txt	862329	862329	yes
honesty_B_bench16.txt	3024920	3024920	yes
honesty_B_perft5.txt	4865609	4865609	yes
honesty_P_bench11.txt	312866	312866	yes
honesty_P_bench13.txt	862329	862329	yes
honesty_P_bench16.txt	3024920	3024920	yes
honesty_P_perft5.txt	4865609	4865609	yes
```

Each line was a fresh process. The harness sent `uci` (to record id name) and the bench or perft command. It sent no setoption.

## Three O runs

Known table, run (1) and (2): sum 9,500,069; first three 41,311 / 24,872 / 28,574; (2) equal to (1) on all 200.
Known table, run (3), arm 10: sum 9,845,650; first three 23,395 / 31,504 / 35,958; 200 differ.

`python3 read_runs.py orun` on `o_B.raw`, `o_P_off.raw`, `o_P_on.raw`:

```
B positions 200
sum 9500069
first 41311 24872 28574
Poff positions 200
sum 9500069
first 41311 24872 28574
differ_from_base 0 of 200
Pon positions 200
sum 9845650
first 23395 31504 35958
differ_from_base 200 of 200
```

Run (1), run (2), and run (3) match the table. on_ok=yes. off_identical=yes.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. book=ok. Seat 020 takes every 90th line of `uho.epd` starting at line 20. The last 300 of those lines were kept for the controls. Chunk openings are the lines above that tail. A check of the 18 finished chunks found 4500 openings, 4500 unique, and 0 in the control tail.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`: `setoption name HindsightDepth value true` count 20; `unknown option|invalid value|No such option` count 0. arrive=ok.

C-HALF, `python3 games_tsv.py pool FULL half.tsv` (`half_pool.txt`):

```
side FULL: games 400 W-L-D 238-26-136 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 4, 45, 86, 65] Elo +205.04 95% [+179.52, +232.71]
```

FULL's Elo is +205.04, above +20. half_elo=+205.04.

## POOL.txt and chunks

18 chunks, 9000 games, each `chunk_N.tsv` has 500 lines. `play.log` has no FAILED line. `play.out` ends with `minute 95: no new chunk`.

`python3 games_tsv.py pool ON chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 9000 W-L-D 2470-2268-4262 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [178, 1040, 1927, 1112, 243] Elo +7.80 95% [+3.12, +12.48]
```

## Suspicions, not proven

fastchess wrote `/agent/repos/dwqww/config.json` because `play.sh` was started with the repository as its cwd. I opened that file. `resign.enabled`, `draw.enabled`, `maxmoves.enabled`, `tb_adjudication.enabled`, and `sprt.enabled` are all false. Both engine commands are the base `forge` binary, HindsightDepth true against false, nodes 20000 on both. I did not commit `config.json`. The chunk `.out` files do not contain the word adjudication. This is a suspicion about the file's presence, not a claim that a game was cut short.

## What I did NOT do

I did not fetch or apply a patch. I did not edit engine source. I did not open a pull request. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not commit a PGN, an executable, a net file, or `config.json`. I did not start a chunk after `play.sh` printed `minute 95: no new chunk`. I did not force-push. The handoff branch had no `FABLE_TO_grok2_*.md` at STEP 1 or at any STEP 4 push, so I did not touch `~/STOP_PLAY`.

## What I am NOT sure about

I am not sure the arm id string is required to be `K3`. That is the label on row 10 of THE 10 ARMS, and it is what RESULT.txt uses.

I sent `uci` before each honesty command. I am not sure the brief wanted that extra command. No setoption was sent, and the four honesty node counts still matched.

## Times

times: see stamps.txt

## git status --short and ls -la

The two command outputs are appended below this line.

```
$ git status --short
A  forge-combo29/grok2/020/POOL.txt
AM forge-combo29/grok2/020/REPORT.md
A  forge-combo29/grok2/020/RESULT.txt
M  forge-combo29/grok2/020/stamps.txt
?? config.json

$ ls -la forge-combo29/grok2/020
total 3060
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2271 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56739 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51508 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56546 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51636 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56555 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51456 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56584 Nov 20 14:35 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51486 Nov 20 14:35 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56268 Nov 20 14:39 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51412 Nov 20 14:39 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56317 Nov 20 14:44 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51577 Nov 20 14:44 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56671 Nov 20 14:49 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51570 Nov 20 14:49 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56605 Nov 20 14:54 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51587 Nov 20 14:54 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56134 Nov 20 14:59 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51462 Nov 20 14:59 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56172 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51197 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56559 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51246 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55926 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51348 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56375 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51497 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56149 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51459 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56279 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51439 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55989 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56142 Nov 20 14:11 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 14:11 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56317 Nov 20 14:16 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51365 Nov 20 14:16 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46731 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1144 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42223 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   8481 Nov 20 13:26 harness.py
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 13:26 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:26 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:26 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    196 Nov 20 13:26 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:26 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    198 Nov 20 13:26 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1049 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu 282296 Nov 20 13:26 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    925 Nov 20 13:26 o_B.raw.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu 282290 Nov 20 13:27 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    968 Nov 20 13:27 o_P_off.raw.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 o_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu 282175 Nov 20 13:27 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu    966 Nov 20 13:27 o_P_on.raw.meta
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:28 o_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu    825 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   2872 Nov 20 13:28 read_runs.py
-rw-r--r-- 1 ubuntu ubuntu   5170 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   2027 Nov 20 15:04 stamps.txt
```
