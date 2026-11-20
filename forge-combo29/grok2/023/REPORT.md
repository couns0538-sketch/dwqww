# grok2 seat 023

Arm 3, B8a. Source seat 078. Commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0 on for-fable-and-opus/grok-078. SWITCH IdeaB8. Model Grok 4.7. No FABLE_TO_grok2 file was on handoff/fable-opus-combo29-all-20261114 at the fetches during this run.

## Patch

`sha256sum ~/arm.patch` printed `b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649`, the table value. `git apply --check` and `git apply` in the work tree both exited 0. `git -C /agent/repos/work diff --stat` after apply:

```
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

The patch is not committed. IdeaB8_Weight and IdeaB8_Swing were left at their defaults and were never sent.

Release build with CMake and `/usr/bin/g++` (GCC 13.3.0), `FORGE_MARCH=x86-64-v4`, `FORGE_PORTABLE=OFF`. The machine has AVX-512 and BMI2, so the portable flags were not used. `build_meta.txt` records the exe sha256 values. Its `compiler` line is blank because the cache key is `CMAKE_CXX_COMPILER:STRING=/usr/bin/g++`, not `FILEPATH`.

## Honesty

Known targets: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Pasted output of `honesty_table.py` (reads the raw files):

```
honesty_B_bench11.txt info string bench depth 11 nodes 312866 time 168 nps 1862297
honesty_B_bench13.txt info string bench depth 13 nodes 862329 time 465 nps 1854470
honesty_B_bench16.txt info string bench depth 16 nodes 3024920 time 1505 nps 2009913
honesty_B_perft5.txt nodes 4865609
honesty_P_bench11.txt info string bench depth 11 nodes 312866 time 265 nps 1180626
honesty_P_bench13.txt info string bench depth 13 nodes 862329 time 574 nps 1502315
honesty_P_bench16.txt info string bench depth 16 nodes 3024920 time 1677 nps 1803768
honesty_P_perft5.txt nodes 4865609
```

Both exes match on all four. Each command was a fresh process with no setoption before it. Raw files and `.meta` files are in this folder.

## O runs

Table for arm 3: exe B sum 9,500,069, first three 41,311 / 24,872 / 28,574. Switch false equals B on all 200. Switch true: sum 9,295,189, first three 24,947 / 29,945 / 39,302, 200 differ.

Pasted output of `osum.py` on the raw transcripts:

```
forge-combo29/grok2/023/o_B.raw.txt positions 200 sum 9500069 first 41311 24872 28574
forge-combo29/grok2/023/o_P_off.raw.txt positions 200 sum 9500069 first 41311 24872 28574
differ 0 of 200
equal yes
```

```
forge-combo29/grok2/023/o_B.raw.txt positions 200 sum 9500069 first 41311 24872 28574
forge-combo29/grok2/023/o_P_on.raw.txt positions 200 sum 9295189 first 24947 29945 39302
differ 200 of 200
equal no
```

Run (1) matches. Run (2) is identical to run (1) on all 200 positions. Run (3) matches the sum, the first three, and 200 positions that differ. S14 was sent in the table order, then Threads 1, Hash 16, and for the patched engine `setoption name IdeaB8 value false` or `true`. The option list is in each `.meta` file.

## Book

`book_sha.txt`, from `sha256sum` and `wc -l`:

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
  29245 /home/ubuntu/mine.epd
```

Zip and epd match the brief. Seat 023 takes line 23 and every 90th line after it. Chunks used the first 19*250 = 4750 lines of `mine.epd`. The reserved 300 control lines start at line 28946 of `mine.epd` and were not played in the chunks.

## C-ARRIVE

`arrive_check.txt`: `true_count 20`, `bad_count 0`. The 20 log lines around the first `setoption name IdeaB8 value true` are in that file. The engine line is `ON <--- setoption name IdeaB8 value true`. fastchess accepted `engine=true`.

## C-HALF

Pasted output of `games_tsv.py pool FULL` on `half.tsv` (also in `half_pool.txt`):

```
side FULL: games 400 W-L-D 237-33-130 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 10, 39, 80, 69] Elo +195.51 95% [+167.05, +226.58]
```

FULL (20000 nodes) against HALF (10000 nodes), both with IdeaB8 false. Elo +195.51 is above +20. Pass.

## Pool

19 chunks, 9500 games. Each `chunk_N.tsv` in HEAD is 500 lines (`git show | wc -l` for N = 1..19). `play.out` ends with `minute 95: no new chunk`. Chunk 19 had already finished (`2026-11-20T15:00:20Z chunk 19 done`). No chunk was killed. `cut -f5` of every chunk tsv: `9500 normal`.

Pasted `POOL.txt` (output of `python3 ~/games_tsv.py pool ON` on `chunk_*.tsv`):

```
side ON: games 9500 W-L-D 2656-2515-4329 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [227, 1122, 1948, 1189, 264] Elo +5.16 95% [+0.47, +9.84]
```

## suspicions, not proven

The node counts matched the table on every position that the table names, so I have no suspicion that exe P is a different build.

The match interval starts above 0. This is one sample of 4750 pairs. I did not play a second sample.

Commit `2690e5853` stored 160 lines of `chunk_3.tsv` because the tsv was still being written. The next commit, `2219908fc`, stored 500 lines. HEAD is the 500-line file. One `stamps.txt` line at `2026-11-20T13:46:34Z` was split across three physical lines by a newline inside the chunk list. The times on the other lines are `date -u` output.

## what I did NOT do

I did not open a pull request. I did not change engine source in the branch. I did not send any patch option except IdeaB8. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebase adjudication. I did not play the reserved 300 openings. I did not fall back to arm 10. I did not force-push.

## what I am NOT sure about

fastchess wrote an untracked `config.json` in the repository root (not in this folder) while the controls ran. I opened it. `resign`, `draw`, `maxmoves`, `tb_adjudication`, and `sprt` all have `"enabled": false`. I am not sure whether fastchess reloads that file between games. The match command line had no adjudication flags, and all 9500 tsv terminations are `normal`.

## times: see stamps.txt

The first line is `2026-11-20T13:21:51Z STEP 1 seat`. The last line is the STEP 5 stamp.

## git status --short

```
 M forge-combo29/grok2/023/stamps.txt
?? config.json
?? forge-combo29/grok2/023/POOL.txt
?? forge-combo29/grok2/023/REPORT.md
?? forge-combo29/grok2/023/RESULT.txt
```

## ls -la

```
total 3180
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2137 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    372 Nov 20 13:28 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    579 Nov 20 13:26 build_meta.txt
-rw-r--r-- 1 ubuntu ubuntu  56590 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55696 Nov 20 14:23 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51389 Nov 20 14:23 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56353 Nov 20 14:28 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:28 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56494 Nov 20 14:32 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51444 Nov 20 14:32 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56067 Nov 20 14:37 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51506 Nov 20 14:37 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56375 Nov 20 14:42 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:42 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56569 Nov 20 14:46 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51381 Nov 20 14:46 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56397 Nov 20 14:51 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51600 Nov 20 14:51 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55759 Nov 20 14:55 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51426 Nov 20 14:55 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56196 Nov 20 15:00 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51420 Nov 20 15:00 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56303 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51245 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56238 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56379 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51393 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56444 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51364 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  55957 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51320 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55817 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51192 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56265 Nov 20 14:04 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:04 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  55984 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51359 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56135 Nov 20 14:13 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 14:13 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46660 Nov 20 13:31 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:31 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1068 Nov 20 13:32 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42279 Nov 20 13:31 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 13:25 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 13:25 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:25 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 13:25 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   4553 Nov 20 13:25 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    492 Nov 20 13:27 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu    572 Nov 20 13:27 honesty_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu 281892 Nov 20 13:26 o_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    902 Nov 20 13:26 o_B.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    202 Nov 20 13:26 o_off_table.txt
-rw-r--r-- 1 ubuntu ubuntu    202 Nov 20 13:26 o_on_table.txt
-rw-r--r-- 1 ubuntu ubuntu 282097 Nov 20 13:26 o_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    936 Nov 20 13:26 o_P_off.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282266 Nov 20 13:26 o_P_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    935 Nov 20 13:26 o_P_on.raw.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   5955 Nov 20 13:26 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1389 Nov 20 13:26 osum.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6293 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1176 Nov 20 15:05 stamps.txt
```
