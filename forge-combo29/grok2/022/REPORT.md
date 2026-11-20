# Seat 022 arm 2 (B1b)

Arm 2, source seat 080, commit e778c1358711c0571e8f5cc4df87083cce98e03a, switch IdeaB1. Model Grok 4.7. Branch for-fable-and-opus/grok2-022.

## Patch sha256 and git apply

`sha256sum ~/arm.patch` (saved in patch.sha256):

```
d9e077d7365c96807200f52126e7a2823db65b2c4e5113371050317b019e8196  /home/ubuntu/arm.patch
```

That is the arm table's sha256. `git rev-parse FETCH_HEAD` after `git fetch --depth 1 origin for-fable-and-opus/grok-080` printed e778c1358711c0571e8f5cc4df87083cce98e03a. `git apply --check ~/arm.patch && git apply ~/arm.patch` in the work tree printed APPLY OK. `git diff --stat` afterwards is work_diff_stat.txt:

```
 forge-combo29/include/forge/nnue.hpp   | 19 +++++++
 forge-combo29/include/forge/search.hpp |  5 ++
 forge-combo29/src/nnue.cpp             | 62 ++++++++++++++++++++++
 forge-combo29/src/search.cpp           | 96 +++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |  4 +-
 5 files changed, 183 insertions(+), 3 deletions(-)
```

The host has AVX-512 and BMI2, so the release build did not pass FORGE_PORTABLE. Compiler `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. Command in build_note.txt: `cmake -S forge-combo29 -B forge-combo29/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build forge-combo29/build -j2`. Exe B is /agent/repos/base/forge-combo29/build/forge. Exe P is /agent/repos/work/forge-combo29/build/forge.

## Honesty numbers

A fresh process for each line, no setoption before the measured command. The nodes below are grep of the committed raw files:

```
honesty_B_bench11.raw: info string bench depth 11 nodes 312866
honesty_B_bench13.raw: info string bench depth 13 nodes 862329
honesty_B_bench16.raw: info string bench depth 16 nodes 3024920
honesty_B_perft5.raw: nodes 4865609
honesty_P_bench11.raw: info string bench depth 11 nodes 312866
honesty_P_bench13.raw: info string bench depth 13 nodes 862329
honesty_P_bench16.raw: info string bench depth 16 nodes 3024920
honesty_P_perft5.raw: nodes 4865609
```

Known targets are 312866, 862329, 3024920, and 4865609. Both exes match all four. The first harness attempt timed out (it selected on a buffered pipe and missed lines already read). Those runs wrote no raw files. The files above are the rerun.

## Three O runs

`python3 o_table.py` reading o_B.raw, o_P_off.raw, and o_P_on.raw:

```
B n=200 sum=9500069 first=41311 24872 28574
P_off n=200 sum=9500069 first=41311 24872 28574
P_on n=200 sum=9748678 first=17841 25977 43905
off_differ=0 on_differ=200
off_len_match=True on_len_match=True
```

Against the brief: run (1) sum 9500069 and first three 41311 / 24872 / 28574, match. Run (2) equal to run (1) on all 200 positions, match (off_differ=0). Run (3) arm 2: sum 9748678, first three 17841 / 25977 / 43905, 200 differ, match. Options are in the .meta files: Threads 1, Hash 16, the S14 list, and IdeaB1 false or true on exe P. Exe B was not sent IdeaB1.

## Book sha256

book_sha.txt:

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
epd_lines 2632036
mine_lines 29245
```

Both hashes match the brief. Seat 022 took every 90th line of the book starting at line 22 (29245 lines). The last 300 of those are ctl.epd and were not used as match openings. Chunks 1 to 13 used lines 1 to 3250 of mine.epd.

## C-ARRIVE and C-HALF

arrive_check.txt, from the trace log of `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`:

```
setoption name IdeaB1 value true: 20
unknown option|invalid value|No such option: 0
```

engine=true was accepted. The count of the true setoption is 20, and the refusal count is 0.

half_pool.txt, from `python3 ~/games_tsv.py pool FULL` on half.tsv (400 games, 200 pairs):

```
side FULL: games 400 W-L-D 216-29-155 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 3, 54, 96, 47] Elo +176.10 95% [+153.70, +199.95]
```

FULL at 20000 nodes against HALF at 10000 nodes, both IdeaB1 false. Elo +176.10 is above +20. Pass.

## POOL.txt and chunks

13 chunks, each 500 games, 6500 games. `python3 ~/games_tsv.py pool ON` on chunk_1.tsv through chunk_13.tsv wrote POOL.txt:

```
side ON: games 6500 W-L-D 1755-1712-3033 pairs 3250 (openings not in exactly 2 games: 0)
ptnml [155, 779, 1337, 826, 153] Elo +2.30 95% [-3.28, +7.88]
```

No play.log line contains FAILED. Each chunk out file has 0 lines matching "adjudication". play.sh printed `minute 95: no new chunk` after chunk 13 and exited. Chunk 13's log time is 2026-11-20T15:00:12Z, before minute 103 (15:04:46Z). No fastchess process was killed.

## suspicions, not proven

The 95% interval [-3.28, +7.88] includes both a loss and a gain of a few Elo. I am not claiming IdeaB1 gained strength. The node counts for the patch matched the arm table on all 200 positions, so I have no suspicion that exe P is the wrong build.

## what I did NOT do

I did not open a pull request. I did not commit an engine source file or a binary. I did not send IdeaB1_Lanes, IdeaB1_Fade, IdeaB1_Scale, or IdeaB1_Cap. I did not pass -draw, -resign, -maxmoves, or tablebase adjudication. I did not replay an opening. I did not play the reserved last 300 lines of mine.epd. No FABLE_TO_grok2 file was on the channel at the fetches I made, so I did not touch ~/STOP_PLAY.

## what I am NOT sure about

C-HALF was started with the repository as the working directory, and fastchess wrote an untracked config.json there. I deleted it. In that file resign, draw, maxmoves, and tablebase adjudication were enabled false. Later matches were started from the home directory. I am not sure fastchess has no other default cutoff, but the chunk logs do not contain the word adjudication, and the games that I saw ended by mate, repetition, the fifty-move rule, or insufficient material.

The git status and ls pasted below were captured after POOL.txt, RESULT.txt, and this report's body existed, and before this listing was appended. The byte size they show for REPORT.md is the size before the listing was added.

I did not run `git apply --check` a second time after the patch was already applied.

## times: see stamps.txt

## git status --short and ls -la

The listing is appended below this line.

```
$ git status --short
 M forge-combo29/grok2/022/stamps.txt
?? forge-combo29/grok2/022/POOL.txt
?? forge-combo29/grok2/022/REPORT.md
?? forge-combo29/grok2/022/RESULT.txt

$ ls -la forge-combo29/grok2/022
total 2660
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:03 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:21 ..
-rw-r--r-- 1 ubuntu ubuntu   2176 Nov 20 13:33 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    217 Nov 20 13:37 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    542 Nov 20 13:30 build_note.txt
-rw-r--r-- 1 ubuntu ubuntu  56392 Nov 20 14:41 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51374 Nov 20 14:41 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  55580 Nov 20 14:47 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51116 Nov 20 14:47 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56003 Nov 20 14:54 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51405 Nov 20 14:54 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56395 Nov 20 15:00 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51449 Nov 20 15:00 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56216 Nov 20 13:44 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51095 Nov 20 13:44 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56639 Nov 20 13:50 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51236 Nov 20 13:50 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56445 Nov 20 13:56 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51246 Nov 20 13:56 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56537 Nov 20 14:03 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51281 Nov 20 14:03 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56258 Nov 20 14:09 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51470 Nov 20 14:09 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56691 Nov 20 14:15 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51548 Nov 20 14:15 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56077 Nov 20 14:22 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51164 Nov 20 14:22 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56680 Nov 20 14:28 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51466 Nov 20 14:28 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56523 Nov 20 14:35 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51436 Nov 20 14:35 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:26 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:37 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47178 Nov 20 13:37 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:37 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu    985 Nov 20 13:37 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42308 Nov 20 13:37 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:37 half_tsv_count.txt
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5279 Nov 20 13:29 honesty_B_bench11.raw
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5279 Nov 20 13:29 honesty_B_bench13.raw
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5281 Nov 20 13:29 honesty_B_bench16.raw
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:29 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5554 Nov 20 13:29 honesty_B_perft5.raw
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5584 Nov 20 13:29 honesty_P_bench11.raw
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5584 Nov 20 13:29 honesty_P_bench13.raw
-rw-r--r-- 1 ubuntu ubuntu    190 Nov 20 13:29 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5586 Nov 20 13:29 honesty_P_bench16.raw
-rw-r--r-- 1 ubuntu ubuntu    192 Nov 20 13:29 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5859 Nov 20 13:29 honesty_P_perft5.raw
-rw-r--r-- 1 ubuntu ubuntu   4221 Nov 20 13:29 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu    965 Nov 20 13:37 match.sh
-rw-r--r-- 1 ubuntu ubuntu    928 Nov 20 13:30 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 318426 Nov 20 13:30 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu    962 Nov 20 13:30 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 318747 Nov 20 13:30 o_P_off.raw
-rw-r--r-- 1 ubuntu ubuntu    961 Nov 20 13:30 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 319682 Nov 20 13:30 o_P_on.raw
-rw-r--r-- 1 ubuntu ubuntu   4983 Nov 20 13:29 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   1633 Nov 20 13:26 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:30 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu     89 Nov 20 13:30 patch.sha256
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:37 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   6549 Nov 20 15:03 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:21 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    668 Nov 20 15:03 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    349 Nov 20 13:30 work_diff_stat.txt
```
