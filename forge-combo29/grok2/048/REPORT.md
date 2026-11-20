# grok2 seat 048

Arm 8, K4b. Source seat 043. Switch IdeaK4. Commit 2f38a63656ec17062b581c933fcc77d961b946f1.

## Patch sha256 and git apply

The patch file sha256 matches the arm table. `git apply --check` and `git apply` both exited 0 on the work tree. The work tree is not this branch; no engine source is committed.

```
command: sha256sum ~/arm.patch
b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
expected_sha256 b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81
source_commit 2f38a63656ec17062b581c933fcc77d961b946f1
apply: git apply --check ~/arm.patch && git apply ~/arm.patch (both exit 0, recorded before this file)
worktree_diff_stat:
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)
```

The machine has AVX-512 and BMI2 (g++ 13.3.0), so the release build used the CMake default `-march=x86-64-v4` and did not set FORGE_PORTABLE. IdeaK4_Shrink was not sent; it stayed at the patch default.

## Honesty numbers

`extract_honesty.py` over the raw bench and perft files. Expected: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on both exes.

```
honesty_b_bench11.txt nodes 312866
honesty_b_bench13.txt nodes 862329
honesty_b_bench16.txt nodes 3024920
honesty_b_perft5.txt nodes 4865609
honesty_p_bench11.txt nodes 312866
honesty_p_bench13.txt nodes 862329
honesty_p_bench16.txt nodes 3024920
honesty_p_perft5.txt nodes 4865609
```

All eight match.

## Three O runs

`extract_o.py` on the raw transcripts. Expected base sum 9500069, first three 41311 / 24872 / 28574. Expected switch-off identical to base on all 200. Expected switch-on for arm 8: sum 8983632, first three 23741 / 21846 / 35911, 200 differ.

```
file /agent/repos/dwqww/forge-combo29/grok2/048/o_b.txt
count 200
sum 9500069
first 41311 24872 28574
---
file /agent/repos/dwqww/forge-combo29/grok2/048/o_off.txt
count 200
sum 9500069
first 41311 24872 28574
differ_from_first 0
---
file /agent/repos/dwqww/forge-combo29/grok2/048/o_on.txt
count 200
sum 8983632
first 23741 21846 35911
differ_from_first 200
---
```

All three match the table. Options sent, in order, were Threads 1, Hash 16, then the S14 list, then IdeaK4 false or true. Each was followed by isready. No unknown-option or invalid-value line appeared.

## Book sha256

```
sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
expected_zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
expected_epd_lines 2632036
expected_epd_sha 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
wc mine ctl
  29245 /home/ubuntu/mine.epd
    300 /home/ubuntu/ctl.epd
     10 /home/ubuntu/ctl_arrive.epd
    200 /home/ubuntu/ctl_half.epd
  29755 total
```

Zip and epd both match. Seat 048 took every 90th line starting at line 48. The last 300 lines of that slice were held back for the controls. The 22 chunks used lines 1-5500 of mine.epd and did not reach that reserve.

## C-ARRIVE and C-HALF

C-ARRIVE: `grep -c` of `setoption name IdeaK4 value true` was 20. `grep -c` of `unknown option|invalid value|No such option` was 0. The 20 log lines around the first switch setoption are in arrive_check.txt. The engine line in that window is `setoption name IdeaK4 value true`.

C-HALF, `games_tsv.py pool FULL` on half.tsv. Pass bar was Elo above +20.

```
side FULL: games 400 W-L-D 230-41-129 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 6, 47, 95, 51] Elo +178.33 95% [+154.09, +204.29]
```

Passed.

## POOL.txt and chunks

22 chunks, each 500 games, 11000 games. `play.log` has 22 `chunk N done` lines and no FAILED line. Pasted POOL.txt, from `games_tsv.py pool ON` on every chunk tsv:

```
side ON: games 11000 W-L-D 2852-3016-5132 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [293, 1381, 2260, 1329, 237] Elo -5.18 95% [-9.48, -0.88]
```

## suspicions, not proven

The pooled interval sits entirely below zero. That is the script's pair-score result. I did not try to explain it, and I did not rerun games.

Chunk 22 started after chunk 21 finished at 14:56:51Z. Minute 95 was 14:57:20Z. play.sh's own minute check allowed the chunk. It finished at 15:01:06Z, before minute 103 (15:05:20Z). I did not kill it.

During C-HALF, fastchess wrote an untracked config.json in the repository root because that shell's cwd was the repo. In that file, resign, draw, maxmoves, and tablebase adjudication were all `"enabled": false`. I deleted the file and did not commit it. Match commands never passed `-draw`, `-resign`, `-maxmoves`, or `-tb`. Chunk outs have no `adjudicat` line. The tsv termination field is `normal`.

## what I did NOT do

I did not open a pull request. I did not edit engine source on this branch. I did not commit an executable, a net, a PGN, or the book. I did not send IdeaK4_Shrink. I did not fall back to arm 10. I did not repeat an opening. No file `FABLE_TO_grok2_<N>.md` existed on `handoff/fable-opus-combo29-all-20261114` at STEP 1 or at any STEP 4 push, so no extra channel instruction was applied.

## what I am NOT sure about

I am not sure fastchess reads a config from a path other than the process cwd. Play was started from /tmp. The only config I inspected had adjudication switched off, and the command line did not turn it on.

The honesty bench processes were sent only the bench or perft line and quit. The id name stored in the .meta files is from a separate process that was sent `uci` then `quit`.

## times: see stamps.txt

The first stamp is 2026-11-20T13:22:20Z STEP 1. Later lines are the command output of `date -u` appended in each step.

## git status --short and ls -la

Taken after POOL.txt, REPORT.md, RESULT.txt, and the STEP 5 stamp existed, and before this section was appended. The byte size of REPORT.md in that ls is the size before these lines.

```
$ git status --short
 M forge-combo29/grok2/048/stamps.txt
?? forge-combo29/grok2/048/POOL.txt
?? forge-combo29/grok2/048/REPORT.md
?? forge-combo29/grok2/048/RESULT.txt

$ ls -la forge-combo29/grok2/048
total 3560
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2248 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    601 Nov 20 13:32 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56445 Nov 20 14:12 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51373 Nov 20 14:12 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56010 Nov 20 14:16 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:16 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56377 Nov 20 14:20 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51553 Nov 20 14:20 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56070 Nov 20 14:24 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51369 Nov 20 14:24 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56054 Nov 20 14:28 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:28 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56311 Nov 20 14:32 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51599 Nov 20 14:32 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56464 Nov 20 14:36 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51638 Nov 20 14:36 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56922 Nov 20 14:40 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51617 Nov 20 14:40 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56322 Nov 20 14:44 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51344 Nov 20 14:44 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56503 Nov 20 14:48 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51461 Nov 20 14:48 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56632 Nov 20 13:37 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51239 Nov 20 13:37 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56276 Nov 20 14:52 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51547 Nov 20 14:52 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56472 Nov 20 14:56 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51453 Nov 20 14:56 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56535 Nov 20 15:01 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51675 Nov 20 15:01 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56273 Nov 20 13:41 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51274 Nov 20 13:41 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56671 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51371 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56353 Nov 20 13:49 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51338 Nov 20 13:49 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56138 Nov 20 13:53 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51384 Nov 20 13:53 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56092 Nov 20 13:57 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 13:57 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56192 Nov 20 14:00 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51505 Nov 20 14:00 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56470 Nov 20 14:04 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 14:04 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56299 Nov 20 14:08 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51563 Nov 20 14:08 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    458 Nov 20 13:28 extract_honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1803 Nov 20 13:25 extract_o.py
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:28 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46718 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1080 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42361 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:24 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:24 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:25 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   4933 Nov 20 13:24 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:25 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:25 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:25 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    237 Nov 20 13:25 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:25 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    239 Nov 20 13:25 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:25 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   5038 Nov 20 13:25 honesty_p_uci.txt
-rwxr-xr-x 1 ubuntu ubuntu   2034 Nov 20 13:24 honesty.py
-rw-r--r-- 1 ubuntu ubuntu    282 Nov 20 13:28 honesty_table.txt
-rwxr-xr-x 1 ubuntu ubuntu   1016 Nov 20 13:28 match.sh
-rw-r--r-- 1 ubuntu ubuntu 308809 Nov 20 13:26 o_b.txt
-rw-r--r-- 1 ubuntu ubuntu    773 Nov 20 13:26 o_b.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 308934 Nov 20 13:26 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    807 Nov 20 13:26 o_off.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 307825 Nov 20 13:26 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu    806 Nov 20 13:26 o_on.txt.meta
-rwxr-xr-x 1 ubuntu ubuntu   3864 Nov 20 13:25 o_run.py
-rw-r--r-- 1 ubuntu ubuntu    363 Nov 20 13:26 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    768 Nov 20 13:26 patch_check.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:28 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6145 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    785 Nov 20 15:03 stamps.txt
```
