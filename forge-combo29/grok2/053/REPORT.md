# Seat 053, arm 3 (B8a)

Arm 3, source seat 078, commit 7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0, switch IdeaB8. Model Grok 4.7. `git fetch --depth 1 origin for-fable-and-opus/grok-078` printed FETCH_HEAD `7dc4890ba02c8009aa0682a1b3d28a9eae85a6f0`.

## Patch

```
b72f21931608c3bbada95c6c93a61068b32a128986af2159d30b5a861c4e4649  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git apply --check ~/arm.patch` and `git apply ~/arm.patch` in the work tree both succeeded. The work tree still shows:

```
 forge-combo29/include/forge/search.hpp |  23 ++++
 forge-combo29/src/search.cpp           | 186 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +
 3 files changed, 210 insertions(+), 3 deletions(-)
```

No engine source was committed. IdeaB8_Weight and IdeaB8_Swing were left at their defaults.

The first CMake configure used `/usr/bin/c++` (Clang 18) and failed with `cannot find -lstdc++`. The binaries that were measured were built with `g++` (GCC 13.3.0) and GCC's libstdc++, Release, default march x86-64-v4. The CPU has AVX-512 and BMI2, so FORGE_PORTABLE was left off.

## Honesty

Pasted from `python3 table_o.py` reading the raw transcripts:

```
HONESTY
B bench11 312866 expected 312866 OK
B bench13 862329 expected 862329 OK
B bench16 3024920 expected 3024920 OK
B perft5 4865609 expected 4865609 OK
P bench11 312866 expected 312866 OK
P bench13 862329 expected 862329 OK
P bench16 3024920 expected 3024920 OK
P perft5 4865609 expected 4865609 OK
```

Each line was a fresh process and no setoption. Exe B is `/tmp/forge-base/forge`. Exe P is `/tmp/forge-work/forge`.

## Three O runs

Same script, same raw files (`orun_B.txt`, `orun_P_off.txt`, `orun_P_on.txt`):

```
O_RUNS
B positions 200 sum 9500069 first 41311 24872 28574
B expected_sum 9500069 expected_first 41311 24872 28574
B_SUM OK
B_FIRST OK
P_OFF positions 200 sum 9500069 first 41311 24872 28574 differ_from_B 0
P_OFF_IDENTICAL yes
P_ON positions 200 sum 9295189 first 24947 29945 39302 differ_from_B 200
P_ON expected_sum 9295189 expected_first 24947 29945 39302 expected_differ 200
P_ON_SUM OK
P_ON_FIRST OK
P_ON_DIFFER OK
```

Against the arm table: base sum 9,500,069 and first three 41,311 / 24,872 / 28,574; switch off identical to base on all 200; switch on sum 9,295,189, first three 24,947 / 29,945 / 39,302, 200 differ. All of those held. Arm 10 was not played.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

2632036 lines. Both hashes match the brief. Seat 053 took every 90th line starting at line 53 (`~/mine.epd`, 29245 lines). The last 300 lines were the controls and were not used by the chunks.

## C-ARRIVE

`arrive_check.txt`: `true_count 20`, `bad_count 0`. The first `setoption name IdeaB8 value true` is in that file with the 20 surrounding log lines. fastchess accepted `engine=true`.

## C-HALF

Pasted from `python3 ~/games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 231-28-141 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 9, 31, 104, 55] Elo +194.34 95% [+169.02, +221.68]
```

FULL at 20000 nodes against HALF at 10000, switch false on both. Elo is above +20.

## Pool

17 chunks, 500 games each, 8500 games. Each `chunk_N.tsv` is 500 lines. `play.log` has no FAILED line. Pasted from `python3 ~/games_tsv.py pool ON chunk_*.tsv` into `POOL.txt`:

```
side ON: games 8500 W-L-D 2383-2146-3971 pairs 4250 (openings not in exactly 2 games: 0)
ptnml [190, 974, 1743, 1095, 248] Elo +9.69 95% [+4.74, +14.64]
```

`match.sh` passed no `-draw`, `-resign`, `-maxmoves`, or tablebase flag. A grep of the chunk PGNs for `adjudic` found none. Every tsv termination field is the word `normal` (fastchess's header, including games whose console line said mate).

## suspicions, not proven

None beyond this: I did not read all 8500 PGN move lists by hand. `games_tsv.py` parsed every game (it exits on a parse error) and the pair count has 0 openings that are not in exactly two games.

Commit `98ed1e2e7` stored `chunk_14.tsv` at 241 lines, because a watcher read the file while `games_tsv.py` was still writing it. The next commit, `6f53fae42`, added the other 259 lines and `chunk_14.out`. The file in HEAD has 500 lines. Later chunks were committed only after the tsv had 500 lines, the `.out` existed, and `play.log` said that chunk was done.

## what I did NOT do

No pull request. No engine source committed. No second build of the patch. Arm 10 was not used. IdeaB8_Weight and IdeaB8_Swing were not sent. No opening was repeated to add games. The handoff branch never contained a `FABLE_TO_grok2_<N>.md`, so nothing on that channel changed the run and `~/STOP_PLAY` was not created. Play stopped on its own at minute 95 after chunk 17; fastchess was not killed.

## what I am NOT sure about

The RESULT field `id` is not defined in the brief. I filled `B8a`, the short name of arm 3 in the arm table.

fastchess writes `Termination "normal"` for every game, including mates. I am not sure that header is the chess ending reason. The Result header and the fastchess console text are what the pool uses.

## times: see stamps.txt

The first stamp is `2026-11-20T13:22:25Z STEP 1`. Chunk 17 finished at `2026-11-20T15:01:41Z`. Play then printed `minute 95: no new chunk`.

## git status --short

```
 M forge-combo29/grok2/053/stamps.txt
?? config.json
?? forge-combo29/grok2/053/POOL.txt
?? forge-combo29/grok2/053/REPORT.md
?? forge-combo29/grok2/053/RESULT.txt
```

## ls -la

```
total 2912
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:04 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2133 Nov 20 13:32 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56556 Nov 20 14:26 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51565 Nov 20 14:26 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56222 Nov 20 14:31 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51590 Nov 20 14:31 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56063 Nov 20 14:37 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51431 Nov 20 14:37 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56717 Nov 20 14:42 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51569 Nov 20 14:42 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  55820 Nov 20 14:47 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 14:47 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56039 Nov 20 14:52 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 14:52 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56425 Nov 20 14:57 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51567 Nov 20 14:57 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56390 Nov 20 15:01 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51598 Nov 20 15:01 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56036 Nov 20 13:41 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51274 Nov 20 13:41 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56267 Nov 20 13:46 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51199 Nov 20 13:46 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 13:51 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51356 Nov 20 13:51 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56304 Nov 20 13:56 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51361 Nov 20 13:56 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56354 Nov 20 14:01 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51531 Nov 20 14:01 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56326 Nov 20 14:06 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51293 Nov 20 14:06 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56635 Nov 20 14:11 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51498 Nov 20 14:11 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56095 Nov 20 14:16 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51356 Nov 20 14:16 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55965 Nov 20 14:21 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51304 Nov 20 14:21 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2802 Nov 20 13:32 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46849 Nov 20 13:35 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:35 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu  42210 Nov 20 13:35 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:29 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:29 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:29 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:29 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    172 Nov 20 13:29 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:29 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:29 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:29 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4912 Nov 20 13:26 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:32 match.sh
-rw-r--r-- 1 ubuntu ubuntu    822 Nov 20 13:29 orun_B.meta
-rw-r--r-- 1 ubuntu ubuntu 282143 Nov 20 13:29 orun_B.txt
-rw-r--r-- 1 ubuntu ubuntu    856 Nov 20 13:29 orun_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 282329 Nov 20 13:29 orun_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    855 Nov 20 13:29 orun_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 282312 Nov 20 13:29 orun_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   5167 Nov 20 13:26 orun.py
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:29 patch_sha256.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:32 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:03 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5605 Nov 20 15:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:04 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    675 Nov 20 15:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    722 Nov 20 13:29 table_o.out
-rw-r--r-- 1 ubuntu ubuntu   3462 Nov 20 13:26 table_o.py
```
