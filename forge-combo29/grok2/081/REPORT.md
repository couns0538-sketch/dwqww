# Seat 081, arm 1 (B1a)

Source seat 030, branch `for-fable-and-opus/grok-030`, commit `416700fe0ace1656a1285fc536c347718c1a4af7`. Switch `IdeaB1`. This seat's branch is `for-fable-and-opus/grok2-081`.

## Patch

`sha256sum ~/arm.patch` printed the arm table's hash, and `git apply --check` then `git apply` in the work tree both succeeded:

```
8f004d04b5eca26451e846eba346912e30c0a444746687f63b51a9df99c7171b  /home/ubuntu/arm.patch
```

`git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-030` printed `416700fe0ace1656a1285fc536c347718c1a4af7`.

The machine has AVX-512 and BMI2 and g++ 13.3.0, so both release builds used the CMake default (`FORGE_MARCH=x86-64-v4`, `FORGE_PORTABLE` off). Exe B is `/tmp/build-base/forge`. Exe P is `/tmp/build-work/forge`. No engine source and no binary was committed.

## Honesty

A fresh process for each line, no `setoption`. Expected: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, `go perft 5` = 4865609. Grep of the saved files:

```
forge-combo29/grok2/081/honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 164 nps 1907719
forge-combo29/grok2/081/honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 431 nps 2000763
forge-combo29/grok2/081/honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1555 nps 1945286
forge-combo29/grok2/081/honesty_B_perft5.txt:nodes 4865609
forge-combo29/grok2/081/honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 177 nps 1767604
forge-combo29/grok2/081/honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 461 nps 1870561
forge-combo29/grok2/081/honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1485 nps 2036983
forge-combo29/grok2/081/honesty_P_perft5.txt:nodes 4865609
```

## Three O runs

S14 in the listed order, then Threads 1, then Hash 16. Run 1 is exe B and does not send `IdeaB1` (exe B has no such option). Run 2 sends `IdeaB1 false`. Run 3 sends `IdeaB1 true`. `IdeaB1_Scale` and `IdeaB1_Fade` were never sent. Pasted output of `o_table.py` on the three row files:

```
positions 200 200 200
B sum 9500069 first 41311 24872 28574
OFF sum 9500069 first 41311 24872 28574 differ 0
ON sum 10081213 first 12481 31753 31668 differ 200
```

Arm table for B1a: sum 10,081,213; first three 12,481 / 31,753 / 31,668; 200 differ. Run 1 matches 9,500,069 and 41,311 / 24,872 / 28,574. Run 2 matches run 1 on all 200. Run 3 matches the arm table.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
2632036 /home/ubuntu/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes match the brief. Seat 081 takes every 90th line starting at line 81 (`wc -l` of `~/mine.epd` was 29244). The last 300 lines were the controls and were not used as chunk openings. 20 chunks use the first 5000 lines.

## C-ARRIVE

`arrive_check.txt` records the two counts: `setoption name IdeaB1 value true` occurred 20 times, and `unknown option|invalid value|No such option` occurred 0 times. The 20 log lines around the first switch setoption are in that file. The engine line is `ON <--- setoption name IdeaB1 value true`.

## C-HALF

Pasted output of `python3 ~/games_tsv.py pool FULL forge-combo29/grok2/081/half.tsv`:

```
side FULL: games 400 W-L-D 248-34-118 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 10, 35, 86, 69] Elo +207.46 95% [+180.08, +237.37]
```

FULL (20000 nodes) against HALF (10000 nodes), switch false on both. Elo +207.46 is above +20.

## Pool

20 chunks, 10000 games, each `chunk_N.tsv` has 500 lines. `awk` over every chunk: `10000 normal`. White and black are each 5000 ON and 5000 OFF. Pasted `POOL.txt` (output of `python3 ~/games_tsv.py pool ON` on the twenty chunk files):

```
side ON: games 10000 W-L-D 2665-2613-4722 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [236, 1221, 2056, 1229, 258] Elo +1.81 95% [-2.72, +6.34]
```

## Suspicions, not proven

fastchess, started with the repo as its working directory, wrote an untracked `config.json` in the repo root. I read it during chunk 1: resign, draw, maxmoves, and tb_adjudication were all `enabled: false`. I did not commit that file. I did not re-read it after every later chunk. The committed evidence that games were not adjudicated is the termination field: 10000 of 10000 are `normal`.

## What I did NOT do

I did not open a pull request. I did not change engine source. I did not send `IdeaB1_Scale` or `IdeaB1_Fade`. I did not pass `-draw`, `-resign`, `-maxmoves`, or tablebases. I did not fall back to arm 10. I did not repeat an opening. I did not commit a PGN, an executable, a net, or `config.json`. I did not force-push. No `FABLE_TO_grok2_*.md` file was on `handoff/fable-opus-combo29-all-20261114` at STEP 1 or at any later fetch, so no channel note applied.

## What I am NOT sure about

I did not compare fastchess's own pentanomial with `games_tsv.py` on all 10000 games. The reported Elo is only the `games_tsv.py` pool. I did not log the node count of every match move; C-HALF is the evidence that the node limit reaches the engine. After chunk 13, `~/commit_chunks.sh` committed each finished chunk about once a minute and fetched the channel. That script is outside the repo.

## times: see stamps.txt

The first stamp is `2026-11-20T13:23:21Z STEP 1 seat`. Chunk 20's stamp is `2026-11-20T15:00:19Z chunks 20`. `play.sh` then printed `minute 95: no new chunk`.

## git status --short and ls -la

Captured immediately before the STEP 5 commit. `config.json` is the untracked fastchess file described above.

```
$ git status --short
 M forge-combo29/grok2/081/stamps.txt
?? config.json
?? forge-combo29/grok2/081/POOL.txt
?? forge-combo29/grok2/081/REPORT.md
?? forge-combo29/grok2/081/RESULT.txt

$ ls -la forge-combo29/grok2/081
total 3284
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2208 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56060 Nov 20 14:16 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:16 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56687 Nov 20 14:20 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51270 Nov 20 14:20 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55861 Nov 20 14:25 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 14:25 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56419 Nov 20 14:29 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 14:29 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56199 Nov 20 14:33 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51475 Nov 20 14:33 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56562 Nov 20 14:37 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51439 Nov 20 14:37 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56609 Nov 20 14:42 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 14:42 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56391 Nov 20 14:46 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51434 Nov 20 14:46 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56443 Nov 20 14:50 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51485 Nov 20 14:50 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56389 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51688 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56438 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51129 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56822 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56317 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56265 Nov 20 13:46 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51371 Nov 20 13:46 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56809 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51441 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56862 Nov 20 13:54 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51519 Nov 20 13:54 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56565 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56397 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51399 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56166 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51498 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55967 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51366 Nov 20 14:12 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46466 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu  42063 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    771 Nov 20 13:27 o1_b.meta
-rw-r--r-- 1 ubuntu ubuntu 281917 Nov 20 13:27 o1_b.raw.txt
-rw-r--r-- 1 ubuntu ubuntu  31913 Nov 20 13:27 o1_b.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    805 Nov 20 13:27 o2_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281875 Nov 20 13:27 o2_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu  31935 Nov 20 13:27 o2_off.rows.txt
-rw-r--r-- 1 ubuntu ubuntu    804 Nov 20 13:27 o3_on.meta
-rw-r--r-- 1 ubuntu ubuntu 283263 Nov 20 13:27 o3_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu  32077 Nov 20 13:27 o3_on.rows.txt
-rw-r--r-- 1 ubuntu ubuntu   5250 Nov 20 13:27 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1090 Nov 20 13:27 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5861 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    227 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    780 Nov 20 15:02 stamps.txt
```
