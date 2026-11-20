# grok2 seat 010 arm 10

## Arm and source seat

Seat 010, arm 10, id K3. Source seat: none. SWITCH HindsightDepth. Model Grok 4.7. The base engine's own option; there is no morning patch.

## Patch sha256 and git apply

No patch. `patch=none`. git apply was not run. `../work` was created at 6b98f2170a3210e71beed04bbd2553972c253ed7 and left unpatched. exe P is exe B:

```
exe=/agent/repos/base/forge-combo29/build/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=Chess Engine Forge 6.4.24 candidate
```

Built with g++ 13.3.0, `-DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release`, default `FORGE_MARCH` x86-64-v4. The CPU has AVX-512 and BMI2, so `FORGE_PORTABLE` stayed off. The first cmake used `/usr/bin/c++` (clang 18) and failed to link libstdc++; that build directory was removed and the engine was configured again with g++. See `decision_arm10.txt`.

## Honesty numbers

`python3 forge-combo29/grok2/010/summarize.py honesty forge-combo29/grok2/010 B`

```
B bench11 nodes 312866 expected 312866 OK
info string bench depth 11 nodes 312866 time 168 nps 1862297
B bench13 nodes 862329 expected 862329 OK
info string bench depth 13 nodes 862329 time 437 nps 1973292
B bench16 nodes 3024920 expected 3024920 OK
info string bench depth 16 nodes 3024920 time 1417 nps 2134735
B perft5 nodes 4865609 expected 4865609 OK
nodes 4865609
```

`python3 forge-combo29/grok2/010/summarize.py honesty forge-combo29/grok2/010 P`

```
P bench11 nodes 312866 expected 312866 OK
info string bench depth 11 nodes 312866 time 166 nps 1884734
P bench13 nodes 862329 expected 862329 OK
info string bench depth 13 nodes 862329 time 447 nps 1929147
P bench16 nodes 3024920 expected 3024920 OK
info string bench depth 16 nodes 3024920 time 1446 nps 2091922
P perft5 nodes 4865609 expected 4865609 OK
nodes 4865609
```

Known pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes match. No setoption on these runs.

## Three O runs

Known table, exe B: sum 9500069; first three 41311 / 24872 / 28574.
Arm 10 SWITCH true: sum 9845650; first three 23395 / 31504 / 35958; 200 differ.

`python3 forge-combo29/grok2/010/summarize.py orun forge-combo29/grok2/010/o_B.txt`

```
file forge-combo29/grok2/010/o_B.txt
positions 200
sum 9500069
first3 41311 24872 28574
```

`python3 forge-combo29/grok2/010/summarize.py orun forge-combo29/grok2/010/o_P_off.txt forge-combo29/grok2/010/o_B.txt`

```
file forge-combo29/grok2/010/o_P_off.txt
positions 200
sum 9500069
first3 41311 24872 28574
differ_vs forge-combo29/grok2/010/o_B.txt 0
```

`python3 forge-combo29/grok2/010/summarize.py orun forge-combo29/grok2/010/o_P_on.txt forge-combo29/grok2/010/o_B.txt`

```
file forge-combo29/grok2/010/o_P_on.txt
positions 200
sum 9845650
first3 23395 31504 35958
differ_vs forge-combo29/grok2/010/o_B.txt 200
```

Run (1) matches the table. Run (2) matches run (1) on all 200 positions. Run (3) matches the arm 10 row. S14, Threads 1 and Hash 16 were sent; HindsightDepth was omitted on exe B, set false on run (2), set true on run (3).

## Book sha256

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
  2632036 /home/ubuntu/uho.epd
    29245 /home/ubuntu/mine.epd
```

Both digests match the brief. Seat 010 takes every 90th line starting at line 10. The last 300 lines of mine.epd were held back for the controls.

## C-ARRIVE and C-HALF

C-ARRIVE counts from `arrive_check.txt`: `setoption name HindsightDepth value true` occurred 20 times. `unknown option|invalid value|No such option` occurred 0 times. fastchess accepted `engine=true`. The 20 log lines around the first switch setoption are in `arrive_check.txt`.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/010/half.tsv` (file `half_pool.txt`):

```
side FULL: games 400 W-L-D 223-34-143 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 7, 45, 100, 48] Elo +178.33 95% [+155.01, +203.24]
```

FULL's Elo is +178.33, above +20. Pass.

## POOL.txt and chunks

22 chunks, each 500 games, 11000 games. Every termination field is `normal`. Openings not in exactly 2 games: 0.

`POOL.txt`:

```
side ON: games 11000 W-L-D 3035-2907-5058 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [250, 1311, 2270, 1399, 270] Elo +4.04 95% [-0.24, +8.33]
```

## suspicions, not proven

The point estimate for HindsightDepth on, at 20000 nodes, is about +4 Elo. The 95% interval includes 0. That is not a demonstrated gain.

## what I did NOT do

I did not apply a patch, fetch a source seat, or compile `../work`. I did not open a pull request. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not repeat an opening. I did not commit an engine binary, a net, or a PGN. No `FABLE_TO_grok2_<N>.md` file existed on `handoff/fable-opus-combo29-all-20261114` at the fetches I made, including the last one during this step. I did not kill a running chunk: play.sh printed `minute 95: no new chunk` after chunk 22 had already been written.

## what I am NOT sure about

I am not sure the RESULT field `id` is specified anywhere except the arm label. I filled `K3` because that is the label on row 10 of THE 10 ARMS. I am not sure a +4 Elo estimate this size is stable past this sample; the interval still covers a small negative number. fastchess wrote an untracked `config.json` into the repository while C-HALF ran from that directory. Adjudication entries in it were `enabled: false`, and the match command did not turn adjudication on. I deleted that untracked file. It is not in the commit.

## times: see stamps.txt

## git status --short and ls -la

The first snapshot was taken one command before RESULT.txt was written, so that listing did not show RESULT.txt. This replacement was taken with POOL.txt, REPORT.md, RESULT.txt and stamps.txt all on disk.

```
 M forge-combo29/grok2/010/REPORT.md
```

```
total 3488
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2250 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:26 B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5223 Nov 20 13:26 B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  56285 Nov 20 14:10 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:10 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56675 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51558 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56066 Nov 20 14:18 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51545 Nov 20 14:18 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56194 Nov 20 14:23 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51550 Nov 20 14:23 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56372 Nov 20 14:26 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 14:26 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56227 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56493 Nov 20 14:34 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51580 Nov 20 14:34 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  55989 Nov 20 14:38 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 14:38 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56178 Nov 20 14:42 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 14:42 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56078 Nov 20 14:46 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 14:46 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56041 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51234 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56451 Nov 20 14:50 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51476 Nov 20 14:50 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  55833 Nov 20 14:54 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 14:54 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56148 Nov 20 14:58 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51388 Nov 20 14:58 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56368 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51278 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55940 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51229 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56385 Nov 20 13:46 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51319 Nov 20 13:46 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56433 Nov 20 13:50 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51297 Nov 20 13:50 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55975 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51288 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56497 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51348 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56012 Nov 20 14:02 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51357 Nov 20 14:02 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56648 Nov 20 14:06 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51424 Nov 20 14:06 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    602 Nov 20 13:27 decision_arm10.txt
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46987 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu    990 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42332 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   6066 Nov 20 13:25 harness.py
-rwxr-xr-x 1 ubuntu ubuntu    973 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    793 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu     88 Nov 20 13:27 o_B.summary.txt
-rw-r--r-- 1 ubuntu ubuntu 281788 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    835 Nov 20 13:26 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu    136 Nov 20 13:27 o_P_off.summary.txt
-rw-r--r-- 1 ubuntu ubuntu 281737 Nov 20 13:26 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 13:26 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu    137 Nov 20 13:27 o_P_on.summary.txt
-rw-r--r-- 1 ubuntu ubuntu 281893 Nov 20 13:26 o_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5002 Nov 20 13:26 P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5004 Nov 20 13:26 P_bench16.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu    180 Nov 20 13:26 P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5223 Nov 20 13:26 P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5972 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2913 Nov 20 13:25 summarize.py
```
