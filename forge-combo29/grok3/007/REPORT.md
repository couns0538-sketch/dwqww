# grok3 seat 007

Seat 007, arm 1, 20,000 nodes, chunks of 250 openings (500 games). Model Grok 4.7. SEAT.txt: `seat 007, arm 1, nodes 20000, model Grok 4.7, 2026-11-20T18:48:43Z, token 16840878716125`. Branch `for-fable-and-opus/grok3-007`. Match is the main match: IdeaB8 and HindsightDepth both on, against both off.

## Patch

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`, the required hash. The patch came from `4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt` (`git rev-parse FETCH_HEAD` printed that commit). In the work tree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`, `git apply --check ~/b8.patch` and `git apply ~/b8.patch` both exited 0 (`APPLY OK`).

The first cmake used `/usr/bin/c++`, which is Clang 18 and failed to link (`cannot find -lstdc++`). The brief requires g++ (GCC 13 or newer, GCC's own C++ library). I removed `~/build` and configured again with `-DCMAKE_CXX_COMPILER=g++`. CMake identified GNU 13.3.0. `/proc/cpuinfo` has AVX-512 and BMI2, so I did not add `-DFORGE_PORTABLE=ON` or `-DFORGE_MARCH`. The engine is `/home/ubuntu/build/forge`. Nothing of the build was committed.

## Honesty

Each line was a fresh process, with no `setoption`. Raw output is in this folder.

- bench 11: `nodes 312866` (required 312866)
- bench 13: `nodes 862329` (required 862329)
- bench 16: `nodes 3024920` (required 3024920)
- go perft 5: `nodes 4865609` (required 4865609)

## Four O runs

`o_runs.py` on `/home/ubuntu/build/forge` and `~/first200.fens` (`sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines). Sums below are `awk` over the committed `.rows.txt` files. Each `.meta` names exe `/home/ubuntu/build/forge`, sha256 `09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422`, id name `Chess Engine Forge 6.4.24 candidate`.

Known text, and this build:

1. Both off. Required sum 9,500,069 and first three 41,311 / 24,872 / 28,574. File: rows 200, sum 9500069, first 41311 24872 28574. `sha256sum o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7` (required that hash).
2. IdeaB8 only. Required sum 9,718,009 and first three 17,283 / 17,878 / 31,115. File: rows 200, sum 9718009, first 17283 17878 31115.
3. HindsightDepth only. Required sum 9,845,650 and first three 23,395 / 31,504 / 35,958. File: rows 200, sum 9845650, first 23395 31504 35958.
4. Both on. No required answer. File: rows 200, sum 9758416, first 18538 34070 39093. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed 200.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07` (required that hash). `wc -l ~/uho.epd` printed 2632036. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` (required 2632036 lines and that hash). Seat openings: `wc -l ~/mine.epd` printed 13390. The last 300 lines were kept for the controls. Chunks take the top; 11 chunks use 2,750 lines.

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): `setoption name IdeaB8 value true` count 20, `setoption name HindsightDepth value true` count 20, refusal count 0. fastchess accepted `engine=true`. The twenty log lines around the first IdeaB8 setoption are in that file.

C-HALF: `python3 ~/games_tsv.py pool FULL forge-combo29/grok3/007/half.tsv` printed `side FULL: games 400 W-L-D 285-40-75 pairs 200 (openings not in exactly 2 games: 0)` and `ptnml [3, 5, 34, 60, 98] Elo +247.69 95% [+214.26, +285.60]`. FULL's Elo is above +20. The same numbers are in `half.out`.

## POOL.txt and chunks

11 chunks, each 500 games, 5,500 games. `POOL.txt` pasted as it stands:

```
side ON: games 5500 W-L-D 1628-1330-2542 pairs 2750 (openings not in exactly 2 games: 0)
ptnml [103, 569, 1175, 733, 170] Elo +18.84 95% [+12.81, +24.88]
```

Every chunk log contains one `Finished match`. Grep of all `chunk_*.out` for adjudicat, resign, maxmoves, syzygy, or tablebase printed 0 on each file. The 5,500 finish reasons in those logs are: White mates 1641, Black mates 1317, 3-fold repetition 1742, fifty moves 440, insufficient mating material 348, stalemate 12. The TSV `Termination` field is `normal` on all 5,500 rows. White and Black are each ON 2750 times and OFF 2750 times. Result counts in the TSV files: 1-0 1641, 0-1 1317, 1/2-1/2 2542.

The 95% interval [+12.81, +24.88] contains about +17 and does not contain about +10. That is the interval `games_tsv.py` printed. I do not call the two ideas additive or overlapping beyond that interval.

## suspicions, not proven

fastchess wrote `config.json` in the repository root at 19:38, because `play.sh` was started with that working directory. I opened it. `resign.enabled`, `draw.enabled`, `maxmoves.enabled`, and `tb_adjudication` are false. I did not commit it. I am not sure whether fastchess loaded that file during the match. The match command did not pass adjudication flags, and the chunk logs contain none of those words.

No `FABLE_TO_grok3_<N>.md` was on `handoff/fable-opus-combo29-all-20261114` at step 1 or in the middle of step 4 (`git ls-tree` of `forge-combo29/soak_all/`). Nothing from the channel changed this run.

## what I did NOT do

I did not open a pull request. I did not change engine source. I did not commit an executable, a net, a PGN, the book, or the patch. I did not force-push, and I did not push any branch except `for-fable-and-opus/grok3-007`. I did not play the fallback match. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not repeat an opening.

## what I am NOT sure about

I am not sure the node counts of run 4 will match every other seat until those seats are compared. This seat's run 4 sum is 9758416, first three 18538 / 34070 / 39093, and 200 positions differ from run 1. I am not sure whether `config.json` in the repo root was read by fastchess. I am not sure a later channel file appeared after the mid-step-4 fetch.

## times: see stamps.txt

The first stamp is `2026-11-20T18:49:01Z STEP 1 seat`. Minute 46 fell after chunk 11 was already running. Chunk 11 finished at `2026-11-20T19:38:05Z`. `play.out` then printed `minute 46: no new chunk`.

## git status --short

 M forge-combo29/grok3/007/stamps.txt
?? config.json
?? forge-combo29/grok3/007/POOL.txt
?? forge-combo29/grok3/007/REPORT.md
?? forge-combo29/grok3/007/RESULT.txt

## ls -la forge-combo29/grok3/007

total 1384
drwxr-xr-x 2 ubuntu ubuntu  4096 Nov 20 19:41 .
drwxr-xr-x 3 ubuntu ubuntu  4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu  2381 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 56069 Nov 20 19:33 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 51626 Nov 20 19:33 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 56162 Nov 20 19:38 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 51670 Nov 20 19:38 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 56259 Nov 20 18:57 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 51524 Nov 20 18:57 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 56447 Nov 20 19:01 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 51486 Nov 20 19:01 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 56215 Nov 20 19:05 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 51530 Nov 20 19:05 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 56285 Nov 20 19:09 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 51607 Nov 20 19:09 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 55861 Nov 20 19:13 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 51324 Nov 20 19:13 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 56222 Nov 20 19:17 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 51632 Nov 20 19:17 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 56315 Nov 20 19:21 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 51576 Nov 20 19:21 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 55870 Nov 20 19:25 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 51477 Nov 20 19:25 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 56497 Nov 20 19:29 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 51745 Nov 20 19:29 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  2779 Nov 20 18:52 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu 45585 Nov 20 18:52 half.out
-rw-r--r-- 1 ubuntu ubuntu   986 Nov 20 18:52 half.sh
-rw-r--r-- 1 ubuntu ubuntu 41958 Nov 20 18:52 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu   274 Nov 20 18:50 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu  1022 Nov 20 18:52 match.sh
-rw-r--r-- 1 ubuntu ubuntu  2899 Nov 20 18:50 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:50 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2895 Nov 20 18:50 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   839 Nov 20 18:50 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:50 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   840 Nov 20 18:50 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  2896 Nov 20 18:50 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   841 Nov 20 18:50 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  3582 Nov 20 18:52 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu  1755 Nov 20 18:52 play.sh
-rw-r--r-- 1 ubuntu ubuntu   154 Nov 20 19:39 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu  9702 Nov 20 19:41 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu   295 Nov 20 19:40 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   540 Nov 20 19:41 stamps.txt
