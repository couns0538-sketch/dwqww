# Seat 016 arm 6

Arm 6, id S32, source seat 074, commit 0fd01685b0465c11e29816b5a759e6496d2a69ae, switch IdeaS32.
exe P is /home/ubuntu/build-work/forge. exe B is /home/ubuntu/build-base/forge.
Both report id name Chess Engine Forge 6.4.24 candidate.

## Patch

sha256 of ~/arm.patch, from patch_sha256.txt:

```
18fd94526ddf7f0d7a3af2c584f478d983ebdb8bfb68fd1193eaa1b893c6add5  /home/ubuntu/arm.patch
```

That is the arm 6 sha256. `git apply --check` succeeded, then `git apply` applied the patch in the work tree. After the builds, `git apply --reverse --check` also succeeded. apply_stat.txt:

```
 forge-combo29/include/forge/search.hpp |  6 ++++++
 forge-combo29/src/search.cpp           | 30 +++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  5 +++++
 3 files changed, 40 insertions(+), 1 deletion(-)
```

The CPU has AVX-512F/BW/CD/DQ/VL and BMI2, and g++ is 13.3.0, so the release build used the CMake default `-march=x86-64-v4` with FORGE_PORTABLE left off.

## Honesty

Pasted from `python3 tables.py`, which reads the raw bench and perft files:

```
honesty
honesty_B_bench11.txt nodes 312866 expect 312866 ok
honesty_B_bench13.txt nodes 862329 expect 862329 ok
honesty_B_bench16.txt nodes 3024920 expect 3024920 ok
honesty_B_perft5.txt nodes 4865609 expect 4865609 ok
honesty_P_bench11.txt nodes 312866 expect 312866 ok
honesty_P_bench13.txt nodes 862329 expect 862329 ok
honesty_P_bench16.txt nodes 3024920 expect 3024920 ok
honesty_P_perft5.txt nodes 4865609 expect 4865609 ok
```

## Three O runs

Same script, against the arm table (B sum 9500069, first 41311 / 24872 / 28574; on sum 9547450, first 41442 / 24989 / 28711; 200 differ):

```
O
B positions 200 sum 9500069 first 41311 24872 28574
P_off positions 200 sum 9500069 first 41311 24872 28574
P_on positions 200 sum 9547450 first 41442 24989 28711
off_equal 200 of 200
on_differ 200 of 200
B_vs_table ok
off_vs_B yes
on_vs_table yes
```

exe B was not sent IdeaS32. That option does not exist on the plain engine. exe P was sent IdeaS32 false for run (2) and IdeaS32 true for run (3). Threads, Hash, and the S14 options were sent in that order before every position, each followed by isready. IdeaS32_OwedSlack was never sent.

## Book

book_sha256.txt:

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both match the stated copy. `wc -l` on the epd was 2632036. Seat 016 took every 90th line from line 16: 29245 lines in mine.epd. The last 300 were held back for the controls.

## C-ARRIVE

arrive_check.txt counts:

```
grep -c setoption name IdeaS32 value true: 20
grep -c unknown option|invalid value|No such option: 0
```

The first setoption of the switch is in that file, with the surrounding log lines. arrive=ok.

## C-HALF

Pasted from half_pool.txt, which is the stdout of `python3 games_tsv.py pool FULL half.tsv`:

```
side FULL: games 400 W-L-D 236-36-128 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 8, 39, 94, 58] Elo +190.85 95% [+165.12, +218.64]
```

FULL's Elo is +190.85, above +20. half=ok.

## Pool

18 chunks, 9000 games. Each chunk tsv has 500 lines. POOL.txt:

```
side ON: games 9000 W-L-D 2416-2436-4148 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [200, 1118, 1888, 1090, 204] Elo -0.77 95% [-5.45, +3.91]
```

Every termination field in the 9000 rows is the word normal, which is what fastchess wrote in the PGN header. The pool script accepted every result as 1-0, 0-1, or 1/2-1/2.

## suspicions, not proven

The point estimate is -0.77 Elo. The 95% interval is [-5.45, +3.91]. That interval includes a small gain and a small loss. This sample does not separate a 3 to 8 Elo gain from noise, and it does not establish a loss of that size either.

I did not replay this morning's seat 030 PGN through games_tsv.py, so I have not checked that script's published known answer on that file.

## what I did NOT do

I did not open a pull request. I did not commit engine source, the patch, an executable, a net, or a PGN. I did not switch to arm 10, because run (3) matched the table. I did not pass adjudication flags to fastchess. fastchess wrote config.json in the repository root while the match ran there; resign, draw, maxmoves, and tb_adjudication are enabled false in that file, and I did not commit it. I did not send IdeaS32_OwedSlack. No FABLE_TO_grok2 file was on the handoff branch at the fetches I made. I did not kill a running chunk: play.sh printed "minute 95: no new chunk" after chunk 18 had already finished, which was before minute 103.

## what I am NOT sure about

I am not sure the morning O harness sent the S14 options once per process or before every position. This run sent them before every position, and the node counts matched the table. I am not sure which fastchess revision was intended beyond "clone --depth 1" of the official repository. The build printed GIT_SHA d6e3a7a.

times: see stamps.txt

## git status --short and ls -la

The block below is the command output taken after these step 5 files existed, and it is appended by the shell.

```
$ git status --short
 M forge-combo29/grok2/016/stamps.txt
?? config.json
?? forge-combo29/grok2/016/POOL.txt
?? forge-combo29/grok2/016/REPORT.md
?? forge-combo29/grok2/016/RESULT.txt

$ ls -la forge-combo29/grok2/016
total 3680
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu     55 Nov 20 13:26 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    229 Nov 20 13:26 apply_stat.txt
-rw-r--r-- 1 ubuntu ubuntu   2201 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:27 book_sha256.txt
-rw-r--r-- 1 ubuntu ubuntu  56186 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51422 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56255 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56453 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51402 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56485 Nov 20 14:35 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51467 Nov 20 14:35 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56525 Nov 20 14:40 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51670 Nov 20 14:40 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56083 Nov 20 14:45 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51459 Nov 20 14:45 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56085 Nov 20 14:50 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51345 Nov 20 14:50 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56449 Nov 20 14:55 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51599 Nov 20 14:55 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  55991 Nov 20 15:00 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51504 Nov 20 15:00 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56067 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51255 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56321 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51271 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55892 Nov 20 13:45 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51223 Nov 20 13:45 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56693 Nov 20 13:50 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51382 Nov 20 13:50 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56201 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51516 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56300 Nov 20 14:00 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51402 Nov 20 14:00 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56438 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  55812 Nov 20 14:10 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51435 Nov 20 14:10 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56286 Nov 20 14:15 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51353 Nov 20 14:15 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46743 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:30 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1090 Nov 20 13:27 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42150 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    715 Nov 20 13:24 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1028 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    797 Nov 20 13:25 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 502510 Nov 20 13:25 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:25 o_B.rows
-rw-r--r-- 1 ubuntu ubuntu    832 Nov 20 13:25 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 514057 Nov 20 13:25 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:25 o_P_off.rows
-rw-r--r-- 1 ubuntu ubuntu    831 Nov 20 13:25 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 513788 Nov 20 13:25 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:25 o_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu   4579 Nov 20 13:24 o_run.py
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:26 patch_sha256.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5382 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1017 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   2847 Nov 20 13:25 tables.py
```
