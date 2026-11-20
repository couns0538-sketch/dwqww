# grok2 seat 018 arm 8

Arm 8, K4b. Source seat 043. Switch IdeaK4. Branch for-fable-and-opus/grok2-018. Model Grok 4.7.

## Patch

Source commit fetched as `for-fable-and-opus/grok-043`, then again by commit id. `patch_check.txt`:

```
rev 2f38a63656ec17062b581c933fcc77d961b946f1
b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  -
local b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
```

That sha256 is the arm table's sha256. `git apply --check` then `git apply` on the work tree. `patch_apply.txt`:

```
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)
```

The patch was not committed. IdeaK4_Shrink was left at its default and was never sent.

## Builds

Both trees are the base commit `6b98f2170a3210e71beed04bbd2553972c253ed7`. Release CMake with `g++` 13.3.0. This machine has AVX-512 and BMI2, so the build did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. The first configure used `/usr/bin/c++` (Clang) and failed to link `libstdc++`; the builds that were measured were reconfigured with `-DCMAKE_CXX_COMPILER=g++`.

exe B: `/agent/repos/base/forge-combo29/build/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`

exe P: `/agent/repos/work/forge-combo29/build/forge` sha256 `56a73dc402d07e94344aa1953b5a50e303be29b0bf6dfec1effca93ec1a3b655`

id name on both: `Chess Engine Forge 6.4.24 candidate`

## Honesty

`honesty_table.py` on the raw bench/perft files. exe B (`honesty_b.table`):

```
bench11 nodes 312866 expect 312866 ok
bench13 nodes 862329 expect 862329 ok
bench16 nodes 3024920 expect 3024920 ok
perft5 nodes 4865609 expect 4865609 ok
honesty ok
```

exe P (`honesty_p.table`): the same five lines, `honesty ok`.

## Three O runs

Positions file sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines. S14, Threads 1, Hash 16, depth 12. Script `o_table.py`.

(1) exe B, `o_b.table`:

```
file forge-combo29/grok2/018/o_b.txt
positions 200
sum 9500069
first 41311 24872 28574
```

Known: sum 9,500,069; first three 41,311 / 24,872 / 28,574. Match.

(2) exe P, IdeaK4 false, `o_off.table`:

```
file forge-combo29/grok2/018/o_off.txt
positions 200
sum 9500069
first 41311 24872 28574
```

`o_table.py compare` of B against off, `o_off_vs_b.table`:

```
positions 200
differ 0
equal
```

(3) exe P, IdeaK4 true, `o_on.table`:

```
file forge-combo29/grok2/018/o_on.txt
positions 200
sum 8983632
first 23741 21846 35911
```

Known for this arm: sum 8,983,632; first three 23,741 / 21,846 / 35,911; 200 differ. `o_on_vs_b.table`:

```
positions 200
differ 200
not_equal
```

Match. Each run's `.meta` names the exe it started, that exe's sha256, the id name, and every option line.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

2632036 lines. Both hashes match the brief. Seat 018 takes every 90th line starting at line 18. `~/mine.epd` has 29245 lines. The last 300 are the controls. Chunks used the top, 18 times 250 openings.

## C-ARRIVE and C-HALF

C-ARRIVE: `arrive_check.txt` records `switch_true_count 20` and `bad_count 0`. The window around the first switch setoption includes:

```
[Engine] [13:27:34.051183] <     140324039030464>  ON <--- setoption name IdeaK4 value true
```

C-HALF: `half_pool.txt` (script `games_tsv.py pool FULL`):

```
side FULL: games 400 W-L-D 224-33-143 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 12, 39, 95, 54] Elo +180.58 95% [+155.29, +207.75]
```

FULL's Elo is above +20. Pass. fastchess also printed Elo 180.58 for FULL vs HALF.

## Pool

18 chunks, 9000 games. `POOL.txt`:

```
side ON: games 9000 W-L-D 2276-2506-4218 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [260, 1176, 1796, 1070, 198] Elo -8.88 95% [-13.71, -4.05]
```

IdeaK4 on is behind IdeaK4 off by 8.88 Elo on these games. The 95% interval is entirely below zero. Openings not in exactly two games: 0.

## Suspicions, not proven

None about the harness. The node counts match the morning build on all 200 positions, the off switch matches exe B on all 200, and C-HALF shows the 20000-node side beating the 10000-node side by +180 Elo. The match loss is the measured result of this patch, not a failed control.

fastchess wrote `/agent/repos/dwqww/config.json` while the match cwd was the repository. Its resign, draw, maxmoves, and tablebase adjudication flags are all `enabled: false`. I did not commit that file. No `-draw`, `-resign`, `-maxmoves`, or tablebase argument was passed.

## What I did not do

I did not open a pull request. I did not change engine source in the repository and I did not commit an exe, a net, an object file, or a PGN. I did not send IdeaK4_Shrink. I did not play arm 10. I did not repeat an opening. I did not force-push. No `FABLE_TO_grok2` file was on the handoff branch at any fetch, so nothing from the channel changed the run.

## What I am not sure about

The Elo and interval are exactly the printed output of the given `games_tsv.py`. I did not recompute them with another library. I did not read all 9000 games by hand; the pool script reported every game scored and every opening in exactly two games. Later chunks took about five minutes instead of four minutes forty-seven seconds. The node limit was unchanged.

## Times

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok2/018/stamps.txt
?? config.json
?? forge-combo29/grok2/018/POOL.txt
?? forge-combo29/grok2/018/REPORT.md
?? forge-combo29/grok2/018/RESULT.txt
?? forge-combo29/grok2/018/chunk_18.out
?? forge-combo29/grok2/018/chunk_18.tsv
```

## ls -la forge-combo29/grok2/018

```
total 3080
drwxr-xr-x 4 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2128 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56150 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55989 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51273 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56521 Nov 20 14:31 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51437 Nov 20 14:31 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56091 Nov 20 14:36 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 14:36 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56690 Nov 20 14:41 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51584 Nov 20 14:41 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55867 Nov 20 14:46 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:46 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56975 Nov 20 14:51 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51603 Nov 20 14:51 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56079 Nov 20 14:56 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51468 Nov 20 14:56 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56171 Nov 20 15:01 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 15:01 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56296 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51227 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56620 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51438 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56248 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51408 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56520 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51497 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56679 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56352 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56436 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51409 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56556 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51627 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56202 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46928 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1011 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42276 Nov 20 13:30 half.tsv
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 13:26 honesty_b
-rw-r--r-- 1 ubuntu ubuntu    166 Nov 20 13:27 honesty_b.table
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 13:26 honesty_p
-rw-r--r-- 1 ubuntu ubuntu    166 Nov 20 13:27 honesty_p.table
-rw-r--r-- 1 ubuntu ubuntu    340 Nov 20 13:25 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu    745 Nov 20 13:25 honesty_table.py
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    796 Nov 20 13:26 o_b.meta
-rw-r--r-- 1 ubuntu ubuntu   1983 Nov 20 13:26 o_b.table
-rw-r--r-- 1 ubuntu ubuntu 308850 Nov 20 13:26 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    830 Nov 20 13:26 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu   1985 Nov 20 13:26 o_off.table
-rw-r--r-- 1 ubuntu ubuntu 309000 Nov 20 13:26 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu     29 Nov 20 13:27 o_off_vs_b.table
-rw-r--r-- 1 ubuntu ubuntu    829 Nov 20 13:26 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu   1982 Nov 20 13:26 o_on.table
-rw-r--r-- 1 ubuntu ubuntu 307864 Nov 20 13:26 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu     35 Nov 20 13:27 o_on_vs_b.table
-rw-r--r-- 1 ubuntu ubuntu   4110 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   2047 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    211 Nov 20 13:27 patch_apply.txt
-rw-r--r-- 1 ubuntu ubuntu    208 Nov 20 13:27 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5888 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    661 Nov 20 15:03 stamps.txt
```
