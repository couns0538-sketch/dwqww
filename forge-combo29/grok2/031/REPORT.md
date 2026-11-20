# grok2 seat 031

Arm 1, B1a, source seat 030, switch IdeaB1. Branch for-fable-and-opus/grok2-031. Model Grok 4.7.

## Patch

Source commit from `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-030`:

```
416700fe0ace1656a1285fc536c347718c1a4af7
```

`sha256sum ~/arm.patch` (the file written by `git show FETCH_HEAD:forge-combo29/grok/030/idea.patch.txt`):

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

That is the arm table sha256. In `/agent/repos/work`, `git apply --check ~/arm.patch` then `git apply ~/arm.patch` both exited 0. `git diff --stat` there:

```
 forge-combo29/include/forge/search.hpp |  3 ++
 forge-combo29/src/search.cpp           | 67 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  6 ++-
 3 files changed, 74 insertions(+), 2 deletions(-)
```

The same text is in `patch_check.txt`. IdeaB1_Scale and IdeaB1_Fade were left at the patch defaults and were never sent. The engine sources were not committed. The first CMake attempt used `/usr/bin/c++` (Clang 18) and failed to link `-lstdc++`. Both measured binaries were then configured with `-DCMAKE_CXX_COMPILER=g++` (g++ 13.3.0) and Release. This machine has avx512f and bmi2, so FORGE_PORTABLE stayed OFF and FORGE_MARCH stayed the CMake default x86-64-v4.

## Honesty

`python3 sum_raw.py honesty` on the raw bench and perft transcripts. exe B is `/agent/repos/base/forge-combo29/build/forge`. exe P is `/agent/repos/work/forge-combo29/build/forge`.

```
prefix hon_B
bench11 nodes 312866 expect 312866 ok
bench13 nodes 862329 expect 862329 ok
bench16 nodes 3024920 expect 3024920 ok
perft5 nodes 4865609 expect 4865609 ok
honesty_miss 0
prefix hon_P
bench11 nodes 312866 expect 312866 ok
bench13 nodes 862329 expect 862329 ok
bench16 nodes 3024920 expect 3024920 ok
perft5 nodes 4865609 expect 4865609 ok
honesty_miss 0
```

## Three O runs

`python3 sum_raw.py orun o_B.txt o_Poff.txt o_Pon.txt`:

```
positions B 200 OFF 200 ON 200
B sum 9500069 first3 41311 / 24872 / 28574
OFF sum 9500069 first3 41311 / 24872 / 28574
ON sum 10081213 first3 12481 / 31753 / 31668
OFF positions differing from B 0
ON positions differing from B 200
expect B sum 9500069 first3 41311 / 24872 / 28574
expect ON sum 10081213 first3 12481 / 31753 / 31668 differ 200
```

Run (1) matches the known base sum and first three. Run (2), IdeaB1 false, matches run (1) on all 200 positions. Run (3), IdeaB1 true, matches the arm row: sum 10081213, first three 12481 / 31753 / 31668, 200 positions differ.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. Seat 031 openings are every 90th line of that file starting at line 31.

## C-ARRIVE and C-HALF

C-ARRIVE counts from `arrive_check.txt` (`grep -c` on `~/arrive.log`):

```
setoption name IdeaB1 value true: 20
unknown option|invalid value|No such option: 0
```

The engine log line in that file is `ON <--- setoption name IdeaB1 value true`. fastchess accepted `engine=true`.

C-HALF, `python3 games_tsv.py pool FULL half.tsv` (also `half_pool.txt`):

```
side FULL: games 400 W-L-D 234-31-135 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 6, 43, 93, 58] Elo +194.34 95% [+169.59, +221.02]
```

FULL's Elo is above +20.

## POOL.txt

17 chunks, 8500 games. Each `chunk_N.tsv` is 500 lines. Pasted `POOL.txt`:

```
side ON: games 8500 W-L-D 2266-2252-3982 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [175, 1068, 1783, 1016, 208] Elo +0.57 95% [-4.25, +5.39]
```

## suspicions, not proven

Chunk 3 pooled alone during the match printed Elo -25.76 with a 95% interval that excluded 0. Later chunks did not stay there: the committed pool above is +0.57 and the interval includes 0. That single-chunk print was not given its own file.

Five games were draws of 15 to 19 plies (both colors). They are scored 1/2-1/2. I do not have a reason to call them broken games.

Every tsv Termination field is the word normal, while the fastchess console lines name mates and draws by repetition, fifty moves, and insufficient material. The pool uses Result. I did not prove the header is wrong, and I did not use it for the Elo.

`config.json` appeared untracked at the repository root. match.sh does not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. A grep of the chunk logs for adjudicat, resign, maxmoves, syzygy, and tablebase was 0 on the chunks that existed at that check. The json's own enabled flags for those are false. I did not commit the json.

## what I did NOT do

I did not open a pull request. I did not edit engine code. I did not commit an executable, a net, a PGN, or the book. I did not send IdeaB1_Scale or IdeaB1_Fade. I did not fall back to arm 10. I did not repeat an opening to get more games. I did not start chunk 18: play.sh printed `minute 95: no new chunk` after chunk 17. No `FABLE_TO_grok2_*.md` file was on the handoff branch at the fetches I made. I did not rerun C-HALF; the first run passed.

## what I am NOT sure about

I am not sure which process created the root `config.json`. I am not sure the morning swarm stored the same Termination header. I am sure the node counts and the pool line above were printed by the committed scripts from the committed raw files, because I ran them again at the end and the prints matched `o_table.txt`, the honesty tables, and `POOL.txt`.

## times: see stamps.txt

First stamp `2026-11-20T13:22:09Z STEP 1`. Chunk 17 stamp `2026-11-20T14:59:38Z`. play.sh stopped at minute 95.

## git status --short and ls -la

The next two blocks are the command output captured after this report and RESULT.txt were written, and after the STEP 5 stamp line was appended.

```
$ git status --short
 M forge-combo29/grok2/031/stamps.txt
?? config.json
?? forge-combo29/grok2/031/POOL.txt
?? forge-combo29/grok2/031/REPORT.md
?? forge-combo29/grok2/031/RESULT.txt
```

```
$ ls -la forge-combo29/grok2/031
total 3032
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2203 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56396 Nov 20 14:22 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51401 Nov 20 14:22 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56731 Nov 20 14:28 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51660 Nov 20 14:28 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56014 Nov 20 14:33 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51306 Nov 20 14:33 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56266 Nov 20 14:38 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51477 Nov 20 14:38 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56455 Nov 20 14:43 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51561 Nov 20 14:43 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56330 Nov 20 14:49 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51283 Nov 20 14:49 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56537 Nov 20 14:54 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51584 Nov 20 14:54 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56378 Nov 20 14:59 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 14:59 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56511 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51158 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56144 Nov 20 13:42 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 13:42 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56463 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51518 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56067 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51295 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56437 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56054 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51401 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  55991 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51572 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56419 Nov 20 14:12 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51437 Nov 20 14:12 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56140 Nov 20 14:17 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51419 Nov 20 14:17 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46736 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu    977 Nov 20 13:28 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42226 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu   6596 Nov 20 13:26 harness.py
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5040 Nov 20 13:26 hon_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5040 Nov 20 13:26 hon_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5042 Nov 20 13:26 hon_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5255 Nov 20 13:26 hon_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:28 hon_B_table.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5201 Nov 20 13:26 hon_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5201 Nov 20 13:26 hon_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5203 Nov 20 13:26 hon_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:26 hon_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5416 Nov 20 13:26 hon_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    183 Nov 20 13:28 hon_P_table.txt
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:26 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 308862 Nov 20 13:26 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:26 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 309046 Nov 20 13:26 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    829 Nov 20 13:26 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 310078 Nov 20 13:26 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu    344 Nov 20 13:28 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    728 Nov 20 13:28 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6122 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    646 Nov 20 15:02 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3435 Nov 20 13:26 sum_raw.py
```
