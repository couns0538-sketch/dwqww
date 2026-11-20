# Seat 027, arm 7

Arm 7, K4a. Source seat 093, commit ddc850cbf04b8c7a8592624037844077b33c8ab0, switch IdeaK4. Model Grok 4.7. Branch for-fable-and-opus/grok2-027.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` printed:

```
e271ef8db279ae69205760de6a8619708ce605ba0b147f0b841ad9055ae839a9  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch` then `git apply ~/arm.patch` in the work tree both exited 0. `git -C ../work diff --stat` printed:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 18 +++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 23 insertions(+), 1 deletion(-)
```

The CPU reports AVX-512 and BMI2, and g++ is 13.3.0, so both release builds used the CMake default (`-march=x86-64-v4`, FORGE_PORTABLE off). IdeaK4_Shrink was left at the patch default and was never sent.

## Honesty numbers

`honesty_table.py` on the raw files:

```
b bench11 nodes 312866 expect 312866 MATCH
b bench13 nodes 862329 expect 862329 MATCH
b bench16 nodes 3024920 expect 3024920 MATCH
b perft5 nodes 4865609 expect 4865609 MATCH
p bench11 nodes 312866 expect 312866 MATCH
p bench13 nodes 862329 expect 862329 MATCH
p bench16 nodes 3024920 expect 3024920 MATCH
p perft5 nodes 4865609 expect 4865609 MATCH
```

Each line is a fresh process. The process was sent `uci`, then `bench 11` or `bench 13` or `bench 16` or `go perft 5`, then `quit`. No setoption.

## Three O runs

`otable.py` on `o_b.txt`, `o_poff.txt`, and `o_pon.txt`:

```
B sum 9500069 first 41311 24872 28574
Poff sum 9500069 first 41311 24872 28574
Pon sum 8921190 first 24693 26341 35070
Poff identical 200 of 200
Pon differ 200 of 200
B expect sum 9500069 first 41311 24872 28574 MATCH
Pon expect sum 8921190 first 24693 26341 35070 differ 200 MATCH
```

The arm table for K4a is sum 8,921,190, first three 24,693 / 26,341 / 35,070, 200 differ. Exe B is sum 9,500,069, first three 41,311 / 24,872 / 28,574. Exe P with IdeaK4 false matches exe B on all 200 positions.

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 027 took every 90th line of `uho.epd` starting at line 27 (`wc -l ~/mine.epd` was 29245). The last 300 lines were held out for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE, from `arrive_check.txt`:

```
grep -c "setoption name IdeaK4 value true" ~/arrive.log
20
grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The 20 log lines around the first switch setoption are in that file. The engine received `setoption name IdeaK4 value true`.

C-HALF, `games_tsv.py pool FULL` on `half.tsv`:

```
side FULL: games 400 W-L-D 233-19-148 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 5, 33, 105, 57] Elo +207.46 95% [+183.44, +233.41]
```

FULL's Elo is +207.46, above +20.

## POOL.txt

20 chunks, 10000 games. `games_tsv.py pool ON` wrote `POOL.txt`:

```
side ON: games 10000 W-L-D 2696-2691-4613 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [235, 1227, 2076, 1222, 240] Elo +0.17 95% [-4.32, +4.66]
```

## Suspicions, not proven

None.

## What I did not do

I did not open a pull request. I did not commit an engine source file, an executable, a net, a PGN, or the opening book. I did not send IdeaK4_Shrink. I did not turn on draw, resign, max-move, or tablebase adjudication. I did not replay an opening. I did not switch to arm 10. I did not change git user.name; it was already set. No `FABLE_TO_grok2_<N>.md` file was on the handoff branch at any fetch. An untracked `config.json` appeared in the repository root while fastchess was running with that directory as the shell's current directory. I did not add it.

## What I am not sure about

The `id` field in RESULT.txt is `K4a`, the name on arm 7's row. I am sure of the seat, the switch, and the numbers above.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/027/stamps.txt
?? config.json
?? forge-combo29/grok2/027/POOL.txt
?? forge-combo29/grok2/027/REPORT.md
?? forge-combo29/grok2/027/RESULT.txt
```

## ls -la

```
total 3276
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2290 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56114 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51360 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55710 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51414 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56224 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51365 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56119 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51337 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56210 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51520 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51317 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56666 Nov 20 14:41 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51464 Nov 20 14:41 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56469 Nov 20 14:45 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51586 Nov 20 14:45 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56263 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51268 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56477 Nov 20 14:54 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51535 Nov 20 14:54 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  55769 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51213 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56159 Nov 20 14:58 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 14:58 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56509 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51209 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56255 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51377 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56468 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51339 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56054 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51366 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56517 Nov 20 13:58 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51236 Nov 20 13:58 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56027 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51359 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56061 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56410 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51494 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47012 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:33 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42351 Nov 20 13:33 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:27 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:27 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5099 Nov 20 13:27 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    221 Nov 20 13:27 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5101 Nov 20 13:27 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 13:27 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5312 Nov 20 13:27 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1847 Nov 20 13:27 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:27 honesty_table_b.txt
-rw-r--r-- 1 ubuntu ubuntu    175 Nov 20 13:27 honesty_table_p.txt
-rw-r--r-- 1 ubuntu ubuntu   1200 Nov 20 13:25 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu    965 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 13:26 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu 281620 Nov 20 13:26 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    873 Nov 20 13:26 o_poff.meta
-rw-r--r-- 1 ubuntu ubuntu 281765 Nov 20 13:26 o_poff.txt
-rw-r--r-- 1 ubuntu ubuntu    872 Nov 20 13:26 o_pon.meta
-rw-r--r-- 1 ubuntu ubuntu 280796 Nov 20 13:26 o_pon.txt
-rw-r--r-- 1 ubuntu ubuntu   6103 Nov 20 13:26 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1933 Nov 20 13:25 otable.py
-rw-r--r-- 1 ubuntu ubuntu    282 Nov 20 13:27 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4287 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     73 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    733 Nov 20 15:01 stamps.txt
```
