# grok3 seat 013

Seat 013, arm 1, 20,000 nodes, chunk 250 openings (500 games). Model Grok 4.7. Match is main: IdeaB8 and HindsightDepth both on, against both off. Local branch grok3-seat, remote for-fable-and-opus/grok3-013.

## Patch

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`. That is the required hash. The blob came from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt`. `git rev-parse FETCH_HEAD` after fetching `for-fable-and-opus/grok-028` printed that commit. `git apply --check ~/b8.patch` and `git apply ~/b8.patch` in the work tree `../work` (base `6b98f2170a3210e71beed04bbd2553972c253ed7`) both succeeded.

The machine has AVX-512 and BMI2 (`/proc/cpuinfo`) and `g++` is GCC 13.3.0, so the cmake line did not add `-DFORGE_PORTABLE` or `-DFORGE_MARCH`. `/usr/bin/c++` could not link `-lstdc++`. The brief says cmake with g++, so the configure command was `cmake -S ../work/forge-combo29 -B ~/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++`. The built file is `/home/ubuntu/build/forge`. Nothing of the build was committed.

## Honesty

A fresh process for each line, no setoption. Raw files in this folder:

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 183 nps 1709650`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 494 nps 1745605`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1600 nps 1890575`
- `honesty_perft5.txt`: `nodes 4865609`

These are the required node counts: 312866, 862329, 3024920, 4865609.

## Four O runs

`o_runs.py` on `/home/ubuntu/build/forge` and `~/first200.fens` (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines). Each `.meta` names that exe, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, `id name Chess Engine Forge 6.4.24 candidate`. Recounted from the row files with awk:

| run | file | sum | first three | against the brief |
| --- | --- | --- | --- | --- |
| (1) both off | `o_off.rows.txt` | 9500069 | 41311 / 24872 / 28574 | equal to 9,500,069 and 41,311 / 24,872 / 28,574 |
| (2) IdeaB8 only | `o_b8.rows.txt` | 9718009 | 17283 / 17878 / 31115 | equal to 9,718,009 and 17,283 / 17,878 / 31,115 |
| (3) HindsightDepth only | `o_k3.rows.txt` | 9845650 | 23395 / 31504 / 35958 | equal to 9,845,650 and 23,395 / 31,504 / 35,958 |
| (4) both on | `o_both.rows.txt` | 9758416 | 18538 / 34070 / 39093 | no known answer in the brief |

`sha256sum o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`.

`paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200`. All 200 positions differ in node count. Option lines in the meta files: off is IdeaB8 false and HindsightDepth false; b8 is true/false; k3 is false/true; both is true/true.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed `2632036`. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both hashes match the brief. `~/mine.epd` has 13390 lines.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): IdeaB8 value true count 20, HindsightDepth value true count 20, refusal count 0. The same file has 20 log lines around the first `setoption name IdeaB8 value true`. Pass.

C-HALF, `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/013/half.tsv` printed:

```
side FULL: games 400 W-L-D 279-39-82 pairs 200 (openings not in exactly 2 games: 0)
ptnml [3, 3, 34, 71, 89] Elo +240.82 95% [+209.51, +275.95]
```

FULL Elo +240.82 is above +20. Pass. `half.out` and `half.tsv` are in this folder.

## POOL.txt

10 chunks, each 500 games, 5000 games. `python3 ~/games_tsv.py pool ON forge-combo29/grok3/013/chunk_*.tsv` wrote `POOL.txt`:

```
side ON: games 5000 W-L-D 1539-1206-2255 pairs 2500 (openings not in exactly 2 games: 0)
ptnml [101, 501, 1027, 706, 165] Elo +23.17 95% [+16.73, +29.64]
```

## suspicions, not proven

None. I have no observation that contradicts a file in this folder.

## what I did NOT do

I did not open a pull request. I did not change engine source. I did not push with `--force` and I did not push any branch except `for-fable-and-opus/grok3-013`. I did not play the fallback match. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not commit the engine, a PGN, the book, or `config.json` (fastchess wrote that file in the repository root because `play.sh` was started with the repository as its working directory; adjudication fields in it are disabled). I did not kill a chunk: chunk 10 finished at 2026-11-20T19:37:20Z and `play.sh` then printed `minute 46: no new chunk`. No `FABLE_TO_grok3_<N>.md` existed on `handoff/fable-opus-combo29-all-20261114` at STEP 1 or at the STEP 4 channel read.

## what I am NOT sure about

I did not read other seats' `o_both.rows.txt`. I am not sure that run (4) matches every other seat. This seat's runs (1), (2) and (3) match the known answers.

## times: see stamps.txt

## git status --short and ls -la

```
 M forge-combo29/grok3/013/stamps.txt
?? config.json
?? forge-combo29/grok3/013/POOL.txt
?? forge-combo29/grok3/013/REPORT.md
?? forge-combo29/grok3/013/RESULT.txt
```

```
total 1276
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:40 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2301 Nov 20 18:54 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56204 Nov 20 19:37 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51619 Nov 20 19:37 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56243 Nov 20 18:58 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51542 Nov 20 18:58 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56702 Nov 20 19:03 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51675 Nov 20 19:03 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56397 Nov 20 19:07 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51558 Nov 20 19:07 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56157 Nov 20 19:12 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51637 Nov 20 19:12 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 55592 Nov 20 19:16 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51483 Nov 20 19:16 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56247 Nov 20 19:20 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51520 Nov 20 19:20 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56007 Nov 20 19:24 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51498 Nov 20 19:24 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 55954 Nov 20 19:29 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51587 Nov 20 19:29 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56323 Nov 20 19:33 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51654 Nov 20 19:33 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:54 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45710 Nov 20 18:54 half.out
-rwxr-xr-x 1 ubuntu ubuntu   986 Nov 20 18:54 half.sh
-rw-r--r-- 1 ubuntu ubuntu 42004 Nov 20 18:53 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:52 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:52 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:52 honesty_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu  1022 Nov 20 18:54 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:52 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:52 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:52 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:52 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:52 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:52 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:54 o_runs.py
-rwxr-xr-x 1 ubuntu ubuntu  1755 Nov 20 18:54 play.sh
-rw-r--r-- 1 ubuntu ubuntu   154 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  5665 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   295 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    90 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   453 Nov 20 19:41 stamps.txt
```
