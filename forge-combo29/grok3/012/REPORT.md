# grok3 seat 012

Seat 012, arm 3, 60,000 nodes. Chunk size 100 openings (200 games). Match is the main match: ON (IdeaB8=true, HindsightDepth=true) against OFF (both false). Model name passed to take_seat3.sh: Grok 4.7.

## Patch

`sha256sum ~/b8.patch` printed:

```
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/b8.patch
```

That is the required hash. The patch bytes came from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`. `git rev-parse FETCH_HEAD` after fetching `for-fable-and-opus/grok-028` printed that same commit. `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both succeeded in the work tree `../work` at base `6b98f2170a3210e71beed04bbd2553972c253ed7`. The apply changed three files (`search.hpp`, `search.cpp`, `uci.cpp`): 173 insertions, 4 deletions. Nothing from the build or the patched sources was committed.

The first cmake used `/usr/bin/c++`, which is Clang 18.1.3, and failed to link (`cannot find -lstdc++`). The brief requires g++ (GCC 13 or newer). I deleted `~/build` and configured again with `-DCMAKE_CXX_COMPILER=/usr/bin/g++`. That compiler is GCC 13.3.0. The machine has AVX-512 and BMI2, so I did not pass `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. The built engine is `/home/ubuntu/build/forge`. Its sha256, from `o_both.rows.txt.meta`, is `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`. id name: `Chess Engine Forge 6.4.24 candidate`.

## Honesty

Fresh processes, no setoption before the command. Raw files are in this folder.

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 167 nps 1873449`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 458 nps 1882814`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1460 nps 2071863`
- `honesty_perft5.txt` last line: `nodes 4865609`

All four match the known numbers (312866, 862329, 3024920, 4865609).

## Four O runs

`~/first200.fens` sha256 is `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (200 lines).

Known text, and what this seat printed:

1. IdeaB8=false HindsightDepth=false. Required sum 9,500,069 and first three 41,311 / 24,872 / 28,574. Printed: `rows 200 sum 9,500,069 first three 41,311 / 24,872 / 28,574`. `o_off.rows.txt` begins `41311`, `24872`, `28574`. `sha256sum` of `o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`, the required hash.
2. IdeaB8=true HindsightDepth=false. Required sum 9,718,009 and first three 17,283 / 17,878 / 31,115. Printed: `rows 200 sum 9,718,009 first three 17,283 / 17,878 / 31,115`. `o_b8.rows.txt` begins `17283`, `17878`, `31115`.
3. IdeaB8=false HindsightDepth=true. Required sum 9,845,650 and first three 23,395 / 31,504 / 35,958. Printed: `rows 200 sum 9,845,650 first three 23,395 / 31,504 / 35,958`. `o_k3.rows.txt` begins `23395`, `31504`, `35958`.
4. Both true. No known answer. Printed: `rows 200 sum 9,758,416 first three 18,538 / 34,070 / 39,093`. `o_both.rows.txt` begins `18538`, `34070`, `39093`. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200 (every position's node count differs from run 1).

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Zip hash, line count, and epd hash match the known copy. `~/mine.epd` has 13390 lines (lines at or after 2,150,012, every 36th).

## games_tsv.py known answer

`~/ka.tsv` from `for-fable-and-opus/grok2-004` `forge-combo29/grok2/004/chunk_1.tsv`. sha256 `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`.

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required print.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): IdeaB8 value true count 20, HindsightDepth value true count 20, refusal count 0. The same file has 20 log lines around the first `setoption name IdeaB8 value true`, which fastchess sent to engine ON.

C-HALF: 400 games. `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/012/half.tsv` printed:

```
side FULL: games 400 W-L-D 287-41-72 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 3, 37, 55, 101] Elo +249.08 95% [+214.90, +288.00]
```

FULL's Elo is +249.08, above +20. Pass.

## POOL.txt

9 chunks, each 200 games, 1800 games. Every Termination field in the nine tsv files is `normal` (1800 of 1800). No chunk failed and no commit or push line in `~/play.log` says FAILED. play.sh then printed `minute 46: no new chunk` and exited. Chunk 9 finished at 19:37:29Z, before minute 51.

Pasted `POOL.txt`:

```
side ON: games 1800 W-L-D 486-393-921 pairs 900 (openings not in exactly 2 games: 0)
ptnml [19, 195, 390, 266, 30] Elo +17.97 95% [+8.33, +27.63]
```

## suspicions, not proven

The point estimate +17.97 at 60,000 nodes sits near the "about +17 if they add" figure from the 20,000-node single-idea results. The 95% interval [+8.33, +27.63] also covers about +10. This seat did not play 2,000 or 20,000 nodes for the pair, so it does not decide add versus overlap.

## what I did NOT do

I did not open a pull request. I did not change engine source except by applying the given patch in the outside work tree. I did not commit an executable, a net, a PGN, or `config.json`. I did not force-push, and I did not write any branch except `for-fable-and-opus/grok3-012`. I did not start a chunk after minute 46. I did not turn on adjudication (`match.sh` has no `-draw`, `-resign`, `-maxmoves`, or tablebases). I did not play the fallback match. No `FABLE_TO_grok3_*.md` exists on `handoff/fable-opus-combo29-all-20261114` (listed at step 1 and again during step 4), so there was no STOP file.

## what I am NOT sure about

fastchess wrote an untracked `config.json` in the repository root because that was the working directory. I left it untracked. Its resign, draw, maxmoves, and tablebase flags are `enabled: false`. I am sure the 1800 committed games are scored from the tsv files; I am not sure a later reader will ignore `config.json`, so it is named here.

## times: see stamps.txt

## git status --short and ls -la

The paste below was taken after POOL.txt, REPORT.md, RESULT.txt, and the step 5 stamp line existed, and before the step 5 commit.

```
$ git status --short
 M forge-combo29/grok3/012/stamps.txt
?? config.json
?? forge-combo29/grok3/012/POOL.txt
?? forge-combo29/grok3/012/REPORT.md
?? forge-combo29/grok3/012/RESULT.txt

$ ls -la forge-combo29/grok3/012
total 628
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:39 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2235 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 22504 Nov 20 18:59 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 20735 Nov 20 18:59 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 22529 Nov 20 19:04 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 20616 Nov 20 19:04 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 22422 Nov 20 19:09 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 20610 Nov 20 19:09 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 22903 Nov 20 19:14 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 20713 Nov 20 19:14 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 22801 Nov 20 19:18 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 20662 Nov 20 19:18 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 22974 Nov 20 19:23 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 20723 Nov 20 19:23 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 22571 Nov 20 19:28 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 20805 Nov 20 19:28 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 22410 Nov 20 19:32 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 20704 Nov 20 19:32 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 22511 Nov 20 19:37 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 20730 Nov 20 19:37 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:55 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45526 Nov 20 18:54 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:55 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41947 Nov 20 18:54 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:55 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:55 play.sh
-rw-r--r-- 1 ubuntu ubuntu   146 Nov 20 19:38 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  6672 Nov 20 19:39 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   287 Nov 20 19:39 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    88 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   479 Nov 20 19:39 stamps.txt
```
