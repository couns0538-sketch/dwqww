# grok3 seat 002

Seat 002, arm 2, 2000 nodes. Chunk size 500 openings (1000 games). Match is main: IdeaB8 true and HindsightDepth true (ON) against both false (OFF). SEAT.txt: `seat 002, arm 2, nodes 2000, model Grok 4.7, 2026-11-20T18:48:31Z, token 276201675532545`.

## Patch

`sha256sum ~/b8.patch` printed `f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474`. That is the required hash. The patch was `git show 4bf95fd80adf523e97fa250bb8572c946cf0fc75:forge-combo29/grok/028/idea.patch.txt` after `git rev-parse FETCH_HEAD` printed `4bf95fd80adf523e97fa250bb8572c946cf0fc75`. In the worktree `../work` at `6b98f2170a3210e71beed04bbd2553972c253ed7`, `git apply --check ~/b8.patch` then `git apply ~/b8.patch` printed `APPLY_OK` and:

```
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

Nothing of that worktree or the binary was committed. `/usr/bin/c++` is Clang 18.1.3 and its link failed (`cannot find -lstdc++`). The brief requires g++ and GCC's C++ library. `g++` is GCC 13.3.0 and links. CMake was re-run with `-DCMAKE_CXX_COMPILER=g++` and identified `GNU 13.3.0`. The CPU has AVX-512 and BMI2, so no portable flags. The engine file is `/home/ubuntu/build/forge`.

## Honesty

Fresh processes, no setoption. Raw files in this folder.

- `honesty_bench11.txt`: `info string bench depth 11 nodes 312866 time 164 nps 1907719`
- `honesty_bench13.txt`: `info string bench depth 13 nodes 862329 time 441 nps 1955394`
- `honesty_bench16.txt`: `info string bench depth 16 nodes 3024920 time 1459 nps 2073283`
- `honesty_perft5.txt` last line: `nodes 4865609`

Required: 312866, 862329, 3024920, 4865609. All four match.

## Four O runs

`o_runs.py` on `/home/ubuntu/build/forge` and `~/first200.fens` (sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`, 200 lines). Sums below were counted again from the row files.

| run | options | sum | first three | required |
| --- | --- | --- | --- | --- |
| o_off | IdeaB8=false HindsightDepth=false | 9500069 | 41311 / 24872 / 28574 | 9500069 and 41311 / 24872 / 28574 |
| o_b8 | IdeaB8=true HindsightDepth=false | 9718009 | 17283 / 17878 / 31115 | 9718009 and 17283 / 17878 / 31115 |
| o_k3 | IdeaB8=false HindsightDepth=true | 9845650 | 23395 / 31504 / 35958 | 9845650 and 23395 / 31504 / 35958 |
| o_both | IdeaB8=true HindsightDepth=true | 9758416 | 18538 / 34070 / 39093 | no known answer |

`sha256sum forge-combo29/grok3/002/o_off.rows.txt` printed `dc1329e5625abd4e0fc1b5a10ab47f7409010db8024b0035e01054a94bdca5a7`. That is the required hash. `paste o_off.rows.txt o_both.rows.txt | awk '$2 != $5' | wc -l` printed `200` (all 200 positions differ). Each run wrote 200 rows. The `.meta` files name exe `/home/ubuntu/build/forge`, id name `Chess Engine Forge 6.4.24 candidate`, and the option lines that were sent. o_both.rows.txt.meta includes `setoption name IdeaB8 value true` and `setoption name HindsightDepth value true`.

## Book

`sha256sum ~/uho.zip` printed `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. `wc -l ~/uho.epd` printed `2632036`. `sha256sum ~/uho.epd` printed `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both hashes match the brief. `~/mine.epd` has 13390 lines (seat 002, lines at or after 2150002, every 36th).

## games_tsv.py known answer

`sha256sum ~/ka.tsv` printed `6d3192c4f5e3a131b3c290cab89e23517b53bbb112d3c4f44ac9ae16c4c293fd`. `python3 ~/games_tsv.py pool ON ~/ka.tsv` printed:

```
side ON: games 500 W-L-D 137-132-231 pairs 250 (openings not in exactly 2 games: 0)
ptnml [16, 59, 89, 76, 10] Elo +3.47 95% [-17.59, +24.57]
```

That is the required text.

## C-ARRIVE and C-HALF

C-ARRIVE (`arrive_check.txt`): IdeaB8 value true count 20, HindsightDepth value true count 20, refusal pattern count 0. The same file has the 20 log lines around the first `setoption name IdeaB8 value true`. fastchess accepted `engine=true`.

C-HALF, from `half.tsv` with `python3 ~/games_tsv.py pool FULL`:

```
side FULL: games 400 W-L-D 266-53-81 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 9, 47, 58, 84] Elo +206.25 95% [+175.44, +240.28]
```

FULL's Elo is +206.25, above +20. Pass. `half.out` also ends with `Finished match` and fastchess Elo 206.25.

## POOL.txt and chunks

26 chunks. Each `chunk_N.tsv` is 1000 lines. Each `chunk_N.out` contains `Finished match` once. 0 games with a result other than 1-0, 0-1, or 1/2-1/2. `play.sh` then printed `openings used up` and exited 0. Usable openings are 13390 - 300 = 13090; 26 * 500 = 13000, and 27 * 500 = 13500 would pass the reserved tail, so the script stops. No `FAILED` line in `~/play.log`. No pull of a 27th chunk.

Pasted `POOL.txt`:

```
side ON: games 26000 W-L-D 9602-8268-8130 pairs 13000 (openings not in exactly 2 games: 0)
ptnml [1074, 2587, 4820, 2969, 1550] Elo +17.84 95% [+14.53, +21.16]
```

## suspicions, not proven

The both-on node sum (9758416) sits between the plain engine and each idea alone. That is a fact about depth-12 node counts on these 200 positions. It is not, by itself, a measurement of Elo overlap. The Elo in POOL.txt is the measurement this seat was asked for.

fastchess wrote `config.json` in the repository root because `play.sh` was started with that working directory. In that file, resign, draw, maxmoves, and tablebase adjudication are `enabled: false`. The file is outside this folder and was not committed. I did not pass `-draw`, `-resign`, or `-maxmoves`.

## what I did NOT do

No pull request. No `--force`. No commit of engine source, the exe, a net, a PGN, or the book. No second build. No fallback match (`ON_B8` stays true). No repeated opening. No chunk after the script said openings were used up. No edit of another branch. The channel fetch at STEP 1 and again during STEP 4 listed no `FABLE_TO_grok3_*.md`.

## what I am NOT sure about

I have not seen another seat's `o_both` rows, so I cannot check that 9758416 and 18538/34070/39093 are what the other seats printed. The 95% interval is the one `games_tsv.py` prints from the pair scores. I did not recount the 26000 games by hand beyond the script, the 1000-line check, and the zero bad-result check.

## times: see stamps.txt

The first line of stamps.txt is `2026-11-20T18:48:46Z STEP 1`. Chunk 26 is `2026-11-20T19:25:26Z chunk 26 done`. `play.out` then says `openings used up`.

## git status --short and ls -la

Taken after POOL.txt, REPORT.md, RESULT.txt, and the STEP 5 stamp line were written, before the STEP 5 commit. `config.json` is the fastchess dump described above and is not added.

```
$ git status --short
 M forge-combo29/grok3/002/stamps.txt
?? config.json
?? forge-combo29/grok3/002/POOL.txt
?? forge-combo29/grok3/002/REPORT.md
?? forge-combo29/grok3/002/RESULT.txt

$ ls -la forge-combo29/grok3/002
total 5784
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 19:30 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 18:48 ..
-rw-r--r-- 1 ubuntu ubuntu   2227 Nov 20 18:52 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu 111526 Nov 20 19:05 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu 102745 Nov 20 19:05 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu 111038 Nov 20 19:06 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu 102450 Nov 20 19:06 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu 110754 Nov 20 19:07 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu 102655 Nov 20 19:07 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu 110289 Nov 20 19:09 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu 102348 Nov 20 19:09 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu 110836 Nov 20 19:10 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu 102686 Nov 20 19:10 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu 111283 Nov 20 19:11 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu 102507 Nov 20 19:11 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu 111218 Nov 20 19:13 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu 102630 Nov 20 19:13 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu 111198 Nov 20 19:14 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu 102542 Nov 20 19:14 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu 110723 Nov 20 19:15 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu 102401 Nov 20 19:15 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu 111108 Nov 20 19:16 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu 102572 Nov 20 19:16 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu 110885 Nov 20 18:54 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu 102530 Nov 20 18:54 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu 110832 Nov 20 19:18 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu 102677 Nov 20 19:18 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu 111365 Nov 20 19:19 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu 102594 Nov 20 19:19 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu 110581 Nov 20 19:20 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu 102435 Nov 20 19:20 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu 110640 Nov 20 19:21 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu 102578 Nov 20 19:21 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu 110297 Nov 20 19:23 chunk_24.out
-rw-r--r-- 1 ubuntu ubuntu 102374 Nov 20 19:23 chunk_24.tsv
-rw-r--r-- 1 ubuntu ubuntu 110951 Nov 20 19:24 chunk_25.out
-rw-r--r-- 1 ubuntu ubuntu 102418 Nov 20 19:24 chunk_25.tsv
-rw-r--r-- 1 ubuntu ubuntu 110163 Nov 20 19:25 chunk_26.out
-rw-r--r-- 1 ubuntu ubuntu 102264 Nov 20 19:25 chunk_26.tsv
-rw-r--r-- 1 ubuntu ubuntu 110855 Nov 20 18:55 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu 102577 Nov 20 18:55 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu 110644 Nov 20 18:56 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu 102433 Nov 20 18:56 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu 110998 Nov 20 18:58 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu 102861 Nov 20 18:58 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu 110980 Nov 20 18:59 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu 102594 Nov 20 18:59 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu 110916 Nov 20 19:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu 102502 Nov 20 19:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu 110926 Nov 20 19:01 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu 102717 Nov 20 19:01 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu 110637 Nov 20 19:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu 102461 Nov 20 19:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu 111228 Nov 20 19:04 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu 102740 Nov 20 19:04 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 18:51 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  45643 Nov 20 18:52 half.out
-rw-r--r-- 1 ubuntu ubuntu    986 Nov 20 18:51 half.sh
-rw-r--r-- 1 ubuntu ubuntu  41944 Nov 20 18:52 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 18:50 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 18:50 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 18:50 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1022 Nov 20 18:51 match.sh
-rw-r--r-- 1 ubuntu ubuntu   2899 Nov 20 18:50 o_b8.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:50 o_b8.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2895 Nov 20 18:50 o_both.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    839 Nov 20 18:50 o_both.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:50 o_k3.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    840 Nov 20 18:50 o_k3.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   2896 Nov 20 18:50 o_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    841 Nov 20 18:50 o_off.rows.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   3582 Nov 20 18:50 o_runs.py
-rw-r--r-- 1 ubuntu ubuntu   1755 Nov 20 18:51 play.sh
-rw-r--r-- 1 ubuntu ubuntu    160 Nov 20 19:28 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6954 Nov 20 19:30 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    299 Nov 20 19:30 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 18:48 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1013 Nov 20 19:30 stamps.txt
```
